"""Compare supervised classifiers required by the IAAC roadmap."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    AdaBoostClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB, GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

if __package__:
    from .data_preprocessing import (
        TARGET,
        convert_numeric_like_columns,
        feature_columns,
        load_and_deduplicate,
    )
else:
    from data_preprocessing import (
        TARGET,
        convert_numeric_like_columns,
        feature_columns,
        load_and_deduplicate,
    )

RANDOM_STATE = 42


def make_preprocessors(features: pd.DataFrame) -> dict[str, ColumnTransformer]:
    numeric = features.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]

    def create(numeric_scaler, sparse_threshold: float = 1.0) -> ColumnTransformer:
        numeric_pipeline = Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("scaler", numeric_scaler)]
        )
        categorical_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        return ColumnTransformer(
            [
                ("numeric", numeric_pipeline, numeric),
                ("categorical", categorical_pipeline, categorical),
            ],
            sparse_threshold=sparse_threshold,
        )

    return {
        "standard_sparse": create(StandardScaler()),
        "gaussian_dense": create(StandardScaler(), sparse_threshold=0.0),
        "bernoulli_sparse": create(MinMaxScaler()),
    }


def make_models(features: pd.DataFrame, include_xgboost: bool) -> dict[str, Pipeline]:
    preprocessors = make_preprocessors(features)
    standard = preprocessors["standard_sparse"]
    models = {
        "logistic_regression": Pipeline(
            [
                ("preprocess", standard),
                ("model", LogisticRegression(
                    max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE
                )),
            ]
        ),
        "decision_tree": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", DecisionTreeClassifier(
                    class_weight="balanced", random_state=RANDOM_STATE
                )),
            ]
        ),
        "knn": Pipeline(
            [
                ("preprocess", standard),
                ("model", KNeighborsClassifier(n_neighbors=5, n_jobs=-1)),
            ]
        ),
        "gaussian_naive_bayes": Pipeline(
            [
                ("preprocess", preprocessors["gaussian_dense"]),
                ("model", GaussianNB()),
            ]
        ),
        "bernoulli_naive_bayes": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", BernoulliNB()),
            ]
        ),
        "linear_svm": Pipeline(
            [
                ("preprocess", standard),
                ("model", SVC(kernel="linear", class_weight="balanced")),
            ]
        ),
        "rbf_svm": Pipeline(
            [
                ("preprocess", standard),
                ("model", SVC(kernel="rbf", class_weight="balanced")),
            ]
        ),
        "adaboost": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", AdaBoostClassifier(random_state=RANDOM_STATE)),
            ]
        ),
        "gradient_boosting": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", GradientBoostingClassifier(random_state=RANDOM_STATE)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                )),
            ]
        ),
        "extra_trees": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", ExtraTreesClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                )),
            ]
        ),
    }
    if include_xgboost:
        if importlib.util.find_spec("xgboost") is None:
            raise ImportError(
                "XGBoost was requested but is not installed. Install it with "
                "'python -m pip install xgboost' and rerun."
            )
        from xgboost import XGBClassifier

        models["xgboost"] = Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", XGBClassifier(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    eval_metric="logloss",
                    tree_method="hist",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                )),
            ]
        )
    return models


def malware_scores(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["model"].classes_)
    malware_index = classes.index("Malware")
    if hasattr(model, "predict_proba"):
        return model.predict_proba(features)[:, malware_index]
    return model.decision_function(features)


def train_and_compare(
    data_path: Path,
    output_dir: Path,
    include_xgboost: bool = False,
    model_dir: Path = Path("models/ransomware"),
    dataset_name: str = "ransomware",
) -> pd.DataFrame:
    if not dataset_name.strip():
        raise ValueError("Dataset name must not be empty.")
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    frame, preparation_stats = load_and_deduplicate(data_path)
    frame = convert_numeric_like_columns(frame)
    columns = feature_columns(frame)
    features = frame[columns]
    target = frame[TARGET]
    train_validation_x, test_x, train_validation_y, test_y = train_test_split(
        features,
        target,
        test_size=0.20,
        stratify=target,
        random_state=RANDOM_STATE,
    )
    train_x, validation_x, train_y, validation_y = train_test_split(
        train_validation_x,
        train_validation_y,
        test_size=0.25,
        stratify=train_validation_y,
        random_state=RANDOM_STATE,
    )

    records = []
    fitted_models = {}
    for name, model in make_models(train_x, include_xgboost).items():
        model.fit(train_x, train_y)
        fitted_models[name] = model
        predictions = model.predict(validation_x)
        scores = malware_scores(model, validation_x)
        records.append(
            {
                "model": name,
                "accuracy": accuracy_score(validation_y, predictions),
                "precision_malware": precision_score(
                    validation_y, predictions, pos_label="Malware", zero_division=0
                ),
                "recall_malware": recall_score(
                    validation_y, predictions, pos_label="Malware", zero_division=0
                ),
                "f1_malware": f1_score(
                    validation_y, predictions, pos_label="Malware", zero_division=0
                ),
                "roc_auc": roc_auc_score(validation_y == "Malware", scores),
                "pr_auc": average_precision_score(validation_y == "Malware", scores),
                "score_type": (
                    "probability"
                    if hasattr(model, "predict_proba")
                    else "decision_function (not calibrated probability)"
                ),
            }
        )

    results = pd.DataFrame(records).sort_values(
        ["recall_malware", "precision_malware", "f1_malware"],
        ascending=False,
    )
    results.to_csv(output_dir / "supervised_model_comparison.csv", index=False)
    winner_name = str(results.iloc[0]["model"])
    model_files = []
    for name, model in fitted_models.items():
        model.fit(train_validation_x, train_validation_y)
        model_path = model_dir / f"{name}.joblib"
        joblib.dump(model, model_path)
        model_files.append(model_path.name)
    winner = fitted_models[winner_name]
    (model_dir / "feature_schema.json").write_text(
        json.dumps(columns, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    test_predictions = winner.predict(test_x)
    test_scores = malware_scores(winner, test_x)
    final_test_metrics = {
        "accuracy": accuracy_score(test_y, test_predictions),
        "precision_malware": precision_score(
            test_y, test_predictions, pos_label="Malware", zero_division=0
        ),
        "recall_malware": recall_score(
            test_y, test_predictions, pos_label="Malware", zero_division=0
        ),
        "f1_malware": f1_score(
            test_y, test_predictions, pos_label="Malware", zero_division=0
        ),
        "roc_auc": roc_auc_score(test_y == "Malware", test_scores),
        "pr_auc": average_precision_score(test_y == "Malware", test_scores),
    }
    report = {
        "dataset": dataset_name,
        "target": TARGET,
        "positive_class": "Malware",
        "split": {
            "method": "stratified train_test_split",
            "test_size": 0.20,
            "validation_size": 0.20,
            "training_size": 0.60,
            "random_state": RANDOM_STATE,
            "train_rows": len(train_x),
            "validation_rows": len(validation_x),
            "test_rows": len(test_x),
        },
        "cleaning": preparation_stats,
        "features": columns,
        "selection_rule": "Highest validation Malware recall, then precision, then F1; the test set is held out until final evaluation.",
        "selected_model": winner_name,
        "deployment_artifacts": {
            "model": f"{winner_name}.joblib",
            "models_directory": str(model_dir),
            "model_files": model_files,
            "feature_schema": "feature_schema.json",
            "fit_data": "train + validation",
        },
        "final_test_metrics": final_test_metrics,
        "regression_scope": (
            "Not trained: this dataset has categorical labels (Class, Category, Family) "
            "and no continuous outcome appropriate for regression."
        ),
        "models": results.to_dict(orient="records"),
    }
    (output_dir / "supervised_learning_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ConfusionMatrixDisplay.from_predictions(
        test_y, test_predictions, labels=["Benign", "Malware"], colorbar=False
    ).figure_.savefig(
        output_dir / "supervised_confusion_matrix.png", dpi=160, bbox_inches="tight"
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare supervised-learning classifiers for malware detection."
    )
    parser.add_argument("--data", type=Path, default=Path("ransom.csv"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument(
        "--model-dir", type=Path, default=Path("models/ransomware")
    )
    parser.add_argument("--dataset-name", default="ransomware")
    parser.add_argument(
        "--include-xgboost",
        action="store_true",
        help="Include XGBoost if installed; it is an optional dependency.",
    )
    args = parser.parse_args()
    results = train_and_compare(
        args.data,
        args.output,
        args.include_xgboost,
        args.model_dir,
        args.dataset_name,
    )
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()

"""Compare supervised classifiers required by the IAAC roadmap."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import (
    AdaBoostClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    average_precision_score,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    learning_curve,
    train_test_split,
)
from sklearn.naive_bayes import BernoulliNB, GaussianNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

if __package__:
    from .data_preprocessing import (
        TARGET,
        Log1pSkewedNonNegative,
        convert_numeric_like_columns,
        feature_columns,
        load_and_deduplicate,
    )
else:
    from data_preprocessing import (
        TARGET,
        Log1pSkewedNonNegative,
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
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("log1p", Log1pSkewedNonNegative()),
                ("scaler", numeric_scaler),
            ]
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
        "multinomial_naive_bayes": Pipeline(
            [
                ("preprocess", preprocessors["bernoulli_sparse"]),
                ("model", MultinomialNB()),
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
    for model in models.values():
        model.steps.insert(1, ("select", SelectKBest(score_func=f_classif, k="all")))
    return models


def malware_scores(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["model"].classes_)
    malware_index = classes.index("Malware")
    if hasattr(model, "predict_proba"):
        return model.predict_proba(features)[:, malware_index]
    return model.decision_function(features)


def parameter_grid(model_name: str, selection_k: int) -> dict[str, list[object]]:
    """Keep the tuning grid small and explicit for reproducible local runs."""
    feature_counts: list[object] = ["all"]
    if selection_k > 0:
        feature_counts.append(selection_k)
    grid: dict[str, list[object]] = {"select__k": feature_counts}
    model_grids: dict[str, dict[str, list[object]]] = {
        "logistic_regression": {"model__C": [0.1, 1.0, 10.0]},
        "decision_tree": {
            "model__max_depth": [10, None],
            "model__min_samples_leaf": [1, 5],
        },
        "knn": {
            "model__n_neighbors": [3, 5, 9],
            "model__weights": ["uniform", "distance"],
        },
        "gaussian_naive_bayes": {
            "model__var_smoothing": [1e-11, 1e-9, 1e-7]
        },
        "bernoulli_naive_bayes": {"model__alpha": [0.1, 1.0, 10.0]},
        "multinomial_naive_bayes": {"model__alpha": [0.1, 1.0, 10.0]},
        "linear_svm": {"model__C": [0.1, 1.0, 10.0]},
        "rbf_svm": {"model__C": [0.1, 1.0]},
        "adaboost": {
            "model__n_estimators": [50, 100],
            "model__learning_rate": [0.5, 1.0],
        },
        "gradient_boosting": {
            "model__n_estimators": [100, 200],
            "model__max_depth": [1, 3],
        },
        "random_forest": {
            "model__n_estimators": [100, 200],
            "model__max_depth": [None, 20],
        },
        "extra_trees": {
            "model__n_estimators": [100, 200],
            "model__max_depth": [None, 20],
        },
        "xgboost": {
            "model__max_depth": [3, 6],
            "model__learning_rate": [0.05, 0.1],
        },
    }
    if model_name not in model_grids:
        raise ValueError(f"No hyperparameter grid defined for {model_name}.")
    grid.update(model_grids[model_name])
    return grid


def train_and_compare(
    data_path: Path,
    output_dir: Path,
    include_xgboost: bool = False,
    model_dir: Path = Path("models/ransomware"),
    dataset_name: str = "ransomware",
    cv_folds: int = 3,
) -> pd.DataFrame:
    if not dataset_name.strip():
        raise ValueError("Dataset name must not be empty.")
    if cv_folds < 2:
        raise ValueError("cv_folds must be at least 2.")
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
        print(f"A treinar {name}...", flush=True)
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
        print(f"Concluído {name}.", flush=True)

    results = pd.DataFrame(records).sort_values(
        ["recall_malware", "precision_malware", "f1_malware"],
        ascending=False,
    )
    results.to_csv(output_dir / "supervised_model_comparison.csv", index=False)
    initial_winner_name = str(results.iloc[0]["model"])
    initial_winner = fitted_models[initial_winner_name]
    print(f"Seleção inicial por validação: {initial_winner_name}.", flush=True)

    preprocessed_train = initial_winner.named_steps["preprocess"].transform(train_x)
    selection_k = min(32, max(0, preprocessed_train.shape[1] - 1))
    cv = StratifiedKFold(
        n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE
    )
    scoring = {
        "recall_malware": make_scorer(
            recall_score, pos_label="Malware", zero_division=0
        ),
        "precision_malware": make_scorer(
            precision_score, pos_label="Malware", zero_division=0
        ),
        "f1_malware": make_scorer(
            f1_score, pos_label="Malware", zero_division=0
        ),
        "roc_auc": "roc_auc",
    }
    print(
        f"A afinar {initial_winner_name} com {cv_folds}-fold CV "
        "no conjunto treino+validação...",
        flush=True,
    )
    search = GridSearchCV(
        estimator=clone(initial_winner),
        param_grid=parameter_grid(initial_winner_name, selection_k),
        scoring=scoring,
        refit="recall_malware",
        cv=cv,
        n_jobs=1,
        return_train_score=True,
        error_score="raise",
    )
    search.fit(train_validation_x, train_validation_y)
    winner_name = initial_winner_name
    tuned_winner = search.best_estimator_
    fitted_models[winner_name] = tuned_winner
    cv_train_recall = float(search.cv_results_["mean_train_recall_malware"][search.best_index_])
    cv_validation_recall = float(search.cv_results_["mean_test_recall_malware"][search.best_index_])
    generalization_gap = cv_train_recall - cv_validation_recall
    if generalization_gap > 0.10:
        fit_diagnostic = "potential_overfitting"
    elif cv_train_recall < 0.70 and cv_validation_recall < 0.70:
        fit_diagnostic = "potential_underfitting"
    else:
        fit_diagnostic = "no_strong_recall_signal_of_underfit_or_overfit"
    cv_results = pd.DataFrame(search.cv_results_)
    cv_results.to_csv(output_dir / "hyperparameter_search.csv", index=False)
    best_cv_metrics = {
        metric: {
            "mean": float(search.cv_results_[f"mean_test_{metric}"][search.best_index_]),
            "std": float(search.cv_results_[f"std_test_{metric}"][search.best_index_]),
        }
        for metric in scoring
    }
    print(
        f"CV concluída: recall médio={cv_validation_recall:.4f}, "
        f"diagnóstico={fit_diagnostic}.",
        flush=True,
    )
    learning_sizes, train_curve, validation_curve = learning_curve(
        estimator=clone(tuned_winner),
        X=train_validation_x,
        y=train_validation_y,
        train_sizes=np.linspace(0.2, 1.0, 5),
        cv=cv,
        scoring=scoring["recall_malware"],
        n_jobs=1,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    learning_curve_frame = pd.DataFrame(
        {
            "training_rows": learning_sizes,
            "train_recall_mean": train_curve.mean(axis=1),
            "train_recall_std": train_curve.std(axis=1),
            "validation_recall_mean": validation_curve.mean(axis=1),
            "validation_recall_std": validation_curve.std(axis=1),
        }
    )
    learning_curve_frame.to_csv(output_dir / "learning_curve.csv", index=False)
    plt.figure(figsize=(8, 5))
    plt.plot(
        learning_sizes,
        learning_curve_frame["train_recall_mean"],
        marker="o",
        label="Treino CV",
    )
    plt.plot(
        learning_sizes,
        learning_curve_frame["validation_recall_mean"],
        marker="o",
        label="Validação CV",
    )
    plt.fill_between(
        learning_sizes,
        learning_curve_frame["validation_recall_mean"]
        - learning_curve_frame["validation_recall_std"],
        learning_curve_frame["validation_recall_mean"]
        + learning_curve_frame["validation_recall_std"],
        alpha=0.18,
    )
    plt.xlabel("Amostras de treino por fold")
    plt.ylabel("Recall de Malware")
    plt.ylim(0, 1.02)
    plt.title(f"Learning curve — {winner_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "learning_curve.png", dpi=160)
    plt.close()

    model_files = []
    for name, model in fitted_models.items():
        print(f"A guardar {name}...", flush=True)
        if name != winner_name:
            model.fit(train_validation_x, train_validation_y)
        model_path = model_dir / f"{name}.joblib"
        joblib.dump(model, model_path)
        model_files.append(model_path.name)
        print(f"Guardado {model_path}.", flush=True)
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
        "model_selection": {
            "initial_validation_winner": initial_winner_name,
            "final_model": winner_name,
            "initial_validation_metrics": results.iloc[0].to_dict(),
            "test_used_for_selection": False,
        },
        "cross_validation": {
            "method": "StratifiedKFold",
            "folds": cv_folds,
            "shuffle": True,
            "random_state": RANDOM_STATE,
            "scope": "train+validation only; test remains held out",
            "best_parameters": search.best_params_,
            "best_validation_metrics": best_cv_metrics,
            "mean_train_recall_malware": cv_train_recall,
            "mean_validation_recall_malware": cv_validation_recall,
            "recall_generalization_gap": generalization_gap,
            "fit_diagnostic": fit_diagnostic,
            "learning_curve": {
                "artifact": "learning_curve.csv",
                "plot": "learning_curve.png",
                "scope": "train+validation only",
                "points": learning_curve_frame.to_dict(orient="records"),
            },
            "diagnostic_rule": (
                "Potential overfitting if train-CV recall minus validation-CV recall > 0.10; "
                "potential underfitting if both recalls < 0.70. These are screening thresholds, "
                "not proof of model capacity."
            ),
            "search_results": "hyperparameter_search.csv",
        },
        "feature_selection": {
            "method": "SelectKBest(f_classif) inside the pipeline",
            "selection_k_candidate": selection_k if selection_k > 0 else "all",
            "fit_scope": "each training fold only",
            "best_k": search.best_params_.get("select__k", "all"),
        },
        "feature_engineering": {
            "method": "log1p for non-negative numeric features with |training skewness| > 1",
            "implementation": "Log1pSkewedNonNegative within each model pipeline",
            "fit_scope": "each training fold only",
        },
        "regularization": {
            "method": "model-specific complexity/regularization parameters searched by CV",
            "best_parameters": {
                key: value
                for key, value in search.best_params_.items()
                if key.endswith("__C")
                or key.endswith("__alpha")
                or key.endswith("__max_depth")
                or key.endswith("__min_samples_leaf")
            },
        },
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
    plt.close("all")
    RocCurveDisplay.from_predictions(
        test_y == "Malware",
        test_scores,
        name=winner_name,
    )
    plt.title(f"ROC — {winner_name}")
    plt.tight_layout()
    plt.savefig(output_dir / "supervised_roc_curve.png", dpi=160)
    plt.close()
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
        "--cv-folds",
        type=int,
        default=3,
        help="Stratified folds used to tune the validation-selected model (default: 3).",
    )
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
        args.cv_folds,
    )
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()

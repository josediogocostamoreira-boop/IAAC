"""Train and evaluate leakage-safe binary ransomware classifiers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    ConfusionMatrixDisplay,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline

from data_preprocessing import TARGET, build_preprocessor, convert_numeric_like_columns, feature_columns, load_and_deduplicate


def make_models(preprocessor):
    return {
        "dummy": Pipeline(
            [("preprocess", preprocessor), ("model", DummyClassifier(strategy="prior"))]
        ),
        "logistic_regression": Pipeline(
            [
                ("preprocess", preprocessor),
                ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocess", preprocessor),
                ("model", RandomForestClassifier(
                    n_estimators=200, class_weight="balanced", n_jobs=-1, random_state=42
                )),
            ]
        ),
        "extra_trees": Pipeline(
            [
                ("preprocess", preprocessor),
                ("model", ExtraTreesClassifier(
                    n_estimators=200, class_weight="balanced", n_jobs=-1, random_state=42
                )),
            ]
        ),
    }


def positive_scores(model, features):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(features)[:, 1]
    return model.decision_function(features)


def evaluate(model, features, target) -> dict[str, float]:
    predictions = model.predict(features)
    scores = positive_scores(model, features)
    return {
        "accuracy": accuracy_score(target, predictions),
        "precision_malware": precision_score(target, predictions, pos_label="Malware", zero_division=0),
        "recall_malware": recall_score(target, predictions, pos_label="Malware", zero_division=0),
        "f1_malware": f1_score(target, predictions, pos_label="Malware", zero_division=0),
        "roc_auc": roc_auc_score(target == "Malware", scores),
        "pr_auc": average_precision_score(target == "Malware", scores),
    }


def train(data_path: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame, preparation_stats = load_and_deduplicate(data_path)
    frame = convert_numeric_like_columns(frame)
    columns = feature_columns(frame)
    features = frame[columns]
    target = frame[TARGET]
    train_x, test_x, train_y, test_y = train_test_split(
        features, target, test_size=0.20, stratify=target, random_state=42
    )
    preprocessor = build_preprocessor(frame, columns)
    models = make_models(preprocessor)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scoring = {
        "accuracy": "accuracy",
        "precision_malware": make_scorer(precision_score, pos_label="Malware", zero_division=0),
        "recall_malware": make_scorer(recall_score, pos_label="Malware", zero_division=0),
        "f1_malware": make_scorer(f1_score, pos_label="Malware", zero_division=0),
        "roc_auc": "roc_auc",
    }
    records = []
    fitted_models = {}
    for name, model in models.items():
        cv_result = cross_validate(model, train_x, train_y, cv=cv, scoring=scoring, n_jobs=1)
        model.fit(train_x, train_y)
        fitted_models[name] = model
        test_metrics = evaluate(model, test_x, test_y)
        record = {"model": name, **test_metrics}
        for metric in scoring:
            record[f"cv_{metric}"] = float(np.mean(cv_result[f"test_{metric}"]))
        records.append(record)

    metrics = pd.DataFrame(records).sort_values("recall_malware", ascending=False)
    best_name = str(metrics.iloc[0]["model"])
    best_model = fitted_models[best_name]
    joblib.dump(best_model, output_dir / "ransomware_classifier.joblib")
    predictions = best_model.predict(test_x)
    ConfusionMatrixDisplay.from_predictions(
        test_y, predictions, labels=["Benign", "Malware"], colorbar=False
    ).figure_.savefig(output_dir / "confusion_matrix.png", dpi=160, bbox_inches="tight")
    classifier = best_model.named_steps["model"]
    if hasattr(classifier, "feature_importances_"):
        names = best_model.named_steps["preprocess"].get_feature_names_out()
        pd.DataFrame(
            {"feature": names, "importance": classifier.feature_importances_}
        ).sort_values("importance", ascending=False).to_csv(
            output_dir / "feature_importance.csv", index=False
        )
    metrics.to_csv(output_dir / "model_metrics.csv", index=False)
    (output_dir / "preparation_stats.json").write_text(
        json.dumps(
            {**preparation_stats, "feature_count": len(columns), "selected_model": best_name},
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "feature_schema.json").write_text(json.dumps(columns, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("ransom.csv"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    print(train(args.data, args.output).to_string(index=False))


if __name__ == "__main__":
    main()

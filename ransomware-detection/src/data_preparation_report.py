"""Reproducible Sprint 2 data-preparation audit.

The report is deliberately separate from model training: it measures cleaning,
missing values, outliers, feature redundancy and class balance without silently
dropping suspicious observations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from data_preprocessing import (
    TARGET,
    convert_numeric_like_columns,
    feature_columns,
    load_and_deduplicate,
)


def outlier_summary(frame: pd.DataFrame, numeric_columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in numeric_columns:
        series = frame[column].dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        rows.append(
            {
                "feature": column,
                "missing": int(frame[column].isna().sum()),
                "unique": int(frame[column].nunique()),
                "q1": float(q1),
                "q3": float(q3),
                "lower_bound": float(lower),
                "upper_bound": float(upper),
                "outliers_iqr": int(((series < lower) | (series > upper)).sum()),
                "skewness": float(series.skew()),
            }
        )
    return pd.DataFrame(rows).sort_values("outliers_iqr", ascending=False)


def correlated_pairs(frame: pd.DataFrame, numeric_columns: list[str], threshold: float) -> pd.DataFrame:
    correlation = frame[numeric_columns].corr(method="spearman").abs()
    upper = correlation.where(np.triu(np.ones(correlation.shape), k=1).astype(bool))
    pairs = upper.stack().reset_index()
    pairs.columns = ["feature_1", "feature_2", "abs_spearman"]
    return pairs[pairs["abs_spearman"] >= threshold].sort_values(
        "abs_spearman", ascending=False
    )


def engineered_feature_candidates(frame: pd.DataFrame, numeric_columns: list[str]) -> list[str]:
    """Identify non-negative, strongly skewed features suitable for log1p."""
    candidates = []
    for column in numeric_columns:
        series = frame[column].dropna()
        if not series.empty and series.min() >= 0 and abs(series.skew()) > 1:
            candidates.append(column)
    return candidates


def build_report(data_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned, cleaning = load_and_deduplicate(data_path)
    cleaned = convert_numeric_like_columns(cleaned)
    columns = feature_columns(cleaned)
    features = cleaned[columns]
    target = cleaned[TARGET]
    train_x, test_x, train_y, test_y = train_test_split(
        features, target, test_size=0.20, stratify=target, random_state=42
    )
    numeric = train_x.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [column for column in train_x.columns if column not in numeric]
    quality = outlier_summary(train_x, numeric)
    quality.to_csv(output_dir / "feature_quality.csv", index=False)
    pairs = correlated_pairs(train_x, numeric, threshold=0.95)
    pairs.to_csv(output_dir / "high_correlation_pairs.csv", index=False)

    constant = [column for column in numeric if train_x[column].nunique(dropna=True) <= 1]
    correlated_to_drop = sorted(set(pairs["feature_2"])) if not pairs.empty else []
    selected_numeric = [
        column for column in numeric if column not in constant and column not in correlated_to_drop
    ]
    report = {
        "source": str(data_path),
        "cleaning": cleaning,
        "split": {
            "random_state": 42,
            "test_size": 0.20,
            "train_rows": len(train_x),
            "test_rows": len(test_x),
            "train_class_counts": train_y.value_counts().to_dict(),
            "test_class_counts": test_y.value_counts().to_dict(),
            "shared_md5_after_cleaning": 0,
        },
        "missing_values": {
            "total_before_pipeline": int(features.isna().sum().sum()),
            "numeric_columns": numeric,
            "categorical_columns": categorical,
            "imputation": {
                "numeric": "median fitted on training data",
                "categorical": "most_frequent fitted on training data",
            },
        },
        "outliers": {
            "method": "IQR (1.5 x IQR)",
            "numeric_features_with_outliers": int((quality["outliers_iqr"] > 0).sum()),
            "action": "report only; no automatic deletion",
        },
        "feature_selection": {
            "input_feature_count": len(columns),
            "constant_numeric_features": constant,
            "high_correlation_features_to_review": correlated_to_drop,
            "high_correlation_threshold": 0.95,
            "high_correlation_pair_count": len(pairs),
            "selected_numeric_feature_count": len(selected_numeric),
            "selection_fit_scope": "training split only",
        },
        "feature_scaling": {
            "method": "StandardScaler",
            "fit_scope": "training split only",
            "implemented_in": "src/data_preprocessing.py",
        },
        "feature_engineering": {
            "log1p_candidates": engineered_feature_candidates(train_x, numeric),
            "rule": "non-negative numeric features with absolute skewness > 1",
            "status": "candidates reported; not applied without validation",
        },
        "feature_extraction": {
            "available_features": len(columns),
            "source": "PE metadata and observed behavior columns in ransom.csv",
            "limitation": "automatic extraction from a raw .exe is not implemented",
        },
        "imbalance": {
            "class_counts": target.value_counts().to_dict(),
            "minority_to_majority_ratio": float(target.value_counts().min() / target.value_counts().max()),
            "strategy": "stratified split and class_weight='balanced' in supervised baselines",
        },
    }
    (output_dir / "data_preparation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Sprint 2 data-preparation report.")
    parser.add_argument("--data", type=Path, default=Path("ransom.csv"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    report = build_report(args.data, args.output)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

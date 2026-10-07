"""Data loading and leakage-safe preprocessing for the ransomware dataset."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import skew
from sklearn.base import BaseEstimator, TransformerMixin

TARGET = "Class"
IDENTIFIERS = {"md5", "sha1"}
FUTURE_TARGETS = {"Category", "Family"}
EXPECTED_CLASSES = {"Benign", "Malware"}


class Log1pSkewedNonNegative(BaseEstimator, TransformerMixin):
    """Apply log1p only to skewed non-negative numeric columns learned in fit."""

    def __init__(self, skew_threshold: float = 1.0) -> None:
        self.skew_threshold = skew_threshold

    def fit(self, X, _y=None):
        values = np.asarray(X, dtype=float)
        if values.ndim != 2:
            raise ValueError("Expected a 2D numeric feature matrix.")
        self.n_features_in_ = values.shape[1]
        self.log_mask_ = np.zeros(self.n_features_in_, dtype=bool)
        for index in range(self.n_features_in_):
            column = values[:, index]
            finite = column[np.isfinite(column)]
            if finite.size > 2 and finite.min() >= 0:
                column_skew = float(skew(finite, bias=False))
                self.log_mask_[index] = (
                    np.isfinite(column_skew)
                    and abs(column_skew) > self.skew_threshold
                )
        return self

    def transform(self, X):
        values = np.asarray(X, dtype=float).copy()
        if values.ndim != 2 or values.shape[1] != self.n_features_in_:
            raise ValueError("Feature matrix does not match the fitted schema.")
        values[:, self.log_mask_] = np.log1p(values[:, self.log_mask_])
        return values

    def get_feature_names_out(self, input_features=None):
        if input_features is None:
            return np.asarray(
                [f"x{index}" for index in range(self.n_features_in_)], dtype=object
            )
        return np.asarray(input_features, dtype=object)


def parse_numeric_value(value: object) -> float:
    """Parse decimal/hex values while returning NaN for descriptive text."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    match = re.search(r"0x[0-9a-fA-F]+", text)
    if match:
        return float(int(match.group(0), 16))
    try:
        return float(text)
    except ValueError:
        return np.nan


def convert_numeric_like_columns(frame: pd.DataFrame, threshold: float = 0.90) -> pd.DataFrame:
    """Convert object columns only when most values are numeric or hexadecimal."""
    result = frame.copy()
    for column in result.select_dtypes(include=["object", "string"]).columns:
        parsed = result[column].map(parse_numeric_value)
        if parsed.notna().mean() >= threshold:
            result[column] = parsed
    return result


def load_and_deduplicate(path: str | Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load data, remove conflicting hashes, and keep one row per MD5."""
    frame = pd.read_csv(path, encoding="utf-8-sig")
    required = IDENTIFIERS | {TARGET}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    frame[TARGET] = frame[TARGET].astype("string").str.strip()
    invalid_labels = sorted(set(frame[TARGET].dropna()) - EXPECTED_CLASSES)
    if invalid_labels:
        raise ValueError(f"Unexpected Class labels: {invalid_labels}")

    before = len(frame)
    missing_required = int(frame[["md5", TARGET]].isna().any(axis=1).sum())
    frame = frame.dropna(subset=["md5", TARGET]).copy()
    conflict_mask = frame.groupby("md5")[TARGET].transform("nunique") > 1
    conflicting_rows = int(conflict_mask.sum())
    frame = frame.loc[~conflict_mask].drop_duplicates("md5", keep="first")
    stats = {
        "rows_before": before,
        "rows_after": len(frame),
        "rows_missing_required": missing_required,
        "conflicting_rows_removed": conflicting_rows,
        "unique_md5": int(frame["md5"].nunique()),
    }
    return frame, stats


def feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return model features without identifiers or target leakage columns."""
    excluded = IDENTIFIERS | {TARGET} | FUTURE_TARGETS
    return [column for column in frame.columns if column not in excluded]


def build_preprocessor(frame: pd.DataFrame, columns: Iterable[str]):
    """Build a ColumnTransformer; fitting is deliberately left to the caller."""
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    selected = frame[list(columns)]
    numeric = selected.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [column for column in selected.columns if column not in numeric]
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("log1p", Log1pSkewedNonNegative()),
            ("scale", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric_pipeline, numeric), ("categorical", categorical_pipeline, categorical)],
        remainder="drop",
    )

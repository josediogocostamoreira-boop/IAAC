"""Preparação reproduzível de dados para deteção de intrusão.

As transformações que aprendem parâmetros são ajustadas apenas no treino, para
evitar data leakage entre os conjuntos de treino e teste.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
TARGET_COLUMN = "attack_detected"
IDENTIFIER_COLUMNS = ("session_id",)


class IQRCapper(BaseEstimator, TransformerMixin):
    """Limita outliers aos limites IQR aprendidos no treino, por coluna."""

    def __init__(self, factor: float = 1.5):
        self.factor = factor

    def fit(self, X, y=None):
        values = np.asarray(X, dtype=float)
        q1, q3 = np.nanpercentile(values, [25, 75], axis=0)
        iqr = q3 - q1
        self.lower_ = q1 - self.factor * iqr
        self.upper_ = q3 + self.factor * iqr
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.lower_, self.upper_)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features, dtype=object)


def _engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Cria atributos interpretáveis sem usar a variável alvo."""
    data = frame.copy()
    if {"failed_logins", "login_attempts"}.issubset(data.columns):
        data["failed_login_ratio"] = data["failed_logins"] / (data["login_attempts"] + 1)
    if {"network_packet_size", "session_duration"}.issubset(data.columns):
        data["packet_rate"] = data["network_packet_size"] / (data["session_duration"] + 1)
    if "ip_reputation_score" in data.columns:
        data["ip_reputation_risk"] = 1 - data["ip_reputation_score"].clip(0, 1)
    return data


def _make_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric = X.select_dtypes(include=np.number).columns.tolist()
    categorical = X.select_dtypes(exclude=np.number).columns.tolist()
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("outlier_capping", IQRCapper()),
        ("scaler", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, categorical),
    ], remainder="drop", verbose_feature_names_out=False)


@dataclass
class PreparedData:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: pd.Series
    y_test: pd.Series
    preprocessor: ColumnTransformer
    feature_names: list[str]
    metadata: dict

    def as_dict(self) -> dict:
        return self.__dict__


def load_and_preprocess_data(csv_path="data/cybersecurity_intrusion_data.csv",
                             save_path="models/processed_data.pkl",
                             test_size: float = 0.20) -> PreparedData:
    """Lê, valida, divide estratificadamente e transforma o dataset."""
    df = pd.read_csv(csv_path)
    target = TARGET_COLUMN if TARGET_COLUMN in df.columns else df.columns[-1]
    if df[target].nunique(dropna=True) != 2:
        raise ValueError(f"O alvo '{target}' deve ser binário para esta pipeline.")

    X = df.drop(columns=[target]).drop(columns=list(IDENTIFIER_COLUMNS), errors="ignore")
    X = _engineer_features(X)
    y = df[target].astype(int)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE
    )
    preprocessor = _make_preprocessor(X_train_raw)
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    prepared = PreparedData(
        X_train=X_train, X_test=X_test, y_train=y_train.reset_index(drop=True),
        y_test=y_test.reset_index(drop=True), preprocessor=preprocessor,
        feature_names=preprocessor.get_feature_names_out().tolist(),
        metadata={"target": target, "raw_features": X.columns.tolist(), "rows": len(df),
                  "test_size": test_size, "random_state": RANDOM_STATE},
    )
    destination = Path(save_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        pickle.dump(prepared.as_dict(), handle)
    return prepared


def load_prepared_data(path="models/processed_data.pkl") -> PreparedData:
    with open(path, "rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Artefacto antigo detetado; execute novamente a preparação.")
    return PreparedData(**payload)

"""Avaliação, seleção e otimização de classificadores."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from .data_prep import PreparedData

def _probabilities(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return 1 / (1 + np.exp(-model.decision_function(X)))

def evaluate_all_models(models, data: PreparedData):
    """Calcula métricas de teste e F1 com validação cruzada estratificada (5 folds)."""
    cv, rows, matrices = StratifiedKFold(5, shuffle=True, random_state=42), [], {}
    for name, model in models.items():
        predicted, probability = model.predict(data.X_test), _probabilities(model, data.X_test)
        f1_train, f1_test = f1_score(data.y_train, model.predict(data.X_train)), f1_score(data.y_test, predicted)
        # O preprocessor é ajustado em cada fold: não há leakage do fold de validação.
        cv_pipeline = Pipeline([("preprocessor", clone(data.preprocessor)), ("model", clone(model))])
        scores = cross_val_score(cv_pipeline, data.X_train_raw, data.y_train, cv=cv, scoring="f1", n_jobs=1)
        gap = f1_train - f1_test
        rows.append({"model": name, "accuracy": accuracy_score(data.y_test, predicted), "precision": precision_score(data.y_test, predicted, zero_division=0), "recall": recall_score(data.y_test, predicted, zero_division=0), "f1_test": f1_test, "f1_cv_mean": scores.mean(), "f1_cv_std": scores.std(), "roc_auc": roc_auc_score(data.y_test, probability), "f1_train": f1_train, "generalization_gap": gap, "diagnosis": "overfitting" if gap > .10 else ("underfitting" if f1_test < .60 else "balanced")})
        matrices[name] = confusion_matrix(data.y_test, predicted).tolist()
    results = pd.DataFrame(rows).sort_values(["f1_cv_mean", "f1_test"], ascending=False).reset_index(drop=True)
    return results, results.iloc[0]["model"], matrices

def tune_random_forest(data: PreparedData):
    """Otimiza o Random Forest sem ajustar o pré-processador nos folds de validação."""
    pipeline = Pipeline([
        ("preprocessor", clone(data.preprocessor)),
        ("model", RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1)),
    ])
    parameters = {
        "model__n_estimators": [150, 250],
        "model__max_depth": [8, 12, None],
        "model__min_samples_leaf": [1, 3, 5],
    }
    grid = GridSearchCV(
        pipeline,
        parameters,
        cv=StratifiedKFold(3, shuffle=True, random_state=42),
        scoring="f1",
        n_jobs=-1,
    )
    return grid.fit(data.X_train_raw, data.y_train)

"""Avaliação, seleção e otimização de classificadores."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
try:  # suporta execução como módulo e a partir dos notebooks
    from .data_prep import load_prepared_data
    from .train import load_models
except ImportError:
    from data_prep import load_prepared_data
    from train import load_models

def _probabilities(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return 1 / (1 + np.exp(-model.decision_function(X)))

def evaluate_all_models(models_path="models/trained_models.pkl", data_path="models/processed_data.pkl", results_path="models/model_metrics.csv"):
    """Calcula métricas de teste e F1 com validação cruzada estratificada (5 folds)."""
    data, models = load_prepared_data(data_path), load_models(models_path)
    cv, rows, matrices = StratifiedKFold(5, shuffle=True, random_state=42), [], {}
    for name, model in models.items():
        predicted, probability = model.predict(data.X_test), _probabilities(model, data.X_test)
        f1_train, f1_test = f1_score(data.y_train, model.predict(data.X_train)), f1_score(data.y_test, predicted)
        # Execução sequencial: evita processos órfãos em ambientes Windows/notebooks.
        scores = cross_val_score(clone(model), data.X_train, data.y_train, cv=cv, scoring="f1", n_jobs=1)
        gap = f1_train - f1_test
        rows.append({"model": name, "accuracy": accuracy_score(data.y_test, predicted), "precision": precision_score(data.y_test, predicted, zero_division=0), "recall": recall_score(data.y_test, predicted, zero_division=0), "f1_test": f1_test, "f1_cv_mean": scores.mean(), "f1_cv_std": scores.std(), "roc_auc": roc_auc_score(data.y_test, probability), "f1_train": f1_train, "generalization_gap": gap, "diagnosis": "overfitting" if gap > .10 else ("underfitting" if f1_test < .60 else "balanced")})
        matrices[name] = confusion_matrix(data.y_test, predicted).tolist()
    results = pd.DataFrame(rows).sort_values(["f1_cv_mean", "f1_test"], ascending=False).reset_index(drop=True)
    destination = Path(results_path); destination.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(destination, index=False)
    destination.with_suffix(".json").write_text(json.dumps({"selection_metric": "mean F1 in stratified 5-fold CV", "best_model": results.iloc[0]["model"], "confusion_matrices": matrices}, indent=2), encoding="utf-8")
    return results, results.iloc[0]["model"], matrices

def tune_random_forest(X_train, y_train):
    """GridSearchCV pequeno e reproduzível, otimizado para F1."""
    grid = GridSearchCV(RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1), {"n_estimators": [150, 250], "max_depth": [8, 12, None], "min_samples_leaf": [1, 3, 5]}, cv=StratifiedKFold(3, shuffle=True, random_state=42), scoring="f1", n_jobs=-1)
    return grid.fit(X_train, y_train)

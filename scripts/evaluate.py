import os
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier

def evaluate_all_models(models_path='../models/trained_models.pkl', data_path='../models/processed_data.pkl'):
    """
    Avaliação avançada: Métricas de Teste, Cross-Validation e Deteção de Overfitting.
    """
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
        X_train_prep, X_test_prep, y_train, y_test = data[0], data[1], data[2], data[3]
        
    with open(models_path, 'rb') as f:
        trained_models = pickle.load(f)
        
    results = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for name, model in trained_models.items():
        # Previsões no conjunto de Teste
        y_pred_test = model.predict(X_test_prep)
        y_prob_test = model.predict_proba(X_test_prep)[:, 1] if hasattr(model, "predict_proba") else [0]*len(y_pred_test)
        
        # Previsões no conjunto de Treino (para avaliar Overfitting)
        y_pred_train = model.predict(X_train_prep)
        f1_train = f1_score(y_train, y_pred_train, zero_division=0)
        f1_test = f1_score(y_test, y_pred_test, zero_division=0)
        
        # Validação Cruzada (Cross-Validation F1-Score)
        cv_scores = cross_val_score(model, X_train_prep, y_train, cv=cv, scoring='f1')
        
        # Diagnóstico de Overfitting/Underfitting
        gap = f1_train - f1_test
        status = "Overfitting" if gap > 0.10 else ("Underfitting" if f1_test < 0.60 else "Balanceado")
        
        results.append({
            'Modelo': name,
            'Accuracy': round(accuracy_score(y_test, y_pred_test), 4),
            'Precision': round(precision_score(y_test, y_pred_test, zero_division=0), 4),
            'Recall': round(recall_score(y_test, y_pred_test, zero_division=0), 4),
            'F1-Test': round(f1_test, 4),
            'F1-CV (5-Fold)': round(cv_scores.mean(), 4),
            'ROC-AUC': round(roc_auc_score(y_test, y_prob_test), 4),
            'Diagnóstico': status
        })
        
    results_df = pd.DataFrame(results).sort_values(by='F1-Test', ascending=False)
    return results_df, X_train_prep, X_test_prep, y_train, y_test

def tune_random_forest(X_train_prep, y_train, X_test_prep, y_test):
    """
    GridSearchCV com Cross-Validation para Hyperparameter Tuning.
    """
    param_grid = {
        'n_estimators': [50, 100, 150],
        'max_depth': [6, 8, 12],
        'min_samples_split': [2, 5]
    }
    
    grid = GridSearchCV(
        RandomForestClassifier(class_weight='balanced', random_state=42),
        param_grid, cv=3, scoring='f1', n_jobs=-1
    )
    grid.fit(X_train_prep, y_train)
    
    return grid.best_params_, grid.best_score_, grid.best_estimator_
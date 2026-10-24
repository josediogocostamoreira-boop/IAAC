"""Treino dos classificadores definidos no roadmap."""
from __future__ import annotations

import pickle
from pathlib import Path

from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import BernoulliNB, GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

RANDOM_STATE = 42


def build_classifiers():
    """Modelos de classificação abordados no módulo de aprendizagem supervisionada."""
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, class_weight="balanced", random_state=RANDOM_STATE),
        "k-NN": KNeighborsClassifier(n_neighbors=11),
        "Gaussian Naive Bayes": GaussianNB(),
        "Bernoulli Naive Bayes": BernoulliNB(),
        "SVM (RBF)": SVC(kernel="rbf", C=1.0, class_weight="balanced", probability=False, random_state=RANDOM_STATE),
        "SVM (Polynomial)": SVC(kernel="poly", degree=3, class_weight="balanced", probability=False, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=250, max_depth=12, min_samples_leaf=3, class_weight="balanced", n_jobs=-1, random_state=RANDOM_STATE),
        "AdaBoost": AdaBoostClassifier(n_estimators=150, learning_rate=0.7, random_state=RANDOM_STATE),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=3, random_state=RANDOM_STATE),
    }
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(n_estimators=75, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, eval_metric="logloss", random_state=RANDOM_STATE)
    except ImportError:
        pass
    return models


def train_all_classifiers(X_train, y_train, save_path="models/trained_models.pkl"):
    trained = {}
    for name, model in build_classifiers().items():
        print(f"  -> A treinar {name}...")
        trained[name] = model.fit(X_train, y_train)
    destination = Path(save_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        pickle.dump({"models": trained}, handle)
    return trained


def load_models(path="models/trained_models.pkl"):
    with open(path, "rb") as handle:
        payload = pickle.load(handle)
    return payload["models"] if isinstance(payload, dict) and "models" in payload else payload

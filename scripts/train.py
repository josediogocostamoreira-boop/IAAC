import os
import pickle
import warnings
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from xgboost import XGBClassifier

warnings.filterwarnings('ignore')

def train_all_classifiers(X_train, y_train, save_path='../models/trained_models.pkl'):
    """
    Treina todos os modelos do Roadmap (incluindo variantes e XGBoost).
    """
    models = {
        'Logistic Regression': LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42),
        'Decision Tree': DecisionTreeClassifier(class_weight='balanced', max_depth=6, random_state=42),
        'k-NN': KNeighborsClassifier(n_neighbors=5),
        'Gaussian Naïve Bayes': GaussianNB(),
        'Bernoulli Naïve Bayes': BernoulliNB(),
        'SVM (RBF Kernel)': SVC(kernel='rbf', class_weight='balanced', probability=True, random_state=42),
        'SVM (Poly Kernel)': SVC(kernel='poly', degree=3, class_weight='balanced', probability=True, random_state=42),
        'Random Forest': RandomForestClassifier(class_weight='balanced', n_estimators=100, max_depth=8, random_state=42),
        'AdaBoost': AdaBoostClassifier(n_estimators=50, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'XGBoost': XGBClassifier(n_estimators=100, eval_metric='logloss', random_state=42)
    }
    
    trained_models = {}
    for name, model in models.items():
        print(f"  -> A treinar {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model
        
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        pickle.dump(trained_models, f)
        
    return trained_models
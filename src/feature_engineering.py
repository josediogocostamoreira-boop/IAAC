import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
import json

if __package__:
    from .project_paths import DEFAULT_DATASET_PATH, PROJECT_ROOT, validate_dataset_path
else:
    from project_paths import DEFAULT_DATASET_PATH, PROJECT_ROOT, validate_dataset_path


def select_features(path, n_samples=100000, top_k=20, target_col='Label'):
    df = pd.read_csv(validate_dataset_path(path))
    if 'label' in df.columns and 'Label' not in df.columns:
        df = df.rename(columns={'label':'Label'})
    if len(df) > n_samples:
        df = df.sample(n=n_samples, random_state=42)
    X = df.drop(columns=[target_col])
    y = df[target_col]
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = X[col].astype('category').cat.codes
    # quick RF to estimate importances
    rf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    rf.fit(X, y)
    importances = rf.feature_importances_
    feat_imp = pd.Series(importances, index=X.columns).sort_values(ascending=False)
    selected = feat_imp.head(top_k).index.tolist()
    return selected, feat_imp


def train_with_selected(path, selected_features, n_samples=200000, target_col='Label', out_dir='models'):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(validate_dataset_path(path))
    if 'label' in df.columns and 'Label' not in df.columns:
        df = df.rename(columns={'label':'Label'})
    if len(df) > n_samples:
        df = df.sample(n=n_samples, random_state=42)
    X = df[selected_features]
    y = df['Label']
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = X[col].astype('category').cat.codes
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    rf = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42)
    rf.fit(X_train_s, y_train)
    preds = rf.predict(X_test_s)
    report = classification_report(y_test, preds, output_dict=True)
    joblib.dump(rf, os.path.join(out_dir, 'rf_selected.joblib'))
    joblib.dump(scaler, os.path.join(out_dir, 'rf_selected_scaler.joblib'))
    pd.DataFrame(report).to_csv(os.path.join(out_dir, 'rf_selected_report.csv'))
    return report


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATASET_PATH
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    selected, feat_imp = select_features(path, n_samples=100000, top_k=top_k)
    model_dir = PROJECT_ROOT / 'models'
    os.makedirs(model_dir, exist_ok=True)
    with open(model_dir / 'selected_features.json', 'w', encoding='utf-8') as f:
        json.dump(selected, f, indent=2)
    feat_imp.to_csv(model_dir / 'feature_importances.csv')
    print('Selected features:', selected)
    report = train_with_selected(path, selected, n_samples=200000, out_dir=model_dir)
    print(f'Training report saved to {model_dir / "rf_selected_report.csv"}')

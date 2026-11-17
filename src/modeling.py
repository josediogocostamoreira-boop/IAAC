import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

if __package__:
    from .project_paths import DEFAULT_DATASET_PATH, PROJECT_ROOT, validate_dataset_path
else:
    from project_paths import DEFAULT_DATASET_PATH, PROJECT_ROOT, validate_dataset_path


def load_and_sample(path, n_samples=100000, random_state=42):
    df = pd.read_csv(validate_dataset_path(path))
    if n_samples and len(df) > n_samples:
        df = df.sample(n=n_samples, random_state=random_state)
    return df


def prepare_features(df, target_col='Label'):
    # Ensure consistent column name
    if 'Label' not in df.columns and 'label' in df.columns:
        df = df.rename(columns={'label':'Label'})
    X = df.drop(columns=[target_col])
    y = df[target_col]
    # Simple encoder for any object types
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = X[col].astype('category').cat.codes
    return X, y


def train_rf(X_train, y_train):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    model.fit(X_train_scaled, y_train)
    return model, scaler


def format_classification_report(report):
    lines = [f"Accuracy: {report['accuracy'] * 100:.2f}%"]
    lines.append(f"{'':>12} {'precision':>10} {'recall':>10} {'f1-score':>10} {'support':>9}")
    for label, metrics in report.items():
        if isinstance(metrics, dict):
            lines.append(
                f"{label:>12} {metrics['precision'] * 100:>9.2f}% "
                f"{metrics['recall'] * 100:>9.2f}% "
                f"{metrics['f1-score'] * 100:>9.2f}% "
                f"{metrics['support']:>9.0f}"
            )
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATASET_PATH
    out_dir = sys.argv[2] if len(sys.argv) > 2 else PROJECT_ROOT / 'models'
    os.makedirs(out_dir, exist_ok=True)
    df = load_and_sample(path, n_samples=100000)
    X, y = prepare_features(df, target_col='Label')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model, scaler = train_rf(X_train, y_train)
    # evaluate
    X_test_scaled = scaler.transform(X_test)
    preds = model.predict(X_test_scaled)
    report = classification_report(y_test, preds, output_dict=True)
    print('Classification report (percentages):')
    print(format_classification_report(report))
    joblib.dump(model, os.path.join(out_dir, 'rf_model.joblib'))
    joblib.dump(scaler, os.path.join(out_dir, 'scaler.joblib'))
    pd.DataFrame(report).to_csv(os.path.join(out_dir, 'rf_report.csv'))
    print('Model and artifacts saved to', out_dir)

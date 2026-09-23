import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_data(path):
    df = pd.read_csv(path)
    return df


def basic_clean(df):
    # drop duplicates
    df = df.drop_duplicates()
    # drop columns with all nulls
    df = df.dropna(axis=1, how='all')
    return df


def handle_missing(df, strategy='mean'):
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isna().sum() > 0:
            if strategy == 'mean':
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == 'median':
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(0)
    return df


def scale_features(X_train, X_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler


def split_data(df, target_col='label', test_size=0.2, random_state=42):
    X = df.drop(columns=[target_col])
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    return X_train, X_test, y_train, y_test


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '../archive/final_dataset.csv'
    df = load_data(path)
    df = basic_clean(df)
    df = handle_missing(df)
    X_train, X_test, y_train, y_test = split_data(df)
    X_train, X_test, scaler = scale_features(X_train, X_test)
    print('Done')

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.decomposition import PCA

def load_and_preprocess_data(csv_path='../data/cybersecurity_intrusion_data.csv', save_path='../models/processed_data.pkl'):
    """
    Pré-processamento completo: Limpeza, Feature Engineering, Feature Selection e Scaling.
    """
    df = pd.read_csv(csv_path)
    
    # Separar Features e Target
    target_col = 'Network_Intrusion_Detected' if 'Network_Intrusion_Detected' in df.columns else df.columns[-1]
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 1. Feature Engineering (Criação de novos atributos)
    num_cols = X.select_dtypes(include=[np.number]).columns
    if len(num_cols) >= 2:
        X['Feature_Ratio_1_2'] = X[num_cols[0]] / (X[num_cols[1]] + 1e-5)
        X['Feature_Sum_1_2'] = X[num_cols[0]] + X[num_cols[1]]
    
    # Tratar variáveis categóricas se existirem
    X = pd.get_dummies(X, drop_first=True)
    
    # 2. Imputação de Valores Omissos
    imputer = SimpleImputer(strategy='median')
    X_imputed = imputer.fit_transform(X)
    
    # 3. Divisão Treino / Teste
    X_train, X_test, y_train, y_test = train_test_split(X_imputed, y, test_size=0.2, random_state=42, stratify=y)
    
    # 4. Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 5. Feature Selection (Manter as melhores k features)
    k_features = min(15, X_train_scaled.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k_features)
    X_train_selected = selector.fit_transform(X_train_scaled, y_train)
    X_test_selected = selector.transform(X_test_scaled)
    
    # 6. Feature Extraction (PCA para redução de dimensionalidade)
    pca = PCA(n_components=0.95, random_state=42) # Mantém 95% da variância
    X_train_pca = pca.fit_transform(X_train_selected)
    X_test_pca = pca.transform(X_test_selected)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        pickle.dump((X_train_selected, X_test_selected, y_train, y_test, scaler, selector, pca), f)
        
    return X_train_selected, X_test_selected, y_train, y_test, scaler
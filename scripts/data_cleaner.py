import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def carregar_e_limpar_dados(caminho_csv):
    df = pd.read_csv(caminho_csv)
    if 'session_id' in df.columns:
        df = df.drop(columns=['session_id'])
    df['encryption_used'] = df['encryption_used'].fillna('Desconhecido')
    return df

def preparar_dados_para_treino(df, target_col='attack_detected', test_size=0.2, random_state=42):
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    colunas_texto = X.select_dtypes(include=['object']).columns
    colunas_numericas = X.select_dtypes(exclude=['object']).columns
    
    X = pd.get_dummies(X, columns=colunas_texto, drop_first=True)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    scaler = StandardScaler()
    X_train[colunas_numericas] = scaler.fit_transform(X_train[colunas_numericas])
    X_test[colunas_numericas] = scaler.transform(X_test[colunas_numericas])
    
    return X_train, X_test, y_train, y_test, scaler
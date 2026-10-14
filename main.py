import sys
import os
sys.path.append('scripts')

from data_prep import load_and_preprocess_data
from train import train_all_classifiers
from evaluate import evaluate_all_models, tune_random_forest
from agent import CybersecurityReportingAgent

def main():
    print("==================================================")
    print(" PIPELINE COMPLETA DE DETEÇÃO DE INTRUSÃO (CRISP-ML)")
    print("==================================================\n")
    
    # 1. Preparação dos Dados
    print("[1/4] A executar Pré-processamento de Dados...")
    X_train_prep, X_test_prep, y_train, y_test, preprocessor = load_and_preprocess_data(
        csv_path='data/cybersecurity_intrusion_data.csv',
        save_path='models/processed_data.pkl'
    )
    
    # 2. Treino de Modelos
    print("[2/4] A treinar Classificadores...")
    trained_models = train_all_classifiers(
        X_train_prep, y_train, save_path='models/trained_models.pkl'
    )
    
    # 3. Avaliação e Otimização
    print("[3/4] A avaliar Modelos...")
    results_df, _, _, _, _ = evaluate_all_models(
        models_path='models/trained_models.pkl',
        data_path='models/processed_data.pkl'
    )
    print("\nResultados dos Modelos:")
    print(results_df.to_string(index=False))
    
    # 4. Agente Generativo de Cibersegurança
    print("\n[4/4] A executar Agente Generativo de Cibersegurança...")
    agent = CybersecurityReportingAgent(model_path='models/trained_models.pkl')
    
    # Testar com uma amostra de teste
    sample_data = X_test_prep[0:1]
    relatorio = agent.analyze_session_and_generate_report(sample_data)
    print(relatorio)

if __name__ == '__main__':
    main()
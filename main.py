"""Ponto de entrada da pipeline CRISP-ML de deteção de intrusão."""
from scripts.agent import CybersecurityReportingAgent
from scripts.data_prep import load_and_preprocess_data
from scripts.evaluate import evaluate_all_models
from scripts.train import train_all_classifiers

def main():
    print("=== PIPELINE CRISP-ML | DETEÇÃO DE INTRUSÕES ===")
    print("[1/4] Preparação: split, imputação, IQR, encoding e scaling")
    prepared = load_and_preprocess_data()
    print("[2/4] Treino dos classificadores")
    train_all_classifiers(prepared.X_train, prepared.y_train)
    print("[3/4] Avaliação e seleção por F1 em CV estratificada")
    results, best_model, _ = evaluate_all_models()
    print(results.to_string(index=False)); print(f"\nModelo selecionado: {best_model}")
    print("[4/4] Demonstração do sistema multiagente")
    print(CybersecurityReportingAgent(model_name=best_model).analyze_session_and_generate_report(prepared.X_test[:1]))

if __name__ == "__main__":
    main()

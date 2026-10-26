"""Ponto de entrada da pipeline de classificação de intrusões."""
from scripts.data_prep import load_and_preprocess_data
from scripts.evaluate import evaluate_all_models
from scripts.train import train_all_classifiers

def main():
    print("=== CLASSIFICAÇÃO DE INTRUSÕES ===")
    print("[1/3] Preparação dos dados")
    prepared = load_and_preprocess_data()
    print("[2/3] Treino dos classificadores")
    models = train_all_classifiers(prepared.X_train, prepared.y_train)
    print("[3/3] Avaliação e seleção por F1 em validação cruzada")
    results, best_model, _ = evaluate_all_models(models, prepared)
    print(results.to_string(index=False))
    print(f"\nModelo selecionado: {best_model}")

if __name__ == "__main__":
    main()

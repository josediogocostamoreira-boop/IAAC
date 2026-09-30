"""Avalia de forma reproduzível o modelo guardado no conjunto de teste."""

from __future__ import annotations

import argparse
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from agent_system import AgenteAnalista
from data_cleaner import carregar_e_limpar_dados, preparar_dados_para_treino


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia o classificador de intrusões guardado.")
    parser.add_argument("--csv", type=Path, default=Path("data/cybersecurity_intrusion_data.csv"))
    args = parser.parse_args()

    dados = carregar_e_limpar_dados(args.csv)
    _, x_test, _, y_test, _ = preparar_dados_para_treino(dados)
    analista = AgenteAnalista()
    previsoes = analista.modelo.predict(x_test)

    print("=== Avaliação do modelo guardado ===")
    print(f"Accuracy : {accuracy_score(y_test, previsoes):.4f}")
    print(f"Precision: {precision_score(y_test, previsoes, zero_division=0):.4f}")
    print(f"Recall   : {recall_score(y_test, previsoes, zero_division=0):.4f}")
    print(f"F1-score : {f1_score(y_test, previsoes, zero_division=0):.4f}")
    print("\nMatriz de confusão [[TN, FP], [FN, TP]]:")
    print(confusion_matrix(y_test, previsoes))
    print("\nRelatório por classe:")
    print(classification_report(y_test, previsoes, digits=4, zero_division=0))


if __name__ == "__main__":
    main()

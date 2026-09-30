"""Executa a análise de um ou mais registos de sessões de rede."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from agent_system import AgenteAnalista, AgenteRelator


def main() -> None:
    parser = argparse.ArgumentParser(description="Deteção de intrusões a partir de um CSV.")
    parser.add_argument("csv", type=Path, help="CSV com sessões de rede.")
    parser.add_argument("--linha", type=int, default=None, help="Índice da linha a analisar; por omissão, analisa todas.")
    parser.add_argument("--saida", type=Path, help="Ficheiro de texto onde guardar os relatórios.")
    args = parser.parse_args()

    dados = pd.read_csv(args.csv)
    if dados.empty:
        raise ValueError("O CSV não contém sessões para analisar.")
    if args.linha is not None:
        if args.linha < 0 or args.linha >= len(dados):
            raise IndexError(f"A linha deve estar entre 0 e {len(dados) - 1}.")
        dados = dados.iloc[[args.linha]]

    analista, relator = AgenteAnalista(), AgenteRelator()
    relatorios = []
    for _, sessao in dados.iterrows():
        sessao_dict = sessao.to_dict()
        resultado = analista.analisar_sessao(sessao_dict)
        relatorios.append(relator.gerar_relatorio(sessao_dict, resultado))

    conteudo = "\n\n".join(relatorios)
    print(conteudo)
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(conteudo + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

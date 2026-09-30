# Intrusion Detection Dataset

Projeto de deteção de intrusões baseado num modelo Random Forest e num sistema multiagente simples:

- `AgenteAnalista`: prepara sessões de rede e calcula o diagnóstico;
- `AgenteRelator`: transforma o diagnóstico num relatório de incidente;
- `scripts/run_analysis.py`: interface de linha de comando para analisar CSVs.

## Instalação

```bash
pip install -r requirements.txt
```

## Utilização

Analisa todas as sessões de um ficheiro:

```bash
python scripts/run_analysis.py data/cybersecurity_intrusion_data.csv
```

Analisa apenas uma sessão e grava o relatório:

```bash
python scripts/run_analysis.py data/cybersecurity_intrusion_data.csv --linha 0 --saida outputs/relatorio.txt
```

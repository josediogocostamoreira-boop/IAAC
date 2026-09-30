# Intrusion Detection Dataset

Projeto de deteção de intrusões baseado num modelo Random Forest e num sistema multiagente simples:

- `AgenteAnalista`: prepara sessões de rede e calcula o diagnóstico;
- `AgenteRelator`: transforma o diagnóstico num relatório de incidente;
- `scripts/run_analysis.py`: interface de linha de comando para analisar CSVs.
- `scripts/evaluate_model.py`: avaliação reprodutível do modelo guardado.

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

## Avaliação

```bash
python scripts/evaluate_model.py
```

## Documentação do projeto

- [Pipeline CRISP-ML](docs/crisp_ml.md)
- [Backlog SCRUM](docs/scrum_backlog.md)
- [Diagramas de arquitetura](docs/architecture.md)
- [Guia técnico](docs/technical_guide.md)

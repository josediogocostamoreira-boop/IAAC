# Sistema de Deteção de Intrusões

Projeto IAAC de aprendizagem supervisionada para classificar sessões de rede como normais ou intrusões. A pipeline segue CRISP-ML e disponibiliza um deployment local e um sistema multiagente auditável.

## Executar

```powershell
python -m pip install -r requirements.txt
python main.py
```

Os resultados são guardados em `models/model_metrics.csv` e `models/model_metrics.json`. Para classificar uma sessão, use `scripts/predict.py`; veja o exemplo em [PROJECT_DELIVERABLES.md](docs/PROJECT_DELIVERABLES.md).

## Estrutura

- `data/` — dataset de cibersegurança.
- `notebook/` — EDA, preparação, treino e avaliação.
- `scripts/` — módulos reutilizáveis da pipeline e deployment.
- `models/` — artefactos serializados gerados pela execução.
- `docs/` — diagramas, backlog, decisões e guia de entrega.

Consulte [PROJECT_DELIVERABLES.md](docs/PROJECT_DELIVERABLES.md) para a rastreabilidade dos requisitos, Scrum, CRISP-ML e limitações a resolver pelo grupo antes da entrega.

Para a apresentação e defesa oral dos algoritmos, consulte [MODEL_GUIDE.md](docs/MODEL_GUIDE.md).

Intrusion Detection - Projeto de Análise e Preparação de Dados

Conteúdo:
- notebooks/: Notebooks de análise e EDA
- src/: Scripts de preparação e modelos
- docs/: Documentação e backlog

Como começar:
1. Criar um ambiente virtual Python 3.8+ e instalar dependências:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Baixar o dataset do Kaggle e colocar em `archive/`.
3. Rodar o EDA e treinar baseline com os scripts em `src/`.
	- `src/run_eda.py` — gera `outputs/` com head, summary e distribuição da label.
	- `src/modeling.py` — treina RandomForest baseline (usa amostra por padrão) e salva em `models/`.

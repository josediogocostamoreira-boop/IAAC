Intrusion Detection - Projeto de Análise e Preparação de Dados

Conteúdo:
- notebooks/: Notebooks de análise e EDA
- src/: Scripts de preparação e modelos
- docs/: Documentação e backlog

Como começar (PowerShell, a partir da raiz do repositório):

```bash
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
git lfs install
git lfs pull
```

O dataset em `archive/final_dataset.csv` é guardado com Git LFS (cerca de 155 MB).
Se não tiver Git LFS configurado, instale-o e execute `git lfs pull`; o ficheiro
de 134 bytes que aparece antes disso é apenas um ponteiro, não os dados.

Executar a análise e o modelo baseline:

```bash
python src\run_eda.py
python src\modeling.py
```

`src/run_eda.py` gera os resultados em `outputs/` e `src/modeling.py` treina um
Random Forest com uma amostra por padrão e guarda os artefactos em `models/`.
Os caminhos de entrada por omissão são relativos à raiz do projeto; também se
pode passar um caminho CSV como primeiro argumento.
As métricas no terminal são apresentadas em percentagem, arredondadas a duas
casas decimais; o `rf_report.csv` mantém os valores na escala de 0 a 1.

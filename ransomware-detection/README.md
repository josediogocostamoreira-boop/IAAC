# Deteção de ransomware

Projeto de Machine Learning para distinguir ficheiros benignos de ficheiros
maliciosos e, numa segunda fase, caracterizar a categoria/família do malware.

## Conteúdo

- [`ransom.csv`](./ransom.csv): dataset usado no projeto (21.752 amostras, 77 colunas).
- [`eda_ransomware_dataset_2024.ipynb`](./eda_ransomware_dataset_2024.ipynb):
  exploração univariada, bivariada, multivariada e correlações.
- [`docs/business-understanding.md`](./docs/business-understanding.md):
  problema, objetivos, stakeholders, riscos e critérios de sucesso.
- [`docs/data-understanding.md`](./docs/data-understanding.md):
  inventário e diagnóstico inicial do dataset.
- [`docs/data-preparation.md`](./docs/data-preparation.md):
  plano reproduzível de limpeza, encoding e divisão dos dados.
- [`docs/product-backlog.md`](./docs/product-backlog.md): user stories e
  critérios de aceitação.
- [`docs/sprint-backlog.md`](./docs/sprint-backlog.md): distribuição sugerida
  para o primeiro sprint.
- [`docs/scrum-templates.md`](./docs/scrum-templates.md): templates de Daily,
  Sprint Review e Sprint Retrospective.
- [`src/data_preprocessing.py`](./src/data_preprocessing.py): preparação
  leakage-safe e deduplicação por MD5.
- [`src/train.py`](./src/train.py): baseline Dummy, Logistic Regression,
  Random Forest e Extra Trees.

## Ambiente

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Abrir o notebook e selecionar o kernel `.venv`. O notebook espera encontrar
`ransom.csv` na mesma pasta.

## Objetivo técnico

O primeiro problema é uma classificação binária (`Class`: `Benign` ou
`Malware`). O problema multiclasse (`Category` ou `Family`) fica como extensão,
depois de validar o primeiro modelo. O dataset contém 10.876 amostras de cada
classe, mas possui 7.849 MD5 repetidos; por isso a preparação deve remover
duplicados por artefacto antes de separar treino e teste.

## Treinar os baselines

```powershell
python src/train.py --data ransom.csv --output results
```

O comando cria métricas em `results/model_metrics.csv`, estatísticas de
preparação em `results/preparation_stats.json`, o schema de features e o
pipeline do melhor modelo em `results/ransomware_classifier.joblib`.

## Resultado do baseline

Após remover hashes com rótulos conflitantes e deduplicar por MD5, ficaram
13.886 artefactos únicos. O Random Forest foi selecionado pelo maior recall de
malware no teste: 99,55%, com ROC-AUC de 99,94%. Estes valores são um baseline
reprodutível, não uma garantia de desempenho em amostras novas; a validação
externa e a análise por família continuam necessárias.

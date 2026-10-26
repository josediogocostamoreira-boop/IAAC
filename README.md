# Sistema de Deteção de Intrusões

Projeto de classificação supervisionada de sessões de rede, organizado em torno dos tópicos do Roadmap: compreensão dos dados, preparação, aprendizagem supervisionada e avaliação/otimização de modelos.

## Executar

Instale as dependências e execute a pipeline:

```powershell
python -m pip install -r requirements.txt
python main.py
```

O programa prepara os dados, treina os classificadores e apresenta as métricas no terminal. Para explorar cada etapa, abra os notebooks da pasta `notebook/` e execute as células pela ordem indicada.

## Notebooks

- `01_Data_Understanding.ipynb` — estatística descritiva, visualizações, análise univariada/bivariada e correlações de Pearson e Spearman;
- `02_Data_Preparation.ipynb` — valores em falta, valores extremos, divisão dos dados, normalização e engenharia de atributos;
- `03_Supervised_Learning.ipynb` — treino de classificadores supervisionados;
- `04_Model_Evaluation_Optimization.ipynb` — matriz de confusão, precision, recall, F1, curva ROC-AUC, validação cruzada, análise de sobreajuste/subajuste e tuning;
- `main_pipeline.ipynb` — execução integrada das etapas acima.

## Estrutura

- `data/` — dataset utilizado na experiência;
- `notebook/` — análise e experimentação por etapa;
- `scripts/` — implementação reutilizável de preparação, treino e avaliação;
- `docs/` — rastreabilidade, guia de modelos e decisões técnicas;
- `main.py` — execução integrada da pipeline;
- `requirements.txt` — dependências.

O alvo é `attack_detected` (0: normal, 1: intrusão). Os resultados dependem do dataset disponível e devem ser interpretados como experimentais, não como garantia de desempenho numa rede real.

## Documentação

- [Rastreabilidade do projeto](docs/PROJECT_DELIVERABLES.md)
- [Guia dos modelos](docs/MODEL_GUIDE.md)
- [Notas técnicas da pipeline](docs/TECHNICAL_DOCUMENTATION.md)

# Rastreabilidade do projeto

O projeto aborda as etapas do Roadmap aplicáveis à classificação de sessões de rede: compreensão dos dados e EDA, preparação, aprendizagem supervisionada, avaliação e otimização. O alvo é `attack_detected` (0: normal, 1: intrusão).

| Tópico do Roadmap | Evidência no projeto |
|---|---|
| EDA univariada, bivariada e visualização | `notebook/01_Data_Understanding.ipynb` |
| Estatística descritiva, skewness e kurtosis | `notebook/01_Data_Understanding.ipynb` |
| Correlação de Pearson e Spearman | `notebook/01_Data_Understanding.ipynb` |
| Valores em falta, outliers, divisão e scaling | `scripts/data_prep.py`, `notebook/02_Data_Preparation.ipynb` |
| Feature engineering | `scripts/data_prep.py` |
| Classificação supervisionada | `scripts/train.py`, `notebook/03_Supervised_Learning.ipynb` |
| Matriz de confusão, precision, recall, F1 e ROC-AUC | `scripts/evaluate.py`, `notebook/04_Model_Evaluation_Optimization.ipynb` |
| Validação cruzada e seleção de modelos | `scripts/evaluate.py` |
| Diagnóstico de sobreajuste/subajuste | `scripts/evaluate.py` |
| Otimização de hiperparâmetros | `scripts/evaluate.py`, `notebook/04_Model_Evaluation_Optimization.ipynb` |
| Product backlog e Scrum | Histórico de tarefas e registos reais do grupo |

O Roadmap menciona também conteúdos de regressão, mas o problema e o dataset deste projeto têm um alvo binário de classificação. A implementação mantém esse âmbito e não inventa uma variável de regressão.

## User stories

| ID | User story | Critério de aceitação | Sprint |
|---|---|---|---|
| US-01 | Como analista, quero compreender a distribuição e qualidade dos dados. | EDA com estatísticas, visualizações e correlações. | 1 |
| US-02 | Como cientista de dados, quero preparar os dados antes de treinar. | Divisão treino/teste, tratamento e scaling reproduzíveis. | 2 |
| US-03 | Como analista, quero comparar classificadores. | Métricas e matriz de confusão para os modelos. | 3 |
| US-04 | Como equipa, queremos melhorar a seleção do modelo. | Validação cruzada e tuning documentados. | 4 |

Os registos de Daily Scrum, Sprint Review, Retrospective, participantes e atribuição das tarefas devem refletir o trabalho real do grupo. Não devem ser preenchidos com informação inventada.

## Execução

```powershell
python -m pip install -r requirements.txt
python main.py
```

A execução apresenta as métricas no terminal. Os notebooks permitem executar e examinar cada etapa separadamente.

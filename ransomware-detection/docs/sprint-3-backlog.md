# Sprint 3 — Supervised Learning

**Objetivo:** comparar algoritmos de classificação supervisionada para
identificar malware, com avaliação reproduzível e teste independente.

| ID | Tarefa | Critério de aceitação | Evidência |
|---|---|---|---|
| S3-01 | Treinar Logistic Regression e Decision Tree | Pipeline sem leakage e métricas calculadas | CSV de comparação — concluído |
| S3-02 | Treinar k-NN e Naive Bayes | Imputação/encoding/escala adequados aos algoritmos | CSV de comparação — concluído |
| S3-03 | Treinar SVM linear e RBF | ROC-AUC/PR-AUC e tipo do score identificados | CSV de comparação — concluído |
| S3-04 | Treinar ensemble: AdaBoost, Gradient Boosting e Random Forest | Recall de Malware comparável | CSV de comparação — concluído |
| S3-05 | Avaliar XGBoost como extensão opcional | Execução apenas quando instalado | Opção `--include-xgboost` — não executado |
| S3-06 | Selecionar pelo conjunto de validação | Teste não usado para escolher o modelo | Relatório JSON — concluído |
| S3-07 | Avaliar uma única vez no conjunto de teste | Métricas e matriz de confusão guardadas | `supervised_learning_report.json` — concluído |
| S3-08 | Registar a decisão de não usar regressão | Não existe alvo contínuo adequado | `supervised-learning.md` — concluído |

O benchmark usa split estratificado 60/20/20. O modelo é ordenado por recall
de Malware na validação; precision e F1 servem de desempate. O conjunto de
teste permanece isolado até à avaliação final.

O registo preenchido da sprint, com Planning, simulação de Daily, Review e
Retrospective proposta para validação pela equipa, está em
[`sprint-3-template.md`](./sprint-3-template.md).

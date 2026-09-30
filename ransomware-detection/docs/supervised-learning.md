# Supervised Learning — Module 6

## Enquadramento

O objetivo do projeto é prever rótulos de malware, pelo que a tarefa adequada
é **classificação supervisionada**. O CSV disponibiliza rótulos categóricos
`Class`, `Category` e `Family`; não contém uma variável resposta contínua
justificada para regressão. Por isso, Linear Regression e regressão de árvores
não são treinadas artificialmente neste projeto.

## Algoritmos implementados

O script [`supervised_learning.py`](../src/supervised_learning.py) compara:

- Logistic Regression;
- Decision Tree Classifier;
- k-Nearest Neighbors;
- Gaussian Naive Bayes;
- Bernoulli Naive Bayes;
- SVM linear e RBF;
- AdaBoost;
- Gradient Boosting;
- Random Forest;
- Extra Trees;
- XGBoost, opcional.

Os pipelines imputam, codificam e escalam features a partir do conjunto de
treino. A divisão é estratificada em treino, validação e teste. O modelo é
escolhido pela recall de Malware na validação (com precision e F1 como
desempate); o teste só é usado para a avaliação final.

## Métricas

O relatório contém accuracy, precision, recall, F1, ROC-AUC e PR-AUC. Para
SVM, os scores de decisão não são probabilidades calibradas; por isso estão
identificados como `decision_function`.

## Execução

```powershell
python src/supervised_learning.py --data ransom.csv --output results
```

Para acrescentar XGBoost (dependência opcional):

```powershell
python -m pip install xgboost
python src/supervised_learning.py --data ransom.csv --output results --include-xgboost
```

Artefactos produzidos:

- `supervised_model_comparison.csv`: comparação dos modelos na validação;
- `supervised_learning_report.json`: split, algoritmo escolhido e métricas
  finais no teste;
- `supervised_confusion_matrix.png`: matriz de confusão do modelo escolhido
  no conjunto de teste.

Este benchmark não altera o classificador existente em
`results/ransomware_classifier.joblib`.

## Execução no dataset atual

Foram comparados 11 classificadores (XGBoost não estava instalado). A seleção
por recall na validação escolheu **Gradient Boosting**. No teste intocado,
obteve:

| Métrica | Resultado |
|---|---:|
| Accuracy | 99,14% |
| Precision de Malware | 98,67% |
| Recall de Malware | 99,55% |
| F1 de Malware | 99,11% |
| ROC-AUC | 99,87% |
| PR-AUC | 99,87% |

Estes números são uma avaliação holdout do dataset disponível e não garantem
o mesmo desempenho em famílias ou amostras futuras.

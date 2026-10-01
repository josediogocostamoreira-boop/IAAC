# Supervised Learning — Module 6

## Enquadramento

O objetivo é classificar a coluna `Class` como `Benign` ou `Malware`. `Category`
e `Family` são rótulos categóricos e podem ser tratados como tarefas
multiclasse futuras; não existe variável contínua adequada para regressão.

## Classificadores

`src/supervised_learning.py` compara Logistic Regression, Decision Tree,
k-Nearest Neighbors, Gaussian e Bernoulli Naive Bayes, SVM linear/RBF,
AdaBoost, Gradient Boosting, Random Forest e Extra Trees. XGBoost é opcional.
Todos usam pipelines scikit-learn com imputação, encoding e escala aprendidos
dentro do treino.

## Seleção e avaliação

A divisão é estratificada: 60% treino, 20% validação e 20% teste. A seleção
usa recall de Malware na validação, com precision e F1 como desempate. O teste
fica reservado à avaliação final. O vencedor e todos os outros pipelines são
ajustados novamente com treino e validação antes de serem guardados.

## Execução

```powershell
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware
```

Para incluir XGBoost:

```powershell
python -m pip install xgboost
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware --include-xgboost
```

## Artefactos

- `results/supervised_model_comparison.csv`: resultados de validação;
- `results/supervised_learning_report.json`: split, modelo selecionado e
  métricas finais do teste;
- `results/supervised_confusion_matrix.png`: matriz de confusão no teste;
- `models/ransomware/*.joblib`: pipelines dos classificadores;
- `models/ransomware/feature_schema.json`: nomes/ordem das features.

`src/predict.py`, `src/serve.py` e os agentes resolvem o modelo selecionado a
partir do relatório e usam o schema guardado com os pipelines. Scores SVM são
`decision_function`, não probabilidades calibradas.

## Limitações

Os resultados do holdout do dataset atual não demonstram generalização a outras
famílias, fontes ou datasets. Os dados dos restantes elementos do grupo ainda
não estão disponíveis nesta pasta.

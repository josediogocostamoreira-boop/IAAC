# Supervised Learning — Module 6

## Enquadramento

O objetivo é classificar a coluna `Class` como `Benign` ou `Malware`. `Category`
e `Family` são rótulos categóricos e podem ser tratados como tarefas
multiclasse futuras; não existe variável contínua adequada para regressão.

## Classificadores

`src/supervised_learning.py` compara Logistic Regression, Decision Tree,
k-Nearest Neighbors, Gaussian, Bernoulli e Multinomial Naive Bayes, SVM
linear/RBF, AdaBoost, Gradient Boosting, Random Forest e Extra Trees. XGBoost
é opcional.
Todos usam pipelines scikit-learn com seleção de features, engenharia `log1p`,
imputação, encoding e escala aprendidos dentro do treino.

## Seleção e avaliação

A divisão é estratificada: 60% treino, 20% validação e 20% teste. A seleção
inicial usa recall de Malware na validação, com precision e F1 como desempate.
O modelo selecionado é afinado com `GridSearchCV` e `StratifiedKFold` no
conjunto treino+validação; o teste fica reservado à avaliação final. A
pesquisa inclui regularização/complexidade do algoritmo e número de features.
O relatório compara recall de treino-CV com recall de validação-CV para
sinalizar possível overfitting ou underfitting; os limiares são heurísticas,
não prova de capacidade de generalização. O vencedor afinado e os restantes
pipelines são ajustados com treino e validação antes de serem guardados.

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
- `results/hyperparameter_search.csv`: combinações e resultados CV do modelo
  selecionado;
- `results/learning_curve.csv` e `results/learning_curve.png`: recall de treino
  e validação ao aumentar os dados de treino;
- `results/supervised_roc_curve.png`: curva ROC no holdout;
- `results/supervised_learning_report.json`: split, modelo selecionado e
  métricas finais do teste, parâmetros afinados, CV e diagnóstico de fit;
- `results/supervised_confusion_matrix.png`: matriz de confusão no teste;
- `models/ransomware/*.joblib`: pipelines dos classificadores;
- `models/ransomware/feature_schema.json`: nomes/ordem das features.

`src/predict.py`, `src/serve.py` e os agentes resolvem o modelo selecionado a
partir do relatório e usam o schema guardado com os pipelines. Scores SVM são
`decision_function`, não probabilidades calibradas.

## Regressão, regularização e limites

O alvo `Class` é categórico (`Benign`/`Malware`), por isso regressão não é
adequada à pergunta. A secção de regressão do roadmap não está marcada como
mínima; executá-la exigiria um target contínuo diferente. Regularização e
complexidade são afinadas quando suportadas pelo modelo selecionado, incluindo
parâmetros como `C`, profundidade e número mínimo de amostras nas folhas.

## Limitações

Os resultados do holdout do dataset atual não demonstram generalização a outras
famílias, fontes ou datasets. Os dados dos restantes elementos do grupo ainda
não estão disponíveis nesta pasta.

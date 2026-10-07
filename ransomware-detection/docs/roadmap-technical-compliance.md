# Matriz técnica do roadmap IAAC

Esta matriz acompanha a implementação técnica. Não é evidência de reuniões,
aprovação do docente, composição do grupo ou aceitação do Product Owner.

## Data Understanding e EDA

| Requisito técnico | Implementação/evidência |
|---|---|
| Visão geral, limpeza e distribuições | `src/data_preprocessing.py`, `src/roadmap_eda.py`, `results/roadmap/eda/eda_summary.json` |
| Análise univariada numérica e categórica | Sumários numéricos/categóricos e distribuições CSV/PNG |
| Análise bivariada e significância | Mann-Whitney U para features numéricas; qui-quadrado para categóricas; tamanho de efeito e correção Benjamini-Hochberg |
| Análise multivariada | PCA exploratória, scores, loadings e variância explicada |
| Visualização | Distribuições, boxplots por classe, heatmaps Pearson/Spearman e scatter PCA |
| Correlação de Pearson e Spearman | Matrizes completas e pares em `results/roadmap/eda/` |
| Skewness, kurtosis e outliers | Sumário univariado e `results/feature_quality.csv`; outliers IQR são reportados e não removidos automaticamente |

Reproduzir:

```powershell
python src/roadmap_eda.py --data ransom.csv --output results/roadmap/eda
python src/data_preparation_report.py --data ransom.csv --output results/roadmap/preparation
```

P-values e associações são descritivos, não causais. Os p-values das análises
por feature são ajustados para comparações múltiplas. A PCA é exploratória,
ajustada ao dataset limpo completo e não é validação preditiva.

## Data Preparation

| Requisito técnico | Implementação/evidência |
|---|---|
| Limpeza, missing e conflitos | Validação de rótulos e hashes; conflitos por MD5 removidos e reportados |
| Split e controlo de leakage | Deduplicação por MD5 antes do split; transformações ajustadas dentro de cada fold |
| Outliers | IQR, skewness e kurtosis reportados; sem remoção silenciosa |
| Feature selection | `SelectKBest(f_classif)` dentro do pipeline; número de features afinado por CV |
| Feature engineering | `Log1pSkewedNonNegative` aprende por fold as features não negativas com skewness absoluta > 1 |
| Scaling, encoding e missing | Imputação, one-hot encoding e escaladores dentro dos pipelines |
| Desbalanceamento | Distribuição reportada; `class_weight='balanced'` nos modelos compatíveis |
| Feature extraction | Extração estática PE para `.exe` e `.exe` em ZIP em `src/extract_features.py`; comportamento não é inventado |

## Supervised Learning e Model Evaluation

| Requisito técnico | Implementação/evidência |
|---|---|
| Classificação | 12 classificadores, incluindo Gaussian, Bernoulli e Multinomial Naive Bayes; XGBoost opcional |
| Model selection | Recall de Malware na validação, precision/F1 como desempate |
| Cross-validation | `StratifiedKFold`, 3 folds por omissão, apenas em treino+validação |
| Hyperparameter tuning | `GridSearchCV` no modelo selecionado, usando recall de Malware |
| Regularização/complexidade | Pesquisa dos parâmetros aplicáveis (`C`, alpha, profundidade, folhas, estimadores, learning rate) |
| Overfitting/underfitting | Gap train-CV versus validação-CV e learning curve; limiares de triagem explícitos |
| Métricas e matriz de confusão | Accuracy, precision, recall, F1, ROC-AUC, PR-AUC, matriz de confusão e curva ROC no teste reservado |
| Teste independente | O holdout não é usado para seleção ou afinação |
| Regressão | Não aplicável ao target categórico `Class`; regressão não está marcada como mínima no roadmap |

Executar:

```powershell
python src/supervised_learning.py --data ransom.csv --output results/roadmap/model_evaluation --model-dir models/roadmap/ransomware --cv-folds 3
```

Na execução reproduzida neste projeto, a limpeza reduziu 21.752 linhas para
13.886 após remover 611 registos com rótulos conflitantes por MD5. O benchmark
comparou 12 classificadores e selecionou Random Forest. No holdout, obteve
accuracy 0,9924, precision de Malware 0,9875, recall 0,9970, F1 0,9922 e
ROC-AUC 0,9990. O gap de recall entre treino-CV e validação-CV foi 0,0030,
sem sinal forte de over/underfitting segundo a heurística implementada. Estes
valores descrevem apenas este dataset e split; não provam generalização para
outras fontes.

O diagnóstico de overfitting/underfitting é uma heurística baseada no recall,
não uma prova. Os resultados do dataset atual não demonstram generalização a
outras fontes, famílias ou datasets.

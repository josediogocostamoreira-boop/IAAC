# Notas técnicas da pipeline

## Compreensão e preparação dos dados

O dataset é lido de `data/cybersecurity_intrusion_data.csv`. A coluna-alvo é `attack_detected`; o identificador `session_id` é removido porque não representa um atributo útil para generalizar para sessões novas.

A preparação em `scripts/data_prep.py` divide os dados de forma estratificada, reservando 20% para teste, com seed 42. As variáveis numéricas recebem imputação pela mediana, limitação de extremos pelo intervalo interquartil e `StandardScaler`. As variáveis categóricas recebem imputação pela categoria mais frequente e one-hot encoding. O pré-processador é ajustado no treino e aplicado ao teste.

São criadas três features derivadas: razão de logins falhados, ritmo de pacotes e risco associado à reputação do IP. O processo de preparação não utiliza a variável-alvo para calcular estas features.

## Classificação supervisionada

`scripts/train.py` define classificadores abordados no Roadmap: regressão logística, árvore de decisão, k-NN, Naive Bayes, SVM, Random Forest, AdaBoost, Gradient Boosting e XGBoost quando a dependência está instalada. Todos recebem o mesmo conjunto de treino preparado. O Multinomial Naive Bayes inclui uma escala MinMax, pois requer valores não negativos.

## Avaliação e otimização

`scripts/evaluate.py` calcula accuracy, precision, recall, F1, ROC-AUC, matriz de confusão e a diferença entre F1 de treino e teste. A seleção ordena os modelos pela F1 média em validação cruzada estratificada de cinco folds. Em cada fold, uma cópia do pré-processador é ajustada apenas nos dados de treino desse fold.

A função `tune_random_forest` usa GridSearchCV com F1 e validação cruzada estratificada para comparar número de estimadores, profundidade máxima e mínimo de amostras por folha. O pré-processador é ajustado dentro de cada fold, evitando que a pesquisa use estatísticas da validação. O resultado é devolvido ao notebook e apresentado; não são criados ficheiros CSV/JSON ou modelos serializados.

## Interpretação

Precision e recall devem ser lidos em conjunto. Um falso positivo é um registo normal classificado como intrusão; um falso negativo é uma intrusão classificada como normal. A escolha de um classificador depende do compromisso entre estes erros e do contexto de utilização. As métricas deste projeto descrevem apenas a experiência com o dataset disponível.

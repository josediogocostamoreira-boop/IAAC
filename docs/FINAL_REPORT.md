# Intrusion Detection - Relatório Técnico

## 1. Introdução
Este projeto tem como objetivo desenvolver um pipeline de Machine Learning para detecção de intrusão em dados tabulares, com foco em classificação binária ou multiclasse dependendo da estrutura do dataset. O trabalho foi organizado em etapas de preparação dos dados, análise exploratória, seleção de features, treinamento de modelos e avaliação de desempenho.

A solução foi implementada em Python, utilizando bibliotecas como pandas, scikit-learn e joblib, com organização modular em scripts dentro da pasta src. O pipeline foi pensado para permitir reuso, automação e fácil reprodução dos experimentos.

---

## 2. Objetivo do projeto
O objetivo principal é criar uma base de processamento e modelagem capaz de:

- carregar e limpar dados de rede/IoT;
- identificar padrões relevantes para a classificação de intrusão;
- reduzir a dimensionalidade por meio de seleção de features;
- treinar modelos de classificação robustos;
- avaliar métricas de desempenho;
- armazenar os modelos e relatórios gerados para uso posterior.

---

## 3. Arquitetura do projeto
A estrutura do repositório foi organizada da seguinte forma:

- notebooks/: notebooks de análise exploratória e prototipagem;
- src/: scripts responsáveis por preparação, EDA, feature engineering e modelagem;
- archive/: dataset principal utilizado para treinamento;
- outputs/: resultados intermediários da análise exploratória;
- models/: artefatos finais do modelo e relatórios de desempenho;
- docs/: documentação e relatórios técnicos.

Os principais arquivos do pipeline são:

- [src/data_preparation.py](../src/data_preparation.py): preparação e normalização dos dados;
- [src/run_eda.py](../src/run_eda.py): geração de estatísticas e distribuição da classe-alvo;
- [src/feature_engineering.py](../src/feature_engineering.py): seleção automática de atributos e treino final;
- [src/modeling.py](../src/modeling.py): baseline de Random Forest;
- [README.md](../README.md): instruções gerais de execução.

---

## 4. Fonte de dados
O dataset principal está localizado em archive/final_dataset.csv. A base contém registros tabulares com múltiplas variáveis e uma coluna alvo responsável por identificar a classe de atividade, usualmente chamada de label ou Label.

Como parte do processamento, o código realiza conversões de nomes de colunas para garantir compatibilidade entre diferentes convenções de nomenclatura. Essa etapa é importante para evitar inconsistências em pipelines automatizados.

---

## 5. Pipeline técnico

### 5.1 Preparação dos dados
No script [src/data_preparation.py](../src/data_preparation.py), a primeira etapa inclui:

- leitura do CSV via pandas;
- remoção de linhas duplicadas;
- eliminação de colunas totalmente vazias;
- preenchimento de valores ausentes em colunas numéricas;
- divisão dos dados em treino e teste usando train_test_split;
- padronização com StandardScaler.

A função split_data realiza a separação com stratify=y, preservando a proporção da classe alvo entre treino e teste. Isso reduz o risco de viés em classificadores sensíveis ao desbalanceamento.

### 5.2 Análise exploratória
O script [src/run_eda.py](../src/run_eda.py) gera um conjunto de artefatos úteis para avaliação descritiva:

- head do dataset;
- informações de shape e dtypes;
- valores nulos por coluna;
- estatísticas descritivas das variáveis numéricas;
- distribuição da variável alvo, quando presente.

Esses outputs servem para validar a qualidade da base e verificar se o conjunto está balanceado, se há campos incompletos ou se existem sinais de anomalia na distribuição dos dados.

### 5.3 Engenharia de características
A etapa de feature engineering é implementada em [src/feature_engineering.py](../src/feature_engineering.py). O processo compreende:

- leitura do dataset e padronização do nome da classe alvo;
- amostragem do conjunto para limitar o tempo de processamento;
- conversão de colunas categóricas em códigos numéricos;
- treinamento de um Random Forest para estimar a importância de cada feature;
- seleção das top_k variáveis mais relevantes;
- salvamento das importâncias e das features selecionadas em arquivos JSON/CSV.

Essa etapa é essencial porque reduz ruído, aumenta a interpretabilidade do modelo e pode melhorar o desempenho geral em cenários com muitas variáveis.

### 5.4 Treinamento do modelo
Os modelos são treinados com RandomForestClassifier, com ajuste de parâmetros simples e robustos:

- n_estimators=100 ou 200;
- n_jobs=-1 para paralelização;
- random_state=42 para reprodutibilidade;
- divisão estratificada entre treino e teste.

Além disso, as features são normalizadas antes do treinamento para padronizar a escala e melhorar a estabilidade do classificador. Após o treinamento, o código utiliza classification_report para analisar precision, recall, f1-score e support.

---

## 6. Avaliação de desempenho
A avaliação do modelo é realizada a partir das métricas derivadas do conjunto de teste. As métricas mais relevantes são:

- accuracy: proporção geral de acertos;
- precision: proporção de previsões corretas entre as positivas;
- recall: capacidade do modelo de identificar corretamente os casos positivos;
- f1-score: média harmônica entre precision e recall;
- support: número de instâncias por classe.

Os relatórios gerados são salvos em arquivos CSV dentro da pasta models, sendo possível reutilizar os resultados para comparação entre versões do modelo.

---

## 7. Artefatos produzidos
O projeto gera uma série de artefatos que documentam o processo:

- outputs/head.csv: amostra inicial do dataset;
- outputs/summary.txt: resumo estatístico do conjunto;
- outputs/label_distribution.csv e .png: distribuição da classe alvo;
- models/feature_importances.csv: importância das variáveis;
- models/selected_features.json: lista das features selecionadas;
- models/rf_model.joblib: modelo baseline salvo;
- models/rf_selected.joblib: modelo treinado com features selecionadas;
- models/rf_report.csv e rf_selected_report.csv: relatórios de classificação.

Esses arquivos são fundamentais para análise, reprodução e apresentação dos resultados.

---

## 8. Resultados esperados e observações
Durante os experimentos, os modelos de Random Forest podem atingir valores muito altos de acurácia, dependendo da estrutura do dataset. Isso é um sinal positivo, mas também merece atenção crítica: resultados muito próximos de 1.00 podem indicar que o problema é relativamente simples ou que há alguma forma de vazamento de informação, especialmente quando a base está fortemente separada por classes.

Portanto, é recomendável validar o desempenho com técnicas mais rigorosas, como:

- validação cruzada estratificada;
- validação temporal, quando há dependência temporal nos dados;
- comparação com outros algoritmos;
- revisão da origem das features para confirmar que não há leaks.

---

## 9. Limitações e riscos
Algumas limitações do projeto atual incluem:

- uso de amostragem para reduzir o volume de dados;
- processamento simples de variáveis categóricas;
- ausência de uma validação mais rigorosa do tipo time-based split;
- possibilidade de overfitting em bases altamente separáveis;
- dependência de uma única estratégia de feature selection.

Essas limitações não invalidam a solução, mas mostram que o pipeline é um protótipo funcional e passível de aprimoramento.

---

## 10. Próximos passos
Para evoluir o trabalho, os próximos passos recomendados são:

1. aplicar validação cruzada estratificada e validação temporal;
2. testar outros algoritmos, como XGBoost, SVM e Logistic Regression;
3. comparar desempenho com e sem feature selection;
4. revisar colunas para detectar leakage ou redundância;
5. construir um pipeline automatizado de treinamento e avaliação;
6. implementar dashboard de monitoramento para métricas e previsões.

---

## 11. Conclusão
O projeto implementa um pipeline completo de detecção de intrusão baseado em Machine Learning, cobrindo desde a preparação dos dados até a avaliação do modelo. A organização modular em scripts permite fácil manutenção e extensão da solução, enquanto os artefatos gerados tornam o processo reprodutível e documentado.

O conjunto de técnicas adotado é adequado para um protótipo funcional de classificação de intrusão, com potencial para evoluir para um sistema mais robusto e validado em cenários reais. O principal diferencial do trabalho está na combinação de análise exploratória, seleção inteligente de features e treinamento de modelo supervisionado dentro de uma estrutura organizada e reutilizável.


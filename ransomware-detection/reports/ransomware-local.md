# Relatório assistido por agente generativo

> Os resultados abaixo são formatados pelo programa a partir dos artefactos do benchmark. A nota generativa não é validada e não é um veredito de segurança.

## Resultados verificáveis

- Dataset: ransomware
- Classificador selecionado: gradient_boosting
- Tamanho do conjunto de teste: 2778
- Linhas classificadas na demonstração: 3

### Métricas no conjunto de teste

| Métrica | Valor |
|---|---:|
| Accuracy | 0.9914 |
| Precision (Malware) | 0.9867 |
| Recall (Malware) | 0.9955 |
| F1 (Malware) | 0.9911 |
| ROC-AUC | 0.9987 |
| PR-AUC | 0.9987 |

### Distribuição das previsões da demonstração

| Classe prevista | Linhas |
|---|---:|
| Benign | 3 |

A demonstração não é uma avaliação independente. Os scores de decisão não são probabilidades calibradas.

### Exemplos de previsões (máximo 10)

| # | Classe | Score | Tipo |
|---:|---|---:|---|
| 1 | Benign | 0.002411 | probability |
| 2 | Benign | 0.006078 | probability |
| 3 | Benign | 0.001253 | probability |

## Resultado do agente generativo

A saída generativa foi rejeitada pelo validador porque não corresponde ao token esperado (REVIEW_REQUIRED). O texto rejeitado foi omitido para evitar apresentar afirmações não verificadas. Nota controlada: A classificação automática apoia a triagem; a decisão exige validação humana.

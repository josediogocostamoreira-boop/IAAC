# Pipeline CRISP-ML — Intrusion Detection Dataset

Este documento descreve a pipeline que o código implementa. Deve ser usado como apoio técnico e validado pelo grupo antes da entrega.

## 1. Business understanding

Objetivo: classificar sessões de rede como tráfego normal (`0`) ou potencial ataque (`1`) para apoiar a resposta inicial a incidentes.

Métrica principal: F1-score da classe de ataque. Esta métrica equilibra precisão e recall, importante quando falsos positivos cansam a equipa de segurança e falsos negativos deixam intrusões passar.

## 2. Data understanding

Fonte: `data/cybersecurity_intrusion_data.csv`.

- 9.537 sessões;
- alvo: `attack_detected`;
- identificador removido: `session_id`;
- atributos numéricos: tamanho do pacote, tentativas de login, duração da sessão, reputação do IP, logins falhados e horário invulgar;
- atributos categóricos: protocolo, cifragem e browser.

## 3. Data preparation

Implementado em `scripts/data_cleaner.py`:

1. lê o CSV e remove `session_id`, que é apenas identificador;
2. preenche valores ausentes de `encryption_used` com `Desconhecido`;
3. separa atributos e alvo;
4. aplica one-hot encoding às categorias;
5. divide treino/teste de forma estratificada (80/20, `random_state=42`);
6. normaliza apenas atributos numéricos com `StandardScaler` treinado no conjunto de treino.

## 4. Model development

O notebook `01_treino_modelos.ipynb` compara Logistic Regression, Decision Tree, Random Forest e Gradient Boosting. O Random Forest foi selecionado e guardado em `models/melhor_modelo.pkl`, juntamente com o scaler em `models/scaler.pkl`.

Trade-off: Random Forest é menos interpretável do que uma árvore única, mas é mais robusto à variância e apresentou o melhor F1-score entre os modelos testados.

## 5. Evaluation

Execute a avaliação reprodutível a partir da raiz do projeto:

```bash
python scripts/evaluate_model.py
```

No treino guardado no notebook, o Random Forest obteve Accuracy 0,8863, Precision 0,9969, Recall 0,7479 e F1-score 0,8547. A avaliação deve ser novamente executada no ambiente de entrega, pois versões diferentes das bibliotecas podem alterar ligeiramente os resultados.

## 6. Deployment and monitoring

`scripts/run_analysis.py` recebe um CSV bruto, prepara cada sessão com as mesmas features usadas no treino, classifica-a e emite um relatório de incidente. Para produção, recomenda-se registar previsões, confiança, falsos positivos reportados pelos analistas e drift nas distribuições das features.

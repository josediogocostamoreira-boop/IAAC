# Decisões técnicas e trade-offs

`data_prep.py` elimina `session_id`: é um identificador único e permitiria memorizar sessões, não generalizar. A divisão estratificada preserva a proporção de ataques. A imputação mediana/moda torna a pipeline tolerante a valores em falta; IQR capping reduz a influência de extremos sem apagar registos. O `OneHotEncoder(handle_unknown="ignore")` evita falhas em protocolos ou browsers novos. A normalização é indispensável para k-NN e SVM.

Os modelos são todos treinados com a mesma representação para uma comparação justa. Há árvores e ensembles para relações não lineares; regressão logística para uma referência interpretável; Naive Bayes como baseline rápido; k-NN e SVM como métodos geométricos. XGBoost é opcional para o projeto continuar funcional quando a biblioteca não estiver instalada.

O F1 é o critério primário porque equilibra falsos positivos e falsos negativos. ROC-AUC e PR-AUC avaliam a ordenação por probabilidade; precision e recall tornam o custo operacional visível. Um desfasamento de F1 treino–teste superior a 0,10 assinala sobreajuste. A validação cruzada usa cinco folds estratificados e seed fixa para comparação reprodutível.

O deployment usa o mesmo preprocessor serializado, evitando incompatibilidade de colunas. O agente de risco não afirma ser um LLM: aplica regras explícitas sobre a probabilidade, adequadas para uma demonstração auditável. Para a valorização com um LLM/Unsloth/Transformers ou CrewAI, deve-se acrescentar um adaptador que não transmita dados sensíveis sem autorização, faça validação de saída e mantenha este classificador como fonte de verdade.

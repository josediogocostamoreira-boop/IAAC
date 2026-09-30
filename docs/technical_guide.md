# Guia técnico: decisões, código e testes

Este documento explica as decisões de implementação. É documentação técnica de apoio; o grupo deve confirmar a sua exatidão e redigir autonomamente o relatório académico solicitado na disciplina.

## `data_cleaner.py`

`carregar_e_limpar_dados` centraliza a leitura e a limpeza mínima. Remove `session_id` porque identificadores únicos permitem ao modelo memorizar linhas, mas não descrevem o comportamento de uma sessão. Preenche `encryption_used` com `Desconhecido` para preservar os registos e tornar a ausência de valor uma categoria explícita.

`preparar_dados_para_treino` evita data leakage: faz a divisão estratificada antes de ajustar o `StandardScaler`, e ajusta o scaler apenas em `X_train`. A codificação one-hot torna categorias utilizáveis pelos classificadores de scikit-learn; `drop_first=True` remove uma coluna redundante por categoria.

## `agent_system.py`

`AgenteAnalista` carrega o modelo e o scaler uma vez no construtor. O uso de caminhos baseados em `Path(__file__)` permite chamar o sistema a partir da raiz, de um notebook ou de outro diretório sem depender do diretório atual.

`preparar_sessao` recebe um dicionário ou `DataFrame`. Remove campos que não foram usados no treino, codifica categorias e usa `reindex(columns=self.feature_names, fill_value=0)` para obter exatamente as features do modelo. Isto protege a inferência contra colunas novas, colunas ausentes e ordenação diferente. O scaler é aplicado apenas às colunas numéricas que conheceu no treino.

`analisar_sessao` usa `predict` para a classe e `predict_proba` para comunicar risco. A probabilidade da classe 1 é devolvida explicitamente, para que o relatório não confunda confiança na classe prevista com risco de ataque.

`AgenteRelator` gera uma recomendação determinística baseada no resultado: bloqueio/isolamento quando existe ataque e monitorização nos restantes casos. Este comportamento é auditável e seguro como fallback, mas ainda não é um agente generativo LLM.

## `run_analysis.py`

A CLI aceita um CSV inteiro ou uma linha através de `--linha`. Valida CSV vazio e índices inválidos. A opção `--saida` guarda relatórios em UTF-8 e cria a pasta de destino quando necessário.

## `evaluate_model.py`

O script reconstrói a divisão de teste com o mesmo `random_state=42` e mostra accuracy, precision, recall, F1-score, matriz de confusão e relatório por classe. Precision e recall são ambos necessários: uma precision alta reduz alertas falsos, enquanto recall alto reduz ataques não detetados.

## Casos testados

1. Dependências, modelo e scaler carregam sem erro.
2. Uma sessão marcada como ataque produz diagnóstico de ameaça.
3. Uma sessão normal produz diagnóstico de tráfego normal.
4. As 9.537 sessões são preparadas com 14 features esperadas pelo modelo.
5. A CLI cria e grava um relatório em UTF-8.

## Limitações e próximo incremento

O dataset é estático; em produção é necessário monitorizar drift e validar os alertas com analistas. Para cumprir a valorização do enunciado, o próximo incremento deve acrescentar um relator LLM local (por exemplo, Transformers) ou um segundo orquestrador (CrewAI/n8n), mantendo o relator atual como fallback quando o modelo generativo não estiver disponível.

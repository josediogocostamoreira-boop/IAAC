# Gestão SCRUM — Backlog do projeto

Este é um backlog técnico inicial. O grupo deve atribuir responsáveis, estimativas e datas reais no quadro SCRUM utilizado na disciplina.

| Sprint | User story | Critério de aceitação | Estado |
|---|---|---|---|
| 1 | Como analista, quero carregar e compreender o dataset para definir o problema de classificação. | Dataset documentado, alvo identificado e qualidade verificada. | Concluído |
| 1 | Como cientista de dados, quero preparar dados reutilizáveis para treinar modelos de forma consistente. | Funções em `data_cleaner.py`; divisão estratificada e scaler sem leakage. | Concluído |
| 2 | Como analista, quero comparar vários classificadores para selecionar o melhor modelo. | Quatro modelos avaliados no notebook e métricas registadas. | Concluído |
| 2 | Como operador, quero guardar o modelo e o scaler para reutilização. | Artefactos presentes em `models/`. | Concluído |
| 3 | Como SOC analyst, quero analisar um CSV bruto e receber uma recomendação de ação. | `run_analysis.py` gera diagnóstico e relatório. | Concluído |
| 3 | Como avaliador, quero reproduzir as métricas do modelo guardado. | `evaluate_model.py` imprime métricas e matriz de confusão. | Concluído |
| 4 | Como analista, quero um relator LLM que contextualize incidentes. | Integração testada com um modelo local ou API autorizada, com fallback documentado. | Pendente |
| 4 | Como equipa, queremos apresentar arquitetura, resultados e limitações. | Diagramas, slides e demonstração ensaiada. | Pendente |

## Definition of Done

Uma tarefa só é considerada concluída quando o código está no repositório, é executável a partir de uma instalação limpa, tem instruções de utilização e foi revisto pelo elemento responsável.

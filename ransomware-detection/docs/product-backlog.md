# Product Backlog

Prioridade: **P0** é obrigatório, **P1** importante e **P2** extensão.

| ID | User story | Prioridade | Critérios de aceitação | Estimativa |
|---|---|---|---|---:|
| US-01 | Como analista, quero carregar e validar o dataset para conhecer a sua qualidade. | P0 | Shape, tipos, missing, duplicados e rótulos documentados. | 3 |
| US-02 | Como analista, quero visualizar a distribuição das classes para avaliar viés. | P0 | Gráficos e tabela de `Class`, `Category` e `Family`. | 2 |
| US-03 | Como cientista de dados, quero tratar hexadecimais e categorias sem perder informação. | P0 | Regras de conversão e colunas finais documentadas. | 5 |
| US-04 | Como cientista de dados, quero evitar leakage de hashes repetidos. | P0 | Nenhuma hash partilhada entre treino e teste; conflitos reportados. | 5 |
| US-05 | Como analista, quero analisar relações entre features e classe. | P0 | EDA bivariada, testes e interpretação das limitações. | 5 |
| US-06 | Como cientista de dados, quero medir correlações Pearson/Spearman. | P1 | Heatmaps e pares acima do limiar documentados. | 3 |
| US-07 | Como cientista de dados, quero avaliar assimetria e outliers. | P1 | Skewness, kurtosis e IQR apresentados sem remoção automática. | 3 |
| US-08 | Como equipa, queremos um baseline reproduzível. | P1 | Pipeline, split, seed e métricas guardados. | 5 |
| US-09 | Como analista SOC, quero otimizar recall de malware. | P1 | Limiar justificado e matriz de confusão apresentada. | 5 |
| US-10 | Como analista, quero explicar uma previsão. | P2 | Importância de features ou explicação local disponível. | 5 |
| US-11 | Como equipa, queremos classificar a categoria de malware. | P2 | Modelo multiclasse e macro-F1 reportados. | 5 |
| US-12 | Como equipa, queremos um relatório final reproduzível. | P0 | Método, resultados, riscos e próximos passos revistos. | 3 |

## Estado no fim do Sprint 2

Concluídas: US-01 a US-09 e US-12, no âmbito de Data Understanding, EDA,
Data Preparation e baseline. US-10 e US-11 permanecem no backlog para
explicabilidade e classificação multiclasse.

## Definição de pronto

Uma user story está pronta quando o código/notebook corre, os resultados são
reproduzíveis, existe evidência (tabela ou gráfico), as limitações estão
documentadas e outro elemento consegue repetir o procedimento.

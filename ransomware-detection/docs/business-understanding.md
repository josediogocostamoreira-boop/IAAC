# Business Understanding

## Problema

Equipas de segurança precisam de uma forma rápida e consistente de sinalizar
ficheiros potencialmente maliciosos. A análise manual é dispendiosa, pode
atrasar a resposta e não escala para grandes volumes. O projeto pretende
construir uma base de dados analítica e um classificador que apoie a triagem de
ficheiros, sem substituir a análise humana.

## Objetivo de negócio

Reduzir o tempo de triagem e priorizar amostras com maior probabilidade de
serem malware/ransomware, mantendo um nível de falsos negativos suficientemente
baixo para não deixar ameaças passar despercebidas.

## Objetivos analíticos

1. Criar um classificador binário para `Class` (`Benign`/`Malware`).
2. Medir precision, recall, F1 e ROC-AUC, dando prioridade ao recall de malware.
3. Explorar `Category` e `Family` como tarefas multiclasse posteriores.
4. Produzir um pipeline reproduzível de preparação de dados.
5. Identificar limitações, fuga de dados e condições em que o modelo não deve
   ser usado.

## Stakeholders e utilizadores

| Stakeholder | Necessidade |
|---|---|
| Analista SOC | Receber uma prioridade/alerta explicável |
| Equipa de resposta | Reduzir o tempo até à investigação |
| Engenharia de dados | Pipeline reprodutível e auditável |
| Gestão | Métricas de desempenho e risco compreensíveis |
| Equipa académica | Método, evidência e documentação reproduzíveis |

## Critérios de sucesso

- O pipeline corre a partir de uma instalação limpa usando o `requirements.txt`.
- O conjunto de teste é separado sem duplicar o mesmo artefacto entre treino e
  teste.
- O relatório inclui matriz de confusão, recall, precision, F1 e ROC-AUC.
- Todas as transformações aprendidas (imputação, encoding, escala) são
  ajustadas apenas no treino.
- O sistema sinaliza explicitamente casos fora do domínio e não apresenta uma
  previsão como decisão definitiva.

## Restrições e riscos

- Os dados são características estáticas/observadas de ficheiros e podem não
  representar todas as famílias ou versões atuais.
- A repetição de MD5 pode causar sobre-estimativa se não for tratada.
- Falsos negativos têm custo elevado; o limiar não deve ser escolhido apenas
  para maximizar accuracy.
- Hashes identificam amostras, mas não são características úteis para
  generalização e devem ser excluídos do modelo.
- O resultado é apoio à decisão, não prova de que um ficheiro é seguro.

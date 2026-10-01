# Sprint 3 — Supervised Learning

**Duração prevista:** duas semanas
**Datas reais:** preencher com a equipa
**Equipa e papéis:** preencher nomes de Product Owner, Scrum Master e
elementos responsáveis pelas tarefas.

## Sprint Backlog

**Objetivo:** comparar classificadores supervisionados para deteção binária de
malware e avaliar o modelo selecionado sem usar o conjunto de teste para a
seleção.

| Ordem | User story / tarefa | Prioridade | Estado | Evidência |
|---:|---|---|---|---|
| 1 | US-13 — definir os splits de treino, validação e teste | P1 | Concluído | `results/supervised_learning_report.json` |
| 2 | Implementar pipelines para Logistic Regression, Decision Tree, k-NN, Naive Bayes e SVM | P1 | Concluído | `src/supervised_learning.py` |
| 3 | Implementar ensembles: AdaBoost, Gradient Boosting, Random Forest e Extra Trees | P1 | Concluído | `src/supervised_learning.py` |
| 4 | Comparar métricas na validação e selecionar o modelo | P1 | Concluído | `results/supervised_model_comparison.csv` |
| 5 | Avaliar o modelo escolhido uma vez no teste e guardar a matriz de confusão | P1 | Concluído | `results/supervised_learning_report.json`, `results/supervised_confusion_matrix.png` |
| 6 | Registar a decisão sobre regressão e a extensão XGBoost | P2 | Concluído | `docs/supervised-learning.md` |

**Fora do sprint:** XGBoost, porque a dependência opcional não estava
instalada; regressão, porque o dataset não contém um alvo contínuo adequado.
Deployment, extração automática de características de executáveis e sistema
multiagente ficam para sprints posteriores.

## Sprint Planning

1. **Preparar dados e splits** — começar por este passo para impedir data
   leakage; deduplicar por MD5, depois criar treino/validação/teste
   estratificados.
2. **Implementar os pipelines** — usar imputação, encoding e escala dentro dos
   pipelines para que sejam ajustados apenas nos dados de treino.
3. **Comparar classificadores** — aplicar as mesmas métricas e os mesmos
   splits, tornando os resultados comparáveis.
4. **Selecionar na validação** — ordenar por recall de Malware e usar precision
   e F1 como desempate; não consultar o teste para escolher o modelo.
5. **Avaliar no teste e documentar** — reportar métricas finais, matriz de
   confusão, limitações e decisões.

**Critério de sucesso:** benchmark reproduzível, sem leakage entre artefactos,
seleção baseada na validação e avaliação final reservada ao teste.

## Daily Scrum — simulação para apresentação

> Esta é uma simulação académica baseada no trabalho implementado; não é um
> registo de reuniões reais. Substituir os papéis pelos nomes da equipa e
> adaptar a atualização ao que cada pessoa realmente realizou.

| Elemento / papel | Ontem fiz | Hoje farei | Impedimentos |
|---|---|---|---|
| Elemento responsável por dados | Limpei e dedupliquei por MD5; defini splits estratificados. | Rever contagens e confirmar separação dos conjuntos. | Nenhum impedimento técnico conhecido. |
| Elemento responsável por modelos | Implementei os pipelines dos classificadores do sprint. | Comparar métricas de validação e rever scores SVM. | XGBoost não instalado; ficou opcional e fora do benchmark executado. |
| Elemento responsável por documentação/integração | Registei resultados, limitações e decisões. | Preparar demonstração e recolher feedback do PO. | Feedback/aceitação do PO ainda por registar. |

## Sprint Review

**Data da review:** a preencher
**Participantes / Product Owner:** a preencher

- **Incremento demonstrado:** benchmark executável em
  `src/supervised_learning.py`; comparação CSV; relatório JSON; matriz de
  confusão.
- **User stories/tarefas concluídas:** US-13 e tarefas S3-01 a S3-08,
  tecnicamente concluídas conforme os artefactos disponíveis.
- **Dados usados:** 13.886 amostras únicas depois da limpeza; split
  estratificado 60% treino, 20% validação e 20% teste.
- **Modelos comparados:** 11 classificadores. XGBoost não foi executado.
- **Seleção:** Gradient Boosting foi selecionado na validação pelo maior
  recall de Malware, com precision e F1 como desempate.
- **Avaliação final no teste:** accuracy 99,14%; precision de Malware 98,67%;
  recall de Malware 99,55%; F1 99,11%; ROC-AUC 99,87%; PR-AUC 99,87%.
- **Decisão/feedback do PO:** ainda não registado; confirmar aceitação na review
  real antes de fechar formalmente o sprint.
- **Itens devolvidos ao backlog:** XGBoost opcional; deployment; extração de
  features diretamente de `.exe`; classificação multiclasse; integração
  multiagente.

## Sprint Retrospective

> Síntese inicial para discussão da equipa. Confirmar e ajustar após a
> retrospectiva real; não representa feedback recolhido de participantes.

| Continuar | Parar | Começar |
|---|---|---|
| Usar pipelines do scikit-learn e splits reproduzíveis. | Selecionar modelos consultando o conjunto de teste. | Registar responsáveis, datas, decisões e impedimentos nas reuniões. |
| Deduplicar por MD5 e reportar limitações dos dados. | Tratar score de decisão do SVM como probabilidade calibrada. | Recolher feedback do PO e validar o modelo com dados externos. |

### Ações para o próximo sprint

| Ação proposta | Responsável | Prazo |
|---|---|---|
| Validar os resultados e critérios de aceitação com o PO | A atribuir | Próxima review |
| Testar generalização em dados externos e rever possíveis fontes de leakage | A atribuir | Próximo sprint |
| Escolher entre deployment, classificação multiclasse e explicabilidade | Equipa/PO | Próximo Sprint Planning |
| Decidir se vale a pena instalar e avaliar XGBoost | A atribuir | Próximo sprint |

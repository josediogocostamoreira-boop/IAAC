# Sprint 4 — Multi-dataset, notebook e deployment

**Estado:** backlog e implementação técnica propostos; preencher as datas,
participantes, prioridades e responsáveis com a equipa. Só `ransom.csv` está
disponível nesta pasta.

**Objetivo:** demonstrar o fluxo de classificação e deployment para o dataset
disponível, mantendo SCRUM e CRISP-ML explícitos e preparando a integração dos
restantes datasets aprovados quando forem entregues.

| Prioridade | Tarefa | Critério de aceitação | Estado |
|---|---|---|---|
| P1 | Comparar classificadores por dataset | Benchmark scikit-learn seleciona por validação e reserva teste para avaliação | Implementado para ransomware |
| P1 | Guardar os pipelines e schema | Classificadores finais ficam em `models/<dataset>/` | Implementado para ransomware |
| P1 | Integrar CLI e API de deployment | Inferência usa o modelo selecionado e valida features | Implementado para ransomware |
| P1 | Criar notebook e módulos Python | Notebook invoca todos os modelos e funções auxiliares | Implementado para ransomware |
| P2 | Integrar agente generativo local | Agente Transformers participa no fluxo; saídas fora do token aprovado são rejeitadas | Validado no notebook; relatório gerado |
| P2 | Integrar alternativa CrewAI | Crew sequencial usa o mesmo modelo local através de API localhost e valida a saída | Validado no notebook; relatório gerado |
| P2 | Documentar arquitetura e caso de uso | Três diagramas descrevem pipelines e agentes por dataset | Implementado |
| P1 | Registar cerimónias SCRUM reais | Datas, participantes, decisões e feedback efetivamente recolhidos | Pendente da equipa |
| P1 | Confirmar grupo e fontes de dados | 3–4 elementos e um dataset aprovado por elemento | Pendente da equipa/docente |
| P1 | Executar pipelines dos restantes datasets | Cada CSV aprovado tem schema, treino, teste e deployment próprios | Bloqueado: ficheiros/rótulos não disponíveis |

**Definition of Done:** critérios técnicos testados, outputs reproduzíveis e
review real registada. Não marcar como terminado qualquer evento de SCRUM que
não tenha ocorrido.

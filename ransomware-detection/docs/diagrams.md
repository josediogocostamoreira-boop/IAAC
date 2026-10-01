# Arquitetura multiagente e caso de uso

Os diagramas mostram a arquitetura pretendida por dataset aprovado. Nesta
branch só está configurado `ransom.csv`; os datasets dos restantes elementos
devem ser adicionados depois de recebidos e validados.

## Pipeline CRISP-ML por dataset e armazenamento

```mermaid
flowchart LR
    D1[Dataset aprovado 1] --> P1[Pipeline CRISP-ML 1]
    D2[Dataset aprovado 2] --> P2[Pipeline CRISP-ML 2]
    DN[Dataset aprovado N] --> PN[Pipeline CRISP-ML N]
    P1 --> M1[(models / dataset-1)]
    P2 --> M2[(models / dataset-2)]
    PN --> MN[(models / dataset-N)]
    P1 --> R1[(results / dataset-1)]
    P2 --> R2[(results / dataset-2)]
    PN --> RN[(results / dataset-N)]
    M1 --> CA[Agente classificador por dataset]
    M2 --> CA
    MN --> CA
    R1 --> MA[Agente de métricas]
    R2 --> MA
    RN --> MA
    CA --> GA[Agente generativo local Hugging Face]
    MA --> GA
    GA --> OUT[Relatório assistido para revisão humana]
```

## Multiagente local e alternativa CrewAI

```mermaid
flowchart TB
    INPUT[Features pré-extraídas por dataset] --> SELECT[Selecionar modelo pelo benchmark]
    SELECT --> CLASSIFIER[Agente classificador]
    METRICS[JSON de avaliação e métricas] --> ANALYST[Agente analista]
    CLASSIFIER --> FACTS[Factos JSON verificados]
    ANALYST --> FACTS
    FACTS --> PY[Orquestrador Python]
    PY --> HF[Agente generativo Transformers local]
    FACTS --> CREW[CrewAI sequential crew]
    CREW --> CA[Agente analista CrewAI]
    CA --> CR[Agente redator CrewAI]
    CR --> LOCAL[API OpenAI-compatible localhost]
    LOCAL --> HF
    HF --> REPORT[Relatório factual assistido]
```

## Caso de uso para os datasets do grupo

```mermaid
sequenceDiagram
    actor Equipa as Elementos do grupo (3–4)
    participant DS as Datasets aprovados
    participant Pipe as Pipelines CRISP-ML independentes
    participant Models as Diretório models por dataset
    participant Agents as Agentes Python ou CrewAI
    actor SOC as Analista de cibersegurança
    Equipa->>DS: Regista um dataset aprovado por elemento
    DS->>Pipe: Valida target, features, qualidade e split sem leakage
    Pipe->>Pipe: Compara classificadores scikit-learn por dataset
    Pipe->>Models: Guarda todos os classificadores e o schema
    SOC->>Agents: Solicita relatório de triagem
    Agents->>Models: Carrega o melhor classificador de cada dataset
    Agents->>Agents: Cruza previsões com métricas verificadas
    Agents-->>SOC: Relatório assistido com limitações e revisão humana
```

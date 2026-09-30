# Diagramas do sistema multiagente

Os diagramas Mermaid abaixo podem ser visualizados diretamente no GitHub.

## 1. Arquitetura de deployment

```mermaid
flowchart LR
    CSV[CSV de sessões] --> CLI[run_analysis.py]
    CLI --> A[AgenteAnalista]
    A --> P[Preparação: encoding + scaler]
    P --> M[(Random Forest\nmelhor_modelo.pkl)]
    M --> R[Resultado: ataque, confiança, risco]
    R --> G[AgenteRelator]
    G --> O[Relatório de incidente]
```

## 2. Sequência de análise de uma sessão

```mermaid
sequenceDiagram
    participant U as Operador
    participant C as CLI
    participant A as AgenteAnalista
    participant M as Modelo
    participant R as AgenteRelator
    U->>C: CSV / sessão
    C->>A: analisar_sessao(dados brutos)
    A->>A: validar, codificar e normalizar
    A->>M: predict + predict_proba
    M-->>A: classe e probabilidades
    A-->>R: diagnóstico e indicadores
    R-->>C: relatório e recomendação
    C-->>U: resultado
```

## 3. Caso de uso SOC

```mermaid
flowchart TD
    SOC[Analista SOC] -->|carrega sessões| S[Sistema de deteção]
    S -->|tráfego normal| MON[Monitorização contínua]
    S -->|ameaça detetada| INC[Relatório de incidente]
    INC --> BLOCK[Bloquear IP]
    INC --> REV[Revogar credenciais]
    INC --> ISO[Isolar recurso e analisar]
```

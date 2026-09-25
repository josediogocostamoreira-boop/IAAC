# Sprint 2 — Data Preparation

**Objetivo:** transformar o dataset limpo numa base preparada para modelação,
com decisões reproduzíveis sobre qualidade, split, features e balanceamento.

| ID | Tarefa | User story | Evidência | Estado |
|---|---|---|---|---|
| S2-01 | Validar limpeza, hashes e conflitos | US-04 | `preparation_stats.json` | Done |
| S2-02 | Medir missing values e definir imputação | US-03 | `data_preparation_report.json` | Done |
| S2-03 | Medir outliers por IQR e skewness | US-07 | `feature_quality.csv` | Done |
| S2-04 | Criar split estratificado reproduzível | US-04 | split no relatório | Done |
| S2-05 | Medir constantes e correlações | US-06 | `high_correlation_pairs.csv` | Done |
| S2-06 | Aplicar escala no pipeline sem leakage | US-03 | `data_preprocessing.py` | Done |
| S2-07 | Avaliar candidatos de engenharia de features | US-07 | candidatos `log1p` | Done |
| S2-08 | Documentar extração e limites do dataset | US-12 | `data-preparation.md` | Done |
| S2-09 | Tratar desbalanceamento na modelação | US-09 | `class_weight='balanced'` | Done |

## Critérios de aceitação

- O relatório pode ser recriado com um único comando.
- Nenhuma transformação aprendida usa o conjunto de teste.
- Missing values são imputados no pipeline, nunca com estatísticas globais.
- Outliers são medidos e justificados; não são removidos silenciosamente.
- O split é estratificado e usa `random_state=42`.
- A estratégia de balanceamento é explícita e comparável.
- As limitações da extração a partir de `.exe` estão registadas.

## Review e retrospectiva

Na Sprint Review devem ser demonstrados o relatório JSON, a tabela de
qualidade e as decisões de preparação. Na retrospectiva devem ser preenchidos
os pontos continuar/parar/começar no template SCRUM.

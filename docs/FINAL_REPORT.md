# Intrusion Detection - Relatório Final

## Resumo
Conduzimos EDA, preparação de dados e testes de modelos baseline (RandomForest e XGBoost) usando uma amostra do dataset IoT Intrusion Detection.

## Artefatos principais
- `notebooks/EDA_Data_Understanding.ipynb` — EDA inicial
- `notebooks/Modeling_Baseline.ipynb` — passos de modelagem
- `src/data_preparation.py` — script de limpeza e preparação
- `src/run_eda.py` — script para gerar outputs de EDA
- `src/modeling.py`, `src/train_xgb.py` — scripts de treino
- `outputs/` — resultados do EDA
- `models/` — modelos e relatórios (.joblib, .csv)

## Resultados
- Dataset: `archive/final_dataset.csv` (1,175,222 linhas; 24 colunas)
- RandomForest (sample 100k): accuracy ~1.00 (ver `models/rf_report.csv`)
- XGBoost (sample 50k): accuracy ~1.00 (ver `models/xgb_report.csv`)

> Observação: resultados perfeitos podem indicar dados balanceados ou leakage; recomendo revisar features e validação temporal.

## Próximos passos recomendados
- Rever features para identificar possível leakage.
- Implementar validação temporal / K-fold estratificado.
- Testar pipelines com menos features (feature importance) e reduzir dimensionalidade.
- Construir dashboard com métricas e exemplos de deteções.
## Feitas agora
- Feature selection automática (top 15) e treino final RandomForest com features selecionadas.
- Arquivos gerados: `models/selected_features.json`, `models/feature_importances.csv`, `models/rf_selected.joblib`, `models/rf_selected_report.csv`.


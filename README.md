# Cybersecurity Intrusion Detection System (CRISP-ML & SCRUM)

Projeto de Machine Learning para deteção automatizada de intrusões de rede e relatórios de cibersegurança.

## 🛠️ Estrutura do Projeto
- `data/`: Dataset de tráfego de rede (`cybersecurity_intrusion_data.csv`).
- `scripts/`:
  - `data_prep.py`: Limpeza, tratamento de outliers (IQR), One-Hot Encoding, StandardScaler e SelectKBest/PCA.
  - `train.py`: Treino de 12 classificadores e 5 regressores.
  - `evaluate.py`: Métricas de desempenho (F1-Score, Precision, Recall, ROC-AUC, MAE, RMSE, R²), Validação Cruzada e Matrizes de Confusão.
  - `agent.py`: Agente Inteligente de Cibersegurança para relatórios automáticos.
- `main.py`: Pipeline principal de execução.
- `docs/`: Documentação de gestão (ML Canvas e Atas SCRUM).

## 🚀 Como Executar
```bash
python main.py
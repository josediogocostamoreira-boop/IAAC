# 🛡️ Cybersecurity Intrusion Detection System (CRISP-ML & SCRUM)

> Sistema Inteligente de Deteção de Intrusões e Análise de Risco em Redes com Aprendizagem Supervisionada e Relatórios Automáticos.

---

## 📌 Índice
- [Visão Geral](#-visão-geral)
- [Metodologia & Arquitetura (CRISP-ML)](#-metodologia--arquitetura-crisp-ml)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Modelos Treinados](#-modelos-treinados)
- [Gestão do Projeto (SCRUM)](#-gestão-do-projeto-scrum)
- [Instalação e Execução](#-instalação-e-execução)
- [Documentação do Projeto](#-documentação-do-projeto)

---

## 📖 Visão Geral
Este projeto desenvolve uma solução ponta-a-ponta de aprendizagem automática (*Machine Learning*) direcionada para a cibersegurança. Utiliza **12 algoritmos de classificação** para detetar tráfego malicioso e **5 algoritmos de regressão** para estimar métricas contínuas de rede, integrando um **Agente Inteligente de Cibersegurança** para a geração automática de diagnósticos de risco.

---

## ⚙️ Metodologia & Arquitetura (CRISP-ML)

O fluxo de trabalho foi estruturado de acordo com o ciclo de vida **CRISP-ML**:

1. **Business & Data Understanding**: Análise descritiva, avaliação de *skewness*/*kurtosis* e cálculo de matrizes de correlação (Pearson e Spearman).
2. **Data Preparation**:
   - Preenchimento de valores ausentes em `encryption_used`.
   - Limpeza e limitação de *outliers* através do método **IQR Capping**.
   - Codificação categórica via **One-Hot Encoding** e normalização com **StandardScaler**.
3. **Model Building & Cross-Validation**: Treino supervisionado com **Stratified 5-Fold Cross-Validation**.
4. **Model Evaluation & Selection**: Seleção automática dos melhores modelos com base no **F1-Score / ROC-AUC** (Classificação) e **R² / MAE** (Regressão).
5. **Deployment & Agent Integration**: Agente de IA (`CybersecurityReportingAgent`) para diagnósticos e relatórios de segurança.

---

## 📁 Estrutura do Repositório

```text
Projeto_IAAC/
│
├── data/
│   └── cybersecurity_intrusion_data.csv   # Dataset de tráfego de rede
├── docs/
│   ├── ML_Canvas.pdf                     # Machine Learning Canvas
│   └── Atas_Scrum.pdf                    # Atas de Reuniões e Gestão SCRUM
├── notebook/
│   ├── 01_Data_Understanding.ipynb
│   ├── 02_Data_Preparation.ipynb
│   ├── 03_Supervised_Learning.ipynb
│   └── 04_Model_Evaluation_Optimization.ipynb
├── scripts/
│   ├── data_prep.py                      # Limpeza, IQR capping, encoding e scaling
│   ├── train.py                          # Treino dos 17 modelos supervisionados
│   ├── evaluate.py                       # Matrizes de confusão e extração de métricas
│   └── agent.py                          # Agente Inteligente de Cibersegurança
├── requirements.txt                      # Dependências do projeto
├── main.py                               # Pipeline principal de execução
└── README.md                             # Documentação principal
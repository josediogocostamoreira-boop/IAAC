"""Sistema multiagente local: previsão, risco e relatório."""
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
try:
    from .train import load_models
except ImportError:
    from train import load_models

@dataclass
class Prediction:
    label: int
    probability: float
    model_name: str

class ClassificationAgent:
    def __init__(self, models_path="models/trained_models.pkl", model_name=None):
        models = load_models(models_path)
        metrics_path = Path(models_path).with_name("model_metrics.csv")
        if model_name is None and metrics_path.exists():
            model_name = pd.read_csv(metrics_path).iloc[0]["model"]
        self.model_name = model_name or "Random Forest"
        self.model = models.get(self.model_name)
        if self.model is None: self.model_name, self.model = next(iter(models.items()))
    def predict(self, features):
        probability = float(self.model.predict_proba(features)[0, 1])
        return Prediction(int(probability >= .5), probability, self.model_name)

class RiskAgent:
    def assess(self, prediction):
        p = prediction.probability
        if p >= .80: return "CRÍTICO", "Bloquear a origem, isolar a sessão e abrir incidente no SOC."
        if p >= .50: return "ALTO", "Aplicar autenticação reforçada e investigar a sessão."
        if p >= .25: return "MÉDIO", "Manter a sessão sob monitorização reforçada."
        return "BAIXO", "Manter monitorização normal e registar o evento."

class ReportingAgent:
    def generate(self, prediction, risk, action):
        status = "INTRUSÃO PROVÁVEL" if prediction.label else "TRÁFEGO PROVAVELMENTE NORMAL"
        return f"RELATÓRIO AUTOMÁTICO DE CIBERSEGURANÇA\nEstado: {status}\nModelo: {prediction.model_name}\nProbabilidade de intrusão: {prediction.probability:.1%}\nNível de risco: {risk}\nRecomendação: {action}"

class CybersecurityReportingAgent:
    """Orquestrador dos três agentes, usado por notebook e deployment."""
    def __init__(self, model_path="models/trained_models.pkl", model_name=None):
        self.classifier, self.risk, self.reporter = ClassificationAgent(model_path, model_name), RiskAgent(), ReportingAgent()
    def analyze_session_and_generate_report(self, sample_data_prep):
        prediction = self.classifier.predict(sample_data_prep); risk, action = self.risk.assess(prediction)
        return self.reporter.generate(prediction, risk, action)

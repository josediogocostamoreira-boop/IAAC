import pickle
import pandas as pd

class CybersecurityReportingAgent:
    """
    Agente Generativo/Analista de Cibersegurança que interage com o melhor 
    modelo de classificação e elabora relatórios de diagnóstico.
    """
    def __init__(self, model_path='../models/trained_models.pkl'):
        with open(model_path, 'rb') as f:
            models = pickle.load(f)
            self.model = models['Random Forest'] # Melhor modelo identificado
            
    def analyze_session_and_generate_report(self, sample_data_prep):
        """
        Gera o diagnóstico de segurança com base na previsão do modelo.
        """
        prediction = self.model.predict(sample_data_prep)[0]
        prob = self.model.predict_proba(sample_data_prep)[0][1]
        
        status = "AMEAÇA DETETADA (INTRUSÃO)" if prediction == 1 else "TRÁFEGO NORMAL"
        risk_level = "CRÍTICO" if prob > 0.8 else ("MÉDIO" if prob > 0.5 else "BAIXO")
        
        report = f"""
        =====================================================
        RELATÓRIO AUTOMÁTICO DE CIBERSEGURANÇA (SISTEMA MULTIAGENTE)
        =====================================================
        Status da Sessão: {status}
        Probabilidade de Ataque: {prob*100:.2f}%
        Nível de Risco: {risk_level}
        
        Recomendação do Agente:
        {'[AÇÃO IMEDIATA] Bloquear IP de origem, isolar sessão e notificar equipa de SOC.' if prediction == 1 else '[OK] Sessão limpa. Manter monitorização contínua.'}
        =====================================================
        """
        return report
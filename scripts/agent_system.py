import joblib
import pandas as pd

class AgenteAnalista:
    """
    Agente 1: Carrega o melhor modelo treinado (.pkl) e faz a classificação da sessão.
    """
    def __init__(self, model_path='../models/melhor_modelo.pkl', scaler_path='../models/scaler.pkl'):
        self.modelo = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        
    def analisar_sessao(self, dados_sessao_df):
        previsao = self.modelo.predict(dados_sessao_df)[0]
        probabilidade = self.modelo.predict_proba(dados_sessao_df)[0][previsao]
        
        return {
            'e_ataque': bool(previsao == 1),
            'diagnostico': "AMEAÇA/ATAQUE DETETADO" if previsao == 1 else "TRÁFEGO NORMAL",
            'confianca': round(probabilidade * 100, 2)
        }


class AgenteRelator:
    """
    Agente 2: Agente Generativo que elabora relatórios de cibersegurança.
    """
    def gerar_relatorio(self, dados_sessao_dict, resultado_analise):
        status = resultado_analise['diagnostico']
        confianca = resultado_analise['confianca']
        
        logins_falhados = dados_sessao_dict.get('failed_logins', 'N/A')
        reputacao_ip = dados_sessao_dict.get('ip_reputation_score', 'N/A')
        duracao = dados_sessao_dict.get('session_duration', 'N/A')
        
        relatorio = f"""
============================================================
           RELATÓRIO DE INCIDENTE DE CIBERSEGURANÇA
============================================================
DIAGNÓSTICO FINAL : {status}
GRAU DE CONFIANÇA : {confianca}%

[ANÁLISE DE INDICADORES DE RISCO (IOCs)]
- Tentativas de Login Falhadas : {logins_falhados}
- Score de Reputação do IP     : {reputacao_ip}
- Duração da Sessão (seg)     : {duracao}

[PARECER TÉCNICO E RECOMENDAÇÃO DE AÇÃO]
"""
        if resultado_analise['e_ataque']:
            relatorio += (
                "Atenção: A sessão apresentou padrões anómalos compatíveis com uma intrusão.\n"
                "Ação Recomendada: Bloquear imediatamente o IP no Firewall, revogar as credenciais "
                "da sessão ativa e isolar os recursos afetados para análise forense."
            )
        else:
            relatorio += (
                "A sessão apresentou comportamento dentro dos parâmetros normais de tráfego.\n"
                "Ação Recomendada: Nenhuma ação corretiva é necessária. Manter a monitorização contínua."
            )
            
        return relatorio
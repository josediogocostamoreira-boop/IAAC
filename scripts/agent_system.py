"""Sistema multiagente para deteção e reporte de intrusões."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "melhor_modelo.pkl"
DEFAULT_SCALER_PATH = PROJECT_ROOT / "models" / "scaler.pkl"


class AgenteAnalista:
    """Carrega o modelo e classifica sessões de rede brutas ou preparadas."""

    def __init__(self, model_path: str | Path = DEFAULT_MODEL_PATH,
                 scaler_path: str | Path = DEFAULT_SCALER_PATH) -> None:
        self.modelo = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.feature_names = list(getattr(self.modelo, "feature_names_in_", []))
        if not self.feature_names:
            raise ValueError("O modelo não contém nomes de features; volte a treiná-lo com um DataFrame pandas.")

    def preparar_sessao(self, dados_sessao: pd.DataFrame | Mapping[str, Any]) -> pd.DataFrame:
        """Converte sessões brutas para as features esperadas pelo modelo."""
        if isinstance(dados_sessao, Mapping):
            dados = pd.DataFrame([dados_sessao])
        elif isinstance(dados_sessao, pd.DataFrame):
            dados = dados_sessao.copy()
        else:
            raise TypeError("dados_sessao deve ser um DataFrame ou um dicionário.")

        if set(dados.columns) == set(self.feature_names):
            return dados.reindex(columns=self.feature_names)

        dados = dados.drop(columns=["session_id", "attack_detected"], errors="ignore")
        if dados.empty:
            raise ValueError("A sessão não contém campos para análise.")
        texto = dados.select_dtypes(include=["object", "string", "category"]).columns.tolist()
        dados[texto] = dados[texto].fillna("Desconhecido")
        dados = pd.get_dummies(dados, columns=texto, drop_first=True)
        dados = dados.reindex(columns=self.feature_names, fill_value=0)

        numeric_features = list(getattr(self.scaler, "feature_names_in_", []))
        missing_numeric = [name for name in numeric_features if name not in dados.columns]
        if missing_numeric:
            raise ValueError(f"Features numéricas em falta: {', '.join(missing_numeric)}")
        for column in numeric_features:
            dados[column] = pd.to_numeric(dados[column], errors="raise")
        dados[numeric_features] = self.scaler.transform(dados[numeric_features])
        return dados

    def analisar_sessao(self, dados_sessao: pd.DataFrame | Mapping[str, Any]) -> dict[str, Any]:
        """Devolve diagnóstico, confiança e probabilidade de ataque."""
        dados_preparados = self.preparar_sessao(dados_sessao)
        previsao = int(self.modelo.predict(dados_preparados)[0])
        probabilidades = self.modelo.predict_proba(dados_preparados)[0]
        classes = list(self.modelo.classes_)
        prob_ataque = float(probabilidades[classes.index(1)]) if 1 in classes else float(probabilidades[previsao])
        return {
            "e_ataque": previsao == 1,
            "diagnostico": "AMEAÇA/ATAQUE DETETADO" if previsao == 1 else "TRÁFEGO NORMAL",
            "confianca": round(float(probabilidades[classes.index(previsao)]) * 100, 2),
            "probabilidade_ataque": round(prob_ataque * 100, 2),
        }


class AgenteRelator:
    """Produz relatórios legíveis a partir do diagnóstico do analista."""

    def gerar_relatorio(self, dados_sessao: Mapping[str, Any], resultado_analise: Mapping[str, Any]) -> str:
        status = resultado_analise["diagnostico"]
        confianca = resultado_analise["confianca"]
        prob_ataque = resultado_analise["probabilidade_ataque"]
        severidade = "ALTA" if prob_ataque >= 80 else "MÉDIA" if prob_ataque >= 50 else "BAIXA"
        relatorio = f"""
============================================================
           RELATÓRIO DE INCIDENTE DE CIBERSEGURANÇA
============================================================
DIAGNÓSTICO FINAL : {status}
GRAU DE CONFIANÇA : {confianca}%
RISCO DE ATAQUE   : {prob_ataque}% ({severidade})

[ANÁLISE DE INDICADORES DE RISCO (IOCs)]
- ID da Sessão                  : {dados_sessao.get('session_id', 'N/A')}
- Tentativas de Login Falhadas  : {dados_sessao.get('failed_logins', 'N/A')}
- Score de Reputação do IP      : {dados_sessao.get('ip_reputation_score', 'N/A')}
- Duração da Sessão (seg)       : {dados_sessao.get('session_duration', 'N/A')}
- Acesso em horário invulgar    : {dados_sessao.get('unusual_time_access', 'N/A')}

[PARECER TÉCNICO E RECOMENDAÇÃO DE AÇÃO]
"""
        if resultado_analise["e_ataque"]:
            relatorio += ("A sessão apresentou padrões anómalos compatíveis com uma intrusão.\n"
                          "Ação recomendada: bloquear o IP, revogar credenciais da sessão ativa "
                          "e isolar os recursos afetados para análise forense.")
        else:
            relatorio += ("A sessão apresentou comportamento dentro dos parâmetros normais.\n"
                          "Ação recomendada: manter a monitorização contínua.")
        return relatorio.strip()

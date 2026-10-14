import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Criar pasta docs caso não exista
os.makedirs("docs", exist_ok=True)

# 1. Gerar docs/ML_Canvas.pdf
doc_canvas = SimpleDocTemplate("docs/ML_Canvas.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story_canvas = []

title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#1A365D'))
body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, leading=12)

story_canvas.append(Paragraph("Machine Learning Canvas - Deteção de Intrusão", title_style))
story_canvas.append(Spacer(1, 15))

canvas_data = [
    [Paragraph("<b>Proposta de Valor</b>", body_style), Paragraph("Deteção automática em tempo real de tentativas de intrusão em redes para reforço de segurança do SOC.", body_style)],
    [Paragraph("<b>Objetivo de Negócio</b>", body_style), Paragraph("Reduzir MTTR (Tempo Médio de Resposta) e mitigar Falsos Negativos em acessos não autorizados.", body_style)],
    [Paragraph("<b>Fonte de Dados</b>", body_style), Paragraph("Logs de tráfego de rede e sessões (9.537 registos, 11 atributos).", body_style)],
    [Paragraph("<b>Tarefas de ML</b>", body_style), Paragraph("Classificação Binária (Ataque: 0/1) e Regressão Contínua (Tempo de Sessão).", body_style)],
    [Paragraph("<b>Métricas Offline</b>", body_style), Paragraph("F1-Score, Precision, Recall, ROC-AUC, MSE, RMSE, R².", body_style)],
    [Paragraph("<b>Métricas Online</b>", body_style), Paragraph("Tempo de inferência < 100ms e taxa de aceitação dos pareceres do Agente.", body_style)]
]

t_canvas = Table(canvas_data, colWidths=[150, 350])
t_canvas.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
    ('PADDING', (0,0), (-1,-1), 8),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
story_canvas.append(t_canvas)
doc_canvas.build(story_canvas)

# 2. Gerar docs/Atas_Scrum.pdf
doc_scrum = SimpleDocTemplate("docs/Atas_Scrum.pdf", pagesize=letter)
story_scrum = []

story_scrum.append(Paragraph("Documentação de Gestão SCRUM & Backlog", title_style))
story_scrum.append(Spacer(1, 15))

scrum_text = """
<b>Product Backlog & User Stories (GitHub Projects)</b><br/><br/>
• <b>US-01 (EDA)</b>: Como Analista de SOC, quero gráficos de correlação de Pearson/Spearman.<br/>
• <b>US-02 (Data Prep)</b>: Como Engenheiro de ML, quero tratamento de outliers via IQR e imputação de nulos.<br/>
• <b>US-03 (Modeling)</b>: Como Cientista de Dados, quero treinar e avaliar classificadores e regressores.<br/>
• <b>US-04 (Agent)</b>: Como Gestor de Segurança, quero um agente generativo para relatórios automáticos.<br/><br/>
<b>Ata de Daily Scrum Meeting (21/09/2026)</b><br/>
• <i>O que foi feito ontem:</i> Imputação de nulos na variável encryption_used.<br/>
• <i>O que será feito hoje:</i> Criação de atributos rácio (failed_login_ratio).<br/>
• <i>Impedimentos:</i> Nenhum.<br/><br/>
<b>Ata de Sprint Review & Retrospective (30/09/2026)</b><br/>
• <i>Sprint Review:</i> Apresentação da pipeline 'main.py' com 17 modelos treinados.<br/>
• <i>Retrospective:</i> Manter estratégia de branches no GitHub e modularização em scripts.
"""

story_scrum.append(Paragraph(scrum_text, body_style))
doc_scrum.build(story_scrum)

print("✅ PDFs gerados com sucesso dentro da pasta 'docs/'!")
# Deteção de ransomware

Projeto de classificação de características extraídas de ficheiros para apoiar
a triagem de malware. O projeto não executa ficheiros `.exe`.

## Conteúdo principal

- [`ransom.csv`](./ransom.csv): dataset atualmente disponível.
- [`src/data_preprocessing.py`](./src/data_preprocessing.py): validação,
  preparação e deduplicação por MD5.
- [`src/supervised_learning.py`](./src/supervised_learning.py): benchmark
  scikit-learn, seleção por validação e avaliação num teste reservado.
- [`src/predict.py`](./src/predict.py): inferência para CSV e para todos os
  classificadores guardados.
- [`src/extract_features.py`](./src/extract_features.py): extração estática de
  features PE de executáveis `.exe` e de `.exe` dentro de arquivos ZIP.
- [`src/serve.py`](./src/serve.py): API HTTP local.
- [`src/agent_system.py`](./src/agent_system.py): agentes Python com modelo
  generativo Hugging Face executado localmente.
- [`src/run_crewai_agents.py`](./src/run_crewai_agents.py): alternativa
  multiagente com CrewAI.
- [`model-deployment.ipynb`](./model-deployment.ipynb): benchmark, inferência
  de todos os modelos guardados e uso dos agentes.
- [`docs/diagrams.md`](./docs/diagrams.md): arquitetura multiagente e caso de
  uso com múltiplos datasets.
- [`docs/sprint-4-backlog.md`](./docs/sprint-4-backlog.md): backlog SCRUM para
  integração e deployment.
- [`docs/sprint-4-template.md`](./docs/sprint-4-template.md): registo das
  cerimónias reais do Sprint 4.

## Preparar o ambiente

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Seleciona o kernel `.venv` ao abrir os notebooks.

## SCRUM e CRISP-ML

O projeto contém backlog e templates SCRUM em `docs/`. O backlog do Sprint 4
acompanha treino, integração, testes e deployment. Datas, participantes,
responsáveis, aprovação dos datasets e resultados de reuniões têm de ser
preenchidos com evidência real pela equipa.

As fases CRISP-ML e as decisões existentes estão documentadas em
`docs/business-understanding.md`, `docs/data-understanding.md`,
`docs/data-preparation.md` e `docs/supervised-learning.md`. O deployment local e
as suas limitações estão em `docs/deployment.md`.

## Treinar e guardar os classificadores

Gerar tabelas, testes estatísticos e visualizações EDA do roadmap:

```powershell
python src/roadmap_eda.py --data ransom.csv --output results/roadmap/eda
```

Treinar, selecionar e afinar:

```powershell
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware --cv-folds 3
```

O script compara 12 classificadores scikit-learn, escolhe o modelo por recall
de Malware na validação, afina-o com validação cruzada estratificada e usa o
teste apenas na avaliação final. A seleção e a engenharia de features são
aprendidas dentro dos folds. Todos os pipelines finais são guardados em
`models/ransomware/`; o modelo selecionado e o schema são usados pela
inferência. Para XGBoost, instala-o explicitamente e acrescenta
`--include-xgboost`.

## Aplicação gráfica Windows

Para criar uma aplicação gráfica com opções para selecionar o CSV, executar EDA,
gerar o relatório de preparação, treinar/afinar modelos, consultar métricas e
gráficos, fazer previsões, iniciar a API e gerir o bot Telegram:

```powershell
powershell -ExecutionPolicy Bypass -File build_windows.ps1
.\dist\RansomwareTrainer.exe
```

O executável deve ser usado com a pasta do projeto, incluindo `src/` e um CSV,
disponível junto do executável ou selecionado na interface. **Gerar EDA** e
**Relatório de preparação** criam evidência em `results/roadmap/`; **Treinar e
avaliar modelos** compara os classificadores, executa validação cruzada e
afinação de hiperparâmetros e guarda métricas e gráficos em `results/`. O
número de folds é configurável e XGBoost pode ser incluído como dependência
opcional. **Ver avaliação e gráficos** mostra o relatório do teste reservado e
a comparação dos modelos. Os botões de artefactos abrem os resultados de EDA e
preparação. Se o executável não encontrar `.venv`, **Instalar dependências**
cria esse ambiente com Python 3.13 e instala os requisitos do projeto.
Para usar o bot dentro da janela, seleciona **Instalar dependências Telegram**,
depois **Iniciar bot Telegram**. A janela pede o token do BotFather num campo
oculto e permite restringir o acesso a IDs Telegram. O token só é passado ao
processo filho; não é guardado em ficheiro nem apresentado no registo. Mantém
a aplicação aberta enquanto usas o bot. O botão correspondente permite pará-lo.

O botão **Extrair .exe/.zip** cria um CSV de features PE estáticas para um
executável `.exe` ou para os `.exe` contidos num arquivo ZIP. Depois, usa
**Fazer previsão** e escolhe o CSV criado.

A extração não executa os ficheiros. As features comportamentais (atividade de
rede, processos e registo) não estão disponíveis na análise estática; essas
colunas ficam em falta e são imputadas pelo modelo, pelo que a previsão pode
ser menos fiável do que nos dados originais. Outros formatos, como PDF, Office
ou imagens, não são suportados.

## Notebook e versão Python

Executa `model-deployment.ipynb` do início ao fim. O notebook chama os mesmos
módulos Python que a CLI, compara as previsões de todos os classificadores e
invoca a equipa multiagente selecionada.

```powershell
python -m unittest discover -s tests -v
```

A matriz técnica do roadmap e os comandos de reprodução estão em
[`docs/roadmap-technical-compliance.md`](./docs/roadmap-technical-compliance.md).

## Deployment do classificador

```powershell
python src/serve.py
```

Por omissão, o serviço só escuta em `127.0.0.1:8000`. O endpoint `POST
/predict` recebe JSON com features pré-extraídas. Consulta `docs/deployment.md`.

## Sistema multiagente opcional

Os agentes usam o modelo Hugging Face `HuggingFaceTB/SmolLM2-360M-Instruct`
localmente. O cache fica em `models/huggingface/`; nenhuma amostra é enviada a
um serviço externo. A versão CrewAI disponibiliza uma API local compatível com
OpenAI para usar o mesmo modelo.
As saídas livres do LLM não são publicadas diretamente: o relatório só aceita
o token `REVIEW_REQUIRED`, convertido numa nota controlada; qualquer resposta
fora do formato é marcada como rejeitada e omitida.

```powershell
python -m pip install -r requirements-ai.txt
python src/run_agents.py --input sample.csv --output reports/ransomware.md
python src/run_crewai_agents.py --input sample.csv --output reports/ransomware-crewai.md
```

## Bot Telegram

O bot opcional permite conversar localmente com o SmolLM2 e enviar `.exe`/`.zip`
para análise estática pelo classificador treinado. Instalação, configuração
segura do token do BotFather e utilização estão em
[`docs/telegram-bot.md`](./docs/telegram-bot.md).

## Limites que dependem da equipa

Atualmente só existe `ransom.csv`. Não é possível comprovar aqui a composição
de 3–4 elementos, a aprovação do docente nem treinar nos datasets dos outros
elementos sem receber os respetivos ficheiros e rótulos. Esses dados devem ser
validados e registados pela equipa antes de afirmar cobertura de todos os
datasets.

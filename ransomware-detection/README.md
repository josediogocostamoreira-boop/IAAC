# Deteção de ransomware

Projeto de classificação de características extraídas de ficheiros para apoiar
a triagem de malware. O deployment não executa nem analisa ficheiros `.exe`.

## Conteúdo principal

- [`ransom.csv`](./ransom.csv): dataset atualmente disponível.
- [`src/data_preprocessing.py`](./src/data_preprocessing.py): validação,
  preparação e deduplicação por MD5.
- [`src/supervised_learning.py`](./src/supervised_learning.py): benchmark
  scikit-learn, seleção por validação e avaliação num teste reservado.
- [`src/predict.py`](./src/predict.py): inferência para CSV e para todos os
  classificadores guardados.
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

```powershell
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware
```

O script compara 11 classificadores scikit-learn, escolhe o modelo por recall
de Malware na validação e usa o teste apenas na avaliação final. Todos os
pipelines finais são guardados em `models/ransomware/`; o modelo selecionado e
o schema são usados pela inferência. Para XGBoost, instala-o explicitamente e
acrescenta `--include-xgboost`.

## Aplicação gráfica Windows

Para criar uma aplicação gráfica com botões para instalar dependências, treinar,
fazer previsões e iniciar a API:

```powershell
powershell -ExecutionPolicy Bypass -File build_windows.ps1
.\dist\RansomwareTrainer.exe
```

O executável deve ser usado com `ransom.csv`, `models/` e `results/` na pasta
do projeto. A aplicação não analisa diretamente ficheiros `.exe`; recebe CSVs
com as features já extraídas.

## Notebook e versão Python

Executa `model-deployment.ipynb` do início ao fim. O notebook chama os mesmos
módulos Python que a CLI, compara as previsões de todos os classificadores e
invoca a equipa multiagente selecionada.

```powershell
python -m unittest discover -s tests -v
```

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

## Limites que dependem da equipa

Atualmente só existe `ransom.csv`. Não é possível comprovar aqui a composição
de 3–4 elementos, a aprovação do docente nem treinar nos datasets dos outros
elementos sem receber os respetivos ficheiros e rótulos. Esses dados devem ser
validados e registados pela equipa antes de afirmar cobertura de todos os
datasets.

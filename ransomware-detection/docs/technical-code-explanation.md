# Explicação técnica do pipeline e dos agentes

Documento de apoio à compreensão do código. As sínteses generativas não
substituem os dados medidos nem decisões dos analistas.

## CRISP-ML e classificadores

1. `src/data_preprocessing.py` valida rótulos binários, remove linhas sem
   identificador/rótulo e trata hashes MD5 conflituosas antes da deduplicação.
   Identificadores e rótulos futuros não entram nas features.
2. `src/supervised_learning.py` converte valores hexadecimais, divide os dados
   em treino, validação e teste e ajusta imputação, encoding e scaling dentro
   de pipelines scikit-learn.
3. Compara 11 classificadores, seleciona por recall de Malware na validação e
   usa precision e F1 como desempate. O teste é reservado à medição final.
4. Os classificadores finais são ajustados com treino e validação e guardados
   em `models/ransomware/`. `feature_schema.json` preserva a ordem das
   features exigidas na inferência.
5. `src/predict.py` fornece inferência comum para CSV, API e notebook. Expõe
   scores de probabilidade nos modelos que os suportam e assinala
   `decision_function` como não calibrada nos SVM.
6. `src/serve.py` disponibiliza `/health` e `/predict`; limita tamanho de pedido,
   número de linhas e formato. O serviço fica em localhost por omissão.

## Multiagente opcional

`src/agent_system.py` compõe três responsabilidades: o agente classificador
carrega o vencedor do benchmark, o analista agrega métricas e previsões
verificáveis e o agente generativo local participa na decisão de exigir revisão
humana. Para impedir que texto livre do LLM introduza métricas ou afirmações
inventadas, o relatório só aceita o token `REVIEW_REQUIRED` e transforma-o numa
nota controlada pelo programa. Qualquer outra saída é explicitamente rejeitada
e omitida do relatório.

`src/crewai_agents.py` implementa a variante CrewAI. Os agentes CrewAI chamam o
mesmo modelo Transformers através de um endpoint compatível com OpenAI limitado
a `127.0.0.1`; não há chave externa nem envio dos dados a terceiros. A validação
do token e a formatação segura do relatório são partilhadas com a variante
Python.

## Limitações

- A entrada são features pré-extraídas; não se executa nem inspeciona um `.exe`.
- Previsões do próprio dataset servem apenas para demonstrar inferência, não
  generalização externa.
- Um score não garante que um ficheiro é seguro; decisão final é humana.
- O modelo generativo pode não respeitar o formato; nesse caso, a saída é
  rejeitada e o relatório usa apenas a nota controlada pelo programa.
- Só há um dataset nesta pasta. Os restantes dados, aprovação do docente e
  composição do grupo têm de ser fornecidos/confirmados pela equipa.

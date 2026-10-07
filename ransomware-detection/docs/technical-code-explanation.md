# Relatório técnico: explicação do código do projeto

**Projeto:** IAAC — deteção e triagem de ficheiros potencialmente maliciosos  
**Versão do código explicada:** estado do repositório em 7 de outubro de 2026  
**Linguagem principal:** Python  
**Objetivo deste documento:** explicar a organização, as classes, as funções e os blocos lógicos do código, incluindo a razão das escolhas, os compromissos e os casos limite tratados.

> Este relatório foi preparado com apoio de um assistente de IA. A descrição foi confrontada com os módulos e testes presentes no repositório; a equipa deve rever e validar o conteúdo antes de o entregar. As referências de linhas correspondem à versão indicada e podem mudar quando o código for alterado.

## Como ler a explicação

O projeto contém vários milhares de linhas entre aplicação gráfica, treino,
análise, API, bot, agentes, notebooks e testes. Para evitar copiar o código e
repetir texto sem acrescentar compreensão, a explicação segue os **intervalos
de linhas** de cada módulo. Cada intervalo cobre uma unidade coerente: imports
e configuração, uma classe, uma função ou um bloco de fluxo de controlo.
Assim, todos os módulos Python de `src/` e os testes de `tests/` são mapeados;
não se reproduz literalmente cada linha.

“Protegido” significa que há uma validação/limite no código ou um teste que
comprova o comportamento indicado. Não significa que o sistema seja seguro em
produção. Quando não existe teste dedicado, isso é assinalado como tal.

## 1. Mapa geral da aplicação

O fluxo principal é:

1. **Preparar e validar dados:** `data_preprocessing.py` carrega o CSV, valida
   a etiqueta binária e remove registos sem identificador/etiqueta ou com
   rótulos incompatíveis para a mesma hash.
2. **Explorar e auditar:** `roadmap_eda.py` calcula resumos, testes estatísticos,
   correlações e PCA descritiva; `data_preparation_report.py` documenta
   valores ausentes, outliers e redundância sem apagar linhas.
3. **Treinar:** `supervised_learning.py` compara classificadores, escolhe por
   recall Malware na validação, afina o vencedor com cross-validation e mede
   uma única vez no teste reservado.
4. **Inferir:** `predict.py` carrega o modelo serializado e o respetivo schema,
   valida colunas, produz rótulos e scores.
5. **Receber ficheiros:** `extract_features.py` lê atributos estáticos PE de
   `.exe` e `.exe` dentro de `.zip`; não executa os ficheiros.
6. **Disponibilizar:** `serve.py` fornece API HTTP local; `app.py` oferece GUI
   Windows; `telegram_bot.py` integra conversa e envio de amostras.
7. **Sintetizar factos:** `agent_system.py` e `crewai_agents.py` mostram
   workflows opcionais com LLM, separados do classificador supervisionado.

### Componentes e fronteiras

| Área | Ficheiros | Responsabilidade |
|---|---|---|
| Dados e preparação | `src/data_preprocessing.py`, `src/data_preparation_report.py` | Limpar, converter, descrever e preparar features |
| Exploração | `src/roadmap_eda.py`, `eda_ransomware_dataset_2024.ipynb` | EDA, testes e visualizações |
| Treino | `src/supervised_learning.py`, `src/train.py` | Dois fluxos de benchmark, com desenhos experimentais diferentes |
| Inferência | `src/predict.py` | Usar pipelines treinados em CSV/DataFrame |
| Ficheiros PE | `src/extract_features.py` | Extração estática com limites de tamanho |
| Serviços | `src/serve.py`, `src/local_llm_server.py` | API de classificação e endpoint local para CrewAI |
| Experiência de utilizador | `src/app.py`, `src/telegram_bot.py` | GUI Windows e bot opcional |
| Agentes | `src/agent_system.py`, `src/crewai_agents.py`, `src/run_agents.py`, `src/run_crewai_agents.py` | Orquestração e saída generativa controlada |
| Qualidade | `tests/` | Testes unitários e integração HTTP com dados sintéticos/mocks |
| Empacotamento | `build_windows.ps1` | Criação do executável de ambiente de trabalho |

`src/__init__.py` e `tests/__init__.py` contêm apenas docstrings: identificam,
respetivamente, o pacote de módulos da aplicação e o pacote de testes. Não
definem lógica executável adicional.

`src/train.py` é um fluxo mais simples/antigo de benchmark; o README recomenda
`src/supervised_learning.py` para o pipeline atual, com seleção, pesquisa de
hiperparâmetros e teste reservado. Os resultados dos dois programas não devem
ser misturados: `train.py` mede um split 80/20 e ordena por métricas do teste,
enquanto `supervised_learning.py` tem treino/validação/teste e separa seleção
da avaliação final.

---

## 2. Dados e pré-processamento — `src/data_preprocessing.py`

**Papel do módulo:** concentrar as regras que têm de ser iguais durante treino,
EDA e preparação. Este módulo é importado por outros, não inicia tarefas por
si.

### Linhas 1–18: imports e regras do domínio

`TARGET`, `IDENTIFIERS`, `FUTURE_TARGETS` e `EXPECTED_CLASSES` centralizam as
colunas de rótulo e exclusão. `Category` e `Family` são excluídas do preditor
porque são rótulos alternativos que revelariam informação que o classificador
binário não deve conhecer (target leakage). Num `set`, a pesquisa de pertença
é simples e não depende da ordem.

### Linhas 20–56: classe `Log1pSkewedNonNegative`

É um transformer compatível com o contrato scikit-learn (`BaseEstimator` e
`TransformerMixin`), para que possa viver **dentro** de um `Pipeline` e ser
ajustado novamente em cada fold.

- `__init__` (23–24) guarda o limite de assimetria; não calcula nada ainda,
  respeitando o padrão de estimadores sklearn.
- `fit` (26–41) exige matriz 2D, regista o número de features e calcula
  assimetria em valores finitos de cada coluna. Marca para transformação
  apenas colunas com mais de dois valores finitos, mínimo não negativo e
  `abs(skew) > skew_threshold`.
- `transform` (43–48) copia os dados, valida dimensão e largura contra o
  `fit`, e aplica `log1p` somente às colunas marcadas. Valores negativos e
  colunas menos assimétricas mantêm a escala original.
- `get_feature_names_out` (50–56) preserva nomes recebidos ou gera nomes
  `x0`, `x1`, etc., permitindo interoperar com ferramentas sklearn.

**Porquê / trade-off:** `log1p(x)` comprime caudas longas e é definido em zero;
aplicar apenas a features não negativas evita transformar valores inválidos.
Aprender a máscara no `fit` previne que estatísticas do conjunto de teste
influenciem o pré-processamento. A heurística `|skew| > 1` não garante melhor
classificação; é uma escolha empírica, sujeita a validação.

**Casos limite no código:** matriz que não é 2D, alteração do número de
colunas após treino, valores infinitos/NaN durante estimativa da assimetria e
colunas constantes. Não existe um teste isolado para cada caso; `test_roadmap_compliance.py`
confirma que a decisão de transformação é aprendida no treino e que colunas
negativas ficam intactas.

### Linhas 58–70: `parse_numeric_value`

Converte nulos para `NaN`, procura uma representação hexadecimal `0x...` e
converte-a para inteiro decimal representado como `float`; caso contrário tenta
`float(text)`. Texto descritivo não numérico torna-se `NaN`, em vez de provocar
falha de todo o CSV.

**Compromisso:** aceitar números embutidos em texto hexadecimal ajuda nos
campos PE exportados como strings. Uma string com mais de um número usa o
primeiro match hexadecimal; valores não reconhecidos perdem a representação
original quando a coluna é posteriormente considerada numérica. A regra de
conversão por coluna reduz esse risco.

### Linhas 72–80: `convert_numeric_like_columns`

Trabalha sobre cópia do DataFrame; em colunas object/string, converte todos os
valores com `parse_numeric_value` e substitui a coluna só quando pelo menos
90% dos valores resultam numéricos. O limiar impede converter categorias com
alguns valores que por acaso parecem números.

**Outlier/salvaguarda:** texto inválido mantém-se numa coluna categórica se
ultrapassar a tolerância de 10%; abaixo do limiar vira `NaN` apenas quando a
coluna inteira passa para numérica. O limiar é configurável, mas não há teste
específico para valores exatamente nos 90%.

### Linhas 82–109: `load_and_deduplicate`

1. Lê CSV em UTF-8 com BOM opcional.
2. Exige `md5`, `sha1` e `Class`; comunica explicitamente colunas em falta.
3. Normaliza o texto de `Class` e recusa classes fora de `Benign`/`Malware`.
4. Conta e elimina linhas sem MD5 ou classe.
5. Agrupa por MD5 e marca **todas** as linhas cuja hash tem mais de uma classe.
6. Elimina esses conflitos e conserva uma observação por MD5.
7. Devolve dados e contagens de auditoria.

**Porquê:** excluir hashes com rótulos incompatíveis evita treinar com
supervisão contraditória e remover duplicados reduz contaminação entre
partições. **Trade-off:** não decide qual rótulo conflituoso é correto; elimina
os registos e pode reduzir dados úteis. O relatório regista quantos saíram.

**Salvaguardas:** falha perante schema obrigatório ausente ou rótulo
inesperado; ignora linha sem identificador/alvo; torna hash única no output.
O teste dedicado que cobre cada regra está incompleto: a limpeza é exercitada
indiretamente pelos testes de EDA e treino sintético.

### Linhas 111–115: `feature_columns`

Produz, preservando a ordem original, colunas que não são MD5/SHA1, `Class`,
`Category` ou `Family`. Esta é a barreira principal contra identificação direta
da amostra e leakage dos alvos.

### Linhas 117–143: `build_preprocessor`

Identifica colunas numéricas/categóricas e cria um `ColumnTransformer`:

- Numéricas: imputação por mediana → `Log1pSkewedNonNegative` → `StandardScaler`.
- Categóricas: imputação pela categoria mais frequente → one-hot encoding,
  ignorando categorias inéditas na inferência.
- `remainder="drop"` exclui campos que não pertençam às listas de features.

A função **constrói**, não ajusta, o pré-processador. O chamador é responsável
por colocá-lo num pipeline e executar `fit` apenas nos dados de treino. Na
versão de `supervised_learning.py`, existem variantes específicas de scaler;
esta função é usada no fluxo simples `train.py`.

---

## 3. Benchmark supervisionado principal — `src/supervised_learning.py`

### Linhas 1–67: bibliotecas, imports e semente

As métricas, classificadores, validação cruzada, seleção de features e
serialização estão explícitos no topo. O bloco condicional de import (40–67)
permite executar o módulo como `python src/supervised_learning.py` ou importá-lo
como pacote `src.supervised_learning`. `RANDOM_STATE = 42` torna as divisões e
componentes estocásticos reproduzíveis, mas não congela versões de bibliotecas
nem garante bit a bit em qualquer hardware.

### Linhas 69–100: `make_preprocessors`

Separa colunas numéricas/categóricas uma vez e declara helper local `create`.
Todas as variantes imputam dentro do pipeline, transformam features numéricas
assimétricas e codificam categorias com `handle_unknown="ignore"`.

- `standard_sparse`: StandardScaler, para modelos sensíveis a escala.
- `gaussian_dense`: StandardScaler e matriz densa para GaussianNB.
- `bernoulli_sparse`: MinMaxScaler, útil para modelos que esperam valores não
  negativos/limitados e pipelines esparsos.

**Trade-off:** configurações por família de algoritmo evitam uma transformação
inadequada universal, mas aumentam caminhos a manter. `OneHotEncoder` sem
`sparse_output` explícito usa o default instalado; o comportamento/performance
depende da versão sklearn dentro do intervalo suportado.

### Linhas 102–220: `make_models`

Cria pipelines para 12 modelos base: regressão logística, árvore de decisão,
KNN, Gaussian/Bernoulli/Multinomial Naive Bayes, SVM linear e RBF, AdaBoost,
Gradient Boosting, Random Forest e Extra Trees. XGBoost é opcional e só
importado quando solicitado; se não estiver instalado, levanta erro acionável.

Os pipelines compartilham a preparação adequada e colocam `SelectKBest(f_classif)`
depois do pré-processamento. Inicialmente `k="all"` mantém todas as features;
a pesquisa CV pode comparar todas com uma seleção reduzida.

**Porquê:** comparar famílias diferentes fornece baseline e evita assumir que
um único algoritmo é ótimo. `class_weight="balanced"` em vários modelos
compensa diferenças de classe sem duplicar linhas. A seleção por ANOVA é barata,
mas captura relação univariada e pode descartar interações úteis. Naive Bayes
faz hipóteses fortes; a comparação serve precisamente para as testar.

**Outliers:** imputação e transformação são dentro dos pipelines. Não há
remoção automática de outliers neste benchmark. `MinMaxScaler` pode ser afetado
por extremos; os algoritmos de árvore são menos sensíveis à escala, mas a
seleção de features ainda pode ser sensível.

### Linhas 222–228: `malware_scores`

Procura a posição da classe positiva no `classes_` do estimador e devolve a
coluna correspondente de `predict_proba`; quando não existe probabilidade usa
`decision_function`. Isto evita assumir que Malware é sempre índice 1.
Decision scores não são probabilidades calibradas.

### Linhas 230–278: `parameter_grid`

Define grids pequenos e explícitos por modelo: regularização, profundidade,
número de vizinhos, smoothing/alpha, estimadores e learning rate. Inclui
`select__k` com todas as features e, se possível, 32 selecionadas. Um nome de
modelo sem grid levanta `ValueError`.

**Trade-off:** grids pequenos limitam custo e permitem execução local, mas não
garantem que o ótimo global esteja incluído. A escolha de 32 é um candidato,
não uma verdade teórica.

### Linhas 280–600: `train_and_compare`

**Validação inicial (280–379):** valida nome do dataset e `cv_folds >= 2`,
cria diretórios, chama a limpeza/conversão, seleciona features e separa o teste
(20%) estratificado. Divide os restantes 80% em treino (60% do total) e
validação (20%). Cada modelo é ajustado em treino; métricas na validação
incluem accuracy, precision/recall/F1 da classe Malware e ROC/PR-AUC. A tabela
é ordenada por recall, depois precisão e F1.

**Escolha e tuning (380–455):** seleciona vencedor só pela tabela de validação.
`StratifiedKFold` executa CV no conjunto treino+validação, com scorers de
recall, precisão, F1 e ROC-AUC. `GridSearchCV` refaz o pipeline dentro de cada
fold, seleciona por `recall_malware`, com `error_score="raise"` para não ocultar
falhas. Resultados completos da pesquisa são gravados em CSV.

**Diagnóstico e learning curve (456–519):** compara recall médio treino/validação.
Gap acima de 0,10 sinaliza potencial overfit; ambos abaixo de 0,70 sinalizam
potencial underfit; caso contrário grava “sem sinal forte”. São limiares de
triagem, não prova matemática. A curva varia o tamanho de treino dentro da CV,
regista média/desvio e grava CSV e PNG.

**Guardar e avaliação final (520–600):** os modelos não selecionados são
ajustados em treino+validação; o vencedor pesquisado já foi re-ajustado pelo
GridSearchCV. Serializa pipelines `.joblib`, grava schema de features, calcula
métricas uma vez no teste e produz JSON, matriz de confusão e curva ROC. O JSON
regista que o teste não foi usado na seleção, parâmetros, métricas e limitações.

**Trade-offs e risco metodológico:** recall foi escolhido por prioridade de
reduzir falsos negativos, podendo aumentar falsos positivos. O split é aleatório
e estratificado, não temporal nem por família; amostras relacionadas podem
aparecer em lados diferentes mesmo após deduplicação por MD5. A busca seleciona
o vencedor inicial na validação e faz CV do vencedor em treino+validação; por
isso as métricas CV não são um conjunto externo independente. O teste mantém-se
fora dessa seleção.

**Casos cobertos por teste:** `test_roadmap_compliance.py` treina num dataset
sintético, exige ficheiros principais, CV e diagnóstico, confirma que o teste
não participa na seleção e que o modelo selecionado é serializado. Não cobre
todos os algoritmos, erros de sistema de ficheiros, todas as combinações do
grid ou comparação com dados externos.

### Linhas 601–635: `main`

Expõe CLI para dataset, pasta de resultados/modelos, nome do dataset, folds e
XGBoost opcional. Passa argumentos para `train_and_compare` e imprime tabela.
`if __name__ == "__main__"` separa execução CLI de importação do módulo.

---

## 4. Benchmark simplificado — `src/train.py`

### Linhas 1–35: imports

Importa regressão logística, DummyClassifier, Random Forest e Extra Trees,
métricas e split. O módulo reutiliza a preparação central; pode ser chamado
como script ou pacote.

### Linhas 38–67: `make_models`, `positive_scores`, `evaluate`

`make_models` monta baseline de classe-prioritária, regressão logística e duas
árvores em pipelines. `positive_scores` prefere `predict_proba` e usa
`decision_function` como fallback. `evaluate` calcula métricas binárias com
Malware como positivo e `zero_division=0`, impedindo warning/divisão por zero
quando um modelo não prevê positivos.

### Linhas 70–147: `train`

Limpa e converte dados, divide 80/20 estratificado, faz CV de 3 folds em treino
para os quatro modelos, ajusta cada um no treino e avalia cada um no teste.
Escolhe o que tem maior recall **no teste**, serializa-o e grava matriz,
métricas, estatísticas e schema; modelos baseados em árvores também geram
importâncias.

**Limitação importante:** por escolher o vencedor olhando métricas do teste,
este script não fornece estimativa final imparcial do processo de seleção.
Usar `supervised_learning.py` para a avaliação principal, em que a escolha
ocorre na validação e o teste fica reservado. As importâncias de árvore são
associações do modelo, não explicações causais.

### Linhas 150–164: `main`

CLI simples (`--data`, `--output`) e apresentação tabular. Sem tuning extenso,
é mais rápido/legível, mas não substitui o benchmark recomendado.

---

## 5. EDA reprodutível — `src/roadmap_eda.py`

### Linhas 1–36: ambiente e imports

Seleciona backend gráfico `Agg` antes de importar pyplot, para gerar ficheiros
sem janela gráfica. Reutiliza a mesma limpeza e conversão que o treino.

### Linhas 38–50: `benjamini_hochberg`

Ordena p-values, aplica o fator `n/rank`, força monotonicidade de trás para a
frente e restaura a ordem original, limitando q-values a 1. Corrige o problema
de testar muitas features: reduz falsos positivos esperados sem tratar os
testes como independentes.

### Linhas 52–73: `numeric_summary`

Por feature numérica, calcula contagem, missing, média, desvio-padrão, mínimo,
quartis, mediana, máximo, assimetria e curtose. Para amostras insuficientes,
emite `NaN` em vez de inventar estatística.

### Linhas 75–112: `numeric_bivariate_tests`

Compara Benign e Malware por Mann–Whitney U bilateral, resume medianas e
calcula rank-biserial effect size. Exclui ausentes por feature, guarda tamanhos
de amostra, corrige p-values BH e ordena por q-value.

**Trade-off:** teste não paramétrico e medianas são menos sensíveis à
normalidade/outliers extremos que teste de médias, mas diferenças
estatisticamente significativas não implicam utilidade preditiva.

### Linhas 113–142: `categorical_bivariate_tests`

Preenche missing com categoria explícita, monta tabela de contingência,
descarta tabelas sem pelo menos duas categorias/classes, calcula qui-quadrado,
graus de liberdade e V de Cramér, aplica BH.

**Caso limite:** coluna constante/sem variabilidade é ignorada; categorias
raras podem produzir contagens esperadas pequenas, situação em que a
aproximação qui-quadrado pode ser fraca. Não há agrupamento automático das
categorias raras nem teste exato.

### Linhas 144–169: `_save_class_distributions`

Gera CSV completo e PNG para Class/Category/Family, representa ausentes e
limita somente a visualização categórica às 30 categorias mais frequentes.
Fecha figuras depois de gravar para não acumular memória em processamento
batch.

### Linhas 170–217: `_save_correlation_evidence`

Calcula correlações Pearson e Spearman, matrizes CSV, lista pares únicos da
triangular superior, exporta pares com `|r| >= 0,80` e heatmaps das 25
variáveis de maior variância. Se não existem colunas numéricas, devolve
contagens zero em vez de tentar plotar matriz vazia.

**Trade-offs:** Pearson mede associação linear; Spearman mede associação de
ordem/monótona e é menos dependente de escala. O corte 0,80 destaca relações
para inspeção; não remove variáveis. Features escolhidas pelo maior variância
para heatmap podem ocultar variáveis menos variáveis mas relevantes.

### Linhas 218–266: `_save_multivariate_evidence`

Quando há pelo menos duas features e duas linhas, troca infinitos por missing,
imputa mediana, escala e ajusta PCA de 2 componentes em todo o conjunto limpo.
Grava scores/loadings, variância explicada e scatter plot.

**Advertência:** isto é EDA descritiva, não validação de modelo; o ajuste com
todas as linhas inclui futuro teste apenas no gráfico exploratório e não deve
ser reutilizado como avaliação preditiva.

### Linhas 267–350: `generate_eda`; 351–366: `main`

`generate_eda` encadeia limpeza, conversão, separação de tipos, distribuições,
resumos uni/bivariados, boxplots, correlações e PCA; termina com JSON que
explicita métodos e limites interpretativos. `main` lê `--data`/`--output`,
imprime JSON e permite execução repetível.

**Teste:** `test_roadmap_compliance.py` verifica que dataset sintético gera
distribuições/testes/correlações/PCA e os artefactos CSV/PNG/JSON esperados.
Não verifica valores estatísticos de todas as features nem hipótese/correção
para casos raros.

---

## 6. Relatório de qualidade dos dados — `src/data_preparation_report.py`

### Linhas 1–32: imports

Reutiliza limpeza/conversão, NumPy/pandas e split estratificado. A docstring
declara a intenção: auditar sem remover automaticamente observações suspeitas.

### Linhas 34–58: `outlier_summary`

Para cada feature numérica calcula Q1/Q3, intervalo IQR e quantidade além de
`1,5 × IQR`, mais missing, únicos, assimetria e curtose. Features totalmente
ausentes são ignoradas.

**Trade-off:** IQR é uma regra robusta de sinalização, não prova de erro; por
isso o programa reporta outliers sem apagar nem winsorizar valores legítimos
de malware.

### Linhas 60–68: `correlated_pairs`

Usa Spearman absoluto, filtra pares únicos pela triangular superior e limiar
configurável (invocado em 0,95). Evita duplicar A–B/B–A. Correlação é sugestão
de revisão, não eliminação automática do modelo.

### Linhas 70–78: `engineered_feature_candidates`

Lista variáveis numéricas não negativas com assimetria absoluta acima de 1,
candidatas a log1p. A lista é diagnóstica; a transformação efetiva aprende
máscara dentro de cada fold.

### Linhas 80–174: `build_report`

Cria split estratificado 80/20 para auditar distribuição e schema, calcula
qualidade no treino, exporta pares correlacionados, identifica variáveis
constantes e possíveis redundâncias, compõe JSON com dados ausentes, imputação,
outliers, escala, features e desequilíbrio. `shared_md5_after_cleaning` é
reportado como zero depois da deduplicação.

**Distinção importante:** este split 80/20 pertence ao relatório de preparação;
não é o split 60/20/20 do benchmark de `supervised_learning.py`. A lista de
`correlated_to_drop` é revisão recomendada, não a lista aplicada no treino.

### Linhas 175–185: `main`

CLI com CSV e diretório de saída; grava e apresenta relatório. Não há teste
dedicado a cada campo JSON; a rotina é exercitada pelos artefactos de EDA e
pelos testes da engenharia de features.

---

## 7. Inferência — `src/predict.py`

### Linhas 1–17: imports

Usa `joblib` e pandas. A conversão de números reaproveita a preparação do
treino para tentar manter consistência.

### Linhas 19–37: `load_model_bundle`

Exige modelo e `feature_schema.json` junto do artefacto; carrega o pipeline e
valida que o schema é lista não vazia de strings sem duplicados.

**Segurança:** `joblib.load` desserializa objetos Python e pode executar código
se o ficheiro for malicioso. Só carregar modelos de fonte confiável, por
exemplo modelos gerados localmente. A validação do schema não autentica o
modelo.

### Linhas 39–47: `confidence_level`

Converte a distância da probabilidade a 0,5 em níveis alto/médio/baixo. Esta é
uma classificação de distância e só se aplica a outputs de `predict_proba`;
não é garantia de calibração nem “confiança clínica” do resultado.

### Linhas 49–99: `predict_frame`

Recusa DataFrame vazio e lista features esperadas em falta; seleciona colunas
pela ordem do schema, converte colunas numéricas, prevê classe e confirma que o
modelo conhece Malware. Para modelos probabilísticos emite probabilidade,
confidence e tipo de score; para SVM, orienta o `decision_function` para
Malware e marca-o explicitamente como não calibrado. Mantém `source_file` e
`md5` se chegaram na entrada.

**Trade-offs/casos limite:** campos adicionais não entram no modelo; os campos
exigidos em falta provocam erro explícito. Não se recusa ausência de valores
nas células, pois o pipeline pode imputar. Não valida se probability está
calibrada nem impõe limiar próprio. O teste cobre entrada vazia, feature em
falta, associação previsão/hash/source e confidence.

### Linhas 101–118: `predict_all_models`

Procura `.joblib` na pasta, lê schema/CSV, executa cada modelo, adiciona nome
do modelo e concatena resultados. Sem modelos, lança `FileNotFoundError`.
Assume que schema existe e tem formato correto; validação explícita robusta
fica centralizada parcialmente em `load_model_bundle`, que esta função não usa.

### Linhas 120–134: `resolve_selected_model`

Lê relatório, exige identificador de modelo textual e ficheiro correspondente.
Converte estado “não treinado/artefacto em falta” em erros acionáveis, em vez
de escolher silenciosamente outro modelo.

### Linhas 136–149: `predict_file`

Carrega bundle e CSV, chama `predict_frame`, opcionalmente cria diretório e
grava CSV. Retorna também o DataFrame para outros módulos.

### Linhas 150–171: `main`

CLI exige `--input`; permite modelo direto ou resolução pelo relatório,
configura caminhos e destino CSV. Erros de dados/artefacto propagam como
falha visível.

**Testes:** `test_prediction_service.py` usa `StubModel` para testar caminho
controlado; cobre previsões, confidence, metadados, feature em falta e entrada
vazia. Testa também descoberta/execução de modelos salvos em diretório
temporário.

---

## 8. Extração PE estática — `src/extract_features.py`

### Linhas 1–80: imports, limites e schema PE

Mapas DOS/PE definem quais campos são recolhidos e como os nomes do formato
PE se mapeiam para nomes do projeto. Tipos de máquina conhecidos são
traduzidos para etiquetas legíveis. Limites de recursos:

| Limite | Valor | Objetivo |
|---|---:|---|
| Executável/membro | 50 MiB | Evitar ler amostras enormes |
| Arquivo ZIP comprimido | 250 MiB | Limitar entrada de arquivo |
| Total descomprimido de executáveis | 500 MiB | Restringir ZIP bomb |
| Número de membros | 500 | Limitar custo de enumeração |

### Linhas 82–95: `_numeric` e `_read_bytes`

`_numeric` converte números para int, ausência/infinitos para `NaN`. `_read_bytes`
verifica tamanho anunciado e ainda lê no máximo `MAX_PE_SIZE + 1`; a segunda
verificação protege contra divergência entre stat e bytes recebidos.

### Linhas 97–146: `_parse_pe`

Exige prefixo DOS `MZ`, invoca `pefile.PE(..., fast_load=True)` e converte
exceções de formato/índice/estrutura para `ValueError` compreensível. Calcula
MD5/SHA1 do conteúdo; inicializa campos opcionais como desconhecidos/NaN;
extrai cabeçalho DOS, arquitetura, tipo PE, campos opcionais e atributos de
secções `.text`/`.rdata`.

**Porquê fast_load e whitelist de secções:** extrair só os campos de que o
modelo precisa reduz custo e superfície de parsing. Não equivale a análise
dinâmica. Nomes/atributos podem faltar em PE malformado; os valores ausentes
são convertidos em NaN para que o pipeline lide com eles.

### Linhas 148–156: `_feature_row`

Combina nome de origem, hashes e os campos requeridos pelo schema. Qualquer
feature não extraída recebe NaN; por exemplo rede/registry/processos não podem
ser conhecidos por leitura estática.

### Linhas 158–168: `load_schema`

Lê JSON e exige lista não vazia de nomes únicos string. Erro de JSON ou
ficheiro inexistente não é ocultado.

### Linhas 170–221: `extract_file`

Confirma ficheiro existente. Para ZIP, aplica os quatro limites de recursos,
abre em streaming com `ZipFile`, percorre apenas membros `.exe` e lê cada
membro pela API do ZIP sem extrair para disco. Para `.exe`, verifica o limite e
lê bytes. Extensões não suportadas, ZIP inválido e arquivo sem executáveis
causam erro explícito. Devolve DataFrame com identidade de origem e colunas na
ordem do schema, removendo metadados auxiliares duplicados do corpo de
features.

**Trade-off:** filtrar por extensão `.exe` é conveniente, mas extensão não
prova formato; `_parse_pe` valida também `MZ` e parser PE. ZIP com qualquer
membro excessivo falha toda a extração, em vez de ignorar silenciosamente esse
membro. Não há execução do conteúdo.

**Testes (`test_extract_features.py`):** formato PDF/extension rejeitada;
ZIP com dois executáveis e um ficheiro de texto só gera linhas dos executáveis
e não cria ficheiros extraídos; ZIP sem EXE falha; executável sem `MZ` falha.
Os testes substituem o parser PE por mock no cenário ZIP; não validam uma ampla
coleção de binários PE reais ou todas as variantes de ZIP bomb.

### Linhas 222–247: `main`

CLI obriga `--input` e `--output`, carrega schema, extrai, grava CSV e avisa
que telemetria dinâmica está em falta. Diretório de saída é criado se preciso.

---

## 9. API de classificação — `src/serve.py`

### Linhas 1–26: imports e limites

`MAX_REQUEST_BYTES` limita corpo JSON a 2 MiB; `MAX_BATCH_SIZE` limita lote a
256 linhas. `Any` é usado para construir payload HTTP heterogéneo.

### Linhas 28–123: `make_handler` e classe local `PredictionHandler`

A fábrica fecha sobre modelo/schema e devolve uma classe handler.

- `_send_json` serializa UTF-8, define content type, comprimento, `no-store` e
  `nosniff`, e envia status/corpo.
- `do_GET` aceita só `/health`; qualquer caminho é 404.
- `do_POST` aceita só `/predict`; valida tipo JSON, `Content-Length`, corpo
  não vazio/abaixo do limite, JSON parseável, objeto, lista `instances` não
  vazia, limite de lote e instâncias com apenas valores escalares.
- `predict_frame` centraliza esquema e inferência. `ValueError` torna-se 400;
  scores NumPy são convertidos para escalares JSON.

**Porquê validação em camadas:** rejeitar cedo formato e dimensões reduz
acidentes de interface e payloads excessivos. **Limites:** servidor mínimo da
biblioteca padrão, sem autenticação, rate limit, TLS, logging de auditoria ou
proteção contra clientes lentos. Não expor na rede sem controlos adicionais.
O comprimento declarado é usado para leitura; a implementação não é um
servidor endurecido para internet pública.

### Linhas 125–128: `PredictionServer`

Ativa threads daemon e reutilização de endereço. Útil para protótipo local; não
é substituto de servidor HTTP de produção.

### Linhas 130–165: `main`

Permite indicar artefacto diretamente ou resolver vencedor pelo relatório,
host/porta e diretórios; valida intervalo da porta e carrega pipeline/schema
antes de ouvir. O host default é `127.0.0.1`, reduzindo exposição acidental.
Ctrl+C encerra de forma legível.

**Teste:** integração local com porta efémera comprova `/health`, previsão
válida e 400 para feature em falta. Não cobre todos os erros de protocolo
(415/413/JSON inválido/limite de lote) nem segurança externa.

---

## 10. Interface gráfica Windows — `src/app.py`

### Linhas 1–42: imports, paleta e `find_project_root`

Tkinter fornece GUI sem framework externo; `queue`, `threading` e
`subprocess` permitem delegar operações pesadas. `find_project_root` verifica
um conjunto limitado de pastas candidatas por `ransom.csv` e `src/`; se nenhuma
for projeto, falha explicitamente em vez de usar diretório arbitrário.

### Linhas 44–61: `RansomwareApp.__init__`

Configura janela, dimensões mínimas, raiz do projeto, dataset inicial, fila de
saída, referências de processos, folds CV e opção XGBoost. Constrói tema e UI;
agenda leitura periódica da fila. O estado do processo é guardado para evitar
operações concorrentes e permitir parar o bot.

### Linhas 62–116: `_configure_dark_theme`

Centraliza cores/estilos `ttk` e estados hover/disabled. É apresentação, sem
efeito nos dados ou modelo.

### Linhas 117–275: `_build_ui`

Cria frames e botões para seleção CSV, instalação, treino, previsão, extração,
API, Telegram, EDA, relatório de preparação e avaliação. Spinbox restringe
folds na interface; checkbox ativa XGBoost. Os botões de artefacto abrem
resultados se existirem. Uma nota informa a limitação estática. A caixa de log
é somente leitura e tem scrollbar.

**Trade-off:** GUI chama os mesmos scripts CLI em subprocessos, evitando
duplicar lógica de ML dentro de callbacks; em contrapartida depende da estrutura
de pastas/ambiente externo.

### Linhas 276–383: log, processo assíncrono e Python

- `_write` habilita temporariamente `Text`, acrescenta mensagem e volta a
  bloqueá-lo.
- `_run_async` é atalho para uma sequência de um comando.
- `_run_sequence_async` bloqueia botões, impede operação concorrente, inicia
  worker daemon, executa comandos no diretório do projeto, junta stderr a
  stdout, transmite linhas por fila, espera código de saída e regista falha.
- `_drain_output` corre na thread Tk principal, consome fila e atualiza widgets;
  re-agenda após 100 ms. Isto evita atualizar Tk diretamente em thread de
  trabalho.
- `_set_buttons` sincroniza disponibilidade dos controlos, preservando o
  controlo de parar bot quando necessário.
- `_python_command` prioriza `.venv`; para executável empacotado procura Python
  instalado e falha com mensagem se não houver.

**Casos protegidos:** operação concorrente, erro de criação do subprocesso,
saída com encoding inválido (substitui bytes), código de saída não zero e
Python ausente. A lógica de thread/processos não tem teste automatizado
dedicado neste repositório.

### Linhas 384–439: seleção e instalação

`select_dataset` usa diálogo de CSV. `install_dependencies` e
`install_telegram_dependencies` montam comandos sem shell intermediário;
quando executável empacotado não tem `.venv`, cria ambiente e instala
requirements respetivos. A dependência Telegram tem manifesto próprio e é
opcional.

**Trade-off:** instalação pela interface é acessível, mas requer rede,
permissões e Python/venv. Não inclui confirmação de hashes de pacote nem
ambiente isolado para produção.

### Linhas 440–534: `_prompt_telegram_settings`

Abre diálogo modal; o campo do token usa máscara `*`; valida separador,
prefixo numérico, segredo não vazio e ausência de whitespace; valida IDs
inteiros positivos ou pede confirmação explícita para acesso sem allowlist.
Retorna token/IDs em memória, ou `None` ao cancelar.

**Salvaguarda:** token não é colocado no comando/log nem gravado em ficheiro.
Ainda assim, passa pela variável de ambiente do processo filho; não se deve
considerar uma GUI como cofre de segredos.

### Linhas 535–612: `toggle_telegram_bot` e encerramento

Se bot já existe, termina subprocesso e atualiza rótulo. Ao iniciar, impede
operação de treino concorrente, pede settings, prepara ambiente, inicia
`telegram_bot.py`, remove token do dicionário local após a chamada `Popen` e
consome output em thread. `_close_application` termina bot antes de destruir a
janela; `_drain_output` recebe sinal de encerramento.

**Limite:** termina com `terminate`, não confirma shutdown gracioso nem
aguarda o processo em todas as circunstâncias.

### Linhas 619–687: ações de treino e relatórios

`train` valida folds 2–10, passa CSV/dirs e opção XGBoost ao script principal.
`run_eda` e `run_preparation_report` invocam os scripts correspondentes.
Todas chamam `_run_async`, mantendo interface responsiva.

### Linhas 688–784: `show_evaluation`

Lê JSON do benchmark, extrai modelo, métricas teste, diagnóstico CV e
comparação validação; se ficheiro/chaves inválidas mostra aviso explícito.
Cria janela de texto sem edição e botões para pastas/gráficos.

### Linhas 785–799: `_open_path`

Verifica existência, usa `os.startfile` no Windows e apresenta falha OS.

### Linhas 800–862: `predict`

Confirma Python, relatório, JSON, modelo correspondente, pede input CSV e
caminho de saída, chama `predict.py`. Distingue ainda “treino não executado”,
“JSON inválido” e “artefacto ausente”.

### Linhas 863–907: `extract_features`

Diálogos para `.exe`/`.zip` e destino CSV; invoca `extract_features.py` com o
schema treinado e informa que depois é necessário executar previsão.

### Linhas 908–961: `start_api`; linha 962 em diante: entry point

Verifica relatório e modelo; executa API local em subprocesso e lê saída em
thread. O programa inicia `RansomwareApp().mainloop()` só como script.

**Trade-off geral da GUI:** oferece fluxo acessível reaproveitando CLIs e
mensagens de erro; a maior parte dos callbacks depende de Windows e não está
coberta por testes automatizados. Testar manualmente operação longa,
encerramento durante treino, ambiente incompleto, caminhos com espaços,
instalação e bot é recomendado.

---

## 11. Bot Telegram — `src/telegram_bot.py`

### Linhas 1–32: imports, constantes e projeto

Define limites para upload (20 MiB), histórico, mensagens, resposta e até cinco
previsões listadas; aceita extensões `.exe` e `.zip`. Usa `asyncio` para
integração com python-telegram-bot, mas envia inferência pesada para thread.

### Linhas 34–66: `ChatGenerator`, `parse_allowed_user_ids`,
`validate_bot_token`

O Protocol define interface injetável para modelo de chat e facilita mocks.
Parser transforma IDs separados por vírgula em `frozenset`, rejeita texto não
numérico/IDs ≤0. Validador verifica formato do token sem incluir o valor secreto
na exceção; é validação de forma, não validação com Telegram.

### Linhas 68–105: truncamento e resumo

`truncate_telegram_message` corta para limite com marcador. `format_prediction_summary`
conta Malware/Benign, mostra até cinco resultados e apresenta probabilidade ou
decision score conforme saída. A mensagem avisa que a decisão requer revisão,
que a análise é estática e que não prova segurança; restantes casos são
indicados como omitidos.

**Outlier:** score pode ser `decision_function`, por isso não é formatado como
percentagem. O bot reduz resposta para caber no limite de mensagens.

### Linhas 108–181: `TelegramBotService`

`__init__` guarda modelo, allowlist, fábrica injetável, lock e histórico por
utilizador. `is_allowed` só permite qualquer utilizador se allowlist estiver
vazia (com aviso no arranque).

`_generate_chat` inicializa o modelo uma vez, fora do loop async usando
`to_thread`, serializa inferência pelo lock, injeta instruções de segurança,
guarda conversa por user ID, remove mensagem do utilizador em falha e rejeita
resposta vazia. Mantém system prompt e últimas mensagens limitadas.

`_analyze_file` resolve classificador selecionado pelo relatório, carrega schema,
extrai features e classifica sem execução do ficheiro.

### Linhas 183–222: comandos Telegram

`start` e `help` explicam capacidades; `show_id` mostra ID para allowlist;
`reset` apaga histórico daquele user. Estes handlers consultam atributos do
update via `getattr` para tolerar updates parciais.

### Linhas 223–256: `handle_text`

Exige message/user/chat e `_allow_update`; verifica texto não vazio e máximo
4000 caracteres, confirma que modelo está a preparar, gera resposta e trata
exceções com logging detalhado local e mensagem genérica ao utilizador.

### Linhas 257–310: `handle_document`

Verifica utilizador/chat antes de aceder ao documento; reduz nome a basename,
aceita apenas `.exe`/`.zip`, pré-valida tamanho quando Telegram o fornece, faz
download para diretório temporário, verifica o tamanho efetivo e delega análise
para thread. O `TemporaryDirectory` remove ficheiro ao sair. `ValueError`,
ficheiro ausente e OS error recebem mensagem controlada; erro inesperado é
registado e não expõe stack trace ao utilizador.

**Limite importante:** pré-validação é por extensão e tamanho, não valida
origem/segurança do conteúdo. O extrator aplica validação PE/ZIP e limites
próprios. Telegram recebe o ficheiro durante o upload; o projeto não controla
essa infraestrutura externa.

### Linhas 311–323: `_allow_update`

Bloqueia grupos/canais por privacidade; depois exige ID permitido quando há
allowlist. Denega por omissão se há lista configurada e o utilizador não está
nela. Se a lista está vazia, `is_allowed` permite todos, explicitamente
avisado no arranque/UI.

### Linhas 325–399: `main`

Lê model ID por CLI/env, exige `TELEGRAM_BOT_TOKEN`, valida forma do token e
IDs antes de importar dependência opcional. Monta handlers `/start`, `/help`,
`/id`, `/reset`, texto não comando e documentos. Long polling arranca no fim;
`InvalidToken` gera orientação para revogar/substituir, sem reimprimir o token.

**Testes (`test_telegram_bot.py`):** parser de allowlist (válido, inválido,
não positivo), validação de formato sem mostrar segredo, limite de resposta,
resumo de métricas/nota humana, texto privado usando gerador fake, rejeição
de grupo e user não permitido, download para diretório temporário e análise.
Não testa conversa real com Telegram, token real, envio de ZIP malicioso,
falhas de rede, limites máximos exatos nem ciclo de vida GUI/subprocesso.

---

## 12. Agentes generativos locais — `src/agent_system.py`

### Linhas 1–46: imports, tokens e Protocols

`DEFAULT_MODEL_ID` identifica o modelo generativo opcional. `REVIEW_REQUIRED_TOKEN`
e `REVIEW_REQUIRED_NOTE` separam token técnico e mensagem controlada pelo
programa. Protocols tipam tokenizer, pipeline Transformers e interface de chat,
facilitando injeção de fake em teste e evitando acoplamento direto a classes
externas.

### Linhas 48–91: `TransformersTextGenerator`

Carrega `transformers` só quando é instanciado; dependência ausente vira erro
acionável. Cria cache, carrega tokenizer/modelo e pipeline em CPU (`device=-1`).
`generate` faz geração determinística (`do_sample=False`), limita novos tokens,
exige output com texto não vazio. `generate_chat` aplica template de conversa
correto do tokenizer.

**Trade-offs:** CPU simplifica compatibilidade e reduz requisito de GPU, com
latência potencialmente maior. Modelo de linguagem não é o classificador.

### Linhas 93–110: `ClassifierAgent.run`

Valida relatório, lê nome de modelo selecionado, exige artefacto e chama
`predict_file`. Regista nome selecionado nos attrs do DataFrame para o agente
de métricas poder conferir que previsão e benchmark coincidem.

### Linhas 111–157: `MetricsAnalystAgent.run`

Lê factos verificáveis do benchmark, verifica modelo e tamanho do teste, calcula
contagens da demonstração e até dez linhas exemplo com score e tipo. Métricas
vêm do relatório guardado, não são recalculadas pelas previsões demonstrativas.

**Trade-off/limite:** exemplos são inferência da entrada fornecida; não se deve
confundir com avaliação independente do conjunto de teste. O relatório marca
isso.

### Linhas 159–194: `GenerativeReportAgent`

Aceita gerador injetado ou inicializa Transformers. A execução descarta `facts`
(`del facts`) e pede ao LLM apenas o token `REVIEW_REQUIRED`. Intenção: impedir
texto livre com métricas inventadas. O LLM não analisa os resultados nem
contribui uma conclusão substantiva — apenas aciona nota fixa.

**Trade-off:** reduz risco de afirmações inventadas, mas torna contribuição
generativa funcionalmente mínima. A segurança não depende de prompt sozinho:
validação no código do relatório decide o que é publicado.

### Linhas 196–203: `create_agent_facts`

Executa classificador e analista em sequência e devolve o pacote de factos
controlados para relatório.

### Linhas 205–288: `write_agent_report`

Valida tipos dos blocos, formata tabela de métricas/contagens/exemplos e
compara `narrative.strip()` ao token exato. Se corresponde, escreve nota
controlada; senão marca output como rejeitado e omite o texto gerado. Não usa
resposta livre como prova.

### Linhas 290–300: `run_agent_team`

Orquestra facts → LLM → writer e devolve caminho output. Pode descarregar
modelo na primeira utilização; necessidade de rede/cache é requisito do
ambiente, não envio dos ficheiros PE ao gerador pelo fluxo descrito.

**Testes:** mocks confirmam que dados métricos/selecionados aparecem no
relatório e que saída generativa fora do token exato é omitida. Não provam
qualidade factual geral de qualquer LLM ou privacidade do ambiente fora do
código.

---

## 13. CrewAI e servidor compatível — `src/crewai_agents.py`,
`src/local_llm_server.py`

### `crewai_agents.py`

- Linhas 1–32: imports locais e `CrewRunner` Protocol para fluxo sync/async.
- Linhas 34–117: `_build_crew` desativa telemetry CrewAI por default,
  importa dependência apenas quando necessária, carrega o mesmo gerador local,
  cria servidor em `127.0.0.1` numa porta efémera e configura cliente LLM
  compatível. Cria dois agentes com uma iteração e sem delegação: analista e
  redator. As duas tarefas restringem resposta ao token de revisão. Se setup
  falhar, fecha socket antes de propagar exceção.
- Linhas 119–123: `_stop_server` chama shutdown, close e join com timeout.
- Linhas 125–135: `run_crewai_report` executa kickoff síncrono, fecha serviço
  em `finally`.
- Linhas 137–149: variante async aguarda `kickoff_async`, com o mesmo cleanup.

**Trade-offs:** integração local mantém modelo comum e evita chave API remota,
mas mantém servidor HTTP local temporário e a dependência CrewAI opcional.
Prompt restritivo continua não sendo validação; `write_agent_report` é o
validador final.

### `local_llm_server.py`

- Linhas 1–13: Protocol do gerador.
- Linhas 15–109: `make_handler` devolve handler local. `_send_json` formata
  resposta; `do_GET` implementa `/v1/models`; `do_POST` aceita apenas
  `/v1/chat/completions`, JSON até 1 MiB, lista de 1–32 mensagens com role e
  content strings. Chama o gerador injetado e responde estrutura compatível
  com chat completion.
- Linhas 111–113: servidor threaded com threads daemon e reuse address.

**Casos inválidos protegidos:** rota desconhecida, content-type errado,
content-length inválido/vazio/excessivo, JSON inválido, lista de mensagens
vazia/grande e item sem tipos corretos.

**Teste:** endpoint é iniciado em loopback/porta efémera e um gerador fake
comprova a resposta. Não há testes para cada status 400/413/415 ou concorrência.

---

## 14. Entrypoints — `src/run_agents.py`, `src/run_crewai_agents.py`

Os dois módulos são wrappers de CLI, não duplicam lógica:

- `run_agents.py` (linhas 1–41) aceita input, output, relatório, diretório de
  modelos, model ID e cache; chama `run_agent_team`.
- `run_crewai_agents.py` (linhas 1–44) lê mesmos parâmetros, chama
  `create_agent_facts`, execução CrewAI e writer de relatório seguro.
- O bloco `if __name__ == "__main__"` permite importar sem iniciar modelo.

**Escolha:** CLIs explícitas tornam a execução reproduzível e reutilizável;
erros de parsing/dependências não são convertidos em sucesso aparente.

---

## 15. Gerador do relatório anterior — `src/build_project_report.py`

Este ficheiro gera o relatório geral de ML criado anteriormente; é ferramenta
documental, não faz parte do pipeline do classificador.

- Linhas 1–22: imports `python-docx`, estilos, cores, caminhos.
- Linhas 24–41: `shade` aplica fundo de célula; `set_cell_text` substitui
  conteúdo de célula e define estilo.
- Linhas 43–61: `add_table` cria cabeçalho, linhas, zebra e larguras.
- Linhas 63–81: `add_paragraph` e `add_bullets` formatam texto/listas.
- Linhas 83–107: `add_heading` define hierarquia e `add_figure` insere artefacto
  se existe, ou regista ausência em texto.
- Linhas 108–124: `add_page` compõe bloco de conteúdo por tipos
  (`p`, `bullets`, `table`, `figure`, `subheading`); a estrutura é flexível,
  mas os `type: ignore` refletem que os payloads são tuplos heterogéneos.
- Linhas 126–132: `add_page_number` adiciona campo Word de página.
- Linhas 134–441: `build_report` define formato A4/margens/styles/cabeçalho/
  rodapé, compõe capa e capítulos a partir de artefactos, grava properties e
  DOCX em `reports/`.
- Linhas 442–443: entrypoint imprime caminho gerado.

**Trade-off:** conteúdo do relatório e código de apresentação residem no mesmo
script, fácil de executar mas longo e menos modular. Sem Word/LibreOffice no
ambiente usado, as quebras explícitas foram contadas mas paginação renderizada
não foi comprovada.

---

## 16. Aplicação como executável — `build_windows.ps1`

Sequência do script:

1. `$ErrorActionPreference = "Stop"` interrompe em erros PowerShell.
2. Se `.venv` não existe, cria ambiente com `py -3.13 -m venv`.
3. Instala requisitos principais e PyInstaller, verificando `$LASTEXITCODE`
  após cada processo.
4. Executa PyInstaller com `--noconfirm`, `--clean`, `--onefile`,
  `--windowed`, nome `RansomwareTrainer`, entrada `src\app.py`.
5. Imprime local do executável e lembra dependências externas esperadas.

**Trade-off:** `--onefile --windowed` simplifica distribuição e evita consola,
mas o executável ainda depende dos dados/modelos/recursos não embutidos e o
primeiro arranque pode extrair ficheiros temporários. O script não assina o
executável nem verifica origem/hashes dos pacotes instalados.

---

## 17. Notebooks

### `model-deployment.ipynb` (10 células)

Notebook de demonstração com passos: setup/caminhos; treino/comparação;
invocação de inferência; API local; agentes generativos. As células chamam os
módulos Python, servindo como interface exploratória e não como uma
implementação alternativa validada independentemente. A ordem de execução
importa; células executadas fora de ordem podem ter estado obsoleto.

### `eda_ransomware_dataset_2024.ipynb` (29 células)

Notebook exploratório com setup, carregamento, visão geral, missing/duplicados,
distribuições, histogramas, estatística, boxplots, testes, pairplot, PCA,
Pearson/Spearman e IQR. É um artefacto exploratório; para execução repetível e
resultados versionáveis, a EDA de `src/roadmap_eda.py` é a entrada de CLI.

**Limite de inspeção:** este relatório mapeia as células por secção/objetivo,
não comenta cada expressão/célula individual do notebook. Valores exibidos em
outputs persistidos podem ficar desatualizados após alteração do dataset ou
do kernel.

---

## 18. Testes automatizados: o que está realmente coberto

### `tests/test_extract_features.py`

`StaticFeatureExtractionTests` verifica formato não suportado; leitura lógica
de múltiplos `.exe` de ZIP sem extrair membros para disco; ZIP sem executável;
e EXE sem cabeçalho MZ.

### `tests/test_prediction_service.py`

- `StubModel`/geradores fake fornecem respostas determinísticas, evitando
  carregar modelos grandes ou contactar serviços externos.
- `PredictionFrameTests`: previsão binária, metadados, nível de confiança,
  erro de schema em falta e DataFrame vazio.
- `AgentWorkflowTests`: descobrir modelos salvos, combinar factos de
  benchmark/previsões, guardar relatório e rejeitar narrativa livre.
- `PredictionHTTPTests`: inicia servidor local efémero; verifica health,
  classificação e 400 para input com feature errada; `tearDown` fecha servidor
  e junta thread.
- `LocalLLMHTTPTests`: verifica que endpoint de chat chama gerador fake e
  encerra servidor em `finally`.

### `tests/test_roadmap_compliance.py`

`make_dataset` cria classes equilibradas com features sintéticas. Teste de
feature engineering garante log1p apenas em feature não negativa assimétrica,
ajustada pelo treino, preservando outra coluna. Teste EDA exige os artefactos
CSV/PNG/JSON. Teste de treino exercita CV, diagnóstico, parâmetros, seleção
sem teste e serialização do vencedor.

### `tests/test_telegram_bot.py`

Mocks para modelo/mensagem/API Telegram cobrem IDs, formato de token, limite de
resposta, formato de resumo, conversa privada, rejeição de grupo/ID não
autorizado e transferência de anexo para diretório temporário.

### Fora da cobertura explícita

- Não há testes automatizados da GUI Tkinter, instalação por subprocesso,
  build PyInstaller ou encerramento da GUI.
- Não há teste com token/Telegram real ou falha de rede.
- Não há análise dinâmica/sandbox de malware nem testes com famílias inéditas.
- Não há benchmark externo, avaliação temporal, calibração de probabilidades
  nem cobertura de cada combinação de hiperparâmetros.
- Vários limites HTTP e ZIP têm validação no código, mas sem teste explícito
  para o valor exato do limite e suas fronteiras.

Estes pontos são oportunidades para trabalho futuro, não prova de que o
comportamento esteja errado.

---

## 19. Trade-offs transversais e casos de outlier

| Escolha de implementação | Benefício | Custo/risco residual |
|---|---|---|
| Recall Malware como critério primário | Reduz FN na seleção | Pode elevar FP; custos reais não medidos |
| Deduplicar por MD5 e remover conflitos | Evita etiquetas contraditórias e duplicados exatos | Não remove parentesco de variantes; perde registos em conflito |
| Pipeline sklearn | Ajusta transformações por fold e facilita inferência igual | Versões do ambiente e compatibilidade do pickle continuam relevantes |
| Mediana/moda para missing | Mantém linhas com dados parcialmente ausentes | Valor imputado pode esconder ausência sistemática |
| IQR apenas reportado | Evita apagar malware raro que pareça outlier | Outliers legítimos podem influenciar modelos sensíveis à escala |
| Extrair PE sem execução | Menor risco do que executar amostra | Não vê comportamento dinâmico; features de runtime ficam ausentes |
| Limites de tamanho/membros | Contém consumo em EXE/ZIP/HTTP | Não substitui parser endurecido, sandbox ou limites do sistema |
| API/bot em localhost/privado | Reduz exposição acidental | Sem auth/TLS/rate limit na API; allowlist Telegram deve ser configurada |
| LLM local + token validado no writer | Texto livre inválido não passa ao relatório | Geração continua opcional e não é evidência de classificação |
| Testes com mocks/dataset sintético | Rápidos, repetíveis e sem amostras perigosas | Não simulam diversidade nem comportamento do mundo real |

Outliers de dados estatísticos não são necessariamente ficheiros maliciosos.
Outliers de formato/entrada — CSV sem coluna, PE malformado, ZIP excessivo,
JSON inválido, lista grande, token fora do formato, utilizador não autorizado —
devem ser rejeitados com erro claro, não convertidos em previsão “Benign”.

---

## 20. Comandos de reprodução e conclusão

Na pasta `ransomware-detection`, os comandos documentados são:

```powershell
python src/roadmap_eda.py --data ransom.csv --output results/roadmap/eda
python src/data_preparation_report.py --data ransom.csv --output results/roadmap/preparation
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware --cv-folds 3
python -m unittest discover -s tests -v
```

O código é composto por um pipeline supervisionado principal, um extrator
estático, uma camada de inferência e interfaces opcionais. As escolhas foram
feitas para preservar separação entre treino e inferência, evitar executar
ficheiros e manter revisão humana. As métricas do conjunto local são evidência
de funcionamento experimental, não garantia de desempenho em malware futuro.

**Declaração de IA:** um assistente de IA foi usado para estruturar e redigir
esta explicação. Os nomes e comportamentos descritos devem ser conferidos com o
código e os testes antes de avaliação académica; não se deve apresentar texto
gerado como validação independente.

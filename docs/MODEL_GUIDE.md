# Guia dos modelos para apresentação

Este guia serve para explicar os modelos usados no projeto sem ler código ou slides. Para cada modelo, apresenta a ideia, a razão de inclusão e uma frase curta que pode ser dita na apresentação.

## Logistic Regression

**O que faz:** estima a probabilidade de uma sessão ser uma intrusão através de uma combinação linear das variáveis e da função logística.

**Porque foi usada:** é uma baseline simples, rápida e interpretável. Permite perceber se relações aproximadamente lineares já distinguem tráfego normal de ataques.

**Vantagem e limitação:** os coeficientes são fáceis de interpretar, mas o modelo tem dificuldade em representar relações complexas e não lineares.

**Frase para dizer:** “Usámos regressão logística como referência interpretável; assim conseguimos comparar se os modelos mais complexos trazem realmente melhoria.”

## Decision Tree

**O que faz:** cria regras do tipo “se a reputação do IP for baixa e houver falhas de login, então existe maior risco”.

**Porque foi usada:** as regras são intuitivas para uma equipa de cibersegurança e representam interações não lineares entre atributos.

**Vantagem e limitação:** é muito explicável, mas uma árvore demasiado profunda pode memorizar os dados de treino. Por isso foram definidos limites de profundidade e de amostras por folha.

**Frase para dizer:** “A árvore de decisão traduz os dados em regras próximas das regras que um analista SOC aplicaria.”

## k-Nearest Neighbors (k-NN)

**O que faz:** classifica uma sessão pela classe predominante das sessões mais semelhantes no conjunto de treino.

**Porque foi usada:** é um método simples baseado em proximidade, útil como comparação com os modelos que aprendem regras ou fronteiras globais.

**Vantagem e limitação:** não assume uma forma fixa para a fronteira de decisão, mas é sensível à escala dos atributos e pode ser lento com muitos dados. Por isso os atributos numéricos foram normalizados.

**Frase para dizer:** “O k-NN pergunta quais são as sessões históricas mais parecidas com a sessão atual e usa a decisão dessas vizinhas.”

## Gaussian Naive Bayes

**O que faz:** calcula a probabilidade de ataque assumindo que os atributos numéricos seguem distribuições gaussianas e são condicionalmente independentes.

**Porque foi usada:** é um baseline probabilístico muito rápido, adequado para mostrar o impacto da hipótese de independência.

**Vantagem e limitação:** funciona bem com poucos recursos e produz probabilidades, mas a independência entre variáveis raramente é totalmente verdadeira em tráfego de rede.

**Frase para dizer:** “É um modelo rápido que combina evidências de cada atributo, mas simplifica a realidade ao assumir independência entre eles.”

## Multinomial Naive Bayes

**O que faz:** calcula probabilidades assumindo atributos não negativos, sendo comum em contagens e representações categóricas.

**Porque foi usada:** completa as três variantes de Naive Bayes indicadas no roadmap. A pipeline aplica MinMaxScaler antes deste modelo para cumprir o requisito matemático de valores não negativos.

**Vantagem e limitação:** é simples e rápido, mas a hipótese de distribuição multinomial pode não representar perfeitamente variáveis contínuas de rede.

**Frase para dizer:** “Incluímos Multinomial Naive Bayes para cobrir a variante pedida no roadmap, garantindo antes que os atributos têm valores não negativos.”

## Bernoulli Naive Bayes

**O que faz:** aplica Naive Bayes a atributos binários, por exemplo indicadores resultantes do one-hot encoding de protocolo, browser e encriptação.

**Porque foi usada:** permite comparar uma variante de Naive Bayes mais adequada a sinais de presença/ausência.

**Vantagem e limitação:** é simples e eficiente com dados binários, mas perde alguma informação quantitativa dos atributos contínuos.

**Frase para dizer:** “Esta variante é especialmente indicada para variáveis do tipo sim/não criadas pela codificação categórica.”

## Support Vector Machine — RBF

**O que faz:** encontra uma fronteira de separação com margem máxima; o kernel RBF permite que essa fronteira seja não linear.

**Porque foi usada:** ataques podem resultar de combinações não lineares entre tamanho de pacotes, duração, reputação e tentativas de login.

**Vantagem e limitação:** consegue criar fronteiras complexas e robustas, mas pode demorar mais a treinar e é menos interpretável do que uma árvore.

**Frase para dizer:** “O SVM RBF procura a separação mais segura entre tráfego normal e intrusão, mesmo quando essa separação não é uma linha reta.”

## Support Vector Machine — Polynomial

**O que faz:** usa um kernel polinomial para modelar interações entre atributos até ao grau definido.

**Porque foi usada:** compara uma forma alternativa de fronteira não linear com o kernel RBF.

**Vantagem e limitação:** pode capturar interações polinomiais explícitas, mas a escolha do grau influencia muito a complexidade e o risco de sobreajuste.

**Frase para dizer:** “Incluímos o kernel polinomial para testar se interações estruturadas entre variáveis explicavam melhor os ataques.”

## Random Forest

**O que faz:** treina muitas árvores de decisão com amostras e subconjuntos de atributos diferentes e combina os seus votos.

**Porque foi usada:** é um modelo robusto para dados tabulares e normalmente reduz o sobreajuste de uma única árvore.

**Vantagem e limitação:** capta relações complexas, suporta bem outliers e permite medir importância de atributos; em troca, é menos explicável do que uma árvore individual.

**Frase para dizer:** “A Random Forest reduz o risco de uma regra isolada estar errada ao combinar a decisão de muitas árvores.”

## AdaBoost

**O que faz:** constrói modelos fracos sequencialmente, dando maior atenção aos exemplos que os modelos anteriores classificaram mal.

**Porque foi usada:** representa boosting e permite avaliar se focar nos casos difíceis melhora a deteção de ataques.

**Vantagem e limitação:** pode melhorar classificadores simples, mas é sensível a ruído e a outliers, pois estes podem receber demasiado peso.

**Frase para dizer:** “O AdaBoost aprende progressivamente com os erros anteriores, focando-se nas sessões que foram mais difíceis de classificar.”

## Gradient Boosting

**O que faz:** adiciona árvores pequenas de forma sequencial para corrigir os erros residuais do conjunto anterior.

**Porque foi usada:** é um dos métodos mais eficazes em dados tabulares e teve o melhor F1 médio em validação cruzada neste projeto.

**Vantagem e limitação:** obtém boa precisão ao modelar relações complexas; exige controlo de hiperparâmetros, porque muitas árvores ou uma taxa de aprendizagem alta podem causar sobreajuste.

**Frase para dizer:** “O Gradient Boosting foi selecionado porque, nos nossos testes, apresentou o melhor equilíbrio entre precision e recall medido pelo F1.”

## XGBoost

**O que faz:** é uma implementação otimizada de gradient boosting que inclui regularização e mecanismos eficientes de treino.

**Porque foi usada:** permite comparar um algoritmo de boosting de estado da arte com o Gradient Boosting do scikit-learn.

**Vantagem e limitação:** é rápido, poderoso e tem regularização para ajudar a generalização; no entanto, tem mais hiperparâmetros e é mais difícil de explicar e afinar.

**Frase para dizer:** “O XGBoost é uma versão otimizada e regularizada do boosting, incluída para comparar desempenho com um método de referência atual.”

## Como justificar a escolha final

O modelo final não é escolhido apenas pela accuracy, porque num problema de intrusões uma classe pode ser mais frequente do que outra. A seleção usa o **F1 médio em validação cruzada estratificada**, que equilibra precision e recall e reduz a dependência de uma única divisão treino/teste. A tabela de resultados é apresentada pelo notebook de avaliação ou por `main.py`.

Na apresentação, indiquem sempre o resultado que consta no ficheiro de métricas gerado na última execução. No estado atual, o **Gradient Boosting** é o modelo selecionado.

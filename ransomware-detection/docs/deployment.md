# Deployment local do classificador

## Âmbito

O serviço expõe o classificador binário como uma API HTTP local. Recebe
características já extraídas e devolve classe e score. Não abre, executa nem
extrai características de ficheiros `.exe`; as previsões apoiam triagem humana
e não garantem segurança.

## Treinar e iniciar

```powershell
python src/supervised_learning.py --data ransom.csv --output results --model-dir models/ransomware
python src/serve.py --host 127.0.0.1 --port 8000
```

O servidor resolve o modelo selecionado pelo relatório em
`results/supervised_learning_report.json` e carrega o pipeline e
`models/ransomware/feature_schema.json`. Pode ser indicada outra seleção com
`--model` ou outros caminhos com `--report` e `--models-dir`.

## Endpoints

- `GET /health` — confirma que o serviço e o modelo carregado estão prontos.
- `POST /predict` — recebe até 256 linhas JSON, com um limite de 2 MiB.

Exemplo do corpo do pedido (substituir `feature_name` pelo nome de uma feature
presente em `models/ransomware/feature_schema.json`):

```json
{
  "instances": [
    {"feature_name": 1}
  ]
}
```

O pedido tem de conter todas as features do schema. Features adicionais são
ignoradas. JSON inválido ou features em falta recebem HTTP 400; pedidos acima
dos limites recebem HTTP 413; tipo de conteúdo não JSON recebe HTTP 415. O
serviço escuta em `127.0.0.1` por omissão. Uma exposição em rede exige
autenticação, TLS e controlos operacionais que este protótipo não implementa.

## Segurança operacional

`joblib` carrega objetos Python serializados, que podem executar código se
forem de fonte maliciosa. Carrega apenas modelos gerados localmente pelo
projeto. Não envies executáveis para este protótipo.

## Verificação

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
python src/predict.py --input sample.csv
```

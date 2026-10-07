# Bot Telegram local

O bot usa long polling: o processo local consulta o Telegram, por isso não é
necessário abrir uma porta no router nem expor a API do classificador. O SmolLM2
gera as respostas de conversa localmente. As mensagens passam pelos servidores
do Telegram, e o modelo Transformers pode descarregar os pesos da Hugging Face
na primeira utilização.

## Criar o bot e instalar

1. No Telegram, abre `@BotFather`, usa `/newbot` e guarda o token fornecido.
2. No PowerShell, entra na pasta `ransomware-detection` e instala as dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-telegram.txt
```

3. Define o token apenas na sessão local do PowerShell; substitui o valor pelo
   token real, sem o colocar no código, num ficheiro versionado ou no GitHub:

```powershell
$env:TELEGRAM_BOT_TOKEN = "TOKEN_FORNECIDO_PELO_BOTFATHER"
```

4. Inicia temporariamente o bot sem allowlist e envia `/id` numa conversa
   privada para saber o teu ID numérico. Para a operação normal, para o bot,
   define a allowlist e inicia novamente:

```powershell
$env:TELEGRAM_ALLOWED_USER_IDS = "O_TEU_ID_NUMERICO"
.\.venv\Scripts\python.exe src\telegram_bot.py
```

Para permitir mais utilizadores, separa os IDs por vírgulas. A allowlist é
opcional no código, mas recomendada: sem ela, qualquer pessoa que encontre o
bot pode usar o modelo e submeter ficheiros para análise. O processo tem de
continuar aberto para o bot responder; `Ctrl+C` termina-o.

## Utilização

- Envia texto na conversa privada para conversar com `HuggingFaceTB/SmolLM2-360M-Instruct`.
- Usa `/reset` para apagar o histórico temporário dessa conversa e `/help` para
  ver os comandos.
- Envia um `.exe` ou `.zip` para extração estática de features PE e classificação.
  O modelo precisa de ter sido treinado antes:

```powershell
.\.venv\Scripts\python.exe src\supervised_learning.py --data ransom.csv --output results --model-dir models\ransomware --cv-folds 3
```

O bot só aceita ficheiros até 20 MiB, limita a extração pelos limites de
`src/extract_features.py`, não executa ficheiros e apaga a cópia temporária
após a análise. Features comportamentais não são obtidas estaticamente. As
previsões destinam-se a triagem e exigem revisão humana; não certificam que um
ficheiro é seguro.

As conversas são mantidas apenas em memória durante a execução do bot. Não
envies segredos ou dados pessoais. Para parar, usa `Ctrl+C` e revoga o token
no BotFather se este tiver sido exposto.

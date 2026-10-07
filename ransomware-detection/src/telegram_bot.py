"""Telegram bot for local chat and static PE malware triage."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Protocol

import pandas as pd

if __package__:
    from .agent_system import DEFAULT_MODEL_ID, TransformersTextGenerator
    from .extract_features import extract_file
    from .predict import load_model_bundle, predict_frame, resolve_selected_model
else:
    from agent_system import DEFAULT_MODEL_ID, TransformersTextGenerator
    from extract_features import extract_file
    from predict import load_model_bundle, predict_frame, resolve_selected_model

LOGGER = logging.getLogger("iaac.telegram")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_TELEGRAM_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_CHAT_HISTORY_MESSAGES = 8
MAX_CHAT_INPUT_CHARACTERS = 4000
MAX_TELEGRAM_REPLY_CHARACTERS = 3900
MAX_PREDICTION_ROWS_IN_REPLY = 5
ALLOWED_UPLOAD_SUFFIXES = {".exe", ".zip"}


class ChatGenerator(Protocol):
    def generate_chat(self, messages: list[dict[str, str]]) -> str: ...


def parse_allowed_user_ids(value: str | None) -> frozenset[int]:
    """Parse optional comma-separated Telegram numeric user IDs."""
    if value is None or not value.strip():
        return frozenset()
    try:
        user_ids = frozenset(int(item.strip()) for item in value.split(","))
    except ValueError as error:
        raise ValueError(
            "TELEGRAM_ALLOWED_USER_IDS deve conter IDs numéricos separados por vírgulas."
        ) from error
    if any(user_id <= 0 for user_id in user_ids):
        raise ValueError("Os IDs Telegram permitidos têm de ser números positivos.")
    return user_ids


def validate_bot_token(token: str) -> None:
    """Reject common token entry mistakes without including the secret in errors."""
    bot_id, separator, secret = token.partition(":")
    if (
        not separator
        or not bot_id.isdecimal()
        or not secret
        or any(character.isspace() for character in token)
    ):
        raise ValueError(
            "Formato inválido. Usa o token completo fornecido pelo @BotFather "
            "(inclui o prefixo numérico e os dois-pontos); não uses o username."
        )


def truncate_telegram_message(text: str) -> str:
    if len(text) <= MAX_TELEGRAM_REPLY_CHARACTERS:
        return text
    suffix = "\n\n[Resposta reduzida]"
    return text[: MAX_TELEGRAM_REPLY_CHARACTERS - len(suffix)].rstrip() + suffix


def format_prediction_summary(
    filename: str, predictions: pd.DataFrame
) -> str:
    malware_count = int((predictions["prediction"] == "Malware").sum())
    benign_count = int((predictions["prediction"] == "Benign").sum())
    lines = [
        f"Análise estática concluída: {filename}",
        f"Executáveis analisados: {len(predictions)}",
        f"Classificados como Malware: {malware_count}",
        f"Classificados como Benign: {benign_count}",
        "",
        "Resultados individuais (a classificação exige revisão humana):",
    ]
    for _, row in predictions.head(MAX_PREDICTION_ROWS_IN_REPLY).iterrows():
        source = str(row.get("source_file", filename))
        if "malware_probability" in row and pd.notna(row["malware_probability"]):
            score = f"probabilidade de Malware: {float(row['malware_probability']):.1%}"
        else:
            score = f"score do modelo: {float(row['malware_score']):.3f}"
        lines.append(f"- {source}: {row['prediction']} ({score})")
    omitted = len(predictions) - MAX_PREDICTION_ROWS_IN_REPLY
    if omitted > 0:
        lines.append(f"... e mais {omitted} resultados; consulta o CSV local para a lista completa.")
    lines.extend(
        [
            "",
            "A análise foi estática: o ficheiro não foi executado. "
            "Isto não prova que um ficheiro seja seguro.",
        ]
    )
    return truncate_telegram_message("\n".join(lines))


class TelegramBotService:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        allowed_user_ids: frozenset[int] = frozenset(),
        generator_factory: Callable[[str, Path], ChatGenerator] = TransformersTextGenerator,
    ) -> None:
        self.model_id = model_id
        self.allowed_user_ids = allowed_user_ids
        self.generator_factory = generator_factory
        self.generator: ChatGenerator | None = None
        self.model_lock = asyncio.Lock()
        self.history: dict[int, list[dict[str, str]]] = {}

    def is_allowed(self, user_id: int | None) -> bool:
        return (
            user_id is not None
            and (not self.allowed_user_ids or user_id in self.allowed_user_ids)
        )

    async def _generate_chat(self, user_id: int, text: str) -> str:
        async with self.model_lock:
            if self.generator is None:
                self.generator = await asyncio.to_thread(
                    self.generator_factory,
                    self.model_id,
                    PROJECT_ROOT / "models" / "huggingface",
                )
            history = self.history.setdefault(
                user_id,
                [
                    {
                        "role": "system",
                        "content": (
                            "És um assistente do projeto IAAC de deteção de malware. "
                            "Responde em português europeu, com clareza. Distingue "
                            "o classificador Benign/Malware do modelo de conversa. "
                            "Não afirmes que uma previsão prova que um ficheiro é "
                            "seguro; recomenda sempre validação humana. Não peças "
                            "nem reveles tokens, palavras-passe ou outros segredos."
                        ),
                    }
                ],
            )
            history.append({"role": "user", "content": text})
            messages = [*history]
            try:
                answer = await asyncio.to_thread(
                    self.generator.generate_chat, messages
                )
            except Exception:
                history.pop()
                raise
            answer = answer.strip()
            if not answer:
                history.pop()
                raise RuntimeError("O modelo de conversa devolveu uma resposta vazia.")
            answer = truncate_telegram_message(answer)
            history.append({"role": "assistant", "content": answer})
            system_message = history[0]
            self.history[user_id] = [
                system_message,
                *history[-MAX_CHAT_HISTORY_MESSAGES:],
            ]
            return answer

    def _analyze_file(self, file_path: Path, filename: str) -> str:
        report_path = PROJECT_ROOT / "results" / "supervised_learning_report.json"
        models_dir = PROJECT_ROOT / "models" / "ransomware"
        model_path = resolve_selected_model(report_path, models_dir)
        model, schema = load_model_bundle(model_path)
        feature_rows = extract_file(file_path, schema)
        predictions = predict_frame(model, schema, feature_rows)
        return format_prediction_summary(filename, predictions)

    async def start(self, update: Any, context: Any) -> None:
        del context
        message = getattr(update, "effective_message", None)
        if message is not None:
            await message.reply_text(
                "Olá! Sou o bot local do projeto IAAC. Envia uma pergunta para "
                "conversar, ou usa /help para ver os comandos e os tipos de ficheiro."
            )

    async def help(self, update: Any, context: Any) -> None:
        del context
        message = getattr(update, "effective_message", None)
        if message is not None:
            await message.reply_text(
                "Comandos:\n"
                "/start — iniciar\n"
                "/help — ajuda\n"
                "/id — mostrar o teu ID Telegram para configurar a lista de acesso\n"
                "/reset — limpar o histórico da conversa\n\n"
                "Também podes enviar texto para conversar com o SmolLM2 local, "
                "ou enviar um .exe/.zip para análise estática. O ficheiro não é "
                "executado. O modelo precisa de estar treinado para analisar ficheiros."
            )

    async def show_id(self, update: Any, context: Any) -> None:
        del context
        message = getattr(update, "effective_message", None)
        user = getattr(update, "effective_user", None)
        if message is not None and user is not None:
            await message.reply_text(f"O teu ID Telegram é: {user.id}")

    async def reset(self, update: Any, context: Any) -> None:
        del context
        user = getattr(update, "effective_user", None)
        message = getattr(update, "effective_message", None)
        if user is not None:
            self.history.pop(user.id, None)
        if message is not None:
            await message.reply_text("Histórico da conversa apagado.")

    async def handle_text(self, update: Any, context: Any) -> None:
        del context
        message = getattr(update, "effective_message", None)
        user = getattr(update, "effective_user", None)
        chat = getattr(update, "effective_chat", None)
        if message is None or user is None or chat is None:
            return
        if not await self._allow_update(message, user, chat):
            return
        text = getattr(message, "text", "")
        if not isinstance(text, str) or not text.strip():
            await message.reply_text("Envia uma mensagem de texto.")
            return
        if len(text) > MAX_CHAT_INPUT_CHARACTERS:
            await message.reply_text(
                f"A mensagem é demasiado longa. O limite é "
                f"{MAX_CHAT_INPUT_CHARACTERS} caracteres."
            )
            return
        await message.reply_text(
            "A preparar a resposta local. Na primeira utilização, o modelo pode "
            "demorar a carregar e a descarregar."
        )
        try:
            answer = await self._generate_chat(user.id, text.strip())
        except Exception:
            LOGGER.exception("Falha ao gerar resposta para uma mensagem Telegram.")
            await message.reply_text(
                "Não foi possível gerar uma resposta. Confirma as dependências "
                "de requirements-telegram.txt e tenta novamente."
            )
            return
        await message.reply_text(answer)

    async def handle_document(self, update: Any, context: Any) -> None:
        message = getattr(update, "effective_message", None)
        user = getattr(update, "effective_user", None)
        chat = getattr(update, "effective_chat", None)
        if message is None or user is None or chat is None:
            return
        if not await self._allow_update(message, user, chat):
            return
        document = getattr(message, "document", None)
        if document is None:
            await message.reply_text("Não foi possível ler o anexo.")
            return
        filename = Path(str(getattr(document, "file_name", "") or "upload")).name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_UPLOAD_SUFFIXES:
            await message.reply_text("Formato não suportado. Envia apenas .exe ou .zip.")
            return
        file_size = getattr(document, "file_size", None)
        if isinstance(file_size, int) and file_size > MAX_TELEGRAM_UPLOAD_BYTES:
            await message.reply_text("O ficheiro excede o limite de 20 MiB do bot.")
            return
        bot = getattr(context, "bot", None)
        if bot is None:
            await message.reply_text("O serviço de transferência não está disponível.")
            return

        await message.reply_text(
            "A analisar o ficheiro sem o executar. Isto pode demorar um pouco."
        )
        try:
            with tempfile.TemporaryDirectory(prefix="iaac-telegram-") as directory:
                file_path = Path(directory) / f"upload{suffix}"
                telegram_file = await bot.get_file(document.file_id)
                await telegram_file.download_to_drive(custom_path=file_path)
                if file_path.stat().st_size > MAX_TELEGRAM_UPLOAD_BYTES:
                    raise ValueError("O ficheiro excede o limite de 20 MiB do bot.")
                result = await asyncio.to_thread(
                    self._analyze_file, file_path, filename
                )
        except (FileNotFoundError, ValueError, OSError) as error:
            LOGGER.info("Análise de anexo rejeitada ou indisponível: %s", error)
            await message.reply_text(
                f"Não foi possível analisar o ficheiro: {error}"
            )
            return
        except Exception:
            LOGGER.exception("Falha ao analisar um anexo Telegram.")
            await message.reply_text(
                "Ocorreu um erro durante a análise. Confirma que o modelo está "
                "treinado e consulta o registo local para obter detalhes."
            )
            return
        await message.reply_text(result)

    async def _allow_update(self, message: Any, user: Any, chat: Any) -> bool:
        if getattr(chat, "type", None) != "private":
            await message.reply_text(
                "Por privacidade, envia mensagens e ficheiros ao bot numa conversa privada."
            )
            return False
        user_id = getattr(user, "id", None)
        if not self.is_allowed(user_id):
            LOGGER.warning("Pedido recusado para utilizador Telegram não autorizado.")
            await message.reply_text("Este bot não está configurado para a tua conta.")
            return False
        return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inicia o bot Telegram local do classificador IAAC."
    )
    parser.add_argument(
        "--model-id",
        default=os.environ.get("IAAC_CHAT_MODEL", DEFAULT_MODEL_ID),
        help="Modelo Transformers local (default: SmolLM2-360M-Instruct).",
    )
    args = parser.parse_args()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        parser.error("Define a variável de ambiente TELEGRAM_BOT_TOKEN antes de iniciar.")
    try:
        validate_bot_token(token)
    except ValueError as error:
        parser.error(str(error))
    try:
        allowed_user_ids = parse_allowed_user_ids(
            os.environ.get("TELEGRAM_ALLOWED_USER_IDS")
        )
    except ValueError as error:
        parser.error(str(error))

    try:
        from telegram.ext import (  # type: ignore[import-not-found]
            Application,
            CommandHandler,
            MessageHandler,
            filters,
        )
        from telegram.error import InvalidToken
    except ImportError as error:
        raise SystemExit(
            "Dependência Telegram em falta. Instala requirements-telegram.txt."
        ) from error

    service = TelegramBotService(args.model_id, allowed_user_ids)
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", service.start))
    application.add_handler(CommandHandler("help", service.help))
    application.add_handler(CommandHandler("id", service.show_id))
    application.add_handler(CommandHandler("reset", service.reset))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, service.handle_text)
    )
    application.add_handler(
        MessageHandler(filters.Document.ALL, service.handle_document)
    )
    if not allowed_user_ids:
        LOGGER.warning(
            "TELEGRAM_ALLOWED_USER_IDS não definido; qualquer utilizador que encontre "
            "o bot pode enviar mensagens e ficheiros."
        )
    LOGGER.info(
        "Bot Telegram iniciado em long polling; modelo de conversa: %s",
        args.model_id,
    )
    try:
        application.run_polling()
    except InvalidToken:
        LOGGER.error(
            "O Telegram rejeitou o token. Revoga-o com @BotFather e define "
            "TELEGRAM_BOT_TOKEN com o novo token completo."
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    main()

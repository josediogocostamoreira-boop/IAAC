from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from src.telegram_bot import (
    MAX_TELEGRAM_REPLY_CHARACTERS,
    TelegramBotService,
    format_prediction_summary,
    parse_allowed_user_ids,
    truncate_telegram_message,
    validate_bot_token,
)


class FakeGenerator:
    def __init__(self, model_id: str, cache_dir: Path) -> None:
        self.model_id = model_id
        self.cache_dir = cache_dir

    def generate_chat(self, messages: list[dict[str, str]]) -> str:
        return f"Resposta: {messages[-1]['content']}"


class FakeMessage:
    def __init__(self, text: str = "", document: object | None = None) -> None:
        self.text = text
        self.document = document
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


class TelegramBotTests(unittest.TestCase):
    def test_parses_allowlisted_user_ids(self) -> None:
        self.assertEqual(parse_allowed_user_ids("123, 456,123"), {123, 456})
        self.assertEqual(parse_allowed_user_ids(None), frozenset())
        with self.assertRaisesRegex(ValueError, "numéricos"):
            parse_allowed_user_ids("123,not-an-id")
        with self.assertRaisesRegex(ValueError, "positivos"):
            parse_allowed_user_ids("0")

    def test_validates_token_shape_without_returning_secret(self) -> None:
        validate_bot_token("123456789:secret-part")
        with self.assertRaisesRegex(ValueError, "token completo"):
            validate_bot_token("not-a-bot-token")

    def test_limits_reply_to_telegram_message_length(self) -> None:
        result = truncate_telegram_message("x" * (MAX_TELEGRAM_REPLY_CHARACTERS + 10))
        self.assertLessEqual(len(result), MAX_TELEGRAM_REPLY_CHARACTERS)
        self.assertTrue(result.endswith("[Resposta reduzida]"))

    def test_formats_classifier_results_and_human_review_notice(self) -> None:
        predictions = pd.DataFrame(
            [
                {
                    "source_file": "archive.zip!sample.exe",
                    "prediction": "Malware",
                    "malware_probability": 0.91,
                }
            ]
        )
        summary = format_prediction_summary("archive.zip", predictions)
        self.assertIn("Malware: 1", summary)
        self.assertIn("probabilidade de Malware: 91.0%", summary)
        self.assertIn("revisão humana", summary)
        self.assertIn("não foi executado", summary)

    def test_private_text_message_uses_local_generator(self) -> None:
        async def run() -> tuple[list[str], list[dict[str, str]]]:
            message = FakeMessage("Como funciona o classificador?")
            update = SimpleNamespace(
                effective_message=message,
                effective_user=SimpleNamespace(id=42),
                effective_chat=SimpleNamespace(type="private"),
            )
            service = TelegramBotService(
                allowed_user_ids=frozenset({42}),
                generator_factory=FakeGenerator,
            )
            await service.handle_text(update, SimpleNamespace())
            assert service.generator is not None
            return message.replies, service.history[42]

        replies, history = asyncio.run(run())
        self.assertEqual(len(replies), 2)
        self.assertIn("Resposta: Como funciona", replies[1])
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[-1]["role"], "assistant")

    def test_rejects_non_private_chat(self) -> None:
        async def run() -> list[str]:
            message = FakeMessage("Olá")
            update = SimpleNamespace(
                effective_message=message,
                effective_user=SimpleNamespace(id=42),
                effective_chat=SimpleNamespace(type="group"),
            )
            service = TelegramBotService(
                allowed_user_ids=frozenset({42}),
                generator_factory=FakeGenerator,
            )
            await service.handle_text(update, SimpleNamespace())
            return message.replies

        replies = asyncio.run(run())
        self.assertEqual(len(replies), 1)
        self.assertIn("conversa privada", replies[0])

    def test_rejects_user_outside_allowlist(self) -> None:
        async def run() -> list[str]:
            message = FakeMessage("Olá")
            update = SimpleNamespace(
                effective_message=message,
                effective_user=SimpleNamespace(id=42),
                effective_chat=SimpleNamespace(type="private"),
            )
            service = TelegramBotService(
                allowed_user_ids=frozenset({7}),
                generator_factory=FakeGenerator,
            )
            await service.handle_text(update, SimpleNamespace())
            return message.replies

        replies = asyncio.run(run())
        self.assertEqual(len(replies), 1)
        self.assertIn("não está configurado", replies[0])

    def test_document_is_downloaded_to_temp_and_analyzed(self) -> None:
        class FakeTelegramFile:
            async def download_to_drive(self, custom_path: Path) -> None:
                custom_path.write_bytes(b"MZ")

        class FakeTelegramBot:
            async def get_file(self, file_id: str) -> FakeTelegramFile:
                self.file_id = file_id
                return FakeTelegramFile()

        class FakeService(TelegramBotService):
            assertion_result = False

            def _analyze_file(self, file_path: Path, filename: str) -> str:
                self.assertion_result = (
                    file_path.read_bytes() == b"MZ" and filename == "sample.exe"
                )
                return "Classificação de teste."

        async def run() -> tuple[list[str], bool]:
            message = FakeMessage(
                document=SimpleNamespace(
                    file_name="sample.exe", file_size=2, file_id="telegram-file-id"
                )
            )
            update = SimpleNamespace(
                effective_message=message,
                effective_user=SimpleNamespace(id=42),
                effective_chat=SimpleNamespace(type="private"),
            )
            service = FakeService(allowed_user_ids=frozenset({42}))
            context = SimpleNamespace(bot=FakeTelegramBot())
            await service.handle_document(update, context)
            return message.replies, service.assertion_result

        replies, analyzed = asyncio.run(run())
        self.assertTrue(analyzed)
        self.assertEqual(replies[-1], "Classificação de teste.")


if __name__ == "__main__":
    unittest.main()

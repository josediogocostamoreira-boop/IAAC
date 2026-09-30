"""Minimal localhost OpenAI-compatible chat endpoint for CrewAI."""

from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Protocol


class ChatGenerator(Protocol):
    def generate_chat(self, messages: list[dict[str, str]]) -> str: ...


def make_handler(
    generator: ChatGenerator, model_name: str = "local-transformers"
) -> type[BaseHTTPRequestHandler]:
    class LocalChatHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path != "/v1/models":
                self._send_json(404, {"error": "Endpoint não encontrado."})
                return
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": model_name,
                            "object": "model",
                            "owned_by": "local",
                        }
                    ],
                },
            )

        def do_POST(self) -> None:
            if self.path != "/v1/chat/completions":
                self._send_json(404, {"error": "Endpoint não encontrado."})
                return
            if not self.headers.get("Content-Type", "").lower().startswith(
                "application/json"
            ):
                self._send_json(415, {"error": "Esperado application/json."})
                return
            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_json(400, {"error": "Content-Length inválido."})
                return
            if content_length < 1:
                self._send_json(400, {"error": "Corpo vazio."})
                return
            if content_length > 1024 * 1024:
                self._send_json(413, {"error": "Pedido acima de 1 MiB."})
                return
            try:
                payload = json.loads(self.rfile.read(content_length))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(400, {"error": "JSON inválido."})
                return
            messages = payload.get("messages") if isinstance(payload, dict) else None
            if (
                not isinstance(messages, list)
                or not messages
                or len(messages) > 32
                or any(
                    not isinstance(message, dict)
                    or not isinstance(message.get("role"), str)
                    or not isinstance(message.get("content"), str)
                    for message in messages
                )
            ):
                self._send_json(400, {"error": "Campo messages inválido."})
                return
            answer = generator.generate_chat(
                [
                    {"role": message["role"], "content": message["content"]}
                    for message in messages
                ]
            )
            self._send_json(
                200,
                {
                    "id": "chatcmpl-local",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": answer},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )

    return LocalChatHandler


class LocalLLMServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

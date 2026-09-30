"""Serve the trained ransomware classifier over a small local HTTP API."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

if __package__:
    from .predict import (
        load_model_bundle,
        predict_frame,
        resolve_selected_model,
    )
else:
    from predict import load_model_bundle, predict_frame, resolve_selected_model

MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_BATCH_SIZE = 256


def make_handler(
    model: Pipeline, schema: list[str]
) -> type[BaseHTTPRequestHandler]:
    class PredictionHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path != "/health":
                self._send_json(404, {"error": "Endpoint não encontrado."})
                return
            self._send_json(200, {"status": "ready"})

        def do_POST(self) -> None:
            if self.path != "/predict":
                self._send_json(404, {"error": "Endpoint não encontrado."})
                return
            if not self.headers.get("Content-Type", "").lower().startswith(
                "application/json"
            ):
                self._send_json(
                    415, {"error": "Content-Type deve ser application/json."}
                )
                return
            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_json(400, {"error": "Content-Length inválido."})
                return
            if content_length < 1:
                self._send_json(400, {"error": "O pedido não contém conteúdo."})
                return
            if content_length > MAX_REQUEST_BYTES:
                self._send_json(413, {"error": "Pedido excede o limite de 2 MiB."})
                return

            try:
                payload = json.loads(self.rfile.read(content_length))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(400, {"error": "O corpo não contém JSON válido."})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"error": "O JSON deve ser um objeto."})
                return
            instances = payload.get("instances")
            if not isinstance(instances, list) or not instances:
                self._send_json(
                    400, {"error": "'instances' deve ser uma lista não vazia."}
                )
                return
            if len(instances) > MAX_BATCH_SIZE:
                self._send_json(
                    413, {"error": f"O lote máximo é de {MAX_BATCH_SIZE} linhas."}
                )
                return
            if any(
                not isinstance(instance, dict)
                or any(
                    isinstance(value, (dict, list))
                    for value in instance.values()
                )
                for instance in instances
            ):
                self._send_json(
                    400,
                    {"error": "Cada instância deve ser um objeto com valores escalares."},
                )
                return

            try:
                predictions = predict_frame(
                    model, schema, pd.DataFrame.from_records(instances)
                )
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return

            records = []
            for record in predictions.to_dict(orient="records"):
                records.append(
                    {
                        key: value.item() if isinstance(value, np.generic) else value
                        for key, value in record.items()
                    }
                )
            self._send_json(200, {"predictions": records})

    return PredictionHandler


class PredictionServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inicia a API local de classificação de features."
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Pipeline treinado (.joblib); por omissão usa o modelo selecionado.",
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/supervised_learning_report.json")
    )
    parser.add_argument("--models-dir", type=Path, default=Path("models/ransomware"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port deve estar entre 1 e 65535.")

    model_path = (
        Path(args.model)
        if args.model
        else resolve_selected_model(args.report, args.models_dir)
    )
    model, schema = load_model_bundle(model_path)
    with PredictionServer(
        (args.host, args.port), make_handler(model, schema)
    ) as server:
        print(f"API pronta em http://{args.host}:{args.port} (Ctrl+C para parar)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nAPI terminada.")


if __name__ == "__main__":
    main()

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.agent_system import (
    GenerativeReportAgent,
    REVIEW_REQUIRED_NOTE,
    REVIEW_REQUIRED_TOKEN,
    create_agent_facts,
    write_agent_report,
)
from src.local_llm_server import LocalLLMServer, make_handler as make_llm_handler
from src.predict import predict_all_models, predict_frame
from src.serve import PredictionServer, make_handler


class StubModel:
    classes_ = np.array(["Benign", "Malware"])

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        return np.where(features["feature"].astype(float) > 0, "Malware", "Benign")

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        malware = np.where(features["feature"].astype(float) > 0, 0.9, 0.1)
        return np.column_stack((1 - malware, malware))


class StubTextGenerator:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def generate_chat(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return "Síntese de teste baseada nos factos fornecidos."


class StubChatGenerator:
    def generate_chat(self, _messages: list[dict[str, str]]) -> str:
        assert _messages
        return "Resposta local."


class PredictionFrameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = StubModel()

    def test_predict_frame_returns_predictions_and_hash(self) -> None:
        features = pd.DataFrame(
            {
                "feature": [1, -1],
                "md5": ["a", "b"],
                "source_file": ["first.exe", "bundle.zip!second.exe"],
            }
        )

        result = predict_frame(self.model, ["feature"], features)

        self.assertEqual(result["prediction"].tolist(), ["Malware", "Benign"])
        self.assertEqual(result["md5"].tolist(), ["a", "b"])
        self.assertEqual(
            result["source_file"].tolist(),
            ["first.exe", "bundle.zip!second.exe"],
        )
        self.assertEqual(result["confidence"].tolist(), ["alto", "alto"])

    def test_predict_frame_rejects_missing_features(self) -> None:
        with self.assertRaisesRegex(ValueError, "feature"):
            predict_frame(self.model, ["feature"], pd.DataFrame({"other": [1]}))

    def test_predict_frame_rejects_empty_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "não contém linhas"):
            predict_frame(self.model, ["feature"], pd.DataFrame(columns=["feature"]))


class AgentWorkflowTests(unittest.TestCase):
    def test_all_saved_models_can_be_called(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models_dir = root / "models"
            models_dir.mkdir()
            joblib.dump(StubModel(), models_dir / "stub.joblib")
            (models_dir / "feature_schema.json").write_text(
                json.dumps(["feature"]), encoding="utf-8"
            )
            input_path = root / "sample.csv"
            pd.DataFrame({"feature": [1, -1]}).to_csv(input_path, index=False)

            results = predict_all_models(models_dir, input_path)

            self.assertEqual(results["model"].unique().tolist(), ["stub"])
            self.assertEqual(results["prediction"].tolist(), ["Malware", "Benign"])

    def test_agents_share_verified_classifier_facts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models_dir = root / "models"
            models_dir.mkdir()
            joblib.dump(StubModel(), models_dir / "stub.joblib")
            (models_dir / "feature_schema.json").write_text(
                json.dumps(["feature"]), encoding="utf-8"
            )
            report_path = root / "report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "dataset": "test-corpus",
                        "selected_model": "stub",
                        "final_test_metrics": {
                            "accuracy": 0.95,
                            "precision_malware": 0.9,
                        },
                        "split": {"test_rows": 100},
                    }
                ),
                encoding="utf-8",
            )
            input_path = root / "sample.csv"
            pd.DataFrame({"feature": [1, -1]}).to_csv(input_path, index=False)

            facts = create_agent_facts(input_path, report_path, models_dir)
            text_generator = StubTextGenerator()
            narrative = GenerativeReportAgent(
                generator=text_generator
            ).run(facts)
            output_path = root / "agent-report.md"
            write_agent_report(facts, narrative, output_path)

            self.assertEqual(facts["selected_model"], "stub")
            self.assertEqual(facts["dataset"], "test-corpus")
            self.assertEqual(facts["prediction_counts"], {"Malware": 1, "Benign": 1})
            self.assertEqual(
                narrative, "Síntese de teste baseada nos factos fornecidos."
            )
            self.assertIn(REVIEW_REQUIRED_TOKEN, text_generator.messages[0]["content"])
            self.assertTrue(output_path.is_file())
            report_content = output_path.read_text(encoding="utf-8")
            self.assertIn("Precision (Malware)", report_content)
            self.assertIn("0.95", report_content)
            self.assertIn("A saída generativa foi rejeitada", report_content)
            self.assertIn(REVIEW_REQUIRED_NOTE, report_content)
            self.assertNotIn(narrative, report_content)

    def test_report_accepts_only_controlled_agent_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            facts = {
                "dataset": "test",
                "selected_model": "stub",
                "test_rows": 10,
                "prediction_count": 1,
                "test_metrics": {"accuracy": 0.9},
                "prediction_counts": {"Benign": 1},
                "sample_predictions": [],
            }
            output_path = root / "agent-report.md"

            write_agent_report(facts, REVIEW_REQUIRED_TOKEN, output_path)

            report_content = output_path.read_text(encoding="utf-8")
            self.assertIn(REVIEW_REQUIRED_NOTE, report_content)
            self.assertNotIn("A saída generativa foi rejeitada", report_content)


class PredictionHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = PredictionServer(
            ("127.0.0.1", 0), make_handler(StubModel(), ["feature"])
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(
        self, method: str, path: str, body: str | None = None
    ) -> tuple[int, dict[str, object]]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = json.loads(response.read())
        connection.close()
        return response.status, result

    def test_health_and_prediction_endpoints(self) -> None:
        status, payload = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ready"})

        status, payload = self.request(
            "POST", "/predict", json.dumps({"instances": [{"feature": 2}]})
        )
        self.assertEqual(status, 200)
        predictions = payload["predictions"]
        self.assertIsInstance(predictions, list)
        self.assertEqual(predictions[0]["prediction"], "Malware")

    def test_prediction_endpoint_reports_invalid_input(self) -> None:
        status, payload = self.request(
            "POST", "/predict", json.dumps({"instances": [{"unknown": 2}]})
        )
        self.assertEqual(status, 400)
        self.assertIsInstance(payload["error"], str)
        self.assertIn("feature", payload["error"])


class LocalLLMHTTPTests(unittest.TestCase):
    def test_local_chat_endpoint_uses_injected_generator(self) -> None:
        server = LocalLLMServer(
            ("127.0.0.1", 0), make_llm_handler(StubChatGenerator())
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_address[1], timeout=5
            )
            body = json.dumps(
                {"messages": [{"role": "user", "content": "facts"}]}
            )
            connection.request(
                "POST",
                "/v1/chat/completions",
                body=body,
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = json.loads(response.read())
            connection.close()

            self.assertEqual(response.status, 200)
            self.assertEqual(
                payload["choices"][0]["message"]["content"], "Resposta local."
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

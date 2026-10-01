"""Local classifier, metric-analysis, and generative-report agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import pandas as pd

if __package__:
    from .predict import predict_file
else:
    from predict import predict_file

DEFAULT_MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"
REVIEW_REQUIRED_TOKEN = "REVIEW_REQUIRED"
REVIEW_REQUIRED_NOTE = (
    "A classificação automática apoia a triagem; a decisão exige validação humana."
)


class ChatTemplateTokenizer(Protocol):
    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool,
        add_generation_prompt: bool,
    ) -> str: ...


class TextGenerationPipeline(Protocol):
    def __call__(
        self,
        prompt: str,
        *,
        max_new_tokens: int,
        do_sample: bool,
        return_full_text: bool,
    ) -> list[dict[str, object]]: ...


class ChatTextGenerator(Protocol):
    def generate_chat(self, messages: list[dict[str, str]]) -> str: ...


class TransformersTextGenerator:
    def __init__(self, model_id: str, cache_dir: Path) -> None:
        try:
            from transformers import (  # type: ignore[import-not-found]
                AutoModelForCausalLM,
                AutoTokenizer,
                pipeline,
            )
        except ImportError as error:
            raise RuntimeError(
                "Agentes generativos opcionais em falta. Instala "
                "'requirements-ai.txt' no ambiente do projeto."
            ) from error

        cache_dir.mkdir(parents=True, exist_ok=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, cache_dir=cache_dir
        )
        self._tokenizer: ChatTemplateTokenizer = tokenizer
        self._pipeline: TextGenerationPipeline = pipeline(
            "text-generation", model=model, tokenizer=tokenizer, device=-1
        )

    def generate(self, prompt: str, max_new_tokens: int = 384) -> str:
        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        if not outputs or not isinstance(outputs[0].get("generated_text"), str):
            raise RuntimeError("O modelo local não devolveu texto.")
        text = str(outputs[0]["generated_text"]).strip()
        if not text:
            raise RuntimeError("O modelo local devolveu um relatório vazio.")
        return text

    def generate_chat(self, messages: list[dict[str, str]]) -> str:
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        return self.generate(prompt)


class ClassifierAgent:
    def run(self, input_path: Path, models_dir: Path, report_path: Path) -> pd.DataFrame:
        if not report_path.is_file():
            raise FileNotFoundError(f"Relatório do benchmark não encontrado: {report_path}")
        benchmark = json.loads(report_path.read_text(encoding="utf-8"))
        selected_model = benchmark.get("selected_model")
        if not isinstance(selected_model, str) or not selected_model:
            raise ValueError("O relatório não contém um modelo selecionado.")
        model_path = models_dir / f"{selected_model}.joblib"
        if not model_path.is_file():
            raise FileNotFoundError(
                f"O modelo selecionado não foi encontrado: {model_path}"
            )
        predictions = predict_file(model_path, input_path)
        predictions.attrs["selected_model"] = selected_model
        return predictions


class MetricsAnalystAgent:
    def run(
        self,
        predictions: pd.DataFrame,
        report_path: Path,
        input_path: Path,
    ) -> dict[str, object]:
        benchmark = json.loads(report_path.read_text(encoding="utf-8"))
        selected_model = benchmark["selected_model"]
        if predictions.attrs.get("selected_model") != selected_model:
            raise ValueError("O modelo das previsões não coincide com o benchmark.")
        final_metrics = benchmark["final_test_metrics"]
        split = benchmark.get("split", {})
        if not isinstance(split, dict) or not isinstance(split.get("test_rows"), int):
            raise ValueError("O relatório não contém a dimensão do conjunto de teste.")
        prediction_counts = {
            str(label): int(count)
            for label, count in predictions["prediction"].value_counts().items()
        }
        sample_rows = []
        score_column = (
            "malware_probability"
            if "malware_probability" in predictions
            else "malware_score"
        )
        for record in predictions.head(10).to_dict(orient="records"):
            sample_rows.append(
                {
                    "prediction": str(record["prediction"]),
                    "score": float(record[score_column]),
                    "score_type": str(record["score_type"]),
                }
            )
        return {
            "dataset": benchmark.get("dataset", input_path.stem),
            "selected_model": selected_model,
            "test_metrics": {
                str(name): float(value) for name, value in final_metrics.items()
            },
            "test_rows": split["test_rows"],
            "prediction_count": len(predictions),
            "prediction_counts": prediction_counts,
            "sample_predictions": sample_rows,
            "sample_rows_shown": len(sample_rows),
            "sample_rows_omitted": max(0, len(predictions) - len(sample_rows)),
        }


class GenerativeReportAgent:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        cache_dir: Path = Path("models/huggingface"),
        generator: ChatTextGenerator | None = None,
    ) -> None:
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.generator = generator

    def run(self, facts: dict[str, object]) -> str:
        if self.generator is None:
            self.generator = TransformersTextGenerator(
                self.model_id, self.cache_dir
            )
        del facts
        messages = [
            {
                "role": "system",
                "content": (
                    "És um agente de classificação de cibersegurança. A tua resposta "
                    f"tem de ser exatamente o token {REVIEW_REQUIRED_TOKEN}. "
                    "Não devolvas qualquer outro texto."
                ),
            },
            {
                "role": "user",
                "content": (
                    "A classificação automática nunca substitui a revisão humana. "
                    f"Devolve apenas {REVIEW_REQUIRED_TOKEN}."
                ),
            },
        ]
        return self.generator.generate_chat(messages)


def create_agent_facts(
    input_path: Path,
    report_path: Path,
    models_dir: Path = Path("models/ransomware"),
) -> dict[str, object]:
    predictions = ClassifierAgent().run(input_path, models_dir, report_path)
    return MetricsAnalystAgent().run(predictions, report_path, input_path)


def write_agent_report(
    facts: dict[str, object], narrative: str, output_path: Path
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = facts["test_metrics"]
    prediction_counts = facts["prediction_counts"]
    samples = facts["sample_predictions"]
    if not isinstance(metrics, dict) or not isinstance(prediction_counts, dict):
        raise ValueError("Os factos do relatório têm estrutura inválida.")
    if not isinstance(samples, list):
        raise ValueError("As previsões de demonstração têm estrutura inválida.")

    metric_labels = {
        "accuracy": "Accuracy",
        "precision_malware": "Precision (Malware)",
        "recall_malware": "Recall (Malware)",
        "f1_malware": "F1 (Malware)",
        "roc_auc": "ROC-AUC",
        "pr_auc": "PR-AUC",
    }
    metric_lines = [
        f"| {metric_labels.get(str(name), str(name))} | {float(value):.4f} |"
        for name, value in metrics.items()
    ]
    count_lines = [
        f"| {str(label)} | {int(count)} |"
        for label, count in prediction_counts.items()
    ]
    sample_lines = [
        f"| {index} | {str(sample['prediction'])} | {float(sample['score']):.6f} | "
        f"{str(sample['score_type'])} |"
        for index, sample in enumerate(samples, start=1)
    ]
    metric_table = "\n".join(metric_lines)
    count_table = "\n".join(count_lines)
    sample_table = "\n".join(sample_lines)
    narrative_is_valid = narrative.strip() == REVIEW_REQUIRED_TOKEN
    narrative_status = (
        REVIEW_REQUIRED_NOTE
        if narrative_is_valid
        else (
            "A saída generativa foi rejeitada pelo validador porque não corresponde "
            f"ao token esperado ({REVIEW_REQUIRED_TOKEN}). O texto rejeitado foi "
            "omitido para evitar apresentar afirmações não verificadas. "
            f"Nota controlada: {REVIEW_REQUIRED_NOTE}"
        )
    )
    content = f"""# Relatório assistido por agente generativo

> Os resultados abaixo são formatados pelo programa a partir dos artefactos do benchmark. A nota generativa não é validada e não é um veredito de segurança.

## Resultados verificáveis

- Dataset: {facts['dataset']}
- Classificador selecionado: {facts['selected_model']}
- Tamanho do conjunto de teste: {facts['test_rows']}
- Linhas classificadas na demonstração: {facts['prediction_count']}

### Métricas no conjunto de teste

| Métrica | Valor |
|---|---:|
{metric_table}

### Distribuição das previsões da demonstração

| Classe prevista | Linhas |
|---|---:|
{count_table}

A demonstração não é uma avaliação independente. Os scores de decisão não são probabilidades calibradas.

### Exemplos de previsões (máximo 10)

| # | Classe | Score | Tipo |
|---:|---|---:|---|
{sample_table}

## Resultado do agente generativo

{narrative_status}
"""
    output_path.write_text(content, encoding="utf-8")


def run_agent_team(
    input_path: Path,
    report_path: Path,
    output_path: Path,
    models_dir: Path = Path("models/ransomware"),
    model_id: str = DEFAULT_MODEL_ID,
    cache_dir: Path = Path("models/huggingface"),
) -> Path:
    facts = create_agent_facts(input_path, report_path, models_dir)
    narrative = GenerativeReportAgent(model_id, cache_dir).run(facts)
    write_agent_report(facts, narrative, output_path)
    return output_path

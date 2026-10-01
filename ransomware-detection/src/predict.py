"""Classify new feature rows with the trained ransomware model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

if __package__:
    from .data_preprocessing import convert_numeric_like_columns
else:
    from data_preprocessing import convert_numeric_like_columns


def load_model_bundle(model_path: Path) -> tuple[Pipeline, list[str]]:
    """Load the fitted pipeline and its ordered input feature schema."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
    schema_path = model_path.with_name("feature_schema.json")
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema do modelo não encontrado: {schema_path}")

    model = joblib.load(model_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if (
        not isinstance(schema, list)
        or not schema
        or any(not isinstance(column, str) for column in schema)
        or len(schema) != len(set(schema))
    ):
        raise ValueError(f"Schema inválido: {schema_path}")
    return model, schema


def confidence_level(probability: float) -> str:
    """Translate the model probability into a simple, documented label."""
    distance = abs(probability - 0.5) * 2
    if distance >= 0.8:
        return "alto"
    if distance >= 0.5:
        return "médio"
    return "baixo"


def predict_frame(
    model: Pipeline, schema: list[str], frame: pd.DataFrame
) -> pd.DataFrame:
    """Predict from a frame of pre-extracted features using the model bundle."""
    if frame.empty:
        raise ValueError("O CSV/JSON de entrada não contém linhas.")
    missing = sorted(set(schema) - set(frame.columns))
    if missing:
        raise ValueError(
            "A entrada não contém todas as features esperadas pelo modelo: "
            + ", ".join(missing)
        )

    features = convert_numeric_like_columns(frame[schema])
    predictions = model.predict(features)
    classes = list(model.classes_)
    if "Malware" not in classes:
        raise ValueError("O modelo carregado não tem a classe 'Malware'.")
    if hasattr(model, "predict_proba"):
        malware_scores = model.predict_proba(features)[:, classes.index("Malware")]
        result = pd.DataFrame(
            {
                "prediction": predictions,
                "malware_probability": malware_scores,
                "confidence": [
                    confidence_level(float(value)) for value in malware_scores
                ],
                "score_type": "probability",
            }
        )
    elif hasattr(model, "decision_function"):
        decision_scores = model.decision_function(features)
        if len(classes) == 2 and classes.index("Malware") == 0:
            decision_scores = -decision_scores
        result = pd.DataFrame(
            {
                "prediction": predictions,
                "malware_score": decision_scores,
                "score_type": "decision_function (not calibrated probability)",
            }
        )
    else:
        raise ValueError(
            "O modelo carregado não disponibiliza probability nem decision_function."
        )
    if "md5" in frame:
        result.insert(0, "md5", frame["md5"].values)
    return result


def predict_all_models(
    models_dir: Path, input_path: Path
) -> pd.DataFrame:
    """Run every saved classifier against the same feature CSV."""
    model_paths = sorted(models_dir.glob("*.joblib"))
    if not model_paths:
        raise FileNotFoundError(f"Não foram encontrados modelos em {models_dir}.")
    schema_path = models_dir / "feature_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    frame = pd.read_csv(input_path, encoding="utf-8-sig")
    results = []
    for model_path in model_paths:
        model = joblib.load(model_path)
        predictions = predict_frame(model, schema, frame)
        predictions.insert(0, "model", model_path.stem)
        results.append(predictions)
    return pd.concat(results, ignore_index=True)


def resolve_selected_model(report_path: Path, models_dir: Path) -> Path:
    """Resolve the benchmark-selected classifier from its saved report."""
    if not report_path.is_file():
        raise FileNotFoundError(f"Relatório do benchmark não encontrado: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    selected_model = report.get("selected_model")
    if not isinstance(selected_model, str) or not selected_model:
        raise ValueError("O relatório não contém um modelo selecionado.")
    model_path = models_dir / f"{selected_model}.joblib"
    if not model_path.is_file():
        raise FileNotFoundError(
            f"O modelo selecionado não foi encontrado: {model_path}"
        )
    return model_path


def predict_file(
    model_path: Path,
    input_path: Path,
    output_path: Path | None = None,
) -> pd.DataFrame:
    model, schema = load_model_bundle(model_path)
    frame = pd.read_csv(input_path, encoding="utf-8-sig")
    result = predict_frame(model, schema, frame)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classifica linhas CSV com o modelo de deteção de ransomware."
    )
    parser.add_argument("--input", type=Path, required=True, help="CSV com as features do ficheiro.")
    parser.add_argument(
        "--model",
        type=Path,
        help="Pipeline treinado (.joblib); por omissão usa o modelo selecionado.",
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/supervised_learning_report.json")
    )
    parser.add_argument("--models-dir", type=Path, default=Path("models/ransomware"))
    parser.add_argument("--output", type=Path, help="CSV opcional para guardar as previsões.")
    args = parser.parse_args()
    model_path = args.model or resolve_selected_model(args.report, args.models_dir)
    print(predict_file(model_path, args.input, args.output).to_string(index=False))


if __name__ == "__main__":
    main()

"""Classify new feature rows with the trained ransomware model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from data_preprocessing import convert_numeric_like_columns


def confidence_level(probability: float) -> str:
    """Translate the model probability into a simple, documented label."""
    distance = abs(probability - 0.5) * 2
    if distance >= 0.8:
        return "alto"
    if distance >= 0.5:
        return "médio"
    return "baixo"


def predict_file(
    model_path: Path,
    input_path: Path,
    output_path: Path | None = None,
) -> pd.DataFrame:
    model = joblib.load(model_path)
    schema_path = model_path.with_name("feature_schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    frame = pd.read_csv(input_path, encoding="utf-8-sig")
    missing = sorted(set(schema) - set(frame.columns))
    if missing:
        raise ValueError(
            "O CSV não contém todas as features esperadas pelo modelo: "
            + ", ".join(missing)
        )

    features = convert_numeric_like_columns(frame[schema])
    predictions = model.predict(features)
    probabilities = model.predict_proba(features)
    classes = list(model.classes_)
    malware_index = classes.index("Malware")
    malware_probability = probabilities[:, malware_index]
    result = pd.DataFrame(
        {
            "prediction": predictions,
            "malware_probability": malware_probability,
            "confidence": [confidence_level(float(value)) for value in malware_probability],
        }
    )
    if "md5" in frame:
        result.insert(0, "md5", frame["md5"].values)
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
        default=Path("results/ransomware_classifier.joblib"),
        help="Pipeline treinado (.joblib).",
    )
    parser.add_argument("--output", type=Path, help="CSV opcional para guardar as previsões.")
    args = parser.parse_args()
    if not args.model.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {args.model}. Execute primeiro src\\train.py."
        )
    print(predict_file(args.model, args.input, args.output).to_string(index=False))


if __name__ == "__main__":
    main()

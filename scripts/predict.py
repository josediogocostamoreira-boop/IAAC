"""Deployment local: classifica uma sessão recebida como JSON."""
import argparse, json
import pandas as pd
try:
    from .agent import CybersecurityReportingAgent
    from .data_prep import _engineer_features, load_prepared_data
except ImportError:
    from agent import CybersecurityReportingAgent
    from data_prep import _engineer_features, load_prepared_data

def predict_session(session, data_path="models/processed_data.pkl", models_path="models/trained_models.pkl"):
    prepared = load_prepared_data(data_path)
    row = pd.DataFrame([session]).drop(columns=["session_id", "attack_detected"], errors="ignore")
    row = _engineer_features(row).reindex(columns=prepared.metadata["raw_features"])
    return CybersecurityReportingAgent(models_path).analyze_session_and_generate_report(prepared.preprocessor.transform(row))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--session", required=True, help="Objeto JSON com uma sessão")
    print(predict_session(json.loads(parser.parse_args().session)))

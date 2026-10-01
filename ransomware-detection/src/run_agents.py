"""Run the local Hugging Face multi-agent workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from .agent_system import DEFAULT_MODEL_ID, run_agent_team
else:
    from agent_system import DEFAULT_MODEL_ID, run_agent_team


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera uma síntese local baseada no melhor classificador."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/ransomware.md"))
    parser.add_argument(
        "--report", type=Path, default=Path("results/supervised_learning_report.json")
    )
    parser.add_argument("--models-dir", type=Path, default=Path("models/ransomware"))
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument(
        "--cache-dir", type=Path, default=Path("models/huggingface")
    )
    args = parser.parse_args()
    output = run_agent_team(
        args.input,
        args.report,
        args.output,
        args.models_dir,
        args.model_id,
        args.cache_dir,
    )
    print(f"Relatório gerado: {output}")


if __name__ == "__main__":
    main()

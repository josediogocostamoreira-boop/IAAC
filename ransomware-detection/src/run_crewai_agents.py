"""Run the CrewAI multi-agent workflow against the selected classifier."""

from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from .agent_system import (
        DEFAULT_MODEL_ID,
        create_agent_facts,
        write_agent_report,
    )
    from .crewai_agents import run_crewai_report
else:
    from agent_system import DEFAULT_MODEL_ID, create_agent_facts, write_agent_report
    from crewai_agents import run_crewai_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera localmente um relatório com agentes CrewAI."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/ransomware-crewai.md")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/supervised_learning_report.json")
    )
    parser.add_argument("--models-dir", type=Path, default=Path("models/ransomware"))
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument(
        "--cache-dir", type=Path, default=Path("models/huggingface")
    )
    args = parser.parse_args()
    facts = create_agent_facts(args.input, args.report, args.models_dir)
    narrative = run_crewai_report(facts, args.model_id, args.cache_dir)
    write_agent_report(facts, narrative, args.output)
    print(f"Relatório CrewAI gerado: {args.output}")


if __name__ == "__main__":
    main()

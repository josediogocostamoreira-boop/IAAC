"""CrewAI implementation using the same locally hosted Transformers model."""

from __future__ import annotations

import json
import os
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Protocol

if __package__:
    from .agent_system import (
        DEFAULT_MODEL_ID,
        REVIEW_REQUIRED_TOKEN,
        TransformersTextGenerator,
    )
    from .local_llm_server import LocalLLMServer, make_handler
else:
    from agent_system import (
        DEFAULT_MODEL_ID,
        REVIEW_REQUIRED_TOKEN,
        TransformersTextGenerator,
    )
    from local_llm_server import LocalLLMServer, make_handler


class CrewRunner(Protocol):
    def kickoff(self, *, inputs: dict[str, str]) -> object: ...

    async def kickoff_async(self, *, inputs: dict[str, str]) -> object: ...


def _build_crew(
    model_id: str,
    cache_dir: Path,
) -> tuple[CrewRunner, LocalLLMServer, threading.Thread]:
    os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
    try:
        from crewai import Agent, Crew, LLM, Process, Task  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError(
            "CrewAI opcional em falta. Instala 'requirements-ai.txt' no ambiente."
        ) from error

    generator = TransformersTextGenerator(model_id, cache_dir)
    server = LocalLLMServer(
        ("127.0.0.1", 0), make_handler(generator)
    )
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}/v1"
        local_llm = LLM(
            model="openai/local-transformers",
            api_key="local-only",
            base_url=base_url,
            custom_openai=True,
            temperature=0,
            max_tokens=384,
        )
        analyst = Agent(
            role="Analista de resultados de classificação",
            goal="Alertar sobre a necessidade de validação humana sem inventar limitações.",
            backstory=(
                "Analista de cibersegurança que comunica em português europeu. "
                "Distingue evidência de demonstração. Não inventa métricas, causas, "
                "garantias nem afirmações sem suporte."
            ),
            llm=local_llm,
            allow_delegation=False,
            max_iter=1,
            verbose=False,
        )
        reporter = Agent(
            role="Redator de relatório técnico",
            goal="Comunicar em português europeu que a decisão requer validação.",
            backstory=(
                "Redator técnico em português europeu. Evita números, métricas, "
                "nomes, títulos, causas e garantias. Comunica apenas factos "
                "explícitos."
            ),
            llm=local_llm,
            allow_delegation=False,
            max_iter=1,
            verbose=False,
        )
        analysis_task = Task(
            description=(
                "Determina se uma classificação automática deve ser revista por "
                "uma pessoa. A resposta tem de ser exatamente "
                f"{REVIEW_REQUIRED_TOKEN}. Não devolvas qualquer outro texto."
            ),
            expected_output=f"Exatamente {REVIEW_REQUIRED_TOKEN}.",
            agent=analyst,
        )
        report_task = Task(
            description=(
                "Repete apenas o token devolvido pelo agente anterior, sem "
                "pontuação, explicações ou qualquer outro conteúdo."
            ),
            expected_output=f"Exatamente {REVIEW_REQUIRED_TOKEN}.",
            agent=reporter,
            context=[analysis_task],
        )
        crew = Crew(
            agents=[analyst, reporter],
            tasks=[analysis_task, report_task],
            process=Process.sequential,
            verbose=False,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
    except Exception:
        server.server_close()
        raise

    return crew, server, thread


def _stop_server(server: ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def run_crewai_report(
    facts: dict[str, object],
    model_id: str = DEFAULT_MODEL_ID,
    cache_dir: Path = Path("models/huggingface"),
) -> str:
    crew, server, thread = _build_crew(model_id, cache_dir)
    try:
        return str(crew.kickoff(inputs={"facts": json.dumps(facts, ensure_ascii=False)}))
    finally:
        _stop_server(server, thread)


async def run_crewai_report_async(
    facts: dict[str, object],
    model_id: str = DEFAULT_MODEL_ID,
    cache_dir: Path = Path("models/huggingface"),
) -> str:
    crew, server, thread = _build_crew(model_id, cache_dir)
    try:
        result = await crew.kickoff_async(
            inputs={"facts": json.dumps(facts, ensure_ascii=False)}
        )
        return str(result)
    finally:
        _stop_server(server, thread)

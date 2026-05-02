"""Log Analysis agent — Agent 1 of 5.

LangGraph node that scans the incident log stream and returns a structured
LogAnalysisOutput. Runs in parallel with metrics_correlator and
deployment_tracker.
"""

from __future__ import annotations

from pagerzero.agents.prompts import log_analysis as prompt
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentState, LogAnalysisOutput


def make_log_analysis_node(llm: LLMClient):
    """Build the LangGraph node closure with the LLM client captured.

    Returns an async callable matching LangGraph's node signature:
    `(state: IncidentState) -> dict[str, Any]`. The returned dict is merged
    into the graph state.
    """

    async def log_analysis_node(state: IncidentState) -> dict:
        result = await llm.complete(
            system_prompt=prompt.SYSTEM_PROMPT,
            user_prompt=prompt.build_user_prompt(state.input),
            response_model=LogAnalysisOutput,
            max_tokens=2048,
        )
        return {"log_analysis": result}

    return log_analysis_node

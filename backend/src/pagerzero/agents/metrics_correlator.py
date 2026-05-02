"""Metrics Correlator agent — Agent 2 of 5.

LangGraph node that reads the per-minute time series and identifies the
incident inflection point and leading vs lagging indicators.
"""

from __future__ import annotations

from pagerzero.agents.prompts import metrics_correlator as prompt
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentState, MetricsOutput


def make_metrics_correlator_node(llm: LLMClient):
    async def metrics_correlator_node(state: IncidentState) -> dict:
        result = await llm.complete(
            system_prompt=prompt.SYSTEM_PROMPT,
            user_prompt=prompt.build_user_prompt(state.input),
            response_model=MetricsOutput,
            max_tokens=1024,
        )
        return {"metrics_correlation": result}

    return metrics_correlator_node

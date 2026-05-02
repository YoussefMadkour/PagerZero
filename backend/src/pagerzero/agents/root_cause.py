"""Root Cause agent — Agent 4 of 5.

Synthesizer that runs after agents 1, 2, 3 have all completed. Reads their
three structured outputs and produces ranked root-cause hypotheses with
per-source evidence citations.
"""

from __future__ import annotations

from pagerzero.agents.prompts import root_cause as prompt
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentState, RootCauseOutput


def make_root_cause_node(llm: LLMClient):
    async def root_cause_node(state: IncidentState) -> dict:
        # Convergence point: all three upstream agents must have populated
        # their fields. LangGraph's edge structure guarantees this; the
        # asserts make the contract explicit and produce a clear error if
        # the graph is ever miswired.
        assert state.log_analysis is not None, "log_analysis output missing"
        assert state.metrics_correlation is not None, "metrics_correlation output missing"
        assert state.deployment_correlation is not None, "deployment_correlation output missing"

        result = await llm.complete(
            system_prompt=prompt.SYSTEM_PROMPT,
            user_prompt=prompt.build_user_prompt(
                incident=state.input,
                log_analysis=state.log_analysis,
                metrics=state.metrics_correlation,
                deployments=state.deployment_correlation,
            ),
            response_model=RootCauseOutput,
            max_tokens=2048,
        )
        return {"root_cause": result}

    return root_cause_node

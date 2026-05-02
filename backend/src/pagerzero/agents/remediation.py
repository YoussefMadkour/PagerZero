"""Remediation agent — Agent 5 of 5.

Final node. Reads the top root-cause hypothesis and produces the on-call
runbook: immediate mitigation, rollback procedure, drafted incident report,
and stakeholder notification.
"""

from __future__ import annotations

from pagerzero.agents.prompts import remediation as prompt
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentState, RemediationOutput


def make_remediation_node(llm: LLMClient):
    async def remediation_node(state: IncidentState) -> dict:
        assert state.root_cause is not None, "root_cause output missing"

        result = await llm.complete(
            system_prompt=prompt.SYSTEM_PROMPT,
            user_prompt=prompt.build_user_prompt(
                incident=state.input,
                root_cause=state.root_cause,
            ),
            response_model=RemediationOutput,
            max_tokens=2048,
        )
        return {"remediation": result}

    return remediation_node

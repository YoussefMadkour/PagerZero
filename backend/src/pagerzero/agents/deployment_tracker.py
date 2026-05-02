"""Deployment Tracker agent — Agent 3 of 5.

LangGraph node that ranks recent deployments by likelihood of causing the
active incident.
"""

from __future__ import annotations

from pagerzero.agents.prompts import deployment_tracker as prompt
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import DeploymentOutput, IncidentState


def make_deployment_tracker_node(llm: LLMClient):
    async def deployment_tracker_node(state: IncidentState) -> dict:
        result = await llm.complete(
            system_prompt=prompt.SYSTEM_PROMPT,
            user_prompt=prompt.build_user_prompt(state.input),
            response_model=DeploymentOutput,
            max_tokens=1024,
        )
        return {"deployment_correlation": result}

    return deployment_tracker_node

"""Day 0 smoke test: schemas + scenario loader + mock client all integrate."""

from __future__ import annotations

import pytest

from pagerzero.data.scenario_loader import available_scenarios, load_scenario
from pagerzero.llm import MockLLMClient
from pagerzero.schemas import (
    DeploymentOutput,
    LogAnalysisOutput,
    MetricsOutput,
    RemediationOutput,
    RootCauseOutput,
)


def test_scenario_a_loads() -> None:
    assert "scenario_a_memory_leak" in available_scenarios()
    inc = load_scenario("scenario_a_memory_leak")
    assert inc.service_name == "payment-service"
    assert len(inc.metrics) == 120
    assert len(inc.deployments) == 3
    assert "OutOfMemoryError" in inc.logs


@pytest.mark.parametrize(
    "model",
    [
        LogAnalysisOutput,
        MetricsOutput,
        DeploymentOutput,
        RootCauseOutput,
        RemediationOutput,
    ],
)
async def test_mock_returns_each_agent_response(model: type) -> None:
    client = MockLLMClient(simulated_latency_seconds=0.0)
    out = await client.complete(
        system_prompt="test",
        user_prompt="test",
        response_model=model,
    )
    assert isinstance(out, model)


async def test_root_cause_evidence_threading() -> None:
    """Root cause output must cite evidence from each upstream agent."""
    client = MockLLMClient(simulated_latency_seconds=0.0)
    rc = await client.complete(
        system_prompt="",
        user_prompt="",
        response_model=RootCauseOutput,
    )
    top = rc.top_hypothesis
    assert top.confidence_percent >= 50
    assert top.evidence_from_logs
    assert top.evidence_from_metrics
    assert top.evidence_from_deployments

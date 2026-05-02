"""Day 1 integration tests for the parallel agent pipeline."""

from __future__ import annotations

import time

from pagerzero.data.scenario_loader import load_scenario
from pagerzero.graph import build_graph
from pagerzero.llm import MockLLMClient
from pagerzero.schemas import (
    DeploymentOutput,
    IncidentState,
    LogAnalysisOutput,
    MetricsOutput,
)


async def test_graph_runs_three_agents_on_scenario_a() -> None:
    incident = load_scenario("scenario_a_memory_leak")
    state = IncidentState(incident_id="inc_test", input=incident)

    graph = build_graph(MockLLMClient(simulated_latency_seconds=0.0))
    result = await graph.ainvoke(state)

    assert isinstance(result["log_analysis"], LogAnalysisOutput)
    assert isinstance(result["metrics_correlation"], MetricsOutput)
    assert isinstance(result["deployment_correlation"], DeploymentOutput)

    # Sanity-check the canned scenario A outputs survived the round trip
    assert result["metrics_correlation"].primary_degraded_metric == "memory"
    assert result["deployment_correlation"].most_likely_culprit is not None
    assert result["deployment_correlation"].most_likely_culprit.commit_sha == "abc123f"


async def test_three_agents_run_in_parallel_not_sequentially() -> None:
    """If the three branches were sequential, total wall-time would be ~3x the
    per-call latency. Parallel execution should be ~1x.
    """
    incident = load_scenario("scenario_a_memory_leak")
    state = IncidentState(incident_id="inc_parallel", input=incident)

    per_call_latency = 0.3
    graph = build_graph(MockLLMClient(simulated_latency_seconds=per_call_latency))

    start = time.perf_counter()
    await graph.ainvoke(state)
    elapsed = time.perf_counter() - start

    # Sequential would be ~0.9s; parallel should be ~0.3s plus a small overhead.
    # Use 0.6s as the threshold so we have margin against CI jitter.
    assert elapsed < 0.6, f"agents appear to be sequential (took {elapsed:.2f}s)"


async def test_graph_streams_per_node_lifecycle_events() -> None:
    """The dashboard's per-agent status animation depends on astream_events
    emitting on_chain_start / on_chain_end for each node.
    """
    incident = load_scenario("scenario_a_memory_leak")
    state = IncidentState(incident_id="inc_stream", input=incident)
    graph = build_graph(MockLLMClient(simulated_latency_seconds=0.0))

    started: set[str] = set()
    ended: set[str] = set()
    expected_nodes = {"log_analysis", "metrics_correlator", "deployment_tracker"}

    async for event in graph.astream_events(state):
        kind = event["event"]
        name = event.get("name", "")
        if name in expected_nodes:
            if kind == "on_chain_start":
                started.add(name)
            elif kind == "on_chain_end":
                ended.add(name)

    assert started == expected_nodes
    assert ended == expected_nodes

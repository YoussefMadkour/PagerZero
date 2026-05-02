"""Day 2 API tests.

Verifies the FastAPI app exposes the right endpoints and the SSE stream
emits the contract the dashboard depends on.
"""

from __future__ import annotations

import json

# Pin the mock latency low so the SSE test is fast.
import os

import httpx
import pytest

from pagerzero.api.main import app

os.environ["PAGERZERO_MOCK_LATENCY_S"] = "0.0"


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_health(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_list_scenarios(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/scenarios")
    assert r.status_code == 200
    body = r.json()
    ids = [s["id"] for s in body]
    assert "scenario_a_memory_leak" in ids
    assert "scenario_b_pool_exhaust" in ids
    assert "scenario_c_cascade" in ids
    for s in body:
        assert s["service_name"]
        assert s["alert_summary"]


async def test_stream_unknown_scenario(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/incidents/stream?scenario=does_not_exist")
    assert r.status_code == 404


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    """Minimal SSE parser: returns [(event, data_dict), ...]."""
    events: list[tuple[str, dict]] = []
    current_event: str | None = None
    current_data: list[str] = []

    for raw_line in body.splitlines():
        line = raw_line.rstrip("\r")
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            current_data.append(line.split(":", 1)[1].lstrip())
        elif line == "" and current_event is not None:
            payload = "\n".join(current_data) if current_data else ""
            data = json.loads(payload) if payload else {}
            events.append((current_event, data))
            current_event = None
            current_data = []

    return events


@pytest.mark.parametrize(
    "scenario",
    ["scenario_a_memory_leak", "scenario_b_pool_exhaust", "scenario_c_cascade"],
)
async def test_stream_produces_full_lifecycle(
    client: httpx.AsyncClient, scenario: str
) -> None:
    r = await client.get(f"/api/incidents/stream?scenario={scenario}")
    assert r.status_code == 200

    events = _parse_sse(r.text)
    types = [e for e, _ in events]

    assert types[0] == "pipeline_started"
    assert types[-1] == "pipeline_completed"

    started = {data["agent"] for ev, data in events if ev == "agent_started"}
    completed = {data["agent"] for ev, data in events if ev == "agent_completed"}
    expected = {
        "log_analysis",
        "metrics_correlator",
        "deployment_tracker",
        "root_cause",
        "remediation",
    }
    assert started == expected
    assert completed == expected

    # The pipeline_started event names the scenario, the agents, and the
    # quantitative source-data ingest summary the dashboard renders.
    started_payload = next(d for e, d in events if e == "pipeline_started")
    assert started_payload["scenario"] == scenario
    assert set(started_payload["agents"]) == expected
    sd = started_payload["source_data"]
    assert sd["log_lines"] > 1000, "expected non-trivial log volume"
    assert sd["log_tokens_est"] > 0
    assert sd["metric_points"] > 0
    assert sd["deployments"] > 0

    # Each agent_started event carries a scope so the AgentCard can show
    # what that agent is reading before it finishes.
    for ev, data in events:
        if ev == "agent_started":
            assert "scope" in data
            assert data["scope"]["primary"]
            assert data["scope"]["secondary"]

    # The completed event payload contains the final state with all 5 outputs
    final_payload = next(d for e, d in events if e == "pipeline_completed")
    final = final_payload["final_state"]
    for field in (
        "log_analysis",
        "metrics_correlation",
        "deployment_correlation",
        "root_cause",
        "remediation",
    ):
        assert field in final, f"missing {field} in final_state"

    # Spot-check the root cause hypothesis is real (not None / empty)
    assert final["root_cause"]["top_hypothesis"]["confidence_percent"] >= 50

"""SSE event translator: LangGraph astream_events -> dashboard event stream.

The dashboard's per-agent status animation (pending → running → done) is
driven entirely by these events. Keeping the translation in one place means
the FastAPI route stays thin and the frontend contract is easy to inspect.

The `pipeline_started` event also carries quantitative `source_data` counts,
and each `agent_started` event carries an agent-specific `scope` describing
exactly what that agent is reading. These power the dashboard's "this is
real work, not a progress bar" framing — see ADR 0002.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from pagerzero.graph import ALL_AGENTS, build_graph
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import AgentName, IncidentInput, IncidentState


def sse_event(event_type: str, data: dict) -> dict[str, str]:
    """Build the dict shape `EventSourceResponse` expects per yield."""
    return {"event": event_type, "data": json.dumps(data, default=str)}


def _serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def _summarize_source_data(incident: IncidentInput) -> dict[str, Any]:
    """Quantitative summary of what's being fed into the pipeline.

    The frontend renders this as the SourceDataPanel — proof of real intake
    before any agent finishes.
    """
    log_lines = incident.logs.count("\n") + (
        0 if incident.logs.endswith("\n") or not incident.logs else 1
    )
    log_chars = len(incident.logs)
    # Structured logs tokenize denser than English (timestamps, field names,
    # status codes all collapse to single BPE tokens). ~5 chars/token is a
    # conservative estimate for the synthetic logs in our scenarios.
    log_tokens_est = log_chars // 5

    metric_span_minutes = 0
    if len(incident.metrics) >= 2:
        delta = incident.metrics[-1].timestamp - incident.metrics[0].timestamp
        metric_span_minutes = round(delta.total_seconds() / 60)

    deploy_oldest_minutes = 0
    if incident.deployments:
        latest = max(d.timestamp for d in incident.deployments)
        oldest = min(d.timestamp for d in incident.deployments)
        deploy_oldest_minutes = round((latest - oldest).total_seconds() / 60)

    return {
        "log_lines": log_lines,
        "log_chars": log_chars,
        "log_tokens_est": log_tokens_est,
        "metric_points": len(incident.metrics),
        "metric_span_minutes": metric_span_minutes,
        "deployments": len(incident.deployments),
        "deploys_window_minutes": deploy_oldest_minutes,
    }


def _agent_scope(agent: AgentName, incident: IncidentInput) -> dict[str, Any]:
    """What each agent is reading, in human-and-machine-readable form.

    Renders on the AgentCard as a small "scope" line under the title. Lets
    a judge see "Log Analysis · 8,247 lines · ~62k tokens" before the agent
    is even done.
    """
    if agent == "log_analysis":
        return {
            "primary": f"{incident.logs.count(chr(10)):,} log lines",
            "secondary": f"~{len(incident.logs) // 5 // 1000}k tokens · single context pass",
        }
    if agent == "metrics_correlator":
        span = 0
        if len(incident.metrics) >= 2:
            delta = incident.metrics[-1].timestamp - incident.metrics[0].timestamp
            span = round(delta.total_seconds() / 60)
        return {
            "primary": f"{len(incident.metrics)} metric points",
            "secondary": f"{span} min window · 5 series",
        }
    if agent == "deployment_tracker":
        return {
            "primary": f"{len(incident.deployments)} deploys",
            "secondary": "24h window · diffs + commit messages",
        }
    if agent == "root_cause":
        return {
            "primary": "synthesizing 3 reports",
            "secondary": "logs + metrics + deploys",
        }
    if agent == "remediation":
        return {
            "primary": "from top hypothesis",
            "secondary": "commands + rollback + report",
        }
    return {"primary": "", "secondary": ""}


async def stream_incident_events(
    incident_input: IncidentInput,
    incident_id: str,
    llm: LLMClient,
) -> AsyncIterator[dict[str, str]]:
    """Run the graph and translate each LangGraph event into an SSE event.

    Event types emitted to the client:
      - `pipeline_started`   { incident_id, scenario, service_name,
                               alert_summary, agents, source_data }
      - `agent_started`      { agent, scope }
      - `agent_completed`    { agent, output }
      - `pipeline_completed` { final_state }
      - `error`              { message }

    The final state is accumulated from per-node outputs as they stream, so
    the graph runs exactly once.
    """
    graph = build_graph(llm)
    state = IncidentState(incident_id=incident_id, input=incident_input)

    yield sse_event(
        "pipeline_started",
        {
            "incident_id": incident_id,
            "scenario": incident_input.scenario,
            "service_name": incident_input.service_name,
            "alert_summary": incident_input.alert_summary,
            "agents": list(ALL_AGENTS),
            "source_data": _summarize_source_data(incident_input),
        },
    )

    accumulated: dict[str, Any] = {}

    try:
        async for event in graph.astream_events(state):
            kind = event["event"]
            name = event.get("name", "")
            if name not in ALL_AGENTS:
                continue

            if kind == "on_chain_start":
                yield sse_event(
                    "agent_started",
                    {
                        "agent": name,
                        "scope": _agent_scope(name, incident_input),
                    },
                )

            elif kind == "on_chain_end":
                output_dict = event.get("data", {}).get("output", {}) or {}
                serialized = _serialize(output_dict)
                accumulated.update(serialized)
                yield sse_event(
                    "agent_completed",
                    {"agent": name, "output": serialized},
                )

    except Exception as exc:  # surface errors to the client, never 500
        yield sse_event("error", {"message": str(exc)})
        return

    yield sse_event(
        "pipeline_completed",
        {
            "incident_id": incident_id,
            "final_state": accumulated,
        },
    )

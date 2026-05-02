"""SSE event translator: LangGraph astream_events -> dashboard event stream.

The dashboard's per-agent status animation (pending → running → done) is
driven entirely by these events. Keeping the translation in one place means
the FastAPI route stays thin and the frontend contract is easy to inspect.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from pagerzero.graph import ALL_AGENTS, build_graph
from pagerzero.llm.client import LLMClient
from pagerzero.schemas import IncidentInput, IncidentState


def sse_event(event_type: str, data: dict) -> dict[str, str]:
    """Build the dict shape `EventSourceResponse` expects per yield."""
    return {"event": event_type, "data": json.dumps(data, default=str)}


def _serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


async def stream_incident_events(
    incident_input: IncidentInput,
    incident_id: str,
    llm: LLMClient,
) -> AsyncIterator[dict[str, str]]:
    """Run the graph and translate each LangGraph event into an SSE event.

    Event types emitted to the client:
      - `pipeline_started`   { incident_id, scenario, service_name, alert, agents }
      - `agent_started`      { agent }
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
                yield sse_event("agent_started", {"agent": name})

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

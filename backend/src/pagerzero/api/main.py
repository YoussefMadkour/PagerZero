"""PagerZero FastAPI app.

Run locally with:
    uv run uvicorn pagerzero.api.main:app --reload --port 8000

Endpoints:
    GET  /api/health                            health check
    GET  /api/scenarios                         list available demo scenarios
    GET  /api/incidents/stream?scenario=NAME    SSE stream of agent events
"""

from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from pagerzero.api.events import stream_incident_events
from pagerzero.data.scenario_loader import available_scenarios, load_scenario
from pagerzero.llm import MockLLMClient
from pagerzero.llm.client import LLMClient

app = FastAPI(title="PagerZero", version="0.1.0")

# Permissive CORS for the hackathon demo. Tighten before any non-demo use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_llm_client(scenario: str) -> LLMClient:
    """Pick the LLM backend based on environment.

    Local dev / Day 0-3: returns MockLLMClient with the requested scenario.
    From Day 4 onward: when PAGERZERO_LLM_BACKEND=vllm is set and a
    VLLMClient is implemented, this will route to real Qwen.
    """
    backend = os.getenv("PAGERZERO_LLM_BACKEND", "mock").lower()
    if backend == "mock":
        latency = float(os.getenv("PAGERZERO_MOCK_LATENCY_S", "0.4"))
        return MockLLMClient(scenario=scenario, simulated_latency_seconds=latency)
    raise ValueError(f"Unknown LLM backend: {backend}")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health + which LLM backend is wired in.

    The dashboard reads `llm_backend` to render an honest HardwareBadge —
    it shows "Mock LLM" while running against MockLLMClient and switches
    to "AMD MI300X · Qwen2.5-72B" only when the real VLLMClient is in use.
    Lying to the judges about which compute is doing the thinking would
    sink the whole AMD story.
    """
    backend = os.getenv("PAGERZERO_LLM_BACKEND", "mock").lower()
    return {"status": "ok", "llm_backend": backend}


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, str]]:
    """Lightweight metadata for the dashboard's scenario picker."""
    out: list[dict[str, str]] = []
    for name in available_scenarios():
        incident = load_scenario(name)
        out.append(
            {
                "id": name,
                "service_name": incident.service_name,
                "alert_summary": incident.alert_summary,
            }
        )
    return out


@app.get("/api/incidents/stream")
async def stream_incident(
    scenario: str = Query(..., description="Scenario id from /api/scenarios"),
) -> EventSourceResponse:
    """SSE endpoint that runs the agent pipeline and streams per-agent events.

    The dashboard opens this with `new EventSource('/api/incidents/stream?scenario=...')`.
    """
    if scenario not in available_scenarios():
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {scenario}")

    incident_input = load_scenario(scenario)
    incident_id = f"inc_{uuid.uuid4().hex[:12]}"
    llm = get_llm_client(scenario)

    return EventSourceResponse(
        stream_incident_events(incident_input, incident_id, llm),
    )

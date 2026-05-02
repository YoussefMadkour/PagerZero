# ADR 0001 — Orchestration framework: LangGraph

**Status:** Accepted · 2026-05-01
**Context:** AMD Developer Hackathon Track 1 (AI Agents). Solo build, 9-day window.

## Decision

Use **LangGraph 1.x** for the multi-agent pipeline.

## Why this and not the alternatives

PagerZero is a structured DAG: three independent specialists (logs / metrics / deploys) run in parallel, a synthesizer reads all three, then a remediation step closes it out. Outputs are strict Pydantic JSON consumed by a UI. Latency budget is 90 seconds end-to-end. The dashboard needs per-node `running → done` events to drive the live agent-card animation.

| Framework | Fit for PagerZero |
|---|---|
| **LangGraph** ✅ | Explicit graph with parallel node execution. State is a Pydantic model; non-overlapping fields merge cleanly, conflicting ones use reducers. `astream_events` emits per-node lifecycle events that map 1:1 to the SSE feed driving the dashboard. Deterministic, low-magic, OpenAI-compat clients (vLLM on AMD) drop in via the standard `openai` SDK. LangGraph 1.x is stable. |
| **CrewAI** ❌ | Role-based "agents + tasks + crew" tuned for *creative collaboration* (researcher → writer → editor). Parallel execution is bolted-on; state is implicit; forcing strict Pydantic outputs fights the framework's higher-level abstractions. Wrong shape for a structured DAG with strict JSON contracts. |
| **AutoGen** ❌ | Conversational multi-agent (group-chat). Strong for code execution and reasoning loops where agents debate. We don't want our agents to talk to each other — we want three independent specialists to produce JSON in parallel, then a synthesizer reads all three. Group-chat overhead works against the 90-second latency budget. |

The hackathon explicitly lists all three as eligible, so this is purely a fit-for-problem call, not a points call.

## Consequences

- LangGraph events are the source of truth for agent status. The state model does **not** track status itself; the SSE endpoint translates `on_chain_start` / `on_chain_end` / `on_chain_error` into per-agent UI updates.
- Each node returns a partial state dict containing only its own field — no reducers needed for the agent output fields because they don't overlap.
- LLM client is injected via closure when the graph is built (`build_graph(llm: LLMClient)`), so swapping `MockLLMClient` for `VLLMClient` at deploy time touches one call site.
- If a future agent needs to write to a shared field (e.g. multiple agents tagging severity), we use `Annotated[T, reducer]` on that specific field.

## Roadmap notes (out of scope for the hackathon)

- A conversational triage agent that asks the on-call engineer clarifying questions could be added later as an AutoGen group-chat sidecar — orthogonal to the core DAG and easy to bolt on without touching the LangGraph pipeline.

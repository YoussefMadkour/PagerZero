# PagerZero

> Five large-context language model agents read your incident in parallel. Root cause in 90 seconds.

Built for the [AMD Developer Hackathon](https://lablab.ai/event/amd-developer-hackathon) — Track 1: AI Agents & Agentic Workflows.

---

## What it does

When a service goes down, on-call engineers spend ~45 minutes manually reading logs, checking metrics, and guessing what changed. PagerZero collapses that work into ~90 seconds.

The moment an alert fires:

1. **Log Analysis** — finds anomaly clusters across 8,000+ log lines in a *single* 128k-context pass. No chunking, no map-reduce, no information lost between line 1 and line 8,000.
2. **Metrics Correlator** — identifies inflection points and leading-vs-lagging indicators across the 2-hour time series.
3. **Deployment Tracker** — correlates recent deploys against the incident timeline and flags suspicious code paths.
4. **Root Cause** — synthesizes all three signal streams into ranked hypotheses with confidence scores and per-source evidence citations.
5. **Remediation** — generates actionable CLI commands, rollback procedure, and a drafted incident report.

Agents 1, 2, and 3 run **concurrently**. Agent 4 fans them in. Agent 5 closes it out.

## Why this needs MI300X — the compute story

This isn't an API call with AMD branding stapled on. The hardware is load-bearing.

- **128k-token single pass.** Each agent sees the entire incident in one prompt. 8,000 log lines plus structured metrics plus deploy diffs lands around 60-70k input tokens. Smaller-context models force you to chunk and map-reduce, which destroys the cross-line correlation that makes root-cause analysis work.
- **Five concurrent large-context inferences.** Three of the agents read the full incident in parallel. MI300X's **192 GB HBM3** and **~5.3 TB/s memory bandwidth** are what makes parallel multi-agent inference at this scale latency-feasible. You're not bottlenecked moving the KV cache.
- **Latency budget is 90 seconds, hard.** A real on-call engineer waiting on this won't tolerate 4-minute analysis. On CPU or a smaller GPU, you either chunk (and lose signal) or serialize the agents (and miss the budget). Neither survives production.

The Hugging Face Space and AMD Developer Cloud hosting are *deployment plumbing* — required for prize eligibility, not what makes the system work. The differentiator is the memory and bandwidth profile of the underlying compute.

## Stack

| Layer | Choice |
|---|---|
| Model | [Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct) — 128k context |
| Serving | vLLM on ROCm |
| Compute | AMD Instinct MI300X |
| Orchestration | LangGraph (parallel branches 1/2/3 → 4 → 5) — see [ADR 0001](docs/adr/0001-orchestration-framework.md) |
| Backend | FastAPI + Server-Sent Events |
| Frontend | Next.js 16 + Tailwind 4 |
| Hosting | AMD Developer Cloud (backend) + Hugging Face Space (frontend) |

See [ADR 0002](docs/adr/0002-amd-compute-narrative.md) for how the compute story is reflected in the product UI (hardware badge, per-agent token counts, parallel-vs-sequential timing visual).

## Repo layout

```
backend/    Python 3.12 — FastAPI + LangGraph agent pipeline
frontend/   Next.js 16 dashboard with live agent status SSE
infra/      vLLM launch scripts and AMD deploy helpers
docs/       ADRs and architecture notes
```

## Local development

Prereqs: Python 3.12, Node 22, [uv](https://github.com/astral-sh/uv).

```bash
# Backend (uses MockLLMClient — no GPU needed)
cd backend
uv sync
uv run python scripts/generate_scenarios.py
uv run pytest                                       # 16 tests, ~1s
uv run uvicorn pagerzero.api.main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev                                         # http://localhost:3000
```

The `MockLLMClient` returns deterministic canned responses keyed by scenario, so the full pipeline runs in seconds with zero GPU. The real `VLLMClient` (Qwen2.5-72B on MI300X) drops in via a single env var: `PAGERZERO_LLM_BACKEND=vllm`.

## Demo scenarios

| Scenario | What broke | What it tests |
|---|---|---|
| `scenario_a_memory_leak` | Session cache deploy removed eviction; heap exhaustion 47 min later | Cross-source synthesis (logs + metrics + deploy all point at one commit) |
| `scenario_b_pool_exhaust` | Flash-sale traffic exhausted the database connection pool | Honest "no culprit deploy" path — capacity event, not code event |
| `scenario_c_cascade` | Disabled circuit breaker amplified an upstream slowdown into a full outage | Multi-hypothesis ranking with a clear primary and a secondary investigation |

## License

MIT — see [LICENSE](./LICENSE).

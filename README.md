# PagerZero

> Autonomous incident response. Five parallel agents on AMD MI300X. Root cause in 90 seconds.

Built for the [AMD Developer Hackathon](https://lablab.ai/event/amd-developer-hackathon) — Track 1: AI Agents & Agentic Workflows.

---

## What it does

When a service goes down, on-call engineers spend ~45 minutes manually reading logs, checking metrics, and guessing what changed. PagerZero does this in 90 seconds.

Five specialized LLM agents run in parallel the moment an alert fires:

1. **Log Analysis** — finds anomaly clusters across 8,000+ log lines in a single 128k-context pass
2. **Metrics Correlator** — identifies inflection points and leading-vs-lagging indicators
3. **Deployment Tracker** — correlates recent deploys against the incident timeline
4. **Root Cause** — synthesizes all three signal streams into ranked hypotheses with confidence scores
5. **Remediation** — generates actionable commands and a drafted incident report

## Stack

- **Model:** [Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct) (128k context)
- **Serving:** vLLM on ROCm
- **Compute:** AMD Instinct MI300X via AMD Developer Cloud
- **Orchestration:** LangGraph (parallel execution for agents 1/2/3, then 4 → 5)
- **Backend:** FastAPI + Server-Sent Events for live agent status
- **Frontend:** Next.js 16 + Tailwind 4
- **Demo hosting:** Hugging Face Spaces

## Why AMD

Processing 8,000 log lines + 2-hour metric history + deployment diffs in a single 128k-token context — and running five agents in parallel — exercises the memory bandwidth that MI300X is built for. This is not an API call with AMD as decoration; the compute is load-bearing.

## Repo layout

```
backend/    Python 3.12 — FastAPI + LangGraph agent pipeline
frontend/   Next.js 16 dashboard with live agent status SSE
infra/      vLLM launch scripts and AMD deploy helpers
docs/       Architecture diagrams, decisions
```

## Local development

Prereqs: Python 3.12, Node 22, uv.

```bash
# Backend (uses MockLLMClient — no GPU needed)
cd backend
uv sync
uv run python scripts/generate_scenarios.py
uv run pytest

# Frontend
cd frontend
npm install
npm run dev
```

The `MockLLMClient` returns deterministic canned responses keyed by scenario, so the full LangGraph pipeline + FastAPI + Next.js dashboard runs locally in seconds with zero AMD credit burn. The real `VLLMClient` (Qwen2.5-72B) is swapped in only at deployment.

## Demo scenarios

| Scenario | What broke |
|---|---|
| `scenario_a_memory_leak` | Session cache deploy removed eviction; heap exhaustion 47 min later |
| `scenario_b_pool_exhaust` | Flash-sale traffic exhausted the database connection pool |
| `scenario_c_cascade` | Disabled circuit breaker caused retry-storm cascade |

## License

MIT — see [LICENSE](./LICENSE).

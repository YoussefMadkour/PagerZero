# PagerZero — current status

_Last updated: 2026-05-02_

A live status tracker so we can pick up where we left off. The full plan
lives at `~/.claude/plans/i-want-to-build-replicated-yao.md`; this is the
short-form version.

---

## What's done

### Backend (`/backend`)
- Pydantic v2 schemas for every agent IO + the LangGraph state — [schemas.py](../backend/src/pagerzero/schemas.py)
- `LLMClient` ABC with `MockLLMClient` (canned per-scenario fixtures) — [llm/](../backend/src/pagerzero/llm/)
- All five agents implemented as LangGraph nodes with separate prompts — [agents/](../backend/src/pagerzero/agents/)
- Full graph: `START → [3 parallel] → root_cause → remediation → END` — [graph.py](../backend/src/pagerzero/graph.py)
- FastAPI app with `/api/health`, `/api/scenarios`, and SSE `/api/incidents/stream` — [api/](../backend/src/pagerzero/api/)
- Per-scenario fixtures for all three demo incidents — [llm/fixtures/](../backend/src/pagerzero/llm/fixtures/)
- Three full demo scenarios with synthetic logs/metrics/deploys — [data/scenarios/](../backend/src/pagerzero/data/scenarios/)
- 16 tests passing in <1.5s, ruff clean

### Frontend (`/frontend`)
- Next.js 16 + Tailwind 4 + Geist Sans/Mono
- Design system: monochrome surfaces, single amber accent, sharp 6px radii — [globals.css](../frontend/src/app/globals.css)
- Dashboard page wires Header, ScenarioPicker, AlertBanner, AgentCard×5, RootCausePanel, RemediationPanel, ParallelTimingChart
- `useIncidentRun` hook drives the SSE state machine — [lib/useIncidentRun.ts](../frontend/src/lib/useIncidentRun.ts)
- Hardware badge in header is the AMD compute story made visible
- ParallelTimingChart shows observed-vs-sequential speedup post-run

### Docs
- [ADR 0001](adr/0001-orchestration-framework.md) — LangGraph over CrewAI/AutoGen
- [ADR 0002](adr/0002-amd-compute-narrative.md) — AMD compute, not hosting, is the differentiator

### Tooling
- `scripts/dev.sh` — one-command boot for both servers with cleanup trap
- Mock-first dev flow: full pipeline runs in <2s on a laptop, no GPU

---

## What still needs to be done

### Before AMD spinup — UX credibility
- [x] Source-data ingest panel (lines/tokens/points/deploys counts)
- [x] Per-agent scope badges on each AgentCard
- [x] Realistic incident IDs in scenario labels (`PAY-2479` etc.)
- [x] Spacebar shortcut to fire run + dropdown click-outside-to-close
- [x] One-line specialization per agent + role chip (`specialist · specialist · specialist · synthesizer · operator`) so the multi-agent architecture reads at a glance
- [x] Visible error banner when the SSE run fails (was silent before)
- [x] Honest HardwareBadge: "Mock LLM · dev mode" in dev, "Qwen2.5-72B · MI300X" only when really running on AMD
- [x] SuspectCommitCard surfaces the full deploy detail (author, timestamp, files changed, diff summary) for the commit the agents flagged
- [ ] Click-into AgentDetail slide-over (full input the agent saw + full output + the prompt). Polish item.
- [ ] Log-tail animation during ingestion (cosmetic, sells the live feel)

### "Does this look fabricated?" — design decision

**Question:** should we set up a real-looking GitHub repo (`pagerzero-demo/payment-service` with the bad commit actually pushed) so the demo doesn't feel staged?

**Decision: no.** Approach C from the discussion — keep the system self-contained, but make the demo data have the **texture of real ops data** so it reads as authentic. Specifically:

- Author emails (`alice@payco.network`), commit messages, file paths, diff summaries are already in the scenario data and now render in the dashboard via SuspectCommitCard.
- Incident IDs follow real tracker conventions (`PAY-2479`, `CHK-1138`).
- The commands in the Remediation panel are real `kubectl` / `git` invocations, not pseudo-code.
- All times, severities, and confidence numbers are consistent across the agent outputs.

A fake live GitHub repo would add ~half a day of work and one more thing that can break on stage. The texture-of-real-data approach gets 90% of the credibility for ~5% of the work. If a judge asks "is this real data?", the honest answer is: "synthetic incidents we generated to make the demo deterministic — the agent code, the LangGraph orchestration, and the AMD compute path are all real."

### When you spin up the AMD instance
1. **Provision** — sign in to AMD Developer Cloud, spin up an MI300X instance, note the public IP and SSH key path.
2. **Install ROCm + vLLM** on the instance:
   ```bash
   # On the MI300X box
   pip install vllm   # ROCm wheels via the official AMD index
   ```
3. **Pull the model** (first run takes 10-20 min):
   ```bash
   vllm serve Qwen/Qwen2.5-72B-Instruct \
       --max-model-len 128000 \
       --port 8000 \
       --dtype auto
   ```
   Check `infra/vllm-server.sh` (TBD) — wrap the exact recommended flags from AMD's docs.
4. **Smoke test from your laptop**:
   ```bash
   curl -s http://AMD_INSTANCE_IP:8000/v1/models | jq
   curl -s http://AMD_INSTANCE_IP:8000/v1/chat/completions \
     -H "content-type: application/json" \
     -d '{"model":"Qwen/Qwen2.5-72B-Instruct","messages":[{"role":"user","content":"hello"}]}'
   ```
5. **Implement `VLLMClient`** in `backend/src/pagerzero/llm/vllm.py`:
   - Implements `LLMClient`
   - Uses the `openai` SDK pointed at `PAGERZERO_VLLM_BASE_URL`
   - Uses vLLM's guided JSON / outlines mode so output stays Pydantic-valid
   - Add to `get_llm_client()` in `api/main.py` behind `PAGERZERO_LLM_BACKEND=vllm`
6. **Tune prompts** — run each scenario against real Qwen and iterate on the system prompts in `agents/prompts/`. Things that fail on real LLM but worked on mock:
   - JSON drift (extra prose, missing fields)
   - Hallucinated commit SHAs
   - Over-confident severity scores
   - Inconsistent affected_components naming
7. **Capture real numbers** — record actual tokens/sec, single-pass latency, and per-agent wall-clock times. These replace the mock-driven numbers in the ParallelTimingChart and become the credible AMD slide.
8. **CRITICAL**: shut down the instance whenever not actively using it. MI300X burns through the $100 credit fast.

### Deployment (Days 6-7)
- [ ] Backend deploy on AMD Developer Cloud (gunicorn + uvicorn behind nginx)
- [ ] Frontend deploy as a Hugging Face Space (Docker SDK)
- [ ] CORS verification across HF Space → AMD backend
- [ ] End-to-end test of all three scenarios on the public URL
- [ ] First social post tagging @AIatAMD @lablab

### Submission (Days 8-9)
- [ ] 5-minute demo video (script in master plan)
- [ ] Cover image (16:9 PNG)
- [ ] Slide deck (PDF)
- [ ] Fill lablab.ai submission form
- [ ] Second social post with demo GIF
- [ ] Submit before May 10 22:00 EEST (target submission by 18:00 for 4h buffer)

---

## Risks / things to watch

1. **Real Qwen output quality vs mock fixtures.** The mock outputs are hand-tuned to be ideal; real outputs may need significant prompt iteration, especially for the synthesizer (Agent 4) which has to read three structured reports and not contradict any of them.
2. **MI300X credit burn.** Treat the instance like a hotel — check out every night.
3. **vLLM + ROCm + Qwen-72B first-time setup.** Expect Day 3 to disappear into this. Have Qwen2.5-32B as a fallback if blocked past EOD.
4. **HF Space ↔ AMD backend latency / CORS.** Test on Day 6, not the day-of submission.

## Demo readiness gate (when can we record the video?)

All of these need to be true:
- Real Qwen running on MI300X via vLLM
- Backend deployed to AMD Cloud (not local)
- Frontend deployed as HF Space
- All three scenarios run end-to-end on the public URLs in <100s each
- ParallelTimingChart shows observed numbers from real runs, not mock latencies
- Hardware badge shows live token counts during a run

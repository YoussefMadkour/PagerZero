# ADR 0002 — AMD compute story is the differentiator, not AMD hosting

**Status:** Accepted · 2026-05-01
**Context:** Same hackathon as ADR 0001. Reframes how AMD shows up in the product and the pitch.

## Decision

The AMD story is **compute**: 128k-context single-pass inference and five concurrent large-context agents on MI300X memory bandwidth. **Not** "we deployed on AMD Developer Cloud." Cloud hosting is required for prize eligibility but is not load-bearing in the narrative.

## Why this matters

Hosting on AMD Developer Cloud is plumbing — every Track 1 entrant will say it. The judges (engineers from Netflix, Apple, Amazon, JP Morgan, AMD) will tune it out. The framing that *does* survive their filter is hardware-specific: a problem shape that genuinely needs the memory and bandwidth profile of MI300X and would degrade on alternatives.

PagerZero's actual problem shape is exactly that:

| Property | Why MI300X matters |
|---|---|
| 128k-token single-pass log analysis | Smaller-context models force chunking, which destroys cross-line correlation — the whole point of root-cause analysis. |
| Three parallel agents, each consuming the full incident | Five concurrent large-context inferences. 192 GB HBM3 + ~5.3 TB/s bandwidth keeps the KV cache movement off the critical path. |
| 90-second hard latency budget | On CPU or smaller GPU you must serialize agents and miss the budget, or chunk and lose signal. Neither survives production on-call. |

Every one of those statements is defensible against an AMD engineer asking hard questions during pitch Q&A.

## Consequences for the product

This narrative isn't ornamental — it gets baked into three concrete UI elements so judges *see* the compute working, not just hear it on a slide:

1. **Hardware badge** in the dashboard header. Live readout while a run is in flight: `Qwen2.5-72B · MI300X · 8,247 lines · 62k tokens · single pass`. Static when idle, live counts when running.
2. **Per-agent metrics** on each AgentCard: input tokens, output tokens, wall-clock seconds. Visible in the same card as the agent's status.
3. **Parallel-vs-sequential** comparison appears once a run completes. Two-bar visual: "Sequential would have been 5 × max_t ≈ Xs · Parallel ran in Ys." The Y is observed; the X is `5 × max(observed agent times)`. This is the MI300X story made visual.

## Consequences for the pitch

- 30-second AMD slot in the 5-minute video leads with token counts and parallel inference, not "we used AMD's cloud."
- README leads with the compute story and lists hosting as plumbing. Done in this commit.
- When numbers go in (Day 4, after first real Qwen runs), they replace any placeholder estimates. No "approximately" without a measurement to back it.

## What this does NOT change

- The graph architecture (ADR 0001 stands).
- The deployment plan — backend still ships on AMD Developer Cloud, frontend still ships as a HF Space, because both are prize-eligibility requirements.
- The mock-first development flow — `MockLLMClient` still works for everything except the AMD-specific timing numbers.

The change is purely in framing and in three pieces of UI that surface the compute reality of the run.

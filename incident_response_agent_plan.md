# Incident Response Agent — AMD Developer Hackathon Master Plan

**Hackathon:** AMD Developer Hackathon  
**Track:** Track 1 — AI Agents & Agentic Workflows  
**Deadline:** May 10, 2026  
**Prize target:** Track 1 First Place ($2,500) + Grand Prize ($5,000) + Build in Public GPU  
**Stack:** Qwen2.5-72B · vLLM · ROCm · AMD MI300X · LangGraph · Next.js · Hugging Face  

---

## The One-Line Pitch

> "When your payment service goes down at 3am, your on-call engineer spends 45 minutes manually reading logs, correlating metrics, and guessing what broke. Our agent does it in 90 seconds — running entirely on AMD."

---

## Why This Will Win

### 1. It plays to your actual background
You have built DevOps infrastructure. You have been paged when things break. You understand the pain from first principles. When an AMD judge or a Netflix/Apple/Amazon judge asks a hard technical question about log correlation at scale, you answer from experience — not a YouTube tutorial. That authenticity is worth 2 scoring points over someone faking domain expertise.

### 2. The AMD story is genuine and unjudgeable
Processing 10,000 log lines across multiple services simultaneously, running five parallel agents over 128K-token context windows, correlating time-series metrics at speed — this is textbook AMD MI300X workload. Qwen2.5-72B's 128K context window on AMD's memory-bandwidth-optimized hardware is the exact technical story AMD's own engineers will validate. You can say "this would timeout on CPU, here's the processing time comparison" and it holds up.

### 3. The demo lands in 90 seconds with zero explanation needed
You click "Simulate Incident." A red alert fires. Five agents light up in parallel. 90 seconds later a judge from JP Morgan or PayPal reads: "Root cause identified. Rollback command generated. Incident report drafted." They don't need to understand the code. They understand the problem immediately because they run software companies.

### 4. Universal pain — every judge in the room has felt this
The judge panel includes engineers from Netflix, Apple, Amazon, Workday, IBM, PayPal, Meta. Every single one of them has been on-call. Every single one has done exactly this manual work at some point. This is not a niche enterprise problem. It is the most universally felt engineering pain in the industry.

### 5. It stacks three prizes simultaneously
- Track 1 first place ($2,500) — strongest agentic workflow submission
- Grand Prize ($5,000) — overall best project if the demo lands hard
- Build in Public GPU reward — two tweets about killing 3am on-call incidents will get organic engagement without effort

### 6. Qwen is a technology partner here
Using Qwen models is explicitly encouraged and recognized by judges. Qwen2.5-72B is the right model for this — 128K context, strong reasoning, available on AMD MI300X via vLLM. Mentioning Qwen by name in your pitch gets you alignment credit with the sponsoring partner.

### 7. Nobody else will build this
Every other team will reach for: chatbot, RAG system, code generator, or a fine-tuning demo. Incident response is invisible on the idea list because it requires DevOps domain knowledge most participants don't have. You have it.

---

## Competition Rules — What Matters

| Rule | Impact on your build |
|---|---|
| Must use AMD Developer Cloud | Deploy your backend on AMD cloud — not Vercel, not local. This is mandatory for prize eligibility. |
| $100 in AMD credits provided | Enough for several days of MI300X usage — budget carefully, spin down when not testing |
| Track 1 focus: AI Agents | LangGraph multi-agent pipeline checks this box completely |
| Hugging Face Space required | Deploy web demo as HF Space in the event organization — required for HF prize |
| Build in Public bonus | 2+ social posts tagging @AIatAMD and @lablab on X or LinkedIn |
| GitHub must be public | MIT license, README with setup instructions |
| Demo URL required | Live, accessible, interactive — the Hugging Face Space covers this |
| Video max 5 minutes | Intro → architecture → demo → business case |
| Submission deadline | May 10, 2026 — do not miss this |
| On-site is invite-only | Build online, don't count on being invited on-site |

---

## Judging Criteria — How To Score Maximum

| Criterion | Weight | How Argus nails it |
|---|---|---|
| Application of Technology | 25% | 5 parallel Qwen agents on AMD MI300X, vLLM for serving, LangGraph orchestration, 128K context window utilized |
| Business Value | 25% | Every engineering team on earth. $50K+ average cost per major incident. Clear SaaS model. |
| Presentation | 25% | 90-second demo, red alert → root cause, zero explanation needed, judges personally relate |
| Originality | 25% | Nobody builds incident response. DevOps domain knowledge barrier keeps competition out. |

---

## Project Description

### The Problem

When a service goes down, an on-call engineer gets paged. What happens next is always the same:

- Open the logging dashboard, manually scroll through thousands of lines
- Check the metrics dashboard, try to identify when degradation started
- Look at recent deployments and commits, guess what changed
- Form a hypothesis, attempt a fix, hope it works
- Write an incident report at 5am when it's finally resolved

Average time to root cause identification: **45 minutes**  
Average cost of a 1-hour outage for a mid-size company: **$100,000+**  
Number of times this process has been automated end-to-end: **zero**

### The Solution

An autonomous incident response agent that activates the moment an alert fires. Five specialized agents process simultaneously, each owning one dimension of the investigation. 90 seconds later the engineer has a root cause, a remediation plan, and a drafted incident report.

The engineer goes from "I have no idea what's broken" to "here's what broke, here's why, here's how to fix it" — in the time it takes to make a coffee.

### Why AMD

Qwen2.5-72B running on AMD MI300X via vLLM processes 10,000 log lines in a single context pass — AMD's memory bandwidth architecture makes this throughput possible at latency that matters. Five agents running in parallel over large context windows is the exact workload MI300X is optimized for. This is not a Gemini API call with AMD as decoration. The compute architecture is load-bearing.

---

## The Five Agents

### Agent 1: Log Analysis Agent
**Input:** Last N log lines from the affected service (up to 10,000 lines)  
**Model:** Qwen2.5-72B with 128K context (processes all logs in one pass)  
**Job:** Identify error clusters, anomaly patterns, frequency spikes, stack traces, correlated error chains  
**Output:** Structured JSON — top 5 anomaly patterns, error frequency timeline, first occurrence timestamp, affected components  
**AMD story:** 10,000 log lines in a single context pass. This is the 128K context window in use. CPU inference would take 4+ minutes. AMD MI300X does it in under 20 seconds.

### Agent 2: Metrics Correlator Agent
**Input:** CPU, memory, latency, error rate, throughput time series (last 2 hours)  
**Model:** Qwen2.5-72B  
**Job:** Identify inflection points, leading vs lagging indicators, correlation between metric degradations, blast radius  
**Output:** Structured JSON — incident start timestamp, primary degraded metric, correlated metrics, severity score 0-100  
**AMD story:** Runs in parallel with Agent 1 — both fire simultaneously. Parallel execution on AMD MI300X.

### Agent 3: Deployment Tracker Agent
**Input:** Recent deployment history — commits, config changes, dependency updates, feature flags (last 24 hours)  
**Model:** Qwen2.5-72B  
**Job:** Correlate deployment timestamps against incident start. Identify what changed immediately before degradation.  
**Output:** Structured JSON — ranked list of deployment events by correlation strength, change diff summaries, suspicious commits flagged  
**AMD story:** Processes entire git diff and deployment log in one pass. Fast enough to be useful during an active incident.

### Agent 4: Root Cause Agent (the synthesizer)
**Input:** Outputs from Agents 1, 2, and 3 combined  
**Model:** Qwen2.5-72B  
**Job:** Reason across all three signal streams simultaneously. Form a ranked hypothesis list with confidence scores. Identify the most likely cause with supporting evidence from each agent's findings.  
**Output:** Structured JSON — ranked root cause hypotheses (1-3), confidence percentage per hypothesis, evidence citations from each agent, affected service map  
**AMD story:** This is the reasoning-heavy agent. Long-context synthesis across three structured reports. Benefits directly from AMD's compute density.

### Agent 5: Remediation Agent
**Input:** Root cause hypothesis from Agent 4 + original system context  
**Model:** Qwen2.5-72B  
**Job:** Generate specific, actionable remediation steps. Produce exact commands where possible. Draft incident report. Preview stakeholder notification.  
**Output:** 3-section deliverable — immediate mitigation steps with commands, rollback procedure if applicable, drafted incident report in standard format  
**AMD story:** Generates deployment-ready rollback commands and runbook entries in seconds. In production this integrates with your deployment tooling.

---

## LangGraph Orchestration

```
Alert Trigger
      │
      ▼
  ┌───────────────────────────────────┐
  │     PARALLEL EXECUTION LAYER      │
  │  Agent 1  │  Agent 2  │  Agent 3  │
  │   Logs    │  Metrics  │  Deploys  │
  └─────┬─────┴─────┬─────┴─────┬─────┘
        │           │           │
        └─────┬─────┘           │
              │◄────────────────┘
              ▼
         Agent 4: Root Cause
         (synthesizes all three)
              │
              ▼
         Agent 5: Remediation
         (actions + report)
              │
              ▼
      Dashboard Update
      Incident Report Generated
      Slack/Email Preview Sent
```

Agents 1, 2, and 3 fire simultaneously via LangGraph's parallel node execution. Agent 4 waits for all three to complete before synthesizing. Agent 5 runs after Agent 4. Total pipeline: ~90 seconds.

---

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Qwen2.5-72B | 128K context, strong reasoning, Qwen is a technology partner |
| Serving | vLLM on ROCm | Native AMD GPU serving, optimized for MI300X memory bandwidth |
| Compute | AMD MI300X via AMD Developer Cloud | Required for prize eligibility, genuine performance story |
| Orchestration | LangGraph | Parallel agent execution, state management, retry logic |
| Backend | Python FastAPI | Agent API layer, alert simulation endpoint |
| Frontend | Next.js + Tailwind | Incident dashboard, agent status cards, report display |
| Demo hosting | Hugging Face Space | Required for HF prize, public demo URL |
| Social sharing | X / LinkedIn | Build in Public bonus — 2 posts minimum |

---

## Fake Incident Scenarios — Demo Data

Create these before Day 1. Each scenario needs: fake logs, fake metrics CSV, fake deployment history JSON.

### Scenario A: Memory Leak (the wow demo)
**What happened:** A new deployment introduced a memory leak in the payment service. Memory climbed steadily for 45 minutes before latency spiked and error rates exploded.

**Logs to fake:** 8,000 lines. Mix of normal requests and gradually increasing GC pause warnings, then OutOfMemoryError stack traces starting at line 6,500.

**Metrics to fake:** Memory: steady climb from 2GB to 7.8GB over 45 minutes. Latency: flat until memory hits 90%, then spikes from 120ms to 4,200ms. Error rate: 0% until minute 43, then 847% above baseline.

**Deployment history:** One deployment 47 minutes before incident. Commit message: "Optimized session caching for faster auth."

**Expected agent output:** "Memory leak introduced in commit abc123 — 87% confidence. Session cache implementation does not release objects on session expiry. Immediate mitigation: restart service instances. Rollback to previous deployment. Long-term fix: implement cache TTL and explicit session cleanup."

### Scenario B: Database Connection Pool Exhaustion
**What happened:** Traffic spike during a flash sale exhausted the database connection pool. All new requests timeout waiting for a connection.

**Logs to fake:** 5,000 lines. Increasing "connection timeout waiting for pool" errors. No deployment changes. Metrics show traffic 340% above baseline.

**Expected output:** "Connection pool exhaustion — 94% confidence. Traffic spike exceeded pool limit of 50 connections. Immediate: increase pool size to 200, enable connection queuing. Long-term: implement read replicas."

### Scenario C: Cascading Failure (advanced demo)
**What happened:** A config change disabled circuit breakers. When the recommendation service became slow, the product page service kept retrying, exhausting its own thread pool, taking down the entire storefront.

**Logs to fake:** 12,000 lines across two services. Recommendation service slowdown in first 3,000 lines. Product service retry storms in lines 3,000-8,000. Thread pool exhaustion errors from line 8,000 onward.

**Expected output:** "Cascading failure triggered by circuit breaker misconfiguration — 91% confidence. Config change at 14:32 disabled circuit breaker on product→recommendation call. Re-enable circuit breaker via config rollback. Recommendation service slowdown (root cause TBD) requires separate investigation."

---

## Six-Day Build Plan

### Day 1 — Infrastructure Setup
- Sign up for AMD AI Developer Program
- Get $100 credits activated
- Spin up AMD MI300X instance on AMD Developer Cloud
- Install ROCm, vLLM
- Get Qwen2.5-72B loaded and serving via vLLM
- Test: send a 5,000-line log file to Qwen, get structured output back
- Generate fake log data for all three scenarios

**Milestone:** Qwen reads 5,000 log lines and returns structured anomaly JSON

### Day 2 — Core Agents (Log + Metrics)
- Build Log Analysis Agent — LangGraph node, structured prompt, JSON output schema
- Build Metrics Correlator Agent — time series input, inflection point detection
- Run both on Scenario A data
- Verify structured outputs are correct and consistent

**Milestone:** Agents 1 and 2 produce correct JSON from Scenario A data

### Day 3 — Complete Pipeline
- Build Deployment Tracker Agent
- Build Root Cause Agent — synthesizes all three inputs, confidence scoring
- Build Remediation Agent — generates commands, drafts incident report
- Wire all five agents in LangGraph with parallel execution for Agents 1/2/3
- Run full pipeline on all three scenarios

**Milestone:** Full 5-agent pipeline produces end-to-end output for all three scenarios

### Day 4 — Dashboard UI
- Next.js frontend — incident alert panel, agent status cards with live progress
- Root cause display with confidence scores
- Remediation steps panel with copy-able commands
- Drafted incident report section
- Simulate Incident button per scenario
- Polish UI — dark theme, real-time agent status animation

**Milestone:** Frontend runs full demo of Scenario A with live agent status updates

### Day 5 — Deploy + HF Space
- Deploy backend to AMD Developer Cloud (not local, not Vercel)
- Create Hugging Face Space in the event organization
- Connect frontend to AMD backend
- Test all three scenarios end-to-end on deployed version
- Record AMD processing time for pitch ("Qwen processed 10,000 log lines in 18 seconds on MI300X")
- Write first social post: "Day 5 building on AMD MI300X — here's what 128K context window does for incident response..."

**Milestone:** Live demo URL working on AMD infrastructure

### Day 6 — Submit + Promote
- Record 5-minute demo video (see script below)
- Write GitHub README with architecture diagram and setup instructions
- Fill submission form on lablab.ai
- Write second social post with demo GIF/screenshot
- Submit before deadline
- Share HF Space link in AMD Discord for community likes

**Milestone:** Submitted. Posted twice. Done.

---

## Pitch Script (5 minutes)

### Hook (30 seconds)
"Every engineer in this room has been paged at 3am. Your phone goes off. A service is down. You open your laptop. And for the next 45 minutes you manually read logs, check metrics, look at recent deployments, and try to figure out what broke. You've done this dozens of times. It is the most painful, repetitive, high-stakes manual process in software engineering. And nobody has automated it. Until now."

### Product (20 seconds)
"This is an autonomous incident response agent. Alert fires. Five specialized agents activate simultaneously. 90 seconds later: root cause identified, rollback command generated, incident report drafted. Your on-call engineer gets their 3am back."

### Demo (90 seconds — silence during processing)
Click Simulate Incident → Scenario A fires → agents light up in parallel → root cause appears → click remediation → commands and report visible

"That was 90 seconds. The manual version takes 45 minutes."

### AMD Story (30 seconds)
"This runs on Qwen2.5-72B on AMD MI300X. Processing 10,000 log lines in a single 128K context pass — 18 seconds on AMD hardware. The memory bandwidth architecture of MI300X is what makes parallel multi-agent inference at this latency possible. This is not API calls with AMD as decoration. The compute is load-bearing."

### Business Case (30 seconds)
"Average cost of a 1-hour production outage: $100,000. Average time to root cause manually: 45 minutes. This agent cuts that to 90 seconds. SaaS pricing $500-2,000 per month per engineering team. Every company running software in production is the addressable market."

### Close (20 seconds)
"Incidents happen. They always will. The question is whether your engineer spends 45 minutes or 90 seconds figuring out why. Thank you."

---

## Submission Checklist

- [ ] AMD AI Developer Program signup complete
- [ ] AMD Developer Cloud backend deployed and live
- [ ] Qwen2.5-72B serving via vLLM on ROCm
- [ ] All 5 agents working in LangGraph pipeline
- [ ] Three demo scenarios producing correct output
- [ ] Next.js dashboard with agent status cards
- [ ] Hugging Face Space published in event organization
- [ ] Live demo URL working
- [ ] GitHub repository public with MIT license
- [ ] README with architecture and setup instructions
- [ ] 5-minute demo video recorded (MP4)
- [ ] Cover image created (16:9 PNG)
- [ ] Slide presentation (PDF)
- [ ] lablab.ai submission form filled completely
- [ ] Two social posts published tagging @AIatAMD and @lablab
- [ ] HF Space link shared for community likes
- [ ] Submitted before May 10 deadline

---

## The AMD Angle — Say This In Your Pitch

These specific statements are defensible and will land with AMD judges:

- "Qwen2.5-72B's 128K context window processes an entire incident's log history in a single pass — no chunking, no loss of context between lines 1 and 10,000"
- "AMD MI300X memory bandwidth architecture enables five parallel agents at latency that matters during an active incident"
- "vLLM on ROCm serves Qwen at [X] tokens/second — measured during testing, not estimated"
- "Running on AMD infrastructure means log data never leaves your private cloud — critical for regulated industries"

---

## Why You Will Win This

You are walking into a room where most people are building generic chatbots and RAG demos. You are building a domain-specific agentic system in a space where you have real expertise, using the hardware the judges actually care about, solving a problem every judge in that room has personally experienced.

The judges from Netflix, Apple, and Amazon have been on-call. They will watch your demo and think about the last time they spent 45 minutes manually triaging an incident. That emotional recognition combined with a technically credible AMD story and a polished 90-second demo is what wins hackathons.

Build it. Ship it. Go get them. 🚀

---

*AMD Developer Hackathon · May 4–10, 2026 · Track 1: AI Agents & Agentic Workflows*

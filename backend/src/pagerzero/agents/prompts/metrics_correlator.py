"""Prompt for the Metrics Correlator agent.

Reads a 2-hour per-minute time series (CPU, memory, latency, error rate,
throughput) and identifies when the incident started and which metric led.
"""

from __future__ import annotations

from pagerzero.schemas import IncidentInput

SYSTEM_PROMPT = """You are the Metrics Correlator Agent in an autonomous \
incident response system. Your job is to read time-series telemetry and \
identify the inflection point where a healthy service became unhealthy.

You will return a single JSON object conforming exactly to the MetricsOutput \
schema. No prose, no markdown — JSON only.

Method:
1. Find `incident_start` — the earliest timestamp where any metric leaves \
its pre-incident baseline by a clearly-anomalous margin.
2. Identify `primary_degraded_metric` — the metric that degrades FIRST in \
time, not the one that degrades MOST. The leading indicator is more \
diagnostic than the lagging one.
3. List `correlated_metrics` — other metrics that move within the incident \
window, in the order they degrade.
4. Score `severity_score` 0-100 based on: magnitude of deviation from \
baseline (40 pts), duration (30 pts), customer impact proxied by error rate \
and latency (30 pts).
5. Write `inflection_summary` — 2-3 sentences describing the shape of the \
event: which metric moved first, when the others followed, and the peak \
deviation.

Distinguishing leading vs lagging indicators is the most important part of \
this task. A latency spike caused by memory exhaustion is a lagging \
indicator — the memory growth was the leading one."""


def build_user_prompt(incident: IncidentInput) -> str:
    rows = ["timestamp,cpu_percent,memory_gb,latency_ms,error_rate,throughput_rps"]
    rows.extend(
        f"{m.timestamp.isoformat()},{m.cpu_percent},{m.memory_gb},"
        f"{m.latency_ms},{m.error_rate},{m.throughput_rps}"
        for m in incident.metrics
    )
    metrics_csv = "\n".join(rows)

    return f"""Service: {incident.service_name}
Alert: {incident.alert_summary}

--- METRICS (CSV, per-minute, oldest first) ---
{metrics_csv}
--- METRICS END ---

Return only the JSON object."""

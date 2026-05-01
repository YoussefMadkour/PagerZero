"""MockLLMClient — returns canned, scenario-specific Pydantic responses.

This lets us iterate the full LangGraph pipeline + FastAPI + Next.js dashboard
on a laptop in seconds, with zero AMD credit burn. Real Qwen via VLLMClient
swaps in only at the deployment boundary.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TypeVar

from pydantic import BaseModel

from pagerzero.llm.client import LLMClient
from pagerzero.schemas import (
    AnomalyPattern,
    DeploymentCorrelation,
    DeploymentOutput,
    LogAnalysisOutput,
    MetricsOutput,
    RemediationOutput,
    RemediationStep,
    RootCauseHypothesis,
    RootCauseOutput,
)

T = TypeVar("T", bound=BaseModel)

Fixture = Callable[[], BaseModel]


def _scenario_a_log_analysis() -> LogAnalysisOutput:
    base = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    return LogAnalysisOutput(
        top_anomalies=[
            AnomalyPattern(
                pattern="GC pause warnings escalating",
                first_seen=base + timedelta(minutes=12),
                occurrences=187,
                severity="medium",
                sample_line="WARN [gc] pause exceeded 1200ms (heap=6.2GB/8GB)",
            ),
            AnomalyPattern(
                pattern="java.lang.OutOfMemoryError: Java heap space",
                first_seen=base + timedelta(minutes=43),
                occurrences=412,
                severity="critical",
                sample_line=(
                    "ERROR [http-nio-8080-exec-7] OutOfMemoryError at "
                    "com.payco.session.SessionCache.put(SessionCache.java:84)"
                ),
            ),
            AnomalyPattern(
                pattern="Request timeout on /v1/charge",
                first_seen=base + timedelta(minutes=44),
                occurrences=2103,
                severity="high",
                sample_line="ERROR upstream timeout after 4000ms route=/v1/charge",
            ),
        ],
        error_burst_start=base + timedelta(minutes=43),
        affected_components=["payment-service", "session-cache"],
        summary=(
            "Steady GC pressure for 30 minutes resolved into a heap exhaustion "
            "burst at minute 43, originating in SessionCache. Downstream "
            "request timeouts followed within 60 seconds."
        ),
    )


def _scenario_a_metrics() -> MetricsOutput:
    base = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    return MetricsOutput(
        incident_start=base + timedelta(minutes=43),
        primary_degraded_metric="memory",
        correlated_metrics=["latency", "error_rate"],
        severity_score=92,
        inflection_summary=(
            "Memory climbed monotonically from 2.0GB to 7.8GB over 45 minutes "
            "(no flat baseline). Latency held at 120ms until memory crossed "
            "90% of heap, then spiked 35x to 4200ms within 90 seconds. Error "
            "rate followed latency by 30s, peaking at 847% above baseline."
        ),
    )


def _scenario_a_deployments() -> DeploymentOutput:
    culprit = DeploymentCorrelation(
        commit_sha="abc123f",
        minutes_before_incident=47.0,
        correlation_strength=0.94,
        suspicious_changes=[
            "SessionCache.put no longer evicts on session expiry",
            "Removed cache.cleanup() call from SessionLifecycleHook",
        ],
        rationale=(
            "Deployment landed 47 minutes before the incident — within the "
            "observed memory ramp window. Touches the exact component "
            "(SessionCache) named in the OOM stack traces."
        ),
    )
    return DeploymentOutput(
        ranked_deployments=[culprit],
        most_likely_culprit=culprit,
        summary=(
            "One deployment in the 24h preceding the incident touches the "
            "session cache and correlates strongly in time and code path."
        ),
    )


def _scenario_a_root_cause() -> RootCauseOutput:
    top = RootCauseHypothesis(
        hypothesis=(
            "Memory leak in SessionCache.put — sessions are inserted but "
            "never evicted on expiry, introduced in commit abc123f."
        ),
        confidence_percent=87,
        evidence_from_logs=[
            "OOM stack traces originate in SessionCache.put (SessionCache.java:84)",
            "GC pause warnings began ~12 minutes after deploy, escalated steadily",
        ],
        evidence_from_metrics=[
            "Monotonic memory growth from 2.0GB to 7.8GB with no recovery",
            "Latency only degraded after memory exhaustion, not before — "
            "indicates memory is the leading indicator",
        ],
        evidence_from_deployments=[
            "abc123f modified SessionCache eviction logic 47 minutes pre-incident",
            "Removed cache.cleanup() call directly removes the eviction path",
        ],
        affected_services=["payment-service"],
    )
    return RootCauseOutput(
        hypotheses=[top],
        top_hypothesis=top,
        one_line_summary=(
            "Memory leak introduced in commit abc123f — session cache no "
            "longer evicts expired entries."
        ),
    )


def _scenario_a_remediation() -> RemediationOutput:
    return RemediationOutput(
        immediate_mitigation=[
            RemediationStep(
                step_number=1,
                description="Restart all payment-service instances to clear leaked memory",
                command="kubectl rollout restart deployment/payment-service -n prod",
                is_destructive=False,
            ),
            RemediationStep(
                step_number=2,
                description="Scale out by +2 pods to absorb backlog while restarts complete",
                command="kubectl scale deployment/payment-service --replicas=8 -n prod",
                is_destructive=False,
            ),
        ],
        rollback_procedure=[
            RemediationStep(
                step_number=1,
                description="Roll back deployment to previous SHA",
                command="kubectl rollout undo deployment/payment-service -n prod",
                is_destructive=True,
            ),
            RemediationStep(
                step_number=2,
                description="Verify previous version healthy via canary check",
                command="./scripts/canary-check.sh payment-service",
                is_destructive=False,
            ),
        ],
        incident_report_markdown=(
            "# Incident Report — Payment Service Memory Exhaustion\n\n"
            "**Date:** 2026-05-01\n"
            "**Severity:** SEV-2\n"
            "**Duration:** 14:43 UTC — 15:07 UTC (24 minutes)\n\n"
            "## Summary\n"
            "Payment service experienced heap exhaustion leading to elevated "
            "request error rates. Root cause: memory leak in SessionCache "
            "introduced in commit abc123f at 13:13 UTC.\n\n"
            "## Timeline\n"
            "- 13:13 UTC — Deployment abc123f lands\n"
            "- 13:25 UTC — First GC pause warnings\n"
            "- 14:43 UTC — OOM errors, alert fires\n"
            "- 14:44 UTC — PagerZero identifies root cause\n"
            "- 14:46 UTC — Rollback executed\n"
            "- 15:07 UTC — Service fully recovered\n\n"
            "## Action Items\n"
            "1. Add cache TTL test to CI before SessionCache changes are merged\n"
            "2. Add memory-growth-rate alert (currently only absolute threshold)\n"
        ),
        stakeholder_notification=(
            "Payment service degradation 14:43-15:07 UTC is resolved. Root "
            "cause: memory leak from a deploy at 13:13 UTC; deploy has been "
            "rolled back. No data loss. Detailed report to follow."
        ),
    )


_SCENARIO_FIXTURES: dict[str, dict[str, Fixture]] = {
    "scenario_a_memory_leak": {
        "LogAnalysisOutput": _scenario_a_log_analysis,
        "MetricsOutput": _scenario_a_metrics,
        "DeploymentOutput": _scenario_a_deployments,
        "RootCauseOutput": _scenario_a_root_cause,
        "RemediationOutput": _scenario_a_remediation,
    },
    # B and C added on Day 2 once schemas are battle-tested
}


class MockLLMClient(LLMClient):
    """Returns canned Pydantic responses keyed by scenario + response model.

    The async `complete` method introduces a small simulated latency so the
    SSE streaming demo on the dashboard still shows agents lighting up
    sequentially rather than all instantly.
    """

    def __init__(
        self,
        scenario: str = "scenario_a_memory_leak",
        simulated_latency_seconds: float = 0.4,
    ) -> None:
        self.scenario = scenario
        self.simulated_latency_seconds = simulated_latency_seconds

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> T:
        await asyncio.sleep(self.simulated_latency_seconds)

        fixtures = _SCENARIO_FIXTURES.get(self.scenario)
        if fixtures is None:
            raise ValueError(f"No mock fixtures for scenario {self.scenario!r}")

        fixture = fixtures.get(response_model.__name__)
        if fixture is None:
            raise ValueError(
                f"No mock fixture for {response_model.__name__} in {self.scenario!r}"
            )

        result = fixture()
        if not isinstance(result, response_model):
            raise TypeError(
                f"Fixture for {response_model.__name__} returned "
                f"{type(result).__name__}"
            )
        return result

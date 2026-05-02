"""Canned mock responses for scenario_b_pool_exhaust.

Flash-sale traffic 3.4x baseline saturates the 50-conn DB pool. No deploy
correlates — this is a capacity event, not a code event. The agents must
produce an honest "no culprit deploy" answer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pagerzero.schemas import (
    AnomalyPattern,
    DeploymentOutput,
    LogAnalysisOutput,
    MetricsOutput,
    RemediationOutput,
    RemediationStep,
    RootCauseHypothesis,
    RootCauseOutput,
)


def _log_analysis() -> LogAnalysisOutput:
    base = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    return LogAnalysisOutput(
        top_anomalies=[
            AnomalyPattern(
                pattern="Connection timeout waiting for pool",
                first_seen=base + timedelta(minutes=8),
                occurrences=3847,
                severity="critical",
                sample_line=(
                    "ERROR [hikari-pool] connection timeout waiting for "
                    "available connection from pool (active=50/50, waiting=183)"
                ),
            ),
            AnomalyPattern(
                pattern="Latency spike on /v1/checkout",
                first_seen=base + timedelta(minutes=8),
                occurrences=1124,
                severity="high",
                sample_line=(
                    "INFO [http-nio-8080-exec-3] /v1/checkout status=200 "
                    "latency=8400ms"
                ),
            ),
        ],
        error_burst_start=base + timedelta(minutes=8),
        affected_components=["checkout-service", "hikari-pool"],
        summary=(
            "Sharp inflection at 14:08 — hikari connection pool reports "
            "active=50/50 with growing wait queue. Affects all routes that "
            "touch the database. No error stack traces, no application code "
            "fault — this is pure resource starvation."
        ),
    )


def _metrics() -> MetricsOutput:
    base = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    return MetricsOutput(
        incident_start=base + timedelta(minutes=8),
        primary_degraded_metric="throughput",
        correlated_metrics=["latency", "error_rate"],
        severity_score=84,
        inflection_summary=(
            "Throughput jumped from 38 RPS baseline to 130 RPS at 14:08 — "
            "a 3.4x spike consistent with a flash-sale event. Latency "
            "followed within the same minute (80ms → 6500ms peak), then "
            "error rate climbed as pool waits started timing out. Memory and "
            "CPU were normal throughout — this is not a runtime failure, "
            "it's capacity exhaustion under traffic."
        ),
    )


def _deployments() -> DeploymentOutput:
    return DeploymentOutput(
        ranked_deployments=[],
        most_likely_culprit=None,
        summary=(
            "No deployments in the 24h window touch checkout-service code or "
            "the hikari pool configuration. The two recent deploys are "
            "unrelated (error-message copy edit, README badges). This "
            "incident is not deploy-driven."
        ),
    )


def _root_cause() -> RootCauseOutput:
    top = RootCauseHypothesis(
        hypothesis=(
            "Database connection pool exhaustion caused by a 3.4x traffic "
            "spike exceeding the 50-connection pool limit. Not a code or "
            "deploy issue — capacity event."
        ),
        confidence_percent=94,
        evidence_from_logs=[
            "hikari-pool repeatedly reports active=50/50 with growing wait "
            "queue (peak waiting=183)",
            "No application stack traces, no NullPointerExceptions — the "
            "errors are exclusively connection-timeout-waiting-for-pool",
        ],
        evidence_from_metrics=[
            "Throughput jumped 3.4x at 14:08 (38 RPS → 130 RPS)",
            "Memory and CPU stayed in normal ranges throughout — runtime "
            "health is fine, only the DB-bound resource is starved",
        ],
        evidence_from_deployments=[
            "No deploys in the 24h window touch checkout-service or pool config"
        ],
        affected_services=["checkout-service"],
    )
    return RootCauseOutput(
        hypotheses=[top],
        top_hypothesis=top,
        one_line_summary=(
            "Connection pool exhausted by 3.4x traffic spike — capacity "
            "event, not a code issue."
        ),
    )


def _remediation() -> RemediationOutput:
    return RemediationOutput(
        immediate_mitigation=[
            RemediationStep(
                step_number=1,
                description=(
                    "Increase Hikari pool size from 50 to 200 connections via runtime config"
                ),
                command=(
                    "kubectl set env deployment/checkout-service "
                    "HIKARI_MAX_POOL=200 -n prod"
                ),
                is_destructive=False,
            ),
            RemediationStep(
                step_number=2,
                description="Scale checkout-service horizontally to absorb retry backlog",
                command="kubectl scale deployment/checkout-service --replicas=12 -n prod",
                is_destructive=False,
            ),
            RemediationStep(
                step_number=3,
                description=(
                    "Verify database has connection headroom before scaling further"
                ),
                command=(
                    'psql -c "SELECT count(*) FROM pg_stat_activity"'
                ),
                is_destructive=False,
            ),
        ],
        rollback_procedure=[],
        incident_report_markdown=(
            "# Incident Report — Checkout Service Pool Exhaustion\n\n"
            "**Date:** 2026-05-01\n"
            "**Severity:** SEV-2\n"
            "**Duration:** 14:08 UTC — 14:23 UTC (15 minutes)\n\n"
            "## Summary\n"
            "Checkout service became unresponsive when a 3.4x traffic spike "
            "saturated the 50-connection database pool. Mitigated by raising "
            "pool size to 200 and scaling out.\n\n"
            "## Timeline\n"
            "- 14:00 UTC — Marketing email blast goes out\n"
            "- 14:08 UTC — Traffic crosses pool capacity, alert fires\n"
            "- 14:09 UTC — PagerZero identifies as capacity event (no code cause)\n"
            "- 14:11 UTC — Pool size raised to 200; replicas scaled to 12\n"
            "- 14:23 UTC — Wait queue drained, service fully recovered\n\n"
            "## Action Items\n"
            "1. Add a queue-depth alert below pool exhaustion threshold\n"
            "2. Move pool sizing into autoscaler config tied to RPS\n"
            "3. Add read replicas before next planned campaign\n"
            "4. Pre-warn on-call before scheduled marketing email blasts\n"
        ),
        stakeholder_notification=(
            "Checkout was unavailable for ~15 minutes today (14:08-14:23 "
            "UTC) due to higher-than-expected traffic exceeding our database "
            "capacity. We've added capacity and the service is fully "
            "recovered. No orders were lost; customers who hit errors can "
            "safely retry. A detailed report follows."
        ),
    )


FIXTURES = {
    "LogAnalysisOutput": _log_analysis,
    "MetricsOutput": _metrics,
    "DeploymentOutput": _deployments,
    "RootCauseOutput": _root_cause,
    "RemediationOutput": _remediation,
}

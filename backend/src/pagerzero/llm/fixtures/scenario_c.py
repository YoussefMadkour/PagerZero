"""Canned mock responses for scenario_c_cascade.

Config push at 14:32 disables the circuit breaker between product-service
and recommendation-service. Recommendation slowdown at 14:35 is then
amplified by retries into a thread-pool exhaustion at 14:40, taking down
the entire storefront. The deploy is the proximate cause; the slow
recommendation service is a contributing condition.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


def _log_analysis() -> LogAnalysisOutput:
    base = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    return LogAnalysisOutput(
        top_anomalies=[
            AnomalyPattern(
                pattern="Recommendation service slow response",
                first_seen=base + timedelta(minutes=35),
                occurrences=512,
                severity="medium",
                sample_line=(
                    "WARN [rec-svc] slow response latency=4200ms "
                    "endpoint=/v1/recommendations/personalized"
                ),
            ),
            AnomalyPattern(
                pattern="Retry storm against rec-svc",
                first_seen=base + timedelta(minutes=40),
                occurrences=8431,
                severity="high",
                sample_line=(
                    "ERROR [product-svc] retrying call to rec-svc "
                    "(attempt=6/8) timeout=4000ms upstream=rec-svc.prod.svc"
                ),
            ),
            AnomalyPattern(
                pattern="Thread pool exhausted in product-svc",
                first_seen=base + timedelta(minutes=41),
                occurrences=4912,
                severity="critical",
                sample_line=(
                    "ERROR [product-svc] thread pool exhausted "
                    "active=200/200 queue_depth=2400 rejected_requests=true"
                ),
            ),
        ],
        error_burst_start=base + timedelta(minutes=40),
        affected_components=["product-service", "recommendation-service", "storefront"],
        summary=(
            "Two-stage failure. Stage 1 (14:35): rec-svc slows down — root "
            "cause TBD, separate investigation. Stage 2 (14:40): product-svc "
            "retries against the slow rec-svc consume its entire 200-thread "
            "pool, taking storefront down. The retry behavior should have "
            "been gated by a circuit breaker."
        ),
    )


def _metrics() -> MetricsOutput:
    base = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    return MetricsOutput(
        incident_start=base + timedelta(minutes=40),
        primary_degraded_metric="latency",
        correlated_metrics=["error_rate", "throughput", "cpu"],
        severity_score=96,
        inflection_summary=(
            "Two-stage degradation. First inflection at 14:35: latency "
            "drifts from 100ms to 400ms as rec-svc slows. Second inflection "
            "at 14:40: latency explodes to 9000ms+ as product-svc thread "
            "pool fills. Throughput collapses from 85 RPS to <10 RPS. CPU "
            "climbs to 96% from retry overhead. Error rate goes from <1% "
            "to 92% in 4 minutes."
        ),
    )


def _deployments() -> DeploymentOutput:
    culprit = DeploymentCorrelation(
        commit_sha="f4e8a91",
        minutes_before_incident=8.0,
        correlation_strength=0.91,
        suspicious_changes=[
            "circuit_breaker.product_to_rec.enabled set to false",
            "Disabled the protection that prevents retry storms when rec-svc degrades",
        ],
        rationale=(
            "Config push 8 minutes before the incident disabled the exact "
            "circuit breaker that would have prevented retry-storm-driven "
            "thread pool exhaustion. The rec-svc slowdown alone would have "
            "been a minor incident; without the breaker it cascaded into a "
            "full storefront outage."
        ),
    )
    return DeploymentOutput(
        ranked_deployments=[culprit],
        most_likely_culprit=culprit,
        summary=(
            "One config change correlates strongly: a circuit breaker on "
            "the product → rec call path was disabled 8 minutes before the "
            "incident."
        ),
    )


def _root_cause() -> RootCauseOutput:
    top = RootCauseHypothesis(
        hypothesis=(
            "Cascading failure triggered by config push f4e8a91 disabling "
            "the product→rec circuit breaker. When rec-svc slowed at 14:35, "
            "product-svc retries (with no breaker to short-circuit them) "
            "consumed the entire 200-thread pool and took the storefront down."
        ),
        confidence_percent=91,
        evidence_from_logs=[
            "Retry storm pattern: 8431 occurrences of 'retrying call to "
            "rec-svc' starting exactly 5 min after rec-svc slowdown began",
            "Thread pool exhaustion logs (active=200/200) confirm the "
            "specific failure mode the breaker exists to prevent",
        ],
        evidence_from_metrics=[
            "Two-stage curve: gradual latency drift at 14:35 followed by "
            "explosive spike at 14:40 — classic cascade signature",
            "CPU at 96% with collapsed throughput indicates retry overhead, "
            "not legitimate work",
        ],
        evidence_from_deployments=[
            "Config push f4e8a91 (8 min before incident) disabled "
            "circuit_breaker.product_to_rec.enabled",
            "Diff explicitly notes 'temporary while debugging unrelated "
            "rec-svc latency' — author did not anticipate a separate slowdown",
        ],
        affected_services=["storefront", "product-service"],
    )
    secondary = RootCauseHypothesis(
        hypothesis=(
            "Recommendation service performance regression — separate root "
            "cause. The slowdown that started at 14:35 is the contributing "
            "condition that the disabled breaker amplified."
        ),
        confidence_percent=55,
        evidence_from_logs=[
            "rec-svc latency drifted from baseline to 4000ms+ before any "
            "retry storm or thread exhaustion",
        ],
        evidence_from_metrics=[
            "First-stage latency drift at 14:35 precedes any product-svc "
            "symptoms"
        ],
        evidence_from_deployments=[
            "No deploys touch rec-svc in the 24h window — separate "
            "investigation needed (capacity? upstream dependency?)"
        ],
        affected_services=["recommendation-service"],
    )
    return RootCauseOutput(
        hypotheses=[top, secondary],
        top_hypothesis=top,
        one_line_summary=(
            "Cascading failure — config push disabled the circuit breaker "
            "that would have contained an unrelated rec-svc slowdown."
        ),
    )


def _remediation() -> RemediationOutput:
    return RemediationOutput(
        immediate_mitigation=[
            RemediationStep(
                step_number=1,
                description=(
                    "Re-enable the product→rec circuit breaker by reverting the config push"
                ),
                command="git -C /infra/config revert f4e8a91 && /infra/config/apply.sh",
                is_destructive=False,
            ),
            RemediationStep(
                step_number=2,
                description="Restart product-service to clear the saturated thread pool",
                command="kubectl rollout restart deployment/product-service -n prod",
                is_destructive=False,
            ),
        ],
        rollback_procedure=[
            RemediationStep(
                step_number=1,
                description="Revert the config commit that disabled the breaker",
                command="git -C /infra/config revert f4e8a91 && /infra/config/apply.sh",
                is_destructive=True,
            ),
            RemediationStep(
                step_number=2,
                description="Verify circuit breaker is firing under load",
                command=(
                    "curl -s http://product-service.prod.svc/actuator/circuitbreakers"
                    " | jq '.product_to_rec'"
                ),
                is_destructive=False,
            ),
        ],
        incident_report_markdown=(
            "# Incident Report — Storefront Cascade Outage\n\n"
            "**Date:** 2026-05-01\n"
            "**Severity:** SEV-1\n"
            "**Duration:** 14:40 UTC — 14:58 UTC (18 minutes)\n\n"
            "## Summary\n"
            "Storefront went fully unavailable when product-service threads "
            "saturated retrying calls to a slow recommendation service. The "
            "underlying issue: a config push 8 minutes prior disabled the "
            "circuit breaker that exists to prevent exactly this pattern.\n\n"
            "## Timeline\n"
            "- 14:32 UTC — Config push f4e8a91 disables product→rec breaker\n"
            "- 14:35 UTC — rec-svc latency starts climbing (separate cause TBD)\n"
            "- 14:40 UTC — Retry storm exhausts product-svc thread pool\n"
            "- 14:41 UTC — Storefront fully unavailable, alert fires\n"
            "- 14:42 UTC — PagerZero identifies the disabled breaker\n"
            "- 14:45 UTC — Config reverted, product-svc restarted\n"
            "- 14:58 UTC — Service fully recovered\n\n"
            "## Action Items\n"
            "1. Add CI check that blocks PRs disabling production circuit breakers\n"
            "2. Open follow-up investigation for rec-svc 14:35 slowdown\n"
            "3. Add cascading-failure runbook to on-call docs\n"
            "4. Review all 'temporary' config overrides currently in production\n"
        ),
        stakeholder_notification=(
            "The storefront was unavailable for ~18 minutes today "
            "(14:40-14:58 UTC). Root cause: a configuration change that "
            "disabled a safety mechanism, combined with a slowdown in an "
            "adjacent service. The configuration has been reverted, the "
            "service is fully recovered, and a detailed report follows."
        ),
    )


FIXTURES = {
    "LogAnalysisOutput": _log_analysis,
    "MetricsOutput": _metrics,
    "DeploymentOutput": _deployments,
    "RootCauseOutput": _root_cause,
    "RemediationOutput": _remediation,
}

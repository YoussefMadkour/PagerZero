"""Pydantic v2 schemas for PagerZero agent IO and the LangGraph state.

Schemas are the contract between agents. Keep them strict — every agent's
output is the next agent's input.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

# --- Raw inputs (per scenario) ---


class MetricPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_gb: float
    latency_ms: float
    error_rate: float
    throughput_rps: float


class Deployment(BaseModel):
    timestamp: datetime
    commit_sha: str
    author: str
    message: str
    files_changed: list[str]
    diff_summary: str


class IncidentInput(BaseModel):
    scenario: str
    service_name: str
    alert_summary: str
    logs: str  # raw log lines, newline-delimited
    metrics: list[MetricPoint]
    deployments: list[Deployment]


# --- Agent 1: Log Analysis ---


class AnomalyPattern(BaseModel):
    pattern: str
    first_seen: datetime
    occurrences: int
    severity: Literal["low", "medium", "high", "critical"]
    sample_line: str


class LogAnalysisOutput(BaseModel):
    top_anomalies: list[AnomalyPattern] = Field(max_length=5)
    error_burst_start: datetime | None
    affected_components: list[str]
    summary: str


# --- Agent 2: Metrics Correlator ---


class MetricsOutput(BaseModel):
    incident_start: datetime
    primary_degraded_metric: Literal["cpu", "memory", "latency", "error_rate", "throughput"]
    correlated_metrics: list[str]
    severity_score: Annotated[int, Field(ge=0, le=100)]
    inflection_summary: str


# --- Agent 3: Deployment Tracker ---


class DeploymentCorrelation(BaseModel):
    commit_sha: str
    minutes_before_incident: float
    correlation_strength: Annotated[float, Field(ge=0.0, le=1.0)]
    suspicious_changes: list[str]
    rationale: str


class DeploymentOutput(BaseModel):
    ranked_deployments: list[DeploymentCorrelation]
    most_likely_culprit: DeploymentCorrelation | None
    summary: str


# --- Agent 4: Root Cause ---


class RootCauseHypothesis(BaseModel):
    hypothesis: str
    confidence_percent: Annotated[int, Field(ge=0, le=100)]
    evidence_from_logs: list[str]
    evidence_from_metrics: list[str]
    evidence_from_deployments: list[str]
    affected_services: list[str]


class RootCauseOutput(BaseModel):
    hypotheses: list[RootCauseHypothesis] = Field(min_length=1, max_length=3)
    top_hypothesis: RootCauseHypothesis
    one_line_summary: str


# --- Agent 5: Remediation ---


class RemediationStep(BaseModel):
    step_number: int
    description: str
    command: str | None  # exact CLI command if applicable
    is_destructive: bool


class RemediationOutput(BaseModel):
    immediate_mitigation: list[RemediationStep]
    rollback_procedure: list[RemediationStep]
    incident_report_markdown: str
    stakeholder_notification: str


# --- LangGraph state ---


AgentName = Literal[
    "log_analysis",
    "metrics_correlator",
    "deployment_tracker",
    "root_cause",
    "remediation",
]
AgentStatus = Literal["pending", "running", "done", "error"]


class IncidentState(BaseModel):
    """The shared state that flows through the LangGraph pipeline.

    Each parallel branch writes to its own field; reducers are unnecessary
    because the fields don't overlap.
    """

    incident_id: str
    input: IncidentInput
    log_analysis: LogAnalysisOutput | None = None
    metrics_correlation: MetricsOutput | None = None
    deployment_correlation: DeploymentOutput | None = None
    root_cause: RootCauseOutput | None = None
    remediation: RemediationOutput | None = None
    agent_status: dict[AgentName, AgentStatus] = Field(
        default_factory=lambda: {
            "log_analysis": "pending",
            "metrics_correlator": "pending",
            "deployment_tracker": "pending",
            "root_cause": "pending",
            "remediation": "pending",
        }
    )
    error: str | None = None

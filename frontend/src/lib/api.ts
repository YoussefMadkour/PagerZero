/**
 * Backend API contract types and base URL.
 *
 * Mirrors the Pydantic schemas in backend/src/pagerzero/schemas.py. Hand-typed
 * (not generated) so the frontend can iterate independently — keep these in
 * sync when the backend schemas change.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type AgentName =
  | "log_analysis"
  | "metrics_correlator"
  | "deployment_tracker"
  | "root_cause"
  | "remediation";

export const AGENT_ORDER: AgentName[] = [
  "log_analysis",
  "metrics_correlator",
  "deployment_tracker",
  "root_cause",
  "remediation",
];

export const AGENT_LABEL: Record<AgentName, string> = {
  log_analysis: "Log Analysis",
  metrics_correlator: "Metrics Correlator",
  deployment_tracker: "Deployment Tracker",
  root_cause: "Root Cause",
  remediation: "Remediation",
};

export const AGENT_DESCRIPTION: Record<AgentName, string> = {
  log_analysis: "Anomaly clusters across the full log stream",
  metrics_correlator: "Inflection points and leading indicators",
  deployment_tracker: "Recent deploys ranked by correlation",
  root_cause: "Synthesizes all three signal streams",
  remediation: "Commands, rollback, and incident report",
};

export type ScenarioMeta = {
  id: string;
  service_name: string;
  alert_summary: string;
};

/* Demo presentation labels — each scenario gets an incident-tracker-style
 * code (PAY-2479, etc.) and a short title. These render in place of the
 * raw scenario id and frame the demos as real-looking incidents. */
export const SCENARIO_PRESENTATION: Record<
  string,
  { code: string; title: string }
> = {
  scenario_a_memory_leak: {
    code: "PAY-2479",
    title: "Payment service heap exhaustion",
  },
  scenario_b_pool_exhaust: {
    code: "CHK-1138",
    title: "Checkout pool saturation",
  },
  scenario_c_cascade: {
    code: "STF-3041",
    title: "Storefront cascade outage",
  },
};

export function presentScenario(id: string): { code: string; title: string } {
  return (
    SCENARIO_PRESENTATION[id] ?? {
      code: id.toUpperCase().slice(0, 8),
      title: id,
    }
  );
}

export type AnomalyPattern = {
  pattern: string;
  first_seen: string;
  occurrences: number;
  severity: "low" | "medium" | "high" | "critical";
  sample_line: string;
};

export type LogAnalysisOutput = {
  top_anomalies: AnomalyPattern[];
  error_burst_start: string | null;
  affected_components: string[];
  summary: string;
};

export type MetricsOutput = {
  incident_start: string;
  primary_degraded_metric:
    | "cpu"
    | "memory"
    | "latency"
    | "error_rate"
    | "throughput";
  correlated_metrics: string[];
  severity_score: number;
  inflection_summary: string;
};

export type DeploymentCorrelation = {
  commit_sha: string;
  minutes_before_incident: number;
  correlation_strength: number;
  suspicious_changes: string[];
  rationale: string;
};

export type DeploymentOutput = {
  ranked_deployments: DeploymentCorrelation[];
  most_likely_culprit: DeploymentCorrelation | null;
  summary: string;
};

export type RootCauseHypothesis = {
  hypothesis: string;
  confidence_percent: number;
  evidence_from_logs: string[];
  evidence_from_metrics: string[];
  evidence_from_deployments: string[];
  affected_services: string[];
};

export type RootCauseOutput = {
  hypotheses: RootCauseHypothesis[];
  top_hypothesis: RootCauseHypothesis;
  one_line_summary: string;
};

export type RemediationStep = {
  step_number: number;
  description: string;
  command: string | null;
  is_destructive: boolean;
};

export type RemediationOutput = {
  immediate_mitigation: RemediationStep[];
  rollback_procedure: RemediationStep[];
  incident_report_markdown: string;
  stakeholder_notification: string;
};

export type AgentOutput =
  | LogAnalysisOutput
  | MetricsOutput
  | DeploymentOutput
  | RootCauseOutput
  | RemediationOutput;

export type FinalState = {
  log_analysis?: LogAnalysisOutput;
  metrics_correlation?: MetricsOutput;
  deployment_correlation?: DeploymentOutput;
  root_cause?: RootCauseOutput;
  remediation?: RemediationOutput;
};

/* SSE event payloads */

export type SourceData = {
  log_lines: number;
  log_chars: number;
  log_tokens_est: number;
  metric_points: number;
  metric_span_minutes: number;
  deployments: number;
  deploys_window_minutes: number;
};

export type AgentScope = {
  primary: string;
  secondary: string;
};

export type PipelineStartedEvent = {
  type: "pipeline_started";
  data: {
    incident_id: string;
    scenario: string;
    service_name: string;
    alert_summary: string;
    agents: AgentName[];
    source_data: SourceData;
  };
};

export type AgentStartedEvent = {
  type: "agent_started";
  data: { agent: AgentName; scope: AgentScope };
};

export type AgentCompletedEvent = {
  type: "agent_completed";
  data: { agent: AgentName; output: Record<string, unknown> };
};

export type PipelineCompletedEvent = {
  type: "pipeline_completed";
  data: { incident_id: string; final_state: FinalState };
};

export type ErrorEvent = {
  type: "error";
  data: { message: string };
};

export type IncidentEvent =
  | PipelineStartedEvent
  | AgentStartedEvent
  | AgentCompletedEvent
  | PipelineCompletedEvent
  | ErrorEvent;

export async function fetchScenarios(): Promise<ScenarioMeta[]> {
  const r = await fetch(`${API_BASE}/api/scenarios`, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed to load scenarios: ${r.status}`);
  return r.json();
}

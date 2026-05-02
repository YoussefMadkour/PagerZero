"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  AGENT_ORDER,
  type AgentName,
  type AgentScope,
  API_BASE,
  type DeploymentPreview,
  type FinalState,
  type IncidentEvent,
  type PipelineStartedEvent,
  type SourceData,
} from "./api";

export type AgentStatus = "pending" | "running" | "done" | "error";

export type AgentRunState = {
  status: AgentStatus;
  startedAt: number | null;
  endedAt: number | null;
  output: Record<string, unknown> | null;
  scope: AgentScope | null;
};

export type IncidentRunState = {
  /** lifecycle of the whole run */
  phase: "idle" | "running" | "completed" | "error";
  scenario: string | null;
  incidentId: string | null;
  serviceName: string | null;
  alertSummary: string | null;
  sourceData: SourceData | null;
  deploymentsPreview: DeploymentPreview[];
  startedAt: number | null;
  endedAt: number | null;
  agents: Record<AgentName, AgentRunState>;
  finalState: FinalState | null;
  errorMessage: string | null;
};

function freshAgents(): Record<AgentName, AgentRunState> {
  return AGENT_ORDER.reduce(
    (acc, name) => {
      acc[name] = {
        status: "pending",
        startedAt: null,
        endedAt: null,
        output: null,
        scope: null,
      };
      return acc;
    },
    {} as Record<AgentName, AgentRunState>,
  );
}

const initialState: IncidentRunState = {
  phase: "idle",
  scenario: null,
  incidentId: null,
  serviceName: null,
  alertSummary: null,
  sourceData: null,
  deploymentsPreview: [],
  startedAt: null,
  endedAt: null,
  agents: freshAgents(),
  finalState: null,
  errorMessage: null,
};

/**
 * Drives a single SSE-streamed incident run.
 *
 * The hook maintains a tight state machine: idle -> running -> completed|error.
 * Calling `run(scenario)` cancels any in-flight run and starts a new one.
 */
export function useIncidentRun() {
  const [state, setState] = useState<IncidentRunState>(initialState);
  const sourceRef = useRef<EventSource | null>(null);

  const closeSource = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
  }, []);

  const reset = useCallback(() => {
    closeSource();
    setState(initialState);
  }, [closeSource]);

  const run = useCallback(
    (scenario: string) => {
      closeSource();

      setState({
        ...initialState,
        phase: "running",
        scenario,
        startedAt: performance.now(),
        agents: freshAgents(),
      });

      const url = `${API_BASE}/api/incidents/stream?scenario=${encodeURIComponent(scenario)}`;
      const source = new EventSource(url);
      sourceRef.current = source;

      const handleTyped = <T extends IncidentEvent>(
        eventName: T["type"],
        cb: (data: T["data"]) => void,
      ) => {
        source.addEventListener(eventName, (raw: MessageEvent) => {
          try {
            const parsed = JSON.parse(raw.data);
            cb(parsed);
          } catch (err) {
            console.error(`Failed to parse ${eventName}:`, err);
          }
        });
      };

      handleTyped<PipelineStartedEvent>("pipeline_started", (data) => {
        setState((s) => ({
          ...s,
          incidentId: data.incident_id,
          serviceName: data.service_name,
          alertSummary: data.alert_summary,
          sourceData: data.source_data,
          deploymentsPreview: data.deployments_preview,
        }));
      });

      handleTyped<{
        type: "agent_started";
        data: { agent: AgentName; scope: AgentScope };
      }>("agent_started", (data) => {
        setState((s) => ({
          ...s,
          agents: {
            ...s.agents,
            [data.agent]: {
              ...s.agents[data.agent],
              status: "running",
              startedAt: performance.now(),
              scope: data.scope,
            },
          },
        }));
      });

      handleTyped<{
        type: "agent_completed";
        data: { agent: AgentName; output: Record<string, unknown> };
      }>("agent_completed", (data) => {
        setState((s) => ({
          ...s,
          agents: {
            ...s.agents,
            [data.agent]: {
              ...s.agents[data.agent],
              status: "done",
              endedAt: performance.now(),
              output: data.output,
            },
          },
        }));
      });

      handleTyped<{
        type: "pipeline_completed";
        data: { incident_id: string; final_state: FinalState };
      }>("pipeline_completed", (data) => {
        setState((s) => ({
          ...s,
          phase: "completed",
          endedAt: performance.now(),
          finalState: data.final_state,
        }));
        closeSource();
      });

      handleTyped<{ type: "error"; data: { message: string } }>(
        "error",
        (data) => {
          setState((s) => ({
            ...s,
            phase: "error",
            endedAt: performance.now(),
            errorMessage: data.message,
          }));
          closeSource();
        },
      );

      source.onerror = () => {
        // Distinguish a clean close (after pipeline_completed) from a real error.
        setState((s) =>
          s.phase === "completed"
            ? s
            : {
                ...s,
                phase: "error",
                endedAt: performance.now(),
                errorMessage: s.errorMessage ?? "Connection to backend lost",
              },
        );
        closeSource();
      };
    },
    [closeSource],
  );

  useEffect(() => {
    return () => closeSource();
  }, [closeSource]);

  return { state, run, reset };
}

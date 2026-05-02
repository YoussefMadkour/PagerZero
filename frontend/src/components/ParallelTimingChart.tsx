"use client";

import { motion } from "framer-motion";
import { Cpu, Zap } from "lucide-react";

import { AGENT_LABEL, AGENT_ORDER, type AgentName } from "@/lib/api";
import type { AgentRunState } from "@/lib/useIncidentRun";

/**
 * The AMD compute story made visual — see ADR 0002.
 *
 * Shows two stacked bars:
 *   - Observed: actual wall-clock from pipeline_started -> pipeline_completed.
 *   - Sequential equivalent: sum of all per-agent durations (what it would
 *     have taken without parallel execution of agents 1/2/3).
 *
 * The delta is the AMD MI300X parallel-inference saving.
 */
export function ParallelTimingChart({
  agents,
  phase,
  pipelineStartedAt,
  pipelineEndedAt,
}: {
  agents: Record<AgentName, AgentRunState>;
  phase: "idle" | "running" | "completed" | "error";
  pipelineStartedAt: number | null;
  pipelineEndedAt: number | null;
}) {
  const durationsMs: Record<AgentName, number> = AGENT_ORDER.reduce(
    (acc, name) => {
      const a = agents[name];
      acc[name] =
        a.startedAt !== null && a.endedAt !== null
          ? a.endedAt - a.startedAt
          : 0;
      return acc;
    },
    {} as Record<AgentName, number>,
  );

  const observedMs =
    pipelineStartedAt !== null && pipelineEndedAt !== null
      ? pipelineEndedAt - pipelineStartedAt
      : 0;
  const sequentialMs = AGENT_ORDER.reduce(
    (sum, name) => sum + durationsMs[name],
    0,
  );

  const ready = phase === "completed" && observedMs > 0;
  const speedup = ready && observedMs > 0 ? sequentialMs / observedMs : null;
  const max = Math.max(observedMs, sequentialMs, 1);

  return (
    <section className="rounded-[var(--r-md)] border border-line-strong bg-surface-1">
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-state-running" />
          <h3 className="text-[13px] font-semibold tracking-tight">
            Parallel inference
          </h3>
        </div>
        <span className="font-mono text-[11px] uppercase tracking-wider text-text-tertiary">
          MI300X
        </span>
      </header>

      <div className="px-4 py-4">
        {ready ? (
          <>
            <Bar
              label="Observed"
              sublabel="parallel on MI300X"
              ms={observedMs}
              maxMs={max}
              tone="done"
            />
            <div className="mt-3">
              <Bar
                label="Sequential equivalent"
                sublabel="if agents 1-3 ran one-by-one"
                ms={sequentialMs}
                maxMs={max}
                tone="muted"
              />
            </div>
            {speedup !== null && (
              <div className="mt-4 flex items-center gap-2 rounded-[var(--r-sm)] border border-state-running-line bg-[color:var(--state-running-dim)] px-3 py-2 text-[12px]">
                <Zap className="h-3.5 w-3.5 text-state-running" />
                <span className="font-mono text-text-primary">
                  {speedup.toFixed(2)}× speedup
                </span>
                <span className="text-text-tertiary">
                  · saved {((sequentialMs - observedMs) / 1000).toFixed(1)}s
                </span>
              </div>
            )}
          </>
        ) : (
          <p className="text-[12px] text-text-tertiary">
            Parallel-vs-sequential timing appears after the pipeline finishes.
          </p>
        )}

        <ul className="mt-5 space-y-1.5 border-t border-line pt-4 text-[11px] text-text-tertiary">
          {AGENT_ORDER.map((name) => (
            <li key={name} className="flex items-center justify-between">
              <span className="text-text-secondary">{AGENT_LABEL[name]}</span>
              <span className="font-mono tabular-nums">
                {durationsMs[name] > 0
                  ? `${(durationsMs[name] / 1000).toFixed(2)}s`
                  : "—"}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Bar({
  label,
  sublabel,
  ms,
  maxMs,
  tone,
}: {
  label: string;
  sublabel: string;
  ms: number;
  maxMs: number;
  tone: "done" | "muted";
}) {
  const pct = Math.min(100, (ms / maxMs) * 100);
  return (
    <div>
      <div className="flex items-baseline justify-between text-[12px]">
        <div>
          <span className="font-medium text-text-primary">{label}</span>
          <span className="ml-2 text-text-tertiary">{sublabel}</span>
        </div>
        <span className="font-mono tabular-nums text-text-primary">
          {(ms / 1000).toFixed(2)}s
        </span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-[3px] bg-surface-2">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className={
            tone === "done"
              ? "h-full bg-state-done"
              : "h-full bg-state-pending"
          }
        />
      </div>
    </div>
  );
}

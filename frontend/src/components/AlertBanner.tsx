"use client";

import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

import { presentScenario } from "@/lib/api";
import type { IncidentRunState } from "@/lib/useIncidentRun";

/**
 * The active alert "page" — appears at the top of the dashboard the moment a
 * run starts. Visual focal point during the demo.
 */
export function AlertBanner({ runState }: { runState: IncidentRunState }) {
  if (runState.phase === "idle" || !runState.serviceName) {
    return (
      <div
        className="flex items-center gap-3 rounded-[var(--r-md)] border border-dashed border-line-strong bg-surface-1/50 px-4 py-6 text-text-tertiary"
        aria-hidden
      >
        <span className="font-mono text-[12px] uppercase tracking-wider">
          standby
        </span>
        <span className="text-[13px]">
          Pick a scenario above and trigger a simulated incident.
        </span>
      </div>
    );
  }

  const presentation = runState.scenario
    ? presentScenario(runState.scenario)
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="overflow-hidden rounded-[var(--r-md)] border border-state-error-line bg-[color:var(--state-error-dim)]"
    >
      <div className="flex items-start gap-3 p-4">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-state-error" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wider">
            <span className="font-mono font-medium text-state-error">
              alert
            </span>
            <span className="text-text-tertiary">·</span>
            {presentation && (
              <>
                <span className="font-mono text-text-primary">
                  {presentation.code}
                </span>
                <span className="text-text-tertiary">·</span>
              </>
            )}
            <span className="font-mono text-text-tertiary">
              run {runState.incidentId ?? "—"}
            </span>
          </div>
          <h2 className="mt-1 text-[15px] font-semibold tracking-tight text-text-primary">
            {presentation ? presentation.title : runState.serviceName}
          </h2>
          <p className="mt-1 text-[13px] leading-relaxed text-text-secondary">
            <span className="font-mono text-text-tertiary">
              {runState.serviceName} ·{" "}
            </span>
            {runState.alertSummary}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

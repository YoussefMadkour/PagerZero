"use client";

import { motion } from "framer-motion";
import { Check, Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  AGENT_DESCRIPTION,
  AGENT_LABEL,
  type AgentName,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import type { AgentRunState } from "@/lib/useIncidentRun";

const STATE_COPY: Record<AgentRunState["status"], string> = {
  pending: "queued",
  running: "running",
  done: "complete",
  error: "failed",
};

export function AgentCard({
  name,
  state,
  index,
}: {
  name: AgentName;
  state: AgentRunState;
  index: number;
}) {
  const elapsedMs =
    state.startedAt !== null && state.endedAt !== null
      ? state.endedAt - state.startedAt
      : null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.16, ease: "easeOut", delay: index * 0.02 }}
      className={cn(
        "relative flex flex-col rounded-[var(--r-md)] border bg-surface-1 p-4",
        "transition-colors duration-200",
        state.status === "pending" && "border-line",
        state.status === "running" &&
          "border-state-running-line bg-[color:var(--state-running-dim)]",
        state.status === "done" &&
          "border-state-done-line bg-[color:var(--state-done-dim)]",
        state.status === "error" && "border-state-error-line bg-[color:var(--state-error-dim)]",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-text-tertiary">
              agent {String(index + 1).padStart(2, "0")}
            </span>
            <StatePill status={state.status} />
          </div>
          <h3 className="mt-2 truncate text-[14px] font-semibold tracking-tight text-text-primary">
            {AGENT_LABEL[name]}
          </h3>
          <p className="mt-1 text-[12px] leading-relaxed text-text-tertiary">
            {AGENT_DESCRIPTION[name]}
          </p>
        </div>
        <StatusIcon status={state.status} />
      </div>

      {state.scope && (
        <div className="mt-3 rounded-[3px] border border-line/70 bg-surface-0/40 px-2.5 py-1.5">
          <div className="font-mono text-[11px] tabular-nums text-text-secondary">
            {state.scope.primary}
          </div>
          <div className="font-mono text-[10px] text-text-tertiary">
            {state.scope.secondary}
          </div>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between border-t border-line/50 pt-3 text-[11px] text-text-tertiary">
        <span className="font-mono">{STATE_COPY[state.status]}</span>
        <span className="font-mono tabular-nums">
          {elapsedMs !== null
            ? `${(elapsedMs / 1000).toFixed(2)}s`
            : state.status === "running"
              ? <RunningTimer startedAt={state.startedAt} />
              : "—"}
        </span>
      </div>
    </motion.div>
  );
}

function StatePill({ status }: { status: AgentRunState["status"] }) {
  return (
    <span
      className={cn(
        "rounded-[3px] px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider",
        status === "pending" && "bg-surface-2 text-text-tertiary",
        status === "running" && "bg-state-running/20 text-state-running",
        status === "done" && "bg-state-done/20 text-state-done",
        status === "error" && "bg-state-error/20 text-state-error",
      )}
    >
      {status}
    </span>
  );
}

function StatusIcon({ status }: { status: AgentRunState["status"] }) {
  const cls = "h-4 w-4 shrink-0";
  if (status === "running")
    return <Loader2 className={cn(cls, "animate-spin text-state-running")} />;
  if (status === "done")
    return <Check className={cn(cls, "text-state-done")} />;
  if (status === "error") return <X className={cn(cls, "text-state-error")} />;
  return <span className={cn(cls, "block rounded-full bg-state-pending-dim")} />;
}

function RunningTimer({ startedAt }: { startedAt: number | null }) {
  // `performance.now()` is impure, so it only runs inside the effect — never
  // during render. The component re-renders when `now` is set.
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    if (startedAt === null) return;
    const id = setInterval(() => setNow(performance.now()), 100);
    return () => clearInterval(id);
  }, [startedAt]);

  if (startedAt === null || now === null) return <>—</>;
  const elapsed = (now - startedAt) / 1000;
  return <>{elapsed.toFixed(1)}s</>;
}

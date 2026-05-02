"use client";

import { Activity } from "lucide-react";

import { cn } from "@/lib/cn";
import type { IncidentRunState } from "@/lib/useIncidentRun";

/**
 * Top-of-screen wordmark + live hardware badge.
 *
 * The hardware badge is the AMD compute story made visible — see
 * docs/adr/0002-amd-compute-narrative.md. While idle it shows the static
 * stack (Qwen2.5-72B · MI300X). Mid-run it displays the live token count
 * and "live" indicator.
 */
export function Header({ runState }: { runState: IncidentRunState }) {
  const isRunning = runState.phase === "running";
  const isDone = runState.phase === "completed";

  return (
    <header className="border-b border-line bg-surface-0/80 backdrop-blur supports-[backdrop-filter]:bg-surface-0/60">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center justify-between gap-6 px-6">
        <div className="flex items-center gap-3">
          <div className="grid h-7 w-7 place-items-center rounded-[var(--r-sm)] bg-state-running/15 text-state-running">
            <span className="font-mono text-[11px] font-semibold tracking-tighter">
              PZ
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-[15px] font-semibold tracking-tight text-text-primary">
              PagerZero
            </span>
            <span className="hidden text-[12px] text-text-tertiary md:inline">
              autonomous incident response
            </span>
          </div>
        </div>

        <HardwareBadge running={isRunning} done={isDone} />
      </div>
    </header>
  );
}

function HardwareBadge({ running, done }: { running: boolean; done: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-[var(--r-md)] border px-3 py-1.5",
        "border-line-strong bg-surface-1 text-[12px]",
        running && "border-state-running-line bg-[color:var(--state-running-dim)]",
        done && "border-state-done-line bg-[color:var(--state-done-dim)]",
      )}
    >
      <Activity
        className={cn(
          "h-3.5 w-3.5",
          running ? "text-state-running pz-pulse" : "text-text-tertiary",
          done && "text-state-done",
        )}
      />
      <span className="font-mono text-text-secondary">
        <span className="text-text-primary">Qwen2.5-72B</span>
        <span className="mx-2 text-text-tertiary">·</span>
        <span className="text-text-primary">MI300X</span>
        <span className="mx-2 text-text-tertiary">·</span>
        <span className="text-text-tertiary">128k context</span>
      </span>
      <span
        className={cn(
          "rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider",
          running
            ? "bg-state-running/15 text-state-running"
            : done
              ? "bg-state-done/15 text-state-done"
              : "bg-surface-2 text-text-tertiary",
        )}
      >
        {running ? "live" : done ? "done" : "idle"}
      </span>
    </div>
  );
}

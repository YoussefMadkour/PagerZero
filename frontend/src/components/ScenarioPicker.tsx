"use client";

import { motion } from "framer-motion";
import { ChevronDown, Play, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { presentScenario, type ScenarioMeta } from "@/lib/api";

export function ScenarioPicker({
  scenarios,
  selected,
  onSelect,
  onTrigger,
  onReset,
  phase,
}: {
  scenarios: ScenarioMeta[];
  selected: string;
  onSelect: (id: string) => void;
  onTrigger: () => void;
  onReset: () => void;
  phase: "idle" | "running" | "completed" | "error";
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const isRunning = phase === "running";
  const isDone = phase === "completed" || phase === "error";

  const selectedMeta = scenarios.find((s) => s.id === selected);
  const selectedPresentation = presentScenario(selected);

  // Close the dropdown when the user clicks anywhere outside it.
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div className="flex items-center gap-3">
      <div className="relative" ref={wrapperRef}>
        <button
          onClick={() => setOpen((o) => !o)}
          disabled={isRunning}
          className={cn(
            "group flex min-w-[320px] items-center justify-between gap-3",
            "rounded-[var(--r-md)] border border-line-strong bg-surface-1 px-3 py-2",
            "text-left text-[13px] transition-colors",
            "hover:border-line-strong hover:bg-surface-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-text-tertiary">
              <span>scenario</span>
              <span className="rounded-[3px] bg-surface-2 px-1.5 py-0.5 text-text-secondary">
                {selectedPresentation.code}
              </span>
            </div>
            <div className="mt-0.5 truncate text-text-primary">
              {selectedPresentation.title}
              {selectedMeta && (
                <span className="ml-2 text-text-tertiary">
                  · {selectedMeta.service_name}
                </span>
              )}
            </div>
          </div>
          <ChevronDown
            className={cn(
              "h-4 w-4 text-text-tertiary transition-transform",
              open && "rotate-180",
            )}
          />
        </button>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className={cn(
              "absolute left-0 right-0 top-full z-20 mt-1",
              "rounded-[var(--r-md)] border border-line-strong bg-surface-1",
              "shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
            )}
          >
            {scenarios.map((s) => {
              const p = presentScenario(s.id);
              return (
                <button
                  key={s.id}
                  onClick={() => {
                    onSelect(s.id);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex w-full flex-col items-start gap-1 px-3 py-2.5 text-left",
                    "border-b border-line last:border-0",
                    "transition-colors hover:bg-surface-2",
                    selected === s.id && "bg-surface-2",
                  )}
                >
                  <div className="flex items-center gap-2 text-[13px]">
                    <span className="rounded-[3px] bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-text-secondary">
                      {p.code}
                    </span>
                    <span className="text-text-primary">{p.title}</span>
                  </div>
                  <div className="text-[11px] text-text-tertiary">
                    {s.service_name} · {s.alert_summary}
                  </div>
                </button>
              );
            })}
          </motion.div>
        )}
      </div>

      {!isDone ? (
        <button
          onClick={onTrigger}
          disabled={isRunning}
          className={cn(
            "flex items-center gap-2 rounded-[var(--r-md)] px-4 py-2 text-[13px] font-medium",
            "transition-colors",
            isRunning
              ? "bg-state-running/15 text-state-running cursor-not-allowed"
              : "bg-state-running text-surface-0 hover:bg-state-running/90",
          )}
          title="Press space to trigger"
        >
          {isRunning ? (
            <>
              <span className="h-2 w-2 rounded-full bg-state-running pz-pulse" />
              Running
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5" />
              Simulate incident
              <kbd className="ml-1 rounded-[3px] border border-surface-0/40 bg-surface-0/30 px-1 py-0 font-mono text-[10px] uppercase">
                space
              </kbd>
            </>
          )}
        </button>
      ) : (
        <button
          onClick={onReset}
          className={cn(
            "flex items-center gap-2 rounded-[var(--r-md)] px-4 py-2 text-[13px] font-medium",
            "border border-line-strong bg-surface-1 text-text-primary",
            "transition-colors hover:bg-surface-2",
          )}
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reset
        </button>
      )}
    </div>
  );
}

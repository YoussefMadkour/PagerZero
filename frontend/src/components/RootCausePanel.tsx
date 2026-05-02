"use client";

import { motion } from "framer-motion";
import { FileText, GitCommit, LineChart, Target } from "lucide-react";
import type { ComponentType } from "react";

import type { RootCauseOutput } from "@/lib/api";
import { cn } from "@/lib/cn";

export function RootCausePanel({ output }: { output: RootCauseOutput | null }) {
  if (!output) {
    return <PanelEmpty title="Root cause" />;
  }

  const top = output.top_hypothesis;
  const secondary = output.hypotheses.slice(1);

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="rounded-[var(--r-md)] border border-line-strong bg-surface-1"
    >
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-state-done" />
          <h3 className="text-[13px] font-semibold tracking-tight">Root cause</h3>
        </div>
        <ConfidencePill percent={top.confidence_percent} />
      </header>

      <div className="p-4">
        <p className="text-[14px] leading-relaxed text-text-primary">
          {output.one_line_summary}
        </p>
        {top.hypothesis !== output.one_line_summary && (
          <p className="mt-2 text-[13px] leading-relaxed text-text-secondary">
            {top.hypothesis}
          </p>
        )}

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <EvidenceBlock
            label="Logs"
            icon={FileText}
            items={top.evidence_from_logs}
          />
          <EvidenceBlock
            label="Metrics"
            icon={LineChart}
            items={top.evidence_from_metrics}
          />
          <EvidenceBlock
            label="Deployments"
            icon={GitCommit}
            items={top.evidence_from_deployments}
          />
        </div>

        {top.affected_services.length > 0 && (
          <div className="mt-4 flex items-center gap-2 text-[12px] text-text-tertiary">
            <span className="font-mono uppercase tracking-wider">
              affected
            </span>
            {top.affected_services.map((svc) => (
              <span
                key={svc}
                className="rounded-[3px] bg-surface-2 px-1.5 py-0.5 font-mono text-text-secondary"
              >
                {svc}
              </span>
            ))}
          </div>
        )}

        {secondary.length > 0 && (
          <details className="mt-5 group">
            <summary className="cursor-pointer text-[12px] text-text-tertiary hover:text-text-secondary">
              {secondary.length} secondary hypothes{secondary.length > 1 ? "es" : "is"}
            </summary>
            <div className="mt-3 space-y-3 border-l border-line pl-3">
              {secondary.map((h, idx) => (
                <div key={idx} className="text-[13px]">
                  <div className="flex items-center gap-2">
                    <ConfidencePill percent={h.confidence_percent} compact />
                    <span className="font-medium text-text-secondary">
                      Hypothesis {idx + 2}
                    </span>
                  </div>
                  <p className="mt-1 text-text-secondary leading-relaxed">
                    {h.hypothesis}
                  </p>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </motion.section>
  );
}

function ConfidencePill({
  percent,
  compact = false,
}: {
  percent: number;
  compact?: boolean;
}) {
  const tone =
    percent >= 80
      ? "bg-state-done/15 text-state-done"
      : percent >= 60
        ? "bg-state-running/15 text-state-running"
        : "bg-surface-2 text-text-secondary";
  return (
    <span
      className={cn(
        "rounded-[3px] font-mono uppercase tracking-wider tabular-nums",
        compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-[11px]",
        tone,
      )}
    >
      {percent}% confidence
    </span>
  );
}

function EvidenceBlock({
  label,
  icon: Icon,
  items,
}: {
  label: string;
  icon: ComponentType<{ className?: string }>;
  items: string[];
}) {
  return (
    <div className="rounded-[var(--r-sm)] border border-line bg-surface-0/40 p-3">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-text-tertiary">
        <Icon className="h-3 w-3" />
        <span className="font-mono">{label}</span>
      </div>
      <ul className="mt-2 space-y-1.5 text-[12px] leading-snug text-text-secondary">
        {items.map((line, i) => (
          <li key={i} className="flex gap-2">
            <span className="select-none text-text-tertiary">·</span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PanelEmpty({ title }: { title: string }) {
  return (
    <section className="rounded-[var(--r-md)] border border-dashed border-line bg-surface-1/40 p-4">
      <div className="flex items-center gap-2 text-[12px] text-text-tertiary">
        <span className="font-mono uppercase tracking-wider">{title}</span>
        <span>· awaiting synthesis</span>
      </div>
    </section>
  );
}

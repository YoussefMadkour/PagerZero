"use client";

import { motion } from "framer-motion";
import { Database, FileText, GitCommit, LineChart } from "lucide-react";
import type { ComponentType } from "react";

import type { SourceData } from "@/lib/api";

/**
 * Quantitative summary of what's being fed into the pipeline.
 *
 * Renders the moment a run starts, BEFORE any agent finishes. The judge
 * sees: 8,247 log lines + 120 metric points + 3 deploys all on one line —
 * proof of real intake, not a status spinner. See ADR 0002.
 */
export function SourceDataPanel({
  source,
  serviceName,
}: {
  source: SourceData | null;
  serviceName: string | null;
}) {
  if (!source || !serviceName) return null;

  const tokens =
    source.log_tokens_est >= 1000
      ? `${(source.log_tokens_est / 1000).toFixed(1)}k tokens`
      : `${source.log_tokens_est} tokens`;

  return (
    <motion.section
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.16, ease: "easeOut" }}
      className="rounded-[var(--r-md)] border border-line-strong bg-surface-1"
    >
      <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-text-tertiary">
          <Database className="h-3 w-3" />
          <span className="font-mono">ingesting</span>
          <span className="font-mono text-text-secondary">/{serviceName}</span>
        </div>
        <span className="font-mono text-[11px] text-text-tertiary">
          single 128k-context pass per agent
        </span>
      </header>

      <div className="grid grid-cols-3 divide-x divide-line">
        <Cell
          icon={FileText}
          label="logs"
          primary={`${source.log_lines.toLocaleString()} lines`}
          secondary={`~${tokens}`}
        />
        <Cell
          icon={LineChart}
          label="metrics"
          primary={`${source.metric_points} points`}
          secondary={`${source.metric_span_minutes} min · 5 series`}
        />
        <Cell
          icon={GitCommit}
          label="deploys"
          primary={`${source.deployments} commits`}
          secondary={`${source.deploys_window_minutes >= 60 ? `${Math.round(source.deploys_window_minutes / 60)}h` : `${source.deploys_window_minutes}m`} window`}
        />
      </div>
    </motion.section>
  );
}

function Cell({
  icon: Icon,
  label,
  primary,
  secondary,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  primary: string;
  secondary: string;
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <Icon className="h-4 w-4 shrink-0 text-text-tertiary" />
      <div className="min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-wider text-text-tertiary">
          {label}
        </div>
        <div className="mt-0.5 truncate text-[13px] tabular-nums text-text-primary">
          {primary}
        </div>
        <div className="text-[11px] text-text-tertiary">{secondary}</div>
      </div>
    </div>
  );
}

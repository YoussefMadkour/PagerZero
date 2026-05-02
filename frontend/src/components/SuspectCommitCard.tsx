"use client";

import { motion } from "framer-motion";
import { GitCommit, User, FileCode } from "lucide-react";

import type { DeploymentPreview, RootCauseOutput } from "@/lib/api";

/**
 * Renders the actual deploy the agents flagged — author, timestamp, files
 * touched, diff summary. The "is this real?" credibility lift: judges see
 * texture-of-real-ops-data (commit SHAs, file paths, real names), not just
 * "the agent thinks deploy abc123f is suspicious."
 *
 * Joins root_cause output → deployment_correlation.most_likely_culprit
 * SHA against the deployments_preview list shipped at pipeline start.
 */
export function SuspectCommitCard({
  rootCause,
  deployments,
}: {
  rootCause: RootCauseOutput | null;
  deployments: DeploymentPreview[];
}) {
  if (!rootCause) return null;

  // The root_cause output cites evidence_from_deployments which references
  // a commit SHA. Find the matching deployment in the preview.
  const evidenceText = rootCause.top_hypothesis.evidence_from_deployments
    .join(" ")
    .toLowerCase();
  const culprit = deployments.find((d) =>
    evidenceText.includes(d.commit_sha.toLowerCase()),
  );

  if (!culprit) return null;

  const when = new Date(culprit.timestamp);

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="rounded-[var(--r-md)] border border-line-strong bg-surface-1"
    >
      <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <GitCommit className="h-4 w-4 text-state-running" />
          <h3 className="text-[13px] font-semibold tracking-tight">
            Suspect commit
          </h3>
        </div>
        <code className="rounded-[3px] bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-text-secondary">
          {culprit.commit_sha}
        </code>
      </header>

      <div className="px-4 py-3">
        <p className="text-[13px] font-medium leading-snug text-text-primary">
          {culprit.message}
        </p>

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-text-tertiary">
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span className="font-mono text-text-secondary">
              {culprit.author}
            </span>
          </span>
          <span>·</span>
          <time className="font-mono" dateTime={culprit.timestamp}>
            {when.toISOString().replace("T", " ").slice(0, 19)} UTC
          </time>
        </div>

        <div className="mt-3 rounded-[var(--r-sm)] border border-line bg-surface-0/60 p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-text-tertiary">
            <FileCode className="h-3 w-3" />
            <span className="font-mono">
              {culprit.files_changed.length} file
              {culprit.files_changed.length === 1 ? "" : "s"} changed
            </span>
          </div>
          <ul className="mt-1.5 space-y-0.5 font-mono text-[11px] text-text-secondary">
            {culprit.files_changed.map((path) => (
              <li key={path} className="truncate">
                {path}
              </li>
            ))}
          </ul>
          <p className="mt-2.5 border-t border-line pt-2 text-[11px] leading-relaxed text-text-secondary">
            <span className="font-mono uppercase tracking-wider text-text-tertiary">
              diff
            </span>{" "}
            <span>{culprit.diff_summary}</span>
          </p>
        </div>
      </div>
    </motion.section>
  );
}

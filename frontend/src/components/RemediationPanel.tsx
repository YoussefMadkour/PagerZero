"use client";

import { motion } from "framer-motion";
import { Check, Copy, MessageSquare, ScrollText, Wrench } from "lucide-react";
import { useState } from "react";

import type { RemediationOutput, RemediationStep } from "@/lib/api";
import { cn } from "@/lib/cn";

export function RemediationPanel({ output }: { output: RemediationOutput | null }) {
  if (!output) {
    return (
      <section className="rounded-[var(--r-md)] border border-dashed border-line bg-surface-1/40 p-4">
        <div className="flex items-center gap-2 text-[12px] text-text-tertiary">
          <span className="font-mono uppercase tracking-wider">remediation</span>
          <span>· awaiting root cause</span>
        </div>
      </section>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="space-y-4"
    >
      <StepGroup
        icon={Wrench}
        title="Immediate mitigation"
        steps={output.immediate_mitigation}
      />
      {output.rollback_procedure.length > 0 && (
        <StepGroup
          icon={Wrench}
          title="Rollback procedure"
          steps={output.rollback_procedure}
        />
      )}
      <StakeholderNote text={output.stakeholder_notification} />
      <IncidentReport markdown={output.incident_report_markdown} />
    </motion.section>
  );
}

function StepGroup({
  title,
  icon: Icon,
  steps,
}: {
  title: string;
  icon: typeof Wrench;
  steps: RemediationStep[];
}) {
  return (
    <div className="rounded-[var(--r-md)] border border-line-strong bg-surface-1">
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-state-running" />
          <h3 className="text-[13px] font-semibold tracking-tight">{title}</h3>
        </div>
        <span className="font-mono text-[11px] text-text-tertiary tabular-nums">
          {steps.length} step{steps.length !== 1 && "s"}
        </span>
      </header>
      <ol className="divide-y divide-line">
        {steps.map((step) => (
          <li key={step.step_number} className="px-4 py-3">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-[3px] bg-surface-2 font-mono text-[11px] tabular-nums text-text-secondary">
                {step.step_number}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-[13px] leading-relaxed text-text-primary">
                  {step.description}
                  {step.is_destructive && (
                    <span className="ml-2 rounded-[3px] bg-state-error/15 px-1.5 py-0.5 align-middle font-mono text-[10px] uppercase tracking-wider text-state-error">
                      destructive
                    </span>
                  )}
                </p>
                {step.command && <CommandLine command={step.command} />}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function CommandLine({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      /* ignore — clipboard may be unavailable in some demo environments */
    }
  };

  return (
    <div className="mt-2 flex items-center gap-2 rounded-[var(--r-sm)] border border-line bg-surface-0 pl-3">
      <span className="select-none font-mono text-[11px] text-text-tertiary">
        $
      </span>
      <code className="flex-1 truncate font-mono text-[12px] text-text-primary">
        {command}
      </code>
      <button
        onClick={onCopy}
        className={cn(
          "flex items-center gap-1 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wider",
          "border-l border-line text-text-tertiary transition-colors",
          "hover:bg-surface-1 hover:text-text-primary",
        )}
        aria-label="Copy command"
      >
        {copied ? (
          <>
            <Check className="h-3 w-3 text-state-done" />
            copied
          </>
        ) : (
          <>
            <Copy className="h-3 w-3" />
            copy
          </>
        )}
      </button>
    </div>
  );
}

function StakeholderNote({ text }: { text: string }) {
  return (
    <div className="rounded-[var(--r-md)] border border-line bg-surface-1 p-4">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-text-tertiary">
        <MessageSquare className="h-3 w-3" />
        <span className="font-mono">stakeholder notification</span>
      </div>
      <p className="mt-2 text-[13px] leading-relaxed text-text-secondary">
        {text}
      </p>
    </div>
  );
}

function IncidentReport({ markdown }: { markdown: string }) {
  const [open, setOpen] = useState(false);
  return (
    <details
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
      className="rounded-[var(--r-md)] border border-line bg-surface-1"
    >
      <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-[13px] font-semibold tracking-tight">
        <span className="flex items-center gap-2">
          <ScrollText className="h-4 w-4 text-text-secondary" />
          Drafted incident report
        </span>
        <span className="font-mono text-[11px] text-text-tertiary">
          {open ? "hide" : "show"}
        </span>
      </summary>
      <pre className="overflow-x-auto border-t border-line px-4 py-3 font-mono text-[12px] leading-relaxed text-text-secondary whitespace-pre-wrap">
        {markdown}
      </pre>
    </details>
  );
}

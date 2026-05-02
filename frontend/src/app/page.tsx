"use client";

import { useEffect, useState } from "react";

import { AGENT_ORDER, fetchScenarios, type ScenarioMeta } from "@/lib/api";
import { useIncidentRun } from "@/lib/useIncidentRun";

import { AgentCard } from "@/components/AgentCard";
import { AlertBanner } from "@/components/AlertBanner";
import { Header } from "@/components/Header";
import { ParallelTimingChart } from "@/components/ParallelTimingChart";
import { RemediationPanel } from "@/components/RemediationPanel";
import { RootCausePanel } from "@/components/RootCausePanel";
import { ScenarioPicker } from "@/components/ScenarioPicker";
import { SourceDataPanel } from "@/components/SourceDataPanel";

const DEFAULT_SCENARIO = "scenario_a_memory_leak";

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<ScenarioMeta[]>([]);
  const [selected, setSelected] = useState<string>(DEFAULT_SCENARIO);
  const [loadError, setLoadError] = useState<string | null>(null);
  const { state, run, reset } = useIncidentRun();

  useEffect(() => {
    fetchScenarios()
      .then((s) => {
        setScenarios(s);
        if (s.length && !s.find((x) => x.id === DEFAULT_SCENARIO)) {
          setSelected(s[0].id);
        }
      })
      .catch((err) => setLoadError(err.message));
  }, []);

  // Spacebar fires the run when not already running, so the demo can be
  // driven hands-free during a pitch.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code !== "Space") return;
      const target = e.target as HTMLElement | null;
      // Don't hijack space when the user is typing in an input.
      if (
        target &&
        ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)
      )
        return;
      if (state.phase === "running" || !selected) return;
      e.preventDefault();
      if (state.phase === "completed" || state.phase === "error") {
        reset();
      } else {
        run(selected);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [state.phase, selected, run, reset]);

  return (
    <div className="flex min-h-dvh flex-col">
      <Header runState={state} />

      <main className="flex-1 pz-grid-bg">
        <div className="mx-auto w-full max-w-[1400px] px-6 py-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-[22px] font-semibold tracking-tight">
                Incident response console
              </h1>
              <p className="mt-1 text-[13px] text-text-secondary">
                Five agents read the incident in parallel — root cause and
                remediation in seconds, not minutes.
              </p>
            </div>
            <ScenarioPicker
              scenarios={scenarios}
              selected={selected}
              onSelect={setSelected}
              onTrigger={() => run(selected)}
              onReset={reset}
              phase={state.phase}
            />
          </div>

          {loadError && (
            <div className="mt-4 rounded-[var(--r-md)] border border-state-error-line bg-[color:var(--state-error-dim)] px-4 py-3 text-[13px] text-state-error">
              Backend unreachable at <code>/api/scenarios</code>: {loadError}.
              Start it with{" "}
              <code className="font-mono">
                uv run uvicorn pagerzero.api.main:app --port 8000
              </code>
              .
            </div>
          )}

          <div className="mt-6 space-y-3">
            <AlertBanner runState={state} />
            <SourceDataPanel
              source={state.sourceData}
              serviceName={state.serviceName}
            />
          </div>

          <section className="mt-6 grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
            {AGENT_ORDER.map((name, idx) => (
              <AgentCard
                key={name}
                name={name}
                index={idx}
                state={state.agents[name]}
              />
            ))}
          </section>

          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[1.4fr,1fr]">
            <div className="space-y-6">
              <RootCausePanel output={state.finalState?.root_cause ?? null} />
              <RemediationPanel
                output={state.finalState?.remediation ?? null}
              />
            </div>
            <aside className="space-y-6">
              <ParallelTimingChart
                agents={state.agents}
                phase={state.phase}
                pipelineStartedAt={state.startedAt}
                pipelineEndedAt={state.endedAt}
              />
            </aside>
          </div>
        </div>
      </main>

      <footer className="border-t border-line py-4 text-center text-[11px] text-text-tertiary">
        <span className="font-mono">PagerZero</span> · built for AMD Developer
        Hackathon · Track 1 · MIT
      </footer>
    </div>
  );
}

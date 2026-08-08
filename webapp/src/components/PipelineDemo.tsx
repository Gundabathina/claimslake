import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { pipelineDemoStages } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

type Status = "idle" | "running" | "done";

export function PipelineDemo() {
  const [statuses, setStatuses] = useState<Status[]>(pipelineDemoStages.map(() => "idle"));
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef<number | null>(null);

  const reset = () => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    setStatuses(pipelineDemoStages.map(() => "idle"));
    setPlaying(false);
  };

  const run = () => {
    if (playing) return;
    reset();
    setPlaying(true);
    let i = 0;
    const step = () => {
      setStatuses((prev) => {
        const next = [...prev];
        if (i > 0) next[i - 1] = "done";
        if (i < pipelineDemoStages.length) next[i] = "running";
        return next;
      });
      i += 1;
      if (i <= pipelineDemoStages.length) {
        timerRef.current = window.setTimeout(step, 900);
      } else {
        setPlaying(false);
      }
    };
    step();
  };

  useEffect(() => () => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
  }, []);

  return (
    <section id="demo" className="mx-auto max-w-6xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="Pipeline demo"
          title="Watch the DAG run"
          description="A visual simulation of the claimslake_pipeline Airflow DAG's five stages, in the real order they run in."
        />
      </Reveal>

      <Reveal delay={0.1} className="mt-4">
        <div className="rounded-lg border border-gold/30 bg-gold/5 px-4 py-2.5 text-xs text-gold font-mono inline-block">
          SIMULATION — this replays real stage names and order from the DAG; it does not execute Spark, dbt, or
          Airflow in your browser, and shows no invented metrics.
        </div>
      </Reveal>

      <Reveal delay={0.15} className="mt-8">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={run}
            disabled={playing}
            className="focus-ring rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-bg hover:brightness-110 transition disabled:opacity-50"
          >
            {playing ? "Running…" : "Run simulation"}
          </button>
          <button
            onClick={reset}
            className="focus-ring rounded-lg border border-border px-5 py-2.5 text-sm text-text-dim hover:text-text transition"
          >
            Reset
          </button>
        </div>

        <div className="card divide-y divide-border-soft overflow-hidden">
          {pipelineDemoStages.map((stage, i) => {
            const status = statuses[i];
            return (
              <div key={stage.id} className="flex items-start gap-4 p-5">
                <div className="mt-0.5 relative flex h-6 w-6 shrink-0 items-center justify-center">
                  {status === "done" && (
                    <motion.svg
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <circle cx="12" cy="12" r="11" className="fill-accent" />
                      <path d="M7 12.5l3 3 7-7" stroke="#08090c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </motion.svg>
                  )}
                  {status === "running" && (
                    <motion.span
                      animate={{ rotate: 360 }}
                      transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
                      className="h-5 w-5 rounded-full border-2 border-accent border-t-transparent"
                    />
                  )}
                  {status === "idle" && <span className="h-5 w-5 rounded-full border-2 border-border" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-sm font-medium text-text">{stage.title}</span>
                    <span className="font-mono text-[11px] text-text-faint">{stage.id}</span>
                  </div>
                  <p className="mt-1 text-sm text-text-dim">{stage.description}</p>
                </div>
                <span
                  className={`font-mono text-[11px] uppercase tracking-wide shrink-0 mt-1 ${
                    status === "done" ? "text-accent" : status === "running" ? "text-gold" : "text-text-faint"
                  }`}
                >
                  {status}
                </span>
              </div>
            );
          })}
        </div>
      </Reveal>
    </section>
  );
}

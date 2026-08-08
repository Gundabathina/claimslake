import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { architectureNodes } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

const groupColor: Record<string, string> = {
  source: "bg-silver",
  compute: "bg-accent",
  storage: "bg-bronze",
  orchestration: "bg-blue",
  analytics: "bg-gold",
  iac: "bg-blue",
  cicd: "bg-accent",
};

const groupLabel: Record<string, string> = {
  source: "Source",
  compute: "Compute",
  storage: "Storage",
  orchestration: "Orchestration",
  analytics: "Analytics",
  iac: "IaC",
  cicd: "CI/CD",
};

export function Architecture() {
  const [active, setActive] = useState(architectureNodes[0].id);
  const node = architectureNodes.find((n) => n.id === active)!;

  return (
    <section id="architecture" className="mx-auto max-w-6xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="Interactive architecture"
          title="Every component, end to end"
          description="From synthetic source files to a Terraform AWS reference architecture. Click any node to see what it does in this project."
        />
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {architectureNodes.map((n, i) => {
            const isActive = n.id === active;
            return (
              <button
                key={n.id}
                onClick={() => setActive(n.id)}
                className={`focus-ring text-left rounded-xl border p-4 transition-all ${
                  isActive ? "border-accent-dim bg-surface-2" : "border-border bg-surface hover:border-border-soft"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] text-text-faint">{String(i + 1).padStart(2, "0")}</span>
                  <span className={`h-1.5 w-1.5 rounded-full ${groupColor[n.group]}`} aria-hidden />
                </div>
                <p className={`mt-2 text-sm font-medium ${isActive ? "text-accent" : "text-text"}`}>{n.label}</p>
              </button>
            );
          })}
        </div>
      </Reveal>

      <AnimatePresence mode="wait">
        <motion.div
          key={node.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.3 }}
          className="mt-6 card p-6 flex items-start gap-4"
        >
          <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${groupColor[node.group]}`} aria-hidden />
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-mono text-sm font-semibold text-text">{node.label}</h3>
              <span className="font-mono text-[10px] uppercase tracking-wide text-text-faint border border-border rounded-full px-2 py-0.5">
                {groupLabel[node.group]}
              </span>
            </div>
            <p className="mt-2 text-sm text-text-dim leading-relaxed">{node.detail}</p>
          </div>
        </motion.div>
      </AnimatePresence>

      <p className="mt-6 text-xs text-text-faint">
        MinIO stands in locally for S3; nothing here is exposed publicly. The Terraform module describes how the
        same layout would map to real AWS services — see Engineering Decisions below.
      </p>
    </section>
  );
}

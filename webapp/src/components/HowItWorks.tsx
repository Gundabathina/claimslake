import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { layers } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

const colorMap: Record<string, { text: string; bg: string; border: string; dot: string }> = {
  bronze: { text: "text-bronze", bg: "bg-bronze/10", border: "border-bronze/40", dot: "bg-bronze" },
  silver: { text: "text-silver", bg: "bg-silver/10", border: "border-silver/40", dot: "bg-silver" },
  gold: { text: "text-gold", bg: "bg-gold/10", border: "border-gold/40", dot: "bg-gold" },
};

export function HowItWorks() {
  const [active, setActive] = useState(layers[0].id);
  const layer = layers.find((l) => l.id === active)!;
  const c = colorMap[layer.color];

  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="How it works"
          title="Bronze → Silver → Gold"
          description="Synthetic claims data moves through three layers, each with a distinct job. Select a layer to see what actually happens inside it."
        />
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <div className="flex flex-col sm:flex-row items-stretch gap-3 sm:gap-0">
          {layers.map((l, i) => {
            const lc = colorMap[l.color];
            const isActive = l.id === active;
            return (
              <div key={l.id} className="flex items-center flex-1">
                <button
                  onClick={() => setActive(l.id)}
                  className={`focus-ring w-full text-left rounded-xl border px-5 py-4 transition-all ${
                    isActive ? `${lc.border} ${lc.bg}` : "border-border bg-surface hover:border-border-soft"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${lc.dot}`} aria-hidden />
                    <span className={`font-mono text-sm font-semibold ${isActive ? lc.text : "text-text"}`}>
                      {l.name}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-text-faint">{l.tagline}</p>
                </button>
                {i < layers.length - 1 && (
                  <span className="hidden sm:block mx-2 text-text-faint" aria-hidden>
                    →
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </Reveal>

      <AnimatePresence mode="wait">
        <motion.div
          key={layer.id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.35 }}
          className="mt-8 card p-6 sm:p-8"
        >
          <div className="grid md:grid-cols-[1.4fr_1fr] gap-8">
            <div>
              <h3 className={`font-mono text-sm font-semibold uppercase tracking-wide ${c.text}`}>
                {layer.name} layer
              </h3>
              <p className="mt-3 text-text-dim leading-relaxed">{layer.description}</p>
            </div>
            <div>
              <ul className="space-y-2">
                {layer.bullets.map((b) => (
                  <li key={b} className="flex gap-2 text-sm text-text-dim">
                    <span className={`mt-1.5 h-1 w-1 shrink-0 rounded-full ${c.dot}`} aria-hidden />
                    {b}
                  </li>
                ))}
              </ul>
              <div className="mt-5 flex flex-wrap gap-2">
                {layer.tech.map((t) => (
                  <span key={t} className="font-mono text-[11px] rounded-full border border-border px-2.5 py-1 text-text-faint">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </section>
  );
}

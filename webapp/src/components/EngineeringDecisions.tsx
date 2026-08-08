import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { decisions } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

export function EngineeringDecisions() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="decisions" className="mx-auto max-w-4xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="Engineering decisions"
          title="Why it's built this way"
          description="The reasoning behind each major technology and architecture choice."
        />
      </Reveal>

      <Reveal delay={0.1} className="mt-10 card divide-y divide-border-soft overflow-hidden">
        {decisions.map((d, i) => {
          const isOpen = open === i;
          return (
            <div key={d.q}>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                className="focus-ring w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
                aria-expanded={isOpen}
              >
                <span className="text-sm font-medium text-text">{d.q}</span>
                <motion.span
                  animate={{ rotate: isOpen ? 45 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="shrink-0 text-accent text-lg leading-none"
                  aria-hidden
                >
                  +
                </motion.span>
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <p className="px-5 pb-5 text-sm text-text-dim leading-relaxed">{d.a}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </Reveal>
    </section>
  );
}

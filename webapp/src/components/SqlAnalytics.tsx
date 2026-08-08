import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sqlQueries, REPO_URL } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

export function SqlAnalytics() {
  const [active, setActive] = useState(sqlQueries[0].id);
  const query = sqlQueries.find((q) => q.id === active)!;

  return (
    <section id="sql" className="mx-auto max-w-5xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="SQL analytics"
          title="35 curated queries, four real examples"
          description="Actual queries from the sql/ layer — grouped into claims, finance, members, providers, and data quality. Results aren't shown here since they depend on a locally built Gold warehouse; run them yourself with DuckDB."
        />
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <div className="flex flex-wrap gap-2">
          {sqlQueries.map((q) => (
            <button
              key={q.id}
              onClick={() => setActive(q.id)}
              className={`focus-ring rounded-full border px-4 py-2 font-mono text-xs transition-colors ${
                active === q.id
                  ? "border-accent-dim text-accent bg-accent/5"
                  : "border-border text-text-faint hover:text-text-dim"
              }`}
            >
              {q.domain}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={query.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.3 }}
            className="mt-6 card overflow-hidden"
          >
            <div className="px-6 pt-5">
              <h3 className="font-medium text-text">{query.title}</h3>
              <p className="mt-1 text-sm text-text-dim">{query.question}</p>
              <p className="mt-2 text-xs text-text-faint leading-relaxed">{query.why}</p>
            </div>
            <pre className="mt-5 overflow-x-auto bg-surface-2 px-6 py-5 text-[13px] leading-relaxed text-silver font-mono border-t border-border-soft">
{query.sql}
            </pre>
          </motion.div>
        </AnimatePresence>
      </Reveal>

      <p className="mt-6 text-xs text-text-faint">
        Full catalog:{" "}
        <a href={`${REPO_URL}/blob/main/docs/analytics_catalog.md`} target="_blank" rel="noreferrer" className="underline hover:text-text-dim">
          docs/analytics_catalog.md
        </a>{" "}
        · run with <code className="font-mono">duckdb gold/claimslake.duckdb &lt; sql/run_all.sql</code>
      </p>
    </section>
  );
}

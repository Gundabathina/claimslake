import { motion } from "framer-motion";
import { hero, REPO_URL } from "../content";

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-grid">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, rgba(94,234,212,0.14) 0%, rgba(8,9,12,0) 70%)",
        }}
        aria-hidden
      />
      <div className="relative mx-auto max-w-5xl px-5 sm:px-8 pt-28 pb-24 sm:pt-36 sm:pb-32 text-center">
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="font-mono text-xs uppercase tracking-[0.25em] text-accent-dim"
        >
          {hero.eyebrow}
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mt-5 text-5xl sm:text-7xl font-bold tracking-tight text-text text-glow"
        >
          {hero.title}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-3 text-xl sm:text-2xl font-medium text-silver"
        >
          {hero.subtitle}
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-6 max-w-2xl mx-auto text-text-dim leading-relaxed"
        >
          {hero.description}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-9 flex flex-wrap items-center justify-center gap-3"
        >
          {hero.ctas.map((cta) => (
            <a
              key={cta.label}
              href={cta.href}
              target={cta.external ? "_blank" : undefined}
              rel={cta.external ? "noreferrer" : undefined}
              className={
                cta.primary
                  ? "focus-ring rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-bg hover:brightness-110 transition"
                  : "focus-ring rounded-lg border border-border px-6 py-3 text-sm font-semibold text-text hover:border-accent-dim hover:text-accent transition"
              }
            >
              {cta.label} {cta.external ? "↗" : ""}
            </a>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6"
        >
          {hero.stats.map((s) => (
            <div key={s.label} className="card px-4 py-5">
              <div className="font-mono text-2xl font-semibold text-text">{s.value}</div>
              <div className="mt-1 text-xs text-text-faint">{s.label}</div>
            </div>
          ))}
        </motion.div>

        <p className="mt-6 text-xs text-text-faint">
          Verified locally at v1.0.0 ·{" "}
          <a href={REPO_URL} className="underline hover:text-text-dim" target="_blank" rel="noreferrer">
            source on GitHub
          </a>
        </p>
      </div>
    </section>
  );
}

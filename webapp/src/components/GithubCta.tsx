import { ctas, limitations } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

export function GithubCta() {
  return (
    <section id="cta" className="mx-auto max-w-5xl px-5 sm:px-8 py-24">
      <Reveal>
        <div className="card p-8 sm:p-12 text-center bg-grid">
          <SectionHeading
            eyebrow="Explore further"
            title="Three ways to go deeper"
            description="A recruiter path: read the code, read the docs, or see other work."
          />
          <div className="mx-auto mt-4 max-w-none flex flex-col sm:flex-row items-center justify-center gap-3">
            {[ctas.source, ctas.docs, ctas.portfolio].map((c, i) => (
              <a
                key={c.href}
                href={c.href}
                target="_blank"
                rel="noreferrer"
                className={`focus-ring w-full sm:w-auto rounded-lg px-6 py-3 text-sm font-semibold transition ${
                  i === 0
                    ? "bg-accent text-bg hover:brightness-110"
                    : "border border-border text-text hover:border-accent-dim hover:text-accent"
                }`}
              >
                {c.label} ↗
              </a>
            ))}
          </div>
        </div>
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-text-faint">Honest limitations</h3>
        <ul className="mt-4 space-y-2">
          {limitations.map((l) => (
            <li key={l} className="flex gap-2 text-sm text-text-dim">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-text-faint" aria-hidden />
              {l}
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}

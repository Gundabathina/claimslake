import { evidence } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

export function Evidence() {
  return (
    <section id="evidence" className="mx-auto max-w-6xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="Real project evidence"
          title="Backed by the repository, not slides"
          description="Every item below links directly to the file or test suite it describes. No screenshots or demo video are embedded yet — the repository's docs/screenshots/ directory is a placeholder pending capture."
        />
      </Reveal>

      <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {evidence.map((e, i) => (
          <Reveal key={e.title} delay={i * 0.05}>
            <div className="card p-6 h-full flex flex-col">
              <h3 className="font-medium text-text">{e.title}</h3>
              <p className="mt-1 font-mono text-xs text-accent">{e.status}</p>
              <p className="mt-3 text-sm text-text-dim leading-relaxed flex-1">{e.detail}</p>
              <a
                href={e.link.href}
                target="_blank"
                rel="noreferrer"
                className="focus-ring mt-4 inline-flex items-center gap-1 font-mono text-xs text-text-faint hover:text-accent transition-colors"
              >
                {e.link.label} ↗
              </a>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

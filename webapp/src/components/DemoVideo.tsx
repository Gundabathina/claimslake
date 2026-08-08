import { REPO_URL } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

export function DemoVideo() {
  return (
    <section id="video" className="mx-auto max-w-5xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading eyebrow="Project demo video" title="Walkthrough" />
      </Reveal>

      <Reveal delay={0.1}>
        <div className="mt-8 card aspect-video flex flex-col items-center justify-center gap-3 bg-grid">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" className="text-text-faint">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10 8.5l6 3.5-6 3.5v-7z" fill="currentColor" />
          </svg>
          <p className="text-sm text-text-dim">Screen-capture walkthrough coming soon</p>
          <p className="text-xs text-text-faint max-w-sm text-center px-4">
            Listed as future work in the project's changelog. In the meantime, explore the pipeline simulation above
            or read the code directly.
          </p>
          <a
            href={`${REPO_URL}#readme`}
            target="_blank"
            rel="noreferrer"
            className="focus-ring mt-1 text-xs text-accent hover:underline"
          >
            Read the full README ↗
          </a>
        </div>
      </Reveal>
    </section>
  );
}

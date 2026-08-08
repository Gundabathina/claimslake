import { techStack } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

export function TechStack() {
  return (
    <section id="stack" className="mx-auto max-w-5xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading eyebrow="Technical stack" title="Every layer, and why it's there" />
      </Reveal>

      <Reveal delay={0.1} className="mt-10 card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[560px]">
            <thead>
              <tr className="border-b border-border-soft">
                <th className="font-mono text-[11px] uppercase tracking-wide text-text-faint px-5 py-3">Layer</th>
                <th className="font-mono text-[11px] uppercase tracking-wide text-text-faint px-5 py-3">Technology</th>
                <th className="font-mono text-[11px] uppercase tracking-wide text-text-faint px-5 py-3">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {techStack.map((t) => (
                <tr key={t.layer} className="border-b border-border-soft/60 last:border-0">
                  <td className="px-5 py-3 text-sm text-text-dim whitespace-nowrap">{t.layer}</td>
                  <td className="px-5 py-3 text-sm text-text font-medium whitespace-nowrap">{t.tech}</td>
                  <td className="px-5 py-3 text-sm text-text-dim">{t.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Reveal>
    </section>
  );
}

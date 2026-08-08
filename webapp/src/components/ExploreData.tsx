import { sampleData } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

const layers = [
  { key: "bronze", data: sampleData.bronze, color: "bronze" },
  { key: "silver", data: sampleData.silver, color: "silver" },
  { key: "gold", data: sampleData.gold, color: "gold" },
] as const;

const colorText: Record<string, string> = { bronze: "text-bronze", silver: "text-silver", gold: "text-gold" };

export function ExploreData() {
  return (
    <section id="data" className="mx-auto max-w-6xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="Explore the data"
          title="Sample records, layer by layer"
          description="Small synthetic samples showing the shape of the data at each stage. No real patient, member, or claims data — everything here is generated."
        />
      </Reveal>

      <div className="mt-10 grid lg:grid-cols-3 gap-5">
        {layers.map((l, i) => (
          <Reveal key={l.key} delay={i * 0.08}>
            <div className="card p-5 h-full flex flex-col">
              <h3 className={`font-mono text-xs font-semibold uppercase tracking-wide ${colorText[l.color]}`}>
                {l.data.label}
              </h3>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr>
                      {l.data.columns.map((c) => (
                        <th
                          key={c}
                          className="font-mono text-[10px] uppercase tracking-wide text-text-faint pb-2 pr-3 whitespace-nowrap border-b border-border-soft"
                        >
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {l.data.rows.map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td
                            key={ci}
                            className="font-mono text-xs text-text-dim py-2 pr-3 whitespace-nowrap border-b border-border-soft/60"
                          >
                            {cell || <span className="text-text-faint">—</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {"note" in l.data && l.data.note && (
                <p className="mt-4 text-[11px] text-text-faint leading-relaxed">{l.data.note}</p>
              )}
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

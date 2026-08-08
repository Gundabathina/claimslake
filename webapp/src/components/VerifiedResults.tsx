import { verifiedResults } from "../content";
import { SectionHeading } from "./SectionHeading";
import { Reveal } from "./Reveal";

function StatusPill({ status }: { status: string }) {
  const isDone = status.startsWith("Complete") || status === "Verified locally";
  const isRef = status.includes("CI-validated") || status.includes("Reference") || status.includes("Optional");
  return (
    <span
      className={`font-mono text-[11px] rounded-full px-2.5 py-1 border shrink-0 ${
        isDone
          ? "border-accent-dim/40 text-accent bg-accent/5"
          : isRef
          ? "border-gold/40 text-gold bg-gold/5"
          : "border-border text-text-faint"
      }`}
    >
      {status}
    </span>
  );
}

export function VerifiedResults() {
  return (
    <section id="results" className="mx-auto max-w-4xl px-5 sm:px-8 py-24">
      <Reveal>
        <SectionHeading
          eyebrow="Verified results"
          title="Only repository-backed facts"
          description="Straight from the README's milestone and verified-results tables — nothing here is extrapolated."
        />
      </Reveal>

      <Reveal delay={0.1} className="mt-10 card divide-y divide-border-soft overflow-hidden">
        {verifiedResults.map((r) => (
          <div key={r.milestone} className="flex items-center justify-between gap-4 px-5 py-3.5">
            <span className="text-sm text-text">{r.milestone}</span>
            <StatusPill status={r.status} />
          </div>
        ))}
      </Reveal>
    </section>
  );
}

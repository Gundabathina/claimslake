export function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="max-w-2xl">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent-dim mb-3">
        {eyebrow}
      </p>
      <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-text">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-text-dim leading-relaxed">{description}</p>
      )}
    </div>
  );
}

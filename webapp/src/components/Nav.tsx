import { useEffect, useState } from "react";
import { REPO_URL } from "../content";

const LINKS = [
  { href: "#how-it-works", label: "Pipeline" },
  { href: "#architecture", label: "Architecture" },
  { href: "#demo", label: "Demo" },
  { href: "#evidence", label: "Evidence" },
  { href: "#data", label: "Data" },
  { href: "#sql", label: "SQL" },
  { href: "#stack", label: "Stack" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 transition-colors duration-300 ${
        scrolled ? "bg-bg/85 backdrop-blur border-b border-border" : "bg-transparent"
      }`}
    >
      <nav className="mx-auto max-w-6xl px-5 sm:px-8 h-16 flex items-center justify-between">
        <a href="#top" className="font-semibold tracking-tight text-text flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-accent" aria-hidden />
          ClaimsLake
        </a>

        <ul className="hidden md:flex items-center gap-7 font-mono text-[13px] text-text-dim">
          {LINKS.map((l) => (
            <li key={l.href}>
              <a href={l.href} className="hover:text-text transition-colors focus-ring rounded">
                {l.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="hidden md:block">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="focus-ring rounded-lg border border-border px-4 py-2 text-sm text-text hover:border-accent-dim hover:text-accent transition-colors"
          >
            GitHub
          </a>
        </div>

        <button
          className="md:hidden text-text focus-ring rounded p-2"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
            {open ? (
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            ) : (
              <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            )}
          </svg>
        </button>
      </nav>

      {open && (
        <div className="md:hidden border-t border-border bg-bg px-5 pb-5 pt-2">
          <ul className="flex flex-col gap-1 font-mono text-sm text-text-dim">
            {LINKS.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  onClick={() => setOpen(false)}
                  className="block py-2.5 hover:text-text transition-colors"
                >
                  {l.label}
                </a>
              </li>
            ))}
            <li>
              <a
                href={REPO_URL}
                target="_blank"
                rel="noreferrer"
                className="block py-2.5 text-accent"
              >
                GitHub ↗
              </a>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}

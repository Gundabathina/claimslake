import { REPO_URL, PORTFOLIO_URL } from "../content";

export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto max-w-6xl px-5 sm:px-8 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="font-mono text-xs text-text-faint">
          ClaimsLake — synthetic data only · built by Gundabathina
        </p>
        <div className="flex items-center gap-5 font-mono text-xs text-text-faint">
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="hover:text-text-dim transition-colors">
            GitHub
          </a>
          <a href={`${REPO_URL}#readme`} target="_blank" rel="noreferrer" className="hover:text-text-dim transition-colors">
            Docs
          </a>
          <a href={PORTFOLIO_URL} target="_blank" rel="noreferrer" className="hover:text-text-dim transition-colors">
            Portfolio
          </a>
        </div>
      </div>
    </footer>
  );
}

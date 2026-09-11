import { useEffect } from "react";
import { useStore } from "../../state/store";
import { BuildBoard } from "./BuildBoard";
import { InspectionsList } from "./InspectionsList";
import { SiteAppBar } from "./SiteAppBar";
import { SiteNav } from "./SiteNav";

const TITLES = { board: "Build board", inspections: "Inspections" } as const;

/**
 * The whole site surface. Mounted INSTEAD of the design workbench, never over it.
 *
 * That is the design decision the rest of this folder rests on. The readers render as a
 * dialog over a dimmed canvas with Canvas2D and Panel3D still mounted behind them; this is
 * a second top-level surface, so a phone standing in a basement runs no WebGL, fetches no
 * three.js chunk, and holds no plan geometry in memory.
 */
function age(at: number): string {
  if (!at) return "";
  const minutes = Math.round((Date.now() - at) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 48 ? `${hours} h ago` : `${Math.round(hours / 24)} days ago`;
}

export function SiteApp() {
  const sitePage = useStore((s) => s.sitePage);
  const loadSite = useStore((s) => s.loadSite);
  const stale = useStore((s) => s.siteStale);
  const cachedAt = useStore((s) => s.siteCachedAt);
  const error = useStore((s) => s.siteError);
  const dismiss = useStore((s) => s.dismissSiteError);
  // Both banners ride on BOTH pages. `checks_pending` was shipped end to end and rendered
  // by nothing: a board built between a rebuild and the check job shows every
  // finding-derived blocker as absent, which is the one wrong answer this surface must not
  // give quietly.
  const checksPending = useStore(
    (s) => Boolean(s.schedule?.checks_pending || s.inspections?.checks_pending));
  const errors = useStore(
    (s) => (sitePage === "board" ? s.schedule?.errors : s.inspections?.errors) ?? []);

  useEffect(() => { void loadSite(); }, [loadSite]);

  return (
    <div className="site-app">
      <SiteAppBar title={TITLES[sitePage]} />
      {stale && (
        <p className="site-banner" role="status">
          Offline snapshot from {age(cachedAt)} — nothing can be recorded until the engine
          is back. {error ?? "The engine is not reachable."}
        </p>
      )}
      {checksPending && (
        <p className="site-banner" role="status">
          The checks have not run against this model yet, so nothing below is blocked by a
          finding. Wait for the check job before trusting a green line.
        </p>
      )}
      {errors.length > 0 && (
        <div className="site-banner site-banner-error" role="alert">
          The site-state files do not describe a buildable sequence. This is the last valid
          state:
          <ul className="site-list">
            {errors.map((line) => (
              <li key={line} className="site-list-item">
                <span className="site-list-text">
                  <span className="site-list-title">{line}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {error && !stale && (
        <p className="site-banner site-banner-error" role="alert">
          {error}
          <button className="site-assist-chip" onClick={dismiss}>Dismiss</button>
        </p>
      )}
      <main className="site-main">
        {sitePage === "board" ? <BuildBoard /> : <InspectionsList />}
      </main>
      <SiteNav />
    </div>
  );
}

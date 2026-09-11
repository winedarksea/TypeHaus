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
export function SiteApp() {
  const sitePage = useStore((s) => s.sitePage);
  const loadSite = useStore((s) => s.loadSite);
  const stale = useStore((s) => s.siteStale);
  const error = useStore((s) => s.siteError);

  useEffect(() => { void loadSite(); }, [loadSite]);

  return (
    <div className="site-app">
      <SiteAppBar title={TITLES[sitePage]} />
      {stale && (
        <p className="site-banner" role="status">
          Showing the last board this device saw. {error ?? "The engine is not reachable."}
        </p>
      )}
      <main className="site-main">
        {sitePage === "board" ? <BuildBoard /> : <InspectionsList />}
      </main>
      <SiteNav />
    </div>
  );
}

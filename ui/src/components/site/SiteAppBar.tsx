import { Icon } from "../../icons/Icon";
import { useStore } from "../../state/store";

/**
 * MD3 small top app bar, centre-aligned on compact.
 *
 * The leading action is "Design", not a generic back arrow: this is a surface switch, not a
 * step in a history, and an arrow that promised the browser's back behaviour would be
 * lying about what it does.
 */
export function SiteAppBar({ title }: { title: string }) {
  const setSurface = useStore((s) => s.setSurface);
  const loadSite = useStore((s) => s.loadSite);
  const loading = useStore((s) => s.siteLoading);

  return (
    <header className="site-appbar">
      <button
        className="site-appbar-action"
        onClick={() => setSurface("design")}
        title="Back to the drawing"
      >
        <Icon name="arrow-left" size={22} />
        <span className="site-appbar-action-label">Design</span>
      </button>
      <h1 className="site-appbar-title">{title}</h1>
      <button
        className="site-appbar-action site-appbar-trailing"
        onClick={() => void loadSite()}
        title="Refresh from the engine"
        aria-label="Refresh"
        disabled={loading}
      >
        <Icon name={loading ? "search" : "redo"} size={22} />
      </button>
    </header>
  );
}

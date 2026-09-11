import { Icon } from "../../icons/Icon";
import { SITE_PAGES } from "../shell/navigationConfig";
import { useStore } from "../../state/store";
import { useIsCompact } from "../../hooks/useBreakpoint";

/**
 * MD3 navigation bar (compact) / navigation rail (>=680), two destinations.
 *
 * One component for both because the two differ only in orientation and in which class the
 * stylesheet hangs the layout off — unlike the design chrome's rail and bottom bar, these
 * have the same two items, the same labels and the same focus order.
 */
export function SiteNav() {
  const sitePage = useStore((s) => s.sitePage);
  const setSitePage = useStore((s) => s.setSitePage);
  const compact = useIsCompact();

  return (
    <nav className={compact ? "site-nav-bar" : "site-nav-rail"} aria-label="Site pages">
      {SITE_PAGES.map((page) => {
        const selected = sitePage === page.id;
        return (
          <button
            key={page.id}
            className={`site-nav-item${selected ? " active" : ""}`}
            aria-pressed={selected}
            title={page.hint}
            onClick={() => setSitePage(page.id)}
          >
            <span className="site-nav-indicator">
              <Icon name={page.icon} size={22} />
            </span>
            <span className="site-nav-label">{page.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

import { ICON_PATHS } from "./paths";
import type { IconName } from "./names";

/**
 * Inline SVG icon on a 24x24 grid.
 *
 * Always `aria-hidden`: an icon here is either decorating a labelled control or sitting in a
 * button that carries its own accessible name via `title`/`aria-label`. Announcing it twice
 * is worse than not announcing it, and `focusable="false"` keeps IE-era SVG out of the tab
 * order in the browsers that still do that.
 *
 * `stroke: currentColor` is what makes the MD3 state layer work on icon buttons — the icon
 * inherits the button's color, so the layer and the glyph stay in agreement automatically.
 */
export function Icon({ name, size = 20, className }: {
  name: IconName;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      className={className ? `icon ${className}` : "icon"}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      focusable="false"
    >
      {ICON_PATHS[name]}
    </svg>
  );
}

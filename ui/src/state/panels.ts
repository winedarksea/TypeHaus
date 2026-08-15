import type { IconName } from "../icons/names";

/**
 * The left-hand panel destinations, as one enum rather than three independent booleans.
 *
 * The booleans were already subtly wrong: setProjectDrawerOpen and setViewsPanelOpen each
 * force-closed the other, but setIssuesDrawerOpen closed neither, so Issues and Views could
 * both be open at once. Once all three are peer destinations in the navigation rail, "one at
 * a time" has to hold structurally instead of as two pairwise special cases — and the rail's
 * aria-selected needs a single source of truth rather than three booleans to re-derive from.
 */
export type PanelId = "project" | "views" | "issues";

export interface PanelSpec {
  id: PanelId;
  label: string;
  icon: IconName;
  hint: string;
}

/**
 * Order is the rail's order, top to bottom. Views sits first among the view-state panels
 * because it is the most-used destination in the app.
 */
export const PANELS: PanelSpec[] = [
  {
    id: "views",
    label: "Views",
    icon: "layers",
    hint: "Level, disciplines, representation, saved view recipes",
  },
  {
    id: "project",
    label: "Project",
    icon: "folder",
    hint: "Hierarchy, assemblies, building science, roof, details",
  },
  {
    id: "issues",
    label: "Issues",
    icon: "error",
    hint: "Errors, warnings and advisories from the model checks",
  },
];

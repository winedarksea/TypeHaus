import { useStore } from "../../state/store";
import { useIsCompact } from "../../hooks/useBreakpoint";
import { PANELS } from "../../state/panels";
import { Sheet } from "../ui/Sheet";
import { ViewsPanel } from "../ViewsPanel";
import { ProjectDrawer } from "../ProjectDrawer";
import { IssuesDrawer } from "../IssuesDrawer";

/**
 * Renders whichever left panel is active, as a docked panel on laptop/tablet and as a bottom
 * sheet on a phone.
 *
 * The panels themselves are unchanged — they render their own <aside> and their own contents.
 * At compact the same component is simply wrapped in a Sheet, because a 320px panel docked to
 * the left edge of a 390px viewport is not a panel, it is the whole screen with a sliver of
 * drawing behind it.
 */
export function PanelHost() {
  const activePanel = useStore((s) => s.activePanel);
  const setActivePanel = useStore((s) => s.setActivePanel);
  const isCompact = useIsCompact();

  const body = (
    <>
      <ViewsPanel />
      <ProjectDrawer />
      <IssuesDrawer />
    </>
  );

  if (!isCompact) return body;
  if (!activePanel) return null;

  const spec = PANELS.find((p) => p.id === activePanel);
  return (
    <Sheet title={spec?.label ?? "Panel"} onClose={() => setActivePanel(null)}>
      {body}
    </Sheet>
  );
}

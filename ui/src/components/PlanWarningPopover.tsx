import { useStore } from "../state/store";
import type { PlanWarningMarker } from "../model/planWarnings";
import type { Vec2 } from "../model/types";

// What the previously-mute plan markers say when clicked (→ TODO: the glowing red dot). Shows
// the marker's identifier, tier and message, the elements it involves, and any server findings
// that mention them — the same vocabulary the Issues drawer uses, so a marker and an issue read
// as one system.

const POPOVER_WIDTH_PX = 300;
const POPOVER_HEIGHT_ALLOWANCE_PX = 260;
const EDGE_MARGIN_PX = 12;

export function PlanWarningPopover({ marker, screen, viewport, onClose }: {
  marker: PlanWarningMarker;
  screen: Vec2;
  viewport: DOMRect | null;
  onClose: () => void;
}) {
  const model = useStore((s) => s.model);
  const zoomToUid = useStore((s) => s.zoomToUid);

  // Keep the card inside the pane even when the marker sits near an edge.
  const left = Math.max(EDGE_MARGIN_PX, Math.min(screen[0] + EDGE_MARGIN_PX,
    Math.max(EDGE_MARGIN_PX, (viewport?.width ?? 0) - POPOVER_WIDTH_PX - EDGE_MARGIN_PX)));
  const top = Math.max(EDGE_MARGIN_PX, Math.min(screen[1] + EDGE_MARGIN_PX,
    Math.max(EDGE_MARGIN_PX, (viewport?.height ?? 0) - POPOVER_HEIGHT_ALLOWANCE_PX)));

  const jump = (tag: string) => {
    const record = model?.walls.find((wall) => wall.tag === tag);
    if (record) zoomToUid(record.uid);
  };

  return (
    <aside className="plan-warning-popover" style={{ left, top, width: POPOVER_WIDTH_PX }}
      aria-label={`${marker.title} at ${marker.id}`}>
      <div className="plan-warning-head">
        <span className={`sev-dot sev-${marker.tier}`} aria-hidden />
        <div>
          <div className="plan-warning-title">{marker.title}</div>
          <div className="muted reader-mono">{marker.code} · {marker.id}</div>
        </div>
        <button className="wall-assembly-popup-close" onClick={onClose} aria-label="Close marker details">×</button>
      </div>
      <p className="plan-warning-message">{marker.message}</p>
      {marker.elementTags.length > 0 && (
        <div className="reader-tag-cloud">
          {marker.elementTags.map((tag) => (
            <button key={tag} className="reader-tag" onClick={() => jump(tag)} title="Zoom to element">
              {tag}
            </button>
          ))}
        </div>
      )}
      {marker.findings.length > 0 && (
        <>
          <div className="plan-warning-subhead">Related findings</div>
          <ul className="plan-warning-findings">
            {marker.findings.map((finding, index) => (
              <li key={index}>
                <span className={`sev-dot sev-${finding.severity}`} aria-hidden />
                {finding.code && <b className="reader-mono">{finding.code} </b>}
                {finding.message}
              </li>
            ))}
          </ul>
        </>
      )}
    </aside>
  );
}

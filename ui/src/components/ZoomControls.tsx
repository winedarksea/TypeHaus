import { Icon } from "../icons/Icon";
import { BUTTON_DOLLY_FACTOR } from "../three/cameraFraming";

// On-screen zoom, shared by the 2D plan and the 3D panel.
//
// The wheel is a fine zoom on a desk with a mouse, and a bad one everywhere else: a trackpad or
// tablet pinch is ambiguous — the browser may claim it as page zoom before the canvas ever sees
// it. So zoom gets a control you can point at, which no gesture arbitration can take away.
//
// `onZoom` takes a *multiplier* rather than a direction because the two panes zoom in different
// units (the 3D dolly is a radius in metres, the plan is px/m); a factor is the one thing they
// agree on. Above 1 means "further away" in both.
export function ZoomControls({ onZoom, label }: {
  onZoom: (factor: number) => void;
  label: string;
}) {
  return (
    <div className="hud zoom-controls" aria-label={label}>
      <button className="seg-btn icon-btn" aria-label="Zoom in" title="Zoom in"
        onClick={() => onZoom(1 / BUTTON_DOLLY_FACTOR)}>
        <Icon name="zoom-in" size={18} />
      </button>
      <button className="seg-btn icon-btn" aria-label="Zoom out" title="Zoom out"
        onClick={() => onZoom(BUTTON_DOLLY_FACTOR)}>
        <Icon name="zoom-out" size={18} />
      </button>
    </div>
  );
}

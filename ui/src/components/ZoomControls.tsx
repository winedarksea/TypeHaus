import { Icon } from "../icons/Icon";

// On-screen zoom, shared by the 2D plan and the 3D panel.
//
// The wheel is a fine zoom on a desk with a mouse, and a bad one everywhere else: a trackpad or
// tablet pinch is ambiguous — the browser may claim it as page zoom before the canvas ever sees
// it. So zoom gets a control you can point at, which no gesture arbitration can take away.
//
// `onZoom` takes a *multiplier* rather than a direction because the two panes zoom in different
// units (the 3D dolly is a radius in metres, the plan is px/m); a factor is the one thing they
// agree on. Above 1 means "further away" in both.
// One press, as a multiplier on the pane's zoom — roughly four mouse notches. Visible progress
// per tap, without a double-tap overshooting the thing you were trying to get closer to. It
// lives here rather than beside the 3D dolly clamps (three/cameraFraming.ts) because this is the
// only thing that presses it, and importing that module for one number put three.js in the entry
// chunk of a session that never opens the 3D pane.
export const BUTTON_DOLLY_FACTOR = 1.3;

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

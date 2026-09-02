// One top-most text layer for the whole floorplan.
//
// The plan is plain SVG, so paint order is literal JSX document order inside Canvas2D's one
// <svg> — there is no z-index and no sort key. A label emitted inside its own element's <g>
// therefore stacks above that one element and nothing else, which is why a room name, a window
// tag, a stair's "UP n R" or a placeable's name kept drawing *under* neighbouring furniture.
//
// The fix is a single <g> rendered last, with every label site portalling its <text> into it.
// Portalling (rather than lifting the label data up to Canvas2D) keeps every anchor where it
// is: each is computed from geometry local to its shape — the placeable label flips between
// two y's depending on whether a glyph was drawn, the window tag is offset along the wall
// normal, the room label runs its line budget against the projected clear-face extent. Only
// where the node lands in the DOM changes.
import { createContext, useContext, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

// The plan's text halo: an outline painted *under* the glyphs so a label stays readable over
// a hatch or a tinted room fill. Which one you want depends on the text's own fill:
//
//   fill var(--canvas-ink)  → PLAN_TEXT_HALO      (the canvas palette)
//   fill var(--ink)         → PLAN_INK_TEXT_HALO  (the panel palette)
//
// They are not interchangeable. `--ink` and `--canvas-white` are the SAME colour in the dark
// theme (#ECEFF4 — see styles/tokens.css), so a canvas-white halo around --ink text fattens
// every glyph into an unreadable smear. A label drawn in a theme-flipping token has to back
// onto the theme's own background, which is what DetailCanvas.tsx's TEXT_HALO does too.
export const PLAN_TEXT_HALO = {
  paintOrder: "stroke",
  stroke: "var(--canvas-white)",
  strokeWidth: 3,
} as const;

export const PLAN_INK_TEXT_HALO = {
  paintOrder: "stroke",
  stroke: "var(--bg)",
  strokeWidth: 1.5,
  strokeLinejoin: "round",
} as const;

const LabelTarget = createContext<SVGGElement | null>(null);

/** Renders `children`, then the label <g> last so every portalled label paints on top. */
export function PlanLabelLayer({ children }: { children: ReactNode }) {
  // useState, not a ref: mounting the <g> has to trigger the one re-render that lets the
  // descendants below find a target to portal into.
  const [node, setNode] = useState<SVGGElement | null>(null);
  return (
    <LabelTarget.Provider value={node}>
      {children}
      {/* Non-interactive: were a label part of its own group's hit area, a cursor resting on
          the text alone could drive a hover/no-hover oscillation. */}
      <g className="plan-label-layer" ref={setNode} pointerEvents="none" />
    </LabelTarget.Provider>
  );
}

/**
 * Hoists its children into the plan's label layer. Falls back to rendering in place when
 * there is no layer — the first render before the <g> mounts, and any use outside a
 * PlanLabelLayer (SSR, the module loads in scripts/run-geometry-tests.mjs).
 */
export function PlanLabel({ children }: { children: ReactNode }) {
  const node = useContext(LabelTarget);
  return node ? createPortal(children, node) : <>{children}</>;
}

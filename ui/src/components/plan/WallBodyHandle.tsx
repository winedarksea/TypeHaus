// Transparent grab strip along the selected wall's axis (P5 wall-body drag). Mirrors
// NodeHandle: pointer capture, rAF-coalesced moves. Spans skip hosted openings so a tap on a
// door or window still selects it.
import { useRef } from "react";
import type { Vec2 } from "../../model/types";

const GRAB_STROKE_PX = 14;

export function WallBodyHandle({ axis, spans, project, onStart, onMove, onEnd }: {
  axis: [Vec2, Vec2];
  spans: [number, number][];
  project: (p: Vec2) => Vec2;
  onStart: (clientX: number, clientY: number) => void;
  onMove: (clientX: number, clientY: number) => void;
  onEnd: () => void;
}) {
  const dragging = useRef(false);
  const raf = useRef<number | null>(null);
  const [a, b] = axis;
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
  const at = (s: number): Vec2 => project([a[0] + (b[0] - a[0]) * s / len, a[1] + (b[1] - a[1]) * s / len]);
  return (
    <g style={{ cursor: "move" }}
      onPointerDown={(e) => {
        e.stopPropagation();
        (e.currentTarget as Element).setPointerCapture(e.pointerId);
        dragging.current = true;
        onStart(e.clientX, e.clientY);
      }}
      onPointerMove={(e) => {
        if (!dragging.current) return;
        e.stopPropagation();
        const { clientX, clientY } = e;
        if (raf.current == null) {
          raf.current = requestAnimationFrame(() => { raf.current = null; onMove(clientX, clientY); });
        }
      }}
      onPointerUp={(e) => {
        if (!dragging.current) return;
        e.stopPropagation();
        dragging.current = false;
        if (raf.current != null) { cancelAnimationFrame(raf.current); raf.current = null; }
        onEnd();
      }}
    >
      {spans.map(([s0, s1], i) => {
        const [x1, y1] = at(s0);
        const [x2, y2] = at(s1);
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="transparent"
          strokeWidth={GRAB_STROKE_PX} strokeLinecap="butt" />;
      })}
      <title>Drag to move wall</title>
    </g>
  );
}

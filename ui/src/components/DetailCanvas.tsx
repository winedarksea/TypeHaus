import { useMemo, useRef, useState } from "react";
import type { DetailPayload } from "../engine/EngineClient";

// Client-side renderer for a transition-detail scene (→ 11b). The engine ships scene JSON
// (emit/draw/scene.py) — not opaque SVG — so every node is hit-testable here, the read-only
// v1 viewer and the future permit-ready editor sharing one contract. Six drawable node kinds
// map to SVG DOM; each carries its `data-uid` for the (later) hit-test → PatchOp editor hook.
//
// Scene coordinates are model-space inches with z up; SVG y grows downward, so we flip y.

type Pt = [number, number];
type Node = Record<string, any>;

// Feet-inches formatter, ported from pdf_writer._feet_inches (one dimension convention).
function feetInches(totalIn: number): string {
  const total = Math.round(totalIn);
  return `${Math.trunc(total / 12)}'-${Math.abs(total % 12)}"`;
}

// Hatch fills as inline SVG patterns (batt/rigid/concrete/lumber/osb/spray-foam/SOLID).
const HATCH_DEFS: Record<string, JSX.Element> = {
  batt: (
    <pattern id="h-batt" width="6" height="6" patternUnits="userSpaceOnUse">
      <path d="M0 3 Q1.5 0 3 3 T6 3" fill="none" stroke="var(--detail-batt)" strokeWidth="0.4" />
    </pattern>
  ),
  rigid: (
    <pattern id="h-rigid" width="5" height="5" patternUnits="userSpaceOnUse">
      <rect width="5" height="5" fill="none" />
      <path d="M0 5 L5 0" stroke="var(--detail-rigid)" strokeWidth="0.4" />
    </pattern>
  ),
  osb: (
    <pattern id="h-osb" width="4" height="4" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="0.4" fill="var(--detail-osb)" />
      <circle cx="3" cy="3" r="0.4" fill="var(--detail-osb)" />
    </pattern>
  ),
  lumber: (
    <pattern id="h-lumber" width="6" height="6" patternUnits="userSpaceOnUse">
      <path d="M0 0 L6 6" stroke="var(--detail-lumber)" strokeWidth="0.4" />
    </pattern>
  ),
  concrete: (
    <pattern id="h-concrete" width="7" height="7" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="0.5" fill="var(--detail-concrete)" />
      <path d="M4 5 L6 5" stroke="var(--detail-concrete)" strokeWidth="0.4" />
    </pattern>
  ),
  "spray-foam": (
    <pattern id="h-spray-foam" width="5" height="5" patternUnits="userSpaceOnUse">
      <rect width="5" height="5" fill="var(--detail-foam)" />
      <circle cx="2.5" cy="2.5" r="0.9" fill="var(--detail-foam-dot)" />
    </pattern>
  ),
};

function hatchFill(pattern: string): string {
  if (pattern === "SOLID") return "var(--material-concrete)";
  return HATCH_DEFS[pattern] ? `url(#h-${pattern})` : "none";
}

// Per-material fill for cut layers — must match the engine's palette.detail_fill so the
// app and the rendered PNG/PDF of the same detail agree. A pattern alone cannot tell
// concrete, XPS, EPS and polyiso apart; the fill underneath the hatch is what does.
const DETAIL_FILL: Record<string, string> = {
  concrete: "#bfbfbf", spf: "#c8a26a", lsl: "#bb955c",
  osb: "#d9c8a0", "struct-1-plywood": "#d9c8a0", "plywood-subfloor": "#d9c8a0",
  "zip-r": "#3f6d3a", gwb: "#e6e6e6",
  polyiso: "#f4e6b1", "polyiso-foil": "#efdf9e",
  eps: "#c8e0f8", "icf-eps": "#d8e8fa", xps: "#a7d7c5",
  "mineral-wool": "#a8a8a8", fiberglass: "#ddecc8",
  "air-barrier": "#1e3a5f", "standing-seam": "#2f2f2f", "fiber-cement": "#e6e6e6",
  "cedar-tg": "#c8a26a", "sauna-tg": "#e6d4ae", "resilient-channel": "#91979d",
  aggregate: "#7f7f7f", "river-rock": "#a9a9a9", soil: "#d2b48c",
  "spray-foam": "#ffd966", sealant: "#6e4f2a", flashing: "#7a0c0c",
  metal: "#ffffff", "metal-dark": "#2f2f2f", rubber: "#3a3a3a",
  glass: "#bee3f8", gutter: "#8b8b8b",
};

function materialFill(material: string | null | undefined): string | null {
  return (material && DETAIL_FILL[material]) || null;
}

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

function scenePoints(node: Node): Pt[] {
  if (Array.isArray(node.points)) return node.points as Pt[];
  if (Array.isArray(node.boundary)) return node.boundary as Pt[];
  if (Array.isArray(node.anchor)) return [node.anchor as Pt];
  if (Array.isArray(node.insert)) return [node.insert as Pt];
  const pts: Pt[] = [];
  for (const key of ["at", "to", "p0", "p1"]) if (Array.isArray(node[key])) pts.push(node[key] as Pt);
  return pts;
}

function computeBounds(nodes: Node[]): Bounds {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    for (const [x, y] of scenePoints(n)) {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
  }
  if (!isFinite(minX)) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
  return { minX, minY, maxX, maxY };
}

// Flip y (z up in model → y down in SVG) around the scene's max-y.
const fy = (y: number, b: Bounds) => b.maxY + b.minY - y;

export function DetailCanvas({
  payload,
  onPickUid,
}: {
  payload: DetailPayload;
  onPickUid?: (uid: string | null) => void;
}) {
  const nodes = (payload.scene.nodes ?? []) as Node[];
  const bounds = useMemo(() => computeBounds(nodes), [nodes]);
  const pad = Math.max(6, (bounds.maxX - bounds.minX) * 0.08);
  const vb = {
    x: bounds.minX - pad,
    y: bounds.minY - pad,
    w: bounds.maxX - bounds.minX + 2 * pad,
    h: bounds.maxY - bounds.minY + 2 * pad,
  };

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Pt>([0, 0]);
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.min(8, Math.max(0.3, z * (e.deltaY < 0 ? 1.1 : 0.9))));
  };
  const onDown = (e: React.MouseEvent) => {
    drag.current = { x: e.clientX, y: e.clientY, px: pan[0], py: pan[1] };
  };
  const onMove = (e: React.MouseEvent) => {
    if (!drag.current) return;
    setPan([
      drag.current.px + (e.clientX - drag.current.x),
      drag.current.py + (e.clientY - drag.current.y),
    ]);
  };
  const onUp = () => {
    drag.current = null;
  };

  return (
    <svg
      viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
      style={{ width: "100%", height: "100%", background: "var(--panel)", cursor: "grab" }}
      onWheel={onWheel}
      onMouseDown={onDown}
      onMouseMove={onMove}
      onMouseUp={onUp}
      onMouseLeave={onUp}
    >
      <defs>{Object.values(HATCH_DEFS)}</defs>
      <g transform={`translate(${pan[0]} ${pan[1]}) scale(${zoom})`}>
        {nodes.map((n, i) => (
          <SceneNode key={i} node={n} bounds={bounds} onPickUid={onPickUid} />
        ))}
      </g>
    </svg>
  );
}

function SceneNode({
  node,
  bounds,
  onPickUid,
}: {
  node: Node;
  bounds: Bounds;
  onPickUid?: (uid: string | null) => void;
}) {
  const uid = (node.uid as string | undefined) ?? undefined;
  const pick = uid && onPickUid ? () => onPickUid(uid) : undefined;
  const dataUid = uid ? { "data-uid": uid } : {};

  switch (node.node) {
    case "polyline": {
      const pts = (node.points as Pt[]).map(([x, y]) => `${x},${fy(y, bounds)}`).join(" ");
      const stroke = "var(--detail-ink)";
      const sw = (node.lineweight as number) ?? 0.25;
      return node.closed ? (
        <polygon points={pts} fill="none" stroke={stroke} strokeWidth={sw} {...dataUid} />
      ) : (
        <polyline points={pts} fill="none" stroke={stroke} strokeWidth={sw} {...dataUid} />
      );
    }
    case "hatch": {
      const pts = (node.boundary as Pt[]).map(([x, y]) => `${x},${fy(y, bounds)}`).join(" ");
      const base = materialFill(node.material as string | undefined);
      return (
        <>
          {base && <polygon points={pts} fill={base} stroke="none" />}
          <polygon
            points={pts}
            fill={hatchFill(node.pattern as string)}
            stroke="none"
            onClick={pick}
            style={pick ? { cursor: "pointer" } : undefined}
            {...dataUid}
          />
        </>
      );
    }
    case "text": {
      const [x, y] = node.anchor as Pt;
      const anchor = node.align === "center" ? "middle" : node.align === "right" ? "end" : "start";
      return (
        <text
          x={x}
          y={fy(y, bounds)}
          fontSize={(node.height as number) ?? 3}
          textAnchor={anchor}
          transform={node.rotation ? `rotate(${-node.rotation} ${x} ${fy(y, bounds)})` : undefined}
          fill="var(--detail-ink)"
          onClick={pick}
          style={pick ? { cursor: "pointer" } : undefined}
          {...dataUid}
        >
          {node.content as string}
        </text>
      );
    }
    case "leader": {
      const [ax, ay] = node.at as Pt;
      const [tx, ty] = node.to as Pt;
      return (
        <g onClick={pick} style={pick ? { cursor: "pointer" } : undefined} {...dataUid}>
          <line x1={ax} y1={fy(ay, bounds)} x2={tx} y2={fy(ty, bounds)} stroke="var(--detail-line)" strokeWidth={0.3} />
          <circle cx={tx} cy={fy(ty, bounds)} r={0.8} fill="var(--detail-line)" />
          <text x={ax + 1} y={fy(ay, bounds)} fontSize={3} fill="var(--detail-ink)">
            {node.text as string}
          </text>
        </g>
      );
    }
    case "dimension": {
      const [x0, y0] = node.p0 as Pt;
      const [x1, y1] = node.p1 as Pt;
      const label = (node.text as string) ?? feetInches(Math.hypot(x1 - x0, y1 - y0));
      const mx = (x0 + x1) / 2;
      const my = fy((y0 + y1) / 2, bounds);
      return (
        <g {...dataUid}>
          <line x1={x0} y1={fy(y0, bounds)} x2={x1} y2={fy(y1, bounds)} stroke="var(--detail-muted)" strokeWidth={0.3} />
          <text x={mx} y={my - 1} fontSize={3} textAnchor="middle" fill="var(--detail-ink)">
            {label}
          </text>
        </g>
      );
    }
    case "symbol": {
      const [x, y] = node.insert as Pt;
      return <circle cx={x} cy={fy(y, bounds)} r={2} fill="none" stroke="var(--detail-symbol)" strokeWidth={0.3} {...dataUid} />;
    }
    default:
      return null;
  }
}

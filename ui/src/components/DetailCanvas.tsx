import { useLayoutEffect, useMemo, useRef, useState } from "react";
import type { DetailAnnotationSpec, DetailPayload } from "../engine/EngineClient";

// Client-side renderer for a transition-detail scene (→ 11b). The engine ships scene JSON
// (emit/draw/scene.py) — not opaque SVG — so every node is hit-testable here, the read-only
// v1 viewer and the future permit-ready editor sharing one contract. Six drawable node kinds
// map to SVG DOM; each carries its `data-uid` for the hit-test → PatchOp editor hook.
//
// Scene coordinates are model-space inches with z up; SVG y grows downward, so we flip y.
//
// Editing (U10): an authored DetailAnnotation node can be dragged. The drag delta is measured
// in the scene's own inch frame (via the group's inverse screen-CTM), added to the annotation's
// existing anchor-relative offset, and committed as a single-field `offset` PatchOp — so the
// stored value stays relative to the resolved anchor and rides it when geometry changes, never
// an absolute pixel position.

type Pt = [number, number];
type Node = Record<string, any>;

// Model inches per metre — must match emit/draw/details.py M_TO_IN so a committed offset
// (authored in metres) lands exactly where it was dragged.
export const M_TO_IN = 39.37007874015748;

// A drag delta in the group's local (SVG-user) frame — x grows right, y grows *down* — added
// to an annotation's existing anchor-relative offset (metres) → the new offset (metres). The
// scene z axis grows up while local y grows down, hence the sign flip on the second component.
export function draggedOffsetMeters(
  base: Pt,
  dxLocal: number,
  dyLocal: number,
): Pt {
  return [base[0] + dxLocal / M_TO_IN, base[1] - dyLocal / M_TO_IN];
}

// Feet-inches formatter, ported from pdf_writer._feet_inches (one dimension convention).
function feetInches(totalIn: number): string {
  const total = Math.round(totalIn);
  return `${Math.trunc(total / 12)}'-${Math.abs(total % 12)}"`;
}

// Which way a leader's note text runs: away from the thing it points at (mirror of
// pdf_writer._leader_align). A note left of its target must grow leftward or the lettering
// runs back across the leader line into the drawing — the layer-label ladder smear.
export function leaderTextAlign(at: Pt, to: Pt): "start" | "end" {
  return at[0] < to[0] ? "end" : "start";
}

// Text metrics live in ./detailTypography, which the engine's typography.py is checked
// against by test_typography_parity.py. Re-exported here so existing imports resolve.
import {
  CHAR_ASPECT,
  DIM_TEXT_H,
  DIM_TEXT_PT,
  LEADER_TEXT_H,
  modelInPerPt,
} from "./detailTypography";
import type { DetailFrame } from "../engine/EngineClient";
export { CHAR_ASPECT, DIM_TEXT_H, LEADER_TEXT_H };

// Halo behind annotation lettering so it stays legible over hatch fills — the SVG analogue
// of the raster writer's translucent white bbox. Paint-order strokes the page colour behind
// the glyphs, so it tracks the light/dark theme for free.
const TEXT_HALO = {
  stroke: "var(--bg)",
  strokeWidth: 1.1,
  strokeLinejoin: "round" as const,
  paintOrder: "stroke" as const,
};

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
  // Paler than the covered subfloor sheet: catlin's attic deck is the sanded-face
  // underlayment grade because two unfinished lofts walk on it bare, and the detail is
  // where that shows. Mirrors emit/draw/palette.py DETAIL_FILL.
  "plywood-underlayment-sanded": "#e7d8b4",
  "zip-r": "#3f6d3a", gwb: "#e6e6e6",
  polyiso: "#f4e6b1", "polyiso-foil": "#efdf9e",
  eps: "#c8e0f8", "icf-eps": "#d8e8fa", xps: "#a7d7c5",
  "mineral-wool": "#a8a8a8", fiberglass: "#ddecc8",
  "air-barrier": "#1e3a5f", "standing-seam": "#2f2f2f",
  // Same detail ink for all five metal skins — the section drawing shows metal, and
  // snap-lock, nail strip, 26 ga nail strip and the exposed-fastener PBR panel all draw
  // identically to a mechanically seamed pan. Mirrors emit/draw/palette.py DETAIL_FILL.
  "standing-seam-snaplock": "#2f2f2f", "standing-seam-nailstrip": "#2f2f2f",
  "standing-seam-nailstrip-26": "#2f2f2f", "pbr-panel-26": "#2f2f2f",
  // Six metal skins now: the north/south board & batten panel (2026-08-31) draws the same
  // detail ink again. Mirrors emit/draw/palette.py DETAIL_FILL — test_detail_fill_parity.py
  // fails if this table and that one disagree.
  "board-batten-24": "#2f2f2f",
  "fiber-cement": "#e6e6e6",
  "cedar-tg": "#c8a26a", "sauna-shiplap": "#e6d4ae", "resilient-channel": "#91979d",
  aggregate: "#7f7f7f", "river-rock": "#a9a9a9", soil: "#d2b48c",
  "spray-foam": "#ffd966", sealant: "#6e4f2a", flashing: "#7a0c0c",
  metal: "#ffffff", "metal-dark": "#2f2f2f", rubber: "#3a3a3a",
  glass: "#bee3f8", gutter: "#8b8b8b",
  // The house's one exterior dark: the roof edge trim, the eave water chain (drip edge,
  // box gutter, downspouts) and the guards all name it. With no entry it fell through to
  // the near-white fallback and the box gutter drew as a pale ghost beside the apron
  // flashing it laps. Same ink as the five metal skins above, for the reason stated there.
  "metal-dark-exterior": "#2f2f2f",
  // Pressure-treated: the catlin truss wall's outer girts and its block-2 course are KDAT,
  // and with no entry every one of them drew as a blank box — the wet-cycling half of a
  // wall whose whole point is which stick is treated. Greener and greyer than `spf` so the
  // two woods are told apart. Mirrors emit/draw/palette.py DETAIL_FILL.
  kdat: "#b7ad7a",
  // The roof stack, which is the eave detail's whole subject and drew as four near-white
  // boxes in the app. The two membranes are DELIBERATELY different inks: the deck vapour
  // barrier is vapour-TIGHT and the field underlayment must stay vapour-OPEN, and a detail
  // that showed them alike would hide the one substitution that breaks this roof.
  "zip-sheathing": "#3f6d3a", "roof-deck-vapor-barrier": "#1e3a5f",
  "roof-underlayment-synthetic": "#8f8578", "roof-vent-mat": "#dfe6ea",
  "fiberglass-r19": "#ddecc8", "blown-fiberglass": "#e7f2d8",
  polyethylene: "#3f4246", "composite-deck": "#8a7f70",
  "aluminum-extrusion": "#b6bac0", "polycarbonate-multiwall": "#cfe3e8",
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


// A node's lettering height in *scene units* (model inches). `height_pt` wins when set —
// the annotative rule from emit/draw/scene.py — and is converted through the frame's scale.
// Without a frame there is nothing to convert through, so the model-space `height` stands,
// which is exactly what every drawing did before paper space.
export function textHeight(node: Node, frame?: DetailFrame | null): number {
  const isText = node.node === "text";
  const pt = node.height_pt as number | null | undefined;
  if (pt != null && frame) return pt * modelInPerPt(frame.scale);
  return (node.height as number) ?? (isText ? 3 : LEADER_TEXT_H);
}

// Estimated bbox of a text/leader node's lettering. Used to keep a callout column on screen
// when the panel frames a frameless scene — never to size the *drawing*, which is
// computeBounds' rule below.
export function textExtents(node: Node): { xs: [number, number]; ys: [number, number] } | null {
  const isText = node.node === "text";
  const isLeader = node.node === "leader";
  if (!isText && !isLeader) return null;
  const content = (isText ? node.content : node.text) as string | undefined;
  const anchor = (isText ? node.anchor : node.at) as Pt | undefined;
  if (!content || !Array.isArray(anchor)) return null;
  const height = (node.height as number) ?? (isText ? 3 : LEADER_TEXT_H);
  const lines = content.split("\n");
  const width = Math.max(...lines.map((l) => l.length)) * height * CHAR_ASPECT;
  const align = isLeader
    ? (leaderTextAlign(node.at as Pt, node.to as Pt) === "end" ? "right" : "left")
    : ((node.align as string) ?? "left");
  const x0 = align === "right" ? anchor[0] - width
    : align === "center" ? anchor[0] - width / 2 : anchor[0];
  return {
    xs: [x0, x0 + width],
    ys: [anchor[1] - height * lines.length, anchor[1] + height * lines.length],
  };
}

// The drawing's bbox: points and boundaries, nothing else — the mirror of
// pdf_writer.geometry_bounds. **Text never enters it.** A bbox that grew on lettering makes
// the drawing's scale a function of how much prose is attached to it, and the same rule has
// to hold in the viewer or the panel and the print disagree about what the detail is.
export function computeBounds(nodes: Node[]): Bounds {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  const grow = (x: number, y: number) => {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  };
  for (const n of nodes) {
    if ((n.space as string | undefined) === "paper") continue;
    // Points and boundaries only — exactly pdf_writer.geometry_bounds. A leader's `to` and a
    // dimension's `p0`/`p1` are on the geometry, but they are *annotation*, and letting them
    // vote reopens the loop this rule closes.
    const pts = (n.points ?? n.boundary) as Pt[] | undefined;
    if (!Array.isArray(pts)) continue;
    for (const [x, y] of pts) grow(x, y);
  }
  if (!isFinite(minX)) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
  return { minX, minY, maxX, maxY };
}

// Flip y (z up in model → y down in SVG) around the scene's max-y.
const fy = (y: number, b: Bounds) => b.maxY + b.minY - y;

// One draggable annotation: its authored tag + current anchor-relative offset (metres).
interface Editable {
  tag: string;
  base: Pt;
}

// A live local-frame (SVG-user) translate applied to a node while/after a drag.
type DragDelta = { dx: number; dy: number };

function editableMap(annotations: DetailAnnotationSpec[]): Map<string, Editable> {
  const out = new Map<string, Editable>();
  for (const a of annotations) {
    // Only authored annotations carry a minted uid + tag; seed nodes (uid=null) stay read-only.
    if (a.uid && a.tag) out.set(a.uid, { tag: a.tag, base: a.offset ?? [0, 0] });
  }
  return out;
}

export function DetailCanvas({
  payload,
  onPickUid,
  onMoveAnnotation,
}: {
  payload: DetailPayload;
  onPickUid?: (uid: string | null) => void;
  // Commit an anchor-relative offset edit; resolves true on a persisted PatchOp, false if the
  // write was rejected (revision conflict / error) so the optimistic drag can snap back.
  onMoveAnnotation?: (tag: string, offsetMeters: Pt) => Promise<boolean>;
}) {
  const allNodes = (payload.scene.nodes ?? []) as Node[];
  const frame = payload.scene.frame ?? null;
  // Paper nodes render in their own <g> *outside* the pan/zoom group, so the title block and
  // legend hold still while the drawing zooms — which is both what paper space means and
  // better to use than chrome that slides off the panel at 3x.
  const nodes = useMemo(
    () => allNodes.filter((n) => (n.space as string | undefined) !== "paper"), [allNodes]);
  const paperNodes = useMemo(
    () => allNodes.filter((n) => (n.space as string | undefined) === "paper"), [allNodes]);
  const bounds = useMemo(() => computeBounds(nodes), [nodes]);
  const editable = useMemo(() => editableMap(payload.annotations), [payload.annotations]);
  const pad = Math.max(6, (bounds.maxX - bounds.minX) * 0.08);
  const vb = {
    x: bounds.minX - pad,
    y: bounds.minY - pad,
    w: bounds.maxX - bounds.minX + 2 * pad,
    h: bounds.maxY - bounds.minY + 2 * pad,
  };

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Pt>([0, 0]);
  const pans = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const gRef = useRef<SVGGElement | null>(null);

  // Annotation-drag state. The ref drives the commit math (no stale closures); `live` mirrors
  // it into render, and `committed` holds a node in its dragged position across the async commit
  // + payload refetch, so it never snaps back to the anchor and then jump to the saved offset.
  const annoDrag = useRef<
    { uid: string; tag: string; base: Pt; startLocal: Pt; startClient: Pt; last: DragDelta } | null
  >(null);
  const [live, setLive] = useState<{ uid: string; delta: DragDelta } | null>(null);
  const [committed, setCommitted] = useState<Record<string, DragDelta>>({});

  // A fresh payload (post-commit refetch, or a different detail) carries the authoritative
  // offsets, so any optimistic local deltas are done. Clear them *before* paint so the frame
  // that first shows the persisted offset never also carries the now-stale drag delta.
  useLayoutEffect(() => {
    annoDrag.current = null;
    setLive(null);
    setCommitted({});
  }, [payload]);

  // Map a client point into the group's local (SVG-user) frame, where the scene is drawn.
  const clientToLocal = (clientX: number, clientY: number): Pt | null => {
    const g = gRef.current;
    const ctm = g?.getScreenCTM();
    if (!g || !ctm) return null;
    const svg = g.ownerSVGElement;
    if (!svg) return null;
    const p = svg.createSVGPoint();
    p.x = clientX;
    p.y = clientY;
    const local = p.matrixTransform(ctm.inverse());
    return [local.x, local.y];
  };

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.min(8, Math.max(0.3, z * (e.deltaY < 0 ? 1.1 : 0.9))));
  };

  const onAnnotationDown = (uid: string, ed: Editable, e: React.MouseEvent) => {
    // Claim the event so the background pan handler doesn't also fire.
    e.stopPropagation();
    const start = clientToLocal(e.clientX, e.clientY);
    if (!start) return;
    annoDrag.current = {
      uid, tag: ed.tag, base: ed.base, startLocal: start,
      startClient: [e.clientX, e.clientY], last: { dx: 0, dy: 0 },
    };
    setLive({ uid, delta: { dx: 0, dy: 0 } });
  };

  const onDown = (e: React.MouseEvent) => {
    pans.current = { x: e.clientX, y: e.clientY, px: pan[0], py: pan[1] };
  };

  const onMove = (e: React.MouseEvent) => {
    const ad = annoDrag.current;
    if (ad) {
      const cur = clientToLocal(e.clientX, e.clientY);
      if (!cur) return;
      const delta = { dx: cur[0] - ad.startLocal[0], dy: cur[1] - ad.startLocal[1] };
      ad.last = delta;
      setLive({ uid: ad.uid, delta });
      return;
    }
    if (!pans.current) return;
    setPan([
      pans.current.px + (e.clientX - pans.current.x),
      pans.current.py + (e.clientY - pans.current.y),
    ]);
  };

  const endAnnotationDrag = (e: React.MouseEvent) => {
    const ad = annoDrag.current;
    if (!ad) return false;
    annoDrag.current = null;
    setLive(null);
    // A negligible move is a click, not a drag — don't churn a no-op PatchOp.
    const moved = Math.hypot(e.clientX - ad.startClient[0], e.clientY - ad.startClient[1]);
    if (moved < 3) return true;
    const { uid, tag, base, last } = ad;
    setCommitted((c) => ({ ...c, [uid]: last }));
    const offset = draggedOffsetMeters(base, last.dx, last.dy);
    void onMoveAnnotation?.(tag, offset).then((ok) => {
      if (!ok) setCommitted((c) => { const n = { ...c }; delete n[uid]; return n; });
    });
    return true;
  };

  const onUp = (e: React.MouseEvent) => {
    if (endAnnotationDrag(e)) return;
    pans.current = null;
  };

  const onLeave = (e: React.MouseEvent) => {
    endAnnotationDrag(e);
    pans.current = null;
  };

  const dragging = live !== null;
  return (
    <svg
      viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
      style={{ width: "100%", height: "100%", background: "var(--panel)", cursor: dragging ? "grabbing" : "grab" }}
      onWheel={onWheel}
      onMouseDown={onDown}
      onMouseMove={onMove}
      onMouseUp={onUp}
      onMouseLeave={onLeave}
    >
      <defs>
        {Object.values(HATCH_DEFS)}
        {/* Sized in scene units (model inches) so the head stays proportionate to the
            drawing at any zoom, like every other stroke in the scene. */}
        <marker
          id="leader-arrow"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth={3}
          markerHeight={3}
          orient="auto"
          markerUnits="userSpaceOnUse"
        >
          <path d="M0 0 L10 5 L0 10 z" fill="var(--detail-ink)" />
        </marker>
      </defs>
      <g ref={gRef} transform={`translate(${pan[0]} ${pan[1]}) scale(${zoom})`}>
        {nodes.map((n, i) => {
          const uid = n.uid as string | undefined;
          const ed = uid ? editable.get(uid) : undefined;
          const delta = uid && live?.uid === uid ? live.delta : uid ? committed[uid] : undefined;
          return (
            <SceneNode
              key={i}
              node={n}
              bounds={bounds}
              frame={frame}
              onPickUid={onPickUid}
              editable={ed}
              drag={delta ?? null}
              onAnnotationDown={onMoveAnnotation ? onAnnotationDown : undefined}
            />
          );
        })}
      </g>
      {paperNodes.length > 0 && frame ? (
        <g>
          {paperNodes.map((n, i) => (
            <SceneNode key={`paper-${i}`} node={n} bounds={paperBounds(frame)} frame={frame} />
          ))}
        </g>
      ) : null}
    </svg>
  );
}

// Paper-space nodes are in paper inches from the sheet's lower-left; `fy` flips them the same
// way it flips the model, so the bounds handed to it are the sheet itself.
function paperBounds(frame: DetailFrame): Bounds {
  return { minX: 0, minY: 0, maxX: frame.paper[0], maxY: frame.paper[1] };
}

// Render possibly-multi-line content inside an <text>: SVG has no automatic line breaking,
// so each "\n"-separated line becomes a <tspan> re-anchored at x and stepped down one line.
function TextLines({ content, x, lineHeight }: { content: string; x: number; lineHeight: number }) {
  const lines = content.split("\n");
  if (lines.length === 1) return <>{content}</>;
  return (
    <>
      {lines.map((line, i) => (
        <tspan key={i} x={x} dy={i === 0 ? 0 : lineHeight}>
          {line}
        </tspan>
      ))}
    </>
  );
}

function SceneNode({
  node,
  bounds,
  frame,
  onPickUid,
  editable,
  drag,
  onAnnotationDown,
}: {
  node: Node;
  bounds: Bounds;
  frame?: DetailFrame | null;
  onPickUid?: (uid: string | null) => void;
  editable?: Editable;
  drag?: DragDelta | null;
  onAnnotationDown?: (uid: string, ed: Editable, e: React.MouseEvent) => void;
}) {
  const uid = (node.uid as string | undefined) ?? undefined;
  const pick = uid && onPickUid ? () => onPickUid(uid) : undefined;
  const dataUid = uid ? { "data-uid": uid } : {};
  // A node is draggable only when it is an authored annotation and the viewer wired a commit.
  const canDrag = !!(uid && editable && onAnnotationDown);
  const down = canDrag
    ? (e: React.MouseEvent) => onAnnotationDown!(uid!, editable!, e)
    : undefined;
  const dx = drag?.dx ?? 0;
  const dy = drag?.dy ?? 0;

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
      const xS = x + dx;
      const yS = fy(y, bounds) + dy;
      const anchor = node.align === "center" ? "middle" : node.align === "right" ? "end" : "start";
      const h = textHeight(node, frame);
      return (
        <text
          x={xS}
          y={yS}
          fontSize={h}
          textAnchor={anchor}
          dominantBaseline="middle"
          transform={node.rotation ? `rotate(${-node.rotation} ${xS} ${yS})` : undefined}
          fill="var(--detail-ink)"
          onMouseDown={down}
          onClick={pick}
          style={canDrag ? { cursor: "move" } : pick ? { cursor: "pointer" } : undefined}
          {...TEXT_HALO}
          {...dataUid}
        >
          <TextLines content={node.content as string} x={xS} lineHeight={h * 1.2} />
        </text>
      );
    }
    case "leader": {
      const [ax, ay] = node.at as Pt;
      const [tx, ty] = node.to as Pt;
      // The offset positions the label end (`at`); the pointer tip (`to`) stays on the anchor,
      // so a drag moves only the label while the leader keeps pointing at the same geometry.
      const axS = ax + dx;
      const ayS = fy(ay, bounds) + dy;
      const txS = tx;
      const tyS = fy(ty, bounds);
      const lh = textHeight(node, frame);
      const tx0 = axS + (leaderTextAlign(node.at as Pt, node.to as Pt) === "end" ? -1 : 1);
      return (
        <g onMouseDown={down} onClick={pick}
          style={canDrag ? { cursor: "move" } : pick ? { cursor: "pointer" } : undefined} {...dataUid}>
          <line x1={axS} y1={ayS} x2={txS} y2={tyS} stroke="var(--detail-ink)"
            strokeWidth={0.5} markerEnd="url(#leader-arrow)" />
          <text
            x={tx0}
            y={ayS}
            fontSize={lh}
            textAnchor={leaderTextAlign(node.at as Pt, node.to as Pt)}
            dominantBaseline="middle"
            fill="var(--detail-ink)"
            {...TEXT_HALO}
          >
            <TextLines content={node.text as string} x={tx0} lineHeight={lh * 1.2} />
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
          <text x={mx} y={my - 1}
            fontSize={frame ? (node.height_pt as number ?? DIM_TEXT_PT) * modelInPerPt(frame.scale) : DIM_TEXT_H}
            textAnchor="middle" fill="var(--detail-ink)" {...TEXT_HALO}>
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

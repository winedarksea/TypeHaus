import { useCallback, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Opening, Vec2, Wall } from "../model/types";
import {
  deriveNodes,
  formatFtIn,
  pointAlong,
  wallLength,
} from "../model/geometry";
import { materialColor, NORDIC_ACCENT, NORDIC_INK, NORDIC_LINE } from "../nordic/palette";
import { FtInKeypad } from "./FtInKeypad";

// The SVG floorplan editor (→ 21 §Stack: SVG editor). Renders model.json faithfully —
// framed studs + layer hatching or a schematic fill — with tap-select, pinch/drag
// pan-zoom, open-end markers from the integrity findings, and a driven-dimension edit on
// opening position that round-trips through the patch loop. Points are projected in JS
// (crisp strokes, upright text) rather than via an SVG transform.

interface Pending {
  opening: Opening;
  field: "position" | "sill_height";
  initial: string;
}

export function Canvas2D() {
  const model = useStore((s) => s.model)!;
  const view = useStore((s) => s.view);
  const setView = useStore((s) => s.setView);
  const selection = useStore((s) => s.selection);
  const select = useStore((s) => s.select);
  const hoverUid = useStore((s) => s.hoverUid);
  const setHover = useStore((s) => s.setHover);
  const showFraming = useStore((s) => s.showFraming);
  const activeStorey = useStore((s) => s.activeStorey);
  const tool = useStore((s) => s.tool);
  const applyOps = useStore((s) => s.applyOps);

  const svgRef = useRef<SVGSVGElement>(null);
  const pointers = useRef<Map<number, Vec2>>(new Map());
  const pinch = useRef<{ dist: number; scale: number } | null>(null);
  const panLast = useRef<Vec2 | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);

  // World meters → screen px. SVG y grows downward, so flip.
  const project = useCallback(
    (p: Vec2): Vec2 => [view.tx + p[0] * view.scale, view.ty - p[1] * view.scale],
    [view],
  );

  const nodes = useMemo(() => deriveNodes(model.walls), [model.walls]);
  const openEnds = useMemo(() => openEndKeys(model), [model]);

  const wallsOnStorey = model.walls.filter((w) => !activeStorey || w.storey === activeStorey);

  // ---- pan / zoom -----------------------------------------------------------
  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const rect = svgRef.current!.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const factor = Math.exp(-e.deltaY * 0.0015);
    const scale = clampScale(view.scale * factor);
    // keep cursor point stable
    const wx = (cx - view.tx) / view.scale;
    const wy = (view.ty - cy) / view.scale;
    setView({ scale, tx: cx - wx * scale, ty: cy + wy * scale });
  };

  const onPointerDown = (e: React.PointerEvent) => {
    (e.target as Element).setPointerCapture?.(e.pointerId);
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      pinch.current = { dist: Math.hypot(a[0] - b[0], a[1] - b[1]), scale: view.scale };
    } else {
      panLast.current = [e.clientX, e.clientY];
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!pointers.current.has(e.pointerId)) return;
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2 && pinch.current) {
      const [a, b] = [...pointers.current.values()];
      const dist = Math.hypot(a[0] - b[0], a[1] - b[1]);
      setView({ scale: clampScale((pinch.current.scale * dist) / pinch.current.dist) });
      return;
    }
    if (panLast.current) {
      const dx = e.clientX - panLast.current[0];
      const dy = e.clientY - panLast.current[1];
      panLast.current = [e.clientX, e.clientY];
      setView({ tx: view.tx + dx, ty: view.ty + dy });
    }
  };

  const onPointerUp = (e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    if (pointers.current.size === 0) panLast.current = null;
  };

  // ---- edits ----------------------------------------------------------------
  const editOpening = (o: Opening) => {
    setPending({ opening: o, field: "position", initial: formatFtIn(o.center_along_m) });
  };

  const commitPending = async (meters: number) => {
    if (!pending) return;
    const o = pending.opening;
    const ok = await applyOps([
      {
        op: "update",
        type: o.is_door ? "Door" : "Window",
        tag: o.tag,
        fields: { [pending.field]: formatFtIn(meters) },
      },
    ]);
    if (ok) useStore.getState().toast(`${o.tag} ${pending.field} updated`);
    setPending(null);
  };

  return (
    <>
      <svg
        ref={svgRef}
        className="canvas-svg"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <BackgroundGrid view={view} />
        {/* rooms first (tinted fills, behind walls) */}
        {model.rooms
          .filter((r) => !activeStorey || r.storey === activeStorey)
          .map((r) => (
            <polygon
              key={r.uid}
              points={r.clear_face.map(project).map((p) => p.join(",")).join(" ")}
              fill={selection.uid === r.uid ? "rgba(109,138,150,0.28)" : "rgba(109,138,150,0.12)"}
              stroke="none"
              onClick={() => select("room", r.uid)}
            />
          ))}
        {/* walls */}
        {wallsOnStorey.map((w) => (
          <WallShape
            key={w.uid}
            w={w}
            project={project}
            selected={selection.uid === w.uid}
            hovered={hoverUid === w.uid}
            showFraming={showFraming}
            onSelect={() => select("wall", w.uid)}
            onHover={(h) => setHover(h ? w.uid : null)}
          />
        ))}
        {/* openings */}
        {model.openings.map((o) => {
          const host = model.walls.find((w) => w.uid === o.host);
          if (!host || (activeStorey && host.storey !== activeStorey)) return null;
          return (
            <OpeningShape
              key={o.uid}
              o={o}
              host={host}
              project={project}
              scale={view.scale}
              selected={selection.uid === o.uid}
              onSelect={() => select("opening", o.uid)}
              onEdit={() => editOpening(o)}
            />
          );
        })}
        {/* nodes + open-end markers */}
        {[...nodes.values()].map((n) => {
          const [x, y] = project(n.p);
          const open = openEnds.has(n.id);
          return (
            <circle
              key={n.id}
              cx={x}
              cy={y}
              r={open ? 7 : 3.5}
              fill={open ? "#c0392b" : NORDIC_LINE}
              opacity={open ? 0.9 : 0.5}
            >
              {open && (
                <animate
                  attributeName="r"
                  values="6;9;6"
                  dur="1.2s"
                  repeatCount="indefinite"
                />
              )}
            </circle>
          );
        })}
        {/* dimension line for selected wall */}
        {selection.kind === "wall" &&
          (() => {
            const w = wallsOnStorey.find((x) => x.uid === selection.uid);
            if (!w) return null;
            return <WallDimension w={w} project={project} />;
          })()}
      </svg>
      {pending && (
        <FtInKeypad
          label={`${pending.opening.tag} · ${pending.field === "position" ? "position along wall" : "sill height"}`}
          initial={pending.initial}
          onCommit={(m) => void commitPending(m)}
          onCancel={() => setPending(null)}
        />
      )}
      <StoreyTabs model={model} />
      {tool !== "select" && (
        <div className="hud" style={{ left: "auto", right: 12, bottom: "auto", top: 12 }}>
          {tool} tool — tap an element; editing lands as a journaled patch.
        </div>
      )}
    </>
  );
}

function clampScale(s: number): number {
  return Math.min(2000, Math.max(8, s));
}

function BackgroundGrid({ view }: { view: { scale: number; tx: number; ty: number } }) {
  // A 1-foot grid at reasonable zoom; fades out when too dense. Pure decoration.
  const ftPx = view.scale * 0.3048;
  if (ftPx < 6) return <rect width="100%" height="100%" fill="none" />;
  const size = ftPx;
  const id = "grid";
  return (
    <>
      <defs>
        <pattern
          id={id}
          width={size}
          height={size}
          patternUnits="userSpaceOnUse"
          patternTransform={`translate(${view.tx % size},${view.ty % size})`}
        >
          <path d={`M ${size} 0 L 0 0 0 ${size}`} fill="none" stroke="#e6e1d6" strokeWidth={1} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </>
  );
}

function WallShape({
  w,
  project,
  selected,
  hovered,
  showFraming,
  onSelect,
  onHover,
}: {
  w: Wall;
  project: (p: Vec2) => Vec2;
  selected: boolean;
  hovered: boolean;
  showFraming: boolean;
  onSelect: () => void;
  onHover: (h: boolean) => void;
}) {
  const poly = (pts: Vec2[]) => pts.map(project).map((p) => p.join(",")).join(" ");
  const stroke = selected ? NORDIC_ACCENT : hovered ? NORDIC_INK : NORDIC_LINE;
  return (
    <g
      onClick={onSelect}
      onPointerEnter={() => onHover(true)}
      onPointerLeave={() => onHover(false)}
      style={{ cursor: "pointer" }}
    >
      {w.layers.map((ly, i) =>
        ly.polygon.length >= 3 ? (
          <polygon
            key={i}
            points={poly(ly.polygon)}
            fill={materialColor(ly.material)}
            stroke="rgba(0,0,0,0.18)"
            strokeWidth={0.5}
          />
        ) : null,
      )}
      {showFraming &&
        w.members.map((m) => {
          const [x0, y0] = project(m.p0);
          const [x1, y1] = project(m.p1);
          return (
            <line
              key={m.key}
              x1={x0}
              y1={y0}
              x2={x1}
              y2={y1}
              stroke="#8a6d3b"
              strokeWidth={1.5}
              opacity={0.85}
            />
          );
        })}
      {/* axis + selection outline */}
      <line
        x1={project(w.axis[0])[0]}
        y1={project(w.axis[0])[1]}
        x2={project(w.axis[1])[0]}
        y2={project(w.axis[1])[1]}
        stroke={stroke}
        strokeWidth={selected ? 2.5 : 1.5}
        strokeDasharray={w.layers.length === 0 ? "4 4" : undefined}
      />
    </g>
  );
}

function OpeningShape({
  o,
  host,
  project,
  scale,
  selected,
  onSelect,
  onEdit,
}: {
  o: Opening;
  host: Wall;
  project: (p: Vec2) => Vec2;
  scale: number;
  selected: boolean;
  onSelect: () => void;
  onEdit: () => void;
}) {
  const center = pointAlong(host, o.center_along_m);
  const [cx, cy] = project(center);
  const halfPx = (o.width_m / 2) * scale;
  const [a, b] = host.axis;
  const ang = Math.atan2(-(b[1] - a[1]), b[0] - a[0]);
  const dx = Math.cos(ang) * halfPx;
  const dy = Math.sin(ang) * halfPx;
  return (
    <g onClick={onSelect} onDoubleClick={onEdit} style={{ cursor: "pointer" }}>
      <line
        x1={cx - dx}
        y1={cy - dy}
        x2={cx + dx}
        y2={cy + dy}
        stroke={selected ? NORDIC_ACCENT : "#fff"}
        strokeWidth={selected ? 6 : 5}
      />
      <line
        x1={cx - dx}
        y1={cy - dy}
        x2={cx + dx}
        y2={cy + dy}
        stroke={o.is_door ? "#7a5230" : NORDIC_ACCENT}
        strokeWidth={2}
        strokeDasharray={o.is_door ? undefined : "3 2"}
      />
      {selected && <circle cx={cx} cy={cy} r={5} fill={NORDIC_ACCENT} />}
    </g>
  );
}

function WallDimension({ w, project }: { w: Wall; project: (p: Vec2) => Vec2 }) {
  const [a, b] = w.axis;
  const mid: Vec2 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const [mx, my] = project(mid);
  return (
    <text x={mx} y={my - 8} fill={NORDIC_INK} fontSize={12} textAnchor="middle">
      {formatFtIn(wallLength(w))}
    </text>
  );
}

function StoreyTabs({ model }: { model: Model }) {
  const activeStorey = useStore((s) => s.activeStorey);
  const setActiveStorey = useStore((s) => s.setActiveStorey);
  if (model.storeys.length <= 1) return null;
  return (
    <div className="hud" style={{ bottom: "auto", top: 12, left: 12, display: "flex", gap: 6 }}>
      {model.storeys.map((s) => (
        <button
          key={s.tag}
          className={`seg-btn${activeStorey === s.tag ? " active" : ""}`}
          onClick={() => setActiveStorey(s.tag)}
        >
          {s.tag}
        </button>
      ))}
    </div>
  );
}

// Open-end nodes: derived here to mirror the integrity checker's open-end finding when the
// server surfaces it; falls back to graph degree (a node touched by a single wall end).
function openEndKeys(model: Model): Set<string> {
  const nodes = deriveNodes(model.walls);
  const open = new Set<string>();
  for (const n of nodes.values()) if (n.walls.length < 2) open.add(n.id);
  return open;
}

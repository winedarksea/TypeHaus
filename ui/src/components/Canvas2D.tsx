import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Model, Opening, PlanNode, Underlay, Vec2, Wall } from "../model/types";
import {
  deriveNodes,
  formatFtIn,
  M_PER_FT,
  nearestWallHit,
  type Node as GeoNode,
  orthoLock,
  pointAlong,
  snapWorld,
  wallLength,
} from "../model/geometry";
import { materialColor, NORDIC_ACCENT, NORDIC_INK, NORDIC_LINE } from "../nordic/palette";
import { FtInKeypad } from "./FtInKeypad";
import { SunIndicator } from "./SunIndicator";
import { PlacementPopover } from "./PlacementPopover";

// The SVG floorplan editor (→ 21 §Stack: SVG editor). Renders model.json faithfully and
// hosts the full authoring loop: draw walls (rubber-band, node/grid snap, ortho, polyline
// chaining), stretch nodes, drive a wall's length, place openings + claim rooms, split/heal,
// and delete — every edit lands as a journaled macro/patch that round-trips through rebuild.
// Points are projected in JS (crisp strokes, upright text) rather than via an SVG transform.

interface Pending {
  opening: Opening;
  field: "position" | "sill_height";
  initial: string;
}

// A two-click wall stroke in progress; `start` is already snapped.
interface WallDraft {
  start: Vec2;
  startNode: string | null;
}

// A node being dragged (stretch). `tag` is the authored node tag the macro moves.
interface NodeDrag {
  tag: string;
  from: Vec2;
  to: Vec2;
}

// A placement popover request (opening on a wall, or a room seed) anchored at screen px.
type Placement =
  | { kind: "opening"; screen: Vec2; wall: Wall; along_m: number }
  | { kind: "room"; screen: Vec2; seed: Vec2 };

const TAP_PX = 6; // pointer travel under this on up = a tap, not a pan
const HIT_PX = 16; // wall pick tolerance in screen px

export function Canvas2D() {
  const model = useStore((s) => s.model)!;
  const view = useStore((s) => s.view);
  const setView = useStore((s) => s.setView);
  const selection = useStore((s) => s.selection);
  const select = useStore((s) => s.select);
  const selectByTag = useStore((s) => s.selectByTag);
  const hoverUid = useStore((s) => s.hoverUid);
  const setHover = useStore((s) => s.setHover);
  const showFraming = useStore((s) => s.showFraming);
  const activeStorey = useStore((s) => s.activeStorey);
  const tool = useStore((s) => s.tool);
  const applyOps = useStore((s) => s.applyOps);
  const runMacro = useStore((s) => s.runMacro);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const offline = useStore((s) => s.offline);
  const calibrateUnderlay = useStore((s) => s.calibrateUnderlay);
  const toast = useStore((s) => s.toast);

  const svgRef = useRef<SVGSVGElement>(null);
  const pointers = useRef<Map<number, Vec2>>(new Map());
  const pinch = useRef<{ dist: number; scale: number } | null>(null);
  const panLast = useRef<Vec2 | null>(null);
  const gesture = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const shift = useRef(false);
  const [pending, setPending] = useState<Pending | null>(null);
  const [draft, setDraft] = useState<WallDraft | null>(null);
  const [cursor, setCursor] = useState<Vec2 | null>(null); // world-space hover/rubber-band
  const [nodeDrag, setNodeDrag] = useState<NodeDrag | null>(null);
  const [placement, setPlacement] = useState<Placement | null>(null);
  const [dimWall, setDimWall] = useState<Wall | null>(null);
  const [drawAssembly, setDrawAssembly] = useState<string>("");
  const [activeService, setActiveService] = useState<string>("");
  const [showClearances, setShowClearances] = useState(false);
  const [calibrationPoints, setCalibrationPoints] = useState<Vec2[]>([]);
  const [calibrationDistanceFt, setCalibrationDistanceFt] = useState("24");
  const [calibrationMode, setCalibrationMode] = useState(false);

  // World meters → screen px. SVG y grows downward, so flip.
  const project = useCallback(
    (p: Vec2): Vec2 => [view.tx + p[0] * view.scale, view.ty - p[1] * view.scale],
    [view],
  );
  const unproject = useCallback(
    (clientX: number, clientY: number): Vec2 => {
      const rect = svgRef.current!.getBoundingClientRect();
      return [
        (clientX - rect.left - view.tx) / view.scale,
        (view.ty - (clientY - rect.top)) / view.scale,
      ];
    },
    [view],
  );

  const nodes = useMemo(() => deriveNodes(model.walls), [model.walls]);
  const openEnds = useMemo(() => openEndKeys(model), [model]);

  const wallsOnStorey = useMemo(
    () => model.walls.filter((w) => !activeStorey || w.storey === activeStorey),
    [model.walls, activeStorey],
  );
  // Authored nodes on the active storey → the snap/heal/stretch vocabulary (addressed by tag).
  const storeyNodes = useMemo(
    () => (model.nodes ?? []).filter((n) => !activeStorey || n.storey === activeStorey),
    [model.nodes, activeStorey],
  );
  const snapNodes = useMemo(() => {
    const m = new Map<string, GeoNode>();
    for (const n of storeyNodes) m.set(n.tag, { id: n.tag, p: [n.x_m, n.y_m], walls: [] });
    return m;
  }, [storeyNodes]);

  const defaultAssembly = useMemo(() => {
    const counts = new Map<string, number>();
    for (const w of wallsOnStorey) if (w.assembly) counts.set(w.assembly, (counts.get(w.assembly) ?? 0) + 1);
    let best = "";
    let n = -1;
    for (const [a, c] of counts) if (c > n) [best, n] = [a, c];
    return best || model.catalog?.assemblies[0]?.tag || "";
  }, [wallsOnStorey, model.catalog]);
  const wallAssembly = drawAssembly || defaultAssembly;

  const serviceOptions = useMemo(() => [...new Set((model.fixtures ?? [])
    .flatMap((fixture) => fixture.needs))].sort(), [model.fixtures]);
  const visibleFixtures = (model.fixtures ?? []).filter((fixture) =>
    (!activeStorey || fixture.storey === activeStorey) &&
    (!activeService || fixture.needs.includes(activeService)));
  const activeUnderlay = (model.underlays ?? []).find((underlay) => underlay.storey === activeStorey) ?? null;

  const tolM = 12 / view.scale;
  const gridM = view.scale * M_PER_FT >= 14 ? M_PER_FT : null;
  const fmt = (m: number) => formatFtIn(m);

  const nearestNodeTag = useCallback((p: Vec2): string | null => {
    let best: string | null = null;
    let bestD = Infinity;
    for (const n of storeyNodes) {
      const d = Math.hypot(p[0] - n.x_m, p[1] - n.y_m);
      if (d < bestD) [best, bestD] = [n.tag, d];
    }
    return best;
  }, [storeyNodes]);

  const storeyHintFile = useCallback(
    () => storeyNodes.find((n) => n.provenance)?.provenance?.file
      ?? wallsOnStorey.find((w) => w.provenance)?.provenance?.file,
    [storeyNodes, wallsOnStorey],
  );

  // ---- pan / zoom -----------------------------------------------------------
  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const rect = svgRef.current!.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const factor = Math.exp(-e.deltaY * 0.0015);
    const scale = clampScale(view.scale * factor);
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
      gesture.current = null;
    } else {
      panLast.current = [e.clientX, e.clientY];
      gesture.current = { x: e.clientX, y: e.clientY, moved: false };
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    shift.current = e.shiftKey;
    // Rubber-band / snap preview follows the bare pointer for the wall tool (desktop hover).
    if (tool === "wall") setCursor(unproject(e.clientX, e.clientY));
    if (!pointers.current.has(e.pointerId)) return;
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2 && pinch.current) {
      const [a, b] = [...pointers.current.values()];
      const dist = Math.hypot(a[0] - b[0], a[1] - b[1]);
      setView({ scale: clampScale((pinch.current.scale * dist) / pinch.current.dist) });
      return;
    }
    if (gesture.current) {
      const moved = Math.hypot(e.clientX - gesture.current.x, e.clientY - gesture.current.y);
      if (moved > TAP_PX) gesture.current.moved = true;
    }
    if (panLast.current && (!gesture.current || gesture.current.moved)) {
      const dx = e.clientX - panLast.current[0];
      const dy = e.clientY - panLast.current[1];
      panLast.current = [e.clientX, e.clientY];
      setView({ tx: view.tx + dx, ty: view.ty + dy });
    }
  };

  const onPointerUp = (e: React.PointerEvent) => {
    const wasTap = gesture.current && !gesture.current.moved;
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    if (pointers.current.size === 0) panLast.current = null;
    if (wasTap && pointers.current.size === 0) {
      handleTap(unproject(e.clientX, e.clientY));
    }
    gesture.current = null;
  };

  const onDoubleClick = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!activeUnderlay || !calibrationMode) return;
    const rect = svgRef.current!.getBoundingClientRect();
    const point: Vec2 = [(event.clientX - rect.left - view.tx) / view.scale,
      (view.ty - (event.clientY - rect.top)) / view.scale];
    setCalibrationPoints((points) => points.length >= 2 ? [point] : [...points, point]);
  };

  // ---- tool tap dispatch ----------------------------------------------------
  const handleTap = (world: Vec2) => {
    if (calibrationMode) return;
    if (placement) { setPlacement(null); return; }
    if (offline && tool !== "select") { toast("Editing needs the server (offline)", "error"); return; }
    switch (tool) {
      case "select": {
        // Element onClick handles selection; a bare-canvas tap clears it.
        select(null, null);
        break;
      }
      case "wall": {
        const snap = snapWorld(world, snapNodes, tolM, gridM);
        if (!draft) {
          setDraft({ start: snap.point, startNode: snap.nodeId });
        } else {
          const end = shift.current ? orthoLock(draft.start, snap.point) : snap.point;
          void commitWall(draft.start, end);
        }
        break;
      }
      case "opening": {
        const hit = nearestWallHit(wallsOnStorey, world);
        if (hit && hit.dist_m * view.scale < HIT_PX) {
          const [sx, sy] = project(hit.point);
          setPlacement({ kind: "opening", screen: [sx, sy], wall: hit.wall, along_m: hit.along_m });
        } else {
          toast("Tap on a wall to place an opening", "error");
        }
        break;
      }
      case "room": {
        const [sx, sy] = project(world);
        setPlacement({ kind: "room", screen: [sx, sy], seed: world });
        break;
      }
      case "dimension": {
        const hit = nearestWallHit(wallsOnStorey, world);
        if (hit && hit.dist_m * view.scale < HIT_PX) {
          select("wall", hit.wall.uid);
          setDimWall(hit.wall);
        }
        break;
      }
    }
  };

  // ---- commits --------------------------------------------------------------
  const commitWall = async (start: Vec2, end: Vec2) => {
    if (Math.hypot(end[0] - start[0], end[1] - start[1]) < 0.05) {
      toast("Wall too short", "error");
      return;
    }
    if (!activeStorey) { toast("Pick a storey first", "error"); return; }
    if (!wallAssembly) { toast("No assembly to draw with", "error"); return; }
    const res = await runMacro({
      macro: "draw_wall", storey: activeStorey,
      start: [fmt(start[0]), fmt(start[1])], end: [fmt(end[0]), fmt(end[1])],
      assembly: wallAssembly, hint_file: storeyHintFile(),
    });
    if (res) {
      const wallUid = Object.values(res.minted).find((uid) =>
        useStore.getState().model?.walls.some((w) => w.uid === uid && w.assembly === wallAssembly));
      if (wallUid) select("wall", wallUid);
      // Chain: keep drawing from this endpoint (Esc / tool switch ends the run).
      setDraft({ start: end, startNode: null });
    } else {
      setDraft(null);
    }
  };

  const commitDim = async (newLenM: number) => {
    const w = dimWall;
    setDimWall(null);
    if (!w || !activeStorey) return;
    const [a, b] = w.axis;
    const len = wallLength(w);
    if (len < 1e-6) return;
    const ux = (b[0] - a[0]) / len;
    const uy = (b[1] - a[1]) / len;
    const nb: Vec2 = [a[0] + ux * newLenM, a[1] + uy * newLenM];
    const bTag = nearestNodeTag(b);
    if (!bTag) { toast("Can't resolve the wall's end node", "error"); return; }
    const ok = await runMacro({
      macro: "move_nodes", storey: activeStorey, nodes: [bTag],
      dx: nb[0] - b[0], dy: nb[1] - b[1],
    });
    if (ok) toast(`${w.tag} → ${fmt(newLenM)}`);
  };

  const commitNodeDrag = async (drag: NodeDrag) => {
    setNodeDrag(null);
    const dx = drag.to[0] - drag.from[0];
    const dy = drag.to[1] - drag.from[1];
    if (Math.hypot(dx, dy) < 1e-4 || !activeStorey) return;
    await runMacro({ macro: "move_nodes", storey: activeStorey, nodes: [drag.tag], dx, dy });
  };

  const splitWall = async (w: Wall) => {
    if (!activeStorey) return;
    const [a, b] = w.axis;
    const mid: Vec2 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    const res = await runMacro({
      macro: "split_wall", storey: activeStorey, wall: w.tag, at: [fmt(mid[0]), fmt(mid[1])],
    });
    if (res) toast(`${w.tag} split`);
  };

  const healNode = async (tag: string) => {
    if (!activeStorey) return;
    const res = await runMacro({ macro: "heal_walls", storey: activeStorey, node: tag });
    if (res) toast("Joint healed");
  };

  // ---- keyboard: Esc cancels the in-flight gesture, Delete removes selection --
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA")) return;
      if (e.key === "Escape") {
        setDraft(null); setPlacement(null); setDimWall(null); setNodeDrag(null); setPending(null);
        if (calibrationMode) { setCalibrationMode(false); setCalibrationPoints([]); }
      } else if ((e.key === "Delete" || e.key === "Backspace") && selection.uid && !offline) {
        e.preventDefault();
        void deleteSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selection.uid, offline, deleteSelection, calibrationMode]);

  // End a wall run when leaving the wall tool.
  useEffect(() => { if (tool !== "wall") { setDraft(null); setCursor(null); } }, [tool]);

  const saveCalibration = async () => {
    if (!activeUnderlay || calibrationPoints.length !== 2) return;
    const distanceFt = Number(calibrationDistanceFt);
    const measured = Math.hypot(calibrationPoints[1][0] - calibrationPoints[0][0],
      calibrationPoints[1][1] - calibrationPoints[0][1]);
    if (!Number.isFinite(distanceFt) || distanceFt <= 0 || measured <= 0) {
      toast("Enter a positive known distance in feet", "error");
      return;
    }
    const scale = distanceFt * 0.3048 / measured;
    const [anchorX, anchorY] = calibrationPoints[0];
    const ok = await calibrateUnderlay({
      ...activeUnderlay,
      origin_x_m: anchorX - (anchorX - activeUnderlay.origin_x_m) * scale,
      origin_y_m: anchorY - (anchorY - activeUnderlay.origin_y_m) * scale,
      width_m: activeUnderlay.width_m * scale,
      height_m: activeUnderlay.height_m * scale,
    });
    if (ok) { setCalibrationPoints([]); setCalibrationMode(false); }
  };

  // ---- opening driven-dimension edit (double-click an opening) ---------------
  const editOpening = (o: Opening) => {
    setPending({ opening: o, field: "position", initial: formatFtIn(o.center_along_m) });
  };
  const commitPending = async (meters: number) => {
    if (!pending) return;
    const o = pending.opening;
    const ok = await applyOps([{
      op: "update", type: o.is_door ? "Door" : "Window", tag: o.tag,
      fields: { [pending.field]: formatFtIn(meters) },
    }]);
    if (ok) toast(`${o.tag} ${pending.field} updated`);
    setPending(null);
  };

  // Live rubber-band endpoint (snapped, ortho-locked under shift).
  const rubber = useMemo(() => {
    if (tool !== "wall" || !draft || !cursor) return null;
    const snap = snapWorld(cursor, snapNodes, tolM, gridM);
    const end = shift.current ? orthoLock(draft.start, snap.point) : snap.point;
    return { end, len: Math.hypot(end[0] - draft.start[0], end[1] - draft.start[1]) };
  }, [tool, draft, cursor, snapNodes, tolM, gridM]);

  const cursorClass = tool === "select" ? "" : "canvas-draw";

  return (
    <>
      <svg
        ref={svgRef}
        className={`canvas-svg ${cursorClass}`}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={onDoubleClick}
      >
        <BackgroundGrid view={view} />
        {(model.underlays ?? [])
          .filter((underlay) => !activeStorey || underlay.storey === activeStorey)
          .map((underlay) => {
            const [x, y] = project([underlay.origin_x_m, underlay.origin_y_m]);
            const width = underlay.width_m * view.scale;
            const height = underlay.height_m * view.scale;
            return (
              <image key={`${underlay.storey}:${underlay.path}`} href={underlay.url}
                x={x} y={y - height} width={width} height={height} opacity={underlay.opacity}
                pointerEvents="none"
                transform={`rotate(${-underlay.rotation_deg} ${x} ${y})`} />
            );
          })}
        {calibrationPoints.map((point, index) => {
          const [x, y] = project(point);
          return <g key={`calibration-${index}`} pointerEvents="none">
            <circle cx={x} cy={y} r={6} fill="#c55842" />
            <text x={x + 8} y={y - 8} fontSize={11} fill="#9a321f">{index + 1}</text>
          </g>;
        })}
        {/* rooms first (tinted fills, behind walls) */}
        {model.rooms
          .filter((r) => !activeStorey || r.storey === activeStorey)
          .map((r) => (
            <polygon
              key={r.uid}
              points={r.clear_face.map(project).map((p) => p.join(",")).join(" ")}
              fill={selection.uid === r.uid ? "rgba(109,138,150,0.28)" : "rgba(109,138,150,0.12)"}
              stroke="none"
              onClick={() => tool === "select" && select("room", r.uid)}
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
            onSelect={() => tool === "select" && select("wall", w.uid)}
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
              onSelect={() => tool === "select" && select("opening", o.uid)}
              onEdit={() => tool === "select" && editOpening(o)}
            />
          );
        })}
        {(model.fixtures ?? [])
          .filter((fixture) => !activeStorey || fixture.storey === activeStorey)
          .map((fixture) => <FixtureFootprint key={fixture.uid} fixture={fixture} project={project}
            scale={view.scale} dimmed={Boolean(activeService)} />)}
        {(model.furniture ?? [])
          .filter((furniture) => !activeStorey || furniture.storey === activeStorey)
          .map((furniture) => {
            const [x, y] = project(furniture.position);
            const width = furniture.footprint_m[0] * view.scale;
            const depth = furniture.footprint_m[1] * view.scale;
            return (
              <g key={furniture.uid} opacity={0.9} pointerEvents="none">
                <rect x={x - width / 2} y={y - depth / 2} width={width} height={depth}
                  fill="rgba(112,76,52,0.14)" stroke="#704c34" strokeWidth={1.2} />
                <text x={x} y={y + 3} textAnchor="middle" fontSize={9} fill="#553522">
                  {furniture.type.replace("FURN-", "")}
                </text>
              </g>
            );
          })}
        {showClearances && <ClearanceOverlays model={model} storey={activeStorey} project={project}
          scale={view.scale} />}
        {/* nodes + open-end markers; heal affordance on collinear 2-wall joints (select tool) */}
        {[...nodes.values()].map((n) => {
          const [x, y] = project(n.p);
          const open = openEnds.has(n.id);
          const tag = tool === "select" ? nearestNodeTag(n.p) : null;
          const healable = tool === "select" && n.walls.length === 2 && collinearAt(n, model);
          return (
            <g key={n.id}>
              <circle
                cx={x} cy={y} r={open ? 7 : healable ? 6 : 3.5}
                fill={open ? "#c0392b" : healable ? NORDIC_ACCENT : NORDIC_LINE}
                opacity={open ? 0.9 : healable ? 0.85 : 0.5}
                style={{ cursor: healable ? "pointer" : "default" }}
                onClick={healable && tag ? () => void healNode(tag) : undefined}
              >
                {open && <animate attributeName="r" values="6;9;6" dur="1.2s" repeatCount="indefinite" />}
              </circle>
              {healable && <title>Heal joint</title>}
            </g>
          );
        })}
        {/* draggable endpoint handles on the selected wall (stretch → move_nodes) */}
        {tool === "select" && selection.kind === "wall" && (() => {
          const w = wallsOnStorey.find((x) => x.uid === selection.uid);
          if (!w) return null;
          return w.axis.map((p, i) => (
            <NodeHandle
              key={i}
              world={nodeDrag && nodeTagMatches(nodeDrag.tag, p, storeyNodes) ? nodeDrag.to : p}
              project={project}
              onStart={() => {
                const tag = nearestNodeTag(p);
                if (tag) setNodeDrag({ tag, from: p, to: p });
              }}
              onMove={(clientX, clientY) => setNodeDrag((d) => d ? ({
                ...d, to: (() => {
                  const raw = unproject(clientX, clientY);
                  const others = new Map([...snapNodes].filter(([t]) => t !== d.tag));
                  return snapWorld(raw, others, tolM, gridM).point;
                })(),
              }) : d)}
              onEnd={() => setNodeDrag((d) => { if (d) void commitNodeDrag(d); return null; })}
            />
          ));
        })()}
        {/* wall draft: start marker + rubber band + live length */}
        {tool === "wall" && draft && (() => {
          const [sx, sy] = project(draft.start);
          const end = rubber?.end ?? draft.start;
          const [ex, ey] = project(end);
          const [mx, my] = [(sx + ex) / 2, (sy + ey) / 2];
          return (
            <g pointerEvents="none">
              <line x1={sx} y1={sy} x2={ex} y2={ey} stroke={NORDIC_ACCENT} strokeWidth={2}
                strokeDasharray="6 4" />
              <circle cx={sx} cy={sy} r={5} fill={NORDIC_ACCENT} />
              <circle cx={ex} cy={ey} r={5} fill="#fff" stroke={NORDIC_ACCENT} strokeWidth={2} />
              {rubber && rubber.len > 0.01 && (
                <text x={mx} y={my - 8} fill={NORDIC_INK} fontSize={12} textAnchor="middle"
                  style={{ paintOrder: "stroke" }} stroke="#fff" strokeWidth={3}>
                  {formatFtIn(rubber.len)}
                </text>
              )}
            </g>
          );
        })()}
        {/* snap indicator for the wall tool's next click */}
        {tool === "wall" && cursor && (() => {
          const snap = snapWorld(cursor, snapNodes, tolM, gridM);
          if (!snap.nodeId && !gridM) return null;
          const [x, y] = project(snap.point);
          return <circle cx={x} cy={y} r={snap.nodeId ? 7 : 4} fill="none"
            stroke={snap.nodeId ? "#c0392b" : NORDIC_ACCENT} strokeWidth={1.5} pointerEvents="none" />;
        })()}
        {/* dimension line for selected wall */}
        {selection.kind === "wall" && (() => {
          const w = wallsOnStorey.find((x) => x.uid === selection.uid);
          if (!w) return null;
          return <WallDimension w={w} project={project} />;
        })()}
        {activeService && <>
          <rect width="100%" height="100%" fill="rgba(245,243,237,0.74)" pointerEvents="none" />
          {visibleFixtures.map((fixture) => <FixtureFootprint key={`service-${fixture.uid}`}
            fixture={fixture} project={project} scale={view.scale} dimmed={false} />)}
        </>}
      </svg>
      {pending && (
        <FtInKeypad
          label={`${pending.opening.tag} · ${pending.field === "position" ? "position along wall" : "sill height"}`}
          initial={pending.initial}
          onCommit={(m) => void commitPending(m)}
          onCancel={() => setPending(null)}
        />
      )}
      {dimWall && (
        <FtInKeypad
          label={`${dimWall.tag} · length (stretches the end node)`}
          initial={formatFtIn(wallLength(dimWall))}
          onCommit={(m) => void commitDim(m)}
          onCancel={() => setDimWall(null)}
        />
      )}
      {placement && (
        <PlacementPopover
          placement={placement}
          catalog={model.catalog}
          hintFile={storeyHintFile()}
          storey={activeStorey}
          runMacro={runMacro}
          selectByTag={selectByTag}
          onClose={() => setPlacement(null)}
        />
      )}
      <StoreyTabs model={model} />
      <SunIndicator model={model} />
      <div className="hud" style={{ left: 12, top: 12, display: "flex", gap: 6, alignItems: "center" }}>
        <label style={{ fontSize: 12 }}>Services <select value={activeService}
          onChange={(event) => setActiveService(event.target.value)}>
          <option value="">all</option>
          {serviceOptions.map((service) => <option key={service} value={service}>{service}</option>)}
        </select></label>
        <button className="btn" onClick={() => setShowClearances(!showClearances)}>
          {showClearances ? "Hide clearances" : "Clearances"}
        </button>
      </div>
      {activeUnderlay && <UnderlayCalibrationControl underlay={activeUnderlay}
        points={calibrationPoints} distanceFt={calibrationDistanceFt} onDistance={setCalibrationDistanceFt}
        active={calibrationMode} onStart={() => { setCalibrationMode(true); setCalibrationPoints([]); }}
        onSave={() => void saveCalibration()} />}
      {tool !== "select" && (
        <div className="hud" style={{ left: "auto", right: 12, bottom: "auto", top: 12, maxWidth: 260 }}>
          <ToolHint tool={tool} draft={Boolean(draft)}
            assembly={tool === "wall" ? wallAssembly : null}
            assemblies={model.catalog?.assemblies.map((a) => a.tag) ?? []}
            onAssembly={setDrawAssembly}
            onSplit={selection.kind === "wall" ? () => {
              const w = wallsOnStorey.find((x) => x.uid === selection.uid);
              if (w) void splitWall(w);
            } : null} />
        </div>
      )}
    </>
  );
}

function ToolHint({ tool, draft, assembly, assemblies, onAssembly, onSplit }: {
  tool: string;
  draft: boolean;
  assembly: string | null;
  assemblies: string[];
  onAssembly: (tag: string) => void;
  onSplit: (() => void) | null;
}) {
  const hints: Record<string, string> = {
    wall: draft ? "Tap the next corner · Shift = ortho · Esc ends the run" : "Tap to start a wall (snaps to nodes / grid)",
    opening: "Tap a wall to place a window or door",
    room: "Tap inside an enclosed area to claim a room",
    dimension: "Tap a wall to drive its length",
  };
  return (
    <div>
      <div style={{ fontWeight: 600, textTransform: "capitalize", marginBottom: 4 }}>{tool} tool</div>
      <div className="muted">{hints[tool]}</div>
      {tool === "wall" && assembly != null && (
        <label style={{ display: "block", marginTop: 6, fontSize: 12 }}>Assembly{" "}
          <select value={assembly} onChange={(e) => onAssembly(e.target.value)}>
            {assemblies.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
      )}
      {tool === "dimension" && onSplit && (
        <button className="btn" style={{ marginTop: 6 }} onClick={onSplit}>Split at midpoint</button>
      )}
    </div>
  );
}

// A draggable wall endpoint. Captures the pointer so the drag survives leaving the circle.
function NodeHandle({ world, project, onStart, onMove, onEnd }: {
  world: Vec2;
  project: (p: Vec2) => Vec2;
  onStart: () => void;
  onMove: (clientX: number, clientY: number) => void;
  onEnd: () => void;
}) {
  const dragging = useRef(false);
  const raf = useRef<number | null>(null);
  const [x, y] = project(world);
  return (
    <circle
      cx={x} cy={y} r={7} fill="#fff" stroke={NORDIC_ACCENT} strokeWidth={2.5}
      style={{ cursor: "grab" }}
      onPointerDown={(e) => {
        e.stopPropagation();
        (e.target as Element).setPointerCapture(e.pointerId);
        dragging.current = true;
        onStart();
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
    />
  );
}

function UnderlayCalibrationControl({ underlay, points, distanceFt, onDistance, active, onStart, onSave }: {
  underlay: Underlay;
  points: Vec2[];
  distanceFt: string;
  onDistance: (value: string) => void;
  active: boolean;
  onStart: () => void;
  onSave: () => void;
}) {
  const pathParts = underlay.path.split("/");
  const filename = pathParts[pathParts.length - 1];
  return <div className="hud" style={{ left: 12, top: 48, maxWidth: 270 }}>
    <div style={{ fontSize: 12 }}>Reference: {filename}</div>
    {!active ? <button className="btn" onClick={onStart}>Calibrate underlay</button> : <>
      <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
        Double-click two known points on the drawing ({points.length}/2).
      </div>
      {points.length === 2 && <label style={{ display: "block", marginTop: 5, fontSize: 12 }}>
        Known distance (ft) <input value={distanceFt} inputMode="decimal"
          onChange={(event) => onDistance(event.target.value)} style={{ width: 52 }} />
        <button className="btn" onClick={onSave} style={{ marginLeft: 5 }}>Save</button>
      </label>}
    </>}
  </div>;
}

function FixtureFootprint({ fixture, project, scale, dimmed }: {
  fixture: NonNullable<Model["fixtures"]>[number];
  project: (point: Vec2) => Vec2;
  scale: number;
  dimmed: boolean;
}) {
  const [x, y] = project(fixture.position);
  const width = fixture.footprint_m[0] * scale;
  const depth = fixture.footprint_m[1] * scale;
  return <g opacity={dimmed ? 0.35 : 0.9} pointerEvents="none">
    <rect x={x - width / 2} y={y - depth / 2} width={width} height={depth}
      fill="rgba(77,112,128,0.12)" stroke="#4d7080" strokeWidth={1.2} />
    <text x={x} y={y + 3} textAnchor="middle" fontSize={9} fill="#33505c">
      {fixture.type.replace("FX-", "")}
    </text>
  </g>;
}

function ClearanceOverlays({ model, storey, project, scale }: {
  model: Model;
  storey: string | null;
  project: (point: Vec2) => Vec2;
  scale: number;
}) {
  const items = [
    ...(model.fixtures ?? []).map((item) => ({ ...item, kind: "fixture" as const })),
    ...(model.furniture ?? []).map((item) => ({ ...item, kind: "furniture" as const })),
  ].filter((item) => (!storey || item.storey === storey) && item.clearance_m);
  return <g pointerEvents="none">{items.map((item) => {
    const [front, back, left, right] = item.clearance_m!;
    const [x, y] = project(item.position);
    const width = (item.footprint_m[0] + left + right) * scale;
    const depth = (item.footprint_m[1] + front + back) * scale;
    return <rect key={`clearance-${item.uid}`} x={x - width / 2} y={y - depth / 2}
      width={width} height={depth} fill="rgba(197,88,66,0.10)" stroke="#c55842"
      strokeDasharray="4 3" strokeWidth={1} />;
  })}</g>;
}

function clampScale(s: number): number {
  return Math.min(2000, Math.max(8, s));
}

function BackgroundGrid({ view }: { view: { scale: number; tx: number; ty: number } }) {
  const ftPx = view.scale * 0.3048;
  if (ftPx < 6) return <rect width="100%" height="100%" fill="none" />;
  const size = ftPx;
  const id = "grid";
  return (
    <>
      <defs>
        <pattern id={id} width={size} height={size} patternUnits="userSpaceOnUse"
          patternTransform={`translate(${view.tx % size},${view.ty % size})`}>
          <path d={`M ${size} 0 L 0 0 0 ${size}`} fill="none" stroke="#e6e1d6" strokeWidth={1} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </>
  );
}

function WallShape({ w, project, selected, hovered, showFraming, onSelect, onHover }: {
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
    <g onClick={onSelect} onPointerEnter={() => onHover(true)} onPointerLeave={() => onHover(false)}
      style={{ cursor: "pointer" }}>
      {w.layers.map((ly, i) =>
        ly.polygon.length >= 3 ? (
          <polygon key={i} points={poly(ly.polygon)} fill={materialColor(ly.material)}
            stroke="rgba(0,0,0,0.18)" strokeWidth={0.5} />
        ) : null,
      )}
      {showFraming && w.members.map((m) => {
        const [x0, y0] = project(m.p0);
        const [x1, y1] = project(m.p1);
        return <line key={m.key} x1={x0} y1={y0} x2={x1} y2={y1} stroke="#8a6d3b"
          strokeWidth={1.5} opacity={0.85} />;
      })}
      <line x1={project(w.axis[0])[0]} y1={project(w.axis[0])[1]}
        x2={project(w.axis[1])[0]} y2={project(w.axis[1])[1]} stroke={stroke}
        strokeWidth={selected ? 2.5 : 1.5} strokeDasharray={w.layers.length === 0 ? "4 4" : undefined} />
    </g>
  );
}

function OpeningShape({ o, host, project, scale, selected, onSelect, onEdit }: {
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
      <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
        stroke={selected ? NORDIC_ACCENT : "#fff"} strokeWidth={selected ? 6 : 5} />
      <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
        stroke={o.is_door ? "#7a5230" : NORDIC_ACCENT} strokeWidth={2}
        strokeDasharray={o.is_door ? undefined : "3 2"} />
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
        <button key={s.tag} className={`seg-btn${activeStorey === s.tag ? " active" : ""}`}
          onClick={() => setActiveStorey(s.tag)}>
          {s.tag}
        </button>
      ))}
    </div>
  );
}

function openEndKeys(model: Model): Set<string> {
  const nodes = deriveNodes(model.walls);
  const open = new Set<string>();
  for (const n of nodes.values()) if (n.walls.length < 2) open.add(n.id);
  return open;
}

// Whether the two walls meeting at a derived node are (near-)collinear — a healable joint.
function collinearAt(n: GeoNode, model: Model): boolean {
  if (n.walls.length !== 2) return false;
  const dirs: Vec2[] = [];
  for (const uid of n.walls) {
    const w = model.walls.find((x) => x.uid === uid);
    if (!w) return false;
    const [a, b] = w.axis;
    const far: Vec2 = Math.hypot(a[0] - n.p[0], a[1] - n.p[1]) < 1e-4 ? b : a;
    const dx = far[0] - n.p[0];
    const dy = far[1] - n.p[1];
    const len = Math.hypot(dx, dy) || 1;
    dirs.push([dx / len, dy / len]);
  }
  const cross = dirs[0][0] * dirs[1][1] - dirs[0][1] * dirs[1][0];
  return Math.abs(cross) < 0.02;
}

function nodeTagMatches(tag: string, world: Vec2, nodes: PlanNode[]): boolean {
  const n = nodes.find((x) => x.tag === tag);
  return n ? Math.hypot(n.x_m - world[0], n.y_m - world[1]) < 1e-4 : false;
}

import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import type { Selection } from "../state/store";
import type { PreviewGeometry } from "../engine/EngineClient";
import type { CanvasObject, CanvasObjectType, Model, Opening, PlanNode, Stair, Vec2, Wall } from "../model/types";
import {
  deriveNodes,
  formatFtIn,
  M_PER_FT,
  nearestWallHit,
  openingHostWall,
  openingFitsWall,
  openingStartFromCenter,
  type Node as GeoNode,
  orthoLock,
  pointAlong,
  snapWorld,
  wallLength,
} from "../model/geometry";
import { materialColor, NORDIC_ACCENT, NORDIC_INK, NORDIC_LINE } from "../nordic/palette";
import { DoorSettingsPopover } from "./DoorSettingsPopover";
import { WindowSettingsPopover } from "./WindowSettingsPopover";
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

interface OpeningDragPreview {
  opening: Opening;
  host: Wall;
  valid: boolean;
}

// A placement popover request (opening on a wall, or a room seed) anchored at screen px.
type Placement =
  | { kind: "opening"; screen: Vec2; wall: Wall; along_m: number }
  | { kind: "placeable"; screen: Vec2; position: Vec2 }
  | { kind: "room"; screen: Vec2; seed: Vec2 };

// A read-only wall summary kept local to the canvas. The inspector remains the source for
// edits; this card only makes the essential assembly information available at the click.
interface WallAssemblyPopup {
  wallUid: string;
  screen: Vec2;
}

// An opening settings popover request (door: type/handing; window: type), anchored at the
// opening's screen point.
interface DoorPopup {
  opening: Opening;
  screen: Vec2;
}

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
  const showFraming = useStore((s) => s.showFraming);
  const activeStorey = useStore((s) => s.activeStorey);
  const workspace = useStore((s) => s.activeWorkspace);
  const tool = useStore((s) => s.tool);
  const applyOps = useStore((s) => s.applyOps);
  const runMacro = useStore((s) => s.runMacro);
  const previewMacro = useStore((s) => s.previewMacro);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const duplicateSelection = useStore((s) => s.duplicateSelection);
  const offline = useStore((s) => s.offline);
  const toast = useStore((s) => s.toast);

  const svgRef = useRef<SVGSVGElement>(null);
  const pointers = useRef<Map<number, Vec2>>(new Map());
  const pinch = useRef<{ dist: number; scale: number } | null>(null);
  const panLast = useRef<Vec2 | null>(null);
  const gesture = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const suppressPostPanClick = useRef(false);
  const fittedStorey = useRef<string | null>(null);
  const shift = useRef(false);
  // Latest draft + rubber-band, mirrored into refs so the global keydown handler can open the
  // exact-length keypad without re-subscribing on every pointer move.
  const draftRef = useRef<WallDraft | null>(null);
  const rubberRef = useRef<{ end: Vec2; len: number } | null>(null);
  const lengthEntryOpen = useRef(false);
  const [pending, setPending] = useState<Pending | null>(null);
  const [draft, setDraft] = useState<WallDraft | null>(null);
  const [cursor, setCursor] = useState<Vec2 | null>(null); // world-space hover/rubber-band
  const [nodeDrag, setNodeDrag] = useState<NodeDrag | null>(null);
  // Live cascading geometry for the wall(s)/room(s) touched by an in-progress node drag
  // (→ Phase 4). Fetched off the reduced-resolve /macro/preview endpoint, self-throttled by
  // the store to one in-flight request; cleared on drag end/cancel so it never lingers past
  // the drag it belongs to and shadows the committed model.
  const [previewGeom, setPreviewGeom] = useState<PreviewGeometry | null>(null);
  const [openingDragPreview, setOpeningDragPreview] = useState<OpeningDragPreview | null>(null);
  const [placement, setPlacement] = useState<Placement | null>(null);
  const [wallAssemblyPopup, setWallAssemblyPopup] = useState<WallAssemblyPopup | null>(null);
  const [doorPopup, setDoorPopup] = useState<DoorPopup | null>(null);
  const [windowPopup, setWindowPopup] = useState<DoorPopup | null>(null);
  const [dimWall, setDimWall] = useState<Wall | null>(null);
  // Exact-length entry for the wall being drawn (CAD precision): type a length and the next
  // segment lands at that distance along the current rubber-band direction. `dir` is a unit
  // vector captured when the keypad opens; committing draws start → start + dir·length.
  const [lengthEntry, setLengthEntry] = useState<{ start: Vec2; dir: Vec2; initial: string } | null>(null);
  // Desktop-first right-click context menu (Phase 10), anchored in pane coordinates.
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number } | null>(null);
  const drawAssembly = useStore((s) => s.drawAssembly) ?? "";
  const setDrawAssembly = useStore((s) => s.setDrawAssembly);
  const [activeService, setActiveService] = useState<string>("");
  const [showClearances, setShowClearances] = useState(false);

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

  // Stable per-element handlers so the memoized shapes below don't re-render the whole
  // subtree on every hover/selection change (Phase 1b): identity never changes across
  // renders, and tool state is read live from the store at call time.
  const selectEl = useCallback(
    (kind: Selection["kind"], uid: string) => {
      const s = useStore.getState();
      if (s.tool === "select") s.select(kind, uid);
    },
    [],
  );
  const hoverEl = useCallback((uid: string | null) => {
    useStore.getState().setHover(uid);
  }, []);
  const editOpeningStable = useCallback((o: Opening, screen: Vec2) => {
    if (useStore.getState().tool !== "select") return;
    if (o.is_door) {
      setDoorPopup({ opening: o, screen });
    } else {
      setWindowPopup({ opening: o, screen });
    }
  }, []);
  const movePlaceableFromDrag = useCallback((item: CanvasObject, position: Vec2) => {
    if (useStore.getState().tool !== "select") return;
    void runMacro({ macro: "move_placeable", storey: item.storey, tag: item.tag,
      position });
  }, [runMacro]);
  const rotatePlaceableFromHandle = useCallback((item: CanvasObject, degrees: number, freeRotation: boolean) => {
    if (useStore.getState().tool !== "select") return;
    void runMacro({ macro: "rotate_placeable", storey: item.storey, tag: item.tag, degrees,
      free_rotation: freeRotation });
  }, [runMacro]);
  const moveOpeningFromDrag = useCallback((opening: Opening, host: Wall, position: Vec2) => {
    if (useStore.getState().tool !== "select") return;
    const target = nearestOpeningHost(model.walls, host.storey, position);
    setOpeningDragPreview(null);
    if (!target || target.distance_m > 0.6) return;
    const along = formatFtIn(openingStartFromCenter(target.along_m, opening.width_m));
    if (target.wall.tag === host.tag) {
      void runMacro({ macro: "move_opening", storey: host.storey, tag: opening.tag, along });
    } else {
      void runMacro({ macro: "rehost_opening", storey: host.storey, tag: opening.tag,
        host: target.wall.tag, along });
    }
  }, [model.walls, runMacro]);
  const previewOpeningFromDrag = useCallback((opening: Opening, host: Wall, position: Vec2) => {
    const target = nearestOpeningHost(model.walls, host.storey, position);
    if (!target || target.distance_m > 0.6) {
      setOpeningDragPreview(null);
      return;
    }
    setOpeningDragPreview({
      opening: { ...opening, center_along_m: target.along_m }, host: target.wall,
      valid: openingFitsWall(target.wall, target.along_m, opening.width_m),
    });
  }, [model.walls]);
  const selectWallWithPopup = useCallback((wall: Wall, event: React.MouseEvent<SVGGElement>) => {
    const s = useStore.getState();
    if (s.tool !== "select") return;
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    s.select("wall", wall.uid);
    setWallAssemblyPopup({
      wallUid: wall.uid,
      screen: [event.clientX - rect.left, event.clientY - rect.top],
    });
  }, []);

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
  const stairsOnStorey = useMemo(() => {
    const candidates = (model.stairs ?? [])
      .filter((stair) => !activeStorey || stair.storey === activeStorey || stair.to_storey === activeStorey)
      .sort((a, b) => Number(a.storey !== activeStorey) - Number(b.storey !== activeStorey) || a.uid.localeCompare(b.uid));
    const seenOutlines = new Set<string>();
    return candidates.filter((stair) => {
      const outlineKey = stair.outline.map(([x, y]) => `${x.toFixed(6)},${y.toFixed(6)}`).sort().join(";");
      if (seenOutlines.has(outlineKey)) return false;
      seenOutlines.add(outlineKey);
      return true;
    });
  }, [model.stairs, activeStorey]);
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

  const serviceOptions = useMemo(() => [...new Set((model.catalog?.canvas_object_types ?? [])
    .flatMap((type) => type.ports.map((port) => port.service)))].sort(), [model.catalog?.canvas_object_types]);
  const canvasTypes = useMemo(() => new Map((model.catalog?.canvas_object_types ?? [])
    .map((item) => [item.tag, item])), [model.catalog?.canvas_object_types]);
  const visibleServiceObjects = (model.canvas_objects ?? []).filter((item) =>
    item.position_m && (!activeStorey || item.storey === activeStorey) &&
    (!activeService || (item.type ? canvasTypes.get(item.type)?.ports.some((port) => port.service === activeService) : false)));
  const popupWall = useMemo(
    () => wallAssemblyPopup ? model.walls.find((wall) => wall.uid === wallAssemblyPopup.wallUid) ?? null : null,
    [model.walls, wallAssemblyPopup],
  );

  // A popup is meaningful only while its wall remains selected. This also covers selection
  // changes initiated by the sidebar rather than by the SVG itself.
  useEffect(() => {
    if (!wallAssemblyPopup) return;
    if (selection.kind !== "wall" || selection.uid !== wallAssemblyPopup.wallUid || !popupWall) {
      setWallAssemblyPopup(null);
    }
  }, [popupWall, selection, wallAssemblyPopup]);

  // The authored model is in metres, while screen dimensions are only known after the
  // SVG enters its pane.  Fit once per storey so a fresh single-pane view starts with
  // the whole floor visible rather than an arbitrary 120 px/m slice near the origin.
  useLayoutEffect(() => {
    if (!activeStorey || fittedStorey.current === activeStorey) return;
    const svg = svgRef.current;
    if (!svg) return;

    const points: Vec2[] = [
      ...wallsOnStorey.flatMap((wall) => [wall.axis[0], wall.axis[1],
        ...wall.layers.flatMap((layer) => layer.polygon)]),
      ...model.rooms.filter((room) => room.storey === activeStorey)
        .flatMap((room) => room.clear_face),
    ];
    if (!points.length) return;

    const fit = () => {
      const { width, height } = svg.getBoundingClientRect();
      if (width <= 0 || height <= 0) return;
      const xs = points.map(([x]) => x);
      const ys = points.map(([, y]) => y);
      const spanX = Math.max(0.1, Math.max(...xs) - Math.min(...xs));
      const spanY = Math.max(0.1, Math.max(...ys) - Math.min(...ys));
      const padding = 64;
      const scale = clampScale(Math.min((width - padding * 2) / spanX, (height - padding * 2) / spanY));
      setView({
        scale,
        tx: width / 2 - ((Math.min(...xs) + Math.max(...xs)) / 2) * scale,
        ty: height / 2 + ((Math.min(...ys) + Math.max(...ys)) / 2) * scale,
      });
      fittedStorey.current = activeStorey;
    };

    const observer = new ResizeObserver(fit);
    observer.observe(svg);
    fit();
    return () => observer.disconnect();
  }, [activeStorey, model.rooms, setView, wallsOnStorey]);

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
    if (e.pointerType === "mouse" && e.button !== 0) return;
    // Capturing on the viewport (instead of the pressed wall/image child) keeps the
    // gesture alive after the pointer leaves that child or the SVG bounds.
    e.currentTarget.setPointerCapture(e.pointerId);
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
      const currentView = useStore.getState().view;
      setView({ tx: currentView.tx + dx, ty: currentView.ty + dy });
    }
  };

  const onPointerUp = (e: React.PointerEvent) => {
    const wasTap = gesture.current && !gesture.current.moved;
    const wasPan = gesture.current?.moved ?? false;
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    if (pointers.current.size === 0) panLast.current = null;
    if (wasTap && pointers.current.size === 0) {
      handleTap(unproject(e.clientX, e.clientY), [
        e.clientX - e.currentTarget.getBoundingClientRect().left,
        e.clientY - e.currentTarget.getBoundingClientRect().top,
      ]);
    }
    if (wasPan) {
      // Native click follows pointerup.  Let the event finish, then clear the guard
      // so a drag across geometry never becomes an accidental selection.
      suppressPostPanClick.current = true;
      window.setTimeout(() => { suppressPostPanClick.current = false; }, 0);
    }
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      e.currentTarget.releasePointerCapture(e.pointerId);
    }
    gesture.current = null;
  };

  const onClickCapture = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!suppressPostPanClick.current) return;
    e.preventDefault();
    e.stopPropagation();
  };

  // ---- tool tap dispatch ----------------------------------------------------
  const handleTap = (world: Vec2, screen: Vec2) => {
    if (placement) { setPlacement(null); return; }
    if (offline && tool !== "select") { toast("Editing needs the server (offline)", "error"); return; }
    switch (tool) {
      case "select": {
        // Resolve wall taps here instead of relying solely on SVG click bubbling. Pointer
        // capture keeps pan/touch gestures reliable, but can make child click delivery vary
        // across browsers and installed-PWA shells.
        const hit = nearestWallHit(wallsOnStorey, world);
        if (hit && hit.dist_m * view.scale < HIT_PX) {
          select("wall", hit.wall.uid);
          setWallAssemblyPopup({ wallUid: hit.wall.uid, screen });
        } else {
          select(null, null);
          setWallAssemblyPopup(null);
          setDoorPopup(null);
          setWindowPopup(null);
        }
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
      case "placeable": {
        const [sx, sy] = project(world);
        setPlacement({ kind: "placeable", screen: [sx, sy], position: world });
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
      // Chain: keep drawing from this endpoint when armed (ContextBar toggle); otherwise
      // end the run after one segment. Esc / tool switch always ends it.
      if (useStore.getState().chainDraw) setDraft({ start: end, startNode: null });
      else setDraft(null);
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
    setPreviewGeom(null); // the real commit's reload supersedes the preview geometry
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
        setDraft(null); setPlacement(null); setWallAssemblyPopup(null); setDimWall(null); setNodeDrag(null); setPending(null); setDoorPopup(null); setWindowPopup(null);
        setPreviewGeom(null); setLengthEntry(null);
      } else if ((e.key === "Enter" || /^[0-9]$/.test(e.key)) && draftRef.current && !lengthEntryOpen.current) {
        // Precise segment: type a length to place the next corner at an exact distance along the
        // current rubber-band direction (falls back to +x when the pointer sits on the start).
        const d = draftRef.current;
        const r = rubberRef.current;
        let dir: Vec2 = [1, 0];
        if (r && r.len > 1e-4) dir = [(r.end[0] - d.start[0]) / r.len, (r.end[1] - d.start[1]) / r.len];
        e.preventDefault();
        setLengthEntry({ start: d.start, dir, initial: /^[0-9]$/.test(e.key) ? e.key : formatFtIn(r?.len ?? 0) });
      } else if ((e.key === "Delete" || e.key === "Backspace") && selection.uid && !offline) {
        e.preventDefault();
        void deleteSelection();
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "d" && selection.uid && !offline
          && (selection.kind === "opening" || selection.kind === "canvas_object")) {
        e.preventDefault();
        void duplicateSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selection.uid, selection.kind, offline, deleteSelection, duplicateSelection]);

  // End a wall run when leaving the wall tool.
  useEffect(() => { if (tool !== "wall") { setDraft(null); setCursor(null); } }, [tool]);

  // Mirror the in-flight draw gesture into the store so the ContextBar / interaction-state
  // label and App's Esc hierarchy (Phase 2) can see it.
  const setSubOperation = useStore((s) => s.setSubOperation);
  useEffect(() => { setSubOperation(draft != null); }, [draft, setSubOperation]);

  // ---- opening driven-dimension edit (double-click an opening) ---------------
  const commitPending = async (meters: number) => {
    if (!pending) return;
    const o = pending.opening;
    const ok = pending.field === "position"
      ? Boolean(await runMacro({ macro: "move_opening", storey: hostStorey(model, o), tag: o.tag,
        along: formatFtIn(meters) }))
      : await applyOps([{
        op: "update", type: o.is_door ? "Door" : "Window", tag: o.tag,
        fields: { sill_height: formatFtIn(meters) },
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
  draftRef.current = draft;
  rubberRef.current = rubber;
  lengthEntryOpen.current = lengthEntry != null;

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
        onClickCapture={onClickCapture}
        onContextMenu={(e) => {
          const rect = svgRef.current?.getBoundingClientRect();
          if (!rect) return;
          e.preventDefault();
          setCtxMenu({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        }}
      >
        <defs>
          <marker id="stair-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--canvas-wood)" />
          </marker>
        </defs>
        <BackgroundGrid view={view} />
        {/* rooms first (tinted fills, behind walls) — a live drag's preview cascades into
            neighboring rooms' clear-face polygons, matched by tag against the last preview */}
        {model.rooms
          .filter((r) => !activeStorey || r.storey === activeStorey)
          .map((r) => {
            const clearFace = previewGeom?.rooms.find((x) => x.tag === r.tag)?.clear_face
              ?? r.clear_face;
            return (
              <g key={r.uid} onClick={() => tool === "select" && select("room", r.uid)}
                style={{ cursor: tool === "select" ? "pointer" : undefined }}>
                <polygon points={clearFace.map(project).map((p) => p.join(",")).join(" ")}
                  fill="var(--canvas-selection)" stroke="none" />
                {clearFace.length > 0 && (() => {
                  const centroid: Vec2 = [
                    clearFace.reduce((sum, point) => sum + point[0], 0) / clearFace.length,
                    clearFace.reduce((sum, point) => sum + point[1], 0) / clearFace.length,
                  ];
                  const [x, y] = project(centroid);
                  return <text x={x} y={y - 5} textAnchor="middle" pointerEvents="none"
                    fill="var(--canvas-ink)" fontSize={12} fontWeight={700}
                    style={{ paintOrder: "stroke", stroke: "var(--canvas-white)", strokeWidth: 3 }}>
                    <tspan x={x}>{r.tag}</tspan>
                    <tspan x={x} dy={14} fontSize={10} fontWeight={500}>
                      {Math.round(r.area_m2 * 10.7639)} SF
                    </tspan>
                  </text>;
                })()}
              </g>
            );
          })}
        {/* walls — likewise shown at their previewed axis (tag-matched) while a node drag is
            in flight, so connected walls visibly stretch/shrink before the commit lands */}
        {wallsOnStorey.map((w) => {
          const previewAxis = previewGeom?.walls.find((x) => x.tag === w.tag)?.axis;
          const displayWall = previewAxis ? { ...w, axis: previewAxis as [Vec2, Vec2] } : w;
          const displayedOpenings = model.openings
            .filter((opening) => opening.host === w.tag && opening.uid !== openingDragPreview?.opening.uid);
          if (openingDragPreview?.host.tag === w.tag) displayedOpenings.push(openingDragPreview.opening);
          return (
            <WallShape
              key={w.uid}
              w={displayWall}
              openings={displayedOpenings}
              project={project}
              selected={selection.uid === w.uid}
              hovered={hoverUid === w.uid}
              showFraming={showFraming}
              onSelect={selectWallWithPopup}
              onHover={hoverEl}
            />
          );
        })}
        {/* openings */}
        {model.openings.map((o) => {
          const host = openingHostWall(model.walls, o);
          if (!host || (activeStorey && host.storey !== activeStorey)) return null;
          const doubleLeaf = o.is_door
            && model.catalog?.door_types.find((dt) => dt.tag === o.type_ref)?.operation === "double_swing";
          return (
            <OpeningShape
              key={o.uid}
              o={o}
              host={host}
              project={project}
              scale={view.scale}
              selected={selection.uid === o.uid}
              doubleLeaf={doubleLeaf}
              onSelect={selectEl}
              onEdit={editOpeningStable}
              toWorld={unproject}
              onMove={moveOpeningFromDrag}
              onPreview={previewOpeningFromDrag}
              onPreviewEnd={() => setOpeningDragPreview(null)}
            />
          );
        })}
        {openingDragPreview && <OpeningShape
          key={`preview-${openingDragPreview.opening.uid}`}
          o={openingDragPreview.opening}
          host={openingDragPreview.host}
          project={project}
          scale={view.scale}
          selected={false}
          preview={openingDragPreview.valid ? "valid" : "invalid"}
          onSelect={selectEl}
          onEdit={editOpeningStable}
          toWorld={unproject}
          onMove={moveOpeningFromDrag}
        />}
        {stairsOnStorey
          .map((stair) => <StairShape key={stair.uid} stair={stair} project={project}
            selected={selection.uid === stair.uid} hovered={hoverUid === stair.uid}
            onSelect={selectEl} onHover={hoverEl} />)}
        {(model.canvas_objects ?? [])
          // Doors/windows remain topology-aware SVG shapes below; their normalized records
          // serve inspection/interchange consumers and must not render a second footprint.
          .filter((item) => item.domain !== "opening" && item.position_m &&
            (!activeStorey || item.storey === activeStorey))
          .map((item) => <CanvasObjectFootprint key={item.uid} item={item}
            type={item.type ? canvasTypes.get(item.type) : undefined} project={project} scale={view.scale}
            walls={wallsOnStorey}
            selected={selection.uid === item.uid} onSelect={selectEl} toWorld={unproject}
            onMove={movePlaceableFromDrag} onRotate={rotatePlaceableFromHandle} />)}
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
                fill={open ? "var(--error)" : healable ? NORDIC_ACCENT : NORDIC_LINE}
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
              onMove={(clientX, clientY) => setNodeDrag((d) => {
                if (!d) return d;
                const raw = unproject(clientX, clientY);
                const others = new Map([...snapNodes].filter(([t]) => t !== d.tag));
                const to = snapWorld(raw, others, tolM, gridM).point;
                if (activeStorey) {
                  const dx = to[0] - d.from[0];
                  const dy = to[1] - d.from[1];
                  void previewMacro({
                    macro: "move_nodes", storey: activeStorey, nodes: [d.tag], dx, dy,
                  }).then((geom) => { if (geom) setPreviewGeom(geom); });
                }
                return { ...d, to };
              })}
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
              <circle cx={ex} cy={ey} r={5} fill="var(--canvas-white)" stroke={NORDIC_ACCENT} strokeWidth={2} />
              {rubber && rubber.len > 0.01 && (
                <text x={mx} y={my - 8} fill={NORDIC_INK} fontSize={12} textAnchor="middle"
                  style={{ paintOrder: "stroke" }} stroke="var(--canvas-white)" strokeWidth={3}>
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
            stroke={snap.nodeId ? "var(--error)" : NORDIC_ACCENT} strokeWidth={1.5} pointerEvents="none" />;
        })()}
        {/* detail markers (Phase 8): D-tags at junctions, shown in the DOCUMENT workspace */}
        {workspace === "document" && (model.conditions ?? []).map((c, i) => {
          const wall = model.walls.find((w) => c.elements.includes(w.tag) && w.storey === activeStorey);
          if (!wall) return null;
          const mid: Vec2 = [(wall.axis[0][0] + wall.axis[1][0]) / 2, (wall.axis[0][1] + wall.axis[1][1]) / 2];
          const [x, y] = project(mid);
          return (
            <g key={`detail-${c.key}`} pointerEvents="auto" style={{ cursor: "pointer" }}
              onClick={() => select("wall", wall.uid)}>
              <circle cx={x} cy={y} r={9} fill="var(--canvas-white)" stroke={NORDIC_ACCENT} strokeWidth={1.5} />
              <text x={x} y={y + 3} fill={NORDIC_ACCENT} fontSize={9} textAnchor="middle" fontWeight={700}>
                D{i + 1}
              </text>
            </g>
          );
        })}
        {/* dimension line for selected wall */}
        {selection.kind === "wall" && (() => {
          const w = wallsOnStorey.find((x) => x.uid === selection.uid);
          if (!w) return null;
          return <WallDimension w={w} project={project} />;
        })()}
        {activeService && <>
          <rect width="100%" height="100%" fill="var(--canvas-dim)" pointerEvents="none" />
          {visibleServiceObjects.map((item) => <CanvasObjectFootprint key={`service-${item.uid}`} item={item}
            type={item.type ? canvasTypes.get(item.type) : undefined} project={project} scale={view.scale}
            walls={wallsOnStorey}
            selected={selection.uid === item.uid} onSelect={selectEl} toWorld={unproject}
            onMove={movePlaceableFromDrag} onRotate={rotatePlaceableFromHandle} />)}
        </>}
      </svg>
      {pending && (
        <FtInKeypad
          label={`${pending.opening.tag} · ${pending.field === "position" ? "start-jamb station along wall" : "sill height"}`}
          initial={pending.initial}
          onCommit={(m) => void commitPending(m)}
          onCancel={() => setPending(null)}
        />
      )}
      {doorPopup && (
        <DoorSettingsPopover
          opening={doorPopup.opening}
          screen={doorPopup.screen}
          doorTypes={model.catalog?.door_types ?? []}
          applyOps={applyOps}
          toast={toast}
          onEditPosition={() => {
            setPending({ opening: doorPopup.opening, field: "position",
              initial: formatFtIn(openingStartFromCenter(
                doorPopup.opening.center_along_m, doorPopup.opening.width_m,
              )) });
            setDoorPopup(null);
          }}
          onEditSillHeight={() => {
            setPending({ opening: doorPopup.opening, field: "sill_height",
              initial: formatFtIn(doorPopup.opening.sill_m) });
            setDoorPopup(null);
          }}
          onClose={() => setDoorPopup(null)}
        />
      )}
      {windowPopup && (
        <WindowSettingsPopover
          opening={windowPopup.opening}
          screen={windowPopup.screen}
          windowTypes={model.catalog?.window_types ?? []}
          applyOps={applyOps}
          toast={toast}
          onEditPosition={() => {
            setPending({ opening: windowPopup.opening, field: "position",
              initial: formatFtIn(openingStartFromCenter(
                windowPopup.opening.center_along_m, windowPopup.opening.width_m,
              )) });
            setWindowPopup(null);
          }}
          onEditSillHeight={() => {
            setPending({ opening: windowPopup.opening, field: "sill_height",
              initial: formatFtIn(windowPopup.opening.sill_m) });
            setWindowPopup(null);
          }}
          onDelete={() => {
            useStore.getState().select("opening", windowPopup.opening.uid);
            void useStore.getState().deleteSelection();
            setWindowPopup(null);
          }}
          onClose={() => setWindowPopup(null)}
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
      {lengthEntry && (
        <FtInKeypad
          label="Segment length · exact distance along the current direction"
          initial={lengthEntry.initial}
          onCommit={(m) => {
            const { start, dir } = lengthEntry;
            setLengthEntry(null);
            void commitWall(start, [start[0] + dir[0] * m, start[1] + dir[1] * m]);
          }}
          onCancel={() => setLengthEntry(null)}
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
          toast={toast}
          onClose={() => setPlacement(null)}
        />
      )}
      {wallAssemblyPopup && popupWall && (
        <WallAssemblyPopupCard
          wall={popupWall}
          screen={wallAssemblyPopup.screen}
          viewport={svgRef.current?.getBoundingClientRect() ?? null}
          onClose={() => setWallAssemblyPopup(null)}
        />
      )}
      <SunIndicator model={model} />
      <div className="canvas-context-controls">
        <StoreyTabs model={model} />
      <div className="hud" style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <label style={{ fontSize: 12 }}>Services <select value={activeService}
          onChange={(event) => setActiveService(event.target.value)}>
          <option value="">all</option>
          {serviceOptions.map((service) => <option key={service} value={service}>{service}</option>)}
        </select></label>
        <button className="btn" onClick={() => setShowClearances(!showClearances)}>
          {showClearances ? "Hide clearances" : "Clearances"}
        </button>
      </div>
      </div>
      {tool !== "select" && (
        <div className="hud" style={{ left: 12, right: "auto", bottom: "auto", top: "calc(44px + 84px)", maxWidth: 260 }}>
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
      {ctxMenu && (
        <>
          <div className="ctx-overlay" onPointerDown={() => setCtxMenu(null)} onContextMenu={(e) => { e.preventDefault(); setCtxMenu(null); }} />
          <div className="ctx-menu" style={{ left: ctxMenu.x, top: ctxMenu.y }} role="menu">
            {selection.uid ? (
              <>
                <button role="menuitem" onClick={() => { select(null, null); setCtxMenu(null); }}>Deselect</button>
                {!offline && (selection.kind === "opening" || selection.kind === "canvas_object") && (
                  <button role="menuitem" onClick={() => { void duplicateSelection(); setCtxMenu(null); }}>Duplicate</button>
                )}
                {!offline && (
                  <button role="menuitem" className="ctx-danger" onClick={() => { void deleteSelection(); setCtxMenu(null); }}>Delete</button>
                )}
              </>
            ) : (
              <button role="menuitem" disabled>Nothing selected</button>
            )}
          </div>
        </>
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
    wall: draft ? "Tap the next corner · Shift = ortho · type a length for exact · Esc ends" : "Tap to start a wall (snaps to nodes / grid)",
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
  // A generous transparent halo (r=13 → 26px) carries the pointer gesture so the endpoint is
  // easy to grab on touch and at a glance, while the visible dot stays small and uncluttered.
  return (
    <g style={{ cursor: "grab" }}
      onPointerDown={(e) => {
        e.stopPropagation();
        (e.currentTarget as Element).setPointerCapture(e.pointerId);
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
    >
      <circle cx={x} cy={y} r={13} fill="transparent" />
      <circle cx={x} cy={y} r={7} fill="var(--canvas-white)" stroke={NORDIC_ACCENT} strokeWidth={2.5}
        pointerEvents="none" />
    </g>
  );
}

function CanvasObjectFootprint({ item, type, project, scale, walls, selected, onSelect, toWorld, onMove, onRotate }: {
  item: CanvasObject;
  type?: CanvasObjectType;
  project: (point: Vec2) => Vec2;
  scale: number;
  walls: Wall[];
  selected: boolean;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  toWorld: (clientX: number, clientY: number) => Vec2;
  onMove: (item: CanvasObject, position: Vec2) => void;
  onRotate: (item: CanvasObject, degrees: number, freeRotation: boolean) => void;
}) {
  const [draggedPosition, setDraggedPosition] = useState<Vec2 | null>(null);
  const [draggedRotation, setDraggedRotation] = useState<number | null>(null);
  const [alignmentPoint, setAlignmentPoint] = useState<Vec2 | null>(null);
  if (!item.position_m) return null;
  const position = draggedPosition ?? item.position_m;
  const [x, y] = project(position);
  const [widthM, depthM] = type?.footprint_m ?? [0.45, 0.45];
  const width = widthM * scale;
  const depth = depthM * scale;
  const rotation = draggedRotation ?? item.rotation ?? 0;
  const colors: Record<string, [string, string]> = {
    furniture: ["var(--canvas-wood-soft)", "var(--canvas-wood)"],
    plumbing: ["var(--canvas-selection)", "var(--accent)"],
    electrical: ["#fff2bd", "#a66f00"],
    mechanical: ["#dceafb", "#37658d"],
    appliance: ["#e5e7eb", "#4b5563"],
  };
  const [fill, stroke] = colors[item.domain] ?? ["#e5e7eb", "#4b5563"];
  return <g opacity={0.92} style={{ cursor: "grab" }}
    onPointerDown={(event) => { event.stopPropagation(); event.currentTarget.setPointerCapture(event.pointerId); onSelect("canvas_object", item.uid); }}
    onPointerMove={(event) => {
      if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
      const next = toWorld(event.clientX, event.clientY);
      setDraggedPosition(next);
      const hit = nearestWallHit(walls, next);
      setAlignmentPoint(hit && hit.dist_m <= .35 ? hit.point : null);
    }}
    onPointerUp={(event) => {
      if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
      event.currentTarget.releasePointerCapture(event.pointerId);
      const next = toWorld(event.clientX, event.clientY);
      setDraggedPosition(null);
      setAlignmentPoint(null);
      if (Math.hypot(next[0] - item.position_m![0], next[1] - item.position_m![1]) > 0.001) onMove(item, next);
    }}
    onPointerCancel={() => { setDraggedPosition(null); setAlignmentPoint(null); }}>
    {type?.plan_svg ? <image href={type.plan_svg} x={x - width / 2} y={y - depth / 2} width={width} height={depth}
      transform={`rotate(${-rotation} ${x} ${y})`} />
      : <rect x={x - width / 2} y={y - depth / 2} width={width} height={depth}
        fill={fill} stroke={selected ? "var(--ink)" : stroke} strokeWidth={selected ? 2.4 : 1.2}
        transform={`rotate(${-rotation} ${x} ${y})`} />}
    <text x={x} y={y + 3} textAnchor="middle" fontSize={9} fill="var(--ink)" pointerEvents="none">
      {(type?.name ?? item.type ?? item.kind).replace(/^[A-Z]+-/, "")}
    </text>
    {selected && <g>
      <line x1={x} y1={y - depth / 2} x2={x} y2={y - depth / 2 - 18}
        stroke="var(--ink)" strokeWidth={1.2} pointerEvents="none" />
      <circle cx={x} cy={y - depth / 2 - 23} r={5} fill="var(--canvas-selection)" stroke="var(--ink)"
        strokeWidth={1.2} style={{ cursor: "crosshair" }}
        onPointerDown={(event) => {
          event.stopPropagation();
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
          const [worldX, worldY] = toWorld(event.clientX, event.clientY);
          const raw = Math.atan2(worldY - position[1], worldX - position[0]) * 180 / Math.PI;
          setDraggedRotation(event.shiftKey ? raw : Math.round(raw / 15) * 15);
        }}
        onPointerUp={(event) => {
          if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
          event.currentTarget.releasePointerCapture(event.pointerId);
          const [worldX, worldY] = toWorld(event.clientX, event.clientY);
          const raw = Math.atan2(worldY - position[1], worldX - position[0]) * 180 / Math.PI;
          const next = event.shiftKey ? raw : Math.round(raw / 15) * 15;
          setDraggedRotation(null);
          if (Math.abs(next - (item.rotation ?? 0)) > 0.01) onRotate(item, next, event.shiftKey);
        }} />
    </g>}
    {alignmentPoint && draggedPosition && (() => {
      const [ax, ay] = project(alignmentPoint);
      return <line x1={x} y1={y} x2={ax} y2={ay} stroke={NORDIC_ACCENT}
        strokeWidth={1.5} strokeDasharray="4 3" pointerEvents="none" />;
    })()}
  </g>;
}

function ClearanceOverlays({ model, storey, project, scale }: {
  model: Model;
  storey: string | null;
  project: (point: Vec2) => Vec2;
  scale: number;
}) {
  const legacyItems = [
    ...(model.fixtures ?? []).map((item) => ({ ...item, kind: "fixture" as const })),
    ...(model.furniture ?? []).map((item) => ({ ...item, kind: "furniture" as const })),
  ].filter((item) => (!storey || item.storey === storey) && item.clearance_m);
  const resolvedItems = (model.canvas_objects ?? []).filter((item) =>
    (!storey || item.storey === storey) && ((item.required_clearances?.length ?? 0) > 0 || (item.recommended_clearances?.length ?? 0) > 0));
  const openingOverlays = model.openings.filter((opening) => {
    const host = openingHostWall(model.walls, opening);
    return (!storey || host?.storey === storey) && ((opening.swing_clearance?.length ?? 0) > 0 ||
      (opening.framing_bumper?.length ?? 0) > 0);
  });
  return <g pointerEvents="none">{resolvedItems.flatMap((item) => [
    ...(item.required_clearances ?? []).map((polygon, index) => ({ item, polygon, required: true, index })),
    ...(item.recommended_clearances ?? []).map((polygon, index) => ({ item, polygon, required: false, index })),
  ]).map(({ item, polygon, required, index }) => <polygon key={`resolved-clearance-${item.uid}-${index}`}
    points={polygon.map((point) => project(point).join(",")).join(" ")}
    fill={required ? "var(--canvas-selection)" : "var(--canvas-wood-soft)"}
    fillOpacity={0.22} stroke={required ? "var(--error)" : "var(--canvas-wood)"}
    strokeDasharray="4 3" strokeWidth={required ? 1.4 : 1} />)}
  {openingOverlays.map((opening) => <g key={`opening-overlay-${opening.uid}`}>
    {opening.swing_clearance && <polygon points={opening.swing_clearance.map((point) => project(point).join(",")).join(" ")}
      fill="var(--canvas-wood-soft)" fillOpacity={.22} stroke="var(--canvas-wood)" strokeDasharray="4 3" strokeWidth={1} />}
    {opening.framing_bumper && <polygon points={opening.framing_bumper.map((point) => project(point).join(",")).join(" ")}
      fill="none" stroke={NORDIC_ACCENT} strokeDasharray="2 2" strokeWidth={1} />}
  </g>)}
  {legacyItems.map((item) => {
    const [front, back, left, right] = item.clearance_m!;
    const [x, y] = project(item.position);
    const width = (item.footprint_m[0] + left + right) * scale;
    const depth = (item.footprint_m[1] + front + back) * scale;
    return <rect key={`clearance-${item.uid}`} x={x - width / 2} y={y - depth / 2}
      width={width} height={depth} fill="var(--canvas-wood-soft)" stroke="var(--error)"
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
          <path d={`M ${size} 0 L 0 0 0 ${size}`} fill="none" stroke="var(--canvas-grid)" strokeWidth={1} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </>
  );
}

const WallShape = memo(function WallShape({ w, openings, project, selected, hovered, showFraming, onSelect, onHover }: {
  w: Wall;
  openings: Opening[];
  project: (p: Vec2) => Vec2;
  selected: boolean;
  hovered: boolean;
  showFraming: boolean;
  onSelect: (wall: Wall, event: React.MouseEvent<SVGGElement>) => void;
  onHover: (uid: string | null) => void;
}) {
  const poly = (pts: Vec2[]) => pts.map(project).map((p) => p.join(",")).join(" ");
  const stroke = selected ? NORDIC_ACCENT : hovered ? NORDIC_INK : NORDIC_LINE;
  const [axisStart, axisEnd] = w.axis;
  const axisLength = Math.hypot(axisEnd[0] - axisStart[0], axisEnd[1] - axisStart[1]) || 1;
  const wallNormal: Vec2 = [
    -(axisEnd[1] - axisStart[1]) / axisLength,
    (axisEnd[0] - axisStart[0]) / axisLength,
  ];
  const pixelsPerMeter = Math.abs(project([1, 0])[0] - project([0, 0])[0]);
  // Resolved wall layers are continuous polygons.  Punch openings out of the complete wall
  // stack before drawing their plan symbols so a thick rendered wall cannot cover a door.
  const wallThicknessPx = Math.max(8, ...w.layers.flatMap((layer) => layer.polygon.map((point) =>
    Math.abs((point[0] - axisStart[0]) * wallNormal[0] + (point[1] - axisStart[1]) * wallNormal[1])
      * pixelsPerMeter,
  )));
  const [startX, startY] = project(axisStart);
  const [endX, endY] = project(axisEnd);
  const screenAngleDeg = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
  const openingMaskId = `wall-opening-mask-${w.uid}`;
  return (
    <g onClick={(event) => onSelect(w, event)}
      onPointerEnter={() => onHover(w.uid)} onPointerLeave={() => onHover(null)}
      style={{ cursor: "pointer" }}>
      <mask id={openingMaskId} maskUnits="userSpaceOnUse">
        <rect x={-100000} y={-100000} width={200000} height={200000} fill="white" />
        {openings.map((opening) => {
          const [x, y] = project(pointAlong(w, opening.center_along_m));
          const openingWidthPx = opening.width_m * pixelsPerMeter;
          return <rect key={opening.uid} x={x - openingWidthPx / 2 - 1}
            y={y - wallThicknessPx - 1} width={openingWidthPx + 2}
            height={2 * wallThicknessPx + 2} fill="black"
            transform={`rotate(${screenAngleDeg} ${x} ${y})`} />;
        })}
      </mask>
      <g mask={`url(#${openingMaskId})`}>
        {w.layers.map((ly, i) =>
          ly.polygon.length >= 3 ? (
            <polygon key={i} points={poly(ly.polygon)} fill={materialColor(ly.material)}
              stroke="var(--panel-line)" strokeWidth={0.5} />
          ) : null,
        )}
        {showFraming && w.members.map((m) => {
          const [x0, y0] = project(m.p0);
          const [x1, y1] = project(m.p1);
          return <line key={m.key} x1={x0} y1={y0} x2={x1} y2={y1} stroke="var(--canvas-wood)"
            strokeWidth={1.5} opacity={0.85} />;
        })}
        <line x1={startX} y1={startY} x2={endX} y2={endY} stroke={stroke}
          strokeWidth={selected ? 2.5 : 1.5} strokeDasharray={w.layers.length === 0 ? "4 4" : undefined} />
      </g>
    </g>
  );
});

function hostStorey(model: Model, opening: Opening): string {
  return openingHostWall(model.walls, opening)?.storey ?? "";
}

function nearestOpeningHost(walls: Wall[], storey: string, point: Vec2):
  { wall: Wall; along_m: number; distance_m: number } | null {
  let best: { wall: Wall; along_m: number; distance_m: number } | null = null;
  for (const wall of walls) {
    if (wall.storey !== storey) continue;
    const [a, b] = wall.axis;
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const length = Math.hypot(dx, dy);
    if (length < 1e-9) continue;
    const raw = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / (length * length);
    const t = Math.max(0, Math.min(1, raw));
    const projected: Vec2 = [a[0] + t * dx, a[1] + t * dy];
    const distance_m = Math.hypot(point[0] - projected[0], point[1] - projected[1]);
    if (best === null || distance_m < best.distance_m) best = { wall, along_m: t * length, distance_m };
  }
  return best;
}

function WallAssemblyPopupCard({ wall, screen, viewport, onClose }: {
  wall: Wall;
  screen: Vec2;
  viewport: DOMRect | null;
  onClose: () => void;
}) {
  const totalThickness = wall.layers.reduce((sum, layer) => sum + layer.thickness_m, 0);
  // Keep the card in the pane even when the click is close to an edge. The CSS height cap
  // makes this conservative vertical allowance work for long assemblies on small screens.
  const left = Math.max(12, Math.min(screen[0] + 12, Math.max(12, (viewport?.width ?? 0) - 292)));
  const top = Math.max(12, Math.min(screen[1] + 12, Math.max(12, (viewport?.height ?? 0) - 372)));

  return (
    <aside className="wall-assembly-popup" style={{ left, top }} aria-label={`${wall.tag} wall assembly`}>
      <div className="wall-assembly-popup-header">
        <div>
          <div className="wall-assembly-popup-title">Wall · {wall.tag}</div>
          <div className="wall-assembly-popup-assembly">{wall.assembly || "UNCONFIGURED"}</div>
        </div>
        <button className="wall-assembly-popup-close" onClick={onClose} aria-label="Close wall assembly popup">×</button>
      </div>
      <div className="wall-assembly-popup-dimensions">
        <span><b>Length</b>{formatFtIn(wallLength(wall))}</span>
        <span><b>Height</b>{formatFtIn(wall.z1_m - wall.z0_m)}</span>
        <span><b>Thickness</b>{formatFtIn(totalThickness)}</span>
      </div>
      <div className="wall-assembly-popup-layers">
        <div className="wall-assembly-popup-layer-heading">Resolved layers</div>
        {wall.layers.length > 0 ? wall.layers.map((layer, index) => (
          <div className="layer-row" key={`${layer.name}-${index}`}>
            <span className="swatch" style={{ background: materialColor(layer.material) }} />
            <span className="wall-assembly-popup-layer-name">{layer.name}</span>
            <span>{formatFtIn(layer.thickness_m)}</span>
            <span className="wall-assembly-popup-layer-material">{layer.material}</span>
          </div>
        )) : <div className="muted">No resolved layers.</div>}
      </div>
    </aside>
  );
}

const OpeningShape = memo(function OpeningShape({ o, host, project, scale, selected, doubleLeaf, onSelect, onEdit,
  toWorld, onMove, onPreview, onPreviewEnd, preview }: {
  o: Opening;
  host: Wall;
  project: (p: Vec2) => Vec2;
  scale: number;
  selected: boolean;
  doubleLeaf?: boolean;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  onEdit: (o: Opening, screen: Vec2) => void;
  toWorld: (clientX: number, clientY: number) => Vec2;
  onMove: (opening: Opening, host: Wall, position: Vec2) => void;
  onPreview?: (opening: Opening, host: Wall, position: Vec2) => void;
  onPreviewEnd?: () => void;
  preview?: "valid" | "invalid";
}) {
  const center = pointAlong(host, o.center_along_m);
  const [cx, cy] = project(center);
  const halfPx = (o.width_m / 2) * scale;
  const [a, b] = host.axis;
  const ang = Math.atan2(-(b[1] - a[1]), b[0] - a[0]);
  const dx = Math.cos(ang) * halfPx;
  const dy = Math.sin(ang) * halfPx;
  const hingeDirection = o.flip_hinge ? -1 : 1;
  const hingeX = cx + hingeDirection * dx;
  const hingeY = cy + hingeDirection * dy;
  const swingSign = o.flip_swing ? -1 : 1;
  // SVG's y axis is inverted from plan coordinates, so the screen-space +90° normal is
  // [sin(angle), -cos(angle)].  It matches the shared drawing IR's handed plan symbol.
  const leafX = hingeX + swingSign * Math.sin(ang) * o.width_m * scale;
  const leafY = hingeY - swingSign * Math.cos(ang) * o.width_m * scale;
  const wallArcX = hingeX - hingeDirection * 2 * dx;
  const wallArcY = hingeY - hingeDirection * 2 * dy;
  const windowTick = Math.min(6, Math.max(3, scale * 0.08));
  // Press → drag vs. click discrimination (mirrors CanvasObjectFootprint): the ghost
  // preview only follows once the pointer has been captured AND moved past a small px
  // threshold, so a bare hover never drifts the symbol. A press that never crosses the
  // threshold is a click → select + open settings; one that does → commit the move.
  const downRef = useRef<Vec2 | null>(null);
  const movedRef = useRef(false);
  const DRAG_THRESHOLD_PX = 4;
  return (
    <g onDoubleClick={() => !preview && onEdit(o, [cx, cy])}
      onPointerDown={(event) => {
        if (preview) return;
        event.stopPropagation(); event.currentTarget.setPointerCapture(event.pointerId);
        downRef.current = [event.clientX, event.clientY];
        movedRef.current = false;
      }}
      onPointerMove={(event) => {
        if (preview) return;
        if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
        if (!movedRef.current && downRef.current &&
          Math.hypot(event.clientX - downRef.current[0], event.clientY - downRef.current[1]) < DRAG_THRESHOLD_PX) return;
        movedRef.current = true;
        onPreview?.(o, host, toWorld(event.clientX, event.clientY));
      }}
      onPointerUp={(event) => {
        if (preview) return;
        if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
        event.currentTarget.releasePointerCapture(event.pointerId);
        downRef.current = null;
        onPreviewEnd?.();
        if (movedRef.current) {
          const next = toWorld(event.clientX, event.clientY);
          if (Math.hypot(next[0] - center[0], next[1] - center[1]) > 0.001) onMove(o, host, next);
        } else {
          onSelect("opening", o.uid);
          onEdit(o, [cx, cy]);
        }
        movedRef.current = false;
      }}
      onPointerCancel={() => { if (!preview) { downRef.current = null; movedRef.current = false; onPreviewEnd?.(); } }}
      pointerEvents={preview ? "none" : undefined}
      opacity={preview ? .65 : 1}
      style={{ cursor: preview ? undefined : "pointer" }}>
      <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
        stroke={selected ? NORDIC_ACCENT : "var(--canvas-white)"} strokeWidth={selected ? 6 : 5} />
      <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
      stroke={o.is_door ? "var(--canvas-wood)" : NORDIC_ACCENT} strokeWidth={2}
        strokeDasharray={o.is_door ? undefined : "3 2"} />
      {o.is_door ? (doubleLeaf ? <>
        {/* French/double door — two half-width leaves hinged at the jambs, meeting at
            a centre mullion. Both leaves swing to the same side. */}
        {([-1, 1] as const).map((side) => {
          const jx = cx + side * dx;
          const jy = cy + side * dy;
          const lx = jx + swingSign * Math.sin(ang) * halfPx;
          const ly = jy - swingSign * Math.cos(ang) * halfPx;
          return (
            <g key={side}>
              <line x1={jx} y1={jy} x2={lx} y2={ly}
                stroke="var(--canvas-wood)" strokeWidth={1.5} />
              <path d={`M ${cx} ${cy} A ${halfPx} ${halfPx} 0 0 ${swingSign > 0 ? 0 : 1} ${lx} ${ly}`}
                fill="none" stroke="var(--canvas-wood)" strokeWidth={1} />
            </g>
          );
        })}
      </> : <>
        <line x1={hingeX} y1={hingeY} x2={leafX} y2={leafY}
          stroke="var(--canvas-wood)" strokeWidth={1.5} />
        <path d={`M ${wallArcX} ${wallArcY} A ${o.width_m * scale} ${o.width_m * scale} 0 0 ${swingSign > 0 ? 0 : 1} ${leafX} ${leafY}`}
          fill="none" stroke="var(--canvas-wood)" strokeWidth={1} />
      </>) : <>
        <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy}
          stroke={NORDIC_ACCENT} strokeWidth={3} />
        <line x1={cx - Math.sin(ang) * windowTick} y1={cy + Math.cos(ang) * windowTick}
          x2={cx + Math.sin(ang) * windowTick} y2={cy - Math.cos(ang) * windowTick}
          stroke="var(--canvas-white)" strokeWidth={1.2} />
        <text x={cx - Math.sin(ang) * 14} y={cy + Math.cos(ang) * 14} textAnchor="middle"
          fill={NORDIC_ACCENT} fontSize={9} fontWeight={700}
          style={{ paintOrder: "stroke", stroke: "var(--canvas-white)", strokeWidth: 3 }}>{o.tag}</text>
      </>}
      {selected && <circle cx={cx} cy={cy} r={5} fill={NORDIC_ACCENT} />}
      {preview && <circle cx={cx} cy={cy} r={Math.max(6, scale * .08)} fill="none"
        stroke={preview === "valid" ? "var(--success)" : "var(--error)"} strokeWidth={2} />}
    </g>
  );
});

const StairShape = memo(function StairShape({ stair, project, selected, hovered, onSelect, onHover }: {
  stair: Stair;
  project: (p: Vec2) => Vec2;
  selected: boolean;
  hovered: boolean;
  onSelect: (kind: Selection["kind"], uid: string) => void;
  onHover: (uid: string | null) => void;
}) {
  if (stair.outline.length < 3) return null;
  const outline = stair.outline.map(project).map((point) => point.join(",")).join(" ");
  const xs = stair.outline.map((point) => point[0]);
  const ys = stair.outline.map((point) => point[1]);
  const minX = Math.min(...xs); const maxX = Math.max(...xs);
  const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const start: Vec2 = stair.run_direction === "x"
    ? [minX, (minY + maxY) / 2] : [(minX + maxX) / 2, minY];
  const end: Vec2 = stair.run_direction === "x"
    ? [maxX, (minY + maxY) / 2] : [(minX + maxX) / 2, maxY];
  const [directionStart, directionEnd] = stair.run_reversed ? [end, start] : [start, end];
  const [labelX, labelY] = project([(minX + maxX) / 2, (minY + maxY) / 2]);
  const stroke = selected ? NORDIC_ACCENT : hovered ? NORDIC_INK : "var(--canvas-wood)";
  const [arrowStartX, arrowStartY] = project(directionStart);
  const [arrowEndX, arrowEndY] = project(directionEnd);
  return <g onClick={() => onSelect("stair", stair.uid)}
    onPointerEnter={() => onHover(stair.uid)} onPointerLeave={() => onHover(null)}
    style={{ cursor: "pointer" }}>
    <polygon points={outline} fill="var(--canvas-wood-soft)" stroke={stroke}
      strokeWidth={selected ? 2.5 : 1.25} />
    {stair.members.filter((member) => member.category === "tread" || member.category === "winder" || member.category === "landing").map((member) => {
      const [x0, y0] = project(member.p0); const [x1, y1] = project(member.p1);
      return <line key={member.key} x1={x0} y1={y0} x2={x1} y2={y1} stroke={stroke} strokeWidth={1} />;
    })}
    <line x1={arrowStartX} y1={arrowStartY} x2={arrowEndX} y2={arrowEndY} stroke={stroke}
      strokeWidth={1.5} markerEnd="url(#stair-arrow)" />
    <text x={labelX} y={labelY - 5} textAnchor="middle" fontSize={10} fill={stroke}
      style={{ paintOrder: "stroke" }} stroke="var(--canvas-white)" strokeWidth={3}>UP {stair.riser_count} R</text>
  </g>;
});

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
    <div className="hud" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
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

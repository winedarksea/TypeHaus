import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStore } from "../state/store";
import { locateUid } from "../state/locate";
import type { PreviewGeometry } from "../engine/EngineClient";
import type { Opening, Room, Vec2, Wall } from "../model/types";
import { canvasObjectTrade } from "../model/visibility";
import type { PlanWarningMarker } from "../model/planWarnings";
import {
  formatFtIn, M_PER_FT, openingHostWall, snapWorld, orthoLock, wallLength,
} from "../model/geometry";
import { SunIndicator } from "./SunIndicator";
import { ZoomControls } from "./ZoomControls";
import { BackgroundGrid, nodeTagMatches } from "./plan/PlanChrome";
import { CanvasHud } from "./plan/CanvasHud";
import { CanvasObjectFootprint, ClearanceOverlays, NodeHandle } from "./plan/ObjectShapes";
import { WallDimension, WallShape } from "./plan/WallShapes";
import { OpeningShape, StairShape } from "./plan/OpeningShapes";
import {
  DetailMarkerLayer, PlanNodesLayer, RailingOutlines, RoomLayer, SlabOutlines, WallDraftLayer,
  WarningMarkerLayer,
} from "./plan/PlanMarkers";
import { CanvasOverlays } from "./plan/CanvasOverlays";
import { useCanvasInteractions } from "./plan/useCanvasInteractions";
import { useStoreySlice } from "./plan/useStoreySlice";
import { usePanZoom } from "./plan/usePanZoom";
import { dispatchTap } from "./plan/toolDispatch";
import type {
  DoorPopup, LengthEntry, MeasureDraft, NodeDrag, OpeningDragPreview, Pending, Placement,
  WallAssemblyPopup, WallDraft,
} from "./plan/canvasTypes";

// The SVG floorplan editor (→ 21 §Stack: SVG editor). Renders model.json faithfully and
// hosts the full authoring loop: draw walls (rubber-band, node/grid snap, ortho, polyline
// chaining), stretch nodes, drive a wall's length, place openings + claim rooms, split/heal,
// and delete — every edit lands as a journaled macro/patch that round-trips through rebuild.
// Points are projected in JS (crisp strokes, upright text) rather than via an SVG transform.
//
// Split along its documented seams (→ plan/): the local vocabulary in canvasTypes.ts, the
// stable element handlers in useCanvasInteractions.ts, the per-storey memos in
// useStoreySlice.ts, gesture bookkeeping in usePanZoom.ts, the tap routing in toolDispatch.ts,
// the non-element SVG layers in PlanMarkers.tsx and the popover stack in CanvasOverlays.tsx.
// This file keeps the gesture state, the commits, and the element render passes.

// One shared empty list for walls with no openings, so those walls also keep a stable
// `openings` reference across renders (a fresh `[]` would defeat WallShape's memo()).
const NO_OPENINGS: Opening[] = [];

export function Canvas2D() {
  const model = useStore((s) => s.model)!;
  const view = useStore((s) => s.view);
  const selection = useStore((s) => s.selection);
  const select = useStore((s) => s.select);
  const hoverUid = useStore((s) => s.hoverUid);
  const showFraming = useStore((s) => s.showFraming);
  const labelMode = useStore((s) => s.labelMode);
  // The plan reads the same visibility model the 3D panel does (→ model/visibility.ts), so a
  // discipline or an assembly layer hidden in one view is hidden in the other.
  const visibleTrades = useStore((s) => s.visibleTrades);
  const visibleLayerGroups = useStore((s) => s.visibleLayerGroups);
  const activeLens = useStore((s) => s.activeLens);
  const activeStorey = useStore((s) => s.activeStorey);
  const workspace = useStore((s) => s.activeWorkspace);
  const tool = useStore((s) => s.tool);
  const runMacro = useStore((s) => s.runMacro);
  const previewMacro = useStore((s) => s.previewMacro);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const duplicateSelection = useStore((s) => s.duplicateSelection);
  const offline = useStore((s) => s.offline);
  const toast = useStore((s) => s.toast);

  const svgRef = useRef<SVGSVGElement>(null);
  const shift = useRef(false);
  // Latest draft + rubber-band, mirrored into refs so the global keydown handler can open the
  // exact-length keypad without re-subscribing on every pointer move.
  const draftRef = useRef<WallDraft | null>(null);
  const rubberRef = useRef<{ end: Vec2; len: number } | null>(null);
  const lengthEntryOpen = useRef(false);
  const healNodeRef = useRef<(tag: string) => Promise<void>>(async () => {});
  const [pending, setPending] = useState<Pending | null>(null);
  const [draft, setDraft] = useState<WallDraft | null>(null);
  const [measure, setMeasure] = useState<MeasureDraft | null>(null); // read-only two-tap tape
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
  const [warningPopup, setWarningPopup] = useState<{ marker: PlanWarningMarker; screen: Vec2 } | null>(null);
  const [doorPopup, setDoorPopup] = useState<DoorPopup | null>(null);
  const [windowPopup, setWindowPopup] = useState<DoorPopup | null>(null);
  const [dimWall, setDimWall] = useState<Wall | null>(null);
  const [lengthEntry, setLengthEntry] = useState<LengthEntry | null>(null);
  // Desktop-first right-click context menu (Phase 10), anchored in pane coordinates.
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number } | null>(null);
  const drawAssembly = useStore((s) => s.drawAssembly) ?? "";
  const setDrawAssembly = useStore((s) => s.setDrawAssembly);
  const [activeService, setActiveService] = useState<string>("");
  const [showClearances, setShowClearances] = useState(false);

  const {
    project, unproject, selectEl, hoverEl, editOpeningStable, movePlaceableFromDrag,
    rotatePlaceableFromHandle, moveOpeningFromDrag, previewOpeningFromDrag, selectWallWithPopup,
  } = useCanvasInteractions({
    svgRef, setDoorPopup, setWindowPopup, setOpeningDragPreview, setWallAssemblyPopup,
  });

  const tolM = 12 / view.scale;
  const gridM = view.scale * M_PER_FT >= 14 ? M_PER_FT : null;
  const fmt = (m: number) => formatFtIn(m);

  const {
    wallsOnStorey, nodes, openEnds, storeyNodes, stairsOnStorey, slabsOnStorey, railingsOnStorey,
    snapNodes,
    defaultAssembly, serviceOptions, canvasTypes, warningMarkers, nearestNodeTag, storeyHintFile,
  } = useStoreySlice(model, activeStorey, tolM);
  const wallAssembly = drawAssembly || defaultAssembly;

  const visibleServiceObjects = useMemo(() => (model.canvas_objects ?? []).filter((item) =>
    item.position_m && (!activeStorey || item.storey === activeStorey) &&
    (!activeService || (item.type ? canvasTypes.get(item.type)?.ports.some((port) => port.service === activeService) : false))),
  [model.canvas_objects, activeStorey, activeService, canvasTypes]);

  // Openings indexed by host wall tag. Two reasons, both about the wall pass below. The scan it
  // replaces was O(walls x openings) per render, and — the one that actually cost frames — it
  // allocated a fresh array per wall, so WallShape's memo() comparator missed on every render
  // and every wall in the storey re-drew its layer polygons whenever a hover moved.
  //
  // The in-flight opening drag is folded in here rather than at the call site so the host wall
  // still gets one stable array: the dragged opening is drawn at its preview position, not its
  // committed one.
  const openingsByHost = useMemo(() => {
    const byHost = new Map<string, Opening[]>();
    for (const opening of model.openings) {
      if (opening.uid === openingDragPreview?.opening.uid) continue;
      const hosted = byHost.get(opening.host);
      if (hosted) hosted.push(opening);
      else byHost.set(opening.host, [opening]);
    }
    if (openingDragPreview) {
      const host = openingDragPreview.host.tag;
      byHost.set(host, [...(byHost.get(host) ?? []), openingDragPreview.opening]);
    }
    return byHost;
  }, [model.openings, openingDragPreview]);

  const roomsOnStorey = useMemo(
    () => model.rooms.filter((r) => !activeStorey || r.storey === activeStorey),
    [model.rooms, activeStorey],
  );
  const footprintObjects = useMemo(() => (model.canvas_objects ?? [])
    // Doors/windows remain topology-aware SVG shapes below; their normalized records
    // serve inspection/interchange consumers and must not render a second footprint.
    .filter((item) => item.domain !== "opening" && item.position_m &&
      visibleTrades[canvasObjectTrade(item)] &&
      (!activeStorey || item.storey === activeStorey)),
  [model.canvas_objects, visibleTrades, activeStorey]);
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

  // A popover outlives neither its marker nor the storey it belongs to.
  useEffect(() => {
    if (warningPopup && !warningMarkers.some((marker) => marker.key === warningPopup.marker.key)) {
      setWarningPopup(null);
    }
  }, [warningMarkers, warningPopup]);

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

  // Default-then-refine stair placement: the resolver owns the run geometry, so a click just
  // seeds a straight stair up to the next storey, then selects it so the Inspector opens the
  // stair designer for immediate refinement (mirrors the room tool's minted-then-select flow).
  const commitStair = async (seed: Vec2) => {
    if (!activeStorey) return;
    // The stair + its FloorOpening live in the *upper* storey's lists (a stair from basement→main
    // is authored in main's file), so target that storey explicitly and pin its editable file —
    // otherwise the coordinator would route to whichever file merely has a STAIRS list.
    const here = model.storeys.find((s) => s.tag === activeStorey);
    const above = here
      ? model.storeys
          .filter((s) => s.elevation_m > here.elevation_m + 1e-6)
          .sort((a, b) => a.elevation_m - b.elevation_m)[0]
      : undefined;
    if (!above) { toast("No storey above this level for a stair", "error"); return; }
    const upperFile = model.walls.find((w) => w.storey === above.tag && w.provenance?.editable)?.provenance?.file;
    const res = await runMacro({
      macro: "place_stair", storey: activeStorey, to_storey: above.tag,
      seed: [fmt(seed[0]), fmt(seed[1])], hint_file: upperFile ?? undefined,
    });
    if (!res) return;
    const entry = Object.entries(res.minted).find(([tag]) => tag.startsWith("ST-"));
    if (entry) select("stair", entry[1]);
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

  // --- gesture pre-emption (→ W7b) ------------------------------------------
  // An edit that can't be written back already fails synchronously on commit, but only after
  // the user has dragged the thing across the canvas. These two screens refuse it up front.

  // Screen 1, free: the loader told us this element's authoring statement isn't in a
  // `# haus: editable` file. `editable === null` means "no provenance captured" — unknown, not
  // forbidden, so it falls through to the server rehearsal rather than blocking the gesture.
  const refuseIfNotEditable = (uid: string): boolean => {
    const located = locateUid(model, uid);
    if (!located || located.editable !== false) return false;
    toast(`${located.tag} is params-generated — edit ${located.source ?? "its source"} instead`,
      "error");
    return true;
  };

  // Note this screens the *selected* element, which for a node drag is the wall, not the node
  // being moved — nodes carry no uid the model indexes. That is a heuristic (a wall and its
  // nodes are authored together in practice), which is exactly why screen 2 below exists: the
  // rehearsal routes the real op and is the authoritative answer.
  //
  // Screen 2, one round trip: ask the server to rehearse routing for the edit this gesture
  // will eventually commit (a zero-delta move: same ops, no movement). Fired once at
  // drag-start — can_route re-reads every editable file, far too heavy per pointermove.
  const rehearseNodeDrag = async (tag: string) => {
    if (!activeStorey) return;
    const verdict = await previewMacro(
      { macro: "move_nodes", storey: activeStorey, nodes: [tag], dx: 0, dy: 0 }, true);
    // previewMacro toasts the server's reason; cancelling the in-flight drag is ours to do.
    if (verdict === "refused") { setNodeDrag(null); setPreviewGeom(null); }
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
  // Read through a ref so PlanNodesLayer's `onHeal` can be identity-stable while healNode
  // itself stays a plain closure over the live storey/macro runner.
  healNodeRef.current = healNode;

  // Identity-stable props for the memo()'d layers below (→ plan/PlanMarkers.tsx). Written out
  // rather than inlined in the JSX because an inline arrow is a new function every render,
  // which is exactly the reference miss the memo() is there to avoid.
  const selectRoom = useCallback((room: Room) => select("room", room.uid), [select]);
  const selectWall = useCallback((wall: Wall) => select("wall", wall.uid), [select]);
  const healNodeStable = useCallback((tag: string) => { void healNodeRef.current(tag); }, []);
  const openWarningPopup = useCallback((marker: PlanWarningMarker, event: React.MouseEvent) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    setWarningPopup({ marker, screen: [event.clientX - rect.left, event.clientY - rect.top] });
  }, []);

  // ---- tool tap dispatch (→ plan/toolDispatch.ts) ----------------------------
  const handleTap = (world: Vec2, screen: Vec2) => dispatchTap({
    tool, offline, scale: view.scale, placement, draft, measure, shiftRef: shift, wallsOnStorey,
    stairsOnStorey, warningMarkers, snapNodes, tolM, gridM, activeStorey, project, select,
    toast, setPlacement, setDraft, setMeasure, setDimWall, setWallAssemblyPopup, setWarningPopup,
    setDoorPopup, setWindowPopup, commitWall, commitStair,
  }, world, screen);

  const { zoomBy, onPointerDown, onPointerMove, onPointerUp, onClickCapture } = usePanZoom({
    svgRef, model, activeStorey, wallsOnStorey, unproject, onTap: handleTap,
    shiftRef: shift, setCursor,
  });

  // ---- keyboard: Esc cancels the in-flight gesture, Delete removes selection --
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA")) return;
      if (e.key === "Escape") {
        setDraft(null); setMeasure(null); setPlacement(null); setWallAssemblyPopup(null); setDimWall(null); setNodeDrag(null); setPending(null); setDoorPopup(null); setWindowPopup(null);
        setPreviewGeom(null); setLengthEntry(null); setWarningPopup(null);
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
  // Measurements are scratch, not model state: drop them when the tape is put away.
  useEffect(() => { if (tool !== "measure") setMeasure(null); }, [tool]);

  // Mirror the in-flight draw gesture into the store so the ContextBar / interaction-state
  // label and App's Esc hierarchy (Phase 2) can see it.
  const setSubOperation = useStore((s) => s.setSubOperation);
  useEffect(() => { setSubOperation(draft != null); }, [draft, setSubOperation]);

  // Live rubber-band endpoint (snapped, ortho-locked under shift).
  const rubber = useMemo(() => {
    if (tool !== "wall" || !draft || !cursor) return null;
    const snap = snapWorld(cursor, snapNodes, tolM, gridM);
    const end = shift.current ? orthoLock(draft.start, snap.point) : snap.point;
    return { end, len: Math.hypot(end[0] - draft.start[0], end[1] - draft.start[1]) };
  }, [tool, draft, cursor, snapNodes, tolM, gridM]);
  // The measured endpoint: the fixed second tap once there is one, otherwise the live cursor
  // under the same snap + ortho rules the first tap used.
  const measureEnd = useMemo(() => {
    if (tool !== "measure" || !measure) return null;
    if (measure.end) return measure.end;
    if (!cursor) return null;
    const snap = snapWorld(cursor, snapNodes, tolM, gridM);
    return shift.current ? orthoLock(measure.start, snap.point) : snap.point;
  }, [tool, measure, cursor, snapNodes, tolM, gridM]);

  draftRef.current = draft;
  rubberRef.current = rubber;
  lengthEntryOpen.current = lengthEntry != null;

  const cursorClass = tool === "select" ? "" : "canvas-draw";

  return (
    <>
      <svg
        ref={svgRef}
        className={`canvas-svg ${cursorClass}`}
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
        {/* resolved slabs first: the concrete plate everything on this storey stands on */}
        {visibleTrades.concrete && <SlabOutlines slabs={slabsOnStorey} project={project} />}
        {/* rooms next (tinted fills, behind walls; → plan/PlanMarkers.tsx::RoomLayer) */}
        <RoomLayer rooms={roomsOnStorey}
          previewGeom={previewGeom} tool={tool} labelMode={labelMode}
          project={project} onSelect={selectRoom} />
        {/* walls — likewise shown at their previewed axis (tag-matched) while a node drag is
            in flight, so connected walls visibly stretch/shrink before the commit lands */}
        {(visibleTrades.walls || visibleTrades.framing) && wallsOnStorey.map((w) => {
          const previewAxis = previewGeom?.walls.find((x) => x.tag === w.tag)?.axis;
          const displayWall = previewAxis ? { ...w, axis: previewAxis as [Vec2, Vec2] } : w;
          return (
            <WallShape
              key={w.uid}
              w={displayWall}
              openings={openingsByHost.get(w.tag) ?? NO_OPENINGS}
              project={project}
              selected={selection.uid === w.uid}
              hovered={hoverUid === w.uid}
              showFraming={showFraming && visibleTrades.framing}
              showLayers={visibleTrades.walls}
              visibleLayerGroups={visibleLayerGroups}
              activeLens={activeLens}
              onSelect={selectWallWithPopup}
              onHover={hoverEl}
            />
          );
        })}
        {/* openings */}
        {visibleTrades.openings && model.openings.map((o) => {
          const host = openingHostWall(model.walls, o);
          if (!host || (activeStorey && host.storey !== activeStorey)) return null;
          // Both kinds carry an operation now: it picks the door's swing/track glyph and,
          // for a window, the sash tick that separates an operable unit from a picture one.
          const operation = o.is_door
            ? model.catalog?.door_types.find((dt) => dt.tag === o.type_ref)?.operation
            : model.catalog?.window_types.find((wt) => wt.tag === o.type_ref)?.operation;
          return (
            <OpeningShape
              key={o.uid}
              o={o}
              host={host}
              project={project}
              scale={view.scale}
              selected={selection.uid === o.uid}
              operation={operation}
              labelMode={labelMode}
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
        {visibleTrades.stairs && stairsOnStorey
          .map((stair) => <StairShape key={stair.uid} stair={stair} project={project}
            selected={selection.uid === stair.uid} hovered={hoverUid === stair.uid}
            labelMode={labelMode} onSelect={selectEl} onHover={hoverEl} />)}
        {/* guards over the stair wells and open edges, drawn on top of the flight they
            protect. Gated on `stairs`, which is where a `railing` solid lands in the 3D viewer
            (three/solidMaterials.ts::SOLID_CATEGORY_TRADE), so the toggle behaves the same in
            both viewers rather than the plan inventing its own grouping. These two move
            together: re-home the category and this gate goes with it. It was `concrete` for as
            long as the railing category rode the concrete fallback. */}
        {visibleTrades.stairs && <RailingOutlines railings={railingsOnStorey} project={project} />}
        {footprintObjects
          .map((item) => <CanvasObjectFootprint key={item.uid} item={item}
            type={item.type ? canvasTypes.get(item.type) : undefined} project={project} scale={view.scale}
            walls={wallsOnStorey}
            selected={selection.uid === item.uid} labelMode={labelMode} onSelect={selectEl} toWorld={unproject}
            onMove={movePlaceableFromDrag} onRotate={rotatePlaceableFromHandle} />)}
        {showClearances && <ClearanceOverlays model={model} storey={activeStorey} project={project}
          scale={view.scale} />}
        <PlanNodesLayer nodes={nodes} openEnds={openEnds} model={model} tool={tool}
          project={project} nearestNodeTag={nearestNodeTag} onHeal={healNodeStable} />
        <WarningMarkerLayer markers={warningMarkers} activeKey={warningPopup?.marker.key ?? null}
          project={project} onOpen={openWarningPopup} />
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
                if (!tag || refuseIfNotEditable(selection.uid!)) return;
                setNodeDrag({ tag, from: p, to: p });
                void rehearseNodeDrag(tag); // may cancel the drag a beat later
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
                  }).then((geom) => { if (geom && geom !== "refused") setPreviewGeom(geom); });
                }
                return { ...d, to };
              })}
              onEnd={() => setNodeDrag((d) => { if (d) void commitNodeDrag(d); return null; })}
            />
          ));
        })()}
        {tool === "wall" && <WallDraftLayer draft={draft} rubber={rubber} cursor={cursor}
          snapNodes={snapNodes} tolM={tolM} gridM={gridM} project={project} />}
        {workspace === "document" && <DetailMarkerLayer model={model} activeStorey={activeStorey}
          project={project} onSelectWall={selectWall} />}
        {/* measure tape: a scratch two-tap segment, dual-unit readout, never written back */}
        {measure && measureEnd && (() => {
          const [sx, sy] = project(measure.start);
          const [ex, ey] = project(measureEnd);
          const d_m = Math.hypot(measureEnd[0] - measure.start[0], measureEnd[1] - measure.start[1]);
          return (
            <g pointerEvents="none">
              <line x1={sx} y1={sy} x2={ex} y2={ey} stroke="var(--canvas-ink)" strokeWidth={1.5}
                strokeDasharray={measure.end ? undefined : "5 4"} />
              <circle cx={sx} cy={sy} r={4} fill="var(--canvas-white)" stroke="var(--canvas-ink)" strokeWidth={1.5} />
              <circle cx={ex} cy={ey} r={4} fill="var(--canvas-white)" stroke="var(--canvas-ink)" strokeWidth={1.5} />
              {d_m > 0.001 && (
                <text x={(sx + ex) / 2} y={(sy + ey) / 2 - 8} fill="var(--canvas-ink)" fontSize={12}
                  textAnchor="middle" style={{ paintOrder: "stroke" }}
                  stroke="var(--canvas-white)" strokeWidth={3}>
                  {`${formatFtIn(d_m)} / ${d_m.toFixed(2)} m`}
                </text>
              )}
            </g>
          );
        })()}
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
            selected={selection.uid === item.uid} labelMode={labelMode} onSelect={selectEl} toWorld={unproject}
            onMove={movePlaceableFromDrag} onRotate={rotatePlaceableFromHandle} />)}
        </>}
      </svg>
      <CanvasOverlays
        svgRef={svgRef}
        pending={pending} setPending={setPending}
        doorPopup={doorPopup} setDoorPopup={setDoorPopup}
        windowPopup={windowPopup} setWindowPopup={setWindowPopup}
        dimWall={dimWall} setDimWall={setDimWall} onCommitDim={(m) => void commitDim(m)}
        lengthEntry={lengthEntry} setLengthEntry={setLengthEntry}
        onCommitWall={(start, end) => void commitWall(start, end)}
        placement={placement} setPlacement={setPlacement} hintFile={storeyHintFile()}
        wallAssemblyPopup={wallAssemblyPopup} setWallAssemblyPopup={setWallAssemblyPopup}
        popupWall={popupWall}
        warningPopup={warningPopup} setWarningPopup={setWarningPopup}
        ctxMenu={ctxMenu} setCtxMenu={setCtxMenu}
      />
      {/* The plan's bottom-*left* is the extents card, so its zoom stacks over the sun chip on
          the right instead — one cluster, so neither has to know the other's height. */}
      <div className="canvas-nav-controls side">
        <ZoomControls label="Plan zoom" onZoom={zoomBy} />
        <SunIndicator model={model} />
      </div>
      <CanvasHud model={model} serviceOptions={serviceOptions}
        activeService={activeService} setActiveService={setActiveService}
        showClearances={showClearances} setShowClearances={setShowClearances}
        tool={tool} draft={Boolean(draft)} wallAssembly={wallAssembly}
        onAssembly={setDrawAssembly}
        onSplit={selection.kind === "wall" ? () => {
          const w = wallsOnStorey.find((x) => x.uid === selection.uid);
          if (w) void splitWall(w);
        } : null} />
    </>
  );
}

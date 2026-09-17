// The selected wall's two endpoint handles (stretch → move_nodes), with the gesture
// pre-emption that refuses an edit that could never be written back. Split from
// components/Canvas2D.tsx, which keeps the drag and preview state these write into.
import { useRef, useState } from "react";
import type { PreviewGeometry } from "../../engine/EngineClient";
import type { Model, PlanNode, Vec2, Wall } from "../../model/types";
import { snapWorld, type Node as GeoNode } from "../../model/geometry";
import { locateUid } from "../../state/locate";
import { useStore } from "../../state/store";
import { NodeHandle } from "./ObjectShapes";
import { nodeTagMatches } from "./PlanChrome";
import { TAP_PX, type NodeDrag } from "./canvasTypes";
import { WallBodyHandle } from "./WallBodyHandle";
import { bodySpans, offsetDelta, perpendicularOffset, snapOffset } from "./wallDrag";

interface BodyDrag { nodes: [string, string]; from: Vec2; downPx: Vec2; offset: number; moved: boolean }

export function WallNodeHandles({
  wall, model, activeStorey, nodeDrag, setNodeDrag, setPreviewGeom, storeyNodes, snapNodes, tolM, gridM,
  project, unproject, nearestNodeTag,
}: {
  wall: Wall;
  model: Model;
  activeStorey: string | null;
  nodeDrag: NodeDrag | null;
  setNodeDrag: (update: NodeDrag | null | ((drag: NodeDrag | null) => NodeDrag | null)) => void;
  setPreviewGeom: (geom: PreviewGeometry | null) => void;
  storeyNodes: PlanNode[];
  snapNodes: Map<string, GeoNode>;
  tolM: number;
  gridM: number | null;
  project: (p: Vec2) => Vec2;
  unproject: (clientX: number, clientY: number) => Vec2;
  nearestNodeTag: (p: Vec2) => string | null;
}) {
  const previewMacro = useStore((s) => s.previewMacro);
  const runMacro = useStore((s) => s.runMacro);
  const toast = useStore((s) => s.toast);

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

  // --- wall-body drag (P5): both nodes along the wall normal; pinned ends hold server-side --
  const bodyDrag = useRef<BodyDrag | null>(null);
  const [bodyOffset, setBodyOffset] = useState(0);
  const endBodyDrag = () => { bodyDrag.current = null; setBodyOffset(0); };
  const onBodyStart = (clientX: number, clientY: number) => {
    const a = nearestNodeTag(wall.axis[0]);
    const b = nearestNodeTag(wall.axis[1]);
    if (!a || !b || !activeStorey || refuseIfNotEditable(wall.uid)) return;
    bodyDrag.current = { nodes: [a, b], from: unproject(clientX, clientY), downPx: [clientX, clientY],
      offset: 0, moved: false };
    void previewMacro({ macro: "move_nodes", storey: activeStorey, nodes: [a, b], dx: 0, dy: 0 }, true)
      .then((verdict) => { if (verdict === "refused") { endBodyDrag(); setPreviewGeom(null); } });
  };
  const onBodyMove = (clientX: number, clientY: number) => {
    const d = bodyDrag.current;
    if (!d || !activeStorey) return;
    if (!d.moved && Math.hypot(clientX - d.downPx[0], clientY - d.downPx[1]) < TAP_PX) return;
    d.moved = true;
    const offset = snapOffset(perpendicularOffset(wall.axis, d.from, unproject(clientX, clientY)), gridM);
    if (offset === d.offset) return;
    d.offset = offset;
    setBodyOffset(offset);
    const [dx, dy] = offsetDelta(wall.axis, offset);
    void previewMacro({ macro: "move_nodes", storey: activeStorey, nodes: d.nodes, dx, dy })
      .then((geom) => { if (bodyDrag.current === d && geom && geom !== "refused") setPreviewGeom(geom); });
  };
  const onBodyEnd = () => {
    const d = bodyDrag.current;
    endBodyDrag();
    setPreviewGeom(null); // the commit's reload supersedes the preview
    if (!d || !d.moved || d.offset === 0 || !activeStorey) return; // a tap is a no-op
    const [dx, dy] = offsetDelta(wall.axis, d.offset);
    void runMacro({ macro: "move_nodes", storey: activeStorey, nodes: d.nodes, dx, dy });
  };
  const [shiftX, shiftY] = offsetDelta(wall.axis, bodyOffset);
  const bodyAxis: [Vec2, Vec2] = [[wall.axis[0][0] + shiftX, wall.axis[0][1] + shiftY],
    [wall.axis[1][0] + shiftX, wall.axis[1][1] + shiftY]];
  const len = Math.hypot(wall.axis[1][0] - wall.axis[0][0], wall.axis[1][1] - wall.axis[0][1]);

  return <>{!nodeDrag && <WallBodyHandle axis={bodyAxis} project={project}
    spans={bodySpans(len, model.openings.filter((o) => o.host === wall.tag))}
    onStart={onBodyStart} onMove={onBodyMove} onEnd={onBodyEnd} />}
  {wall.axis.map((p, i) => (
    <NodeHandle
      key={i}
      world={nodeDrag && nodeTagMatches(nodeDrag.tag, p, storeyNodes) ? nodeDrag.to : p}
      project={project}
      onStart={() => {
        const tag = nearestNodeTag(p);
        if (!tag || refuseIfNotEditable(wall.uid)) return;
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
  ))}</>;
}

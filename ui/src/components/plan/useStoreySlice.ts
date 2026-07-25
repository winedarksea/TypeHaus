// The active-storey slice of the model: every memoized derivation the SVG floorplan draws
// from, plus the plan-warning marker set and the node/file lookups the macros need. Split
// from components/Canvas2D.tsx along its documented seam — everything here is a pure
// function of (model, activeStorey, view scale); no gesture state, no popovers.
import { useCallback, useMemo } from "react";
import type { CanvasObjectType, Model, PlanNode, Solid, Stair, Vec2, Wall } from "../../model/types";
import {
  junctionDiagnosticMarkers,
  openEndMarker,
  type PlanWarningMarker,
} from "../../model/planWarnings";
import { deriveNodes, type Node as GeoNode } from "../../model/geometry";
import { openEndKeys } from "./PlanChrome";

export interface StoreySlice {
  wallsOnStorey: Wall[];
  nodes: Map<string, GeoNode>;
  openEnds: Set<string>;
  storeyNodes: PlanNode[];
  stairsOnStorey: Stair[];
  slabsOnStorey: Solid[];
  snapNodes: Map<string, GeoNode>;
  defaultAssembly: string;
  serviceOptions: string[];
  canvasTypes: Map<string, CanvasObjectType>;
  warningMarkers: PlanWarningMarker[];
  nearestNodeTag: (p: Vec2) => string | null;
  storeyHintFile: () => string | undefined;
}

export function useStoreySlice(model: Model, activeStorey: string | null, tolM: number): StoreySlice {
  const wallsOnStorey = useMemo(
    () => model.walls.filter((w) => !activeStorey || w.storey === activeStorey),
    [model.walls, activeStorey],
  );
  // Node markers are view-local: deriving them from every storey makes unrelated
  // endpoints appear on the active floorplan when storeys share coordinates.
  const nodes = useMemo(() => deriveNodes(wallsOnStorey), [wallsOnStorey]);
  const openEnds = useMemo(() => openEndKeys(wallsOnStorey), [wallsOnStorey]);
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
  // Resolved slabs on the active storey, drawn as concrete outlines under the walls — the
  // plan's mirror of the sheet emitters' slab pass (emit/draw/foundationplan.py::_emit_slabs).
  const slabsOnStorey = useMemo(
    () => (model.solids ?? []).filter((solid) => solid.category === "slab" &&
      (!activeStorey || solid.storey === activeStorey) && solid.outline.length >= 3),
    [model.solids, activeStorey],
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

  const serviceOptions = useMemo(() => [...new Set((model.catalog?.canvas_object_types ?? [])
    .flatMap((type) => type.ports.map((port) => port.service)))].sort(), [model.catalog?.canvas_object_types]);
  const canvasTypes = useMemo(() => new Map((model.catalog?.canvas_object_types ?? [])
    .map((item) => [item.tag, item])), [model.catalog?.canvas_object_types]);

  // Every plan marker that carries a diagnostic: unjoined wall ends (derived from the drawn
  // wall graph, so the marker set matches exactly what the canvas paints) plus any junction the
  // resolver annotated. `tolM` is the same node tolerance the snap/heal affordances use.
  const warningMarkers = useMemo(() => {
    const wallByUid = new Map(wallsOnStorey.map((wall) => [wall.uid, wall]));
    return [
      ...[...nodes.values()].filter((node) => openEnds.has(node.id)).map((node) =>
        openEndMarker(model, activeStorey, node.p,
          node.walls.map((uid) => wallByUid.get(uid)).filter((wall): wall is Wall => wall != null),
          tolM)),
      ...junctionDiagnosticMarkers(model, activeStorey),
    ];
  }, [model, activeStorey, nodes, openEnds, wallsOnStorey, tolM]);

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
    // Only *editable* provenance may route adds — a params-generated node's file would
    // send the coordinator to a file writeback can't touch.
    () => storeyNodes.find((n) => n.provenance?.editable)?.provenance?.file
      ?? wallsOnStorey.find((w) => w.provenance?.editable)?.provenance?.file,
    [storeyNodes, wallsOnStorey],
  );

  return {
    wallsOnStorey, nodes, openEnds, storeyNodes, stairsOnStorey, slabsOnStorey, snapNodes,
    defaultAssembly, serviceOptions, canvasTypes, warningMarkers, nearestNodeTag, storeyHintFile,
  };
}

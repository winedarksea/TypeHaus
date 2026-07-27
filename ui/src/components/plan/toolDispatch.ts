// What a tap means under each tool: the Canvas2D tap dispatcher, split out along its
// documented seam. Pure dispatch — every commit and every piece of gesture state is handed
// in through `TapDeps`, so this module owns the routing (marker > wall > stair under the
// select tool; snap/ortho under the wall and measure tools; placement popovers; the dimension
// pick) and nothing else.
import type { MutableRefObject } from "react";
import type { PlanWarningMarker } from "../../model/planWarnings";
import type { Stair, Vec2, Wall } from "../../model/types";
import type { Node as GeoNode } from "../../model/geometry";
import { nearestWallHit, orthoLock, snapWorld } from "../../model/geometry";
import type { Selection, Tool } from "../../state/vocabulary";
import { pointInPolygon } from "./OpeningShapes";
import {
  HIT_PX, WARNING_MARKER_HIT_PX,
  type DoorPopup, type MeasureDraft, type Placement, type WallAssemblyPopup, type WallDraft,
} from "./canvasTypes";

export interface TapDeps {
  tool: Tool;
  offline: boolean;
  scale: number; // view.scale, for screen-px hit tests
  placement: Placement | null;
  draft: WallDraft | null;
  measure: MeasureDraft | null;
  shiftRef: MutableRefObject<boolean>;
  wallsOnStorey: Wall[];
  stairsOnStorey: Stair[];
  warningMarkers: PlanWarningMarker[];
  snapNodes: Map<string, GeoNode>;
  tolM: number;
  gridM: number | null;
  activeStorey: string | null;
  project: (p: Vec2) => Vec2;
  select: (kind: Selection["kind"], uid: string | null) => void;
  toast: (message: string, kind?: "info" | "error") => void;
  setPlacement: (placement: Placement | null) => void;
  setDraft: (draft: WallDraft | null) => void;
  setMeasure: (measure: MeasureDraft | null) => void;
  setDimWall: (wall: Wall | null) => void;
  setWallAssemblyPopup: (popup: WallAssemblyPopup | null) => void;
  setWarningPopup: (popup: { marker: PlanWarningMarker; screen: Vec2 } | null) => void;
  setDoorPopup: (popup: DoorPopup | null) => void;
  setWindowPopup: (popup: DoorPopup | null) => void;
  commitWall: (start: Vec2, end: Vec2) => Promise<void>;
  commitStair: (seed: Vec2) => Promise<void>;
}

export function dispatchTap(deps: TapDeps, world: Vec2, screen: Vec2): void {
  const {
    tool, offline, scale, placement, draft, measure, shiftRef, wallsOnStorey, stairsOnStorey,
    warningMarkers, snapNodes, tolM, gridM, activeStorey, project, select, toast,
    setPlacement, setDraft, setMeasure, setDimWall, setWallAssemblyPopup, setWarningPopup,
    setDoorPopup, setWindowPopup, commitWall, commitStair,
  } = deps;
  if (placement) { setPlacement(null); return; }
  // Measure is read-only (nothing is journaled), so it survives offline alongside select.
  if (offline && tool !== "select" && tool !== "measure") { toast("Editing needs the server (offline)", "error"); return; }
  switch (tool) {
    case "select": {
      // Diagnostic markers win the tap. They sit on top of the walls they annotate, and the
      // whole point of them is to be answerable — resolving them here (rather than trusting
      // the per-<g> click) is what actually makes them clickable under pointer capture.
      const markerHit = warningMarkers.find((marker) => {
        const [mx, my] = project(marker.position);
        return Math.hypot(mx - screen[0], my - screen[1]) <= WARNING_MARKER_HIT_PX;
      });
      if (markerHit) {
        setWarningPopup({ marker: markerHit, screen });
        setWallAssemblyPopup(null);
        break;
      }
      setWarningPopup(null);
      // Resolve wall taps here instead of relying solely on SVG click bubbling. Pointer
      // capture keeps pan/touch gestures reliable, but can make child click delivery vary
      // across browsers and installed-PWA shells.
      const hit = nearestWallHit(wallsOnStorey, world);
      if (hit && hit.dist_m * scale < HIT_PX) {
        select("wall", hit.wall.uid);
        setWallAssemblyPopup({ wallUid: hit.wall.uid, screen });
      } else {
        // Pointer capture on the viewport keeps pan/touch reliable but swallows the
        // per-<g> click on filled shapes, so stairs (unlike rooms/placeables, which run
        // their own onPointerDown) must be resolved here by containment.
        const stairHit = stairsOnStorey.find((stair) => pointInPolygon(world, stair.outline));
        if (stairHit) {
          select("stair", stairHit.uid);
          setWallAssemblyPopup(null);
          setDoorPopup(null);
          setWindowPopup(null);
        } else {
          select(null, null);
          setWallAssemblyPopup(null);
          setDoorPopup(null);
          setWindowPopup(null);
        }
      }
      break;
    }
    case "wall": {
      const snap = snapWorld(world, snapNodes, tolM, gridM);
      if (!draft) {
        setDraft({ start: snap.point, startNode: snap.nodeId });
      } else {
        const end = shiftRef.current ? orthoLock(draft.start, snap.point) : snap.point;
        void commitWall(draft.start, end);
      }
      break;
    }
    case "opening": {
      const hit = nearestWallHit(wallsOnStorey, world);
      if (hit && hit.dist_m * scale < HIT_PX) {
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
    case "stair": {
      if (!activeStorey) { toast("Pick a storey first", "error"); return; }
      void commitStair(world);
      break;
    }
    case "dimension": {
      const hit = nearestWallHit(wallsOnStorey, world);
      if (hit && hit.dist_m * scale < HIT_PX) {
        select("wall", hit.wall.uid);
        setDimWall(hit.wall);
      }
      break;
    }
    case "measure": {
      // Two taps, same snapping as the wall tool: the first sets the anchor, the second fixes
      // the segment, and a tap on a fixed segment starts the next measurement.
      const snap = snapWorld(world, snapNodes, tolM, gridM);
      if (!measure || measure.end) {
        setMeasure({ start: snap.point, end: null });
      } else {
        setMeasure({
          start: measure.start,
          end: shiftRef.current ? orthoLock(measure.start, snap.point) : snap.point,
        });
      }
      break;
    }
  }
}

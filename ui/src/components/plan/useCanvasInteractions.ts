// Projection + the stable per-element pointer handlers for the SVG floorplan editor.
// Split from components/Canvas2D.tsx along its documented seam: everything here is either
// the world↔screen mapping or an identity-stable callback the memoized shapes receive, so
// hover/selection churn never re-renders the whole plan subtree (Phase 1b).
import { useCallback } from "react";
import type { RefObject } from "react";
import { useStore } from "../../state/store";
import type { Selection } from "../../state/vocabulary";
import type { CanvasObject, Opening, Vec2, Wall } from "../../model/types";
import { formatFtIn, openingFitsWall, openingStartFromCenter } from "../../model/geometry";
import { nearestOpeningHost } from "./OpeningShapes";
import type { DoorPopup, OpeningDragPreview, WallAssemblyPopup } from "./canvasTypes";

export interface CanvasInteractions {
  project: (p: Vec2) => Vec2;
  unproject: (clientX: number, clientY: number) => Vec2;
  selectEl: (kind: Selection["kind"], uid: string) => void;
  hoverEl: (uid: string | null) => void;
  editOpeningStable: (o: Opening, screen: Vec2) => void;
  movePlaceableFromDrag: (item: CanvasObject, position: Vec2) => void;
  rotatePlaceableFromHandle: (item: CanvasObject, degrees: number, freeRotation: boolean) => void;
  moveOpeningFromDrag: (opening: Opening, host: Wall, position: Vec2) => void;
  previewOpeningFromDrag: (opening: Opening, host: Wall, position: Vec2) => void;
  selectWallWithPopup: (wall: Wall, event: React.MouseEvent<SVGGElement>) => void;
}

export function useCanvasInteractions(args: {
  svgRef: RefObject<SVGSVGElement>;
  setDoorPopup: (popup: DoorPopup | null) => void;
  setWindowPopup: (popup: DoorPopup | null) => void;
  setOpeningDragPreview: (preview: OpeningDragPreview | null) => void;
  setWallAssemblyPopup: (popup: WallAssemblyPopup | null) => void;
}): CanvasInteractions {
  const { svgRef, setDoorPopup, setWindowPopup, setOpeningDragPreview, setWallAssemblyPopup } = args;
  const view = useStore((s) => s.view);
  const walls = useStore((s) => s.model!.walls);
  const runMacro = useStore((s) => s.runMacro);

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
    [svgRef, view],
  );

  // Stable per-element handlers so the memoized shapes don't re-render the whole subtree on
  // every hover/selection change (Phase 1b): identity never changes across renders, and tool
  // state is read live from the store at call time.
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
  }, [setDoorPopup, setWindowPopup]);
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
    const target = nearestOpeningHost(walls, host.storey, position);
    setOpeningDragPreview(null);
    if (!target || target.distance_m > 0.6) return;
    const along = formatFtIn(openingStartFromCenter(target.along_m, opening.width_m));
    if (target.wall.tag === host.tag) {
      void runMacro({ macro: "move_opening", storey: host.storey, tag: opening.tag, along });
    } else {
      void runMacro({ macro: "rehost_opening", storey: host.storey, tag: opening.tag,
        host: target.wall.tag, along });
    }
  }, [walls, runMacro, setOpeningDragPreview]);
  const previewOpeningFromDrag = useCallback((opening: Opening, host: Wall, position: Vec2) => {
    const target = nearestOpeningHost(walls, host.storey, position);
    if (!target || target.distance_m > 0.6) {
      setOpeningDragPreview(null);
      return;
    }
    setOpeningDragPreview({
      opening: { ...opening, center_along_m: target.along_m }, host: target.wall,
      valid: openingFitsWall(target.wall, target.along_m, opening.width_m),
    });
  }, [walls, setOpeningDragPreview]);
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
  }, [svgRef, setWallAssemblyPopup]);

  return {
    project, unproject, selectEl, hoverEl, editOpeningStable, movePlaceableFromDrag,
    rotatePlaceableFromHandle, moveOpeningFromDrag, previewOpeningFromDrag, selectWallWithPopup,
  };
}

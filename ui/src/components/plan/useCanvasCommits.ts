// The Canvas2D commits: each turns a finished gesture (a wall stroke, a stair seed, a driven
// length, a split, a heal, a placement tap, a room rectangle) into one engine macro and selects what it made.
// Split from components/Canvas2D.tsx, which keeps the gesture state these are handed.
import type { CanvasObjectType, Model, Vec2, Wall } from "../../model/types";
import { formatFtIn, normalizeRect, wallLength } from "../../model/geometry";
import { useStore } from "../../state/store";
import { WALL_SNAP_CONFIG } from "./editorConfig";
import { DEFAULT_FOOTPRINT_M } from "./PlaceableGlyph";
import { snapToWall } from "./wallSnap";
import type { WallDraft } from "./canvasTypes";

const fmt = (m: number) => formatFtIn(m);

export interface CanvasCommits {
  commitWall: (start: Vec2, end: Vec2) => Promise<void>;
  commitStair: (seed: Vec2) => Promise<void>;
  commitDim: (wall: Wall | null, newLenM: number) => Promise<void>;
  commitPlaceable: (world: Vec2) => Promise<void>;
  commitRoomRect: (a: Vec2, b: Vec2) => Promise<void>;
  splitWall: (wall: Wall) => Promise<void>;
  healNode: (tag: string) => Promise<void>;
}

export function useCanvasCommits(args: {
  model: Model;
  activeStorey: string | null;
  wallAssembly: string;
  wallsOnStorey: Wall[];
  canvasTypes: Map<string, CanvasObjectType>;
  nearestNodeTag: (p: Vec2) => string | null;
  storeyHintFile: () => string | undefined;
  setDraft: (draft: WallDraft | null) => void;
}): CanvasCommits {
  const { model, activeStorey, wallAssembly, wallsOnStorey, canvasTypes, nearestNodeTag, storeyHintFile, setDraft } = args;
  const runMacro = useStore((s) => s.runMacro);
  const select = useStore((s) => s.select);
  const toast = useStore((s) => s.toast);

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

  const commitDim = async (w: Wall | null, newLenM: number) => {
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

  // One tap of the armed Place tool: snap flush to a wall face in range (as a drag would),
  // place with the ghost's rotation, select the new object, and disarm unless Repeat is on.
  const commitPlaceable = async (world: Vec2) => {
    const s = useStore.getState();
    const typeTag = s.placementType;
    if (!typeTag) { s.setPlacementCatalogOpen(true); return; }
    if (!activeStorey) { toast("Pick a storey first", "error"); return; }
    const type = canvasTypes.get(typeTag);
    let position = world;
    let rotation = s.placementRotation;
    const snap = snapToWall(world, rotation, type?.footprint_m ?? DEFAULT_FOOTPRINT_M, wallsOnStorey, WALL_SNAP_CONFIG);
    if (snap?.snapped) { position = snap.centre; rotation = snap.rotation; }
    const res = await runMacro({
      macro: "place_placeable", storey: activeStorey, type_ref: typeTag,
      position: [fmt(position[0]), fmt(position[1])], rotation: ((rotation % 360) + 360) % 360,
      hint_file: storeyHintFile(),
    });
    if (!res) return;
    const after = useStore.getState();
    const minted = Object.keys(res.minted);
    const tag = minted.find((candidate) => (after.model?.canvas_objects ?? []).some((o) => o.tag === candidate)) ?? minted[0];
    if (tag) {
      after.selectByTag("canvas_object", tag);
      toast(`${tag} placed`);
    }
    if (!after.placementRepeat) after.setTool("select");
  };

  // Two corners → walls for the missing edges plus a Room, then select that room. The minted
  // RM- tag names it; failing that, the one room on this storey that was not there before.
  const commitRoomRect = async (a: Vec2, b: Vec2) => {
    const { w, h } = normalizeRect(a, b);
    if (w < 0.3 || h < 0.3) { toast("Room too small", "error"); return; }
    if (!activeStorey) { toast("Pick a storey first", "error"); return; }
    if (!wallAssembly) { toast("No assembly to draw with", "error"); return; }
    const before = new Set(model.rooms.map((room) => room.uid));
    const res = await runMacro({
      macro: "draw_room_rect", storey: activeStorey, a, b, assembly: wallAssembly,
      occupancy: useStore.getState().roomOccupancy, hint_file: storeyHintFile(),
    });
    if (!res) return;
    const after = useStore.getState();
    const tag = Object.keys(res.minted).find((candidate) => candidate.startsWith("RM-"))
      ?? after.model?.rooms.find((room) => room.storey === activeStorey && !before.has(room.uid))?.tag;
    if (tag) {
      after.selectByTag("room", tag);
      toast(`${tag} drawn`);
    }
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

  return { commitWall, commitStair, commitDim, commitPlaceable, commitRoomRect, splitWall, healNode };
}

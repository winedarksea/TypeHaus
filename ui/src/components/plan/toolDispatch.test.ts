// The measure tool's two-tap state machine, exercised through the real dispatcher. Every
// commit and every piece of gesture state is injected through TapDeps, so a tap here is just
// a function call — no canvas, no store, no engine.
import type { MutableRefObject } from "react";
import type { Vec2 } from "../../model/types";
import type { MeasureDraft, RoomRectDraft } from "./canvasTypes";
import { dispatchTap, type TapDeps } from "./toolDispatch";
import { resolveMeasurementPoint } from "./measurement";
import { thumbScale } from "./PlaceableGlyph";

// A minimal TapDeps: the measure branch only reads tool/offline/measure/shiftRef and the snap
// inputs, so the rest are no-op stubs. `state` is the measure slot the taps drive.
function harness(opts: { shift?: boolean; gridM?: number | null; offline?: boolean; snappingEnabled?: boolean } = {}) {
  const state: { measure: MeasureDraft | null } = { measure: null };
  const snapNodes = new Map([['corner', { id: 'corner', p: [1, 2] as Vec2, walls: [] }]]);
  let snappingEnabled = opts.snappingEnabled ?? false;
  const shiftRef = { current: opts.shift ?? false } as MutableRefObject<boolean>;
  const noop = () => {};
  const tap = (world: Vec2) => {
    const deps = {
      tool: "measure", offline: opts.offline ?? false, scale: 100, placement: null, draft: null,
      measure: state.measure, measurementSnappingEnabled: snappingEnabled, shiftRef, wallsOnStorey: [], stairsOnStorey: [],
      warningMarkers: [], snapNodes, tolM: 0.2,
      gridM: opts.gridM === undefined ? null : opts.gridM, activeStorey: "L1",
      project: (p: Vec2) => p, select: noop, toast: noop,
      setPlacement: noop, setDraft: noop,
      setMeasure: (m: MeasureDraft | null) => { state.measure = m; },
      setDimWall: noop, setWallAssemblyPopup: noop, setWarningPopup: noop,
      setDoorPopup: noop, setWindowPopup: noop,
      commitWall: async () => {}, commitStair: async () => {},
    } as unknown as TapDeps;
    dispatchTap(deps, world, [0, 0]);
  };
  const preview = (world: Vec2) => state.measure?.end ?? resolveMeasurementPoint(world, {
    snappingEnabled, nodes: snapNodes, toleranceM: 0.2, gridM: opts.gridM ?? null,
    start: state.measure?.start ?? null, shiftPressed: shiftRef.current,
  });
  return { state, tap, preview,
    setSnapping: (enabled: boolean) => { snappingEnabled = enabled; },
    setShift: (pressed: boolean) => { shiftRef.current = pressed; },
  };
}

function expectMeasure(actual: MeasureDraft | null, start: Vec2, end: Vec2 | null, what: string) {
  const same = (a: Vec2 | null | undefined, b: Vec2 | null) =>
    (a == null && b == null) || (a != null && b != null && Math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-9);
  if (!actual || !same(actual.start, start) || !same(actual.end, end)) {
    throw new Error(`${what}: got ${JSON.stringify(actual)}, expected start ${JSON.stringify(start)} / end ${JSON.stringify(end)}`);
  }
}

// The Place tool: a tap with nothing armed opens the catalog; with a type armed it places at
// the tap point, with no popover in between.
function placeableHarness(placementType: string | null) {
  const log = { placed: [] as Vec2[], catalogOpened: 0, toasts: [] as string[] };
  const noop = () => {};
  const deps = {
    tool: "placeable", offline: false, scale: 100, placement: null, draft: null, measure: null,
    shiftRef: { current: false }, wallsOnStorey: [], stairsOnStorey: [], warningMarkers: [],
    snapNodes: new Map(), tolM: 0.2, gridM: null, activeStorey: "main", project: (p: Vec2) => p,
    select: noop, toast: (message: string) => { log.toasts.push(message); },
    setPlacement: noop, setDraft: noop, setMeasure: noop, setDimWall: noop, setWallAssemblyPopup: noop,
    setWarningPopup: noop, setDoorPopup: noop, setWindowPopup: noop,
    commitWall: async () => {}, commitStair: async () => {},
    placementType,
    commitPlaceable: async (world: Vec2) => { log.placed.push(world); },
    openPlacementCatalog: () => { log.catalogOpened += 1; },
  } as unknown as TapDeps;
  return { log, tap: (world: Vec2) => dispatchTap(deps, world, [0, 0]) };
}

function runPlaceableDispatchTests() {
  const unarmed = placeableHarness(null);
  unarmed.tap([1, 1]);
  if (unarmed.log.placed.length !== 0 || unarmed.log.catalogOpened !== 1) {
    throw new Error("A tap with no armed type opens the catalog and places nothing");
  }
  const armed = placeableHarness("FURN-ARMCHAIR-35");
  armed.tap([2, 3]);
  if (armed.log.placed.length !== 1 || armed.log.placed[0][0] !== 2 || armed.log.catalogOpened !== 0) {
    throw new Error("A tap with an armed type places it at the tap point");
  }
  // A thumbnail fits the footprint's long side inside the card, margin included.
  if (Math.abs(thumbScale([2, 0.5], 48, 4) - 20) > 1e-9) throw new Error("thumbScale fits the long side");
  if (Math.abs(thumbScale(null, 48, 4) - 40 / 0.45) > 1e-9) throw new Error("thumbScale falls back to the default footprint");
}

// The Room tool: rect mode is two snapped taps and one commit; claim mode opens the popover.
function roomHarness(roomMode: "rect" | "claim") {
  const log = { committed: [] as [Vec2, Vec2][], placements: [] as unknown[] };
  const state: { roomDraft: RoomRectDraft | null } = { roomDraft: null };
  const noop = () => {};
  const tap = (world: Vec2) => dispatchTap({
    tool: "room", offline: false, scale: 100, placement: null, draft: null, measure: null,
    shiftRef: { current: false }, wallsOnStorey: [], stairsOnStorey: [], warningMarkers: [],
    snapNodes: new Map(), tolM: 0.2, gridM: 1, activeStorey: "main", project: (p: Vec2) => p,
    select: noop, toast: noop, setPlacement: (p: unknown) => { if (p) log.placements.push(p); },
    setDraft: noop, setMeasure: noop, setDimWall: noop, setWallAssemblyPopup: noop,
    setWarningPopup: noop, setDoorPopup: noop, setWindowPopup: noop,
    commitWall: async () => {}, commitStair: async () => {},
    roomMode, roomDraft: state.roomDraft,
    setRoomDraft: (d: RoomRectDraft | null) => { state.roomDraft = d; },
    commitRoomRect: async (a: Vec2, b: Vec2) => { log.committed.push([a, b]); },
  } as unknown as TapDeps, world, [0, 0]);
  return { log, state, tap };
}

function runRoomDispatchTests() {
  const rect = roomHarness("rect");
  rect.tap([1.1, 0.9]);
  if (!rect.state.roomDraft || rect.state.roomDraft.start.join() !== "1,1" || rect.log.committed.length !== 0) {
    throw new Error("Rect mode: the first tap sets a snapped corner and commits nothing");
  }
  rect.tap([4.2, 3.1]);
  const commits = rect.log.committed as [Vec2, Vec2][]; // re-read: the first check narrowed length to 0
  const corners = commits.map(([p, q]) => `${p.join()}|${q.join()}`).join(";");
  if (corners !== "1,1|4,3" || rect.state.roomDraft) {
    throw new Error("Rect mode: the second tap commits both snapped corners and clears the draft");
  }
  const claim = roomHarness("claim");
  claim.tap([2, 2]);
  if (claim.log.placements.length !== 1 || claim.state.roomDraft || claim.log.committed.length !== 0) {
    throw new Error("Claim mode: a tap opens the seed popover and draws nothing");
  }
}

export function runToolDispatchTests() {
  runPlaceableDispatchTests();
  runRoomDispatchTests();
  // Tap one anchors, tap two fixes the segment.
  const basic = harness();
  basic.tap([1, 2]);
  expectMeasure(basic.state.measure, [1, 2], null, "The first tap anchors the tape and leaves the end open");
  basic.tap([4, 6]);
  expectMeasure(basic.state.measure, [1, 2], [4, 6], "The second tap fixes the measured segment");

  // Tap three abandons the fixed segment and starts over — measurements never accumulate.
  basic.tap([10, 10]);
  expectMeasure(basic.state.measure, [10, 10], null, "A tap on a fixed segment starts the next measurement");

  // Shift ortho-locks the closing tap exactly as it does under the wall tool.
  const ortho = harness({ shift: true });
  ortho.tap([0, 0]);
  ortho.tap([5, 1]); // dx dominates → the end collapses onto the x axis
  expectMeasure(ortho.state.measure, [0, 0], [5, 0], "Shift ortho-locks the second tap");

  const free = harness({ gridM: 1 });
  free.tap([1.1, 1.9]);
  expectMeasure(free.state.measure, [1.1, 1.9], null, "Free measurement ignores nearby nodes and active grid");
  const freePreview = free.preview([4.2, 6.1]);
  free.tap([4.2, 6.1]);
  expectMeasure(free.state.measure, [1.1, 1.9], freePreview, "The free endpoint matches its preview");

  const snapped = harness({ gridM: 1, snappingEnabled: true });
  snapped.tap([1.1, 1.9]);
  expectMeasure(snapped.state.measure, [1, 2], null, "Optional snapping prefers a nearby node");
  const snappedPreview = snapped.preview([4.2, 6.1]);
  snapped.tap([4.2, 6.1]);
  expectMeasure(snapped.state.measure, [1, 2], [4, 6], "Optional snapping rounds the second point to the grid");
  expectMeasure(snapped.state.measure, [1, 2], snappedPreview, "The snapped endpoint matches its preview");
  snapped.setSnapping(false);
  expectMeasure(snapped.state.measure, [1, 2], snapped.preview([10, 10]), "Toggling snapping leaves a completed measurement fixed");

  const toggled = harness({ gridM: 1 });
  toggled.tap([1.1, 1.9]);
  toggled.setSnapping(true);
  toggled.setShift(true);
  const constrainedPreview = toggled.preview([5.2, 3.1]);
  expectMeasure({ start: [1.1, 1.9], end: constrainedPreview }, [1.1, 1.9], [5, 1.9],
    "Shift applies after snapping and preserves the free anchor");
  toggled.setShift(false);
  expectMeasure({ start: [1.1, 1.9], end: toggled.preview([5.2, 3.1]) }, [1.1, 1.9], [5, 3],
    "Releasing Shift updates the preview without moving the pointer");
  toggled.setShift(true);
  toggled.tap([5.2, 3.1]);
  expectMeasure(toggled.state.measure, [1.1, 1.9], constrainedPreview, "A constrained click matches the preview after toggling snapping");

  // Measuring journals nothing, so unlike the authoring tools it survives offline.
  const offline = harness({ offline: true });
  offline.tap([2, 2]);
  expectMeasure(offline.state.measure, [2, 2], null, "The measure tool stays usable offline");
}

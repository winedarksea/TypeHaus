// The measure tool's two-tap state machine, exercised through the real dispatcher. Every
// commit and every piece of gesture state is injected through TapDeps, so a tap here is just
// a function call — no canvas, no store, no engine.
import type { MutableRefObject } from "react";
import type { Vec2 } from "../../model/types";
import type { MeasureDraft } from "./canvasTypes";
import { dispatchTap, type TapDeps } from "./toolDispatch";

// A minimal TapDeps: the measure branch only reads tool/offline/measure/shiftRef and the snap
// inputs, so the rest are no-op stubs. `state` is the measure slot the taps drive.
function harness(opts: { shift?: boolean; gridM?: number | null; offline?: boolean } = {}) {
  const state: { measure: MeasureDraft | null } = { measure: null };
  const shiftRef = { current: opts.shift ?? false } as MutableRefObject<boolean>;
  const noop = () => {};
  const tap = (world: Vec2) => {
    const deps = {
      tool: "measure", offline: opts.offline ?? false, scale: 100, placement: null, draft: null,
      measure: state.measure, shiftRef, wallsOnStorey: [], stairsOnStorey: [],
      warningMarkers: [], snapNodes: new Map(), tolM: 0.2,
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
  return { state, tap };
}

function expectMeasure(actual: MeasureDraft | null, start: Vec2, end: Vec2 | null, what: string) {
  const same = (a: Vec2 | null | undefined, b: Vec2 | null) =>
    (a == null && b == null) || (a != null && b != null && Math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-9);
  if (!actual || !same(actual.start, start) || !same(actual.end, end)) {
    throw new Error(`${what}: got ${JSON.stringify(actual)}, expected start ${JSON.stringify(start)} / end ${JSON.stringify(end)}`);
  }
}

export function runToolDispatchTests() {
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

  // Both taps run through snapWorld, so an active grid quantises them.
  const grid = harness({ gridM: 1 });
  grid.tap([1.1, 1.9]);
  expectMeasure(grid.state.measure, [1, 2], null, "Measure taps snap to the active grid");

  // Measuring journals nothing, so unlike the authoring tools it survives offline.
  const offline = harness({ offline: true });
  offline.tap([2, 2]);
  expectMeasure(offline.state.measure, [2, 2], null, "The measure tool stays usable offline");
}

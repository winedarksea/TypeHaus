// The TS sweep kernel against Python's, vertex for vertex.
//
// `three/tubeGeometry.ts` and `resolve/sweep.py` are the same mitre written twice — one for
// the viewer, one for the glTF/IFC export and the section slice. A divergence between them is
// invisible until it is in a delivered file, so `ui/src/generated/sweepParity.json` (written
// by `scripts/gen_sweep_parity.py`) carries Python's answer for every shape the mitre has to
// get right, and this asserts TS reproduces it. `packages/engine/tests/test_sweep_kernel.py`
// asserts the fixture itself is current, so neither side can win by editing the file.
import * as THREE from "three";
import parity from "../generated/sweepParity.json";
import type { Vec2 } from "../model/types";
import {
  cleanPath, createSweepGeometry, legFrame, MAX_MITER_DEG, sweepLegs, type Vec3,
} from "./tubeGeometry";

function close(got: number, want: number, tolerance: number, what: string) {
  if (Math.abs(got - want) > tolerance) {
    throw new Error(`${what}: got ${got}, expected ${want}`);
  }
}

// Called by scripts/run-geometry-tests.mjs.
export function runSweepParityTests() {
  for (const testCase of parity.cases) {
    const legs = sweepLegs(testCase.path, testCase.profile as Vec2[]);
    if (legs.length !== testCase.legs.length) {
      throw new Error(
        `${testCase.name}: ${legs.length} legs, Python says ${testCase.legs.length}`);
    }
    legs.forEach((leg, legIndex) => {
      leg.forEach((ring, ringIndex) => {
        const expected = testCase.legs[legIndex][ringIndex];
        if (ring.length !== expected.length) {
          throw new Error(`${testCase.name}: leg ${legIndex} ring ${ringIndex} has `
            + `${ring.length} points, Python says ${expected.length}`);
        }
        ring.forEach((point, pointIndex) => {
          point.forEach((value, axis) => {
            close(value, expected[pointIndex][axis], 1e-9,
              `${testCase.name} leg ${legIndex}/${ringIndex} point ${pointIndex}[${axis}]`);
          });
        });
      });
    });
  }
}

// Called by scripts/run-geometry-tests.mjs.
export function runSweepFrameTests() {
  // The whole reason "up" is world +Z projected perpendicular to the leg: a square rail whose
  // face rolled with the slope would read as a twisted bar.
  const [right, up] = legFrame([3, 0, 2]);
  close(right[0], 0, 1e-12, "a raked leg's right must stay horizontal");
  close(right[1], 1, 1e-12, "a raked leg's right must stay horizontal");
  if (up[2] <= 0) throw new Error("up must point up, not down the slope");

  // A vertical leg has no perpendicular component of +Z and falls back to world +Y.
  const [, verticalUp] = legFrame([0, 0, -1]);
  close(verticalUp[1], 1, 1e-12, "a vertical leg's up");

  if (MAX_MITER_DEG >= 90) throw new Error("a 90 degree turn must butt, not mitre");
  const profile: Vec2[] = [[-0.05, -0.05], [0.05, -0.05], [0.05, 0.05], [-0.05, 0.05]];
  // A mitred vertex: the two legs' shared ring must be the SAME points, or the tube has a
  // hole at every corner.
  const mitred = sweepLegs([[0, 0, 0], [1, 0, 0], [2, 1, 0]], profile);
  mitred[0][1].forEach((point, i) => {
    point.forEach((value, axis) =>
      close(value, mitred[1][0][i][axis], 1e-12, "a 45 degree mitre must close"));
  });
  // A butted vertex: each leg squares off on its own axis rather than throwing a spike.
  const butted = sweepLegs([[0, 0, 0], [1, 0, 0], [1, 1, 0]], profile);
  butted[0][1].forEach((point) => close(point[0], 1, 1e-12, "leg 0 squares off at x=1"));
  butted[1][0].forEach((point) => close(point[1], 0, 1e-12, "leg 1 squares off at y=0"));

  // A repeated vertex is one point, not a zero-length leg.
  const repeated: Vec3[] = [[0, 0, 0], [1, 0, 0], [1, 0, 0], [1, 1, -0.01]];
  if (cleanPath(repeated).length !== 3) throw new Error("cleanPath must drop the repeat");
}


// Called by scripts/run-geometry-tests.mjs.
export function runSweepMeshTests() {
  // PR-M-CW-COLDSTORE-STUB's shape: along, up, along, down, around a corner. A viewer that
  // has NOT been taught about `sweep` extrudes `outline` through the whole Z span instead,
  // which for this run is a 1"-wide L-shaped band 11' long and 6' tall — a giant thin
  // rectangle where a pipe should be. That is what a stale `ui/dist` shows, and it is why
  // this asserts the mesh is the tube rather than the prism.
  const radius = 0.0159;
  const profile: Vec2[] = Array.from({ length: 12 }, (_, i) => {
    const angle = (2 * Math.PI * i) / 12;
    return [radius * Math.cos(angle), radius * Math.sin(angle)] as Vec2;
  });
  const path: Vec3[] = [
    [8.854, 10.394, 0.762], [7.442, 10.394, 0.762], [7.442, 10.394, 2.591],
    [5.486, 10.394, 2.591], [5.486, 10.394, 0.762], [5.486, 9.449, 0.762],
    [5.715, 9.449, 0.762],
  ];
  const solid = {
    uid: "T", tag: "PR-T-RUN", storey: "main", category: "pipe_water_cold",
    outline: [], voids: [], z0_m: 0.746, z1_m: 2.607, assembly: null,
    sweep: { path, profile }, provenance: null,
  };
  const geo = createSweepGeometry(solid as never, [0, 0]);
  if (!geo) throw new Error("a solid carrying a sweep must build a mesh");
  const position = geo.getAttribute("position");
  // Six legs, a 12-gon each, two rings per leg — the tube, not an eight-corner box.
  if (position.count !== 6 * 12 * 2) {
    throw new Error(`Expected 144 tube vertices, got ${position.count}`);
  }
  geo.computeBoundingBox();
  const box = geo.boundingBox!;
  // Scene space is (x, z, -y): the run is 3.37 m along, 1.83 m up, 0.95 m across — plus the
  // section either side. A prism through the same outline would be the same box, so the
  // vertex count above is the load-bearing half of this test; the box is the sanity check.
  const size = box.getSize(new THREE.Vector3());
  for (const [got, want, axis] of [[size.x, 3.368, "x"], [size.y, 1.861, "y"],
    [size.z, 0.977, "z"]] as const) {
    if (Math.abs(got - want) > 0.02) {
      throw new Error(`tube bounds ${axis}: got ${got}, expected about ${want}`);
    }
  }
}

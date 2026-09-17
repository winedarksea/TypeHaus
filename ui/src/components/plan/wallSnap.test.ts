// Wall snap and slide: the flush offset is read off the layer polygons, a skewed object is
// left alone, and an attached object only ever moves along its host.
import type { Vec2, Wall } from "../../model/types";
import { WALL_SNAP_CONFIG } from "./editorConfig";
import { slideAlongWall, slideForNudge, snapToWall, wallFrame } from "./wallSnap";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
const near = (a: number, b: number) => Math.abs(a - b) < 1e-9;
const nearPoint = (a: Vec2, b: Vec2) => near(a[0], b[0]) && near(a[1], b[1]);

// A 4 m wall along +x whose finish faces sit 0.15 m left and 0.10 m right of the axis.
function wall(axis: [Vec2, Vec2] = [[0, 0], [4, 0]]): Wall {
  return {
    uid: "W1", tag: "W-1", storey: "main", axis,
    layers: [{ polygon: [[0, -0.1], [4, -0.1], [4, 0.15], [0, 0.15]] }],
  } as unknown as Wall;
}

export function runWallSnapTests(): void {
  const walls = [wall()];
  const sofa: [number, number] = [1, 0.5];

  const left = snapToWall([2, 0.5], 0, sofa, walls, WALL_SNAP_CONFIG);
  assert(left?.snapped && near(left.gapM, 0.1), "a 10 cm gap on the left face is inside the snap band");
  assert(nearPoint(left.centre, [2, 0.4]), "the snapped back edge sits on the left finish face");
  assert(nearPoint(left.facePoint, [2, 0.15]), "the guide ends at the face, not the axis");

  const right = snapToWall([2, -0.45], 0, sofa, walls, WALL_SNAP_CONFIG);
  assert(right?.snapped && nearPoint(right.centre, [2, -0.35]), "the right face snaps off the other side of the layers");

  const turned = snapToWall([2, 0.7], 88, sofa, walls, WALL_SNAP_CONFIG);
  assert(turned?.snapped && near(turned.rotation, 90), "a near-square object is squared to the wall");
  assert(nearPoint(turned.centre, [2, 0.65]), "the flush offset uses the squared footprint's depth");

  assert(snapToWall([2, 0.6], 45, sofa, walls, WALL_SNAP_CONFIG) === null, "a skewed object is not snapped");
  assert(snapToWall([2, 1.4], 0, sofa, walls, WALL_SNAP_CONFIG) === null, "an object across the room is not snapped");
  assert(snapToWall([-0.5, 0.5], 0, sofa, walls, WALL_SNAP_CONFIG) === null, "beyond the wall's end is not beside it");
  const guideOnly = snapToWall([2, 0.7], 0, sofa, walls, WALL_SNAP_CONFIG);
  assert(guideOnly && !guideOnly.snapped, "a 30 cm gap shows the guide without snapping");

  const frame = wallFrame(wall())!;
  const slid = slideAlongWall(frame, [1, 0.4], [3.2, 0.9]);
  assert(near(slid.station, 3.2) && nearPoint(slid.centre, [3.2, 0.4]), "a slide keeps the object's offset off the wall");
  assert(near(slideAlongWall(frame, [1, 0.4], [9, 0]).station, 4), "a slide stops at the wall's end");

  assert(near(slideForNudge(frame, [0.0254, 0])!, 0.0254), "an arrow along the wall slides it");
  assert(slideForNudge(frame, [0, 0.0254]) === null, "an arrow across the wall is not a slide");
  const reversed = wallFrame(wall([[4, 0], [0, 0]]))!;
  assert(near(slideForNudge(reversed, [0.0254, 0])!, -0.0254), "a slide is measured from the wall's own start");

  console.log("Wall snap tests passed.");
}

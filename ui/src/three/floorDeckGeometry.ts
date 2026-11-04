import type { Floor } from "../model/types";
import { createPlanPrismGeometry, type PlanCenter } from "./planGeometry";

/** The engine's deck datum and slope, with legacy payload support for level floors. */
export function createFloorDeckGeometry(floor: Floor, center: PlanCenter) {
  if (!floor.subfloor || !floor.members.length) return null;
  const points = floor.members.flatMap(member => [member.p0, member.p1]);
  const outline = floor.deck_outline?.length ? floor.deck_outline : [
    [Math.min(...points.map(p => p[0])), Math.min(...points.map(p => p[1]))],
    [Math.max(...points.map(p => p[0])), Math.min(...points.map(p => p[1]))],
    [Math.max(...points.map(p => p[0])), Math.max(...points.map(p => p[1]))],
    [Math.min(...points.map(p => p[0])), Math.max(...points.map(p => p[1]))],
  ];
  const base = floor.deck_z0_m ?? Math.max(...floor.members.map(member => member.z1_m));
  const geometry = createPlanPrismGeometry(outline, base, base + floor.subfloor.thickness_m,
    floor.deck_voids ?? floor.openings, center);
  if (geometry && floor.deck_plane) {
    const plane = floor.deck_plane, positions = geometry.getAttribute("position");
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i) + center[0], y = center[1] - positions.getZ(i);
      const lift = plane.lift_at_origin_m + plane.gradient[0] * (x - plane.origin[0])
        + plane.gradient[1] * (y - plane.origin[1]);
      positions.setY(i, positions.getY(i) + lift);
    }
    positions.needsUpdate = true; geometry.computeVertexNormals();
    geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  }
  return geometry;
}

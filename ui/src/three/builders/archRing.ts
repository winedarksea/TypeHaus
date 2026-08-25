// Voussoir arch rings: the band of radiating bricks that turns around an arched opening in a
// masonry wall, and the thing that makes such an opening read as an *arch* rather than as a
// hole cut through running bond.
//
// Masonry in this viewer is a texture, not per-brick geometry (plans/01-decisions.md #23 keeps
// placed members wood-framing-only), so the arch head used to be a curve sliced out of a
// planar-projected running-bond tile: the courses ran straight through it and stopped dead at
// the soffit. The fix here does NOT model bricks either. It builds one annular ring mesh per
// arch and gives it *polar* UVs into the masonry tile that already exists — radius maps to the
// tile's unit-length axis, arc length to its course axis — so the tile's rectangular bricks
// come out as wedges in world space, and the mortar joints, the recessed-joint normal map and
// the per-unit jitter all arrive with them. No new canvas, no new material, no new cache key.
//
// The ring is laid as a rowlock header ring: one brick deep radially, each voussoir showing
// its 2⅔" course module along the arc, an odd count so a keystone lands on the crown.
//
// VIEWER-ONLY, deliberately (2026-08-21). The engine models an arch as the single scalar
// `arch_rise_m` and knows nothing of rings; the glTF emitter has no textures at all and paints
// each masonry finish one flat colour, so an exported .glb still shows the plain spandrel.
// Adding voussoirs there — or to the BOM, or to the 2D elevation — was explicitly out of scope.
import * as THREE from "three";
import type { Opening, Wall } from "../../model/types";
import { masonryTileSizeM, type MasonryStyle } from "../materials";
import type { PlanCenter } from "../planGeometry";
import { archSoffitCircle, archSoffitSegmentCount, baseRefZ, wallLocalFrame, wallLocalToSceneMatrix } from "./wallFrame";

/**
 * How far the ring stands radially above the soffit: one header, 3⅝".
 *
 * This number is load-bearing for the reference house, not a free choice. `AO-B-BRICK-DOOR`
 * crowns at 84" and the gold register band `brick-band-hi` starts at 88", so a 3⅝" ring puts
 * the extrados at 87⅝" — ⅜" clear under the band. The other common rowlock arch, one full
 * 7⅝" brick length deep, would drive the extrados to 92" and punch straight through the gold,
 * which is the very collision the opening was shortened to 84" to avoid.
 */
export const ARCH_RING_DEPTH_M = 0.0921; // 3⅝"

/**
 * How far the ring stands proud of the wythe's faces and of the soffit: 3/16".
 *
 * A ring flush with the wall would be coplanar with the field on both faces and coincident
 * with the arch soffit on its intrados — three z-fighting surfaces. Standing it proud on every
 * side removes all three at once, and a slightly projecting archivolt is a real detail rather
 * than a rendering trick. It fits: the wythe stands 1" off the concrete behind it.
 *
 * Why 3/16" and not the ⅜" this was first drawn at: the proud offset is also what *exposes*
 * the two skewback end caps. Everything of a cap but the proud sliver is buried inside the
 * wall solid, so the visible remainder is a `proud`-wide, ring-deep face turned nearly
 * edge-on to the light — at ⅜" that read as a black shard hanging off each springline,
 * most obviously on the 14" window. Halving it halves the shard and still leaves far more
 * depth separation than the renderer needs.
 */
export const ARCH_RING_PROUD_M = 0.0048; // 3/16"

/** Fewest voussoirs worth drawing — below this the ring reads as a polygon, not an arch. */
export const ARCH_RING_MIN_BRICKS = 5;

/**
 * How many voussoirs turn this arch: the arc length at the ring's mid-radius over the style's
 * course module, forced odd so one brick is centred on the crown and the ring is symmetric
 * about it — a keystone, which is what the eye reads the arch's centre from.
 */
export function archRingBrickCount(
  radiusM: number, halfAngleRad: number, style: MasonryStyle,
): number {
  const midRadius = radiusM + ARCH_RING_DEPTH_M / 2;
  const courseM = Math.max(1e-6, style.unitM[1]);
  const rounded = Math.round(2 * halfAngleRad * midRadius / courseM);
  const odd = rounded % 2 === 0 ? rounded + 1 : rounded;
  return Math.max(ARCH_RING_MIN_BRICKS, odd);
}

/**
 * A quad's four corners in the wall's local frame, plus the UV of each. `normal` overrides the
 * face normal for that corner: the intrados and extrados give every vertex the analytic radial
 * direction *at its own angle*, so the ring shades as one curve rather than as N flats — the
 * same treatment `applySmoothArchSoffitNormals` gives the wall's own soffit.
 */
interface RingVertex {
  along: number; elevation: number; across: number; u: number; v: number;
  normal?: readonly [number, number, number];
}

// Push one quad as two triangles, oriented so its front face looks along `normal`. Deriving
// the winding from the geometry rather than by hand is what keeps six differently-oriented
// surfaces (two faces, intrados, extrados, two skewbacks) consistent under FrontSide culling.
function pushQuad(
  positions: number[], normals: number[], uvs: number[],
  corners: readonly [RingVertex, RingVertex, RingVertex, RingVertex],
  normal: readonly [number, number, number],
): void {
  const [a, b, c, d] = corners;
  const edge1 = [b.along - a.along, b.elevation - a.elevation, b.across - a.across];
  const edge2 = [c.along - a.along, c.elevation - a.elevation, c.across - a.across];
  const cross = [
    edge1[1] * edge2[2] - edge1[2] * edge2[1],
    edge1[2] * edge2[0] - edge1[0] * edge2[2],
    edge1[0] * edge2[1] - edge1[1] * edge2[0],
  ];
  const facing = cross[0] * normal[0] + cross[1] * normal[1] + cross[2] * normal[2];
  const ring = facing >= 0 ? [a, b, c, d] : [a, d, c, b];
  for (const index of [0, 1, 2, 0, 2, 3]) {
    const vertex = ring[index];
    const vertexNormal = vertex.normal ?? normal;
    positions.push(vertex.along, vertex.elevation, vertex.across);
    normals.push(vertexNormal[0], vertexNormal[1], vertexNormal[2]);
    uvs.push(vertex.u, vertex.v);
  }
}

/**
 * The voussoir ring for one arched opening in one masonry wall layer, in scene space, or
 * `null` when this opening/wall/layer combination cannot carry one.
 *
 * The gate matches `createSmoothArchedWallLayerGeometry` — a square head, a raked wall or a
 * junction-mitered footprint all decline — so the two paths never disagree about which
 * openings are arches and which walls can be built against.
 */
export function createArchRingGeometry(
  opening: Opening, wall: Wall, polygon: readonly [number, number][], center: PlanCenter,
  style: MasonryStyle,
): THREE.BufferGeometry | null {
  const rise = opening.arch_rise_m ?? 0;
  if (rise <= 1e-9 || wall.top_z0_m != null || wall.top_z1_m != null) return null;
  const frame = wallLocalFrame(wall, polygon);
  if (!frame) return null;

  const { radiusM, halfAngleRad, depthM } = archSoffitCircle(opening.width_m / 2, rise);
  // The soffit circle's centre, in the wall's local frame. The springline rule is the one the
  // whole codebase measures from: `height_m` already includes the rise.
  const centerAlong = opening.center_along_m;
  const springline = baseRefZ(wall) + opening.sill_m + Math.max(0, opening.height_m - rise);
  const centerElevation = springline - depthM;
  // Proud on the intrados too, so no ring surface is ever coincident with the wall's own.
  const innerRadius = Math.max(1e-4, radiusM - ARCH_RING_PROUD_M);
  const outerRadius = radiusM + ARCH_RING_DEPTH_M;
  // Local across runs inward from the layer's maximum-across face, so proud is negative at one
  // end and past the thickness at the other.
  const frontAcross = -ARCH_RING_PROUD_M;
  const backAcross = frame.maxAcross - frame.minAcross + ARCH_RING_PROUD_M;

  const bricks = archRingBrickCount(radiusM, halfAngleRad, style);
  // Tessellate to the same chord tolerance as the soffit, but round up to a whole number of
  // facets per voussoir so every mortar joint in the texture falls on a real facet edge.
  const perBrick = Math.max(1,
    Math.ceil(archSoffitSegmentCount(outerRadius, halfAngleRad) / bricks));
  const segments = bricks * perBrick;

  const [tileAlongM, tileUpM] = masonryTileSizeM(style);
  const unitU = tileAlongM > 1e-9 ? style.unitM[0] / tileAlongM : 1 / 3;
  const courseV = tileUpM > 1e-9 ? style.unitM[1] / tileUpM : 1 / 6;
  // Each voussoir gets exactly one whole unit cell of the tile radially and one whole course
  // along the arc — so the ring reads as one brick deep however thin it physically is. Odd
  // courses in the tile are half-lapped, so odd voussoirs start half a unit over; without that
  // shift every other voussoir would straddle a joint instead of sitting on a brick.
  const uStart = (brick: number) => (brick % 2 === 0 ? 0 : unitU / 2);

  const positions: number[] = [], normals: number[] = [], uvs: number[] = [];
  const angleAt = (segment: number) => -halfAngleRad + 2 * halfAngleRad * segment / segments;
  const vAt = (segment: number) => segment * courseV / perBrick;
  const brickAt = (segment: number) => Math.min(bricks - 1, Math.floor(segment / perBrick));
  const point = (
    segment: number, radius: number, across: number, u: number, radialSign = 0,
  ): RingVertex => {
    const angle = angleAt(segment);
    return {
      along: centerAlong + radius * Math.sin(angle),
      elevation: centerElevation + radius * Math.cos(angle),
      across,
      u, v: vAt(segment),
      ...(radialSign === 0 ? {} : {
        normal: [radialSign * Math.sin(angle), radialSign * Math.cos(angle), 0] as const,
      }),
    };
  };

  for (let segment = 0; segment < segments; segment++) {
    const brick = brickAt(segment);
    const u0 = uStart(brick), u1 = u0 + unitU;
    const angle = angleAt(segment + 0.5);
    const radial: [number, number, number] = [Math.sin(angle), Math.cos(angle), 0];

    // Front and back faces: radius spans the tile's unit axis, arc its course axis.
    for (const [across, facing] of [
      [frontAcross, -1] as const, [backAcross, 1] as const,
    ]) {
      pushQuad(positions, normals, uvs, [
        point(segment, innerRadius, across, u0),
        point(segment + 1, innerRadius, across, u0),
        point(segment + 1, outerRadius, across, u1),
        point(segment, outerRadius, across, u1),
      ], [0, 0, facing]);
    }
    // Intrados and extrados: the wall's thickness now spans the unit axis, so the same joints
    // carry on around the reveal instead of the stretched stripe a planar projection gives.
    for (const [radius, sign] of [
      [innerRadius, -1] as const, [outerRadius, 1] as const,
    ]) {
      pushQuad(positions, normals, uvs, [
        point(segment, radius, frontAcross, u0, sign),
        point(segment + 1, radius, frontAcross, u0, sign),
        point(segment + 1, radius, backAcross, u1, sign),
        point(segment, radius, backAcross, u1, sign),
      ], [sign * radial[0], sign * radial[1], 0]);
    }
  }

  // The two skewbacks, where the ring dies into the wall beside the jamb. Mostly buried, but
  // an open end would show the ring hollow from a raking view.
  for (const [segment, sign] of [[0, -1] as const, [segments, 1] as const]) {
    const angle = angleAt(segment);
    const brick = brickAt(Math.max(0, segment - 1));
    const u0 = uStart(brick), u1 = u0 + unitU;
    pushQuad(positions, normals, uvs, [
      point(segment, innerRadius, frontAcross, u0),
      point(segment, outerRadius, frontAcross, u1),
      point(segment, outerRadius, backAcross, u1),
      point(segment, innerRadius, backAcross, u0),
    ], [sign * Math.cos(angle), -sign * Math.sin(angle), 0]);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.applyMatrix4(wallLocalToSceneMatrix(frame, center));
  return geometry;
}

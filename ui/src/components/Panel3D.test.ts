import * as THREE from "three";
import type { CanvasObject, Catalog, Floor, FootingBedding, Member, ModelPart, Opening, Roof, Solid, Stair, Vec2, Wall, Model } from "../model/types";
import { compassBearingScreenDirection } from "./Panel3D";
import { BUTTON_DOLLY_FACTOR } from "./ZoomControls";
import { solidCategoryLabel } from "../model/solidLabels";
import {
  clampDollyRadius, frameRadiusForBounds, MAX_DOLLY_RADIUS_M,
  MIN_DOLLY_RADIUS_M, normalizedWheelDeltaPx, pinchDollyRadius, VIEW_FIT_MIN_RADIUS_M,
  VIEW_FIT_POLAR_ANGLE, WHEEL_MAX_STEP_PX,
} from "../three/cameraFraming";
import { wholeHouseGlbAssignment } from "../three/wholeHouseGlb";
import { isRenderedInScene } from "../three/builders/registry";
import {
  buildCanvasObjectParts, canvasObjectFallbackGeometry, earthElevation, earthOutline, earthVoids,
  EARTH_FALLBACK_HALF_SIZE_M,
} from "../three/builders/site";
import {
  archSoffitCircle, archSoffitSample, archSoffitSegmentCount, buildOpening, buildWall,
  createSmoothArchedWallLayerGeometry, wallLayerPieces, withoutCollinearVertices,
} from "../three/builders/walls";
import {
  buildFloor, buildFootingBedding, buildRoof, buildSolid, buildStair, FOOTING_BEDDING_COLOR,
} from "../three/builders/structure";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import {
  SOLID_CATEGORY_COLOR, SOLID_CATEGORY_TRADE, createSolidMaterial,
  solidColor, solidOpacity, solidTrade,
} from "../three/solidMaterials";
import { ALL_TRADES, type Trade } from "../state/vocabulary";
import { carriesMemberIdentity, resolveMemberPickUid } from "../three/memberPicking";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const PALETTE = RESOLVED_NORDIC_PALETTE.light;

// A fresh, empty selection registry — the two structures createScene threads through every
// builder (the raycast target list and the uid → materials index the highlight pass drives).
function registry() {
  return { picks: [] as THREE.Mesh[], byUid: new Map<string, THREE.Material[]>() };
}

function wall(axis: Wall["axis"], topZ0: number | null = null, topZ1: number | null = null): Wall {
  return {
    uid: "wall", tag: "W-1", storey: "S-1", assembly: "A-1", provenance: null, axis,
    z0_m: 0, z1_m: 3, top_z0_m: topZ0, top_z1_m: topZ1, plate_base_z_m: null, plate_top_z_m: null, layout_axis: null, is_foundation: false,
    layers: [], members: [],
  };
}

function opening(centerAlongM: number, sillM = 0.9, heightM = 1.2, archRiseM = 0, widthM = 1): Opening {
  return {
    uid: "opening", tag: "O-1", host: "W-1", kind: "window", is_door: false,
    provenance: null, type_ref: "WIN", width_m: widthM, height_m: heightM, sill_m: sillM,
    center_along_m: centerAlongM, arch_rise_m: archRiseM, flip_hinge: false, flip_swing: false,
  };
}

// Called by scripts/run-geometry-tests.mjs. This verifies the CSG-free split used for
// partial-height openings: no generated wall piece may occupy the sill-to-head interval.
export function runOpeningGeometryTests() {
  const horizontal = wallLayerPieces(wall([[0, 0], [4, 0]]), [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2)]);
  assert(horizontal.length === 4, "Window splits a rectangular wall layer into side, sill, and header pieces");
  assert(!horizontal.some((piece) => piece.z0_m < 2.1 && piece.z1_m > 0.9 && piece.polygon.some(([x]) => x > 1.5 && x < 2.5)),
    "No horizontal-wall piece fills the window void");

  // A raked wall cannot be swept as one Shape, so its arch still falls back to stepped strips —
  // but they are stepped by angle, so no single strip carries a springline-sized riser.
  const rakedArch = wallLayerPieces(wall([[0, 0], [4, 0]], 3, 2.4),
    [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2, 0, 1, 0.5)]);
  const archSpandrels = rakedArch.filter((piece) => piece.z0_m > 0);
  assert(archSpandrels.length === archSoffitSegmentCount(0.5),
    "Strip fallback tessellates the arch to its radius-derived segment count");
  assert(Math.max(...archSpandrels.map((piece) => piece.z0_m)) > Math.min(...archSpandrels.map((piece) => piece.z0_m)),
    "Arch soffit rises from its springlines to a visible crown");
  const risers = archSpandrels.slice(1).map((piece, index) => Math.abs(piece.z0_m - archSpandrels[index].z0_m));
  assert(Math.max(...risers) < 0.5 / 2,
    "Angular sampling keeps every soffit step well under the radius — even-x steps dropped ~85% of it at the springline");

  const vertical = wallLayerPieces(wall([[0, 0], [0, 4]]), [[-0.1, 0], [0.1, 0], [0.1, 4], [-0.1, 4]], [opening(2)]);
  assert(vertical.length === 4, "Vertical wall uses the same axis-relative opening split");

  const raked = wallLayerPieces(wall([[0, 0], [4, 0]], 3, 2.4), [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [opening(2, 0.9, 1)]);
  assert(raked.some((piece) => piece.topIsRaked), "Header pieces preserve a raked wall top");

  const mitered = wallLayerPieces(
    wall([[0, 0], [4, 0]]),
    [[-0.25, 0], [0, -0.25], [4, -0.25], [4, 0.25], [0, 0.25]],
    [opening(2)],
  );
  assert(mitered.some((piece) => piece.polygon.some(([x, y]) => x === -0.25 && y === 0)),
    "Opening splitting preserves a junction-solved miter vertex");

  // A door can start *below* the wall hosting it: the Catlin garage's overhead door lands on
  // the slab, one 22" ICF stem reveal under W-G-E's base. Height is measured from that
  // threshold, so the head must come down with it — both builders have to agree with
  // resolve/geometry_walls.py, which measures from the (unclamped) threshold too.
  const stemReveal = 0.5588, doorHeight = 2.1336;
  const onStem = { ...wall([[0, 0], [4, 0]]), z0_m: stemReveal, z1_m: stemReveal + 2.4384 };
  const dropped = { ...opening(2, -stemReveal, doorHeight, 0, 1.6), kind: "door" as const, is_door: true };
  const head = doorHeight;  // threshold (0) + height, NOT the wall base + height

  const belowGrade = wallLayerPieces(onStem, [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [dropped]);
  assert(!belowGrade.some((piece) => piece.z0_m < stemReveal - 1e-9),
    "A below-base threshold adds no wall piece under the wall itself");
  assert(!belowGrade.some((piece) => piece.z0_m < head - 1e-9 && piece.z1_m > stemReveal + 1e-9
    && piece.polygon.some(([x]) => x > 1.5 && x < 2.5)),
    "No wall piece fills the dropped door's void between the wall base and its head");
  assert(belowGrade.some((piece) => Math.abs(piece.z0_m - head) < 1e-9),
    "The header piece starts at the head measured from the threshold, not from the wall base");

  // Same rule in the swept-Shape builder, which only engages for arched openings — hence the
  // arch rise here. Its springline is the threshold plus the square part of the opening, so
  // it is the term that moves if the threshold is read off the clamped bottom instead.
  // Elevation survives as the geometry's Y (the extrude maps across to Z).
  const archRise = 0.4;
  const archedDrop = { ...dropped, arch_rise_m: archRise };
  const swept = createSmoothArchedWallLayerGeometry(
    onStem, [[0, -0.1], [4, -0.1], [4, 0.1], [0, 0.1]], [archedDrop], [0, 0]);
  assert(swept, "An arched opening admits the wall layer to the swept-Shape path");
  const ys = Array.from(swept!.getAttribute("position").array).filter((_, i) => i % 3 === 1);
  const springline = doorHeight - archRise;  // from the threshold at 0, not from the wall base
  assert(ys.some((y) => Math.abs(y - springline) < 1e-6),
    "Swept hole springs from the threshold-measured springline");
  assert(!ys.some((y) => Math.abs(y - (stemReveal + springline)) < 1e-6),
    "Swept hole never springs from the wall base, which is where a clamped threshold would put it");
}

// Arches must read as true half circles, not a stack of stripes. That needs the swept-Shape
// path — and the guard that admits a layer to it has to see past the collinear vertices
// junction resolution leaves on the ring, or every real arched wall falls back to strips.
export function runArchGeometryTests() {
  assert(withoutCollinearVertices([[0, 0], [2, 0], [4, 0], [4, 1], [0, 1]]).length === 4,
    "A rectangle padded with an edge-splitting vertex reduces to its four corners");
  assert(withoutCollinearVertices([[-0.25, 0], [0, -0.25], [4, -0.25], [4, 0.25], [0, 0.25]]).length === 5,
    "A junction-solved miter vertex is a real corner and survives reduction");
  assert(withoutCollinearVertices([[0, 0], [4, 0], [4, 1], [4, 1], [0, 1]]).length === 4,
    "Duplicate vertices collapse without inventing a corner");

  assert(archSoffitSegmentCount(1.2192) > archSoffitSegmentCount(0.3),
    "Tessellation follows the arch radius rather than a flat constant");

  // A 16" concrete layer as one rectangle padded to six points — the shape a junction-solved
  // arched wall arrives in. The literals are self-contained; the wall they were taken from
  // (the sunken garden's arched cross-wall) was retired 2026-08-18.
  const archWall = wall([[0, 0], [6, 0]]);
  const paddedThinRect: [number, number][] = [[0.5, -0.2], [0.5, 0], [0.5, 0.2], [5.5, 0.2], [5.5, 0], [5.5, -0.2]];
  const arch = opening(3, 0.1, 2.4, 1.2, 2.4);
  const smooth = createSmoothArchedWallLayerGeometry(archWall, paddedThinRect, [arch], [0, 0]);
  assert(smooth !== null, "A collinear-padded rectangle still takes the smooth swept-arch path");
  const box = new THREE.Box3().setFromBufferAttribute(smooth.getAttribute("position") as THREE.BufferAttribute);
  assert(Math.abs((box.max.z - box.min.z) - 0.4) < 1e-6,
    "The swept layer keeps its full authored thickness");

  // Every soffit vertex carries the analytic cylinder normal, so adjacent facets shade as one
  // curve instead of ARCH segment-count flats. Wall axis is +x, so scene x/y are the shape plane.
  const position = smooth.getAttribute("position");
  const normal = smooth.getAttribute("normal");
  const springline = archWall.z0_m + arch.sill_m + (arch.height_m - (arch.arch_rise_m ?? 0));
  let soffitVertices = 0;
  for (let index = 0; index < position.count; index++) {
    // The front/back caps also have vertices on the arc; they must keep their axial normals.
    if (Math.abs(normal.getZ(index)) > 0.5) continue;
    const dx = position.getX(index) - arch.center_along_m;
    const dy = position.getY(index) - springline;
    const distance = Math.hypot(dx, dy);
    // Positions are float32, so allow a hair of slack around the circle and the springline.
    if (dy < 1e-4 || Math.abs(distance - 1.2) > 1e-4) continue;
    soffitVertices++;
    const aligned = Math.abs(normal.getX(index) * dx / distance + normal.getY(index) * dy / distance);
    assert(aligned > 1 - 1e-5 && Math.abs(normal.getZ(index)) < 1e-5,
      "Soffit normals are radial to the arch circle, not per-facet");
  }
  assert(soffitVertices > archSoffitSegmentCount(1.2),
    "The soffit ring was actually found and smoothed");

  // A banded layer (`Layer.extent` / `Layer.slot`) must be swept over its OWN z-range, not the
  // wall's. Until 2026-08-20 this path ignored the band, so the sunken garden's five-region
  // Ishtar wythe — arched door, arched window, therefore swept — built five coincident
  // full-height solids in five colours and rendered as z-fighting noise instead of bands.
  const yRange = (geo: THREE.BufferGeometry | null) => {
    assert(geo !== null, "The banded region still takes the swept-arch path");
    const bounds = new THREE.Box3().setFromBufferAttribute(
      geo.getAttribute("position") as THREE.BufferAttribute);
    return [bounds.min.y, bounds.max.y] as const;
  };
  const banded = (z0: number | null, z1: number | null) => createSmoothArchedWallLayerGeometry(
    archWall, paddedThinRect, [arch], [0, 0], { z0_m: z0, z1_m: z1 });

  const unbanded = yRange(createSmoothArchedWallLayerGeometry(archWall, paddedThinRect, [arch], [0, 0]));
  assert(Math.abs(unbanded[0]) < 1e-6 && Math.abs(unbanded[1] - 3) < 1e-6,
    "A layer with no band still sweeps the whole wall, exactly as before");

  const plinth = yRange(banded(null, 0.05));
  assert(Math.abs(plinth[0]) < 1e-6 && Math.abs(plinth[1] - 0.05) < 1e-6,
    "A band below the opening's sill sweeps only its own courses");
  assert(plinth[1] < unbanded[1] - 1e-6,
    "Two regions of one split row no longer sweep the same full-height solid");

  const cutByArch = yRange(banded(null, 2.0));
  assert(Math.abs(cutByArch[1] - 2.0) < 1e-6,
    "A band whose top cuts through the arch head stops at the band, not the crown");

  const above = yRange(banded(2.6, null));
  assert(Math.abs(above[0] - 2.6) < 1e-6 && Math.abs(above[1] - 3) < 1e-6,
    "A band clear above the arch crown runs to the wall top");
  // The field above a door is solid brick. With the hole suppressed the swept solid is a plain
  // box: eight distinct corners, which an opening-punched outline can never reduce to.
  const aboveCorners = new Set<string>();
  const abovePosition = banded(2.6, null)!.getAttribute("position");
  for (let index = 0; index < abovePosition.count; index++) {
    aboveCorners.add([abovePosition.getX(index), abovePosition.getY(index), abovePosition.getZ(index)]
      .map((value) => value.toFixed(4)).join(","));
  }
  assert(aboveCorners.size === 8, "An opening entirely below a band punches no hole in it");

  assert(banded(2.6, 2.6) === null,
    "A zero-height band builds nothing rather than an inverted shape");

  assert(createSmoothArchedWallLayerGeometry(archWall, paddedThinRect, [opening(3)], [0, 0]) === null,
    "A wall with no arched opening keeps the ordinary extrusion path");
  assert(createSmoothArchedWallLayerGeometry(
    wall([[0, 0], [6, 0]], 3, 2.4), paddedThinRect, [arch], [0, 0]) === null,
    "A raked wall cannot be swept as one Shape and falls back to strips");
  assert(createSmoothArchedWallLayerGeometry(archWall,
    [[-0.25, 0], [0, -0.2], [6, -0.2], [6, 0.2], [0, 0.2]], [arch], [0, 0]) === null,
    "A genuinely non-rectangular (mitered) footprint still falls back to strips");

  // Segmental heads: a rise that is a fraction of the half-span (here 2" on a 14" opening)
  // must draw a shallow arc, not clamp to a full half-circle of width/2 regardless of the
  // authored rise. Mirrors `test_segmental_arch_crown_lands_on_the_authored_head` in
  // packages/engine/tests/test_macros_gltf_m2.py — keep the two in step.
  const halfSpan = 0.1778, rise = 0.0508;  // 7" and 2"
  const segmental = archSoffitCircle(halfSpan, rise);
  assert(segmental.radiusM > halfSpan && Math.abs(segmental.depthM - (segmental.radiusM - rise)) < 1e-12,
    "A shallow rise gives a circle bigger than the opening, centred below it");
  const count = archSoffitSegmentCount(segmental.radiusM, segmental.halfAngleRad);
  const samples = Array.from({ length: count + 1 }, (_value, segment) =>
    archSoffitSample(segment, count, segmental.radiusM, segmental.halfAngleRad));
  assert(Math.abs(samples[0].offsetM + halfSpan) < 1e-9 && Math.abs(samples[0].heightM) < 1e-9 &&
    Math.abs(samples[count].offsetM - halfSpan) < 1e-9 && Math.abs(samples[count].heightM) < 1e-9,
    "The arc runs springline to springline");
  const crown = Math.max(...samples.map(({ heightM }) => heightM));
  assert(Math.abs(crown - rise) < 1e-4 && crown < halfSpan,
    "The crown lands on the authored rise, not on the radius");
  // rise === half-span is still exactly the semicircle every existing arch is built on.
  const half = archSoffitCircle(halfSpan, halfSpan);
  assert(Math.abs(half.radiusM - halfSpan) < 1e-12 && Math.abs(half.depthM) < 1e-12 &&
    Math.abs(half.halfAngleRad - Math.PI / 2) < 1e-12,
    "A rise of half the span is the semicircle, unchanged");
}

export function runEarthGeometryTests() {
  const model = { site: { lat: 0, lon: 0, true_north_deg: 0,
    parcel: [[-2, -1], [4, -1], [4, 3], [-2, 3]] } } as Model;
  const parcel = earthOutline(model, [0, 0]);
  assert(parcel.length === 4 && parcel[0][0] === -2 && parcel[2][1] === 3,
    "Earth uses the authored parcel outline");

  const fallback = earthOutline({} as Model, [3, 5]);
  assert(fallback[0][0] === 3 - EARTH_FALLBACK_HALF_SIZE_M &&
    fallback[2][1] === 5 + EARTH_FALLBACK_HALF_SIZE_M,
    "Earth falls back to a large centered sheet without a parcel");

  assert(earthElevation({ site: { lat: 0, lon: 0, true_north_deg: 0, grade_m: 1.5 } } as Model) === 1.5,
    "Earth uses the serialized site grade");
  assert(earthElevation({} as Model) === 0, "Earth defaults to the main-floor datum");

  // Excavations punch holes in the site sheet so the earth no longer bleeds up through the
  // spaces that were dug for it. The rings are resolved server-side from slabs at or below
  // grade (resolve/site_earth.py) and arrive already unioned into disjoint outer boundaries —
  // one per structure, which is why the viewer must not re-derive them. The old room-derived
  // version could only ever see one storey of one structure, so a detached garage and an
  // open-air sunken garden (no shared storey, room set or wall loop) stayed uncut.
  const withVoids = {
    site: {
      lat: 0, lon: 0, true_north_deg: 0,
      earth_voids: [
        [[0, 0], [7, 0], [7, 3], [0, 3]], // house
        [[10, 0], [16, 0], [16, 6], [10, 6]], // detached garage — its own structure
        [[0, 8], [4, 8], [4, 12], [0, 12]], // open-air sunken garden — no rooms at all
        [[1, 1], [1, 1]], // degenerate ring is skipped
      ],
    },
    // Rooms are deliberately present and disagree with the voids: nothing here may fall back
    // to them, or the multi-structure fix silently regresses.
    storeys: [{ tag: "L1", elevation_m: 0 }],
    rooms: [{ storey: "L1", clear_face: [[0, 0], [4, 0], [4, 3], [0, 3]] }],
  } as unknown as Model;
  const voids = earthVoids(withVoids);
  assert(voids.length === 3, "Every excavated structure cuts the sheet, not just the house");
  assert(voids.every((ring) => ring.length === 4), "Each cut is the resolved outer ring");
  assert(voids.some(([first]) => first[0] === 10) && voids.some(([first]) => first[1] === 8),
    "The detached garage and the sunken garden both cut, though neither shares a storey with the house");

  assert(earthVoids({} as Model).length === 0,
    "No serialized voids → a solid sheet (older model.json), never a room-derived guess");
  assert(earthVoids({ rooms: [{ storey: "L1", clear_face: [[0, 0], [4, 0], [4, 3]] }],
    storeys: [{ tag: "L1", elevation_m: 0 }] } as unknown as Model).length === 0,
    "Rooms alone never cut the sheet — the engine owns this derivation now");
}

export function runFootingBeddingGeometryTests() {
  const bedding = {
    uid: "FB-1", tag: "FB-1", storey: "L1", host: "F-1",
    outline: [[0, 0], [3, 0], [3, 1], [0, 1]], z0_m: -1.2, z1_m: -0.9,
    aggregate: "washed-stone", geotextile: true, drain_tile: true, provenance: null,
  } as FootingBedding;
  const group = new THREE.Group();
  const schematic = registry();
  buildFootingBedding(group, bedding, [0, 0], "schematic", schematic.picks, schematic.byUid);
  const meshes = group.children.filter((child): child is THREE.Mesh => child instanceof THREE.Mesh);
  assert(meshes.length === 1, "Footing bedding renders one gravel prism (schematic omits the edge overlay)");
  const box = new THREE.Box3().setFromObject(meshes[0]);
  assert(Math.abs(box.min.y - -1.2) < 1e-6 && Math.abs(box.max.y - -0.9) < 1e-6,
    "Gravel bed spans the authored undercut below the footing underside");
  assert((meshes[0].material as THREE.MeshStandardMaterial).color.getHex() === FOOTING_BEDDING_COLOR,
    "Gravel bed uses the aggregate colour, not concrete grey");

  // Nordic mode adds a faceted edge overlay for legibility.
  const nordic = new THREE.Group();
  const nordicRegistry = registry();
  buildFootingBedding(nordic, bedding, [0, 0], "nordic", nordicRegistry.picks, nordicRegistry.byUid);
  assert(nordic.children.some((child) => child instanceof THREE.LineSegments),
    "Nordic footing bedding gains an edge overlay");
  assert(nordicRegistry.picks.length === 1,
    "The edge overlay stays out of the raycast set — only the gravel prism is pickable");

  const degenerate = new THREE.Group();
  const skipped = registry();
  buildFootingBedding(degenerate, { ...bedding, z1_m: -1.2 } as FootingBedding, [0, 0], "schematic",
    skipped.picks, skipped.byUid);
  assert(degenerate.children.length === 0, "Zero-thickness bedding produces no geometry");
  assert(skipped.picks.length === 0, "Geometry-free bedding registers nothing to pick");
}

// --- B7: solid finishes ------------------------------------------------------
// Every non-wall prism used to render as one concrete grey. Category + assembly now drive the
// finish, mirroring emit/gltf/emitter.py::_solid_color / _PALETTE.

const POST_PAINT_CATALOG = {
  window_types: [], door_types: [], occupancies: [], materials: [],
  assemblies: [{
    tag: "POST_WHITE_PAINT", editable: false, provenance: null, stc: null, variant_of: null,
    layers: [{ name: "post-paint-white", material: "post-paint-white", function: "structure", thickness_m: 0.1397 }],
  }],
} as Catalog;

function solid(category: string, assembly: string | null = null, uid = "S-1",
  material: string | null = null): Solid {
  return {
    uid, tag: uid, storey: "L1", category, assembly, provenance: null, material,
    outline: [[0, 0], [1, 0], [1, 0.2], [0, 0.2]], voids: [], z0_m: 0, z1_m: 2.4,
  } as Solid;
}

// A material that declares itself see-through the only way one can: an alpha byte on its
// authored colour. Nothing infers translucency from a category or a tag.
const GLASS_CATALOG = {
  window_types: [], door_types: [], occupancies: [], assemblies: [],
  materials: [{ tag: "guard-glass", name: "Guard glass", color: "#8fb7c97a" }],
} as unknown as Catalog;

export function runSolidMaterialTests() {
  assert(solidColor(solid("beam"), undefined, PALETTE) === SOLID_CATEGORY_COLOR.beam,
    "An unfinished beam reads as wood from the category palette");
  assert(SOLID_CATEGORY_COLOR.beam !== PALETTE.member.concrete,
    "The beam colour is wood, not the concrete fallback the old buildSolid used");

  // The TODO's headline case: six 6x6 posts carry assembly=POST_WHITE_PAINT.
  const painted = solidColor(solid("column", "POST_WHITE_PAINT"), POST_PAINT_CATALOG, PALETTE);
  assert(painted === 0xf4f2ee, `A painted post reads as its paint colour, got ${painted.toString(16)}`);
  assert(painted !== SOLID_CATEGORY_COLOR.column,
    "The authored assembly overrides the bare column palette entry");

  // Gutters, fascia and flashings were invisible grey slivers before B7.
  for (const category of ["gutter", "fascia", "flashing"]) {
    const color = solidColor(solid(category), undefined, PALETTE);
    assert(color === SOLID_CATEGORY_COLOR[category], `${category} uses its own palette entry`);
    assert(color !== PALETTE.member.concrete, `${category} no longer renders as concrete grey`);
  }

  // An unmapped category falls back to the theme's neutral rather than inventing a colour.
  // (Construction returns used to arrive here as "return:*" solids; the engine emits none
  // now — they are records on Model.construction_returns, drawn by nothing.)
  assert(solidColor(solid("no-such-category"), undefined, PALETTE) === PALETTE.member.concrete,
    "An unmapped category falls back to the theme's neutral, matching the emitter's _FALLBACK");

  const metal = createSolidMaterial(solid("gutter"), undefined, "nordic", PALETTE);
  assert(metal.metalness > 0, "Shop-finished metal accessories render metallic");
  const concrete = createSolidMaterial(solid("slab"), undefined, "nordic", PALETTE);
  assert(concrete.metalness === 0, "Cast concrete stays fully dielectric");

  // A solid is not automatically concrete. BM-M-HALL and BM-S-HALL rendered under the Concrete
  // toggle while RB-HOUSE — the same authored element kind, re-typed by the resolver as a roof
  // member — rendered under Framing. The engine keeps the same table (emit/trades.py) and
  // tests/test_solid_trade_parity.py holds the two literals in agreement; these assertions
  // cover the lookup itself, which that text-reading test cannot see.
  assert(solidTrade(solid("beam")) === "framing",
    "A standalone beam is framing, not concrete");
  assert(solidTrade(solid("column")) === "framing",
    "A standalone post is framing, not concrete");
  assert(solidTrade(solid("pipe_drain")) === "plumbing",
    "A routed waste line follows the Plumbing toggle");
  assert(solidTrade(solid("vacuum_breaker")) === "plumbing",
    "A backflow device follows the pipe it interrupts, not the concrete fallback");
  assert(solidTrade(solid("penetration_seal")) === "plumbing",
    "So does the seal around a pipe crossing the envelope");
  // Per-device categories, so the Inspector heading names the device rather than its family.
  // "pipe accessory" was true of a shutoff, a preventer and a can of foam alike.
  assert(solidCategoryLabel("vacuum_breaker") === "Vacuum breaker",
    "A known category gets its human name");
  assert(solidCategoryLabel("some_new_thing") === "Some new thing",
    "An unmapped category is still readable on the day it lands");
  assert(solidCategoryLabel(undefined) === "Solid", "A category-less solid still has a heading");
  assert(solidTrade(solid("vent")) === "mechanical", "A vent riser is mechanical");
  assert(solidTrade(solid("fascia")) === "roof", "Roof edge trim rides the roof toggle");
  // The stormwater run is one toggle end to end: the gutter used to sit under Roof and the
  // pit it drains to on the concrete fallback, which meant no single checkbox showed drainage.
  assert(solidTrade(solid("gutter")) === "drainage", "A gutter is the head of the storm run");
  assert(solidTrade(solid("downspout")) === "drainage", "A leader follows its gutter");
  assert(solidTrade(solid("sump")) === "drainage", "The pit is the tail of the same run");
  assert(solidTrade(solid("glazing")) === "openings", "Glazing reads as fenestration");
  assert(solidTrade(solid("soffit")) === "floors",
    "A dropped soffit is finished like the ceiling it hangs under");
  assert(solidTrade(solid("slab")) === "concrete", "A pour is still concrete");
  assert(solidTrade(solid("no-such-category")) === "concrete",
    "An unclassified category falls back to concrete rather than dropping out of the scene");
  for (const category of Object.keys(SOLID_CATEGORY_TRADE)) {
    assert(ALL_TRADES.includes(SOLID_CATEGORY_TRADE[category]),
      `${category} maps to a trade with no THREE.Group: ${SOLID_CATEGORY_TRADE[category]}`);
  }

  // Guards ride the stairs toggle, and the plan viewer's RailingOutlines gate
  // (components/Canvas2D.tsx) is on the same trade — the two have to agree or a railing shows
  // in one viewer and not the other. They rode the concrete fallback for a long time.
  for (const category of ["railing", "railing_infill", "railing_glass"]) {
    assert(solidTrade(solid(category)) === "stairs",
      `${category} follows the guard it belongs to, not the concrete fallback`);
  }
  // Connection hardware, by what kind of connection it is. 49 PV rail clamps and 8 gutter
  // straps used to sit under Concrete for want of anywhere better.
  assert(solidTrade(solid("connector")) === "framing",
    "A hanger, tie, post base or hold-down is the carpenter's hardware");
  assert(solidTrade(solid("snow_guard")) === "roof", "A snow rail sits on the roof skin");
  assert(solidTrade(solid("seam_clamp")) === "roof",
    "So does a seam clamp, whatever it happens to be holding");

  // --- translucency ----------------------------------------------------------------------
  // `solidOpacity` used to walk the assembly ONLY, while `solidColor` right above it read the
  // direct material ref as well. A guard's glass lite gets its translucency from a material
  // ref (its posts and its lite share one Railing.assembly and are not the same material), so
  // it shipped translucent in the .glb and rendered OPAQUE — and single-sided — in the live
  // viewer. Colour and opacity have to walk the same ladder.
  const lite = solid("railing_glass", "RAILING_DARK_METAL", "S-GLASS", "guard-glass");
  assert(Math.abs(solidOpacity(lite, GLASS_CATALOG) - 0x7a / 255) < 1e-6,
    `A lite whose translucency comes from a material ref is see-through, got ${solidOpacity(lite, GLASS_CATALOG)}`);
  const glassMaterial = createSolidMaterial(lite, GLASS_CATALOG, "nordic", PALETTE);
  assert(glassMaterial.transparent, "...and its THREE material blends");
  assert(glassMaterial.side === THREE.DoubleSide,
    "A pane is a thin prism: without both faces it disappears from one side");
  assert(glassMaterial.metalness === 0,
    "railing_glass is deliberately outside METALLIC_SOLID_CATEGORIES — under it a lite renders as dark metal");
  const picket = createSolidMaterial(solid("railing_infill"), undefined, "nordic", PALETTE);
  assert(picket.metalness > 0, "Opaque infill is the same mill aluminium as the frame");
  assert(solidOpacity(solid("railing"), undefined) === 1,
    "A solid that names no translucent material is opaque");
}

// --- B7: pick registration ---------------------------------------------------
// picks[] is the only raycast target and byUid drives the emissive highlight, so a builder that
// forgets either leaves its element unselectable. One assertion per builder that opts in.

function member(key: string): Member {
  return {
    key, category: "joist", profile: "2x10", p0: [0, 0], p1: [3, 0], z0_m: 2.4, z1_m: 2.65,
    length_m: 3, z0_end_m: null, z1_end_m: null, shape: "rect", width_m: 0.038, depth_m: 0.235,
    flange_width_m: null, flange_thickness_m: null, web_thickness_m: null, plies: 1,
    orient: null,
  } as Member;
}

function registered(group: THREE.Group, uid: string, kind: string, picks: THREE.Mesh[],
  byUid: Map<string, THREE.Material[]>, label: string) {
  const mine = picks.filter((mesh) => mesh.userData.uid === uid);
  assert(mine.length > 0, `${label} pushes at least one mesh into the raycast set`);
  assert(mine.every((mesh) => mesh.userData.selectionKind === kind),
    `${label} tags every pickable mesh with selectionKind "${kind}"`);
  assert((byUid.get(uid) ?? []).length > 0, `${label} indexes its materials for the highlight pass`);
  assert(group.children.length > 0, `${label} actually built geometry`);
}

export function runSelectionRegistrationTests() {
  const solidGroup = new THREE.Group();
  const solids = registry();
  buildSolid(solidGroup, solid("column", null, "SO-1"), [0, 0], "schematic", PALETTE, undefined,
    solids.picks, solids.byUid);
  registered(solidGroup, "SO-1", "solid", solids.picks, solids.byUid, "buildSolid");

  const beddingGroup = new THREE.Group();
  const beddings = registry();
  buildFootingBedding(beddingGroup, {
    uid: "FB-9", tag: "FB-9", storey: "L1", host: "F-1",
    outline: [[0, 0], [3, 0], [3, 1], [0, 1]], z0_m: -1.2, z1_m: -0.9,
    aggregate: "washed-stone", geotextile: true, drain_tile: true, provenance: null,
  } as FootingBedding, [0, 0], "schematic", beddings.picks, beddings.byUid);
  registered(beddingGroup, "FB-9", "footing_bedding", beddings.picks, beddings.byUid, "buildFootingBedding");

  // A floor's joists build into the framing group, not the floors group — the floors toggle
  // hides the deck alone, and the joist bucket still carries its own per-member identity so
  // the deck selects as the floor while a joist selects as a joist.
  const floorGroup = new THREE.Group();
  const floorFramingGroup = new THREE.Group();
  const floors = registry();
  buildFloor(floorGroup, {
    uid: "FL-1", tag: "FL-1", storey: "L1", direction: "x", provenance: null, openings: [],
    subfloor: { material: "osb", thickness_m: 0.019 }, members: [member("J-1"), member("J-2")],
  } as Floor, [0, 0], "schematic", PALETTE, floors.picks, floors.byUid, floorFramingGroup);
  registered(floorGroup, "FL-1", "floor", floors.picks, floors.byUid, "buildFloor");
  assert(floorFramingGroup.children.length > 0, "buildFloor draws joists into the framing group");
  assert(floors.picks.length > 1, "The subfloor deck and the joist bucket are both raycast targets");
  const joistBucket = floors.picks.find(carriesMemberIdentity);
  assert(joistBucket !== undefined, "buildFloor makes its joist bucket pickable");
  assert(resolveMemberPickUid(joistBucket!, 1, null) === "FL-1::J-2",
    "Instance 1 of the floor's joist bucket resolves to the second joist, not to the floor");
  assert((floors.byUid.get("FL-1") ?? []).includes(joistBucket!.material as THREE.Material),
    "Selecting the floor still lights its joists — the bucket stays in the owner's highlight set");

  // A wall's own closure members (the derived bands carrying a skin layer up to the roof it
  // meets) split by what they continue: a cladding closure is envelope skin and belongs with
  // the wall body on the walls toggle, while a furring closure (a truss wall's outrigger band)
  // is still lumber and stays on the framing toggle with the studs.
  const tradeGroups = Object.fromEntries(
    ALL_TRADES.map((trade) => [trade, new THREE.Group()]),
  ) as Record<Trade, THREE.Group>;
  const walls = registry();
  const closureWall = wall([[0, 0], [4, 0]]);
  closureWall.members = [
    { ...member("W-1-closure-0-cladding"), category: "cladding", material: "standing-seam" },
    { ...member("W-1-closure-0-outrigger"), category: "furring", material: "kdat" },
  ];
  buildWall(tradeGroups, closureWall, [], [0, 0], "schematic", PALETTE, walls.picks, walls.byUid);
  assert(tradeGroups.walls.children.length > 0,
    "A wall's cladding closure band builds into the walls group");
  assert(tradeGroups.framing.children.length > 0,
    "A wall's furring closure band still builds into the framing group");

  // The Swinburne truss pack. Every piece of it names a material — the block is spf, the
  // outrigger and the ladder blocking kdat, the tab and the buck struct-1-plywood — and every
  // piece is lumber a carpenter cuts, so the whole pack belongs on the framing toggle beside
  // the studs. Routing on "does it name a material" instead of on the category put all of it
  // on the Walls trade under the "Other" layer group, which is how a truss wall came to be
  // present in the model and in 2D and *absent from 3D*. Nothing here is envelope skin, so
  // the walls group must take none of it.
  const trussGroups = Object.fromEntries(
    ALL_TRADES.map((trade) => [trade, new THREE.Group()]),
  ) as Record<Trade, THREE.Group>;
  const trussWall = wall([[0, 0], [4, 0]]);
  trussWall.members = [
    { ...member("stud-000"), category: "stud", material: null },
    { ...member("strapping-outrigger-000"), category: "strapping", material: "kdat" },
    { ...member("block-truss-000-00"), category: "truss_block", material: "spf" },
    { ...member("tab-truss-000-00"), category: "truss_tab", material: "struct-1-plywood" },
    { ...member("ladder-0-head"), category: "truss_blocking", material: "kdat" },
    { ...member("filler-0-left"), category: "truss_filler", material: "kdat" },
    { ...member("buck-0-head"), category: "buck", material: "struct-1-plywood" },
  ];
  buildWall(trussGroups, trussWall, [], [0, 0], "schematic", PALETTE, registry().picks,
    registry().byUid);
  assert(trussGroups.walls.children.length === 0,
    "No piece of the truss pack is envelope skin — the walls group takes none of it");
  assert(trussGroups.framing.children.length > 0,
    "The truss pack draws with the studs, on the framing toggle");

  // The CATLIN TRUSS pack, beside it, for the same reason and with different keys. Two tiers
  // of flat girts, so two blocks (block-1 spf, block-2 kdat), two jamb posts per RO named for
  // their band, head and sill courses per band, and a 6" buck. It has no tab and no filler at
  // all. Every piece names a material and every piece is lumber, so the walls group must take
  // none of it either — the routing rule is the member's category, not its wall type, and
  // this is what proves the second truss wall did not need a second rule.
  const girtGroups = Object.fromEntries(
    ALL_TRADES.map((trade) => [trade, new THREE.Group()]),
  ) as Record<Trade, THREE.Group>;
  const girtWall = wall([[0, 0], [4, 0]]);
  girtWall.members = [
    { ...member("stud-000"), category: "stud", material: null },
    { ...member("strapping-inner-girt-000"), category: "strapping", material: "spf" },
    { ...member("strapping-outer-girt-000"), category: "strapping", material: "kdat" },
    { ...member("block-1-000-00"), category: "truss_block", material: "spf" },
    { ...member("block-2-000-00"), category: "truss_block", material: "kdat" },
    { ...member("strapping-jamb-inner-girt-000-0"), category: "strapping", material: "spf" },
    { ...member("strapping-jamb-outer-girt-000-1"), category: "strapping", material: "kdat" },
    { ...member("ladder-head-outer-girt-000"), category: "truss_blocking", material: "kdat" },
    { ...member("ladder-sill-inner-girt-000"), category: "truss_blocking", material: "spf" },
    { ...member("buck-head-000"), category: "buck", material: "struct-1-plywood" },
  ];
  buildWall(girtGroups, girtWall, [], [0, 0], "schematic", PALETTE, registry().picks,
    registry().byUid);
  assert(girtGroups.walls.children.length === 0,
    "No piece of the girt pack is envelope skin — the walls group takes none of it");
  assert(girtGroups.framing.children.length > 0,
    "The girt pack draws with the studs, on the framing toggle");

  const roofGroup = new THREE.Group();
  const roofs = registry();
  buildRoof(roofGroup, {
    uid: "R-1", tag: "R-1", storey: "L1", form: "gable",
    footprint: [[0, 0], [6, 0], [6, 4], [0, 4]], eave_z_m: 3, ridge_z_m: 4.5,
    ridge_direction: "x", assembly: "ROOF-1", surface_area_m2: 26, members: [], provenance: null,
  } as Roof, [0, 0], "schematic", PALETTE, undefined, roofs.picks, roofs.byUid);
  registered(roofGroup, "R-1", "roof", roofs.picks, roofs.byUid, "buildRoof");

  // ** A CLOSURE BAND IS THE WALL'S, NOT THE ROOF'S. ** The roof resolves it (only the roof
  // planes say how high the layer climbs) but it is the wall's own skin carried past the top
  // plate, and it carries that wall's uid. Routing skin by its container instead filed a
  // gable end's whole raking face — five layers of real wall — under the roof toggle, where
  // turning the roof off took the wall with it, and a click on it selected the roof.
  const closureRoof = new THREE.Group();
  const closureWalls = new THREE.Group();
  const closures = registry();
  const closure = {
    ...member("W-1-closure-0-cladding"), parent_uid: "W-1", category: "cladding",
    material: "standing-seam", p0: [0, 0], p1: [6, 0], z0_m: 3, z1_m: 4.5,
    z0_end_m: 3, z1_end_m: 4.5,
  } as Member;
  const ridgeCap = { ...member("ridge-vent-cap"), parent_uid: "R-1", category: "ridge_cap" } as Member;
  buildRoof(closureRoof, {
    uid: "R-1", tag: "R-1", storey: "L1", form: "gable",
    footprint: [[0, 0], [6, 0], [6, 4], [0, 4]], eave_z_m: 3, ridge_z_m: 4.5,
    ridge_direction: "x", assembly: "ROOF-1", surface_area_m2: 26,
    members: [closure, ridgeCap], provenance: null,
  } as Roof, [0, 0], "schematic", PALETTE, undefined, closures.picks, closures.byUid,
    undefined, undefined, closureWalls);
  assert(closureWalls.children.length > 0,
    "The closure band draws into the walls group, so the walls toggle owns it");
  assert(resolveMemberPickUid(closureWalls.children[0] as THREE.Mesh, 0, 0) === "W-1::W-1-closure-0-cladding",
    "Clicking the closure band selects it as the wall's member, not the roof's");
  assert((closures.byUid.get("W-1") ?? []).length > 0,
    "Selecting the wall highlights the closure band that finishes it");
  assert(closureRoof.children.length > 0,
    "The roof keeps the skin it does own — the ridge cap stays on the roof toggle");

  // A stair is nothing *but* members, so every one of its picks now resolves to a tread or a
  // stringer rather than to the stair. The stair is still reachable — from the 2D plan, and
  // from the member inspector's parent link — and still highlights, because its member bucket
  // stays in byUid.
  const stairGroup = new THREE.Group();
  const stairs = registry();
  buildStair(stairGroup, { uid: "ST-1", members: [member("T-1"), member("T-2")] } as Stair,
    [0, 0], "schematic", PALETTE, stairs.picks, stairs.byUid);
  assert(stairs.picks.length > 0 && stairs.picks.every(carriesMemberIdentity),
    "buildStair's picks are all member buckets");
  assert(resolveMemberPickUid(stairs.picks[0], 0, null) === "ST-1::T-1",
    "Clicking the first tread selects that tread");
  assert((stairs.byUid.get("ST-1") ?? []).length > 0,
    "buildStair still indexes its materials so selecting the stair highlights it");

  const openingGroup = new THREE.Group();
  const openings = registry();
  buildOpening(openingGroup, opening(2), wall([[0, 0], [4, 0]]), [0, 0], "schematic", PALETTE,
    undefined, openings.picks, openings.byUid);
  registered(openingGroup, "opening", "opening", openings.picks, openings.byUid, "buildOpening");

  // A rough opening has no filling to click on, so it must register nothing at all.
  const roughGroup = new THREE.Group();
  const rough = registry();
  buildOpening(roughGroup, { ...opening(2), kind: "rough_opening" } as Opening,
    wall([[0, 0], [4, 0]]), [0, 0], "schematic", PALETTE, undefined, rough.picks, rough.byUid);
  assert(rough.picks.length === 0 && roughGroup.children.length === 0,
    "An unfilled rough opening builds nothing and registers nothing");

  const door = { ...opening(2, 0, 2, 0, 1.5), kind: "door", is_door: true } as Opening;
  const bifoldGroup = new THREE.Group();
  const bifoldRegistry = registry();
  buildOpening(bifoldGroup, door, wall([[0, 0], [4, 0]]), [0, 0], "schematic", PALETTE,
    "bifold", bifoldRegistry.picks, bifoldRegistry.byUid);
  assert(bifoldGroup.children.length === 8,
    "A closed bifold renders four frame pieces and four coplanar leaves");

  const sliderGroup = new THREE.Group();
  const sliderRegistry = registry();
  buildOpening(sliderGroup, door, wall([[0, 0], [4, 0]]), [0, 0], "schematic", PALETTE,
    "slide", sliderRegistry.picks, sliderRegistry.byUid, true);
  assert(sliderGroup.children.length === 8,
    "A closed slider renders its frame, stile, track, and two panels");
  assert(new Set(sliderGroup.children.map((child) => child.position.z.toFixed(9))).size === 1,
    "Closed slider panels remain in the wall plane rather than posing open");
}

export function runCanvasObjectGeometryTests() {
  assert(canvasObjectFallbackGeometry("cylinder", 0.4, 1, 0.6).type === "CylinderGeometry",
    "Configured cylinder primitives are rendered before their GLB is ready");
  assert(canvasObjectFallbackGeometry("unsupported", 0.4, 1, 0.6).type === "BoxGeometry",
    "Unknown primitives retain the footprint-box fallback");

  const target = new THREE.Vector3(0, 0, 0);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
  camera.position.set(5, 5, 5);
  camera.lookAt(target);
  const northFromSoutheast = compassBearingScreenDirection(camera, target, 0, 0);
  camera.position.set(-5, 5, 5);
  camera.lookAt(target);
  const northFromSouthwest = compassBearingScreenDirection(camera, target, 0, 0);
  assert(Math.abs(northFromSoutheast[0] - northFromSouthwest[0]) > 0.5,
    "Compass north responds to camera orbit");

  camera.position.set(5, 5, 5);
  camera.lookAt(target);
  const rotatedTrueNorth = compassBearingScreenDirection(camera, target, 0, 90);
  assert(Math.hypot(
    northFromSoutheast[0] - rotatedTrueNorth[0],
    northFromSoutheast[1] - rotatedTrueNorth[1],
  ) > 0.5, "Compass north responds to site true-north rotation");
}

// A generated massing is one group of boxes, not one mesh — but it is still one *object*:
// every part has to answer to the same uid, or clicking an arm would select an arm.
export function runCanvasObjectPartsTests() {
  const group = new THREE.Group();
  const { picks, byUid } = registry();
  const item = {
    uid: "CO-1", tag: "F-1", storey: "L1", kind: "Furniture", type: "FURN-SOFA-84",
    domain: "furniture", room: null, position_m: [2, 3] as Vec2, rotation: 90,
    host: null, attachment: null,
  } as CanvasObject;
  const parts: ModelPart[] = [
    { center: [0, 0.3, 0.4], size: [2, 0.2, 0.8], color: "#8c8f95" },
    { center: [-0.8, 0, 0.3], size: [0.14, 0.9, 0.6], color: "#8c8f95" },
    { center: [0, -0.1, 0.45], size: [1.6, 0.6, 0.12], color: "#adb0b3" },
  ];
  const built = buildCanvasObjectParts(group, item, parts, [0, 0], "schematic", 1.5, picks, byUid);

  assert(built instanceof THREE.Group, "A multi-part massing builds a group, not a single mesh");
  assert(built.children.length === parts.length, "Every part becomes its own box mesh");
  registered(group, "CO-1", "canvas_object", picks, byUid, "buildCanvasObjectParts");
  assert(picks.filter((mesh) => mesh.userData.uid === "CO-1").length === parts.length,
    "Clicking any part selects the whole object: all of them are raycast targets for one uid");
  // Two roles, three parts — the highlight pass must reach both materials and no duplicates.
  assert((byUid.get("CO-1") ?? []).length === 2,
    "One material per distinct colour, shared across the parts that use it");

  // Placement lives on the group; a part only carries its local offset, mapped plan → scene
  // as (x, z, -y). Nothing may be baked into the meshes themselves.
  assert(Math.abs(built.position.y - 1.5) < 1e-9, "The group sits at the object's base elevation");
  assert(Math.abs(built.position.x - 2) < 1e-9 && Math.abs(built.position.z + 3) < 1e-9,
    "The group carries the plan position");
  assert(Math.abs(built.rotation.y - Math.PI / 2) < 1e-9, "The group carries the plan rotation");
  const back = built.children[0] as THREE.Mesh;
  assert(Math.abs(back.position.x) < 1e-9 && Math.abs(back.position.y - 0.4) < 1e-9
    && Math.abs(back.position.z + 0.3) < 1e-9, "A part offset maps (x, y, z) -> (x, z, -y)");
  assert(back.rotation.y === 0, "Rotation is the group's job, never the part's");
}

// The whole-house glb only becomes the primary scene when its nodes map back to trades (and,
// for selectable elements, model uids). A single untagged "building" node — today's emitter
// output — must classify as unstructured so the model.json baseline stands with no regression.
export function runWholeHouseGlbTests() {
  assert(wholeHouseGlbAssignment("building", undefined) === null,
    "The monolithic color-bucketed node is unstructured → glb is not promoted");
  assert(wholeHouseGlbAssignment(undefined, {}) === null, "A node with no trade is unassigned");
  assert(wholeHouseGlbAssignment("not-a-trade|wall|W-1", undefined) === null,
    "An unknown trade token does not classify");

  const fromExtras = wholeHouseGlbAssignment(undefined, { trade: "walls", uid: "W-1", kind: "wall" });
  assert(fromExtras !== null && fromExtras.trade === "walls" && fromExtras.uid === "W-1"
    && fromExtras.kind === "wall", "glTF extras assign trade + uid + selection kind");

  const fromName = wholeHouseGlbAssignment("furniture|canvas_object|CO-9", undefined);
  assert(fromName !== null && fromName.trade === "furniture" && fromName.uid === "CO-9"
    && fromName.kind === "canvas_object", "The <trade>|<kind>|<uid> name convention is the fallback");

  const envelopeOnly = wholeHouseGlbAssignment("roof", undefined);
  assert(envelopeOnly !== null && envelopeOnly.trade === "roof" && envelopeOnly.uid === null
    && envelopeOnly.kind === null, "Non-selectable envelope geometry only needs its trade");

  const extrasWinName = wholeHouseGlbAssignment("walls|wall|FROM-NAME", { trade: "concrete", uid: "FROM-EXTRAS", kind: "wall" });
  assert(extrasWinName !== null && extrasWinName.trade === "concrete" && extrasWinName.uid === "FROM-EXTRAS",
    "Explicit extras take precedence over the name convention");

  // B7 widened the kind vocabulary on both sides of the export
  // (emit/gltf/emitter.py::_SELECTION_KINDS ↔ state/store.ts SelectionKind).
  for (const kind of ["opening", "room", "solid", "footing_bedding", "floor", "roof", "stair"]) {
    const widened = wholeHouseGlbAssignment(undefined, { trade: "concrete", uid: "X-1", kind });
    assert(widened !== null && widened.kind === kind, `glb nodes may declare kind "${kind}"`);
  }
  const bogus = wholeHouseGlbAssignment(undefined, { trade: "concrete", uid: "X-1", kind: "gutter" });
  assert(bogus !== null && bogus.kind === null,
    "A kind outside the shared vocabulary is dropped rather than trusted");
}

// Default / reset framing (→ TODO: "the 'default zoom' for reset is poorly calculated").
export function runViewFramingTests() {
  const verticalFov = THREE.MathUtils.degToRad(50);
  const aspect = 16 / 9;
  // A house-shaped box: long in plan, comparatively low. The old bounding-sphere fit dollied
  // back far enough to contain the plan diagonal, which is why the model landed small.
  const house = new THREE.Box3(new THREE.Vector3(-10, 0, -6), new THREE.Vector3(10, 8, 6));
  const target = house.getCenter(new THREE.Vector3());
  const theta = Math.PI * 0.25;
  const phi = VIEW_FIT_POLAR_ANGLE;
  const radius = frameRadiusForBounds(house, target, theta, phi, verticalFov, aspect);

  const sphereRadius = house.getBoundingSphere(new THREE.Sphere()).radius;
  const limitingHalfFov = Math.min(verticalFov / 2, Math.atan(Math.tan(verticalFov / 2) * aspect));
  const oldFit = sphereRadius / Math.sin(limitingHalfFov) * 1.15;
  assert(radius < oldFit, "The exact corner fit must frame a house tighter than a bounding-sphere fit");

  // Every corner has to land inside the frustum, or "frame the whole model" does not.
  const camera = new THREE.PerspectiveCamera(50, aspect, 0.05, 5000);
  camera.position.set(
    target.x + radius * Math.sin(phi) * Math.cos(theta),
    target.y + radius * Math.cos(phi),
    target.z + radius * Math.sin(phi) * Math.sin(theta));
  camera.lookAt(target);
  camera.updateMatrixWorld(true);
  for (const x of [house.min.x, house.max.x]) {
    for (const y of [house.min.y, house.max.y]) {
      for (const z of [house.min.z, house.max.z]) {
        const ndc = new THREE.Vector3(x, y, z).project(camera);
        assert(Math.abs(ndc.x) <= 1 && Math.abs(ndc.y) <= 1,
          `Corner (${x}, ${y}, ${z}) must sit inside the framed view`);
      }
    }
  }

  // A narrow split pane needs to pull further back than a wide one for the same building —
  // which is why reset recomputes the fit instead of replaying a stored snapshot.
  const narrow = frameRadiusForBounds(house, target, theta, phi, verticalFov, 0.6);
  assert(narrow > radius, "A narrower pane must dolly further out");

  assert(frameRadiusForBounds(new THREE.Box3(new THREE.Vector3(), new THREE.Vector3()),
    new THREE.Vector3(), theta, phi, verticalFov, aspect) === VIEW_FIT_MIN_RADIUS_M,
    "A degenerate box still yields a usable dolly distance");

  // Wheel normalization: a line-mode notch and a pixel-mode flick must land in the same range.
  assert(normalizedWheelDeltaPx(3, 1) === 48, "Line-mode deltas are converted to pixels");
  assert(normalizedWheelDeltaPx(4000, 0) === WHEEL_MAX_STEP_PX,
    "A trackpad flick is clamped so one gesture cannot cross the whole zoom range");
  assert(normalizedWheelDeltaPx(-4000, 0) === -WHEEL_MAX_STEP_PX, "Clamping is symmetric");

  // Dolly range: wheel, pinch and the on-screen buttons share one clamp, so no input can put
  // the camera somewhere another input cannot get it back from.
  assert(clampDollyRadius(0) === MIN_DOLLY_RADIUS_M && clampDollyRadius(1e6) === MAX_DOLLY_RADIUS_M,
    "A dolly distance is pinned to the usable range at both ends");
  assert(clampDollyRadius(12) === 12, "A distance already in range is left alone");

  // A press of zoom-out followed by zoom-in has to land back where it started, or the buttons
  // walk the view somewhere new every time you change your mind.
  const pressed = clampDollyRadius(clampDollyRadius(12 * BUTTON_DOLLY_FACTOR) / BUTTON_DOLLY_FACTOR);
  assert(Math.abs(pressed - 12) < 1e-9, "Zoom out then in returns the camera to its start");
  assert(clampDollyRadius(12 * BUTTON_DOLLY_FACTOR) > 12 && BUTTON_DOLLY_FACTOR > 1,
    "A zoom-out press moves the camera further away");

  // Pinch: the span between the fingers maps to the dolly inversely, anchored on the span the
  // gesture opened at rather than integrated per move.
  assert(pinchDollyRadius(20, 100, 200) === 10, "Fingers twice as far apart halve the distance");
  assert(pinchDollyRadius(20, 200, 100) === 40, "Fingers half as far apart double it");
  assert(pinchDollyRadius(20, 100, 100) === 20, "A span back at its opening value restores the zoom");
  assert(pinchDollyRadius(20, 100, 0) === MAX_DOLLY_RADIUS_M,
    "A degenerate span cannot produce a non-finite dolly distance");
  assert(pinchDollyRadius(MIN_DOLLY_RADIUS_M, 100, 400) === MIN_DOLLY_RADIUS_M,
    "Pinch honours the same near clamp the wheel does");

  // Picking has to honour the same visibility the renderer does, or a hidden trade keeps
  // intercepting clicks aimed at whatever it was hiding.
  const tradeGroup = new THREE.Group();
  const layerMesh = new THREE.Mesh();
  tradeGroup.add(layerMesh);
  assert(isRenderedInScene(layerMesh), "A visible mesh under a visible group is pickable");
  tradeGroup.visible = false;
  assert(!isRenderedInScene(layerMesh), "Hiding the trade group takes its meshes out of the raycast");
  tradeGroup.visible = true;
  layerMesh.visible = false;
  assert(!isRenderedInScene(layerMesh), "Hiding one assembly layer takes just that mesh out");
}

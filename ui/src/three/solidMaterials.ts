// Surface finishes for resolved solids (→ 21 §3D panel). Every non-wall, non-roof prism the
// resolver produces — slabs, footings, pads, 6x6 posts, beams, guard rails, dowels, thermal
// breaks, connectors, sump pits, vent risers, fascia, gutters and flashings — arrives as a
// `Solid` with a `category` and an optional `assembly`. Until this module existed they all
// rendered as one concrete grey, which made a painted post, an aluminium gutter and a footing
// visually indistinguishable.
//
// Two parallel palettes are the known duplication here (same as three/members.ts CATEGORY_COLOR
// for framing members): these colours mirror emit/gltf/emitter.py `_PALETTE`, whose linear 0..1
// RGB values are the source of truth for the export. Change one, change the other.
import * as THREE from "three";
import type { Catalog, Solid } from "../model/types";
import { materialColor, materialOpacity, type ResolvedNordicPalette } from "../nordic/palette";
import type { Trade } from "../state/vocabulary";

// solid category → sRGB hex, mirroring emit/gltf/emitter.py `_PALETTE` (the same keys, its
// linear triples rounded to 8-bit). Categories with no entry fall back to the theme's concrete
// grey, matching the emitter's `_FALLBACK`.
export const SOLID_CATEGORY_COLOR: Record<string, number> = {
  slab: 0x8c8f91,
  footing: 0x7a7d80,
  pad: 0x808285,
  column: 0x99999e, // concrete/wood posts (sonotube, 6x6 pillars)
  beam: 0x9e7547, // PT / built-up wood beams — wood, never concrete
  railing: 0xcccfd4, // aluminium guard
  dowel: 0x338c59, // GFRP rebar (green)
  thermal_break: 0xf28c26, // XPS foam block (orange)
  connector: 0x595c61, // galvanized hardware
  sump: 0x4d5257, // pit
  vent: 0xe0e0db, // painted vent pipe
  // routed plumbing runs (engine resolve/mep.py _emit_pipe_solids), riser-diagram colors —
  // mirrors emit/gltf/palette.py, change one change the other.
  pipe_drain: 0x333338, // ABS/PVC waste, near-black
  pipe_vent: 0xe0e0db, // same as the vent risers
  pipe_water_hot: 0xcc4038, // red PEX
  pipe_water_cold: 0x3366bf, // blue PEX
  pipe_gas: 0xd9bf33, // yellow CSST
  pipe_radon: 0x8c9499, // bare gray
  fascia: 0xebebe6, // PVC fascia
  gutter: 0xd9dbde, // metal gutter
  flashing: 0xbfc4cc, // metal flashing
  // A dropped soffit is painted gwb, like the ceiling it hangs under — not concrete, which
  // is what the fallback would have made the second-floor HVAC chase. Same triple the glTF
  // palette's "soffit" carries (0.88, 0.88, 0.85), so the viewer and the export agree.
  soffit: 0xe0e0d9,
};

// solid category → visibility trade, mirroring packages/engine/src/typehaus/emit/trades.py
// `SOLID_CATEGORY_TRADE` (change one, change the other — tests/test_solid_trade_parity.py checks
// both directions). Every solid used to be handed to the `concrete` group regardless of what it
// was, which filed the standalone beams and posts away from the studs and rafters they carry,
// and put all 791 routed pipe solids behind the Concrete toggle instead of Plumbing.
//
// Categories absent here take the `concrete` fallback. `railing` and `connector` are on it
// deliberately, not by omission — see the engine table for why.
export const SOLID_CATEGORY_TRADE: Record<string, Trade> = {
  // Standalone structure: an authored Beam/Post is the same lumber as the members it carries,
  // and an authored ridge beam already appears under framing (the engine re-types it as a
  // FramedMember owned by the roof).
  beam: "framing",
  column: "framing",
  // Routed plumbing runs, one category per system (engine resolve/mep.py).
  pipe_drain: "plumbing",
  pipe_vent: "plumbing",
  pipe_water_hot: "plumbing",
  pipe_water_cold: "plumbing",
  pipe_gas: "plumbing",
  pipe_radon: "plumbing",
  // Bath/dryer exhaust and the radon riser.
  vent: "mechanical",
  // Fenestration and the extrusions that hold it, plus the rainscreen base closure — envelope
  // detail, hidden with the openings rather than with the concrete.
  glazing: "openings",
  glazing_trim: "openings",
  bug_screen: "openings",
  // Roof edge trim.
  fascia: "roof",
  gutter: "roof",
  flashing: "roof",
  // A dropped soffit is framed and finished like the ceiling it hangs under.
  soffit: "floors",
  // Equal to the fallback, named so the parity test's "unclassified" list stays meaningful.
  slab: "concrete",
  footing: "concrete",
  pad: "concrete",
  dowel: "concrete",
  thermal_break: "concrete",
};

/** The trade group a resolved solid belongs to (engine: emit/trades.py::solid_trade). */
export function solidTrade(solid: Pick<Solid, "category">): Trade {
  return SOLID_CATEGORY_TRADE[solid.category?.toLowerCase() ?? ""] ?? "concrete";
}

// Shop-finished metal accessories read as metal, not matte plastic: a gutter, a drip flashing
// and an aluminium guard all catch the environment light the way the standing-seam wall finish
// does. Everything else stays fully dielectric.
const METALLIC_SOLID_CATEGORIES = new Set(["railing", "gutter", "flashing", "connector"]);

// Painted finishes name their colour in the material ref ("post-paint-white"). The served
// catalog (server/model_json.py) carries only tag/name/R/perm/density, so the engine's authored
// `Material.color` never reaches the browser and familyOf() cannot classify the ref. Recognise
// the paint word here, exactly as the exporter recognises a "white" masonry ref
// (emit/gltf/emitter.py::_is_white_brick), rather than letting a painted post fall through to a
// neutral grey.
const PAINT_COLOR: Record<string, number> = {
  white: 0xf4f2ee,
  black: 0x2b2b2b,
  grey: 0x9a9a97,
  gray: 0x9a9a97,
};

export function paintedFinishColor(materialRef: string | null | undefined): number | null {
  if (!materialRef) return null;
  const ref = materialRef.toLowerCase();
  if (!ref.includes("paint") && !ref.includes("enamel")) return null;
  for (const [word, color] of Object.entries(PAINT_COLOR)) if (ref.includes(word)) return color;
  return null;
}

// The finish colour for one resolved solid, mirroring emit/gltf/emitter.py::_solid_color:
// an authored assembly wins (its structure layer's material is the visible face), otherwise the
// per-category palette. Returned as a THREE-ready sRGB integer.
export function solidColor(
  solid: Pick<Solid, "category" | "assembly">,
  catalog: Catalog | undefined,
  palette: ResolvedNordicPalette,
): number {
  const assembly = solid.assembly
    ? catalog?.assemblies.find((candidate) => candidate.tag === solid.assembly)
    : undefined;
  const layers = assembly?.layers ?? [];
  const layer = layers.find((candidate) => candidate.function === "structure") ?? layers[0];
  if (layer) {
    // Pass the catalog's materials through: without them `materialColor` never sees an
    // authored `Material.color`, so every assembly-backed solid fell to its family tone
    // (the porch composite deck's authored #8a7f70 among them).
    return paintedFinishColor(layer.material)
      ?? new THREE.Color(materialColor(layer.material, palette, catalog?.materials)).getHex();
  }
  return SOLID_CATEGORY_COLOR[solid.category] ?? palette.member.concrete;
}

// The opacity of one resolved solid, from its assembly's visible layer. A material declares
// that it is see-through by authoring an alpha byte on its colour (`#RRGGBBAA`); nothing is
// inferred from the category or the tag, so a new translucent material needs no code here.
// Mirrors emit/gltf/palette.py::_hex_rgba + emit/gltf/scene.py's BLEND/doubleSided switch —
// change one, change the other, or the `.glb` and the live viewer disagree.
export function solidOpacity(
  solid: Pick<Solid, "assembly">,
  catalog: Catalog | undefined,
): number {
  const assembly = solid.assembly
    ? catalog?.assemblies.find((candidate) => candidate.tag === solid.assembly)
    : undefined;
  const layers = assembly?.layers ?? [];
  const layer = layers.find((candidate) => candidate.function === "structure") ?? layers[0];
  return layer ? materialOpacity(layer.material, catalog?.materials) : 1;
}

export function createSolidMaterial(
  solid: Pick<Solid, "category" | "assembly">,
  catalog: Catalog | undefined,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
): THREE.MeshStandardMaterial {
  const metallic = METALLIC_SOLID_CATEGORIES.has(solid.category);
  const opacity = solidOpacity(solid, catalog);
  const translucent = opacity < 1;
  return new THREE.MeshStandardMaterial({
    color: solidColor(solid, catalog, palette),
    roughness: metallic ? 0.35 : translucent ? 0.15 : mode === "nordic" ? 0.9 : 1,
    metalness: metallic ? 0.8 : 0,
    flatShading: mode === "schematic",
    transparent: translucent,
    opacity,
    // A pane is a thin prism: without both faces it disappears from one side.
    side: translucent ? THREE.DoubleSide : THREE.FrontSide,
    depthWrite: !translucent,
  });
}

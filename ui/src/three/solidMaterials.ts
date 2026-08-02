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
import {
  materialColor, materialOpacity, statesOwnColor, type ResolvedNordicPalette,
} from "../nordic/palette";
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
  // In-line supply devices, one category per PipeAccessoryKind. Brass for anything with a
  // body you turn; the arrestor is a sealed steel chamber and the seal is not metal at all.
  main_shutoff: 0xb89447, // brass
  shutoff: 0xb89447,
  backflow_preventer: 0xb89447,
  vacuum_breaker: 0xb89447,
  ro_stub: 0xb89447,
  water_hammer_arrestor: 0x9ea3a8,
  penetration_seal: 0xf2b859,
  fascia: 0xebebe6, // PVC fascia
  gutter: 0xd9dbde, // metal gutter
  flashing: 0xbfc4cc, // metal flashing
  // Stormwater below the gutter — the leader is the gutter's own aluminium, the buried three
  // read as perforated tile and washed rock so a drainage view is not one grey.
  downspout: 0xd9dbde, // leader, same aluminium as the gutter it drains
  drain_tile: 0x292624, // corrugated HDPE tile — warmer than the ABS `pipe_drain` beside it
  french_drain: 0x9e998f, // washed-rock trench
  drywell: 0x857f78, // soakaway aggregate
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
  // In-line supply devices (engine resolve/mep.py::_resolve_pipe_accessory), one category
  // per PipeAccessoryKind — a solid's category is what the inspector labels it with, and
  // "pipe accessory" tells a reader nothing about which device they clicked.
  main_shutoff: "plumbing",
  shutoff: "plumbing",
  backflow_preventer: "plumbing",
  vacuum_breaker: "plumbing",
  water_hammer_arrestor: "plumbing",
  ro_stub: "plumbing",
  penetration_seal: "plumbing",
  // Bath/dryer exhaust and the radon riser.
  vent: "mechanical",
  // Fenestration and the extrusions that hold it, plus the rainscreen base closure — envelope
  // detail, hidden with the openings rather than with the concrete.
  glazing: "openings",
  glazing_trim: "openings",
  bug_screen: "openings",
  // Roof edge trim.
  fascia: "roof",
  flashing: "roof",
  // Stormwater. A gutter hangs on the roof edge but *is* the head of a run that continues
  // down the leader, through the perimeter tile and out to daylight, so the whole run rides
  // one toggle instead of being split between roof and concrete. The last three have no
  // instances yet — declared so the first one authored is routed, not poured into concrete.
  gutter: "drainage",
  downspout: "drainage",
  sump: "drainage",
  drain_tile: "drainage",
  french_drain: "drainage",
  drywell: "drainage",
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
const METALLIC_SOLID_CATEGORIES = new Set([
  "railing", "gutter", "downspout", "flashing", "connector",
]);

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
  solid: Pick<Solid, "category" | "assembly" | "material">,
  catalog: Catalog | undefined,
  palette: ResolvedNordicPalette,
): number {
  // A trim run names its material directly rather than through an assembly, and that ref wins
  // over the category — it is how a gutter ordered in the roof's trim coil says so. Only a
  // material the catalog actually describes counts (materialColor's family inference would
  // repaint every generic "aluminum" run), so a run that never stated a colour is unchanged.
  if (statesOwnColor(solid.material, catalog?.materials)) {
    return new THREE.Color(materialColor(solid.material, palette, catalog?.materials)).getHex();
  }
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
  solid: Pick<Solid, "category" | "assembly" | "material">,
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

// Solid category → what a person calls it. The Inspector used to print the raw category as
// its heading, which reads fine for `slab` and badly for everything with an underscore in
// it — and worst of all for a family name: "pipe accessory" is true of a shutoff, a backflow
// preventer and a can of foam alike, so it told a reader nothing about the thing they had
// just clicked. Categories are now per-device (see SOLID_CATEGORY_TRADE above); this map
// gives the rest of them sentence case too.
//
// Anything absent falls back to the category with its underscores opened out, so a new
// category is readable on the day it lands and gets a proper name when someone has one.
const SOLID_CATEGORY_LABEL: Record<string, string> = {
  main_shutoff: "Main shutoff valve",
  shutoff: "Isolation valve",
  backflow_preventer: "Backflow preventer",
  vacuum_breaker: "Vacuum breaker",
  water_hammer_arrestor: "Water-hammer arrestor",
  ro_stub: "RO tap provision (capped)",
  penetration_seal: "Envelope penetration seal",
  pipe_drain: "Waste pipe",
  pipe_vent: "Vent pipe",
  pipe_water_hot: "Hot water pipe",
  pipe_water_cold: "Cold water pipe",
  pipe_gas: "Gas pipe",
  pipe_radon: "Radon pipe",
  drain_tile: "Drain tile",
  french_drain: "French drain",
  drywell: "Drywell",
  downspout: "Downspout",
  sump: "Sump pit",
  thermal_break: "Thermal break",
  bug_screen: "Rainscreen base closure",
  glazing_trim: "Glazing trim",
  window_trim: "Window casing",
  opening_frame: "Opening frame",
  ridge_cap: "Ridge cap",
  corner_trim: "Corner trim",
};

export function solidCategoryLabel(category: string | null | undefined): string {
  if (!category) return "Solid";
  const key = category.trim().toLowerCase();
  const known = SOLID_CATEGORY_LABEL[key];
  if (known) return known;
  const opened = key.replace(/_/g, " ");
  return opened.charAt(0).toUpperCase() + opened.slice(1);
}

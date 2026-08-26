// Surface finishes for resolved solids (→ 21 §3D panel). Every non-wall, non-roof prism the
// resolver produces — slabs, footings, pads, 6x6 posts, beams, guard rails, dowels, thermal
// breaks, connectors, sump pits, vent risers, fascia, gutters and flashings — arrives as a
// `Solid` with a `category` and an optional `assembly`. Until this module existed they all
// rendered as one concrete grey, which made a painted post, an aluminium gutter and a footing
// visually indistinguishable.
//
// These colours and the trade grouping below are generated, not authored here — see
// packages/engine/src/typehaus/emit/vocabulary_manifest.py. `emit/gltf/palette.py`'s
// `_PALETTE` is the one Python source for both this table and three/members.ts
// CATEGORY_COLOR (the same dict; a slab and a stud just happen to live in the same
// authored table). `emit/trades.py`'s `SOLID_CATEGORY_TRADE` is the source for the trade
// grouping. The per-category rationale (why a guard's infill is split from its frame, why
// a sleeve rides plumbing, why the whole stormwater run is one toggle, and so on) lives as
// comments on those two Python tables now — this file has no literal left to hang a comment
// on. Change a colour or a trade there and regenerate ui/src/generated/vocabulary.json; do
// not hand-edit this file or the JSON.
import * as THREE from "three";
import type { Catalog, Solid } from "../model/types";
import {
  materialColor, materialOpacity, statesOwnColor, type ResolvedNordicPalette,
} from "../nordic/palette";
import type { Trade } from "../state/vocabulary";
import { NORDIC_ROUGHNESS, standardMaterial } from "./surfaces";
import vocabulary from "../generated/vocabulary.json";

// solid category → sRGB hex. Categories with no entry fall back to the theme's concrete
// grey, matching the emitter's `_FALLBACK`.
export const SOLID_CATEGORY_COLOR: Record<string, number> = vocabulary.solidColors;

// solid category → visibility trade. Every solid used to be handed to the `concrete` group
// regardless of what it was, which filed the standalone beams and posts away from the studs
// and rafters they carry, and put all 791 routed pipe solids behind the Concrete toggle
// instead of Plumbing (→ emit/trades.py). Categories absent here take the `concrete`
// fallback, which now means only what it says: the pours, and the dowels and thermal-break
// blocks cast into them.
export const SOLID_CATEGORY_TRADE: Record<string, Trade> = vocabulary.solidTrades as Record<string, Trade>;

/** The trade group a resolved solid belongs to (engine: emit/trades.py::solid_trade). */
export function solidTrade(solid: Pick<Solid, "category">): Trade {
  return SOLID_CATEGORY_TRADE[solid.category?.toLowerCase() ?? ""] ?? "concrete";
}

// Shop-finished metal accessories read as metal, not matte plastic: a gutter, a drip flashing
// and an aluminium guard all catch the environment light the way the standing-seam wall finish
// does. Everything else stays fully dielectric.
// `railing_glass` is deliberately absent: metalness is keyed on category alone, so a glass
// lite listed here renders as dark metal however its material is authored.
const METALLIC_SOLID_CATEGORIES = new Set([
  "railing", "railing_infill", "gutter", "downspout", "flashing", "connector",
  "snow_guard", "seam_clamp", "panel_strap",
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

// The opacity of one resolved solid. A material declares that it is see-through by authoring
// an alpha byte on its colour (`#RRGGBBAA`); nothing is inferred from the category or the tag,
// so a new translucent material needs no code here. Mirrors emit/gltf/palette.py::_hex_rgba +
// emit/gltf/scene.py's BLEND/doubleSided switch — change one, change the other, or the `.glb`
// and the live viewer disagree.
//
// The direct `solid.material` ref is read first, exactly as `solidColor` above reads it: this
// used to walk the assembly ONLY, so a solid whose translucency came from a material ref (a
// glass railing lite, a trim run in a tinted coil) exported translucent in the `.glb` and
// rendered opaque — and single-sided, since `createSolidMaterial` keys `transparent` / `side` /
// `depthWrite` off this — in the live viewer. Colour and opacity have to walk the same ladder
// or a pane picks up its glass tint and none of its transparency.
export function solidOpacity(
  solid: Pick<Solid, "assembly" | "material">,
  catalog: Catalog | undefined,
): number {
  if (statesOwnColor(solid.material, catalog?.materials)) {
    return materialOpacity(solid.material, catalog?.materials);
  }
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
  return standardMaterial(solidColor(solid, catalog, palette), mode, {
    roughness: metallic ? 0.35 : translucent ? 0.15 : mode === "nordic" ? NORDIC_ROUGHNESS.matte : 1,
    metalness: metallic ? 0.8 : 0,
    transparent: translucent,
    opacity,
    // A pane is a thin prism: without both faces it disappears from one side.
    side: translucent ? THREE.DoubleSide : THREE.FrontSide,
    depthWrite: !translucent,
  });
}


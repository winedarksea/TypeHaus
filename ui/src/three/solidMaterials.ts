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
import { materialColor, type ResolvedNordicPalette } from "../nordic/palette";

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
  fascia: 0xebebe6, // PVC fascia
  gutter: 0xd9dbde, // metal gutter
  flashing: 0xbfc4cc, // metal flashing
};

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

export function createSolidMaterial(
  solid: Pick<Solid, "category" | "assembly">,
  catalog: Catalog | undefined,
  mode: "nordic" | "schematic",
  palette: ResolvedNordicPalette,
): THREE.MeshStandardMaterial {
  const metallic = METALLIC_SOLID_CATEGORIES.has(solid.category);
  return new THREE.MeshStandardMaterial({
    color: solidColor(solid, catalog, palette),
    roughness: metallic ? 0.35 : mode === "nordic" ? 0.9 : 1,
    metalness: metallic ? 0.8 : 0,
    flatShading: mode === "schematic",
  });
}

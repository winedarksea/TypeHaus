// The Nordic presentation preset for the UI — a TS mirror of the engine's single
// palette module (emit/draw/palette.py, #24, → 21 §Nordic preset). The light tokens mirror
// export colors; the dark tokens are UI-only so print/export output remains unchanged.

// CSS variables keep SVG surfaces live when the theme changes without requiring every
// drawing component to duplicate a subscription. Three.js receives resolved values below.
export const NORDIC_BG = "var(--bg)";
export const NORDIC_INK = "var(--ink)";
export const NORDIC_LINE = "var(--line)";
export const NORDIC_ACCENT = "var(--accent)";

// Material colors fall back through hatch families keyed by material name substrings,
// mirroring palette.material_color's family lookup.
export const HATCH_FAMILY_COLOR: Record<string, string> = {
  lumber: "var(--material-lumber)", osb: "var(--material-osb)", rigid: "var(--material-rigid)",
  batt: "var(--material-batt)", gypsum: "var(--material-gypsum)", membrane: "var(--material-membrane)",
  siding: "var(--material-siding)", metal: "var(--material-metal)", concrete: "var(--material-concrete)",
  masonry: "var(--material-masonry)",
};

export const CONTROL_COLOR: Record<string, string> = {
  air: "var(--control-air)", water: "var(--control-water)", vapor: "var(--control-vapor)", thermal: "var(--control-thermal)",
};

/**
 * How a floor finish behaves under light. Colour is *not* here — it comes from the catalog
 * material whose tag is the finish string (`materialColor`), so the library, the .glb and
 * the viewer all read one definition. What is here is the surface, which no material field
 * carries: under a single light source four flat fills of similar value are hard to tell
 * apart, and the roughness is what actually separates carpet from tile on screen.
 *
 * Keyed by the finish strings the plan authors. An unlisted finish gets `DEFAULT_FLOOR_SURFACE`
 * rather than nothing, so a new finish renders as a plausible matte floor from the day it is
 * authored instead of disappearing.
 */
export interface FloorSurface {
  readonly roughness: number;
  readonly metalness: number;
}

export const DEFAULT_FLOOR_SURFACE: FloorSurface = { roughness: 0.8, metalness: 0 };

export const FLOOR_FINISH_SURFACE: Record<string, FloorSurface> = {
  // Pile scatters everything; no specular lobe at all.
  carpet: { roughness: 1, metalness: 0 },
  // Site-finished oak and a factory wear layer both keep a low sheen — enough to catch a
  // highlight, not enough to mirror. LVP reads a touch glossier than oak.
  oak: { roughness: 0.55, metalness: 0 },
  lvp: { roughness: 0.45, metalness: 0 },
  // Glazed porcelain is the shiniest thing on any of these floors.
  tile: { roughness: 0.2, metalness: 0 },
  // A sealer leaves the slab flat but not dead — matte, slightly above carpet.
  "sealed-concrete": { roughness: 0.85, metalness: 0 },
  // Rolled rubber is dead matte and dark.
  rubber: { roughness: 0.95, metalness: 0 },
};

/** The lighting response for a floor finish; never undefined. */
export function floorSurface(finish: string | null | undefined): FloorSurface {
  return (finish && FLOOR_FINISH_SURFACE[finish]) || DEFAULT_FLOOR_SURFACE;
}

const FALLBACK = "var(--material-fallback)";

export interface ResolvedNordicPalette {
  bg: string;
  edge: string;
  highlight: string;
  material: Record<string, string>;
  member: Record<string, number>;
}

export const RESOLVED_NORDIC_PALETTE: Record<"light" | "dark", ResolvedNordicPalette> = {
  light: {
    bg: "#f4f2ed", edge: "#4a463d", highlight: "#2a3d45",
    material: { lumber: "#d8c9a6", osb: "#c9a86a", rigid: "#e8d64f", batt: "#f3c6d0", gypsum: "#efeae2", membrane: "#4a4a4a", siding: "#b8bcc0", metal: "#6b7076", concrete: "#a9a9a9", masonry: "#9c5a45", fallback: "#cfc9bd" },
    member: { wood: 0xb3854f, concrete: 0xb0b0b0 },
  },
  dark: {
    bg: "#2E3440", edge: "#D8DEE9", highlight: "#88C0D0",
    material: { lumber: "#D6B06F", osb: "#D09A57", rigid: "#EBCB8B", batt: "#D9A4B2", gypsum: "#D8DEE9", membrane: "#BFC8D5", siding: "#AEB8C6", metal: "#9AA8BA", concrete: "#B0B8C4", masonry: "#A86550", fallback: "#C4BDAE" },
    member: { wood: 0xd6b06f, concrete: 0xb0b8c4 },
  },
};

// Heuristic family lookup: match a hatch/material identifier against the known families.
// The engine sends a resolved family per layer only in the section card; for the plan we
// infer from the material ref string so both surfaces still agree on wood/gyp/insulation.
export function familyOf(materialRef: string | null | undefined): string | null {
  if (!materialRef) return null;
  const s = materialRef.toLowerCase();
  const table: [string, string][] = [
    ["gyp", "gypsum"],
    ["dry", "gypsum"],
    ["osb", "osb"],
    ["zip", "osb"],
    ["ply", "osb"],
    ["stud", "lumber"],
    ["lumber", "lumber"],
    ["wood", "lumber"],
    ["spf", "lumber"],
    ["rigid", "rigid"],
    ["xps", "rigid"],
    ["eps", "rigid"],
    ["poly", "rigid"],
    ["batt", "batt"],
    ["mineral", "batt"],
    ["fiberglass", "batt"],
    ["cellulose", "batt"],
    ["wrb", "membrane"],
    ["membrane", "membrane"],
    ["barrier", "membrane"],
    ["siding", "siding"],
    ["clad", "siding"],
    // Cellular-PVC trim: the derived fascia / soffit / drip members name it, and without an
    // entry they read as the neutral `fallback` rather than as painted trim.
    // (`air-barrier` already lands on "membrane" via the "barrier" needle above.)
    ["pvc", "siding"],
    ["metal", "metal"],
    ["seam", "metal"],
    ["steel", "metal"],
    ["concrete", "concrete"],
    ["conc", "concrete"],
    ["slab", "concrete"],
    ["brick", "masonry"],
    ["masonry", "masonry"],
    ["cmu", "masonry"],
    ["block", "masonry"],
    ["stone", "masonry"],
    ["veneer", "masonry"],
  ];
  for (const [needle, fam] of table) if (s.includes(needle)) return fam;
  return null;
}

// Material refs whose colour is fixed by their finish rather than inferred from their family.
// Mirrors _FINISH_BASE in packages/engine/src/typehaus/emit/gltf/palette.py — the .glb and the
// viewer must agree, and the family guess is wrong for finish variants (a charcoal trim coil
// is "metal" by family, which would paint it the palette's blue-grey).
const FINISH_BASE: Readonly<Record<string, string>> = {
  "metal-dark-exterior": "#1c1f24",
  // The exposed-fastener PBR panel: the same white as the seamed skin (0xE8E8E2), which is
  // what createStandingSeamMaterial paints it. Mirrors _FINISH_BASE in emit/gltf/palette.py.
  "ribbed-panel": "#e8e8e2",
  // Cellular PVC trim (garage fascia/soffit) is factory-white, not the "siding" family's
  // blue-grey the substring guess falls to. Mirrors _FINISH_BASE in emit/gltf/palette.py.
  "pvc-cellular": "#f4f2ee",
};

// The authored-appearance slice of a catalog material (ui/src/model/types.ts MaterialSpec).
// Structural so palette.ts stays free of model imports and tests can pass literals.
export interface MaterialAppearance {
  readonly tag: string;
  readonly color?: string | null;
  readonly finish?: string | null;
  // A sealer/stain rather than a covering: it colours what it is applied over and adds no
  // thickness, so nothing draws a plane for it (see `buildRoomFloor`).
  readonly coating?: boolean | null;
}

/**
 * Does this ref state its own colour — a named finish, or a catalog material with an authored
 * `color` — rather than leaving `materialColor` to guess a family from substrings?
 *
 * The distinction matters wherever a material ref is an *override* on something that already
 * has a colour of its own (a solid's category palette): a stated colour should win, a guessed
 * one should not repaint every generic "aluminum" run in the model.
 */
export function statesOwnColor(
  materialRef: string | null | undefined,
  materials?: readonly MaterialAppearance[],
): boolean {
  if (!materialRef) return false;
  if (FINISH_BASE[materialRef.toLowerCase()]) return true;
  return Boolean(authoredAppearance(materialRef, materials)?.color);
}

/** The catalog entry for a material tag, when the model shipped one. */
export function authoredAppearance(
  materialRef: string | null | undefined,
  materials?: readonly MaterialAppearance[],
): MaterialAppearance | undefined {
  if (!materialRef || !materials) return undefined;
  return materials.find((material) => material.tag === materialRef);
}

/**
 * Colour for a material ref. An authored `color` from the catalog wins: the material states
 * what it looks like, which is the only way white brick can read as anything but the masonry
 * family's red. Only when nothing is authored do we fall back to inferring a hatch family from
 * substrings in the tag — a guess that is right for generic refs and wrong for finish variants.
 */
export function materialColor(
  materialRef: string | null | undefined,
  palette?: ResolvedNordicPalette,
  materials?: readonly MaterialAppearance[],
): string {
  // A material whose *finish* is named in FINISH_BASE resolves there first. Members carry a
  // material ref but no catalog (memberColor passes only the palette), so an authored colour
  // is invisible to them — and formed edge trim in a second coil colour is a member. Mirrors
  // _FINISH_BASE in emit/gltf/palette.py; keep the two in step.
  const named = materialRef ? FINISH_BASE[materialRef.toLowerCase()] : undefined;
  if (named) return named;
  const authored = authoredAppearance(materialRef, materials)?.color;
  // An authored colour may carry an alpha byte (`#RRGGBBAA`) to declare that the material is
  // see-through. THREE.Color cannot parse eight digits, so the alpha is stripped here and
  // read separately by `materialOpacity` — the two stay in step because both parse the same
  // authored string. The GLB exporter does the same split in emit/gltf/palette.py::_hex_rgba.
  if (authored) return authored.length === 9 ? authored.slice(0, 7) : authored;
  const fam = familyOf(materialRef);
  if (palette) return palette.material[fam ?? "fallback"] ?? palette.material.fallback;
  if (fam && HATCH_FAMILY_COLOR[fam]) return HATCH_FAMILY_COLOR[fam];
  return FALLBACK;
}

/**
 * Opacity for a material ref: the alpha byte of an authored `#RRGGBBAA` colour, or 1.
 *
 * Alpha is honoured end to end in the `.glb` (`alphaMode: BLEND` + double-sided below 1.0);
 * this is the browser's half of the same contract, so the exported model and the live viewer
 * agree about which surfaces you can see through. A material that authors no alpha is opaque,
 * which is every material in the library except the glazing.
 */
export function materialOpacity(
  materialRef: string | null | undefined,
  materials?: readonly MaterialAppearance[],
): number {
  const authored = authoredAppearance(materialRef, materials)?.color;
  if (!authored || authored.length !== 9) return 1;
  const alpha = Number.parseInt(authored.slice(7, 9), 16);
  return Number.isNaN(alpha) ? 1 : alpha / 255;
}

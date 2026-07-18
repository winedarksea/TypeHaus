// The Nordic presentation preset for the UI — a TS mirror of the engine's single
// palette module (emit/draw/palette.py, #24, → 21 §Nordic preset). The 2D SVG editor,
// the 3D panel, and the section card all consume these values so wood looks the same
// everywhere. Keep in lockstep with palette.py.

export const NORDIC_BG = "#f4f2ed";
export const NORDIC_INK = "#33312c";
export const NORDIC_LINE = "#5b574f";
export const NORDIC_ACCENT = "#6d8a96";

// Material colors fall back through hatch families keyed by material name substrings,
// mirroring palette.material_color's family lookup.
export const HATCH_FAMILY_COLOR: Record<string, string> = {
  lumber: "#d8c9a6",
  osb: "#c9a86a",
  rigid: "#e8d64f",
  batt: "#f3c6d0",
  gypsum: "#efeae2",
  membrane: "#4a4a4a",
  siding: "#b8bcc0",
  metal: "#6b7076",
  concrete: "#a9a9a9",
};

export const CONTROL_COLOR: Record<string, string> = {
  air: "#c0392b",
  water: "#2980b9",
  vapor: "#8e44ad",
  thermal: "#e67e22",
};

const FALLBACK = "#cfc9bd";

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
    ["metal", "metal"],
    ["steel", "metal"],
    ["concrete", "concrete"],
    ["conc", "concrete"],
    ["slab", "concrete"],
  ];
  for (const [needle, fam] of table) if (s.includes(needle)) return fam;
  return null;
}

export function materialColor(materialRef: string | null | undefined): string {
  const fam = familyOf(materialRef);
  if (fam && HATCH_FAMILY_COLOR[fam]) return HATCH_FAMILY_COLOR[fam];
  return FALLBACK;
}

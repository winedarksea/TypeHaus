"""The centralized Nordic presentation preset — one muted palette shared by the 3D
viewer, the SVG editor, and 2D detail hatches (#24, → 21 §Nordic preset)."""

from __future__ import annotations

# Muted Nordic palette; material colors fall back to these hatch-family defaults.
NORDIC_BG = "#f4f2ed"
NORDIC_INK = "#33312c"
NORDIC_LINE = "#5b574f"
NORDIC_ACCENT = "#6d8a96"

HATCH_FAMILY_COLOR: dict[str, str] = {
    "lumber": "#d8c9a6",
    "osb": "#c9a86a",
    "rigid": "#e8d64f",
    "batt": "#f3c6d0",
    "gypsum": "#efeae2",
    "membrane": "#4a4a4a",
    "siding": "#b8bcc0",
    "metal": "#6b7076",
    "concrete": "#a9a9a9",
    "masonry": "#9c5a45",
}

# The material-family fallback colour (light preset) — matches
# RESOLVED_NORDIC_PALETTE.light.material.fallback in ui/src/nordic/palette.ts.
_FAMILY_FALLBACK = "#cfc9bd"

# Ordered substring table mirroring familyOf() in ui/src/nordic/palette.ts. First match
# wins, so more specific needles precede broader ones. Both surfaces infer a hatch family
# from the raw material ref so the 3D viewer and the glTF export agree on wood/gyp/metal/…
_FAMILY_NEEDLES: tuple[tuple[str, str], ...] = (
    ("gyp", "gypsum"), ("dry", "gypsum"),
    ("osb", "osb"), ("zip", "osb"), ("ply", "osb"),
    ("stud", "lumber"), ("lumber", "lumber"), ("wood", "lumber"), ("spf", "lumber"),
    ("rigid", "rigid"), ("xps", "rigid"), ("eps", "rigid"), ("poly", "rigid"),
    ("batt", "batt"), ("mineral", "batt"), ("fiberglass", "batt"), ("cellulose", "batt"),
    ("wrb", "membrane"), ("membrane", "membrane"), ("barrier", "membrane"),
    ("siding", "siding"), ("clad", "siding"),
    ("metal", "metal"), ("seam", "metal"), ("steel", "metal"),
    ("concrete", "concrete"), ("conc", "concrete"), ("slab", "concrete"),
    ("brick", "masonry"), ("masonry", "masonry"), ("cmu", "masonry"),
    ("block", "masonry"), ("stone", "masonry"), ("veneer", "masonry"),
)


def family_of(material_ref: str | None) -> str | None:
    """Infer a hatch/material family from a material ref by substring (first match wins).

    A Python mirror of familyOf() in ui/src/nordic/palette.ts so the glTF export colours a
    layer by its material family (wood/gyp/metal/…) exactly as the 3D viewer does.
    """
    if not material_ref:
        return None
    s = material_ref.lower()
    for needle, fam in _FAMILY_NEEDLES:
        if needle in s:
            return fam
    return None


def material_family_color(material_ref: str | None) -> str:
    """Family-resolved colour for a material ref, falling back to the neutral family colour.

    Mirrors materialColor() in ui/src/nordic/palette.ts against the light (export) preset.
    """
    fam = family_of(material_ref)
    if fam is not None and fam in HATCH_FAMILY_COLOR:
        return HATCH_FAMILY_COLOR[fam]
    return _FAMILY_FALLBACK

# Control-layer badge colors.
CONTROL_COLOR: dict[str, str] = {
    "air": "#c0392b",
    "water": "#2980b9",
    "vapor": "#8e44ad",
    "thermal": "#e67e22",
}


def material_color(hatch: str | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    if hatch and hatch in HATCH_FAMILY_COLOR:
        return HATCH_FAMILY_COLOR[hatch]
    return "#cfc9bd"


# --- detail fills -------------------------------------------------------------------
# Per-material fill + hatch for cut details, ported from the catlin-house reference
# drawings (ifcplot/detail_utils.py MATERIAL_COLORS/HATCHES). A detail reads by material,
# not by layer function: concrete, XPS, EPS, polyiso and spray foam are all "insulation or
# structure" but must be told apart at a glance. Keys are material *tags*
# (``Material.tag`` / ``ResolvedLayer.material_ref``).
DETAIL_FILL: dict[str, str] = {
    "concrete": "#bfbfbf",
    "spf": "#c8a26a",
    "lsl": "#bb955c",
    "osb": "#d9c8a0",
    "struct-1-plywood": "#d9c8a0",
    "plywood-subfloor": "#d9c8a0",
    "zip-r": "#3f6d3a",
    "gwb": "#e6e6e6",
    "polyiso": "#f4e6b1",
    "polyiso-foil": "#efdf9e",
    "eps": "#c8e0f8",
    "icf-eps": "#d8e8fa",
    "xps": "#a7d7c5",
    "mineral-wool": "#a8a8a8",
    "fiberglass": "#ddecc8",
    "air-barrier": "#1e3a5f",
    "standing-seam": "#2f2f2f",
    "fiber-cement": "#e6e6e6",
    "cedar-tg": "#c8a26a",
    "sauna-tg": "#e6d4ae",
    "resilient-channel": "#91979d",
    # detail components + context, not assembly layers
    "aggregate": "#7f7f7f",
    "river-rock": "#a9a9a9",
    "soil": "#d2b48c",
    "spray-foam": "#ffd966",
    "sealant": "#6e4f2a",
    "flashing": "#7a0c0c",
    "metal": "#ffffff",
    "metal-dark": "#2f2f2f",
    "rubber": "#3a3a3a",
    "glass": "#bee3f8",
    "gutter": "#8b8b8b",
}

# Material tag → hatch family (the writers map families to their own pattern syntax).
DETAIL_HATCH: dict[str, str] = {
    "concrete": "concrete",
    "spf": "lumber",
    "lsl": "lumber",
    "cedar-tg": "lumber",
    "sauna-tg": "lumber",
    "osb": "osb",
    "struct-1-plywood": "osb",
    "plywood-subfloor": "osb",
    "zip-r": "osb",
    "gwb": "gypsum",
    "polyiso": "rigid",
    "polyiso-foil": "rigid",
    "eps": "rigid",
    "icf-eps": "rigid",
    "xps": "rigid",
    "mineral-wool": "batt",
    "fiberglass": "batt",
    "air-barrier": "membrane",
    "standing-seam": "metal",
    "aggregate": "gravel",
    "river-rock": "gravel",
    "soil": "soil",
    "spray-foam": "foam",
}

_FALLBACK_FILL = "#e8e4da"


def detail_fill(material_ref: str | None, function: str | None = None) -> str:
    """Fill colour for a cut layer, by material tag, falling back to its layer function."""
    if material_ref and material_ref in DETAIL_FILL:
        return DETAIL_FILL[material_ref]
    return {
        "structure": "#c8a26a", "sheathing": "#d9c8a0", "insulation": "#ddecc8",
        "membrane": "#1e3a5f", "cladding": "#2f2f2f", "finish": "#e6e6e6",
        "furring": "#c8a26a", "airgap": "#eef2f5",
    }.get(function or "", _FALLBACK_FILL)


def detail_hatch(material_ref: str | None, function: str | None = None) -> str | None:
    """Hatch family for a cut layer, by material tag, falling back to its layer function."""
    if material_ref and material_ref in DETAIL_HATCH:
        return DETAIL_HATCH[material_ref]
    return {
        "structure": "lumber", "sheathing": "osb", "insulation": "batt",
        "membrane": "membrane",
    }.get(function or "")

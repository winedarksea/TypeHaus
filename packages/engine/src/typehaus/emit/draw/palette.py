"""The centralized Nordic presentation preset — one muted palette shared by the 3D
viewer, the SVG editor, and 2D detail hatches (#24, → 21 §Nordic preset)."""

from __future__ import annotations

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
    # A shade paler than the subfloor sheet above it, deliberately: catlin's attic deck is
    # the sanded-face underlayment grade because two rooms walk on it bare, and a cut detail
    # that draws it identically to the covered decks below hides the one fact the tag exists
    # to record. Same osb hatch — it is still a veneer panel.
    "plywood-underlayment-sanded": "#e7d8b4",
    "zip-r": "#3f6d3a",
    # The roof rebuild's six new tags (2026-08-20). Every one of them was drawing as the
    # #e8e4da fallback with no hatch — six near-white bands stacked on each other in the
    # one detail whose whole job is to tell the roof's layers apart. These tables are
    # explicit by tag on purpose (a substring guess would colour "roof-vent-mat" as metal),
    # so a new material has to be entered here or it renders as nothing.
    "zip-sheathing": "#3f6d3a",
    "roof-deck-vapor-barrier": "#1e3a5f",
    # Deliberately NOT the deck barrier's navy, though both are self-adhered sheets: the
    # whole point of this roof is that one is vapour-tight and the other must not be, and
    # the drawing is where a roofer sees that. Warm grey against the barrier's navy.
    "roof-underlayment-synthetic": "#8f8578",
    "roof-vent-mat": "#dfe6ea",
    "fiberglass-r19": "#ddecc8",
    "blown-fiberglass": "#e7f2d8",
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
    "standing-seam-snaplock": "#2f2f2f",
    "standing-seam-nailstrip": "#2f2f2f",
    "standing-seam-nailstrip-26": "#2f2f2f",
    # The exposed-fastener PBR panel draws as the same metal ink as the four seam profiles:
    # a section shows a metal skin, and 1/2" of snap-lock pan and 1 1/4" of PBR rib differ
    # in thickness (which the layer carries) and in nothing this table decides. It is listed
    # explicitly because these tables match by TAG and never guess — `pbr-panel-26` hits no
    # needle in `_FAMILY_NEEDLES` ("clad"/"metal"/"seam" are all absent from it), so without
    # this row it would draw as the near-white fallback with no hatch.
    "pbr-panel-26": "#2f2f2f",
    "fiber-cement": "#e6e6e6",
    "cedar-tg": "#c8a26a",
    "sauna-tg": "#e6d4ae",
    "resilient-channel": "#91979d",
    # detail components + context, not assembly layers
    "aggregate": "#7f7f7f",
    "river-rock": "#a9a9a9",
    "soil": "#d2b48c",
    # The radon sump's moulded basin (→ resolve/accessories.py::_resolve_sump). Black
    # polyethylene, so it reads as the void it is against the flatwork it sits in.
    "polyethylene": "#3f4246",
    "spray-foam": "#ffd966",
    "sealant": "#6e4f2a",
    "flashing": "#7a0c0c",
    "metal": "#ffffff",
    "metal-dark": "#2f2f2f",
    "rubber": "#3a3a3a",
    "glass": "#bee3f8",
    "gutter": "#8b8b8b",
    # Breezeway materials. Without these three the section falls through to the cladding
    # default and paints the whole enclosure near-black — the one drawing whose job is to
    # tell the sheet, its extrusion and the decking apart.
    "polycarbonate-multiwall": "#cfe3e8",
    "aluminum-extrusion": "#b6bac0",
    "composite-deck": "#8a7f70",
}

# Material tag → hatch family (the writers map families to their own pattern syntax).
# ``"none"`` is a family in its own right: *fill me, pattern me not*. It has to be a real
# value rather than a missing one, because a band with no hatch node at all loses its
# **fill** too (``section_clip.rect_nodes`` only emits the Hatch when there is a pattern),
# and a colourless band is exactly what this is trying to avoid.
#
# **The rigid boards are the ``None`` case, deliberately.** A hatch answers the question
# "what is this?" for a drawing printed in one colour, and a *coloured* cut band has already
# answered it: the polyiso is straw, the EPS is ice blue, the XPS is green, and nothing else
# in the palette is close to any of them. Laying the "xx" crosshatch over the top of that put
# a grey grid across the two widest bands in the roof — the eye read the grid before it read
# the colour, and two boards of different foam became one hatched field. Every foam here is a
# board, so they go bare together; the batts and the spray foam keep their patterns, because
# what tells a batt from a board *is* the texture.
DETAIL_HATCH: dict[str, str] = {
    "concrete": "concrete",
    "spf": "lumber",
    "lsl": "lumber",
    "cedar-tg": "lumber",
    "sauna-tg": "lumber",
    "osb": "osb",
    "struct-1-plywood": "osb",
    "plywood-subfloor": "osb",
    "plywood-underlayment-sanded": "osb",
    "zip-r": "osb",
    "zip-sheathing": "osb",
    "gwb": "gypsum",
    "polyiso": "none",
    "polyiso-foil": "none",
    "eps": "none",
    "icf-eps": "none",
    "xps": "none",
    "mineral-wool": "batt",
    "fiberglass": "batt",
    "fiberglass-r19": "batt",
    "blown-fiberglass": "batt",
    "air-barrier": "membrane",
    "roof-deck-vapor-barrier": "membrane",
    "roof-underlayment-synthetic": "membrane",
    # The vent mat is an air gap that happens to be a product: hatching it as a membrane
    # would draw the one layer in this roof that is mostly air as a solid sheet.
    "roof-vent-mat": "airgap",
    "standing-seam": "metal",
    "standing-seam-snaplock": "metal",
    "standing-seam-nailstrip": "metal",
    "standing-seam-nailstrip-26": "metal",
    "pbr-panel-26": "metal",
    "aggregate": "gravel",
    "river-rock": "gravel",
    "soil": "soil",
    # A moulded basin is one wall thickness of plastic, not a field of anything: the dark
    # fill says what it is and a pattern over it would only read as a second material.
    "polyethylene": "none",
    "spray-foam": "foam",
    # Glazing draws as a plain tinted fill: a hatch pattern over a translucent sheet reads
    # as a solid, which is the one thing the material is not.
    "polycarbonate-multiwall": "glass",
    "aluminum-extrusion": "metal",
    "composite-deck": "lumber",
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
    """Hatch family for a cut layer, by material tag, falling back to its layer function.

    An entry of ``"none"`` is a deliberate *no hatch*, not a missing one, and wins over the
    function fallback below — otherwise a bare-by-design rigid board would go straight back
    to the ``insulation`` default and pick up the batt stipple instead.
    """
    if material_ref and material_ref in DETAIL_HATCH:
        return DETAIL_HATCH[material_ref]
    return {
        "structure": "lumber", "sheathing": "osb", "insulation": "batt",
        "membrane": "membrane",
    }.get(function or "")


_FUNCTION_AIA = {
    "structure": "A-WALL",
    "sheathing": "A-WALL",
    "cladding": "A-WALL",
    "finish": "A-WALL-FINI",
    "insulation": "A-WALL-INSU",
    "membrane": "A-WALL-PATT",
    "airgap": "A-WALL-PATT",
    "furring": "A-WALL",
}


def aia_layer(function: str | None) -> str:
    """The AIA layer a cut band of this layer function belongs on.

    Beside :func:`detail_hatch` because it is the same decision from the other side: what a
    band is *drawn as* (pattern) and what it is *filed under* (layer) are both properties of
    the layer's function, and two modules answering one of each is how they drift apart.
    """
    return _FUNCTION_AIA.get(function or "", "A-WALL")

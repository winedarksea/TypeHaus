"""The export's colour vocabulary: layer function / member category → RGBA, plus the material
finish colours that follow a named material rather than its category.

Mirrored by ui/src/three/members.ts ``CATEGORY_COLOR`` and ui/src/three/materials.ts — a tone
that changes here has to change there too, or the .glb and the live viewer disagree.
"""

from __future__ import annotations

from typehaus.emit.draw.palette import family_of, material_color, material_family_color
from typehaus.resolve.model import ResolvedModel


# function/category → RGBA color (linear, 0..1). Keys are lowercased layer functions and
# member categories; anything unmatched falls back to a neutral gray.
_PALETTE: dict[str, tuple[float, float, float, float]] = {
    "structure": (0.62, 0.45, 0.28, 1.0),
    "insulation": (0.93, 0.74, 0.36, 1.0),
    "sheathing": (0.72, 0.72, 0.70, 1.0),
    "cladding": (0.55, 0.58, 0.60, 1.0),
    "lining": (0.90, 0.89, 0.86, 1.0),
    "finish": (0.90, 0.89, 0.86, 1.0),
    "membrane": (0.30, 0.45, 0.55, 1.0),
    "air_gap": (0.80, 0.85, 0.90, 0.35),
    "furring": (0.68, 0.52, 0.34, 1.0),
    # framing member categories
    "stud": (0.70, 0.52, 0.33, 1.0),
    "plate": (0.66, 0.48, 0.30, 1.0),
    "header": (0.60, 0.42, 0.26, 1.0),
    "raked_plate": (0.66, 0.48, 0.30, 1.0),
    "corner": (0.64, 0.46, 0.29, 1.0),
    "stringer": (0.60, 0.42, 0.26, 1.0),
    "tread": (0.70, 0.52, 0.33, 1.0),
    "winder": (0.70, 0.52, 0.33, 1.0),
    # Opening framing. These existed in ui/src/three/members.ts CATEGORY_COLOR only, so a
    # header's king/jack/cripple studs read as lumber in the browser and as the grey fallback
    # in the GLB. Same tones as their whole-stud/plate/header siblings, as the viewer has.
    "king": (0.70, 0.52, 0.33, 1.0),
    "jack": (0.70, 0.52, 0.33, 1.0),
    "cripple": (0.70, 0.52, 0.33, 1.0),
    "sill": (0.66, 0.48, 0.30, 1.0),
    "bearing_stiffener": (0.60, 0.42, 0.26, 1.0),
    # stair landing platforms + the U-stair well partition read as framing lumber; the
    # concrete-wall hanger/ledger band is galvanized grey like "connector". Mirrored in
    # ui/src/three/members.ts CATEGORY_COLOR (GLB/three.js parity convention).
    "landing": (0.72, 0.55, 0.36, 1.0),
    # The winder newel carries every winder's narrow end — a post-sized member, so it takes
    # the header/stringer tone rather than the lighter tread lumber.
    "newel": (0.60, 0.42, 0.26, 1.0),
    "partition": (0.70, 0.52, 0.33, 1.0),
    "trimmer": (0.66, 0.48, 0.30, 1.0),
    "hanger": (0.35, 0.36, 0.38, 1.0),
    "joist": (0.72, 0.55, 0.36, 1.0),
    "rim": (0.66, 0.48, 0.30, 1.0),
    "ridge_beam": (0.55, 0.38, 0.22, 1.0),
    # Stick-framed roof lumber + the blocking that fills between it. These had no entry at
    # all, so ~260 members rendered as the neutral gray fallback in *both* renderers (the
    # "garage truss should visualize as wood" report). Values chosen to round-trip exactly
    # to the hex literals in ui/src/three/members.ts CATEGORY_COLOR.
    "rafter": (0.678, 0.498, 0.310, 1.0),        # 0xad7f4f
    "blocking": (0.639, 0.463, 0.247, 1.0),      # 0xa3763f
    "outlooker": (0.722, 0.549, 0.361, 1.0),     # 0xb88c5c
    "barge_rafter": (0.549, 0.384, 0.220, 1.0),  # 0x8c6238
    # roof truss members + the birdsmouth seat cut
    "top_chord": (0.70, 0.52, 0.33, 1.0),
    "bottom_chord": (0.66, 0.48, 0.30, 1.0),
    "truss_web": (0.74, 0.57, 0.38, 1.0),
    "truss_heel": (0.60, 0.42, 0.26, 1.0),
    "seat_cut": (0.58, 0.40, 0.24, 1.0),
    "floor": (0.82, 0.80, 0.76, 1.0),
    "roof": (0.35, 0.37, 0.40, 1.0),
    "slab": (0.55, 0.56, 0.57, 1.0),
    "footing": (0.48, 0.49, 0.50, 1.0),
    "pad": (0.50, 0.51, 0.52, 1.0),
    "column": (0.60, 0.60, 0.62, 1.0),  # concrete/wood posts (sonotube, 6x6 pillars)
    "beam": (0.62, 0.46, 0.28, 1.0),  # PT / built-up wood beams
    "furniture": (0.46, 0.31, 0.20, 1.0),
    # opening fillings — frame/leaf/panel read as wood; glazing is translucent blue-grey
    # (0x8fb7c9 @ 0.48), matching ui/src/components/Panel3D.tsx buildOpening. The frame tone is
    # the viewer's light-theme member wood (0xb3854f, ui/src/nordic/palette.ts); the .glb has no
    # theme to follow, so it ships the default one buildOpening reads for the same boxes.
    "opening_frame": (0.702, 0.522, 0.310, 1.0),
    "glass": (0.561, 0.718, 0.788, 0.48),
    # accessories (→ resolve/accessories.py)
    "railing": (0.80, 0.81, 0.83, 1.0),   # aluminum guard
    "dowel": (0.20, 0.55, 0.35, 1.0),     # GFRP rebar (green)
    "thermal_break": (0.95, 0.55, 0.15, 1.0),  # XPS foam block (orange)
    "connector": (0.35, 0.36, 0.38, 1.0),  # galvanized hardware
    "sump": (0.30, 0.32, 0.34, 1.0),       # pit
    "vent": (0.88, 0.88, 0.86, 1.0),       # painted vent pipe
    "fascia": (0.92, 0.92, 0.90, 1.0),     # PVC fascia
    "soffit": (0.88, 0.88, 0.85, 1.0),     # vented soffit panel under the overhang
    "gutter": (0.85, 0.86, 0.87, 1.0),     # metal gutter
    "flashing": (0.75, 0.77, 0.80, 1.0),   # metal flashing
}
_FALLBACK = (0.70, 0.70, 0.70, 1.0)


def _color(key: str) -> tuple[float, float, float, float]:
    return _PALETTE.get(key.lower(), _FALLBACK)


def _hex_rgba(hex_str: str) -> tuple[float, float, float, float]:
    # Fed straight into baseColorFactor like the existing _solid_color path; no sRGB→linear
    # conversion, matching the emitter's other palette values which are authored directly.
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)
    return _FALLBACK


# Finish classification mirrors ui/src/three/materials.ts so the export approximates the
# viewer's procedural finishes with one flat base colour (no baked textures): a standing-seam
# wall reads near-white, CMU reads grey block, white brick reads whitewashed, and any other
# recognised material falls back to its material-family colour.
#
# ``_FINISH_BASE`` is keyed by the engine's finish vocabulary (model/materials.py
# ``Material.finish``, mirrored by MASONRY_STYLES in ui/src/three/materials.ts). A resolved
# layer carries only its material *ref*, not the authored Material, so the ref is matched
# against that vocabulary by name first — an exact, spelling-independent hit for any material
# whose tag is its finish — and only then falls back to the substring guesswork below.
_SEAM_BASE = "#e8e8e2"          # Panel3D.tsx createStandingSeamMaterial base (0xE8E8E2)
_CMU_BASE = "#9c988f"           # materials.ts CMU_STYLE.base
_WHITE_BRICK_BASE = "#e9e6df"   # materials.ts WHITE_BRICK_STYLE.base
_DECK_BOARD_BASE = "#b9bcc0"    # materials.ts ALUMINUM_DECK_BASE_COLOR (0xb9bcc0)

_FINISH_BASE: dict[str, str] = {
    "standing-seam": _SEAM_BASE,
    "cmu": _CMU_BASE,
    "white-brick": _WHITE_BRICK_BASE,
}


def _is_standing_seam(material_ref: str | None) -> bool:
    if not material_ref:
        return False
    s = material_ref.lower()
    return "seam" in s or (family_of(material_ref) == "metal" and "standing" in s)


def _is_cmu(material_ref: str | None) -> bool:
    if family_of(material_ref) != "masonry":
        return False
    s = (material_ref or "").lower()
    return "cmu" in s or "block" in s or "concrete mason" in s


def _is_white_brick(material_ref: str | None) -> bool:
    s = (material_ref or "").lower()
    return "white" in s or "limewash" in s or "whitewash" in s


def _is_aluminum_deck_board(material_ref: str | None) -> bool:
    """Aluminum plank decking — the viewer's grooved 5.5" board finish (materials.ts
    isAluminumDeckBoard). The metal family colour would read as dark flashing, so the
    export pins the plank's own mill-finish base instead."""
    if not material_ref:
        return False
    s = material_ref.lower()
    return "deck" in s and ("alum" in s or family_of(material_ref) == "metal")


def _material_finish_color(material_ref: str | None,
                           function: str) -> tuple[float, float, float, float]:
    """Colour a material by its named finish, else its family + finish classification, mirroring
    the viewer's materialColor. ``function`` is the lowercased layer function string
    ("cladding", …), used for the standing-seam test and as the fallback palette key when no
    family is recognised."""
    named = _FINISH_BASE.get((material_ref or "").lower())
    if named is not None:
        return _hex_rgba(named)
    if function == "cladding" and _is_standing_seam(material_ref):
        return _hex_rgba(_SEAM_BASE)
    if _is_aluminum_deck_board(material_ref):
        return _hex_rgba(_DECK_BOARD_BASE)
    if family_of(material_ref) == "masonry":
        if _is_cmu(material_ref):
            return _hex_rgba(_CMU_BASE)
        if _is_white_brick(material_ref):
            return _hex_rgba(_WHITE_BRICK_BASE)
        return _hex_rgba(material_family_color(material_ref))  # default red brick → masonry
    if family_of(material_ref) is not None:
        return _hex_rgba(material_family_color(material_ref))
    return _color(function)


def _layer_color(layer) -> tuple[float, float, float, float]:
    """Colour a resolved wall layer by material family; falls back to the function palette for
    layers with no recognisable material ref."""
    return _material_finish_color(layer.material_ref, layer.function)


def _solid_color(model: ResolvedModel, solid) -> tuple[float, float, float, float]:
    """A solid with an authored assembly (e.g. a composite/aluminum deck) reads with its
    material colour; otherwise it falls back to the per-category palette."""
    if solid.assembly:
        assembly = model.plan.library.resolve_assembly(solid.assembly)
        if assembly is not None and assembly.layers:
            idx = assembly.structure_index()
            layer = assembly.layers[idx if idx is not None else 0]
            if _is_aluminum_deck_board(layer.material_ref):
                return _hex_rgba(_DECK_BOARD_BASE)
            material = next((m for m in model.plan.library.materials
                             if m.tag == layer.material_ref), None)
            if material is not None:
                return _hex_rgba(material_color(material.hatch, material.color))
    return _color(solid.category)

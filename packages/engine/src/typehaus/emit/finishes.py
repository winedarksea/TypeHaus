"""The shared material-key vocabulary: what a surface *is*, not what colour it is.

The IR (:mod:`typehaus.resolve.geometry_ir`) carries a ``material_key`` per part rather than
an RGBA, because the two consumers want different things from the same fact:

* the **exporter** maps a key to one flat colour — portable, and what Revit/SketchUp read;
* the **viewer** maps the same key to a procedural material (grain, seam spacing, roughness),
  themed light or dark, and switchable between nordic and schematic modes.

Encoding a colour in the IR would force the viewer to reverse-engineer the finish back out of
an RGB triple, which is how the two ended up disagreeing in the first place.

The vocabulary is the layer-function and member-category names the model already uses — the
keys ``emit/gltf/palette.py`` and ``ui/src/three/members.ts`` were both already keyed by. This
module names that set so it is a contract rather than two dictionaries that happen to overlap,
which ``tests/test_palette_parity.py`` checks in both directions.
"""

from __future__ import annotations

from typehaus.emit.draw.palette import family_of
from typehaus.resolve.model import FramedMember

# Assembly layer functions: the bands a wall/roof/floor stack is built from.
LAYER_KEYS = frozenset({
    "structure", "insulation", "sheathing", "cladding", "lining", "finish", "membrane",
    "air_gap", "airgap", "furring",
})

# Whole-element surfaces that are not a layer of a stack.
ELEMENT_KEYS = frozenset({
    "floor", "roof", "slab", "footing", "pad", "column", "beam", "furniture", "earth",
    "opening_frame", "glass", "solar",
})

# Accessory and trim products (→ resolve/accessories.py, resolve/roof_trim.py).
ACCESSORY_KEYS = frozenset({
    "railing", "dowel", "thermal_break", "connector", "sump", "vent", "fascia", "soffit",
    "gutter", "ridge_cap", "corner_trim", "flashing",
    # Resolved solid categories the glTF palette never had an entry for, so they take its
    # neutral-grey fallback today. Naming them here keeps the IR honest about what they are
    # — a glazing panel is not "structure" — and leaves picking their tones to the emitter
    # switch, where a colour change is a reviewable diff rather than a side effect.
    "glazing", "glazing_trim", "bug_screen",
})

# Material families, inferred from a material ref by `emit/draw/palette.family_of` (mirrored
# in `ui/src/nordic/palette.ts::familyOf`). A part whose finish follows its *material* rather
# than its role — a standing-seam closure band, a CMU veneer course — keys on one of these.
FAMILY_KEYS = frozenset({
    "gypsum", "osb", "lumber", "rigid", "batt", "membrane", "siding", "metal", "concrete",
    "masonry",
})

# Framing member categories. A member's key is its category, so a rafter is lumber and a
# hanger is galvanized steel without either emitter deciding that for itself.
MEMBER_KEYS = frozenset({
    "stud", "plate", "header", "raked_plate", "corner", "stringer", "tread", "winder",
    "king", "jack", "cripple", "sill", "bearing_stiffener", "landing", "landing_framing",
    "newel", "partition", "trimmer", "hanger", "joist", "rim", "ridge_beam", "brace",
    "rafter", "blocking", "outlooker", "barge_rafter", "top_chord", "bottom_chord",
    "truss_web", "truss_heel", "seat_cut",
})

MATERIAL_KEYS = LAYER_KEYS | ELEMENT_KEYS | ACCESSORY_KEYS | MEMBER_KEYS | FAMILY_KEYS

# What an unrecognized key resolves to. Named rather than implicit so a part that falls
# through is visible as "we do not know this finish" instead of silently neutral grey.
FALLBACK_KEY = "structure"


def normalize(key: str | None) -> str:
    """Fold a raw category/function string onto the vocabulary."""
    if not key:
        return FALLBACK_KEY
    folded = key.strip().lower()
    return folded if folded in MATERIAL_KEYS else FALLBACK_KEY


def member_material_key(member: FramedMember) -> str:
    """The finish key for a framing member.

    A member that names a ``material`` is a *skin* band — a wall→roof closure, a roof-edge
    cladding strip — not lumber, so it takes its layer's finish rather than the category
    palette. That distinction is why a standing-seam closure reads as white metal instead of
    generic framing grey, and both emitters have to make it identically.
    """
    if member.material:
        family = family_of(member.material)
        if family is not None:
            return normalize(family)
    return normalize(member.category)

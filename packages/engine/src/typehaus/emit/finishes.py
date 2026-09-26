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
from typehaus.model.layer_functions import LAYER_FUNCTIONS, values_where
from typehaus.resolve.model import FramedMember
from typehaus.resolve.solid_categories import categories_where

# Assembly layer functions: the bands a wall/roof/floor stack is built from.
LAYER_KEYS = values_where(finish_key=True) | frozenset({"lining", "air_gap"})

# Whole-element surfaces that are not a layer of a stack: the registry's ``element`` rows plus
# the part keys that are not categories.
ELEMENT_KEYS = categories_where(finish_group="element") | frozenset({
    "furniture", "opening_frame", "glass", "solar",
})

# Accessory and trim products: the registry's ``accessory`` rows plus part keys that are not
# categories. ``corner_trim``; exterior window casing (resolve/geometry_openings.py), whose
# colour is authored in both palettes; and a sectional overhead door's panel, split from its
# frame because it is a factory-finished product in its own colour; an interior door's
# painted leaf; and a concealed frame's reveal and the lever sets
# (resolve/geometry_door_products.py).
ACCESSORY_KEYS = categories_where(finish_group="accessory") | frozenset({
    "corner_trim", "window_trim", "overhead_door", "door_leaf", "shadow_gap",
    "door_hardware",
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
    "rafter", "blocking", "outlooker", "barge_rafter", "roof_truss", "seat_cut",
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


def layer_material_key(material_ref: str | None, function: str | None) -> str:
    """The finish key for an assembly layer — its *material family* when it names one.

    The same rule the emitters' colour lookup already followed (``_material_finish_color``
    consults ``family_of`` before falling back to the function palette): a standing-seam
    roofing layer and a membrane underlayment are both "cladding"/"membrane" by function, but
    what the eye reads is metal and felt. Layers with no recognisable material ref keep their
    function, which is what the layer palette was keyed by all along.
    """
    family = family_of(material_ref) if material_ref else None
    if family is not None and family in MATERIAL_KEYS:
        return family
    return normalize(function)


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


# --- layer groups ------------------------------------------------------------------------
# The band families a stack is built from, stamped on every ``GPart.layer_group`` of the
# geometry IR. Engine-internal since 2026-09-12: the viewer toggles by TRADE
# (``emit/trade_rules.layer_trade``), so nothing here is mirrored into the UI any more.
LAYER_VISIBILITY_GROUPS = (*dict.fromkeys(
    row.visibility_group for row in LAYER_FUNCTIONS.values() if row.visibility_group != "other"
), "other")

# Synonyms the engine emits for the same bucket. `lining` is an interior finish stack, and
# `fascia`/`soffit` are the derived eave trim that continues the cladding plane.
LAYER_GROUP_ALIASES = {
    "air_gap": "airgap",
    "lining": "finish",
    "fascia": "cladding",
    "soffit": "cladding",
    "roofing": "cladding",
}


def layer_visibility_group(layer_function: str | None) -> str:
    """Bucket a layer function (or a skin member's category) into a togglable group."""
    key = (layer_function or "").strip().lower()
    if not key:
        return "other"
    if key in LAYER_VISIBILITY_GROUPS:
        return key
    return LAYER_GROUP_ALIASES.get(key, "other")

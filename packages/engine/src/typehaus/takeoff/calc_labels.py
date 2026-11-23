"""Plain words for a symbol, and words for a flag — so ``soil_presumed 1 -`` reads ``yes``.

Order of precedence: the ``Quantity.label`` a calc module set, then the kind's own
``declare_sheet(labels=...)``, then the shared dictionary below (review E-10). A name none
of them knows prints as itself; a test lists them for the LA-fill lanes to close.
"""

from __future__ import annotations

from typehaus.engineering.item import Quantity, sheet_spec

#: The common input names across kinds. A kind-specific meaning belongs in that kind's
#: ``declare_sheet(labels=...)``, not here.
COMMON: dict[str, str] = {
    "fc": "concrete compressive strength f'c",
    "fy": "reinforcement yield strength f_y",
    "concrete_unit_weight": "unit weight of concrete",
    "active_efp": "active equivalent fluid pressure",
    "at_rest_efp": "at-rest equivalent fluid pressure",
    "soil_presumed": "soil class presumed from a code table (not measured)",
    "friction_coefficient": "base friction coefficient mu",
    "allowable_bearing": "allowable soil bearing pressure",
    "retained_height": "retained height H, footing underside to grade",
    "stem_thickness": "stem thickness",
    "stem_height": "stem height above the footing",
    "footing_width": "footing width B",
    "footing_depth": "footing depth",
    "toe": "toe length, stem face to footing edge",
    "heel": "heel length, stem back to footing edge",
    "toe_embedment": "soil cover over the toe (passive)",
    "stem_cover": "clear cover to stem bars",
    "footing_cover": "clear cover to footing bars",
    "stem_bar": "stem bar size",
    "stem_spacing": "stem bar spacing",
    "toe_bar": "toe (bottom) bar size",
    "toe_spacing": "toe (bottom) bar spacing",
    "heel_bar": "heel (top) bar size",
    "heel_spacing": "heel (top) bar spacing",
    "width": "member width b",
    "depth": "member depth d",
    "span": "span between supports",
    "back_span": "span between the two posts s",
    "overhang_a": "overhang past the first post a",
    "overhang_b": "overhang past the second post b",
    "tributary_area": "roof area carried",
    "design_snow": "design roof snow (drift included)",
    "design_dead": "design roof dead load",
    "uniform_load": "line load, dead + snow",
    "plies": "number of plies",
    "ply_depth": "ply depth",
    "truss_chord_width": "truss bottom-chord width",
    "truss_bearing_length": "truss chord length on the beam",
    "truss_reaction_max": "largest truss reaction on the beam",
    "floor_live": "floor live load",
    "floor_dead": "floor dead load",
    "roof_snow": "roof snow load",
}


def label(kind: str, quantity: Quantity) -> str:
    """The plain-word meaning of one input, or ``""`` when nobody has said."""
    return (quantity.label or sheet_spec(kind).labels.get(quantity.name, "")
            or COMMON.get(quantity.name, ""))


def is_flag(quantity: Quantity) -> bool:
    return quantity.unit in ("-", "flag") or quantity.name.endswith("_presumed")


def value_text(quantity: Quantity, num) -> str:  # type: ignore[no-untyped-def]
    """A flag as ``yes``/``no``; anything else positional."""
    if is_flag(quantity) and quantity.value in (0.0, 1.0):
        return "yes" if quantity.value else "no"
    return num(quantity.value)


def unit_text(quantity: Quantity) -> str:
    return "" if is_flag(quantity) else (quantity.unit or "")

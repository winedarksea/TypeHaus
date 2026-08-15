"""The parts a guard is built from: their sections, and which material each one wears.

A guard is rarely one material. A glass balcony rail is aluminium posts, an aluminium cap
and a glass lite; ``Railing.assembly`` can only say one thing about all three. So each part
resolves its own material ref through a three-rung ladder:

1. the ``Railing``'s own field (``post_material`` / ``rail_material`` / ``infill_material``),
2. the ``RailingType`` catalog record's default for that part,
3. **nothing** — ``material=None`` with ``assembly=el.assembly``, exactly as today.

Rung three is deliberately "do nothing" rather than "stamp the assembly's structure
material". Leaving the ref empty lets the *existing* third rung of the colour walk run
unchanged (``emit/gltf/palette.py::_solid_color`` and ``ui/src/three/solidMaterials.ts::
solidColor`` both fall to the assembly on their own), which is provably the same value with
no ``_FINISH_BASE``-ordering risk — a house that authors none of this renders exactly as it
did.

The three product dimensions have the same shape. R312.1.3 constrains the *gap*, never the
picket, so the picket's own width is a product fact: it comes off the ``RailingType`` and
falls back to a stock section here.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.geometry import nominal_actual_m
from typehaus.resolve.model import ResolvedModel

#: Posts and rails — the frame — keep the category they have always had, so every existing
#: consumer (the 2D plan filter, the trades gate, the BOM's frame row) is untouched.
RAILING_CATEGORY = "railing"
#: Infill that is not see-through: balusters, cable, mesh, an opaque sheet.
RAILING_INFILL_CATEGORY = "railing_infill"
#: A translucent panel. Its own category because metalness is keyed on category alone —
#: under ``railing`` a glass lite renders as dark metal (METALLIC_SOLID_CATEGORIES).
RAILING_GLASS_CATEGORY = "railing_glass"

#: The horizontal rail's square section. A guard rail is stock extrusion, not a sized member.
RAIL_SECTION_M = inch(1.5).meters
#: Stock 3/4" square picket, 3/16" cable, 1/2" lite — used where the product states nothing.
_DEFAULT_BALUSTER_WIDTH = inch(0.75)
_DEFAULT_CABLE_DIAMETER = inch(0.1875)
_DEFAULT_PANEL_THICKNESS = inch(0.5)
#: A panel-topping cap has to swallow the lite plus a glazing bite either side.
_PANEL_CAP_BITE = inch(0.25)


@dataclass(frozen=True)
class RailingParts:
    """Resolved per-part materials and sections for one railing."""

    post_material: str | None
    rail_material: str | None
    infill_material: str | None
    post_section_m: float
    rail_section_m: float
    baluster_width_m: float
    cable_diameter_m: float
    panel_thickness_m: float
    #: ``railing_glass`` when the infill material declares itself see-through, else
    #: ``railing_infill``. Picked explicitly rather than inferred from a tag substring: a
    #: panel that never named a translucent material is not glass, and saying so is correct.
    infill_category: str
    #: ``RailingType.glazing`` — what R308.4.4 reads. ``None`` means the product is silent.
    glazing: str | None


def resolve_parts(model: ResolvedModel, el: Railing) -> RailingParts:
    """Walk the material ladder and the product dimensions for one railing."""
    product = next((p for p in model.plan.library.railing_types
                    if p.tag == el.type_ref), None) if el.type_ref else None

    def material(field: str) -> str | None:
        return getattr(el, field, None) or getattr(product, field, None)

    def dimension(field: str, fallback) -> float:
        stated = getattr(product, field, None) if product is not None else None
        return (stated if stated is not None else fallback).meters

    infill_material = material("infill_material")
    panel_thickness = dimension("panel_thickness", _DEFAULT_PANEL_THICKNESS)
    # A cap over a panel is wide enough to take the lite plus its bite, and never narrower
    # than the stock rail — the reveal is derived from the panel, not authored beside it.
    rail_section = (max(RAIL_SECTION_M, panel_thickness + 2.0 * _PANEL_CAP_BITE.meters)
                    if el.infill == "panel" else RAIL_SECTION_M)
    return RailingParts(
        post_material=material("post_material"),
        rail_material=material("rail_material"),
        infill_material=infill_material,
        post_section_m=nominal_actual_m(el.post_size),
        rail_section_m=rail_section,
        baluster_width_m=dimension("baluster_width", _DEFAULT_BALUSTER_WIDTH),
        cable_diameter_m=dimension("cable_diameter", _DEFAULT_CABLE_DIAMETER),
        panel_thickness_m=panel_thickness,
        infill_category=(RAILING_GLASS_CATEGORY
                         if el.infill == "panel" and is_translucent(model, infill_material)
                         else RAILING_INFILL_CATEGORY),
        glazing=getattr(product, "glazing", None),
    )


def is_translucent(model: ResolvedModel, material_ref: str | None) -> bool:
    """Does this material declare itself see-through?

    A material says so exactly one way: by authoring an 8-digit ``#RRGGBBAA`` colour whose
    alpha byte is not ``ff``. That is the same fact ``emit/gltf/palette.py::_hex_rgba`` and
    ``ui/src/nordic/palette.ts::materialOpacity`` already parse, so nothing new has to be
    kept in step — and a new translucent material needs no code here at all.
    """
    if not material_ref:
        return False
    material = next((m for m in model.plan.library.materials
                     if m.tag == material_ref), None)
    color = getattr(material, "color", None)
    if not color:
        return False
    hex_digits = color.lstrip("#")
    if len(hex_digits) != 8:
        return False
    try:
        return int(hex_digits[6:8], 16) < 255
    except ValueError:
        return False

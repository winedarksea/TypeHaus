"""Wall base trim: one catalog base along every free panel bottom edge."""

from __future__ import annotations

from typehaus.library.trim.metal_sales import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.runs import (
    add_horizontal_run,
    covered_below,
    kit_faces,
    subtract_spans,
)
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M

# An opening whose bottom is within the base's upstand of the panel bottom breaks the base;
# a door sill above that (a threshold over a skirt) leaves it unbroken beneath.
_DOOR_REACH_M = 3 * M_PER_IN


def resolve_base_trim(model) -> None:
    """Sweep the kit's base trim under each stack of panels, broken at floor-level openings.

    The section is the sheet's inner line, thickened inboard, so it is swept one sheet out:
    the back leg then lies on the girt plane instead of across the cavity mouth.
    """
    entries = list(kit_faces(model, TrimCondition.BASE))
    faces = [face for face, _ in entries]
    for face, key in entries:
        if covered_below(face, faces):
            continue
        cuts = [(a, b) for opening, a, b in face.openings(model)
                if face.wall.base_ref_z_m + opening.sill_m < face.z0 + _DOOR_REACH_M]
        for span, (lo, hi) in enumerate(subtract_spans(face.lo, face.hi, cuts), 1):
            add_horizontal_run(model, face, PROFILES[key], key,
                               f"TRIM-{face.wall.tag}-BASE-S{span}", lo, hi, face.z0,
                               depth=SHEET_24_GA_M)

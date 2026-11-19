"""Wall base trim: one catalog base along every free panel bottom edge."""

from __future__ import annotations

from typehaus.library.trim.catalog import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.corner_closures import corner_end_cuts
from typehaus.resolve.cladding_trim.runs import (
    add_horizontal_run,
    covered_below,
    kit_faces,
    subtract_spans,
)
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.rainscreen_closures import screens_rainscreen_base

# An opening whose bottom is within the base's upstand of the panel bottom breaks the base;
# a door sill above that (a threshold over a skirt) leaves it unbroken beneath.
_DOOR_REACH_M = 3 * M_PER_IN
#: A base's end short of a corner C-Closure's return, as the BBD75 band's.
_CLOSURE_GAP_M = M_PER_IN / 16


def base_trim_spans(model):
    """``(face, key, span, lo, hi, z, depth)`` for every base run, the trim's foot line.

    The section is the sheet's inner line, thickened inboard, so it is swept one sheet out:
    the back leg then lies on the girt plane instead of across the cavity mouth. Over a
    screened cavity base the foot is raised ``trim_rise`` off the seat, so the pan edge
    drains and the screen breathes under it; the back leg laps the screen on the EPDM.
    A run stops at a wide outside corner (``corner_end_cuts``).
    """
    entries = list(kit_faces(model, TrimCondition.BASE))
    faces = [face for face, _ in entries]
    for face, key in entries:
        if covered_below(face, faces):
            continue
        cuts = [(a, b) for opening, a, b in face.openings(model)
                if face.wall.base_ref_z_m + opening.sill_m < face.z0 + _DOOR_REACH_M]
        # Stop at a wide outside corner, which lands on the strip top: the run and its strip
        # no longer reach into the corner trim or the adjoining wall's base.
        cuts += corner_end_cuts(model, face, _CLOSURE_GAP_M)
        spec = _base_spec(model, face)
        rise = spec.trim_rise.meters if spec and screens_rainscreen_base(model, face.wall) \
            else 0.0
        depth = _leg_depth_m(model, face)
        for span, (lo, hi) in enumerate(subtract_spans(face.lo, face.hi, cuts), 1):
            yield face, key, span, lo, hi, face.z0 + rise, depth


def _base_spec(model, face):
    assembly = model.plan.library.resolve_assembly(face.wall.assembly)
    return assembly.rainscreen_base_flashing if assembly else None


def _leg_depth_m(model, face) -> float:
    """The back leg's outer face off the back plane: isolation, then one sheet."""
    spec = _base_spec(model, face)
    return SHEET_24_GA_M + (spec.isolation_thickness.meters if spec else 0.0)


def base_leg_depth_m(model, wall, layer) -> float:
    """Outer face of the base's back leg off ``layer``'s back plane, else 0 (no free base).

    Matched by uid and layer name: ``board_batten`` replaces the layer object.
    """
    faces = [face for face, _ in kit_faces(model, TrimCondition.BASE)]
    for face in faces:
        if (face.wall.uid == wall.uid and face.layer.name == layer.name
                and not covered_below(face, faces)):
            return _leg_depth_m(model, face)
    return 0.0


def resolve_base_trim(model) -> None:
    """Sweep the kit's base trim under each stack of panels, broken at floor-level openings."""
    for face, key, span, lo, hi, z, depth in list(base_trim_spans(model)):
        add_horizontal_run(model, face, PROFILES[key], key,
                           f"TRIM-{face.wall.tag}-BASE-S{span}", lo, hi, z, depth=depth,
                           under_skin=True)

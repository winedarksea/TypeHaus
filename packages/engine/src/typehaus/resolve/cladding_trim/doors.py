"""Exterior door trim on profiled metal walls, and the small rough openings."""

from __future__ import annotations

from dataclasses import replace

from typehaus.library.trim.catalog import PROFILES
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.runs import add_vertical_run, kit_faces
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.flashing_solids import flashing_solid
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.opening_flashing import head_flashing_section

# A rough opening this small is a penetration closed by its fixture's own flange and sealant.
SMALL_PENETRATION_M = 6 * M_PER_IN


def door_face(model, wall):
    """(face, jamb key, head key) for a door's host wall, or None off a kit-trimmed wall."""
    jambs = {face.wall.tag: (face, key) for face, key in kit_faces(model, TrimCondition.DOOR_JAMB)}
    heads = {face.wall.tag: key for face, key in kit_faces(model, TrimCondition.DOOR_HEAD)}
    if wall.tag not in jambs or wall.tag not in heads:
        return None
    return (*jambs[wall.tag], heads[wall.tag])


def add_door_trim(model, wall, opening, frame, cfg, material, *, catalog: bool) -> bool:
    """Append jambs for a kit-trimmed door and a swept drip head unless the unit carries its own.

    Jambs finish the panel against the casing edge. The head is the legacy drip section
    swept as a billable cut, so the 3D piece and the order agree; a catalog door's head
    belongs to the product, or to the band that passes over it.
    """
    found = door_face(model, wall)
    if found is None:
        return False
    face, jamb_key, head_key = found
    placement = opening.doorway.exterior_placement if opening.doorway else None
    casing = placement.specification.casing_width.meters if placement else 0.0
    sill = wall.base_ref_z_m + opening.sill_m
    head = sill + opening.height_m
    _, lo, hi = next(item for item in face.openings(model) if item[0].uid == opening.uid)
    for side, station, inward in (("LEFT", lo - casing, -1.0), ("RIGHT", hi + casing, 1.0)):
        add_vertical_run(model, face, PROFILES[jamb_key], jamb_key,
                         f"{opening.tag}-TRIM-JAMB-{side}", station, max(sill, face.z0),
                         head + casing, inward, host_ref=opening.tag)
    if not catalog:
        _add_head(model, wall, opening, frame, cfg, material, head_key)
    return True


def _add_head(model, wall, opening, frame, cfg, material, key):
    profile = PROFILES[key]
    head = head_flashing_section(wall, opening, frame, cfg)
    for index, (start, end, stock) in enumerate(split_stock_run(
            head.span, tuple(v * M_PER_IN for v in profile.stock_lengths_in),
            profile.min_lap_in * M_PER_IN)):
        point = frame.point(head.start + start, 0.0, 0.0)
        mesh = folded_section_mesh(
            head.points, point, (*frame.outward, 0.0), (0.0, 0.0, 1.0),
            (*(v * (end - start) for v in frame.along), 0.0), SHEET_24_GA_M)
        solid = flashing_solid(
            uid=f"{opening.uid}-trim-head-{index}",
            tag=f"{opening.tag}-TRIM-HEAD-{index + 1}", storey=wall.storey,
            category="cladding_trim", mesh=mesh, material=material, host_ref=opening.tag)
        model.solids.append(replace(solid, product=key, trim_length_m=end - start,
                                    trim_stock_length_in=stock / M_PER_IN))

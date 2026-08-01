"""Below-grade context: the grade line, the soil body, and the perimeter drain.

A grade line, a soil hatch, a french drain and its river-rock surround are drawing
conventions, not building elements: Revit calls them detail components and they live in the
view, not the model. They are derived from the live cut and the resolved planes around it —
the same way joint treatments are — so they track a geometry edit instead of freezing
authored coordinates.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import M_TO_IN, PERIMETER_DRAIN
from typehaus.emit.draw.detail_components.geometry import (
    closed_region,
    outboard_is_high,
    rect_points,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.scene import IRNode, Polyline


def grade_line(u0: float, u1: float, grade_z: float, wall_face_u: float) -> list[IRNode]:
    """The finish-grade line, drawn only outboard of the wall face it slopes away from."""
    start = max(u0, wall_face_u)
    if start >= u1:
        return []
    return [Polyline(points=((start, grade_z), (u1, grade_z)), layer="L-SITE-GRAD",
                     lineweight=0.5, tag="detail-component:grade-line")]


def soil_body(u0: float, u1: float, grade_z: float, z_bottom: float) -> list[IRNode]:
    """Undisturbed soil across ``[u0, u1]``, from grade down to the crop bottom."""
    if u0 >= u1 or grade_z <= z_bottom:
        return []
    return closed_region(rect_points(u0, z_bottom, u1, grade_z),
                         "soil", "soil", "soil", lineweight=0.0)


def french_drain(center_u: float, invert_z: float,
                 diameter_in: float | None = None,
                 rock_width_in: float | None = None,
                 rock_depth_in: float | None = None) -> list[IRNode]:
    """Perforated drain tile in a washed-rock surround, sitting on the footing bedding.

    Drawn as its rock envelope plus the pipe bore — the reference's own construction. The
    pipe is a square-cut octagon rather than a circle because the IR has no arc primitive
    that both writers render. Each dimension is the authored ``DrainTile`` field when the
    bedding carries a spec; None falls back to the pinned reference numbers, which is what
    every one of these was before the model had fields to hold them.
    """
    cfg = PERIMETER_DRAIN
    half_rock = (rock_width_in if rock_width_in is not None else cfg.rock_width_in) / 2.0
    rock_depth = rock_depth_in if rock_depth_in is not None else cfg.rock_depth_in
    nodes = closed_region(
        rect_points(center_u - half_rock, invert_z,
                    center_u + half_rock, invert_z + rock_depth),
        "river-rock", "river-rock", "gravel",
    )
    radius = (diameter_in if diameter_in is not None else cfg.drain_diameter_in) / 2.0
    center_z = invert_z + radius + cfg.pipe_bedding_in
    flat = radius * cfg.octagon_half_flat_ratio
    nodes.extend(closed_region(
        ((center_u - flat, center_z - radius), (center_u + flat, center_z - radius),
         (center_u + radius, center_z - flat), (center_u + radius, center_z + flat),
         (center_u + flat, center_z + radius), (center_u - flat, center_z + radius),
         (center_u - radius, center_z + flat), (center_u - radius, center_z - flat)),
        "french-drain", "aggregate", None, lineweight=0.35,
    ))
    return nodes


def faces_soil(wall) -> bool:
    """Whether this foundation wall is detailed for soil contact.

    Read from the assembly, not the tag: a wall that backfills against earth carries
    damp-proofing or exterior rigid insulation outboard of its concrete, and an interior
    basement bearing wall — slab on both sides — does not. Drawing soil and a perimeter drain
    against the latter would be a drawing that lies about the building.
    """
    if not wall.is_foundation:
        return False
    structure = next((i for i, ly in enumerate(wall.layers)
                      if ly.function == "structure"), None)
    if structure is None:
        return False
    for layer in wall.layers[structure + 1:]:
        if layer.function in ("membrane", "insulation") and not layer.is_cavity:
            return True
    return False


def footing_under(model, wall):
    """The strip footing carrying this wall, by the ``FT-<wall suffix>`` naming convention."""
    suffix = wall.tag[2:] if wall.tag.startswith("W-") else wall.tag
    return next((s for s in model.solids
                 if s.category == "footing" and s.tag == f"FT-{suffix}"), None)


def drain_tile_spec_for(model, footing):
    """The authored ``DrainTile`` spec on this footing's bedding, or None.

    ``FootingBedding.drain_tile_spec`` is the model field that says what the bare
    ``drain_tile: bool`` cannot — pipe size, sock, discharge. Read from plan source
    (``host_ref`` names the footing) because the resolved bedding record does not carry
    the spec; None keeps the pinned reference dimensions.
    """
    if footing is None:
        return None
    return next((element.drain_tile_spec
                 for element in model.plan.elements_of_kind("FootingBedding")
                 if element.host_ref == footing.tag), None)


def build_below_grade_components(model, wall, crop, direction: str,
                                 station: float) -> list[IRNode]:
    """Grade, soil and the perimeter drain for a below-grade wall, from resolved planes.

    Returns nothing unless the cut actually reaches below grade — an above-grade junction has
    no soil to draw, and guessing one would be a drawing that lies.
    """
    site = model.plan.project.site
    if site.grade is None or crop is None or not faces_soil(wall):
        return []
    (cu0, cz0), (cu1, cz1) = crop
    grade_z = site.grade.meters
    if not (cz0 < grade_z < cz1):
        return []

    u_lo, u_hi = wall_cut_bounds_m(wall, direction, station)
    if u_lo is None:
        return []
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return []
    face = u_hi if is_outboard_high else u_lo

    face_in = face * M_TO_IN
    grade_in, bottom_in = grade_z * M_TO_IN, cz0 * M_TO_IN
    crop_lo_in, crop_hi_in = cu0 * M_TO_IN, cu1 * M_TO_IN
    # Soil fills the crop on whichever side of the wall is outdoors, and the grade line runs
    # with it — mirrored, never assumed, so a wall detailed the other way round still reads.
    if is_outboard_high:
        soil_lo, soil_hi = max(crop_lo_in, face_in), crop_hi_in
    else:
        soil_lo, soil_hi = crop_lo_in, min(crop_hi_in, face_in)
    nodes: list[IRNode] = []
    nodes += soil_body(soil_lo, soil_hi, grade_in, bottom_in)
    if soil_lo < soil_hi:
        nodes.append(Polyline(points=((soil_lo, grade_in), (soil_hi, grade_in)),
                              layer="L-SITE-GRAD", lineweight=0.5,
                              tag="detail-component:grade-line"))

    # The perimeter drain sits on the footing bedding. Only draw it when the footing is
    # actually in frame — a wall-top junction cropped 4 ft down the basement wall does not
    # reach it, and a drain floating at the crop edge is worse than no drain.
    footing = footing_under(model, wall)
    spec = drain_tile_spec_for(model, footing)
    diameter_in = _spec_inches(spec, "diameter")
    rock_width_in = _spec_inches(spec, "rock_width") or PERIMETER_DRAIN.rock_width_in
    rock_depth_in = _spec_inches(spec, "rock_depth") or PERIMETER_DRAIN.rock_depth_in
    rock_depth_m = rock_depth_in / M_TO_IN
    if footing is not None and cz0 <= footing.z0_m and footing.z0_m + rock_depth_m <= cz1:
        offset = rock_width_in / 2.0 + PERIMETER_DRAIN.rock_offset_from_wall_in
        sign = 1.0 if is_outboard_high else -1.0
        nodes += french_drain(face_in + sign * offset, footing.z0_m * M_TO_IN,
                              diameter_in=diameter_in, rock_width_in=rock_width_in,
                              rock_depth_in=rock_depth_in)
    return nodes


def _spec_inches(spec, field: str) -> float | None:
    """One optional ``Length`` off a ``DrainTile``, in the drawing's inches."""
    length = getattr(spec, field, None) if spec is not None else None
    return length.meters * M_TO_IN if length is not None else None

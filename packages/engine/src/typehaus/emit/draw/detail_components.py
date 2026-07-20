"""2D detail components — the drawn context a junction needs but the model does not carry.

A grade line, a soil hatch, a french drain and its river-rock surround are drawing
conventions, not building elements: Revit calls them detail components and they live in the
view, not the model. TypeHaus derives them the same way it derives joint treatments — from
the live cut and the resolved planes around it — so they track a geometry edit instead of
freezing authored coordinates.

They are emitted as ordinary ``Polyline``/``Hatch`` nodes carrying a
``detail-component:<name>`` tag, deliberately *not* as new ``Symbol`` names: the writers
already render polylines and hatches correctly and keep them hit-testable, whereas an
unknown ``Symbol`` degrades to a bare circle.

Section coordinates throughout: ``u`` is the in-section axis, ``z`` is world z, both in
model inches at the point these nodes are built (the cutter's convention).
"""

from __future__ import annotations

from typehaus.emit.draw.scene import Hatch, IRNode, Polyline

M_TO_IN = 39.37007874015748

LAYER = "A-DETL-CMPT"

# Reference dimensions (catlin-house Pset_ifcPlot_BasementConstruction), in inches.
DRAIN_DIAMETER_IN = 4.0
ROCK_WIDTH_IN = 10.0
ROCK_DEPTH_IN = 8.0


def _closed(points, tag: str, material: str | None, pattern: str | None,
            lineweight: float = 0.18) -> list[IRNode]:
    pts = tuple(points)
    nodes: list[IRNode] = []
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer=LAYER, material=material))
    nodes.append(Polyline(points=pts, layer=LAYER, closed=True, lineweight=lineweight,
                          tag=f"detail-component:{tag}"))
    return nodes


def grade_line(u0: float, u1: float, grade_z: float, wall_face_u: float) -> list[IRNode]:
    """The finish-grade line, drawn only outboard of the wall face it slopes away from."""
    start = max(u0, wall_face_u)
    if start >= u1:
        return []
    return [Polyline(points=((start, grade_z), (u1, grade_z)), layer="L-SITE-GRAD",
                     lineweight=0.5, tag="detail-component:grade-line")]


def soil_body(u0: float, u1: float, grade_z: float, z_bottom: float,
              wall_face_u: float) -> list[IRNode]:
    """Undisturbed soil outboard of the wall, from grade down to the crop bottom."""
    start = max(u0, wall_face_u)
    if start >= u1 or grade_z <= z_bottom:
        return []
    return _closed(
        ((start, z_bottom), (u1, z_bottom), (u1, grade_z), (start, grade_z)),
        "soil", "soil", "soil", lineweight=0.0,
    )


def french_drain(center_u: float, invert_z: float) -> list[IRNode]:
    """Perforated drain tile in a washed-rock surround, sitting on the footing bedding.

    Drawn as its rock envelope plus the pipe bore — the reference's own construction. The
    pipe is a square-cut octagon rather than a circle because the IR has no arc primitive
    that both writers render.
    """
    half_rock = ROCK_WIDTH_IN / 2.0
    nodes = _closed(
        ((center_u - half_rock, invert_z),
         (center_u + half_rock, invert_z),
         (center_u + half_rock, invert_z + ROCK_DEPTH_IN),
         (center_u - half_rock, invert_z + ROCK_DEPTH_IN)),
        "river-rock", "river-rock", "gravel",
    )
    r = DRAIN_DIAMETER_IN / 2.0
    cz = invert_z + r + 1.0
    k = r * 0.4142  # octagon: tan(22.5°)
    nodes.extend(_closed(
        ((center_u - k, cz - r), (center_u + k, cz - r),
         (center_u + r, cz - k), (center_u + r, cz + k),
         (center_u + k, cz + r), (center_u - k, cz + r),
         (center_u - r, cz + k), (center_u - r, cz - k)),
        "french-drain", "aggregate", None, lineweight=0.35,
    ))
    return nodes


def faces_soil(wall) -> bool:
    """Whether this foundation wall is detailed for soil contact.

    Read from the assembly, not the tag: a wall that backfills against earth carries
    damp-proofing or exterior rigid insulation outboard of its concrete, and an interior
    basement bearing wall — slab on both sides — does not. Drawing soil and a perimeter
    drain against the latter would be a drawing that lies about the building.
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


def build_below_grade_components(model, wall, crop, direction: str,
                                 station: float) -> list[IRNode]:
    """Grade, soil and the perimeter drain for a below-grade wall, from resolved planes.

    Returns nothing unless the cut actually reaches below grade — an above-grade junction
    has no soil to draw, and guessing one would be a drawing that lies.
    """
    site = model.plan.project.site
    if site.grade is None or crop is None or not faces_soil(wall):
        return []
    (cu0, cz0), (cu1, cz1) = crop
    grade_z = site.grade.meters
    if not (cz0 < grade_z < cz1):
        return []

    u_lo, u_hi = _wall_faces(wall, direction, station)
    if u_lo is None:
        return []
    # Which side is outdoors comes from the assembly, not the drawing: layers are ordered
    # interior→exterior, so the last layer sits on the outboard face. Reading it off the
    # crop instead would just reflect the crop's own asymmetry back at us.
    outboard_is_high = _outboard_is_high(wall, direction, station)
    if outboard_is_high is None:
        return []
    face = u_hi if outboard_is_high else u_lo

    to_in = M_TO_IN
    nodes: list[IRNode] = []
    if outboard_is_high:
        nodes += soil_body(cu0 * to_in, cu1 * to_in, grade_z * to_in, cz0 * to_in,
                           face * to_in)
        nodes += grade_line(cu0 * to_in, cu1 * to_in, grade_z * to_in, face * to_in)
    else:
        # Mirror: soil fills from the crop's low edge up to the wall's inboard face.
        nodes += _mirrored_soil(cu0 * to_in, face * to_in, grade_z * to_in, cz0 * to_in)
        nodes.append(Polyline(points=((cu0 * to_in, grade_z * to_in),
                                      (face * to_in, grade_z * to_in)),
                              layer="L-SITE-GRAD", lineweight=0.5,
                              tag="detail-component:grade-line"))

    # The perimeter drain sits on the footing bedding. Only draw it when the footing is
    # actually in frame — a wall-top junction cropped 4 ft down the basement wall does not
    # reach it, and a drain floating at the crop edge is worse than no drain.
    footing = _footing_under(model, wall)
    if footing is not None and cz0 <= footing.z0_m and footing.z0_m + ROCK_DEPTH_IN / M_TO_IN <= cz1:
        offset = (ROCK_WIDTH_IN / 2.0 + 1.0) * (1.0 if outboard_is_high else -1.0)
        nodes += french_drain(face * to_in + offset, footing.z0_m * to_in)
    return nodes


def _mirrored_soil(u0: float, u1: float, grade_z: float, z_bottom: float) -> list[IRNode]:
    if u0 >= u1 or grade_z <= z_bottom:
        return []
    return _closed(((u0, z_bottom), (u1, z_bottom), (u1, grade_z), (u0, grade_z)),
                   "soil", "soil", "soil", lineweight=0.0)


def _outboard_is_high(wall, direction: str, station: float) -> bool | None:
    """True when the wall's outermost layer sits at the high end of the section axis."""
    from typehaus.emit.draw.section import _ring_cut_intervals

    depth = wall.depth_layers()
    if len(depth) < 2:
        return None
    first = _ring_cut_intervals(depth[0].polygon, direction, station)
    last = _ring_cut_intervals(depth[-1].polygon, direction, station)
    if not first or not last:
        return None
    return sum(last[0]) > sum(first[0])


def _wall_faces(wall, direction: str, station: float):
    from typehaus.emit.draw.section import _ring_cut_intervals

    bounds: list[float] = []
    for layer in wall.layers:
        for (a, b) in _ring_cut_intervals(layer.polygon, direction, station):
            bounds.extend((a, b))
    if not bounds:
        return None, None
    return min(bounds), max(bounds)


def _footing_under(model, wall):
    """The strip footing carrying this wall, by the ``FT-<wall suffix>`` naming convention."""
    suffix = wall.tag[2:] if wall.tag.startswith("W-") else wall.tag
    return next((s for s in model.solids
                 if s.category == "footing" and s.tag == f"FT-{suffix}"), None)

"""Where a derived corner STHD goes, and whether ESR-2920 Figure 1 lets it go there.

A leaf of ``joints/sills.py``: the corner's inside face of the stud band, and the fit test
that keeps the house rule (``holdowns_per_run_end``) to corners a published installation
reaches. ``sills`` is imported lazily, so the two never import each other at load.
"""

from __future__ import annotations

import math

from typehaus.joints.model import axis_of
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.ties import EMBEDDED_STRAPS
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sill_bearing import stud_band

#: A derived STHD draws as the STHD14 (``tie_mesh``'s representative).
_STRAP_HALF_WIDTH_M = EMBEDDED_STRAPS["STHD14"].width_in / 2.0 * M_PER_IN


def _span(polygon, axis: tuple) -> tuple[float, float]:
    offsets = [p[0] * axis[0] + p[1] * axis[1] for p in polygon]
    return min(offsets), max(offsets)


def _centre(polygon, axis: tuple) -> float:
    return sum(_span(polygon, axis)) / 2.0


def _inside_corner(model: ResolvedModel, ret, ends, other) -> tuple | None:
    """``(point, outward)``: the strap on ``ret``'s stud-band inside face, inside the corner.

    Across the run the leaf lies on the band's interior face; along it the strap's centre
    stands half its width past the perpendicular band's interior face (S-103's notched sill).
    """
    band, perp = stud_band(model, ret), stud_band(model, other)
    run = math.dist(*ends)
    if band is None or perp is None or run <= 0.0:
        return None
    d = ((ends[1][0] - ends[0][0]) / run, (ends[1][1] - ends[0][1]) / run)
    n = (-d[1], d[0])
    s_n = 1.0 if _centre(perp, n) > _centre(band, n) else -1.0
    s_d = 1.0 if _centre(band, d) > _centre(perp, d) else -1.0
    across = _span(band, n)[1 if s_n > 0 else 0]
    along = _span(perp, d)[1 if s_d > 0 else 0] + s_d * _STRAP_HALF_WIDTH_M
    point = (d[0] * along + n[0] * across, d[1] * along + n[1] * across)
    return point, (-s_n * n[0], -s_n * n[1])


def placed(model: ResolvedModel, runs: list, point, tol: float) -> tuple | None:
    """``(return, axis, leaf xy, outward)`` of a corner's strap, or ``None`` where it cannot
    rise plumb from a Figure 1 entry: the house rule places a strap only where a published
    installation fits (ESR-2920 prints no jog), and no code asks for one at a corner."""
    at = [(ret, ends) for ret, ends in runs if any(math.dist(point, p) <= tol for p in ends)]
    ret, ends = at[0]
    end_axis = axis_of(*ends)
    other = next((o for o, o_ends in at if axis_of(*o_ends) != end_axis), None)
    placed = _inside_corner(model, ret, ends, other) if other is not None else None
    xy, outward = placed if placed is not None else ((point[0], point[1]), None)
    if outward is not None and not plumb_entry_fits(model, ret, xy, outward):
        return None
    return ret, end_axis, xy, outward


def plumb_entry_fits(model: ResolvedModel, ret, xy, outward) -> bool:
    """The catalog spoon reaches across the core from the leaf, so the strap needs no jog."""
    from typehaus.joints.sills import Station, strap_holdown_model
    from typehaus.resolve.connector_geometry.ties import SILHOUETTE, strap_part

    wall = model.wall(ret.element_tags[0]) if ret.element_tags else None
    layer = next((lyr for lyr in wall.layers if lyr.function == "structure" and lyr.polygon),
                 None) if wall is not None else None
    if layer is None:
        return True
    probe = Station(run_tag=ret.tag, storey=ret.storey, point_m=xy, z_m=ret.z0_m, axis="x",
                    framed_tag=ret.element_tags[1] if len(ret.element_tags) > 1 else None)
    dims = EMBEDDED_STRAPS[strap_part(strap_holdown_model(model, probe))]
    # The frame turns the spoon toward the far face; it fits where that reach, less cover,
    # takes the catalog projection from the leaf itself (``embedded_strap_frame``'s rule).
    offsets = [(p[0] - xy[0]) * outward[0] + (p[1] - xy[1]) * outward[1]
               for p in layer.polygon]
    reach_in = max(max(offsets), -min(offsets)) / M_PER_IN
    return reach_in - SILHOUETTE.embedded_spoon_cover_in >= dims.spoon_projection_in - 1e-6

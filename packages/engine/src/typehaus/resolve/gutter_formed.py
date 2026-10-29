"""A catalog gutter swept as its one formed piece at true gauge, with its end-cap plates.

The authored ``path`` is the line of the section's origin (the back's water face at the back
top), ``top_elevation`` that origin's height, ``back_side`` which way the wall is. The flange
takes the host roof's pitch. Under an Image II eave that runs past the path's ends, the
trough runs on to the eave's end so the eave's face, kick and lip stop over it; the caps close
it there (``library/trim/metal_sales.FORMED_GUTTERS``).
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.library.trim.metal_sales import FORMED_GUTTERS
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.flashing_solids import flashing_solid
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_slice import sweep_mesh
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.roof_edge_geometry import roof_slope
from typehaus.resolve.roof_image_ii_eave import LAP_GAP_M

#: How far off the run an eave piece may lie and still be the one this gutter hangs under.
_EAVE_REACH_M = 12 * M_PER_IN
_UP = (0.0, 0.0, 1.0)


def resolve_formed_gutter(model, el, storey: str) -> bool:
    """Append the gutter and its caps; ``False`` when the product has no formed section."""
    spec = FORMED_GUTTERS.get(getattr(el, "product", None) or "")
    roof = next((r for r in model.roofs if r.tag == el.host_ref), None)
    if spec is None or roof is None:
        return False
    section_of, cap_of, (left_part, right_part) = spec
    section = tuple((x * M_PER_IN, y * M_PER_IN) for x, y in section_of(roof_slope(roof)))
    cap = tuple((x * M_PER_IN, y * M_PER_IN) for x, y in cap_of(SHEET_24_GA_M / M_PER_IN))
    path = [p.xy_m for p in el.path]
    top = el.top_elevation.meters
    last = len(path) - 2
    for i, (a, b) in enumerate(zip(path[:-1], path[1:], strict=True)):
        d, n, length = _frame(a, b, el.back_side)
        e0, e1 = _eave_overrun(roof, a, d, n, length)
        e0, e1 = (e0 if i == 0 else 0.0), (e1 if i == last else 0.0)
        start = (a[0] - d[0] * e0, a[1] - d[1] * e0, top)
        run = tuple(d[k] * (length + e0 + e1) for k in range(2)) + (0.0,)
        axis = (n[0], n[1], 0.0)
        mesh = folded_section_mesh(section, start, axis, _UP, run, SHEET_24_GA_M)
        model.solids.append(replace(flashing_solid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey, category="gutter",
            mesh=mesh, material=el.material, host_ref=el.host_ref, billed_elsewhere=False),
            product=el.product))
        # Viewed from the front (facing the wall), the left hand is (n.y, -n.x).
        end_is_left = d[0] * n[1] - d[1] * n[0] > 0.0
        ends = []
        if i == 0:
            ends.append((-(e0 + LAP_GAP_M + SHEET_24_GA_M), a, not end_is_left))
        if i == last:
            ends.append((length + e1 + LAP_GAP_M, a, end_is_left))
        for along, base, is_left in ends:
            hand = "L" if is_left else "R"
            origin = (base[0] + d[0] * along, base[1] + d[1] * along, top)
            plate = _plate_mesh(cap, origin, axis, (d[0] * SHEET_24_GA_M,
                                                    d[1] * SHEET_24_GA_M, 0.0))
            model.solids.append(replace(flashing_solid(
                uid=f"{el.uid}-cap-{hand.lower()}", tag=f"{el.tag}-CAP-{hand}", storey=storey,
                category="gutter", mesh=plate, material=el.material, host_ref=el.host_ref,
                billed_elsewhere=False), product=left_part if is_left else right_part))
    return True


def _frame(a, b, back_side: str):
    """``(along unit, outboard unit, length)``; the wall is on ``back_side`` of a->b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    d = (dx / length, dy / length)
    n = (d[1], -d[0]) if back_side == "left" else (-d[1], d[0])
    return d, n, length


def _eave_overrun(roof, a, d, n, length: float) -> tuple[float, float]:
    """How far the host's Image II eave piece runs past each end of this segment."""
    from typehaus.resolve.roof_image_ii import CONNECTION_EAVE

    e0 = e1 = 0.0
    for member in roof.members:
        if member.connection != CONNECTION_EAVE:
            continue
        ends = [(p[0] - a[0], p[1] - a[1]) for p in (member.p0, member.p1)]
        if any(abs(x * n[0] + y * n[1]) > _EAVE_REACH_M for x, y in ends):
            continue
        along = [x * d[0] + y * d[1] for x, y in ends]
        e0, e1 = max(e0, -min(along)), max(e1, max(along) - length)
    return e0, e1


def _plate_mesh(polygon, origin, first_axis, run):
    """A flat plate: ``polygon`` in (first_axis, up) at ``origin``, extruded along ``run``."""
    points = [tuple(origin[k] + first_axis[k] * u + _UP[k] * v for k in range(3))
              for u, v in polygon]
    area = sum(p[0] * q[1] - q[0] * p[1]
               for p, q in zip(polygon, (*polygon[1:], polygon[0]), strict=True))
    # (first_axis x up) . run decides which winding faces along the extrusion.
    facing = (first_axis[1] * run[0] - first_axis[0] * run[1]) * area
    if facing < 0:
        points.reverse()
    return sweep_mesh(GSweep(profile=tuple(points), extrude=run))

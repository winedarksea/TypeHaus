"""Oriented plan footprint + z-band for a framing member (shapely-free).

Deliberately more precise than ``emit/gltf/emitter.py``'s ``add_member_box``, which
uses ``half_width`` for both plan directions (a square approximation). The
interference check needs the true thickness×depth rectangle so a joist bearing on a
beam reads as a thin band, not a square. ``add_member_box`` is intentionally left as
is — changing it would alter rendered geometry with no benefit here; emit may later
adopt this helper.

Returns a plain :data:`~typehaus.resolve.model.Ring` so this module stays free of the
geometry kernel; callers (the check) wrap it in a shapely ``Polygon``.
"""

from __future__ import annotations

import math

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, Ring


def member_footprint(member: FramedMember) -> tuple[Ring, float, float]:
    """Oriented plan footprint + ``(z_lo, z_hi)`` for a framing member."""
    cs = cross_section(member.profile)
    (x0, y0), (x1, y1) = member.p0, member.p1
    dx, dy = x1 - x0, y1 - y0
    run = math.hypot(dx, dy)

    zs = [member.z0_m, member.z1_m]
    if member.z0_end_m is not None:
        zs.append(member.z0_end_m)
    if member.z1_end_m is not None:
        zs.append(member.z1_end_m)
    z_lo, z_hi = min(zs), max(zs)

    if run < 1e-9:
        # Vertical member: an oriented width_m × depth_m rectangle centered at p0,
        # long axis along member.orient (axis-aligned when orient is None).
        hw, hd = cs.width_m / 2.0, cs.depth_m / 2.0
        if member.orient is not None:
            ox, oy = member.orient
            olen = math.hypot(ox, oy)
            if olen > 1e-9:
                ux, uy = ox / olen, oy / olen  # depth (long) axis
                px, py = -uy, ux  # width (thickness) axis
                ring = [
                    (x0 + ux * hd + px * hw, y0 + uy * hd + py * hw),
                    (x0 - ux * hd + px * hw, y0 - uy * hd + py * hw),
                    (x0 - ux * hd - px * hw, y0 - uy * hd - py * hw),
                    (x0 + ux * hd - px * hw, y0 + uy * hd - py * hw),
                ]
                return ring, z_lo, z_hi
        ring = [(x0 - hw, y0 - hd), (x0 + hw, y0 - hd),
                (x0 + hw, y0 + hd), (x0 - hw, y0 + hd)]
        return ring, z_lo, z_hi

    # Horizontal/sloped member: thickness-wide band along p0->p1.
    hw = cs.width_m / 2.0
    nx, ny = -dy / run * hw, dx / run * hw  # perpendicular half-width offset
    ring = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
            (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
    return ring, z_lo, z_hi

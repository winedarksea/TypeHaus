"""A take-off or tee drawn as a flanged collar (decision #114, #136).

The collar is a tube of the branch section from the main's surface for the row's
``collar_length`` (else the record's ``length_m``, else 2"). The flange is a thin plate on
that surface, 1/2" oversize all round; on a round main it is a saddle that follows the
curve, so it never floats off the shell.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.resolve.boot_solids import COLLAR_LENGTH_M, FLANGE_LAP_M, FLANGE_T_M
from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.duct_mesh import (
    _FACETS,
    Section,
    _add,
    _dot,
    _unit,
    loft,
    parse_section,
    prism,
)
from typehaus.resolve.geometry_ir import GMesh, Vec3
from typehaus.resolve.sweep import leg_frame

#: A round main's saddle stops this fraction of its radius from the silhouette.
_SADDLE_MAX = 0.98


def run_at(model: Any, tag: str, point: Vec3) -> tuple[Any, Vec3 | None]:
    """The run and its unit direction at the leg nearest ``point`` (plan, then z)."""
    duct = next((d for d in model.ducts if d.tag == tag), None)
    if duct is None or len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
        return duct, None
    pts = [(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)]
    best = None
    for a, b in zip(pts, pts[1:], strict=False):
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        n2 = sum(c * c for c in ab)
        if n2 < 1e-12:
            continue
        t = max(0.0, min(1.0, sum((point[i] - a[i]) * ab[i] for i in range(3)) / n2))
        gap = math.dist(point, _add(a, ab, t))
        if best is None or gap < best[0]:
            best = (gap, ab)
    return duct, _unit(best[1]) if best else None


def surface_offset(model: Any, part: Any, axis: Vec3) -> float:
    """From the main's centreline out to its surface along ``axis`` (a take-off's start)."""
    _, direction = run_at(model, part.run_tag, part.point)
    section = parse_section(part.size)
    if section is None or direction is None:
        return 0.0
    if section.is_round:
        return section.width / 2.0
    right, up = leg_frame(direction)
    ar = abs(_dot(axis, right))
    au = abs(_dot(axis, up))
    reach = (section.width / 2.0 / ar if ar > 1e-9 else math.inf,
             section.depth / 2.0 / au if au > 1e-9 else math.inf)
    return min(reach) if min(reach) < math.inf else 0.0


def collar_length(model: Any, part: Any) -> float:
    """The collar's length: the house row's ``collar_length``, else the record's, else 2"."""
    from typehaus.resolve.duct_standard import duct_standard

    standard, _ = duct_standard(getattr(model, "plan", None))
    row = standard.part(part.kind, part.size, part.branch) if standard is not None else None
    if row is not None and row.collar_length is not None:
        return row.collar_length.meters
    return part.length_m or COLLAR_LENGTH_M


def takeoff_branch_start(model: Any, part: Any) -> float:
    """Distance from ``part.point`` along ``part.axis`` to the collar's outer end."""
    axis = _unit(part.axis)
    if axis is None:
        return 0.0
    return surface_offset(model, part, axis) + collar_length(model, part)


def _outline(branch: Section, saddle: bool) -> list[tuple[float, float]]:
    """The flange's convex outline in (right, up), 1/2" past the collar all round."""
    hw, hd = branch.width / 2.0 + FLANGE_LAP_M, branch.depth / 2.0 + FLANGE_LAP_M
    if branch.is_round:
        return [(hw * math.cos(2 * math.pi * i / _FACETS), hd * math.sin(2 * math.pi * i / _FACETS))
                for i in range(_FACETS)]
    steps = 4 if saddle else 1  # a curved main needs points along each edge
    corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    return [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
            for a, b in zip(corners, corners[1:] + corners[:1], strict=True)
            for k in range(steps)]


def flange_mesh(origin: Vec3, axis: Vec3, branch: Section, main: Section | None,
                run: Vec3 | None) -> GMesh:
    """A thin plate on the main's surface at ``origin``, normal to ``axis``. Over a round
    main whose axis crosses the take-off it dips with the shell (a saddle)."""
    right, up = leg_frame(axis)
    radius = main.width / 2.0 if main is not None and main.is_round else None
    across = None
    if radius is not None and run is not None and abs(_dot(axis, run)) < 0.2:
        across = _unit((axis[1] * run[2] - axis[2] * run[1], axis[2] * run[0] - axis[0] * run[2],
                        axis[0] * run[1] - axis[1] * run[0]))
    bottom, top = [], []
    for u, v in _outline(branch, across is not None):
        p = _add(_add(origin, right, u), up, v)
        dip = 0.0
        if across is not None and radius is not None:
            lateral = min(abs(_dot(tuple(p[i] - origin[i] for i in range(3)), across)),
                          radius * _SADDLE_MAX)
            dip = math.sqrt(radius ** 2 - lateral ** 2) - radius
        base = _add(p, axis, dip)
        bottom.append(base)
        top.append(_add(base, axis, FLANGE_T_M))
    return prism(bottom, top)


def takeoff_mesh(model: Any, part: Any, axis: Vec3, branch: Section) -> GMesh:
    """The collar tube plus its flange, for a ``takeoff`` / ``tee`` / ``drain_tee`` record."""
    start = _add(part.point, axis, surface_offset(model, part, axis))
    _, run = run_at(model, part.run_tag, part.point)
    tube = loft(start, axis, branch, branch, collar_length(model, part))
    return combine_meshes(tube, flange_mesh(start, axis, branch, parse_section(part.size), run))

"""A framing angle nailed member-to-plate: one leaf up a member face, one flat on the sill.

The A35 as a joist-to-sill or block-to-sill tie (C-C-2026 A35 installation "joist to sill"):
the strip's width runs along the face, and its length folds half up the face and half
across the sill top. ``ties._angle_tie`` keeps the upright post-to-beam frame the authored
angles use. Heights come from the sill return under the tie, never from authored values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.catalog import ROLE_SILL_TIE, ROLE_WALL_TOP_TIE
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import box_mesh, combine_meshes, transform_mesh
from typehaus.resolve.geometry_ir import GMesh

_ALIASES = {"A35Z": "A35", "A35SS": "A35"}
#: Clear of the member or block the leaf sits beside.
_GAP_M = 0.125 * M_PER_IN
#: How far a ply partner's or rim's end may sit from the tied end and still be at it.
_NEAR_M = 6.0 * M_PER_IN


@dataclass(frozen=True)
class PlateAngle:
    width_m: float  # along the face
    leg_m: float  # each leaf, off the heel
    thickness_m: float


def plate_angle_dims(part: str) -> PlateAngle | None:
    from typehaus.resolve.connector_geometry.ties import ANGLES, STEEL_THICKNESS_IN

    name = _ALIASES.get(part.strip().upper(), part.strip().upper())
    if name != "A35":
        return None
    d = ANGLES[name]
    return PlateAngle(d.leaf_width_in * M_PER_IN, d.height_in / 2.0 * M_PER_IN,
                      STEEL_THICKNESS_IN[d.gauge] * M_PER_IN)


def is_plate_angle(joint, part: str) -> bool:
    return joint.role in (ROLE_WALL_TOP_TIE, ROLE_SILL_TIE) and plate_angle_dims(part) is not None


def plate_angle_mesh(dims: PlateAngle, centre, inward, z_m: float) -> GMesh:
    """The L with its heel centred on ``centre`` (on the face, at ``z_m``), flat leaf inward."""
    w, leg, t = (v / M_PER_IN for v in (dims.width_m, dims.leg_m, dims.thickness_m))
    body = combine_meshes(box_mesh((-w / 2, 0.0, 0.0), (w / 2, leg, t)),
                          box_mesh((-w / 2, 0.0, t), (w / 2, t, leg)))
    nx, ny = inward
    return transform_mesh(body, origin_m=(centre[0], centre[1], z_m),
                          x_axis=(ny, -nx, 0.0), y_axis=(nx, ny, 0.0), z_axis=(0.0, 0.0, 1.0))


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = math.hypot(dx, dy) or 1.0
    return dx / run, dy / run


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1]


def footprint(centre, inward, dims):
    """The flat leaf's plan rectangle on the sill."""
    from shapely.geometry import Polygon

    h, (nx, ny) = dims.width_m / 2.0, inward
    heel = (ny, -nx)
    return Polygon([(centre[0] + heel[0] * s + nx * d, centre[1] + heel[1] * s + ny * d)
                    for s, d in ((-h, 0.0), (h, 0.0), (h, dims.leg_m), (-h, dims.leg_m))])


def _framing(index) -> list:
    """``(bounds, member)`` for every floor member but the rims, once per index."""
    from typehaus.resolve.framing.profiles import cross_section

    cached = index.__dict__.get("_plate_angle_framing")
    if cached is None:
        cached = []
        for floor in index.model.floors:
            for m in floor.members:
                if m.category == "rim":
                    continue
                r = (m.plan_width_m or cross_section(m.profile).width_m) / 2.0
                cached.append(((min(m.p0[0], m.p1[0]) - r, min(m.p0[1], m.p1[1]) - r,
                                max(m.p0[0], m.p1[0]) + r, max(m.p0[1], m.p1[1]) + r), r, m))
        index.__dict__["_plate_angle_framing"] = cached
    return cached


def _clear(index, centre, inward, dims) -> bool:
    """No framing but the rims stands where the tie would lie."""
    from shapely.geometry import LineString

    spot = footprint(centre, inward, dims)
    x0, y0, x1, y1 = spot.bounds
    for (a, b, c, d), r, m in _framing(index):
        if a >= x1 or c <= x0 or b >= y1 or d <= y0:
            continue
        if LineString([m.p0, m.p1]).buffer(r, cap_style=2).intersection(spot).area > 1e-7:
            return False
    return True


def _sill_tie_face(index, joint, floor, dims):
    """``(centre, inward)`` for a joist-end tie, beside its joist on the side away from any
    ply partner (a pack's second tie takes the other outer face); a lone member takes the
    first side clear of framing. An I-joist or LSL end ties on the end rim's inboard face;
    a truss or sawn end on its own side face."""
    from typehaus.hardware.plan_geometry import distance_point_to_segment
    from typehaus.resolve.framing.profiles import cross_section

    key, _, ply = (joint.carried_member_key or "").partition("#")
    member = index.members.get(key)
    if member is None:
        return None
    point = joint.point
    end, far = ((member.p0, member.p1) if math.dist(point, member.p0)
                <= math.dist(point, member.p1) else (member.p1, member.p0))
    u = _unit(end, far)
    a = (-u[1], u[0])
    width = member.plan_width_m or cross_section(member.profile).width_m
    lo, hi = -width / 2.0, width / 2.0
    partners = []
    for s in floor.members:
        if s.category != "sister_joist" or abs(_dot(_unit(s.p0, s.p1), a)) > 0.01:
            continue
        if min(math.dist(point, s.p0), math.dist(point, s.p1)) > _NEAR_M:
            continue
        off = _dot((s.p0[0] - end[0], s.p0[1] - end[1]), a)
        sw = s.plan_width_m or cross_section(s.profile).width_m
        lo, hi = min(lo, off - sw / 2.0), max(hi, off + sw / 2.0)
        partners.append(off)
    half = dims.width_m / 2.0
    face = None
    if cross_section(member.profile).shape == "i_joist" or "lsl" in member.profile.lower():
        rims = [r for r in floor.members if r.category == "rim"
                and abs(_dot(_unit(r.p0, r.p1), u)) < 0.01
                and distance_point_to_segment(end, r.p0, r.p1) <= _NEAR_M]
        face = 0.0
        if rims:
            rim = min(rims, key=lambda r: distance_point_to_segment(end, r.p0, r.p1))
            rw = rim.plan_width_m or cross_section(rim.profile).width_m
            face = _dot((rim.p0[0] - end[0], rim.p0[1] - end[1]), u) + rw / 2.0

    def placed(side):
        across = hi if side > 0 else lo
        if face is not None:
            lateral = across + side * (_GAP_M + half)
            return ((end[0] + u[0] * face + a[0] * lateral,
                     end[1] + u[1] * face + a[1] * lateral), u)
        along = _GAP_M + half
        return ((end[0] + a[0] * across + u[0] * along, end[1] + a[1] * across + u[1] * along),
                (a[0] * side, a[1] * side))

    if partners:
        side = (-1.0 if sum(partners) >= 0.0 else 1.0) * (-1.0 if ply else 1.0)
        return placed(side)
    options = [placed(-1.0), placed(1.0)]
    return next((p for p in options if _clear(index, *p, dims)), options[0])


def plate_angle_body(index, joint) -> GMesh | None:
    """The tie at a wall-top station or a joist end, on its face and the sill top."""
    from typehaus.joints.wall_top import edge_face, sill_returns, sill_top_z

    dims = plate_angle_dims(joint.part)
    wall = index.model.wall(joint.members[0]) if joint.members else None
    floor = index.hosts.get(joint.members[1]) if len(joint.members) > 1 else None
    if dims is None or wall is None or floor is None:
        return None
    if joint.role == ROLE_WALL_TOP_TIE:
        face = edge_face(floor, wall)
        if face is None:
            return None
        placed = (joint.point, face[1])
    else:
        placed = _sill_tie_face(index, joint, floor, dims)
        if placed is None:
            return None
    centre, inward = placed
    top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
    probe = (centre[0] + inward[0] * dims.leg_m / 2, centre[1] + inward[1] * dims.leg_m / 2)
    returns = index.__dict__.get("_plate_angle_returns")
    if returns is None:
        returns = index.__dict__["_plate_angle_returns"] = sill_returns(index.model)
    z_m = sill_top_z(index.model, probe, top, returns)
    return plate_angle_mesh(dims, centre, inward, joint.z_m if z_m is None else z_m)

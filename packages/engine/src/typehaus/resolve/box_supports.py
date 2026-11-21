"""How each device box holds to its framing (decision #149), read off ``BoxRow.support``.

* Wall ``stud_side`` (a nail-on box): ``stud_seat`` lists every upright of the box's wall
  that spans its height and depth, sets the box against one face (off by the ear's
  thickness) and keeps the smallest move that lands it clear of every member, opening,
  pocket and other box. The bank moves with it (``device_banks._place``).
* Wall ``stud_span``: a bracket across the bay, stud face to stud face; no move.
* Ceiling: the host's members parallel to the dominant direction near the point give a
  face each side (``ceiling_fit``): a ``joist_span`` bar runs face to face, its span read
  as member centres or clear opening against the listed range; a ``joist_side`` bracket (or
  a nail-on box) reaches the nearer face; ``member_under`` screws under the member over
  the point. Ceiling boxes never move (#140).

A mount that cannot reach records a ``fault`` and draws nothing; ``electrical.box_support``
FAILs it. The mount is its own solid, so the box's outline and collision stay body-only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from shapely.geometry import MultiPoint
from shapely.geometry.polygon import orient

from typehaus.model.electrical import BoxSupport
from typehaus.quantities import M_PER_IN
from typehaus.resolve.box_support_mesh import block, side_plate, spanning_bar
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.model import ResolvedSolid

Point = tuple[float, float]
Vec3 = tuple[float, float, float]
TOL_M = 0.125 * M_PER_IN  # an overlap under 1/8" is a touch
SPAN_TOL_M = 0.25 * M_PER_IN  # a listed range read to the nearest 1/4"
_SEAT_DEPTH_M = 0.5 * M_PER_IN  # a stud must back at least this much of the box's side
_MAX_SHIFT_M = 16 * M_PER_IN
_PLATE_MARGIN_M = 0.5 * M_PER_IN  # a plate's overhang past its box, each side
_REACH_M = 30 * M_PER_IN  # members farther than this off the point are not its flanks
_ABOVE_M = 0.6  # a host member's underside at most this far over the face
_ANGLE_TOL = math.radians(3)
_FURRING_MIN_M = 1.5 * M_PER_IN  # 2x furring holds a box; 1x strapping does not
#: What a bar or bracket may bear on; the first set sets the bay's direction.
_PRIMARY = frozenset({"joist", "sister_joist", "trimmer", "rafter", "roof_truss"})
_FRAMING = _PRIMARY | {"rim", "header", "ledger", "blocking", "plate", "strongback",
                       "barge_rafter", "outlooker", "ridge_beam"}


@dataclass(frozen=True)
class SupportFit:
    kind: str
    product: str | None
    members: tuple[str, ...] = ()
    span_m: float | None = None
    shift_m: float = 0.0
    fault: str | None = None
    mesh: GMesh | None = None


def _span(points: list[Point], axis: Point, origin: Point = (0.0, 0.0)) -> tuple[float, float]:
    values = [(x - origin[0]) * axis[0] + (y - origin[1]) * axis[1] for x, y in points]
    return min(values), max(values)


def _overlap(a: tuple[float, float], b: tuple[float, float]) -> float:
    return min(a[1], b[1]) - max(a[0], b[0])


def _uprights(model: Any, wall: Any, face_point: Point, tangent: Point, normal: Point,
              z0: float, z1: float, depth: float):
    """(seats, obstacles) as station spans along ``tangent``: a seat is an upright spanning
    the box's band and backing its side; an obstacle any upright, opening, pocket, other
    box or wall end in its band and depth."""
    box_n = (-depth, 0.0)
    seats, obstacles = [], []
    for member in wall.members:
        if member.p0 != member.p1 or member.plan_outline is not None:
            continue
        if _overlap((member.z0_m, member.z1_m), (z0, z1)) <= TOL_M:
            continue
        solid = member_box(member)
        if solid is None:
            continue
        ring = [(x, y) for x, y, _z in solid.corners_bottom]
        depth_overlap = _overlap(_span(ring, normal, face_point), box_n)
        if depth_overlap <= TOL_M:
            continue  # the other face's stud in a staggered wall
        span = _span(ring, tangent)
        obstacles.append(span)
        if (depth_overlap >= min(_SEAT_DEPTH_M, depth) and member.z0_m <= z0 + TOL_M
                and member.z1_m >= z1 - TOL_M):
            seats.append((span, member.child_key))
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay) or 1.0
    u = ((bx - ax) / length, (by - ay) / length)
    for o in model.openings:
        if o.host_wall != wall.tag:
            continue
        sill = wall.base_ref_z_m + o.sill_m
        if _overlap((sill, sill + o.height_m), (z0, z1)) <= 0:
            continue
        a = o.center_along_m - o.width_m / 2 - (o.pocket_run_m if o.pocket_sign < 0 else 0)
        b = o.center_along_m + o.width_m / 2 + (o.pocket_run_m if o.pocket_sign > 0 else 0)
        obstacles.append(_span([(ax + u[0] * a, ay + u[1] * a), (ax + u[0] * b, ay + u[1] * b)],
                               tangent))
    for other in model.device_boxes:  # a back-to-back box shares the cavity
        if (other.wall_tag != wall.tag or other.mounting == "surface"
                or _overlap((other.z0_m, other.z1_m), (z0, z1)) <= 0):
            continue
        if _overlap(_span(list(other.footprint), normal, face_point), box_n) > TOL_M:
            obstacles.append(_span(list(other.footprint), tangent))
    ends = _span([(ax, ay), (bx, by)], tangent)
    obstacles += [(ends[0] - 1.0, ends[0]), (ends[1], ends[1] + 1.0)]
    face = _face_run(wall, face_point, tangent, normal, z0, z1)
    if face is not None:  # an inside corner: the plate must clear the other wall's face
        obstacles += [(face[0] - 1.0, face[0] + _PLATE_MARGIN_M),
                      (face[1] - _PLATE_MARGIN_M, face[1] + 1.0)]
    return seats, obstacles


def _face_run(wall: Any, face_point: Point, tangent: Point, normal: Point, z0: float,
              z1: float) -> tuple[float, float] | None:
    """The finish face's run along ``tangent`` about the device: the outermost layers'
    spans merged where they touch, the one holding ``face_point``; None if none does."""
    pieces = []
    for layer in wall.layers:
        if layer.is_cavity or not layer.polygon:
            continue
        if (layer.z0_m is not None and layer.z0_m >= z1) or (
                layer.z1_m is not None and layer.z1_m <= z0):
            continue
        pieces.append((_span(list(layer.polygon), normal, face_point)[1],
                       _span(list(layer.polygon), tangent)))
    if not pieces:
        return None
    outer = max(reach for reach, _ in pieces)
    spans = sorted(span for reach, span in pieces if reach >= outer - 1e-3)
    here = face_point[0] * tangent[0] + face_point[1] * tangent[1]
    merged: list[list[float]] = []
    for lo, hi in spans:
        if merged and lo <= merged[-1][1] + TOL_M:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return next(((lo, hi) for lo, hi in merged if lo - TOL_M <= here <= hi + TOL_M), None)


def stud_seat(model: Any, wall: Any, face_point: Point, tangent: Point, normal: Point,
              lo: float, hi: float, z0: float, z1: float, depth: float,
              thick: float) -> tuple[float, str, int] | None:
    """(shift along ``tangent``, stud key, side -1/+1) setting the box ``lo..hi`` (absolute
    stations along ``tangent``) against the nearest clear stud face, or None."""
    seats, obstacles = _uprights(model, wall, face_point, tangent, normal, z0, z1, depth)
    best = None
    for (a, b), key in seats:
        for side, shift in ((-1, b + thick - lo), (1, a - thick - hi)):
            if abs(shift) > _MAX_SHIFT_M or (best is not None and abs(shift) >= abs(best[0])):
                continue
            if all(_overlap(span, (lo + shift, hi + shift)) <= TOL_M for span in obstacles):
                best = (shift, key, side)
    return best


def stud_flanks(model: Any, wall: Any, face_point: Point, tangent: Point, normal: Point,
                lo: float, hi: float, z0: float, z1: float, depth: float):
    """(left, right, clash): the stud faces either side of a box ``lo..hi`` as (station,
    key, half-thickness) or None, and whether anything sits in the box's span."""
    seats, obstacles = _uprights(model, wall, face_point, tangent, normal, z0, z1, depth)
    left = max(((b, k, (b - a) / 2) for (a, b), k in seats if b <= lo + TOL_M), default=None)
    right = min(((a, k, (b - a) / 2) for (a, b), k in seats if a >= hi - TOL_M), default=None)
    clash = any(_overlap(span, (lo, hi)) > TOL_M for span in obstacles)
    return left, right, clash


def wall_fit(support: BoxSupport, seat: tuple[float, str, int] | None, origin: Vec3,
             tangent: Point, normal: Point, width: float, height: float, depth: float,
             flanks: tuple | None = None) -> SupportFit:
    """A wall box's mount, after ``stud_seat`` (``stud_side``) or ``stud_flanks``
    (``stud_span``, stations absolute along ``tangent``); ``origin`` is the face centre."""
    kind, product = support.kind, support.product_ref
    w, thick = (part.meters for part in support.section)
    if kind == "stud_side":
        if seat is None:
            return SupportFit(kind, product, fault=(
                f"no stud face within {_MAX_SHIFT_M / M_PER_IN:.0f} in. seats the nail-on box "
                "clear of the framing, openings and other boxes"))
        shift, key, side = seat
        length = support.length.meters if support.length else height
        mesh = side_plate(origin, (*tangent, 0.0), (*normal, 0.0), (0.0, 0.0, 1.0), side,
                          width / 2, depth, support.offset.meters, w, thick, length)
        return SupportFit(kind, product, (key,), None, shift, mesh=mesh)
    if kind == "stud_span" and flanks is not None:
        left, right, clash = flanks
        if clash:
            return SupportFit(kind, product, fault=(
                "the bracketed box sits over framing, an opening, another box or the corner"))
        if left is None or right is None:
            return SupportFit(kind, product, fault="the bracket finds a stud on one side only")
        here = origin[0] * tangent[0] + origin[1] * tangent[1]
        (s0, k0, h0), (s1, k1, h1) = left, right
        span = s1 - s0 if support.span_basis == "clear" else s1 - s0 + h0 + h1
        fault = _range_fault(support, span, f"{k0} and {k1}")
        t3, n3 = (*tangent, 0.0), (*normal, 0.0)
        centre = _at(origin, (n3, -support.offset.meters - thick / 2))
        mesh = None if fault else spanning_bar(centre, t3, (0.0, 0.0, 1.0), n3, s0 - here,
                                               s1 - here, w, thick, support.profile)
        return SupportFit(kind, product, (k0, k1), span, fault=fault, mesh=mesh)
    return SupportFit(kind, product, fault=(
        f"a wall box's {kind!r} mount is not derived; author a stud_side or stud_span row"))


def _range_fault(support: BoxSupport, span: float, between: str) -> str | None:
    if support.span is None:
        return None
    low, high = (part.meters for part in support.span)
    if low - SPAN_TOL_M <= span <= high + SPAN_TOL_M:
        return None
    return (f"{span / M_PER_IN:.2f} in. {support.span_basis} between {between} is outside "
            f"its {low / M_PER_IN:g}-{high / M_PER_IN:g} in. range")


@dataclass(frozen=True)
class Furring:
    """A ceiling lining's furring layer with a ``FramingSpec``: its band over the face."""

    name: str
    spacing_m: float
    half_m: float  # half the member's thickness
    z0_m: float  # above the finish face
    z1_m: float


def ceiling_fit(support: BoxSupport, members: list[Any], host: str, origin: Vec3,
                axis: Vec3, width: float, under: str | None = None,
                furring: Furring | None = None, footprint: tuple = ()) -> SupportFit:
    """A ceiling box's mount off its host's ``members``; ``under`` names the member a
    surface box hangs from where the caller already found it. A mount at a height inside
    a ``furring`` band (2x or deeper) bears on the furring, laid at its spacing (its strips
    are a field layout, not members): a bar spans one bay of it."""
    kind, product = support.kind, support.product_ref
    w, t = (part.meters for part in support.section)
    up = (-axis[0], -axis[1], -axis[2])
    if (furring is not None and kind != "member_under"
            and furring.z1_m - furring.z0_m >= _FURRING_MIN_M
            and furring.z0_m - TOL_M <= support.offset.meters <= furring.z1_m + TOL_M):
        on = (f"{host}/{furring.name}",)
        if kind != "joist_span":
            return SupportFit(kind, product, on)
        clear = furring.spacing_m - 2 * furring.half_m
        span = clear if support.span_basis == "clear" else furring.spacing_m
        fault = _range_fault(support, span, f"{furring.name} strips")
        along = _in_plane((1.0, 0.0, 0.0), axis)
        mesh = None if fault else spanning_bar(
            _at(origin, (up, support.offset.meters)), along, _cross(up, along), up,
            -clear / 2, clear / 2, w, t, support.profile)
        return SupportFit(kind, product, on, span, fault=fault, mesh=mesh)
    if kind == "member_under":
        if under is None:
            under = _member_over(members, origin)
        if under is None:
            return SupportFit(kind, product, fault=f"no member of {host} over the box")
        m = _in_plane(_member_dir(members, under), axis)
        across = _cross(m, up)
        length = support.length.meters if support.length else width
        mesh = block(_at(origin, (axis, t / 2)), (m, across, up), (length / 2, w / 2, t / 2))
        return SupportFit(kind, product, (f"{host}/{under}",), mesh=mesh)
    flanks = _flanks(members, origin, axis)
    if flanks is None:
        return SupportFit(kind, product, fault=f"no framing of {host} near the box")
    direction, left, right = flanks
    across_plan = (-direction[1], direction[0])
    along = _lift(across_plan, axis)
    m = _in_plane((*direction, 0.0), axis)
    centre = _at(origin, (up, support.offset.meters))
    if kind == "joist_span":
        if left is None or right is None:
            return SupportFit(kind, product, fault=(
                f"the bar finds a {host} member on one side only within "
                f"{_REACH_M / M_PER_IN:.0f} in."))
        (s0, k0, h0), (s1, k1, h1) = left, right
        clear = s1 - s0
        span = clear if support.span_basis == "clear" else clear + h0 + h1
        fault = _range_fault(support, span, f"{host}/{k0} and {k1}")
        mesh = None if fault else spanning_bar(centre, along, m, up, s0, s1, w, t,
                                               support.profile)
        return SupportFit(kind, product, (f"{host}/{k0}", f"{host}/{k1}"), span, fault=fault,
                          mesh=mesh)
    # joist_side, or a nail-on box on a ceiling: the nearer face within reach of its edge.
    reach = (support.reach.meters if support.reach is not None
             else t + TOL_M if kind == "stud_side" else 0.0)
    near = [f for f in (left, right) if f is not None]
    if not near:
        return SupportFit(kind, product, fault=f"no member of {host} beside the box")
    s, key, _ = min(near, key=lambda f: abs(f[0]))
    half = max((abs((x - origin[0]) * across_plan[0] + (y - origin[1]) * across_plan[1])
                for x, y in footprint), default=width / 2)  # the box across the members
    gap = abs(s) - half
    if gap < -TOL_M:
        return SupportFit(kind, product, (f"{host}/{key}",), gap, fault=(
            f"the box sits {-gap / M_PER_IN:.2f} in. into {host}/{key}"))
    if gap > reach + TOL_M:
        return SupportFit(kind, product, (f"{host}/{key}",), gap, fault=(
            f"the nearer {host} member face ({key}) is {gap / M_PER_IN:.2f} in. off the box; "
            f"its mount reaches {reach / M_PER_IN:.2f} in."))
    edge = math.copysign(half, s)
    mesh = spanning_bar(centre, along, m, up, min(edge, s), max(edge, s), w, t, support.profile)
    return SupportFit(kind, product, (f"{host}/{key}",), gap, mesh=mesh)


def _flanks(members: list[Any], origin: Vec3, axis: Vec3):
    """(member plan direction, left face, right face): each face (signed offset across the
    members from the point, key, half-thickness), from the dominant direction near it."""
    near = []
    for member in members:
        (x0, y0), (x1, y1) = member.p0, member.p1
        run = math.hypot(x1 - x0, y1 - y0)
        if run < 1e-6 or member.category not in _FRAMING:
            continue
        u = ((x1 - x0) / run, (y1 - y0) / run)
        rx, ry = origin[0] - x0, origin[1] - y0
        along, offset = rx * u[0] + ry * u[1], rx * -u[1] + ry * u[0]
        if not -TOL_M <= along <= run + TOL_M or abs(offset) > _REACH_M:
            continue
        foot = (x0 + u[0] * along, y0 + u[1] * along)
        bottom = member.z0_m
        if member.z0_end_m is not None:
            bottom += (member.z0_end_m - member.z0_m) * along / run
        gap = bottom - _plane_z(origin, axis, foot)
        if not -0.05 <= gap <= _ABOVE_M:
            continue
        near.append((math.atan2(u[1], u[0]) % math.pi, member))
    if not near:
        return None

    def parallel(a: float, b: float) -> bool:
        d = abs(a - b) % math.pi
        return min(d, math.pi - d) <= _ANGLE_TOL
    lead = [a for a, m in near if m.category in _PRIMARY] or [a for a, _ in near]
    angle = max(lead, key=lambda a: sum(parallel(a, b) for b in lead))
    direction = (math.cos(angle), math.sin(angle))
    left = right = None
    for a, member in near:
        if not parallel(a, angle):
            continue
        offset = ((origin[0] - member.p0[0]) * direction[1]
                  - (origin[1] - member.p0[1]) * direction[0])
        half = cross_section(member.profile).width_m / 2
        s = offset  # the member's axis, across from the point
        if s < 0 and (left is None or s + half > left[0]):
            left = (s + half, member.child_key, half)
        elif s >= 0 and (right is None or s - half < right[0]):
            right = (s - half, member.child_key, half)
    return direction, left, right


def _member_over(members: list[Any], origin: Vec3) -> str | None:
    from shapely.geometry import Point as SPoint
    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint
    for member in members:
        if member.p0 == member.p1:
            continue
        ring, _, _ = member_footprint(member)
        if len(ring) >= 3 and Polygon(ring).covers(SPoint(origin[:2])):
            return member.child_key
    return None


def _member_dir(members: list[Any], key: str) -> Vec3:
    member = next((m for m in members if m.child_key == key), None)
    if member is None or member.p0 == member.p1:
        return (1.0, 0.0, 0.0)
    (x0, y0), (x1, y1) = member.p0, member.p1
    run = math.hypot(x1 - x0, y1 - y0)
    return ((x1 - x0) / run, (y1 - y0) / run, 0.0)


def support_fields(fit: SupportFit) -> dict[str, Any]:
    """The ``ResolvedDeviceBox`` mount fields of ``fit``."""
    return {"support_kind": fit.kind, "support_product": fit.product,
            "support_members": fit.members, "support_span_m": fit.span_m,
            "stud_shift_m": fit.shift_m, "support_fault": fit.fault}


def support_solid(uid: str, tag: str, storey: str, fit: SupportFit) -> ResolvedSolid | None:
    """``<device uid>-box-support``, category ``electrical_box_support``; None with no mesh."""
    if fit.mesh is None:
        return None
    hull = orient(MultiPoint([p[:2] for p in fit.mesh.positions]).convex_hull, 1.0)
    return ResolvedSolid(
        uid=f"{uid}-box-support", tag=f"{tag}-BOX-SUPPORT", storey=storey,
        category="electrical_box_support",
        outline=[tuple(p) for p in list(hull.exterior.coords)[:-1]],
        z0_m=min(p[2] for p in fit.mesh.positions), z1_m=max(p[2] for p in fit.mesh.positions),
        product=fit.product, body_mesh=fit.mesh, derived=True)  # billed in [electrical_boxes]


def _plane_z(origin: Vec3, axis: Vec3, xy: Point) -> float:
    if abs(axis[2]) < 1e-9:
        return origin[2]
    return origin[2] - (axis[0] * (xy[0] - origin[0]) + axis[1] * (xy[1] - origin[1])) / axis[2]


def _lift(plan: Point, axis: Vec3) -> Vec3:
    """A plan direction lifted onto the face plane, its plan part unchanged."""
    z = 0.0 if abs(axis[2]) < 1e-9 else -(plan[0] * axis[0] + plan[1] * axis[1]) / axis[2]
    return (plan[0], plan[1], z)


def _in_plane(v: Vec3, axis: Vec3) -> Vec3:
    lifted = _lift(v[:2], axis)
    norm = math.sqrt(sum(c * c for c in lifted)) or 1.0
    return (lifted[0] / norm, lifted[1] / norm, lifted[2] / norm)


def _at(origin: Vec3, *terms: tuple[Vec3, float]) -> Vec3:
    return tuple(origin[i] + sum(v[i] * k for v, k in terms) for i in range(3))


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

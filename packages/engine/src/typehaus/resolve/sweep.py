"""Swept runs: one section carried along a 3D polyline — the shared kernel.

``ResolvedSolid`` is a plan ring extruded straight up in Z, which is the only shape a prism
can speak — anything that rakes or slopes cannot be one prism.

A run is one thing, so it is one solid. :class:`~typehaus.resolve.model.SolidSweep` says
"I am a section carried along a 3D polyline", and this module is the geometry behind that
sentence — mitred at the corners, one :class:`~typehaus.resolve.geometry_ir.GBox` per leg.
Both the Python emitters and the viewer (``ui/src/three/tubeGeometry.ts``) mirror it, and
``tests/test_sweep_kernel.py`` plus the shared TS fixture pin the two together.

Frame convention
----------------
A leg's local "up" is **world +Z projected perpendicular to the leg axis**, so a rectangular
rail's flat face stays level on a rake instead of rolling with the slope; a vertical leg has
no such projection and falls back to world **+Y**. "right" is ``up × d``, which makes
``(right, up, d)`` right-handed — so a profile wound counter-clockwise in ``(u, v)`` comes
out with its side facets facing outward, exactly as ``GBox`` wants them.

Stdlib only, like the rest of ``resolve/`` — the whole engine runs in Pyodide.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.resolve.geometry_ir import Ring3, Vec2, Vec3

if TYPE_CHECKING:  # the IR carries the sweep, so the reference stays type-only
    from typehaus.resolve.model import SolidSweep

#: Past this much deviation from straight, an interior vertex stops being a mitre and starts
#: being a *fitting*: a 90° turn in a drain is an elbow you buy, and a 90° mitre in a rail is
#: a spike four diameters long. Legs on either side of such a vertex butt square instead.
MAX_MITER_DEG = 80.0

#: A *plan* corner mitres much further than a section does: the mitre of two offset lines is
#: exactly the union of two butted rectangles at 90°, and only starts over-reaching as the
#: run doubles back on itself. Past this, the silhouette squares the corner off instead.
_MAX_PLAN_MITER_DEG = 150.0

#: Two path points closer than this (in 3D) are the same point — a repeated plan vertex with
#: the same invert, which a run picks up from authored elbows.
_EPS_M = 1e-9


def round_profile(radius: float, facets: int) -> tuple[Vec2, ...]:
    """A regular ``facets``-gon of the given radius, wound counter-clockwise in ``(u, v)``.

    Vertex-centred at angle 0, so an even facet count puts flats top and bottom of a
    horizontal run — the silhouette a pipe or a round handrail reads as.
    """
    if facets < 3:
        raise ValueError("round_profile needs at least three facets")
    return tuple((radius * math.cos(2.0 * math.pi * i / facets),
                  radius * math.sin(2.0 * math.pi * i / facets))
                 for i in range(facets))


def rect_profile(width: float, depth: float) -> tuple[Vec2, ...]:
    """A rectangle ``width`` across the leg (u) by ``depth`` through it (v), CCW."""
    hw, hd = width / 2.0, depth / 2.0
    return ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))


def _sub3(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot3(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross3(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm3(a: Vec3) -> float:
    return math.sqrt(_dot3(a, a))


def _unit3(a: Vec3) -> Vec3:
    n = _norm3(a)
    if n < 1e-15:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def clean_path(path: tuple[Vec3, ...] | list[Vec3]) -> tuple[Vec3, ...]:
    """The path with consecutive duplicate points dropped — never fewer than the first."""
    out: list[Vec3] = []
    for point in path:
        point = (float(point[0]), float(point[1]), float(point[2]))
        if out and _norm3(_sub3(point, out[-1])) <= _EPS_M:
            continue
        out.append(point)
    return tuple(out)


def leg_frame(direction: Vec3) -> tuple[Vec3, Vec3]:
    """``(right, up)`` for a leg running along ``direction`` — see the module docstring."""
    d = _unit3(direction)
    up = _sub3((0.0, 0.0, 1.0), (d[0] * d[2], d[1] * d[2], d[2] * d[2]))
    if _norm3(up) < 1e-9:  # a vertical leg: world +Z has no perpendicular component
        up = _sub3((0.0, 1.0, 0.0), (d[0] * d[1], d[1] * d[1], d[2] * d[1]))
    up = _unit3(up)
    return _cross3(up, d), up


def _ring_at(vertex: Vec3, direction: Vec3, right: Vec3, up: Vec3,
             profile: tuple[Vec2, ...], plane_normal: Vec3) -> Ring3:
    """The leg's profile placed at ``vertex`` and cut by the plane with ``plane_normal``.

    Each profile point is slid *along the leg axis* until it meets the plane. With
    ``plane_normal == direction`` that slide is zero and the ring is square to the leg,
    which is the butt joint; with the bisector it is the mitre. Because both legs at a
    vertex slide their own ring onto the *same* plane from frames that share world +Z, the
    two rings land on the same points and the tube closes.
    """
    denominator = _dot3(direction, plane_normal)
    points: list[Vec3] = []
    for u, v in profile:
        offset = (right[0] * u + up[0] * v,
                  right[1] * u + up[1] * v,
                  right[2] * u + up[2] * v)
        t = 0.0 if abs(denominator) < 1e-9 else -_dot3(offset, plane_normal) / denominator
        points.append((vertex[0] + offset[0] + direction[0] * t,
                       vertex[1] + offset[1] + direction[1] * t,
                       vertex[2] + offset[2] + direction[2] * t))
    return tuple(points)


def sweep_legs(sweep: SolidSweep) -> list[tuple[Ring3, Ring3]]:
    """One ``(start_ring, end_ring)`` pair per leg — each pair is exactly one ``GBox``.

    Interior vertices mitre: the shared ring lies in the plane bisecting the two legs, so a
    gentle rake change or a slack plan bend is a continuous tube with no seam. Past
    :data:`MAX_MITER_DEG` the legs butt square instead of throwing a spike four diameters
    long — which is also honest, because a turn that sharp is a fitting in the field.
    """
    path = clean_path(sweep.path)
    profile = tuple(sweep.profile)
    if len(path) < 2 or len(profile) < 3:
        return []
    dirs = [_unit3(_sub3(path[i + 1], path[i])) for i in range(len(path) - 1)]
    frames = [leg_frame(d) for d in dirs]
    normals: list[Vec3] = [dirs[0]]
    cos_limit = math.cos(math.radians(MAX_MITER_DEG))
    for i in range(1, len(dirs)):
        previous, current = dirs[i - 1], dirs[i]
        if _dot3(previous, current) >= cos_limit:
            normals.append(_unit3((previous[0] + current[0], previous[1] + current[1],
                                   previous[2] + current[2])))
        else:
            normals.append((0.0, 0.0, 0.0))  # butt: each leg squares off on its own axis
    normals.append(dirs[-1])
    legs: list[tuple[Ring3, Ring3]] = []
    for i, direction in enumerate(dirs):
        right, up = frames[i]
        start_normal = normals[i] if _norm3(normals[i]) > 1e-9 else direction
        end_normal = normals[i + 1] if _norm3(normals[i + 1]) > 1e-9 else direction
        legs.append((_ring_at(path[i], direction, right, up, profile, start_normal),
                     _ring_at(path[i + 1], direction, right, up, profile, end_normal)))
    return legs


def is_round_profile(profile: tuple[Vec2, ...]) -> bool:
    """Whether a section is a faceted circle rather than a shaped one.

    Six facets or more, all on one radius. Both stock round sections in the engine clear it
    (a pipe's 12-gon, a round handrail's 8-gon) and a square rail's four corners do not,
    which is the distinction IFC wants: a circular run is one ``IfcSweptDiskSolid`` over its
    directrix — the IFC4 idiom for a pipe *and* for a rail — and a shaped one is not.
    """
    if len(profile) < 6:
        return False
    radii = [math.hypot(u, v) for u, v in profile]
    return max(radii) - min(radii) <= 1e-9 * max(max(radii), 1.0)


def profile_radius_m(profile: tuple[Vec2, ...]) -> float:
    """The circumscribed radius of a section — its true radius when it is round."""
    return max((math.hypot(u, v) for u, v in profile), default=0.0)


def sweep_leg_axes(sweep: SolidSweep) -> list[tuple[Vec3, Vec3, Vec3, float]]:
    """``(origin, axis, ref_direction, length)`` per leg — an extrusion's four inputs.

    The straight-extrusion reading of a run, for IFC: ``origin`` is the leg's start point on
    the centreline, ``axis`` the direction it runs, ``ref_direction`` the profile's local X
    (the same "right" :func:`leg_frame` gives, so the section is oriented as the tessellated
    geometry has it). ``IfcExtrudedAreaSolid`` cannot express the mitre, so a leg exported
    this way is square-ended — which for a shaped section is the honest approximation, and a
    round one takes the swept-disk path instead and keeps its mitre.
    """
    path = clean_path(sweep.path)
    out: list[tuple[Vec3, Vec3, Vec3, float]] = []
    for i in range(len(path) - 1):
        delta = _sub3(path[i + 1], path[i])
        run = _norm3(delta)
        if run < _EPS_M:
            continue
        direction = _unit3(delta)
        right, _up = leg_frame(direction)
        out.append((path[i], direction, right, run))
    return out


def sweep_length_m(sweep: SolidSweep) -> float:
    """Developed 3D length of the run — what a rail or a pipe is actually billed by."""
    path = clean_path(sweep.path)
    return sum(_norm3(_sub3(path[i + 1], path[i])) for i in range(len(path) - 1))


def sweep_z_extent(sweep: SolidSweep) -> tuple[float, float]:
    """``(z0, z1)`` of the whole run *including* the section — the solid's Z extents."""
    zs = [point[2] for leg in sweep_legs(sweep) for ring in leg for point in ring]
    if not zs:
        path = clean_path(sweep.path)
        return (min(p[2] for p in path), max(p[2] for p in path)) if path else (0.0, 0.0)
    return (min(zs), max(zs))


def _plan_half_width(profile: tuple[Vec2, ...]) -> float:
    """How far the section reaches sideways — its extent along the leg's local "right"."""
    return max((abs(u) for u, _v in profile), default=0.0)


def sweep_plan_silhouette(sweep: SolidSweep) -> list[Vec2]:
    """The run's plan footprint, as the ring ``ResolvedSolid.outline`` keeps carrying.

    Consumers that have not been taught about sweeps — the plan sheet's railing polylines,
    the take-off's centroid — read ``outline`` and must keep getting something honest. This
    is the polyline offset each side by the section's half width, mitred at the corners —
    which at a butted 90° turn is *exactly* the union of the two squared-off legs, and only
    starts over-reaching as the run doubles back, where it squares off instead. A leg with
    no plan direction (a vertical drop) contributes nothing but the point it drops through.
    """
    path = clean_path(sweep.path)
    half = _plan_half_width(tuple(sweep.profile))
    plan: list[Vec2] = []
    for x, y, _z in path:
        if not plan or math.hypot(x - plan[-1][0], y - plan[-1][1]) > 1e-9:
            plan.append((x, y))
    if not plan:
        return []
    if len(plan) == 1 or half <= 0.0:
        (x, y) = plan[0]
        return [(x - half, y - half), (x + half, y - half),
                (x + half, y + half), (x - half, y + half)]
    normals: list[Vec2] = []
    for i in range(len(plan) - 1):
        dx, dy = plan[i + 1][0] - plan[i][0], plan[i + 1][1] - plan[i][1]
        n = math.hypot(dx, dy) or 1.0
        normals.append((-dy / n, dx / n))
    cos_limit = math.cos(math.radians(_MAX_PLAN_MITER_DEG))
    left: list[Vec2] = []
    right: list[Vec2] = []

    def place(point: Vec2, offset: Vec2) -> None:
        left.append((point[0] + offset[0], point[1] + offset[1]))
        right.append((point[0] - offset[0], point[1] - offset[1]))

    for i, point in enumerate(plan):
        if i == 0 or i == len(plan) - 1:
            edge = normals[0] if i == 0 else normals[-1]
            place(point, (edge[0] * half, edge[1] * half))
            continue
        before, after = normals[i - 1], normals[i]
        if before[0] * after[0] + before[1] * after[1] >= cos_limit:
            mx, my = before[0] + after[0], before[1] + after[1]
            scale2 = mx * mx + my * my
            factor = half * 2.0 / scale2 if scale2 > 1e-12 else half
            place(point, (mx * factor, my * factor))
        else:
            place(point, (before[0] * half, before[1] * half))
            place(point, (after[0] * half, after[1] * half))
    return left + list(reversed(right))


@dataclass(frozen=True)
class Turn:
    """One interior vertex of a run: where it turns, and by how much.

    ``angle_deg`` is the true 3D deviation from straight — a vertical drop meeting a
    horizontal branch measures the 90° it actually is, rather than the plan-only guess the
    fitting estimate used to make. ``plan_angle_deg`` is the same deviation projected into
    plan, which is what tells a 90° sweep on the flat from a 90° drop.
    """

    index: int
    point: Vec3
    angle_deg: float
    plan_angle_deg: float


def sweep_turns(sweep: SolidSweep) -> list[Turn]:
    """Every interior vertex that actually turns — the fitting take-off's input."""
    path = clean_path(sweep.path)
    turns: list[Turn] = []
    for i in range(1, len(path) - 1):
        before = _unit3(_sub3(path[i], path[i - 1]))
        after = _unit3(_sub3(path[i + 1], path[i]))
        angle = math.degrees(math.acos(max(-1.0, min(1.0, _dot3(before, after)))))
        pa = math.hypot(before[0], before[1])
        pb = math.hypot(after[0], after[1])
        if pa < 1e-9 or pb < 1e-9:
            plan_angle = 0.0  # a vertical leg has no plan direction to turn from
        else:
            cosine = (before[0] * after[0] + before[1] * after[1]) / (pa * pb)
            plan_angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
        if angle > 1e-6:
            turns.append(Turn(index=i, point=path[i], angle_deg=angle,
                              plan_angle_deg=plan_angle))
    return turns


def simplify_path(points: tuple[Vec3, ...] | list[Vec3], plan_tol_m: float,
                  z_tol_m: float) -> tuple[Vec3, ...]:
    """Drop every vertex that neither the plan nor the section's Z would miss.

    A rail is *sampled* off the walking surface under it — one point every quarter metre —
    and a straight flight's samples all lie on one line. Collapsing them is what turns 60
    stations back into the 2-point run the carpenter cuts; a winder, whose samples genuinely
    curve, keeps as many as its own tolerance needs.

    The test is against the chord from the last **kept** vertex, not from the neighbour, so
    error cannot accumulate across a long collapse.
    """
    path = clean_path(points)
    if len(path) < 3:
        return path
    kept = [path[0]]
    anchor = 0
    index = 1
    while index < len(path) - 1:
        candidate = index + 1
        if _within(path, anchor, candidate, plan_tol_m, z_tol_m):
            index = candidate
            continue
        kept.append(path[index])
        anchor = index
        index += 1
    kept.append(path[-1])
    return tuple(kept)


def _within(path: tuple[Vec3, ...], anchor: int, end: int,
            plan_tol_m: float, z_tol_m: float) -> bool:
    """Whether every vertex between ``anchor`` and ``end`` hugs the chord between them."""
    a, b = path[anchor], path[end]
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    plan_len = math.hypot(dx, dy)
    for i in range(anchor + 1, end):
        p = path[i]
        if plan_len < 1e-12:
            if math.hypot(p[0] - a[0], p[1] - a[1]) > plan_tol_m:
                return False
            t = (p[2] - a[2]) / dz if abs(dz) > 1e-12 else 0.0
        else:
            t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (plan_len * plan_len)
            if abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / plan_len > plan_tol_m:
                return False
        if abs(p[2] - (a[2] + dz * t)) > z_tol_m:
            return False
    return True

"""How each air terminal meets the run it names, read from 3D geometry (decision #136).

``terminal_joints(model)`` keys a ``TerminalJoint`` by register tag for every ``Register``
naming a ``duct_ref`` whose run resolves. The kind is derived, never authored (an authored
field would go stale on every UI drag), tried in this order:

* ``inlet``: the run's ``end_terminal_ref`` names it; its last vertex meets the dimensioned
  inlet (``problem`` = ``terminal_connections.inlet_connection_error``).
* ``drop``: a plain ceiling neck the run is ``engaged`` with; the run end nearest the
  collar top (``problem`` = ``terminal_drops.collar_seat_problem``).
* ``through``: a leg crosses the terminal's ROOM face inside the face and carries on past
  it into the room by more than ``plane_m``: the run passes through the grille.
* ``end``: a run end behind the face (``terminal_faces.terminal_face``) within
  ``boot_reach_m`` of it, its centre over the face (face half-extent plus the run's half
  section, each way), and not past the room face. ``turn`` is ``straight`` when the run
  leaves along the face normal, ``90`` when it arrives across it.
* ``side``: a ray from the face centre along its normal hits a leg's surface within
  ``boot_reach_m``, the boot's mouth (the face's extent along the leg) clear of the leg's
  ends: a take-off collar on the trunk.
* ``unreached``: none of these; ``detail`` gives the nearest end.

Fields are metres. ``point`` is on the run's centreline where the boot meets it (the end
vertex, the side hit, the room-face crossing for ``through``); ``axis`` the run's unit
direction there (into the run for an end); ``face`` the terminal's duct-side face;
``gap_m`` the boot's reach from the face to the run's near surface (an end's own tip when
straight); ``offset_m`` the run's centre off the face centre, across the normal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_branches import duct_ends
from typehaus.resolve.terminal_faces import TerminalFace, inlet_face, terminal_face

Vec3 = tuple[float, float, float]

INLET, DROP, THROUGH, END, SIDE, UNREACHED = (
    "inlet", "drop", "through", "end", "side", "unreached")
STRAIGHT, TURN_90 = "straight", "90"

#: The most a boot spans from the terminal face to the run's near surface: a 4" round
#: take-off collar tall (``mep.register_reach``'s boot drop). Catlin's largest is 3.1".
BOOT_REACH_M = 4.0 * M_PER_IN
#: A point this close to a plane is on it.
PLANE_TOLERANCE_M = M_PER_IN / 16.0
#: An end leaving within 45 degrees of the face normal takes a straight boot.
STRAIGHT_COS = math.cos(math.radians(45.0))


@dataclass(frozen=True)
class JointTolerances:
    """The census-frozen limits; lateral reach is derived (face half-extent + run half
    section), never a constant. A register outside these needs a house fix, not a wider one."""

    boot_reach_m: float = BOOT_REACH_M
    plane_m: float = PLANE_TOLERANCE_M
    straight_cos: float = STRAIGHT_COS


TOLERANCES = JointTolerances()


@dataclass(frozen=True)
class TerminalJoint:
    """One register's connection to its run (see the module docstring)."""

    register: str
    run: str
    kind: str
    point: Vec3 | None = None
    axis: Vec3 | None = None
    face: TerminalFace | None = None
    turn: str | None = None
    leg: int | None = None
    end_index: int | None = None
    gap_m: float | None = None
    offset_m: float | None = None
    detail: str = ""
    problem: str | None = None


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _sub(a, b) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _along(p, d, k: float) -> Vec3:
    return (p[0] + d[0] * k, p[1] + d[1] * k, p[2] + d[2] * k)


def _unit(v) -> Vec3 | None:
    n = math.sqrt(_dot(v, v))
    return (v[0] / n, v[1] / n, v[2] / n) if n > 1e-9 else None


def _in(metres: float) -> str:
    return f'{metres / M_PER_IN:.1f}"'


def half_section(duct: Any, axis: Vec3, direction: Vec3) -> float:
    """The run's half section along ``direction``, for a leg along ``axis``. Along the axis
    itself it is the half section along the turn's other direction, so call it with a
    direction across the leg. A rectangular riser's orientation is unread: its smaller half.
    """
    if duct.diameter_m is not None:
        return duct.diameter_m / 2.0
    w, d = duct.width_m / 2.0, duct.depth_m / 2.0
    right = _unit((axis[1], -axis[0], 0.0))
    if right is None:
        return min(w, d)
    up = (right[1] * axis[2] - right[2] * axis[1], right[2] * axis[0] - right[0] * axis[2],
          right[0] * axis[1] - right[1] * axis[0])
    return abs(_dot(direction, right)) * w + abs(_dot(direction, up)) * d


def _points(duct: Any) -> list[Vec3]:
    return [(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)]


def terminal_joints(model: Any, tol: JointTolerances = TOLERANCES) -> dict[str, TerminalJoint]:
    """``{register tag: TerminalJoint}`` for every placed register naming a resolved run."""
    from typehaus.resolve.terminal_drops import collars_by_run, engaged

    types = {t.tag: t for t in getattr(model.plan.library, "register_types", ())}
    objects = {o.tag: o for o in model.canvas_objects}
    ducts = {d.tag: d for d in model.ducts
             if len(d.path) >= 2 and len(d.z_m) == len(d.path)}
    collars = collars_by_run(model)
    out: dict[str, TerminalJoint] = {}
    for el in model.plan.all_elements():
        if el.element_kind != "Register" or not getattr(el, "duct_ref", None):
            continue
        duct, obj = ducts.get(el.duct_ref), objects.get(el.tag)
        if duct is None or obj is None:
            continue  # no run or no placed register: other checks say so
        authored = model.plan.by_tag(duct.tag)
        if getattr(authored, "end_terminal_ref", None) == el.tag:
            out[el.tag] = _inlet(model, el.tag, duct)
            continue
        seated = dict(engaged(duct, collars.get(duct.tag, ())))
        if el.tag in seated:
            out[el.tag] = _drop(model, el.tag, obj, types.get(obj.type_ref), duct,
                                seated[el.tag])
            continue
        out[el.tag] = classify(el.tag, duct, _face(model, obj, types.get(obj.type_ref), duct),
                               tol)
    return out


def _face(model: Any, obj: Any, register_type: Any, duct: Any) -> TerminalFace | None:
    mid = ((obj.body_z0_m + obj.body_z1_m) / 2.0
           if obj.body_z0_m is not None and obj.body_z1_m is not None else 0.0)
    toward = min(_points(duct), key=lambda p: math.dist(p, (*obj.position, mid)))
    return terminal_face(model, obj, register_type, toward)


def _inlet(model: Any, tag: str, duct: Any) -> TerminalJoint:
    from typehaus.resolve.terminal_connections import inlet_connection_error

    pts = _points(duct)
    index = len(pts) - 1
    axis = _unit(_sub(pts[index - 1], pts[index]))
    face = inlet_face(model, tag)
    off = math.dist(pts[index], face.centre) if face else None
    detail = (f"{duct.tag} ends on {tag}'s dimensioned inlet"
              + (f", {_in(off)} off its centre" if off is not None else ""))
    return TerminalJoint(tag, duct.tag, INLET, pts[index], axis, face, STRAIGHT, index - 1,
                         index, None, off, detail, inlet_connection_error(model, tag))


def _drop(model: Any, tag: str, obj: Any, register_type: Any, duct: Any,
          collar: Any) -> TerminalJoint:
    from typehaus.resolve.terminal_drops import collar_seat_problem

    top = (collar.x, collar.y, collar.z_top)
    span, index, point, axis = min(((math.dist(p, top), i, p, a) for i, p, a in duct_ends(duct)),
                                   key=lambda e: e[0])
    at_end = index != 0
    problem = collar_seat_problem(duct.path, duct.z_m, at_end, tag, collar, duct)
    return TerminalJoint(
        tag, duct.tag, DROP, point, axis, terminal_face(model, obj, register_type), STRAIGHT,
        index - 1 if at_end else 0, index, span, math.dist(point[:2], top[:2]),
        f"{duct.tag} {'end' if at_end else 'start'} is {_in(span)} from {tag}'s collar top",
        problem)


def classify(tag: str, duct: Any, face: TerminalFace | None,
             tol: JointTolerances = TOLERANCES) -> TerminalJoint:
    """``through`` / ``end`` / ``side`` / ``unreached`` for a run against a placed face."""
    if face is None:
        return TerminalJoint(tag, duct.tag, UNREACHED, detail=(
            f"{tag}'s face cannot be placed (no host behind it), so {duct.tag} cannot be "
            "read against it"))
    pts = _points(duct)
    return (_through(tag, duct, face, pts, tol) or _end(tag, duct, face, pts, tol)
            or _side(tag, duct, face, pts, tol) or _unreached(tag, duct, face, tol))


def _lateral(face: TerminalFace, p: Vec3) -> tuple[float, float]:
    r = _sub(p, face.centre)
    return _dot(r, face.width_axis), _dot(r, face.height_axis)


def _through(tag, duct, face, pts, tol) -> TerminalJoint | None:
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        da = _dot(_sub(a, face.centre), face.normal) + face.room_offset_m
        db = _dot(_sub(b, face.centre), face.normal) + face.room_offset_m
        past = -min(da, db)
        if da * db >= 0.0 or past <= tol.plane_m:
            continue
        hit = _along(a, _sub(b, a), da / (da - db))
        u, v = _lateral(face, hit)
        if abs(u) > face.width_m / 2.0 + tol.plane_m or abs(v) > face.height_m / 2.0 + tol.plane_m:
            continue  # crosses the face's plane beside it
        return TerminalJoint(
            tag, duct.tag, THROUGH, hit, _unit(_sub(b, a)), face, None, k,
            offset_m=math.hypot(u, v),
            detail=(f"{duct.tag} passes through {tag}'s face and runs {_in(past)} on into the "
                    f"room (leg {k}, {_in(math.hypot(u, v))} off its centre)"))
    return None


def _end(tag, duct, face, pts, tol) -> TerminalJoint | None:
    best = None
    for index, point, axis in duct_ends(duct):
        cos = _dot(axis, face.normal)
        if cos <= -tol.straight_cos:
            continue  # the run comes back at the face from the room side
        straight = cos >= tol.straight_cos
        dn = _dot(_sub(point, face.centre), face.normal)
        near = 0.0 if straight else half_section(duct, axis, face.normal)
        gap = dn - near
        if gap > tol.boot_reach_m + tol.plane_m or gap < -face.room_offset_m - tol.plane_m:
            continue
        u, v = _lateral(face, point)
        if not all(abs(off) <= half + _cross_half(duct, axis, e, face.normal) + tol.plane_m
                   for off, half, e in ((u, face.width_m / 2.0, face.width_axis),
                                        (v, face.height_m / 2.0, face.height_axis))):
            continue
        offset = math.hypot(u, v)
        rank = max(gap, 0.0) + offset
        if best is None or rank < best[0]:
            leg = 0 if index == 0 else len(pts) - 2
            best = (rank, TerminalJoint(
                tag, duct.tag, END, point, axis, face, STRAIGHT if straight else TURN_90, leg,
                index, gap, offset,
                f"{duct.tag} {'start' if index == 0 else 'end'} stands {_in(gap)} behind "
                f"{tag}'s {face.source} and {_in(offset)} off its centre "
                f"({'straight' if straight else '90'} boot)"))
    return best[1] if best else None


def _cross_half(duct, axis, direction, normal) -> float:
    """The run's half section along a face axis; along the run's own axis (a 90 end
    overshooting the face) the half section toward the face."""
    across = _sub(direction, _along((0.0, 0.0, 0.0), axis, _dot(direction, axis)))
    if math.sqrt(_dot(across, across)) < 0.5:
        return half_section(duct, axis, normal)
    return half_section(duct, axis, direction)


def _side(tag, duct, face, pts, tol) -> TerminalJoint | None:
    n = face.normal
    best = None
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        length = math.dist(a, b)
        d = _unit(_sub(b, a))
        if d is None or abs(_dot(d, n)) >= tol.straight_cos:
            continue  # a leg along the normal meets the face end-on, if at all
        w = _sub(a, face.centre)
        dn, wd, wn = _dot(d, n), _dot(w, d), _dot(w, n)
        den = 1.0 - dn * dn
        t = (dn * wn - wd) / den  # along the leg
        s = (wn - dn * wd) / den  # along the ray
        mouth = (abs(_dot(d, face.width_axis)) * face.width_m
                 + abs(_dot(d, face.height_axis)) * face.height_m) / 2.0
        if t < mouth or t > length - mouth:
            continue
        hit = _along(a, d, t)
        miss = _sub(hit, _along(face.centre, n, s))
        off = math.sqrt(_dot(miss, miss))
        if off > (half_section(duct, d, _unit(miss)) if off > 1e-9 else 0.0) + tol.plane_m:
            continue
        gap = s - half_section(duct, d, n)
        if gap < -tol.plane_m or gap > tol.boot_reach_m + tol.plane_m:
            continue
        if best is None or gap < best[0]:
            best = (gap, TerminalJoint(
                tag, duct.tag, SIDE, hit, d, face, None, k, None, gap, off,
                f"{tag}'s {face.source} stands {_in(gap)} off {duct.tag}'s side (leg {k}, "
                f"{_in(min(t, length - t))} from its nearer end)"))
    return best[1] if best else None


def _unreached(tag, duct, face, tol) -> TerminalJoint:
    rows = []
    for index, point, _ in duct_ends(duct):
        dn = _dot(_sub(point, face.centre), face.normal)
        rows.append((math.dist(point, face.centre), index, dn, math.hypot(*_lateral(face, point))))
    span, index, dn, off = min(rows)
    return TerminalJoint(
        tag, duct.tag, UNREACHED, face=face, end_index=index, gap_m=dn, offset_m=off,
        detail=(f"no end of {duct.tag} meets {tag}'s {face.source}, nor its side: the nearest "
                f"end stands {_in(dn)} behind it and {_in(off)} off its centre "
                f"(boot reach {_in(tol.boot_reach_m)})"))

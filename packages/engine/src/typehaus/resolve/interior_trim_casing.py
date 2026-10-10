"""Door casing: a picture frame on each finished face of a cased door.

In the host wall's frame, ``d`` measured out from the opening's centre line:

    inner edge = rough opening / 2 - jamb_allowance + reveal
    outer edge = inner edge + casing_width
    head bottom = rough-opening head - jamb_allowance + reveal

The legs run from the room's finished floor to the head; the head sits on them, flush with
their outer edges. A leg that runs into an adjacent wall, fixed casework or a neighbouring
door's casing is scribed back to it, and left off when less than ``min_leg_width`` is left;
each is a ``CasingClip`` that ``advisory.casing_clipped`` reports, never a silent trim.
"""

from __future__ import annotations

from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.interior_trim_scope import TrimScope, cased, face_function, is_finish
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.model_trim import CasingClip, ResolvedDoorCasing, TrimPiece
from typehaus.resolve.room_lookup import room_owning

# How far into the room the owner probe stands off the face.
_ROOM_PROBE_M = 0.15
# A raised sill (a hatch) gets a bottom piece; a door's threshold does not.
_RAISED_SILL_M = 0.05
# Overlap thinner than this is a touch, not an obstruction.
_TOUCH_M = 0.002


def resolve_door_casings(plan, model: ResolvedModel, scope: TrimScope) -> None:
    walls = {wall.tag: wall for wall in model.walls}
    laid: list[tuple[str, str, object]] = []  # (storey, opening tag, leg polygon)
    for opening in sorted(model.openings, key=lambda o: o.uid):
        if not opening.is_door or opening.kind != "door":
            continue
        if not cased(scope.door_types.get(opening.type_ref or "")):
            continue
        wall = walls.get(opening.host_wall)
        if wall is None:
            continue
        for side in (1, -1):
            casing = _casing(plan, model, scope, wall, opening, side, laid)
            if casing is not None:
                model.door_casings.append(casing)


def _casing(plan, model, scope: TrimScope, wall: ResolvedWall, opening, side: int, laid):
    from shapely.geometry import Polygon

    origin, tangent, normal, axis_length = wall_frame(wall)
    faces = finish_faces(wall)
    center = opening_center(wall, opening)
    if axis_length <= 1e-9 or faces is None or center is None:
        return None
    # A pocket's centre is shifted into its cavity; the casing stays on the axis station.
    cx = origin[0] + tangent[0] * opening.center_along_m
    cy = origin[1] + tangent[1] * opening.center_along_m
    face = faces[1] if side > 0 else faces[0]

    def at(d: float, offset: float) -> tuple[float, float]:
        return (cx + tangent[0] * d + normal[0] * offset, cy + tangent[1] * d + normal[1] * offset)

    s = scope.standard
    t, width = s.thickness.meters, s.casing_width.meters
    inner = opening.width_m / 2.0 - s.jamb_allowance.meters + s.reveal.meters
    outer = inner + width
    room = room_owning(model, wall.storey, at(0.0, face + side * _ROOM_PROBE_M))
    if room is None or room.tag not in scope.rooms:
        return None
    floor_z, _structural = scope.floors(model, room)
    into_wall = (-normal[0] * side, -normal[1] * side)
    function = face_function(wall, at(outer, face), into_wall, floor_z, floor_z + 0.1)
    if not is_finish(function):
        return None

    def rect(d0: float, d1: float) -> tuple[tuple[float, float], ...]:
        n0, n1 = face, face + side * t
        return (at(d0, n0), at(d1, n0), at(d1, n1), at(d0, n1))

    head_z = wall.base_ref_z_m + opening.sill_m + opening.height_m - s.jamb_allowance.meters \
        + s.reveal.meters
    sill_z = wall.base_ref_z_m + opening.sill_m
    raised = opening.sill_m > _RAISED_SILL_M or sill_z - floor_z > _RAISED_SILL_M
    # A hatch's frame closes with a sill piece mirroring the head; the legs stand on it.
    sill_z0 = sill_z + s.jamb_allowance.meters - s.reveal.meters - width
    leg_z0 = sill_z0 + width if raised else floor_z
    envelope = Polygon(rect(-outer, outer)).envelope.buffer(_TOUCH_M)
    obstacles = [(tag, polygon) for tag, polygon, z0, z1 in _obstacles(plan, model, scope, wall)
                 if z0 < head_z + width and z1 > leg_z0 and polygon.intersects(envelope)]
    obstacles.extend((f"casing of {tag}", polygon) for storey, tag, polygon in laid
                     if storey == wall.storey and tag != opening.tag)

    clips: list[CasingClip] = []
    reach: dict[int, float] = {}
    legs = []
    for sign, name in ((-1, "leg_left"), (1, "leg_right")):
        stop, blocker = outer, None
        strip = Polygon(rect(sign * inner, sign * outer))
        for tag, polygon in obstacles:
            hit = strip.intersection(polygon)
            if hit.is_empty or hit.area <= _TOUCH_M * t:
                continue
            nearest = min(abs(_station(cx, cy, tangent, x, y)) for x, y in _coords(hit))
            if nearest < stop:
                stop, blocker = max(nearest, inner), tag
        remaining = stop - inner
        dropped = remaining < s.min_leg_width.meters
        if blocker is not None:
            clips.append(CasingClip(piece=name, obstruction=blocker,
                                    remaining_m=max(remaining, 0.0), dropped=dropped))
        reach[sign] = stop
        if not dropped:
            legs.append(TrimPiece(name=name, outline=rect(sign * inner, sign * stop),
                                  z0_m=leg_z0, z1_m=head_z, length_m=head_z - leg_z0,
                                  width_m=remaining))
            laid.append((wall.storey, opening.tag, Polygon(rect(sign * inner, sign * stop))))
    pieces = list(legs)
    span = reach[-1] + reach[1]
    pieces.append(TrimPiece(name="head", outline=rect(-reach[-1], reach[1]), z0_m=head_z,
                            z1_m=head_z + width, length_m=span, width_m=width))
    if raised:
        pieces.append(TrimPiece(name="sill", outline=rect(-reach[-1], reach[1]),
                                z0_m=sill_z0, z1_m=sill_z0 + width, length_m=span,
                                width_m=width))
    label = "L" if side > 0 else "R"
    return ResolvedDoorCasing(
        uid=f"{opening.uid}-casing-{label.lower()}", tag=f"CASING-{opening.tag}-{label}",
        storey=wall.storey, opening_ref=opening.tag, opening_uid=opening.uid,
        wall_tag=wall.tag, room=room.tag, side=side, material_ref=s.material_ref,
        thickness_m=t, casing_width_m=width, pieces=tuple(pieces), clips=tuple(clips),
        profile=s.profile)


def _obstacles(plan, model: ResolvedModel, scope: TrimScope, host: ResolvedWall):
    """``(tag, plan polygon, z0, z1)`` a leg may run into on the host's storey: every other
    wall's body and the fixed things trim stops at (``TrimScope.fixed_footprints``)."""
    key = ("casing walls", host.storey)
    if key not in scope._cache:
        scope._cache[key] = [(wall.tag, scope.body(wall), wall.z0_m, wall.z1_m)
                             for wall in model.walls
                             if wall.storey == host.storey and wall.layers
                             and not scope.body(wall).is_empty]
    return ([entry for entry in scope._cache[key] if entry[0] != host.tag]
            + list(scope.fixed_footprints(plan, model, host.storey)))


def _station(cx, cy, tangent, x, y) -> float:
    return (x - cx) * tangent[0] + (y - cy) * tangent[1]


def _coords(geometry):
    for part in getattr(geometry, "geoms", (geometry,)):
        exterior = getattr(part, "exterior", None)
        yield from (exterior.coords if exterior is not None else part.coords)

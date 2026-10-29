"""R311.1 the egress door, and R311.2 its clear width and height (decision #97).

Only the door a plan designates (``Door.egress``) is graded for R311.2; any other exterior
door gets no R311.2 finding, because the rule does not cover it. That is not an N/A.
Widths and heights are ``ResolvedOpening.sizing``'s installed clear figures
(``resolve/door_sizing``): the maker's published ones where authored, else estimated.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DoorOperation, Occupancy
from typehaus.quantities import inch

_MIN_DOOR_CLEAR = inch(32)  # R311.2, read strictly: below 32" FAILs
_MIN_DOOR_CLEAR_HEIGHT = inch(78)  # R311.2
_SIDE_HINGED = (DoorOperation.SWING, DoorOperation.DOUBLE_SWING)
_PROBE_M = 0.15
_IN = 0.0254
_EGRESS = "code.R311_1_egress_door"
_WIDTH = "code.R311_door_width"
_HEIGHT = "code.R311_2_door_height"


def _doors(ctx: CheckContext):
    return [e for e in ctx.plan.all_elements() if e.element_kind == "Door"]


def designated_egress_doors(ctx: CheckContext):
    return [door for door in _doors(ctx) if getattr(door, "egress", False)]


def _door_type(ctx: CheckContext, door):
    return next((t for t in ctx.plan.library.door_types if t.tag == door.type_ref), None)


def _opening(ctx: CheckContext, door):
    return next((o for o in ctx.model.openings if o.tag == door.tag), None)


def _side_rooms(ctx: CheckContext, opening):
    """The rooms either side of the opening's host wall, at its centre."""
    from typehaus.resolve.geometry import wall_frame
    from typehaus.resolve.room_lookup import room_owning

    wall = ctx.model.wall(opening.host_wall)
    if wall is None:
        return []
    (sx, sy), (ux, uy), (nx, ny), _run = wall_frame(wall)
    cx, cy = sx + ux * opening.center_along_m, sy + uy * opening.center_along_m
    reach = wall.thickness_m / 2 + _PROBE_M
    rooms = [room_owning(ctx.model, wall.storey, (cx + side * nx * reach, cy + side * ny * reach))
             for side in (-1, 1)]
    return [room for room in rooms if room is not None]


@check(Tier.CODE, _EGRESS)
def egress_door_designated(ctx: CheckContext) -> list[Finding]:
    """R311.1 — one designated egress door: exterior, side-hinged, not from the garage.

    The route from every habitable room to it (not through a garage) is NOT graded here.
    """
    designated = designated_egress_doors(ctx)
    if not designated:
        return [_fail(_EGRESS, "no door is designated the egress door (Door.egress); R311.1 "
                      "requires at least one side-hinged exterior egress door",
                      (), "R311.1")]
    out: list[Finding] = []
    for door in designated:
        door_type, opening = _door_type(ctx, door), _opening(ctx, door)
        if door_type is None or opening is None:
            out.append(_unknown(_EGRESS, f"{door.tag}: no resolved door type or opening",
                                (door.tag,), "R311.1"))
            continue
        rooms = _side_rooms(ctx, opening)
        problems = []
        if not door_type.exterior:
            problems.append("is not an exterior door")
        if door_type.operation not in _SIDE_HINGED:
            problems.append(f"is not side-hinged ({door_type.operation.value})")
        if any(room.occupancy == Occupancy.GARAGE.value for room in rooms):
            problems.append("opens from the garage")
        if problems:
            out.append(_fail(_EGRESS, f"egress door {door.tag} " + " and ".join(problems),
                             (door.tag,), "R311.1"))
            continue
        inside = ", ".join(sorted(room.tag for room in rooms)) or "no resolved room"
        out.append(_pass(_EGRESS, f"{door.tag} is the designated egress door: exterior, "
                         f"side-hinged, opening from {inside}. The egress route from every "
                         "habitable room to it is not graded", "R311.1"))
    return out


def _grade(ctx: CheckContext, cid: str, value_of, minimum, what: str) -> list[Finding]:
    designated = designated_egress_doors(ctx)
    if not designated:
        return [_unknown(cid, "no designated egress door to grade (code.R311_1_egress_door)",
                         (), "R311.2")]
    out: list[Finding] = []
    for door in designated:
        opening = _opening(ctx, door)
        sizing = opening.sizing if opening is not None else None
        value, basis = value_of(sizing) if sizing is not None else (None, "")
        if value is None:
            out.append(_unknown(cid, f"{door.tag}: no {what} could be read", (door.tag,),
                                "R311.2"))
        elif value < minimum.meters - 1e-6:
            out.append(_fail(cid, f"egress door {door.tag} {what} {value / _IN:.2f}\" < "
                             f"{minimum.inches:g}\" ({basis})", (door.tag,), "R311.2"))
        else:
            out.append(_pass(cid, f"egress door {door.tag} {what} {value / _IN:.2f}\" >= "
                             f"{minimum.inches:g}\" ({basis})", "R311.2"))
    return out


@check(Tier.CODE, _WIDTH)
def egress_door_width(ctx: CheckContext) -> list[Finding]:
    """R311.2 — 32" of clear width at the designated egress door, leaf(s) at 90 degrees."""
    return _grade(ctx, _WIDTH, lambda s: (s.clear_w_m, s.basis_of("clear_w")),
                  _MIN_DOOR_CLEAR, "clear width")


@check(Tier.CODE, _HEIGHT)
def egress_door_height(ctx: CheckContext) -> list[Finding]:
    """R311.2 — 78" of installed clear height: top of threshold to underside of head stop."""
    return _grade(ctx, _HEIGHT, lambda s: (s.clear_h_m, s.basis_of("clear_h")),
                  _MIN_DOOR_CLEAR_HEIGHT, "clear height")

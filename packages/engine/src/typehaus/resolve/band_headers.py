"""A flush header in the floor band over a wall opening (``Door.header_in_band``).

The host wall frames no header there (``framing/band_opening.py``); the floor's authored
``JoistReinforcement`` plies, clipped by ``extent``, are the beam. This module finds those
plies on the wall's line and reports an ERROR when none covers the opening: a wall told its
header is in the band, with nothing in the band, carries the floor above on a nailer.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.findings import Finding, failed

_IN = 0.0254
#: The least seat a ply needs past each rough-opening edge — one 1 1/2" jack.
MIN_BEARING_M = 1.5 * _IN
#: How far outboard of a rough-opening edge a jamb-pack member is looked for.
_PACK_REACH_M = 12 * _IN
_PACK_KINDS = ("jack", "king")


@dataclass(frozen=True)
class BandHeader:
    door: str
    wall: str
    floor: str
    plies: tuple  # the floor's sister_joist FramedMembers over the opening
    #: Stations along the host wall's axis (m from its start node).
    ro_lo: float
    ro_hi: float
    pack_lo: float
    pack_hi: float


def _frame(axis):
    (x0, y0), (x1, y1) = axis
    dx, dy = x1 - x0, y1 - y0
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / length, dy / length

    def along(p):
        return (p[0] - x0) * ux + (p[1] - y0) * uy

    def across(p):
        return (p[1] - y0) * ux - (p[0] - x0) * uy

    return (ux, uy), along, across


def _pack(wall, along, edge: float, sign: int) -> float:
    """The outer face of the jamb pack on one side of a rough-opening edge."""
    faces = [along(m.p0) + sign * 0.75 * _IN for m in wall.members
             if m.category in _PACK_KINDS
             and 0.0 < sign * (along(m.p0) - edge) <= _PACK_REACH_M]
    return (max(faces) if sign > 0 else min(faces)) if faces else edge


def band_header(model, door_tag: str) -> BandHeader | str:
    """The band header over ``door_tag``, or why there is none."""
    door = model.plan.by_tag(door_tag)
    floor_tag = getattr(door, "header_in_band", None)
    opening = next((o for o in model.openings if o.tag == door_tag), None)
    wall = model.wall(getattr(door, "host", None) or "")
    if not floor_tag or opening is None or wall is None:
        return f"{door_tag} has no resolved opening on a resolved wall"
    floor = next((f for f in model.floors if f.tag == floor_tag), None)
    if floor is None:
        return f"{floor_tag} did not resolve a joist field"
    (ux, uy), along, across = _frame(wall.axis)
    ro_lo = opening.center_along_m - opening.width_m / 2.0
    ro_hi = opening.center_along_m + opening.width_m / 2.0
    offsets = [across(p) for layer in wall.layers for p in layer.polygon]
    band = (min(offsets), max(offsets)) if offsets else (0.0, 0.0)
    plies = []
    for member in floor.members:
        if member.category != "sister_joist":
            continue
        dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
        length = (dx * dx + dy * dy) ** 0.5
        if length <= 0 or abs(dx * ux + dy * uy) / length < 0.999:
            continue  # not parallel to the wall
        if not band[0] - 1e-6 <= across(member.p0) <= band[1] + 1e-6:
            continue  # not over the wall
        lo, hi = sorted((along(member.p0), along(member.p1)))
        if lo <= ro_lo - MIN_BEARING_M + 1e-6 and hi >= ro_hi + MIN_BEARING_M - 1e-6:
            plies.append(member)
    if not plies:
        return (f"{floor_tag} has no reinforcement ply on {wall.tag}'s line reaching "
                f"{MIN_BEARING_M / _IN:.1f}\" past both jambs of {door_tag}")
    return BandHeader(door_tag, wall.tag, floor_tag, tuple(plies), ro_lo, ro_hi,
                      _pack(wall, along, ro_lo, -1), _pack(wall, along, ro_hi, +1))


def band_header_doors(plan) -> list:
    return [e for e in plan.all_elements() if getattr(e, "header_in_band", None)]


def band_header_findings(model) -> list[Finding]:
    out: list[Finding] = []
    for door in band_header_doors(model.plan):
        found = band_header(model, door.tag)
        if isinstance(found, str):
            out.append(failed(
                "integrity.header_in_band",
                f"{door.tag} names {door.header_in_band}'s band as its header, but {found}; "
                "its wall frames no header there", (door.tag, door.header_in_band),
                fix=("author a JoistReinforcement on that floor's line with an extent "
                     "covering both jamb packs, or drop header_in_band")))
    return out

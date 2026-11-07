"""``mep.door_transfer_air`` — the air a closed door must pass, at its realized undercut.

A zone (rooms joined by cased openings) whose terminals do not balance moves its net air
through its doors. A leaf with no bottom seal passes it under its undercut
(``resolve/door_undercut``), a sharp-edged slot: Q = 1.07 A sqrt(dP), cfm, in^2 and Pa
(Building America / ACCA), so dP = (Q / 1.07 A)^2 against
``MepPreferences.door_transfer_max_pa``. The zone a stair reaches is the house, at neutral
pressure; a zone with one door is a dead end that door alone serves (a bath, a closet). Air
that must cross another closed zone is a network this check does not solve: UNKNOWN. The
hand-worked basis is ``houses/catlin/notes/system1_return_path.md``. ADVISORY: 3 Pa is
Manual D's line, not code.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable, passed, unknown
from typehaus.model.enums import DoorOperation
from typehaus.resolve.door_product_spec import house_trim_standard
from typehaus.resolve.door_undercut import realized_undercut
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring, opening_rooms

_CID = "mep.door_transfer_air"
_IN = 0.0254
#: cfm per in^2 of slot per sqrt(Pa): the sharp-edged orifice the hand note uses.
_SLOT_CFM_PER_IN2_ROOT_PA = 1.07
#: Below this net flow a zone's imbalance is rounding, not air that has to move.
_MIN_NET_CFM = 1.0
_STAIR_TOUCH_M = 0.05
_SIGN = {"supply": 1.0, "return": -1.0, "exhaust": -1.0, "dryer": -1.0}
_TRACK = (DoorOperation.SLIDE, DoorOperation.BIFOLD)


def _pressure_pa(cfm: float, area_in2: float) -> float:
    return (cfm / (_SLOT_CFM_PER_IN2_ROOT_PA * area_in2)) ** 2 if area_in2 > 0 else float("inf")


class _Zones:
    """Rooms joined by open paths, each with its net cfm, unrated terminals and doors."""

    def __init__(self, ctx: CheckContext):
        model = ctx.model
        types = {t.tag: t for t in model.plan.library.door_types}
        self.parent = {r.tag: r.tag for r in model.rooms}
        self.doors: list[tuple[str, str, object, object]] = []
        for opening in model.openings:
            if opening.kind == "window" or opening.is_blind or opening.penetration_for:
                continue
            a, b = (r.tag if r is not None else None for r in opening_rooms(model, opening))
            door_type = types.get(opening.type_ref or "")
            if a is None or b is None or a == b or (door_type is not None and door_type.exterior):
                continue
            if not opening.is_door or door_type is None:
                self.parent[self.find(a)] = self.find(b)
            else:
                self.doors.append((a, b, opening, door_type))
        self.net: dict[str, float] = {}
        self.transfers: dict[str, list[str]] = {}
        self.unrated: dict[str, list[str]] = {}
        self._flows(ctx)
        self.house = {self.find(r.tag) for r in model.rooms if _touches_stair(model, r)}

    def find(self, room: str) -> str:
        while self.parent[room] != room:
            room = self.parent[room]
        return room

    def _flows(self, ctx: CheckContext) -> None:
        rooms = ctx.model.rooms
        for storey in ctx.model.plan.storeys:
            for element in ctx.model.plan.storey_elements(storey.tag):
                if element.element_kind != "Register":
                    continue
                room = element.room
                if room is None:
                    point = Point(placed_xy(ctx.model, element))
                    room = next((r.tag for r in rooms if r.storey == storey.tag
                                 and len(axis_ring(r)) >= 3
                                 and axis_polygon(r).contains(point)), None)
                if room is None or room not in self.parent:
                    continue  # ventilation_distribution reports a register in no room
                zone = self.find(room)
                kind = element.kind.value
                if kind == "transfer":
                    self.transfers.setdefault(zone, []).append(element.tag)
                elif element.design_cfm is None:
                    self.unrated.setdefault(zone, []).append(element.tag)
                else:
                    cfm = _SIGN.get(kind, 0.0) * element.design_cfm
                    self.net[zone] = self.net.get(zone, 0.0) + cfm

    def edges(self, zone: str):
        """``(far zone, opening, door type)`` for each door out of ``zone``."""
        for a, b, opening, door_type in self.doors:
            za, zb = self.find(a), self.find(b)
            if za != zb and zone in (za, zb):
                yield (zb if za == zone else za), opening, door_type


def _touches_stair(model, room) -> bool:
    if len(axis_ring(room)) < 3:
        return False
    face = axis_polygon(room).buffer(_STAIR_TOUCH_M)
    return any(room.storey in (s.storey, s.to_storey) and len(s.outline) >= 3
               and face.intersects(Polygon(s.outline)) for s in model.stairs)


def _slot(opening, door_type):
    """``(area in2, term)``, or None where the gap is not known."""
    gap = realized_undercut(opening)
    if gap is None or door_type.operation in _TRACK:
        return None
    width = opening.sizing.leaf_w_m if opening.sizing is not None else opening.width_m
    area = (width / _IN) * (gap.higher_m / _IN)
    return area, f'{opening.tag} {width / _IN:.1f}" x {gap.higher_m / _IN:.2f}" = {area:.1f} in2'


def _grade(zones: _Zones, zone: str, members: list[str], limit: float,
           widest_m: float | None) -> Finding:
    tags = tuple(members)
    name = "+".join(members)
    if zones.unrated.get(zone):
        return unknown(_CID, f"{name}: {', '.join(zones.unrated[zone])} state no design_cfm", tags)
    net = zones.net.get(zone, 0.0)
    if zone in zones.house:
        return passed(_CID, f"{name} nets {net:.0f} cfm, open to the house at its stair", tags)
    edges = list(zones.edges(zone))
    if not edges:
        return unknown(_CID, f"{name} nets {net:.0f} cfm and has no door the model can see; "
                             "a path through a stair well or floor opening is not traced", tags)
    relief, chained, folded = [], [], []
    for far, opening, door_type in edges:
        dead_end = far not in zones.house and len(list(zones.edges(far))) == 1
        if len(edges) == 1 or far in zones.house:
            relief.append((opening, door_type))
        elif dead_end:
            if not door_type.bottom_seal:
                net += zones.net.get(far, 0.0)  # it draws its air through this zone
            folded.append(far)
        else:
            chained.append(far)
    tags += tuple(o.tag for _f, o, _t in edges)
    flow = f"{name} nets {abs(net):.0f} cfm {'out' if net > 0 else 'in'}" + (
        f" (with {', '.join(folded)})" if folded else "")
    if abs(net) < _MIN_NET_CFM:
        return passed(_CID, f"{flow}: balanced", tags)
    area, terms, gaps, widths = 0.0, [], [], 0.0
    for opening, door_type in relief:
        if door_type.bottom_seal:
            terms.append(f"{opening.tag} sealed")
            continue
        slot = _slot(opening, door_type)
        if slot is None:
            gaps.append(opening.tag)
            continue
        area += slot[0]
        terms.append(slot[1])
        widths += slot[0] / (realized_undercut(opening).higher_m / _IN)
    pressure = _pressure_pa(abs(net), area)
    held = (f"{flow} under {'; '.join(terms)}: {pressure:.1f} Pa" if area > 0
            else f"{flow} with no open undercut to the house ({'; '.join(terms) or 'no door'})")
    if pressure <= limit and not chained:
        return passed(_CID, f"{held}, within {limit:g} Pa", tags)
    others = zones.transfers.get(zone, []) + gaps
    if others or chained:
        what = ([f"{', '.join(others)} add area the model does not rate"] if others else []) + (
            [f"air also crosses {', '.join(chained)}, a network this check does not solve"]
            if chained else [])
        return unknown(_CID, f"{held}; {'; '.join(what)}", tags)
    need = abs(net) / (_SLOT_CFM_PER_IN2_ROOT_PA * limit ** 0.5)
    at_max = ""
    if widest_m is not None and widths > 0:
        best = widths * widest_m / _IN
        at_max = (f"; at the house's {widest_m / _IN:.2f}\" maximum undercut {best:.1f} in2 "
                  f"holds {_pressure_pa(abs(net), best):.1f} Pa")
    return advisory(_CID, f"ADVISORY — {held}, over {limit:g} Pa; it needs {need:.0f} in2 of "
                          f"free area{at_max}", tags, Result.ADVISORY,
                    fix="add a transfer grille or jump duct, or a return in the room")


@check(Tier.ADVISORY, _CID)
def door_transfer_air(ctx: CheckContext) -> list[Finding]:
    """Each zone whose terminals do not balance, graded at its doors' realized undercuts."""
    zones = _Zones(ctx)
    members: dict[str, list[str]] = {}
    for room in sorted(zones.parent):
        members.setdefault(zones.find(room), []).append(room)
    graded = sorted(z for z in members
                    if abs(zones.net.get(z, 0.0)) >= _MIN_NET_CFM or zones.unrated.get(z))
    if not graded:
        return [not_applicable(_CID, "no zone's terminals leave air to move through a door")]
    rule = getattr(house_trim_standard(ctx.model.plan), "door_undercut", None)
    widest = rule.maximum.meters if rule is not None else None
    limit = ctx.preferences.mep.door_transfer_max_pa
    return [_grade(zones, zone, members[zone], limit, widest) for zone in graded]

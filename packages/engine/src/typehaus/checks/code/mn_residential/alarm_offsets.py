"""R314.3.3 / R314.3.4 and NFPA 72 — how far a smoke alarm keeps off what nuisance-trips it.

Horizontal plan distances from each smoke or combo head (``resolve.alarms.alarm_xy``) to:

* the door of a room holding a tub or shower, 3 ft (2018 IRC R314.3.4);
* a ceiling fan's blade tip, 3 ft, and a supply register, 3 ft (NFPA 72 §29.11.3.4, which
  R314.1 adopts for installation — its item numbers move between editions, so the clause is
  cited whole);
* a permanently installed cooking appliance (``ApplianceType.cooking``): photoelectric 6 ft,
  ionization 20 ft, 10 ft with a silence switch (R314.3.3). ``Alarm`` carries no sensor
  technology, so 6-20 ft is UNKNOWN until one is stated.

Every limit yields where it "would prevent placement" R314.3 requires; that exception is the
fix hint, not a pass. Only hazards on the alarm's own storey are measured. A door is a typed
opening on the bath's boundary (``room_doors``), measured to its width along the wall. A fan
or register counts only along a path that crosses no wall body: a grille in the bedroom
behind a hall alarm is 2 ft away in plan and nowhere near it in air.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import AlarmKind, DuctSystem, LuminaireForm
from typehaus.resolve.alarms import alarm_xy
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.overlay import union_all
from typehaus.resolve.room_openings import room_doors

_CID = "code.R314_alarm_offsets"
_FT = 0.3048
_THREE_FT, _PHOTO_FT, _ION_FT = 3.0, 6.0, 20.0
_SMOKE = (AlarmKind.SMOKE, AlarmKind.COMBO)
_BATHING_SYMBOLS = {"tub", "tub-shower", "shower", "shower-neo-angle",
                    "kohler-underscore-6032", "kohler-underscore-6036"}
_EXCEPTION = ("Move the head, or record that this is the only spot R314.3 leaves for it — "
              "each limit yields where it would prevent required placement.")


def _door_segment(model, opening):
    wall = model.wall(opening.host_wall)
    centre = None if wall is None else opening_center(wall, opening)
    if centre is None:
        return None
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / run, (y1 - y0) / run
    half = opening.width_m / 2.0
    return LineString([(centre[0] - ux * half, centre[1] - uy * half),
                       (centre[0] + ux * half, centre[1] + uy * half)])


def _walls(model, storey: str):
    rings = [Polygon(layer.polygon) for wall in model.walls if wall.storey == storey
             for layer in wall.layers if len(layer.polygon) >= 3]
    return union_all(rings) if rings else None


def _reach(head: Point, geom, walls, through_walls: bool) -> float | None:
    """Plan distance from ``head`` to ``geom``; ``None`` when only a wall separates them."""
    dist = head.distance(geom)
    if through_walls or walls is None or dist <= 0.02:
        return dist
    a, b = nearest_points(head, geom)
    path = LineString([a, b])
    path = LineString([path.interpolate(0.01), path.interpolate(path.length - 0.01)])
    return None if path.intersects(walls) else dist


def _three_ft_hazards(ctx: CheckContext, storey: str) -> list[tuple[str, str, object, bool]]:
    """``(tag, what, plan geometry, measured through walls)`` for every 3 ft hazard."""
    model, plan = ctx.model, ctx.plan
    fixture_types = {t.tag: t for t in plan.library.fixture_types}
    device_types = {t.tag: t for t in plan.library.electrical_device_types}
    bodies = {o.tag: o for o in model.canvas_objects}
    elements = plan.storey_elements(storey)
    out: list[tuple[str, str, object, bool]] = []
    wet = {e.room for e in elements if e.element_kind == "Fixture" and e.room
           and getattr(fixture_types.get(e.type_ref), "plan_symbol", None) in _BATHING_SYMBOLS}
    for room in model.rooms:
        if room.tag in wet and room.storey == storey:
            for door in room_doors(model, room):
                segment = _door_segment(model, door)
                if segment is not None:
                    out.append((door.tag, f"the door of {room.tag} (tub/shower)", segment,
                                True))
    for e in elements:
        body = bodies.get(e.tag)
        if body is None:
            continue
        if e.element_kind == "ElectricalDevice":
            product = device_types.get(e.type_ref or "")
            if getattr(product, "form", None) is LuminaireForm.CEILING_FAN_LIGHT:
                radius = max(product.footprint[0].meters, product.footprint[1].meters) / 2
                out.append((e.tag, "a ceiling fan's blade tip",
                            Point(body.position).buffer(radius), False))
        elif e.element_kind == "Register" and e.kind is DuctSystem.SUPPLY:
            if len(body.footprint) >= 3:
                out.append((e.tag, "a supply register", Polygon(body.footprint), False))
    return out


def _cooking(ctx: CheckContext, storey: str) -> list[tuple[str, object]]:
    types = {t.tag: t for t in ctx.plan.library.appliance_types}
    bodies = {o.tag: o for o in ctx.model.canvas_objects}
    out = []
    for e in ctx.plan.storey_elements(storey):
        body = bodies.get(e.tag)
        if (e.element_kind == "Appliance" and body is not None and len(body.footprint) >= 3
                and getattr(types.get(e.type_ref or ""), "cooking", False)):
            out.append((e.tag, Polygon(body.footprint)))
    return out


@check(Tier.CODE, _CID)
def alarm_offsets(ctx: CheckContext) -> list[Finding]:
    """Each smoke head 3 ft off a bath door, fan blade and supply register; 6-20 ft off a range."""
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        elements = ctx.plan.storey_elements(storey.tag)
        rooms = {e.tag: e for e in elements if e.element_kind == "Room"}
        alarms = [e for e in elements if e.element_kind == "Alarm" and e.kind in _SMOKE]
        if not alarms:
            continue
        hazards = _three_ft_hazards(ctx, storey.tag)
        walls = _walls(ctx.model, storey.tag)
        cooking = _cooking(ctx, storey.tag)
        for alarm in alarms:
            xy = alarm_xy(alarm, rooms.get(alarm.room or ""))
            if xy is None:
                out.append(unknown(_CID, f"{alarm.tag}: no position and no hosting room to "
                                   "measure from", (alarm.tag,), code="R314.3"))
                continue
            head = Point(xy)
            reaches = ((_reach(head, geom, walls, through), tag, what)
                       for tag, what, geom, through in hazards)
            close = sorted((d / _FT, tag, what) for d, tag, what in reaches
                           if d is not None and d / _FT < _THREE_FT - 1e-6)
            for dist, tag, what in close:
                out.append(failed(_CID, f"{alarm.tag} is {dist:.1f} ft from {what} ({tag}); "
                                  "3 ft minimum", (alarm.tag, tag), code="R314.3.4",
                                  fix=_EXCEPTION))
            ranges = sorted((head.distance(geom) / _FT, tag) for tag, geom in cooking)
            near = ranges[0] if ranges else None
            if near is not None and near[0] < _PHOTO_FT:
                out.append(failed(_CID, f"{alarm.tag} is {near[0]:.1f} ft from cooking "
                                  f"appliance {near[1]}; 6 ft minimum even for a "
                                  "photoelectric head", (alarm.tag, near[1]),
                                  code="R314.3.3", fix=_EXCEPTION))
            elif near is not None and near[0] < _ION_FT:
                out.append(unknown(_CID, f"{alarm.tag} is {near[0]:.1f} ft from cooking "
                                   f"appliance {near[1]}: a photoelectric head passes, an "
                                   "ionization head needs 20 ft (10 ft with a silence "
                                   "switch), and the alarm states neither",
                                   (alarm.tag, near[1]), code="R314.3.3",
                                   fix="State a photoelectric head, or move it 20 ft off."))
            elif not close:
                out.append(passed(_CID, f"{alarm.tag} clears bath doors, fan blades and "
                                  "supply registers by 3 ft and any cooking appliance by "
                                  "20 ft", (alarm.tag,), code="R314.3.3"))
    return out

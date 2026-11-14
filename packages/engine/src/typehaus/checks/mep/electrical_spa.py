"""2026 NEC Article 680 Part IV — spas and hot tubs (680.40-680.44), graded from the model.

Graded: 680.44(A) GFCI on every spa circuit (a circuit flagged ``Circuit.spa`` or named by an
``EquipmentKind.SPA``); 680.41(A) (N/A in a one-family dwelling); and, for a modeled spa body,
680.41(B) line-voltage equipment 5 ft off (a self-contained unit is excepted) and indoors
680.43(A)/(C) receptacle and switch distances. Distance is plan distance from the body outline
to the device, which is at most the cord path: a wall between them leaves a near device UNKNOWN
rather than FAIL. Not graded, and said so in every finding that needs it: the spa body when it
is not modeled; outdoors, Part I/II (680.12 disconnect, 680.21/.22, 680.26 bonding), whose
pages are unread; 680.43(B) luminaires, (D)-(F) bonding; 680.44(B)/(C) (no field).
Part V fountains, 680.34/.35 and 680.45 pools: the model has no such element, so absence is
not evidence and they emit nothing. ``docs/nec-2026-paraphrase-680.md``.
"""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind, EquipmentKind
from typehaus.model.nec import NEC, cite
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID = "code.NEC_680_spa"
_FT = 0.3048
_SWITCH_M, _EQUIPMENT_M = 5 * _FT, 5 * _FT
_RECEPTACLE_MIN_M, _RECEPTACLE_MAX_M = 6 * _FT, 10 * _FT
_RECEPTACLE_KINDS = frozenset({DeviceKind.RECEPTACLE, DeviceKind.RECEPTACLE_GFCI})
# Line-voltage equipment boxes 680.41(B) separates (receptacles, switches and luminaires have
# their own rules; a disconnect and a panel are "equipment exceeding the low-voltage limit").
_EQUIPMENT_KINDS = frozenset({DeviceKind.DISCONNECT, DeviceKind.PANEL,
                              DeviceKind.JUNCTION_BOX, DeviceKind.METER})
_PART_I_II_UNREAD = ("Part I/II (680.12 disconnect within sight and 5 ft away, 680.21/.22, "
                     "680.26 equipotential bonding) is not yet read in print and is ungraded")


def _spa_circuits(ctx: CheckContext, spas: list) -> dict[str, object]:
    named = {s.circuit for s in spas if s.circuit}
    return {c.tag: c for c in ctx.plan.library.circuits if c.spa or c.tag in named}


def _is_indoors(ctx: CheckContext, obj) -> bool:
    from shapely.geometry import Polygon

    centre = Polygon(obj.footprint).centroid
    return any(room.storey == obj.storey and axis_polygon(room).contains(centre)
               for room in ctx.model.rooms if len(axis_ring(room)) >= 3)


def _walls(ctx: CheckContext, storey: str) -> list:
    from shapely.geometry import LineString

    return [LineString(w.axis).buffer(w.thickness_m / 2.0, cap_style=2)
            for w in ctx.model.walls if w.storey == storey and len(w.axis) >= 2]


def _separated(body, point, walls: list) -> bool:
    """A wall band lies across the straight line from the body to ``point``. Ends are trimmed
    by 0.2 m so the wall a device is mounted on, or a tub's own surround, is not a barrier."""
    from shapely.geometry import LineString
    from shapely.ops import nearest_points

    a, b = nearest_points(body, point)
    line = LineString([a, b])
    if line.length <= 0.4:
        return False
    core = LineString([line.interpolate(0.2), line.interpolate(line.length - 0.2)])
    return any(core.intersects(w) for w in walls)


def _plan_distance(body, obj) -> float:
    from shapely.geometry import Point, Polygon

    point = Point(obj.position) if not obj.footprint else Polygon(obj.footprint).centroid
    return body.distance(point)


def _line_voltage_tags(ctx: CheckContext, spa_tags: set[str]) -> set[str]:
    out = {e.tag for e in ctx.plan.all_elements()
           if e.element_kind == "ElectricalDevice" and e.kind in _EQUIPMENT_KINDS}
    out |= {e.tag for e in ctx.plan.all_elements()
            if e.element_kind == "Equipment" and e.circuit and e.tag not in spa_tags}
    return out


def _geometry(ctx: CheckContext, spa, obj, circuits: dict, types: dict,
              indoors: bool) -> list[Finding]:
    from shapely.geometry import Point, Polygon

    body = Polygon(obj.footprint)
    walls = _walls(ctx, obj.storey)
    spa_tags = {s.tag for s in ctx.plan.all_elements()
                if s.element_kind == "Equipment" and s.kind is EquipmentKind.SPA}
    product = types.get(spa.type_ref or "")
    self_contained = getattr(product, "spa_self_contained", None)
    elements = {e.tag: e for e in ctx.plan.all_elements()
                if e.element_kind in ("ElectricalDevice", "Equipment")}
    here = [o for o in ctx.model.canvas_objects
            if o.storey == obj.storey and o.tag in elements and o.tag != spa.tag]
    out: list[Finding] = []

    # 680.41(B): equipment above the low-voltage contact limit stays 5 ft off, or is walled off.
    code_b = cite(NEC.SPA_EQUIPMENT_DISTANCE)
    equipment = _line_voltage_tags(ctx, spa_tags)
    for other in sorted(here, key=lambda o: o.tag):
        if other.tag not in equipment:
            continue
        gap = _plan_distance(body, other)
        if gap >= _EQUIPMENT_M:
            continue
        point = Point(other.position)
        if self_contained:
            out.append(by_result(_CID, Result.PASS, f"{other.tag} is {gap / _FT:.1f} ft from "
                                 f"{spa.tag}, excepted: a self-contained spa",
                                 (other.tag,), code_b))
        elif _separated(body, point, walls):
            out.append(by_result(_CID, Result.PASS, f"{other.tag} is {gap / _FT:.1f} ft from "
                                 f"{spa.tag} with a wall between", (other.tag,), code_b))
        else:
            verdict = Result.UNKNOWN if self_contained is None else Result.FAIL
            note = ("; FAILS unless the spa is a listed self-contained unit "
                    "(EquipmentType.spa_self_contained is not stated)" if self_contained is None
                    else "")
            out.append(by_result(_CID, verdict, f"{other.tag} is {gap / _FT:.1f} ft from "
                                 f"{spa.tag}, under 5 ft with no barrier{note}",
                                 (other.tag, spa.tag), code_b,
                                 "move it 5 ft off, or put a solid wall or fence between"))
    if not indoors:
        out.append(by_result(_CID, Result.UNKNOWN,
                             f"{spa.tag} stands outdoors: 680.42 sends it to "
                             f"{_PART_I_II_UNREAD}; the 680.42(B) perimeter-bonding waiver "
                             "also needs its four conditions stated (above grade, rim 28 in. "
                             "over perimeter surfaces)", (spa.tag,), cite(NEC.SPA_OUTDOOR)))
        return out
    return out + _indoor(ctx, spa, body, here, elements, circuits, walls)


def _indoor(ctx: CheckContext, spa, body, here: list, elements: dict, circuits: dict,
            walls: list) -> list[Finding]:
    from shapely.geometry import Point

    code_a, code_c = cite(NEC.SPA_INDOOR_RECEPTACLES), cite(NEC.SPA_INDOOR_SWITCHES)
    out: list[Finding] = []
    qualifying: list[str] = []
    for other in sorted(here, key=lambda o: o.tag):
        device = elements[other.tag]
        if getattr(device, "element_kind", "") != "ElectricalDevice":
            continue
        gap = _plan_distance(body, other)
        barrier = _separated(body, Point(other.position), walls)
        if device.kind is DeviceKind.SWITCH and gap < _SWITCH_M:
            result = Result.UNKNOWN if barrier else Result.FAIL
            out.append(by_result(_CID, result, f"switch {device.tag} is {gap / _FT:.1f} ft from "
                                 f"{spa.tag}, under 5 ft" + ("; a wall lies between, so the "
                                 "measured path is not computed" if barrier else ""),
                                 (device.tag,), code_c, "move it 5 ft off"))
        if device.kind not in _RECEPTACLE_KINDS:
            continue
        circuit = circuits.get(device.circuit or "")
        gfci = device.kind is DeviceKind.RECEPTACLE_GFCI or bool(
            getattr(_circuit(ctx, device.circuit), "gfci", False))
        if circuit is not None and not gfci:  # (A)(3): a spa supply receptacle is GFCI
            out.append(by_result(_CID, Result.FAIL, f"receptacle {device.tag} supplies "
                                 f"{spa.tag} with no GFCI", (device.tag,),
                                 cite(NEC.SPA_INDOOR_RECEPTACLES + "(3)")))
        if gap < _RECEPTACLE_MIN_M:
            result = Result.UNKNOWN if barrier else Result.FAIL
            out.append(by_result(_CID, result, f"receptacle {device.tag} is {gap / _FT:.1f} ft "
                                 f"from {spa.tag}, under 6 ft" + ("; a wall lies between, so "
                                 "the cord path is not computed" if barrier else ""),
                                 (device.tag,), cite(NEC.SPA_INDOOR_RECEPTACLES + "(1)"),
                                 "move it 6 ft off"))
        elif gap <= _RECEPTACLE_MAX_M and not barrier and circuit is None:
            qualifying.append(device.tag)
        if gap <= _RECEPTACLE_MAX_M and not gfci:
            out.append(by_result(_CID, Result.FAIL, f"receptacle {device.tag} is within 10 ft "
                                 f"of {spa.tag} with no GFCI or SPGFCI", (device.tag,), code_a,
                                 "GFCI breaker or device"))
    if qualifying:
        out.append(by_result(_CID, Result.PASS, f"{spa.tag}: general-purpose receptacle "
                             f"{', '.join(qualifying)} within 6-10 ft", tuple(qualifying), code_a))
    else:
        out.append(by_result(_CID, Result.FAIL, f"{spa.tag}: no 125 V general-purpose receptacle "
                             "lies 6-10 ft from it in plan with an open path", (spa.tag,), code_a,
                             "add a GFCI receptacle 6-10 ft away"))
    return out


def _circuit(ctx: CheckContext, tag: str | None):
    return next((c for c in ctx.plan.library.circuits if c.tag == tag), None)


@check(Tier.CODE, _CID)
def spa_and_hot_tub(ctx: CheckContext) -> list[Finding]:
    """680.44 GFCI on a spa circuit; 680.41(A); the spa body's distances where it is modeled."""
    spas = [e for e in ctx.plan.all_elements()
            if e.element_kind == "Equipment" and e.kind is EquipmentKind.SPA]
    circuits = _spa_circuits(ctx, spas)
    if not spas and not circuits:
        return []  # the model has no pool or fountain element, so silence is not N/A
    out: list[Finding] = []
    code_gfci = cite(NEC.SPA_GFCI)
    for circuit in sorted(circuits.values(), key=lambda c: c.tag):
        if circuit.gfci:
            kind = "Class C SPGFCI" if circuit.gfci_class == "C" else "GFCI"
            out.append(by_result(_CID, Result.PASS, f"{circuit.tag} (spa) is on a {kind} breaker",
                                 (circuit.tag,), code_gfci))
        else:
            out.append(by_result(_CID, Result.FAIL, f"{circuit.tag} supplies a spa with no "
                                 "GFCI or SPGFCI", (circuit.tag,), code_gfci,
                                 "GFCI breaker, or a listed unit marked with integral GFCI "
                                 "(680.44(B), which the model cannot state)"))
    dwellings = [b for b in ctx.plan.project.buildings if b.kind == "dwelling"]
    one_dwelling = len(dwellings) == 1
    out.append(by_result(
        _CID, Result.NOT_APPLICABLE if one_dwelling else Result.UNKNOWN,
        "680.41(A) emergency switch reaches other than one-family dwellings; this plan has one "
        "dwelling building" if one_dwelling else
        "680.41(A) emergency switch: the plan does not state a one-family dwelling",
        (), cite(NEC.SPA_EMERGENCY_SWITCH)))
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    placed = {o.tag: o for o in ctx.model.canvas_objects}
    if not spas:
        out.append(by_result(
            _CID, Result.UNKNOWN,
            f"{', '.join(sorted(circuits))} supplies a spa that is not modeled, so 680.41(B) "
            "separation, indoor vs outdoor (680.42/.43) and receptacle and switch distances are "
            f"ungraded; if it is outdoors, {_PART_I_II_UNREAD} too", tuple(circuits),
            cite(NEC.SPA_EQUIPMENT_DISTANCE),
            "model it as an Equipment of kind SPA with its footprint"))
    for spa in spas:
        obj = placed.get(spa.tag)
        if obj is None or len(obj.footprint or ()) < 3:
            out.append(by_result(_CID, Result.UNKNOWN, f"{spa.tag} has no resolved footprint",
                                 (spa.tag,), cite(NEC.SPA_EQUIPMENT_DISTANCE)))
            continue
        out += _geometry(ctx, spa, obj, circuits, types, _is_indoors(ctx, obj))
    return out

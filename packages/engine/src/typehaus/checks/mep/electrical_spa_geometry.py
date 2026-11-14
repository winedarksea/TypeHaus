"""NEC 680 spa distances graded off a modeled ``EquipmentKind.SPA`` footprint.

680.13, 680.22, 680.41 and 680.43.

Distance is plan distance from the footprint outline (the outer edge, so a near-miss reads
conservatively) to the device. It is at most the cord path or the water's-edge path the code
measures, so a wall between them leaves a near device UNKNOWN, never FAIL. Indoors 680.43(A)
and (C) replace 680.22(A) and (C); everything else applies in both. Luminaire heights are read
as mount elevation (an upper bound on the clearance over the water), so only a low luminaire
can FAIL. Not graded here: 680.43(B) indoor luminaires, listed-for-use switches, "within sight".
"""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_CID = "code.NEC_680_spa"
_FT = 0.3048
_5FT, _6FT, _10FT, _20FT = 5 * _FT, 6 * _FT, 10 * _FT, 20 * _FT
_REQUIRED_RECEPTACLE_MAX_AFF_M = 6.5 * _FT  # 680.22(A)(1): 6 ft 6 in. above the serving surface
_OVER_WATER_M = 12 * _FT  # 680.22(B)(1)
_RECEPTACLES = frozenset({DeviceKind.RECEPTACLE, DeviceKind.RECEPTACLE_GFCI})
# Line-voltage boxes 680.41(B) / 680.22(F) separate; receptacles, switches and lights have
# rules of their own.
_EQUIPMENT = frozenset({DeviceKind.DISCONNECT, DeviceKind.PANEL, DeviceKind.JUNCTION_BOX,
                        DeviceKind.METER})


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


def _walls(ctx: CheckContext, storey: str) -> list:
    from shapely.geometry import LineString

    return [LineString(w.axis).buffer(w.thickness_m / 2.0, cap_style=2)
            for w in ctx.model.walls if w.storey == storey and len(w.axis) >= 2]


def _gfci(ctx: CheckContext, device) -> bool:
    circuit = next((c for c in ctx.plan.library.circuits if c.tag == device.circuit), None)
    return device.kind is DeviceKind.RECEPTACLE_GFCI or bool(getattr(circuit, "gfci", False))


def _elevation_m(device) -> float | None:
    elevation = getattr(getattr(device, "mount", None), "elevation", None)
    return None if elevation is None else elevation.meters


def spa_geometry(ctx: CheckContext, spa, obj, circuits: dict, types: dict,
                 indoors: bool) -> list[Finding]:
    from shapely.geometry import Point, Polygon

    body, walls = Polygon(obj.footprint), _walls(ctx, obj.storey)
    self_contained = getattr(types.get(spa.type_ref or ""), "spa_self_contained", None)
    elements = {e.tag: e for e in ctx.plan.all_elements()
                if e.element_kind in ("ElectricalDevice", "Equipment") and e.tag != spa.tag}
    near = []  # (element, plan gap m, wall between)
    for other in sorted(ctx.model.canvas_objects, key=lambda o: o.tag):
        if other.storey == obj.storey and other.tag in elements:
            point = Point(other.position)
            near.append((elements[other.tag], body.distance(point),
                         _separated(body, point, walls)))

    def ft(gap: float) -> str:
        return f"{gap / _FT:.1f} ft"

    def graded(limit: float, gap: float, barrier: bool) -> Result | None:
        """None when the limit is met; UNKNOWN when a wall hides the true path."""
        return None if gap >= limit else (Result.UNKNOWN if barrier else Result.FAIL)

    out: list[Finding] = []
    # 680.13: a maintenance disconnect on a spa circuit, 5 ft off, or a barrier giving a 5 ft reach.
    code_13 = cite(NEC.SPA_MAINT_DISCONNECT)
    for device, gap, barrier in near:
        if device.element_kind != "ElectricalDevice" or device.kind is not DeviceKind.DISCONNECT \
                or device.circuit not in circuits:
            continue
        result = graded(_5FT, gap, barrier)
        out.append(by_result(
            _CID, result or Result.PASS,
            f"{device.tag} (680.13 maintenance disconnect) is {ft(gap)} from {spa.tag}"
            + (", under 5 ft" if result else ", at least 5 ft; within-sight and accessibility "
               "are not graded")
            + ("; a wall lies between, and 680.13 needs a 5 ft reach path around it" if barrier
               and result else ""), (device.tag,), code_13, "move it 5 ft off" if result else None))
    # 680.41(B) / 680.22(F): other line-voltage equipment, 5 ft off or walled off.
    code_b = cite(NEC.SPA_EQUIPMENT_DISTANCE, NEC.POOL_OTHER_EQUIPMENT)
    for element, gap, barrier in near:
        if element.circuit in circuits:
            continue  # the spa's own supply: its disconnect is 680.13's, its receptacle (A)'s
        is_box = (element.kind in _EQUIPMENT if element.element_kind == "ElectricalDevice"
                  else bool(element.circuit))
        if not is_box or gap >= _5FT:
            continue
        if self_contained:
            out.append(by_result(_CID, Result.PASS, f"{element.tag} is {ft(gap)} from {spa.tag}"
                                 ", excepted: a self-contained spa", (element.tag,), code_b))
        elif barrier:
            out.append(by_result(_CID, Result.PASS, f"{element.tag} is {ft(gap)} from "
                                 f"{spa.tag} with a wall between", (element.tag,), code_b))
        else:
            note = ("; FAILS unless the spa is a listed self-contained unit "
                    "(EquipmentType.spa_self_contained is not stated)" if self_contained is None
                    else "")
            out.append(by_result(_CID, Result.UNKNOWN if self_contained is None else Result.FAIL,
                                 f"{element.tag} is {ft(gap)} from {spa.tag}, under 5 ft with no "
                                 f"barrier{note}", (element.tag, spa.tag), code_b,
                                 "move it 5 ft off, or put a solid wall or fence between"))
    out += _receptacles(ctx, spa, circuits, near, indoors)
    out += _switches_outlets_lights(ctx, spa, near, indoors, ft, graded)
    out.append(by_result(
        _CID, Result.UNKNOWN,
        f"{spa.tag} 680.26 equipotential bonding is ungraded: the model has no bonding grid, "
        "reinforcement, perimeter surface or fixed-metal data, and the 680.42(B) perimeter "
        "waiver needs its four conditions stated (listed self-contained for aboveground use, "
        "not indoor-only, on or above grade, rim 28 in. over perimeter surfaces within 30 in.)",
        (spa.tag,), cite(NEC.POOL_EQUIPOTENTIAL, NEC.SPA_BONDING_WAIVER)))
    return out


def _receptacles(ctx: CheckContext, spa, circuits: dict, near: list,
                 indoors: bool) -> list[Finding]:
    # Indoors 680.43(A) (6-10 ft, GFCI within 10 ft); outdoors Part II's 680.22(A) (6-20 ft).
    reach = _10FT if indoors else _20FT
    code = cite(NEC.SPA_INDOOR_RECEPTACLES if indoors else NEC.POOL_RECEPTACLES)
    required = cite(NEC.SPA_INDOOR_RECEPTACLES if indoors else NEC.POOL_RECEPTACLE_REQUIRED)
    out: list[Finding] = []
    qualifying: list[str] = []
    for device, gap, barrier in near:
        if device.element_kind != "ElectricalDevice" or device.kind not in _RECEPTACLES:
            continue
        on_spa = device.circuit in circuits
        gfci = _gfci(ctx, device)
        if on_spa and not gfci:  # a supply or circulation receptacle takes GFCI
            out.append(by_result(_CID, Result.FAIL, f"receptacle {device.tag} supplies "
                                 f"{spa.tag} with no GFCI", (device.tag,), code))
        if gap < _6FT:
            result = Result.UNKNOWN if barrier else Result.FAIL
            out.append(by_result(
                _CID, result, f"receptacle {device.tag} is {gap / _FT:.1f} ft from {spa.tag}, "
                "under 6 ft" + ("; a wall lies between, so the cord path is not computed"
                                if barrier else ""), (device.tag,), code, "move it 6 ft off"))
        elif gap <= reach and not barrier and not on_spa:
            elevation = _elevation_m(device)
            if indoors or (elevation is not None and elevation <= _REQUIRED_RECEPTACLE_MAX_AFF_M):
                qualifying.append(device.tag)
        if gap <= reach and not gfci:
            out.append(by_result(_CID, Result.FAIL, f"receptacle {device.tag} is within "
                                 f"{reach / _FT:.0f} ft of {spa.tag} with no GFCI or SPGFCI",
                                 (device.tag,), code, "GFCI breaker or device"))
    where = f"6-{reach / _FT:.0f} ft"
    if qualifying:
        out.append(by_result(_CID, Result.PASS, f"{spa.tag}: general-purpose receptacle "
                             f"{', '.join(qualifying)} within {where}"
                             + ("" if indoors else " and at most 6 ft 6 in. up (mount height "
                                "read as height above the serving surface)"),
                             tuple(qualifying), required))
    else:
        out.append(by_result(_CID, Result.FAIL, f"{spa.tag}: no 125 V general-purpose receptacle "
                             f"{where} away in plan with an open path"
                             + ("" if indoors else ", at most 6 ft 6 in. up"), (spa.tag,),
                             required, f"add a GFCI receptacle {where} away"))
    return out


def _switches_outlets_lights(ctx: CheckContext, spa, near: list, indoors: bool, ft,
                             graded) -> list[Finding]:
    code_sw = cite(NEC.SPA_INDOOR_SWITCHES if indoors else NEC.POOL_SWITCHES)
    out: list[Finding] = []
    for device, gap, barrier in near:
        if device.element_kind != "ElectricalDevice":
            continue
        if device.kind is DeviceKind.SWITCH and (result := graded(_5FT, gap, barrier)):
            out.append(by_result(
                _CID, result, f"switch {device.tag} is {ft(gap)} from {spa.tag}, under 5 ft; "
                "unless listed for use that close" + ("; a wall lies between and the code wants "
                "a 5 ft reach path around it" if barrier else ""), (device.tag,), code_sw,
                "move it 5 ft off"))
        elif device.kind is DeviceKind.DATA_OUTLET and (result := graded(_10FT, gap, barrier)):
            out.append(by_result(  # 680.22(E): other outlets 10 ft, cord-path measured
                _CID, result, f"outlet {device.tag} is {ft(gap)} from {spa.tag}, under 10 ft",
                (device.tag,), cite(NEC.POOL_OTHER_OUTLETS), "move it 10 ft off"))
        elif device.kind is DeviceKind.LIGHT and not indoors and gap < _10FT:
            out += _luminaire(ctx, spa, device, gap, ft)
    return out


def _luminaire(ctx: CheckContext, spa, device, gap: float, ft) -> list[Finding]:
    """680.22(B)(1)/(4): within 5 ft (or over) 12 ft above the water; 5-10 ft GFCI unless 5 ft
    up and rigidly attached. The water level is unstated, so a height can only fail."""
    code = cite(NEC.POOL_LUMINAIRES)
    elevation = _elevation_m(device)
    if gap < _5FT:
        low = elevation is not None and elevation < _OVER_WATER_M
        return [by_result(_CID, Result.FAIL if low else Result.UNKNOWN,
                          f"luminaire {device.tag} is {ft(gap)} from {spa.tag}: needs 12 ft over "
                          "the maximum water level; its mount height is "
                          + ("below that" if low else "not enough to grade (water level unstated)"),
                          (device.tag,), code)]
    if _gfci(ctx, device):
        return [by_result(_CID, Result.PASS, f"luminaire {device.tag} is {ft(gap)} from "
                          f"{spa.tag} on GFCI", (device.tag,), code)]
    low = elevation is not None and elevation < 5 * _FT
    return [by_result(_CID, Result.FAIL if low else Result.UNKNOWN,
                      f"luminaire {device.tag} is {ft(gap)} from {spa.tag} with no GFCI: it "
                      "needs to be 5 ft over the water and rigidly attached; "
                      + ("it is lower" if low else "water level and attachment are unstated"),
                      (device.tag,), code, "GFCI breaker for the lighting circuit")]

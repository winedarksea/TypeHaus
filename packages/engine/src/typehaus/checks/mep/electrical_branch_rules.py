"""CODE-tier 2026 NEC rules on what a panel and a bathroom circuit carry.

215.18(B) / 230.67(B) Ex.: an SPD in each panel holding branch breakers, read from
``Circuit.spd``. A panel with none is UNKNOWN, since an SPD in an adjacent enclosure is not
modeled. 210.11(C)(3): the circuit feeding a 210.52(D) receptacle is 120 V, 20 A and has no
other outlets, unless it serves one bathroom, where that bathroom's other outlets may share it.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle
from typehaus.checks.mep.electrical_code import _room_of, _wall_barrier
from typehaus.checks.mep.electrical_receptacles import (
    _BASIN_REACH_M,
    _basins,
    _disqualified,
    _enclosures,
    _floor_datums,
    _receptacles,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy
from typehaus.model.nec import NEC, cite
from typehaus.resolve.panel_space import panels
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring
from typehaus.takeoff.service_load import _circuit_consumers

_SPD_CID = "code.NEC_215_18_spd"
_BATH_CID = "code.NEC_210_11_C3_bathroom_circuit"


@check(Tier.CODE, _SPD_CID)
def panel_surge_protection(ctx: CheckContext) -> list[Finding]:
    """215.18(B) / 230.67(B) Ex. -- every panel holding branch breakers has its own SPD."""
    code = cite(NEC.FEEDER_SPD, NEC.SERVICE_SPD)
    panel_list = panels(ctx.plan)
    if not panel_list:
        return [by_result(_SPD_CID, Result.NOT_APPLICABLE, "no panel in the plan", (), code)]
    circuits = ctx.plan.library.circuits
    if not circuits:
        return [by_result(_SPD_CID, Result.UNKNOWN, "the plan states no circuits", (), code)]
    out: list[Finding] = []
    for panel in panel_list:
        held = [c for c in circuits if c.panel_ref == panel.tag]
        if all(c.spd or c.source for c in held):
            continue  # no branch breakers, so neither section reaches it
        spds = sorted(c.tag for c in held if c.spd)
        if spds:
            out.append(by_result(_SPD_CID, Result.PASS,
                                 f"{panel.tag} holds its SPD ({', '.join(spds)})", (), code))
        else:
            out.append(by_result(
                _SPD_CID, Result.UNKNOWN,
                f"{panel.tag} holds branch breakers and no circuit is marked spd=True; an "
                "SPD in an adjacent enclosure would satisfy this but is not modeled",
                (panel.tag,), code, f"set spd=True on the SPD circuit in {panel.tag}"))
    if not out:
        return [by_result(_SPD_CID, Result.NOT_APPLICABLE,
                          "no panel holds a branch breaker", (), code)]
    return out


@check(Tier.CODE, _BATH_CID)
def bathroom_receptacle_circuit(ctx: CheckContext) -> list[Finding]:
    """210.11(C)(3) -- the required bathroom receptacle's circuit, and what else is on it."""
    code = cite(NEC.BATHROOM_BRANCH)
    bathrooms = {room.tag: room for room in ctx.model.rooms
                 if room.occupancy == Occupancy.BATHROOM.value}
    basins, unclassified = _basins(ctx, bathrooms)
    if not basins:
        if unclassified:
            return [by_result(_BATH_CID, Result.UNKNOWN,
                              "a bathroom fixture is not classified as basin or not", (), code)]
        return [by_result(_BATH_CID, Result.NOT_APPLICABLE,
                          "no lavatory basin is modeled in any bathroom", (), code)]
    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append((room, axis_polygon(room)))
    by_tag = {room.tag: room for room in ctx.model.rooms}
    circuit_of: dict[str, Any] = {}
    storey_of: dict[str, str] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            storey_of[element.tag] = storey.tag
            if element.element_kind == "ElectricalDevice":
                circuit_of[element.tag] = getattr(element, "circuit", None)

    in_scope, out = _required_circuits(ctx, basins, rooms, by_tag, circuit_of, code)
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    consumers = _circuit_consumers(ctx.model)
    for tag in sorted(in_scope):
        circuit = circuits.get(tag)
        if circuit is None:
            continue  # electrical.circuit_refs reports a dangling reference
        out.append(_grade_circuit(ctx, circuit, consumers.get(tag, []), rooms, by_tag,
                                  storey_of, code))
    return out


def _required_circuits(ctx: CheckContext, basins: list, rooms: dict[str, list],
                       by_tag: dict[str, Any], circuit_of: dict[str, Any],
                       code: str) -> tuple[set[str], list[Finding]]:
    """Circuit tags carrying a receptacle that counts for a basin, and any untraceable one."""
    from shapely.geometry import Point, Polygon

    devices = _receptacles(ctx, rooms, by_tag)
    enclosures = _enclosures(ctx)
    floors = _floor_datums(ctx)
    barriers = _wall_barrier(ctx)
    in_scope: set[str] = set()
    out: list[Finding] = []
    for basin, basin_room in basins:
        carcass = Polygon(basin.footprint)
        for obj, room in devices:
            if obj.storey != basin.storey:
                continue
            if carcass.distance(Point(obj.position)) > _BASIN_REACH_M:
                continue
            if _disqualified(obj, room, basin_room, carcass, enclosures, floors,
                             barriers.get(obj.storey)) is not None:
                continue
            circuit = circuit_of.get(obj.tag)
            if circuit:
                in_scope.add(circuit)
            else:
                out.append(by_result(_BATH_CID, Result.UNKNOWN,
                                     f"{obj.tag} serves {basin.tag} and names no circuit",
                                     (obj.tag,), code, f"set circuit= on {obj.tag}"))
    return in_scope, out


def _grade_circuit(ctx: CheckContext, circuit: Any, consumers: list, rooms: dict[str, list],
                   by_tag: dict[str, Any], storey_of: dict[str, str], code: str) -> Finding:
    """One finding for one circuit: its rating first, then the outlets it carries."""
    from shapely.geometry import Point

    if circuit.poles != 1 or circuit.breaker_amps != 20:
        return by_result(_BATH_CID, Result.FAIL,
                         f"{circuit.tag} feeds a required bathroom receptacle and is "
                         f"{circuit.breaker_amps} A, {circuit.poles}-pole, not 120 V 20 A",
                         (circuit.tag,), code, f"make {circuit.tag} a 1-pole 20 A circuit")
    outside: list[str] = []
    other_equipment: list[str] = []
    served: set[str] = set()
    on_circuit = {element.tag for element in consumers}
    for element in consumers:
        if getattr(element, "plugs_into", None) in on_circuit:
            continue  # a cord-and-plug load in one of this circuit's receptacles
        xy = placed_xy(ctx.model, element)
        storey_rooms = rooms.get(storey_of.get(element.tag, ""), ())
        room = None if xy is None else _room_of(element, Point(xy), storey_rooms, by_tag)
        if room is None or room.occupancy != Occupancy.BATHROOM.value:
            outside.append(element.tag)
            continue
        served.add(room.tag)
        if not _is_receptacle_outlet(ctx, element):
            other_equipment.append(element.tag)
    if outside:
        return by_result(_BATH_CID, Result.FAIL,
                         f"{circuit.tag} feeds a required bathroom receptacle and also "
                         f"{', '.join(sorted(outside))} outside any bathroom",
                         (circuit.tag, *sorted(outside)), code,
                         f"move those outlets off {circuit.tag}")
    if other_equipment and len(served) > 1:
        return by_result(_BATH_CID, Result.FAIL,
                         f"{circuit.tag} serves {len(served)} bathrooms and also "
                         f"{', '.join(sorted(other_equipment))}; only a single-bathroom "
                         "circuit may carry other outlets",
                         (circuit.tag, *sorted(other_equipment)), code,
                         f"move those outlets off {circuit.tag}")
    return by_result(_BATH_CID, Result.PASS,
                     f"{circuit.tag} is 120 V 20 A serving {len(served)} bathroom(s)", (), code)


def _is_receptacle_outlet(ctx: CheckContext, element: Any) -> bool:
    return element.element_kind == "ElectricalDevice" and _counts_as_a_125v_receptacle(ctx, element)

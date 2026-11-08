"""2026 NEC 210.8(D) and (F) — GFCI by what an outlet feeds, not where it is.

Split from ``electrical_code.py`` (the 210.8(A) location rule) to keep both under the file
limit. (D) lists appliances whose outlet needs GFCI wherever it stands. The model names four
of them: an electric range or other cooking unit (``ApplianceType.cooking`` with a 240 V
need), a clothes dryer (the population text ``code.M1502_dryer_exhaust`` reads), a
dishwasher (the same, by name) and a sump pump (``Sump.pump``). An outlet is traced through
the circuit the item names, else to a receptacle within reach; one that cannot be traced is
UNKNOWN. Disposers and water heaters are not on the list the sources show, so are not graded.
(F) is every outdoor outlet: a Class A GFCI passes, a Class C SPGFCI (``Circuit.gfci_class``)
passes only where every outlet is HVAC (Ex. 3), and an unprotected one fails.
"""

from __future__ import annotations

from typing import NamedTuple

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding, Result
from typehaus.model.enums import Service
from typehaus.model.nec import NEC, cite
from typehaus.resolve.placeables import placed_xy

_CID = "code.E3902_gfci_locations"
# How far a receptacle may sit off an appliance's plan footprint and still be the one it
# plugs into: the range's box is behind it at 6", the dryer's on the wall the tower backs to.
_APPLIANCE_REACH_M = 24 * 0.0254
# 210.8(F) reaches outlets on branch circuits of 60 A or less (2026; was 50 A).
_OUTDOOR_MAX_AMPS = 60
# The Equipment kinds a Class C SPGFCI may protect under 210.8(F) Ex. 3.
_HVAC_KINDS = frozenset({"heat_pump", "air_handler", "ducted_air_handler", "indoor_head",
                         "furnace", "erv"})


class _Item(NamedTuple):
    tag: str
    storey: str
    body: object  # shapely geometry the reach is measured from
    reason: str
    circuit: str | None  # the branch the item names, where it names one
    volts: str  # "240" or "120": which receptacles can be its outlet


def _items(ctx: CheckContext) -> list[_Item]:
    """Every 210.8(D) appliance the model can name."""
    from shapely.geometry import Point, Polygon

    types = {t.tag: t for t in ctx.plan.library.appliance_types}
    out: list[_Item] = []
    for obj in ctx.model.canvas_objects:
        if obj.kind != "Appliance" or len(obj.footprint) < 3:
            continue
        product = types.get(obj.type_ref or "")
        needs = {getattr(n, "value", n) for n in getattr(product, "needs", ())}
        words = " ".join((obj.tag, obj.type_ref or "",
                          getattr(product, "name", "") or "")).lower()
        body = Polygon(obj.footprint)
        if Service.POWER_240.value in needs and getattr(product, "cooking", False):
            # A range is item (8); a wall oven or cooktop is another (D) item.
            item = NEC.GFCI_RANGE if getattr(product, "plan_symbol", "") == "range" \
                else NEC.GFCI_APPLIANCES
            out.append(_Item(obj.tag, obj.storey, body,
                             f"{item} (electric cooking appliance {obj.tag})", None, "240"))
        elif Service.POWER_240.value in needs and "dryer" in words:
            out.append(_Item(obj.tag, obj.storey, body,
                             f"{NEC.GFCI_DRYER} (clothes dryer {obj.tag})", None, "240"))
        if "dishwasher" in words:
            out.append(_Item(obj.tag, obj.storey, body,
                             f"{NEC.GFCI_APPLIANCES} (dishwasher {obj.tag})", None, "120"))
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            pump = getattr(element, "pump", None) if element.element_kind == "Sump" else None
            if pump is None:
                continue
            xy = placed_xy(ctx.model, element)
            out.append(_Item(element.tag, storey.tag, Point(xy),
                             f"{NEC.GFCI_SUMP} (sump pump in {element.tag})",
                             pump.circuit_ref, "120"))
    return out


def appliance_receptacles(ctx: CheckContext, receptacles: list[tuple[object, str]],
                          ) -> tuple[dict[str, str], list[Finding]]:
    """{receptacle tag: its (D) reason}, plus findings for items with no receptacle.

    ``receptacles`` is the 210.8(A) population, (device, storey). An item that names its
    circuit takes that circuit's receptacles, or grades the circuit itself when none (it is
    hardwired); one that names none takes the receptacles within reach of its voltage.
    """
    from shapely.geometry import Point

    code = cite(NEC.GFCI_APPLIANCES)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    circuits = {c.tag: c for c in ctx.plan.library.circuits}

    def volts(device) -> set[str]:
        ports = getattr(types.get(device.type_ref or ""), "ports", ())
        found = {"240" if p.service.value == "power_240" else "120" for p in ports
                 if p.service.value in ("power_120", "power_240")}
        return found or ({"240"} if device.kind.value == "receptacle_240" else {"120"})

    by_storey: dict[str, list[tuple[object, object]]] = {}
    for device, storey in receptacles:
        by_storey.setdefault(storey, []).append((device, Point(placed_xy(ctx.model, device))))
    reasons: dict[str, str] = {}
    findings: list[Finding] = []
    for item in _items(ctx):
        here = by_storey.get(item.storey, ())
        if item.circuit:
            near = [d for d, _ in here if d.circuit == item.circuit]
        else:
            near = [d for d, p in here if item.volts in volts(d)
                    and item.body.distance(p) <= _APPLIANCE_REACH_M]
        for device in near:
            reasons[device.tag] = "; ".join(filter(None, (reasons.get(device.tag),
                                                          item.reason)))
        if near:
            continue
        circuit = circuits.get(item.circuit or "")
        if circuit is None:
            findings.append(by_result(_CID, Result.UNKNOWN,
                                      f"{item.reason}: names no circuit and no receptacle "
                                      "is within 2 ft of it, so its outlet cannot be traced",
                                      (item.tag,), code,
                                      "place its receptacle, or name its circuit"))
        elif circuit.gfci and getattr(circuit, "gfci_class", "A") == "A":
            findings.append(by_result(_CID, Result.PASS, f"{item.reason}: hardwired on GFCI "
                                      f"breaker {circuit.tag}", (), code))
        else:
            findings.append(by_result(_CID, Result.FAIL,
                                      f"{item.reason}: hardwired on {circuit.tag}, which has "
                                      "no Class A GFCI", (item.tag, circuit.tag), code,
                                      f"set gfci=True on {circuit.tag}"))
    return reasons, findings


def outdoor_outlets(ctx: CheckContext, outdoor: dict[str, tuple[str, str]],
                    ) -> list[Finding]:
    """210.8(F) per outdoor circuit.

    ``outdoor`` maps each outdoor Equipment consumer to (circuit, equipment kind);
    receptacles outdoors are 210.8(A)(4)'s.
    """
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    by_circuit: dict[str, list[str]] = {}
    kinds: dict[str, set[str]] = {}
    for tag, (circuit_tag, kind) in outdoor.items():
        by_circuit.setdefault(circuit_tag, []).append(tag)
        kinds.setdefault(circuit_tag, set()).add(kind)
    code = cite(NEC.GFCI_OUTDOOR_OUTLETS)
    out: list[Finding] = []
    for circuit_tag, tags in sorted(by_circuit.items()):
        circuit = circuits.get(circuit_tag)
        if circuit is None or circuit.breaker_amps > _OUTDOOR_MAX_AMPS:
            continue
        fed = ", ".join(sorted(tags))
        hvac = kinds[circuit_tag] <= _HVAC_KINDS
        class_c = getattr(circuit, "gfci_class", "A") == "C"
        if getattr(circuit, "gfci", False) and class_c and not hvac:
            out.append(by_result(_CID, Result.FAIL,
                                 f"{circuit_tag} is a Class C SPGFCI feeding non-HVAC outdoor "
                                 f"outlet(s) {fed}; {NEC.GFCI_OUTDOOR_OUTLETS} Ex. 3 accepts "
                                 "Class C only for listed HVAC", (circuit_tag, *sorted(tags)),
                                 code, f"make {circuit_tag} a Class A GFCI"))
        elif getattr(circuit, "gfci", False):
            how = ("a Class C SPGFCI on HVAC (Ex. 3); its disconnect is marked \"Warning: "
                   "Class C SPGFCI Protection Provided for HVAC Unit\"" if class_c
                   else "GFCI-protected")
            out.append(by_result(_CID, Result.PASS, f"{circuit_tag} is {how} — "
                                 f"{NEC.GFCI_OUTDOOR_OUTLETS} outdoor outlet ({fed})", (), code))
        else:
            fix = (f"set gfci=True on {circuit_tag} (Class C SPGFCI is allowed for listed "
                   "HVAC)" if hvac else f"set gfci=True on {circuit_tag}")
            out.append(by_result(_CID, Result.FAIL,
                                 f"{circuit_tag} feeds outdoor outlet(s) {fed} with no GFCI; "
                                 f"{NEC.GFCI_OUTDOOR_OUTLETS} requires it",
                                 (circuit_tag, *sorted(tags)), code, fix))
    return out

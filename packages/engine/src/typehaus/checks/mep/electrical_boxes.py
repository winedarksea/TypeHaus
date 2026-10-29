"""``electrical.box_fill`` — NEC 314.16(B) fill, and a flush box's depth against its cavity.

A box is graded **through-fed** — the worst ordinary case — except a receptacle that is its
circuit's only load, which is end-fed (one cable); a switch or thermostat always has a line
and a load cable. Counted: cables of the
insulated conductors (a 1-pole circuit's hot and neutral; a 2-pole's two hots, plus a neutral
where the device has a 120 V half or a 14- configuration), two volumes per yoke
(314.16(B)(4)), and one for all the equipment grounds together (314.16(B)(5)). The unit
volume is Table 314.16(B)'s, at the gauge the breaker implies — 15 A 14 AWG, 20 A 12 AWG,
30 A 10 AWG. Box volume is the standard's row: Table 314.16(A) or the marked volume, plus a
marked raised cover or ring. A FAIL names the next box up. Hand-worked oracle:
``houses/catlin/notes/basement_surface_wiring.md`` §Box fill.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.model.electrical import METAL_BOX_VOLUME_IN3
from typehaus.quantities import M_PER_IN
from typehaus.resolve.device_boxes import takes_box

_CID = "electrical.box_fill"
_CODE = "NEC 314.16(B)"
#: Copper branch-circuit gauge by breaker rating (NEC 240.4(D), 310.16 at 60 °C).
GAUGE_BY_BREAKER_A = {15: 14, 20: 12, 30: 10, 40: 8, 50: 6}
_RECEPTACLES = frozenset({"receptacle", "gfci", "receptacle_240"})
#: Table 314.16(B), in³ per conductor by AWG.
VOLUME_PER_CONDUCTOR_IN3 = {14: 2.0, 12: 2.25, 10: 2.5, 8: 3.0, 6: 5.0}


def insulated_per_cable(poles: int, has_neutral: bool) -> int:
    return 2 if poles == 1 else (3 if has_neutral else 2)


def required_volume_in3(gauge: int, poles: int, has_neutral: bool, gangs: int,
                        cables: int = 2) -> float:
    """Cables × insulated conductors + 2 per yoke + 1 for all grounds."""
    count = cables * insulated_per_cable(poles, has_neutral) + 2 * gangs + 1
    return count * VOLUME_PER_CONDUCTOR_IN3[gauge]


def next_box_up(required_in3: float) -> str:
    fits = sorted((volume, name) for name, volume in METAL_BOX_VOLUME_IN3.items()
                  if volume >= required_in3)
    if not fits:
        return f"no Table 314.16(A) box holds {required_in3:.1f} in³ — split the splice"
    volume, name = fits[0]
    return f"a {name} box ({volume:g} in³) or a listed box marked ≥ {required_in3:.1f} in³"


def _has_neutral(product_type: Any | None) -> bool:
    nema = getattr(product_type, "nema", None) or ""
    services = {getattr(port.service, "value", None)
                for port in getattr(product_type, "ports", ())}
    return nema.startswith("14-") or {"power_120", "power_240"} <= services


def _grade(box: Any, circuits: dict[str, Any], types: dict[str, Any],
           type_ref: str | None, loads: dict[str, int]) -> Finding:
    tags = (box.device_tag,)
    if box.device_kind == "data_outlet":
        return not_applicable(_CID, f"{box.device_tag} is a data outlet: Class 2 / comms "
                                    "cabling is outside 314.16", tags, code=_CODE)
    where = f"{box.device_tag}'s {box.mounting} {box.gangs}-gang box ({box.box_product})"
    if box.cavity_m is not None and box.depth_m > box.cavity_m + 1e-4:
        return failed(_CID, f"{where} is {box.depth_m / M_PER_IN:.2f}\" deep in a "
                            f"{box.cavity_m / M_PER_IN:.2f}\" cavity", tags,
                      code="NEC 314.20 / 314.23",
                      fix="a shallower box row in the BoxStandard, or a deeper cavity")
    circuit = circuits.get(box.circuit or "")
    if circuit is None:
        return unknown(_CID, f"{where} names no circuit, so its conductors are unknown",
                       tags, code=_CODE, fix="name the device's circuit")
    gauge = GAUGE_BY_BREAKER_A.get(circuit.breaker_amps)
    if gauge is None or box.volume_in3 is None:
        return unknown(_CID, f"{where}: no gauge for a {circuit.breaker_amps} A breaker or no "
                             "box volume", tags, code=_CODE)
    end_fed = box.device_kind in _RECEPTACLES and loads.get(circuit.tag, 0) <= 1
    cables = 1 if end_fed else 2
    feed = "through-fed" if cables == 2 else "end-fed"
    required = required_volume_in3(gauge, circuit.poles,
                                   _has_neutral(types.get(type_ref or "")), box.gangs, cables)
    if required > box.volume_in3 + 1e-6:
        return failed(_CID, f"{where} holds {box.volume_in3:g} in³; {feed} {gauge} AWG "
                            f"needs {required:.2f} in³", tags, code=_CODE,
                      fix=f"step up to {next_box_up(required)}")
    return passed(_CID, f"{where}: {required:.2f} in³ of {feed} {gauge} AWG in "
                        f"{box.volume_in3:g} in³", tags, code=_CODE)


@check(Tier.ADVISORY, _CID)
def box_fill(ctx: CheckContext) -> list[Finding]:
    """Each derived device box against its through-fed fill and its cavity depth."""
    boxes = list(ctx.model.device_boxes)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    if not boxes:
        declared = any(el.element_kind == "BoxStandard" for el in ctx.plan.all_elements())
        wants = [obj.tag for obj in ctx.model.canvas_objects
                 if obj.kind == "ElectricalDevice" and obj.attachment_wall is not None
                 and takes_box(ctx.plan.by_tag(obj.tag), types.get(obj.type_ref or ""))]
        if declared or not wants:
            return [not_applicable(_CID, "no wall device takes a derived box", code=_CODE)]
        return [unknown(_CID, f"{len(wants)} wall device(s) but no BoxStandard, so no box is "
                              "modeled", code=_CODE,
                        fix="declare one BoxStandard (decision #93)")]
    circuits = {circuit.tag: circuit for circuit in ctx.plan.library.circuits}
    type_refs = {obj.tag: obj.type_ref for obj in ctx.model.canvas_objects}
    loads: dict[str, int] = {}
    for element in ctx.plan.all_elements():
        circuit = getattr(element, "circuit", None)
        if circuit and element.element_kind in ("ElectricalDevice", "Equipment"):
            loads[circuit] = loads.get(circuit, 0) + 1
    return [_grade(box, circuits, types, type_refs.get(box.device_tag), loads)
            for box in boxes]

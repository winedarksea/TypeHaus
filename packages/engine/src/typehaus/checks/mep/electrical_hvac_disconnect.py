"""``electrical.hvac_disconnect`` — 2026 NEC Article 440 at each circuit-fed heat pump.

440.14: each outdoor heat-pump unit and ducted air handler on its own circuit needs a
disconnecting means within sight of it and readily accessible (it may be in the equipment). The
disconnect is the ``DeviceKind.DISCONNECT`` device on the unit's circuit. Within sight is read
as a straight plan line to the unit's footprint with no wall across it (the
``electrical_spa_geometry`` approach); Article 100's distance limit is not read, so the gap is
reported, not graded. Indoor heads carry no circuit (the outdoor unit feeds them) and are
skipped. A unit with no disconnect device on its circuit is UNKNOWN.

440.4(B)/440.22(C): the breaker is at most the marked maximum OCPD, read from the equipment
type (``max_overcurrent_a``). A circuit feeding several pieces (an air handler and its heat
kit) is graded against the one with the largest MCA: a kit's published row marks the unit with
the kit fitted. 440.35 (conductors at least the MCA) waits on a conductor size, which no circuit
carries. 440.11 (lock or tool) and 440.12(A)(1) (115% rating) read the disconnect type's
``lockable`` and ``disconnect_rating_a``; 115% of the MCA bounds 115% of the summed rated-load
currents from above, so a rating at or over it passes and one under it is UNKNOWN.
Not graded: 440.10 (needs the available fault current at the service), readily accessible,
110.26(A) working space, panels that obscure the nameplate.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_spa_geometry import _separated, _walls
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_CID = "electrical.hvac_disconnect"
_FT = 0.3048
_KINDS = frozenset({"heat_pump", "ducted_air_handler"})
_DISCONNECT_MARGIN = 1.15  # 440.12(A)(1)


@check(Tier.ADVISORY, _CID)
def hvac_disconnect(ctx: CheckContext) -> list[Finding]:
    """Article 440 at each circuit-fed heat pump or air handler: disconnect, OCPD, rating."""
    units = [e for e in ctx.plan.all_elements()
             if e.element_kind == "Equipment" and getattr(e, "circuit", None)
             and getattr(getattr(e, "kind", None), "value", None) in _KINDS]
    if not units:
        return [not_applicable(_CID, "no circuit-fed heat pump or air handler is authored",
                               code=cite(NEC.HVAC_DISCONNECT))]
    disconnects = [e for e in ctx.plan.all_elements()
                   if e.element_kind == "ElectricalDevice" and e.kind is DeviceKind.DISCONNECT]
    nameplates = _nameplates(ctx, {u.circuit for u in units})
    return (_in_sight(ctx, units, disconnects) + _max_ocpd(ctx, nameplates)
            + _disconnect_ratings(ctx, nameplates, disconnects))


def _in_sight(ctx: CheckContext, units, disconnects) -> list[Finding]:
    from shapely.geometry import Point, Polygon

    code = cite(NEC.HVAC_DISCONNECT)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    out: list[Finding] = []
    for unit in sorted(units, key=lambda e: e.tag):
        obj = objects.get(unit.tag)
        mine = [d for d in disconnects if d.circuit == unit.circuit]
        if not mine or obj is None:
            out.append(unknown(
                _CID, f"{unit.tag} (circuit {unit.circuit}) has no disconnect device on its "
                      "circuit; 440.14 lets the equipment carry one, which the model cannot say",
                (unit.tag,), code=code, fix="author a DISCONNECT device on the circuit, or state "
                                            "that the unit has an integral one"))
            continue
        body = Polygon(obj.footprint)
        for disc in mine:
            other = objects.get(disc.tag)
            if other is None or other.storey != obj.storey:
                out.append(unknown(_CID, f"{disc.tag} is not on {unit.tag}'s level, so "
                                         "sight cannot be read in plan", (unit.tag, disc.tag),
                                   code=code))
                continue
            gap = body.distance(Point(other.position))
            if _separated(body, Point(other.position), _walls(ctx, obj.storey)):
                out.append(unknown(
                    _CID, f"{disc.tag} is {gap / _FT:.1f} ft from {unit.tag} with a wall "
                          "between, so within sight is not shown", (unit.tag, disc.tag),
                    code=code))
            else:
                out.append(passed(
                    _CID, f"{disc.tag} is {gap / _FT:.1f} ft from {unit.tag} in plan with no "
                          "wall between (distance limit and accessibility not graded)",
                    (unit.tag, disc.tag), code=code))
    return out


def _nameplates(ctx: CheckContext, circuits: set[str]) -> dict[str, tuple[str, object]]:
    """circuit -> (governing equipment tag, its type): the largest stated MCA on the circuit."""
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    out: dict[str, tuple[str, object]] = {}
    for e in sorted(ctx.plan.all_elements(), key=lambda e: e.tag):
        if e.element_kind != "Equipment" or getattr(e, "circuit", None) not in circuits:
            continue
        kind = types.get(e.type_ref or "")
        mca = getattr(kind, "min_circuit_ampacity_a", None)
        held = out.get(e.circuit)
        held_mca = getattr(held[1], "min_circuit_ampacity_a", None) if held else None
        if held is None or (mca is not None and (held_mca is None or mca > held_mca)):
            out[e.circuit] = (e.tag, kind)
    return out


def _max_ocpd(ctx: CheckContext, nameplates) -> list[Finding]:
    code = cite(NEC.HVAC_NAMEPLATE, NEC.HVAC_MAX_OCPD)
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    out: list[Finding] = []
    awaiting_conductors: list[str] = []
    for name, (tag, kind) in sorted(nameplates.items()):
        circuit = circuits.get(name)
        if circuit is None:
            continue
        mca = getattr(kind, "min_circuit_ampacity_a", None)
        mocp = getattr(kind, "max_overcurrent_a", None)
        if mocp is None:
            out.append(unknown(_CID, f"{name}: {tag}'s type states no maximum OCPD, so the "
                                     f"{circuit.breaker_amps} A breaker is ungraded",
                               (name, tag), code=code,
                               fix="author max_overcurrent_a and min_circuit_ampacity_a from "
                                   "the published submittal"))
            continue
        verb = passed if circuit.breaker_amps <= mocp else failed
        out.append(verb(_CID, f"{name}: {circuit.breaker_amps} A breaker against {tag}'s "
                              f"marked maximum OCPD {mocp} A (MCA {mca} A)", (name, tag),
                        code=code))
        if mca is not None:
            awaiting_conductors.append(f"{name} {mca:g} A")
    if awaiting_conductors:
        out.append(unknown(_CID, "440.35 conductors at least the marked MCA ("
                                 + ", ".join(awaiting_conductors) + "): no circuit carries a "
                                 "conductor size", code=cite(NEC.HVAC_COMBINATION_CONDUCTORS)))
    return out


def _disconnect_ratings(ctx: CheckContext, nameplates, disconnects) -> list[Finding]:
    dev_types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    out: list[Finding] = []
    unstated: dict[str, list[str]] = {}
    for disc in sorted((d for d in disconnects if d.circuit in nameplates), key=lambda d: d.tag):
        kind = dev_types.get(disc.type_ref or "")
        lockable = getattr(kind, "lockable", None)
        rating = getattr(kind, "disconnect_rating_a", None)
        if lockable is None or rating is None:
            unstated.setdefault(disc.type_ref or "(no type)", []).append(disc.tag)
        if lockable is not None:
            verb, how = (passed, "locks or needs a tool") if lockable else (failed, "does not lock")
            out.append(verb(_CID, f"{disc.tag}: its enclosure {how} (440.11)", (disc.tag,),
                            code=cite(NEC.HVAC_DISCONNECT_ENCLOSURE)))
        if rating is None:
            continue
        mca = getattr(nameplates[disc.circuit][1], "min_circuit_ampacity_a", None)
        code = cite(NEC.HVAC_DISCONNECT_RATING)
        if mca is None:
            out.append(unknown(_CID, f"{disc.tag}: {disc.circuit}'s equipment states no MCA "
                                     "to grade the rating against", (disc.tag,), code=code))
        elif rating >= _DISCONNECT_MARGIN * mca:
            out.append(passed(_CID, f"{disc.tag}: a {rating} A switch covers 115% of "
                                    f"{disc.circuit}'s MCA {mca:g} A "
                                    f"({_DISCONNECT_MARGIN * mca:.1f} A)", (disc.tag,), code=code))
        else:
            out.append(unknown(_CID, f"{disc.tag}: {rating} A is under 115% of the MCA "
                                     f"{mca:g} A; the rated-load current decides", (disc.tag,),
                               code=code))
    for type_tag, tags in sorted(unstated.items()):
        out.append(unknown(_CID, f"{type_tag} states no lockable enclosure or ampere rating, so "
                                 f"440.11 and 440.12(A)(1) are ungraded for {', '.join(tags)}",
                           tuple(tags),
                           code=cite(NEC.HVAC_DISCONNECT_ENCLOSURE, NEC.HVAC_DISCONNECT_RATING),
                           fix="author lockable and disconnect_rating_a from the switch's "
                               "datasheet"))
    return out

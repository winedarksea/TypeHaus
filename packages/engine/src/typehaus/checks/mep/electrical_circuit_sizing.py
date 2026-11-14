"""Branch-circuit sizing — 2026 NEC 210.19(A)(1), 210.19(C), 210.20(A), 210.21(B), 210.23(B).

``electrical.continuous_load_circuit``: a circuit with a continuous load takes a breaker (and
conductors) of at least the noncontinuous load plus 125% of the continuous load. Where the
circuit authors ``continuous_va`` the split is exact, and authored conductors are held to the
same figure at their 110.14(C)(1) column (210.19(A)(1)). Otherwise the arithmetic runs on the
whole connected VA (``_connected_va``): breaker >= 125% passes whatever the split; short of it
is FAIL only for a known-continuous load (a fixed storage water heater of 120 gal or less,
422.13, off ``EquipmentType.storage_gallons``), else UNKNOWN. Left to their own checks: heat
pumps (Art. 440), fixed space heat (424.5, ``electrical.space_heat_circuit``) and EVSE (625.41,
``electrical.evse_circuit``). A range is graded by 210.19(C) (>= 8 3/4 kW takes 40 A).

``electrical.single_receptacle_rating``: 210.21(B)(1), the one receptacle on an individual
circuit is rated at least the circuit, read off ``ElectricalDeviceType.nema``. A combination
device (two receptacles) is not a single receptacle and is skipped; no NEMA is UNKNOWN.

``electrical.multi_receptacle_rating``: 210.21(B)(3), on a circuit serving two or more receptacles
each is rated per Table 210.21(B)(3) (15 A circuit: 15; 20: 15 or 20; 30: 30; 40: 40 or 50; 50:
50; above 50 A: at least the circuit), and 210.22 lets no 10 A circuit serve receptacles. A device
with no NEMA gives UNKNOWN. A deadfront (blank-face GFCI) holds no receptacle and is skipped.

``electrical.permissible_loads``: 210.23(B) on 15/20 A circuits, off
``EquipmentType.utilization_connection``: (1) a cord-and-plug item at most 80% of the rating;
(2) fastened-in-place equipment at most 50% where the circuit also serves receptacles or
lighting. Equipment on a circuit with no receptacle cannot be cord-and-plug connected there.
"""

from __future__ import annotations

import re

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.ampacity import ampacity, termination_column
from typehaus.model.nec import NEC, cite

_CID = "electrical.continuous_load_circuit"
_REC_CID = "electrical.single_receptacle_rating"
CONTINUOUS_FACTOR = 1.25
STORAGE_HEATER_CONTINUOUS_MAX_GAL = 120.0  # 422.13: 450 L or less
RANGE_MIN_VA = 8750.0  # 210.19(C): ranges of 8 3/4 kW or more
RANGE_MIN_AMPS = 40
_OWN_CHECK = frozenset({"source", "heat_pump", "resistance_heat", "ev"})
_RECEPTACLES = frozenset({"receptacle", "gfci", "receptacle_240"})


def _holds_receptacle(e, device_types: dict) -> bool:
    """A receptacle device, not a deadfront (blank-face GFCI) that shares its kind."""
    return (e.element_kind == "ElectricalDevice" and e.kind.value in _RECEPTACLES
            and not getattr(device_types.get(e.type_ref), "deadfront", False))


def _consumers(ctx: CheckContext) -> dict[str, list]:
    by: dict[str, list] = {}
    for e in ctx.plan.all_elements():
        ref = getattr(e, "circuit", None)
        if ref:
            by.setdefault(ref, []).append(e)
    return by


def _storage_gallons(ctx: CheckContext, consumers: list) -> tuple[bool, float | None]:
    """(has a storage water heater, its rated gallons if stated)."""
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    for e in consumers:
        if e.element_kind == "Equipment" and getattr(e.kind, "value", "") == "water_heater":
            return True, getattr(types.get(e.type_ref), "storage_gallons", None)
    return False, None


@check(Tier.ADVISORY, _CID)
def continuous_load_circuit(ctx: CheckContext) -> list[Finding]:
    """Each circuit's breaker against 125% of its connected load; ranges against 210.19(C)."""
    from typehaus.takeoff.service_load import _bucket, _connected_va

    consumers = _consumers(ctx)
    code = cite(NEC.BRANCH_OCPD_LOAD, NEC.BRANCH_CONDUCTOR_LOAD)
    out: list[Finding] = []
    graded: list[str] = []
    ungraded: list[str] = []
    for circuit in ctx.plan.library.circuits:
        on = consumers.get(circuit.tag, [])
        if circuit.source or circuit.spd or _bucket(ctx.model, circuit, on) in _OWN_CHECK:
            continue
        va = _connected_va(ctx.model, circuit, on)
        if va <= 0:
            ungraded.append(circuit.tag)
            continue
        amps = va / (240.0 if circuit.poles == 2 else 120.0)
        need = CONTINUOUS_FACTOR * amps
        tags = (circuit.tag, *(e.tag for e in on))
        if "range" in circuit.description.lower():
            verb = passed if (va < RANGE_MIN_VA or circuit.breaker_amps >= RANGE_MIN_AMPS) \
                else failed
            out.append(verb(_CID, f"{circuit.tag}: a {va / 1000:.1f} kW range on a "
                                  f"{circuit.breaker_amps} A breaker (40 A minimum from "
                                  "8 3/4 kW)", tags, code=cite(NEC.BRANCH_RANGE)))
            continue
        has_wh, gallons = _storage_gallons(ctx, on)
        ok = circuit.breaker_amps + 1e-9 >= need
        if circuit.continuous_va is not None and not (has_wh and gallons is not None):
            out.append(_split_finding(circuit, va, tags, code))
        elif has_wh and gallons is not None and gallons <= STORAGE_HEATER_CONTINUOUS_MAX_GAL:
            out.append((passed if ok else failed)(
                _CID, f"{circuit.tag}: {gallons:.0f} gal storage water heater is continuous "
                      f"(422.13): {amps:.1f} A x 125% = {need:.1f} A against a "
                      f"{circuit.breaker_amps} A breaker", tags,
                code=cite(NEC.STORAGE_WATER_HEATER, NEC.BRANCH_OCPD_LOAD)))
        elif ok:
            graded.append(circuit.tag)
        else:
            what = ("a water heater with no storage_gallons stated, so 422.13 cannot be "
                    "applied; " if has_wh else "")
            out.append(unknown(
                _CID, f"{circuit.tag}: {amps:.1f} A on a {circuit.breaker_amps} A breaker is "
                      f"under 125% ({need:.1f} A); {what}the model does not say how much of "
                      "the load is continuous (3 h or more)", tags, code=code,
                fix="state whether the load is continuous, or raise the breaker"))
    if graded:
        out.append(passed(_CID, f"{len(graded)} circuits carry their connected load at 125% "
                                "or less of the breaker, so pass whatever part is continuous",
                          tuple(graded), code=code))
    if ungraded:
        out.append(unknown(_CID, f"{len(ungraded)} circuits state no load, so 125% cannot be "
                                 "read", tuple(ungraded), code=code))
    if not out:
        return [not_applicable(_CID, "no branch circuit states a load", code=code)]
    return out


def _split_finding(circuit, va: float, tags: tuple[str, ...], code: str) -> Finding:
    """210.20(A) / 210.19(A)(1) on an authored continuous/noncontinuous split."""
    volts = 240.0 if circuit.poles == 2 else 120.0
    cont = min(circuit.continuous_va, va)
    need = (va - cont) / volts + CONTINUOUS_FACTOR * cont / volts
    msg = (f"{circuit.tag}: {(va - cont) / volts:.1f} A noncontinuous + 125% of "
           f"{cont / volts:.1f} A continuous = {need:.1f} A against the "
           f"{circuit.breaker_amps} A breaker")
    ok = circuit.breaker_amps + 1e-9 >= need
    if circuit.conductor_awg is not None:
        column = termination_column(circuit.breaker_amps, circuit.conductor_awg,
                                    circuit.termination_temp_c)
        amps = ampacity(circuit.conductor_material, circuit.conductor_awg, column)
        msg += f" and #{circuit.conductor_awg}'s {amps} A at {column} °C"
        ok = ok and amps + 1e-9 >= need
    return (passed if ok else failed)(_CID, msg, tags, code=code)


def _receptacle_amps(nema: str | None) -> int | None:
    match = re.fullmatch(r"L?\d+-(\d+)R", nema or "")
    return int(match.group(1)) if match else None


@check(Tier.ADVISORY, _REC_CID)
def single_receptacle_rating(ctx: CheckContext) -> list[Finding]:
    """210.21(B)(1): a lone receptacle on an individual circuit is rated >= the breaker."""
    code = cite(NEC.SINGLE_RECEPTACLE)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    out: list[Finding] = []
    seen = 0
    consumers = _consumers(ctx)
    for circuit in ctx.plan.library.circuits:
        devices = [e for e in consumers.get(circuit.tag, [])
                   if e.element_kind == "ElectricalDevice"
                   and not getattr(types.get(e.type_ref), "deadfront", False)]
        if len(devices) != 1 or devices[0].kind.value not in _RECEPTACLES:
            continue
        device = devices[0]
        nema = getattr(types.get(device.type_ref), "nema", None)
        if nema and "/" in nema:
            continue  # a combination device holds two receptacles
        seen += 1
        rating = _receptacle_amps(nema)
        tags = (circuit.tag, device.tag)
        if rating is None:
            out.append(unknown(_REC_CID, f"{device.tag} on {circuit.tag} states no NEMA "
                                         "configuration, so its rating is unknown", tags,
                               code=code))
        elif rating < circuit.breaker_amps:
            out.append(failed(_REC_CID, f"{device.tag} ({nema}) is rated {rating} A on "
                                        f"{circuit.tag}'s {circuit.breaker_amps} A breaker",
                              tags, code=code))
        else:
            out.append(passed(_REC_CID, f"{device.tag} ({nema}) is rated {rating} A on "
                                        f"{circuit.tag}'s {circuit.breaker_amps} A breaker",
                              tags, code=code))
    if not seen:
        return [not_applicable(_REC_CID, "no circuit serves a single receptacle", code=code)]
    return out


#: Table 210.21(B)(3): receptacle ratings (A) allowed on a multi-outlet circuit of a given rating.
_TABLE_210_21_B_3 = {15: (15,), 20: (15, 20), 30: (30,), 40: (40, 50), 50: (50,)}
_MULTI_CID = "electrical.multi_receptacle_rating"


def _allowed(breaker: int) -> tuple[int, ...] | None:
    """Receptacle ratings the circuit allows; above 50 A, any at or over the circuit."""
    if breaker > 50:
        return (breaker,)
    return _TABLE_210_21_B_3.get(breaker, ())


@check(Tier.ADVISORY, _MULTI_CID)
def multi_receptacle_rating(ctx: CheckContext) -> list[Finding]:
    """210.21(B)(3) / 210.22: each receptacle on a multi-receptacle circuit fits the table."""
    code = cite(NEC.MULTI_RECEPTACLE, NEC.INDIVIDUAL_CIRCUIT)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    consumers = _consumers(ctx)
    out: list[Finding] = []
    for circuit in ctx.plan.library.circuits:
        devices = [e for e in consumers.get(circuit.tag, []) if _holds_receptacle(e, types)]
        ratings: list[int | None] = []
        for device in devices:
            nema = getattr(types.get(device.type_ref), "nema", None)
            parts = nema.split("/") if nema else [None]
            ratings.extend(_receptacle_amps(part) for part in parts)
        if len(ratings) < 2:
            continue  # one receptacle: 210.21(B)(1)'s case
        tags = (circuit.tag, *(d.tag for d in devices))
        allowed = _allowed(circuit.breaker_amps)
        if None in ratings:
            out.append(unknown(_MULTI_CID, f"{circuit.tag}: {ratings.count(None)} of its "
                                           f"{len(ratings)} receptacles state no NEMA "
                                           "configuration, so their rating is unknown", tags,
                               code=code, fix="author the receptacle type's NEMA"))
        elif not allowed:
            out.append(failed(_MULTI_CID, f"{circuit.tag}: a {circuit.breaker_amps} A circuit "
                                          "may not serve receptacles", tags, code=code))
        else:
            bad = sorted({r for r in ratings if r not in allowed and not (
                circuit.breaker_amps > 50 and r >= circuit.breaker_amps)})
            if bad:
                out.append(failed(_MULTI_CID, f"{circuit.tag}: {bad} A receptacles on a "
                                              f"{circuit.breaker_amps} A circuit; Table "
                                              f"210.21(B)(3) allows {list(allowed)} A", tags,
                                  code=code))
            else:
                out.append(passed(_MULTI_CID, f"{circuit.tag}: {len(ratings)} receptacles "
                                              f"({sorted(set(ratings))} A) on "
                                              f"{circuit.breaker_amps} A fit Table 210.21(B)(3)",
                                  tags, code=code))
    if not out:
        return [not_applicable(_MULTI_CID, "no circuit serves two or more receptacles",
                               code=code)]
    return out


_LOADS_CID = "electrical.permissible_loads"
CORD_AND_PLUG_MAX = 0.80  # 210.23(B)(1)
FASTENED_MIXED_MAX = 0.50  # 210.23(B)(2)
_SMALL_CIRCUITS = (15, 20)


@check(Tier.ADVISORY, _LOADS_CID)
def permissible_loads(ctx: CheckContext) -> list[Finding]:
    """210.23(B): cord-and-plug equipment <= 80%, fastened <= 50% on a mixed 15/20 A circuit."""
    from typehaus.takeoff.service_load import _connected_va

    code = cite(NEC.BRANCH_LOAD_LIMITS)
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    device_types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    consumers = _consumers(ctx)
    out: list[Finding] = []
    for circuit in ctx.plan.library.circuits:
        on = consumers.get(circuit.tag, [])
        equipment = [e for e in on if e.element_kind == "Equipment"]
        if circuit.breaker_amps not in _SMALL_CIRCUITS or not equipment:
            continue
        receptacles = [e for e in on if _holds_receptacle(e, device_types)]
        lights = [e for e in on if e.element_kind == "LightRun" or (
            e.element_kind == "ElectricalDevice" and e.kind.value == "light")]
        rating_va = circuit.breaker_amps * (240.0 if circuit.poles == 2 else 120.0)
        tags = (circuit.tag, *(e.tag for e in equipment))
        if len(equipment) > 1:
            out.append(unknown(_LOADS_CID, f"{circuit.tag}: {len(equipment)} pieces of "
                                           "equipment share the circuit's one load figure",
                               tags, code=code))
            continue
        item = equipment[0]
        how = getattr(types.get(item.type_ref), "utilization_connection", None)
        if how is None and not receptacles:
            how = "fastened"  # nothing on the circuit to plug into
        share = _connected_va(ctx.model, circuit, on) / rating_va
        if how is None:
            out.append(unknown(_LOADS_CID, f"{circuit.tag}: {item.tag}'s type does not say "
                                           "cord-and-plug or fastened in place", tags,
                               code=code, fix="author EquipmentType.utilization_connection"))
        elif how == "cord_and_plug":
            verb = passed if share <= CORD_AND_PLUG_MAX + 1e-9 else failed
            out.append(verb(_LOADS_CID, f"{circuit.tag}: cord-and-plug {item.tag} is "
                                        f"{share:.1%} of {circuit.breaker_amps} A (80% at "
                                        "most, 210.23(B)(1))", tags, code=code))
        elif receptacles or lights:
            verb = passed if share <= FASTENED_MIXED_MAX + 1e-9 else failed
            out.append(verb(_LOADS_CID, f"{circuit.tag}: fastened {item.tag} is {share:.1%} "
                                        f"of {circuit.breaker_amps} A beside "
                                        f"{len(receptacles) + len(lights)} other outlets (50% "
                                        "at most, 210.23(B)(2))", tags, code=code))
        else:
            out.append(passed(_LOADS_CID, f"{circuit.tag}: fastened {item.tag} alone on the "
                                          "circuit; 210.23(B)(2)'s 50% applies only beside "
                                          "lighting or cord-and-plug loads", tags, code=code))
    if not out:
        return [not_applicable(_LOADS_CID, "no 15 or 20 A circuit supplies equipment",
                               code=code)]
    return out

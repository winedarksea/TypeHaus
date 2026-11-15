"""Branch-circuit conductors against their breaker and their EGC (2026 NEC), off the authored
``Circuit.conductor_awg`` / ``conductor_material`` / ``egc_awg`` / ``termination_temp_c``.

``electrical.conductor_protection``: 240.4. The breaker may not exceed the conductor's Table 310.16
ampacity at its 110.14(C)(1) termination column (60 °C to 100 A and 14-1 AWG unless the circuit
authors 75 °C listed terminations), capped by 240.4(D) for 14-10 AWG. 240.4(B)'s next size up is
taken only where no receptacle is on the circuit (it is refused to a branch circuit with more
than one cord-and-plug receptacle, and a duplex is two). Air-conditioning equipment follows
Article 440 (240.4(G)): a heat-pump circuit short of plain 240.4 is UNKNOWN, not FAIL. No
ambient correction or 310.15(C)(1) adjustment is applied (the model holds no conductor routing).

``electrical.egc_size``: Table 250.122 by the breaker, never larger than the circuit conductors
(250.122(A)). Where the conductors are larger than the smallest the breaker allows, 250.122(D)
enlarges the table EGC by the same circular-mil ratio (AWG areas from ``grounding_tables.kcmil``),
still capped by (A). The engine applies no 310.15(B)/(C) derating, so every enlargement counts.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory_fail, failed, passed, unknown
from typehaus.checks.mep.electrical_circuit_sizing import _holds_receptacle
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.ampacity import (
    SMALL_CONDUCTOR_MAX_OCPD,
    ampacity,
    egc_minimum,
    max_ocpd,
    size_at_least,
    smallest_size_for,
    termination_column,
)
from typehaus.model.grounding_tables import kcmil
from typehaus.model.nec import NEC, cite

_PROTECT_CID = "electrical.conductor_protection"
_EGC_CID = "electrical.egc_size"
_METAL = {"cu": "Cu", "al": "Al"}
_KCMIL_TOLERANCE = 0.9995  # AWG areas are rounded; matches grounding_tables.larger


def _receptacle_count(ctx: CheckContext) -> dict[str, int]:
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    count: dict[str, int] = {}
    for e in ctx.plan.all_elements():
        if getattr(e, "circuit", None) and _holds_receptacle(e, types):
            count[e.circuit] = count.get(e.circuit, 0) + 1
    return count


def _hvac_circuits(ctx: CheckContext) -> set[str]:
    from typehaus.takeoff.service_load import _bucket

    on: dict[str, list] = {}
    for e in ctx.plan.all_elements():
        if getattr(e, "circuit", None):
            on.setdefault(e.circuit, []).append(e)
    return {c.tag for c in ctx.plan.library.circuits
            if _bucket(ctx.model, c, on.get(c.tag, [])) == "heat_pump"}


def _label(circuit) -> str:
    return f"#{circuit.conductor_awg} {_METAL[circuit.conductor_material]}"


@check(Tier.ADVISORY, _PROTECT_CID)
def conductor_protection(ctx: CheckContext) -> list[Finding]:
    """240.4 / 240.4(B) / 240.4(D): each authored conductor protects at its breaker."""
    code = cite(NEC.CONDUCTOR_PROTECTION, NEC.AMPACITY_TABLE, NEC.TERMINATION_TEMP)
    receptacles = _receptacle_count(ctx)
    hvac = _hvac_circuits(ctx)
    out: list[Finding] = []
    unsized: list[str] = []
    for circuit in ctx.plan.library.circuits:
        if circuit.spd:
            continue  # the SPD's leads are the device's own, not a branch circuit
        if circuit.conductor_awg is None:
            unsized.append(circuit.tag)
            continue
        size, metal = circuit.conductor_awg, circuit.conductor_material
        column = termination_column(circuit.breaker_amps, size, circuit.termination_temp_c)
        next_up = receptacles.get(circuit.tag, 0) == 0
        top = max_ocpd(metal, size, column, next_size_up=next_up)
        tags = (circuit.tag,)
        if top is None:
            out.append(unknown(_PROTECT_CID, f"{circuit.tag}: {_label(circuit)} is a conditional "
                                             "240.4(D) size or outside Table 310.16", tags,
                               code=code))
            continue
        amps = ampacity(metal, size, column)
        why = [f"{amps} A in Table 310.16"]
        if top > amps:
            why.append(f"next size up {top} A by 240.4(B)")
        if (metal, size) in SMALL_CONDUCTOR_MAX_OCPD:
            why.append(f"240.4(D) cap {SMALL_CONDUCTOR_MAX_OCPD[metal, size]} A")
        msg = (f"{circuit.tag}: {_label(circuit)} at {column} °C ({'; '.join(why)}) is "
               f"protected at {top} A at most; the breaker is {circuit.breaker_amps} A")
        if circuit.breaker_amps <= top:
            out.append(passed(_PROTECT_CID, msg, tags, code=code))
        elif circuit.tag in hvac:
            out.append(unknown(_PROTECT_CID, msg + "; air-conditioning conductors follow "
                                                   "Article 440 (240.4(G)): grade them on the "
                                                   "unit's MCA and maximum OCPD", tags,
                               code=cite(NEC.CONDUCTOR_PROTECTION, NEC.SPECIFIC_CONDUCTORS)))
        else:
            out.append(failed(_PROTECT_CID, msg, tags, code=code,
                              fix="a larger conductor or a smaller breaker"))
    if unsized:
        out.append(unknown(_PROTECT_CID, f"{len(unsized)} circuits author no conductor size",
                           tuple(unsized), code=code, fix="author Circuit.conductor_awg"))
    return out


@check(Tier.ADVISORY, _EGC_CID)
def egc_size(ctx: CheckContext) -> list[Finding]:
    """250.122 / (A) / (D): the wire EGC against the breaker and the circuit conductors."""
    code = cite(NEC.EGC_SIZE, NEC.EGC_TABLE)
    out: list[Finding] = []
    missing: list[str] = []
    for circuit in ctx.plan.library.circuits:
        if circuit.spd or circuit.conductor_awg is None:
            continue
        if circuit.egc_awg is None:
            missing.append(circuit.tag)
            continue
        metal, size, egc = circuit.conductor_material, circuit.conductor_awg, circuit.egc_awg
        table = egc_minimum(circuit.breaker_amps, metal)
        need = size if size_at_least(table, size) else table  # 250.122(A)
        tags = (circuit.tag,)
        what = (f"{circuit.tag}: #{egc} {_METAL[metal]} EGC with {_label(circuit)} on "
                f"{circuit.breaker_amps} A; Table 250.122 gives #{table}")
        if not size_at_least(egc, need):
            out.append(advisory_fail(_EGC_CID, what + (f", #{need} by 250.122(A)" if need != table
                                                else ""), tags, code=code,
                              fix="a larger EGC"))
            continue
        base = smallest_size_for(circuit.breaker_amps, metal, circuit.termination_temp_c)
        enlarged = base is not None and size != base and size_at_least(size, base)
        if not enlarged:
            out.append(passed(_EGC_CID, what, tags, code=code))
            continue
        ratio = kcmil(size) / kcmil(base)
        required = min(kcmil(table) * ratio, kcmil(size))
        what += (f"; conductors enlarged past #{base} (x{ratio:.2f} by area), so 250.122(D) "
                 f"wants {required:.2f} kcmil against #{egc}'s {kcmil(egc):.2f}")
        code_d = cite(NEC.EGC_UPSIZED)
        if kcmil(egc) >= required * _KCMIL_TOLERANCE:
            out.append(passed(_EGC_CID, what, tags, code=code_d))
        else:
            out.append(advisory_fail(_EGC_CID, what, tags, code=code_d,
                                     fix="enlarge the EGC in proportion, or match the conductors"))
    if missing:
        out.append(unknown(_EGC_CID, f"{len(missing)} sized circuits author no wire EGC",
                           tuple(missing), code=code, fix="author Circuit.egc_awg"))
    return out

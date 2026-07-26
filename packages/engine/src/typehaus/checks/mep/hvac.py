"""HVAC checks — duct/joist-bay coordination (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.mep import is_parallel_to_floor

_M_TO_IN = 39.37007874015748


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


def _fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {reason}",
                   element_tags=tags, result=Result.UNKNOWN)


@check(Tier.STRUCTURAL, "mep.duct_joist_bay")
def duct_joist_bay(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay":
            continue
        if duct.floor_ref is None or not any(f.tag == duct.floor_ref for f in ctx.model.floors):
            out.append(_unknown(
                "mep.duct_joist_bay", f"duct {duct.tag} floor_ref did not resolve",
                (duct.tag,),
            ))
            continue
        if duct.conflicts or not duct.depth_ok:
            problems = list(duct.conflicts)
            if not duct.depth_ok:
                problems.append(f"depth {duct.depth_m * _M_TO_IN:.1f}\" exceeds joist depth")
            out.append(_fail(
                "mep.duct_joist_bay", f"duct {duct.tag}: " + "; ".join(problems), (duct.tag,),
            ))
            continue
        note = f"duct {duct.tag} occupies its joist bay cleanly"
        if duct.crossings:
            points = ", ".join(
                f"({x * _M_TO_IN / 12:.1f}', {y * _M_TO_IN / 12:.1f}')" for x, y in duct.crossings
            )
            note += (f"; crosses bearing wall(s) at {points} — "
                    "provide fire blocking per R302.11")
        out.append(_pass("mep.duct_joist_bay", note, (duct.tag,)))
    return out


@check(Tier.ADVISORY, "mep.duct_direction_hint")
def duct_direction_hint(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    floors = {f.tag: f for f in ctx.model.floors}
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay" or duct.floor_ref not in floors:
            continue
        if not is_parallel_to_floor(list(duct.path), floors[duct.floor_ref]):
            out.append(_advisory_fail(
                "mep.duct_direction_hint",
                f"duct {duct.tag} runs across joists in JOIST_BAY routing — "
                "route across joists in a soffit or chase", (duct.tag,),
            ))
    return out


def _storey_is_conditioned_here(ctx: CheckContext, storey_tag: str) -> bool:
    from typehaus.energy import _storey_is_conditioned

    return _storey_is_conditioned(ctx.plan, storey_tag)


def _heating_zones(ctx: CheckContext) -> list[tuple[str, frozenset[str], object]]:
    """Partition the conditioned storeys among the capacity-rated equipment types.

    A type whose name calls out storey tags (catlin's ``... basement zone)`` minisplit)
    claims those storeys; the remaining conditioned storeys go to the type that names
    none of them (catlin's upstairs unit → main + second + attic). The unconditioned
    garage never enters a zone — same scoping as the block load itself.
    """
    conditioned = [s.tag for s in ctx.plan.storeys if _storey_is_conditioned_here(ctx, s.tag)]
    rated = [eq for eq in ctx.plan.library.equipment_types
             if eq.heating_capacity_btuh is not None
             or eq.heating_capacity_at_design_btuh is not None]
    named: list[tuple[object, frozenset[str]]] = []
    unnamed: list[object] = []
    for eq in rated:
        claims = frozenset(tag for tag in conditioned if tag in eq.name.lower())
        (named.append((eq, claims)) if claims else unnamed.append(eq))
    claimed = frozenset().union(*(c for _, c in named)) if named else frozenset()
    remainder = frozenset(t for t in conditioned if t not in claimed)
    zones = [(f"{'+'.join(sorted(claims))} zone ({eq.tag})", claims, eq)
             for eq, claims in named]
    if len(unnamed) == 1 and remainder:
        # One default heater takes everything unclaimed.
        eq = unnamed[0]
        zones.append((f"{'+'.join(sorted(remainder))} zone ({eq.tag})", remainder, eq))
    else:
        # Zero storeys left, or several heaters with no named storeys: ambiguous —
        # reported by the caller as UNKNOWN rather than split by guesswork.
        zones.extend((f"unassigned zone ({eq.tag})", frozenset(), eq) for eq in unnamed)
    return zones


@check(Tier.ADVISORY, "mep.heating_capacity")
def heating_capacity(ctx: CheckContext) -> list[Finding]:
    """Per-zone UA block load at design temp vs the zone heater's at-design capacity.

    Only the equipment types that carry an authored ``heating_capacity*`` rating count as
    zone heat sources. Radiant floor mats (12 W/ft2 surface tempering), the electric
    fireplace, and the garage unit heater are supplemental by design (plan/circuits.py)
    and are excluded — none of them is sized to carry a room, and the garage is
    unconditioned anyway. Nothing here is a Manual J: it reuses ``estimate_block_load``
    with a storey filter, and missing inputs stay UNKNOWN, never estimated.
    """
    from typehaus.energy import estimate_block_load

    cid = "mep.heating_capacity"
    zones = _heating_zones(ctx)
    if not zones:
        return [_unknown(cid, "no equipment type carries a heating_capacity_btuh / "
                              "heating_capacity_at_design_btuh rating")]
    seen: set[str] = set()
    out: list[Finding] = []
    for zone_name, storeys, eq in zones:
        if not storeys or storeys & seen:
            out.append(_unknown(
                cid, f"{eq.tag}: zone storeys ambiguous — could not partition the "
                     "conditioned storeys among the rated heaters", (eq.tag,)))
            continue
        seen |= storeys
        report = estimate_block_load(ctx.model, ctx.preferences, storeys=storeys)
        load = report.heating_load_btu_per_hour
        capacity = eq.heating_capacity_at_design_btuh
        if capacity is None:
            out.append(_unknown(
                cid, f"{zone_name}: load {load:,.0f} Btu/h at design, but {eq.tag} has "
                     "no heating_capacity_at_design_btuh", (eq.tag,)))
            continue
        margin = capacity - load
        detail = (f"{zone_name}: block load {load:,.0f} Btu/h at design vs "
                  f"{capacity:,.0f} Btu/h at-design capacity "
                  f"(margin {margin:+,.0f} Btu/h; radiant/fireplace/garage heater "
                  "excluded as supplemental)")
        if report.unknown_inputs:
            out.append(_unknown(
                cid, f"{detail}; block-load inputs missing: "
                     + ", ".join(report.unknown_inputs), (eq.tag,)))
        elif margin >= 0:
            out.append(_pass(cid, detail, (eq.tag,)))
        else:
            out.append(_advisory_fail(cid, detail + " — undersized at design temp",
                                      (eq.tag,)))
    return out

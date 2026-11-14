"""Underground raceways, NEC 2026 300.7 and 300.8(A)(3): cover, protection, seals, corrosion.

``mep.conduit_burial`` grades Table 300.7(A) (``model/burial.py``) against every authored run
that lies in earth or under a building (``resolve/conduit_reaches.py``). Cover is Note 1: the
top of the run to the top of the slab over it, else of the local grade. The row is "all
locations" unless a slab over it is 4 in. thick or more AND extends 6 in. past the run's sides
(then the slab row); the slab row also needs "no vehicular traffic", which the model does not
carry, so the finding says it is assumed. Columns: the method's (EMT and PVC are Column 3),
plus Column 4 where the run's circuit is 120 V, 20 A or less, with GFCI (Note 4, shallowest).

``electrical.underground_raceway`` reads the rest of 300.7 and 300.8(A)(3) where the model
holds the data, and says UNKNOWN where it does not (conductor insulation, seal products, EMT
corrosion protection, PVC schedule).

**ADVISORY tier, never a permit gate.** Grade is a design elevation, not a survey, so a
shortfall reports as ``Result.ADVISORY`` with the numbers, for the owner to decide.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.burial import (
    UNDER_SLAB_EDGE_IN,
    UNDER_SLAB_MIN_THICKNESS_IN,
    BurialLocation,
    circuit_columns,
    shallowest_in,
)
from typehaus.model.nec import NEC, cite
from typehaus.resolve.conduit_reaches import Sample, build_site, samples

BURIAL_CID = "mep.conduit_burial"
UNDERGROUND_CID = "electrical.underground_raceway"
_IN = 0.0254
_CACHE: dict[int, tuple[object, dict]] = {}


def reaches(model) -> dict[str, list[Sample]]:
    """``{run tag: samples}`` for every authored, elevation-placed run; memoised per model."""
    held = _CACHE.get(id(model))
    if held is not None and held[0] is model:
        return held[1]
    site = build_site(model)
    result = {run.tag: samples(model, run, site) for run in model.conduits
              if run.derived is None and run.z_m is not None}
    _CACHE.clear()
    _CACHE[id(model)] = (model, result)
    return result


def _power(run) -> bool:
    """Article 300 excludes Class 2, communications and the like (300.1(B))."""
    return run.service is None or str(run.service).startswith("power")


def _length_in(group: list[Sample]) -> float:
    return len(group) * 3.0  # one sample per 3 in. along the run


def _circuit_columns(ctx: CheckContext, run):
    """Columns from the run's circuits (or its end device's), and a note on the basis."""
    tags = list(run.circuits)
    if not tags:
        for ref in (run.to_ref, run.from_ref):
            element = ctx.plan.by_tag(ref) if ref else None
            if getattr(element, "circuit", None):
                tags.append(element.circuit)
                break
    circuits = [c for c in ctx.plan.library.circuits if c.tag in tags]
    if run.service is None or not circuits:
        why = "a spare carries no circuit" if run.service is None else "no circuit is named"
        return circuit_columns(run.material, volts=None, amps=None, gfci=False), why
    ok = all(c.poles == 1 and c.breaker_amps <= 20 and c.gfci for c in circuits)
    volts, amps = (120, 20) if ok else (240, 99)
    return (circuit_columns(run.material, volts=volts, amps=amps, gfci=ok),
            f"circuit {', '.join(sorted(tags))}")


def _location(group: list[Sample]) -> tuple[BurialLocation, str]:
    first = group[0]
    if first.surface_tag is None:
        return BurialLocation.ALL_OTHER, "under open grade"
    edges = [s.slab_edge_clear_m for s in group if s.slab_edge_clear_m is not None]
    edge_in = min(edges) / _IN if edges else None
    thick = first.slab_thickness_in or 0.0
    over = f"under slab {first.surface_tag} ({thick:.0f} in.)"
    if thick + 1e-6 < UNDER_SLAB_MIN_THICKNESS_IN:
        return BurialLocation.ALL_OTHER, f"{over}, thinner than the 4 in. the slab row needs"
    if edge_in is None or edge_in + 1e-6 < UNDER_SLAB_EDGE_IN:
        have = "unknown" if edge_in is None else f"{max(edge_in, 0):.1f} in."
        return (BurialLocation.ALL_OTHER,
                f"{over}, but its edge clears the run by {have}, not the {UNDER_SLAB_EDGE_IN:.0f} "
                "in. the slab row needs")
    return (BurialLocation.UNDER_SLAB,
            f"{over}, edge {edge_in:.1f} in. clear (no vehicles assumed: not modelled)")


@check(Tier.ADVISORY, BURIAL_CID)
def conduit_burial(ctx: CheckContext) -> list[Finding]:
    """Cover over every run in earth against Table 300.7(A); under a building 300.7(C)."""
    code = cite(NEC.BURIAL_COVER, NEC.UNDER_BUILDING) + f" ({NEC.BURIAL_TABLE})"
    by_tag = reaches(ctx.model)
    schematic = sorted(r.tag for r in ctx.model.conduits
                       if r.derived is None and r.z_m is None and _power(r))
    out: list[Finding] = []
    buried = 0
    for run in ctx.model.conduits:
        group = by_tag.get(run.tag, [])
        earth = [s for s in group if s.kind == "earth"]
        under = [s for s in group if s.kind == "under_building"]
        if not earth and not under:
            continue
        buried += 1
        out.extend(_grade_run(ctx, run, earth, under, code))
    out.extend(_cast_in_walls(ctx.model, by_tag, code))
    if schematic:
        out.append(unknown(BURIAL_CID, f"raceways {', '.join(schematic)} author no per-vertex "
                           "elevations, so whether any is buried is not graded",
                           tuple(schematic), code=code, fix="author ConduitRun.elevations"))
    if not buried and not schematic and not out:
        embedded = sorted({r.tag for r in ctx.model.conduits
                           if any(s.kind == "in_wall" for s in by_tag.get(r.tag, []))
                           and r.derived is None})
        return [not_applicable(BURIAL_CID, "every elevation-placed raceway lies indoors, in a "
                               "wall or in the open; none is in earth or under a slab",
                               tuple(embedded), code=code)]
    return out


def _cast_in_walls(model, by_tag, code) -> list[Finding]:
    """A run lying in a wall that stands outside every building is neither under a slab nor
    in earth; whether Table 300.7(A) reaches a raceway cast into a retaining wall is a
    reviewer's call, so it is reported and not graded."""
    out = []
    for run in model.conduits:
        group = by_tag.get(run.tag, [])
        walls = sorted({s.host for s in group if s.kind == "in_wall" and s.building is None})
        if walls and not any(s.kind == "earth" for s in group):
            out.append(unknown(BURIAL_CID, f"{run.tag} runs inside {', '.join(walls)}, a wall "
                               "outside every building: cast into concrete, not direct-buried, "
                               "so its cover is the wall's, not a Table 300.7(A) row",
                               (run.tag, *walls), code=code,
                               fix="confirm with the inspector that no table row applies"))
    return out


def _grade_run(ctx, run, earth, under, code) -> list[Finding]:
    columns, basis = _circuit_columns(ctx, run)
    findings: list[Finding] = []
    groups: dict[str | None, list[Sample]] = defaultdict(list)
    for s in earth:
        groups[s.surface_tag].append(s)
    parts, worst = [], None
    for _tag, group in sorted(groups.items(), key=lambda item: str(item[0])):
        location, reason = _location(group)
        need, column = shallowest_in(location, columns)
        have = min((s.surface_z - s.top) / _IN for s in group)
        ys = sorted(s.y / 0.3048 for s in group)
        parts.append(f"{reason}, {_length_in(group) / 12:.1f} ft from y={ys[0]:.1f}' to "
                     f"{ys[-1]:.1f}': cover {have:.1f} in. against {need:g} in. "
                     f"(row '{location.value}', Column {column.value})")
        short = need - have
        if short > 1e-6 and (worst is None or short > worst):
            worst = short
    if under:
        parts.append(f"{_length_in(under) / 12:.1f} ft under a building in a raceway "
                     f"(row 'under a building', 0 in.)")
    msg = f"{run.tag} ({run.material}, {basis}): " + "; ".join(parts)
    if worst is None:
        findings.append(passed(BURIAL_CID, msg, (run.tag,), code=code))
    else:
        findings.append(advisory(
            BURIAL_CID, "ADVISORY - " + msg + f" - up to {worst:.1f} in. shallow",
            (run.tag,), Result.ADVISORY, code=code,
            fix="lower the run, widen the slab 6 in. past it, or move it under the slab row"))
    return findings


def _emerges(group: list[Sample]) -> list[Sample]:
    """The top sample of each vertical leg that rises out of earth or from under a slab."""
    found = []
    for a, b in zip(group, group[1:], strict=False):
        if (a.vertical and b.vertical and a.kind in ("earth", "under_building")
                and b.kind in ("indoor", "open")):
            found.append(b)
    return found


@check(Tier.ADVISORY, UNDERGROUND_CID)
def underground_raceway(ctx: CheckContext) -> list[Finding]:
    """300.7(B) wet conductors, (D) emerging from grade, (G) seals, 300.8(A)(3) corrosion."""
    by_tag = reaches(ctx.model)
    runs = {r.tag: r for r in ctx.model.conduits}
    buried = {t: g for t, g in by_tag.items() if any(s.kind in ("earth", "under_building")
                                                     for s in g)}
    foundation = {w.tag for w in ctx.model.walls if w.is_foundation}
    cast = {t: g for t, g in by_tag.items()
            if any(s.kind == "in_wall" and s.host in foundation for s in g)}
    if not buried and not cast:
        return [not_applicable(UNDERGROUND_CID, "no elevation-placed raceway is in earth, under "
                               "a slab or in a foundation wall", code=cite(NEC.UNDERGROUND))]
    out: list[Finding] = []
    for tag, group in sorted(buried.items()):
        run = runs[tag]
        out.extend(_wet(run))
        out.extend(_seal(run))
        out.extend(_emergence(run, group))
    for tag in sorted(set(buried) | set(cast)):
        out.extend(_corrosion(runs[tag], tag in buried))
    return out


def _wet(run) -> list[Finding]:
    code = cite(NEC.UNDERGROUND_WET, "310.10(C)")
    if run.service is None:
        return [not_applicable(UNDERGROUND_CID, f"{run.tag} is a spare with no conductors, so "
                               "no wet-rating applies", (run.tag,), code=code)]
    return [unknown(UNDERGROUND_CID, f"{run.tag}: the inside of an underground raceway is a wet "
                    "location; the conductor insulation type is not modelled (wet-rated, e.g. "
                    "THWN-2, is required)", (run.tag,), code=code,
                    fix="specify the conductor type on the circuit schedule")]


def _seal(run) -> list[Finding]:
    code = cite(NEC.RACEWAY_SEALS)
    if run.service is None:
        return [passed(UNDERGROUND_CID, f"{run.tag} is a spare, capped by the model's own "
                       "convention (service None), so it is plugged as 300.7(G) asks for spare "
                       "raceways; the sealant product is a specification item",
                       (run.tag,), code=code)]
    return [unknown(UNDERGROUND_CID, f"{run.tag}: moisture could reach live parts through this "
                    "buried raceway; no seal at either end is modelled", (run.tag,), code=code,
                    fix="specify a sealant identified for the conductors at the building end")]


def _emergence(run, group: list[Sample]) -> list[Finding]:
    rises = _emerges(group)
    if not rises:
        return []
    code = cite(NEC.EMERGING_FROM_GRADE, NEC.UNDERGROUND_DAMAGE)
    top = rises[-1]
    where = f"rising at ({top.x / .3048:.1f}', {top.y / .3048:.1f}') inside {top.host}"
    base = (f"{run.tag} emerges from below the floor, {where}; it is a raceway, so 300.7(D)(1) "
            "(direct-buried conductors) does not apply, and a garage floor is treated as "
            "subject to physical damage under 300.7(D)(4)")
    if run.material == "emt":
        return [passed(UNDERGROUND_CID, base + ": EMT is on its list", (run.tag,), code=code)]
    if run.material == "pvc":
        return [unknown(UNDERGROUND_CID, base + ": PVC must be Schedule 80 there (352.10(K)) and "
                        "the model holds only 'pvc' (Schedule 40)", (run.tag,), code=code,
                        fix="author the PVC schedule")]
    return [advisory(UNDERGROUND_CID, "ADVISORY - " + base + f": {run.material} is not listed",
                     (run.tag,), Result.ADVISORY, code=code)]


def _corrosion(run, buried: bool) -> list[Finding]:
    if run.material != "emt":
        return []
    code = cite(NEC.CORROSION_IN_EARTH, NEC.EMT_CORROSION)
    how = "in earth" if buried else "cast into a foundation wall"
    return [unknown(UNDERGROUND_CID, f"{run.tag}: EMT {how}; 358.10(B)(1) allows galvanized or "
                    "stainless EMT there only with corrosion protection that is also approved "
                    "for the condition, and none is modelled (aluminium EMT needs approved "
                    "supplementary protection, 358.10(B)(2))",
                    (run.tag,), code=code,
                    fix="state the EMT's approved corrosion protection, or use IMC, RMC or PVC")]

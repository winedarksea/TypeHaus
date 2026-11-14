"""Raceway protection and temperature, NEC 2026 300.6 and 300.9(A).

``mep.raceway_physical_damage``: 300.6(A)(1)/(A)(2)/(D)/(F) ask for a 1 1/4 in. setback or a
1/16 in. steel plate wherever a cable or raceway passes through or runs along wood framing;
each carries an exception for EMT, RMC, IMC, rigid PVC and RTRC, so only ENT is graded. NM
cable is not drawn (only its derived 3/4 in. EMT sleeve is, decision #93), so what the
cable itself needs is outside this model. 300.6(E): a raceway under roof decking keeps 1 1/2 in.
from it, measured here to the roof plane (the decking underside is a little lower, so a pass
holds and a shortfall is conservative).

``mep.raceway_condensation``: 300.9(A) asks a raceway that runs from the interior to the
exterior of a building to be sealed against warm air circulating to the cold end. No seal is
modelled, so each such POWER raceway is UNKNOWN (data, Class 2 and the like are outside
Article 300 by 300.1(B)). 300.9(A)(2) onward is unread.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.mep.conduit_burial import reaches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite
from typehaus.resolve.pipe_sections import raceway_outside_diameter_m

DAMAGE_CID = "mep.raceway_physical_damage"
CONDENSATION_CID = "mep.raceway_condensation"
_IN = 0.0254
ROOF_DECK_CLEAR_IN = 1.5
_NEAR_ROOF_IN = 60.0  # only runs within 5 ft of a roof plane are worth a line


@check(Tier.ADVISORY, DAMAGE_CID)
def raceway_physical_damage(ctx: CheckContext) -> list[Finding]:
    """300.6(A)/(D)/(F) by material, and 300.6(E) against every roof plane."""
    runs = ctx.model.conduits
    if not runs:
        return [not_applicable(DAMAGE_CID, "this model draws no raceway",
                               code=cite(NEC.PHYSICAL_DAMAGE))]
    out = []
    exempt = sorted(r.tag for r in runs if r.material in ("emt", "pvc"))
    ent = sorted(r.tag for r in runs if r.material == "ent")
    code = cite(NEC.DAMAGE_BORED_HOLES, NEC.DAMAGE_PARALLEL_FRAMING, NEC.DAMAGE_SHALLOW_GROOVES)
    out.append(passed(DAMAGE_CID, f"{len(exempt)} EMT and PVC raceways are excepted from the "
                      "steel-plate and 1 1/4 in. rules (Exception No. 1 of 300.6(A)(1), (A)(2), "
                      "(D) and (F)); NM cable itself is not drawn, only its EMT sleeve",
                      tuple(exempt[:12]), code=code))
    if ent:
        out.append(unknown(DAMAGE_CID, f"ENT raceways {', '.join(ent)} are not on the exception "
                           "lists: through or along wood framing they keep 1 1/4 in. from the "
                           "edge or take a 1/16 in. steel plate, and the model does not say "
                           "which framing they touch", tuple(ent), code=code,
                           fix="check each lead's route against the studs and joists"))
    out.extend(_roof_decking(ctx))
    return out


def _roof_decking(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.roof_geometry import roof_height_at

    code = cite(NEC.DAMAGE_ROOF_DECKING)
    by_tag = reaches(ctx.model)
    roofs = [(r, Polygon(r.footprint)) for r in ctx.model.roofs if len(r.footprint) >= 3]
    near: dict[str, float] = {}
    for run in ctx.model.conduits:
        if run.derived is not None or run.tag not in by_tag or not _is_power(run):
            continue
        radius = raceway_outside_diameter_m(run.trade_size_m, run.material) / 2
        for s in by_tag[run.tag]:
            for roof, shape in roofs:
                if shape.contains(Point(s.x, s.y)):
                    gap = (roof_height_at(roof, (s.x, s.y)) - (s.z + radius)) / _IN
                    if 0 <= gap < _NEAR_ROOF_IN:
                        near[run.tag] = min(near.get(run.tag, gap), gap)
    if not near:
        return [not_applicable(DAMAGE_CID, "no elevation-placed raceway comes within 5 ft of a "
                               "roof plane, so none is under roof decking", code=code)]
    out = []
    for tag, gap in sorted(near.items()):
        msg = (f"{tag} is {gap:.1f} in. under the roof plane at its closest, against "
               f"{ROOF_DECK_CLEAR_IN} in. (to the plane; the decking underside is lower)")
        if gap >= ROOF_DECK_CLEAR_IN:
            out.append(passed(DAMAGE_CID, msg, (tag,), code=code))
        else:
            out.append(advisory(DAMAGE_CID, "ADVISORY - " + msg, (tag,), Result.ADVISORY,
                                code=code, fix="lower the raceway or box it in concrete"))
    return out


def _is_power(run) -> bool:
    return run.service is None or str(run.service).startswith("power")


@check(Tier.ADVISORY, CONDENSATION_CID)
def raceway_condensation(ctx: CheckContext) -> list[Finding]:
    """A power raceway from a building's interior to its exterior, or to another building."""
    code = cite(NEC.RACEWAY_CONDENSATION)
    by_tag = reaches(ctx.model)
    crossing = []
    for run in ctx.model.conduits:
        group = by_tag.get(run.tag, [])
        if run.derived is not None or not group or not _is_power(run):
            continue
        indoors = {s.host for s in group if s.kind in ("indoor", "under_building")}
        # A wall outside every building (a court retaining wall) is exterior too.
        outdoors = any(s.kind in ("earth", "open") or (s.kind == "in_wall" and s.building is None)
                       for s in group)
        if indoors and (outdoors or len(indoors) > 1):
            crossing.append((run, sorted(indoors), outdoors))
    if not crossing:
        return [not_applicable(CONDENSATION_CID, "no elevation-placed power raceway passes "
                               "between the interior of a building and the exterior or another "
                               "building", code=code)]
    return [unknown(
        CONDENSATION_CID,
        f"{run.tag} passes from {', '.join(hosts)} "
        f"{'through the weather' if outdoors else 'into another building'}; the conduit "
        "or sleeve is not modelled with a seal against warm air reaching its cold end "
        "(300.9(A)(1))", (run.tag,), code=code,
        fix="specify a sealant or seal fitting at the warm end") for run, hosts, outdoors
        in crossing]

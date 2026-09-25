"""Does a body of soakaway stone hold the design snowmelt that reaches it?

One finding per body of stone with a flood course in it (``FootingBedding.soakaway_depth``).
Storage is the course's voids plus what the soil takes over a slow melt; demand is the ground
snow load, as water, off every area drain's stated catchment that discharges into the body.

Snowmelt governs a below-grade court, not the design rain: the court's grate is frozen when
the rain would matter, and when it thaws the water arrives over days. That is why the soil is
credited for ``DESIGN_MELT_HOURS`` — a slow-melt credit, not a storm one. Oracle:
``houses/catlin/notes/court_soakaway_storage.md``.

ADVISORY: the rate is usually presumed from a soil class, and a soils report closes it.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.checks._authoring import advisory, not_applicable
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.stormwater import AreaDrain
from typehaus.model.structure import FootingBedding
from typehaus.resolve.drainage_network import EdgeKind, build_network, stone_bodies
from typehaus.resolve.overlay import union_all

#: Hours of infiltration credited against a melt. A melt is slow — the same 48 h the MN
#: Stormwater Manual gives a basin to drain — so the soil is counted over it; a storm gets
#: no such credit and is not what this grades.
DESIGN_MELT_HOURS = 48.0
#: Water, lb/cf: a snow load in psf over this is a depth of water in feet.
WATER_PCF = 62.4
_IN = 0.0254
_FT = 0.3048
_CF = _FT ** 3


def _poly(ring):
    return Polygon(ring).buffer(0)


def _course(members) -> tuple[float, float, list[str]]:
    """``(void volume m³, bottom area m², unstated)`` — laps between beds counted once."""
    counted = Polygon()
    voids = 0.0
    unstated: list[str] = []
    for bed in sorted(members, key=lambda b: b.tag):
        piece = _poly(bed.outline).difference(counted)
        counted = union_all([counted, _poly(bed.outline)])
        if bed.void_ratio is None:
            unstated.append(f"{bed.tag} void_ratio")
            continue
        voids += piece.area * (bed.z0_m - bed.stone_z0_m) * bed.void_ratio
    return voids, counted.area, unstated


def _infiltration_m3(members) -> tuple[float, list[str]]:
    counted = Polygon()
    total = 0.0
    unstated: list[str] = []
    for bed in sorted(members, key=lambda b: b.tag):
        piece = _poly(bed.outline).difference(counted)
        counted = union_all([counted, _poly(bed.outline)])
        if bed.infiltration_in_per_hr is None:
            unstated.append(f"{bed.tag} infiltration_in_per_hr")
            continue
        total += piece.area * bed.infiltration_in_per_hr * _IN * DESIGN_MELT_HOURS
    return total, unstated


def _catchment_m2(ctx: CheckContext, body: frozenset[str]) -> tuple[float, list[str]]:
    network = build_network(ctx.model.plan)
    drains = {e.tag: e for e in ctx.model.plan.all_elements() if isinstance(e, AreaDrain)}
    feeding = sorted(e.source for e in network.edges
                     if e.kind is EdgeKind.PRIMARY and e.source in drains and e.target in body)
    area = sum(_poly([p.xy_m for p in drains[t].catchment]).area
               for t in feeding if len(drains[t].catchment) >= 3)
    return area, [t for t in feeding if len(drains[t].catchment) >= 3]


@check(Tier.ADVISORY, "drainage.soakaway_storage")
def soakaway_storage(ctx: CheckContext) -> list[Finding]:
    """The course's voids plus a slow melt's infiltration hold the design snowmelt."""
    cid = "drainage.soakaway_storage"
    beds = {b.tag: b for b in ctx.model.footing_beddings}
    if not any(b.soakaway_z0_m is not None for b in beds.values()):
        return [not_applicable(cid, "no bedding carries a soakaway course")]
    bodies = stone_bodies(ctx.model)
    seen: set[frozenset[str]] = set()
    out: list[Finding] = []
    for tag, bed in sorted(beds.items()):
        if bed.soakaway_z0_m is None:
            continue
        body = bodies.get(tag, frozenset({tag}))
        if body in seen:
            continue
        seen.add(body)
        out.extend(_grade_body(ctx, body, [beds[t] for t in sorted(body) if t in beds]))
    return out


def _grade_body(ctx: CheckContext, body: frozenset[str], members) -> list[Finding]:
    cid = "drainage.soakaway_storage"
    tags = tuple(sorted(body))
    course = [b for b in members if b.soakaway_z0_m is not None]
    voids, bottom, unstated = _course(course)
    soaked, rate_unstated = _infiltration_m3(course)
    unstated += rate_unstated
    area, feeders = _catchment_m2(ctx, body)
    psf = ctx.model.plan.project.site.ground_snow_load_psf
    if not feeders:
        unstated.append("a catchment on any area drain discharging here")
    if psf is None:
        unstated.append("Site.ground_snow_load_psf")
    out: list[Finding] = []
    if unstated:
        out.append(advisory(cid, f"UNKNOWN — soakaway storage under {', '.join(tags)} is "
                                 f"ungraded: nothing states {'; '.join(unstated)}",
                            tags, Result.UNKNOWN))
    else:
        demand = psf / WATER_PCF * _FT * area
        presumed = sorted({b.infiltration_basis for b in course}) != ["measured"]
        basis = " (presumed rate)" if presumed else ""
        msg = (f"{len(course)}-bed soakaway course holds {voids / _CF:.0f} cf of voids "
               f"({bottom / _FT ** 2:.0f} sf) + {soaked / _CF:.0f} cf infiltrated over "
               f"{DESIGN_MELT_HOURS:.0f} h{basis} = {(voids + soaked) / _CF:.0f} cf, against "
               f"{demand / _CF:.0f} cf of melt ({psf:g} psf over "
               f"{area / _FT ** 2:.0f} sf of catchment via {', '.join(feeders)})")
        result = Result.PASS if voids + soaked >= demand - 1e-9 else Result.FAIL
        out.append(advisory(cid, msg, tags, result))
    out.extend(_lip_finding(ctx, body, members))
    return out


def _lip_finding(ctx: CheckContext, body: frozenset[str], members) -> list[Finding]:
    """Does the body fill its drained frost section before its overflow engages?"""
    cid = "drainage.soakaway_storage"
    authored = {e.tag: e for e in ctx.model.plan.all_elements()
                if isinstance(e, FootingBedding) and e.tag in body}
    stated = sorted((e.overflow_invert.meters, tag) for tag, e in authored.items()
                    if e.overflow_invert is not None)
    if not stated:
        return []
    lip, tag = stated[0]
    drained = min(b.z0_m for b in members)
    tags = tuple(sorted(body))
    if lip > drained + 1e-6:
        return [advisory(
            cid, f"UNKNOWN — {tag}'s overflow lip at {lip / _IN:.1f}\" sits "
                 f"{(lip - drained) / _IN:.0f}\" above the drained section's bottom "
                 f"({drained / _IN:.1f}\"): the drained frost section floods before relief",
            tags, Result.UNKNOWN)]
    return [_pass(cid, f"{tag}'s overflow lip ({lip / _IN:.1f}\") engages at or below the "
                       f"drained section's bottom", tags)]

"""ADVISORY grounding reads (decision #123): coordinated SPDs, single-point entry and the
lightning-ready hooks. Owner design goals, not code: results never carry ERROR severity.
NFPA 780 rules: ``docs/nfpa-780-paraphrase.md`` (``model/nec.py`` ``NFPA780``).
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import advisory
from typehaus.checks.mep.electrical_grounding import (
    crossing_circuits,
    device_types,
    grounding,
    objects,
    root_building,
)
from typehaus.checks.mep.electrical_grounding_bonds import (
    entering_data,
    ibts,
    service_spds,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, NFPA780, cite

SPD_CID = "grounding.spd_coordination"
ENTRY_CID = "grounding.single_point_entry"
LPS_CID = "grounding.lightning_ready"
_FT = 0.3048
_IN = 0.0254
#: A PV DC SPD counts as at its box within this plan distance.
_BESIDE_M = 2.0
#: Power and data enter within this distance of the IBT (owner's stated goal).
ENTRY_REACH_M = 10 * _FT
_TRANSITION_M = 18 * _IN  # NFPA 780 4.2.2.3.1: no Al within 18 in of earth


def _f(cid: str, result: Result, msg: str, tags=(), code=None, fix=None) -> Finding:
    return advisory(cid, msg, tuple(tags), result, code=code, fix=fix)


@check(Tier.ADVISORY, SPD_CID)
def spd_coordination(ctx: CheckContext) -> list[Finding]:
    """SPDs at the service, at each box on the PV DC run, and in each fed outbuilding."""
    code = f"{cite(NEC.SERVICE_SPD)}; {NFPA780.SURGE}"
    g = grounding(ctx)
    out: list[Finding] = []
    if g.root is None:
        out.append(_f(SPD_CID, Result.UNKNOWN, "no service disconnect is modeled", code=code))
    elif found := service_spds(ctx, g.root):
        out.append(_f(SPD_CID, Result.PASS, f"service SPD at {g.root}: {', '.join(found)}",
                      found, code))
    else:
        out.append(_f(SPD_CID, Result.FAIL, f"no SPD at the service {g.root}", (g.root,), code))
    out.extend(_dc_chain(ctx, code))
    out.extend(_outbuildings(ctx, code, g.standard))
    return out


def _dc_chain(ctx: CheckContext, code: str) -> list[Finding]:
    runs = [r for r in ctx.model.conduits if r.service == "power_dc"]
    if not runs:
        return []
    out = []
    bare = sorted(r.tag for r in runs if r.material != "emt")
    if bare:
        out.append(_f(SPD_CID, Result.FAIL, f"PV DC runs not in EMT: {', '.join(bare)}", bare,
                      code, fix="run the DC circuit in continuous EMT, box to inverter"))
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    run_tags = {r.tag for r in runs}
    for run in runs:
        for ref in (run.from_ref, run.to_ref):
            if ref:
                parent[find(ref)] = find(run.tag)
        find(run.tag)
    if len({find(x) for x in parent}) > 1:
        out.append(_f(SPD_CID, Result.FAIL, "the PV DC runs are not one continuous chain",
                      sorted(r.tag for r in runs), code))
    objs, types = objects(ctx), device_types(ctx)
    pv_spds = [o for o in ctx.model.canvas_objects
               if getattr(types.get(o.type_ref or ""), "spd_class", None) == "pv_dc"]
    for end in sorted(set(parent) - run_tags):
        obj = objs.get(end)
        if obj is None:
            out.append(_f(SPD_CID, Result.UNKNOWN, f"DC box {end} has no position", (end,),
                          code))
            continue
        near = [s.tag for s in pv_spds if s.storey == obj.storey
                and math.dist(s.position, obj.position) <= _BESIDE_M]
        if near:
            out.append(_f(SPD_CID, Result.PASS, f"PV DC SPD at {end}: {', '.join(near)}",
                          (end, *near), code))
        else:
            out.append(_f(SPD_CID, Result.UNKNOWN, f"no pv_dc SPD beside DC box {end}; a "
                          "built-in SPD is not modeled", (end,), code,
                          fix="place a pv_dc SPD beside it"))
    return out


def _outbuildings(ctx: CheckContext, code: str, standard) -> list[Finding]:
    types = device_types(ctx)
    out = []
    wanted = getattr(standard, "outbuilding_spds", True)
    for bldg, circuits in sorted(crossing_circuits(ctx).items()):
        if len(circuits) <= 1:
            continue
        if not wanted:
            out.append(_f(SPD_CID, Result.PASS, f"{bldg} (fed by {len(circuits)} circuits): the "
                          "owner declines an outbuilding SPD (GroundingStandard.outbuilding_spds"
                          f"=False), a goal and not a {NEC.SERVICE_SPD} requirement", (), code))
            continue
        found = sorted(o.tag for o in ctx.model.canvas_objects
                       if ctx.plan.building_of(o.storey) == bldg
                       and getattr(types.get(o.type_ref or ""), "spd_class", None) in ("1", "2"))
        result = Result.PASS if found else Result.FAIL
        said = f"SPD in {bldg}: {', '.join(found)}" if found else \
            f"{bldg} is fed by {len(circuits)} circuits and has no SPD"
        out.append(_f(SPD_CID, result, said, found, code))
    return out


@check(Tier.ADVISORY, ENTRY_CID)
def single_point_entry(ctx: CheckContext) -> list[Finding]:
    """Power and data enter on one wall, each within 10 ft of the IBT."""
    code = cite(NEC.INTERSYSTEM_BONDING)
    entries = entering_data(ctx)
    if not entries:
        return [_f(ENTRY_CID, Result.NOT_APPLICABLE, "no data raceway enters from outside",
                   code=code)]
    g, objs = grounding(ctx), objects(ctx)
    meter = objs.get(g.root or "")
    ibt = next((objs[t] for t in ibts(ctx) if t in g.root_system and t in objs), None)
    if meter is None or ibt is None:
        return [_f(ENTRY_CID, Result.UNKNOWN, "the service or a bonded IBT is not located",
                   code=code)]
    out = []
    for run, end in entries:
        data = objs[end]
        problems = []
        if meter.attachment_wall is None or data.attachment_wall is None:
            problems.append("an entry is not wall-hosted")
        elif meter.attachment_wall != data.attachment_wall:
            problems.append(f"power enters {meter.attachment_wall}, data "
                            f"{data.attachment_wall}")
        for obj in (meter, data):
            gap = math.dist(obj.position, ibt.position)
            if gap > ENTRY_REACH_M:
                problems.append(f"{obj.tag} is {gap / _FT:.1f} ft from IBT {ibt.tag}")
        tags = (meter.tag, end, ibt.tag, run.tag)
        if problems:
            out.append(_f(ENTRY_CID, Result.FAIL, "; ".join(problems), tags, code,
                          fix="bring power and data in on one wall beside the IBT"))
        else:
            out.append(_f(ENTRY_CID, Result.PASS, f"{meter.tag} and {end} enter "
                          f"{meter.attachment_wall} within 10 ft of IBT {ibt.tag}", tags, code))
    return out


@check(Tier.ADVISORY, LPS_CID)
def lightning_ready(ctx: CheckContext) -> list[Finding]:
    """Two terminals at opposite corners on one counterpoise with the GES; Al down-leads."""
    code = (f"{NFPA780.GROUND_RING} / {NFPA780.COMMON_GROUNDING} / "
            f"{NFPA780.DISSIMILAR_METALS}")
    g = grounding(ctx)
    terms = [e for e in g.electrodes if e.use == "lps_terminal"]
    leads = [b for b in g.bonds if b.role == "down_lead"]
    if not terms and not leads:
        return [_f(LPS_CID, Result.NOT_APPLICABLE, "no lightning hooks are authored",
                   code=code)]
    out = [_corners(ctx, g, terms, code)]
    std = g.standard
    rise = (std.transition_min_height.meters
            if std is not None and std.transition_min_height is not None else _TRANSITION_M)
    from typehaus.resolve.site_earth import site_grade_elevation_m

    grade = site_grade_elevation_m(ctx.model)
    for lead in sorted(leads, key=lambda b: b.tag):
        if not lead.path:
            out.append(_f(LPS_CID, Result.UNKNOWN, f"{lead.tag} is not located", (lead.tag,),
                          code))
            continue
        low = min(p[2] for p in lead.path) - grade
        high = max(p[2] for p in lead.path) - grade
        if lead.material == "aluminum" and low + 1e-4 < rise:
            out.append(_f(LPS_CID, Result.FAIL, f"aluminium {lead.tag} comes to {low / _IN:.0f} "
                          f"in above grade; the Cu transition stays {rise / _IN:.0f} in up",
                          (lead.tag,), code))
        elif lead.material == "copper" and high > rise + _IN:
            out.append(_f(LPS_CID, Result.FAIL, f"copper {lead.tag} runs above grade on the "
                          "metal skin; use aluminium there", (lead.tag,), code))
        else:
            out.append(_f(LPS_CID, Result.PASS, f"{lead.material} {lead.tag}: "
                          f"{low / _IN:.0f} to {high / _IN:.0f} in from grade", (lead.tag,),
                          code))
    return out


def _corners(ctx: CheckContext, g, terms: list, code: str) -> Finding:
    tags = tuple(e.tag for e in terms)
    if len(terms) < 2:
        return _f(LPS_CID, Result.FAIL, f"{len(terms)} lightning terminal(s); two at opposite "
                  "corners are the goal", tags, code)
    if any(e.tag not in g.root_system for e in terms):
        return _f(LPS_CID, Result.FAIL, "the terminals are not on one counterpoise with the "
                  "service's electrode system", tags, code)
    from typehaus.resolve.room_lookup import axis_ring

    home = root_building(ctx, g)
    pts = [p for r in ctx.model.rooms if ctx.plan.building_of(r.storey) == home
           for p in axis_ring(r)]
    if not pts:
        return _f(LPS_CID, Result.UNKNOWN, "the building has no rooms to find corners by", tags,
                  code)
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
    cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
    quad = {e.tag: (e.xy[0] > cx, e.xy[1] > cy) for e in terms}
    diagonal = any(qa[0] != qb[0] and qa[1] != qb[1]
                   for a, qa in quad.items() for b, qb in quad.items() if a < b)
    if not diagonal:
        return _f(LPS_CID, Result.FAIL, "no two terminals sit at diagonally opposite corners",
                  tags, code)
    return _f(LPS_CID, Result.PASS, f"terminals {', '.join(tags)} at opposite corners on the "
              "service's counterpoise", tags, code)

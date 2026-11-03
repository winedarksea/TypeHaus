"""CODE-tier electrical rules — a panel's working space and dedicated space, NEC 110.26.

110.26(A): in front of the panel, 36" deep (Condition 1, 120/240 V), max(30", panel
width) wide and floor to max(6'-6", panel top) high, clear of everything. The panel need
not be centred in that width, so the window slides along the face in 1" steps; any clear
position passes. Door swings are not graded: 110.26 does not forbid a door over the
working space at a dwelling panel, only the 110.26(C) egress rules for large equipment.

110.26(E)(1): ``resolve/panel_space.dedicated_spaces`` (the router's hard prism too). A pipe
or duct in it fails; conduit is the installation and is allowed.
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.checks.integrity.clear_zones import obstruction_prisms, potential_run_footprints
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, by_result
from typehaus.resolve.mep_envelopes import Prism, envelopes
from typehaus.resolve.overlay import union_all
from typehaus.resolve.panel_space import dedicated_spaces, floor_and_top, panels

_WORK, _DEDICATED = "electrical.panel_working_space", "electrical.panel_dedicated_space"
_IN = 0.0254
_DEPTH_M, _WIDTH_M, _HEIGHT_M = 36 * _IN, 30 * _IN, 78 * _IN
_STEP_M = 1 * _IN
_SHRINK_M = 0.001  # contact is not intrusion


def _panels(ctx: CheckContext) -> list:
    return panels(ctx.plan)


def _wall_prisms(ctx: CheckContext) -> list[Prism]:
    out = []
    for wall in ctx.model.walls:
        rings = [Polygon(layer.polygon) for layer in wall.layers if len(layer.polygon) >= 3]
        if rings:
            out.append(Prism(wall.tag, "wall", union_all(rings), wall.z0_m, wall.z1_m))
    return out


def _hits(zone: Polygon, z0: float, z1: float, prism: Prism) -> bool:
    return (min(z1, prism.z1_m) - max(z0, prism.z0_m) > _SHRINK_M
            and prism.footprint.is_valid and zone.intersects(prism.footprint)
            and zone.intersection(prism.footprint).area > 0)


def _frame(body) -> tuple[tuple[float, float], tuple[float, float]]:
    """Along-face and outward (local ``-y``) unit vectors of a placed body."""
    a = math.radians(body.rotation_degrees)
    return (math.cos(a), math.sin(a)), (math.sin(a), -math.cos(a))


def _windows(body):
    """Every 110.26(A) window position as a shrunk plan polygon, in sliding order."""
    along, out = _frame(body)
    s = [px * along[0] + py * along[1] for px, py in body.footprint]
    f = max(px * out[0] + py * out[1] for px, py in body.footprint)
    lo, hi = min(s), max(s)
    width = max(_WIDTH_M, hi - lo)
    slack = width - (hi - lo)
    for i in range(math.ceil(slack / _STEP_M - 1e-9) + 1):
        a = hi - width + min(i * _STEP_M, slack)
        corners = [(a, f), (a + width, f), (a + width, f + _DEPTH_M), (a, f + _DEPTH_M)]
        yield Polygon([(u * along[0] + v * out[0], u * along[1] + v * out[1])
                       for u, v in corners]).buffer(-_SHRINK_M, join_style=2)


@check(Tier.CODE, _WORK)
def panel_working_space(ctx: CheckContext) -> list[Finding]:
    """NEC 110.26(A): a clear 36"-deep, 30"-wide, 6'-6"-high space in front of each panel."""
    code = "NEC 110.26(A)"
    panels = _panels(ctx)
    if not panels:
        return [by_result(_WORK, Result.NOT_APPLICABLE, "no panel in the plan", (), code)]
    bodies = {item.tag: item for item in ctx.model.canvas_objects}
    run_envelopes = envelopes(ctx.model)
    candidates = obstruction_prisms(ctx.model, run_envelopes) + _wall_prisms(ctx)
    potential = potential_run_footprints(ctx.model)
    gap_runs = [env.tag for env in run_envelopes if env.gaps and not env.prisms]
    out: list[Finding] = []
    for panel in panels:
        body = bodies.get(panel.tag)
        band = None if body is None else floor_and_top(panel, body)
        if body is None or band is None or len(body.footprint) < 3:
            out.append(by_result(_WORK, Result.UNKNOWN, f"{panel.tag}: no resolved body and "
                                 "mount elevation to place a working space on",
                                 (panel.tag,), code))
            continue
        floor, top = band
        z0, z1 = floor + _SHRINK_M, max(floor + _HEIGHT_M, top)
        skip = {panel.tag, body.attachment_wall}
        best: list[str] = []
        gaps: list[str] = []
        clear = False
        for zone in _windows(body):
            blocked = sorted({p.tag for p in candidates
                              if p.tag not in skip and _hits(zone, z0, z1, p)})
            if blocked:
                best = blocked if not best or len(blocked) < len(best) else best
                continue
            maybe = sorted(tag for tag in gap_runs
                           if potential.get(tag) is None or zone.intersects(potential[tag]))
            if not maybe:
                clear = True
                break
            gaps = gaps or maybe
        if clear:
            out.append(by_result(_WORK, Result.PASS, f"{panel.tag}: 36\" x 30\" working "
                                 f"space clear from the floor to {(z1 - floor) / _IN:.0f}\"",
                                 (panel.tag,), code))
        elif gaps:
            out.append(by_result(_WORK, Result.UNKNOWN, f"{panel.tag}: working space clear "
                                 f"of every resolved body, but run(s) {', '.join(gaps)} "
                                 "have no elevations to grade", (panel.tag, *gaps), code))
        else:
            out.append(by_result(_WORK, Result.FAIL, f"{panel.tag}: no 36\" x 30\" "
                                 f"working-space position is clear; the best is blocked by "
                                 f"{', '.join(best)}", (panel.tag, *best), code,
                                 fix="Move the obstruction out of the 36\"-deep space in "
                                 "front of the panel, or move the panel."))
    return out


@check(Tier.CODE, _DEDICATED)
def panel_dedicated_space(ctx: CheckContext) -> list[Finding]:
    """NEC 110.26(E)(1): no pipe or duct over a panel's footprint, up to 6 ft above it."""
    code = "NEC 110.26(E)(1)"
    panels = _panels(ctx)
    if not panels:
        return [by_result(_DEDICATED, Result.NOT_APPLICABLE, "no panel in the plan", (), code)]
    spaces = dedicated_spaces(ctx.model)
    run_envelopes = [env for env in envelopes(ctx.model) if env.kind != "conduit"]
    potential = potential_run_footprints(ctx.model)
    out: list[Finding] = []
    for panel in panels:
        space = spaces.get(panel.tag)
        if space is None:
            out.append(by_result(_DEDICATED, Result.UNKNOWN, f"{panel.tag}: no resolved "
                                 "body to project a dedicated space from", (panel.tag,), code))
            continue
        floor, z1 = space.floor_m, space.z1_m
        zone = Polygon(space.footprint).buffer(-_SHRINK_M, join_style=2)
        intruders = sorted({p.tag for env in run_envelopes for p in env.prisms
                            if _hits(zone, floor, z1, p)})
        gaps = sorted(env.tag for env in run_envelopes if env.gaps and not env.prisms
                      and (potential.get(env.tag) is None
                           or zone.intersects(potential[env.tag])))
        if intruders:
            out.append(by_result(_DEDICATED, Result.FAIL, f"{panel.tag}: "
                                 f"{', '.join(intruders)} pass through the dedicated space "
                                 f"over the panel ({(z1 - floor) / _IN:.0f}\" AFF)",
                                 (panel.tag, *intruders), code,
                                 fix="Reroute the pipe or duct clear of the panel's "
                                 "footprint, floor to structure."))
        elif gaps:
            out.append(by_result(_DEDICATED, Result.UNKNOWN, f"{panel.tag}: run(s) "
                                 f"{', '.join(gaps)} could cross the dedicated space but "
                                 "have no elevations", (panel.tag, *gaps), code))
        else:
            out.append(by_result(_DEDICATED, Result.PASS, f"{panel.tag}: no pipe or duct "
                                 f"over the panel up to {(z1 - floor) / _IN:.0f}\" AFF",
                                 (panel.tag,), code))
    return out

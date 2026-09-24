"""Does a pumped sump's water actually leave by the line it names?

``SumpPump.discharge`` names a receiver; ``discharge_line_ref`` names the ``PipeRun`` that
gets the water there. This grades the line: its system, that it leaves the pit, that it
lands on the receiver, that it does not re-rise after its high point (a trap that freezes),
that a check valve holds the column, and that a buried receiver shallower than frost has a
freeze relief. ADVISORY like the rest of site drainage. ``mep.pit_footing_clearance`` asks
the pit's other question: whether the hole it sits in cuts a footing.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks._authoring import advisory, not_applicable
from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.mep import Sump
from typehaus.model.trim import Downspout
from typehaus.resolve.drainage_network import DAYLIGHT

_IN = 0.0254
#: A line's end may land this far outside a leader's own radius — the wye's reach.
LEADER_SLACK_M = 6.0 * _IN
#: Rounding a line's profile may not count as a re-rise.
_RISE_TOL_M = 0.25 * _IN
#: Plan overlap below which a pit only touches a pour — faceting, not a cut. 1/4 sq in.
_SLIVER_M2 = 0.25 * _IN * _IN


def _pit(ctx: CheckContext, tag: str):
    return next((s for s in ctx.model.solids if s.tag == tag and s.category == "sump"), None)


@check(Tier.ADVISORY, "drainage.pump_discharge")
def pump_discharge(ctx: CheckContext) -> list[Finding]:
    """A pumped pit's line leaves the pit, lands on its receiver, and cannot back up."""
    cid = "drainage.pump_discharge"
    plan = ctx.model.plan
    pumps = [e for e in plan.all_elements() if isinstance(e, Sump) and e.pump is not None]
    if not pumps:
        return [not_applicable(cid, "no sump carries a pump")]
    runs = {r.tag: r for r in ctx.model.pipe_runs}
    out: list[Finding] = []
    for sump in pumps:
        pump = sump.pump
        receiver = (pump.discharge or "").strip()
        if (not receiver or receiver.lower() == DAYLIGHT) and pump.discharge_line_ref is None:
            continue
        if pump.discharge_line_ref is None:
            out.append(advisory(cid, f"UNKNOWN — {sump.tag}'s pump discharges to {receiver} "
                                     f"by no modelled line", (sump.tag,), Result.UNKNOWN))
            continue
        line = runs.get(pump.discharge_line_ref)
        if line is None:
            out.append(advisory(cid, f"{sump.tag}'s discharge line {pump.discharge_line_ref} "
                                     f"is not a resolved pipe run", (sump.tag,), Result.FAIL))
            continue
        out.extend(_grade_line(ctx, sump, line, plan.by_tag(receiver)))
    return out


def _grade_line(ctx: CheckContext, sump: Sump, line, receiver) -> list[Finding]:
    cid = "drainage.pump_discharge"
    tags = (sump.tag, line.tag)
    pump = sump.pump
    problems: list[str] = []
    if line.system != "sump_discharge":
        problems.append(f"it is a {line.system!r} run, not a sump_discharge line")
    z = list(line.z_m or ())
    pit = _pit(ctx, sump.tag)
    if pit is not None and line.path:
        shape = Polygon(pit.outline)
        if shape.distance(Point(line.path[0])) > 1e-3 or (
                z and not pit.z0_m - 1e-6 <= z[0] <= pit.z1_m + 0.5):
            problems.append(f"it does not start in {sump.tag}'s pit")
    if isinstance(receiver, Downspout) and line.path:
        problems.extend(_lands_on_leader(line, z, receiver))
    if z:
        high = z.index(max(z))
        if any(b > a + _RISE_TOL_M for a, b in zip(z[high:-1], z[high + 1:], strict=True)):
            problems.append("it re-rises after its high point, a trap that holds water")
    out = [advisory(cid, f"{sump.tag}'s line {line.tag}: {why}", tags, Result.FAIL)
           for why in problems]
    if not pump.check_valve:
        out.append(advisory(cid, f"{sump.tag}'s pump has no check valve: the column in "
                                 f"{line.tag} falls back into the pit", tags, Result.FAIL))
    out.extend(_freeze(ctx, sump, receiver, tags))
    if not out:
        out.append(_pass(cid, f"{sump.tag} pumps through {line.tag} to "
                              f"{pump.discharge}, check valve fitted", tags))
    return out


def _lands_on_leader(line, z, leader: Downspout) -> list[str]:
    end = Point(line.path[-1])
    radius = leader.diameter.meters / 2.0
    if end.distance(Point(leader.position.xy_m)) > radius + LEADER_SLACK_M:
        return [f"it ends off {leader.tag} in plan"]
    ext = leader.extension
    if z and ext is not None and not (ext.inlet_invert.meters - 1e-6 <= z[-1]
                                      <= leader.bottom_elevation.meters + 1e-6):
        return [f"its wye at {z[-1] / _IN:.1f}\" is off {leader.tag}'s extension riser "
                f"({ext.inlet_invert.meters / _IN:.1f}\" to "
                f"{leader.bottom_elevation.meters / _IN:.1f}\")"]
    return []


def _freeze(ctx: CheckContext, sump: Sump, receiver, tags) -> list[Finding]:
    """A buried receiver above frost freezes; without a relief the pump dead-heads."""
    cid = "drainage.pump_discharge"
    if not isinstance(receiver, Downspout) or receiver.extension is None:
        return []
    frost_in = getattr(ctx.profile, "frost_depth_in", None)
    grade = ctx.model.plan.project.site.grade
    if frost_in is None or grade is None:
        return []
    cover_in = (grade.meters - receiver.extension.inlet_invert.meters) / _IN
    if cover_in >= frost_in or sump.pump.freeze_relief:
        return []
    return [advisory(cid, f"UNKNOWN — {receiver.tag}'s extension is buried {cover_in:.0f}\" "
                          f"against a {frost_in:.0f}\" frost depth and {sump.tag}'s line has "
                          f"no freeze relief: a frozen receiver dead-heads the pump",
                     tags, Result.UNKNOWN)]


@check(Tier.INTEGRITY, "mep.pit_footing_clearance")
def pit_footing_clearance(ctx: CheckContext) -> list[Finding]:
    """A sump pit does not cut footing concrete: a clash, not a code rule.

    UPC 314.1's 45° influence line governs a trench running alongside a footing, which
    stays open while a pipe is laid and backfilled. A lined pit is a basin set in a hole the
    size of itself, so the rule is not applied to it. Only plan overlap beyond a sliver *and*
    overlapping z ranges FAIL. Drain tile, bedding and sub-slab solids are not footings, so
    tile under the pit (it drains into it) passes by construction.
    """
    cid = "mep.pit_footing_clearance"
    pits = [s for s in ctx.model.solids if s.category == "sump" and len(s.outline) >= 3]
    if not pits:
        return [not_applicable(cid, "no sump pit is modelled")]
    bearings = [(s, Polygon(s.outline)) for s in ctx.model.solids
                if s.category in ("footing", "pad") and len(s.outline) >= 3]
    out: list[Finding] = []
    for pit in pits:
        hole = Polygon(pit.outline)
        cut = [f"{footing.tag} ({hole.intersection(footprint).area / _IN ** 2:.1f} sq in)"
               for footing, footprint in sorted(bearings, key=lambda item: item[0].tag)
               if pit.z0_m < footing.z1_m - 1e-9 and footing.z0_m < pit.z1_m - 1e-9
               and hole.intersection(footprint).area > _SLIVER_M2]
        if not cut:
            out.append(_pass(cid, f"{pit.tag} cuts no footing concrete", (pit.tag,)))
            continue
        out.append(_fail(cid, f"{pit.tag} cuts footing concrete: {'; '.join(cut)} — move the pit "
                              f"clear of the pour", (pit.tag,)))
    return out

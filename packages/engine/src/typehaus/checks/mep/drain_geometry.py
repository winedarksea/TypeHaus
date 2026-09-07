"""Two facts about a drain's *shape* that nothing else in the engine grades.

``mep.drain_offset_geometry`` — a drop drawn as a slant. ``mep.drain_slope`` grades the
flattest segment of a run, which is the half of the question that governs whether water
moves; nothing looked at the steepest, so a leg falling nine and a half feet across four
feet of plan passed every rule in the file. There is no fitting that makes that shape.

``mep.fixture_drain_reach`` — whether a run that claims to serve a fixture gets anywhere
near it. ``serves`` is an authored claim, and it feeds ``accumulated_serves`` ->
``branch_load`` -> ``mep.pipe_sizing``, so an unverified one is silently sizing pipe.

Both live here rather than in ``plumbing_dwv.py``, which is 433 lines and cannot take
another sixty.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.plumbing_common import _M_TO_FT, VERTICAL_PLAN_FT
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN


@check(Tier.CODE, "mep.drain_offset_geometry")
def drain_offset_geometry(ctx: CheckContext) -> list[Finding]:
    """A sloped drain segment must be a fitting somebody can buy, not a drop drawn slanted.

    ``mep.drain_slope`` grades a run by its **flattest** segment, because that is the one
    where the water stops. Nothing graded the steepest, and the two failure modes are not
    the same thing: too flat is a drain that will not scour, too steep is a piece of
    geometry that does not correspond to any assembly of pipe and fittings. Catlin carried
    one of the latter — ``PR-A-STUBATH-DRAIN``'s second leg fell **114.5" over 4.16 ft of
    plan**, 27.5"/ft, a dog-leg standing in for a stack and a horizontal branch that had
    never been drawn as two things.

    **The test is a conjunction, and it has to be.** Neither term separates the defect from
    an ordinary route on its own:

    * *Slope alone* fails a legitimate 45-degree offset, which is exactly 12"/ft. Catlin's
      steepest honest segment is ``PR-M-DRYER-COND`` at 15.2"/ft — a condensate line making
      a short drop to a receptor, and a fitting that exists.
    * *Fall alone* fails a long branch at a steepish grade, where the total is large because
      the run is long and every foot of it is buildable.

    Together they say what is actually wrong: this segment is steeper than the steepest
    fitting on the truck **and** it descends further than any offset would. The defect
    cleared both by a factor of six. See ``MepPreferences.max_drain_offset_slope_in_per_ft``
    and ``max_drain_offset_fall_in`` for where the two numbers come from.

    True verticals are exempt — a stack has no slope, and the drop the fix authors is one.
    The exemption uses :data:`~typehaus.checks.mep.plumbing_common.VERTICAL_PLAN_FT`, the
    same tolerance ``mep.drain_slope`` skips a vertical on, lifted to a shared constant so
    the two cannot drift into disagreeing about which segments exist.

    CODE rather than ADVISORY: P3005.3 governs the shape of a drain's changes in direction,
    and a segment failing both terms here is not a fitting the code recognises. What the
    check does *not* claim is a fitting take-off — it grades the polyline, and a route that
    passes still has to be built out of real elbows.
    """
    cid = "mep.drain_offset_geometry"
    rules = ctx.preferences.mep
    graded = 0
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system != "drain" or run.z_m is None or len(run.z_m) != len(run.path):
            continue
        for index in range(len(run.path) - 1):
            a, b = run.path[index], run.path[index + 1]
            plan_ft = (((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5) * _M_TO_FT
            if plan_ft <= VERTICAL_PLAN_FT:
                continue  # a stack; it has no slope to be too steep
            graded += 1
            fall_in = (run.z_m[index] - run.z_m[index + 1]) / M_PER_IN
            if fall_in <= 0:
                continue  # level or backfall — mep.drain_slope's finding, not this one
            slope = fall_in / plan_ft
            if (slope <= rules.max_drain_offset_slope_in_per_ft
                    or fall_in <= rules.max_drain_offset_fall_in):
                continue
            out.append(_fail(
                cid,
                f"pipe run {run.tag} segment {index} falls {fall_in:.1f}\" over {plan_ft:.2f} "
                f"ft of plan — {slope:.1f}\"/ft, past the "
                f"{rules.max_drain_offset_slope_in_per_ft:.0f}\"/ft of a 45-degree fitting, "
                f"and further than the {rules.max_drain_offset_fall_in:.0f}\" any offset "
                "descends. This is a vertical drop and a sloped branch drawn as one diagonal",
                (run.tag,),
                fix="split the segment: repeat the plan vertex to author the drop (two "
                    "elevations at one point), then run the horizontal leg at its own grade. "
                    "The drop has to land high enough that the leg below it still holds "
                    "1/4\"/ft to its tie-in"))
    if not out:
        out.append(_pass(
            cid, f"{graded} sloped drain segment(s): none falls more than "
                 f"{rules.max_drain_offset_fall_in:.0f}\" at more than "
                 f"{rules.max_drain_offset_slope_in_per_ft:.0f}\"/ft — every change in "
                 "direction is a fitting that exists", ()))
    return out


def _closest_on_segment(a: tuple[float, float], b: tuple[float, float],
                        p: tuple[float, float]) -> tuple[float, float]:
    """``(distance from p to segment ab, parameter t in [0,1] of the closest point)``.

    Arithmetic rather than ``LineString.project``/``interpolate`` for the reason
    ``mep.trap_arm_length`` already documents: a drain point that lands exactly on the run —
    which is what a *correct* branch looks like — makes ``project`` warn about a NaN it then
    returns 0.0 for, on every build. This needs the parameter as well as the distance
    anyway, to read the run's elevation where it passes closest.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = dx * dx + dy * dy
    if span <= 0.0:
        return (((p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2) ** 0.5, 0.0)
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / span
    t = min(1.0, max(0.0, t))
    cx, cy = a[0] + t * dx, a[1] + t * dy
    return ((((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5), t)


#: How far below its own floor a run may sit and still count as reaching a fixture on it,
#: and how far above. Down: a fixture's waste leaves through the deck and the branch that
#: takes it hangs under that deck — catlin's main-floor fixtures meet their branches at the
#: basement ceiling, 1'-10" down, and its legitimate heads sit 1.6"-3" under their own decks.
#: So the band deliberately reaches the ceiling plane of the storey below, and no further.
#: Up: a trap arm rises a few inches off the floor, never a foot.
#:
#: Without a vertical gate the plan-only test is nonsense — a basement main passing under a
#: main-floor sink "reaches" it by forty inches of concrete.
_REACH_BELOW_FT = 2.0
_REACH_ABOVE_FT = 0.5


@check(Tier.ADVISORY, "mep.fixture_drain_reach")
def fixture_drain_reach(ctx: CheckContext) -> list[Finding]:
    """A drain run that names a fixture in ``serves`` has to get near it.

    ``serves`` is an authored claim and nothing tested it. It is not decoration: it feeds
    ``accumulated_serves`` -> ``branch_load`` -> ``mep.pipe_sizing``, so a fixture named on a
    run it does not touch is silently sizing pipe, and ``mep.trap_arm_length`` measures an
    arm to a vent for a fixture whose waste piping was never drawn.

    Catlin had nine of them, and the measurement is what makes the threshold defensible
    rather than tuned. Plan distance from each drained fixture's derived drain point to the
    nearest polyline of a run naming it came out **bimodal with a clean hole in the middle**:
    every fixture with a branch actually drawn to it measured 0"-8", and the nine without
    measured 15.6" and up (to 79.3"). Twelve inches sits in the hole with about 50% margin
    on each side. The whole second-storey bathroom group had stacks and no branch or trap-arm
    piping at all, which is why the suite bath's water closet read as undrained in the viewer.

    **Empty ``serves`` is a FAIL, not an UNKNOWN.** A fixture standing over nothing is
    positive evidence of a defect, not a gap in what the model can see — the model can see
    perfectly well that no run in it names this fixture.

    **The vertical gate is load-bearing.** Distance is measured in plan, so without it a
    basement main passing beneath a main-floor lavatory "reaches" it. A run counts only where
    it passes within :data:`_REACH_BELOW_FT` below and :data:`_REACH_ABOVE_FT` above the
    fixture's own storey datum; every legitimate head on catlin sits 1.6"-3" under its deck,
    comfortably inside.

    ADVISORY: no section says a ``serves`` tuple has to be true, because no section knows
    what a ``serves`` tuple is. It is a fact about the model's own consistency, and a FAIL
    at any severity breaks the 0-FAIL gate.
    """
    from typehaus.model.enums import Service
    from typehaus.resolve.mep import _expected_drain_point

    cid = "mep.fixture_drain_reach"
    rules = ctx.preferences.mep
    limit_m = rules.fixture_drain_reach_in * M_PER_IN
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    elevations = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        datum = elevations.get(storey.tag, 0.0)
        low = datum - _REACH_BELOW_FT / _M_TO_FT
        high = datum + _REACH_ABOVE_FT / _M_TO_FT
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.DRAIN not in fixture_type.needs:
                continue
            drain_point = _expected_drain_point(ctx.model, fixture.tag)
            if drain_point is None:
                # Word-for-word ``mep.trap_arm_length``'s branch: the two checks read the
                # same derivation and must never disagree about whether it resolved.
                out.append(_unknown(cid, f"fixture {fixture.tag} has no resolvable "
                                         "drain point", (fixture.tag,)))
                continue
            runs = [r for r in ctx.model.pipe_runs
                    if r.system == "drain" and fixture.tag in r.serves]
            if not runs:
                out.append(advisory(
                    cid, f"no drain run in this model names {fixture.tag} — nothing "
                         "drains it", (fixture.tag,), Result.FAIL,
                    fix="author the branch that drains it, and name the fixture in that "
                        "run's `serves`"))
                continue
            best: tuple[float, str] | None = None
            for run in runs:
                if len(run.path) < 2:
                    continue
                z = run.z_m if run.z_m and len(run.z_m) == len(run.path) else None
                for index in range(len(run.path) - 1):
                    a, b = run.path[index], run.path[index + 1]
                    distance, t = _closest_on_segment(a, b, drain_point)
                    if z is not None:
                        here = z[index] + (z[index + 1] - z[index]) * t
                        if not (low <= here <= high):
                            continue  # a different floor's pipe passing under this fixture
                    if best is None or distance < best[0]:
                        best = (distance, run.tag)
            if best is None:
                out.append(advisory(
                    cid,
                    f"the run(s) naming {fixture.tag} — {', '.join(r.tag for r in runs)} — "
                    f"never pass within {_REACH_BELOW_FT:.0f} ft below or "
                    f"{_REACH_ABOVE_FT * 12:.0f}\" above {storey.tag}'s datum, so none of "
                    "them is on this fixture's floor at all",
                    (fixture.tag, *(r.tag for r in runs)), Result.FAIL))
                continue
            gap_in = best[0] / M_PER_IN
            if best[0] <= limit_m + 1e-9:
                out.append(_pass(
                    cid, f"fixture {fixture.tag}'s drain point is {gap_in:.1f}\" from "
                         f"{best[1]}, which names it", (fixture.tag, best[1])))
            else:
                out.append(advisory(
                    cid,
                    f"fixture {fixture.tag}'s drain point is {gap_in:.1f}\" from the nearest "
                    f"pipe of {best[1]}, the closest run naming it — past the "
                    f"{rules.fixture_drain_reach_in:.0f}\" a branch and a trap arm can be "
                    "left undrawn. The `serves` claim is sizing that run's pipe either way",
                    (fixture.tag, best[1]), Result.FAIL,
                    fix="author the branch and trap arm this fixture actually needs, ending "
                        "on the run that serves it. Expect mep.trap_arm_length's limit to "
                        "DROP when it does: it takes the minimum diameter over the serving "
                        "runs, and a truthful 1 1/2\" arm is not the 3\" stack"))
    return out

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

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.mep.plumbing_common import _M_TO_FT, VERTICAL_PLAN_FT
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
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

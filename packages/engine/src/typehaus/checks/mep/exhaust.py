"""M1502 clothes-dryer exhaust.

Three independent failures, all common, all invisible without a rule: the duct runs too far
for the appliance to push lint through it, it joins another exhaust system, or it terminates
somewhere it will be pulled straight back in. The first is a length budget the code states
in feet and elbows; the other two are relationships between runs.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DuctSystem

# M1502.4.5.1: 35 feet of developed length from the connection to the termination, less
# 5 feet per 45-degree bend and 2.5 feet per 90-degree bend.
_MAX_DEVELOPED_FT = 35.0
_ELBOW_45_PENALTY_FT = 2.5
_ELBOW_90_PENALTY_FT = 5.0
# Below this turn, the polyline is following a wall, not making a fitting.
_MIN_TURN_DEGREES = 20.0


def _finding(cid, result, message, tags, code, fix=None) -> Finding:
    if result is Result.NOT_APPLICABLE:
        return not_applicable(cid, message, tags, code=code)
    if result is Result.PASS:
        return passed(cid, message, tags, code=code)
    if result is Result.UNKNOWN:
        return unknown(cid, message, tags, code=code, fix=fix)
    return failed(cid, message, tags, code=code, fix=fix)


@check(Tier.CODE, "code.M1502_dryer_exhaust")
def dryer_exhaust(ctx: CheckContext) -> list[Finding]:
    """M1502 — the dryer duct is independent, short enough, and vents outdoors."""
    import math

    cid, code = "code.M1502_dryer_exhaust", "M1502"
    appliance_types = {t.tag: t for t in ctx.plan.library.appliance_types}
    # The product's *name* is part of the population text, not only its tag and type_ref.
    # Without it catlin's dryer was invisible to this check: the element is FX-M-LAUNDRY and
    # the type is APPL-LG-WASHTOWER, neither of which contains the word, so the house
    # reported "no dryer is modeled" while a heat-pump dryer stood in the laundry — and the
    # ductless exemption below, which the type was chosen for and which the type's own
    # comment says this check reads, never ran. A substring match is a blunt population
    # rule, but it is blunt over everything the model actually says the appliance is.
    dryers = [e for e in ctx.plan.all_elements()
              if e.element_kind == "Appliance"
              and "dryer" in " ".join((
                  e.tag, e.type_ref or "",
                  getattr(appliance_types.get(e.type_ref), "name", "") or "")).lower()]
    # M1502.1 — the section does not reach a listed condensing (ductless) dryer. Its moisture
    # leaves as condensate down a drain, so there is no duct to be too long, to share, or to
    # terminate in the wrong place, and demanding one would be demanding a hole in the
    # envelope for nothing.
    ductless = [d for d in dryers
                if getattr(appliance_types.get(d.type_ref), "ductless", False)]
    dryers = [d for d in dryers if d not in ductless]
    runs = [d for d in ctx.plan.all_elements()
            if d.element_kind == "DuctRun" and d.system is DuctSystem.DRYER]
    if not dryers and not runs:
        if ductless:
            return [_finding(cid, Result.PASS,
                             f"{', '.join(sorted(d.tag for d in ductless))} is a condensing "
                             "(ductless) dryer — M1502.1 exempts it from this section", (),
                             "M1502.1")]
        # UNKNOWN, deliberately not N/A. A dwelling does laundry; "no dryer is modeled"
        # in a house with a laundry room is a gap in the model, not a fact about the
        # building, and calling it N/A would be exactly the unearned use of that verdict
        # Result.NOT_APPLICABLE's own docstring rules out.
        return [_finding(cid, Result.UNKNOWN, "no dryer and no dryer exhaust run are "
                         "modeled", (), code)]
    if not runs:
        return [_finding(cid, Result.FAIL,
                         f"dryer {', '.join(sorted(d.tag for d in dryers))} has no "
                         "DuctSystem.DRYER exhaust run; M1502.2 requires an independent "
                         "exhaust to the outdoors",
                         tuple(sorted(d.tag for d in dryers)), "M1502.2",
                         "author a DuctRun with system=DuctSystem.DRYER from the dryer to "
                         "an exterior termination")]

    out: list[Finding] = []
    for run in runs:
        points = [p.xy_m for p in run.path]
        if len(points) < 2:
            out.append(_finding(cid, Result.UNKNOWN, f"{run.tag} has no routed path to "
                                "measure", (run.tag,), "M1502.4.5.1"))
            continue
        # strict=False on both windows: the tails are deliberately one and two shorter
        # than ``points`` — that raggedness *is* the sliding window.
        straight_ft = sum(
            math.dist(a, b) for a, b in zip(points, points[1:], strict=False)) / 0.3048
        penalty_ft = 0.0
        elbows = 0
        for a, b, c in zip(points, points[1:], points[2:], strict=False):
            turn = _turn_degrees(a, b, c, math)
            if turn < _MIN_TURN_DEGREES:
                continue
            elbows += 1
            # Anything past 45 degrees is charged as a 90; the code tabulates the two
            # fittings that exist, not a continuum.
            penalty_ft += (_ELBOW_90_PENALTY_FT if turn > 45.0 + 1e-6
                           else _ELBOW_45_PENALTY_FT)
        developed = straight_ft + penalty_ft
        detail = (f"{developed:.0f}' developed ({straight_ft:.0f}' of duct + "
                  f"{penalty_ft:.0f}' for {elbows} fitting(s))")
        if developed > _MAX_DEVELOPED_FT + 1e-6:
            out.append(_finding(cid, Result.FAIL,
                                f"{run.tag} runs {detail}; M1502.4.5.1 allows 35'",
                                (run.tag,), "M1502.4.5.1",
                                "shorten the run, remove elbows, or specify a booster fan "
                                "with the manufacturer's own length table"))
        else:
            out.append(_finding(cid, Result.PASS, f"{run.tag} runs {detail} (<= 35')",
                                (), "M1502.4.5.1"))

        # M1502.2: the exhaust is independent of every other system.
        shared = [other.tag for other in ctx.plan.all_elements()
                  if other.element_kind == "Register" and other.duct_ref == run.tag
                  and other.kind is not DuctSystem.DRYER]
        if shared:
            out.append(_finding(cid, Result.FAIL,
                                f"{run.tag} also terminates {', '.join(sorted(shared))}; "
                                "M1502.2 requires the dryer exhaust to be independent of "
                                "all other systems", (run.tag, *sorted(shared)), "M1502.2"))

        # M1502.3: it terminates outdoors, not into another room.
        end = points[-1]
        inside = _room_containing(ctx, run, end)
        if inside is not None:
            out.append(_finding(cid, Result.FAIL,
                                f"{run.tag} terminates inside {inside}; M1502.3 requires "
                                "termination to the outdoors",
                                (run.tag, inside), "M1502.3"))
        else:
            out.append(_finding(cid, Result.PASS, f"{run.tag} terminates outside every "
                                "resolved room face", (), "M1502.3"))
    return out


def _turn_degrees(a, b, c, math) -> float:
    """The deflection angle at b, in degrees — 0 for straight-through."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cosine = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cosine))


def _room_containing(ctx: CheckContext, run, point) -> str | None:
    from shapely.geometry import Point, Polygon

    probe = Point(point)
    storey = getattr(run, "storey", None)
    for room in ctx.model.rooms:
        if storey is not None and room.storey != storey:
            continue
        if len(room.clear_face) >= 3 and Polygon(room.clear_face).covers(probe):
            return room.tag
    return None

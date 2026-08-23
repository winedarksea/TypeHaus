"""What a railing is actually drawn as, and what R311.7.8 is willing to say about it.

Five defects, all visible in the 3D viewer and none of them caught by anything:

1. A raking handrail was a row of disconnected floating cubes — each band 1-1/2" tall over
   0.25 m of plan, which on a 7.5/11 flight is a 5" vertical gap between consecutive pieces.
   Written for the *guard* case, where a picket stands in the gap; a bare ``rail_count=1``
   handrail has nothing to hide it with.
2. A rail authored ``"1.5in round — Type I"`` drew square.
3. ``Railing.mount`` was read by nobody, so a 36" floor post stood at every station of every
   wall-mounted rail.
4. The rake sampled the *nearest* flight by clamped distance, so a band beside the straight
   run took its elevation from the winder fan below it.
5. Post spacing used ``int(seg // spacing)`` where it wanted ``ceil``, giving RL-A-STAIR a
   9'-3" bay on a guard authored at 5'-0" o.c.

And the check: R311.7.8 graded authored values only, which is how a handrail that stopped
short of its flight passed R311.7.8.2 — ``continuous`` is a bool defaulting to ``True``.
"""

from __future__ import annotations

import math

import pytest
from _helpers import CATLIN

from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.quantities import ft, inch, pt

CHECK_ID = "code.R311_7_8_handrail"


def _solids(model, tag: str, suffix: str):
    return [s for s in model.solids if s.tag.startswith(f"{tag}-{suffix}")]


def _bands(model, tag: str):
    """Rail solids grouped into bands: one shared plan axis, one contiguous run of z.

    Both halves matter — a round section is a stack of solids on one axis, and a guard with
    ``rail_count=2`` puts two such stacks on that same axis a guard-height apart.
    """
    stacks: dict[tuple[float, float], list] = {}
    for solid in _solids(model, tag, "RAIL"):
        cx = sum(x for x, _y in solid.outline) / len(solid.outline)
        cy = sum(y for _x, y in solid.outline) / len(solid.outline)
        stacks.setdefault((round(cx, 4), round(cy, 4)), []).append(solid)
    out: dict[tuple[float, float, int], list] = {}
    for (cx, cy), group in stacks.items():
        run, level = [], 0
        for solid in sorted(group, key=lambda item: item.z0_m):
            if run and solid.z0_m > max(p.z1_m for p in run) + 1e-9:
                out[(cx, cy, level)] = run
                run, level = [], level + 1
            run.append(solid)
        out[(cx, cy, level)] = run
    return out


# --- 1. the raking rail is continuous ------------------------------------------------

@pytest.mark.parametrize("tag", ["RL-A-HANDRAIL", "RL-M-HANDRAIL-E", "RL-M-HANDRAIL-W",
                                 "RL-S-HANDRAIL-E", "RL-S-HANDRAIL-W"])
def test_a_raking_handrail_has_no_vertical_gaps(catlin_model, tag):
    """Union the rail solids' z ranges: a continuous rail is *one* interval."""
    ranges = sorted((s.z0_m, s.z1_m) for s in _solids(catlin_model, tag, "RAIL"))
    assert ranges, tag
    merged = [list(ranges[0])]
    for z0, z1 in ranges[1:]:
        if z0 <= merged[-1][1] + 1e-9:
            merged[-1][1] = max(merged[-1][1], z1)
        else:
            merged.append([z0, z1])
    assert len(merged) == 1, f"{tag} draws as {len(merged)} disconnected pieces: {merged}"


# --- 2. a round profile draws round ---------------------------------------------------

def test_a_rail_authored_round_is_drawn_round(catlin_model):
    """A faceted circle is a stack of bands whose plan widths differ; a square is one band."""
    stacks = _bands(catlin_model, "RL-M-HANDRAIL-E")
    assert stacks
    widths = set()
    for group in stacks.values():
        assert len(group) > 1, "a round section is faceted into a stack, not one prism"
        for solid in group:
            xs = [x for x, _y in solid.outline]
            ys = [y for _x, y in solid.outline]
            widths.add(round(min(max(xs) - min(xs), max(ys) - min(ys)), 4))
    assert len(widths) > 1, "every band the same width is a square bar, not a round one"
    assert max(widths) <= inch(1.5).meters + 1e-9


def test_a_guard_with_no_stated_profile_is_left_square(catlin_model):
    """Type I also admits a shaped non-circular rail, so silence is not a circle."""
    for group in _bands(catlin_model, "RL-A-STAIR").values():
        assert len(group) == 1


# --- 3. mount="wall" means brackets, not posts ----------------------------------------

@pytest.mark.parametrize("tag", ["RL-A-HANDRAIL", "RL-M-HANDRAIL-E", "RL-S-HANDRAIL-W"])
def test_a_wall_mounted_rail_stands_on_no_posts(catlin_model, tag):
    assert not _solids(catlin_model, tag, "POST"), f"{tag} is screwed to a wall"
    brackets = _solids(catlin_model, tag, "BRACKET")
    assert brackets, f"{tag} has to be held up by something"
    for bracket in brackets:
        assert bracket.z1_m - bracket.z0_m < inch(6).meters, "a bracket, not a post"


def test_a_fascia_mounted_guard_keeps_its_posts(catlin_model):
    """The change reads ``mount``; it does not stop reading anything else."""
    assert _solids(catlin_model, "RL-A-STAIR", "POST")
    assert not _solids(catlin_model, "RL-A-STAIR", "BRACKET")


def test_a_bracket_reaches_the_wall_face_it_lands_on(catlin_model):
    """Not a stub of arbitrary length: the arm is as long as the gap it has to cross."""
    bracket = _solids(catlin_model, "RL-M-HANDRAIL-E", "BRACKET")[0]
    xs = [x for x, _y in bracket.outline]
    ys = [y for _x, y in bracket.outline]
    arm = max(max(xs) - min(xs), max(ys) - min(ys))
    assert inch(1).meters < arm < inch(9).meters


# --- 4. the rake follows the flight the rail is beside --------------------------------

def test_the_rake_takes_its_elevation_from_the_flight_it_runs_along(catlin_model):
    """Consecutive bands of one rail climb by one band's worth, not by three of them.

    The first band of RL-A-HANDRAIL sat 0.40 m from the straight flight it rakes along and
    0.28 m from the last nosing of the winder fan below it. Ranking on clamped distance gave
    it the winder's elevation and a 0.416 m step against its neighbours' 0.176 m.
    """
    stacks = _bands(catlin_model, "RL-A-HANDRAIL")
    ordered = [((cx, cy), (min(s.z0_m for s in g) + max(s.z1_m for s in g)) / 2.0)
               for (cx, cy, _level), g in sorted(stacks.items())]
    steps = [abs(b - a) for (_p, a), (_q, b) in zip(ordered, ordered[1:])]
    interior = sorted(steps)[:-2]  # the flight junction genuinely does step a full riser
    assert max(interior) < inch(3).meters, f"a band out of step with its neighbours: {steps}"


# --- 5. post spacing is a maximum ------------------------------------------------------

def test_no_bay_exceeds_the_authored_post_spacing(catlin_plan):
    """``int(seg // spacing)`` left the whole remainder in the last bay.

    Walked in *path* order rather than by sorting the drawn posts: a railing that turns a
    corner has two stations that are near each other in x and far apart along the run.
    """
    from typehaus.model.structure import Railing
    from typehaus.resolve.railings.frame import MIN_POST_SPACING_M, railing_post_stations

    seen = 0
    for railing in (e for e in catlin_plan.all_elements() if isinstance(e, Railing)):
        spacing = max(railing.post_spacing.meters, MIN_POST_SPACING_M)
        stations = railing_post_stations([p.xy_m for p in railing.path], spacing)
        for (x0, y0), (x1, y1) in zip(stations, stations[1:]):
            seen += 1
            bay = math.hypot(x1 - x0, y1 - y0)
            assert bay <= spacing + 1e-6, (
                f"{railing.tag} has a {bay / 0.0254:.0f}\" bay at "
                f"{railing.post_spacing.inches:.0f}\" o.c.")
    assert seen


def test_the_stations_still_divide_a_segment_evenly(catlin_model):
    """Evenly, not at exactly ``spacing`` from the start — else a segment a millimetre over
    a whole number of bays ends in a millimetre-wide bay."""
    from typehaus.resolve.railings.frame import railing_post_stations

    stations = railing_post_stations([(0.0, 0.0), (10.001, 0.0)], 5.0)
    bays = [b[0] - a[0] for a, b in zip(stations, stations[1:])]
    assert len(bays) == 3
    assert min(bays) > 3.0


# --- 6. R311.7.8 measures --------------------------------------------------------------

def _handrail_findings(plan):
    from typehaus.checks.run import run

    report = run(plan, CATLIN, tier=Tier.CODE)
    return [f for f in report.findings if f.check_id == CHECK_ID]


@pytest.fixture(scope="module")
def handrail_findings(catlin_plan):
    return _handrail_findings(catlin_plan)


def test_the_house_passes_on_measured_geometry_not_on_authored_claims(handrail_findings):
    assert handrail_findings
    assert all(f.result is Result.PASS for f in handrail_findings), [
        f.message for f in handrail_findings if f.result is not Result.PASS]
    assert any("as drawn" in f.message for f in handrail_findings)


def test_a_handrail_that_stops_short_of_its_flight_now_fails(catlin_plan):
    """The defect the rule shipped with: ``continuous=True`` is a default, not evidence."""
    from typehaus.model.structure import Railing

    stumped = []
    for element in catlin_plan.all_elements():
        if isinstance(element, Railing) and element.tag == "RL-S-HANDRAIL-E":
            # Halve the run: the top of the flight loses its rail entirely.
            (ax, ay), (bx, by) = element.path[0].xy_m, element.path[-1].xy_m
            stumped.append(element.model_copy(update={"path": (
                element.path[0], pt(ft(0, (ax + bx) / 2 / 0.0254),
                                    ft(0, (ay + by) / 2 / 0.0254)))}))
    assert stumped
    plan = catlin_plan
    for short in stumped:
        storey = next(tag for tag, group in plan.elements.items()
                      if any(e.tag == short.tag for e in group))
        plan = plan.with_elements(storey, [
            short if e.tag == short.tag else e for e in plan.elements[storey]])
    findings = _handrail_findings(plan)
    failures = [f for f in findings if f.result is Result.FAIL]
    assert failures, [f.message for f in findings]
    assert any("R311.7.8.2" in (f.code_ref or "") for f in failures)


def test_a_stated_diameter_outside_type_i_fails(catlin_plan):
    """R311.7.8.3 Type I circular is 1-1/4" to 2"; a 3" bar is not graspable."""
    from typehaus.model.structure import Railing

    plan = catlin_plan
    for storey, group in list(plan.elements.items()):
        if not any(isinstance(e, Railing) and e.tag == "RL-A-HANDRAIL" for e in group):
            continue
        plan = plan.with_elements(storey, [
            e.model_copy(update={"graspable_profile": "3in round — Type I"})
            if isinstance(e, Railing) and e.tag == "RL-A-HANDRAIL" else e
            for e in group])
    findings = _handrail_findings(plan)
    assert any(f.result is Result.FAIL and "R311.7.8.3" in (f.code_ref or "")
               for f in findings), [f.message for f in findings]

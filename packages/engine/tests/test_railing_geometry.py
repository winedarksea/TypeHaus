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


def _rails(model, tag: str):
    """This railing's rail solids — one per level now, each carrying its own 3D polyline."""
    return _solids(model, tag, "RAIL")


def _stations(model, tag: str, step_m: float = 0.25):
    """``(plan point, centreline z)`` resampled along the top rail's own swept path.

    These tests used to walk the *bands* a raking rail was chopped into — one per 1-1/2" of
    fall, times the round section's facet bands — because that stack was all the prism IR
    could say. The rail is one solid with one polyline now (→ resolve/sweep.py), so the
    stations are sampled off it rather than recovered from a pile of pieces. Same
    measurement, one source.
    """
    rails = [s for s in _rails(model, tag) if s.sweep is not None]
    assert rails, f"{tag} draws no swept rail"
    path = max(rails, key=lambda s: s.z1_m).sweep.path
    out = []
    for a, b in zip(path, path[1:]):
        run = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(int(math.ceil(run / step_m)), 1)
        for k in range(steps):
            t = k / steps
            out.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                        a[2] + (b[2] - a[2]) * t))
    out.append(((path[-1][0], path[-1][1]), path[-1][2]))
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
    """A round section is a faceted circle profile on the sweep — not a square one.

    It used to be readable only from the drawn bands (a stack whose plan widths differ), the
    prism IR having no way to say "circle". The sweep carries the section itself, so the
    question is answered where it is asked.
    """
    from typehaus.resolve.sweep import is_round_profile, profile_radius_m

    rails = [s for s in _rails(catlin_model, "RL-M-HANDRAIL-E") if s.sweep is not None]
    assert rails
    for rail in rails:
        assert is_round_profile(rail.sweep.profile), "authored round, drawn square"
        assert profile_radius_m(rail.sweep.profile) <= inch(0.75).meters + 1e-9
    widths = {round(max(x for x, _y in r.outline) - min(x for x, _y in r.outline), 4)
              for r in rails}
    assert widths


def test_a_guard_with_no_stated_profile_is_left_square(catlin_model):
    """Type I also admits a shaped non-circular rail, so silence is not a circle."""
    from typehaus.resolve.sweep import is_round_profile

    rails = [s for s in _rails(catlin_model, "RL-A-STAIR") if s.sweep is not None]
    assert rails
    for rail in rails:
        assert len(rail.sweep.profile) == 4
        assert not is_round_profile(rail.sweep.profile)


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
    """Consecutive stations of one rail climb by one station's worth, not by three of them.

    The first band of RL-A-HANDRAIL sat 0.40 m from the straight flight it rakes along and
    0.28 m from the last nosing of the winder fan below it. Ranking on clamped distance gave
    it the winder's elevation and a 0.416 m step against its neighbours' 0.176 m. The
    sampling that fed that ranking is still there — it is what the sweep's path is built
    from — so the measurement still has to hold; it is now read off the one solid the rail
    became instead of off the pile of bands it used to be.
    """
    zs = [z for _point, z in _stations(catlin_model, "RL-A-HANDRAIL")]
    # The *second* difference, not the first: a rail climbing a flight steps by a riser at
    # every station and that is not a defect. What was wrong was one station stepping three
    # times as far as the two either side of it — a kink, which is what this measures.
    kinks = [abs(zs[i] - (zs[i - 1] + zs[i + 1]) / 2.0) for i in range(1, len(zs) - 1)]
    interior = sorted(kinks)[:-1]  # the flight junction genuinely is one real kink
    assert max(interior) < inch(3).meters, f"a station out of step with its neighbours: {kinks}"


def test_a_raking_rail_is_one_solid_per_level(catlin_model):
    """The defect this whole change is about: a straight 13-ft bar was 292 solids.

    One band per 1-1/2" of fall, times ``rail_count``, times the round section's four facet
    bands — and railings came to 1,149 of the house's 2,857 solids, each of them a separate
    glTF node, a separate ``IfcRailing`` and a separate polyline on the plan sheet.
    """
    from typehaus.model.structure import Railing

    element = next(e for e in catlin_model.plan.all_elements()
                   if isinstance(e, Railing) and e.tag == "RL-A-HANDRAIL")
    rails = _rails(catlin_model, "RL-A-HANDRAIL")
    assert len(rails) == max(element.rail_count, 1)
    assert all(rail.sweep is not None for rail in rails)


def test_a_straight_flight_collapses_to_the_points_it_is_cut_at(catlin_model):
    """The sampled path is simplified, so a rail is authored geometry again, not stations."""
    rail = next(s for s in _rails(catlin_model, "RL-A-HANDRAIL") if s.sweep is not None)
    assert 2 <= len(rail.sweep.path) <= 12, rail.sweep.path


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

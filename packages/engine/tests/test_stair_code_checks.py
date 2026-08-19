"""The R311.7 stair checks measure built members, not authored intent.

``code.R311_7_stair_geometry`` once *reported* headroom by reading the arrival storey's
nominal ceiling height — 11' of "headroom" for a winder climbing into a roof. The checks
here each measure resolved output: plumb clearance sampled along the sloped nosing line
against floor/roof/soffit structure, flight width off the tread boards, landing depth off
the deck members. Each check gets a two-sided synthetic test (a geometry that passes AND
one that fails), so no rule can rot into always-pass or always-fail.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.checks.code.mn_residential.fall_protection import stairwell_guard
from typehaus.checks.code.mn_residential.stairs import (
    stair_handrail,
    stair_headroom,
    stair_landing_depth,
    stair_width,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedStair
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR


_RISER = 0.19
_GOING = 0.254


@pytest.fixture(scope="module")
def catlin_ctx():
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    return ctx


def _tread(index: int, width_m: float = 1.0) -> FramedMember:
    y = _GOING * index
    centre = y + (_GOING - inch(1).meters) / 2.0
    top = _RISER * (index + 1)
    return FramedMember("S", f"tread-{index:03d}", "tread", "deck 11x1.5",
                        (0.0, centre), (width_m, centre), top - inch(1.5).meters, top,
                        width_m, riser_line=((0.0, y), (width_m, y)))


def _flight(tread_count: int = 4, width_m: float = 1.0) -> ResolvedStair:
    return ResolvedStair(uid="S", tag="S-STR", storey="main", to_storey="second",
                         outline=[], riser_count=tread_count + 1, riser_height_m=_RISER,
                         tread_depth_m=inch(11).meters, run_direction="y",
                         run_reversed=False, layout="straight", turn_direction=None,
                         winder_count=0,
                         members=tuple(_tread(i, width_m) for i in range(tread_count)),
                         going_depth_m=_GOING, nosing_depth_m=inch(1).meters)


def _deck_at(z: float) -> ResolvedFloor:
    return ResolvedFloor(uid="F", tag="F-DECK", storey="second", direction="x",
                         members=(), deck_outline=[(-5.0, -5.0), (5.0, -5.0),
                                                   (5.0, 5.0), (-5.0, 5.0)],
                         deck_voids=(), deck_z0_m=z, deck_z1_m=z + 0.018)


def _ctx(stair, floors=()):
    return SimpleNamespace(model=SimpleNamespace(stairs=[stair], floors=list(floors),
                                                 roofs=[], soffits=[]))


# ------------------------------------------------------------------- headroom
def test_headroom_passes_and_fails_on_the_measured_plumb_clearance():
    """The walk tops out at ~0.95 m (synthesized arrival station); a deck whose underside
    clears that by more than 6'-8" passes, one that pinches it fails — same flight."""
    tall = _ctx(_flight(), [_deck_at(3.5)])
    assert [f.result for f in stair_headroom(tall)] == [Result.PASS]
    low = _ctx(_flight(), [_deck_at(2.8)])
    findings = stair_headroom(low)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "F-DECK" in findings[0].message  # names the obstructing element


def test_headroom_never_passes_by_absence():
    findings = stair_headroom(_ctx(_flight()))
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_headroom_ignores_structure_below_the_walk():
    """A deck under the flight (the floor it springs from) is not overhead."""
    findings = stair_headroom(_ctx(_flight(), [_deck_at(-0.5), _deck_at(3.5)]))
    assert [f.result for f in findings] == [Result.PASS]


def test_catlin_stair_headroom_is_measured_and_passes(catlin_ctx):
    findings = {f.message.split()[0]: f for f in stair_headroom(catlin_ctx)}
    assert set(findings) == {"ST-B2M", "ST-M2S", "ST-S2A"}
    for finding in findings.values():
        assert finding.result is Result.PASS, finding.message
        assert "plumb under" in finding.message  # a measurement, not a storey attribute
    # The winder's overhead constraint is the roof it climbs into, not a nominal ceiling.
    assert "RF-" in findings["ST-S2A"].message


# ---------------------------------------------------------------------- width
def test_width_measures_the_tread_boards():
    wide = _ctx(_flight(width_m=1.0))  # ~39.4"
    assert [f.result for f in stair_width(wide)] == [Result.PASS]
    narrow = _ctx(_flight(width_m=0.8))  # ~31.5"
    assert [f.result for f in stair_width(narrow)] == [Result.FAIL]


def test_catlin_stair_widths_pass_at_or_above_the_minimum(catlin_ctx):
    findings = stair_width(catlin_ctx)
    assert len(findings) == 3
    assert all(f.result is Result.PASS for f in findings)
    # ST-S2A rides the 36" limit exactly — the tolerance idiom is what keeps it passing.
    assert any("36.00" in f.message for f in findings)
    # Every stair now carries handrails, so each pass also reports the measured clear
    # width past the rail (the R311.7.1 31.5"/27" rules, no longer deferred).
    assert all("clear past" in f.message for f in findings), \
        [f.message for f in findings]


def _handrail_at(x_in: float, tag: str = "RL-T"):
    """A synthetic handrail running up the _flight fixture at plan ``x`` (inches)."""
    from typehaus.model import pt
    from typehaus.model.structure import Railing

    return Railing(uid="AAAAAAAAAZ", tag=tag,
                   path=(pt(inch(x_in), inch(-4)), pt(inch(x_in), inch(48))),
                   height=inch(36), base_elevation=inch(0), post_spacing=inch(48),
                   rail_count=1, role="handrail", serves_stair="S-STR",
                   top_height=inch(36), graspable_profile="type-I")


def _ctx_with_rails(stair, rails):
    return SimpleNamespace(
        model=SimpleNamespace(stairs=[stair], floors=[], roofs=[], soffits=[]),
        plan=SimpleNamespace(all_elements=lambda: list(rails)))


def test_width_measures_clear_width_past_a_handrail():
    """The 31.5" one-side rule, two-sided: a 39.4" flight keeps ~36.6" past a rail hugging
    its edge and passes; the same flight with the rail 8" into it keeps ~30.6" and fails —
    the geometry the old check's docstring deferred until a handrail existed to measure."""
    wide = _ctx_with_rails(_flight(width_m=1.0), [_handrail_at(2.0)])
    assert [f.result for f in stair_width(wide)] == [Result.PASS]
    pinched = _ctx_with_rails(_flight(width_m=1.0), [_handrail_at(8.0)])
    findings = stair_width(pinched)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "31.5" in findings[0].message


def test_width_past_rails_both_sides_uses_the_27_inch_limit():
    both_tight = _ctx_with_rails(
        _flight(width_m=1.0),
        [_handrail_at(8.0), _handrail_at(1.0 / .0254 - 8.0, tag="RL-T2")])
    findings = stair_width(both_tight)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "27.0" in findings[0].message
    both_edge = _ctx_with_rails(
        _flight(width_m=1.0),
        [_handrail_at(2.0), _handrail_at(1.0 / .0254 - 2.0, tag="RL-T2")])
    assert [f.result for f in stair_width(both_edge)] == [Result.PASS]


# ------------------------------------------------------------------- landings
def _with_landing(depth_m: float) -> ResolvedStair:
    stair = _flight()
    landing = FramedMember("S", "landing-lower", "landing", "deck 42x1.5",
                           (0.5, 1.2), (0.5, 1.2 + depth_m), 0.9, 0.94, depth_m)
    return ResolvedStair(**{**stair.__dict__, "members": (*stair.members, landing)})


def test_landing_depth_measures_the_deck_member():
    deep = _ctx(_with_landing(1.0))
    assert [f.result for f in stair_landing_depth(deep)] == [Result.PASS]
    shallow = _ctx(_with_landing(0.8))  # ~31.5" in the direction of travel
    assert [f.result for f in stair_landing_depth(shallow)] == [Result.FAIL]


def test_catlin_landings_pass_both_axes(catlin_ctx):
    findings = stair_landing_depth(catlin_ctx)
    # Two U-stairs x two half-landings; the winder stair has no landing members.
    assert len(findings) == 4
    assert all(f.result is Result.PASS for f in findings)


# ------------------------------------------------------------------ handrails
def test_catlin_flights_have_graded_handrails(catlin_ctx):
    """Every 4+-riser stair carries authored, graded handrails: one wall-mounted rail per
    flight (two per U stair, one along the winder stair's straight flight), each raked
    along the nosing line at resolve and graded here on top_height (34"-38" above the
    nosings), continuity and graspability."""
    findings = stair_handrail(catlin_ctx)
    assert [f.result for f in findings] == [Result.PASS] * 5, \
        [f.message for f in findings]
    assert {f.message.split()[0] for f in findings} == {"ST-B2M", "ST-M2S", "ST-S2A"}


def test_handrail_is_unknown_when_no_handrail_is_authored_anywhere(catlin_ctx):
    """No Railing in the whole plan declares a handrail role -> a modeling gap (UNKNOWN),
    never a silent pass and never a fabricated deficiency."""
    from typehaus.model.structure import Railing

    ctx = _ctx_with_elements(
        catlin_ctx,
        lambda e: None if isinstance(e, Railing) and e.role == "handrail" else e)
    findings = stair_handrail(ctx)
    assert len(findings) == 3
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert all("handrail" in f.message for f in findings)


def test_a_stair_left_without_its_handrail_fails_once_any_exists(catlin_ctx):
    """Handrails are adopted in this house but ST-S2A's is knocked out -> that stair is a
    deficiency FAIL while the others keep passing."""
    ctx = _ctx_with_elements(
        catlin_ctx,
        lambda e: None if getattr(e, "serves_stair", None) == "ST-S2A" else e)
    by_stair: dict = {}
    for f in stair_handrail(ctx):
        by_stair.setdefault(f.message.split()[0], set()).add(f.result)
    assert by_stair["ST-S2A"] == {Result.FAIL}
    assert by_stair["ST-B2M"] == {Result.PASS}
    assert by_stair["ST-M2S"] == {Result.PASS}


def test_handrail_not_required_under_four_risers():
    stub = _flight(tread_count=2)  # 3 risers
    assert [f.result for f in stair_handrail(_ctx(stub))] == [Result.PASS]


def test_catlin_guards_pass_the_four_inch_sphere_rule(catlin_ctx):
    """R312.1.3 measures all five authored guards: baluster infill at a 4" clear gap — the
    largest opening the sphere rule admits — flips the census from UNKNOWN to PASS. The
    handrail-only railings are deliberately absent: they are not guards.

    There is no ``Wall.guard`` in the plan any more. Until 2026-08-18 the porch was guarded
    by three W-SG-RAIL-* masonry parapets, which passed by construction (solid masonry
    admits no sphere); RL-SG-PORCH replaced all three and is measured like every other
    railing, off its drawn pickets."""
    from typehaus.checks.code.mn_residential.fall_protection import guard_opening_limit

    findings = guard_opening_limit(catlin_ctx)
    tags = sorted(t for f in findings for t in (f.message.split()[0],))
    assert tags == ["RL-A-STAIR", "RL-S-STAIR", "RL-S-STAIRHEAD",
                    "RL-SG-BALCONY", "RL-SG-PORCH"], [f.message for f in findings]
    assert {f.result for f in findings} == {Result.PASS}


def test_the_sphere_rule_is_measured_off_the_drawn_infill_not_only_the_field(catlin_ctx):
    """The defect this rule shipped with: RL-SG-BALCONY passed on ``baluster_spacing``
    alone while the 3D view showed a 42" guard with two bars and 40" of daylight between
    them, because the infill had never been drawn. Every passing baluster finding now has to
    quote a *drawn* gap, so a resolver that stops emitting pickets fails this rule rather
    than silently going back to asserting a compliance it does not depict."""
    from typehaus.checks.code.mn_residential.fall_protection import guard_opening_limit

    drawn = [f for f in guard_opening_limit(catlin_ctx) if "draws" in f.message]
    assert sorted(f.message.split()[0] for f in drawn) == [
        "RL-A-STAIR", "RL-S-STAIR", "RL-S-STAIRHEAD", "RL-SG-BALCONY", "RL-SG-PORCH"]


# --- R312.1 stair-well guards ----------------------------------------------------------

def _ctx_with_elements(ctx, keep):
    """The real catlin context with its authored element list filtered/mapped — the
    cheapest way to knock a railing out (or shrink one) without a second plan load."""
    elements = [keep(e) for e in ctx.plan.all_elements()]
    elements = [e for e in elements if e is not None]
    plan = SimpleNamespace(all_elements=lambda: elements)
    return SimpleNamespace(plan=plan, model=ctx.model, preferences=ctx.preferences)


def test_catlin_stair_wells_are_guarded(catlin_ctx):
    findings = stairwell_guard(catlin_ctx)
    assert {f.result for f in findings} == {Result.PASS}, [f.message for f in findings]
    by_msg = {f.message.split(":")[0]: f.message for f in findings}
    # Both wells adjudicated, and the pass names the members actually doing the guarding —
    # the second-storey well's east edge is RL-S-STAIR plus wall W-S-C4B beyond y=30'-10",
    # which is exactly the split this check exists to measure.
    assert set(by_msg) == {"FO-S-STAIR", "FO-A-STAIR"}
    assert "RL-S-STAIR" in by_msg["FO-S-STAIR"]
    assert "RL-A-STAIR" in by_msg["FO-A-STAIR"]


def test_removing_the_stairhead_guard_opens_the_south_edge(catlin_ctx):
    ctx = _ctx_with_elements(
        catlin_ctx, lambda e: None if getattr(e, "tag", "") == "RL-S-STAIRHEAD" else e)
    findings = stairwell_guard(ctx)
    fails = [f for f in findings if f.result is Result.FAIL]
    assert fails and any("FO-S-STAIR" in f.message and "south edge" in f.message
                         for f in fails), [f.message for f in findings]


def test_a_34_inch_railing_is_not_a_guard(catlin_ctx):
    from typehaus.model.structure import Railing

    def shrink(e):
        if isinstance(e, Railing) and e.tag == "RL-S-STAIRHEAD":
            return e.model_copy(update={"height": inch(34)})
        return e

    findings = stairwell_guard(_ctx_with_elements(catlin_ctx, shrink))
    fails = [f for f in findings if f.result is Result.FAIL and "FO-S-STAIR" in f.message]
    assert fails, [f.message for f in findings]


def test_guard_check_never_passes_by_absence(catlin_ctx):
    from typehaus.model.floors import FloorOpening

    ctx = _ctx_with_elements(
        catlin_ctx, lambda e: None if isinstance(e, FloorOpening) else e)
    findings = stairwell_guard(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_the_stair_throat_is_not_an_open_side(catlin_ctx):
    """The second-storey well's south edge is guarded RL-S-STAIRHEAD + the flight entry;
    with the railing gone the *whole* remainder reports, but the throat span itself
    (x 10'-3 3/8"..13'-9 3/4", where ST-M2S arrives) never does on the intact plan —
    pinned by the clean pass above. Here: the reported gap with the railing removed is
    the railing's own span, not the throat's."""
    ctx = _ctx_with_elements(
        catlin_ctx, lambda e: None if getattr(e, "tag", "") == "RL-S-STAIRHEAD" else e)
    fail = next(f for f in stairwell_guard(ctx)
                if f.result is Result.FAIL and "FO-S-STAIR" in f.message)
    # The gap starts at the railing's authored west end (13'-9 3/4" = 13.81'), east of
    # the throat — the flight's own entry span stays exempt.
    assert "13.8" in fail.message, fail.message

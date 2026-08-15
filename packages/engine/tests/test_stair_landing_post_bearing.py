"""Landing-post load path (plans/TODO.md "Stair framing follow-ups", defect 3).

``resolve/stairs.py`` drops a 4x4 under every landing-platform corner no host wall reaches
and stops it at the subfloor of the storey the flight springs from — it never asks whether
that subfloor is carrying anything. The advisory belongs in the STRUCTURAL tier and not in
``resolve_envelope_geometry``, whose finding contract is bad references only: a post landing
mid-bay on an I-joist deck resolves perfectly well and is still a point load on a member
sized for a uniform one.

Catlin exercises the PASS path (both flights' posts land on concrete). The synthetic models
below are what prove the rule can fail at all, and that it fails for the right reason.
"""

from __future__ import annotations

from types import SimpleNamespace


from typehaus.checks import build_context
from typehaus.checks.structural.stairs import landing_post_bearing
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedStair
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR


_DECK_Z = 0.0
_POST_TOP_Z = 1.5


def test_catlin_landing_posts_all_land_on_something_bearing(catlin_model):
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = landing_post_bearing(ctx)
    posts = [member for stair in catlin_model.stairs for member in stair.members
             if member.child_key.startswith("landing-post-")]
    assert posts, "catlin posts down the landing corners no wall reaches"
    assert len(findings) == len(posts)
    assert all(finding.result is Result.PASS for finding in findings), [
        finding.message for finding in findings if finding.result is not Result.PASS]
    assert all(finding.severity.value == "warn" for finding in findings)


# ------------------------------------------------------------------- synthetic
def _post(point):
    return FramedMember("S", "landing-post-000", "landing", "4x4", point, point,
                        _DECK_Z, _POST_TOP_Z, _POST_TOP_Z - _DECK_Z, orient=(1.0, 0.0))


def _stair_with_post(point=(2.0, 2.0)):
    return ResolvedStair(uid="S", tag="S-1", storey="main", to_storey="second", outline=[],
                         riser_count=14, riser_height_m=0.18, tread_depth_m=0.28,
                         run_direction="x", run_reversed=False, layout="u_split_landing",
                         turn_direction=None, winder_count=0, members=(_post(point),))


def _solid(tag, category, z1, ring):
    return SimpleNamespace(tag=tag, category=category, outline=ring, z0_m=z1 - 0.2, z1_m=z1)


def _ctx(solids=(), walls=()):
    model = SimpleNamespace(stairs=[_stair_with_post()], solids=list(solids),
                            walls=list(walls))
    return SimpleNamespace(model=model)


_SQUARE = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]


def test_a_post_on_a_bare_framed_deck_is_reported():
    """No slab, no beam, no bearing wall: nothing traces the corner reaction to ground."""
    findings = landing_post_bearing(_ctx())
    assert [finding.result for finding in findings] == [Result.FAIL]
    assert "block the joist bay" in (findings[0].fix_hint or "")


def test_a_slab_under_the_post_clears_it():
    ctx = _ctx(solids=[_solid("SL-1", "slab", _DECK_Z, _SQUARE)])
    assert [finding.result for finding in landing_post_bearing(ctx)] == [Result.PASS]


def test_a_beam_under_the_post_clears_it():
    ctx = _ctx(solids=[_solid("BM-1", "beam", _DECK_Z, _SQUARE)])
    assert [finding.result for finding in landing_post_bearing(ctx)] == [Result.PASS]


def test_a_slab_that_stops_short_of_the_post_does_not_clear_it():
    """Elevation alone is not a load path — the slab has to be *under* the post."""
    away = [(6.0, 6.0), (8.0, 6.0), (8.0, 8.0), (6.0, 8.0)]
    ctx = _ctx(solids=[_solid("SL-1", "slab", _DECK_Z, away)])
    assert [finding.result for finding in landing_post_bearing(ctx)] == [Result.FAIL]


def test_a_slab_at_the_wrong_elevation_does_not_clear_it():
    """A slab a storey below is not what the post is standing on."""
    ctx = _ctx(solids=[_solid("SL-1", "slab", _DECK_Z - 2.7, _SQUARE)])
    assert [finding.result for finding in landing_post_bearing(ctx)] == [Result.FAIL]


def test_a_wall_topping_out_under_the_post_clears_it():
    wall = SimpleNamespace(tag="W-1", axis=((0.0, 2.0), (4.0, 2.0)), z0_m=-2.7,
                           z1_m=_DECK_Z, thickness_m=inch(5.5).meters)
    assert [finding.result for finding in landing_post_bearing(_ctx(walls=[wall]))] == [
        Result.PASS]


def test_no_landing_posts_reports_unknown_rather_than_passing():
    model = SimpleNamespace(stairs=[], solids=[], walls=[])
    findings = landing_post_bearing(SimpleNamespace(model=model))
    assert [finding.result for finding in findings] == [Result.UNKNOWN]

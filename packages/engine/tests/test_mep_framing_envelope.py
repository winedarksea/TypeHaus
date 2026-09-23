"""Runs against framing: the per-wall stud plane, solid floor members, I-joist flanges.

Synthetic geometry pins each rule; the catlin tests pin the three TODO cases they close
(``DU-ERV-RISER-EXH``, the ``FO-M-ERV-OA`` trimmer packs, ``PR-B-LAV1-DRAIN``).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from shapely.geometry import LineString, Point, box

from typehaus.checks.mep import floor_members, joist_flange
from typehaus.checks.mep.framing_envelope import Leg, bite, relation
from typehaus.checks.mep.wall_cavity import _classify
from typehaus.resolve.mep_bore_geometry import leg_crossings
from typehaus.resolve.mep_bores import i_joist_flange_cut
from typehaus.resolve.model import FramedMember

IN = 0.0254


def _riser(x_in, y_in, dia_in, z0_in=-20.0, z1_in=140.0, tag="R") -> Leg:
    r = dia_in / 2 * IN
    a = (x_in * IN, y_in * IN)
    return Leg("pipe", tag, 0, a, a, z0_in * IN, z1_in * IN, r, Point(a).buffer(r), r)


def _level(a_in, b_in, z_in, dia_in, tag="L") -> Leg:
    r = dia_in / 2 * IN
    a, b = (a_in[0] * IN, a_in[1] * IN), (b_in[0] * IN, b_in[1] * IN)
    return Leg("pipe", tag, 0, a, b, z_in * IN, z_in * IN, r,
               LineString([a, b]).buffer(r, cap_style="flat"), r)


def _member(key, category, profile, p0_in, p1_in, z0_in, z1_in,
            orient=None) -> FramedMember:
    p0, p1 = (p0_in[0] * IN, p0_in[1] * IN), (p1_in[0] * IN, p1_in[1] * IN)
    return FramedMember("F", key, category, profile, p0, p1, z0_in * IN, z1_in * IN,
                        Point(p0).distance(Point(p1)), orient=orient)


# --- the rule -------------------------------------------------------------------------

def test_an_i_joist_flange_takes_no_cut_at_all() -> None:
    assert i_joist_flange_cut("11.875 I-joist", 0.0).ok is True
    verdict = i_joist_flange_cut("11.875 I-joist", 0.05)
    assert verdict.ok is False and verdict.limit_in == 0.0
    assert "forbid" in verdict.basis and verdict.remedy


# --- 1. the stud plane, per wall ------------------------------------------------------

#: A 2x4 wall on y=0: stud plane y -1.75..1.75, finished faces at +-2.375.
_PLANE = box(0, -1.75 * IN, 72 * IN, 1.75 * IN)
_BODY = box(0, -2.375 * IN, 72 * IN, 2.375 * IN)
_NORMAL = (0.0, 1.0)


def test_a_riser_half_in_the_stud_plane_is_beside_the_wall_and_fails() -> None:
    """``DU-ERV-RISER-EXH``: a 6" riser 3 1/2" off the axis of a 2x4 wall."""
    score, verdict = _classify(_riser(18.625, 3.5, 6.0), "W", _PLANE, _BODY, _NORMAL)
    assert verdict.kind == "beside" and verdict.ok is False
    assert score / IN == pytest.approx(1.25)
    assert '1.875" away' in verdict.fix  # to clear the 2.375" finished face


def test_a_pipe_inside_the_cavity_passes_and_one_too_big_fails() -> None:
    _s, ok = _classify(_riser(30, 0, 1.5), "W", _PLANE, _BODY, _NORMAL)
    assert ok.kind == "cavity" and ok.ok
    _s, big = _classify(_riser(30, 0, 4.0), "W", _PLANE, _BODY, _NORMAL)
    assert big.kind == "oversize" and not big.ok
    assert "fur the wall out" in big.fix


def test_an_off_centre_pipe_that_would_fit_is_told_to_centre() -> None:
    _s, verdict = _classify(_riser(30, 1.25, 1.5), "W", _PLANE, _BODY, _NORMAL)
    assert verdict.kind == "oversize" and "centre it" in verdict.fix


def test_a_run_through_the_wall_or_past_its_end_is_not_this_rule() -> None:
    assert _classify(_level((30, -10), (30, 10), 50, 2.0), "W", _PLANE, _BODY,
                     _NORMAL) is None
    assert _classify(_riser(73.0, 0.0, 3.0), "W", _PLANE, _BODY, _NORMAL) is None


def test_a_riser_meets_a_stud_across_its_whole_height_not_at_its_midpoint() -> None:
    """The midpoint of a riser from -27.5" to 244" is 108.25", above a 104 3/8" stud."""
    stud = _member("stud-001", "stud", "2x4", (16, 0), (16, 0), 1.5, 104.375,
                   orient=(1.0, 0.0))
    wall = SimpleNamespace(members=[stud], z1_m=120 * IN)
    a = (18.625 * IN, 0.0)
    cuts = leg_crossings(wall, a, a, 244 * IN, -27.5 * IN, 3 * IN)
    assert [cut.member_key for cut in cuts] == ["stud-001"]


# --- 2. solid floor members -----------------------------------------------------------

_TRIMMER = _member("trimmer-X-0-0", "trimmer", "1.75x11.875 LVL", (0, 401.5), (120, 401.5),
                   -11.875, 0.0)
_HEADER = _member("header-X-0", "header", "2-1.75x11.875 LVL", (33, 401.5), (33, 412.5),
                  -11.875, 0.0)


def _run(module, monkeypatch, members, legs_) -> list:
    floor = SimpleNamespace(tag="FS", members=members)
    monkeypatch.setattr(module, "legs", lambda _model: legs_)
    ctx = SimpleNamespace(model=SimpleNamespace(floors=[floor]))
    check = (floor_members.run_through_floor_member if module is floor_members
             else joist_flange.run_in_joist_flange)
    return check(ctx)


def test_a_riser_through_a_trimmer_pack_is_the_members_removal(monkeypatch) -> None:
    [finding] = _run(floor_members, monkeypatch, [_TRIMMER],
                     [_riser(18.625, 403.5, 6.0, tag="DU-RISER")])
    assert finding.result.value == "fail"
    assert "stands through" in finding.message and "trimmer-X-0-0" in finding.message
    assert '1.750"' in finding.message  # the whole 1 3/4" ply


def test_a_leg_across_an_lvl_trimmer_is_an_honest_unknown(monkeypatch) -> None:
    [finding] = _run(floor_members, monkeypatch, [_TRIMMER],
                     [_level((57, 420), (57, 380), -6.0, 0.875, tag="PR-CW")])
    assert finding.result.value == "unknown" and "engineered" in finding.message


def test_a_leg_clear_of_every_member_passes_the_floor(monkeypatch) -> None:
    [finding] = _run(floor_members, monkeypatch, [_TRIMMER, _HEADER],
                     [_riser(80, 380, 2.0)])
    assert finding.result.value == "pass"


def test_across_a_joist_stays_run_member_crossings(monkeypatch) -> None:
    joist = _member("joist-0-001-0", "joist", "2x10", (0, 16), (120, 16), -9.25, 0.0)
    [finding] = _run(floor_members, monkeypatch, [joist],
                     [_level((50, 0), (50, 30), -4.0, 1.0)])
    assert finding.result.value == "pass"


# --- 3. I-joist flanges ---------------------------------------------------------------

_JOIST = _member("joist-0-001-0", "joist", "11.875 I-joist", (1.25, 277.375),
                 (120, 277.375), -11.875, 0.0)


def test_pr_b_lav1_drains_clip_of_the_flange_is_a_fail(monkeypatch) -> None:
    """0.765" of a 1.90" OD inside a 2 1/2" flange at 276 1/8" (TODO)."""
    findings = _run(joist_flange, monkeypatch, [_JOIST],
                    [_riser(72, 275.941, 1.9, z0_in=-15.4, z1_in=0.0, tag="PR-LAV")])
    [finding] = [f for f in findings if f.result.value == "fail"]
    assert '0.766" into a flange' in finding.message


def test_a_riser_clear_of_the_flange_and_a_crossing_through_the_web_pass(
        monkeypatch) -> None:
    findings = _run(joist_flange, monkeypatch, [_JOIST], [
        _riser(72, 274.0, 1.9, z0_in=-15.4, z1_in=0.0),
        _level((60, 260), (60, 290), -6.0, 1.9)])  # the window's question, not this one
    assert [f.result.value for f in findings] == ["pass"]


def test_bite_reads_a_clipped_end_as_the_clip() -> None:
    footprint = box(0, 0, 10 * IN, 2.5 * IN)
    leg = _riser(10.5, 1.25, 2.0)
    assert bite(leg, footprint, (0.0, 1.0)) / IN == pytest.approx(0.5, abs=0.01)
    assert relation(leg, _JOIST) == "riser"


# --- catlin ---------------------------------------------------------------------------

@pytest.mark.slow
def test_catlin_the_exhaust_riser_is_reported_against_its_wall_like_its_twin(
        catlin_ctx) -> None:
    from typehaus.checks.mep.routing_bores import run_through_stud

    by_pair = {f.element_tags: f for f in run_through_stud(catlin_ctx)}
    for riser in ("DU-ERV-RISER-SUP", "DU-ERV-RISER-EXH"):
        finding = by_pair[(riser, "W-M-MECH-S")]
        assert finding.result.value == "fail" and "stands beside" in finding.message


@pytest.mark.slow
def test_catlin_the_erv_trimmer_packs_stand_in_live_risers(catlin_ctx) -> None:
    fails = [f for f in floor_members.run_through_floor_member(catlin_ctx)
             if f.result.value == "fail" and f.element_tags[1] == "FS-M-MECH"]
    runs = {f.element_tags[0] for f in fails if "FO-M-ERV-OA" in f.message}
    assert {"DU-ERV-RISER-SUP", "DU-ERV-RISER-EXH", "CD-B-ATTIC-RISER"} <= runs


@pytest.mark.slow
def test_catlin_pr_b_lav1_drain_is_in_a_flange(catlin_ctx) -> None:
    [finding] = [f for f in joist_flange.run_in_joist_flange(catlin_ctx)
                 if f.element_tags == ("PR-B-LAV1-DRAIN", "FS-M-MECH")]
    assert finding.result.value == "fail" and "joist-0-001-0" in finding.message

"""§6 and §7 of `houses/catlin/notes/framing_bore_limits.md`, reproduced numerically.

Two halves of one question — what happens where a run meets a member R602.6 does not
describe. A header is collected and honestly ungraded; a cut top plate past 50% is now a
determinate verdict, because `PlateTie` gives the model somewhere to say the strap is there.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.model.refs import PublishedHole
from typehaus.model.registry import constructor_names, element_kinds
from typehaus.model.structure import PlateTie
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.mep_bore_geometry import _CUTTABLE_CATEGORIES, leg_crossings
from typehaus.resolve.mep_bores import header_bore, top_plate_cut
from typehaus.resolve.model import FramedMember, ResolvedWall


def _ctx(model) -> CheckContext:
    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2020)

#: catlin's ordinary built-up header: 2-2x8 is 3.000" x 7.250".
HEADER = "2-2x8"
HEADER_DEPTH_IN = 7.25


# --- §6 headers --------------------------------------------------------------------------

def test_a_header_is_collected_at_all() -> None:
    """The one-literal bug: the member list left headers out, so a run over a door met
    nothing and the report was silent about it."""
    assert "header" in _CUTTABLE_CATEGORIES


def test_an_ordinary_hole_in_a_header_is_unknown_and_never_invented() -> None:
    """No IRC table publishes a bore limit for a header, and none is borrowed."""
    verdict = header_bore(HEADER, 4.0)
    assert verdict.ok is None
    assert "NO IRC table" in verdict.basis
    assert "R502.8.1 governs floor joists" in verdict.basis
    assert verdict.limit_in is None  # nothing was claimed as a limit


def test_the_joist_fraction_is_quoted_for_scale_and_binds_nothing() -> None:
    verdict = header_bore(HEADER, 4.0)
    assert "binding on nothing here" in verdict.basis
    assert f'{HEADER_DEPTH_IN / 3.0:.2f}"' in verdict.basis


def test_a_hole_under_the_joist_fraction_is_still_unknown() -> None:
    """2.38" is inside D/3 = 2.42" — and D/3 is a joist's rule, so it decides nothing."""
    assert header_bore(HEADER, 2.375).ok is None


def test_a_penetration_as_deep_as_the_header_severs_it_and_needs_no_table() -> None:
    verdict = header_bore(HEADER, HEADER_DEPTH_IN)
    assert verdict.ok is False
    assert "severed header does not carry the opening" in verdict.basis
    assert verdict.remedy is not None


@pytest.mark.parametrize("profile", ["2-1.75x14 LVL", "3-1.75x5.5 LVL"])
def test_an_engineered_header_is_the_fabricator_s_chart(profile: str) -> None:
    verdict = header_bore(profile, 4.0)
    assert verdict.ok is None
    assert "fabricator's chart" in verdict.basis


def test_catlin_s_remaining_header_crossings_are_all_reported(catlin_model_ro) -> None:
    """Four runs meet a header in this house and every one of them was silent before §6.

    It was six until the 2026-09-22 reroute pass: `DU-B-ERV-R-SAUNA-SUP` took `W-B-CW`'s
    west clear bay and `DU-B-ERV-R-GYM` rose over `D-B-GYM`'s header into the open wall
    between it and the top plate. The four left are the three drains and the sauna's
    extract, and each one's refusal is measured in `notes/framing_bore_limits.md` §8.5.
    """
    from typehaus.checks.mep.routing_bores import run_through_header

    findings = run_through_header(_ctx(catlin_model_ro))
    assert len(findings) == 4
    assert {f.result.value for f in findings} == {"unknown"}


# --- §6 where along the header, and how much of it ------------------------------------

#: catlin's own basement header, in inches: 39" long, 7.25" deep, its top at -22.19.
_H_X0, _H_X1 = 37.50, 76.50
_H_Z0, _H_Z1 = -29.44, -22.19


def _header_wall() -> ResolvedWall:
    member = FramedMember(
        parent_uid="W-TEST", child_key="header-0", category="header", profile=HEADER,
        p0=(_H_X0 * M_PER_IN, 0.0), p1=(_H_X1 * M_PER_IN, 0.0),
        z0_m=_H_Z0 * M_PER_IN, z1_m=_H_Z1 * M_PER_IN,
        length_m=(_H_X1 - _H_X0) * M_PER_IN)
    return ResolvedWall(uid="W-TEST", tag="W-TEST", storey="basement", assembly="INT",
                        axis=((_H_X0 * M_PER_IN, 0.0), (_H_X1 * M_PER_IN, 0.0)),
                        layers=(), z0_m=-96.0 * M_PER_IN, z1_m=_H_Z1 * M_PER_IN,
                        members=(member,))


def _cross(x_in: float, z_in: float, diameter_in: float):
    """One level leg crossing the header square on, at ``x_in``, centred at ``z_in``."""
    radius = diameter_in / 2.0 * M_PER_IN
    cuts = leg_crossings(_header_wall(), (x_in * M_PER_IN, -12.0 * M_PER_IN),
                         (x_in * M_PER_IN, 12.0 * M_PER_IN),
                         z_in * M_PER_IN, z_in * M_PER_IN, radius)
    assert len(cuts) == 1
    return cuts[0]


def test_a_crossing_of_a_horizontal_member_reports_the_crossing_not_the_midpoint() -> None:
    """The station is where the run MEETS the header, not the header's own centroid.

    Reading a header's centroid put every one of catlin's six crossings at dead midspan
    (57.00" on this member), which is a wrong z as well as a station no hole chart can be
    read against: a hole's cost to a bending member is a question about where along the span.
    """
    cut = _cross(39.25, -21.94, 4.0)
    midspan = (_H_X0 + _H_X1) / 2.0
    assert cut.station[0] / M_PER_IN == pytest.approx(39.25)
    assert abs(cut.station[0] / M_PER_IN - midspan) > 17.0


def test_a_partial_overlap_is_a_notch_depth_and_not_a_full_diameter_bore() -> None:
    """DU-B-ERV-R-SAUNA-SUP: a 4" duct 0.25" over the header top takes 1.75" off it."""
    cut = _cross(39.25, _H_Z1 + 0.25, 4.0)
    assert cut.diameter_in == pytest.approx(4.0)
    assert cut.through_in == pytest.approx(1.75)
    verdict = header_bore(cut.profile, cut.diameter_in, through_in=cut.through_in)
    assert verdict.kind == "notch"
    assert "notch off a face" in verdict.basis


def test_a_run_wholly_inside_the_member_loses_nothing_to_the_clip() -> None:
    cut = _cross(54.0, -27.21, 2.375)
    assert cut.through_in == pytest.approx(cut.diameter_in)
    assert header_bore(cut.profile, cut.diameter_in,
                       through_in=cut.through_in).kind == "bore"


def test_the_catlin_header_crossings_are_at_their_true_stations(
        catlin_model_ro) -> None:
    """§6's table, from the model. Every one of these printed 57.00" before 2026-09-22.

    Two rows of that table are gone because their runs moved, not because the reading did:
    `DU-B-ERV-R-SAUNA-SUP`'s 1.75" notch and `DU-B-ERV-R-GYM`'s 4.00" bore are the two the
    station fix made legible, and both were rerouted the same day.
    """
    from typehaus.checks.mep.routing_bores import _crossings

    stations = {tag: (cut.station[0] / M_PER_IN, cut.station[1] / M_PER_IN, cut.through_in)
                for tag, _wall, cuts in _crossings(_ctx(catlin_model_ro))
                for cut in cuts if cut.category == "header"}
    expected = {
        "DU-B-ERV-R-SAUNA-EXH": (45.00, 216.0, 3.25),
        "PR-B-KITCH-DRAIN": (54.00, 216.0, 2.375),
        "PR-M-S-BATH1-DRAIN": (54.77, 216.0, 3.50),
        "PR-B-MAIN-DRAIN": (72.00, 216.0, 4.50),
    }
    assert set(stations) == set(expected)
    for tag, want in expected.items():
        assert stations[tag] == pytest.approx(want, abs=0.01), tag


def test_the_two_rerouted_runs_cut_nothing_at_all(catlin_model_ro) -> None:
    """The reroute's own contract: not a smaller hole, NO hole.

    `DU-B-ERV-R-SAUNA-SUP` crosses `W-B-CW` in its west clear bay and `DU-B-ERV-R-GYM`
    crosses `W-B-CS3` in the 5 3/4" of open wall between `D-B-GYM`'s header and the double
    top plate, 7.8" from the nearest cripple either way. Neither appears in any bore
    finding — header, stud or plate.
    """
    from typehaus.checks.mep.routing_bores import _crossings

    ctx = _ctx(catlin_model_ro)
    walls = {"DU-B-ERV-R-SAUNA-SUP": "W-B-CW", "DU-B-ERV-R-GYM": "W-B-CS3"}
    for tag, wall, cuts in _crossings(ctx):
        if walls.get(tag) == wall.tag:
            assert not cuts, (tag, wall.tag, [c.member_key for c in cuts])


# --- §8 a header hole chart, read --------------------------------------------------------

#: Weyerhaeuser TJ-9000 (April 2021) p.26, ALLOWABLE HOLES, 1.55E TimberStrand LSL, the
#: 11 7/8" row — the chart §8 of the note transcribes. Round holes only; 8" off each
#: bearing; the middle 1/3 of the depth; two holes 2 x the larger diameter apart.
_LSL = "2-1.75x11.875 LSL"
_LSL_DEPTH_IN = 11.875


def _tj9000(**overrides) -> PublishedHole:
    row = dict(
        source="Weyerhaeuser TJ-9000 Trus Joist Beam, Header and Column Specifier's "
               "Guide (April 2021) p.26",
        table="ALLOWABLE HOLES — 1.55E TimberStrand LSL, 11 7/8\" row",
        member=_LSL, max_diameter=inch(3.625), zone_from_bearing=inch(8.0),
        depth_fraction=1.0 / 3.0, min_spacing_diameters=2.0, round_holes_only=True,
        load_basis="uniform and/or concentrated loads anywhere along the member",
        condition="round holes only; no holes in a header in plank orientation")
    row.update(overrides)
    return PublishedHole(**row)


def _charted(diameter_in: float, *, from_bearing_in: float = 12.0,
             edge_clear_in: float = 4.0, nearest_cut_in: float | None = None,
             through_in: float | None = None, chart: PublishedHole | None = None,
             profile: str = _LSL):
    return header_bore(profile, diameter_in, through_in=through_in,
                       chart=chart if chart is not None else _tj9000(),
                       from_bearing_in=from_bearing_in, span_in=36.0,
                       edge_clear_in=edge_clear_in, nearest_cut_in=nearest_cut_in)


def test_without_a_chart_an_engineered_header_is_still_the_fabricator_s_chart() -> None:
    """The refusal stands word for word; only a chart in hand reaches past it."""
    assert header_bore(_LSL, 2.0).ok is None
    assert "fabricator's chart" in header_bore(_LSL, 2.0).basis


def test_the_chart_is_read_before_the_engineered_refusal_and_publishes_a_pass() -> None:
    verdict = _charted(3.5)
    assert verdict.ok is True
    assert "3.62\"" in verdict.basis and "TJ-9000" in verdict.basis
    assert "round holes only" in verdict.basis  # the condition, printed


def test_a_hole_over_the_published_diameter_is_a_fail_with_the_margin() -> None:
    verdict = _charted(4.5)
    assert verdict.ok is False
    assert verdict.limit_in == pytest.approx(3.625)
    assert "by 0.88\"" in verdict.basis


def test_a_legal_hole_in_the_bearing_zone_is_still_a_fail() -> None:
    """PR-B-MAIN-DRAIN's case, and the reason a chart is a SHAPE and not one number."""
    verdict = _charted(3.0, from_bearing_in=3.0)
    assert verdict.ok is False
    assert "3.00\" from the nearest bearing" in verdict.basis


def test_a_hole_outside_the_depth_band_is_a_fail() -> None:
    """Every one of catlin's six sits within 1 1/4" of the header's bottom face."""
    verdict = _charted(3.0, edge_clear_in=1.04)
    assert verdict.ok is False
    assert "clear wood to the nearer face" in verdict.basis
    assert f'{_LSL_DEPTH_IN / 3.0:.2f}"' in verdict.basis


def test_two_holes_closer_than_the_chart_allows_fail_on_the_pair() -> None:
    """A per-run pass cannot see this: each hole is legal and the pair is not."""
    assert _charted(3.5, nearest_cut_in=7.5).ok is True
    verdict = _charted(3.5, nearest_cut_in=0.77)
    assert verdict.ok is False
    assert "nearest other hole" in verdict.basis


def test_the_spacing_is_two_diameters_of_the_LARGER_of_the_pair() -> None:
    """catlin's case: a 2.38" and a 3.50" hole 0.77" apart. Graded on the 2.38" alone the
    smaller hole would be asked for 4.75" and the larger for 7.00" — one pair, two answers.
    """
    verdict = header_bore(_LSL, 2.375, chart=_tj9000(), from_bearing_in=15.0, span_in=36.0,
                          edge_clear_in=4.0, nearest_cut_in=6.0, nearest_diameter_in=3.5)
    assert verdict.ok is False
    assert '7.00"' in verdict.basis


def test_a_notch_is_not_a_round_hole_and_the_chart_refuses_it() -> None:
    """The two sauna radials clip the header's top; no row of a round-hole chart reaches
    a notch, whatever its depth."""
    verdict = _charted(4.0, through_in=1.75)
    assert verdict.ok is False
    assert "ROUND HOLES ONLY" in verdict.basis


def test_a_retyped_header_drifts_off_the_row_and_grades_nothing() -> None:
    verdict = _charted(2.0, profile=HEADER)
    assert verdict.ok is None
    assert "does not describe this header" in verdict.basis
    assert HEADER in verdict.basis


def test_a_guard_the_crossing_cannot_answer_is_a_mismatch_not_agreement() -> None:
    verdict = _charted(2.0, from_bearing_in=None)
    assert verdict.ok is None
    assert "passed nothing to compare it against" in verdict.basis


def test_a_span_longer_than_the_row_was_read_at_drifts() -> None:
    verdict = header_bore(_LSL, 2.0, chart=_tj9000(span=inch(36.0)),
                          from_bearing_in=12.0, span_in=48.0, edge_clear_in=4.0)
    assert verdict.ok is None
    assert "this header spans" in verdict.basis


def test_published_hole_is_a_registered_dialect_constructor() -> None:
    assert "PublishedHole" in constructor_names()


def test_a_header_names_the_opening_it_was_framed_around(catlin_model_ro) -> None:
    """``child_key`` stays ``header-0`` — every section golden is keyed on it — so the
    door's tag rides beside it. Without it no chart can be found for a header at all."""
    from typehaus.checks.mep.routing_bores import _crossings

    openings = {tag: cut.opening_tag
                for tag, _wall, cuts in _crossings(_ctx(catlin_model_ro))
                for cut in cuts if cut.category == "header"}
    assert openings["PR-B-KITCH-DRAIN"] == "D-B-FURN"
    assert openings["PR-B-MAIN-DRAIN"] == "D-B-FURN"
    assert all(cut.child_key == "header-0"
               for wall in catlin_model_ro.walls for cut in wall.members
               if cut.opening_tag == "D-B-FURN" and cut.category == "header")


def test_the_bearing_is_the_jack_face_and_not_the_member_end(catlin_model_ro) -> None:
    """A header runs OVER its jacks, so its ends are not its bearings: PR-B-MAIN-DRAIN is
    4.50" from the member end and 3.00" from the bearing the chart measures from."""
    from typehaus.checks.mep.routing_bores import _crossings, _from_bearing_in

    ctx = _ctx(catlin_model_ro)
    for tag, _wall, cuts in _crossings(ctx):
        if tag != "PR-B-MAIN-DRAIN":
            continue
        cut = next(c for c in cuts if c.category == "header")
        assert cut.from_end_m / M_PER_IN == pytest.approx(4.50, abs=0.01)
        assert _from_bearing_in(ctx, cut) == pytest.approx(3.00, abs=0.01)
        assert cut.edge_clear_in == pytest.approx(0.60, abs=0.01)
        break
    else:  # pragma: no cover - the crossing is pinned above
        pytest.fail("PR-B-MAIN-DRAIN no longer crosses a header")


# --- §7 the plate tie --------------------------------------------------------------------

def test_a_penetration_as_wide_as_the_plate_is_not_a_plate_cut() -> None:
    """An 18" duct does not notch a 2x4 top plate; it interrupts it. Nine of catlin's
    thirteen were reported as "18.00" out of a 3.50" plate"."""
    verdict = top_plate_cut("2x4", 18.0, tie=False)
    assert verdict.ok is None
    assert "framed opening with a header over it" in verdict.basis


def test_the_tie_authored_is_a_pass_and_absent_is_a_fail() -> None:
    assert top_plate_cut("2x4", 2.375, tie=True).ok is True
    fail = top_plate_cut("2x4", 2.375, tie=False)
    assert fail.ok is False
    assert "no PlateTie in this model covers it" in fail.basis
    assert fail.remedy is not None and "16 ga" in fail.remedy


def test_not_looking_is_not_the_same_as_looking_and_finding_nothing() -> None:
    """``tie=None`` keeps the pre-schema reading: conditional, with the detail stated."""
    verdict = top_plate_cut("2x4", 2.375)
    assert verdict.ok is True and verdict.remedy is not None


def test_a_cut_under_half_the_plate_is_a_pass_with_or_without_a_tie() -> None:
    for tie in (None, True, False):
        assert top_plate_cut("2x6", 1.375, tie=tie).ok is True


def test_plate_tie_is_a_registered_element_and_a_dialect_constructor() -> None:
    assert "PlateTie" in element_kinds()
    assert "PlateTie" in constructor_names()


def test_plate_tie_carries_r602_6_1_s_own_numbers() -> None:
    tie = PlateTie(tag="PTIE-W-B-ESS-W", wall="W-B-ESS-W")
    assert tie.gauge == pytest.approx(0.054)
    assert tie.width.inches == pytest.approx(1.5)
    assert tie.lap.inches == pytest.approx(6.0)
    assert tie.nails_each_side == 8


def test_an_empty_covers_ties_every_cut_in_that_wall() -> None:
    from typehaus.checks.mep.routing_bores import plate_ties

    plan = SimpleNamespace(all_elements=lambda: [
        PlateTie(tag="PTIE-A", wall="W-A"),
        PlateTie(tag="PTIE-B", wall="W-B", covers=("PR-B-KITCH-DRAIN",)),
    ])
    ties = plate_ties(SimpleNamespace(model=SimpleNamespace(plan=plan)))
    assert ties == {"W-A": frozenset({"*"}), "W-B": frozenset({"PR-B-KITCH-DRAIN"})}


def test_catlin_s_one_real_plate_cut_fails_for_want_of_a_tie(catlin_model_ro) -> None:
    """The other nine are framed openings, which is a different question (§6).

    It was four until the wet-wall retype on 2026-09-20. Three of those cuts were legal
    the moment their plates became 2x6: the R602.6.1 tie line is half the plate depth, so
    it went 1.75" -> 2.75" and the sauna vent's two cuts and the kitchen drain's one fell
    under it. What is left is `PR-B-SAUNA-VENT` through `W-B-ESS-S`, the one wall in that
    group nothing bores hard enough to have been retyped.

    Ten UNKNOWNs since 2026-09-22: the tenth is that same vent SEVERING `W-B-ESS-W`'s 2x6
    plate — under the width line, but across the plate through its whole 1.50" thickness.
    """
    from typehaus.checks.mep.routing_bores import run_through_plate

    findings = run_through_plate(_ctx(catlin_model_ro))
    results = [f.result.value for f in findings]
    assert results.count("fail") == 1
    assert results.count("unknown") == 10

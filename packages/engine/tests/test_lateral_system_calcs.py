"""The shear split, against ``notes/entry_column_base_fixity.md`` §7.

The note is hand-worked in a separate pass and this module reproduces it term by term: the
wind bands of §7a, the propped-cantilever influence coefficients of §7b, the three
stiffnesses of §7c, the flexible/rigid test of §7d, the shares of §7e and the deck's and
panel's own limit states in §7f. A calc that only agrees with itself is not verified.

The pure functions are exercised on the note's own inputs rather than on the house, so a
model change moves the landed assertions at the foot and leaves the algebra alone — which is
the point of the split: an arithmetic regression and a geometry change should not look the
same.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.diaphragm_basis import (
    CHORD_E_PSI,
    DIAPHRAGM_ASPECT_BLOCKED,
    DIAPHRAGM_ASPECT_UNBLOCKED,
    FLEXIBLE_DRIFT_MULTIPLE,
    Line,
    cantilever_stiffness_lb_per_in,
    chord_force_lb,
    diaphragm_deflection_in,
    distribute,
    member_area_in2,
    rigidity_shares,
    round_inertia_in4,
    shear_wall_deflection_in,
    tributary_shares,
)
from typehaus.engineering.item import Status
from typehaus.engineering.lateral_system import KIND
from typehaus.engineering.roof_moment import _propped

#: §7c. ``PIER_CONCRETE_12`` specifies f'c 5,000 psi.
_E_CONCRETE_PSI = 57_000.0 * 5_000.0 ** 0.5

#: §7c's two shafts, base to head.
_SHAFT_IN = {"PT-BW-RE": 15.349 * 12.0, "PT-BW-RNE": 12.729 * 12.0}


# --- §7b: the propped shaft --------------------------------------------------------------


def test_the_propped_cantilever_matches_the_published_table() -> None:
    """``a = L/2`` is the row every structures table prints: ``R_B = 5P/16``, ``M_A = 3PL/16``.

    Checked against the closed form rather than against catlin, because an influence
    coefficient that drifted would move a base moment by a factor of three and still look
    like a number somebody computed.
    """
    moment, head, base = _propped(load_lb=1_000.0, at_ft=5.0, height_ft=10.0)
    assert head == pytest.approx(5_000.0 / 16.0, abs=0.5)
    assert moment == pytest.approx(3 * 1_000.0 * 10.0 / 16.0, abs=0.5)
    assert base == pytest.approx(1_000.0 - head, abs=0.5)


def test_a_load_standing_on_the_prop_leaves_the_base_no_moment() -> None:
    """Both degenerate ends, because a free body that is wrong there is wrong everywhere."""
    moment, head, base = _propped(1_000.0, at_ft=10.0, height_ft=10.0)
    assert moment == pytest.approx(0.0, abs=1e-6)
    assert head == pytest.approx(1_000.0, abs=1e-6)
    moment, head, base = _propped(1_000.0, at_ft=0.0, height_ft=10.0)
    assert moment == pytest.approx(0.0, abs=1e-6)
    assert base == pytest.approx(1_000.0, abs=1e-6)


@pytest.mark.parametrize("tag,arm_ft,expected", [("PT-BW-RE", 9.957, 523.4),
                                                 ("PT-BW-RNE", 7.337, 444.6)])
def test_the_canopy_drag_moments_reproduce_the_note(tag, arm_ft, expected) -> None:
    """§7b's two lines, at 181.5 lb of drag per column."""
    moment, _head, _base = _propped(181.5, arm_ft, _SHAFT_IN[tag] / 12.0)
    assert moment == pytest.approx(expected, rel=0.005)


def test_propping_a_shaft_never_makes_its_base_moment_larger() -> None:
    """The whole claim in one line: a held head cannot be worse than a free one."""
    for arm in (1.0, 3.0, 6.0, 9.0, 11.0):
        moment, _head, _base = _propped(500.0, arm, 12.0)
        assert moment < 500.0 * arm


# --- §7c: the stiffnesses ----------------------------------------------------------------


@pytest.mark.parametrize("tag,expected", [("PT-BW-RE", 1_970.0), ("PT-BW-RNE", 3_453.0)])
def test_the_column_stiffnesses_reproduce_the_note(tag, expected) -> None:
    """``3EI/h³`` on a 12" round at f'c 5,000 psi."""
    stiffness = cantilever_stiffness_lb_per_in(
        _E_CONCRETE_PSI, round_inertia_in4(12.0), _SHAFT_IN[tag])
    assert stiffness == pytest.approx(expected, rel=0.005)


def test_the_short_column_is_the_stiff_one_and_by_the_cube() -> None:
    """The fact that makes `PT-BW-RNE` the worse column even as the total demand fell.

    Stiffness goes as ``1/h³``, so the 12.73' shaft is 1.75 times the 15.35' one and takes
    the larger share of exactly the case nobody else resists.
    """
    short = cantilever_stiffness_lb_per_in(_E_CONCRETE_PSI, round_inertia_in4(12.0),
                                           _SHAFT_IN["PT-BW-RNE"])
    tall = cantilever_stiffness_lb_per_in(_E_CONCRETE_PSI, round_inertia_in4(12.0),
                                          _SHAFT_IN["PT-BW-RE"])
    assert short / tall == pytest.approx(
        (_SHAFT_IN["PT-BW-RE"] / _SHAFT_IN["PT-BW-RNE"]) ** 3, rel=0.001)


def test_the_panel_deflection_reproduces_the_note_term_by_term() -> None:
    """§7c's three terms of SDPWS 4.3.2 on `W-BW-SCREEN` at its settled 110.2 plf."""
    v, h, b, ga, da = 110.2, 4.083, 6.573, 11.0, 0.0625
    area = member_area_in2("2x4", 2)
    assert area == pytest.approx(10.5, abs=0.01)
    bending = 8.0 * v * h ** 3 / (CHORD_E_PSI * area * b)
    shear = v * h / (1000.0 * ga)
    rotation = h * da / b
    assert bending == pytest.approx(0.0006, abs=0.0002)
    assert shear == pytest.approx(0.0409, abs=0.0005)
    assert rotation == pytest.approx(0.0388, abs=0.0005)
    total = shear_wall_deflection_in(v, h, b, ga, area, da)
    assert total == pytest.approx(bending + shear + rotation, rel=1e-9)
    assert total == pytest.approx(0.0803, abs=0.001)
    assert (v * b) / total == pytest.approx(9_017.0, rel=0.02)


def test_a_panel_with_no_anchorage_slip_is_stiffer_and_the_term_is_the_reason() -> None:
    """The authored ``d_a`` is the term that dominates a squat panel, and this says so.

    It matters because it is the one input on ``ShearPanelSpec`` that is an assumption
    rather than a table read — 1/16" of bearing take-up — so a reader has to be able to see
    how much it is doing.
    """
    area = member_area_in2("2x4", 2)
    with_slip = shear_wall_deflection_in(110.2, 4.083, 6.573, 11.0, area, 0.0625)
    without = shear_wall_deflection_in(110.2, 4.083, 6.573, 11.0, area, 0.0)
    assert without < with_slip
    assert (with_slip - without) / with_slip > 0.40


def test_a_built_up_profile_is_not_counted_twice() -> None:
    """``CrossSection.width_m`` already carries a built-up profile's plies.

    ``"3-2x12"`` resolves 4.5" wide with ``plies == 3``, so multiplying by that field as
    well reads a 50 in² member as 152 — which would make a chord look three times stiffer
    than it is and quietly reduce a column's share of the shear.
    """
    assert member_area_in2("3-2x12", 1) == pytest.approx(4.5 * 11.25, abs=0.01)
    assert member_area_in2("2-2x8", 1) == pytest.approx(3.0 * 7.25, abs=0.01)
    assert member_area_in2("2x4", 2) == pytest.approx(2 * 1.5 * 3.5, abs=0.01)
    assert member_area_in2("6x6", 1) == pytest.approx(5.5 * 5.5, abs=0.01)


def test_the_deflection_equations_refuse_a_missing_input() -> None:
    """Refuses rather than defaults — the contract the whole module is built on."""
    area = member_area_in2("2x4", 2)
    assert shear_wall_deflection_in(100.0, 4.0, 0.0, 11.0, area, 0.0) is None
    assert shear_wall_deflection_in(100.0, 4.0, 6.0, 0.0, area, 0.0) is None
    assert diaphragm_deflection_in(100.0, 24.0, 0.0, 12.0, 5.25, 0.0) is None
    assert cantilever_stiffness_lb_per_in(0.0, 1.0, 1.0) is None
    assert member_area_in2("not-a-member", 0) is None


# --- §7d: rigid or flexible --------------------------------------------------------------


def test_the_diaphragm_deflection_reproduces_the_note() -> None:
    """§7d's N-S block: SDPWS 4.2.2 on 24' x 6' at 96.7 plf, with a plated splice at the peak."""
    delta = diaphragm_deflection_in(96.7, 24.0, 6.0, 12.0, 5.25, 0.03)
    assert delta == pytest.approx(0.0973, abs=0.001)


def test_the_flexible_rigid_test_is_run_at_the_tributary_split() -> None:
    """ASCE 7-16 §26.2, and the reason the distribution it is evaluated at is stated.

    The test asks whether assuming the deck FLEXIBLE is self-consistent, so it is evaluated
    at the deflections the flexible idealization itself produces. Run at the rigid shares it
    would depend on the assumption under test and could oscillate — rigid shares saying
    flexible, tributary shares saying rigid, and nothing settling.
    """
    lines = [
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=9_017.0),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_970.0),
        Line(tag="RNE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=3_453.0),
    ]
    result = distribute("y", 1_160.3, lines, 24.0, 6.0, 12.0, 5.25, 0.03)
    assert result is not None
    assert result.rigid is True
    assert result.diaphragm_deflection_in == pytest.approx(0.0973, abs=0.002)
    assert result.average_drift_in == pytest.approx(0.0986, abs=0.002)
    assert "RIGID and the split is by RIGIDITY" in result.basis


def test_a_limp_deck_flips_the_verdict_and_the_split_with_it() -> None:
    """The other side of the same test, because a threshold nobody crosses is not tested.

    Soften the deck far enough and it stops carrying load across the building: the lines
    revert to independent supports under their own tributary, and the two columns on one
    station go from 14%/24% to 25% each.
    """
    lines = [
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=9_017.0),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_970.0),
        Line(tag="RNE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=3_453.0),
    ]
    limp = distribute("y", 1_160.3, lines, 24.0, 6.0, 0.4, 5.25, 0.03)
    assert limp is not None
    assert limp.rigid is False
    assert limp.diaphragm_deflection_in > FLEXIBLE_DRIFT_MULTIPLE * limp.average_drift_in
    assert limp.shares["RE"] == pytest.approx(0.25, abs=0.005)
    assert limp.shares["RNE"] == pytest.approx(0.25, abs=0.005)
    assert limp.shares["panel"] == pytest.approx(0.50, abs=0.005)


def test_a_line_with_no_stiffness_refuses_the_whole_distribution() -> None:
    """A line silently worth zero hands its share to its neighbours, which is the one
    failure mode a distribution must not have."""
    lines = [
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=None),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_970.0),
    ]
    assert rigidity_shares(lines) is None
    assert distribute("y", 1_000.0, lines, 24.0, 6.0, 12.0, 5.25, 0.0) is None


# --- §7e: the shares ----------------------------------------------------------------------


def test_the_shares_reproduce_the_note() -> None:
    """§7e's two blocks. The E-W case has no panel in it at all, and that is the point."""
    ns = rigidity_shares([
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=9_977.0),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_568.0),
        Line(tag="RNE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_568.0),
    ])
    assert ns is not None
    assert ns["RE"] == pytest.approx(0.120, abs=0.003)
    assert ns["RNE"] == pytest.approx(0.120, abs=0.003)
    assert ns["panel"] == pytest.approx(0.761, abs=0.003)

    # ** THE E-W CASE IS 50/50 NOW, AND IT IS 50/50 UNDER TRIBUTARY TOO. ** §6a put both
    # bases on one plane, so the two columns have the same shaft and the same 3EI/h³. That
    # is what makes the governing case indifferent to §7d's rigid/flexible call.
    ew = rigidity_shares([
        Line(tag="RE", kind="cast column", station_ft=37.5, stiffness_lb_per_in=1_568.0),
        Line(tag="RNE", kind="cast column", station_ft=42.48, stiffness_lb_per_in=1_568.0),
    ])
    assert ew is not None
    assert ew["RE"] == pytest.approx(0.500, abs=0.003)
    assert ew["RNE"] == pytest.approx(0.500, abs=0.003)


def test_tributary_splits_a_shared_station_between_its_peers() -> None:
    """A flexible deck delivers load to a POSITION and a rigid one to a STIFFNESS.

    Two columns on one station are one support under tributary and two under rigidity, and
    getting that backwards would quietly halve or double a column's demand.
    """
    lines = [
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=9_017.0),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_970.0),
        Line(tag="RNE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=3_453.0),
    ]
    shares = tributary_shares(lines)
    assert shares["panel"] == pytest.approx(0.5, abs=1e-9)
    assert shares["RE"] == pytest.approx(0.25, abs=1e-9)
    assert shares["RNE"] == pytest.approx(0.25, abs=1e-9)
    assert sum(shares.values()) == pytest.approx(1.0, abs=1e-9)


def test_the_chord_force_reproduces_the_note() -> None:
    """§7f: ``V L / (8 W)`` — a deep beam's flange force at midspan."""
    assert chord_force_lb(1_189.4, 24.0, 6.0) == pytest.approx(594.7, rel=0.005)
    assert chord_force_lb(1_000.0, 10.0, 0.0) is None


# --- the landed house ---------------------------------------------------------------------


def test_the_canopy_record_reproduces_section_7f(catlin_ctx) -> None:
    """§7f's table, on the model. PASS, and one row of it passes by exactly nothing."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    assert record.status is Status.OK, record.summary
    states = {state.name: state for state in record.limit_states}

    aspect = states["diaphragm span-to-depth"]
    assert aspect.demand == pytest.approx(4.0, abs=0.01)
    assert aspect.capacity == pytest.approx(DIAPHRAGM_ASPECT_BLOCKED, abs=1e-9)
    assert aspect.ok, "at the limit, not past it"
    # ** THE BLOCKING IS LOAD-BEARING IN THE LITERAL SENSE. ** Unblocked the limit is 3.0
    # and this deck is a FAIL, and there is nothing to trade: the depth is the passage and
    # the span is the columns.
    assert aspect.demand > DIAPHRAGM_ASPECT_UNBLOCKED

    assert states["diaphragm unit shear"].demand == pytest.approx(150.8, rel=0.01)
    assert states["W-BW-SCREEN unit shear"].demand == pytest.approx(149.2, rel=0.01)
    assert states["W-BW-SCREEN aspect ratio"].demand == pytest.approx(0.621, abs=0.005)
    holdown = states["W-BW-SCREEN hold-down tension"]
    assert holdown.demand == pytest.approx(609.3, rel=0.01)
    assert holdown.capacity == pytest.approx(2_190.0, abs=1.0), "the ABU66SS already there"


def test_the_chord_force_is_printed_and_not_graded(catlin_ctx) -> None:
    """A chord is a wood member in tension with a splice in it and this engine holds no NDS
    reference design values for one. Printed as an input and named in the notes — not put in
    ``missing``, because the calculation ran; this is a state it does not reach. Since
    2026-09-22 the note also says WHO designs it (§8b, and the test below)."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["chord_force_y"] == pytest.approx(594.7, rel=0.01)
    assert not record.missing
    assert any("PRINTED HERE AND DESIGNED BY THE FABRICATOR" in note
               for note in record.notes)
    assert not [s for s in record.limit_states if "chord" in s.name]


def test_the_collectors_are_named_and_they_resolve(catlin_ctx) -> None:
    """A collector that is not in the model is a load path that is not drawn.

    The whole reduction the declaration buys rests on the deck's shear reaching each
    resisting line, and what carries it there is a real member with a real connection at
    each end. catlin names the two headers; both resolve, and if either stopped the record
    would go INCOMPLETE rather than keep publishing a reduced demand.
    """
    roof = catlin_ctx.plan.by_tag("RF-BW-CANOPY")
    assert roof.diaphragm.collector_refs == ("BM-BW-RW", "BM-BW-RE")
    assert all(catlin_ctx.plan.by_tag(t) is not None
               for t in roof.diaphragm.collector_refs)
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    assert not record.missing
    assert any("COLLECTOR IS A CLAIM WITH TAGS ON IT" in note for note in record.notes)


def test_a_roof_with_no_declared_diaphragm_raises_no_item(catlin_ctx) -> None:
    """The claim is what creates the obligation. A deck whose sheathing is only sheathing
    carries none, and inventing one for it would report a defect in an ordinary roof."""
    keys = {k for k in catlin_ctx.engineering if k.startswith(f"{KIND}/")}
    assert keys == {f"{KIND}/RF-BW-CANOPY"}


# --- §8b: the chord is delegated, not graded ---------------------------------------------


def test_the_chord_force_goes_on_the_truss_order(catlin_ctx) -> None:
    """§8b. A truss's own top chord is the chord, so the axial force is the FABRICATOR's.

    Combined axial and bending at a plated section is the component designer's chart, and
    this engine holds no NDS reference design values for a chord anyway — so the 595 lb rides
    the existing ``rafter/<roof>`` deferral rather than becoming a limit state here. What the
    record must still do is print the number and name where it went.
    """
    from typehaus.engineering.deferred import DEFERRALS

    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["chord_force_y"] == pytest.approx(594.7, rel=0.01)
    assert not [s for s in record.limit_states if "chord" in s.name.lower()]
    delegated = [n for n in record.notes if "DESIGNED BY THE FABRICATOR" in n]
    assert delegated and "rafter/RF-BW-CANOPY" in delegated[0]
    assert "0.030" in delegated[0], "the splice slip the rigid/flexible call rests on"
    deliverable = DEFERRALS["rafter"].deliverable
    assert "TOP CHORDS" in deliverable and "chord_splice_slip" in deliverable


# --- §8c-§8e: the three collectors --------------------------------------------------------


def test_the_west_line_needs_no_drag_strut(catlin_ctx) -> None:
    """§8c. The panel is LONGER than the deck's depth, so the drag length is zero."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    row = next(s for s in record.limit_states
               if s.name.startswith("W-BW-SCREEN collector"))
    assert row.demand == pytest.approx(6.0, abs=0.01), "the deck's depth on that line"
    assert row.capacity >= row.demand - 1e-9, "the panel runs the whole of it"
    assert "0.000' and the drag force" in row.citation
    assert row.is_detailing, "a zero force is not a governing state"


def test_the_east_collector_grades_the_connection_not_the_member(catlin_ctx) -> None:
    """§8d. The HETA20Z pair's three-term interaction at the head, N-S, torsion included."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    row = next(s for s in record.limit_states
               if s.name == "PT-BW-RE collector end connection, N-S")
    assert row.demand == pytest.approx(0.443, abs=0.01)
    assert row.capacity == pytest.approx(1.0, abs=1e-9)
    assert "FL11473" in row.citation and "2,560" in row.citation
    # The in-plane force is the DIRECT share with the torsional increment on it, not either
    # on its own: 142.3 + 200.2 = 342.5 lb.
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["collector_reaction_PT-BW-RE_y"] == pytest.approx(342.5, rel=0.01)


def test_the_north_line_collector_is_the_strap_line(catlin_ctx) -> None:
    """§8e. No canopy member stands on the north line, so seven LSTA24s collect it.

    17.1 plf and 58.7 lb per strap against ESR-2105 Table 3's 1,235 lb — the "near 18 plf"
    the authoring comment estimated, computed. The record must also SAY that this path
    crosses into the neighbouring roof, because it is the one direction in which the canopy
    is not freestanding.
    """
    from typehaus.hardware.catalog import allowable_for_model

    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    row = next(s for s in record.limit_states if s.name.startswith("LSTA24 strap line"))
    assert row.demand == pytest.approx(58.7, abs=0.5)
    assert row.capacity == pytest.approx(allowable_for_model("LSTA24").uplift_lb, abs=1.0)
    assert row.capacity == pytest.approx(1_235.0, abs=1.0), "ESR-2105 Table 3, LSTA24 row"
    assert "17.1 plf" in row.citation
    assert any("CROSSES INTO RF-GARAGE" in note for note in record.notes)


# --- §8f: the concrete under the hold-down ------------------------------------------------


def test_the_holdown_anchor_is_edge_limited_and_that_is_the_calculation() -> None:
    """§8f. A 5/8" x 10" bolt at the centre of a 12" round pier, ACI 318-19 Ch. 17.

    ``c_a`` is 6" on every side at once, so the projected area is the pier's own section and
    ``A_Nc/A_Nco`` is 0.20 — the whole of the answer. Both readings of §17.6.2 are computed
    and the LOWER is graded, which is the unreduced one here.
    """
    from typehaus.engineering.holdown_anchor import (
        breakout_shear,
        breakout_tension,
        pullout_tension,
        round_pier_anchor,
        side_face_blowout_applies,
        steel_tension,
    )

    anchor = round_pier_anchor("PT-BW-GW", 12.0, 5_000.0)
    assert anchor.h_ef_in == pytest.approx(7.89, abs=0.02), "derived, not assumed"
    assert anchor.c_a_in == pytest.approx(6.0, abs=1e-9)
    capacity, ratio, how = breakout_tension(anchor)
    assert ratio == pytest.approx(0.202, abs=0.005)
    assert capacity == pytest.approx(4_528.0, rel=0.01)
    assert "§17.6.2.1.2 h_ef' would give 7,464" in how, "the code reading, printed beside it"
    assert pullout_tension(anchor) == pytest.approx(18_784.0, rel=0.01)
    assert steel_tension(anchor) == pytest.approx(9_662.0, rel=0.01)
    assert breakout_shear(anchor)[0] == pytest.approx(3_661.0, rel=0.01)
    assert not side_face_blowout_applies(anchor), "§17.6.4 wants h_ef > 2.5 c_a1"


def test_the_anchor_rows_land_on_the_record(catlin_ctx) -> None:
    """§8f's demands: the overturning couple PLUS the column's net roof uplift, at 0.6W."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    tension = next(s for s in record.limit_states if "anchor tension" in s.name)
    shear = next(s for s in record.limit_states if "anchor shear" in s.name)
    both = next(s for s in record.limit_states if "interaction" in s.name)
    assert tension.demand == pytest.approx((609.3 + 433.2) / 0.6, rel=0.01)
    assert shear.demand == pytest.approx(980.7 / 2 / 0.6, rel=0.01)
    assert tension.ratio == pytest.approx(0.384, abs=0.01)
    assert shear.ratio == pytest.approx(0.223, abs=0.01)
    assert both.demand == pytest.approx((tension.ratio + shear.ratio) / 1.2, abs=0.005)
    assert both.ratio < 1.0
    assert any("ESR-1622 §5.6" in note or "out of scope" in note for note in record.notes)


# --- §8g: torsion --------------------------------------------------------------------------


def test_the_centre_of_rigidity_is_not_under_the_load(catlin_ctx) -> None:
    """§8g. e = 8.20', M_t = 9,751 lb-ft — the moment the rigidity split left over."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["torsion_eccentricity_y"] == pytest.approx(8.20, abs=0.05)
    assert inputs["torsion_moment_y"] == pytest.approx(9_751.0, rel=0.01)
    # E-W is nearly centred, and that is a fact about the geometry rather than an omission.
    assert abs(inputs["torsion_eccentricity_x"]) < 0.25


def test_torsion_is_carried_by_the_pair_itself_and_takes_the_split_back_to_statics() -> None:
    """§8g's arithmetic on the note's own lines, not on the house.

    Two N-S lines at 6' and 30' and two E-W lines 4.98' apart: 98.6% of ``J`` is the N-S
    pair's own couple, and once the term is in, the panel lands within a hair of the lever
    rule the deck's statics demanded all along.
    """
    from typehaus.engineering.torsion import torsional_distribution

    along = [
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=9_970.5,
             x_ft=6.0, y_ft=39.93),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_567.7,
             x_ft=30.0, y_ft=37.5),
        Line(tag="RNE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_567.7,
             x_ft=30.0, y_ft=42.479),
    ]
    across = [line for line in along if line.kind == "cast column"]
    result = torsional_distribution("y", 1_189.41, 19.937, along, across)
    assert result is not None and result.stable
    assert result.centre_ft == pytest.approx(11.742, abs=0.01)
    assert result.moment_lb_ft == pytest.approx(9_748.0, rel=0.01)
    assert result.along_fraction == pytest.approx(0.986, abs=0.003)
    total = {tag: result.direct_lb[tag] + result.torsional_lb[tag] for tag in result.direct_lb}
    assert sum(total.values()) == pytest.approx(1_189.41, rel=1e-6), "equilibrium"
    assert total["panel"] == pytest.approx(504.4, rel=0.01)
    assert total["RE"] == pytest.approx(342.5, rel=0.01)
    # The lever rule for a load at 19.937' between lines at 6' and 30' is the sanity check.
    assert total["panel"] / 1_189.41 == pytest.approx((30.0 - 19.937) / 24.0, abs=0.01)


def test_a_relief_is_not_credited_and_an_increment_is() -> None:
    """The panel is relieved by nearly half and is still graded at its direct share."""
    from typehaus.engineering.torsion import torsional_distribution

    along = [
        Line(tag="panel", kind="shear panel", station_ft=6.0, stiffness_lb_per_in=9_970.5,
             x_ft=6.0, y_ft=39.93),
        Line(tag="RE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_567.7,
             x_ft=30.0, y_ft=37.5),
        Line(tag="RNE", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_567.7,
             x_ft=30.0, y_ft=42.479),
    ]
    result = torsional_distribution("y", 1_189.41, 19.937, along,
                                    [line for line in along if line.kind == "cast column"])
    assert result is not None
    assert result.torsional_lb["panel"] < 0.0
    assert result.multipliers["panel"] == pytest.approx(1.0, abs=1e-9)
    assert result.multipliers["RE"] == pytest.approx(2.41, abs=0.02)


def test_two_lines_on_one_station_with_nothing_across_are_a_mechanism() -> None:
    """The stability half of the row: torsion is a stability statement before it is a number.

    A pair of lines on ONE station and nothing perpendicular cannot react a torsional moment
    at all, and the row says so rather than dividing by a J of zero.
    """
    from typehaus.engineering.torsion import torsional_distribution

    along = [
        Line(tag="A", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_567.7,
             x_ft=30.0, y_ft=37.5),
        Line(tag="B", kind="cast column", station_ft=30.0, stiffness_lb_per_in=1_567.7,
             x_ft=30.0, y_ft=42.479),
    ]
    result = torsional_distribution("y", 1_000.0, 18.0, along, [])
    assert result is not None and not result.stable
    assert "NO TORSIONAL RESISTANCE" in result.how
    assert all(value == 0.0 for value in result.torsional_lb.values())
    # The same lines, with the OTHER axis's pair supplying the couple, are stable — which is
    # exactly what the canopy has and is why its torsion row is a number rather than a red.
    stable = torsional_distribution("y", 1_000.0, 18.0, along, along)
    assert stable is not None and stable.stable


def test_the_canopy_record_still_passes_with_every_new_row_on_it(catlin_ctx) -> None:
    """The verdict, stated: nothing added here governs, and span-to-depth still does."""
    record = catlin_ctx.engineering[f"{KIND}/RF-BW-CANOPY"]
    assert record.status is Status.OK, record.summary
    governing = record.governing
    assert governing is not None and governing.name == "diaphragm span-to-depth"
    assert governing.ratio == pytest.approx(1.0, abs=0.01)
    graded = [s for s in record.limit_states if not s.is_detailing]
    assert all(s.ratio <= 1.0 for s in graded), [s.name for s in graded if s.ratio > 1.0]

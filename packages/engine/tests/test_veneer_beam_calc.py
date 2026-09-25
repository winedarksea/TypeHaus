"""``veneer_beam/W-SG-BRKBM`` against ``notes/sunken_garden_veneer_beam.md`` §6.

Since 2026-09-22 the record reads the 17'-0" court (§6i): design span 17.5', wythe 268.86
plf, wu 687.03 plf. The pure-arithmetic test at the end still runs the old 19.5' inputs,
which is a function check and not a house one.

Every number below was worked by hand in the note, at the model's own geometry, before this
file existed. Inputs are read off the resolved model where the test asserts on them, so a
geometry move fails here loudly rather than silently re-basing the oracle.
"""

from __future__ import annotations

import pytest

from typehaus.engineering import Status
from typehaus.engineering.item import Scope
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import bar_count_for_roles, bar_for_roles
from typehaus.engineering.retaining_court.veneer_beam import (
    deflection_after_attachment,
    torsion_design,
)
from typehaus.engineering.veneer_beam import (
    _one,
    carried_wythes,
    enumerate_veneer_beams,
    veneer_beams,
)
from typehaus.engineering.veneer_beam_anchorage import confining_tie_area, hooked_anchorage
from typehaus.model import EndRestraint, HookConfinement
from typehaus.quantities import inch


@pytest.fixture(scope="module")
def record(catlin_plan, catlin_model_ro):
    ctx = EngineeringContext(plan=catlin_plan, model=catlin_model_ro)
    from typehaus.engineering.veneer_beam import compute

    records = {r.key: r for r in compute(ctx)}
    return ctx, records["W-SG-BRKBM"]


def _state(record, name):
    return next(s for s in record.limit_states if s.name.startswith(name))


def test_the_relation_finds_the_beam_and_the_wythe(record) -> None:
    ctx, _ = record
    assert enumerate_veneer_beams(ctx) == ["W-SG-BRKBM"]
    assert carried_wythes(ctx) == ["W-B-BRICK"]


def test_inputs_are_the_concrete_layer_and_the_drawn_wythe(record) -> None:
    """§6a / §6i: 12" of concrete (not the 14" assembly), 17'-0" clear, 6" bearing, and the
    shorter wythe (top at −13 1/3", 89.104" tall): 268.86 plf."""
    _, rec = record
    inputs = {q.name: q.value for q in rec.inputs}
    assert inputs["section_width"] == pytest.approx(12.0)
    assert inputs["section_depth"] == pytest.approx(17.75)
    assert inputs["clear_span"] == pytest.approx(17.0)
    assert inputs["bearing"] == pytest.approx(6.0)
    assert inputs["wythe_load"] == pytest.approx(268.86, abs=0.01)
    assert inputs["self_weight"] == pytest.approx(221.875)
    assert inputs["eccentricity"] == pytest.approx(4.1275, abs=1e-3)
    assert rec.scope is Scope.SCREENING


def test_strength_rows_reproduce_the_hand_pass(record) -> None:
    """§6b and §6c at U = 1.4D, at §6i's 17.5' span: Mu 687.03 × 17.5²/8 = 26,300;
    Vu 687.03 × 17.5/2 = 6,011.5; Tu 1.4 × 268.86 × (4.1275/12) × 8.75 = 1,132.9 ft-lb, so
    At/s and the torsion term scale by 1,132.9/1,337.85 from §6c."""
    _, rec = record
    flex = _state(rec, "flexure")
    assert flex.demand == pytest.approx(26300, abs=1)
    assert flex.capacity == pytest.approx(60747, abs=1)
    assert _state(rec, "minimum flexural steel").demand == pytest.approx(0.639, abs=1e-3)
    shear = _state(rec, "one-way shear")
    assert shear.demand == pytest.approx(6011.5, abs=1)
    assert shear.capacity == pytest.approx(19171, abs=1)
    tt = _state(rec, "torsion transverse")
    assert tt.demand == pytest.approx(0.001743, abs=2e-6)
    assert tt.capacity == pytest.approx(0.0220)
    limit = _state(rec, "torsion section limit")
    assert limit.demand == pytest.approx(46.36, abs=0.01)
    assert limit.capacity == pytest.approx(530.3, abs=0.1)


def test_torsion_detailing_closes(record) -> None:
    """§6c: #3 closed hoops @ 5" against §9.7.6.3.3's ph/8 = 5.25"."""
    _, rec = record
    hoops = _state(rec, "closed hoop spacing")
    assert (hoops.demand, hoops.capacity) == (pytest.approx(5.0), pytest.approx(5.25))
    assert hoops.is_detailing and hoops.ok
    assert _state(rec, "minimum transverse").ratio == pytest.approx(0.241, abs=1e-3)
    longitudinal = _state(rec, "longitudinal steel")
    assert longitudinal.demand == pytest.approx(1.684, abs=1e-3)
    assert longitudinal.capacity == pytest.approx(2.26)
    assert _state(rec, "longitudinal bar spacing").demand == pytest.approx(6.1875)


def test_deflection_is_two_rows_and_tms_l_over_600_is_the_strict_one(record) -> None:
    """§6i: after-attachment 0.0786" at the claimed α 0.25 on 210" — ℓ/600 0.225,
    ℓ/480 0.180."""
    _, rec = record
    tms = _state(rec, "deflection after the wythe is attached, TMS")
    assert tms.demand == pytest.approx(0.07861, abs=1e-5)
    assert tms.capacity == pytest.approx(0.350)
    assert tms.ratio == pytest.approx(0.225, abs=1e-3)
    assert "TMS 402-22 §13.1.2.3" in tms.citation
    aci = _state(rec, "deflection after the wythe is attached, ACI")
    assert aci.demand == pytest.approx(0.07861, abs=1e-5)
    assert (aci.capacity, aci.ratio) == (pytest.approx(0.4375), pytest.approx(0.180, abs=1e-3))
    # The old NOT-GRADED note is gone; the credit says what it is instead.
    assert not any("NOT GRADED: TMS" in note for note in rec.notes)
    assert any("SERVICEABILITY ONLY" in note and "α 0.25 is CLAIMED" in note
               for note in rec.notes)


def _stripped(record):
    """The same record with ``end_restraint`` taken off the beam — a simple span again."""
    ctx, _ = record
    beam, carried = veneer_beams(ctx)[0]
    return _one(ctx, beam.model_copy(update={"end_restraint": None}), carried)


def test_the_fixity_credit_is_never_assumed(record) -> None:
    """Strip `end_restraint` and the beam is a simple span again: ℓ/600 goes back to the
    uncredited 0.110" (§6i). It was 1.242 and OVER at 19'-0"; at 17'-0" the simple span
    closes on its own, so the credit is reported rather than needed — and still never
    assumed: the stripped record carries the simple-span number, not the credited one."""
    stripped = _stripped(record)
    tms = _state(stripped, "deflection after the wythe is attached, TMS")
    assert tms.demand == pytest.approx(0.1101, abs=1e-4)
    assert tms.ratio == pytest.approx(0.315, abs=1e-3)
    assert tms.ok and stripped.status is Status.OK
    assert _state(stripped, "deflection after the wythe is attached, ACI").ratio == (
        pytest.approx(0.252, abs=1e-3))
    # No joint rows and no credit note without the authored claim.
    assert not [s for s in stripped.limit_states if "end moment into" in s.name]
    assert not any("SERVICEABILITY ONLY" in note for note in stripped.notes)


def test_the_fixity_credit_buys_no_strength(record) -> None:
    """Every STRENGTH row is identical with and without the credit — §6f's whole safety."""
    _, rec = record
    stripped = _stripped(record)
    for name in ("flexure, simple span", "minimum flexural steel", "one-way shear",
                 "torsion transverse", "torsion section limit",
                 "longitudinal steel, flexure + torsion"):
        credited, bare = _state(rec, name), _state(stripped, name)
        assert (credited.demand, credited.capacity) == (bare.demand, bare.capacity), name
    assert _state(rec, "flexure, simple span").ratio == pytest.approx(0.433, abs=1e-3)
    assert "no end fixity credited" in _state(rec, "flexure, simple span").citation


def test_the_joint_receives_the_end_moment(record) -> None:
    """§6f / §6i: M_end 4,383 ft-lb — 0.072 in the beam, 0.287 into each wall as PLAIN
    concrete over b_eff 36", and V = 12 M/d = 3,492 lb of end-moment shear (0.106). The
    elastic bound is printed too, at the AUTHORED ``elastic_fixity`` 0.487 (§6i)."""
    _, rec = record
    negative = _state(rec, "negative flexure at the supports")
    assert negative.demand == pytest.approx(4383, abs=1)
    assert (negative.capacity, negative.ratio) == (pytest.approx(60747, abs=1),
                                                   pytest.approx(0.072, abs=1e-3))
    for wall in ("W-SG-W1", "W-SG-E1"):
        moment = _state(rec, f"end moment into {wall}")
        assert moment.demand == pytest.approx(4383, abs=1)
        assert moment.capacity == pytest.approx(15273.5, abs=1)
        assert moment.ratio == pytest.approx(0.287, abs=1e-3)
        assert "Table 14.5.2.1" in moment.citation and "b_eff 36\"" in moment.citation
        # Graded at the elastic bound as well, so the derate spends nobody else's capacity:
        # 0.487 × 687.03 × 17.5²/12 = 8,539 ft-lb against 15,273: §6i's elastic α at 17.5'.
        assert "α 0.487" in moment.citation
        assert "8,539 ft-lb, d/c 0.559" in moment.citation
        shear = _state(rec, f"end-moment shear into {wall}")
        assert shear.demand == pytest.approx(3492, abs=1)
        assert shear.capacity == pytest.approx(32933.5, abs=1)
        assert shear.ratio == pytest.approx(0.106, abs=1e-3)


def test_end_restraint_round_trips() -> None:
    restraint = EndRestraint(fixity=0.25, elastic_fixity=0.514,
                             effective_width=inch(36.0), source="§6f")
    again = EndRestraint.model_validate(restraint.model_dump())
    assert again == restraint
    assert EndRestraint(fixity=0.0).elastic_fixity is None


def test_end_restraint_closes_on_ties_and_footing_dowels(record) -> None:
    """§6e (2026-09-21): top-y hooked with Ath 0.80 → ψr 1.0, 7.11" in 9.00"; bottom-y on
    3 #5 dowels cast straight in FT-SG-W1/E1, 21.21" in 30.00"."""
    _, rec = record
    assert rec.status is Status.OK, rec.missing
    assert not rec.missing
    for wall in ("W-SG-W1", "W-SG-E1"):
        hook = _state(rec, f"hooked development of top-y into {wall}")
        assert (hook.demand, hook.capacity) == (pytest.approx(7.11, abs=0.01), pytest.approx(9.0))
        assert hook.ratio == pytest.approx(0.790, abs=1e-3)
        assert "Ath 0.800 in² vs 0.4 Ahs 0.372" in hook.citation
    for footing in ("FT-SG-W1", "FT-SG-E1"):
        dowel = _state(rec, f"dowel development of bottom-y into {footing}")
        assert dowel.demand == pytest.approx(21.21, abs=0.01)
        assert dowel.capacity == pytest.approx(30.0)
        assert dowel.ratio == pytest.approx(0.707, abs=1e-3)
        steel = _state(rec, f"dowel steel against bottom-y at {footing}")
        assert (steel.demand, steel.capacity) == (pytest.approx(0.93), pytest.approx(0.93))
        assert steel.is_detailing
    # The class B lap is a graded row since 2026-09-22, not a note: 27.58" in the authored
    # 30" projection (66 + 30 = one 8'-0" stock bar), and the hoops' 135° hook with it.
    assert not any("27.58\"" in note for note in rec.notes)
    for footing in ("FT-SG-W1", "FT-SG-E1"):
        lap = _state(rec, f"dowel lap of bottom-y past the {footing} joint")
        assert (lap.demand, lap.capacity) == (pytest.approx(27.58, abs=0.01),
                                              pytest.approx(30.0))
        assert lap.is_detailing and lap.ok
    hook = _state(rec, "closed hoop hook angle")
    assert (hook.demand, hook.capacity) == (135.0, 135.0)
    assert hook.is_detailing and hook.ok
    # Deflection has stopped governing; the hooked development does (0.790 > 0.433).
    assert _state(rec, "hooked development of top-y into W-SG-W1").ratio == max(
        s.ratio for s in rec.limit_states if not s.is_detailing)


def test_tie_credit_follows_section_25_4_3_3() -> None:
    """Two #4 perpendicular ties @ 5" count (Ath 0.80); one tie, or 5.25" apart, count nothing."""
    ties = HookConfinement(bar=4, count=2, spacing=inch(5.0), legs=2, orientation="perpendicular")
    assert confining_tie_area(ties, hooked_bar=5, ldh_in=7.11) == (pytest.approx(0.80), [])
    one = ties.model_copy(update={"count": 1})
    wide = ties.model_copy(update={"spacing": inch(5.25)})
    assert confining_tie_area(one, hooked_bar=5, ldh_in=7.11)[0] == 0.0
    assert confining_tie_area(wide, hooked_bar=5, ldh_in=7.11)[0] == 0.0
    assert confining_tie_area(None, hooked_bar=5, ldh_in=7.11)[0] == 0.0
    ldh, _s, psi_r_one, _c = hooked_anchorage(
        bar=5, count=3, width_in=12.0, cover_in=2.0, hoop_diameter_in=0.375,
        side_cover_in=6.19, fc_psi=5000.0, tie_area_in2=0.371)
    assert not psi_r_one and ldh == pytest.approx(11.38, abs=0.01)


def test_hooked_anchorage_reproduces_section_6e() -> None:
    """ψr 1.6 at 3.31" spacing → 11.38"; spread past 6db (ψr 1.0) → 7.11" (§6e, §6b)."""
    ldh, spacing, spaced, covered = hooked_anchorage(
        bar=5, count=3, width_in=12.0, cover_in=2.0, hoop_diameter_in=0.375,
        side_cover_in=6.19, fc_psi=5000.0)
    assert spacing == pytest.approx(3.3125)
    assert (spaced, covered) == (False, True)
    assert ldh == pytest.approx(11.38, abs=0.01)
    ldh, _s, spaced, _c = hooked_anchorage(
        bar=5, count=2, width_in=12.0, cover_in=2.0, hoop_diameter_in=0.375,
        side_cover_in=6.19, fc_psi=5000.0)
    assert spaced and ldh == pytest.approx(7.11, abs=0.01)


def test_the_soft_joint_gap_is_named_with_its_geometry(record) -> None:
    _, rec = record
    note = next(n for n in rec.notes if n.startswith("SOFT JOINTS"))
    # 3/8" at the east end since 2026-09-22 — N-B-BRICK-E moved west so BIA TN 18A's
    # sealant joint over compressible filler has somewhere to go at BOTH ends.
    assert "4.00\" clear of W-SG-W1" in note and "0.38\" clear of W-SG-E1" in note


def test_pure_arithmetic_matches_the_note_without_the_model() -> None:
    tors = torsion_design(tu_ftlb=1337.854, vu_lb=6918.18, width_in=12.0, depth_in=17.75,
                          d_in=15.0625, cover_in=2.0, hoop_diameter_in=0.375,
                          hoop_leg_area_in2=0.11, hoop_spacing_in=5.0, fc_psi=5000.0)
    assert tors.ph_in == pytest.approx(42.0)
    assert tors.al_required_in2 == pytest.approx(1.0451, abs=1e-4)
    kwargs = dict(span_ft=19.5, service_plf=506.826, self_plf=221.875, width_in=12.0,
                  depth_in=17.75, d_in=15.0625, tension_in2=0.93, compression_in2=0.93,
                  fc_psi=5000.0)
    defl = deflection_after_attachment(**kwargs)
    assert defl.cracked_inertia_in4 == pytest.approx(1065.8, abs=0.1)
    assert defl.effective_inertia_in4 == pytest.approx(2052.5, abs=0.1)
    assert defl.long_term_factor == pytest.approx(1.5908, abs=1e-4)
    assert defl.after_attachment_in == pytest.approx(0.4844, abs=1e-4)

    # ** α = 0 IS BIT-IDENTICAL TO THE SIMPLE SPAN, and this is an EXACT comparison. **
    # The hex float is the value the engine produced before `end_fixity` existed; the
    # `5 − 4α` shape factor is exactly 5.0 there, and §24.2.3.6's 0.70/0.30 average is NOT
    # taken at α = 0 (it is written for a member continuous at both ends). A credit that
    # restates the uncredited row is a credit nobody can check.
    assert defl.after_attachment_in == float.fromhex("0x1.effbefd575c56p-2")
    assert deflection_after_attachment(**kwargs, end_fixity=0.0).after_attachment_in == (
        defl.after_attachment_in)

    # §6f's claimed row, worked by hand: Ie,mid 3,463.1, Ie,end 5,592.4 (uncracked),
    # Ie,avg 4,101.9, Δ after attachment 0.18109".
    fixed = deflection_after_attachment(**kwargs, end_fixity=0.25)
    assert fixed.effective_inertia_end_in4 == pytest.approx(5592.4, abs=0.1)
    assert fixed.effective_inertia_in4 == pytest.approx(4101.9, abs=0.1)
    mid = (fixed.effective_inertia_in4 - 0.30 * fixed.effective_inertia_end_in4) / 0.70
    assert mid == pytest.approx(3463.1, abs=0.1)
    assert fixed.after_attachment_in == pytest.approx(0.18109, abs=1e-5)
    assert fixed.negative_moment_ftlb == pytest.approx(4015.0, abs=0.1)
    assert (fixed.limit_600_in, fixed.limit_480_in) == (pytest.approx(0.390),
                                                        pytest.approx(0.4875))
    # 0.514 elastic, and the α where the beam would read uncracked at service — the claim
    # sits below it, so no part of the credit rests on staying uncracked.
    elastic = deflection_after_attachment(**kwargs, end_fixity=0.514)
    assert elastic.after_attachment_in == pytest.approx(0.0927, abs=1e-4)
    assert elastic.effective_inertia_in4 == pytest.approx(5592.4, abs=0.1)


def test_the_count_accessor_leaves_the_spacing_accessor_refusing_counts(catlin_plan) -> None:
    beam = catlin_plan.by_tag("W-SG-BRKBM")
    assert bar_for_roles(beam.reinforcement, ("bottom-y",)) is None
    assert bar_count_for_roles(beam.reinforcement, ("bottom-y",)) == (5, 3, 1)
    assert bar_count_for_roles(beam.reinforcement, ("horizontal",)) == (4, 1, 2)

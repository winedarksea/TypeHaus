"""``veneer_beam/W-SG-BRKBM`` against ``notes/sunken_garden_veneer_beam.md`` §6j.

Since 2026-10-10 the record reads the beam's real bearing (§6j): its pour sits on
FT-SG-W1/E1's toes, so it spans 11'-0" between the toe faces — design span 12.255', wythe
268.86 plf, wu 687.03 plf — and Tu falls below §22.7.4.1's threshold. The pure-arithmetic
test at the end still runs the old 19.5' inputs, which is a function check, not a house one.

Every number below was worked by hand in the note, at the model's own geometry, before this
file was re-based. Inputs are read off the resolved model where the test asserts on them, so
a geometry move fails here loudly rather than silently re-basing the oracle.
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
    """§6j: 12" of concrete (not the 14" assembly), 11'-0" clear between the toe faces with
    3'-6" of bearing on each, and the wythe at 268.86 plf. Two #5 bottom, two #4 top."""
    _, rec = record
    inputs = {q.name: q.value for q in rec.inputs}
    assert inputs["section_width"] == pytest.approx(12.0)
    assert inputs["section_depth"] == pytest.approx(17.75)
    assert inputs["clear_span"] == pytest.approx(11.0)
    assert inputs["bearing"] == pytest.approx(42.0)
    assert inputs["wythe_load"] == pytest.approx(268.86, abs=0.01)
    assert inputs["self_weight"] == pytest.approx(221.875)
    assert inputs["eccentricity"] == pytest.approx(4.1275, abs=1e-3)
    assert (inputs["bottom_bars"], inputs["top_bars"]) == (2.0, 2.0)
    assert inputs["end_fixity"] == 0.0
    assert rec.scope is Scope.SCREENING
    assert any(n.startswith("SPAN: 11.00' clear between FT-SG-W1 and FT-SG-E1") for n in rec.notes)


def test_strength_rows_reproduce_the_hand_pass(record) -> None:
    """§6j at U = 1.4D on L = min(11 + d, 11 + 3.5) = 12.255': Mu 12,898; Vu 4,210;
    As,req 0.2114 so §9.6.1.3's 4/3 is 0.2819 and waives §9.6.1.2's 0.639; φMn 41,007 on
    2 #5."""
    _, rec = record
    flex = _state(rec, "flexure")
    assert flex.demand == pytest.approx(12898, abs=1)
    assert flex.capacity == pytest.approx(41007, abs=1)
    minimum = _state(rec, "minimum flexural steel")
    assert minimum.demand == pytest.approx(0.2819, abs=1e-4)
    assert "§9.6.1.3" in minimum.citation and minimum.ok
    shear = _state(rec, "one-way shear")
    assert shear.demand == pytest.approx(4209.8, abs=1)
    assert shear.capacity == pytest.approx(19171, abs=1)


def test_torsion_is_below_the_threshold_and_its_detailing_is_not_owed(record) -> None:
    """§6j: Tu 1.4 × 268.86 × (4.1275/12) × 12.255/2 = 793.3 ft-lb against φT_th 842.5,
    d/c 0.942 — §22.7.4.1 lets it be neglected, so no hoop, side-bar or Al rows exist and
    Vu 4,210 is under §9.6.3.1's 9,586 Av,min trigger."""
    _, rec = record
    tors = _state(rec, "torsion below the §22.7.4.1 threshold")
    assert tors.demand == pytest.approx(793.3, abs=0.1)
    assert tors.capacity == pytest.approx(842.5, abs=0.1)
    assert tors.ratio == pytest.approx(0.942, abs=1e-3)
    trigger = _state(rec, "shear below the Av,min trigger")
    assert trigger.capacity == pytest.approx(9585.9, abs=0.5) and trigger.ok
    names = {s.name for s in rec.limit_states}
    for gone in ("closed hoop spacing", "torsion transverse steel, equilibrium (one leg)",
                 "longitudinal steel, flexure + torsion", "closed hoop hook angle"):
        assert gone not in names, gone
    assert rec.status is Status.OK and not rec.missing


def test_deflection_is_two_rows_and_tms_l_over_600_is_the_strict_one(record) -> None:
    """§6j: uncracked (Ma 9,213 < ⅔Mcr), Δ after attachment 0.02595" on 147.06" — ℓ/600
    0.106, ℓ/480 0.085, with no fixity claimed."""
    _, rec = record
    tms = _state(rec, "deflection after the wythe is attached, TMS")
    assert tms.demand == pytest.approx(0.02595, abs=1e-5)
    assert tms.capacity == pytest.approx(0.2451, abs=1e-4)
    assert tms.ratio == pytest.approx(0.106, abs=1e-3)
    assert "TMS 402-22 §13.1.2.3" in tms.citation
    aci = _state(rec, "deflection after the wythe is attached, ACI")
    assert aci.ratio == pytest.approx(0.085, abs=1e-3)
    assert not any("SERVICEABILITY ONLY" in note for note in rec.notes)
    assert not [s for s in rec.limit_states if "end moment into" in s.name]


def test_the_bottom_row_reaches_its_support_through_the_toe_dowels(record) -> None:
    """§6j: §9.7.3.8.1 — ⅓ of 2 #5 (0.207 in²) into the support, on 2 #5 dowels 12" into
    each toe; class B lap 27.58" in the 30" projection. The top row is hangers, ungraded."""
    _, rec = record
    for footing in ("FT-SG-W1", "FT-SG-E1"):
        into = _state(rec, f"positive steel into the support at {footing}")
        assert (into.demand, into.capacity) == (pytest.approx(0.2067, abs=1e-4),
                                                pytest.approx(0.62))
        ext = _state(rec, f"dowel extension into {footing}")
        assert (ext.demand, ext.capacity) == (6.0, pytest.approx(12.0))
        lap = _state(rec, f"dowel lap of bottom-y past the {footing} joint")
        assert (lap.demand, lap.capacity) == (pytest.approx(27.58, abs=0.01),
                                              pytest.approx(30.0))
    assert not [s for s in rec.limit_states if s.name.startswith("hooked development")]
    assert any("straight hangers" in n for n in rec.notes)


def test_without_the_toe_bearing_the_light_cage_would_not_do(record) -> None:
    """Take FT-SG-W1/E1 out of the model and the beam spans 17'-0" wall to wall again: Tu
    goes back above φT_th, the torsion rows return, and the #3 @ 12" cage fails §9.7.6.3.3.
    The bearing is what the light steel rests on, so it is checked, never assumed."""
    import dataclasses

    ctx, _ = record
    model = dataclasses.replace(ctx.model, solids=[
        s for s in ctx.model.solids if s.tag not in ("FT-SG-W1", "FT-SG-E1")])
    bare = EngineeringContext(plan=ctx.plan, model=model)
    beam, carried = veneer_beams(bare)[0]
    rec = _one(bare, beam, carried)
    assert {q.name: q.value for q in rec.inputs}["clear_span"] == pytest.approx(17.0)
    hoops = _state(rec, "closed hoop spacing")
    assert not hoops.ok
    assert rec.status is not Status.OK


def test_an_authored_fixity_still_buys_no_strength(record) -> None:
    """§6f's machinery survives the re-base: author an `end_restraint` and the joint rows
    appear, while every strength row is identical with and without it."""
    ctx, rec = record
    beam, carried = veneer_beams(ctx)[0]
    credited = _one(ctx, beam.model_copy(update={"end_restraint": EndRestraint(
        fixity=0.25, elastic_fixity=0.487, effective_width=inch(36.0), source="§6f")}),
        carried)
    assert [s for s in credited.limit_states if "end moment into" in s.name]
    for name in ("flexure, simple span", "minimum flexural steel", "one-way shear",
                 "torsion below the §22.7.4.1 threshold"):
        a, b = _state(rec, name), _state(credited, name)
        assert (a.demand, a.capacity) == (b.demand, b.capacity), name


def test_end_restraint_round_trips() -> None:
    restraint = EndRestraint(fixity=0.25, elastic_fixity=0.514,
                             effective_width=inch(36.0), source="§6f")
    again = EndRestraint.model_validate(restraint.model_dump())
    assert again == restraint
    assert EndRestraint(fixity=0.0).elastic_fixity is None


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
    assert bar_count_for_roles(beam.reinforcement, ("bottom-y",)) == (5, 2, 1)
    assert bar_count_for_roles(beam.reinforcement, ("horizontal",)) is None

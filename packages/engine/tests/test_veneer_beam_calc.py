"""``veneer_beam/W-SG-BRKBM`` against ``notes/sunken_garden_veneer_beam.md`` §6.

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
from typehaus.engineering.sunken_garden.veneer_beam import (
    deflection_after_attachment,
    torsion_design,
)
from typehaus.engineering.veneer_beam import (
    carried_wythes,
    enumerate_veneer_beams,
    hooked_anchorage,
)


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
    """§6a: 12" of concrete (not the 14" assembly), 19'-0" clear, 6" bearing, 284.95 plf."""
    _, rec = record
    inputs = {q.name: q.value for q in rec.inputs}
    assert inputs["section_width"] == pytest.approx(12.0)
    assert inputs["section_depth"] == pytest.approx(17.75)
    assert inputs["clear_span"] == pytest.approx(19.0)
    assert inputs["bearing"] == pytest.approx(6.0)
    assert inputs["wythe_load"] == pytest.approx(284.95, abs=0.01)
    assert inputs["self_weight"] == pytest.approx(221.875)
    assert inputs["eccentricity"] == pytest.approx(4.1275, abs=1e-3)
    assert rec.scope is Scope.SCREENING


def test_strength_rows_reproduce_the_hand_pass(record) -> None:
    """§6b and §6c at U = 1.4D."""
    _, rec = record
    flex = _state(rec, "flexure")
    assert flex.demand == pytest.approx(33726, abs=1)
    assert flex.capacity == pytest.approx(60747, abs=1)
    assert _state(rec, "minimum flexural steel").demand == pytest.approx(0.639, abs=1e-3)
    shear = _state(rec, "one-way shear")
    assert shear.demand == pytest.approx(6918, abs=1)
    assert shear.capacity == pytest.approx(19171, abs=1)
    tt = _state(rec, "torsion transverse")
    assert tt.demand == pytest.approx(0.002058, abs=2e-6)
    assert tt.capacity == pytest.approx(0.0220)
    limit = _state(rec, "torsion section limit")
    assert limit.demand == pytest.approx(54.03, abs=0.01)
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


def test_deflection_is_graded_at_l_over_480_not_240(record) -> None:
    """§6d: after-attachment 0.4844" against ℓ/480 = 0.4875"."""
    _, rec = record
    defl = _state(rec, "deflection")
    assert defl.demand == pytest.approx(0.4844, abs=1e-4)
    assert defl.capacity == pytest.approx(0.4875)
    assert defl.ratio == pytest.approx(0.994, abs=1e-3)
    assert any("ℓ/600" in note and "1.24" in note for note in rec.notes)


def test_end_restraint_is_incomplete_never_an_assumed_hook(record) -> None:
    """§6e: no hook is authored, so INCOMPLETE naming it; the bottom row meets the footing."""
    _, rec = record
    assert rec.status is Status.INCOMPLETE
    assert not any(s.name.startswith("hooked development") for s in rec.limit_states)
    assert sum("`BarSpec.hooks`" in m and "top-y" in m for m in rec.missing) == 2
    assert sum("bottom-y" in m and "FT-SG-" in m for m in rec.missing) == 2
    assert any("ℓdh 11.38\" against 9.00\" (d/c 1.26)" in note for note in rec.notes)


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
    note = next(n for n in rec.notes if n.startswith("MODEL GAP"))
    assert "4.00\" clear of W-SG-W1" in note and "0.00\" clear of W-SG-E1" in note


def test_pure_arithmetic_matches_the_note_without_the_model() -> None:
    tors = torsion_design(tu_ftlb=1337.854, vu_lb=6918.18, width_in=12.0, depth_in=17.75,
                          d_in=15.0625, cover_in=2.0, hoop_diameter_in=0.375,
                          hoop_leg_area_in2=0.11, hoop_spacing_in=5.0, fc_psi=5000.0)
    assert tors.ph_in == pytest.approx(42.0)
    assert tors.al_required_in2 == pytest.approx(1.0451, abs=1e-4)
    defl = deflection_after_attachment(
        span_ft=19.5, service_plf=506.826, self_plf=221.875, width_in=12.0, depth_in=17.75,
        d_in=15.0625, tension_in2=0.93, compression_in2=0.93, fc_psi=5000.0)
    assert defl.cracked_inertia_in4 == pytest.approx(1065.8, abs=0.1)
    assert defl.effective_inertia_in4 == pytest.approx(2052.5, abs=0.1)
    assert defl.long_term_factor == pytest.approx(1.5908, abs=1e-4)


def test_the_count_accessor_leaves_the_spacing_accessor_refusing_counts(catlin_plan) -> None:
    beam = catlin_plan.by_tag("W-SG-BRKBM")
    assert bar_for_roles(beam.reinforcement, ("bottom-y",)) is None
    assert bar_count_for_roles(beam.reinforcement, ("bottom-y",)) == (5, 3, 1)
    assert bar_count_for_roles(beam.reinforcement, ("horizontal",)) == (4, 1, 2)

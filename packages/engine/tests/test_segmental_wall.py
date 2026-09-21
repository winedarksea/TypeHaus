"""``tiered_retaining`` — the SRW apron's own gravity free body.

Oracle: ``houses/catlin/notes/raised_garden_srw.md``, hand-worked separately. §3–§8 are
reproduced here against ``engineering/segmental_wall.analyse``; the catlin tests read the
section off the resolved model and check the record lands where the note says.
"""

from __future__ import annotations

import math

import pytest

from typehaus import FoundationWall, PublishedSpan, SegmentalWallSpec, ft, inch
from typehaus.engineering import DEFERRALS, EngineeringContext, EngineeringResults, Status
from typehaus.engineering.item import Scope
from typehaus.engineering.retaining_wall import enumerate_walls
from typehaus.engineering.segmental_wall import (
    KIND,
    Section,
    _one,
    analyse,
    lower_tiers,
    published_refusal,
    segmental_walls,
)
from typehaus.engineering.srw_gravity import coulomb_ka, phi_from_efp

_APRON = ("W-RG-BLOCK", "W-RG-WEST", "W-RG-EAST", "W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY")
#: The note's §1 section: AB Classic, 3'-4" retained over one 8" course, 0.97' deep, 130 pcf,
#: 6° setback.
_NOTE = Section(retained_ft=10.0 / 3.0, embedment_ft=8.0 / 12.0, unit_depth_ft=0.97,
                unit_weight_pcf=130.0, batter_deg=6.0, course_ft=8.0 / 12.0)


# --- the note, §1-§8 ----------------------------------------------------------------------

@pytest.mark.parametrize(("soil_pcf", "phi"), [(110.0, 27.818), (130.0, 31.966)])
def test_phi_is_read_back_off_the_efp(soil_pcf, phi) -> None:
    assert phi_from_efp(40.0, soil_pcf) == pytest.approx(phi, abs=1e-3)


def test_the_coulomb_form_reproduces_abs_printed_sample() -> None:
    """AB Commercial Installation Manual p.11: φ 30°, δ 0.66φ, 12° setback, K_a 0.2197."""
    assert coulomb_ka(30.0, 0.66 * 30.0, 12.0) == pytest.approx(0.2197, abs=3e-4)


# §3's table: soil pcf -> (K_a, P_h, P_v, M_r, FS sliding, FS overturning, x̄, q, shear).
_SECTION_3 = {
    110.0: (0.28285, 242.97, 54.07, 410.68, 1.213, 1.268, 0.1553, 2397.0, 168.7),
    130.0: (0.23499, 235.72, 64.53, 422.30, 1.506, 1.344, 0.1898, 1998.0, 163.7),
}


@pytest.mark.parametrize("soil_pcf", sorted(_SECTION_3))
def test_the_free_body_reproduces_section_3(soil_pcf) -> None:
    ka, p_h, p_v, m_r, sliding, overturning, x, q, shear = _SECTION_3[soil_pcf]
    phi = phi_from_efp(40.0, soil_pcf)
    body = analyse(_NOTE, soil_pcf, phi, math.tan(math.radians(phi)))
    assert body.weight_plf == pytest.approx(504.40, abs=0.01)
    assert body.ka == pytest.approx(ka, abs=5e-5)
    assert body.thrust_h_plf == pytest.approx(p_h, abs=0.02)
    assert body.thrust_v_plf == pytest.approx(p_v, abs=0.02)
    assert body.resisting_moment == pytest.approx(m_r, abs=0.05)
    assert body.fs_sliding == pytest.approx(sliding, abs=0.001)
    assert body.fs_overturning == pytest.approx(overturning, abs=0.001)
    assert body.resultant_ft == pytest.approx(x, abs=1e-3)
    assert body.bearing_psf == pytest.approx(q, abs=1.0)
    assert body.course_shear_plf == pytest.approx(shear, abs=0.1)


def test_the_ibc_fallback_of_section_3() -> None:
    phi = phi_from_efp(40.0, 110.0)
    assert analyse(_NOTE, 110.0, phi, 0.25).fs_sliding == pytest.approx(0.575, abs=0.001)


@pytest.mark.parametrize(("soil_pcf", "sliding", "overturning"), [
    (110.0, 1.30, 1.71), (130.0, 1.65, 1.85)])
def test_ab_stone_of_section_8(soil_pcf, sliding, overturning) -> None:
    stone = Section(10 / 3, 8 / 12, 0.97, 130.0, batter_deg=12.0, course_ft=8 / 12)
    phi = phi_from_efp(40.0, soil_pcf)
    body = analyse(stone, soil_pcf, phi, math.tan(math.radians(phi)))
    assert body.fs_sliding == pytest.approx(sliding, abs=0.005)
    assert body.fs_overturning == pytest.approx(overturning, abs=0.005)


@pytest.mark.parametrize(("height", "sliding"), [(3.0, 1.578), (3.2, 1.487)])
def test_the_lowered_terrace_of_section_8(height, sliding) -> None:
    phi = phi_from_efp(40.0, 110.0)
    body = analyse(Section(height, 0.0, 0.97, 130.0, batter_deg=6.0), 110.0, phi,
                   math.tan(math.radians(phi)))
    assert body.fs_sliding == pytest.approx(sliding, abs=0.001)


# --- catlin ---------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    return EngineeringContext(plan=catlin_plan, model=catlin_model_ro, soil_class="GM")


@pytest.fixture(scope="module")
def records(ctx):
    results = EngineeringResults(ctx)
    return {tag: results[f"{KIND}/{tag}"] for tag in _APRON}


def test_the_kind_is_computed_not_deferred(ctx) -> None:
    assert KIND not in DEFERRALS
    assert [w.tag for w in segmental_walls(ctx)] == sorted(_APRON)
    # Disjoint from the cantilever suite: _retaining_walls is not widened to the apron.
    assert not set(_APRON) & set(enumerate_walls(ctx))


def test_every_leg_is_over_at_the_notes_numbers(records) -> None:
    """§3 at the loose end: overturning fails at BOTH ends, so the verdict is OVER."""
    for tag, record in records.items():
        assert record.status is Status.OVER, tag
        assert record.scope is Scope.SCREENING
        states = {s.name: s for s in record.limit_states}
        assert states["sliding"].capacity == pytest.approx(1.213, abs=0.001), tag
        assert states["overturning"].capacity == pytest.approx(1.268, abs=0.001), tag
        assert states["bearing"].demand == pytest.approx(2397.0, abs=1.0), tag
        assert states["course interface shear"].capacity == pytest.approx(3.82, abs=0.01)
        assert record.governing.name == "sliding"
        assert record.governing.ratio == pytest.approx(1.237, abs=0.001)
        inputs = {q.name: q.value for q in record.inputs}
        # Retained height is the authored fill, never drop_ft.
        assert inputs["retained_height"] == pytest.approx(10 / 3, abs=1e-3)
        assert inputs["course_height"] == pytest.approx(8 / 12, abs=1e-6)
        assert inputs["pad_friction_angle"] == pytest.approx(36.0)
        # The dense end fails overturning too (1.344) — named in the note, not a straddle.
        assert "overturning 1.34" in " ".join(record.notes)


def test_embedment_reads_the_nearest_station(records) -> None:
    ratios = {tag: next(s.ratio for s in r.limit_states if s.name == "base-course embedment")
              for tag, r in records.items()}
    assert ratios["W-RG-BLOCK"] == pytest.approx(0.75, abs=1e-3)
    assert ratios["W-RG-WEST"] == pytest.approx(0.75, abs=1e-3)
    assert ratios["W-RG-EAST"] == pytest.approx(0.75, abs=1e-3)
    assert ratios["W-RG-WEST-BALCONY"] == pytest.approx(0.50, abs=1e-3)
    assert ratios["W-RG-EAST-BALCONY"] == pytest.approx(6 / 11, abs=1e-3)
    for tag in ("W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY"):
        assert any(n.startswith("MISMATCH") for n in records[tag].notes), tag


@pytest.mark.parametrize(("tag", "lower"), [
    ("W-RG-BLOCK", "W-SG-S"), ("W-RG-WEST", "W-SG-W2"), ("W-RG-EAST", "W-SG-E2")])
def test_the_tier_row_prints_the_violation(records, tag, lower) -> None:
    row = next(s for s in records[tag].limit_states if s.name.startswith("tier"))
    assert row.name == f"tier independence vs {lower}"
    assert row.demand == pytest.approx(18.24, abs=0.01)
    assert row.capacity == pytest.approx(2.974, abs=0.005)
    assert row.ratio == pytest.approx(6.13, abs=0.01)
    assert row.is_detailing


def test_the_returns_have_no_parallel_tier(records) -> None:
    for tag in ("W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY"):
        assert not [s for s in records[tag].limit_states if s.name.startswith("tier")]


def test_the_ab_classic_is_authored_on_every_leg(records) -> None:
    notes = " ".join(records["W-RG-BLOCK"].notes)
    assert "Unit weight from the product data" in notes
    assert "NOT GRADED: global stability" in notes
    assert records["W-RG-BLOCK"].missing == ()


def test_a_passing_wall_on_a_fallback_is_incomplete_then_ok(ctx, monkeypatch) -> None:
    """A PASS resting on an ungraded interface or a fallback unit weight is not OK."""
    import typehaus.engineering.segmental_wall as module

    monkeypatch.setattr(module, "lower_tiers", lambda _ctx, _wall: [])  # no court beside it
    wall = ctx.plan.by_tag("W-RG-BLOCK")
    low = wall.model_copy(update={"unbalanced_fill": inch(2),
                                  "srw": SegmentalWallSpec(source="test", unit_depth=ft(3))})
    record = _one(ctx, low)
    assert record.status is Status.INCOMPLETE
    assert any("interface shear" in m for m in record.missing)
    full = low.model_copy(update={"srw": SegmentalWallSpec(
        source="test", unit_depth=ft(3), unit_weight_pcf=125.0,
        interface_shear_lb_per_ft=1000.0)})
    assert _one(ctx, full).status is Status.OK


def test_a_verdict_inside_the_soil_band_is_incomplete(ctx, monkeypatch) -> None:
    """§8's 3.4' free body: sliding 1.41 at 110 pcf, 1.74 at 130 — the soil decides it."""
    import typehaus.engineering.segmental_wall as module

    monkeypatch.setattr(module, "lower_tiers", lambda _ctx, _wall: [])
    wall = ctx.plan.by_tag("W-RG-BLOCK")
    record = _one(ctx, wall.model_copy(update={"unbalanced_fill": ft(3.4 - 8 / 12)}))
    assert record.status is Status.INCOMPLETE
    assert any("measured soil friction angle" in m for m in record.missing)


# --- the published row is refused in code ----------------------------------------------------

def _row(span_ft: float) -> PublishedSpan:
    return PublishedSpan(source="maker chart", table="gravity, level backfill",
                         member="12in unit", span=ft(span_ft), condition="drained")


def test_the_published_row_is_refused_until_every_guard_is_answered(ctx) -> None:
    wall = ctx.plan.by_tag("W-RG-BLOCK")
    tiers = lower_tiers(ctx, wall)

    def refusal(spec, assembly=wall.assembly, near=tiers):
        return published_refusal(
            ctx, wall.model_copy(update={"srw": spec, "assembly": assembly}), near)

    assert refusal(SegmentalWallSpec(source="s")) is None  # no row, nothing to refuse
    assert "DRAINAGE" in refusal(SegmentalWallSpec(source="s", published=_row(5)))
    drained = "SUNKEN_GARDEN_WALL_DRAINED"
    assert "batter" in refusal(SegmentalWallSpec(source="s", published=_row(5)), drained)
    battered = SegmentalWallSpec(source="s", batter_deg=9.5, published=_row(5))
    assert "cap" in refusal(battered, drained)
    capped = battered.model_copy(update={"cap": "cap unit"})
    assert "inside 2H" in refusal(capped, drained)
    assert "publishes 3.00'" in refusal(
        capped.model_copy(update={"published": _row(3)}), drained, [])
    assert refusal(capped, drained, []) is None


def test_the_spec_round_trips() -> None:
    spec = SegmentalWallSpec(source="doc", batter_deg=9.5, unit_depth=inch(12),
                             unit_weight_pcf=120.0, interface_shear_lb_per_ft=900.0,
                             cap="cap", published=_row(3))
    wall = FoundationWall(uid="X", tag="W-X", start_node="a", end_node="b",
                          assembly="A", srw=spec)
    assert FoundationWall.model_validate_json(wall.model_dump_json()) == wall
    assert FoundationWall.model_validate(wall.model_dump()) == wall

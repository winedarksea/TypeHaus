"""``tiered_retaining`` — the SRW apron's own gravity free body.

Oracle: ``houses/catlin/notes/raised_garden_srw.md``, hand-worked separately. §3–§8 are
reproduced here against ``engineering/segmental_wall.analyse``; the catlin tests read the
section off the resolved model and check the record lands where the note says.
"""

from __future__ import annotations

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

_APRON = ("W-RG-BLOCK", "W-RG-WEST", "W-RG-EAST", "W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY")
#: The note's §1 section: 3'-4" retained, 8" embedded, 12" unit, 2200 kg/m3.
_NOTE = Section(retained_ft=10.0 / 3.0, embedment_ft=8.0 / 12.0, unit_depth_ft=1.0,
                unit_weight_pcf=137.34)


# --- the note, §3-§8 ----------------------------------------------------------------------

def test_the_free_body_reproduces_section_3() -> None:
    body = analyse(_NOTE, 45.0, 0.25)
    assert body.thrust_plf == pytest.approx(360.0, abs=0.05)
    assert body.overturning_moment == pytest.approx(480.0, abs=0.1)
    assert body.weight_plf == pytest.approx(549.37, abs=0.05)
    assert body.resisting_moment == pytest.approx(274.68, abs=0.05)
    assert body.fs_sliding == pytest.approx(0.381, abs=0.001)
    assert body.fs_overturning == pytest.approx(0.572, abs=0.001)
    assert body.resultant_ft == pytest.approx(-0.374, abs=0.001)
    assert body.eccentricity_ft == pytest.approx(0.874, abs=0.001)
    assert body.bearing_psf is None  # the resultant is off the base


def test_course_shear_demand_is_section_5() -> None:
    assert analyse(_NOTE, 45.0, 0.25).course_shear_plf == pytest.approx(275.6, abs=0.1)


@pytest.mark.parametrize(("section", "friction", "sliding", "overturning"), [
    (Section(10 / 3, 8 / 12, 1.0, 120.0), 0.25, 0.333, 0.500),
    (_NOTE, 0.35, 0.534, 0.572),
    (Section(10 / 3, 8 / 12, 1.0, 137.34, batter_deg=9.5), 0.25, 0.381, 0.955),
])
def test_the_sensitivities_of_section_7(section, friction, sliding, overturning) -> None:
    body = analyse(section, 45.0, friction)
    assert body.fs_sliding == pytest.approx(sliding, abs=0.001)
    assert body.fs_overturning == pytest.approx(overturning, abs=0.001)


@pytest.mark.parametrize(("depth", "friction"), [(3.93, 0.25), (2.81, 0.35)])
def test_the_deeper_unit_of_section_8_reaches_sliding_1_5(depth, friction) -> None:
    body = analyse(Section(10 / 3, 8 / 12, depth, 137.34), 45.0, friction)
    assert body.fs_sliding == pytest.approx(1.5, abs=0.005)
    assert body.bearing_psf is not None


@pytest.mark.parametrize(("height", "friction"), [(1.02, 0.25), (1.42, 0.35)])
def test_the_lowered_terrace_of_section_8_reaches_sliding_1_5(height, friction) -> None:
    body = analyse(Section(height, 0.0, 1.0, 137.34), 45.0, friction)
    assert body.fs_sliding == pytest.approx(1.5, abs=0.01)


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
    for tag, record in records.items():
        assert record.status is Status.OVER, tag
        assert record.scope is Scope.SCREENING
        states = {s.name: s for s in record.limit_states}
        assert states["sliding"].capacity == pytest.approx(0.381, abs=0.001), tag
        assert states["overturning"].capacity == pytest.approx(0.572, abs=0.001), tag
        off_base = states["bearing — resultant on the base"]
        assert off_base.ratio == pytest.approx(1.75, abs=0.01), tag
        assert record.governing.name == "sliding"
        # Retained height is the authored fill, never drop_ft.
        inputs = {q.name: q.value for q in record.inputs}
        assert inputs["retained_height"] == pytest.approx(10 / 3, abs=1e-3)


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


def test_open_inputs_are_named_on_an_over_record(records) -> None:
    notes = " ".join(records["W-RG-BLOCK"].notes)
    assert "interface shear" in notes and "unit weight" in notes
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

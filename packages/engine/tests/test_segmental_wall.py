"""The NCMA/AB gravity free body's arithmetic, and the apron's section reading.

``tiered_retaining`` is retired (2026-11-23): every leg is read off AB Table 1.3
(``test_srw_chart.py``). What stays pinned here is ``srw_gravity``'s hand-oracled free body
(``houses/catlin/notes/raised_garden_srw.md`` §2-§8: AB Stones 12°, §3c's superseded AB
Classic 6°) and the reading ``tier_surcharge`` and the chart share.
"""

from __future__ import annotations

import math

import pytest

from typehaus import (
    FoundationWall,
    PublishedSpan,
    SegmentalWallSpec,
    SrwChartSection,
    SrwDrain,
    SrwDrainageZone,
    ft,
    inch,
)
from typehaus.engineering import EngineeringContext
from typehaus.engineering.retaining_wall import enumerate_walls
from typehaus.engineering.segmental_wall import (
    Section,
    Tier,
    analyse,
    lower_tiers,
    published_refusal,
    segmental_walls,
)
from typehaus.engineering.srw_gravity import (
    DrainageZone,
    coulomb_ka,
    phi_from_efp,
    trial_wedge,
)

_ALL = ("W-RG-BLOCK", "W-RG-WEST", "W-RG-EAST", "W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY")
#: The note's §1 section: AB Stones, 3'-4" retained over one 8" course, 0.97' deep, 130 pcf,
#: 12° setback. ``_CLASSIC`` is §3c's superseded 6° unit, otherwise identical.
_STONE = Section(retained_ft=10.0 / 3.0, embedment_ft=8.0 / 12.0, unit_depth_ft=0.97,
                 unit_weight_pcf=130.0, batter_deg=12.0, course_ft=8.0 / 12.0)
_CLASSIC = Section(retained_ft=10.0 / 3.0, embedment_ft=8.0 / 12.0, unit_depth_ft=0.97,
                   unit_weight_pcf=130.0, batter_deg=6.0, course_ft=8.0 / 12.0)
_SECTIONS = {"stone": _STONE, "classic": _CLASSIC}


# --- the note, §1-§8 ----------------------------------------------------------------------

@pytest.mark.parametrize(("soil_pcf", "phi"), [(110.0, 27.818), (130.0, 31.966)])
def test_phi_is_read_back_off_the_efp(soil_pcf, phi) -> None:
    assert phi_from_efp(40.0, soil_pcf) == pytest.approx(phi, abs=1e-3)


def test_the_coulomb_form_reproduces_abs_printed_sample() -> None:
    """AB Commercial Installation Manual p.11: φ 30°, δ 0.66φ, 12° setback, K_a 0.2197."""
    assert coulomb_ka(30.0, 0.66 * 30.0, 12.0) == pytest.approx(0.2197, abs=3e-4)


# Native at the face: (unit, pcf) -> (K_a, P_h, P_v, M_r, FS sliding, FS OT, x̄, q, shear).
_SECTION_3 = {
    ("stone", 110.0): (0.24564, 214.76, 24.64, 489.95, 1.300, 1.711, 0.3849, 883.0, 149.14),
    ("stone", 130.0): (0.19839, 203.61, 33.38, 500.90, 1.648, 1.845, 0.4266, 755.0, 141.39),
    # §3c, superseded
    ("classic", 110.0): (0.28285, 242.97, 54.07, 410.68, 1.213, 1.268, 0.1553, 2397.0, 168.7),
    ("classic", 130.0): (0.23499, 235.72, 64.53, 422.30, 1.506, 1.344, 0.1898, 1998.0, 163.7),
}


@pytest.mark.parametrize(("unit", "soil_pcf"), sorted(_SECTION_3))
def test_the_free_body_reproduces_section_3(unit, soil_pcf) -> None:
    ka, p_h, p_v, m_r, sliding, overturning, x, q, shear = _SECTION_3[(unit, soil_pcf)]
    phi = phi_from_efp(40.0, soil_pcf)
    body = analyse(_SECTIONS[unit], soil_pcf, phi, math.tan(math.radians(phi)))
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


@pytest.mark.parametrize(("batter", "soil_pcf", "plane", "exit_ft"), [
    (12.0, 110.0, 50.083, 3.347), (12.0, 130.0, 52.523, 3.067),
    (6.0, 110.0, 52.431, 3.077), (6.0, 130.0, 54.885, 2.813)])
def test_the_trial_wedge_is_coulomb_on_one_material(batter, soil_pcf, plane, exit_ft) -> None:
    """§2b: with no zone the wedge search returns §3's closed form."""
    phi = phi_from_efp(40.0, soil_pcf)
    wedge = trial_wedge(4.0, soil_pcf, phi, batter)
    closed = 0.5 * soil_pcf * coulomb_ka(phi, 2 / 3 * phi, batter) * 16.0
    assert wedge.thrust_plf == pytest.approx(closed, abs=0.01)
    assert wedge.plane_deg == pytest.approx(plane, abs=0.002)
    assert wedge.reach_ft == pytest.approx(exit_ft, abs=0.001)


# With 12" of rock: (unit, pcf) -> (ρ, share, φ_eq, P_a, sliding, OT, x̄, q, shear, exit).
_SECTION_3B = {
    ("stone", 110.0): (49.706, 0.3935, 31.212, 181.27, 1.538, 2.020, 0.4663, 604.0, 120.52,
                       3.392),
    ("stone", 130.0): (52.384, 0.4480, 33.821, 187.18, 1.806, 2.018, 0.4689, 606.0, 125.73,
                       3.082),
    # §3c, superseded
    ("classic", 110.0): (52.135, 0.3718, 31.031, 215.45, 1.383, 1.436, 0.2217, 1657.0,
                         141.73, 3.110),
    ("classic", 130.0): (54.793, 0.4163, 33.692, 225.99, 1.615, 1.435, 0.2239, 1680.0,
                         148.97, 2.822),
}
_ROCK = DrainageZone(width_ft=1.0, phi_deg=36.0)


@pytest.mark.parametrize(("unit", "soil_pcf"), sorted(_SECTION_3B))
def test_the_wall_rock_reproduces_section_3b(unit, soil_pcf) -> None:
    plane, share, phi_eq, p_a, sliding, overturning, x, q, shear, exit_ft = (
        _SECTION_3B[(unit, soil_pcf)])
    phi = phi_from_efp(40.0, soil_pcf)
    body = analyse(_SECTIONS[unit], soil_pcf, phi, math.tan(math.radians(phi)), _ROCK)
    assert body.wedge.plane_deg == pytest.approx(plane, abs=0.002)
    assert body.wedge.zone_share == pytest.approx(share, abs=1e-4)
    assert body.wedge.phi_equiv_deg == pytest.approx(phi_eq, abs=1e-3)
    assert body.thrust_plf == pytest.approx(p_a, abs=0.01)
    assert body.fs_sliding == pytest.approx(sliding, abs=0.001)
    assert body.fs_overturning == pytest.approx(overturning, abs=0.001)
    assert body.resultant_ft == pytest.approx(x, abs=1e-3)
    assert body.bearing_psf == pytest.approx(q, abs=1.0)
    assert body.course_shear_plf == pytest.approx(shear, abs=0.02)
    assert body.wedge.reach_ft == pytest.approx(exit_ft, abs=0.001)


@pytest.mark.parametrize(("unit", "zone", "soil_pcf", "sliding", "overturning"), [
    ("stone", DrainageZone(1.0, 34.0), 110.0, 1.470, 1.931),   # §3b: fails sliding
    ("stone", DrainageZone(1.0, 34.0), 130.0, 1.723, 1.927),
    ("classic", DrainageZone(1.0, 34.0), 110.0, 1.335, 1.389),
    ("classic", DrainageZone(1.0, 34.0), 130.0, 1.558, 1.387),
    ("classic", DrainageZone(2.0, 36.0), 110.0, 1.594, 1.645),
    ("classic", DrainageZone(2.0, 36.0), 130.0, 1.737, 1.536)])
def test_the_sensitivities_of_sections_3b_and_3c(unit, zone, soil_pcf, sliding,
                                                 overturning) -> None:
    phi = phi_from_efp(40.0, soil_pcf)
    body = analyse(_SECTIONS[unit], soil_pcf, phi, math.tan(math.radians(phi)), zone)
    assert body.fs_sliding == pytest.approx(sliding, abs=0.001)
    assert body.fs_overturning == pytest.approx(overturning, abs=0.001)


@pytest.mark.parametrize(("batter", "soil_pcf", "zone", "restricted"), [
    (12.0, 110.0, _ROCK, 177.39), (12.0, 130.0, _ROCK, 186.85),
    (6.0, 110.0, None, 248.69), (6.0, 110.0, _ROCK, 215.05)])
def test_the_confined_strip_takes_off_almost_nothing(batter, soil_pcf, zone,
                                                     restricted) -> None:
    """§6b: the steepest plane that exits inside the 2.974' strip."""
    phi = phi_from_efp(40.0, soil_pcf)
    steep = math.degrees(math.atan(4.0 / 2.974))
    wedge = trial_wedge(4.0, soil_pcf, phi, batter, zone, min_plane_deg=steep)
    assert wedge.thrust_plf == pytest.approx(restricted, abs=0.02)


def test_the_ibc_fallback_of_section_3c() -> None:
    phi = phi_from_efp(40.0, 110.0)
    assert analyse(_CLASSIC, 110.0, phi, 0.25).fs_sliding == pytest.approx(0.575, abs=0.001)


@pytest.mark.parametrize(("height", "sliding"), [(3.0, 1.578), (3.2, 1.487)])
def test_the_lowered_terrace_of_section_3c(height, sliding) -> None:
    phi = phi_from_efp(40.0, 110.0)
    body = analyse(Section(height, 0.0, 0.97, 130.0, batter_deg=6.0), 110.0, phi,
                   math.tan(math.radians(phi)))
    assert body.fs_sliding == pytest.approx(sliding, abs=0.001)


# --- catlin ---------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    return EngineeringContext(plan=catlin_plan, model=catlin_model_ro, soil_class="GM")


@pytest.mark.parametrize(("tag", "lower"), [
    ("W-RG-BLOCK", "W-SG-S"), ("W-RG-WEST", "W-SG-W2"), ("W-RG-EAST", "W-SG-E2")])
def test_the_perimeter_legs_stand_back_to_back(ctx, tag, lower) -> None:
    """§1/§6: each leg faces the yard and its court wall faces the court, so the 2H terrace
    row is not tripped (the chart sheet's tier line is `answered`)."""
    tier = next(t for t in lower_tiers(ctx, ctx.plan.by_tag(tag)) if t.tag == lower)
    assert tier.parallel and tier.back_to_back is True
    assert tier.clear_ft == pytest.approx(2.974, abs=0.005)
    assert "corroborated by grade station" in tier.facing_basis


def test_every_apron_leg_is_a_segmental_wall_and_none_is_a_register_item(ctx) -> None:
    from typehaus.engineering.registry import registered_kinds

    assert [w.tag for w in segmental_walls(ctx)] == sorted(_ALL)
    assert not set(_ALL) & set(enumerate_walls(ctx))     # the cantilever suite is not widened
    assert "tiered_retaining" not in registered_kinds()


def test_the_returns_have_no_parallel_tier(ctx) -> None:
    for tag in ("W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY"):
        assert not [t for t in lower_tiers(ctx, ctx.plan.by_tag(tag)) if t.parallel]


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
    rock = SrwDrainageZone(width=inch(12), friction_angle_deg=36.0, source="s")
    assert "batter" in refusal(SegmentalWallSpec(source="s", published=_row(5),
                                                 drainage_zone=rock))
    drained = "SUNKEN_GARDEN_WALL_DRAINED"
    assert "batter" in refusal(SegmentalWallSpec(source="s", published=_row(5)), drained)
    battered = SegmentalWallSpec(source="s", batter_deg=9.5, published=_row(5))
    assert "cap" in refusal(battered, drained)
    capped = battered.model_copy(update={"cap": "cap unit"})
    # F9: a back-to-back wall (BLOCK's court wall) is not this rule's tier; a same-facing one is.
    assert refusal(capped, drained) is None
    same = Tier("W-SG-S", 9.12, 2.97, True, False, "t")
    assert "faces the same way" in refusal(capped, drained, [same])
    assert "facing is not established" in refusal(
        capped, drained, [Tier("W-SG-S", 9.12, 2.97, True, None, "t")])
    assert refusal(capped, drained, [Tier("X", 9.12, 2.97, False, None, "")]) is None
    assert "publishes 3.00'" in refusal(
        capped.model_copy(update={"published": _row(3)}), drained, [])
    assert refusal(capped, drained, []) is None


def test_the_spec_round_trips() -> None:
    spec = SegmentalWallSpec(source="doc", batter_deg=9.5, unit_depth=inch(12),
                             unit_weight_pcf=120.0, interface_shear_lb_per_ft=900.0,
                             cap="cap", published=_row(3),
                             chart=SrwChartSection(
                                 batter_deg=12.0, soil_phi_deg=27.0, cap_height=inch(4),
                                 min_buried=inch(6), min_wall_rock=inch(12),
                                 founding_compaction_pct=95.0, lift=inch(8),
                                 drain=SrwDrain(pipe="p", outlet_ref="FB-X")),
                             drainage_zone=SrwDrainageZone(width=inch(12),
                                                           friction_angle_deg=36.0, source="s"))
    wall = FoundationWall(uid="X", tag="W-X", start_node="a", end_node="b",
                          assembly="A", srw=spec)
    assert FoundationWall.model_validate_json(wall.model_dump_json()) == wall
    assert FoundationWall.model_validate(wall.model_dump()) == wall

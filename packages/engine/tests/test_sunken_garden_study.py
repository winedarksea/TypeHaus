"""Independent benchmarks and integration checks for the revised courtyard study."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from typehaus.analytical.sunken_garden_coupled import analyse_coupled
from typehaus.diff.compare import variant_plan
from typehaus.diff.variants import find_variant, load_variants
from typehaus.engineering.sunken_garden.comparison import COURTYARD_LAYOUTS, sizing_study
from typehaus.engineering.sunken_garden.inputs import (
    BasedValue,
    PlantingProfile,
    default_design_input,
)
from typehaus.engineering.sunken_garden.loads import (
    finite_strip_lateral_pressure_psf,
    integrate_pressure,
)
from typehaus.engineering.sunken_garden.veneer_beam import check_veneer_beam
from typehaus.source.loader import load_plan
from typehaus.source.parameter_overrides import activated, parameter


def _items(plan):
    return [item for storey in plan.elements.values() for item in storey]


def test_fhwa_finite_strip_benchmark() -> None:
    # Independently evaluated from 2q/pi[beta-sin(beta)cos(2alpha)] with q=300 psf,
    # z=2 ft, adjacent 3 ft strip: beta=atan(1.5), alpha=pi/2-beta/2.
    pressure = finite_strip_lateral_pressure_psf(
        surcharge_psf=300.0, depth_ft=2.0, near_edge_ft=0.0, width_ft=3.0)
    assert pressure == pytest.approx(275.847, rel=1e-5)
    setback = finite_strip_lateral_pressure_psf(
        surcharge_psf=300.0, depth_ft=2.0, near_edge_ft=3.0, width_ft=3.0)
    assert setback == pytest.approx(19.999, rel=2e-3)
    assert setback < pressure


def test_partial_height_soil_is_less_than_frozen_full_height_comparison() -> None:
    design = default_design_input()
    layout = PlantingProfile("yard-grade", 0.0, 0.0, 0.0)
    partial = integrate_pressure(design, layout)
    historical = integrate_pressure(design, layout, full_height_comparison=True)
    assert partial.thrust_plf == pytest.approx(750.0, rel=2e-3)
    assert partial.moment_at_footing_top_ftlb_per_ft == pytest.approx(1250.0, rel=2e-3)
    assert historical.thrust_plf > partial.thrust_plf * 3.0


def test_blocked_drain_adds_the_independent_five_foot_water_triangle() -> None:
    design = default_design_input()
    layout = PlantingProfile("yard-grade", 0.0, 0.0, 0.0)
    dry = integrate_pressure(design, layout)
    wet = integrate_pressure(design, layout, wet=True)
    assert wet.thrust_plf - dry.thrust_plf == pytest.approx(62.4 * 5.0 ** 2 / 2.0, rel=2e-3)


def test_corrected_veneer_beam_uses_strength_load_and_aci_minimum() -> None:
    result = check_veneer_beam()
    assert result.effective_span_ft == pytest.approx(19.5)
    assert result.factored_load_plf == pytest.approx(636.0)
    assert result.factored_moment_ftlb == pytest.approx(30229.875)
    assert result.minimum_steel_in2 == pytest.approx(0.63905, rel=1e-4)
    assert result.provided_steel_in2 == pytest.approx(0.93)
    assert result.flexure_ratio < 1.0
    assert result.shear_ratio < 1.0


def test_catlin_variants_are_isolated_and_keep_wall_identity() -> None:
    house = Path("houses/catlin")
    variants = load_variants(house)
    against = variant_plan(find_variant(variants, "against-wall-24-brick").selection(house))
    reference = variant_plan(find_variant(variants, "reference").selection(house))
    against_items = _items(against)
    reference_items = _items(reference)
    assert any(item.tag == "RL-SG-COURT" for item in against_items)
    assert not any(item.tag == "RL-SG-COURT" for item in reference_items)
    against_wall = next(item for item in against_items if item.tag == "W-SG-W2")
    reference_wall = next(item for item in reference_items if item.tag == "W-SG-W2")
    assert against_wall.uid == reference_wall.uid
    assert any(item.tag == "SP-SG-ARCH-OVERFLOW" for item in reference_items)
    assert any(item.tag == "PR-SG-ARCH-OVERFLOW" for item in reference_items)


def test_parameter_context_restores_and_unknown_house_parameter_fails() -> None:
    assert parameter("example", 12.0) == 12.0
    with activated({"example": 10.0}) as consumed:
        assert parameter("example", 12.0) == 10.0
        assert consumed == {"example"}
    assert parameter("example", 12.0) == 12.0
    loaded = load_plan(Path("houses/starter"), parameter_overrides={"typo.parameter": 1})
    assert loaded.plan is None
    assert any(item.check_id == "loader.unknown_parameter_override"
               for item in loaded.findings)


def test_setback_variant_builds_separate_closed_planter_and_fiber_screen() -> None:
    house = Path("houses/catlin")
    variant = find_variant(load_variants(house), "setback-36-fiber-cement")
    items = _items(variant_plan(variant.selection(house)))
    assert len([item for item in items if item.tag.startswith("W-RGV-")]) == 8
    walkout = next(item for item in items if item.tag == "W-B-BRICK")
    assert walkout.assembly == "BASEMENT_FIBER_CEMENT_SCREEN"


def _solvable_design():
    design = default_design_input()
    return replace(
        design,
        soil=replace(
            design.soil,
            vertical_support_pci=BasedValue(150.0, "benchmark"),
            horizontal_support_pci=BasedValue(25.0, "benchmark"),
        ),
        connections=replace(
            design.connections,
            balcony_reactions_lb=BasedValue((5000.0,) * 4, "benchmark"),
        ),
    )


def test_coupled_model_refuses_missing_site_and_column_inputs() -> None:
    result = analyse_coupled(default_design_input(), COURTYARD_LAYOUTS[0])
    assert not result.successful
    assert "soil-support modulus" in result.unresolved[0]


def test_coupled_plate_model_equilibrates_and_converges() -> None:
    design = _solvable_design()
    coarse = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=4.0)
    fine = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=2.0)
    assert coarse.successful, coarse.unresolved
    assert fine.successful, fine.unresolved
    assert fine.equilibrium_error is not None and fine.equilibrium_error < 0.01
    assert coarse.maximum_translation_in == pytest.approx(fine.maximum_translation_in, rel=0.15)
    assert fine.model is not None
    assert {plate.tag for plate in fine.model.plates} >= {
        "W-SG-W1", "W-SG-W2", "W-SG-E1", "W-SG-E2", "W-SG-S",
        "FT-SG-W1/W2", "FT-SG-E1/E2", "FT-SG-S",
    }


def test_removed_tie_and_unequal_loading_are_real_model_changes() -> None:
    design = _solvable_design()
    symmetric = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=4.0)
    unequal = analyse_coupled(
        design, COURTYARD_LAYOUTS[0], mesh_ft=4.0,
        west_multiplier=1.0, east_multiplier=0.25, include_veneer_tie=False,
    )
    assert symmetric.successful and unequal.successful
    assert unequal.model is not None
    assert "W-SG-BRKBM" not in {member.id for member in unequal.model.members}
    assert unequal.maximum_translation_in != pytest.approx(symmetric.maximum_translation_in)


def test_sizing_sweep_is_bounded_and_never_claims_development() -> None:
    candidates = sizing_study(COURTYARD_LAYOUTS[0])
    assert {item.stem_in for item in candidates} == {10.0, 12.0}
    assert min(item.footing_width_ft for item in candidates) == 4.0
    assert max(item.footing_width_ft for item in candidates) == 7.0
    assert all(item.toe_ft >= 1.0 and item.heel_ft >= 1.0 for item in candidates)
    assert not any(item.development_resolved for item in candidates)

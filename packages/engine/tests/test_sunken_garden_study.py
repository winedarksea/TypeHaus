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
    """Hand pass at the model's OWN ordinary retained height, 5.786458 ft.

    ** THE OLD EXPECTATIONS (750 plf / 1250 ft-lb) WERE THE 5.0 ft LITERAL. ** They were
    arithmetically right and described a wall the house does not build; see
    ``inputs.CATLIN_ORDINARY_RETAINED_HEIGHT_FT``. Re-derived independently at H = 5.786458:

    * thrust  = efp H^2 / 2 = 60 x 5.786458^2 / 2 = **1,004.49 plf**
    * moment  = efp H^3 / 6 = 60 x 5.786458^3 / 6 = **1,937.44 ft-lb/ft**

    Both terms scale as a power of the height, which is why nine inches moved the thrust by
    a third: the literal was not a rounding, it was a different wall.
    """
    design = default_design_input()
    layout = PlantingProfile("yard-grade", 0.0, 0.0, 0.0)
    height = design.soil.ordinary_retained_height_ft.value
    assert height == pytest.approx(5.786458333, abs=1e-6)
    partial = integrate_pressure(design, layout)
    historical = integrate_pressure(design, layout, full_height_comparison=True)
    assert partial.thrust_plf == pytest.approx(60.0 * height ** 2 / 2.0, rel=2e-3)
    assert partial.thrust_plf == pytest.approx(1004.49, rel=2e-3)
    assert partial.moment_at_footing_top_ftlb_per_ft == pytest.approx(
        60.0 * height ** 3 / 6.0, rel=2e-3)
    assert partial.moment_at_footing_top_ftlb_per_ft == pytest.approx(1937.44, rel=2e-3)
    assert historical.thrust_plf > partial.thrust_plf * 2.0


def test_blocked_drain_adds_the_independent_five_foot_water_triangle() -> None:
    design = default_design_input()
    layout = PlantingProfile("yard-grade", 0.0, 0.0, 0.0)
    dry = integrate_pressure(design, layout)
    wet = integrate_pressure(design, layout, wet=True)
    assert wet.thrust_plf - dry.thrust_plf == pytest.approx(62.4 * 5.0 ** 2 / 2.0, rel=2e-3)


def test_corrected_veneer_beam_uses_strength_load_and_aci_minimum() -> None:
    """Hand pass at **U = 1.4D**, ACI 318-19 Eq. (5.3.1a). Oracle: note §3.

    ** THE LOAD FACTOR WAS 1.2 UNTIL 2026-09-14 (636 plf, Mu 30,230 ft-lb). ** The member
    carries a brick wythe and its own concrete and nothing else, so (5.3.1b) ``1.2D + 1.6L``
    reduces to 1.2D, which is not a combination ACI publishes; (5.3.1a) governs a dead-only
    member. Re-derived independently:

    * w  = 308 + 222                                  = 530 plf service
    * wu = 1.4 x 530                                  = **742 plf**
    * L  = min(19.0 + d/12, 19.0 + 0.5)               = **19.5 ft** (centre-to-centre)
    * Mu = 742 x 19.5^2 / 8                           = **35,268 ft-lb**
    * Vu = 742 x 19.5 / 2                             = **7,234 lb**
    """
    result = check_veneer_beam()
    assert result.effective_span_ft == pytest.approx(19.5)
    assert result.service_load_plf == pytest.approx(530.0)
    assert result.factored_load_plf == pytest.approx(742.0)
    assert result.factored_moment_ftlb == pytest.approx(35268.1875)
    assert result.factored_shear_lb == pytest.approx(7234.5)
    assert result.provided_steel_in2 == pytest.approx(0.93)
    assert result.flexure_ratio < 1.0
    assert result.shear_ratio < 1.0


def test_two_number_fives_do_not_clear_aci_minimum_steel_at_the_real_mix() -> None:
    """**R6.** The note selected 2 #5 on a minimum computed at f'c 4,000. The mix is 5,000.

    ACI 318-19 §9.6.1.2 takes the **greater** of the two expressions, at d = 15.0625":

    * 3 sqrt(5000) x 12 x 15.0625 / 60000 = **0.639 in^2**   <- governs
    * 200 x 12 x 15.0625 / 60000          = **0.603 in^2**

    2 #5 is 0.620 in^2 and falls about 3% short. §9.6.1.3's exception — steel one third over
    the demand — does not rescue it either: 4/3 x 0.578 = 0.771 in^2, larger still. Three #5
    is the study section and clears both.
    """
    result = check_veneer_beam()
    assert result.effective_depth_in == pytest.approx(15.0625)
    assert result.minimum_steel_in2 == pytest.approx(0.63905, rel=1e-4)
    assert result.minimum_steel_in2 > 2 * 0.31
    assert result.required_steel_in2 * 4.0 / 3.0 > 2 * 0.31
    assert result.provided_steel_in2 > result.minimum_steel_in2


def test_the_beams_torsion_is_computed_and_is_above_the_threshold() -> None:
    """**The note asserted this away; the arithmetic does not agree, in a useful direction.**

    Note §4 said "compatibility torsion may be neglected below the cracking threshold" and
    compared against a T_cr it put at "on the order of 9 ft-k" at f'c 4,000. Two provisions
    were being conflated. At the real 5,000 psi mix, Acp = 12 x 17.75 = 213 in^2,
    pcp = 59.5 in, Acp^2/pcp = 762.5 in^3:

    * threshold  phi x 0.25 sqrt(f'c) Acp^2/pcp = 0.75 x 0.25 x 70.71 x 762.5 / 12
                                                = **842 ft-lb**  (§22.7.4.1)
    * cracking   phi x 4.00 sqrt(f'c) Acp^2/pcp = **13,479 ft-lb**  (§22.7.5.1)
    * demand     1.4 x 106.26 x 19.5 / 2        = **1,450 ft-lb**

    So the twist **does** redistribute — it is 9% of cracking, and §22.7.3.2 applies — and it
    is also **1.7x the threshold**, which means §9.6.4's minimum torsional reinforcement is
    owed whatever the compatibility argument concludes. Closed hoops with 135-degree hooks
    and longitudinal steel, not the open #3 stirrups the note specified.
    """
    result = check_veneer_beam()
    assert result.torsion_ftlb_per_ft == pytest.approx(106.26, rel=1e-4)
    assert result.factored_torsion_ftlb == pytest.approx(1450.45, rel=1e-4)
    assert result.phi_threshold_torsion_ftlb == pytest.approx(842.46, rel=1e-4)
    assert result.phi_cracking_torsion_ftlb == pytest.approx(13479.3, rel=1e-4)
    assert result.torsion_redistributes
    assert not result.torsion_may_be_neglected
    assert any("§9.6.4" in item for item in result.unresolved), result.unresolved


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
    """Convergence asserted where it exists, and the coarse mesh labelled for what it is.

    ** THIS USED TO COMPARE 4 ft AGAINST 2 ft AT rel=0.15, AND IT PASSED BY LUCK. ** The
    load was a triangle whose apex sat at the old 5.0 ft literal; at the model's own 5.7865
    the same two meshes are 22% apart and the assertion failed — not because anything
    regressed, but because a 3-by-5 element wall was never converged and the old load shape
    happened to hide it. (Band-averaging the plate pressure, added in the same pass, moved
    it by a fifth of a percent: the discretisation is the shell, not the load lumping.)

    Measured sweep, max translation in inches:
    4.0 -> 0.009627, 3.0 -> 0.008739, 2.0 -> 0.007898, 1.5 -> 0.007622, 1.0 -> 0.007806.

    ** RE-MEASURED 2026-09-22 AT THE 17'-0" COURT ** (the literal basis now matches it):
    4.0 -> 0.009503, 3.0 -> 0.008675, 2.0 -> 0.008067, 1.5 -> 0.007576, 1.0 -> 0.007307,
    0.75 -> 0.007655. **2 ft is no longer within 5% of 1 ft** (10.4%); 1.5 ft is (3.7%), and
    below that the sweep scatters about ±5% rather than settling. So the claims asserted now
    are: 1.5 ft is converged to the 1 ft mesh, 2 ft (the default) runs high by about a
    tenth, and 4 ft is a screening mesh that runs higher still — bounded, but not a result to
    quote. Equilibrium holds to machine precision at every mesh, which is the separate and
    stronger statement.
    """
    design = _solvable_design()
    coarse = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=4.0)
    default = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=2.0)
    fine = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=1.5)
    finest = analyse_coupled(design, COURTYARD_LAYOUTS[0], mesh_ft=1.0)
    for result in (coarse, default, fine, finest):
        assert result.successful, result.unresolved
        assert result.equilibrium_error is not None and result.equilibrium_error < 0.01
    assert fine.maximum_translation_in == pytest.approx(
        finest.maximum_translation_in, rel=0.05)
    assert default.maximum_translation_in > fine.maximum_translation_in
    assert default.maximum_translation_in == pytest.approx(
        finest.maximum_translation_in, rel=0.12)
    assert coarse.maximum_translation_in > default.maximum_translation_in
    assert coarse.maximum_translation_in == pytest.approx(
        default.maximum_translation_in, rel=0.25)
    assert default.model is not None
    assert {plate.tag for plate in default.model.plates} >= {
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


def _catlin_context():
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = load_plan(catlin)
    assert result.plan is not None, [f.message for f in result.findings]
    model, _ = resolve(result.plan)
    return EngineeringContext(plan=result.plan, model=model)


def test_the_study_reads_the_authored_court_and_not_a_literal() -> None:
    """**The lint that stops the two bodies of code drifting apart again.**

    Until 2026-09-14 the study package hard-coded its court and nothing compared that court
    with the one the house authors. It did not match: the ordinary retained height was 5.0 ft
    against the model's 5.7865, so every case in the report — including the terrace decision
    it exists to answer — ran on a wall nine inches short.

    Each expectation below is the authored model measured independently: the stem is
    ``W-SG-S``'s own top-to-bottom dimension, the footing is ``FT-SG-W2``'s (``FT-SG-S``
    adds 16" of toe), the clear width is the E/W wall axes 18 ft apart less one 12-inch
    stem (20 ft until the court narrowed to 17'-0" on 2026-09-22), and the ordinary height
    is the authored -3'-4" south yard above the -9'-1 7/16" footing top.
    """
    from typehaus.engineering.sunken_garden.model_inputs import design_input_from_model

    design, fell_back = design_input_from_model(_catlin_context())
    assert fell_back == (), fell_back
    geometry = design.geometry
    assert geometry.concrete_stem_height_ft == pytest.approx(9.119791666, abs=1e-6)
    assert geometry.stem_thickness_in == pytest.approx(12.0, abs=1e-6)
    assert geometry.footing_width_ft == pytest.approx(7.0, abs=1e-6)
    assert geometry.footing_depth_ft == pytest.approx(1.0, abs=1e-6)
    assert geometry.toe_ft == pytest.approx(3.0, abs=1e-6)
    assert geometry.heel_ft == pytest.approx(3.0, abs=1e-6)
    # FT-SG-S alone carries 16" more toe; the legs set the common section.
    assert geometry.end_toe_extension_ft == pytest.approx(16.0 / 12.0, abs=1e-6)
    assert geometry.clear_width_ft == pytest.approx(17.0, abs=1e-6)
    assert geometry.retained_side_length_ft == pytest.approx(16.0 + 4.0 / 12.0, abs=1e-6)
    height = design.soil.ordinary_retained_height_ft
    assert height.value == pytest.approx(5.786458333, abs=1e-6)
    assert height.measured is True
    # The two halves of the stem, and they have to add up: ordinary yard plus the 40-inch
    # terrace IS the full wall. 5.7865 + 3.3333 = 9.1198 exactly.
    assert height.value + 40.0 / 12.0 == pytest.approx(
        geometry.concrete_stem_height_ft, abs=1e-6)


def test_the_literal_basis_agrees_with_the_model_it_stands_in_for() -> None:
    """``default_design_input()`` is the no-plan fallback; a fallback that lies is worse.

    It is allowed to exist — the load benchmarks above and the report's standalone path both
    need a design input with no house in hand — but it is not allowed to describe a
    different building. This is the assertion that was missing when it did.
    """
    from typehaus.engineering.sunken_garden.model_inputs import design_input_from_model

    literal = default_design_input()
    derived, _ = design_input_from_model(_catlin_context())
    for field in ("clear_width_ft", "retained_side_length_ft", "footing_depth_ft",
                  "stem_thickness_in", "footing_width_ft", "toe_ft",
                  "end_toe_extension_ft"):
        assert getattr(literal.geometry, field) == pytest.approx(
            getattr(derived.geometry, field), abs=1e-3), field
    assert literal.geometry.concrete_stem_height_ft == pytest.approx(
        derived.geometry.concrete_stem_height_ft, abs=1e-3)
    assert literal.soil.ordinary_retained_height_ft.value == pytest.approx(
        derived.soil.ordinary_retained_height_ft.value, abs=1e-6)


def test_no_stability_case_is_a_silent_duplicate_of_another() -> None:
    """**R3.** ``one-side-only`` and ``staged-backfill`` were byte-identical to
    ``symmetric-service`` and ``max(...)`` could print any of the three as governing.

    They are gone — they are system cases, not per-foot ones — and this is the rule that
    keeps a new inert case from taking their place: every case in the sweep must differ from
    every other in the numbers a reader would act on.
    """
    from typehaus.engineering.sunken_garden.comparison import _cases

    design = default_design_input()
    cases = _cases(design, COURTYARD_LAYOUTS[0])
    assert len(cases) >= 3
    assert len({case.case for case in cases}) == len(cases)
    fingerprints = {
        case.case: (round(case.pressure.thrust_plf, 6),
                    round(case.pressure.moment_at_footing_top_ftlb_per_ft, 6),
                    round(case.vertical_weight_plf, 6))
        for case in cases
    }
    assert len(set(fingerprints.values())) == len(cases), fingerprints

"""The fifth build stage: walls as shells on springs, and the refusal when it cannot.

``analytical/shells.py`` is the producer the ``Plate``/``SupportSpring``/``PlatePressure``
machinery never had on the project build path. Two things have to be true of it and each is
worth a test of its own: on catlin it must **refuse**, because no subgrade modulus is
authored and a presumptive bearing pressure is not a stiffness; and given a modulus it must
really mesh, or the refusal is only hiding an empty stage.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from typehaus.analytical import Plate, PlatePressure, SupportSpring  # re-export contract
from typehaus.analytical.build import build_analytical_model
from typehaus.analytical.graph import LoadCaseKind
from typehaus.analytical.shells import PSF_TO_PA, SHELL_KINDS, derive_shells
from typehaus.analytical.scope import build_scope
from typehaus.cli.engineering_load import load_engineering

HOUSE = Path(__file__).resolve().parents[3] / "houses" / "catlin"

#: The moduli a real geotechnical report would carry. Nothing in the engine may default
#: these; the test authors them so the producer is exercised, and says so.
TEST_VERTICAL_PCI = 150.0
TEST_HORIZONTAL_PCI = 75.0
TEST_BASIS = "a test's own number, standing in for a geotechnical report"


@pytest.fixture(scope="module")
def load():
    return load_engineering(HOUSE)


def _with_subgrade(ctx):
    """``ctx`` with the two moduli authored — preferences are frozen, so replace them."""
    structural = dataclasses.replace(
        ctx.preferences.structural,
        soil_vertical_subgrade_pci=TEST_VERTICAL_PCI,
        soil_horizontal_subgrade_pci=TEST_HORIZONTAL_PCI,
        soil_subgrade_basis=TEST_BASIS)
    preferences = dataclasses.replace(ctx.preferences, structural=structural)
    return dataclasses.replace(ctx, preferences=preferences)


def test_catlin_refuses_to_mesh_a_wall_it_has_no_stiffness_for(load):
    model = build_analytical_model(load.ctx)
    assert model.plates == ()
    assert model.support_springs == ()
    assert model.plate_pressures == ()
    refusals = [gap for gap in model.gaps if "subgrade" in gap]
    assert len(refusals) == 1, model.gaps
    # The refusal has to NAME what it wants and which items it cost, or it is a shrug.
    assert "soil_vertical_subgrade_pci" in refusals[0]
    assert "soil_horizontal_subgrade_pci" in refusals[0]
    assert "retaining_wall/W-SG-E2" in refusals[0]


def test_a_presumptive_bearing_pressure_is_not_offered_as_a_stiffness(load):
    """Every wall record publishes ``allowable_bearing``; none of it may reach a spring."""
    shells = derive_shells(load.ctx, build_scope(load.ctx))
    assert shells.springs == []
    assert "not a stiffness" in shells.gaps[0]


def test_given_a_modulus_the_walls_really_mesh(load):
    ctx = _with_subgrade(load.ctx)
    model = build_analytical_model(ctx)
    assert not [gap for gap in model.gaps if "subgrade" in gap]
    assert model.plates, "the stage produced nothing with a stiffness in hand"
    assert all(isinstance(plate, Plate) for plate in model.plates)
    assert all(isinstance(spring, SupportSpring) for spring in model.support_springs)
    assert all(isinstance(p, PlatePressure) for p in model.plate_pressures)
    # Every plate carries exactly one earth pressure, and nothing else does.
    assert len(model.plate_pressures) == len(model.plates)
    assert {p.case for p in model.plate_pressures} == {LoadCaseKind.EARTH}
    assert {p.plate for p in model.plate_pressures} == {p.id for p in model.plates}
    # Both spring directions at every base node, and no spring anywhere else.
    base = {spring.node for spring in model.support_springs}
    assert {spring.dof for spring in model.support_springs} == {"DZ", "DX"}
    assert len(model.support_springs) == 2 * len(base)
    assert all(spring.stiffness_n_m > 0.0 for spring in model.support_springs)
    assert all(TEST_BASIS in spring.basis for spring in model.support_springs)


def test_the_meshed_walls_are_the_ones_that_stop_being_gaps(load):
    ctx = _with_subgrade(load.ctx)
    scope = build_scope(ctx)
    walls = {item for item in scope.item_ids if ctx.engineering[item].kind in SHELL_KINDS}
    assert walls, "catlin has retaining walls or this test has stopped asking anything"
    meshed = derive_shells(ctx, scope).tags_by_item
    assert set(meshed) == walls
    model = build_analytical_model(ctx)
    for item in walls:
        assert not [gap for gap in model.gaps if gap.startswith(f"{item}:")]


def test_the_earth_pressure_is_the_bands_average_and_zero_above_the_soil(load):
    """A plate gets its band's MEAN of the triangular profile, not a midpoint sample."""
    ctx = _with_subgrade(load.ctx)
    scope = build_scope(ctx)
    shells = derive_shells(ctx, scope)
    record = ctx.engineering["retaining_wall/W-SG-E2"]
    inputs = {q.name: q.value for q in record.inputs}
    by_plate = {p.plate: p for p in shells.pressures}
    wall_plates = [p for p in shells.plates if p.tag == "W-SG-E2"]
    pressures = [by_plate[p.id].pressure_pa / PSF_TO_PA for p in wall_plates]
    # The deepest band cannot exceed the profile's own value at the base of the wall.
    assert max(pressures) <= inputs["active_efp"] * inputs["retained_height"] + 1e-6
    # And nothing is negative: above the retained soil the profile is zero, never suction.
    assert min(pressures) >= 0.0


# --------------------------------------------------------------- typed load combinations
def test_the_one_combination_catlin_declares_survives_into_the_export(load):
    """It did not, and nothing said so.

    ``girt_screw``'s ``"ASCE 7-16 §2.4.1(7) 0.6W"`` was read back out of its own prose, and
    the clause number in front of the factors made it unparseable — so the only combination
    in the house was dropped in silence and the export carried unit cases alone.
    """
    model = build_analytical_model(load.ctx)
    named = {combination.name: combination for combination in model.combinations}
    wind = named.get("ASCE 7-16 §2.4.1(7) 0.6W")
    assert wind is not None, sorted(named)
    assert wind.factors == {LoadCaseKind.WIND: 0.6}
    assert wind.source.startswith("girt_screw/")


def test_the_moment_columns_export_the_combination_that_actually_governed(load):
    """`deck_post` runs a five-combination §2.3.1 envelope; the winner reaches the graph."""
    model = build_analytical_model(load.ctx)
    envelope = [c for c in model.combinations if c.name.startswith("ASCE 7-16 §2.3.1")]
    assert envelope, [c.name for c in model.combinations]
    for combination in envelope:
        assert combination.factors, combination.name
        assert LoadCaseKind.DEAD in combination.factors
        assert combination.source.startswith("deck_post/")
        # The label and the factors are two statements of one thing and must agree.
        for letter, kind in (("W", LoadCaseKind.WIND), ("S", LoadCaseKind.SNOW)):
            head = combination.name.split("§2.3.1 ")[1]
            assert (letter in head) == (kind in combination.factors), combination.name


def test_an_item_that_names_no_combination_is_a_declared_gap_not_a_silence(load):
    model = build_analytical_model(load.ctx)
    lines = [gap for gap in model.gaps if "name no load combination" in gap]
    assert len(lines) == 1, model.gaps
    assert "forms no ASD or LRFD envelope" in lines[0]

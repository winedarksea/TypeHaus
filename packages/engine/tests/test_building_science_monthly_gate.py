"""Monthly (ISO 13788-style) condensation gate, soil-coupled ΔT, and block-load scoping.

Stream building-science: the monthly worst-month reduction is the pass/fail *gate* while
the 99%-design-hour walk stays a cold-snap *screen*; below-grade components see the soil
temperature, not the design air; unconditioned storeys carry no block-load UA; and the two
starter library walls, re-authored with a real vented cavity, earn a real permeance verdict.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.checks.building_science.condensation import (
    CHECK_ID,
    SCREEN_CHECK_ID,
    condensation_risk,
)
from typehaus.checks.building_science.glaser import (
    analyze_assembly,
    analyze_assembly_monthly,
    analyze_layers_monthly,
    glaser_layers,
)
from typehaus.checks.code.mn_residential.profile import get_profile
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.energy import estimate_block_load
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Building,
    CavityFill,
    Layer,
    LayerFunction,
    Library,
    Material,
    MonthlyNormal,
    Node,
    Occupancy,
    PlanModel,
    Project,
    Room,
    Site,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

# The MSP 1991-2020 shape, spelled inline so the worst-month pick is hand-checkable.
_NORMALS = (
    MonthlyNormal(temp_f=16.2, rh=73.7), MonthlyNormal(temp_f=20.6, rh=70.2),
    MonthlyNormal(temp_f=33.3, rh=64.5), MonthlyNormal(temp_f=47.1, rh=55.6),
    MonthlyNormal(temp_f=59.5, rh=57.2), MonthlyNormal(temp_f=69.7, rh=62.4),
    MonthlyNormal(temp_f=74.3, rh=64.4), MonthlyNormal(temp_f=71.8, rh=67.5),
    MonthlyNormal(temp_f=63.5, rh=67.0), MonthlyNormal(temp_f=49.5, rh=65.1),
    MonthlyNormal(temp_f=34.8, rh=69.4), MonthlyNormal(temp_f=22.0, rh=75.0),
)

_GYPSUM = Material(tag="gwb", name="Gypsum board", r_per_inch=0.9, perm_rating=18.8)
_STUD = Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9)
_WOOL = Material(tag="wool", name="Mineral wool", r_per_inch=4.2, perm_rating=116.0)
_PLYWOOD = Material(tag="ply", name="Structural plywood", r_per_inch=1.25, perm_rating=0.30)
_EPS = Material(tag="eps", name="EPS rigid insulation", r_per_inch=4.0, perm_rating=3.9)
_LIBRARY = Library(materials=(_GYPSUM, _STUD, _WOOL, _PLYWOOD, _EPS))


def _framed_wall(tag: str, *outboard: Layer) -> Assembly:
    return Assembly(tag=tag, layers=(
        Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, cavity=CavityFill(material_ref="wool")),
        Layer(name="sheathing", material_ref="ply", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        *outboard,
    ))


def test_monthly_gate_worst_month_is_a_winter_month() -> None:
    """An uninsulated-outboard wall condenses against the January mean but not the July
    one, so the reducer must land on a winter month and report the crossing."""
    risky = _framed_wall("NO-CI")
    assessment = analyze_assembly_monthly(
        risky, _LIBRARY, monthly_normals=_NORMALS, preferences=Preferences())
    assert assessment is not None
    assert assessment.analysis.known, assessment.analysis.unknown_materials
    assert assessment.analysis.has_risk
    assert assessment.month in ("December", "January", "February")
    # The July walk on its own is safe — the gate found the *worst* month, not any month.
    july_only = analyze_layers_monthly(
        "NO-CI", list(risky.layers), _LIBRARY,
        monthly_normals=tuple(_NORMALS[6:7] * 12), interior_setpoint_f=70.0,
        interior_relative_humidity=0.35)
    assert not july_only.analysis.has_risk


def test_monthly_gate_reports_margin_when_every_month_is_safe() -> None:
    safe = _framed_wall("CI", Layer(name="ci", material_ref="eps", thickness=inch(5.0),
                                    function=LayerFunction.INSULATION))
    assessment = analyze_assembly_monthly(
        safe, _LIBRARY, monthly_normals=_NORMALS,
        preferences=Preferences(monthly_interior_relative_humidity=0.20))
    assert assessment is not None
    assert not assessment.analysis.has_risk
    # December (22.0 F but 75% exterior RH) edges out colder-but-drier January: the
    # reducer ranks by how close a plane runs to saturation, not by temperature alone.
    assert assessment.month in ("December", "January")
    assert assessment.analysis.tightest_plane.margin_pa > 0


def test_monthly_gate_needs_twelve_months() -> None:
    partial = analyze_layers_monthly(
        "X", [], _LIBRARY, monthly_normals=_NORMALS[:3], interior_setpoint_f=70.0,
        interior_relative_humidity=0.35)
    assert partial is None


def _plan(*, monthly_normals=(), soil_temp_f=None, second_storey_conditioned=None):
    """One conditioned storey of clad 2x6 walls; optionally a second storey of the same
    walls whose single room is (un)conditioned."""
    assembly = _framed_wall(
        "EXT",
        Layer(name="siding", material_ref="ply", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    )
    library = Library(materials=(_GYPSUM, _STUD, _WOOL, _PLYWOOD, _EPS),
                      assemblies=(assembly,))
    project = Project(name="BS", project_uuid="00000000-0000-4000-8000-0000000000b5",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90),
                                monthly_normals=monthly_normals, soil_temp_f=soil_temp_f),
                      building=Building(name="BS"))
    storeys = [Storey(uid="ST000000b1", tag="s1", elevation=ft(0),
                      default_ceiling_height=ft(9))]
    plan = PlanModel(project=project, library=library, storeys=tuple(storeys))

    def _shell(storey_tag: str, index: int, origin_ft: float, room: Room) -> tuple:
        nodes = tuple(
            Node(uid=f"N{index}{i:08d}", tag=f"N-{storey_tag}-{i}", position=position)
            for i, position in enumerate((
                pt(ft(origin_ft), ft(0)), pt(ft(origin_ft + 20), ft(0)),
                pt(ft(origin_ft + 20), ft(14)), pt(ft(origin_ft), ft(14)),
            ), 1))
        walls = tuple(
            Wall(uid=f"W{index}{i:08d}", tag=f"W-{storey_tag}-{i}",
                 start_node=f"N-{storey_tag}-{start}", end_node=f"N-{storey_tag}-{end}",
                 assembly="EXT", top=ft(9))
            for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
        return (*nodes, *walls, room)

    plan = plan.with_elements("s1", _shell("s1", 1, 0.0, Room(
        uid="RM000000b1", tag="RM-1", seed=pt(ft(10), ft(7)), occupancy=Occupancy.LIVING)))
    if second_storey_conditioned is not None:
        storey2 = Storey(uid="ST000000b2", tag="s2", elevation=ft(0),
                         default_ceiling_height=ft(9))
        plan = PlanModel(project=project, library=library,
                         storeys=(*plan.storeys, storey2),
                         elements=plan.elements)
        plan = plan.with_elements("s2", _shell("s2", 2, 40.0, Room(
            uid="RM000000b2", tag="RM-2", seed=pt(ft(50), ft(7)),
            occupancy=Occupancy.GARAGE, conditioned=second_storey_conditioned)))
    return plan


def _context(plan) -> CheckContext:
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return CheckContext(plan=plan, model=model, preferences=Preferences(),
                        profile=get_profile("mn-2024"), resolve_findings=list(findings))


def test_check_emits_the_gate_and_the_screen_per_assembly() -> None:
    findings = condensation_risk(_context(_plan(monthly_normals=_NORMALS)))
    gate = [f for f in findings if f.check_id == CHECK_ID]
    screen = [f for f in findings if f.check_id == SCREEN_CHECK_ID]
    assert len(gate) == 1 and len(screen) == 1
    assert gate[0].message.startswith("monthly gate (ISO 13788-style)")
    assert gate[0].result in (Result.PASS, Result.FAIL)
    assert screen[0].message.startswith("cold-snap screen")


def test_gate_is_unknown_without_monthly_normals_but_screen_still_runs() -> None:
    findings = condensation_risk(_context(_plan()))
    gate = [f for f in findings if f.check_id == CHECK_ID]
    screen = [f for f in findings if f.check_id == SCREEN_CHECK_ID]
    assert len(gate) == 1 and gate[0].result is Result.UNKNOWN
    assert "Site.monthly_normals" in gate[0].message
    assert len(screen) == 1 and screen[0].result in (Result.PASS, Result.FAIL)


def test_below_grade_components_use_the_soil_delta() -> None:
    plan = _plan(soil_temp_f=47.0)
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    # Recast one resolved wall as a foundation wall: the block load must put the soil ΔT
    # (70-47 = 23 F), not the 85 F design-air ΔT, across it.
    model.walls = [dataclasses.replace(w, is_foundation=(w.tag == "W-s1-1"))
                   for w in model.walls]
    report = estimate_block_load(model, Preferences())
    foundation = next(c for c in report.components if c.kind == "foundation_walls")
    walls = next(c for c in report.components if c.kind == "walls")
    assert foundation.heating_delta_f == pytest.approx(23.0)
    assert walls.heating_delta_f == pytest.approx(85.0)
    assert report.heating_load_btu_per_hour == pytest.approx(sum(
        c.ua_btu_per_hour_f * c.heating_delta_f for c in report.components))
    assert not any("soil_temp_f" in item for item in report.unknown_inputs)


def test_missing_soil_temp_is_a_named_unknown_not_a_silent_air_delta() -> None:
    model, _ = resolve(_plan())
    model.walls = [dataclasses.replace(w, is_foundation=(w.tag == "W-s1-1"))
                   for w in model.walls]
    report = estimate_block_load(model, Preferences())
    foundation = next(c for c in report.components if c.kind == "foundation_walls")
    assert foundation.heating_delta_f == pytest.approx(85.0)  # the stated fallback
    assert any("Site.soil_temp_f" in item for item in report.unknown_inputs)


def test_unconditioned_storey_is_excluded_from_the_block_load() -> None:
    conditioned_model, _ = resolve(_plan(second_storey_conditioned=True))
    unconditioned_model, _ = resolve(_plan(second_storey_conditioned=False))
    with_garage = estimate_block_load(conditioned_model, Preferences())
    without_garage = estimate_block_load(unconditioned_model, Preferences())
    walls_with = next(c for c in with_garage.components if c.kind == "walls")
    walls_without = next(c for c in without_garage.components if c.kind == "walls")
    # Same geometry either way — only the conditioned flag changed, so the unconditioned
    # storey's identical shell (half the clad area) must vanish from the sum.
    assert walls_without.area_ft2 == pytest.approx(walls_with.area_ft2 / 2.0)
    assert without_garage.heating_load_btu_per_hour < with_garage.heating_load_btu_per_hour


def test_library_walls_earn_a_real_permeance_verdict() -> None:
    """The two starter library walls now author FURRING + CLADDING separately, so the
    Glaser walk truncates at the vented cavity and the unrated fiber-cement outside it no
    longer forces UNKNOWN. No permeance is invented: the fiber-cement material still
    carries no vapour rating."""
    from library import HOUSE_WALL_2X4_WITH_CI, HOUSE_WALL_2X6_WITH_ZIPR, STARTER_MATERIALS

    library = Library(materials=STARTER_MATERIALS,
                      assemblies=(HOUSE_WALL_2X4_WITH_CI, HOUSE_WALL_2X6_WITH_ZIPR))
    for assembly in (HOUSE_WALL_2X4_WITH_CI, HOUSE_WALL_2X6_WITH_ZIPR):
        kept = glaser_layers(list(assembly.default_lining) + list(assembly.layers))
        assert [layer.name for layer in kept][-1] != "cladding"
        assert all(layer.material_ref != "fiber-cement" for layer in kept)
        analysis = analyze_assembly(assembly, library, heating_design_temp_f=-15.0,
                                    preferences=Preferences())
        assert analysis.known, (assembly.tag, analysis.unknown_materials)
        assert analysis.tightest_plane is not None
        gate = analyze_assembly_monthly(assembly, library, monthly_normals=_NORMALS,
                                        preferences=Preferences())
        assert gate is not None and gate.analysis.known
    fiber_cement = next(m for m in STARTER_MATERIALS if m.tag == "fiber-cement")
    assert fiber_cement.perm_rating is None
    assert fiber_cement.vapor_permeance_perms is None

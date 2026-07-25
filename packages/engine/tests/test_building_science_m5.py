"""Focused M5 golden-style checks for the building-science consumers."""

from __future__ import annotations

from typehaus.analysis import assembly_r_value
from typehaus.checks.building_science.condensation import analyze_assembly, glaser_layers
from typehaus.checks.building_science.glaser import (
    EXTERIOR_SURFACE_R_US,
    INTERIOR_SURFACE_R_US,
)
from typehaus.checks.building_science.wwr import analyze_wwr
from typehaus.checks.registry import Preferences
from typehaus.energy import estimate_block_load
from typehaus.model import (
    Assembly,
    Building,
    CavityFill,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Occupancy,
    PlanModel,
    Project,
    Room,
    Site,
    Storey,
    Wall,
    Window,
    WindowType,
    centered,
    degF,
    ft,
    inch,
    pt,
    u_us,
)
from typehaus.resolve import resolve

# MN 99% heating design temperature, the boundary the M5 plan names for this walk.
_HEATING_DESIGN_F = -15.0

# Sourced properties, spelled here so the expected planes below are hand-checkable.
_GYPSUM = Material(tag="gwb", name="Gypsum board", r_per_inch=0.9, perm_rating=18.8)
_STUD = Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9)
_WOOL = Material(tag="wool", name="Mineral wool", r_per_inch=4.2, perm_rating=116.0)
_PLYWOOD = Material(tag="ply", name="Structural plywood", r_per_inch=1.25, perm_rating=0.30)
_EPS = Material(tag="eps", name="EPS rigid insulation", r_per_inch=4.0, perm_rating=3.9)
_STEEL = Material(tag="steel", name="Sheet steel", r_per_inch=0.0, vapor_permeance_perms=0.0)

_WALL_MATERIALS = (_GYPSUM, _STUD, _WOOL, _PLYWOOD, _EPS, _STEEL)


def _framed_wall_layers(*outboard: Layer) -> tuple[Layer, ...]:
    """Interior gypsum, an insulated 2x6 bay, plywood sheathing, then ``outboard``."""
    return (
        Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              cavity=CavityFill(material_ref="wool")),
        Layer(name="sheathing", material_ref="ply", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        *outboard,
    )


def test_glaser_reports_crossing_and_missing_perm() -> None:
    wool = Material(tag="wool", name="Mineral wool", r_per_inch=4.0, perm_rating=116.0)
    vapor_closed = Material(tag="barrier", name="Vapor closed membrane", r_per_inch=1.0,
                            perm_rating=0.1)
    assembly = Assembly(tag="RISK", layers=(
        Layer(name="cavity insulation", material_ref="wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
        Layer(name="exterior membrane", material_ref="barrier", thickness=inch(0.1),
              function=LayerFunction.MEMBRANE),
    ))
    library = Library(materials=(wool, vapor_closed))
    risk = analyze_assembly(assembly, library, heating_design_temp_f=_HEATING_DESIGN_F,
                            preferences=Preferences())
    assert risk.crossing_layer == "cavity insulation"
    assert risk.crossing_fraction is not None

    unknown_material = vapor_closed.model_copy(update={"perm_rating": None})
    unknown = analyze_assembly(assembly, Library(materials=(wool, unknown_material)),
                               heating_design_temp_f=_HEATING_DESIGN_F,
                               preferences=Preferences())
    assert unknown.unknown_materials == ("Vapor closed membrane",)


def test_uninsulated_framed_wall_condenses_behind_the_sheathing() -> None:
    """Known stack, known answer: with no exterior insulation the cold side of the
    vapour-open bay sits below the interior dew point, so the crossing is reported at the
    ``stud`` layer — i.e. on the back face of the sheathing, the classic plane."""
    assembly = Assembly(tag="NO-CI", layers=_framed_wall_layers())
    analysis = analyze_assembly(assembly, Library(materials=_WALL_MATERIALS),
                                heating_design_temp_f=_HEATING_DESIGN_F,
                                preferences=Preferences())
    assert analysis.known, analysis.unknown_materials
    assert analysis.crossing_layer == "stud"
    assert 0.0 <= analysis.crossing_fraction <= 1.0
    back_of_sheathing = analysis.points[2]
    assert back_of_sheathing.margin_pa < 0
    # Mineral wool is effectively vapour-open, so the bay carries essentially the full
    # interior vapour pressure out to the sheathing.
    assert back_of_sheathing.vapor_pressure_pa > 0.95 * analysis.points[0].vapor_pressure_pa


def test_exterior_insulation_and_drier_air_clear_the_dew_point() -> None:
    """The same stack with R-20 of exterior EPS and 20% interior RH has no crossing, and
    the reported margin is at the same plane the failing wall condensed on."""
    assembly = Assembly(tag="CI", layers=_framed_wall_layers(
        Layer(name="continuous insulation", material_ref="eps", thickness=inch(5.0),
              function=LayerFunction.INSULATION),
    ))
    analysis = analyze_assembly(
        assembly, Library(materials=_WALL_MATERIALS),
        heating_design_temp_f=_HEATING_DESIGN_F,
        preferences=Preferences(interior_relative_humidity=0.20),
    )
    assert analysis.known, analysis.unknown_materials
    assert analysis.crossing_layer is None
    assert analysis.tightest_plane_name == "stud"
    assert analysis.tightest_plane.margin_pa > 0
    assert analysis.tightest_plane.local_relative_humidity < 1.0


def test_missing_permeance_reports_unknown_naming_the_material() -> None:
    """One unsourced material anywhere in the stack must surface as UNKNOWN naming it,
    not as a profile computed from a substituted default (#32)."""
    unsourced = _PLYWOOD.model_copy(update={"perm_rating": None, "name": "Unrated panel"})
    assembly = Assembly(tag="GAP", layers=_framed_wall_layers())
    analysis = analyze_assembly(
        assembly, Library(materials=(_GYPSUM, _STUD, _WOOL, unsourced, _EPS)),
        heating_design_temp_f=_HEATING_DESIGN_F, preferences=Preferences(),
    )
    assert not analysis.known
    assert analysis.unknown_materials == ("Unrated panel",)
    assert analysis.points == ()
    assert analysis.tightest_plane is None


def test_missing_cavity_fill_permeance_names_the_fill_not_the_stud() -> None:
    """The bay is the path the walk uses, so an unsourced *fill* is the missing input."""
    unsourced_fill = _WOOL.model_copy(update={"perm_rating": None, "name": "Unrated batt"})
    assembly = Assembly(tag="GAP-FILL", layers=_framed_wall_layers())
    analysis = analyze_assembly(
        assembly, Library(materials=(_GYPSUM, _STUD, unsourced_fill, _PLYWOOD)),
        heating_design_temp_f=_HEATING_DESIGN_F, preferences=Preferences(),
    )
    assert analysis.unknown_materials == ("Unrated batt",)


def test_zero_permeance_layer_holds_the_whole_vapour_drop() -> None:
    """A sourced 0-perm sheet is a vapour barrier, not missing data: every plane inboard
    of it stays at interior vapour pressure and every plane outboard drops to exterior."""
    assembly = Assembly(tag="BARRIER", layers=_framed_wall_layers(
        Layer(name="steel skin", material_ref="steel", thickness=inch(0.024),
              function=LayerFunction.MEMBRANE),
        Layer(name="continuous insulation", material_ref="eps", thickness=inch(2.0),
              function=LayerFunction.INSULATION),
    ))
    analysis = analyze_assembly(assembly, Library(materials=_WALL_MATERIALS),
                                heating_design_temp_f=_HEATING_DESIGN_F,
                                preferences=Preferences())
    assert analysis.known, analysis.unknown_materials
    interior_pressure = analysis.points[0].vapor_pressure_pa
    inboard_of_barrier = analysis.points[1:4]  # gwb, stud, sheathing faces
    assert all(point.vapor_pressure_pa == interior_pressure for point in inboard_of_barrier)
    assert analysis.points[-1].vapor_pressure_pa < interior_pressure


def test_glaser_temperature_gradient_reuses_the_r_value_rollup() -> None:
    """The plan's point is that condensation is one more consumer of the R-value walk, so
    the total resistance implied by the profile must equal the rolled-up assembly R."""
    assembly = Assembly(tag="CI", layers=_framed_wall_layers(
        Layer(name="continuous insulation", material_ref="eps", thickness=inch(2.0),
              function=LayerFunction.INSULATION),
    ))
    library = Library(materials=_WALL_MATERIALS)
    analysis = analyze_assembly(assembly, library, heating_design_temp_f=_HEATING_DESIGN_F,
                                preferences=Preferences())
    interior_c = (Preferences().interior_setpoint_f - 32.0) * 5.0 / 9.0
    exterior_c = (_HEATING_DESIGN_F - 32.0) * 5.0 / 9.0
    surface_drop_fraction = (
        (interior_c - analysis.points[0].temperature_c) / (interior_c - exterior_c)
    )
    total_r_us = INTERIOR_SURFACE_R_US / surface_drop_fraction
    rolled_up = assembly_r_value(assembly, library, include_films=False)
    assert rolled_up.known, rolled_up.unknown_materials
    assert abs((total_r_us - INTERIOR_SURFACE_R_US - EXTERIOR_SURFACE_R_US)
               - rolled_up.value.r_us) < 0.05


def test_vented_rainscreen_truncates_the_glaser_walk() -> None:
    """A furring/airgap cavity outboard of the insulation is a back-vented rainscreen: the
    vent and everything beyond it (cladding) are pressure-equalised with outdoor air and
    must be dropped from the interior-to-exterior vapor walk. An interior service cavity
    (no wettable layer inboard) is not a rainscreen and must be kept."""
    def layer(name: str, function: LayerFunction) -> Layer:
        return Layer(name=name, material_ref="m", thickness=inch(1.0), function=function)

    rainscreen = [
        layer("gwb", LayerFunction.FINISH),
        layer("stud", LayerFunction.STRUCTURE),
        layer("ci", LayerFunction.INSULATION),
        layer("furring", LayerFunction.FURRING),
        layer("cladding", LayerFunction.CLADDING),
    ]
    kept = glaser_layers(rainscreen)
    assert [item.name for item in kept] == ["gwb", "stud", "ci"]

    interior_service_cavity = [
        layer("finish", LayerFunction.FINISH),
        layer("service-gap", LayerFunction.AIRGAP),
        layer("stud", LayerFunction.STRUCTURE),
        layer("sheathing", LayerFunction.SHEATHING),
    ]
    assert len(glaser_layers(interior_service_cavity)) == 4


def _envelope_plan() -> PlanModel:
    material = Material(tag="wool", name="Mineral wool", r_per_inch=4.0, perm_rating=116.0)
    # Cladding is what marks a wall as the above-grade envelope for both the block load
    # and the condensation scoping, so an exterior-wall fixture has to carry one.
    assembly = Assembly(tag="EXT", layers=(
        Layer(name="insulation", material_ref="wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
        Layer(name="siding", material_ref="ply", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ))
    library = Library(materials=(material, _PLYWOOD), assemblies=(assembly,), window_types=(
        WindowType(tag="W", width=ft(4), height=ft(4), u_factor=u_us(0.25), shgc=0.4),
    ))
    project = Project(name="M5", project_uuid="00000000-0000-4000-8000-000000000005",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="M5"))
    storey = Storey(uid="ST00000005", tag="s1", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = tuple(Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position) for i, position in enumerate((
        pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
    ), 1))
    walls = tuple(Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{start}",
                       end_node=f"N-{end}", assembly="EXT", top=ft(9))
                  for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
    window = Window(uid="WN0000005", tag="WIN-1", host="W-1", type_ref="W",
                    position=centered(), sill_height=ft(3))
    room = Room(uid="RM00000005", tag="RM-1", seed=pt(ft(10), ft(7)), occupancy=Occupancy.LIVING)
    return PlanModel(project=project, library=library, storeys=(storey,)).with_elements(
        "s1", (*nodes, *walls, window, room)
    )


def test_wwr_and_energy_use_resolved_opening_area() -> None:
    model, findings = resolve(_envelope_plan())
    assert not findings
    south = next(item for item in analyze_wwr(model) if item.facade == "S")
    assert south.glazing_area_m2 > 0
    report = estimate_block_load(model, Preferences())
    assert report.heating_load_btu_per_hour > 0
    assert report.cooling_load_btu_per_hour > report.heating_load_btu_per_hour * 0.1
    assert "roof/slab resolved geometry" in report.unknown_inputs

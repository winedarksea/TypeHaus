"""Focused M5 golden-style checks for the building-science consumers."""

from __future__ import annotations

from typehaus.checks.building_science.condensation import analyze_assembly
from typehaus.checks.building_science.wwr import analyze_wwr
from typehaus.checks.registry import Preferences
from typehaus.energy import estimate_block_load
from typehaus.model import (
    Assembly, Building, Layer, LayerFunction, Library, Material, Node, Occupancy,
    PlanModel, Project, Room, Site, Storey, Wall, Window, WindowType, centered,
    degF, ft, inch, pt, u_us,
)
from typehaus.resolve import resolve


def test_glaser_reports_crossing_and_missing_perm() -> None:
    wool = Material(tag="wool", name="Mineral wool", r_per_inch=4.0, perm_rating=30.0)
    vapor_closed = Material(tag="barrier", name="Vapor closed membrane", r_per_inch=1.0,
                           perm_rating=0.1)
    assembly = Assembly(tag="RISK", layers=(
        Layer(name="cavity insulation", material_ref="wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
        Layer(name="exterior membrane", material_ref="barrier", thickness=inch(0.1),
              function=LayerFunction.MEMBRANE),
    ))
    library = Library(materials=(wool, vapor_closed))
    risk = analyze_assembly(assembly, library, heating_design_temp_f=-15,
                            preferences=Preferences())
    assert risk.crossing_layer == "cavity insulation"
    assert risk.crossing_fraction is not None

    unknown_material = vapor_closed.model_copy(update={"perm_rating": None})
    unknown = analyze_assembly(assembly, Library(materials=(wool, unknown_material)),
                               heating_design_temp_f=-15, preferences=Preferences())
    assert unknown.unknown_materials == ("Vapor closed membrane",)


def _envelope_plan() -> PlanModel:
    material = Material(tag="wool", name="Mineral wool", r_per_inch=4.0, perm_rating=30.0)
    assembly = Assembly(tag="EXT", layers=(
        Layer(name="insulation", material_ref="wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
    ))
    library = Library(materials=(material,), assemblies=(assembly,), window_types=(
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

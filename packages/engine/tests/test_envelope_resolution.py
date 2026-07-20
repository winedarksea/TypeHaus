"""Regression coverage for resolved roof, slab, foundation, footing, and stair geometry."""

from __future__ import annotations

import uuid

from typehaus.checks.registry import Preferences
from typehaus.emit.draw import build_floorplan
from typehaus.energy import estimate_block_load
from typehaus.model import (
    Assembly, Beam, Building, FloorOpening, FloorSystem, Footing, FoundationWall, FramingSpec,
    JoistSpec, Layer, LayerFunction, Library, Material, Node, PlanModel, Project, Roof, RoofForm,
    Site, Slab, Stair, Storey, Wall, degF, ft, inch, pt,
)
from typehaus.quantities import Pitch
from typehaus.resolve import resolve


def _envelope_plan() -> PlanModel:
    assembly = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="Envelope", project_uuid=uuid.UUID("00000000-0000-4000-8000-000000000099"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Envelope"),
    )
    basement = Storey(uid="STBASE0001", tag="basement", elevation=ft(-8),
                      default_ceiling_height=ft(8))
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1)
    )
    main_walls = tuple(
        Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{start}", end_node=f"N-{end}",
             assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)
    )
    foundation_nodes = tuple(
        node.model_copy(update={"uid": f"B{node.uid[1:]}", "tag": f"B-{index}"})
        for index, node in enumerate(nodes, 1)
    )
    foundation_walls = tuple(
        FoundationWall(uid=f"F{i:09d}", tag=f"F-{i}", start_node=f"B-{start}",
                       end_node=f"B-{end}", assembly="EXT", top_elevation=ft(0),
                       bottom_elevation=ft(-8))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)
    )
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),), assemblies=(assembly,)),
                     storeys=(basement, main))
    basement_elements = (*foundation_nodes, *foundation_walls,
                         Footing(uid="FT00000001", tag="FT-1", under="F-1", width=ft(2),
                                 depth=ft(1)),
                         Stair(uid="SR00000001", tag="S-1", floor_opening="FO-1",
                               from_storey="basement", to_storey="main", width=ft(3),
                               run_direction="x", start=pt(ft(0), ft(0))))
    # Ridge runs x-direction at the roof's mid-y (7'); the beam nodes sit on that
    # line so resolve.framing.roof finds a supporting ridge Beam (no ridge_support
    # WARN) — this fixture predates ridge-beam resolution and stays finding-clean.
    ridge_nodes = (
        Node(uid="NBEAM0001", tag="N-B1", position=pt(ft(0), ft(7))),
        Node(uid="NBEAM0002", tag="N-B2", position=pt(ft(20), ft(7))),
    )
    main_elements = (*nodes, *main_walls, *ridge_nodes,
                     FloorOpening(uid="FO00000001", tag="FO-1", outline=(
                         pt(ft(0), ft(0)), pt(ft(12), ft(0)), pt(ft(12), ft(3)), pt(ft(0), ft(3)),
                     )),
                     FloorSystem(uid="FS00000001", tag="FS-1", joists=JoistSpec(),
                                 openings=("FO-1",)),
                     Slab(uid="SL00000001", tag="SL-1", outline=(
                         pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
                     ), thickness=inch(4), assembly="EXT"),
                     Roof(uid="RF00000001", tag="R-1", form=RoofForm.GABLE, pitch=Pitch(4),
                          bearing_refs=("W-1", "W-3"), assembly="EXT", overhang=ft(1)),
                     Beam(uid="BM00000001", tag="RB-1", start_node="N-B1", end_node="N-B2"))
    return plan.with_elements("basement", basement_elements).with_elements("main", main_elements)


def test_foundation_and_footing_honor_explicit_elevations() -> None:
    model, findings = resolve(_envelope_plan())
    assert not findings
    foundation = model.wall("F-1")
    assert foundation is not None and foundation.z0_m == ft(-8).meters and foundation.z1_m == 0
    footing = next(solid for solid in model.solids if solid.tag == "FT-1")
    assert footing.z1_m == foundation.z0_m
    assert footing.z0_m == foundation.z0_m - ft(1).meters


def test_envelope_surfaces_feed_energy_and_stair_symbol() -> None:
    model, findings = resolve(_envelope_plan())
    assert not findings
    assert model.roofs and model.roofs[0].surface_area_m2 > 0
    assert any(solid.category == "slab" for solid in model.solids)
    assert model.stairs and model.stairs[0].riser_count > 0
    assert len(model.stairs[0].members) > model.stairs[0].riser_count
    report = estimate_block_load(model, Preferences())
    assert {component.kind for component in report.components} >= {
        "roof", "slab", "foundation_walls",
    }
    assert not any("roof/slab" in item for item in report.unknown_inputs)
    scene = build_floorplan(model, "basement")
    assert any(getattr(node, "content", "").startswith("UP ") for node in scene.nodes)

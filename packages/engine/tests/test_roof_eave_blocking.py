"""``Roof.eave_blocking``: one on-edge block per rafter bay at a plumb-cut eave.

A synthetic 20'x14' box with a zero-overhang I-joist gable, ridge along x, so the eaves are the
south and north walls and the plumb cut is each wall's stud exterior face.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.model import (
    Assembly,
    Building,
    FramingSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Roof,
    RoofForm,
    Site,
    Storey,
    ToRoof,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.quantities import Pitch
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import cross_section

RAFTER = "11.875 TJI 230"
PLATE_TOP_FT = 9.0


def _plan(*, eave_blocking: str | None, overhang=None, frame: str = "rafter") -> PlanModel:
    wall_assembly = Assembly(tag="EXT", layers=(
        Layer(name="sheathing", material_ref="wood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    framing = (FramingSpec(member=RAFTER, spacing=inch(24)) if frame == "rafter" else
               FramingSpec(member="2x4", roof_frame="truss", heel_height=inch(9.25),
                           chord_member="2x4", web_member="2x4"))
    roof_assembly = Assembly(tag="ROOF", layers=(
        Layer(name="structure", material_ref="wood", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE, framing=framing),
    ))
    project = Project(
        name="Eave", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000e1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Eave"),
    )
    storey = Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(PLATE_TOP_FT))
    nodes = (
        Node(uid="N000000001", tag="N-SW", position=pt(ft(0), ft(0))),
        Node(uid="N000000002", tag="N-SE", position=pt(ft(20), ft(0))),
        Node(uid="N000000003", tag="N-NE", position=pt(ft(20), ft(14))),
        Node(uid="N000000004", tag="N-NW", position=pt(ft(0), ft(14))),
    )
    walls = (
        Wall(uid="W000000001", tag="W-S", start_node="N-SW", end_node="N-SE",
             assembly="EXT", top=ft(PLATE_TOP_FT)),
        Wall(uid="W000000002", tag="W-E", start_node="N-SE", end_node="N-NE",
             assembly="EXT", top=ToRoof(roof_ref="RF")),
        Wall(uid="W000000003", tag="W-N", start_node="N-NE", end_node="N-NW",
             assembly="EXT", top=ft(PLATE_TOP_FT)),
        Wall(uid="W000000004", tag="W-W", start_node="N-NW", end_node="N-SW",
             assembly="EXT", top=ToRoof(roof_ref="RF")),
    )
    roof = Roof(uid="RF00000001", tag="RF", form=RoofForm.GABLE, pitch=Pitch(6, 12),
                bearing_refs=("W-S", "W-N"), assembly="ROOF", overhang=overhang or ft(0),
                ridge_direction="x", eave_blocking=eave_blocking)
    library = Library(materials=(Material(tag="wood", name="Wood", r_per_inch=1.2),),
                      assemblies=(wall_assembly, roof_assembly))
    return PlanModel(project=project, library=library, storeys=(storey,)).with_elements(
        "main", [*nodes, *walls, roof])


def _category(model, category):
    return [m for m in model.roofs[0].members if m.category == category]


def test_one_block_per_bay_per_eave_between_flange_faces_on_the_plate():
    model, _ = resolve(_plan(eave_blocking="2x6"))
    roof = model.roofs[0]
    rafters = _category(model, "rafter")
    blocks = _category(model, "blocking")
    per_side = len(rafters) // 2
    assert per_side >= 2
    assert len(blocks) == 2 * (per_side - 1)

    flange = cross_section(RAFTER).width_m
    block = cross_section("2x6")
    for side in ("lo", "hi"):
        side_blocks = [b for b in blocks if b.child_key.startswith(f"eave-block-{side}-")]
        assert len(side_blocks) == per_side - 1
        # The rafter tails on this side all land on one plumb-cut plane.
        cut = {round(r.p0[1], 6) for r in rafters
               if (r.p0[1] < r.p1[1]) == (side == "lo")}
        assert len(cut) == 1
        cut_y = cut.pop()
        stations = sorted(r.p0[0] for r in rafters if round(r.p0[1], 6) == cut_y)
        for b, (a, c) in zip(sorted(side_blocks, key=lambda m: m.p0[0]),
                             zip(stations, stations[1:], strict=False), strict=True):
            assert b.profile == "2x6" and b.connection == "eave:blocking"
            assert min(b.p0[0], b.p1[0]) == pytest.approx(a + flange / 2)
            assert max(b.p0[0], b.p1[0]) == pytest.approx(c - flange / 2)
            assert b.length_m == pytest.approx(c - a - flange)
            # Outer face on the cut plane, thickness inboard.
            inboard = 1.0 if side == "lo" else -1.0
            assert b.p0[1] == pytest.approx(cut_y + inboard * block.width_m / 2)
            assert b.z0_m == pytest.approx(roof.bearing_z_m)
            assert b.z1_m - b.z0_m == pytest.approx(block.depth_m)


def test_no_blocking_unless_authored():
    model, _ = resolve(_plan(eave_blocking=None))
    assert _category(model, "blocking") == []


def test_no_blocking_where_the_eave_has_no_plumb_cut():
    model, _ = resolve(_plan(eave_blocking="2x6", overhang=inch(16)))
    assert _category(model, "blocking") == []


def test_truss_roof_takes_no_eave_blocking():
    model, _ = resolve(_plan(eave_blocking="2x6", frame="truss"))
    assert _category(model, "blocking") == []

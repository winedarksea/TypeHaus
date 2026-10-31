"""CFA (``resolve.conditioned_area``) on a house whose answer is known by hand.

20' x 30' at the sheathing, two storeys, 4" of foam and cladding outboard (which is not floor
area), a 3' x 10' stair well in the second floor (deducted there, once), and an 8' x 10'
unconditioned porch teed into the east wall (never counted). 600 + 570 = 1,170 sf.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.model import (
    Assembly,
    Building,
    FloorOpening,
    FloorSystem,
    FramingSpec,
    JoistSpec,
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
    degF,
    ft,
    inch,
    pt,
)
from typehaus.model.refs import face
from typehaus.resolve import resolve
from typehaus.resolve.conditioned_area import conditioned_floor_area

_HOUSE = ((0, 0), (20, 0), (20, 10), (20, 20), (20, 30), (0, 30))
_PORCH = ((28, 10), (28, 20))


def _walls(prefix: str, storey: str, assembly: str, pairs, top) -> tuple:
    return tuple(Wall(uid=f"W{storey[:2].upper()}{prefix}{i:05d}", tag=f"W-{storey}-{prefix}{i}",
                      start_node=a, end_node=b, assembly=assembly, top=top,
                      alignment=face("sheathing-ext") if assembly == "EXT" else None)
                 for i, (a, b) in enumerate(pairs, 1))


def _storey(storey: str, porch: bool) -> tuple:
    points = _HOUSE + (_PORCH if porch else ())
    nodes = tuple(Node(uid=f"N{storey[:2].upper()}{i:07d}", tag=f"N-{storey}-{i}",
                       position=pt(ft(x), ft(y))) for i, (x, y) in enumerate(points, 1))
    tag = [n.tag for n in nodes]
    house = _walls("H", storey, "EXT", [(tag[i], tag[(i + 1) % 6]) for i in range(6)], ft(9))
    room = Room(uid=f"RM{storey[:2].upper()}000001", tag=f"RM-{storey}",
                seed=pt(ft(10), ft(15)), occupancy=Occupancy.LIVING)
    out = (*nodes, *house, room)
    if porch:
        out += (*_walls("P", storey, "GUARD",
                        [(tag[2], tag[6]), (tag[6], tag[7]), (tag[7], tag[3])], ft(3)),
                Room(uid="RMPORCH001", tag="RM-PORCH", seed=pt(ft(24), ft(15)),
                     occupancy=Occupancy.STORAGE, conditioned=False))
    return out


def _plan() -> PlanModel:
    ext = Assembly(tag="EXT", layers=(
        Layer(name="gwb", material_ref="gwb", thickness=inch(0.5), function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="sheathing", material_ref="wood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="foam", material_ref="foam", thickness=inch(4),
              function=LayerFunction.INSULATION),
        Layer(name="cladding", material_ref="clad", thickness=inch(0.75),
              function=LayerFunction.CLADDING),
    ))
    guard = Assembly(tag="GUARD", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4")),
    ))
    materials = tuple(Material(tag=t, name=t, r_per_inch=1.0)
                      for t in ("wood", "gwb", "foam", "clad"))
    project = Project(
        name="CFA", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000cf"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="CFA"))
    plan = PlanModel(project=project, library=Library(materials=materials,
                                                      assemblies=(ext, guard)),
                     storeys=(Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                                     default_ceiling_height=ft(9)),
                              Storey(uid="STSECOND01", tag="second", elevation=ft(10),
                                     default_ceiling_height=ft(9))))
    well = FloorOpening(uid="FO00000001", tag="FO-WELL", outline=(
        pt(ft(2), ft(10)), pt(ft(5), ft(10)), pt(ft(5), ft(20)), pt(ft(2), ft(20))))
    deck = FloorSystem(uid="FS00000001", tag="FS-2", joists=JoistSpec(), openings=("FO-WELL",))
    return (plan.with_elements("main", _storey("main", porch=True))
            .with_elements("second", (*_storey("second", porch=False), well, deck)))


def test_cfa_runs_to_the_sheathing_deducts_the_well_once_and_skips_the_porch() -> None:
    model, findings = resolve(_plan())
    assert not [f for f in findings if f.severity.value == "error"]
    rows = {row.storey: row for row in conditioned_floor_area(model).storeys}
    assert set(rows) == {"main", "second"}
    assert rows["main"].area_ft2 == pytest.approx(600.0, abs=0.05)
    assert rows["second"].gross_m2 == pytest.approx(rows["main"].gross_m2, rel=1e-6)
    assert rows["second"].deductions == ("FO-WELL",)
    assert rows["second"].area_ft2 == pytest.approx(570.0, abs=0.05)
    assert conditioned_floor_area(model).area_ft2 == pytest.approx(1170.0, abs=0.1)

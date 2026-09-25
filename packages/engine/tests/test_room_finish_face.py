"""``ResolvedRoom.clear_face`` is the finish face; ``axis_face`` is the ownership cell.

Two rooms, 10' x 10' and 8' x 10' on axes, every wall the same symmetric 1/2" gwb / 3 1/2"
stud / 1/2" gwb stack (4 1/2", so each finish face sits 2 1/4" off its axis whichever way the
stack is aligned). Worked by hand:

    A: (120 - 4.5) x (120 - 4.5) = 115.5 x 115.5 in = 92.64 sf
    B: ( 96 - 4.5) x (120 - 4.5) =  91.5 x 115.5 in = 73.39 sf
"""

from __future__ import annotations

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model import (
    Assembly,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Occupancy,
    PlanModel,
    Room,
    Storey,
    Wall,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve
from typehaus.resolve.room_lookup import room_owning
from typehaus.resolve.room_walls import bounding_walls

_SF = 10.7639


def _plan(project, seed_b=None):
    gwb = Layer(name="gwb", material_ref="gyp", thickness=inch(0.5),
                function=LayerFunction.FINISH)
    assembly = Assembly(tag="P", layers=(
        gwb, Layer(name="stud", material_ref="wood", thickness=inch(3.5),
                   function=LayerFunction.STRUCTURE), gwb.model_copy(update={"name": "gwb2"})))
    storey = Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(8))
    points = {"A": (0, 0), "B": (10, 0), "C": (18, 0), "D": (18, 10), "E": (10, 10),
              "F": (0, 10)}
    nodes = [Node(uid=f"N0000000{i:02d}", tag=f"N{k}", position=pt(ft(x), ft(y)))
             for i, (k, (x, y)) in enumerate(points.items())]
    edges = ("AB", "BC", "CD", "DE", "EF", "FA", "BE")
    walls = [Wall(uid=f"W0000000{i:02d}", tag=f"W{e}", start_node=f"N{e[0]}",
                  end_node=f"N{e[1]}", assembly="P", top=ft(8))
             for i, e in enumerate(edges)]
    rooms = [Room(uid="R000000001", tag="RM-A", seed=pt(ft(5), ft(5)),
                  occupancy=Occupancy.LIVING),
             Room(uid="R000000002", tag="RM-B", seed=seed_b or pt(ft(14), ft(5)),
                  occupancy=Occupancy.LIVING)]
    return PlanModel(
        project=project,
        library=Library(materials=(Material(tag="wood", name="Wood", r_per_inch=1.2),
                                   Material(tag="gyp", name="Gypsum", r_per_inch=0.9)),
                        assemblies=(assembly,)),
        storeys=(storey,),
    ).with_elements("main", [*nodes, *walls, *rooms])


def test_two_rooms_read_their_hand_worked_finish_rectangles(project):
    model, _ = resolve(_plan(project))
    rooms = {r.tag: r for r in model.rooms}
    assert rooms["RM-A"].area_m2 * _SF == pytest.approx(115.5 * 115.5 / 144, abs=0.01)
    assert rooms["RM-B"].area_m2 * _SF == pytest.approx(91.5 * 115.5 / 144, abs=0.01)
    xs = sorted({round(x / inch(1).meters, 3) for x, _y in rooms["RM-B"].clear_face})
    assert xs == [122.25, 213.75]
    # The axis cell is untouched: ownership still tiles the storey.
    assert Polygon(rooms["RM-A"].axis_face).area * _SF == pytest.approx(100.0)


def test_a_point_inside_the_partition_is_owned_but_in_no_clear_face(project):
    model, _ = resolve(_plan(project))
    xy = (ft(10).meters + inch(1).meters, ft(5).meters)  # 1" east of the partition axis
    assert not any(Polygon(r.clear_face).covers(Point(xy)) for r in model.rooms)
    assert room_owning(model, "main", xy).tag == "RM-B"


def test_bounding_walls_follow_the_finish_face(project):
    model, _ = resolve(_plan(project))
    room = next(r for r in model.rooms if r.tag == "RM-A")
    runs = {wall.tag: hi - lo for wall, (lo, hi) in bounding_walls(model, room)}
    assert set(runs) == {"WAB", "WEF", "WFA", "WBE"}
    for run in runs.values():
        assert run / inch(1).meters == pytest.approx(115.5, abs=0.01)


def test_a_seed_inside_a_wall_is_an_error(project):
    # 1" east of the partition axis: inside RM-B's cell, inside the wall's layers.
    model, findings = resolve(_plan(project, seed_b=pt(inch(121), ft(5))))
    hits = [f for f in findings if f.check_id == "integrity.room_seed_in_wall"]
    assert len(hits) == 1 and hits[0].severity.value == "error"
    assert "RM-B" not in {r.tag for r in model.rooms}

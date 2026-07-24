"""Plan-junction geometry is shared by drawings, 3D, framing, DXF, and IFC."""

from __future__ import annotations

from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.model import (
    Assembly,
    CavityFill,
    FramingSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Storey,
    Wall,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve
from typehaus.server.model_json import model_to_dict


def _library() -> Library:
    materials = tuple(Material(tag=tag, name=tag) for tag in (
        "gwb", "spf", "wool", "osb", "foam", "metal",
    ))
    interior = Assembly(tag="INT", layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="wool")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ))
    exterior = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6"),
              cavity=CavityFill(material_ref="wool")),
        Layer(name="sheathing", material_ref="osb", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="foam", material_ref="foam", thickness=inch(4),
              function=LayerFunction.INSULATION),
        Layer(name="cladding", material_ref="metal", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ))
    # A second, different interior assembly that shares the SPF bearing material — a mixed
    # junction the solver resolves by structural continuity, not by a matching layer name.
    plumbing = Assembly(tag="PLUMB", layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="wet-stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ))
    return Library(materials=materials, assemblies=(interior, exterior, plumbing))


def _plan(project, coordinates, edges) -> PlanModel:
    storey = Storey(uid="STJUNCTION", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    nodes = [
        Node(uid=f"JN{index:08d}", tag=tag, position=pt(ft(x), ft(y)),
             open_end=tag != "C")
        for index, (tag, (x, y)) in enumerate(coordinates.items())
    ]
    walls = [
        Wall(uid=f"JW{index:08d}", tag=tag, start_node=start, end_node=end,
             assembly=assembly, top=ft(9))
        for index, (tag, start, end, assembly) in enumerate(edges)
    ]
    return PlanModel(project=project, library=_library(), storeys=(storey,)).with_elements(
        "main", [*nodes, *walls]
    )


def test_same_assembly_l_corner_miters_every_layer_and_cavity(project) -> None:
    plan = _plan(
        project,
        {"C": (0, 0), "E": (10, 0), "NE": (10, 10), "N": (0, 10)},
        [
            ("W-E", "C", "E", "EXT"), ("W-NE", "E", "NE", "EXT"),
            ("W-N", "N", "C", "EXT"), ("W-NW", "NE", "N", "EXT"),
        ],
    )
    model, findings = resolve(plan)
    assert not [finding for finding in findings if finding.severity.value == "error"]
    junction = next(item for item in model.junctions if item.node_tag == "C")
    assert junction.kind == "l" and junction.supported

    east, north = model.wall("W-E"), model.wall("W-N")
    assert east is not None and north is not None
    for layer_name in ("stud", "sheathing", "foam", "cladding"):
        first = Polygon(next(layer for layer in east.layers if layer.name == layer_name).polygon)
        second = Polygon(next(layer for layer in north.layers if layer.name == layer_name).polygon)
        assert first.is_valid and second.is_valid
        assert first.intersection(second).area < 1e-10
        assert first.distance(second) < 1e-9
    stud = next(layer for layer in east.layers if layer.name == "stud")
    cavity = next(layer for layer in east.layers if layer.name == "stud-cavity")
    assert cavity.polygon == stud.polygon
    assert any(member.category == "corner" for member in east.members)


def test_non_orthogonal_l_corner_has_no_miter_overlap(project) -> None:
    plan = _plan(
        project,
        {"C": (0, 0), "E": (10, 0), "D": (7, 7)},
        [("W-E", "C", "E", "INT"), ("W-D", "C", "D", "INT")],
    )
    model, _ = resolve(plan)
    walls = [model.wall(tag) for tag in ("W-E", "W-D")]
    polygons = [Polygon(next(layer for layer in wall.layers if layer.name == "stud").polygon)
                for wall in walls if wall is not None]
    assert polygons[0].intersection(polygons[1]).area < 1e-10
    assert polygons[0].distance(polygons[1]) < 1e-9


def test_mixed_exterior_partition_tee_butts_against_envelope(project) -> None:
    plan = _plan(
        project,
        {"L": (-10, 0), "C": (0, 0), "R": (10, 0), "B": (0, -10)},
        [
            ("W-L", "L", "C", "EXT"),
            ("W-R", "C", "R", "EXT"),
            ("W-B", "B", "C", "INT"),
        ],
    )
    model, findings = resolve(plan)
    junction = next(item for item in model.junctions if item.node_tag == "C")
    assert junction.kind == "t" and junction.supported
    assert not [finding for finding in findings
                if finding.check_id == "integrity.junction_fallback"]
    host = unary_union([
        Polygon(layer.polygon)
        for tag in ("W-L", "W-R")
        for layer in model.wall(tag).depth_layers()
    ])
    branch = unary_union([
        Polygon(layer.polygon) for layer in model.wall("W-B").depth_layers()
    ])
    assert host.intersection(branch).area < 1e-10
    assert host.distance(branch) < 1e-9
    assert any(member.category == "blocking" for tag in ("W-L", "W-R")
               for member in model.wall(tag).members)


def test_x_junction_and_json_diagnostics_are_deterministic(project) -> None:
    plan = _plan(
        project,
        {"L": (-10, 0), "C": (0, 0), "R": (10, 0), "B": (0, -10), "T": (0, 10)},
        [
            ("W-L", "L", "C", "INT"), ("W-R", "C", "R", "INT"),
            ("W-B", "B", "C", "INT"), ("W-T", "C", "T", "INT"),
        ],
    )
    model, _ = resolve(plan)
    junction = next(item for item in model.junctions if item.node_tag == "C")
    assert junction.kind == "x"
    encoded = next(item for item in model_to_dict(model)["junctions"] if item["node"] == "C")
    assert encoded["through_walls"] == sorted(encoded["through_walls"])
    assert encoded["supported"] is True


def test_mixed_interior_tee_resolves_by_structural_continuity(project) -> None:
    # Two INT through walls (one continuous SPF bearing line) with a different-assembly SPF
    # branch: mixed assembly, no cladding, so it is neither same-assembly nor a basic mixed
    # tee — it resolves through the shared bearing role and the branch butts the host.
    plan = _plan(
        project,
        {"L": (-10, 0), "C": (0, 0), "R": (10, 0), "B": (0, -10)},
        [
            ("W-L", "L", "C", "INT"),
            ("W-R", "C", "R", "INT"),
            ("W-B", "B", "C", "PLUMB"),
        ],
    )
    model, findings = resolve(plan)
    junction = next(item for item in model.junctions if item.node_tag == "C")
    assert junction.kind == "t" and junction.supported
    assert not [f for f in findings if f.check_id == "integrity.junction_fallback"]
    host = unary_union([
        Polygon(layer.polygon)
        for tag in ("W-L", "W-R")
        for layer in model.wall(tag).depth_layers()
    ])
    branch = unary_union([
        Polygon(layer.polygon) for layer in model.wall("W-B").depth_layers()
    ])
    assert host.intersection(branch).area < 1e-10
    assert host.distance(branch) < 1e-9


def test_mixed_l_corner_shares_bearing_and_is_supported(project) -> None:
    plan = _plan(
        project,
        {"C": (0, 0), "E": (10, 0), "N": (0, 10)},
        [("W-E", "C", "E", "INT"), ("W-N", "C", "N", "PLUMB")],
    )
    model, findings = resolve(plan)
    junction = next(item for item in model.junctions if item.node_tag == "C")
    assert junction.kind == "l" and junction.supported
    assert not [f for f in findings if f.check_id == "integrity.junction_fallback"]
    east = Polygon(next(ly for ly in model.wall("W-E").layers if ly.name == "stud").polygon)
    north = Polygon(next(ly for ly in model.wall("W-N").layers
                         if ly.name == "wet-stud").polygon)
    assert east.intersection(north).area < 1e-10


def test_stacked_walls_at_one_node_split_into_elevation_tiers() -> None:
    from typehaus.resolve.model import JunctionIncident
    from typehaus.resolve.topology import _classify_tier, _tiers

    # Two walls sharing a plan point but not an elevation band — a guard stacked on a wall.
    lower = JunctionIncident("LOWER", "start", (1.0, 0.0), "CONC", -3.0, 0.0)
    upper = JunctionIncident("UPPER", "start", (1.0, 0.0), "RAIL", 0.0, 1.1)
    tiers = _tiers([lower, upper])
    assert len(tiers) == 2, "stacked walls must not fuse into one high-valence node"
    # A retaining wall poking a little above grade still fuses with its own run below.
    a = JunctionIncident("A", "start", (1.0, 0.0), "CONC", -3.0, 0.15)
    b = JunctionIncident("B", "end", (-1.0, 0.0), "CONC", -3.0, 0.0)
    assert len(_tiers([a, b])) == 1


def test_junction_solved_polygons_round_trip_through_dxf(project, tmp_path) -> None:
    import ezdxf

    from typehaus.emit.draw import build_floorplan, write_dxf

    plan = _plan(
        project,
        {"C": (0, 0), "E": (10, 0), "NE": (10, 10), "N": (0, 10)},
        [
            ("W-E", "C", "E", "EXT"), ("W-NE", "E", "NE", "EXT"),
            ("W-N", "N", "C", "EXT"), ("W-NW", "NE", "N", "EXT"),
        ],
    )
    model, _ = resolve(plan)
    path = write_dxf(build_floorplan(model, "main"), tmp_path / "junctions.dxf")
    document = ezdxf.readfile(path)
    polylines = list(document.modelspace().query("LWPOLYLINE"))
    wall_polylines = [
        polyline for polyline in polylines
        if polyline.has_xdata("TYPEHAUS") and polyline.closed
    ]
    assert wall_polylines
    for polyline in wall_polylines:
        polygon = Polygon([(point[0], point[1]) for point in polyline.get_points()])
        assert polygon.is_valid and polygon.area > 0

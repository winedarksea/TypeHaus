"""Door operation → plan symbol + framing pattern (→ 20 §Drawing IR, 11 §Framing).

Covers the two operations that are not hinged leaves: an overhead sectional garage door
and a bifold pair. Both used to fall through to the 90° swing glyph and to swing-door
framing, which is wrong in plan *and* in the takeoff.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.emit.draw import build_floorplan, write_dxf, write_raster
from typehaus.emit.draw.door_symbols import (
    DOOR_BIFOLD,
    DOOR_OVERHEAD,
    DOOR_SWING,
    DOOR_SWING_DOUBLE,
    door_symbol_geometry,
    door_symbol_params,
)
from typehaus.emit.draw.scene import Symbol
from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import DoorOperation, LayerFunction
from typehaus.model.types import DoorType
from typehaus.quantities import ft, inch
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.solver import frame_wall
from typehaus.resolve.framing.tables import ENGINEERED_LVL, header_depth, header_size
from typehaus.resolve.model import ResolvedWall

GARAGE_DOOR_WIDTH = ft(16)
GARAGE_DOOR_HEIGHT = ft(7)


# --- the enum ---------------------------------------------------------------------


def test_door_operation_accepts_the_legacy_string_form():
    # Authored plan sources and stored model JSON both carry bare strings.
    assert DoorType(tag="DT-X", width=ft(3), height=ft(6, 8),
                    operation="overhead").operation is DoorOperation.OVERHEAD
    assert DoorType(tag="DT-Y", width=ft(3), height=ft(6, 8)).operation is DoorOperation.SWING


def test_door_operation_rejects_an_unknown_value():
    with pytest.raises(ValueError):
        DoorType(tag="DT-Z", width=ft(3), height=ft(6, 8), operation="barn")


# --- plan symbols -----------------------------------------------------------------


def _symbol(name: str, width_in: float, height_in: float = 84.0,
            swing_sign: float = 1.0, rotation: float = 0.0) -> Symbol:
    return Symbol(name=name, insert=(0.0, 0.0), rotation=rotation, scale=width_in,
                  layer="A-DOOR",
                  params=door_symbol_params(name, width_in, height_in, swing_sign))


def test_overhead_symbol_draws_track_and_never_a_swing_arc():
    geometry = door_symbol_geometry(_symbol(DOOR_OVERHEAD, 192.0))
    assert not geometry.arcs, "an overhead sectional does not swing"
    solid = [stroke for stroke in geometry.strokes if not stroke.dashed]
    dashed = [stroke for stroke in geometry.strokes if stroke.dashed]
    # The closed panel spans the opening; the two track legs and the parked panel are
    # above the cut plane and therefore dashed.
    assert len(solid) == 1 and len(dashed) == 3
    (panel,) = solid
    assert abs(panel.points[1][0] - panel.points[0][0]) == pytest.approx(192.0)
    # Track projects into the garage by the door height, on the handed operating side.
    assert max(point[1] for stroke in geometry.strokes for point in stroke.points) \
        == pytest.approx(84.0)


def test_overhead_symbol_track_follows_the_authored_handing():
    flipped = door_symbol_geometry(_symbol(DOOR_OVERHEAD, 192.0, swing_sign=-1.0))
    assert min(point[1] for stroke in flipped.strokes for point in stroke.points) \
        == pytest.approx(-84.0)


def test_bifold_symbol_folds_real_length_leaves_without_an_arc():
    width_in = 60.0
    geometry = door_symbol_geometry(_symbol(DOOR_BIFOLD, width_in))
    assert not geometry.arcs, "a bifold folds against its jambs, it does not swing"
    assert len(geometry.strokes) == 2, "one folded run per half of the pair"
    leaf_length = width_in / 4
    for stroke in geometry.strokes:
        jamb, knuckle, leading_edge = stroke.points
        assert _distance(jamb, knuckle) == pytest.approx(leaf_length)
        assert _distance(knuckle, leading_edge) == pytest.approx(leaf_length)
        assert knuckle[1] > 0, "the knuckle folds toward the operating side"


def test_swing_symbols_keep_their_previous_geometry():
    """Routing the hinged glyphs through the shared module must not move them."""
    single = door_symbol_geometry(_symbol(DOOR_SWING, 36.0))
    (leaf,) = single.strokes
    assert leaf.points == ((0.0, 0.0), pytest.approx((0.0, 36.0)))
    (arc,) = single.arcs
    assert (arc.center, arc.radius, arc.start_angle_deg, arc.end_angle_deg) \
        == ((0.0, 0.0), 36.0, 0.0, 90.0)
    double = door_symbol_geometry(_symbol(DOOR_SWING_DOUBLE, 36.0))
    assert len(double.strokes) == 2 and len(double.arcs) == 2
    assert all(arc.radius == pytest.approx(18.0) for arc in double.arcs)


def _distance(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


# --- the floorplan builder --------------------------------------------------------


def test_catlin_garage_door_emits_the_overhead_symbol(catlin_model):
    garage_door = next(op for op in catlin_model.openings if op.tag == "D-G-OVERHEAD")
    symbols = {node.uid: node for node in build_floorplan(catlin_model, "garage").nodes
               if isinstance(node, Symbol)}
    overhead = symbols[garage_door.uid]
    assert overhead.name == DOOR_OVERHEAD, "the 16 ft sectional must not draw a swing arc"
    assert overhead.params["width_in"] == pytest.approx(GARAGE_DOOR_WIDTH.inches)
    assert overhead.params["track_depth_in"] == pytest.approx(GARAGE_DOOR_HEIGHT.inches)
    assert not door_symbol_geometry(overhead).arcs


def test_catlin_interior_bifolds_emit_the_bifold_symbol(catlin_model):
    names = {node.name for node in build_floorplan(catlin_model, "main").nodes
             if isinstance(node, Symbol)}
    assert DOOR_BIFOLD in names


def test_new_symbols_survive_both_writers(catlin_model, tmp_path):
    scene = build_floorplan(catlin_model, "garage")
    assert write_dxf(scene, tmp_path / "garage.dxf").exists()
    assert write_raster(scene, tmp_path / "garage.png").exists()


# --- framing ----------------------------------------------------------------------


def _wall_and_plan() -> tuple[SimpleNamespace, ResolvedWall]:
    layer = Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    wall = ResolvedWall(uid="W1", tag="W-GARAGE", storey="GARAGE", assembly="TEST_ASM",
                        axis=((0.0, 0.0), (8.0, 0.0)), layers=(), z0_m=0.0, z1_m=3.0)
    return plan, wall


def _overhead_members():
    plan, wall = _wall_and_plan()
    opening = WallOpening(center_m=4.0, width_m=GARAGE_DOOR_WIDTH.meters,
                          height_m=GARAGE_DOOR_HEIGHT.meters, sill_m=0.0, is_door=True,
                          operation=DoorOperation.OVERHEAD)
    return frame_wall(plan, wall, openings=[opening])


def test_overhead_jamb_pack_is_sized_from_the_span_not_the_prescriptive_cap():
    members = _overhead_members()
    jacks = [m for m in members if m.child_key.startswith("jack-")]
    kings = [m for m in members if m.category == "king"]
    # 16 ft at one trimmer per 6 ft → three a side, matched by kings. The width-only
    # prescriptive table caps at two of each however wide the opening gets.
    assert len(jacks) == 6 and len(kings) == 6


def test_overhead_door_gets_track_jamb_legs_and_head_backing():
    members = _overhead_members()
    legs = [m for m in members if m.child_key.startswith("trackjamb-")]
    backing = [m for m in members if m.child_key.startswith("trackbacking-")]
    assert len(legs) == 2 and len(backing) == 1
    assert all(m.profile == "2x6" for m in legs + backing)
    header = next(m for m in members if m.category == "header")
    # The legs stop at the header rather than running through it.
    assert all(m.z1_m == pytest.approx(header.z0_m) for m in legs)
    # The backing sits directly on the header, where the ceiling track hangs from.
    assert backing[0].z0_m == pytest.approx(header.z1_m)


def test_overhead_header_carries_a_real_engineered_depth():
    header = next(m for m in _overhead_members() if m.category == "header")
    assert header.profile == ENGINEERED_LVL
    # 16 ft at L/20 rounds up to the 11-7/8" stocked LVL depth, not the old flat 0.14 m.
    assert header.z1_m - header.z0_m == pytest.approx(inch(11.875).meters)


def test_header_depth_follows_the_named_size():
    assert header_depth("2-2x8", ft(4)).inches == pytest.approx(7.25)
    assert header_depth("2-2x12", ft(8)).inches == pytest.approx(11.25)
    assert header_depth(header_size(ft(16)), ft(16)).inches == pytest.approx(11.875)


def test_bifold_gets_a_flat_head_instead_of_a_bearing_header():
    plan, wall = _wall_and_plan()
    opening = WallOpening(center_m=4.0, width_m=ft(5).meters, height_m=ft(6, 8).meters,
                          sill_m=0.0, is_door=True, operation=DoorOperation.BIFOLD)
    members = frame_wall(plan, wall, openings=[opening])
    header = next(m for m in members if m.category == "header")
    # A bifold hangs from its own head track in a partition; it is not a bearing opening,
    # and it gets none of the overhead door's track framing.
    assert header.profile == "2-2x6"
    assert not [m for m in members if m.child_key.startswith("track")]

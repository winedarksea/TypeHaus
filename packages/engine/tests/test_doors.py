"""Door operation → plan symbol + framing pattern (→ 20 §Drawing IR, 11 §Framing).

Covers the operations that are not a plain hinged leaf — overhead sectional, bifold,
sliding and pocket — each of which used to fall through to the 90° swing glyph (and, for
the sectional, to swing-door framing), which is wrong in plan *and* in the takeoff. It
also pins the swing arc's handedness, and the writers' coverage of the whole plan symbol
vocabulary: an unstyled name is not a missing glyph but a wrong one.
"""

from __future__ import annotations

import math
from dataclasses import replace
from types import SimpleNamespace

import pytest

from library import STARTER_DOOR_TYPES
from typehaus.emit.draw import build_floorplan, write_dxf, write_raster
from typehaus.emit.draw.door_symbols import (
    DOOR_BIFOLD,
    DOOR_OVERHEAD,
    DOOR_POCKET,
    DOOR_SLIDING,
    DOOR_SWING,
    DOOR_SWING_DOUBLE,
    SLIDING_PANEL_CLEARANCE_IN,
    SymbolArc,
    door_symbol_geometry,
    door_symbol_params,
    symbol_name_for_operation,
)
from typehaus.emit.draw.scene import Symbol
from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import DoorOperation, LayerFunction
from typehaus.model.types import DoorType
from typehaus.quantities import ft, inch
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.pockets import pocket_segments
from typehaus.resolve.framing.solver import frame_wall
from typehaus.resolve.framing.tables import (
    ENGINEERED_LVL,
    header_depth,
    header_size,
    pocket_run,
)
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


def test_catlin_door_catalog_tags_state_operation_and_width(catlin_model):
    types = {door_type.tag: door_type for door_type in catlin_model.plan.library.door_types}
    expected = {
        "DT-EXT-SWING36": (36.0, DoorOperation.SWING, True, False),
        "DT-EXT-FRENCH60": (60.0, DoorOperation.DOUBLE_SWING, True, True),
        "DT-EXT-SLIDE60": (60.0, DoorOperation.SLIDE, True, True),
        "DT-INT-SWING32": (32.0, DoorOperation.SWING, False, False),
        "DT-INT-SWING30": (30.0, DoorOperation.SWING, False, False),
        "DT-INT-SWING30-GLAZED": (30.0, DoorOperation.SWING, False, True),
        "DT-INT-SWING30-TRIMLESS": (30.0, DoorOperation.SWING, False, False),
        "DT-INT-SWING24": (24.0, DoorOperation.SWING, False, False),
        "DT-INT-BIFOLD60": (60.0, DoorOperation.BIFOLD, False, False),
        "DT-INT-BIFOLD56": (56.0, DoorOperation.BIFOLD, False, False),
        # RM-M-MUD-CLOSET's bypass slider (2026-08-02): the framed replacement for
        # FURN-M-MUD-CLOSET-S keeps the furniture's sliding-door intent.
        "DT-INT-BYPASS48": (48.0, DoorOperation.SLIDE, False, False),
        # RM-M-PANTRY's bypass pair (2026-08-24). The 60" leaf D-M-MUDC could not have:
        # W-M-MUDC-N's framed span is 63 1/8" and a 62" RO leaves 1 1/8" for jamb packs,
        # where W-M-PAN-S offers 71 1/2".
        "DT-INT-BYPASS60": (60.0, DoorOperation.SLIDE, False, False),
        "DT-INT-DOUBLE60": (60.0, DoorOperation.DOUBLE_SWING, False, False),
        "DT-EXT-OVERHEAD192": (192.0, DoorOperation.OVERHEAD, True, False),
    }
    # The house catalog is the union of its own types and the library's shared pocket
    # family (2026-08-21), which is what D-M-LAUN is typed from. The two tag sets must
    # stay disjoint — `integrity.duplicate_catalog_tag` proves it at load time, and this
    # pins that the promotion did not quietly shadow a house type.
    library_pockets = {door_type.tag for door_type in STARTER_DOOR_TYPES}
    assert set(types) == set(expected) | library_pockets
    assert not (set(expected) & library_pockets)
    assert all(types[tag].operation is DoorOperation.POCKET for tag in library_pockets)
    for tag, (width_in, operation, exterior, glazed) in expected.items():
        door_type = types[tag]
        assert door_type.width.inches == pytest.approx(width_in)
        assert door_type.operation is operation
        assert door_type.exterior is exterior
        assert door_type.glazed is glazed


# --- plan symbols -----------------------------------------------------------------


# A 2x6 stud wall with 1/2" board each side — the catlin interior partition depth.
TEST_WALL_THICKNESS_IN = 6.5


def _symbol(name: str, width_in: float, height_in: float = 84.0, swing_sign: float = 1.0,
            rotation: float = 0.0, hinge_jamb_sign: float = 1.0) -> Symbol:
    return Symbol(name=name, insert=(0.0, 0.0), rotation=rotation, scale=width_in,
                  layer="A-DOOR",
                  params=door_symbol_params(
                      name, width_in, height_in, swing_sign,
                      hinge_jamb_sign=hinge_jamb_sign,
                      host_wall_thickness_in=TEST_WALL_THICKNESS_IN))


def _along(rotation_deg: float, distance_in: float) -> tuple[float, float]:
    """A point ``distance_in`` down the wall from the symbol insert (which is the origin)."""
    angle = math.radians(rotation_deg)
    return (math.cos(angle) * distance_in, math.sin(angle) * distance_in)


def _arc_point(arc: SymbolArc, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return (arc.center[0] + arc.radius * math.cos(angle),
            arc.center[1] + arc.radius * math.sin(angle))


def _arc_sweep_deg(arc: SymbolArc) -> float:
    """How far the writers travel: both draw counter-clockwise from start to end."""
    return (arc.end_angle_deg - arc.start_angle_deg) % 360.0


def _endpoints(arc: SymbolArc) -> tuple[tuple[float, float], tuple[float, float]]:
    return _arc_point(arc, arc.start_angle_deg), _arc_point(arc, arc.end_angle_deg)


def _matches(point, candidates) -> bool:
    return any(_distance(point, candidate) < 1e-6 for candidate in candidates)


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


def test_sliding_symbol_bypasses_the_wall_toward_the_park_jamb():
    width_in = 60.0
    geometry = door_symbol_geometry(_symbol(DOOR_SLIDING, width_in))
    assert not geometry.arcs, "a slider rides a track, it does not swing"
    panel, parked, strike_tick, stop_tick = geometry.strokes
    assert not panel.dashed
    assert parked.dashed and strike_tick.dashed and stop_tick.dashed, \
        "the parked panel lies behind the wall it slides over"
    assert _distance(*panel.points) == pytest.approx(width_in)
    assert _distance(*parked.points) == pytest.approx(width_in), \
        "the panel is its own travel: it parks one leaf width past the jamb"
    standoff = TEST_WALL_THICKNESS_IN / 2 + SLIDING_PANEL_CLEARANCE_IN
    assert all(point[1] == pytest.approx(standoff) for point in panel.points), \
        "the panel rides clear of the wall face, not inside the wall depth"
    # Travel is handed, and stays on the handed operating side of the wall.
    points = [point for stroke in geometry.strokes for point in stroke.points]
    assert max(point[0] for point in points) == pytest.approx(width_in / 2 + width_in)
    assert min(point[0] for point in points) == pytest.approx(-width_in / 2)
    assert all(0.0 <= point[1] <= standoff + 1e-9 for point in points)


def test_sliding_symbol_travel_mirrors_with_the_authored_handing():
    width_in = 60.0
    flipped = door_symbol_geometry(_symbol(DOOR_SLIDING, width_in, hinge_jamb_sign=-1.0))
    points = [point for stroke in flipped.strokes for point in stroke.points]
    assert min(point[0] for point in points) == pytest.approx(-(width_in / 2 + width_in))
    assert max(point[0] for point in points) == pytest.approx(width_in / 2)


def test_pocket_symbol_recedes_into_the_wall_without_standing_off_it():
    width_in = 60.0
    geometry = door_symbol_geometry(_symbol(DOOR_POCKET, width_in))
    assert not geometry.arcs, "a pocket panel slides into the wall, it does not swing"
    panel, concealed, stop = geometry.strokes
    assert not panel.dashed
    assert concealed.dashed and stop.dashed, "everything inside the pocket is concealed"
    assert _distance(*panel.points) == pytest.approx(width_in)
    assert _distance(*concealed.points) == pytest.approx(width_in)
    # On the wall axis, not offset from it — that is what separates it from the slider.
    assert all(point[1] == pytest.approx(0.0)
               for point in panel.points + concealed.points)
    pocket_end = width_in / 2 + width_in
    assert all(point[0] == pytest.approx(pocket_end) for point in stop.points)
    assert _distance(*stop.points) == pytest.approx(TEST_WALL_THICKNESS_IN), \
        "the stop spans the wall the panel hides in — it is the stud closing the cavity"


def test_every_door_operation_draws_its_own_plan_symbol():
    """A shared glyph is a silent lie in plan — sliding and pocket both drew as swings."""
    by_operation = {operation: symbol_name_for_operation(operation)
                    for operation in DoorOperation}
    assert by_operation[DoorOperation.SWING] == DOOR_SWING
    assert len(set(by_operation.values())) == len(DoorOperation)


# --- swing arc handedness ---------------------------------------------------------


@pytest.mark.parametrize("rotation", [0.0, 37.0, 90.0, 180.0, 285.0])
@pytest.mark.parametrize("swing_sign", [1.0, -1.0])
@pytest.mark.parametrize("hinge_jamb_sign", [1.0, -1.0])
def test_single_swing_arc_stays_concave_toward_its_hinge(rotation, swing_sign,
                                                         hinge_jamb_sign):
    """The arc spans shut leaf → open leaf for every handing, never the complement.

    Sweeping a fixed quadrant drew the arc over the wall *beside* the door for every leaf
    hinged the other way, which is what read as a convex swing.
    """
    width_in = 36.0
    geometry = door_symbol_geometry(_symbol(DOOR_SWING, width_in, swing_sign=swing_sign,
                                            rotation=rotation,
                                            hinge_jamb_sign=hinge_jamb_sign))
    (leaf,) = geometry.strokes
    (arc,) = geometry.arcs
    assert arc.center == (0.0, 0.0) and arc.radius == pytest.approx(width_in)
    assert _arc_sweep_deg(arc) == pytest.approx(90.0)
    shut_tip = _along(rotation, -hinge_jamb_sign * width_in)
    open_tip = leaf.points[1]
    ends = _endpoints(arc)
    assert _matches(shut_tip, ends) and _matches(open_tip, ends)
    # Concavity: mid-sweep sits in the quadrant the leaf actually crosses — same side of
    # the wall as the open leaf, same side of the hinge as the shut one.
    mid = _arc_point(arc, arc.start_angle_deg + 45.0)
    assert _dot(mid, open_tip) > 0.0 and _dot(mid, shut_tip) > 0.0


@pytest.mark.parametrize("rotation", [0.0, 37.0, 180.0])
@pytest.mark.parametrize("swing_sign", [1.0, -1.0])
def test_double_swing_leaves_are_mirror_images(rotation, swing_sign):
    """A French pair is symmetric about the mullion — not one concave leaf beside one convex."""
    width_in = 72.0
    half = width_in / 2.0
    geometry = door_symbol_geometry(_symbol(DOOR_SWING_DOUBLE, width_in,
                                            swing_sign=swing_sign, rotation=rotation))
    assert len(geometry.strokes) == 2 and len(geometry.arcs) == 2
    mullion = (0.0, 0.0)
    for arc, jamb_sign in zip(geometry.arcs, (-1.0, 1.0)):
        assert arc.center == pytest.approx(_along(rotation, jamb_sign * half))
        assert arc.radius == pytest.approx(half)
        assert _arc_sweep_deg(arc) == pytest.approx(90.0)
        assert _matches(mullion, _endpoints(arc)), "each leaf shuts against the mullion"
    # Sampling one arc forward and the other backward walks the pair from the mullion
    # outward together, so a mismatch means the leaves are not each other's reflection.
    left, right = geometry.arcs
    for step in range(11):
        left_point = _arc_point(left, left.start_angle_deg + step * 9.0)
        right_point = _arc_point(right, right.end_angle_deg - step * 9.0)
        assert _mirror_across_the_opening_centre(left_point, rotation) \
            == pytest.approx(right_point)


def _distance(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _mirror_across_the_opening_centre(point, rotation_deg: float):
    """Reflect a point in the line through the opening centre, normal to the wall."""
    angle = math.radians(rotation_deg)
    along = (math.cos(angle), math.sin(angle))
    across = (-math.sin(angle), math.cos(angle))
    u, v = _dot(point, along), _dot(point, across)
    return (-u * along[0] + v * across[0], -u * along[1] + v * across[1])


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
    """O-S-CLOSET is the house's only bifold since D-M-LAUN became a pocket (2026-08-21).

    It lives on ``second``; this test read ``main`` while D-M-LAUN was the bifold there.
    Retyping that door emptied the main storey of bifolds, so the storey moved rather than
    the assertion being dropped — the BIFOLD symbol still has to be exercised.
    """
    names = {node.name for node in build_floorplan(catlin_model, "second").nodes
             if isinstance(node, Symbol)}
    assert DOOR_BIFOLD in names


def test_catlin_laundry_door_emits_the_pocket_symbol(catlin_model):
    """D-M-LAUN is the house's (and the repo's) first authored pocket door."""
    laundry = next(op for op in catlin_model.openings if op.tag == "D-M-LAUN")
    symbols = {node.uid: node for node in build_floorplan(catlin_model, "main").nodes
               if isinstance(node, Symbol)}
    assert symbols[laundry.uid].name == DOOR_POCKET
    # A pocket sweeps nothing: no arc, and no swing clearance ring to conflict with the
    # appliances 8-3/4" in front of it — which is the whole reason for the retype.
    assert not door_symbol_geometry(symbols[laundry.uid]).arcs
    assert not laundry.swing_clearance


def test_synthetic_slide_door_emits_the_sliding_symbol():
    """No SLIDE-operation door is instantiated in the catlin model any more — the balcony
    door D-M-BALC was retyped from slide to french, its intended replacement. The catalog
    entry DT-EXT-SLIDE60 is orphaned (no opening references it) but is deliberately kept in
    the catalog, so the SLIDE operation itself must still be exercised synthetically here
    rather than dropped: a slider must not draw a swing arc into the room.
    """
    width_in = 60.0
    assert symbol_name_for_operation(DoorOperation.SLIDE) == DOOR_SLIDING
    geometry = door_symbol_geometry(_symbol(DOOR_SLIDING, width_in))
    assert not geometry.arcs
    assert len(geometry.strokes) == 4


@pytest.mark.parametrize("storey", ["garage", "main"])
def test_new_symbols_survive_both_writers(catlin_model, tmp_path, storey):
    """Garage carries the sectional; main carries the bifolds and the alarms."""
    scene = build_floorplan(catlin_model, storey)
    assert write_dxf(scene, tmp_path / f"{storey}.dxf").exists()
    assert write_raster(scene, tmp_path / f"{storey}.png").exists()


# --- writer coverage of the plan symbol vocabulary --------------------------------

# Both writers fall back to the window-glass bar for a name they do not recognise, so the
# fallback is only correct for the window mark itself. Every other emitted name must have
# a glyph of its own — a smoke alarm drew as glazing for exactly this reason.
WINDOW_MARK_SYMBOL = "window-mark"


def test_every_floorplan_symbol_is_drawn_by_both_writers(catlin_model):
    from typehaus.emit.draw.dxf_writer import SYMBOL_NAMES_WITH_DEDICATED_GLYPH as DXF_GLYPHS
    from typehaus.emit.draw.pdf_writer import SYMBOL_NAMES_WITH_DEDICATED_GLYPH as PDF_GLYPHS

    emitted = {node.name
               for storey in catlin_model.plan.storeys
               for node in build_floorplan(catlin_model, storey.tag).nodes
               if isinstance(node, Symbol)}
    assert emitted, "the catlin plans draw symbols"
    assert emitted - PDF_GLYPHS == {WINDOW_MARK_SYMBOL}, "unstyled names draw as glazing (PDF)"
    assert emitted - DXF_GLYPHS == {WINDOW_MARK_SYMBOL}, "unstyled names draw as glazing (DXF)"


def test_the_alarm_marker_is_styled_rather_than_drawn_as_a_window(catlin_model):
    from typehaus.emit.draw.dxf_writer import _DEVICE_SYMBOLS
    from typehaus.emit.draw.pdf_writer import _MARKER_STYLE

    alarms = [node for storey in catlin_model.plan.storeys
              for node in build_floorplan(catlin_model, storey.tag).nodes
              if isinstance(node, Symbol) and node.name == "alarm"]
    assert alarms, "the catlin plan places smoke/CO alarms"
    assert "alarm" in _MARKER_STYLE and "alarm" in _DEVICE_SYMBOLS
    marker, color = _MARKER_STYLE["alarm"]
    assert marker and color != "#3a6a8a", "the glazing blue was the symptom of the bug"


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


def _pocket_members(width=ft(4), *, flip=False, wall_len=6.0):
    """A 4'-0" pocket in a 20' wall, pocketing toward the end node unless ``flip``."""
    plan, wall = _wall_and_plan()
    wall = replace(wall, axis=((0.0, 0.0), (wall_len, 0.0)))
    sign = -1 if flip else 1
    center = 0.1016 + width.meters / 2 if not flip else wall_len - 0.1016 - width.meters / 2
    opening = WallOpening(center_m=center, width_m=width.meters, height_m=ft(6, 8).meters,
                          sill_m=0.0, is_door=True, operation=DoorOperation.POCKET,
                          pocket_run_m=pocket_run(width).meters, pocket_sign=sign)
    return frame_wall(plan, wall, openings=[opening]), opening


def test_pocket_rough_opening_is_the_published_two_w_plus_one():
    """Every frame kit sizes the RO at 2W + 1"; ``pocket_run`` is the second half of it."""
    assert (ft(4) + pocket_run(ft(4))).inches == pytest.approx(97.0)
    assert (ft(3) + pocket_run(ft(3))).inches == pytest.approx(73.0)
    assert (ft(2, 6) + pocket_run(ft(2, 6))).inches == pytest.approx(61.0)


def test_pocket_leaves_the_mouth_open_and_moves_the_jamb_pack_to_the_closed_end():
    members, opening = _pocket_members()
    mouth = opening.center_m + opening.width_m / 2
    closed = mouth + opening.pocket_run_m
    stations = sorted(m.p0[0] for m in members
                      if m.category in ("king", "jack") and m.p0 == m.p1)
    # Nothing stands at the mouth: that edge is the split jamb the leaf passes through,
    # and a trimmer there is a door that will not open.
    assert not [s for s in stations if abs(s - mouth) < inch(3).meters]
    # Both packs are present, one at the strike jamb and one closing the cavity.
    strike = opening.center_m - opening.width_m / 2
    assert min(stations) < strike + inch(3).meters
    assert max(stations) > closed - inch(0.1).meters


def test_pocket_header_spans_the_opening_and_the_cavity_together():
    members, opening = _pocket_members()
    header = next(m for m in members if m.category == "header")
    # RO + pocket, plus the one jack each end the header bears on: 48 + 49 + 1.5 + 1.5.
    assert header.length_m == pytest.approx(inch(100.0).meters)
    # A pocket hangs from the kit's own head track inside a partition, so the head is a
    # nailer and a track backing — never a bearing header, however wide the span gets.
    assert header.profile == "2-2x6"
    backing = [m for m in members if m.child_key.startswith("trackbacking-")]
    assert len(backing) == 1 and backing[0].z0_m == pytest.approx(header.z1_m)
    # ...and none of the overhead sectional's vertical track framing.
    assert not [m for m in members if m.child_key.startswith("trackjamb-")]


def test_pocket_split_studs_stop_at_the_header_so_the_plates_stay_continuous():
    """This is what lets a partition tee into a wall over a pocket.

    The cavity exists only below the head, so the wall's double top plate runs unbroken
    above it and its bottom plate below. A branch wall ties to both, plate to plate, and
    only its vertical edge floats against the split jamb.
    """
    members, opening = _pocket_members()
    splits = [m for m in members if m.child_key.startswith("pocketsplit-")]
    header = next(m for m in members if m.category == "header")
    assert splits, "a pocket must frame its cavity"
    assert all(m.profile == "2-1x4" for m in splits)
    assert all(m.z1_m == pytest.approx(header.z0_m) for m in splits)
    assert all(m.z0_m == pytest.approx(min(s.z0_m for s in splits)) for m in splits)
    # 12" o.c. from the mouth, and never inside the pack that closes the cavity.
    mouth = opening.center_m + opening.width_m / 2
    offsets = sorted(m.p0[0] - mouth for m in splits)
    assert offsets == pytest.approx([inch(12).meters, inch(24).meters, inch(36).meters])


def test_pocket_frames_no_two_members_on_one_station():
    """The closed end is the relocated jamb pack, not a pack *and* a separate end post."""
    members, _ = _pocket_members()
    stations = [round(m.p0[0], 6) for m in members if m.p0 == m.p1]
    assert len(stations) == len(set(stations))


def test_pocket_can_run_either_way_along_the_wall():
    forward, op_f = _pocket_members()
    reverse, op_r = _pocket_members(flip=True)
    f_splits = sorted(m.p0[0] for m in forward if m.child_key.startswith("pocketsplit-"))
    r_splits = sorted(m.p0[0] for m in reverse if m.child_key.startswith("pocketsplit-"))
    assert len(f_splits) == len(r_splits)
    # flip_hinge picks the side: forward pockets past the opening, reverse before it.
    assert min(f_splits) > op_f.center_m
    assert max(r_splits) < op_r.center_m


def test_a_swing_door_is_untouched_by_the_pocket_path():
    """The pocket branch must be inert for every other operation."""
    plan, wall = _wall_and_plan()
    opening = WallOpening(center_m=4.0, width_m=ft(2, 6).meters, height_m=ft(6, 8).meters,
                          sill_m=0.0, is_door=True, operation=DoorOperation.SWING)
    members = frame_wall(plan, wall, openings=[opening])
    header = next(m for m in members if m.category == "header")
    assert header.length_m == pytest.approx(inch(33.0).meters)  # 30 RO + two jacks
    assert not [m for m in members if "pocket" in m.child_key]


# --- the cavity crossing a node ---------------------------------------------------


def _colinear_plan(*, second_assembly="INT", second_len=1.4224, angled=False):
    """Two walls meeting end-to-start at a node: 64" then 56", the catlin laundry band."""
    from typehaus.model.elements import Wall

    a = Wall(uid="WA", tag="W-A", start_node="N0", end_node="N1", assembly="INT")
    b = Wall(uid="WB", tag="W-B", start_node="N1", end_node="N2", assembly=second_assembly)
    end = (1.6256, second_len) if angled else (1.6256 + second_len, 0.0)
    resolved = {
        "W-A": SimpleNamespace(tag="W-A", axis=((0.0, 0.0), (1.6256, 0.0))),
        "W-B": SimpleNamespace(tag="W-B", axis=((1.6256, 0.0), end)),
    }
    plan = SimpleNamespace(all_elements=lambda: [a, b])
    model = SimpleNamespace(wall=resolved.get)
    return plan, model


def _pocket_opening(width=ft(4)):
    return SimpleNamespace(
        tag="D-TEST", host_wall="W-A",
        center_along_m=inch(4).meters + width.meters / 2, width_m=width.meters,
        pocket_run_m=pocket_run(width).meters, pocket_sign=1)


def test_a_pocket_may_run_across_a_node_into_a_colinear_wall():
    """Wall segmentation at a tee is an authoring convention, not a wall.

    ``classify_storey_junctions`` builds junctions from wall *endpoints*, so a partition
    teeing in has to split the wall it lands on. The two halves are still one plane, one
    assembly and one pair of plates, and the leaf really does travel across the node.
    """
    plan, model = _colinear_plan()
    segments, shortfall = pocket_segments(plan, model, _pocket_opening())
    assert shortfall == pytest.approx(0.0), "a 49\" cavity fits 64\" + 56\" of wall"
    assert [segment.wall_tag for segment in segments] == ["W-A", "W-B"]
    # The mouth is 52" along W-A, which is 64" long, so 12" lands there and the rest next
    # door — the run is contiguous across the node, with no gap and no overlap.
    assert segments[0].high_m == pytest.approx(1.6256)
    assert segments[1].low_m == pytest.approx(0.0)


def test_a_pocket_is_refused_when_the_colinear_run_is_too_short():
    plan, model = _colinear_plan(second_len=inch(6).meters)
    _segments, shortfall = pocket_segments(plan, model, _pocket_opening())
    assert shortfall > 0.0, "a leaf with nowhere to go must be reported, not drawn"


def test_a_pocket_stops_at_a_corner_and_at_an_assembly_change():
    """Neither a turn nor a different assembly continues the run.

    A leaf cannot slide round a corner, and a different assembly is a different wall in
    every way that matters — a thickness change, a different stud depth, often a different
    trade — so the cavity must not be allowed to open into one.
    """
    for kwargs in ({"angled": True}, {"second_assembly": "EXT_2X6"}):
        plan, model = _colinear_plan(**kwargs)
        segments, shortfall = pocket_segments(plan, model, _pocket_opening())
        assert shortfall > 0.0, f"the run must stop: {kwargs}"
        assert [segment.wall_tag for segment in segments] == ["W-A"]

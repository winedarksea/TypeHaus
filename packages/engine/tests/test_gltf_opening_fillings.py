"""The .glb's door/window products, against the live viewer's ``Panel3D.tsx:buildOpening``.

The static export and the interactive viewer are a mirrored pair (see the constants block above
``_add_opening_filling``): both draw a four-piece frame plus either a full-width door panel, a
glass pane, or two swing leaves split at a center mullion. These tests read the finished glTF
back — positions out of the binary blob, one solid per connected triangle group — so they fail
if the export ever regresses to bare void rectangles again.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import NamedTuple

import pytest

from typehaus.emit.gltf import emit_gltf_dict
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.openings import (
    _DOOR_LEAF_THICKNESS_M,
    _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR,
    _OPENING_FRAME_DEPTH_M,
    _OPENING_FRAME_FACE_WIDTH_M,
    _OPENING_FRAME_SPAN_DIVISOR,
    _WINDOW_GLAZING_THICKNESS_M,
    _WINDOW_TRIM_PROUD_DEPTH_M,
    _add_opening_filling,
)
from typehaus.model.enums import DoorOperation
from typehaus.resolve import resolve
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall
from typehaus.source import load_plan

# Positions round-trip through float32, so ~1e-6 m of noise on a 10 m coordinate is expected.
# Weld vertices at 10 µm (well above the noise, far below any real product dimension) and
# compare dimensions at 0.1 mm.
_VERTEX_WELD_PLACES = 5
_DIMENSION_TOLERANCE_M = 1e-4

# Panel3D and the emitter both build a frame of exactly four pieces: two jambs, head, sill.
_FRAME_PIECE_COUNT = 4
# A window in a *clad* wall also ships a four-board exterior casing on the cladding plane
# (two jamb boards, head, apron) — the ``exterior_trim`` part in resolve/geometry_openings.py.
# Doors never do, and neither does a window in an unclad host (concrete, interior).
_TRIM_PIECE_COUNT = 4
# One box = 4 side quads + 2 caps = 12 triangles, de-indexed to 3 vertices each.
_VERTICES_PER_BOX = 36


# --- reading solids back out of the finished glTF --------------------------------------

class _Solid(NamedTuple):
    """One connected box out of a node's mesh, measured in glTF axes (x east, y up, z south)."""

    plan_dimensions_m: tuple[float, float]  # the horizontal footprint's two side lengths, sorted
    height_m: float
    center: tuple[float, float, float]
    material_index: int

    def has_thickness(self, thickness_m: float) -> bool:
        return any(abs(side - thickness_m) < _DIMENSION_TOLERANCE_M
                   for side in self.plan_dimensions_m)


def _read_vec3_accessor(gltf: dict, blob: bytes, accessor_index: int) -> list[tuple[float, ...]]:
    accessor = gltf["accessors"][accessor_index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    start = view["byteOffset"]
    values = struct.unpack_from(f"<{accessor['count'] * 3}f", blob, start)
    return [tuple(values[i:i + 3]) for i in range(0, len(values), 3)]


def _vertex_key(vertex: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(round(component, _VERTEX_WELD_PLACES) for component in vertex)


def _box_vertex_chunks(positions: list[tuple[float, ...]]) -> list[list[tuple[float, ...]]]:
    """Split a de-indexed triangle soup into one chunk per emitted box.

    Vertex-adjacency clustering cannot separate the pieces — a jamb and the sill under it share
    corners exactly — but every product piece is one ``add_prism`` call over a four-sided ring,
    which is a fixed 12 triangles (4 side quads + 2 triangulated caps) of 3 vertices each,
    written contiguously. The 8-distinct-corners assertion below fails loudly if that ever stops
    holding (e.g. a degenerate face gets dropped and shifts the chunking).
    """
    assert len(positions) % _VERTICES_PER_BOX == 0, (
        f"{len(positions)} vertices is not a whole number of 12-triangle boxes")
    return [positions[start:start + _VERTICES_PER_BOX]
            for start in range(0, len(positions), _VERTICES_PER_BOX)]


def _measure_box(corners: list[tuple[float, ...]]) -> tuple[tuple[float, float], float,
                                                            tuple[float, float, float]]:
    """A vertical rectangular prism's footprint side lengths, height and center.

    The footprint sides are read as the two nearest neighbours of one bottom corner — for a
    rectangle the remaining corner is always the (longer) diagonal — so the measurement holds
    for a wall running at any bearing, not only the axis-aligned ones.
    """
    heights = [corner[1] for corner in corners]
    bottom = min(heights)
    footprint = sorted({(round(c[0], _VERTEX_WELD_PLACES), round(c[2], _VERTEX_WELD_PLACES))
                        for c in corners if abs(c[1] - bottom) < _DIMENSION_TOLERANCE_M})
    assert len(footprint) == 4, f"expected a rectangular footprint, got {footprint}"
    origin, *others = footprint
    spans = sorted(math.dist(origin, other) for other in others)
    center = tuple(sum(c[axis] for c in corners) / len(corners) for axis in range(3))
    return (spans[0], spans[1]), max(heights) - bottom, center  # type: ignore[return-value]


def _solids_of_node(gltf: dict, blob: bytes, node: dict) -> list[_Solid]:
    solids: list[_Solid] = []
    for primitive in gltf["meshes"][node["mesh"]]["primitives"]:
        positions = _read_vec3_accessor(gltf, blob, primitive["attributes"]["POSITION"])
        for chunk in _box_vertex_chunks(positions):
            corners = sorted({_vertex_key(vertex) for vertex in chunk})
            assert len(corners) == 8, f"a product piece must be a closed box, got {corners}"
            plan_dimensions, height, center = _measure_box(corners)
            solids.append(_Solid(plan_dimensions, height, center, primitive["material"]))
    return solids


def _opening_node(gltf: dict, uid: str) -> dict:
    node = next((n for n in gltf["nodes"] if n["extras"].get("uid") == uid
                 and n["extras"]["trade"] == "openings"), None)
    assert node is not None, f"opening {uid} shipped no geometry at all"
    return node


def _opening_center_plan_point(wall, opening) -> tuple[float, float]:
    """The opening's center station, in the glTF horizontal axes (model x, -model y)."""
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    along_x, along_y = (x1 - x0) / length, (y1 - y0) / length
    return (x0 + along_x * opening.center_along_m, -(y0 + along_y * opening.center_along_m))


def _frame_width_m(opening, available_height_m: float) -> float:
    return min(_OPENING_FRAME_FACE_WIDTH_M,
               opening.width_m / _OPENING_FRAME_SPAN_DIVISOR,
               available_height_m / _OPENING_FRAME_SPAN_DIVISOR)


# --- fixtures --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, _findings = resolve(result.plan)
    return model


def _first_opening(model, kind: str):
    opening = next((op for op in model.openings if op.kind == kind), None)
    assert opening is not None, f"fixture regression: the plan lost every {kind}"
    return opening


def _host_wall(model, opening):
    return next(wall for wall in model.walls if wall.tag == opening.host_wall)


# --- window / single-operation door ------------------------------------------------------

def test_a_window_ships_a_four_piece_frame_and_one_glass_pane(starter_model):
    opening = _first_opening(starter_model, "window")
    wall = _host_wall(starter_model, opening)
    gltf, blob = emit_gltf_dict(starter_model)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, opening.uid))

    panes = [s for s in solids if s.has_thickness(_WINDOW_GLAZING_THICKNESS_M)]
    trim = [s for s in solids if s.has_thickness(_WINDOW_TRIM_PROUD_DEPTH_M)]
    # A clad-wall frame extends from its interior face to the casing's proud face, so its
    # thickness is per-wall rather than the fixed _OPENING_FRAME_DEPTH_M — identify the
    # frame as everything that is neither glazing nor a casing board.
    frame = [s for s in solids if s not in panes and s not in trim]
    assert len(solids) == _FRAME_PIECE_COUNT + _TRIM_PIECE_COUNT + 1, (
        "a window in a clad wall is four frame pieces, four casing boards and glazing")
    assert len(panes) == 1 and len(frame) == _FRAME_PIECE_COUNT
    assert len(trim) == _TRIM_PIECE_COUNT, "the exterior casing is a four-board picture frame"
    # Glazing is the export's only translucent material — the viewer draws it at 48% opacity.
    assert gltf["materials"][panes[0].material_index]["pbrMetallicRoughness"][
        "baseColorFactor"][3] == pytest.approx(0.48)
    assert gltf["materials"][frame[0].material_index]["alphaMode"] == "OPAQUE"

    available_height = min(opening.height_m, wall.z1_m - wall.z0_m - opening.sill_m)
    frame_width = _frame_width_m(opening, available_height)
    jambs = [s for s in frame if s.height_m == pytest.approx(available_height, abs=_DIMENSION_TOLERANCE_M)]
    heads = [s for s in frame if s.height_m == pytest.approx(frame_width, abs=_DIMENSION_TOLERANCE_M)]
    assert len(jambs) == 2, "two full-height jambs"
    assert len(heads) == 2, "a head and a sill, each one frame-width tall"
    for head in heads:
        assert head.plan_dimensions_m[1] == pytest.approx(opening.width_m, abs=_DIMENSION_TOLERANCE_M)
    assert panes[0].plan_dimensions_m[1] == pytest.approx(
        opening.width_m - 2 * frame_width, abs=_DIMENSION_TOLERANCE_M)


def test_a_single_operation_door_ships_one_full_width_panel(starter_model):
    opening = _first_opening(starter_model, "door")
    wall = _host_wall(starter_model, opening)
    gltf, blob = emit_gltf_dict(starter_model)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, opening.uid))

    panels = [s for s in solids if s.has_thickness(_DOOR_LEAF_THICKNESS_M)]
    assert len(solids) == _FRAME_PIECE_COUNT + 1, "a plain door is four frame pieces plus a panel"
    assert len(panels) == 1, "a single-operation door is one leaf, not two"
    available_height = min(opening.height_m, wall.z1_m - wall.z0_m - opening.sill_m)
    frame_width = _frame_width_m(opening, available_height)
    assert panels[0].plan_dimensions_m[1] == pytest.approx(
        opening.width_m - 2 * frame_width, abs=_DIMENSION_TOLERANCE_M)
    assert panels[0].height_m == pytest.approx(available_height - 2 * frame_width,
                                               abs=_DIMENSION_TOLERANCE_M)
    # No glazing material anywhere in a door node.
    assert all(gltf["materials"][s.material_index]["alphaMode"] == "OPAQUE" for s in solids)


def test_catlin_plant_room_door_ships_translucent_glazing(catlin_model):
    opening = next(op for op in catlin_model.openings if op.tag == "D-S-PLANT")
    door_type = next(dt for dt in catlin_model.plan.library.door_types
                     if dt.tag == opening.type_ref)
    assert door_type.glazed
    gltf, blob = emit_gltf_dict(catlin_model)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, opening.uid))

    panes = [solid for solid in solids if solid.has_thickness(_WINDOW_GLAZING_THICKNESS_M)]
    assert len(panes) == 1
    assert gltf["materials"][panes[0].material_index]["pbrMetallicRoughness"][
        "baseColorFactor"][3] == pytest.approx(0.48)


# --- trimless door -----------------------------------------------------------------------

def test_catlin_trimless_bedroom_door_ships_a_leaf_and_no_frame(catlin_model):
    """DT-INT30-TRIMLESS (drywall return jamb) is the one door the four-frame-piece rule
    deliberately does not apply to: the export ships only the leaf."""
    opening = next(op for op in catlin_model.openings if op.tag == "D-M-BED2")
    door_type = next(dt for dt in catlin_model.plan.library.door_types
                     if dt.tag == opening.type_ref)
    assert door_type.trimless
    wall = _host_wall(catlin_model, opening)
    gltf, blob = emit_gltf_dict(catlin_model)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, opening.uid))

    assert len(solids) == 1, "a trimless door is a bare leaf — no jambs, head, or sill"
    leaf = solids[0]
    assert leaf.has_thickness(_DOOR_LEAF_THICKNESS_M)
    # The leaf keeps its framed size so the drywall reveal reads the same as a cased door.
    available_height = min(opening.height_m, wall.z1_m - wall.z0_m - opening.sill_m)
    frame_width = _frame_width_m(opening, available_height)
    assert leaf.plan_dimensions_m[1] == pytest.approx(
        opening.width_m - 2 * frame_width, abs=_DIMENSION_TOLERANCE_M)
    assert gltf["materials"][leaf.material_index]["alphaMode"] == "OPAQUE"


# --- French / double-swing door ----------------------------------------------------------

@pytest.mark.parametrize("glazed", [True, False])
def test_a_double_swing_door_ships_two_leaves_split_by_a_center_mullion(catlin_model, glazed):
    # Catlin hangs both kinds of pair: the glazed DT-EXT-FRENCH60 exterior doors, and
    # D-B-PLAY's opaque solid-core DT-INT-DOUBLE60. Only the leaf material differs — the
    # frame, the mullion and the two-leaf split are the operation's, not the glazing's.
    double_swing_types = {door_type.tag for door_type in catlin_model.plan.library.door_types
                          if door_type.operation == "double_swing"
                          and door_type.glazed is glazed}
    assert double_swing_types, "fixture regression: catlin lost a double-swing door type"
    opening = next((op for op in catlin_model.openings if op.type_ref in double_swing_types), None)
    assert opening is not None, "fixture regression: catlin lost its French doors"
    wall = _host_wall(catlin_model, opening)
    gltf, blob = emit_gltf_dict(catlin_model)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, opening.uid))

    available_height = min(opening.height_m, wall.z1_m - wall.z0_m - opening.sill_m)
    frame_width = _frame_width_m(opening, available_height)
    clear_width = opening.width_m - 2 * frame_width
    mullion_width = min(frame_width, clear_width / _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR)
    leaf_width = (clear_width - mullion_width) / 2

    leaf_thickness = _WINDOW_GLAZING_THICKNESS_M if glazed else _DOOR_LEAF_THICKNESS_M
    leaves = [s for s in solids if s.has_thickness(leaf_thickness)]
    full_height = [s for s in solids
                   if s.height_m == pytest.approx(available_height, abs=_DIMENSION_TOLERANCE_M)]
    assert len(solids) == _FRAME_PIECE_COUNT + 3, "four frame pieces, a mullion and two leaves"
    assert len(leaves) == 2, "a double_swing door is two leaves"
    for leaf in leaves:
        assert (gltf["materials"][leaf.material_index]["alphaMode"]
                == ("BLEND" if glazed else "OPAQUE"))
        assert leaf.plan_dimensions_m[1] == pytest.approx(leaf_width, abs=_DIMENSION_TOLERANCE_M)
        assert leaf.height_m == pytest.approx(available_height - 2 * frame_width,
                                              abs=_DIMENSION_TOLERANCE_M)

    # The mullion is the full-height piece standing on the opening's center station — the jambs
    # are the same height and can be the same face width, so position is what tells them apart.
    center_x, center_z = _opening_center_plan_point(wall, opening)
    mullions = [s for s in full_height
                if s.has_thickness(_OPENING_FRAME_DEPTH_M)
                and s.has_thickness(mullion_width)
                and math.dist((s.center[0], s.center[2]), (center_x, center_z))
                < _DIMENSION_TOLERANCE_M]
    assert len(mullions) == 1, "exactly one center mullion, on the opening's center station"
    mullion_center = mullions[0].center
    leaf_midpoint = tuple(sum(leaf.center[axis] for leaf in leaves) / 2 for axis in range(3))
    for axis in range(3):
        assert leaf_midpoint[axis] == pytest.approx(mullion_center[axis],
                                                    abs=_DIMENSION_TOLERANCE_M), (
            "the two leaves must sit symmetrically either side of the mullion")


def test_the_balcony_door_ships_the_french_door_solid_shape(catlin_model):
    """D-M-BALC was retyped from a slider to a French pair (DT-EXT-FRENCH60) — a locked
    design decision (the door stays a french door), not a bug — so it now ships the same
    double-swing shape as any other French door: four frame pieces, a center mullion, and
    two leaves (see ``test_a_double_swing_door_ships_two_leaves_split_by_a_center_mullion``
    for the same math against the exterior French door).
    """
    gltf, blob = emit_gltf_dict(catlin_model)
    balcony = next(op for op in catlin_model.openings if op.tag == "D-M-BALC")
    wall = _host_wall(catlin_model, balcony)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, balcony.uid))

    available_height = min(balcony.height_m, wall.z1_m - wall.z0_m - balcony.sill_m)
    frame_width = _frame_width_m(balcony, available_height)
    clear_width = balcony.width_m - 2 * frame_width
    mullion_width = min(frame_width, clear_width / _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR)
    leaf_width = (clear_width - mullion_width) / 2

    assert len(solids) == _FRAME_PIECE_COUNT + 3, "four frame pieces, a mullion and two leaves"
    balcony_leaves = [solid for solid in solids
                      if solid.has_thickness(_WINDOW_GLAZING_THICKNESS_M)]
    assert len(balcony_leaves) == 2, "the balcony french door is two glazed leaves"
    for leaf in balcony_leaves:
        assert leaf.plan_dimensions_m[1] == pytest.approx(leaf_width, abs=_DIMENSION_TOLERANCE_M)
    assert all(gltf["materials"][leaf.material_index]["alphaMode"] == "BLEND"
               for leaf in balcony_leaves)


def test_the_laundry_pocket_ships_one_leaf_on_a_head_track(catlin_model):
    """D-M-LAUN is a pocket door.

    A pocket is drawn closed and coplanar on the same principle the slider below uses: the
    wall over the cavity is drywalled on both faces and genuinely reads solid, so the leaf
    fills its opening rather than being staged inside the wall. The cavity is modelled, but
    as framing — the ``pocketsplit-*`` members and the jamb pack relocated to its closed
    end. What separates it from a swing leaf here is the head track: a pocket has no floor
    track, so unlike the slider the rail sits at the top of the opening.
    """
    pocket = next(op for op in catlin_model.openings if op.tag == "D-M-LAUN")
    assert pocket.type_ref == "DT-POCKET-INT-48"
    door_type = next(dt for dt in catlin_model.plan.library.door_types
                     if dt.tag == "DT-POCKET-INT-48")
    assert door_type.width.inches == pytest.approx(48.0)

    gltf, blob = emit_gltf_dict(catlin_model)
    solids = _solids_of_node(gltf, blob, _opening_node(gltf, pocket.uid))
    leaves = [solid for solid in solids if solid.has_thickness(_DOOR_LEAF_THICKNESS_M)]
    assert len(solids) == _FRAME_PIECE_COUNT + 2  # one leaf, one track
    assert len(leaves) == 1, "a closed pocket door is a single coplanar leaf"


def test_a_synthetic_slider_ships_a_stile_track_and_two_panels():
    """A synthetic opening, since D-M-BALC is a French door: a closed slider stays
    coplanar, with two glazed panels meeting at a narrow stile over a low track.
    """
    parts = opening_parts(_synthetic_wall(), _synthetic_opening("door"),
                          DoorOperation.SLIDE, is_glazed=True)
    solids = [solid for part in parts for solid in part.solids]
    assert len(solids) == _FRAME_PIECE_COUNT + 4  # frame, stile, track, two panes


# --- rough openings and raked walls --------------------------------------------------------

def _synthetic_wall(top_z0_m: float | None = None, top_z1_m: float | None = None,
                    clad: bool = False) -> ResolvedWall:
    """A bare 4 m wall along +x with a single structure layer, for unit-level filling checks.

    ``clad=True`` adds a thin cladding band on the +y side, which is what qualifies a host
    for the exterior window casing.
    """
    layers = [ResolvedLayer(name="structure", material_ref="spf", thickness_m=0.14,
                            function="structure",
                            polygon=((0.0, -0.07), (4.0, -0.07), (4.0, 0.07), (0.0, 0.07)))]
    if clad:
        layers.append(ResolvedLayer(name="cladding", material_ref="fiber-cement",
                                    thickness_m=0.01, function="cladding",
                                    polygon=((0.0, 0.07), (4.0, 0.07), (4.0, 0.08), (0.0, 0.08))))
    return ResolvedWall(
        uid="W-TEST", tag="W-TEST", storey="main", assembly="EXT",
        axis=((0.0, 0.0), (4.0, 0.0)),
        layers=tuple(layers),
        z0_m=0.0, z1_m=3.0, top_z0_m=top_z0_m, top_z1_m=top_z1_m,
    )


def _synthetic_opening(kind: str, height_m: float = 2.0) -> ResolvedOpening:
    return ResolvedOpening(
        uid="OP-TEST", tag="OP-TEST", host_wall="W-TEST", type_ref="DT-TEST",
        width_m=0.9, height_m=height_m, sill_m=0.0, center_along_m=2.0,
        kind=kind, is_door=kind == "door",
    )


def test_a_window_in_an_unclad_wall_ships_no_exterior_casing():
    """The casing sits on a cladding plane; a host without one (concrete, interior) gets none."""
    parts = opening_parts(_synthetic_wall(), _synthetic_opening("window"), None)
    assert [part.key for part in parts] == ["frame", "glass"]


def test_a_window_in_a_clad_wall_ships_a_four_board_exterior_casing():
    parts = opening_parts(_synthetic_wall(clad=True), _synthetic_opening("window"), None)
    assert [part.key for part in parts] == ["frame", "glass", "exterior_trim"]
    trim = parts[-1]
    assert trim.material_key == "window_trim"
    assert len(trim.solids) == _TRIM_PIECE_COUNT
    for solid in trim.solids:
        # Every board sits proud of the exterior cladding face (y=0.08), not in the void.
        across = [y for _x, y in solid.ring]
        assert min(across) == pytest.approx(0.08, abs=1e-9)
        assert max(across) == pytest.approx(0.08 + _WINDOW_TRIM_PROUD_DEPTH_M, abs=1e-9)


def test_a_rough_opening_ships_no_product():
    """A rough opening is an unfilled void: the wall is carved, but no frame or panel is drawn."""
    mb = _MeshBuilder()
    _add_opening_filling(mb, _synthetic_wall(), _synthetic_opening("rough_opening"), None)
    assert mb.is_empty()


def test_a_product_under_a_raked_wall_top_stops_at_the_rake():
    """Mirrors buildOpening's ``availableHeight``: a gable wall's slope clips the product.

    Without this the door keeps its authored height and pushes its head through the roof plane
    — the same failure the raked wall body already guards against.
    """
    wall = _synthetic_wall(top_z0_m=3.0, top_z1_m=1.5)  # rakes down from start to end
    opening = _synthetic_opening("door", height_m=2.6)
    mb = _MeshBuilder()
    _add_opening_filling(mb, wall, opening, None)
    top_elevation = max(position[1] for _color, positions, _idx in mb.buckets()
                        for position in positions)
    # The lower jamb (at the +x end of the opening) sets the ceiling for the whole product.
    lower_jamb_along = opening.center_along_m + opening.width_m / 2
    rake_at_lower_jamb = 3.0 + (1.5 - 3.0) * (lower_jamb_along / 4.0)
    assert top_elevation == pytest.approx(rake_at_lower_jamb, abs=_DIMENSION_TOLERANCE_M)
    assert top_elevation < wall.z0_m + opening.sill_m + opening.height_m

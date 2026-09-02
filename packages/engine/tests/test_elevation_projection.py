"""The hidden-line elevation's geometry half: projection, occlusion, openings, cladding.

``test_elevation_annotations.py`` covers the sheet margin. What is asserted here is the part
a raster snapshot cannot: that the freestanding garage really occludes the house rather than
drawing through it, that a window is distinguishable from a door, that a raked attic wall
comes out raked, and that the drawing agrees with the facade rules ``houses/catlin`` states
about itself.
"""

from __future__ import annotations

import pytest
from shapely.geometry import box

from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.elevation_project import (
    collect_candidates,
    occlude,
    project_solids,
    view_for,
)
from typehaus.emit.draw.scene import Polyline
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import GPrism

FT = 12.0  # drawing units are inches


def _polylines(scene, *layers: str) -> list[Polyline]:
    wanted = set(layers)
    return [node for node in scene.nodes
            if isinstance(node, Polyline) and (not wanted or node.layer in wanted)]


def _tags(scene, *layers: str) -> set[str]:
    return {node.tag for node in _polylines(scene, *layers) if node.tag}


# --- the projection ----------------------------------------------------------------------
def test_the_two_mirrored_views_are_mirrored():
    """North and west are drawn from outside the building, so their u axis runs backwards.

    A north elevation with ``u = +x`` puts west on the left, which is the view from inside.
    """
    south, north = view_for("south"), view_for("north")
    east, west = view_for("east"), view_for("west")
    assert south.u_of(3.0, 0.0) == -north.u_of(3.0, 0.0)
    assert east.u_of(0.0, 3.0) == -west.u_of(0.0, 3.0)
    # Depth grows away from the eye in every view.
    assert south.depth_of(0.0, 5.0) > south.depth_of(0.0, 1.0)
    assert north.depth_of(0.0, 1.0) > north.depth_of(0.0, 5.0)
    assert east.depth_of(1.0, 0.0) > east.depth_of(5.0, 0.0)
    assert west.depth_of(5.0, 0.0) > west.depth_of(1.0, 0.0)


def test_unknown_facing_is_rejected():
    with pytest.raises(ValueError, match="unknown elevation facing"):
        view_for("up")


def test_a_raked_prism_projects_its_slope_not_its_bounding_box():
    """A gable wall's top follows the roof; the old elevation drew a rectangle."""
    view = view_for("south")
    prism = GPrism(ring=((0.0, 0.0), (4.0, 0.0), (4.0, 0.1), (0.0, 0.1)),
                   z0_m=0.0, z1_m=2.0, top=(0.0, 2.0, 2.0, 0.0))
    shadow = project_solids((prism,), view)
    assert shadow.area == pytest.approx(4.0, rel=1e-6)  # the triangle, not the 4x2 box
    assert shadow.bounds == pytest.approx((0.0, 0.0, 4.0, 2.0))


def test_a_full_height_void_does_not_punch_a_hole_in_the_shadow():
    """A vertical shaft is not see-through from a horizontal eye."""
    view = view_for("south")
    prism = GPrism(ring=((0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)), z0_m=0.0, z1_m=2.0,
                   voids=(((1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)),))
    assert project_solids((prism,), view).area == pytest.approx(8.0, rel=1e-6)


# --- occlusion ---------------------------------------------------------------------------
def test_the_house_and_the_garage_occlude_each_other(catlin_model):
    """The freestanding garage stands 4' north of the house. Whichever is nearer the eye
    must hide the other."""
    for facing in ("north", "south"):
        view = view_for(facing)
        pieces = occlude(collect_candidates(catlin_model, view), view)
        regions = [piece.geometry for piece in pieces]
        for index, first in enumerate(regions):
            for second in regions[index + 1:]:
                assert first.intersection(second).area < 1e-3, f"{facing}: overlap"


def test_the_garage_hides_the_north_wall_behind_it(catlin_model):
    """Not merely non-overlapping: the house's own north wall must lose area to the garage."""
    view = view_for("north")
    candidates = collect_candidates(catlin_model, view)
    pieces = {piece.candidate.key: piece for piece in occlude(candidates, view)}
    by_key = {candidate.key: candidate for candidate in candidates}
    north_walls = [key for key in pieces
                   if by_key[key].tag.startswith("W-") and by_key[key].family == "body"
                   and pieces[key].geometry.bounds[3] > 2.0]
    assert north_walls
    hidden = [key for key in north_walls
              if pieces[key].geometry.area < by_key[key].silhouette(view).area - 1.0]
    assert hidden, "nothing on the north facade lost area to the garage in front of it"


def test_interior_partitions_never_reach_the_sheet(catlin_model):
    """An interior wall is behind the cladding and behind the glass; it must be culled."""
    scene = build_elevation(catlin_model, "south")
    tags = _tags(scene)
    assert "W-M-C1" not in tags  # the x=18' centreline bearing wall
    assert "W-M-HS4" not in tags  # the laundry pocket wall


# --- depth banding -----------------------------------------------------------------------
def test_receding_building_goes_to_the_beyond_layer(catlin_model):
    """The garage is a plane of its own on the east elevation and must read lighter."""
    scene = build_elevation(catlin_model, "east")
    beyond = _tags(scene, "A-WALL-BEYD")
    assert any(tag.startswith("W-G") or tag.startswith("RF-GARAGE") for tag in beyond)
    facade = _tags(scene, "A-WALL")
    assert not (beyond & facade), "no element may be on both depth bands"


def test_line_weight_falls_off_with_depth(catlin_model):
    scene = build_elevation(catlin_model, "east")
    facade = [node.lineweight for node in _polylines(scene, "A-WALL")]
    beyond = [node.lineweight for node in _polylines(scene, "A-WALL-BEYD")]
    buried = [node.lineweight for node in _polylines(scene, "A-WALL-BELW")]
    assert facade and beyond and buried
    assert max(beyond) < min(facade)
    assert max(buried) <= max(beyond)


# --- the facade merge --------------------------------------------------------------------
def test_a_facade_draws_as_one_run_not_one_rectangle_per_segment(catlin_model):
    """The south facade is authored as many wall segments across three storeys.

    They are one plane of cladding, so the drawing must carry one outline for the lot —
    a seam at every partition tee and a rule at every storey is the model showing through.
    """
    scene = build_elevation(catlin_model, "south")
    walls = [node for node in _polylines(scene, "A-WALL") if node.tag
             and node.tag.startswith("W-") and node.tag.endswith(("S1", "S2", "S3", "S4"))]
    assert walls
    tallest = max(walls, key=lambda node: max(p[1] for p in node.points)
                  - min(p[1] for p in node.points))
    height = max(p[1] for p in tallest.points) - min(p[1] for p in tallest.points)
    assert height > 25 * FT, "the merged run should span grade to the gable, not one storey"


# --- openings ----------------------------------------------------------------------------
def test_a_window_and_a_door_are_told_apart(catlin_model):
    scene = build_elevation(catlin_model, "south")
    assert _tags(scene, "A-GLAZ", "A-GLAZ-SASH") & {"WIN-M-BED-S1"}
    assert _tags(scene, "A-DOOR") & {"D-M-BALC"}
    assert "D-M-BALC" not in _tags(scene, "A-GLAZ-SASH")


def test_the_south_gable_carries_four_openings_mirrored_about_the_ridge(catlin_model):
    """``houses/catlin/CLAUDE.md`` §Gables: WIN-A-S2/JUL-W/JUL-E/S3 at 12'-8", 16'-0",
    20'-0", 23'-4" — every pair summing to 36'-0". If the drawing disagrees, one of the
    two is wrong."""
    scene = build_elevation(catlin_model, "south")
    centres = {}
    for tag in ("WIN-A-S2", "WIN-A-S-JUL-W", "WIN-A-S-JUL-E", "WIN-A-S3"):
        nodes = [node for node in _polylines(scene) if node.tag == tag]
        assert nodes, f"{tag} missing from the south gable"
        us = [point[0] for node in nodes for point in node.points]
        centres[tag] = (min(us) + max(us)) / 2.0
    assert centres["WIN-A-S2"] == pytest.approx(12 * FT + 8, abs=1.0)
    assert centres["WIN-A-S-JUL-W"] == pytest.approx(16 * FT, abs=1.0)
    assert centres["WIN-A-S-JUL-E"] == pytest.approx(20 * FT, abs=1.0)
    assert centres["WIN-A-S3"] == pytest.approx(23 * FT + 4, abs=1.0)


def test_the_north_gable_pair_sits_at_twelve_and_twenty_four_feet(catlin_model):
    """Same source, same section — and the north view is mirrored, so u = -x."""
    scene = build_elevation(catlin_model, "north")
    for tag, station_ft in (("WIN-A-N1", 12.0), ("WIN-A-N2", 24.0)):
        nodes = [node for node in _polylines(scene) if node.tag == tag]
        assert nodes, f"{tag} missing from the north gable"
        us = [point[0] for node in nodes for point in node.points]
        assert (min(us) + max(us)) / 2.0 == pytest.approx(-station_ft * FT, abs=1.0)


def test_an_operable_window_carries_a_dashed_operation_symbol(catlin_model):
    scene = build_elevation(catlin_model, "south")
    dashed = [node for node in _polylines(scene, "A-GLAZ-SASH")
              if node.linetype == "DASHED"]
    assert dashed, "no operation symbols drawn"
    assert {node.tag for node in dashed} <= {node.tag for node in _polylines(scene)}


def test_the_overhead_door_reads_as_a_sectional_door(catlin_model):
    """A 16' garage door is a stack of 21" panels, which is what identifies it."""
    scene = build_elevation(catlin_model, "east")
    joints = [node for node in _polylines(scene, "A-DOOR")
              if node.tag == "D-G-OVERHEAD" and len(node.points) == 2
              and abs(node.points[0][1] - node.points[1][1]) < 1e-6]
    assert len(joints) >= 3


# --- cladding ----------------------------------------------------------------------------
def test_the_cladding_texture_reaches_the_face_fastened_panel(catlin_model):
    """``pbr-panel-26`` matches none of ``palette.family_of``'s needles, so the catalog's
    own ``exposed_fastener`` flag is what says which module to draw."""
    scene = build_elevation(catlin_model, "south")
    panel = [node for node in _polylines(scene, "A-WALL-FINI")
             if node.tag and node.tag.startswith("W-M-S")]
    assert len(panel) > 5, "the main south facade drew no cladding module at all"
    assert all(abs(node.points[0][0] - node.points[-1][0]) < 1e-6 for node in panel), \
        "a profiled panel's joints run vertically"
    # ...and a coursed material on the same sheet runs the other way.
    masonry = [node for node in _polylines(scene, "A-WALL-FINI")
               if abs(node.points[0][1] - node.points[-1][1]) < 1e-6]
    assert masonry, "the retaining wall's masonry courses should run horizontally"


def test_the_board_and_batten_wall_draws_battens_and_not_seam_pitch(catlin_model):
    """The north/south panel is CONCEALED-fastened and declares ``skin_family``, so on the
    two flags alone ``_recipe_for`` would fall through to ``_SEAM_PITCH_M`` and draw a 16"
    seam rhythm on a wall whose battens stand at 20". The finish is asked FIRST, ahead of
    the ``exposed_fastener`` gate, which is what this pins.

    Measured as the modal gap between adjacent module lines rather than as any one pair: the
    lines are clipped to what is visible, so a run beside an opening is a stub.
    """
    from typehaus.emit.draw.elevation_finish import _BATTEN_PITCH_M, _SEAM_PITCH_M

    scene = build_elevation(catlin_model, "south")
    stations = sorted({round(node.points[0][0], 4)
                       for node in _polylines(scene, "A-WALL-FINI")
                       if node.tag and node.tag.startswith("W-M-S")
                       and abs(node.points[0][0] - node.points[-1][0]) < 1e-6})
    assert len(stations) > 5, "the main south facade drew no cladding module at all"
    gaps = [round(b - a, 3) for a, b in zip(stations[:-1], stations[1:], strict=True)]
    pitch_in = max(set(gaps), key=gaps.count)
    assert pitch_in == pytest.approx(_BATTEN_PITCH_M / M_PER_IN, abs=0.01)
    assert pitch_in != pytest.approx(_SEAM_PITCH_M / M_PER_IN, abs=0.01)


def test_cladding_texture_stays_inside_the_visible_facade(catlin_model):
    scene = build_elevation(catlin_model, "south")
    walls = _polylines(scene, "A-WALL")
    hull = box(*_bounds([node for node in walls]))
    for node in _polylines(scene, "A-WALL-FINI"):
        for point in node.points:
            assert hull.buffer(1e-6).covers(box(point[0], point[1], point[0], point[1]))


def _bounds(nodes) -> tuple[float, float, float, float]:
    us = [point[0] for node in nodes for point in node.points]
    zs = [point[1] for node in nodes for point in node.points]
    return (min(us), min(zs), max(us), max(zs))


# --- roof edge ---------------------------------------------------------------------------
def test_the_eave_water_chain_reaches_the_elevation(catlin_model):
    """``resolve/roof_trim.py`` resolves drip edge, box gutter and downspout as solids, and
    the elevation must draw them."""
    for facing in ("east", "west"):
        scene = build_elevation(catlin_model, facing)
        assert _polylines(scene, "A-ROOF-TRIM"), f"{facing}: no roof edge trim drawn"


def test_the_roof_is_drawn_as_a_surface(catlin_model):
    scene = build_elevation(catlin_model, "west")
    roofs = _polylines(scene, "A-ROOF")
    assert roofs
    assert "RF-HOUSE" in {node.tag for node in roofs}


def test_the_ridge_stands_at_thirty_feet_three(catlin_model):
    """6:12, zero overhang — ``houses/catlin/CLAUDE.md``.

    The drawing tops out at the *finished* ridge, not the structural one: ``ridge_z_m`` is
    the rafter-top plane and this roof carries 6" of polyiso, a nailbase deck, a vent mat
    and the seam above it. A whole extra foot would mean the pitch or the plate had moved.
    """
    scene = build_elevation(catlin_model, "south")
    top = max(point[1] for node in _polylines(scene, "A-WALL", "A-ROOF", "A-ROOF-TRIM")
              for point in node.points)
    structural = max(roof.ridge_z_m for roof in catlin_model.roofs) / M_PER_IN
    assert structural == pytest.approx(30 * FT + 3, abs=1.0)
    assert 0.0 < top - structural < 12.0


def test_a_model_without_the_geometry_ir_says_so(catlin_plan):
    """``resolve_preview`` skips the geometry stage; an elevation cannot be built from one,
    and saying that beats silently drawing a wireframe that is not the same drawing."""
    from typehaus.resolve import resolve_preview

    preview = resolve_preview(catlin_plan)
    with pytest.raises(ValueError, match="geometry IR"):
        build_elevation(preview, "south")

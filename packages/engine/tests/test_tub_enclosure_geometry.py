"""The installed tub detail: shared geometry, access, and a single insulation order."""

from dataclasses import replace

import pytest
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from typehaus.model import TubEnclosureSpec, inch
from typehaus.model.placeable_symbols import model_parts, place_local, plan_symbol_strokes
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.tub_enclosures import ENCLOSURE_CATEGORIES, _ellipse, _frame


@pytest.fixture
def enclosure_solids(catlin_model_ro):
    return [s for s in catlin_model_ro.solids if s.category in ENCLOSURE_CATEGORIES]


def test_kohler_is_an_open_oval_shell_with_a_center_drain():
    width, depth, height = (inch(v).meters for v in (59.6875, 35.75, 21))
    shell, drain, overflow = model_parts("kohler-underscore-6036", width, depth, height)
    assert shell["shape"] == "mesh"
    assert shell["size"] == pytest.approx((width, depth, height))
    assert shell["center"][2] + shell["size"][2]/2 == pytest.approx(height)
    assert drain["center"][:2] == (0, 0)
    assert overflow["center"][1] > 0
    strokes = plan_symbol_strokes("kohler-underscore-6036", width, depth)
    assert max(x for x, _ in strokes[1]["points"]) == pytest.approx(inch(55.5625).meters/2)
    assert max(y for _, y in strokes[1]["points"]) == pytest.approx(inch(28.375).meters/2)
    # No opaque surface spans the basin opening at rim height: all top-plane triangles
    # remain outside the ellipse, whose center must be open to the basin floor.
    mesh = shell["mesh"]
    for triangle in mesh["triangles"]:
        points = [mesh["positions"][index] for index in triangle]
        if all(abs(p[2]-height) < 1e-9 for p in points):
            assert not Polygon([(p[0], p[1]) for p in points]).contains(Point(0, 0))
    # A quarter turn puts the long axis along plan y, including the physical center drain.
    rotated = place_local(strokes[1]["points"], (2, 3), 90)
    assert max(y for _, y in rotated)-min(y for _, y in rotated) == pytest.approx(
        inch(55.5625).meters)


def test_batts_fit_real_framing_and_clear_the_access_panel(catlin_model_ro, enclosure_solids):
    model = catlin_model_ro
    batts = [s for s in enclosure_solids if s.category == "tub_batt"]
    assert batts and all(s.material == "mineral-wool" and s.derived for s in batts)
    panel = next(c for c in model.canvas_objects if c.tag == "FURN-M-BATH2-TUBDK-AP")
    for batt in batts:
        wall = next(w for w in model.walls if w.tag in batt.tag)
        cavity = next(layer for layer in wall.layers if layer.is_cavity)
        assert Polygon(cavity.polygon).buffer(1e-9).covers(Polygon(batt.outline))
        framing = [member for other_wall in model.walls
                   if other_wall.tag in {"W-M-TUBDK-W", "W-M-TUBDK-S"}
                   for member in other_wall.members]
        for member in framing:
            solid = member_box(member)
            assert solid is not None
            corners = solid.corners_bottom+solid.corners_top
            lo, hi = min(p[2] for p in corners), max(p[2] for p in corners)
            if min(hi, batt.z1_m)-max(lo, batt.z0_m) > 1e-8:
                footprint = Polygon([(p[0], p[1]) for p in corners]).convex_hull
                assert footprint.intersection(Polygon(batt.outline)).area < 1e-10
        if wall.tag == panel.attachment_wall and min(batt.z1_m, panel.body_z1_m) > max(
                batt.z0_m, panel.body_z0_m)+1e-9:
            local, _world, _run = _frame(wall)
            panel_range = [local(p)[0] for p in panel.footprint]
            batt_range = [local(p)[0] for p in batt.outline]
            assert min(max(panel_range), max(batt_range))-max(
                min(panel_range), min(batt_range)) <= 1e-8
    for index, batt in enumerate(batts):
        for other in batts[index+1:]:
            if min(batt.z1_m, other.z1_m) > max(batt.z0_m, other.z0_m)+1e-9:
                assert Polygon(batt.outline).intersection(Polygon(other.outline)).area < 1e-10


def test_returns_and_mortar_preserve_support_and_service_access(catlin_model_ro, enclosure_solids):
    model = catlin_model_ro
    tub = next(c for c in model.canvas_objects if c.tag == "FX-M-BATH2-TUB")
    panel = next(c for c in model.canvas_objects if c.tag == "FURN-M-BATH2-TUBDK-AP")
    fixture = model.plan.by_tag(tub.tag)
    spec = fixture.tub_enclosure
    from typehaus.model.placeable_symbols._kohler_underscore import shell_half_axes_at

    returns = [s for s in enclosure_solids if s.category == "tub_insulation_return"]
    mortar, = [s for s in enclosure_solids if s.category == "tub_mortar_bed"]
    assert returns and mortar.material == "mortar"
    assert mortar.z0_m == pytest.approx(inch(.75).meters)
    assert mortar.z1_m-mortar.z0_m == pytest.approx(inch(1).meters)
    union = unary_union([Polygon(s.outline, s.voids) for s in returns])
    assert union.area == pytest.approx(sum(Polygon(s.outline, s.voids).area for s in returns))
    assert union.intersection(Polygon(mortar.outline)).area < 1e-10
    support = _ellipse(spec.support_width.meters/2, spec.support_depth.meters/2,
                       tub.position, tub.rotation_degrees)
    assert Polygon(mortar.outline).equals(support)
    local, _world, _run = _frame(model.wall(panel.attachment_wall))
    panel_range = [local(p)[0] for p in panel.footprint]
    for solid in returns:
        assert not solid.derived
        assert solid.z1_m-solid.z0_m == pytest.approx(inch(3.5).meters)
        assert solid.z0_m == pytest.approx(mortar.z0_m)
        rx, ry = shell_half_axes_at(
            (solid.z1_m-tub.z_m)/inch(21).meters, inch(59.6875).meters, inch(35.75).meters)
        shell_section = _ellipse(rx, ry, tub.position, tub.rotation_degrees)
        assert Polygon(solid.outline, solid.voids).intersection(shell_section).area < 1e-10
        stations = [local(p)[0] for p in solid.outline]
        assert min(max(stations), max(panel_range))-max(
            min(stations), min(panel_range)) <= 1e-8
    # The full 21 in. shell sits on 1 in. of mortar over the ¾ in. subfloor.
    # The downstream connection remains distinct from the physical center drain.
    assert tub.z_m == pytest.approx(inch(1.75).meters)
    assert tub.body_z1_m == pytest.approx(inch(22.75).meters)
    assert fixture.drain_position.xy_m != tub.position


def test_only_lower_returns_add_to_the_insulation_order(catlin_model_ro, enclosure_solids):
    from typehaus.takeoff.envelope import envelope_layer_takeoff
    from typehaus.takeoff.framing import structural_solids_takeoff

    model = catlin_model_ro
    rows = envelope_layer_takeoff(model)
    row, = [r for r in rows if r["scope"] == "tub enclosure"]
    assert row["material"] == "mineral-wool" and row["thickness_in"] == 3.5
    assert row["net_area_sqft"] == round(sum(Polygon(s.outline, s.voids).area
        for s in enclosure_solids if s.category == "tub_insulation_return")*10.7639104, 1)
    without = replace(model, solids=[s for s in model.solids if s not in enclosure_solids])
    assert [r for r in rows if r["scope"] != "tub enclosure"] == envelope_layer_takeoff(without)
    assert structural_solids_takeoff(model) == structural_solids_takeoff(without)


def test_enclosure_spec_rejects_invalid_dimensions():
    with pytest.raises(ValueError, match="positive"):
        TubEnclosureSpec(knee_wall_refs=("west", "south"), access_panel_ref="panel",
                         deck_ref="deck", lower_return_thickness=inch(0))


def test_unresolved_enclosure_reference_reports_failure_without_partial_solids():
    from types import SimpleNamespace

    from typehaus.findings import Result
    from typehaus.resolve.tub_enclosures import resolve_tub_enclosures

    fixture = SimpleNamespace(tag="tub", tub_enclosure=TubEnclosureSpec(
        knee_wall_refs=("west", "south"), access_panel_ref="missing", deck_ref="deck"))
    existing_solid = object()
    model = SimpleNamespace(
        plan=SimpleNamespace(storeys=[SimpleNamespace(tag="main")],
                             storey_elements=lambda _: [fixture]),
        canvas_objects=[], solids=[existing_solid])
    failure, = resolve_tub_enclosures(model)
    assert failure.check_id == "integrity.tub_enclosure" and failure.result == Result.FAIL
    assert failure.element_tags == ("tub",)
    assert model.solids == [existing_solid]


def test_occupied_space_includes_the_rim_and_the_whole_framed_deck(catlin_model_ro):
    model = catlin_model_ro
    tub = next(c for c in model.canvas_objects if c.tag == "FX-M-BATH2-TUB")
    deck = next(s for s in model.solids if s.tag == "SL-M-TUBDK")
    tub_bounds = Polygon(tub.footprint).bounds
    deck_bounds = Polygon(deck.outline).bounds
    assert tub_bounds[2]-tub_bounds[0] == pytest.approx(inch(35.75).meters)
    assert tub_bounds[3]-tub_bounds[1] == pytest.approx(inch(59.6875).meters)
    assert deck_bounds[2]-deck_bounds[0] == pytest.approx(inch(38.375).meters)
    assert deck_bounds[3]-deck_bounds[1] == pytest.approx(inch(70.24).meters)
    assert Polygon(deck.outline).covers(Polygon(tub.footprint))
    assert tub.body_z1_m-tub.body_z0_m == pytest.approx(inch(21).meters)
    assert tub.body_z1_m == pytest.approx(deck.z1_m+inch(.5).meters)

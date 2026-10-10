"""Catlin's code dimensions, stack, quantities, drawings, and export share physical geometry."""

from dataclasses import replace

import pytest
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from typehaus.checks.code.mn_residential.stair_winders import winder_measurements, winder_treads
from typehaus.checks.structural.stair_winders import winder_support_problems
from typehaus.emit.draw import build_floorplan
from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.scene import ArchDimension, Polyline
from typehaus.emit.draw.winder_detail import build_winder_detail
from typehaus.emit.gltf.members import _add_member
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.resolve.geometry_ir import GPrism
from typehaus.resolve.geometry_members import member_solid
from typehaus.server.model_json_shared import _member_json
from typehaus.takeoff.framing import framing_takeoff
from typehaus.takeoff.sheet_goods import sheet_goods_takeoff
from typehaus.takeoff.stairs import stair_tread_takeoff, winder_blank_in


@pytest.fixture
def stair(catlin_model_ro):
    return next(s for s in catlin_model_ro.stairs if s.tag == "ST-S2A")


def test_code_and_support_paths_pass_from_resolved_geometry(stair, catlin_model_ro, catlin_ctx):
    assert not winder_support_problems(
        stair, catlin_model_ro.plan.by_tag(stair.tag), catlin_model_ro
    )
    [finding] = winder_treads(catlin_ctx)
    assert finding.result.value == "pass"
    assert len(winder_measurements(stair).walkline_depths_m) == 3
    assert stair.riser_count == 16 and stair.riser_height_m / 0.0254 == pytest.approx(7.5)
    surfaces = sorted(m.z1_m for m in stair.members if m.category in {"winder", "tread"})
    assert surfaces == pytest.approx([(0.0254 * (121.5 + i * 7.5)) for i in range(1, 16)])
    assert not [m for m in stair.members if m.child_key.startswith("landing-post-")]


@pytest.mark.parametrize(
    "defect",
    ["missing_plywood", "floating_tier", "missing_block", "missing_floor", "wrong_rim_attachment"],
)
def test_support_check_fails_when_real_support_is_removed(stair, catlin_model_ro, defect):
    authored = catlin_model_ro.plan.by_tag(stair.tag)
    members = stair.members
    model = catlin_model_ro
    if defect == "missing_plywood":
        members = tuple(m for m in members if not m.child_key.startswith("stair-subdeck-001-"))
    elif defect == "floating_tier":
        members = tuple(
            replace(m, z0_m=m.z0_m + 0.02, z1_m=m.z1_m + 0.02)
            if m.child_key.startswith("landing-rim-winder1-")
            else m
            for m in members
        )
    elif defect == "missing_block":
        members = tuple(m for m in members if not m.child_key.startswith("landing-joist-winder0-"))
    elif defect == "missing_floor":
        model = replace(model, floors=[replace(f, members=[]) for f in model.floors])
    else:
        members = tuple(
            replace(m, start_connection="winder-box-rim:adjacent-corner")
            if m.category == "stringer"
            else m
            for m in members
        )
    assert winder_support_problems(replace(stair, members=members), authored, model)


def test_complete_plywood_decks_carry_the_next_box_without_hidden_oak(stair):
    previous = None
    previous_top = None
    for tier in range(3):
        plywood = [m for m in stair.members if m.child_key.startswith(f"stair-subdeck-{tier:03d}-")]
        frames = [
            m
            for m in stair.members
            if m.child_key.startswith(
                (f"landing-rim-winder{tier}-", f"landing-joist-winder{tier}-")
            )
        ]
        deck = unary_union([Polygon(m.plan_outline) for m in plywood])
        oak = Polygon(
            next(m for m in stair.members if m.child_key == f"winder-{tier:03d}").plan_outline
        )
        upper = unary_union(
            [
                Polygon(m.plan_outline)
                for m in stair.members
                if m.child_key.startswith(f"stair-subdeck-{tier + 1:03d}-")
            ]
        )
        assert deck.difference(unary_union([oak, upper])).area < 1e-9
        if previous is not None:
            assert all(m.z0_m == pytest.approx(previous_top) for m in frames)
            assert (
                unary_union([Polygon(m.plan_outline) for m in frames])
                .difference(previous.buffer(1e-7))
                .area
                < 1e-9
            )
        for member in plywood:
            assert member.z1_m - member.z0_m == pytest.approx(0.75 * 0.0254)
            assert member.z0_m == pytest.approx(frames[0].z1_m)
            bounds = Polygon(member.plan_outline).bounds
            dims = sorted((bounds[2] - bounds[0], bounds[3] - bounds[1]))
            assert dims[0] <= 48 * 0.0254 and dims[1] <= 96 * 0.0254
        previous, previous_top = deck, plywood[0].z1_m
    stringers = [m for m in stair.members if m.category == "stringer"]
    assert len(stringers) == 3
    assert all(m.start_connection.startswith("winder-box-rim:") for m in stringers)
    assert len([m for m in stair.members if m.child_key.startswith("hanger-winder-")]) == 3


def test_plywood_and_oak_are_counted_once(stair, catlin_model_ro):
    decks = [m for m in stair.members if m.category == "stair_subdeck"]
    [row] = [r for r in sheet_goods_takeoff(catlin_model_ro) if r["scope"] == "stair subdeck"]
    assert row["net_area_sqft"] == pytest.approx(
        round(sum(Polygon(m.plan_outline).area for m in decks) * 10.7639104167, 1)
    )
    rows = stair_tread_takeoff(catlin_model_ro)
    assert sum(r["pieces"] for r in rows if r["stair"] == stair.tag and r["use"] == "winder") == 3
    assert not [r for r in rows if r["use"] == "stair_subdeck"]
    assert not [r for r in framing_takeoff(catlin_model_ro) if r.get("category") == "stair_subdeck"]


def test_json_prisms_gltf_and_blanks_match_physical_panels(stair):
    for member in (m for m in stair.members if m.category in {"winder", "stair_subdeck"}):
        data = _member_json(member)
        assert data["plan_outline"] == [list(p) for p in member.plan_outline]
        solid = member_solid(member)
        assert isinstance(solid, GPrism)
        assert Polygon(solid.ring).equals(Polygon(member.plan_outline))
        mb = _MeshBuilder()
        _add_member(mb, member)
        positions = [p for pos, _indices in mb._buckets.values() for p in pos]
        assert min(p[1] for p in positions) == pytest.approx(member.z0_m)
        assert max(p[1] for p in positions) == pytest.approx(member.z1_m)
        assert min(p[0] for p in positions) == pytest.approx(min(p[0] for p in member.plan_outline))
        if member.category == "winder":
            assert data["nosing_line"] == [list(p) for p in member.nosing_line]
            assert (
                Polygon(member.plan_outline)
                .boundary.buffer(1e-7)
                .covers(LineString(member.nosing_line))
            )
            assert winder_blank_in(member, 0) == winder_blank_in(member, 100)


def test_winder_detail_and_framing_sheet_draw_resolved_edges(
    stair, catlin_model_ro, catlin_sheet_index
):
    scene = build_winder_detail(catlin_model_ro, stair.tag)
    dimensions = [node for node in scene.nodes if isinstance(node, ArchDimension)]
    assert len(dimensions) == 3
    assert sorted(__import__("math").dist(n.p0, n.p1) for n in dimensions) == pytest.approx(
        sorted(v / 0.0254 for v in winder_measurements(stair).walkline_depths_m)
    )
    framing = build_framing_plan(catlin_model_ro, stair.storey)
    keys = {n.tag for n in framing.nodes if isinstance(n, Polyline)}
    assert {m.child_key for m in stair.members if m.category == "stair_subdeck"} <= keys
    sheets = catlin_sheet_index()
    assert any(s.number == "S-501.1" and "winder" in s.title for s in sheets)


def test_architectural_plan_shows_the_actual_clear_inner_boundary(stair, catlin_model_ro):
    scene = build_floorplan(catlin_model_ro, stair.to_storey)
    # The notch's south edge is FO-A-STAIR's south edge, drawn once, by the opening.
    opening = catlin_model_ro.plan.by_tag(catlin_model_ro.plan.by_tag(stair.tag).floor_opening)
    edges = unary_union(
        [
            LineString([(x * 0.0254, y * 0.0254) for x, y in node.points])
            for node in scene.nodes
            if isinstance(node, Polyline)
            and ((node.uid == stair.uid and node.tag.startswith("winder-edge-"))
                 or node.uid == opening.uid)
        ]
    )
    # Drawing unions use the engine's one-micron overlay grid.
    assert edges.buffer(2e-6).covers(LineString(stair.winder_turn.inner_boundary))


def test_wall_rail_surface_meets_every_winder_nose_across_its_width(stair):
    from typehaus.resolve.stairs.walkline import winder_surface_z_at

    for member in (m for m in stair.members if m.category == "winder"):
        a, b = member.nosing_line
        for fraction in (0.1, 0.5, 0.9):
            point = tuple(x + fraction * (y - x) for x, y in zip(a, b, strict=True))
            assert winder_surface_z_at(stair, point) == pytest.approx(member.z1_m)


def test_malformed_authored_turn_reports_an_integrity_finding(catlin_plan):
    from typehaus.resolve import resolve

    original = catlin_plan.by_tag("ST-S2A")
    bad_turn = original.winder_turn.model_copy(
        update={"riser_lines": original.winder_turn.riser_lines[:-1]}
    )
    changed = original.model_copy(update={"winder_turn": bad_turn})
    variant = catlin_plan.with_elements(
        "attic",
        tuple(
            changed if element.tag == original.tag else element
            for element in catlin_plan.storey_elements("attic")
        ),
    )
    model, findings = resolve(variant)
    assert not [s for s in model.stairs if s.tag == original.tag]
    assert any(f.check_id == "integrity.stair_winders" and "n + 1" in f.message for f in findings)
    assert len(catlin_plan.by_tag("ST-S2A").winder_turn.riser_lines) == 4


def test_stringer_attachment_is_hardware_and_is_not_ordered_as_lumber(catlin_model_ro):
    from typehaus.hardware.catalog import ROLE_STAIR_STRINGER_CONNECTOR
    from typehaus.hardware.config import HangerDetectionRules
    from typehaus.takeoff.hangers import joist_hanger_rows

    rows = framing_takeoff(catlin_model_ro)
    assert not [row for row in rows if row["category"] == "hanger" and row["material"] == "steel"]
    hardware = [
        r
        for r in joist_hanger_rows(catlin_model_ro, HangerDetectionRules())
        if r["role"] == ROLE_STAIR_STRINGER_CONNECTOR and "landing-rim-winder" in r["basis"]
    ]
    assert sum(r["count"] for r in hardware) == 3


def _variant(catlin_plan, tag, **update):
    original = catlin_plan.by_tag(tag)
    changed = original.model_copy(update=update)
    return catlin_plan.with_elements(
        "attic",
        tuple(changed if e.tag == tag else e for e in catlin_plan.storey_elements("attic")),
    )


def test_the_turn_sits_under_intact_deck_and_headroom_is_graded_there(stair, catlin_model_ro,
                                                                     catlin_ctx):
    """Only the straight flight is in FO-A-STAIR; R311.7.2 measures the turn under FS-ATTIC."""
    from typehaus.checks.code.mn_residential.stairs import stair_headroom

    opening = catlin_model_ro.plan.by_tag("FO-A-STAIR")
    hole = Polygon([p.xy_m for p in opening.outline]).buffer(1e-7)
    winders = [m for m in stair.members if m.category == "winder"]
    assert any(not hole.covers(Polygon(m.plan_outline)) for m in winders)
    [finding] = [f for f in stair_headroom(catlin_ctx) if f.message.startswith("ST-S2A ")]
    assert finding.result.value == "pass" and "FS-ATTIC" in finding.message


def test_a_straight_tread_under_intact_deck_is_still_refused(catlin_plan):
    from typehaus.quantities import Point2D, inch
    from typehaus.resolve import resolve

    start = catlin_plan.by_tag("ST-S2A").start
    # 2" south: the straight flight's south edge runs under the deck past FO-A-STAIR.
    moved = Point2D(start.x, start.y - inch(2))
    model, findings = resolve(_variant(catlin_plan, "ST-S2A", start=moved))
    assert not [s for s in model.stairs if s.tag == "ST-S2A"]
    assert any(f.check_id == "integrity.stair_opening" and "ST-S2A" in f.message
               for f in findings)


def test_a_turn_under_a_low_deck_fails_headroom(catlin_model_ro):
    """Drop FS-ATTIC 12": the turn under it loses R311.7.2, and the void keeps the flight."""
    from types import SimpleNamespace

    from typehaus.checks.code.mn_residential.stairs import stair_headroom

    drop = 0.3048
    floors = [
        replace(f, deck_z0_m=f.deck_z0_m - drop,
                members=[replace(m, z0_m=m.z0_m - drop, z1_m=m.z1_m - drop) for m in f.members])
        if f.tag == "FS-ATTIC" else f
        for f in catlin_model_ro.floors
    ]
    ctx = SimpleNamespace(model=replace(catlin_model_ro, floors=floors), plan=catlin_model_ro.plan,
                          preferences=None)
    [finding] = [f for f in stair_headroom(ctx) if f.message.startswith("ST-S2A ")]
    assert finding.result.value == "fail" and "FS-ATTIC" in finding.message

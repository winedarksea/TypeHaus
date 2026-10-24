"""Six usable holders, real fixing targets, and a furnishing handoff to the trades."""

from pathlib import Path

import pytest
from shapely.geometry import Polygon

from typehaus.checks.advisory.backing import floating_band_ends
from typehaus.checks.advisory.backing_fixings import wall_fixing_support
from typehaus.model.placeable_symbols import place_local
from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve.framing.backing_panels import backing_bands
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.mep_envelopes import run_polylines, run_sections
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.server.model_json import model_to_dict
from typehaus.source.ops import PatchOp, RawExpr
from typehaus.source.writeback import apply_ops_to_source
from typehaus.takeoff.placeables import placeables_takeoff

ROOMS = ("RM-B-BATH", "RM-M-BATH1", "RM-M-BATH2", "RM-S-BATH1",
         "RM-S-SUITEBATH", "RM-A-STUBATH")


def _holders(model):
    return [obj for obj in model.canvas_objects if obj.type_ref in {"FT-MOEN-ALIGN-TP", "FT-MOEN-ALIGN-TP-CH"}]


def _envelope(holder, depth=6):
    # Back plane remains fixed when the review envelope projects beyond the bare hardware.
    return Polygon(place_local([(-4.055 * IN, 1.67 * IN), (4.055 * IN, 1.67 * IN),
                                (4.055 * IN, (1.67 - depth) * IN),
                                (-4.055 * IN, (1.67 - depth) * IN)],
                               holder.position, holder.rotation_degrees))


def test_every_toilet_has_one_selected_holder_at_26_aff(catlin_plan, catlin_model_ro):
    holders = _holders(catlin_model_ro)
    assert len(holders) == 6
    assert {obj.room for obj in holders} == set(ROOMS)
    wc_rooms = [obj.room for obj in catlin_model_ro.canvas_objects if obj.tag.endswith("-WC")]
    assert sorted(wc_rooms) == sorted(obj.room for obj in holders)
    product = next(t for t in catlin_plan.library.furniture_types if t.tag == holders[0].type_ref)
    assert [length.inches for length in product.footprint] == pytest.approx([8.11, 3.34])
    assert product.height.inches == pytest.approx(1.34)
    assert product.product_ref == "PROD-MOEN-YB0408BN"
    selected = next(p for p in catlin_plan.library.products if p.tag == product.product_ref)
    assert selected.model == "YB0408BN"
    types = {t.tag: t for t in catlin_plan.library.furniture_types}
    for holder in holders:
        expected_product = "PROD-MOEN-YB0408CH" if holder.room == "RM-M-BATH2" else selected.tag
        assert types[holder.type_ref].product_ref == expected_product
        room = next(room for room in catlin_model_ro.rooms if room.tag == holder.room)
        floor = room_finished_floor_elevation(catlin_model_ro, room)
        assert (holder.z_m + 0.67 * IN - floor) / IN == pytest.approx(26)


def test_mounting_positions_are_referenced_to_actual_supports(catlin_model_ro):
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    for room, y in zip(ROOMS[:3], (267.4375, 300.51, 226.74), strict=True):
        holder = next(obj for obj in _holders(catlin_model_ro) if obj.room == room)
        toilet = next(obj for obj in objects.values()
                      if obj.room == room and obj.tag.endswith("-WC"))
        assert holder.position[1] / IN == pytest.approx(y)
        bowl = Polygon(toilet.footprint).bounds
        distance = (y - bowl[3] / IN if room == "RM-M-BATH1" else bowl[1] / IN - y)
        assert distance == pytest.approx(8)
    assert objects["FURN-S-BATH1-TP"].position[0] / IN == pytest.approx(27)
    for tag, y in (("FURN-S-SUITEBATH-TP", 248.25), ("FURN-A-STUBATH-TP", 253)):
        holder = objects[tag]
        vanity = objects[holder.host_fixture_ref]
        assert holder.position[1] / IN == pytest.approx(y)
        assert Polygon(holder.footprint).bounds[2] == pytest.approx(
            Polygon(vanity.footprint).bounds[0])


def test_both_posts_have_exact_support_and_blocks_fill_stud_bays(catlin_ctx):
    findings = [f for f in wall_fixing_support(catlin_ctx)
                if any(tag.endswith("-TP") for tag in f.element_tags)]
    assert len(findings) == 8
    assert all(f.result.value == "pass" for f in findings)
    bands = backing_bands(catlin_ctx.plan)
    count = 0
    for wall in catlin_ctx.model.walls:
        tp_bands = [band for band in bands.get(wall.tag, ()) if "-TP" in band.tag]
        if not tp_bands:
            continue
        assert not floating_band_ends(wall, tp_bands)
        holder = next(obj for obj in _holders(catlin_ctx.model) if obj.attachment_wall == wall.tag)
        for band in tp_bands:
            count += 1
            assert band.profile == "2x6" and band.material_ref == "spf"
            centre = wall.base_ref_z_m + band.elevation_m + band.height_m / 2
            assert centre == pytest.approx(holder.z_m + 0.67 * IN)
    assert count == 5


def test_loaded_roll_and_upward_pivot_clear_bodies_and_door_swings(catlin_model_ro):
    walls = {wall.tag: wall for wall in catlin_model_ro.walls}
    for holder in _holders(catlin_model_ro):
        for depth, low, high in ((6, 23.25, 28.75), (3.34, 25.33, 33.44)):
            envelope = _envelope(holder, depth)
            floor = holder.z_m - 25.33 * IN
            for peer in catlin_model_ro.canvas_objects:
                if (peer.uid == holder.uid or peer.room != holder.room
                        or peer.tag in {holder.host_fixture_ref, holder.tag + "-PAD"}):
                    continue
                if peer.body_z0_m >= floor + high * IN or peer.body_z1_m <= floor + low * IN:
                    continue
                assert envelope.intersection(Polygon(peer.footprint)).area < 1e-7, (
                    holder.tag, peer.tag, depth)
            for door in catlin_model_ro.openings:
                if walls[door.host_wall].storey == holder.storey and door.swing_clearance:
                    assert envelope.intersection(Polygon(door.swing_clearance)).area < 1e-7, (
                        holder.tag, door.tag)


def test_panel_is_raised_and_cabinet_pads_cover_both_post_stations(catlin_plan, catlin_model_ro):
    objects = {obj.tag: obj for obj in catlin_model_ro.canvas_objects}
    panel = catlin_plan.by_tag("FURN-S-BATH1-CH-AP")
    assert panel.uid == "7MW8644E5H"
    assert panel.mount.elevation.inches == pytest.approx(36)
    assert panel.location.attachment.distance_from_start.inches == pytest.approx(9)
    assert catlin_plan.by_tag("BK-S-CH-S-AP").elevation.inches == pytest.approx(34)
    assert objects[panel.tag].body_z0_m > objects["FURN-S-BATH1-TP"].z_m + 8.11 * IN
    pads = [obj for obj in objects.values() if obj.type_ref == "FT-TP-CABINET-BACKING-12"]
    assert len(pads) == 2
    for pad in pads:
        holder = objects[pad.tag.removesuffix("-PAD")]
        vanity = objects[pad.host_fixture_ref]
        assert Polygon(vanity.footprint).buffer(1e-7).covers(Polygon(pad.footprint))
        _, pad_y0, _, pad_y1 = Polygon(pad.footprint).bounds
        for offset in (-3.385, 3.385):
            assert pad_y0 <= holder.position[1] + offset * IN <= pad_y1
        assert pad.body_z0_m < holder.z_m + 0.67 * IN < pad.body_z1_m
        # Pads sit inward of a 3/4 in. cabinet side; their through-fasteners stay on
        # the side panel, clear of the front plane and basin plumbing in the centre.
        assert Polygon(pad.footprint).bounds[0] == pytest.approx(
            Polygon(vanity.footprint).bounds[0] + 0.75 * IN)


def test_new_blocks_do_not_intersect_routed_services(catlin_model_ro):
    from shapely.geometry import LineString, Point

    from typehaus.checks.mep.routing_geometry import crossing_band

    model = catlin_model_ro
    bands = backing_bands(model.plan)
    blocks = []
    for wall in model.walls:
        ordered = sorted(bands.get(wall.tag, ()), key=lambda band: (band.elevation_m, band.tag))
        indices = {index for index, band in enumerate(ordered) if "-TP" in band.tag}
        blocks.extend(member for member in wall.members if any(
            member.child_key.startswith(f"backing-{index}-") for index in indices))
    assert len(blocks) == 5
    sections = run_sections(model)
    for member in blocks:
        outline, bottom, top = member_footprint(member)
        for _, tag, path, heights in run_polylines(model):
            half_width, half_depth, _ = sections[tag]
            footprint = Polygon(outline).buffer(half_width)
            for index, (a, b) in enumerate(zip(path, path[1:], strict=False)):
                za, zb = heights[index:index + 2]
                if a == b:
                    if not footprint.contains(Point(a)):
                        continue
                    low, high = min(za, zb), max(za, zb)
                else:
                    segment = LineString([a, b])
                    crossing = segment.intersection(footprint)
                    if crossing.is_empty:
                        continue
                    low, high = crossing_band(segment, za, zb, crossing)
                assert high + half_depth <= bottom or low - half_depth >= top, (
                    member.parent_uid, member.child_key, tag)


def test_holders_and_pads_are_counted_and_keep_host_in_model_json(catlin_model_ro):
    rows = placeables_takeoff(catlin_model_ro)
    assert sum(row["count"] for row in rows if row["type"] in {"FT-MOEN-ALIGN-TP", "FT-MOEN-ALIGN-TP-CH"}) == 6
    assert sum(row["count"] for row in rows if row["type"] == "FT-TP-CABINET-BACKING-12") == 2
    payload = model_to_dict(catlin_model_ro)
    holders = [obj for obj in payload["canvas_objects"] if obj["type"] in {"FT-MOEN-ALIGN-TP", "FT-MOEN-ALIGN-TP-CH"}]
    assert len(holders) == 6
    assert next(obj for obj in holders if obj["tag"] == "FURN-A-STUBATH-TP")[
        "host_fixture_ref"] == "FX-A-STUBATH-LAV"


def test_host_reference_survives_source_writeback():
    source_path = Path(__file__).resolve().parents[3] / "houses/catlin/plan/bath_accessories.py"
    result = apply_ops_to_source(source_path.read_text(), [PatchOp(
        "update", "Furniture", "FURN-S-SUITEBATH-TP",
        {"position": RawExpr("pt(inch(148.83), inch(248.5))")})])
    assert 'host_fixture_ref="FX-S-SUITEBATH-LAV"' in result.source
    assert "inch(248.5)" in result.source


def test_ifc_keeps_six_furnishing_occurrences_and_cabinet_support(catlin_ifc_path):
    import ifcopenshell
    from ifcopenshell.util.element import get_psets

    model = ifcopenshell.open(str(catlin_ifc_path))
    holders = [obj for obj in model.by_type("IfcFurniture")
               if get_psets(obj).get("TypeHaus_Identity", {}).get("source_type")
               in {"FT-MOEN-ALIGN-TP", "FT-MOEN-ALIGN-TP-CH"}]
    assert len(holders) == 6
    assert all(obj.Representation.Representations[0].RepresentationType == "Tessellation"
               for obj in holders)
    assert all(len(item.CoordIndex) >= 100 for obj in holders
               for item in obj.Representation.Representations[0].Items)
    attic = next(obj for obj in holders if obj.Name == "FURN-A-STUBATH-TP")
    assert get_psets(attic)["TypeHaus_Identity"]["host_fixture_ref"] == "FX-A-STUBATH-LAV"

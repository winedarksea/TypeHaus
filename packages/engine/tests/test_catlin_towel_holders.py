"""Useful towel reach and hanging space, supported fixings, and scheduled hardware."""

from collections import Counter
from types import SimpleNamespace

import pytest
from shapely.geometry import Point, Polygon

from typehaus.checks.advisory.backing import floating_band_ends, wall_backing_present
from typehaus.checks.advisory.backing_fixings import wall_fixing_support
from typehaus.model.placeable_symbols import place_local
from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve.framing.backing_panels import backing_bands
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.mep_envelopes import envelopes
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.takeoff.placeables import placeables_takeoff

HAND = "FT-MOEN-ALIGN-HAND-TOWEL"
BATH = "FT-MOEN-ALIGN-BATH-TOWEL"
HOOK = "FT-MOEN-ALIGN-TOWEL-HOOK"
PAD = "FT-TOWEL-CABINET-BACKING-12"
HAND_CH, BATH_CH, HOOK_CH = (tag + "-CH" for tag in (HAND, BATH, HOOK))
HARDWARE = {HAND, BATH, HOOK, HAND_CH, BATH_CH, HOOK_CH}
# Sink identities make omissions visible, including both basins in the separate alcove.
SINK_HOLDERS = {
    "FX-B-BATH-LAV": "FURN-B-BATH-HAND-TOWEL",
    "FX-M-BATH1-LAV": "FURN-M-BATH1-HAND-TOWEL",
    "FX-M-BATH2-SINK": "FURN-M-BATH2-HAND-TOWEL",
    "FX-S-VANITY-LAV1": "FURN-S-VANITY-HAND-TOWEL1",
    "FX-S-VANITY-LAV2": "FURN-S-VANITY-HAND-TOWEL2",
    "FX-S-BATH1-LAV": "FURN-S-BATH1-HAND-TOWEL",
    "FX-S-SUITEBATH-LAV": "FURN-S-SUITEBATH-HAND-TOWEL",
    "FX-A-STUBATH-LAV": "FURN-A-STUBATH-HAND-TOWEL",
}
SHOWER_HOLDERS = {
    "FX-B-SAUNA-SH": "FURN-B-SAUNA-BATH-TOWEL",
    "FX-M-BATH2-SH": "FURN-M-BATH2-BATH-TOWEL",
    "FX-S-BATH1-SH": "FURN-S-BATH1-BATH-TOWEL",
    "FX-S-SUITEBATH-TUBSH": "FURN-S-SUITEBATH-BATH-TOWEL",
    "FX-A-STUBATH-SH": "FURN-A-STUBATH-BATH-TOWEL",
}


def _hardware(model):
    return [obj for obj in model.canvas_objects if obj.type_ref in HARDWARE]


def _loaded_towel(holder, types):
    width, depth = (v.meters for v in types[holder.type_ref].footprint)
    if holder.type_ref.removesuffix("-CH") == HOOK:
        width, projection, drop = 12 * IN, 6 * IN, 55 * IN
    else:
        projection = 4.5 * IN
        drop = (18 if holder.type_ref.removesuffix("-CH") == HAND else 28) * IN
    polygon = Polygon(
        place_local(
            [
                (-width / 2, depth / 2),
                (width / 2, depth / 2),
                (width / 2, depth / 2 - projection),
                (-width / 2, depth / 2 - projection),
            ],
            holder.position,
            holder.rotation_degrees,
        )
    )
    return polygon, holder.z_m + 0.67 * IN - drop, holder.z_m + 1.34 * IN


def test_each_sink_and_shower_has_reachable_selected_hardware(catlin_plan, catlin_model_ro):
    model = catlin_model_ro
    objects = {o.tag: o for o in model.canvas_objects}
    assert Counter(o.type_ref for o in _hardware(model)) == {
        HAND: 7, HAND_CH: 1, BATH: 3, BATH_CH: 2, HOOK: 1, HOOK_CH: 1}
    bathroom_rooms = {
        r.tag for r in model.rooms if any(word in r.tag for word in ("BATH", "VANITY", "SAUNA"))
    }
    fixture_types = {t.tag: t for t in catlin_plan.library.fixture_types}
    bathroom_sinks = {
        o.tag
        for o in model.canvas_objects
        if o.kind == "Fixture"
        and o.room in bathroom_rooms
        and fixture_types[o.type_ref].basin
    }
    assert bathroom_sinks == set(SINK_HOLDERS)
    bathroom_showers = {
        o.tag for o in model.canvas_objects
        if o.kind == "Fixture" and o.room in bathroom_rooms
        and fixture_types[o.type_ref].plan_symbol in {"shower", "tub-shower", "shower-neo-angle"}
    }
    assert bathroom_showers == set(SHOWER_HOLDERS)
    for sink_tag, holder_tag in SINK_HOLDERS.items():
        sink, holder = objects[sink_tag], objects[holder_tag]
        assert holder.room == sink.room and holder.storey == sink.storey
        assert Polygon(holder.footprint).distance(Polygon(sink.footprint)) <= 30 * IN
    for shower_tag, holder_tag in SHOWER_HOLDERS.items():
        shower, holder = objects[shower_tag], objects[holder_tag]
        assert holder.storey == shower.storey
        assert holder.room == ("RM-B-GYM" if shower_tag == "FX-B-SAUNA-SH" else shower.room)
    types = {t.tag: t for t in catlin_plan.library.furniture_types}
    products = {p.tag: p for p in catlin_plan.library.products}
    assert {products[types[t].product_ref].model for t in HARDWARE} == {
        "YB0486BN",
        "YB0424BN",
        "YB0403BN", "YB0486CH", "YB0424CH", "YB0403CH",
    }
    for holder in _hardware(model):
        assert holder.type_ref.endswith("-CH") == (holder.room == "RM-M-BATH2")
        room = next(r for r in model.rooms if r.tag == holder.room)
        expected = 48 if holder.type_ref.removesuffix("-CH") == HAND else 54 if holder.type_ref.removesuffix("-CH") == BATH else 64
        if holder.host_fixture_ref:
            expected = 32.5 if "SUITEBATH" in holder.tag else 30
        if holder.tag == "FURN-A-STUBATH-BATH-TOWEL":
            expected = 51
        floor = room_finished_floor_elevation(model, room)
        assert (holder.z_m + 0.67 * IN - floor) / IN == pytest.approx(expected)


def test_loaded_towels_clear_bodies_doors_and_each_other(catlin_plan, catlin_model_ro):
    model = catlin_model_ro
    types = {t.tag: t for t in catlin_plan.library.furniture_types}
    walls = {w.tag: w for w in model.walls}
    for holder in _hardware(model):
        polygon, low, high = _loaded_towel(holder, types)
        for peer in model.canvas_objects:
            if (
                peer.uid == holder.uid
                or peer.storey != holder.storey
                or peer.tag in {holder.host_fixture_ref, holder.tag + "-PAD"}
            ):
                continue
            if peer.body_z0_m >= high or peer.body_z1_m <= low:
                continue
            # A wall switch or receptacle under a hung towel is a nuisance, not a clash.
            if peer.kind == "ElectricalDevice" and peer.mount and peer.mount.kind == "wall":
                continue
            assert polygon.intersection(Polygon(peer.footprint)).area < 1e-7, (holder.tag, peer.tag)
        for door in model.openings:
            if walls[door.host_wall].storey == holder.storey and door.swing_clearance:
                assert polygon.intersection(Polygon(door.swing_clearance)).area < 1e-7, (
                    holder.tag,
                    door.tag,
                )
        for peer in _hardware(model):
            if peer.uid == holder.uid or peer.storey != holder.storey:
                continue
            peer_polygon, peer_low, peer_high = _loaded_towel(peer, types)
            if high > peer_low and low < peer_high:
                assert polygon.intersection(peer_polygon).area < 1e-7, (holder.tag, peer.tag)
    # The alcove keeps more than the 21 in. sink-front allowance with towels loaded.
    objects = {o.tag: o for o in model.canvas_objects}
    for sink_tag, holder_tag in SINK_HOLDERS.items():
        if objects[sink_tag].room == "RM-S-VANITY":
            polygon, _, _ = _loaded_towel(objects[holder_tag], types)
            assert polygon.distance(Polygon(objects[sink_tag].footprint)) >= 21 * IN


def test_all_wall_posts_have_support_and_new_courses_fill_their_bays(catlin_ctx):
    findings = [
        f for f in wall_fixing_support(catlin_ctx) if any("TOWEL" in tag for tag in f.element_tags)
    ]
    assert len(findings) == 22
    assert all(f.result.value == "pass" for f in findings), findings
    # A post-supported bar needs no timber behind the free span at its midpoint.
    general_findings = [f for f in wall_backing_present(catlin_ctx)
                        if any("TOWEL" in tag for tag in f.element_tags)]
    assert len(general_findings) == 18  # 15 hardware items and 3 internal pads.
    assert all(f.result.value != "fail" for f in general_findings)
    bands = backing_bands(catlin_ctx.plan)
    emitted = []
    for wall in catlin_ctx.model.walls:
        ordered = sorted(bands.get(wall.tag, ()), key=lambda b: (b.elevation_m, b.tag))
        indices = {i for i, b in enumerate(ordered) if "TOWEL" in b.tag}
        towel_bands = [ordered[i] for i in indices]
        assert not floating_band_ends(wall, towel_bands)
        for band in towel_bands:
            assert band.profile == "2x6" and band.material_ref == "spf"
            holder = next(o for o in _hardware(catlin_ctx.model) if o.tag in band.purpose)
            assert wall.base_ref_z_m + band.elevation_m + band.height_m / 2 == pytest.approx(
                holder.z_m + 0.67 * IN
            )
        blocks = [
            n for n in wall.members if any(n.child_key.startswith(f"backing-{i}-") for i in indices)
        ]
        assert len(blocks) == len(towel_bands)
        emitted.extend(blocks)
        for block in blocks:
            ring, low, high = member_footprint(block)
            for peer in wall.members:
                if peer.category not in {
                    "stud",
                    "corner",
                    "king",
                    "jack",
                    "cripple",
                    "header",
                    "sill",
                }:
                    continue
                peer_ring, peer_low, peer_high = member_footprint(peer)
                if high > peer_low + 1e-7 and low < peer_high - 1e-7:
                    assert Polygon(ring).intersection(Polygon(peer_ring)).area < 1e-7, (
                        wall.tag,
                        block.child_key,
                        peer.child_key,
                    )
    assert len(emitted) == 13
    services = envelopes(catlin_ctx.model)
    for block in emitted:
        ring, low, high = member_footprint(block)
        for service in services:
            for segment in service.prisms:
                if high > segment.z0_m and low < segment.z1_m:
                    assert Polygon(ring).intersection(segment.footprint).area < 1e-8, (
                        block.parent_uid,
                        block.child_key,
                        service.tag,
                    )


def test_cabinet_pads_cover_both_posts_inside_vanity_sides(catlin_plan, catlin_model_ro):
    objects = {o.tag: o for o in catlin_model_ro.canvas_objects}
    types = {t.tag: t for t in catlin_plan.library.furniture_types}
    pads = [o for o in objects.values() if o.type_ref == PAD]
    assert len(pads) == 3
    for pad in pads:
        holder = objects[pad.tag.removesuffix("-PAD")]
        vanity = objects[pad.host_fixture_ref]
        assert holder.host_fixture_ref == vanity.tag
        assert Polygon(vanity.footprint).buffer(1e-7).covers(Polygon(pad.footprint))
        assert pad.body_z0_m < holder.z_m + 0.67 * IN < pad.body_z1_m < vanity.body_z1_m
        for offset, _ in types[HAND].wall_fixing_points:
            # Project through the side onto the interior pad, 1.125 in. inside the side.
            fixing = place_local(
                [(offset.meters, (3.33 / 2 + 1.125) * IN)], holder.position, holder.rotation_degrees
            )[0]
            assert Polygon(pad.footprint).buffer(1e-7).covers(Point(fixing))
        # Pads and fixings keep clear of the front plane used by cabinet doors/drawers.
        assert holder.rotation_degrees % 360 in {0, 180, 270}
        for peer in objects.values():
            if peer.type_ref == "FT-TP-CABINET-BACKING-12" and peer.host_fixture_ref == vanity.tag:
                assert pad.body_z0_m >= peer.body_z1_m


def test_takeoff_and_ifc_include_all_towel_hardware(catlin_model_ro, catlin_ifc_path):
    import ifcopenshell
    from ifcopenshell.util.element import get_psets

    expected = {HAND: 7, HAND_CH: 1, BATH: 3, BATH_CH: 2, HOOK: 1, HOOK_CH: 1, PAD: 3}
    rows = placeables_takeoff(catlin_model_ro)
    assert {t: sum(r["count"] for r in rows if r["type"] == t) for t in expected} == expected
    model = ifcopenshell.open(str(catlin_ifc_path))
    furniture = [
        (o, get_psets(o).get("TypeHaus_Identity", {})) for o in model.by_type("IfcFurniture")
    ]
    assert (
        Counter(
            identity.get("source_type")
            for _, identity in furniture
            if identity.get("source_type") in expected
        )
        == expected
    )
    for obj, identity in furniture:
        if identity.get("source_type") in HARDWARE:
            assert obj.Representation.Representations[0].RepresentationType == "Tessellation"
            assert all(len(item.CoordIndex) >= 100
                       for item in obj.Representation.Representations[0].Items)
        if identity.get("source_type") == PAD:
            assert identity.get("host_fixture_ref")


def test_bath2_tub_bars_are_centred_separate_and_above_the_rim(catlin_model_ro):
    objects = {o.tag: o for o in catlin_model_ro.canvas_objects}
    tub = objects["FX-M-BATH2-TUB"]
    bars = [objects["FURN-M-BATH2-TUB-TOWEL-" + end] for end in ("S", "N")]
    assert [bar.position[1] / IN for bar in bars] == pytest.approx([218.615, 246.615])
    assert sum(bar.position[1] for bar in bars) / 2 == pytest.approx(tub.position[1])
    assert Polygon(bars[0].footprint).distance(Polygon(bars[1].footprint)) / IN == pytest.approx(2.66)
    for bar in bars:
        assert bar.type_ref == BATH_CH
        assert bar.z_m + 0.67 * IN - 28 * IN > tub.body_z1_m
    assert bars[0].attachment_wall == "W-M-BA2E"
    assert any(tag == "W-M-BA2E2" for finding in wall_fixing_support(
        SimpleNamespace(plan=catlin_model_ro.plan, model=catlin_model_ro))
        if bars[0].tag in finding.element_tags for tag in finding.element_tags)

"""Selected north connector geometry, real framing, finish and retired quantities."""

import pytest
from shapely.geometry import Polygon, box

from typehaus import FloorSystem, ft, inch
from typehaus.resolve.ceiling_over import decks_covering


def test_the_old_concrete_and_glazed_connector_is_retired(catlin_plan):
    for tag in ("SL-G-STEP-0", *(f"{prefix}-BW-{i}" for prefix in ("PD", "PR", "PT")
                                 for i in range(1, 5)),
                "GL-BW-WALL-W", "GL-BW-WALL-E", "GL-BW-ROOF", "RL-BW-WEST"):
        assert catlin_plan.by_tag(tag) is None, tag
    # BM-BW-RW/-RE came BACK on 2026-09-10 as the canopy's two roof headers -- the same tags
    # the glazed breezeway used, deliberately reused for the same bearing lines.
    for tag in ("BM-BW-RW", "BM-BW-RE", "PT-BW-W", "PT-BW-E", "PT-BW-RE", "RF-BW-CANOPY"):
        assert catlin_plan.by_tag(tag) is not None, tag
    # No invented part numbers survive anywhere.
    assert not [c for c in catlin_plan.all_elements()
                if "BW-ENGINEERED" in (getattr(c, "size", None) or "")]
    assert catlin_plan.by_tag("FS-BW-FLOOR").uid == "BWFS01AAAA"
    assert catlin_plan.by_tag("ST-G-SERVICE").uid == "X99TD38ZS3"


def test_finished_boards_and_both_stairs_meet_both_sills(catlin_model_ro):
    model = catlin_model_ro
    floors = {f.tag: f for f in model.floors}
    for tag in ("FS-BW-FLOOR",):
        floor = floors[tag]
        assert floor.deck_z1_m == pytest.approx(0)
        assert floor.deck_z0_m == pytest.approx(-inch(0.94).meters)
        assert all(m.z1_m == pytest.approx(-inch(0.94).meters) for m in floor.members)
    # The garage flight rises 34" off the slab; the entry flight 33" off SL-WK-C, 1" over grade.
    for tag, rise_in in (("ST-BW-ENTRY", 33), ("ST-G-SERVICE", 34)):
        stair = next(s for s in model.stairs if s.tag == tag)
        assert stair.arrival_elevation_m == pytest.approx(0)
        assert stair.riser_count == 5
        assert stair.riser_height_m == pytest.approx(inch(rise_in).meters / 5)
    for tag in ("D-M-ENTRY", "D-G-SERVICE"):
        door = next(o for o in model.openings if o.tag == tag)
        wall = next(w for w in model.walls if w.tag == door.host_wall)
        assert model.plan.storey(wall.storey).elevation.meters + door.sill_m == pytest.approx(0)


def test_both_full_door_landing_patches_fit_the_shared_deck(catlin_plan):
    floor = catlin_plan.by_tag("FS-BW-FLOOR")
    surface = Polygon([p.xy_m for p in floor.subfloor_outline])
    house_face = ft(36, 7.25).meters
    garage_face = ft(43, 1.75).meters
    # ** THE BOARDS ARE HELD 1/2" OFF THE CLADDING ON PURPOSE (2026-09-10). ** Run tight to a
    # rainscreened wall they dam the drainage plane and hold water against it. Abutting was
    # never bearing, so the gap costs the landing nothing structurally -- but the 36" patch
    # R311.3 wants is measured from where the DECK starts, not from the wall.
    deck_south = house_face + ft(0, 0.5).meters
    assert surface.buffer(1e-8).covers(box(ft(6.5).meters, deck_south,
                                         ft(9.5).meters, deck_south + ft(3).meters))
    # The 32in service opening is now 6'-11"..9'-7"; its east jamb and the deck edge
    # stay fixed. The retained deck also covers the former, wider 36in landing patch.
    assert surface.buffer(1e-8).covers(box(
        ft(6, 7).meters, garage_face - ft(0, 0.5).meters - ft(3).meters,
        ft(9, 7).meters, garage_face - ft(0, 0.5).meters))
    assert max(p.y.meters for p in floor.subfloor_outline) == pytest.approx(
        garage_face - inch(0.5).meters)
    assert max(p.x.meters for p in floor.subfloor_outline) == pytest.approx(ft(9, 7).meters)


def test_the_service_flight_rises_to_the_threshold_with_no_interior_landing(catlin_model_ro):
    """D-G-SERVICE swings OUT since 2026-10-13 (IRC R311.7.6 exception), so the interior
    landing and everything under it retired, and nothing of the deck crosses W-G-S."""
    model = catlin_model_ro
    for gone in ("FS-BW-GARAGE", "BM-BW-FC", "BM-BW-LAND-HDR", "PT-BW-IC", "PT-BW-IE",
                 "CN-BW-IBASE-C", "CN-BW-IBASE-E", "CN-BW-HGR-FC", "CN-BW-HGR-FE",
                 "RL-BW-GARAGE-E", "RL-BW-GARAGE-W"):
        assert model.plan.by_tag(gone) is None, gone
    door = model.plan.by_tag("D-G-SERVICE")
    assert door.flip_swing and door.flip_hinge
    stair = next(s for s in model.stairs if s.tag == "ST-G-SERVICE")
    # The stringers stop at the head riser's board, which stands against W-G-S's gyp face.
    gyp_face = ft(43, 9.375).meters
    assert min(m.p1[1] for m in stair.members if m.category == "stringer") == pytest.approx(
        gyp_face + ft(0, 0.75).meters)
    # FE is the deck's east edge beam, seat to seat, its tip at the garage's cladding face.
    edge = model.plan.by_tag("BM-BW-FE")
    assert set(edge.bearing_refs) == {"BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"}
    assert not edge.engineering_note
    tip = max(model.plan.by_tag(n).position.y.meters for n in (edge.start_node, edge.end_node))
    assert tip == pytest.approx(ft(43, 1.75).meters)


def test_service_door_narrowing_retains_stair_and_clears_exterior_guard(catlin_plan):
    stair = catlin_plan.by_tag("ST-G-SERVICE")
    assert stair.width.meters / inch(1).meters == pytest.approx(36)
    assert stair.start.x.meters / inch(1).meters == pytest.approx(83.625)
    guard = catlin_plan.by_tag("RL-BW-ENTRY")
    assert min(point.x.meters for point in guard.path) / inch(1).meters == pytest.approx(116.5)
    door = catlin_plan.by_tag("D-G-SERVICE")
    assert door.header_spec == '3-ply 5.5" LVL'


def test_tiers_are_cast_pours_at_an_18in_going_over_a_clear_lower_landing(catlin_model_ro):
    """The tiers are four CAST pours, and this pins the two things that must move together.

    A cut stringer failed three ways here: an 8'-0" horizontal span against DCA 6 Fig. 28 /
    IRC R507.13.1's 6'-0", a 4.71" throat against its 5", and a composite tread wanting
    supports closer than 12". Narrowing the going to 18" fixes the span and does NOT fix the
    throat -- the notch is driven by the long going, so a flatter pitch removes MORE
    material. Framed box tiers replaced it and lasted one afternoon: their eight 42" piers
    were laid out running EAST from the stair foot while the flight runs WEST, so every one
    of them stood under open ground.

    So: no stringer, no framing, no pier. Four `Slab` pours, WEDDING-CAKED -- each running
    from the landing edge to the front of its own tread, so every tier above the first is
    fully bedded on the one below and nothing spans. The treads still resolve, because that
    is what every code rule grading this flight measures.
    """
    model = catlin_model_ro
    stair = next(s for s in model.stairs if s.tag == "ST-BW-ENTRY")
    treads = [m for m in stair.members if m.category == "tread"]
    assert len(treads) == 4
    assert {m.material for m in treads} == {"concrete"}
    # Not one member of this flight is a carriage. The drawings and the takeoff read the field.
    assert not [m for m in stair.members if m.category in ("stringer", "landing_framing")]
    assert stair.tread_depth_m == pytest.approx(inch(18).meters)

    # And the pours themselves: four, one riser thick, each starting at the landing edge and
    # ending one going further east than the tier above it.
    tiers = [model.plan.by_tag(f"SL-BW-TIER{n}") for n in (1, 2, 3, 4)]
    assert all(t is not None for t in tiers)
    assert {round(t.thickness.meters, 6) for t in tiers} == {round(inch(6.6).meters, 6)}
    fronts = [max(p.x.meters for p in t.outline) for t in tiers]
    assert fronts == sorted(fronts, reverse=True), "the cake is not stepping west"
    for lower, upper in zip(fronts, fronts[1:], strict=False):
        assert lower - upper == pytest.approx(inch(18).meters)
    # The landing's east edge is the service door's east jamb since 2026-09-11 (9'-7", was
    # 11'-6"), and the stair foot followed it west to 15'-7".
    assert {round(min(p.x.meters for p in t.outline), 6) for t in tiers} == {
        round(ft(9, 7).meters, 6)}, "a tier that does not reach the landing is not bedded"

    # No pier survives under the flight, and the entry walk starts at its foot, 1/2" off
    # tier 1, at the very elevation the flight springs from.
    assert not [e for e in model.plan.all_elements()
                if getattr(e, "tag", "").startswith("PT-BW-T")]
    walk = model.plan.by_tag("SL-WK-C")
    assert min(p.x.meters for p in walk.outline) == pytest.approx(ft(15, 7.5).meters)
    assert max(p.x.meters for p in walk.outline) >= ft(20, 7).meters
    assert walk.top_elevation.meters == pytest.approx(stair.base_elevation_m)


def test_the_single_garage_slab_cannot_become_a_basement_ceiling(catlin_plan):
    slab = catlin_plan.by_tag("SL-G-FLOOR")
    assert not decks_covering(box(0, 0, ft(36).meters, ft(36).meters),
                             [(catlin_plan.storey("garage"), slab)])


def test_all_connector_floor_bearings_resolve(catlin_model_ro):
    for tag in ("FS-BW-FLOOR",):
        system = catlin_model_ro.plan.by_tag(tag)
        assert isinstance(system, FloorSystem)
        assert all(catlin_model_ro.plan.by_tag(ref) is not None
                   for ref in system.joists.bearing_refs)
        assert any(f.tag == tag and f.members for f in catlin_model_ro.floors)


def test_west_header_equal_tails_preserve_the_canopy_bearing_run(catlin_plan, catlin_model_ro):
    from typehaus.resolve.roof_bearing import roof_bearing

    beam = catlin_plan.by_tag("BM-BW-RW")
    south = catlin_plan.by_tag(beam.start_node).position.y.meters
    north = catlin_plan.by_tag(beam.end_node).position.y.meters
    south_post = catlin_plan.by_tag("PT-BW-CW").position.y.meters
    north_post = catlin_plan.by_tag("PT-BW-CNW").position.y.meters
    assert south_post - south == pytest.approx(north - north_post)
    assert south_post - south == pytest.approx(inch(8.875).meters)
    assert south - inch(439.25).meters == pytest.approx(inch(1.875).meters)
    assert catlin_plan.by_tag("CN-BW-CAP-W").size == "AC6Z"
    assert catlin_plan.by_tag("CN-BW-CAP-NW").size == "AC6Z"
    bearing = roof_bearing(catlin_model_ro, beam.tag)
    assert bearing.axis[0][1] == pytest.approx(inch(447.25).meters)
    assert bearing.axis[1][1] == pytest.approx(inch(518.625).meters)
    assert north - south == pytest.approx(inch(77.5).meters)


def test_shared_trex_surfaces_supports_and_stem_seats(catlin_model_ro):
    from typehaus.library import TREX_ENHANCE_BASICS_DECK_LAYER
    from typehaus.takeoff.framing import framing_takeoff
    from typehaus.takeoff.stairs import stair_tread_takeoff

    model = catlin_model_ro
    for tag, top_in in (("FS-BW-FLOOR", 0), ("FS-SG-PORCH", 0.94)):
        system = model.plan.by_tag(tag)
        assert system.subfloor == TREX_ENHANCE_BASICS_DECK_LAYER
        resolved = next(f for f in model.floors if f.tag == tag)
        assert resolved.deck_z1_m == pytest.approx(inch(top_in).meters)
    for tag, top_in in (("BM-BW-HOUSE-SEAT", -8.19), ("BM-BW-GARAGE-SEAT", -8.19)):
        solid = next(s for s in model.solids if s.tag == tag)
        assert solid.z1_m == pytest.approx(inch(top_in).meters)
    for tag in ("PT-BW-W", "PT-BW-E", "PT-BW-GW", "PT-BW-GE"):
        solid = next(s for s in model.solids if s.tag == tag)
        assert solid.z1_m == pytest.approx(inch(-15.44).meters)
    stair = next(s for s in model.stairs if s.tag == "ST-G-SERVICE")
    stringers = [m for m in stair.members if m.category == "stringer"]
    assert len(stringers) == 5
    xs = sorted(m.p1[0] for m in stringers)
    assert max(b-a for a,b in zip(xs, xs[1:], strict=False)) <= inch(9).meters + 1e-9
    seats = [e for e in model.plan.all_elements() if e.tag.startswith("CN-G-STR-SEAT-")]
    assert len(seats) == len(stringers)
    assert sorted(e.position.x.meters for e in seats) == pytest.approx(xs)
    for seat in seats:
        host = model.wall(seat.connects[1])
        assert min(x for x,y in host.axis) <= seat.position.x.meters <= max(x for x,y in host.axis)
    treads = [m for m in stair.members if m.category == "tread"]
    assert len(treads) == 4
    assert {m.material for m in treads} == {"trex-enhance-basics"}
    assert all(m.z1_m-m.z0_m == pytest.approx(inch(0.94).meters) for m in treads)
    sill = next(m for m in model.wall("W-G-S").members if m.child_key == "sill-0")
    assert sill.material == "kdat" and sill.z1_m == pytest.approx(0)
    [order] = [r for r in stair_tread_takeoff(model) if r["stair"] == stair.tag]
    assert (order["material"], order["pieces"], order["thickness_in"]) == (
        "trex-enhance-basics", 4, 0.94)
    assert order["area_sqft"] == 11
    assert not [r for r in framing_takeoff(model) if r["material"] == "trex-enhance-basics"]

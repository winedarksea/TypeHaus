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
    for tag in ("FS-BW-FLOOR", "FS-BW-GARAGE"):
        floor = floors[tag]
        assert floor.deck_z1_m == pytest.approx(0)
        assert floor.deck_z0_m == pytest.approx(-inch(1).meters)
        assert all(m.z1_m == pytest.approx(-inch(1).meters) for m in floor.members)
    for tag in ("ST-BW-ENTRY", "ST-G-SERVICE"):
        stair = next(s for s in model.stairs if s.tag == tag)
        assert stair.arrival_elevation_m == pytest.approx(0)
        assert stair.riser_count == 5
        assert stair.riser_height_m == pytest.approx(inch(34).meters / 5)
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
    assert surface.buffer(1e-8).covers(box(ft(8.5).meters, garage_face - ft(3).meters,
                                         ft(11.5).meters, garage_face))


def test_interior_landing_has_three_clear_feet_and_real_continuing_beams(catlin_model_ro):
    model = catlin_model_ro
    floor = model.plan.by_tag("FS-BW-GARAGE")
    y_end = max(p.y.meters for p in floor.subfloor_outline)
    assert y_end - ft(43, 13.625).meters == pytest.approx(ft(3).meters)
    stair = next(s for s in model.stairs if s.tag == "ST-G-SERVICE")
    assert min(m.p1[1] for m in stair.members if m.category == "stringer") == pytest.approx(y_end)
    for tag in floor.joists.bearing_refs:
        beam = model.plan.by_tag(tag)
        # No `engineering_note` any more: the escape that turned one into a delegated
        # ENGINEERED finding is deleted, and these beams are graded prescriptively now.
        assert not beam.engineering_note
        # Their tips are POSTED, ending the 4'-2" interior cantilever that broke R507.5.1.
        assert set(beam.bearing_refs) == {"BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT",
                                          f"PT-BW-I{tag[-1]}"}
        end = model.plan.by_tag(beam.end_node).position
        assert end.y.meters == pytest.approx(y_end)
        assert ft(8.5).meters < end.x.meters < ft(11.5).meters


def test_tiers_are_box_frames_at_an_18in_going_over_a_clear_lower_landing(catlin_model_ro):
    """The tiers are BOXES now, not a cut carriage, and the paver landing followed them west.

    A cut stringer failed three ways here: an 8'-0" horizontal span against DCA 6 Fig. 28 /
    IRC R507.13.1's 6'-0", a 4.71" throat against its 5", and a composite tread wanting
    supports closer than 12". Narrowing the going to 18" fixes the span and does NOT fix the
    throat -- the notch is driven by the long going, so a flatter pitch removes MORE material.
    """
    model = catlin_model_ro
    stair = next(s for s in model.stairs if s.tag == "ST-BW-ENTRY")
    treads = [m for m in stair.members if m.category == "tread"]
    assert len(treads) == 4
    assert {m.material for m in treads} == {"composite-deck"}
    # Not one member of this flight is a stringer. The drawings and the takeoff read the field.
    assert not [m for m in stair.members if m.category == "stringer"]
    boxes = [m for m in stair.members if m.category == "landing_framing"]
    assert boxes, "the box tiers resolved no framing"
    # Tread supports at 9" o.c. max -- the STAIR rating of a capped composite board, which
    # runs 8"-12" across the brands against 16" for the same board as decking.
    joists = [m for m in boxes if "joist" in m.child_key]
    ys = sorted({round(m.p0[1], 6) for m in joists})
    assert max(b - a for a, b in zip(ys, ys[1:], strict=False)) <= inch(9).meters + 1e-8
    assert stair.tread_depth_m == pytest.approx(inch(18).meters)
    landing = next(s for s in model.plan.project.site.impervious_surfaces if "paver landing" in s.label)
    assert min(p.x.meters for p in landing.outline) == pytest.approx(ft(17.5).meters)
    assert max(p.x.meters for p in landing.outline) >= ft(22.5).meters


def test_the_single_garage_slab_cannot_become_a_basement_ceiling(catlin_plan):
    slab = catlin_plan.by_tag("SL-G-FLOOR")
    assert not decks_covering(box(0, 0, ft(36).meters, ft(36).meters),
                             [(catlin_plan.storey("garage"), slab)])


def test_all_connector_floor_bearings_resolve(catlin_model_ro):
    for tag in ("FS-BW-FLOOR", "FS-BW-GARAGE"):
        system = catlin_model_ro.plan.by_tag(tag)
        assert isinstance(system, FloorSystem)
        assert all(catlin_model_ro.plan.by_tag(ref) is not None
                   for ref in system.joists.bearing_refs)
        assert any(f.tag == tag and f.members for f in catlin_model_ro.floors)

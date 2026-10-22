"""``WallPaneling`` bands as drawable geometry.

A band billed and was never drawn: ``resolve/paneling.py`` computed the wall, the run and the
band height, kept the area and threw the rectangle away, so a wainscot appeared on the order
and nowhere in the model. These pin the geometry that fixes that, and — more importantly — pin
it *against the area the resolver already computed*, so the polygon can never drift away from
the number that gets ordered.

The side matters as much as the size. A band is an applied surface on the ROOM side of its
wall, and catlin's bands sit on walls whose room is on opposite sides of the axis, so a sign
error shows up here rather than in a screenshot nobody takes.
"""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Polygon

_M2_TO_FT2 = 10.7639104
_IN = 0.0254


@pytest.fixture(scope="module")
def bands(catlin_model):
    return list(catlin_model.panelings)


def _edges(outline) -> list[float]:
    return [math.dist(outline[i], outline[(i + 1) % len(outline)])
            for i in range(len(outline))]


def test_every_room_scoped_band_resolves_geometry(bands):
    """No room-scoped band may bill without a rectangle to draw."""
    room_scoped = [b for b in bands if b.room is not None]
    assert room_scoped, "catlin authors room-scoped paneling; the fixture found none"
    for band in room_scoped:
        assert len(band.outline) == 4, f"{band.tag} on {band.wall_tag} is not a rectangle"
        assert band.z0_m is not None and band.z1_m is not None, \
            f"{band.tag} on {band.wall_tag} has a polygon but no elevations"
        assert band.z1_m > band.z0_m, f"{band.tag} on {band.wall_tag} spans no height"


def test_the_rectangle_is_the_run_by_the_thickness(bands):
    """The long edge is the band's run along the wall; the short edge is its thickness.

    This is what makes the polygon *the same band* the area was measured on, rather than a
    rectangle that merely happens to be near the wall.
    """
    for band in (b for b in bands if b.outline):
        long_edge, short_edge = max(_edges(band.outline)), min(_edges(band.outline))
        assert long_edge == pytest.approx(band.run_m, abs=1e-6), \
            f"{band.tag} on {band.wall_tag}: long edge is not the billed run"
        assert short_edge == pytest.approx(band.thickness_m, abs=1e-6), \
            f"{band.tag} on {band.wall_tag}: short edge is not the band thickness"


def test_the_drawn_band_agrees_with_the_billed_area(bands, catlin_model):
    """run x band height, reconciled against ``area_m2`` plus the openings it subtracts.

    ``area_m2`` is net of the openings punching the band and the gross outline is not, so the
    two reconcile through the openings rather than being equal. Pinning it this way is what
    stops the polygon and the order drifting apart: change either one alone and this fails.
    """
    for band in (b for b in bands if b.outline):
        height = band.z1_m - band.z0_m
        gross = band.run_m * height
        assert gross >= band.area_m2 - 1e-9, \
            f"{band.tag} on {band.wall_tag}: billed more than the band's gross area"
        wall = catlin_model.wall(band.wall_tag)
        punched = 0.0
        for opening in catlin_model.openings:
            if opening.host_wall != band.wall_tag:
                continue
            # The band's own frame: wall-local z up from the wall's base reference.
            b0 = band.z0_m - wall.base_ref_z_m
            b1 = band.z1_m - wall.base_ref_z_m
            dz = min(b1, opening.sill_m + opening.height_m) - max(b0, opening.sill_m)
            if dz > 0.0:
                punched += min(opening.width_m, band.run_m) * dz
        assert gross - band.area_m2 <= punched + 1e-6, \
            f"{band.tag} on {band.wall_tag}: more area subtracted than its openings punch"


def test_the_drawn_pieces_are_the_billed_area(bands):
    """``pieces`` is the band net of its openings: face area summed equals ``area_m2``."""
    for band in (b for b in bands if b.outline):
        drawn = sum(max(_edges(ring)) * (z1 - z0) for ring, z0, z1 in band.pieces)
        assert drawn == pytest.approx(band.area_m2, abs=1e-6), \
            f"{band.tag} on {band.wall_tag}: drawn pieces disagree with the billed area"


def test_the_study_wainscot_stops_at_its_door(bands, catlin_model):
    """No piece of the walnut may cross D-M-STUDY — the gross rectangle was drawn across it."""
    door = next(o for o in catlin_model.openings if o.tag == "D-M-STUDY")
    wall = catlin_model.wall(door.host_wall)
    hole = Polygon(_band_outline_of(wall, door)).buffer(-1e-4)
    host = [b for b in bands if b.tag == "WP-M-STUDY-WAINSCOT" and b.wall_tag == wall.tag]
    assert host and len(host[0].pieces) == 2, "the door splits the band in two"
    for ring, _, _ in host[0].pieces:
        assert not Polygon(ring).intersects(hole), "a wainscot piece crosses D-M-STUDY"


def _band_outline_of(wall, opening):
    """The opening's plan footprint across the whole wall depth."""
    from typehaus.resolve.geometry import add, rect_between, scale, sub, unit

    d = unit(sub(wall.axis[1], wall.axis[0]))
    a = add(wall.axis[0], scale(d, opening.center_along_m - opening.width_m / 2.0))
    b = add(wall.axis[0], scale(d, opening.center_along_m + opening.width_m / 2.0))
    return rect_between(a, b, -0.5, 0.5)


def test_a_band_sits_on_its_room_side_of_the_wall(bands, catlin_model):
    """The whole rectangle lies on the room's side of the wall axis, not the far side.

    Graded against the room's AXIS cell: a replacing band sits in the finish depth, which is
    outside the clear face (that is the finish face itself) but inside the axis cell.
    """
    faces = {room.tag: Polygon(room.axis_face) for room in catlin_model.rooms}
    for band in (b for b in bands if b.outline and b.room):
        face = faces[band.room]
        centroid = Polygon(band.outline).centroid
        assert face.distance(centroid) == pytest.approx(0.0, abs=1e-6), \
            f"{band.tag} on {band.wall_tag} sits on the far side of its wall"


def test_a_replacing_band_occupies_the_finish_it_replaces(bands):
    """``replaces_wall_finish`` sits IN the wall's finish depth; an added band stands proud.

    The sauna splash replaces the basswood liner over two 3' stretches; the study wainscot is
    laid over a finished wall. Drawing both the same way puts one of them in the wrong place —
    a floating tile field, or a wainscot buried in the drywall.
    """
    splash = [b for b in bands if b.tag == "WP-B-SAUNA-SPLASH"]
    wainscot = [b for b in bands if b.tag == "WP-M-STUDY-WAINSCOT"]
    assert splash and wainscot, "catlin authors both a replacing and an added band"
    assert all(b.replaces_wall_finish for b in splash)
    assert not any(b.replaces_wall_finish for b in wainscot)


def test_band_thickness_comes_from_the_material_stock(bands):
    """4/4 walnut draws 3/4" — nominal stock, dressed. Tile has no stock and takes the default.

    ``stock_bf_per_sqft`` is board feet per square foot on nominal thickness, so it doubles as
    the nominal inches; stock under 2" dresses 1/4" thinner.
    """
    for band in bands:
        if band.tag == "WP-M-STUDY-WAINSCOT":
            assert band.thickness_m == pytest.approx(0.75 * _IN, abs=1e-6), \
                "4/4 walnut wainscot draws at its dressed 3/4in"
        if band.tag == "WP-B-SAUNA-SPLASH":
            assert band.thickness_m == pytest.approx(0.5 * _IN, abs=1e-6), \
                "tile states no board stock, so the band takes the default"


def test_the_catlin_bands_are_the_nine_authored_ones(bands, catlin_model):
    """A guard on scope: the reference house authors exactly these, at these heights."""
    by_tag: dict[str, list] = {}
    for band in bands:
        by_tag.setdefault(band.tag, []).append(band)
    assert set(by_tag) == {"WP-B-SAUNA-SPLASH", "WP-M-STUDY-WAINSCOT", "WP-M-STUDY-FELT",
                           "WP-M-BATH2-SURR", "WP-S-SUITE-HEADBOARD", "WP-A-STUBATH-SURR",
                           "WP-M-MUDROOM-SHIPLAP", "WP-M-KIT-BACKSPLASH",
                           "WP-M-BATH2-TUBDK-APRON"}
    # The range backsplash: an authored sheet thickness wins over the material's stock.
    (splash,) = by_tag["WP-M-KIT-BACKSPLASH"]
    assert splash.thickness_m == pytest.approx(0.0008, abs=1e-9)
    assert splash.run_m == pytest.approx(1.0, abs=1e-6)
    # The mudroom's three east-facing walls to 6'-0"; W-M-MECH-E is the L's inner-corner
    # wall that a single room-wide interior point once put on the closet's face.
    assert {b.wall_tag for b in by_tag["WP-M-MUDROOM-SHIPLAP"]} == {
        "W-M-W1", "W-M-MECH-E", "W-M-MUDC-E"}
    for band in by_tag["WP-M-MUDROOM-SHIPLAP"]:
        assert band.z1_m - band.z0_m == pytest.approx(72 * _IN, abs=1e-6)
        assert band.thickness_m == pytest.approx(0.75 * _IN, abs=1e-6)
    # Two 3' spans on two walls of the shower corner, full 7'-6" liner height.
    assert len(by_tag["WP-B-SAUNA-SPLASH"]) == 2
    for band in by_tag["WP-B-SAUNA-SPLASH"]:
        assert band.run_m == pytest.approx(3 * 12 * _IN, abs=1e-6)
        assert band.z1_m - band.z0_m == pytest.approx(90 * _IN, abs=1e-3)
    # North walnut is replaced by the upholstered bench; exposed returns remain.
    assert {b.wall_tag for b in by_tag["WP-M-STUDY-WAINSCOT"]} == {
        "W-M-C3", "W-M-LS", "W-M-CLN2"}
    for band in by_tag["WP-M-STUDY-WAINSCOT"]:
        assert band.z1_m - band.z0_m == pytest.approx(36 * _IN, abs=1e-6)
    # The call booth's felt: south and north walls only, and the band runs 3'-0" to 9'-0".
    # ``height`` is a band HEIGHT added to ``offset``, not a top elevation
    # (resolve/paneling.py) — this is the assertion that catches an author who reads it as
    # one, because ft(9) would resolve here too, but only because the clamp caught it.
    assert len(by_tag["WP-M-STUDY-FELT"]) == 2
    assert {b.wall_tag for b in by_tag["WP-M-STUDY-FELT"]} == {"W-M-CLN2", "W-M-HS4"}
    for band in by_tag["WP-M-STUDY-FELT"]:
        assert band.z0_m == pytest.approx(36 * _IN, abs=1e-6)
        # 107 3/8", not the storey's 108": ``resolve/paneling.py`` clamps a band to the
        # wall's TOP PLATE, and an interior partition's plate now stops 3/4" under the
        # joist soffit over it (``resolve/partition_top.py``). The felt stops where the
        # drywall beside it stops, which is the point of clamping to the plate at all.
        assert band.z1_m == pytest.approx(107.375 * _IN, abs=1e-6)
        assert not band.replaces_wall_finish
        # PET felt states no board stock, so it takes the 1/2" default — which is the panel.
        assert band.thickness_m == pytest.approx(0.5 * _IN, abs=1e-6)
    # RM-M-BATH2's shower surround: the 36" pan's two closed sides, 3'-0" each, floor to
    # ceiling. The walls are W-M-BA2E2 and W-M-BDN1 and NOT W-M-BA2E — FX-M-BATH2-SH's
    # `wall_ref` names the riser's wall, which stops four feet NORTH of the pan (it runs
    # y 18'-0"..22'-4"), so it is not a wall this band can land on. That is the trap this
    # assertion exists to hold.
    closed = [b for b in by_tag["WP-M-BATH2-SURR"] if b.wall_tag != "W-M-TUBDK-S"]
    assert {b.wall_tag for b in closed} == {"W-M-BA2E2", "W-M-BDN1"}
    for band in closed:
        assert band.run_m == pytest.approx(3 * 12 * _IN, abs=1e-6)
        assert band.z0_m == pytest.approx(0.0, abs=1e-6)
        # Floor to ceiling since 2026-10-12: RM-M-BATH2's 106" clear height.
        assert band.z1_m == pytest.approx(106 * _IN, abs=1e-6)
        assert band.replaces_wall_finish
        # A cast panel states no board stock, so it takes the 1/2" default — which is,
        # again, the panel's own thickness.
        assert band.thickness_m == pytest.approx(0.5 * _IN, abs=1e-6)
    # The third span (2026-10-12): the tub deck's knee wall below the north glass, over the
    # pan's 3' only. It stands INSIDE the room, so the span names its face; the band is on
    # the stall (south) side and clamps to the wall's 3/4"..20" body.
    (knee,) = [b for b in by_tag["WP-M-BATH2-SURR"] if b.wall_tag == "W-M-TUBDK-S"]
    assert knee.run_m == pytest.approx(3 * 12 * _IN, abs=1e-3)
    assert (knee.z0_m, knee.z1_m) == pytest.approx((0.75 * _IN, 20 * _IN), abs=1e-6)
    wall = next(w for w in catlin_model.walls if w.tag == "W-M-TUBDK-S")
    assert Polygon(knee.outline).centroid.y < wall.axis[0][1]
    # RM-S-SUITE's headboard band (2026-09-05): the walnut that was briefly the suite FLOOR,
    # stood up behind the bed on the two staggered-stud sound walls between the suite and the
    # vanity. Two walls and not the room's other six — `walls=` is what keeps the band off
    # W-S-W3, whose two flush elm tudor posts the model cannot scribe around — and the band
    # is 0 to 6'-0", `height` again being a band height and not a top elevation.
    assert len(by_tag["WP-S-SUITE-HEADBOARD"]) == 2
    assert {b.wall_tag for b in by_tag["WP-S-SUITE-HEADBOARD"]} == {"W-S-SN1", "W-S-SN2"}
    # ``z0_m``/``z1_m`` here are ABSOLUTE, so the second storey's 10'-0" datum is in them.
    for band in by_tag["WP-S-SUITE-HEADBOARD"]:
        assert band.z1_m - band.z0_m == pytest.approx(72 * _IN, abs=1e-6)
        assert band.z0_m == pytest.approx(120 * _IN, abs=1e-3)
        assert not band.replaces_wall_finish
        assert band.material_ref == "mdf-panel-painted"
        assert band.thickness_m == pytest.approx(0.25 * _IN, abs=1e-6)


def test_the_bands_still_bill_what_they_billed(bands):
    """Removing the north walnut reduces both its drawn and ordered area."""
    walnut = sum(b.area_m2 for b in bands if b.tag == "WP-M-STUDY-WAINSCOT") * _M2_TO_FT2
    tile = sum(b.area_m2 for b in bands if b.tag == "WP-B-SAUNA-SPLASH") * _M2_TO_FT2
    assert walnut == pytest.approx(28.185, abs=0.005)
    assert tile == pytest.approx(45.0, abs=0.5)


# --- a band stops at the ceiling, not at the platform lift --------------------------------


def test_a_full_height_band_on_a_lifted_wall_stops_at_the_top_plate(catlin_plan):
    """``height=None`` means "run it to the wall's top", and since ``resolve/platform.py``
    grows a stacked wall floor-to-floor that top is the underside of the floor ABOVE.

    Panelling is a finish: it stops where the ceiling does. ``RM-M-BATH1`` is bounded by
    four walls, every one of them lifted, so a band with no height authored has to come back
    at the plate on all four or the order buys a joist depth of wainscot per wall.

    Authored here rather than in the house because catlin's own five bands all name a
    ``height`` — the case is real but unexercised, and inventing a sixth band in the house
    to test the engine would be the wrong place to put it.
    """
    from typehaus.model.paneling import WallPaneling
    from typehaus.resolve import resolve

    room = "RM-M-BATH1"
    band = WallPaneling(uid="PNTRIMTEST", tag="PN-TEST-FULLHEIGHT", room=room,
                        material_ref="latex-paint")
    model, _findings = resolve(catlin_plan.with_elements(
        "main", (*catlin_plan.storey_elements("main"), band)))

    records = [p for p in model.panelings if p.tag == "PN-TEST-FULLHEIGHT"]
    assert len(records) == 4, [p.wall_tag for p in records]
    for record in records:
        wall = model.wall(record.wall_tag)
        assert wall.plate_top_z_m is not None, f"{wall.tag} is no longer lifted"
        assert record.band_z1_m == pytest.approx(
            wall.plate_top_z_m - wall.base_ref_z_m, abs=1e-9), wall.tag
        # And it really is shorter than the wall — otherwise the assertion above is
        # satisfied by a plate that happens to be the wall top.
        assert wall.plate_top_z_m < wall.z1_m - _IN


def test_a_span_on_a_wall_inside_its_room_needs_a_face(catlin_plan):
    """Both faces of a knee wall are the room's, so no side can be derived: without
    ``face`` the span is an unbounded-wall ERROR, never a band on a guessed side."""
    from typehaus.model import PanelingSpan, WallPaneling
    from typehaus.quantities import ft, inch
    from typehaus.resolve import resolve

    band = WallPaneling(uid="TSTPNL0001", tag="WP-TEST-KNEE", room="RM-M-BATH2",
                        material_ref="solid-surface-panel", replaces_wall_finish=True,
                        spans=(PanelingSpan(wall_ref="W-M-TUBDK-S", start=inch(4.365),
                                            length=ft(3)),))
    main = (*catlin_plan.storey_elements("main"), band)
    plan = catlin_plan.model_copy(update={"elements": {**catlin_plan.elements, "main": main}})
    model, findings = resolve(plan)
    assert not [b for b in model.panelings if b.tag == "WP-TEST-KNEE"]
    assert any("WP-TEST-KNEE" in f.message and "W-M-TUBDK-S" in f.message for f in findings)


def test_suite_board_and_batten_is_continuous_and_matches_procurement(bands, catlin_model):
    from typehaus.resolve.geometry_millwork import base_run_prisms
    from typehaus.takeoff.hardwood import hardwood_takeoff
    from typehaus.takeoff.interior_trim import interior_trim_takeoff

    suite = [b for b in bands if b.tag == "WP-S-SUITE-HEADBOARD"]
    boards = [piece for band in suite for piece in band.trim_pieces]
    rails = [piece for piece in boards if piece.kind == "paneling top rail"]
    battens = [piece for piece in boards if piece.kind == "paneling batten"]
    assert len(rails) == 1, "the model wall split must not split the top rail"
    assert len(battens) == 8
    assert rails[0].length_m == pytest.approx(sum(b.run_m for b in suite))
    assert rails[0].width_m == pytest.approx(3.5 * _IN)
    assert rails[0].z1_m == pytest.approx(suite[0].z1_m)
    assert all(p.length_m == pytest.approx(65 * _IN) for p in battens)
    assert all(p.width_m == pytest.approx(2.5 * _IN) for p in battens)
    assert all(p.thickness_m == pytest.approx(0.75 * _IN) for p in boards)
    centers = sorted(Polygon(p.outline).centroid.x for p in battens)
    spacing = [b - a for a, b in zip(centers, centers[1:], strict=False)]
    assert max(spacing) <= 16 * _IN
    assert max(spacing) - min(spacing) < 1e-8
    # The MDF's room-facing edge and the trim's back are the same plane.
    back_y = suite[0].outline[3][1]
    assert all(max(y for _, y in p.outline) == pytest.approx(back_y) for p in boards)
    base = [r for r in catlin_model.base_runs if r.room == "RM-S-SUITE"
            and r.wall_tag in {"W-S-SN1", "W-S-SN2"}]
    assert base, "sheet backing must retain the existing base"
    for run in base:
        for prism in base_run_prisms(run):
            assert min(y for _, y in prism.ring) == pytest.approx(
                back_y - 0.75 * _IN, abs=1e-6)
    rows = [r for r in interior_trim_takeoff(catlin_model)
            if r["material"] == "poplar-batten-painted"]
    assert sum(r["pieces"] for r in rows) == len(boards)
    assert sum(r["length_ft"] for r in rows) == pytest.approx(
        sum(p.length_m for p in boards) / 0.3048, abs=0.02)
    milling = hardwood_takeoff(catlin_model)
    assert not any(r["material"] in {"cherry-shiplap", "poplar-batten-painted",
                                     "mdf-panel-painted"} for r in milling)
    assert any(r["material"] == "cherry-trim" for r in milling)
    assert any(r["material"] == "cherry-stool-5q" for r in milling)


def test_suite_receptacle_remains_in_a_clear_panel_bay(bands, catlin_model):
    from shapely.geometry import Point

    device = next(o for o in catlin_model.canvas_objects if o.tag == "ED-S-SUITE-RC5")
    suite = [b for b in bands if b.tag == "WP-S-SUITE-HEADBOARD"]
    # A faceplate must clear the stile beside it; its unchanged station is in the field.
    assert all(Polygon(p.outline).distance(Point(device.position)) > 1.5 * _IN
               for band in suite for p in band.trim_pieces if p.kind == "paneling batten")
    attachment = catlin_model.plan.by_tag(device.tag).location.attachment
    assert attachment.normal_gap.meters == pytest.approx(0.25 * _IN)
    assert attachment.distance_from_start.meters == pytest.approx(12.75 * _IN)

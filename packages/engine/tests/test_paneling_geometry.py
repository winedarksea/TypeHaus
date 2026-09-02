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

    ``area_m2`` is net of the openings punching the band and the outline deliberately is not
    (a door reveal covers the punch), so the two reconcile through the openings rather than
    being equal. Pinning it this way is what stops the polygon and the order drifting apart:
    change either one alone and this fails.
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


def test_a_band_sits_on_its_room_side_of_the_wall(bands, catlin_model):
    """The whole rectangle lies on the room's side of the wall axis, not the far side.

    Derived from the wall's own layer polygons rather than from ``Room.clear_face``, because
    ``resolve/rooms.py::_lining_inset`` insets a claimed face by one uniform figure rather than
    by each wall's own lining — the sauna's 3 1/2" liner does not move its room polygon at all.
    Hanging a band off the clear face would bury the tile splash inside the wall.
    """
    faces = {room.tag: Polygon(room.clear_face) for room in catlin_model.rooms}
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


def test_the_catlin_bands_are_the_four_authored_ones(bands):
    """A guard on scope: the reference house authors exactly these, at these heights."""
    by_tag: dict[str, list] = {}
    for band in bands:
        by_tag.setdefault(band.tag, []).append(band)
    assert set(by_tag) == {"WP-B-SAUNA-SPLASH", "WP-M-STUDY-WAINSCOT", "WP-M-STUDY-FELT",
                           "WP-M-BATH2-SURR"}
    # Two 3' spans on two walls of the shower corner, full 7'-6" liner height.
    assert len(by_tag["WP-B-SAUNA-SPLASH"]) == 2
    for band in by_tag["WP-B-SAUNA-SPLASH"]:
        assert band.run_m == pytest.approx(3 * 12 * _IN, abs=1e-6)
        assert band.z1_m - band.z0_m == pytest.approx(90 * _IN, abs=1e-3)
    # Every bounding wall of the study, to 36".
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
        assert band.z1_m == pytest.approx(108 * _IN, abs=1e-6)
        assert not band.replaces_wall_finish
        # PET felt states no board stock, so it takes the 1/2" default — which is the panel.
        assert band.thickness_m == pytest.approx(0.5 * _IN, abs=1e-6)
    # RM-M-BATH2's marble-look shower surround: the 36" pan's two closed sides,
    # 3'-0" x 7'-0" each on a zero offset. The walls are W-M-BA2E2 and W-M-BDN1 and NOT
    # W-M-BA2E — FX-M-BATH2-SH's `wall_ref` names the riser's wall, three feet west of the
    # pan, which is the trap this assertion exists to hold. W-M-TUBDK-S bounds the room too
    # and must stay out: it is the tub deck's 20 3/4" knee wall, and a room-wide band would
    # clamp to its top and buy 5.3 SF of shower panel on a bath apron. Authoring `spans` is
    # what excludes it.
    assert len(by_tag["WP-M-BATH2-SURR"]) == 2
    assert {b.wall_tag for b in by_tag["WP-M-BATH2-SURR"]} == {"W-M-BA2E2", "W-M-BDN1"}
    for band in by_tag["WP-M-BATH2-SURR"]:
        assert band.run_m == pytest.approx(3 * 12 * _IN, abs=1e-6)
        assert band.z0_m == pytest.approx(0.0, abs=1e-6)
        assert band.z1_m == pytest.approx(84 * _IN, abs=1e-6)
        assert band.replaces_wall_finish
        # A cast panel states no board stock, so it takes the 1/2" default — which is,
        # again, the panel's own thickness.
        assert band.thickness_m == pytest.approx(0.5 * _IN, abs=1e-6)


def test_the_bands_still_bill_what_they_billed(bands):
    """Geometry is additive: the areas this pass draws are the areas it already ordered.

    51 SF of walnut and 45 SF of tile were the numbers before the polygon existed. If adding
    geometry moved either, the band being drawn is not the band being bought.
    """
    walnut = sum(b.area_m2 for b in bands if b.tag == "WP-M-STUDY-WAINSCOT") * _M2_TO_FT2
    tile = sum(b.area_m2 for b in bands if b.tag == "WP-B-SAUNA-SPLASH") * _M2_TO_FT2
    assert walnut == pytest.approx(46.5, abs=0.5)
    assert tile == pytest.approx(45.0, abs=0.5)

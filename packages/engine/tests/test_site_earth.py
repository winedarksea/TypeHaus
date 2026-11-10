"""The site earth sheet's cut-outs (``resolve/site_earth.py``).

Derivation: slabs at or below grade plus the enclosed footprint kept clear of backfill.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon

from typehaus.resolve.site_earth import earth_plane_void_rings, site_grade_elevation_m

FT = 0.3048

# Interior points of the three excavated structures, in feet (project frame).
HOUSE_BASEMENT_POINT_FT = (18.0, 18.0)
GARAGE_POINT_FT = (12.0, 60.0)
SUNKEN_GARDEN_POINT_FT = (18.0, -15.0)
# Open yard — earth must still be there. East of the garage (x=24', y=41'-65') and clear
# of the breezeway in the slot between them.
OPEN_YARD_POINT_FT = (30.0, 48.0)


def _covered_by_a_void(rings, point_ft) -> bool:
    point = Point(point_ft[0] * FT, point_ft[1] * FT)
    return any(Polygon(ring).contains(point) for ring in rings)


def test_every_excavated_structure_cuts_the_earth_sheet(catlin_model_ro) -> None:
    rings = earth_plane_void_rings(catlin_model_ro)
    assert _covered_by_a_void(rings, HOUSE_BASEMENT_POINT_FT), "house basement not cut"
    assert _covered_by_a_void(rings, GARAGE_POINT_FT), "garage slab not cut"
    assert _covered_by_a_void(rings, SUNKEN_GARDEN_POINT_FT), "sunken garden not cut"


def test_open_ground_keeps_its_earth(catlin_model_ro) -> None:
    assert not _covered_by_a_void(earth_plane_void_rings(catlin_model_ro), OPEN_YARD_POINT_FT)


def test_raised_walking_surfaces_do_not_displace_soil(catlin_model_ro) -> None:
    """The balcony deck (10') sits *on* the site, so it must not punch a hole in it.

    Its joists cantilever 9" past the edge beams, so the deck reaches x 8'-3" where the court's
    void starts at the west wall's outer face, 8'-6": the strip between is covered by the
    balcony deck and by nothing at grade — earth belongs there.

    Read off FS-SG-BALCONY's deck sheet, not a SL-SG-DECK solid: the aluminium plank is the
    floor system's ``subfloor`` — there is no deck Slab.
    """
    grade = site_grade_elevation_m(catlin_model_ro)
    deck = next(f for f in catlin_model_ro.floors if f.tag == "FS-SG-BALCONY")
    balcony = Polygon(deck.deck_outline)
    assert deck.deck_z1_m > grade
    under_the_overhang = Point(8.375 * FT, -2.0 * FT)
    assert balcony.contains(under_the_overhang)
    rings = earth_plane_void_rings(catlin_model_ro)
    assert not any(Polygon(ring).contains(under_the_overhang) for ring in rings)


def test_void_rings_are_disjoint(catlin_model_ro) -> None:
    """Stacked slabs (basement + main deck share a footprint) merge into one ring: an
    IfcArbitraryProfileDefWithVoids and a three.js Shape both need non-overlapping holes."""
    polygons = [Polygon(ring) for ring in earth_plane_void_rings(catlin_model_ro)]
    assert len(polygons) == 5  # joined house/court, garage, both rain gardens, drive
    for index, first in enumerate(polygons):
        for second in polygons[index + 1:]:
            assert not first.intersects(second)


def test_model_json_publishes_the_same_rings(catlin_model_ro) -> None:
    """The viewer must not re-derive the cut from rooms — one storey of one structure is
    all a room-derived cut can ever see."""
    from typehaus.server.model_json import model_to_dict

    serialized = model_to_dict(catlin_model_ro)["site"]["earth_voids"]
    derived = earth_plane_void_rings(catlin_model_ro)
    assert len(serialized) == len(derived) == 5
    assert [[tuple(point) for point in ring] for ring in serialized] == derived


def test_ifc_lot_slab_carries_the_voids(catlin_model_ro, catlin_ifc_path: Path) -> None:
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))
    site = f.by_type("IfcSite")[0]
    solid = site.Representation.Representations[0].Items[0]
    profile = solid.SweptArea
    assert profile.is_a("IfcArbitraryProfileDefWithVoids")
    assert len(profile.InnerCurves) == len(earth_plane_void_rings(catlin_model_ro))


def test_court_house_separation_is_clear_of_earth(catlin_model_ro) -> None:
    """The slab ends 10 inches south of the house: walls, cavity and joints fill that strip."""
    from shapely.geometry import box
    from typehaus.resolve.overlay import union_all

    void = union_all([Polygon(ring) for ring in earth_plane_void_rings(catlin_model_ro)])
    court = next(s for s in catlin_model_ro.solids if s.tag == "SL-SG-FLOOR")
    west, _, east, north = Polygon(court.outline).bounds
    separation = box(west, north, east, 0.0)
    assert separation.difference(void).area < 1e-9
    # Keep real yard immediately beside the enclosure rather than expanding all slab holes.
    assert not void.covers(Point(8.375 * FT, -2.0 * FT))

"""The site earth sheet's cut-outs (``resolve/site_earth.py``).

The sheet used to be cut only by the house's own ground-storey rooms, so it sliced straight
through the freestanding garage and the open-air sunken garden — two structures that share
no storey, room set, or wall loop with the house. The derivation is now "every slab that
finishes at or below grade", which reaches all three without naming any of them.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon

from typehaus.resolve import resolve
from typehaus.resolve.site_earth import earth_plane_void_rings, site_grade_elevation_m
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
FT = 0.3048

# Interior points of the three excavated structures, in feet (project frame).
HOUSE_BASEMENT_POINT_FT = (18.0, 18.0)
GARAGE_POINT_FT = (12.0, 60.0)
SUNKEN_GARDEN_POINT_FT = (18.0, -15.0)
# Open yard between the house and the garage — earth must still be there.
OPEN_YARD_POINT_FT = (18.0, 42.0)


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    assert not [f for f in findings if f.severity.value == "error"]
    return model


def _covered_by_a_void(rings, point_ft) -> bool:
    point = Point(point_ft[0] * FT, point_ft[1] * FT)
    return any(Polygon(ring).contains(point) for ring in rings)


def test_every_excavated_structure_cuts_the_earth_sheet(catlin_model) -> None:
    rings = earth_plane_void_rings(catlin_model)
    assert _covered_by_a_void(rings, HOUSE_BASEMENT_POINT_FT), "house basement not cut"
    assert _covered_by_a_void(rings, GARAGE_POINT_FT), "garage slab not cut"
    assert _covered_by_a_void(rings, SUNKEN_GARDEN_POINT_FT), "sunken garden not cut"


def test_open_ground_keeps_its_earth(catlin_model) -> None:
    assert not _covered_by_a_void(earth_plane_void_rings(catlin_model), OPEN_YARD_POINT_FT)


def test_raised_walking_surfaces_do_not_displace_soil(catlin_model) -> None:
    """The balcony deck (10') sits *on* the site, so it must not punch a hole in it.

    Its joists cantilever 6" past the garden walls, so the strip under that overhang is
    covered by the balcony slab and by nothing at grade — earth belongs there.
    """
    grade = site_grade_elevation_m(catlin_model)
    balcony = Polygon(next(s for s in catlin_model.solids if s.tag == "SL-SG-DECK").outline)
    assert min(s.z1_m for s in catlin_model.solids if s.tag == "SL-SG-DECK") > grade
    under_the_overhang = Point(7.75 * FT, -2.0 * FT)
    assert balcony.contains(under_the_overhang)
    rings = earth_plane_void_rings(catlin_model)
    assert not any(Polygon(ring).contains(under_the_overhang) for ring in rings)


def test_void_rings_are_disjoint(catlin_model) -> None:
    """Stacked slabs (basement + main deck share a footprint) merge into one ring: an
    IfcArbitraryProfileDefWithVoids and a three.js Shape both need non-overlapping holes."""
    polygons = [Polygon(ring) for ring in earth_plane_void_rings(catlin_model)]
    assert len(polygons) == 3  # house, garage, sunken garden
    for index, first in enumerate(polygons):
        for second in polygons[index + 1:]:
            assert not first.intersects(second)


def test_model_json_publishes_the_same_rings(catlin_model) -> None:
    """The viewer must not re-derive the cut from rooms — one storey of one structure is
    all a room-derived cut can ever see."""
    from typehaus.server.model_json import model_to_dict

    serialized = model_to_dict(catlin_model)["site"]["earth_voids"]
    derived = earth_plane_void_rings(catlin_model)
    assert len(serialized) == len(derived) == 3
    assert [[tuple(point) for point in ring] for ring in serialized] == derived


def test_ifc_lot_slab_carries_the_voids(catlin_model, tmp_path: Path) -> None:
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path / "site_voids.ifc")
    f = ifcopenshell.open(str(out))
    site = f.by_type("IfcSite")[0]
    solid = site.Representation.Representations[0].Items[0]
    profile = solid.SweptArea
    assert profile.is_a("IfcArbitraryProfileDefWithVoids")
    assert len(profile.InnerCurves) == len(earth_plane_void_rings(catlin_model))

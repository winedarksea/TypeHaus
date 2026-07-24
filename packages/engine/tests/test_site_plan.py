"""Site plan builder — real C-101 (→ Permit-ready plan set Phase 4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.scene import ArchDimension, Polyline, Symbol
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_layer_census_for_parcel_and_setbacks(catlin_model):
    scene = build_site_plan(catlin_model)
    layers = scene.by_layer()
    assert "C-PROP" in layers
    assert "C-PROP-SETB" in layers
    assert {"C-UTIL-SEWER", "C-UTIL-WATER", "C-UTIL-POWER"} <= set(layers)


def test_setback_dimensions_present(catlin_model):
    scene = build_site_plan(catlin_model)
    dims = [n for n in scene.nodes if isinstance(n, ArchDimension)]
    # one setback dimension per authored SetbackSpec (4) plus the existing bbox chain (0
    # here — build_site_plan never called emit_bbox_dimension_chain).
    assert len(dims) == 4


def test_drainage_arrows_point_downhill(catlin_model):
    scene = build_site_plan(catlin_model)
    arrows = [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == "C-TOPO-ARRW"]
    assert arrows
    m_to_in = 39.37007874015748
    spots = {round(s.position.xy_m[1] * m_to_in): s.elevation.meters
            for s in catlin_model.plan.project.site.spot_elevations}
    for arrow in arrows:
        y0, y1 = arrow.points[0][1], arrow.points[1][1]
        e0 = spots.get(round(y0))
        e1 = spots.get(round(y1))
        if e0 is not None and e1 is not None:
            assert e1 < e0  # arrow tip is downhill of its start


def test_starter_omits_utilities_it_does_not_have(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    scene = build_site_plan(model)
    layers = scene.by_layer()
    assert "C-UTIL-POWER" not in layers
    assert "C-UTIL-SEWER" in layers and "C-UTIL-WATER" in layers


def test_site_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_site_plan(catlin_model)
    path = write_dxf(scene, tmp_path / "site.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"C-PROP", "C-PROP-SETB"} <= names


def test_geojson_contours_render_as_topo_basemap(catlin_model):
    from typehaus.emit.draw.scene import Polyline, Text

    assert catlin_model.plan.project.site.contours, "manifest should load basemap contours"
    scene = build_site_plan(catlin_model)
    contour_lines = [n for n in scene.nodes
                     if isinstance(n, Polyline) and n.layer == "C-TOPO-MINR"]
    labels = [n.content for n in scene.nodes
              if isinstance(n, Text) and n.layer == "C-TOPO-MINR"]
    assert len(contour_lines) == len(catlin_model.plan.project.site.contours)
    assert any("'" in label for label in labels)  # each contour labels its grade elevation


def test_foundation_grading_arrows_point_away_and_read_slope(catlin_model):
    from typehaus.emit.draw.scene import Polyline, Text

    scene = build_site_plan(catlin_model)
    arrows = [n for n in scene.nodes
              if isinstance(n, Polyline) and n.layer == "C-TOPO-GRAD"]
    labels = [n.content for n in scene.nodes
              if isinstance(n, Text) and n.layer == "C-TOPO-GRAD"]
    assert arrows  # one grade-away arrow per near-foundation spot station
    assert labels and all("AWAY" in label for label in labels)


def test_load_basemap_geojson_parses_parcel_and_contours(tmp_path: Path):
    import json

    from typehaus.model.site import load_basemap_geojson

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"role": "parcel"},
             "geometry": {"type": "Polygon",
                          "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}},
            {"type": "Feature", "properties": {"role": "contour", "elevation": -1.5},
             "geometry": {"type": "LineString", "coordinates": [[0, 5], [10, 5]]}},
        ],
    }
    path = tmp_path / "bm.geojson"
    path.write_text(json.dumps(geojson))
    basemap = load_basemap_geojson(path)
    assert len(basemap.parcel) == 4  # closing vertex dropped
    assert basemap.parcel[1].xy_m[0] == pytest.approx(10 * 0.3048)
    assert len(basemap.contours) == 1
    assert basemap.contours[0].elevation.meters == pytest.approx(-1.5 * 0.3048)
    assert len(basemap.contours[0].points) == 2


def test_catlin_basemap_fixture_loads(catlin_model):
    from typehaus.model.site import load_basemap_geojson

    fixture = CATLIN_DIR / "plan" / "basemap.geojson"
    basemap = load_basemap_geojson(fixture)
    assert len(basemap.parcel) == 4
    assert basemap.contours  # contour lines present in the survey fixture

"""Site plan builder — real C-101 (→ Permit-ready plan set Phase 4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.scene import ArchDimension, Polyline
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR


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


# --- C3: what a zoning reviewer reads on C-101 -------------------------------------------

def _with_site(model, **updates):
    """Frozen pydantic edit path (mirrors ``test_site_checks._model_with_site``)."""
    import copy

    edited = copy.copy(model)
    site = model.plan.project.site.model_copy(update=updates)
    project = model.plan.project.model_copy(update={"site": site})
    edited.plan = model.plan.model_copy(update={"project": project})
    return edited


def _texts(scene, layer: str) -> list[str]:
    from typehaus.emit.draw.scene import Text

    return [n.content for n in scene.nodes if isinstance(n, Text) and n.layer == layer]


def _fully_annotated(catlin_model):
    """Catlin plus every C-101 input the house may not have authored yet.

    C3's drawing code lands before (and independently of) the house data, so the sheet is
    exercised here against a site that carries one of everything rather than waiting on
    ``houses/catlin`` to grow a driveway.
    """
    from typehaus.model.site import Benchmark, Easement, ErosionControl, StreetFrontage
    from typehaus.quantities import ft, pt

    easement = Easement(kind="utility", width=ft(6),
                        outline=(pt(ft(62), ft(-60)), pt(ft(68), ft(-60)),
                                 pt(ft(68), ft(105)), pt(ft(62), ft(105))),
                        description="DOC. NO. TBD")
    fence = ErosionControl(kind="silt_fence",
                           path=(pt(ft(-32), ft(-60)), pt(ft(68), ft(-60))))
    entrance = ErosionControl(kind="construction_entrance", path=(pt(ft(18), ft(105)),))
    return _with_site(
        catlin_model,
        zoning_district="RL",
        parcel_basis="placeholder",
        easements=(easement,),
        erosion_controls=(fence, entrance),
        streets=(StreetFrontage(name="TBD Avenue", edge=2, right_of_way_ft=60.0),),
        benchmark=Benchmark(position=pt(ft(68), ft(105)), elevation=ft(0),
                            description="top nut of hydrant"),
    )


def test_layer_census_gains_the_c3_annotation_layers(catlin_model):
    layers = set(build_site_plan(_fully_annotated(catlin_model)).by_layer())
    assert {"C-ANNO-TABL", "C-PROP-EASE", "C-EROS", "C-ANNO-BMRK"} <= layers


def test_setback_labels_carry_required_and_provided(catlin_model):
    labels = _texts(build_site_plan(catlin_model), "C-PROP-SETB")
    front = [line for line in labels if line.startswith("FRONT SETBACK")]
    assert front == ["FRONT SETBACK 30'-0\" REQ / 37'-9\" PROVIDED"]
    assert all("REQ" in line and "PROVIDED" in line for line in labels)


def test_lot_lines_print_length_and_bearing(catlin_model):
    from typehaus.emit.draw.site_metrics import lot_line_dimensions

    labels = _texts(build_site_plan(catlin_model), "C-PROP")
    dims = lot_line_dimensions(catlin_model.plan.project.site)
    assert len(dims) == 4
    for _edge, length_ft, bearing in dims:
        assert f"{length_ft:.2f}'  {bearing}" in labels


def test_coverage_percentage_agrees_with_site_metrics(catlin_model):
    """The one number the cover and C-101 must not disagree about."""
    from typehaus.emit.draw.site_metrics import building_coverage_ft2, lot_area_ft2

    site = catlin_model.plan.project.site
    expected = building_coverage_ft2(catlin_model) / lot_area_ft2(site) * 100.0
    rows = [line for line in _texts(build_site_plan(catlin_model), "C-ANNO-TABL")
            if line.startswith("BUILDING COVERAGE")]
    assert rows and f"({expected:.1f}%)" in rows[0]


def test_the_zoning_table_prints_the_district_maximum(catlin_model):
    rows = [line for line in _texts(build_site_plan(_fully_annotated(catlin_model)),
                                    "C-ANNO-TABL")
            if line.startswith(("BUILDING COVERAGE", "BUILDING HEIGHT"))]
    assert any("40% MAX" in row for row in rows)  # RL, St Paul Ord. 23-43
    assert any("35' MAX" in row for row in rows)


def test_a_placeholder_parcel_says_so_on_the_face_of_the_sheet(catlin_model):
    notes = " ".join(_texts(build_site_plan(_fully_annotated(catlin_model)), "C-ANNO-TABL"))
    assert "PLACEHOLDER PARCEL" in notes and "NOT A SURVEY" in notes
    surveyed = _with_site(_fully_annotated(catlin_model), parcel_basis="survey",
                          survey_by="A. Surveyor", survey_date="2026-01-01")
    notes = " ".join(_texts(build_site_plan(surveyed), "C-ANNO-TABL"))
    assert "PLACEHOLDER" not in notes
    # the note is wrapped, so read it back word-wise rather than as one span
    assert "CERTIFIED SURVEY" in notes and "A. SURVEYOR" in notes and "2026-01-01" in notes


def test_erosion_control_street_easement_and_benchmark_read(catlin_model):
    scene = build_site_plan(_fully_annotated(catlin_model))
    assert "SILT FENCE" in _texts(scene, "C-EROS")
    assert "ROCK CONSTRUCTION ENTRANCE" in _texts(scene, "C-EROS")
    assert any("6'-0\" UTILITY EASEMENT" in t for t in _texts(scene, "C-PROP-EASE"))
    assert any("TBD AVENUE — 60' R.O.W." in t for t in _texts(scene, "C-PROP"))
    assert any("BENCHMARK EL." in t for t in _texts(scene, "C-ANNO-BMRK"))


def test_the_table_sits_clear_of_the_lot_it_describes(catlin_model):
    from typehaus.emit.draw.scene import Text

    scene = build_site_plan(_fully_annotated(catlin_model))
    parcel_x = [p.xy_m[0] / 0.0254 for p in catlin_model.plan.project.site.parcel]
    table = [n for n in scene.nodes if isinstance(n, Text) and n.layer == "C-ANNO-TABL"]
    assert table and all(n.anchor[0] > max(parcel_x) for n in table)


def test_starter_omits_the_site_data_it_does_not_have(starter_dir: Path):
    result = load_plan(starter_dir)
    model, _findings = resolve(result.plan)
    layers = set(build_site_plan(model).by_layer())
    assert not ({"C-PROP-EASE", "C-EROS", "C-ANNO-BMRK"} & layers)
    # The zoning table is not optional: a lot with no easements still has an area.
    assert "C-ANNO-TABL" in layers

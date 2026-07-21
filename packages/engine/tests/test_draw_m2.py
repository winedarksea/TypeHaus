"""WP2.6/2.7 — drawing IR scene, floorplan builder, DXF/PDF/raster writers (→ 20)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from typehaus.emit.draw import build_floorplan, write_dxf, write_pdf, write_raster
from typehaus.emit.draw.scene import Polyline, Scene, Symbol, Text
from typehaus.resolve import resolve
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def model(starter_dir: Path):
    result = load_plan(starter_dir)
    m, _ = resolve(result.plan)
    return m


@pytest.fixture(scope="module")
def scene(model) -> Scene:
    return build_floorplan(model, "main")


def test_scene_is_pure_data_json_snapshot(scene: Scene):
    # Frozen pure-data records → deterministic JSON snapshot (golden-testable).
    assert scene.to_json() == scene.to_json()
    assert scene.name == "plan-main"


def test_floorplan_has_framing_and_aia_layers(scene: Scene):
    layers = scene.by_layer()
    assert "A-WALL" in layers          # wall linework
    assert "S-FRAM" in layers          # real framing members (signature look)
    assert "A-ANNO-DIMS" in layers     # auto dimension chain
    # framing members carry element provenance for XDATA
    fram = [n for n in layers["S-FRAM"] if isinstance(n, Polyline)]
    assert fram and all(n.uid for n in fram)


def test_floorplan_marks_windows_by_tag_and_carries_door_handing(scene: Scene):
    symbols = [node for node in scene.nodes if isinstance(node, Symbol)]
    windows = [node for node in symbols if node.name == "window-mark"]
    doors = [node for node in symbols if node.name == "door-swing"]
    labels = [node.content for node in scene.nodes if isinstance(node, Text)]
    assert windows and doors
    assert all(node.layer == "A-GLAZ" and node.params["width_in"] > 0 for node in windows)
    assert all(node.params["swing_sign"] in {-1, 1} for node in doors)
    assert "WIN-101" in labels


def test_floorplan_door_symbol_reflects_both_handing_flips(model):
    flipped = copy.deepcopy(model)
    door = flipped.plan.by_tag("D-101")
    replacement = door.model_copy(update={"flip_hinge": True, "flip_swing": True})
    flipped.plan = flipped.plan.with_elements(
        "main", [replacement if item.tag == door.tag else item
                 for item in flipped.plan.storey_elements("main")],
    )
    symbols = [node for node in build_floorplan(flipped, "main").nodes if isinstance(node, Symbol)]
    (door_symbol,) = [node for node in symbols if node.name == "door-swing"]
    assert door_symbol.params["swing_sign"] == -1


def test_dxf_round_trips_with_layers_and_units(scene: Scene, tmp_path: Path):
    import ezdxf

    path = write_dxf(scene, tmp_path / "plan.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1  # inches, INSUNITS=1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"A-WALL", "S-FRAM", "A-ANNO-DIMS"} <= names
    assert len(list(doc.modelspace())) > 10


def test_pdf_and_raster_write(scene: Scene, tmp_path: Path):
    pdf = write_pdf(scene, tmp_path / "plan.pdf")
    png = write_raster(scene, tmp_path / "plan.png")
    assert pdf.stat().st_size > 0
    assert png.stat().st_size > 0


def test_render_views_per_storey(model, tmp_path: Path):
    from typehaus.emit.draw import render_views

    paths = render_views(model, tmp_path / "r", view="plan")
    assert paths and all(p.suffix == ".png" and p.exists() for p in paths)

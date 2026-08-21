"""A PNG and an SVG of the same detail are the same drawing (→ 30 §Details).

The check that would have shown the stale render artifacts *as* staleness. Two files
claiming to be the same detail can differ in aspect only if one of them was produced by a
different layout — which is exactly what a fit-to-content figure does, since the fit depends
on the content and the content depended on the writer.

With a frame both come off the same paper, so this is now true by construction; the test is
what keeps it that way.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from typehaus.emit.draw.details import build_detail, derive_detail_slices

pytest.importorskip("matplotlib")

_KEY = "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF"


@pytest.fixture(scope="module")
def eave_scene(catlin_model):
    derived = next(d for d in derive_detail_slices(catlin_model) if d.key == _KEY)
    scene, _findings = build_detail(catlin_model, derived)
    return scene


def _render(scene, path):
    from typehaus.emit.draw.pdf_writer import write_raster

    return write_raster(scene, path, title="parity", dpi=110)


def _svg_aspect(path) -> float:
    root = ET.parse(path).getroot()
    box = root.get("viewBox")
    assert box, "the SVG carries no viewBox"
    _x, _y, w, h = (float(v) for v in box.split())
    return w / h


def _png_aspect(path) -> float:
    from PIL import Image

    with Image.open(path) as im:
        return im.size[0] / im.size[1]


def test_png_and_svg_agree_on_the_shape_of_the_page(eave_scene, tmp_path):
    png = _render(eave_scene, tmp_path / "eave.png")
    svg = _render(eave_scene, tmp_path / "eave.svg")
    assert _png_aspect(png) == pytest.approx(_svg_aspect(svg), rel=1e-3)


def test_the_page_is_the_paper_the_scene_chose(eave_scene, tmp_path):
    """Not "whatever bbox the content came to" — the aspect is the card's."""
    paper_w, paper_h = eave_scene.frame.paper
    png = _render(eave_scene, tmp_path / "eave.png")
    assert _png_aspect(png) == pytest.approx(paper_w / paper_h, rel=1e-3)


def test_the_svg_declares_the_paper_size_in_inches(eave_scene, tmp_path):
    svg = _render(eave_scene, tmp_path / "eave.svg")
    root = ET.parse(svg).getroot()
    width = root.get("width") or ""
    number = float(re.sub(r"[^0-9.]", "", width) or 0.0)
    # matplotlib writes points (72 per inch).
    assert number / 72.0 == pytest.approx(eave_scene.frame.paper[0], rel=1e-2)


def test_a_frameless_scene_still_fits_to_its_content(catlin_model, tmp_path):
    """The other path is unchanged — and *not* claimed to be paper-sized."""
    from typehaus.emit.draw.section import build_center_section

    scene = build_center_section(catlin_model)
    assert scene.frame is None
    png = _render(scene, tmp_path / "section.png")
    svg = _render(scene, tmp_path / "section.svg")
    assert _png_aspect(png) == pytest.approx(_svg_aspect(svg), rel=1e-2)

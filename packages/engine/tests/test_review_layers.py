"""The review stack: one vocabulary, and the SVG/PSD that read it (→ 30 §Review exports).

Three things have to hold together or the exports stop being a review tool. Every AIA layer
the writer has a pen for must land in a *named* review group, or a trade quietly disappears
from the print. The SVG's groups must be a re-parenting and not a restack, or the drawing
looks different from the PNG beside it. And the PSD's layers, composited, must be the PNG —
that is the whole claim the format makes.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from typehaus.emit.draw.review_layers import (
    BACKGROUND,
    BY_SLUG,
    DIMENSIONS,
    FIXTURES,
    MARKUP,
    OTHER,
    REVIEW_LAYERS,
    ROOMS,
    SERVICES,
    SHELL,
    STRUCTURE,
    layer_for,
    ordered_slugs,
)

pytest.importorskip("matplotlib")

_SVG = "{http://www.w3.org/2000/svg}"
_INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}"


# --- the vocabulary ---------------------------------------------------------------

def test_every_layer_the_writer_can_draw_has_a_home() -> None:
    """No pen in ``_LAYER_STYLE`` falls through to ``other``.

    ``other`` is the escape hatch for a layer nobody has classified yet. A layer the writer
    already has a colour and a weight for is not that: it is a trade somebody drew on
    purpose, and it belongs in a group a reviewer can name.
    """
    from typehaus.emit.draw.pdf_writer import _LAYER_STYLE

    unclassified = sorted(name for name in _LAYER_STYLE if layer_for(name) == OTHER)
    assert unclassified == []


@pytest.mark.parametrize(("aia", "expected"), [
    ("A-WALL", SHELL), ("A-WALL-INSU", SHELL), ("A-ROOF-TRIM", SHELL), ("A-SLAB", SHELL),
    ("S-FRAM", STRUCTURE), ("S-WALL-BRCE", STRUCTURE), ("S-FNDN-FTNG", STRUCTURE),
    ("A-AREA-IDEN", ROOMS), ("A-ANNO-DIMS", DIMENSIONS),
    ("P-SANR-PIPE", SERVICES), ("M-HVAC-SDFF", SERVICES), ("E-LITE", SERVICES),
    # An A- layer that is a building service, and an M- layer that is not: the two places
    # the discipline letter is the wrong answer, which is why the exact map exists.
    ("A-FLR-HEAT", SERVICES), ("M-HVAC-EQPM", FIXTURES), ("M-EQPT", FIXTURES),
])
def test_layers_land_where_a_reviewer_would_look(aia: str, expected: str) -> None:
    assert layer_for(aia) == expected


def test_an_unknown_layer_is_kept_not_dropped() -> None:
    assert layer_for("X-MYSTERY-9000") == OTHER
    assert layer_for(None) == OTHER
    assert layer_for("") == OTHER


def test_the_order_is_the_index() -> None:
    assert [layer.order for layer in REVIEW_LAYERS] == list(range(len(REVIEW_LAYERS)))
    assert ordered_slugs()[0] == BACKGROUND
    assert ordered_slugs()[-1] == MARKUP
    # The two synthetic groups hold no drawing node and exist only in the PSD.
    assert set(ordered_slugs()) - set(ordered_slugs(include_synthetic=False)) == {
        BACKGROUND, MARKUP}


# --- the exports ------------------------------------------------------------------

@pytest.fixture(scope="module")
def plan_scene(catlin_model):
    from typehaus.emit.draw.floorplan import build_floorplan

    return build_floorplan(catlin_model, "main")


def _groups(root: ET.Element) -> list[ET.Element]:
    return [g for g in root.iter(f"{_SVG}g") if g.get("data-typehaus-layer")]


def test_the_svg_carries_named_review_layers(plan_scene, tmp_path) -> None:
    from typehaus.emit.draw.pdf_writer import write_raster

    root = ET.parse(write_raster(plan_scene, tmp_path / "plan.svg", title="t")).getroot()
    groups = _groups(root)
    assert groups, "no review-layer groups in the SVG"
    for group in groups:
        slug = group.get("data-typehaus-layer")
        assert slug in BY_SLUG
        # Inkscape shows a layer only when both attributes are present.
        assert group.get(f"{_INKSCAPE}groupmode") == "layer"
        assert group.get(f"{_INKSCAPE}label") == BY_SLUG[slug].name
        assert len(group), f"{slug} group is empty"


def test_the_groups_are_a_reparenting_not_a_restack(plan_scene, tmp_path) -> None:
    """Each layer appears once, and they appear bottom-to-top in the vocabulary's order.

    This is what ``ArtistTagger``'s z-order banding buys. If a layer turned up in two runs,
    or out of order, the SVG's paint order would no longer be the PNG's and the two would
    show different drawings.
    """
    from typehaus.emit.draw.pdf_writer import write_raster

    root = ET.parse(write_raster(plan_scene, tmp_path / "plan.svg", title="t")).getroot()
    slugs = [g.get("data-typehaus-layer") for g in _groups(root)]
    assert len(slugs) == len(set(slugs)), f"a layer was split across runs: {slugs}"
    order = ordered_slugs()
    assert slugs == sorted(slugs, key=order.index)


def test_the_svg_ids_are_unique_and_every_artist_is_in_a_group(plan_scene, tmp_path) -> None:
    from typehaus.emit.draw.pdf_writer import write_raster

    root = ET.parse(write_raster(plan_scene, tmp_path / "plan.svg", title="t")).getroot()
    ids = [e.get("id") for e in root.iter() if e.get("id")]
    assert len(ids) == len(set(ids)), "duplicate id in the SVG"
    grouped = {id(e) for g in _groups(root) for e in g.iter()}
    loose = [e.get("id") for e in root.iter()
             if (e.get("id") or "").startswith("th-") and id(e) not in grouped]
    assert loose == [], f"tagged artists outside any review group: {loose[:5]}"


def test_the_svg_pulls_nothing_from_the_network(plan_scene, tmp_path) -> None:
    """A review drawing has to render on a machine that has never seen this repo."""
    from typehaus.emit.draw.pdf_writer import write_raster

    body = write_raster(plan_scene, tmp_path / "plan.svg", title="t").read_text("utf-8")
    for element in ET.fromstring(body).iter():
        for key, value in element.attrib.items():
            if key.endswith("href") or key == "src":
                assert not value.startswith(("http://", "https://", "//")), value
    assert "<script" not in body


# --- raster sizing ----------------------------------------------------------------

def test_long_edge_sizes_the_raster(plan_scene, tmp_path) -> None:
    from PIL import Image

    from typehaus.emit.draw.pdf_writer import write_raster

    path = write_raster(plan_scene, tmp_path / "plan.png", title="t", long_edge=800)
    with Image.open(path) as image:
        assert max(image.size) == 800


def test_dpi_and_long_edge_are_mutually_exclusive(catlin_model, tmp_path) -> None:
    from typehaus.emit.draw.render import render_views

    with pytest.raises(ValueError, match="pass one"):
        render_views(catlin_model, tmp_path, view="plan", dpi=110, long_edge=800)


def test_an_unknown_format_is_refused(catlin_model, tmp_path) -> None:
    from typehaus.emit.draw.render import render_views

    with pytest.raises(ValueError, match="unknown format"):
        render_views(catlin_model, tmp_path, view="plan", fmt="tiff")


def test_the_cli_help_states_the_real_default() -> None:
    """The help text names 4096; nothing else may."""
    import inspect

    from typehaus.cli import cmd_sheets
    from typehaus.emit.draw.render import DEFAULT_LONG_EDGE

    source = inspect.getsource(cmd_sheets.render)
    assert f"default {DEFAULT_LONG_EDGE}" in source


# --- the layered PSD --------------------------------------------------------------

_PSD_EDGE = 600  # small on purpose: this asserts structure, and every pass costs a render


@pytest.fixture(scope="module")
def plan_psd(plan_scene, tmp_path_factory):
    """``(psd path, png path)`` for the same scene at the same size."""
    pytest.importorskip("psd_tools")
    from typehaus.emit.draw.pdf_writer import write_raster
    from typehaus.emit.draw.render import write_scene

    out = tmp_path_factory.mktemp("psd")
    psd = write_scene(plan_scene, out / "plan.psd", "t", 110, _PSD_EDGE)
    png = write_raster(plan_scene, out / "plan.png", title="t", long_edge=_PSD_EDGE)
    return psd, png


def _layer_names(psd_path):
    from psd_tools import PSDImage

    return [layer.name for layer in PSDImage.open(psd_path)]


def test_the_psd_is_the_same_page_as_the_png(plan_psd) -> None:
    from PIL import Image
    from psd_tools import PSDImage

    psd_path, png_path = plan_psd
    with Image.open(png_path) as png:
        assert PSDImage.open(psd_path).size == png.size


def test_the_psd_layers_are_the_review_stack_in_order(plan_psd) -> None:
    names = _layer_names(plan_psd[0])
    assert names[0] == BY_SLUG[BACKGROUND].name, "the ground is not at the bottom"
    assert names[-1] == BY_SLUG[MARKUP].name, "the markup sheet is not on top"
    expected = [BY_SLUG[slug].name for slug in ordered_slugs()]
    # A drawing need not use every layer; the ones it uses must be in the stack's order.
    assert names == sorted(names, key=expected.index)
    assert len(names) == len(set(names))


def test_the_markup_layer_is_empty(plan_psd) -> None:
    """A reviewer's first pencil stroke has to land somewhere that is not the drawing."""
    import numpy as np
    from psd_tools import PSDImage

    markup = next(layer for layer in PSDImage.open(plan_psd[0])
                  if layer.name == BY_SLUG[MARKUP].name)
    # ``composite()`` and not ``topil()``: the latter hands back an opaque alpha channel for
    # a layer whose transparency lives in the record's mask, which is every layer here.
    assert np.asarray(markup.composite().convert("RGBA"))[..., 3].max() == 0


def test_the_psd_composite_is_the_png(plan_psd) -> None:
    """The claim the format makes: flattening the stack gives back the picture.

    Not byte-exact, and it cannot be. Each layer is rasterized against transparency and
    composited afterwards, so wherever two layers' ink overlaps an antialiased edge is
    blended twice instead of drawn once. That shows up as a handful of channel values on a
    thin border of pixels — never as a moved line, which is what a loose *mean* with a tight
    cap on how many pixels may differ at all is there to distinguish.
    """
    import numpy as np
    from PIL import Image
    from psd_tools import PSDImage

    psd_path, png_path = plan_psd
    composite = np.asarray(PSDImage.open(psd_path).composite().convert("RGB"), dtype=float)
    with Image.open(png_path) as image:
        png = np.asarray(image.convert("RGB"), dtype=float)
    delta = np.abs(composite - png)
    assert delta.mean() < 1.0
    assert (delta.max(axis=2) > 24).mean() < 0.001


# --- the permit set is outside all of this ----------------------------------------

def test_the_permit_path_is_neither_tagged_nor_restacked(plan_scene) -> None:
    """``_render_nodes`` without a tagger changes nothing about how the sheet is drawn.

    Banding re-orders, and ``haus print`` is the submittal. A high review layer's fill
    covering a low one's line would be a change to a drawing a plan checker has already
    read, arriving as a side effect of a markup feature. The guard is the z-order: with a
    tagger every artist is lifted into a band of 100, so anything still under 10 proves no
    banding ran.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from typehaus.emit.draw.pdf_writer import _render_nodes

    fig, ax = plt.subplots()
    try:
        _render_nodes(ax, plan_scene)
        artists = [a for name in ("lines", "patches", "texts", "collections")
                   for a in getattr(ax, name)]
        assert artists, "the scene drew nothing"
        assert [a for a in artists if a.get_gid()] == []
        assert max(a.get_zorder() for a in artists) < 10
    finally:
        plt.close(fig)


def test_the_review_path_is_tagged_and_banded(plan_scene) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from typehaus.emit.draw.artist_tags import ArtistTagger
    from typehaus.emit.draw.pdf_writer import _render_nodes

    fig, ax = plt.subplots()
    try:
        tagger = ArtistTagger(ax)
        _render_nodes(ax, plan_scene, tagger)
        assert tagger.by_slug, "nothing was claimed"
        for slug, artists in tagger.by_slug.items():
            band = BY_SLUG[slug].order * 100
            for artist in artists:
                assert artist.get_gid().startswith(f"th-{slug}-")
                assert band <= artist.get_zorder() < band + 100
    finally:
        plt.close(fig)


def test_a_card_with_paper_space_keeps_its_ids_unique(catlin_model, tmp_path) -> None:
    """A detail card draws into two axes, so one review layer can legitimately run twice.

    Model space holds the cut; paper space holds the notes column and title block. Both can
    carry ``notes``, and the second run is suffixed rather than merged into the first —
    merging would mean moving elements between parents, which is the one thing that would
    restack the drawing.
    """
    from typehaus.emit.draw.details import build_detail, derive_detail_slices
    from typehaus.emit.draw.render import write_scene

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:EXT_2X6|ROOF")
    scene, _findings = build_detail(catlin_model, derived)
    root = ET.parse(write_scene(scene, tmp_path / "eave.svg", "eave", 300, 400)).getroot()
    ids = [e.get("id") for e in root.iter() if e.get("id")]
    assert len(ids) == len(set(ids)), "duplicate id across the card's two axes"
    assert [g.get("data-typehaus-layer") for g in _groups(root)], "no groups on the card"

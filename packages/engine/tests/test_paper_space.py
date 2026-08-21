"""Model space, paper space, and the one rule that keeps a drawing at the scale it chose.

The bug this arrangement exists to fix: `pdf_writer._fig` fitted the figure to *everything*
in the scene, lettering included, so a detail's scale was a function of how much prose was
attached to it. Catlin's eave note runs 108 lines; the junction it describes is 40 inches
across. The drawing lost.

So: **text never enters the drawing's bbox**. Annotation is placed into a frame the geometry
chose, and it does not get a vote on what that frame is.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from typehaus.emit.draw.pdf_writer import _scene_bounds, geometry_bounds
from typehaus.emit.draw.scene import ArchDimension, Frame, Leader, NamedPoint, Polyline, Scene, Text
from typehaus.emit.draw.typography import DIM_TEXT_PT


def _square(size: float = 10.0) -> Polyline:
    return Polyline(points=((0.0, 0.0), (size, 0.0), (size, size), (0.0, size)),
                    layer="A-WALL", closed=True)


# --- the rule ---------------------------------------------------------------------------

def test_text_never_enters_the_drawing_bbox():
    geometry = Scene(name="t", nodes=(_square(),))
    lettered = Scene(name="t", nodes=(
        _square(),
        Text(anchor=(200.0, 200.0), content="a note that runs a very long way indeed"),
        Leader(anchor=NamedPoint(xy=(5.0, 5.0)), at=(-300.0, -50.0), to=(5.0, 5.0),
               text="and a leader from off the sheet"),
    ))
    assert geometry_bounds(geometry) == geometry_bounds(lettered) == (0.0, 0.0, 10.0, 10.0)
    # The legacy fit still grows, which is exactly why it is a separate function.
    assert _scene_bounds(lettered) != _scene_bounds(geometry)


def test_annotation_cannot_move_the_drawing():
    """The plan's own acceptance test: 500 note lines and a 200-character leader.

    ``Scene.notes`` was already outside the coordinate space; the leader was not.
    """
    plain = Scene(name="t", nodes=(_square(),))
    loaded = Scene(
        name="t",
        nodes=(_square(),
               Leader(anchor=NamedPoint(xy=(5.0, 5.0)), at=(40.0, 40.0), to=(5.0, 5.0),
                      text="x" * 200)),
        notes=tuple(f"note line {i}" for i in range(500)),
    )
    assert geometry_bounds(plain) == geometry_bounds(loaded)


def test_a_paper_node_is_not_in_the_model_bbox():
    """A title block at x=8.0 *paper* inches is not a wall 8 inches from the origin."""
    scene = Scene(name="t", nodes=(
        _square(),
        Polyline(points=((0.0, 0.0), (8.5, 0.0), (8.5, 11.0)), layer="A-ANNO-TTLB",
                 space="paper"),
    ))
    assert geometry_bounds(scene) == (0.0, 0.0, 10.0, 10.0)


def test_an_empty_or_text_only_scene_has_no_drawing_bounds():
    assert geometry_bounds(Scene(name="t")) is None
    assert geometry_bounds(Scene(name="t", nodes=(Text(anchor=(0.0, 0.0), content="hi"),))) is None


# --- the IR fields ----------------------------------------------------------------------

def test_every_drawn_node_carries_a_space_and_anchors_do_not():
    """``FaceAnchor``/``NamedPoint`` are references, not marks on the page."""
    assert _square().space == "model"
    assert Text(anchor=(0.0, 0.0), content="x").space == "model"
    with pytest.raises(ValidationError):
        NamedPoint(xy=(0.0, 0.0), space="paper")  # extra="forbid"


def test_height_pt_is_unset_by_default_so_nothing_has_changed_yet():
    """B2 lands the vocabulary dormant: no producer sets it, so no drawing moves."""
    assert Text(anchor=(0.0, 0.0), content="x").height_pt is None
    assert Leader(anchor=NamedPoint(xy=(0.0, 0.0)), at=(0.0, 0.0), to=(1.0, 1.0),
                  text="x").height_pt is None


def test_a_dimension_is_always_annotative():
    """Its points are measured and stay on the geometry; its string is a printed size.

    ``height_pt`` is not optional here — it is the literal every writer hardcoded, now said
    once. That is the four-way duplication collapsing into a field.
    """
    ends = (NamedPoint(xy=(0.0, 0.0)), NamedPoint(xy=(10.0, 0.0)))
    dim = ArchDimension(ends=ends, p0=(0.0, 0.0), p1=(10.0, 0.0), offset=3.0)
    assert dim.height_pt == DIM_TEXT_PT
    assert not hasattr(dim, "height")
    # And it takes no `space`: a measured point that moved to paper would measure paper.
    assert dim.space == "model"


# --- the frame --------------------------------------------------------------------------

def test_a_frameless_scene_is_exactly_what_it_was():
    assert Scene(name="t").frame is None


def test_a_frame_says_which_paper_and_which_scale():
    frame = Frame(paper=(8.5, 11.0), viewport=(0.5, 1.5, 4.6, 9.0), center=(20.0, 100.0),
                  scale=1.5, scale_label="1-1/2\" = 1'-0\"",
                  bands={"notes": (5.2, 1.5, 3.4, 9.0)})
    assert frame.bands["notes"][2] == 3.4
    scene = Scene(name="t", nodes=(_square(),), frame=frame)
    # The frame rides the scene through JSON, which is how the viewer gets it.
    assert '"scale_label"' in scene.to_json()
    assert geometry_bounds(scene) == (0.0, 0.0, 10.0, 10.0), "a frame is not geometry"


# --- the writers ------------------------------------------------------------------------

def _sized(scene: Scene, figsize=(6.0, 6.0)) -> list[float]:
    """Point sizes the PDF writer lands on for every label in ``scene``."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from typehaus.emit.draw.pdf_writer import _apply_text_scale, _render_nodes

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal")
    scaled = _render_nodes(ax, scene)
    ax.autoscale_view()
    fig.tight_layout()
    _apply_text_scale(fig, ax, scaled)
    sizes = [artist.get_fontsize() for artist, _h, _pt in scaled]
    plt.close(fig)
    return sizes


def test_an_annotative_label_letters_the_same_at_any_drawing_size():
    """The whole promise: 7 pt is 7 pt whether the cut is 10 inches or 10 feet across."""
    small = Scene(name="t", nodes=(
        _square(10.0), Text(anchor=(5.0, 5.0), content="R-19 BATT", height_pt=7.0)))
    large = Scene(name="t", nodes=(
        _square(400.0), Text(anchor=(5.0, 5.0), content="R-19 BATT", height_pt=7.0)))
    assert _sized(small) == _sized(large) == [7.0]


def test_a_model_space_label_still_scales_with_the_drawing():
    """The other half of the rule — nothing that has no ``height_pt`` has changed."""
    small = _sized(Scene(name="t", nodes=(
        _square(10.0), Text(anchor=(5.0, 5.0), content="x", height=1.6))))
    large = _sized(Scene(name="t", nodes=(
        _square(400.0), Text(anchor=(5.0, 5.0), content="x", height=1.6))))
    assert small[0] > large[0]


def test_the_floor_holds_and_the_ceiling_is_gone():
    """``MIN_PT`` is a legibility floor; the 14 pt clamp above it was hiding scale mistakes.

    A label that wants 40 pt on a 10-inch drawing now gets 40 pt — visibly wrong, which is
    the point. Silently drawing it at 14 is how the oversize lettering survived.
    """
    from typehaus.emit.draw.typography import MIN_PT

    tiny = _sized(Scene(name="t", nodes=(
        _square(4000.0), Text(anchor=(5.0, 5.0), content="x", height=0.01))))
    assert tiny[0] == MIN_PT
    huge = _sized(Scene(name="t", nodes=(
        _square(10.0), Text(anchor=(5.0, 5.0), content="x", height=6.0))))
    assert huge[0] > 14.0


def test_a_dimension_string_reads_its_own_height_pt():
    ends = (NamedPoint(xy=(0.0, 0.0)), NamedPoint(xy=(10.0, 0.0)))
    scene = Scene(name="t", nodes=(
        _square(), ArchDimension(ends=ends, p0=(0.0, 0.0), p1=(10.0, 0.0), offset=3.0,
                                 height_pt=9.0)))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from typehaus.emit.draw.pdf_writer import _render_nodes

    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    _render_nodes(ax, scene)
    sizes = {t.get_fontsize() for t in ax.texts if t.get_text()}
    plt.close(fig)
    assert 9.0 in sizes, "the dimension ignored its IR height"


# --- DXF, which has a real answer for both halves ---------------------------------------

def test_dxf_bakes_an_annotative_height_through_the_frame():
    """``doc.units = 1`` makes paper units inches too, so a printed size converts exactly."""
    from typehaus.emit.draw.dxf_writer import model_text_height

    frame = Frame(paper=(8.5, 11.0), viewport=(0.5, 1.5, 4.6, 9.0), center=(0.0, 0.0),
                  scale=1.5, scale_label="1-1/2\" = 1'-0\"")
    scene = Scene(name="t", frame=frame)
    # 7 pt at 1-1/2" = 1'-0" is 0.778 model inches — against the 1.6" the ladder authored.
    assert model_text_height(1.6, 7.0, scene) == pytest.approx(0.7778, abs=1e-4)
    # A quarter-scale plan: the same 7 pt is a much bigger thing in the model.
    quarter = Scene(name="t", frame=frame.model_copy(update={"scale": 0.25}))
    assert model_text_height(1.6, 7.0, quarter) == pytest.approx(4.6667, abs=1e-4)


def test_without_a_frame_the_model_height_stands():
    """No sheet chosen means no scale to convert through — the frameless path, unchanged."""
    from typehaus.emit.draw.dxf_writer import model_text_height

    assert model_text_height(1.6, 7.0, Scene(name="t")) == 1.6
    assert model_text_height(1.6, None, Scene(name="t")) == 1.6


def test_a_dxf_leader_puts_its_note_at_the_label_end(tmp_path):
    """It used to `set_placement(node.to)` — the *arrow tip*, inside the thing it points at.

    And it hardcoded height 3.0, so ``scene.py``'s claim that both writers honour
    ``Leader.height`` was false.
    """
    pytest.importorskip("ezdxf")
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = Scene(name="t", nodes=(
        _square(),
        Leader(anchor=NamedPoint(xy=(5.0, 5.0)), at=(40.0, 30.0), to=(5.0, 5.0),
               text="polyiso 3\"", height=1.6),
    ))
    doc = ezdxf.readfile(str(write_dxf(scene, tmp_path / "t.dxf")))
    text = next(e for e in doc.modelspace() if e.dxftype() == "TEXT")
    assert text.dxf.height == pytest.approx(1.6)
    placement = text.get_placement()[1]
    assert (placement.x, placement.y) == pytest.approx((40.0, 30.0))


# --- the card ---------------------------------------------------------------------------

def test_a_detail_chooses_a_real_architectural_scale(catlin_model):
    from typehaus.emit.draw.details import build_detail, derive_detail_slices
    from typehaus.emit.draw.sheet_writer import ARCH_SCALES

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    assert scene.frame is not None, "a rendered detail has no paper"
    assert scene.frame.scale in {s for s, _label in ARCH_SCALES}, \
        "the scale fell out of a fit instead of coming off the ladder"
    assert scene.frame.paper in {(8.5, 11.0), (11.0, 8.5)}


def test_notes_cannot_change_the_chosen_scale(catlin_model):
    """Catlin's eave carries 108 note lines. The drawing is 40 inches across.

    Before paper space the notes won: ``_fig`` sized the figure from a bbox that grew on
    text, so the detail printed at whatever scale the prose left room for.
    """
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    assert scene.notes, "this detail is the two-page notes case"
    loud = scene.model_copy(update={
        "notes": scene.notes + tuple(f"and another thing {i}" for i in range(500))})
    assert loud.frame == scene.frame


def test_the_bands_tile_without_overlapping():
    """A legend that ran the full width printed its third column through the notes."""
    from typehaus.emit.draw.detail_card import bands, viewport

    for paper in ((8.5, 11.0), (11.0, 8.5)):
        boxes = dict(bands(paper))
        boxes["viewport"] = viewport(paper)
        names = sorted(boxes)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                ax, ay, aw, ah = boxes[a]
                bx, by, bw, bh = boxes[b]
                assert not (ax < bx + bw - 1e-9 and bx < ax + aw - 1e-9
                            and ay < by + bh - 1e-9 and by < ay + ah - 1e-9), \
                    f"{paper}: {a} overlaps {b}"
        for name, (x, y, w, h) in boxes.items():
            assert x >= -1e-9 and y >= -1e-9
            assert x + w <= paper[0] + 1e-9 and y + h <= paper[1] + 1e-9, name


def test_the_chrome_is_paper_and_the_cut_is_model(catlin_model):
    """The title block and legend stopped being measured off the drawing's own bounds."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    paper = [n for n in scene.nodes if n.space == "paper"]
    assert paper, "no chrome reached paper space"
    titles = [n for n in paper if isinstance(n, Text)]
    assert any(n.content == catlin_model.plan.project.name for n in titles)
    assert any(n.content == "MATERIALS" for n in titles)
    band = scene.frame.bands["title"]
    project = next(n for n in titles if n.content == catlin_model.plan.project.name)
    assert band[1] <= project.anchor[1] <= band[1] + band[3]
    # And every paper node letters at a printed size — there is no scale to be relative to.
    assert all(n.height_pt is not None for n in paper if isinstance(n, Text))


def test_the_orientation_is_whichever_admits_the_larger_scale():
    """Not "tall crop → tall page" — the scale is what a reader gets out of a detail.

    Checked with no notes column, where both orientations are genuinely viable. *With* one,
    landscape wins nearly always, and that is the honest consequence of reserving 3.4" of an
    8.5"-wide page for prose plus two annotation gutters: portrait leaves the drawing almost
    nothing. A card that has to carry construction notes is a landscape card.
    """
    from typehaus.emit.draw.detail_card import card_for_crop

    assert card_for_crop(96.0, 24.0, (0.0, 0.0), notes=False).paper == (11.0, 8.5)
    assert card_for_crop(24.0, 96.0, (0.0, 0.0), notes=False).paper == (8.5, 11.0)
    # A small junction gets a big scale; a long one does not.
    small = card_for_crop(24.0, 30.0, (0.0, 0.0), notes=False)
    assert small.scale > card_for_crop(96.0, 24.0, (0.0, 0.0), notes=False).scale


def test_the_gutters_leave_the_drawing_real_room():
    """The failure mode the gutters can cause: reserve more page than the page has."""
    from typehaus.emit.draw.detail_card import (
        CALLOUT_GUTTER_IN,
        LADDER_GUTTER_IN,
        drawing_box,
        viewport,
    )

    view = viewport((11.0, 8.5), notes=True)
    width, height = drawing_box(view)
    assert width > 2.0, "a landscape card must leave the cut a usable column"
    assert height > 5.0
    assert view[2] > LADDER_GUTTER_IN + CALLOUT_GUTTER_IN

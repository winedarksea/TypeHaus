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

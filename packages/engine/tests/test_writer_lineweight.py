"""What a line's *weight* means, and when a plan stops drawing a wall's layers.

Two writer-side rules that share one cause. ``Polyline.lineweight`` was dead data in the
matplotlib writer — it resolved ``_LAYER_STYLE[layer]`` and threw the node's own weight away
— so every careful 0.18 / 0.25 / 0.35 / 0.5 / 0.7 a scene builder set was invisible on
screen and on paper, and only the DXF ever printed it. A drawing with one weight per layer
cannot say which of two things on the same layer is nearer, which is the vocabulary a
hidden-line elevation, a plan poché and a detail all rest on.

The poché is the same argument from the other end: at 1/4" = 1'-0" a wall's layer sandwich is
narrower than the strokes drawn round it, so the honest thing is to stop drawing the layers
and draw the wall.

Companion to ``test_detail_legibility.py``, which is about what a *cut* has to say; this file
is about the pens the writer says it with.
"""

from __future__ import annotations

from typehaus.emit.draw.pdf_writer import (
    _LAYER_STYLE,
    _POCHE_MAX_SCALE,
    _PT_PER_MM,
    _band_linewidth,
    _poche_for,
    _ring_ccw,
    _stroke_pt,
)
from typehaus.emit.draw.scene import Frame, Hatch, Polyline, Scene

_SQUARE = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))


def _frame(scale: float) -> Frame:
    return Frame(paper=(34.0, 22.0), viewport=(0.5, 0.5, 33.0, 21.0), center=(0.0, 0.0),
                 scale=scale, scale_label="test")


def _scene(name: str, nodes, scale: float | None) -> Scene:
    return Scene(name=name, nodes=tuple(nodes),
                 frame=None if scale is None else _frame(scale))


# --- a millimetre is a millimetre -------------------------------------------------------

def test_the_ir_lineweight_converts_by_the_only_conversion_there_is():
    """mm → pt is 72/25.4 and there is nothing here to tune.

    ``Polyline.lineweight`` is millimetres (``dxf_writer`` writes it out as 1/100 mm) and
    ``_LAYER_STYLE`` is printed points. A point is 1/72", a millimetre is 1/25.4". Any other
    number in that slot would be a fudge factor, and a fudge factor is how the PDF and the
    DXF of one scene come to disagree about a line neither of them computed.
    """
    assert _PT_PER_MM == 72.0 / 25.4
    for mm, pt in ((0.18, 0.5102), (0.25, 0.7087), (0.35, 0.9921), (0.7, 1.9843)):
        node = Polyline(points=_SQUARE, layer="A-WALL", lineweight=mm)
        assert abs(_stroke_pt(node)[1] - pt) < 5e-4, mm


def test_a_node_that_sets_a_weight_beats_its_layer_and_one_that_does_not_takes_it():
    """The rule, both halves. ``model_fields_set`` is what "set one" means: the IR default
    (0.25 mm) is not an authored choice, and a builder that never thought about weight must
    still get the layer's considered pen rather than an accidental 0.71 pt."""
    authored = Polyline(points=_SQUARE, layer="A-WALL", lineweight=0.18)
    silent = Polyline(points=_SQUARE, layer="A-WALL")
    assert abs(_stroke_pt(authored)[1] - 0.18 * _PT_PER_MM) < 1e-9
    assert _stroke_pt(silent)[1] == _LAYER_STYLE["A-WALL"][1]
    # And the ink comes from the layer either way — weight says how near, colour says what.
    assert _stroke_pt(authored)[0] == _stroke_pt(silent)[0] == _LAYER_STYLE["A-WALL"][0]


def test_a_layer_styled_at_zero_weight_is_a_suppression_not_a_thin_pen():
    """``A-AREA-IDEN`` carries room identification, not linework. Honouring a node's weight
    there would put an outline round every room polygon on every plan — a table entry of
    ``0.0`` is the writer being told *do not stroke this*, and a node cannot overrule it."""
    assert _LAYER_STYLE["A-AREA-IDEN"][1] == 0.0
    node = Polyline(points=_SQUARE, layer="A-AREA-IDEN", lineweight=0.7)
    assert _stroke_pt(node)[1] == 0.0


def test_an_unknown_layer_still_draws_rather_than_vanishing():
    """A layer nobody styled falls back to a visible default pen, as it always has —
    ``test_writer_layer_coverage`` is what keeps that from happening on a real sheet."""
    node = Polyline(points=_SQUARE, layer="X-NOT-A-LAYER", lineweight=0.35)
    assert _stroke_pt(node)[1] > 0.0


def test_the_band_cap_still_wins_over_a_heavy_node_weight():
    """The guard the roof taught is downstream of this and stays downstream of it.

    A 1/4"-thick band at 3/4" = 1'-0" is 1.125 printed points wide, so its outline is capped
    at 0.5625 whatever the node asked for. Honouring node weights makes it *easier* to ask
    for a stroke thicker than the band it surrounds, not harder, which is exactly why the cap
    may not be relaxed: it is what keeps a 1.1 pt vent mat from printing as a navy smear.
    """
    quarter_inch = [(0.0, 0.0), (0.25, 0.0), (0.25, 10.0), (0.0, 10.0)]
    heavy = _stroke_pt(Polyline(points=tuple(quarter_inch), layer="A-ROOF",
                                lineweight=0.7, closed=True))[1]
    assert heavy > 1.125, "the node asks for more than the band is wide"
    assert _band_linewidth(quarter_inch, heavy, 0.75) == 0.5625


# --- the plan poché ---------------------------------------------------------------------

def _wall_sandwich():
    """One wall as the plan builders emit it: a band per layer, plus its pattern hatch."""
    def band(u0, u1, layer):
        return Polyline(points=((u0, 0.0), (u1, 0.0), (u1, 120.0), (u0, 120.0)),
                        layer=layer, closed=True, lineweight=0.18, uid="W1")
    return [
        band(0.0, 0.625, "A-WALL-FINI"),
        band(0.625, 6.125, "A-WALL"),
        band(6.125, 10.125, "A-WALL-INSU"),
        band(10.125, 10.625, "A-WALL-PATT"),
        Hatch(boundary=((0.625, 0.0), (6.125, 0.0), (6.125, 120.0), (0.625, 120.0)),
              pattern="lumber", layer="A-WALL-PATT"),
    ]


def test_a_floor_plan_at_plan_scale_collapses_its_walls_and_a_frameless_one_does_not():
    """→ 20 §143's ``simplified_poche``, and the frameless escape hatch beside it.

    Without a :class:`Frame` there is no chosen paper, so there is no printed width to judge
    a band against and no scale the decision could honestly be made at. That scene keeps
    exactly the behaviour it had before any of this existed.
    """
    nodes = _wall_sandwich()
    assert _poche_for(_scene("plan-main", nodes, None), None) is None
    assert _poche_for(_scene("plan-main", nodes, _POCHE_MAX_SCALE), None) is not None
    assert _poche_for(_scene("plan-main", nodes, 0.125), None) is not None


def test_detail_scales_keep_every_layer_they_draw():
    """3/4" = 1'-0" is the detail ladder's coarsest rung and the stack reads there.

    3/8" matters as much: catlin's eight ``wall_foundation`` detail cards land on it, and a
    detail card is precisely the drawing whose subject IS the sandwich.
    """
    nodes = _wall_sandwich()
    for scale in (0.375, 0.5, 0.75, 1.5):
        assert _poche_for(_scene("plan-main", nodes, scale), None) is None, scale


def test_only_a_floor_plan_is_pocheed_however_small_the_scale():
    """The twelve other small-scale drawings on catlin's set that carry a wall sandwich.

    Four exterior elevations at 1/8", the building section and the typical exterior wall
    section at 3/16", six detail cards at 1/4" — a scale test alone would have flattened all
    of them, and each is a drawing that has to keep the layers it draws.
    """
    nodes = _wall_sandwich()
    for name in ("elevation-north", "section-house", "detail-wall_roof", "framing-FS-M-WEST",
                 "site-plan", "foundation-plan"):
        assert _poche_for(_scene(name, nodes, 0.125), None) is None, name


def test_the_poche_swallows_the_sandwich_and_leaves_everything_else_alone():
    """What gets absorbed: closed wall-layer bands, and the wall pattern hatch inside them.

    What does not: an open polyline lying on a wall layer (a line somebody drew across a
    wall is not a band), anything on another layer, and any paper-space node — the legend
    swatch on a card is not architecture.
    """
    poche = _poche_for(_scene("plan-main", _wall_sandwich(), 0.25), None)
    for node in _wall_sandwich():
        assert poche.absorbs(node), node.layer
    assert not poche.absorbs(Polyline(points=((0.0, 0.0), (10.0, 10.0)), layer="A-WALL"))
    assert not poche.absorbs(Polyline(points=_SQUARE, layer="S-FRAM", closed=True))
    assert not poche.absorbs(Polyline(points=_SQUARE, layer="A-WALL", closed=True,
                                      space="paper"))


def test_every_ring_is_wound_one_way_so_filling_them_all_means_union():
    """The poché is one compound path filled under matplotlib's nonzero winding rule.

    Two rings of *opposite* orientation cancel where they overlap, so a junction polygon
    lying over a wall band would punch a hole in the poché instead of merging into it.
    """
    clockwise = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0))
    assert _ring_ccw(clockwise) == list(reversed(clockwise))
    assert _ring_ccw(_SQUARE) == list(_SQUARE)

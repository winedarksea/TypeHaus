"""What makes a cut readable, as opposed to correct.

Every band in the eave detail was in the right place and the drawing still could not be
read: the two widest bands wore a crosshatch that beat their own colour, the four thinnest
were narrower than the stroke drawn round them, and the legend named the wall's materials
and none of the roof's. Those are three different defects with one symptom — a reader
cannot tell which sheet is which — so they are tested together here.

The geometry these rest on is :mod:`test_catlin_eave_water` and the section goldens; this
module is only about what survives the trip to paper.
"""

from __future__ import annotations

from typehaus.emit.draw.details import build_detail, derive_detail_slices
from typehaus.emit.draw.palette import detail_hatch
from typehaus.emit.draw.pdf_writer import _band_linewidth, _min_printed_width_pt
from typehaus.emit.draw.scene import Hatch, Text


def _eave(model):
    detail = next(d for d in derive_detail_slices(model) if d.key.startswith("wall_roof"))
    return build_detail(model, detail)[0]


# --- the boards go bare ----------------------------------------------------------------

def test_a_coloured_board_is_drawn_by_its_colour_and_not_by_a_pattern():
    """The rigid foams answer "what is this?" with their fill, so they take no hatch.

    ``"none"`` and not ``None``: a band with no hatch node at all loses its **fill** too
    (``section_clip.rect_nodes`` only emits the Hatch when there is a pattern), which is
    the opposite of what dropping the crosshatch is for.
    """
    for board in ("polyiso", "polyiso-foil", "eps", "icf-eps", "xps"):
        assert detail_hatch(board, "insulation") == "none", board
    # And the explicit entry beats the function fallback, or a bare board would pick up the
    # batt stipple on the way past.
    assert detail_hatch(None, "insulation") == "batt"
    # The textured families keep their patterns: what tells a batt from a board IS texture.
    assert detail_hatch("fiberglass-r19", "insulation") == "batt"
    assert detail_hatch("spray-foam", "insulation") == "foam"


def test_a_bare_board_still_reaches_the_page_as_a_filled_band(catlin_model):
    """The eave's two 3" polyiso courses are the widest bands in it. They must be there."""
    scene = _eave(catlin_model)
    polyiso = [n for n in scene.nodes if isinstance(n, Hatch) and n.material == "polyiso"]
    assert polyiso, "the roof's foam must still be emitted as Hatch bands"
    assert all(n.pattern == "none" for n in polyiso)


# --- a band's outline may never be wider than the band ----------------------------------

def test_a_band_thinner_than_its_own_stroke_keeps_a_visible_fill():
    """The rule the roof taught: cap the outline at half the band's printed width.

    At 3/4" = 1'-0" the A-ROOF stroke is 1.2 pt and the ventilated mat is 1.1 pt thick on
    paper, so the two edge strokes met in the middle and the mat, the underlayment and the
    drip below them printed as one navy smear.
    """
    quarter_inch = [(0.0, 0.0), (0.25, 0.0), (0.25, 10.0), (0.0, 10.0)]
    assert _min_printed_width_pt(quarter_inch, 0.75) == 1.125
    assert _band_linewidth(quarter_inch, 1.2, 0.75) == 0.5625

    # A band with room to spare is left exactly alone — this is a floor, not a restyling.
    three_inch = [(0.0, 0.0), (3.0, 0.0), (3.0, 10.0), (0.0, 10.0)]
    assert _band_linewidth(three_inch, 1.2, 0.75) == 1.2

    # Narrowest *dimension*, not narrowest axis: a sloped band is measured across itself.
    sloped = [(0.0, 0.0), (12.0, 4.0), (12.0, 4.25), (0.0, 0.25)]
    assert _min_printed_width_pt(sloped, 0.75) < _min_printed_width_pt(
        [(0.0, 0.0), (12.0, 0.0), (12.0, 4.25), (0.0, 0.0)], 0.75)

    # Never thinner than a hairline: a stroke that is a smudge is no clearer than a bar.
    hair = [(0.0, 0.0), (0.01, 0.0), (0.01, 10.0), (0.0, 10.0)]
    assert _band_linewidth(hair, 1.2, 0.75) == 0.15

    # Frameless scenes have no chosen scale, so there is no printed width to compare to.
    assert _band_linewidth(quarter_inch, 1.2, None) == 1.2


# --- the legend names what was drawn -----------------------------------------------------

def test_the_eave_legend_names_the_roof_it_is_mostly_made_of(catlin_model):
    """``_participating_layers`` matched roofs on the element tag (``RF-HOUSE``).

    A wall/roof condition is keyed on the two *assemblies* it joins, so that loop matched
    nothing on the one detail that is mostly roof: fourteen drawn materials, six legended,
    and the underlayment and vent mat the notes spend a paragraph each on were not among
    them.
    """
    scene = _eave(catlin_model)
    legended = {t.content.rsplit("  ", 1)[0] for t in scene.nodes
                if isinstance(t, Text) and t.space == "paper" and '"' in t.content}
    for material in ("osb", "roof-underlayment-synthetic", "roof-vent-mat",
                     "roof-deck-vapor-barrier", "zip-sheathing", "standing-seam"):
        assert material in legended, f"{material} is drawn but not legended"


def test_the_legend_only_names_materials_the_cut_actually_reached(catlin_model):
    """The other half of the same rule: legending a layer the crop missed sends a reader
    looking for something that is not on the sheet."""
    scene = _eave(catlin_model)
    drawn = {n.material for n in scene.nodes if isinstance(n, Hatch) and n.material}
    legended = {t.content.rsplit("  ", 1)[0] for t in scene.nodes
                if isinstance(t, Text) and t.space == "paper" and '"' in t.content}
    assert legended <= drawn, f"legended but never drawn: {sorted(legended - drawn)}"

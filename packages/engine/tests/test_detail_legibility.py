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

import math

import re

from typehaus.emit.draw.details import build_detail, derive_detail_slices
from typehaus.emit.draw.palette import detail_hatch
from typehaus.emit.draw.pdf_writer import _band_linewidth, _min_printed_width_pt
from typehaus.emit.draw.scene import Hatch, Leader, Polyline, Text


def _eave(model):
    detail = next(d for d in derive_detail_slices(model) if d.key.startswith("wall_roof"))
    return build_detail(model, detail)[0]


#: A ladder rung says `<layer name> <n>"` and nothing else. The name may carry a space
#: ("rafter fill"), so it is anything that is not the trailing dimension.
_RUNG_TEXT = re.compile(r'^(?P<name>.+?) [\d.]+"$')


def _rungs(scene):
    """Every roof ladder rung as ``(name, tip)``, where ``tip`` is ``to``.

    ``to`` and not ``anchor``: every renderer draws the single segment ``at → to`` and puts
    the arrowhead on ``to``. ``anchor`` is provenance, and asserting on it would pass while
    the printed arrow pointed somewhere else entirely — which is exactly what happened.

    The continuity callouts share the layer but point at control planes, not at bands; a
    wall rung is flat, its tip at its own row. Both are filtered out here.
    """
    out = []
    for node in scene.nodes:
        if not isinstance(node, Leader) or node.layer != "A-ANNO-TEXT":
            continue
        match = _RUNG_TEXT.match(node.text)
        if match is None or abs(node.at[1] - node.to[1]) <= 1e-9:
            continue
        out.append((match.group("name"), node.to))
    return out


#: How far outside a band an arrow tip may land and still count as inside it: 1/64", the
#: finest line a builder can resolve on a printed detail. It exists because a tip can land
#: exactly ON a band's own boundary — the 2026-08-29 stack-width detail at the attic's
#: rafter plate puts the deck-vb arrow on that band's outboard corner, 0.003" out — and a
#: strict even-odd test calls a point on the edge of the band it names "outside" it. The
#: bug this test was written for is a whole band's width of error (5.4% of the stack per
#: layer, cumulative), not three thousandths.
_CONTAINMENT_TOLERANCE_IN = 1.0 / 64.0


def _contains(points, point) -> bool:
    """Even-odd point-in-polygon, on the outline exactly as it was drawn.

    Tolerant at the boundary by ``_CONTAINMENT_TOLERANCE_IN``: a tip within that of the
    outline counts as contained however the even-odd rule falls on the edge itself.
    """
    u, z = point
    inside = False
    count = len(points)
    for index in range(count):
        (u0, z0), (u1, z1) = points[index], points[(index + 1) % count]
        if (z0 > z) != (z1 > z) and u < u0 + (u1 - u0) * (z - z0) / (z1 - z0):
            inside = not inside
    if inside:
        return True
    return _distance_to_outline(points, point) <= _CONTAINMENT_TOLERANCE_IN


def _distance_to_outline(points, point) -> float:
    """Shortest distance from ``point`` to the closed polyline through ``points``."""
    u, z = point
    best = float("inf")
    count = len(points)
    for index in range(count):
        (u0, z0), (u1, z1) = points[index], points[(index + 1) % count]
        du, dz = u1 - u0, z1 - z0
        span = du * du + dz * dz
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((u - u0) * du + (z - z0) * dz) / span))
        best = min(best, math.hypot(u - (u0 + t * du), z - (z0 + t * dz)))
    return best


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


# --- the ladder reads in the drawing's order ---------------------------------------------

def test_the_roof_ladder_steps_the_same_way_the_roof_stacks(catlin_model):
    """A ladder whose rungs run one way and whose targets run the other is a cat's cradle.

    The eave's ten roof labels stepped DOWN from the roofing while their targets climbed UP
    from the rafter, so every leader crossed every other one and the column read
    rafter-at-the-top over a roof drawn roofing-at-the-top. Rung order and band order are the
    same order, and the only way to be sure of that is to sort on the elevation the band was
    actually drawn at.
    """
    scene = _eave(catlin_model)
    # A ladder rung says `<layer> <n>"` and nothing else — the continuity callouts share the
    # layer and the elbow shape but point at control planes, not at bands. A roof rung then
    # carries its band's own elevation in the anchor and its rung height in `at`; a wall
    # rung's two are equal, which is what tells the two ladders apart.
    rung_text = _RUNG_TEXT
    rungs = [(n.at[1], n.anchor.xy[1]) for n in scene.nodes
             if isinstance(n, Leader) and n.layer == "A-ANNO-TEXT"
             and rung_text.match(n.text) and abs(n.at[1] - n.anchor.xy[1]) > 1e-9]
    assert len(rungs) >= 8, f"the eave should ladder its whole roof stack, got {len(rungs)}"
    rungs.sort(key=lambda pair: -pair[0])          # top rung down
    targets = [target for (_rung, target) in rungs]
    assert targets == sorted(targets, reverse=True), (
        "rungs descend, so their targets must descend too — otherwise the leaders cross: "
        f"{targets}")


def test_every_roof_label_lands_inside_the_band_it_names(catlin_model):
    """The arrow end is *measured* off the band, so this is exact, not approximate.

    The ladder used to walk the assembly's own layer spans and step down from the roof
    plane by each layer's thickness — spending a perpendicular offset as a vertical one. On
    catlin's roof the two differ by 5.4%, which is invisible per layer and cumulative down
    the stack: the roofing pointed at the vent mat, the vent mat and the underlayment both
    at the deck, the deck at the polyiso, and the vapour barrier at the ZIP. Five of nine
    named the wrong band and every one of them looked right, because each still landed
    cleanly on *a* layer. Nothing short of containment catches that.
    """
    checked = 0
    for detail in derive_detail_slices(catlin_model):
        scene = build_detail(catlin_model, detail)[0]
        outlines: dict[str, list] = {}
        for node in scene.nodes:
            if isinstance(node, Polyline) and node.layer == "A-ROOF" and node.tag:
                outlines.setdefault(node.tag.rsplit("/", 1)[-1], []).append(node.points)
        for name, tip in _rungs(scene):
            if name not in outlines:   # the rafter and its fill are drawn as members
                continue
            assert any(_contains(points, tip) for points in outlines[name]), (
                f"{detail.key}: the {name!r} arrow lands at {tip}, which is outside "
                f"every {name} band on the sheet")
            checked += 1
    assert checked >= 8, f"only {checked} roof bands were both drawn and laddered"


def test_a_leader_points_where_its_arrowhead_lands(catlin_model):
    """``anchor`` is not drawn — by anything — so it may not be the truth of a leader.

    ``pdf_writer`` annotates ``at → to``, ``dxf_writer`` adds a two-point leader over the
    same pair, and the viewer's ``DetailCanvas`` draws the same segment. The roof ladder
    once carried the point on the band in ``anchor`` and a shoulder at the label's own row
    in ``to``, describing an elbow that no back end has ever drawn: the arrow stopped at the
    shoulder, several inches off the band, while the IR looked correct. A ladder leader
    keeps one point so that cannot recur.
    """
    scene = _eave(catlin_model)
    for node in scene.nodes:
        if not isinstance(node, Leader) or not _RUNG_TEXT.match(node.text):
            continue
        assert node.anchor.xy == node.to, (
            f"{node.text!r} claims to point at {node.anchor.xy} but its arrowhead lands at "
            f"{node.to}")

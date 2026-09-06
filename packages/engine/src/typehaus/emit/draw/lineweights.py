"""The lineweight hierarchy, one ladder and five names (→ 30 §Graphics).

A construction drawing is read by line weight before it is read by anything else. A reader
scanning a section sees, in order: what is CUT, what is seen in PROFILE beyond the cut,
what is a surface or a pattern, and what is reference — a grid, a dimension, a leader. That
ordering is the drawing's structure, and it only works if the ratio between the heavy and
the light is large enough to survive a plotter, a photocopier and a phone screen. ISO 128-2
puts the floor at **2:1** thick to thin; this module's :data:`CUT` over :data:`REFERENCE` is
3.3:1.

Before this there were thirteen distinct literals across about twenty modules — 0.13, 0.18,
0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8 — with 0.3 and 0.35 both in heavy use
and no rule saying which meant what. Two of them printing side by side is not a hierarchy,
it is noise with a standard deviation.

The **ladder** is ISO 128-2's preferred series, so every weight is a real pen a plotter
knows: 0.13 · 0.18 · 0.25 · 0.35 · 0.50 · 0.70 · 1.00 mm. The **names** are what a module
should reach for; the numbers are which rung the name lands on. Add a name before adding a
number — a fourteenth literal is how the last thirteen happened.
"""

from __future__ import annotations

#: ISO 128-2 preferred line widths, mm. Every constant below is one of these.
LADDER = (0.13, 0.18, 0.25, 0.35, 0.50, 0.70, 1.00)

#: The material the cut plane passes through: wall structure, a slab, a footing, a member
#: in section. Heaviest thing on the sheet, and the reason a section reads as a section.
CUT = 0.50

#: A heavier cut for a whole-building section, where the cut outline is the subject and the
#: interior of every band is drawn inside it. One rung up, so the two never tie.
CUT_HEAVY = 0.70

#: Material seen BEYOND the cut plane, and the outline of anything drawn in elevation — a
#: door leaf, a fixture, a stair beyond. Half of ``CUT``, which is the classic pairing.
PROFILE = 0.35

#: Surfaces, hatches, layer boundaries inside a cut band, furniture, the fine linework of a
#: symbol. The bulk of a drawing by count, and it must not compete with ``PROFILE``.
LIGHT = 0.25

#: Everything that is not the building: dimension lines and their ticks, leaders, grid
#: lines, match lines, the notes band's rules, a bubble outline.
REFERENCE = 0.18

#: The lightest rung — construction lines, an underlay, a centreline, anything a reader
#: should be able to ignore. Below this a line does not survive a photocopier.
FAINT = 0.13

#: Flashing and sheet metal, which convention draws heavy and continuous however thin the
#: material is: a 0.024" aluminium band drawn at its true thickness is invisible, and the
#: point of drawing it is to say the lap order.
FLASHING = 0.50

#: Named for the ratio it guarantees rather than asserted in a comment: ISO 128-2 wants at
#: least 2:1 between the heaviest and lightest weights that share a drawing.
MIN_THICK_THIN_RATIO = 2.0


def snap(width: float) -> float:
    """The nearest rung of :data:`LADDER` to ``width``.

    For a caller that still holds a literal — an authored ``Polyline.lineweight`` from a
    house, or an import. It quantises rather than rejects, because a drawing with a
    slightly wrong pen is a drawing and a drawing with an exception in it is not.
    """
    return min(LADDER, key=lambda rung: abs(rung - width))

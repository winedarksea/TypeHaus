"""Keyed-note bubbles: the K1 on the drawing that points at the K1 in the legend.

A general note applies to the whole detail and needs no pointer. A keyed note is *about a
place* — this flashing, that block — and a construction set says so with a bubble on the
drawing carrying the key, and the same key against the note text in the notes column. That
pairing is the whole of NCS keynoting, and this module draws half of it; the other half is
``SheetNoteSet.sheet_lines``, which already prints the keys.

**A bubble is a Polyline, never a Symbol.** ``plan_marks`` documents why and it is worth
restating: both writers dispatch ``Symbol`` off a closed vocabulary of names, and a name
that is not in it falls through to the ``else`` branch — where it renders as *a window glass
bar*. A six-point polyline plus a centred ``Text`` needs no writer change at all and cannot
render as something else.

Keys are minted **per note file, in authored order**, not per sheet.
``basement_to_framed_wall_detail.md`` reaches six details; numbering per sheet would give
the same note K3 on one and K7 on the next, and a builder cross-referencing two sheets of
the same wall would be reading two different schemes.

No new ``Scene`` field. ``model_dump_json`` emits defaults, so any field added to ``Scene``
would append a line to all 87 goldens — including the 66 with no notes at all. The legend
lives in ``Scene.notes`` and the bubbles in ``Scene.nodes``, both shapes that already exist.
"""

from __future__ import annotations

import math

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw.lineweights import LIGHT
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, DIM_TEXT_PT, model_in_per_pt

#: The bubbles' own layer, so a writer or a viewer can switch them independently of the
#: leader text they sit beside.
KEY_LAYER = "A-ANNO-KEYN"

#: A circle drawn as a polygon. Sixteen sides is what ``plan_marks`` uses for its window
#: bubble and it reads as a circle at every scale a detail prints at.
_SEGMENTS = 16

#: How far the bubble stands off the anchor point, in bubble radii, along +u. Far enough
#: that the outline never sits on the thing it points at.
_STANDOFF_RADII = 2.2


def bubble_radius_in(scale: float | None = None) -> float:
    """Bubble radius in **model** inches: three characters of ``DIM_TEXT_PT`` lettering.

    Three because ``K10`` is the widest key a file's note budget allows. Derived the way
    ``plan_marks.BUBBLE_RADIUS_IN`` is, but taking the *drawing's* scale rather than
    ``PLAN_RESERVATION_SCALE``, because a detail is not a plan: at 1-1/2" = 1'-0" a bubble
    sized off the plan reservation is eight times too big and swallows the junction it is
    pointing at. Falling back to the plan scale keeps a scaleless caller working.
    """
    return 3.0 * DIM_TEXT_PT * CHAR_ASPECT * model_in_per_pt(scale or PLAN_RESERVATION_SCALE)


def bubble_nodes(key: str, at: tuple[float, float], scale: float | None = None) -> list:
    """The outline and the lettering for one bubble centred at ``at`` (model inches)."""
    ux, uz = at
    radius = bubble_radius_in(scale)
    points = tuple(
        (ux + radius * math.cos(2 * math.pi * i / _SEGMENTS),
         uz + radius * math.sin(2 * math.pi * i / _SEGMENTS))
        for i in range(_SEGMENTS)
    )
    return [
        Polyline(points=points, layer=KEY_LAYER, closed=True, lineweight=LIGHT),
        Text(anchor=(ux, uz), content=key, height_pt=DIM_TEXT_PT, layer=KEY_LAYER,
             align="center"),
    ]


def bubble_extent(at: tuple[float, float],
                  scale: float | None = None) -> tuple[float, float, float, float]:
    """``(u0, z0, u1, z1)`` the bubble occupies — what the dodger has to keep clear of."""
    ux, uz = at
    radius = bubble_radius_in(scale)
    return (ux - radius, uz - radius, ux + radius, uz + radius)


def standoff(point: tuple[float, float], scale: float | None = None) -> tuple[float, float]:
    """Where a bubble anchored at ``point`` sits: outboard along +u, at the same height."""
    return (point[0] + _STANDOFF_RADII * bubble_radius_in(scale), point[1])

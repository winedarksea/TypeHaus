"""Opening schedule marks and their bubbles (→ 20 §Drawing IR, A-601).

Full authoring tags are under the writers' 4 pt legibility floor at any plan scale, so the
drawing marks *which schedule row*, not the tag, and the schedule says the rest.

**The mark is per TYPE, not per opening**, and that is the convention rather than a
shortcut: a door/window schedule is a schedule of *types* (A-601's own third column is
``opening.type_ref``), and what a reader needs off the plan is "this is the same unit as
that one" — which fifteen door types and sixteen window types answer in two or three
characters, and eighty per-opening numbers do not.

The mark ladder is derived from the model, deterministically, ordered by type tag: the same
house always mints the same marks, and an opening keeps its mark when an unrelated one is
added ahead of it in the plan source. An opening with no ``type_ref`` gets no mark — A-601
prints ``RO`` for it and there is nothing to key to. Nothing is drawn for it rather than a
mark that points at no row.

**A-601 does not print the Mark column yet.** ``schedules/architectural.py`` builds its rows
from ``(tag, kind, type_ref, size)``; adding ``opening_type_marks(model)`` as a fifth value
closes the key and is the one outstanding half of this.

The bubble is a ``Polyline``, not a ``Symbol``: both writers dispatch symbols by name off a
closed vocabulary (``SYMBOL_NAMES_WITH_DEDICATED_GLYPH``) and an unlisted name is drawn as
a *window glass bar*, not as nothing — so a new glyph is a writer change, and a mark bubble
does not need one. A circle reads window, a hexagon reads door, which is the ordinary
split.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, DIM_TEXT_PT, model_in_per_pt
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

MARK_LAYER = "A-ANNO-SYMB"

#: Radius of a mark bubble, model inches — sized to hold a three-character mark at
#: ``DIM_TEXT_PT`` at the scale plan annotation reserves against.
BUBBLE_RADIUS_IN = 3.0 * DIM_TEXT_PT * CHAR_ASPECT * model_in_per_pt(PLAN_RESERVATION_SCALE)

#: How far off the wall a bubble's centre stands, meters — clear of the glazing bar and of
#: the door leaf, on the wall's outward normal.
BUBBLE_STANDOFF_M = 0.30

_CIRCLE_SEGMENTS = 16


def opening_type_marks(model: ResolvedModel) -> dict[str, str]:
    """``type_ref -> mark`` for every opening type the model actually uses.

    ``D1..Dn`` for doors, ``W1..Wn`` for windows, numbered by sorted type tag. Keyed on the
    *type*, so this is also the mapping A-601 needs to print its Mark column.
    """
    doors: set[str] = set()
    windows: set[str] = set()
    for opening in model.openings:
        if opening.type_ref is None:
            continue
        (doors if opening.is_door else windows).add(opening.type_ref)
    marks: dict[str, str] = {}
    for prefix, tags in (("D", doors), ("W", windows)):
        for index, tag in enumerate(sorted(tags), start=1):
            marks[tag] = f"{prefix}{index}"
    return marks


def preferred_normal(center: tuple[float, float], normal: tuple[float, float],
                     rooms: list[Polygon]) -> tuple[float, float]:
    """Which side of the wall the bubble goes on: the side that lands in a room.

    ``wall_frame``'s normal is the wall's own left-hand normal, not an outward one — it
    follows the authored axis direction, so on catlin's west wall it points out of the
    building and on the east wall it points into it. Taking it as given put four window
    bubbles out in the west dimension tier and the rest inside. A bubble belongs on the
    occupied side, so the test is occupancy: prefer whichever offset point falls inside a
    room on this storey, and keep the wall's own normal when neither or both do (an
    exterior wall with unbuilt space each side has no better answer).
    """
    plus = Point(center[0] + normal[0] * BUBBLE_STANDOFF_M,
                 center[1] + normal[1] * BUBBLE_STANDOFF_M)
    minus = Point(center[0] - normal[0] * BUBBLE_STANDOFF_M,
                  center[1] - normal[1] * BUBBLE_STANDOFF_M)
    in_plus = any(room.contains(plus) for room in rooms)
    in_minus = any(room.contains(minus) for room in rooms)
    return (-normal[0], -normal[1]) if in_minus and not in_plus else normal


def emit_opening_mark(b: SceneBuilder, mark: str, center: tuple[float, float],
                      normal: tuple[float, float], is_door: bool,
                      uid: str) -> tuple[float, float, float, float]:
    """Draw one bubbled mark standing off ``center`` along the wall's outward ``normal``.

    Returns the bubble's ``(minx, miny, maxx, maxy)`` box in metres. A mark stands *into*
    the room it serves, which is where the room's own label block sits, and on catlin's
    main floor ``CLG 8'-11 1/2"`` ran straight through ``D14``. The block is the thing that
    can move — a mark is tied to its opening — so the block is the thing that gets told
    where the bubbles are.
    """
    at = (center[0] + normal[0] * BUBBLE_STANDOFF_M,
          center[1] + normal[1] * BUBBLE_STANDOFF_M)
    ux, uz = _in(at)
    sides = 6 if is_door else _CIRCLE_SEGMENTS
    # A hexagon is drawn point-up so it cannot be mistaken for the circle at small scale.
    phase = math.pi / 2 if is_door else 0.0
    points = tuple(
        (ux + BUBBLE_RADIUS_IN * math.cos(phase + 2 * math.pi * i / sides),
         uz + BUBBLE_RADIUS_IN * math.sin(phase + 2 * math.pi * i / sides))
        for i in range(sides)
    )
    b.add(Polyline(points=points, layer=MARK_LAYER, closed=True, lineweight=0.18, uid=uid))
    b.add(Text(anchor=(ux, uz), content=mark, height_pt=DIM_TEXT_PT,
               layer=MARK_LAYER, align="center"))
    radius_m = BUBBLE_RADIUS_IN * M_PER_IN
    return (at[0] - radius_m, at[1] - radius_m, at[0] + radius_m, at[1] + radius_m)

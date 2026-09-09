"""In-wall backing: a band of solid material a finish trade fastens into.

Backing is the one framing decision a house cannot revisit. Once drywall and tile close a
wall, a twelve-dollar plywood strip becomes a four-figure retrofit, so it is authored where
a screw *might* land rather than where one lands today — a grab bar nobody has bought yet,
a towel bar that will move, a shower valve that gets replaced in twenty years.

**Why this is an element and not a ``FramingSpec`` field.** ``FramingSpec.blocking_heights``
already emits a flat course between studs, but it lives on the *assembly*, so backing one
wall means cloning its assembly — for a wet wall, re-running its Glaser gate, its energy
table and ``truss_wall_opening_support`` against an unreviewed tag — to bill forty board
feet. ``houses/catlin/plan/furniture_types.py`` reached that dead end and wrote it down.
A band is also the wrong *shape* for that field: a course is one member thick (1.5") for a
whole wall, and what a trade needs is a 12"-tall run over a stated length.

The two live side by side. ``blocking_heights`` stays the right tool for a rhythm that
belongs to a wall type; this is the tool for a band that belongs to a place.

**Nothing here is code.** Outside the handrail case — IRC **Table R301.5**'s 200 lb
concentrated load, adopted by Minnesota via Minn. Rules ch. 1309 — no residential code
requires any of this. ADA does not reach a private residence and the IRC sets no grab-bar
load at all. The model spec worth borrowing is California's CRC R328.1.1: 2x8 nominal
minimum, 32" to 39-1/4" above the finished floor, flush with the framing. So the engine's
verdict on backing is ADVISORY (→ ``checks/advisory/backing.py``), never a FAIL.

Not to be confused with **fireblocking** (IRC R302.11), which is a draft stop that fills the
cavity rather than a fastening target laid flat on the stud face. An 8' wall triggers no
horizontal fireblock at all, so every horizontal 2x in an ordinary bathroom is this, not
that. ``checks/code/mn_residential/profile.py`` declares R302.11 outside its coverage and
this element does not change that.
"""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length


@register_element
class WallBacking(Element):
    """A band of backing on one wall, over a run of it, at a stated height.

    ``start``/``length`` are stations measured along the wall axis from its start node, the
    same frame ``PanelingSpan`` uses. Both ``None`` means the wall's whole run.
    """

    #: The wall the band is fastened to. Unlike ``Fixture.wall_ref`` — which names the *wet*
    #: wall a fixture plumbs into — this is the wall the band physically lands in, and a ref
    #: that resolves to nothing is an ERROR rather than a silently deleted band.
    wall_ref: str
    #: Which stud face carries the band: "left" / "right" relative to the authored wall
    #: direction, or "both" for a through-wall band let in from each side.
    face: str = "left"
    #: Station from the wall's start node. None = from the start of the wall.
    start: Length | None = None
    #: Run along the wall. None = to the end of the wall.
    length: Length | None = None
    #: Band bottom above the storey datum.
    elevation: Length
    #: Band height. A CRC R328.1.1 grab-bar band is 7 1/4"; catlin's wet-wall strip is 12".
    height: Length
    #: Cross-section, parsed by ``resolve/framing/profiles.cross_section``. **Write the
    #: decimal**: "0.75x12.0" parses, "3/4x12" falls back silently to 1.5 x 5.5 and draws a
    #: plywood strip as a 2x6.
    profile: str = "0.75x12.0"
    #: Catalog material tag. Sets ``FramedMember.material``, which both keeps the band its
    #: own takeoff row and stops the viewer painting plywood in the generic framing grey.
    material_ref: str = "struct-1-plywood"
    #: What this band is for, in words — "grab bar", "upper cabinet rail", "handrail
    #: brackets". Printed by the coverage advisory and by the framing schedule, because a
    #: framer who knows why a block is there puts it in the right place.
    purpose: str = ""


register_constructor("WallBacking", WallBacking)

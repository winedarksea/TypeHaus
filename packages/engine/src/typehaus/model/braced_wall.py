"""A braced wall panel: the designer's decision about where a line spends its bracing.

IRC R602.10 grades a braced wall LINE by the sum of its PANELS. The lines are derivable
(``resolve/braced_walls.py``); the panels are not, because a panel is a choice — where to
put the full-height sheathed segment that counts, what method it is built to, and what
ends it. This element records that choice and nothing more.

**A designation, not a solid.** It draws on S-103 and grades in
``checks/structural/braced_wall*.py``; it has no IFC/glTF geometry (the ``Slice`` /
``Transition`` precedent). A house files these in a ``# haus: editable`` file only so
``haus fmt`` can mint their uids — they are not UI-movable.

**What is deliberately absent.** No ``adjacent_opening_height`` (derived from the wall's
openings), and no aspect ratio, nail schedule or unit shear: a panel that needs those is
an engineered shear wall, which is ``Wall.shear_panel`` and is out of R602.10's scope.
"""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length

#: R602.10.4 methods the prescriptive grading implements. Anything else is refused by the
#: check rather than read against a row it does not own.
BRACING_METHODS = ("CS-WSP", "WSP")


@register_element
class BracedWallPanel(Element):
    """One braced wall panel on one wall, over a run of it.

    ``start``/``width`` are stations along the wall axis from its start node (the
    ``WallBacking`` frame); both ``None`` is the whole wall. A panel that crosses a wall
    butt is authored once per wall and merged by the resolver.
    """

    #: The wall the panel is sheathed on. A ref that resolves to nothing is an ERROR.
    wall_ref: str
    #: Station from the wall's start node. None = from the start of the wall.
    start: Length | None = None
    #: Run along the wall. None = to the end of the wall.
    width: Length | None = None
    #: IRC R602.10.4 method, as a plan reviewer reads it.
    method: str = "CS-WSP"
    #: A real ``Connector`` tag (kind HOLD_DOWN) at this panel's end, for R602.10.7's
    #: 800-lb end condition. A tag, never prose: a device the model cannot find would grade
    #: as no device (the ``ShearPanelSpec.holdown`` trap).
    hold_down_ref: str | None = None
    #: Why the panel is here, for the drawing and the reviewer.
    note: str = ""


register_constructor("BracedWallPanel", BracedWallPanel)

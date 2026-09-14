"""Where the building's structural connections *are* — a leaf package with four readers.

Most of the hardware in a house is derived, not authored: nobody draws three hundred and
thirty-two hurricane ties. Until this package existed, that derivation lived inside
``takeoff/``, which made a connection's location a private fact of the bill of materials:
``resolve`` is upstream of ``takeoff`` and cannot import it, so a derived tie could be
specified, billed and graded — and never drawn. The ties were real and invisible.

So the *locating* is separated from the *billing*. A :class:`~typehaus.joints.model.Joint`
says a connection of some role exists at a point, at an elevation, on an axis, between
named members. Four readers ask for the same list and each does its own job with it:

* ``takeoff/{uplift,anchors,hangers}.py`` group joints into BOM rows;
* ``checks/structural/uplift_path.py`` counts them against the legs of the load path;
* ``resolve/connector_markers.py`` draws one marker solid each;
* ``emit/draw/roofframingplan.py`` puts the roof's on the framing plan.

The check's no-drift property is what this is *for*: it used to guarantee the report and
the order agreed about the count, and now the drawing cannot drift from either.

**A leaf.** This package imports ``model`` / ``resolve`` / ``quantities`` / ``hardware``
and nothing else — never ``checks``, never ``takeoff``, never ``emit``. A joint is a fact
about the building; a row and a finding are two opinions about that fact, and a locator
that could see either would be tempted to answer differently for each.
``tests/test_joints_leaf.py`` walks the imports and fails on a violation.
"""

from typehaus.joints.derive import derived_joints
from typehaus.joints.model import Joint

__all__ = ["Joint", "derived_joints"]

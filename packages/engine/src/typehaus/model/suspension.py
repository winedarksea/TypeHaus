"""A load hung from the floor framing overhead: a hammock chair, a hanging daybed.

``SuspensionAnchor`` is hosted on the item it carries and has no position of its own, so a
dragged chair takes its anchor along and the anchor's framing (one LVL joist line,
``resolve/suspension_anchors.py``) is re-derived on every build. Deleting the anchor deletes
the framing. ``structural.suspension_anchor`` grades the load path, oracled by the house's
``notes/hanging_seat_anchor.md``. Furniture, not engineering: nothing here reaches the
``haus engineering`` register.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.findings import Finding, Result, Severity
from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.model.types import FurnitureType
from typehaus.quantities import Length, Point2D, inch, pt


class HangingSeatType(FurnitureType):
    """A seat hung from one point overhead. ``height`` is the seat bottom to its own ring;
    the suspension (rope, chain) between that ring and the anchor is not part of the type."""

    #: The occupant load the product is rated for, lb, and the document that says so.
    rated_load_lb: float
    rated_load_source: str
    #: Self weight, lb: added to the anchor's demand unfactored.
    weight_lb: float = 0.0
    #: Plan distance from the hang point to a wall the seat must keep (the maker's figure).
    wall_clearance: Length
    #: Seat bottom above the finished floor when occupied.
    ground_clearance: Length
    #: Ceiling-to-ring suspension the supplied kit can be set to, (min, max).
    suspension_range: tuple[Length, Length]


@register_element
class SuspensionAnchor(Element):
    """One hang point in the floor framing overhead, at ``offset`` in the carried item's frame."""

    #: The placeable (by tag) this anchor holds up; its plan point and rotation place it.
    carries: str
    offset: Point2D = pt(inch(0), inch(0))
    #: The rated static load this anchor answers, lb (before the house's impact factor).
    design_load_lb: float
    #: The joist line laid at the anchor's station, and its grade in ``library/member_grades``.
    framing_member: str = "2-1.75x11.875 LVL"
    member_grade: str = "microllam-lvl-2.0e"
    #: ``StructuralHardware`` tags, top (at the member) to bottom.
    hardware: tuple[str, ...] = ()
    #: Through-bolts in the saddle, and their diameter: the connection the check grades.
    bolts: int = 2
    bolt_diameter: Length = inch(0.625)
    #: The floor system to frame in. ``None``: the one plumb above, on the storey above.
    floor_ref: str | None = None
    source: str = ""


register_constructor("SuspensionAnchor", SuspensionAnchor)
register_constructor("HangingSeatType", HangingSeatType)


def suspension_anchors(plan) -> Iterator[SuspensionAnchor]:
    return (el for el in plan.all_elements() if isinstance(el, SuspensionAnchor))


def dangling_carries(plan) -> list[Finding]:
    """An anchor whose ``carries`` names nothing is a load ERROR, never a silent no-op."""
    tags = {el.tag for el in plan.all_elements()}
    return [Finding(
        severity=Severity.ERROR, check_id="loader.suspension_anchor_carries",
        message=f"SuspensionAnchor {anchor.tag} carries {anchor.carries!r}, which is not "
                "an authored element",
        element_tags=(anchor.tag,), result=Result.FAIL,
        fix_hint="point `carries` at the hung item's tag, or delete the anchor with it")
        for anchor in suspension_anchors(plan) if anchor.carries not in tags]

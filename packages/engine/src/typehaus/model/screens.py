"""Open vertical timber screens, distinct from structural columns and rated guards."""

from typing import Literal

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


@register_element
class SlatScreen(Element):
    start: Point2D
    end: Point2D
    base_elevation: Length
    height: Length
    slat_face: Length
    slat_depth: Length
    clear_gap: Length
    assembly: str
    supported_by: str
    engineering_note: str | None = None
    # --- is this screen the guard, or is it decoration in front of one? ------------------
    # A screen of on-edge slats at a clear gap under 4", framed into cross rails that carry
    # to columns, satisfies IRC R312.1 on its own terms and needs no railing beside it. Say
    # so here and ``checks/guard_lines.py`` presents it to every guard rule; leave it and the
    # screen is a screen, which is the safe default — a decorative slat panel standing in
    # front of a real guard must not be read as one.
    #
    # ``clear_gap`` is the R312.1.3 sphere dimension and ``height`` the R312.1.1 one, so a
    # screen claiming this role is graded on the numbers it already states rather than on
    # the claim. It carries no handrail role: R311.7.8 graspability is a separate fixture.
    role: Literal["screen", "guard"] = "screen"


register_constructor("SlatScreen", SlatScreen)

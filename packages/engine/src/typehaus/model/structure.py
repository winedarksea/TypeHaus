"""Foundation & structural elements (#27 — schema in M1, sheets in M3)."""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.elements import Wall
from typehaus.model.refs import FaceRef
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


@register_element
class FoundationWall(Wall):
    """A Wall in every structural sense, distinguished by kind (→ 11 §Foundations).

    Carries explicit top/bottom elevations for the walkout/sunken-garden condition."""

    top_elevation: Length | None = None
    bottom_elevation: Length | None = None


@register_element
class Footing(Element):
    """Strip/spread footing auto-following its parent's geometry (→ IfcFooting)."""

    under: str  # wall or post tag
    width: Length
    depth: Length


@register_element
class Pad(Element):
    """Isolated pad / thickened slab (→ IfcFooting)."""

    outline: tuple[Point2D, ...]
    thickness: Length


@register_element
class Post(Element):
    """A point structural member (→ IfcColumn)."""

    position: Point2D
    size: str = "6x6"
    height: Length | None = None
    supported_by: str | None = None  # pad/footing tag


@register_element
class Beam(Element):
    """An axis structural member; a valid bearing ref for JoistSpec (→ IfcBeam)."""

    start_node: str
    end_node: str
    size: str = "3.5x11.875 LVL"
    bearing_refs: tuple[str, ...] = ()
    datum: FaceRef | None = None


for _name, _obj in (
    ("FoundationWall", FoundationWall),
    ("Footing", Footing),
    ("Pad", Pad),
    ("Post", Post),
    ("Beam", Beam),
):
    register_constructor(_name, _obj)

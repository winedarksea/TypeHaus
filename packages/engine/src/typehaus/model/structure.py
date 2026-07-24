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
    bottom_elevation: Length | None = None


@register_element
class FootingBedding(Element):
    """Sub-footing excavation/bedding prep beneath a strip Footing.

    Digs an extra ``undercut`` below the footing underside for a compacted washed-stone
    bed on non-woven geotextile (no-slip) with a drain tile — breaks direct footing-to-wet-
    clay contact (thermal loss) and drains the bearing surface. ``perimeter_insulation``
    continues the foundation wall's exterior rigid foam down over the footing sides;
    ``cast_foam_in_aggregate`` optionally casts foam into the stone itself for a further
    thermal cut. Never resizes/moves the footing — an annotation + bearing-prep record."""

    host_ref: str  # Footing tag
    undercut: Length  # additional depth dug below the footing underside
    aggregate: str = "ASTM C33 #57 washed crushed stone"
    geotextile: bool = True
    drain_tile: bool = True
    perimeter_insulation: Length | None = None
    cast_foam_in_aggregate: bool = False


@register_element
class Post(Element):
    """A point structural member (→ IfcColumn)."""

    position: Point2D
    size: str = "6x6"
    height: Length | None = None
    supported_by: str | None = None  # pad/footing tag
    assembly: str | None = None  # optional finish assembly (e.g. paint) for render/IFC material


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
    ("FootingBedding", FootingBedding),
    ("Post", Post),
    ("Beam", Beam),
):
    register_constructor(_name, _obj)

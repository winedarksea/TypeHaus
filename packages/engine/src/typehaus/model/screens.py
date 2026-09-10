"""Open vertical timber screens, distinct from structural columns and rated guards."""

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


register_constructor("SlatScreen", SlatScreen)

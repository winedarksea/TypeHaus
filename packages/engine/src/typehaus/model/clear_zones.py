"""Authored finite volumes reserved for access, activities or future services."""

from typing import Literal, Self

from pydantic import model_validator

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


@register_element
class ClearZone(Element):
    """An immovable reservation, measured above its storey's finished floor.

    Storey membership comes from ``PlanModel.elements``, as for Rooms and Soffits.
    Exceptions are exact element tags; neither a trade nor a tag pattern is a pardon.
    Both policies constrain new routes; recommended permits an unfinished campaign to
    expose existing intrusions without failing the house's integrity gate.
    """

    outline: tuple[Point2D, ...]
    bottom: Length
    top: Length
    purpose: str
    policy: Literal["required", "recommended"] = "required"
    except_tags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_volume(self) -> Self:
        if len(self.outline) < 3:
            raise ValueError("ClearZone outline needs at least three points")
        if self.bottom.meters < 0 or self.top.meters <= self.bottom.meters:
            raise ValueError("ClearZone requires 0 <= bottom < top above finished floor")
        if not self.purpose.strip():
            raise ValueError("ClearZone purpose must describe the reservation")
        return self


register_constructor("ClearZone", ClearZone)

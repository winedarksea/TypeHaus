"""Steel strap braces: flat coil strap cut to length and nailed between two member faces."""

from __future__ import annotations

from pydantic import field_validator

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D, inch

#: Galvanized sheet thickness by gauge, inches (base steel as the strap makers publish it).
GAUGE_THICKNESS_IN: dict[int, float] = {
    12: 0.1046, 14: 0.0747, 16: 0.0598, 18: 0.0478, 20: 0.0359,
}


@register_element
class StrapBrace(Element):
    """A tension-only flat steel strap between two points (one leg of an X-brace).

    Resolves to one thin raked member lying in a vertical plane (``resolve/strap_braces``)
    and bills as HARDWARE, never as lumber (``takeoff/strap_braces``). Each end is a plan
    point plus a project-frame absolute elevation at the centre of the strap's width.
    """

    start: Point2D
    start_elevation: Length
    end: Point2D
    end_elevation: Length
    #: Signed offset of the strap's plane from the start→end plan line, + to the LEFT of
    #: start→end: author member centrelines and push the strap onto the member face.
    face_plane: Length = inch(0)
    product: str  # catalog model, e.g. "CS16"
    width: Length  # strap width, e.g. 1-1/4"
    gauge: int  # sheet gauge; thickness from GAUGE_THICKNESS_IN
    connects: tuple[str, ...] = ()  # member tags it joins
    fasteners_each_end: int  # nail count per end
    fastener: str = ""  # e.g. '10d x 1-1/2" HDG'
    source: str = ""

    @field_validator("gauge")
    @classmethod
    def _known_gauge(cls, value: int) -> int:
        if value not in GAUGE_THICKNESS_IN:
            raise ValueError(f"gauge {value} not in {sorted(GAUGE_THICKNESS_IN)}")
        return value

    @property
    def thickness(self) -> Length:
        return inch(GAUGE_THICKNESS_IN[self.gauge])


register_constructor("StrapBrace", StrapBrace)

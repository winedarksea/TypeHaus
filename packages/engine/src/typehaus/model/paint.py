"""Paint systems, declared once (decision #113): the ``TrimStandard`` / ``DrywallStandard`` pattern.

A ``PaintSpec`` on a coating ``Material`` says what the painter buys: sheen, colour, primer,
coats and the schedule mark. The house's one ``PaintStandard`` names which system each kind
of surface takes; ``resolve/room_paint.py`` applies it face by face, and
``takeoff/trim_paint.py`` bills the trim and door systems off the derived trim and doors.
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element, HausModel
from typehaus.model.enums import Occupancy
from typehaus.model.registry import register_constructor, register_element

Sheen = Literal["flat", "matte", "eggshell", "satin", "semi-gloss", "gloss"]

#: Sheen -> the existing ``Material.finish`` render recipe; no new recipe per sheen.
SHEEN_FINISH: dict[str, str] = {
    "flat": "matte-latex", "matte": "matte-latex", "eggshell": "matte-latex",
    "satin": "satin-enamel", "semi-gloss": "satin-enamel", "gloss": "satin-enamel",
}


class PaintSpec(HausModel):
    """One paint system as specified: what the schedule prints and the RFQ asks for."""

    sheen: Sheen
    colour: str
    # The schedule mark ("PT-1") and the use it prints ("Walls").
    mark: str | None = None
    use: str | None = None
    # A coating Material tag; the primer rides in this system's rate, not as a layer.
    primer_ref: str | None = None
    coats: int = 2

    @property
    def finish_recipe(self) -> str:
        return SHEEN_FINISH[self.sheen]


register_constructor("PaintSpec", PaintSpec)


@register_element
class PaintStandard(Element):
    """The house's paint systems, one coating Material tag per surface kind.

    One per plan (a second is an ``integrity.paint_standard`` error). Without one, rooms
    paint bare gypsum with the library default and nothing else changes.
    """

    walls: str
    ceilings: str
    # Applied to walls and ceilings of ``wet_occupancies`` rooms.
    wet: str | None = None
    wet_occupancies: tuple[Occupancy, ...] = (Occupancy.BATHROOM, Occupancy.LAUNDRY)
    trim: str | None = None
    doors: str | None = None

    def pick(self, occupancy: Occupancy | None, surface: Literal["walls", "ceilings"]) -> str:
        """The system a room of ``occupancy`` takes on ``surface``."""
        if self.wet is not None and occupancy in self.wet_occupancies:
            return self.wet
        return self.ceilings if surface == "ceilings" else self.walls

    def surface_refs(self) -> tuple[str, ...]:
        """The wall/ceiling systems: an authored coat of one of these is a default coat."""
        return tuple(dict.fromkeys(r for r in (self.walls, self.ceilings, self.wet) if r))

    def material_refs(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.surface_refs(),
                                    *(r for r in (self.trim, self.doors) if r))))


register_constructor("PaintStandard", PaintStandard)

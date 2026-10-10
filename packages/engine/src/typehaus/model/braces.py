"""Braces that are not knee braces: steel coil straps, and a framed band of 45° slats."""

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


@register_element
class SlatBrace(Element):
    """A framed band of 45° slats between two chord posts, each slat a knee brace.

    The frame is a flat ``plate`` sill on ``base_elevation``, a flat ``plate`` under
    ``top_elevation`` (the collector soffit) and a ``centre_post`` at midspan; ``start`` and
    ``end`` are the CHORD centres, and the frame runs between their faces. Each bay is filled
    with ``slat`` stock on edge, ``clear_gap`` apart square to the slats, mirrored so every
    slat rises toward the centre post (a chevron). One ``connector`` at each slat end makes
    each slat work in tension and compression, which is what lets the two bays share the
    push (``notes/canopy_west_band.md`` §3b).

    The layout is ``resolve/slat_braces.slat_layout``'s, one rule for the resolver, the dead
    load and the engineering. Lumber bills off the resolved members; the connectors, the plate
    screws and the centre-post ties bill off this element (``takeoff/slat_braces``).
    """

    start: Point2D
    end: Point2D
    chord_size: str = "6x6"
    base_elevation: Length  # underside of the sill, project-frame absolute
    top_elevation: Length  # top of the top plate (the collector soffit), absolute
    plate: str = "2x6"  # sill and top plate, laid flat
    centre_post: str = "6x6"
    slat: str = "2x4"  # on edge: its thin face in the band's plane
    #: Under 2-1/8" the KBS1Z at neighbouring slat ends overlap (its 3" support leg plus the
    #: next one's 1-1/2" brace leaf at 45°); the resolver refuses that.
    clear_gap: Length = inch(2.25)
    #: Signed offset of the slats' axis from the start→end line, + to the LEFT: set it to
    #: put the slats flush with one face of the frame, where the connectors go.
    plane_offset: Length = inch(0)
    #: A slat shorter than this cannot take a connector leg at both ends and is left out.
    min_slat_length: Length = inch(8)
    connector: str = "KBS1Z"  # one per slat end
    #: A slat whose connector leg would run off its bearing face (a frame corner) is screwed
    #: infill instead, toe-screwed at each end and carrying none of the brace force.
    infill_fastener: str = "SDWS22300DB"
    infill_fasteners_each_end: int = 2
    plate_fastener: str = "SDWS22400DB"
    plate_fasteners: int = 8  # per plate, through the plate into what it bears on
    centre_post_tie: str = "A35Z"
    centre_post_ties_each_end: int = 2
    assembly: str | None = None
    #: The wall whose top plate the sill stands on: its dead load joins that line's.
    supported_by: str | None = None
    connects: tuple[str, ...] = ()
    source: str = ""


register_constructor("SlatBrace", SlatBrace)

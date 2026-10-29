"""Sheet metal and lapped membrane in a section cut: filled, heavy, drawn in lap order.

A 24 ga sheet cut at its true 0.024" is a hairline at any detail scale, and the writer caps a
closed band's outline at half the band's printed width, so it stays one. Convention draws
flashing heavy and continuous instead (``lineweights.FLASHING``): the profile is filled and
stroked as an OPEN ring, which the cap does not touch. The pieces are collected during the
cut and drawn last, bottom sheet first, so each lap prints over the sheet it covers.

Scope is the Image II eave family, and the box gutter, wall-head trim and flashing in a cut
that crosses one. Elsewhere — a garage fascia's formed drip, a window's jamb trim — the cut
keeps its older drawing until those details are reviewed against it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.emit.draw.lineweights import FAINT, FLASHING, LIGHT
from typehaus.emit.draw.scene import Hatch, Polyline
from typehaus.emit.draw.section_clip import clip_polygon
from typehaus.quantities import M_PER_IN
from typehaus.resolve.roof_image_ii import (
    CONNECTION_EAVE,
    CONNECTION_RAKE,
    CONNECTION_RAKE_FOOT,
    CONNECTION_STRIP,
)

PAN_END_CONNECTION = "roof:pan-end"
SEAM_END_CONNECTION = "roof:seam-end"

#: Draw order, bottom sheet first. The field membrane is a roof band, drawn before all of
#: these; then the wall head's trim, the gutter (its roof flange is the lowest metal on the
#: deck), the Extended Eave and the rake that sheds onto it, the strip-in over both flanges,
#: and the pan hemmed around the lot.
_SOLID_RANK = {"flashing": 0, "cladding_trim": 0, "gutter": 1}
_MEMBER_RANK = {
    CONNECTION_EAVE: 2,
    CONNECTION_RAKE_FOOT: 3,
    CONNECTION_RAKE: 3,
    CONNECTION_STRIP: 4,
    SEAM_END_CONNECTION: 5,
    PAN_END_CONNECTION: 6,
}
_MEMBRANE_CONNECTIONS = frozenset({CONNECTION_STRIP})
SHEET_SOLID_CATEGORIES = frozenset(_SOLID_RANK)
_LAYER = "A-ROOF"
#: From this scale (paper inches per foot) the stack's true 1/32" gaps print at ~0.2 mm, and
#: a FLASHING stroke either side fills them: the sheets keep their fill and take the faint
#: rung, so the laps read as separate pieces; an unnamed sheet fills dark, as the heavy line
#: drew it. Below it the convention's heavy line stands.
_GAP_SCALE = 3.0


@dataclass(frozen=True)
class SheetCut:
    """One cut profile waiting for its turn: ``outline`` in metres, section frame."""

    rank: int
    outline: tuple
    uid: str | None
    tag: str
    material: str | None
    membrane: bool = False


def member_sheet_rank(member) -> int | None:
    """Lap rank of a roof member drawn as sheet metal or lapped membrane, else ``None``."""
    return _MEMBER_RANK.get(member.connection) if member is not None else None


def is_membrane(member) -> bool:
    return member is not None and member.connection in _MEMBRANE_CONNECTIONS


def sheet_members_by_uid(host) -> dict:
    """The host's sheet-metal members keyed as their IR part is (``member_uid``)."""
    from typehaus.resolve.geometry_members import member_uid

    return {member_uid(member): member for member in getattr(host, "members", ())
            if member.connection in _MEMBER_RANK}


def image_ii_eave_in_cut(model, plane, crop) -> bool:
    """Whether this cut crosses an Image II eave or rake piece inside its crop."""
    from typehaus.resolve.geometry_members import member_solid
    from typehaus.resolve.geometry_slice import slice_solid

    for roof in model.roofs:
        for member in roof.members:
            if member.connection not in (CONNECTION_EAVE, CONNECTION_RAKE_FOOT):
                continue
            solid = member_solid(member)
            if solid is None:
                continue
            for profile in slice_solid(solid, plane):
                if len(clip_polygon(profile.outline, crop)) >= 3:
                    return True
    return False


def emit_sheet_cuts(b, cuts: list[SheetCut], crop, scale: float | None = None) -> None:
    """Every collected sheet, bottom of the lap first; ties keep their cut order."""
    gaps_print = scale is not None and scale >= _GAP_SCALE
    sheet_weight = FAINT if gaps_print else FLASHING
    membrane_weight = min(LIGHT, sheet_weight)
    for cut in sorted(cuts, key=lambda c: c.rank):
        clipped = clip_polygon(cut.outline, crop)
        if len(clipped) < 3:
            continue
        points = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
        b.add(Hatch(boundary=points, pattern="none" if cut.membrane else "metal",
                    layer="A-WALL-PATT", uid=cut.uid,
                    material=cut.material or ("metal-dark" if gaps_print and not cut.membrane
                                              else None)))
        # An OPEN ring: the writer caps a closed band's stroke at half its printed width,
        # which is exactly what made 24 ga a hairline.
        b.add(Polyline(points=points + (points[0],), layer=_LAYER, closed=False,
                       lineweight=membrane_weight if cut.membrane else sheet_weight,
                       uid=cut.uid, tag=cut.tag))


def solid_sheet_cuts(model, solid, plane) -> list[SheetCut]:
    """A sheet-metal solid's cut profiles (gutter, wall-head trim, flashing), for later."""
    from typehaus.resolve.geometry_slice import slice_part

    element = model.geometry.by_uid(solid.uid)
    if element is None:
        return []
    rank = _SOLID_RANK[solid.category]
    return [SheetCut(rank, tuple(profile.outline), solid.uid, solid.tag,
                     part.catalog.material_ref if part.catalog is not None else None)
            for part in element.parts for profile in slice_part(part, plane)]

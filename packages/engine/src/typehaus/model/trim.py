"""Envelope edge trim / roofing accessories along a deck or roof edge.

A balcony/porch edge carries a small family of long, thin run elements the framing does
not: a PVC fascia board closing the joist ends, a hung gutter at the low (front) edge, a
drip flashing turning the deck membrane down into that gutter, and a counter-flashing at
the high (rear) edge tucked up under the house WRB. Each is authored as a plan-frame
polyline run with a cross-section; the resolver extrudes a thin solid so it reads in the
model, IFC, and take-off instead of living only in a note.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.enums import TrimKind
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


class _EdgeRun(Element):
    """Common shape for a trim run: a plan polyline at an elevation with a cross-section."""

    kind: TrimKind
    path: tuple[Point2D, ...]  # plan-frame run, >= 2 points
    top_elevation: Length  # top of the run, project-frame absolute
    depth: Length  # vertical face height of the run
    thickness: Length  # cross-section thickness (out from the edge)
    material: str = ""  # e.g. "PVC", "aluminum"
    host_ref: str | None = None  # deck/slab/fascia tag the run trims


@register_element
class Fascia(_EdgeRun):
    """A fascia board closing the joist/beam ends along a deck edge (e.g. PVC)."""

    kind: TrimKind = TrimKind.FASCIA


@register_element
class EaveSoffit(_EdgeRun):
    """The panel closing the underside of an eave/rake overhang.

    Named for the eave to keep it distinct from :class:`typehaus.model.floors.Soffit`, the
    interior dropped-ceiling element — different feature, same English word.

    Unlike the other edge runs the soffit lies flat: ``thickness`` is the horizontal width
    it spans (wall face out to the fascia) and ``depth`` is the panel's own thickness, so
    the shared ``_EdgeRun`` extrusion produces a horizontal board rather than a vertical one.
    """

    kind: TrimKind = TrimKind.SOFFIT
    vented: bool = False  # continuous intake venting into the roof's eave-to-ridge channel


@register_element
class Gutter(_EdgeRun):
    """A hung gutter channel at the low edge; ``depth`` is the channel height."""

    kind: TrimKind = TrimKind.GUTTER
    slope: str = ""  # optional drainage note, e.g. "1/16 in/ft to SE downspout"


@register_element
class Flashing(_EdgeRun):
    """Edge/counter flashing. ``kind`` distinguishes a front drip into the gutter from a
    rear counter-flashing tucked into the house WRB."""

    kind: TrimKind = TrimKind.DRIP_FLASHING


class FasciaBoard(HausModel):
    """One layer of a built-up fascia, innermost first (a wood nailer, then a PVC cover)."""

    material: str
    thickness: Length  # horizontal, out from the roof edge
    depth: Length      # vertical face height


class EaveGutter(HausModel):
    """A hung gutter derived along a roof's *level* eave edges.

    The authored :class:`Gutter` run is the right element for a deck or a porch edge, whose
    elevation is a fixed fact. A roof's is not: a raised-heel truss lifts the whole deck plane
    during the envelope stage, so an authored elevation drifts off the roof it hangs from.
    Declaring the channel here instead keeps it on the plane, exactly like the fascia.
    """

    material: str
    depth: Length      # channel height
    thickness: Length  # channel width, out from the fascia's outer face
    top_drop: Length   # top of the channel below the roof plane at the eave edge
    edges: tuple[str, ...] = ()  # footprint edges ("south"/"north"/...); empty = every eave
    slope: str = ""    # optional drainage note, e.g. "1/16 in/ft to the east downspout"


class EaveTrim(HausModel):
    """A roof's edge closure, declared once and derived along every eave and rake.

    The fascia/soffit elevations follow the roof plane — including a truss roof's raised-heel
    lift — so they are *derived* from this declaration rather than authored as absolute
    elevations that would silently drift from the roof they trim.
    """

    fascia: tuple[FasciaBoard, ...] = ()
    soffit_material: str = ""
    soffit_thickness: Length | None = None
    soffit_vented: bool = False
    gutter: EaveGutter | None = None


for _name, _obj in (
    ("Fascia", Fascia),
    ("EaveSoffit", EaveSoffit),
    ("Gutter", Gutter),
    ("Flashing", Flashing),
    ("FasciaBoard", FasciaBoard),
    ("EaveGutter", EaveGutter),
    ("EaveTrim", EaveTrim),
):
    register_constructor(_name, _obj)

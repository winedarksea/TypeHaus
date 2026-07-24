"""Envelope edge trim / roofing accessories along a deck or roof edge.

A balcony/porch edge carries a small family of long, thin run elements the framing does
not: a PVC fascia board closing the joist ends, a hung gutter at the low (front) edge, a
drip flashing turning the deck membrane down into that gutter, and a counter-flashing at
the high (rear) edge tucked up under the house WRB. Each is authored as a plan-frame
polyline run with a cross-section; the resolver extrudes a thin solid so it reads in the
model, IFC, and take-off instead of living only in a note.
"""

from __future__ import annotations

from typehaus.model.base import Element
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
class Gutter(_EdgeRun):
    """A hung gutter channel at the low edge; ``depth`` is the channel height."""

    kind: TrimKind = TrimKind.GUTTER
    slope: str = ""  # optional drainage note, e.g. "1/16 in/ft to SE downspout"


@register_element
class Flashing(_EdgeRun):
    """Edge/counter flashing. ``kind`` distinguishes a front drip into the gutter from a
    rear counter-flashing tucked into the house WRB."""

    kind: TrimKind = TrimKind.DRIP_FLASHING


for _name, _obj in (
    ("Fascia", Fascia),
    ("Gutter", Gutter),
    ("Flashing", Flashing),
):
    register_constructor(_name, _obj)

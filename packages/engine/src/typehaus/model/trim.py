"""Envelope edge trim / roofing accessories along a deck or roof edge.

A balcony/porch edge carries a small family of long, thin run elements the framing does
not: a PVC fascia board closing the joist ends, a hung gutter at the low (front) edge, a
drip flashing turning the deck membrane down into that gutter, and a counter-flashing at
the high (rear) edge tucked up under the house WRB. Each is authored as a plan-frame
polyline run with a cross-section; the resolver extrudes a thin solid so it reads in the
model, IFC, and take-off instead of living only in a note.

The :class:`Downspout` is the exception to the shape and the reason for the family: it is a
point, not a run, but a gutter that drains nowhere is not drainage, so it belongs beside the
gutter it empties rather than off in the plumbing.
"""

from __future__ import annotations

from typing import Literal

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
    # Which side of the p0→p1 path faces the building ("left" is the path's left-hand
    # normal, resolve/geometry.py::normal). Every formed run has an inboard and an outboard
    # end, and a section that is not symmetric about its centre line has to know which is
    # which — a drip edge's turn-down hangs off the *outboard* end, so getting this wrong
    # points the drip back at the wall. On a symmetric section (the gutter channel, a plain
    # extruded band) it only decides which band is named BACK and which FRONT.
    back_side: Literal["left", "right"] = "left"


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
    # Net free ventilating area, square inches per linear foot of run — the number printed
    # on the vented-soffit product, not something derivable from the panel's dimensions
    # (perforation pattern and open area vary by an order of magnitude between products).
    # R806.2 is an *area* requirement, so ``vented=True`` alone cannot answer it: without
    # this the attic-ventilation check knows there is intake and not how much.
    net_free_area_in2_per_ft: float | None = None


@register_element
class Gutter(_EdgeRun):
    """A hung gutter channel at the low edge; ``depth`` is the channel height.

    The run resolves as an open-top U — a back sheet, a floor and a front sheet — not as a
    solid bar, so which side of the run faces the building has a name.
    """

    kind: TrimKind = TrimKind.GUTTER
    slope: str = ""  # optional drainage note, e.g. "1/16 in/ft to SE downspout"
    # Which leader the run falls to. The ``slope`` note said so in prose, which nothing could
    # check — two Catlin gutters sloped to downspouts that had never been authored. This is
    # the same statement in a form ``checks/mep/drainage.py`` can hold to a real element.
    downspout_ref: str | None = None


@register_element
class Downspout(Element):
    """The leader carrying a gutter's water down the wall to grade.

    Not an ``_EdgeRun``: the rest of this family runs *along* an edge and is billed by the
    lineal foot of a cross-section, while a leader is a single vertical round pipe at one
    point in plan. It lives here anyway because it is the other half of the gutter — a
    gutter with nowhere to drain is not a drainage system — and because the take-off and the
    roof trade want the two on the same line.

    ``clamp_refs`` names the securement hardware steadying the pipe against the cladding.
    Those clamps are explicitly *not* the leader's primary support; that is what the
    ``Connector`` records say, and it matters to whoever hangs it.
    """

    kind: TrimKind = TrimKind.DOWNSPOUT
    position: Point2D                # plan-frame centre of the pipe
    top_elevation: Length            # the outlet at the gutter floor
    bottom_elevation: Length         # discharge, normally just above grade
    diameter: Length
    material: str = ""
    gutter_ref: str | None = None    # the Gutter tag this leader drains
    clamp_refs: tuple[str, ...] = ()


@register_element
class Flashing(_EdgeRun):
    """Edge/counter flashing. ``kind`` distinguishes a front drip into the gutter from a
    rear counter-flashing tucked into the house WRB.

    A ``DRIP_FLASHING`` resolves as a bent angle — a flat leg lapped under the roofing and a
    turn-down at the outboard end that throws the water clear — so its ``back_side`` is load
    bearing. A ``WRB_COUNTERFLASHING`` is a flat back pan and stays a single band.
    """

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
    downspout_ref: str | None = None  # the leader it falls to (see Gutter.downspout_ref)


@register_element
class GlazingTrim(_EdgeRun):
    """An aluminium extrusion capping a multiwall-glazing panel edge.

    Multiwall polycarbonate is only weathertight once every cut edge is closed: the top
    (high) flute ends get sealed tape under a solid cap, the bottom (low) ends get a vented
    channel with weep holes so the flutes drain, and an edge that butts a wall gets an
    F-channel receiver. They are billed by the lineal foot, not the piece, which is why they
    are edge runs like the fascia/gutter family rather than framing members.

    ``profile`` names the extrusion section in the letter the industry uses ("U", "H", "F",
    "bar"); ``weep_holes`` records the drainage the low channel must be drilled for, which is
    a fabrication instruction and not visible in any geometry.
    """

    kind: TrimKind = TrimKind.GLAZING_CHANNEL
    profile: str = "U"  # "U" | "H" | "F" | "bar"
    # A jamb channel runs up the panel's edge rather than along it, so its ``path`` spans
    # only the sheet thickness and its ``depth`` is the run. The extrusion is billed along
    # its long axis either way; this is what tells the take-off which axis that is.
    vertical: bool = False
    weep_holes: bool = False
    sealed_tape: bool = False  # solid (not vented) tape over a high flute end
    glazing_ref: str | None = None  # the GlazingPanel tag this edge belongs to


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
    # Net free area of the intake soffit, and of the ridge vent this eave's roof exhausts
    # through — both in square inches per linear foot, as the products are rated. The ridge
    # figure lives here rather than on the ridge because the derived ridge-vent run is a
    # product of the roof trim resolution this element drives.
    soffit_nfva_in2_per_ft: float | None = None
    ridge_vent_nfva_in2_per_ft: float | None = None
    gutter: EaveGutter | None = None


for _name, _obj in (
    ("Fascia", Fascia),
    ("EaveSoffit", EaveSoffit),
    ("Gutter", Gutter),
    ("Downspout", Downspout),
    ("Flashing", Flashing),
    ("GlazingTrim", GlazingTrim),
    ("FasciaBoard", FasciaBoard),
    ("EaveGutter", EaveGutter),
    ("EaveTrim", EaveTrim),
):
    register_constructor(_name, _obj)

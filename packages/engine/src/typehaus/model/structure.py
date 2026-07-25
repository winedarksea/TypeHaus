"""Foundation & structural elements (#27 — schema in M1, sheets in M3)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element, HausModel
from typehaus.model.elements import Wall
from typehaus.model.enums import ConnectorKind, RailingKind
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


class DrainTile(HausModel):
    """Drain-tile product spec for a FootingBedding — what the bare ``drain_tile: bool``
    cannot say: pipe size/material, sock, and where the run discharges. A detail slice
    and the take-off read this; the bool keeps meaning merely "one exists"."""

    diameter: Length
    material: str = "perforated corrugated HDPE"
    sock: bool = True  # filter-fabric sock over the perforations
    discharge: str | None = None  # "daylight" | "sump" | free-text run note


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
    # Optional product spec for the tile above; None keeps the bool's bare annotation.
    drain_tile_spec: DrainTile | None = None
    perimeter_insulation: Length | None = None
    cast_foam_in_aggregate: bool = False


@register_element
class Post(Element):
    """A point structural member (→ IfcColumn)."""

    position: Point2D
    size: str = "6x6"
    height: Length | None = None
    # Tag of what the post bears on — a pad/footing/slab, or a wall the post stands on top
    # of (the balcony pillars bear on the masonry porch railing). Unset hangs the post's
    # top at its storey datum instead.
    supported_by: str | None = None
    assembly: str | None = None  # optional finish assembly (e.g. paint) for render/IFC material


@register_element
class Beam(Element):
    """An axis structural member; a valid bearing ref for JoistSpec (→ IfcBeam)."""

    start_node: str
    end_node: str
    size: str = "3.5x11.875 LVL"
    bearing_refs: tuple[str, ...] = ()
    datum: FaceRef | None = None
    # Project-frame absolute top of the beam, overriding the derived bearing-stack drop.
    # The resolver normally hangs a beam a joist depth below its storey datum, which it
    # infers from the FloorSystem that bears on it. A beam that carries no joists but must
    # still sit low — the balcony E-W girts bolt to the pillar faces *under* beams whose own
    # tops are already dropped — has no such inference available, and authoring it into a
    # FloorSystem's bearing_refs to borrow the drop would claim joists it does not carry.
    top_elevation: Length | None = None
    # Optional finish assembly (paint/stain), same contract as Post.assembly: the resolver
    # forwards it to the beam's solid so render/IFC read the finish instead of the bare
    # per-category palette colour. Unset leaves the beam its structural wood colour.
    assembly: str | None = None


@register_element
class Dowel(Element):
    """A fiberglass (GFRP) rebar dowel tying two footings across a thermal break.

    The house and the sunken-garden footings share a compacted bed; where they abut, GFRP
    dowels pin them together *through* a rigid-foam block so the connection transfers shear
    without bridging heat. The dowel is the schema primitive (previously the foam was only
    recorded via ``FootingBedding.cast_foam_in_aggregate`` + a note). ``foam_thickness`` /
    ``foam_psi`` describe the XPS block the dowel passes through — resolved as its own solid
    so the thermal break reads in the model, IFC, and take-off."""

    position: Point2D  # plan center of the dowel span (midpoint of the break)
    axis: str = "y"  # "x" | "y": the direction the dowel bar runs across the break
    length: Length  # embedment-to-embedment span across the joint
    diameter: Length  # bar diameter (e.g. #5 GFRP ≈ 0.625")
    elevation: Length  # bar centerline, project-frame absolute
    count: int = 1  # bars in the row
    spacing: Length | None = None  # o.c. spacing when count > 1 (perpendicular to axis)
    connects: tuple[str, ...] = ()  # the two footing tags doweled together
    foam_thickness: Length | None = None  # XPS thermal-break block thickness (along axis)
    foam_height: Length | None = None  # block height (defaults to footing thickness)
    foam_psi: float = 40.0  # XPS compressive rating


@register_element
class Connector(Element):
    """Modeled connection hardware — joist hangers, hurricane ties, knee braces, post bases.

    Previously carried only as text/notes; this makes the fastener a first-class element
    with a small resolved solid at its connection point (→ IfcMechanicalFastener /
    IfcDiscreteAccessory), and named refs to the members it joins."""

    kind: ConnectorKind
    position: Point2D
    elevation: Length | None = None  # connector center, project-frame absolute
    size: str = ""  # product model, e.g. "APVKB", "H2.5A", "LUS28", "ABU66"
    connects: tuple[str, ...] = ()  # member/wall/post tags the hardware joins
    axis: str | None = None  # optional in-plane run direction ("x" | "y") for braces


@register_element
class KneeBrace(Element):
    """A 45-degree diagonal brace stiffening a post/beam joint (→ IfcMember/BRACE).

    The structural element is the wood diagonal; ``connector`` names the hardware that
    fastens it (a Simpson Outdoor Accents APVKB, say), which resolves as a small marker at
    the upper end. One element per *physical* brace — a post braced in both plan directions
    carries two of them — so the take-off counts braces rather than multiplying a per-joint
    rule that only holds where a beam continues past its post.

    Geometry is the 45-degree triangle a carpenter cuts: the brace leaves the post *face*
    (never its centre — an embedded end reads as a member clash) and runs ``leg`` out along
    ``axis``/``direction`` while rising the same ``leg`` to ``soffit_elevation``. That soffit
    is authored rather than derived because the members a post is braced to need not share
    an elevation: the balcony's N-S braces land on the beam soffit and its E-W braces a girt
    depth lower.
    """

    position: Point2D  # braced post's plan centre
    soffit_elevation: Length  # underside of the member braced to, project-frame absolute
    leg: Length  # horizontal run; equal to the rise at 45 degrees
    axis: str = "y"  # "x" | "y": the plan direction the brace runs from the post
    direction: int = 1  # +1 / -1 sense along ``axis``
    member: str = "2x6"  # the diagonal's own nominal profile
    post_size: str = "6x6"  # braced post's section, so the brace starts at its face
    connector: str = "APVKB45-6"  # hardware model at the joint
    connects: tuple[str, ...] = ()  # post + beam/girt tags the brace joins


@register_element
class Railing(Element):
    """A first-class guard rail framed from posts + rails along a plan path (→ IfcRailing).

    The metal fascia-mounted balcony guard is modeled here rather than approximated as a
    parapet wall. The resolver frames posts at ``post_spacing`` o.c. along ``path`` plus
    ``rail_count`` horizontal rails, all riding at ``base_elevation`` (the deck top)."""

    path: tuple[Point2D, ...]  # guard line, >= 2 plan points
    kind: RailingKind = RailingKind.METAL_FASCIA_MOUNT
    height: Length  # guard height above the deck
    base_elevation: Length  # deck top, project-frame absolute
    post_spacing: Length  # posts o.c. along the path
    post_size: str = "2x2"  # nominal post cross-section
    rail_count: int = 2  # horizontal rails (top + bottom)
    mount: str = "fascia"  # "fascia" | "surface"
    assembly: str | None = None  # optional finish assembly for render/IFC material


@register_element
class GlazingPanel(Element):
    """A flat translucent sheet spanning a frame — multiwall polycarbonate, glass, acrylic.

    Not a :class:`~typehaus.model.elements.Window`: a window is an *opening* cut in a host
    wall and framed by it. This is the sheet itself, standing free in a post-and-beam frame
    with no wall to host it — the enclosure of a breezeway, a canopy, a lean-to. It is also
    not a ``Slab`` with a glazing assembly, because a Slab is pinned to its storey datum and
    a canopy panel sits at whatever absolute elevation its rafters put it.

    ``plane`` picks the extrusion:

    * ``"horizontal"`` — ``outline`` is the panel's footprint, lying flat with its top at
      ``top_elevation`` and its underside a ``thickness`` below.
    * ``"vertical"`` — ``outline`` is the panel's *run* in plan (two or more points), stood
      up from ``base_elevation`` to ``top_elevation`` and given ``thickness`` across the run.

    Sheet economy is a real design constraint for these (they come in 4'x8' stock and cutting
    them is waste), so the take-off bills them by area *and* by whole sheets.
    """

    outline: tuple[Point2D, ...]
    thickness: Length
    top_elevation: Length
    plane: Literal["horizontal", "vertical"] = "horizontal"
    base_elevation: Length | None = None  # vertical panels; required when plane="vertical"
    assembly: str | None = None
    # Applied film — UV, solar-control, or bird-safety patterning. Recorded rather than
    # modeled: it is 2 mil of surface treatment, not a layer with a thermal or dimensional
    # consequence, but it is a line on the order and a note on the drawing.
    film: str | None = None


for _name, _obj in (
    ("DrainTile", DrainTile),
    ("FoundationWall", FoundationWall),
    ("Footing", Footing),
    ("GlazingPanel", GlazingPanel),
    ("Pad", Pad),
    ("FootingBedding", FootingBedding),
    ("Post", Post),
    ("Beam", Beam),
    ("Dowel", Dowel),
    ("Connector", Connector),
    ("KneeBrace", KneeBrace),
    ("Railing", Railing),
):
    register_constructor(_name, _obj)

"""Foundation & structural elements (#27 — schema in M1, sheets in M3)."""

from __future__ import annotations

from typehaus.model.base import Element
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
    perimeter_insulation: Length | None = None
    cast_foam_in_aggregate: bool = False


@register_element
class Post(Element):
    """A point structural member (→ IfcColumn)."""

    position: Point2D
    size: str = "6x6"
    height: Length | None = None
    supported_by: str | None = None  # pad/footing tag
    assembly: str | None = None  # optional finish assembly (e.g. paint) for render/IFC material


@register_element
class Beam(Element):
    """An axis structural member; a valid bearing ref for JoistSpec (→ IfcBeam)."""

    start_node: str
    end_node: str
    size: str = "3.5x11.875 LVL"
    bearing_refs: tuple[str, ...] = ()
    datum: FaceRef | None = None


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


for _name, _obj in (
    ("FoundationWall", FoundationWall),
    ("Footing", Footing),
    ("Pad", Pad),
    ("FootingBedding", FootingBedding),
    ("Post", Post),
    ("Beam", Beam),
    ("Dowel", Dowel),
    ("Connector", Connector),
    ("Railing", Railing),
):
    register_constructor(_name, _obj)

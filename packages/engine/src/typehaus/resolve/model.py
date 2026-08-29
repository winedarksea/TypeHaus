"""ResolvedModel — the IR between the validated PlanModel and the emitters (→ 02).

Whole-building, not per-storey: storeys resolve in the shared project-north frame and are
placed at derived elevations, so sections/details cut across storeys (→ 02 §Pipeline).
All coordinates are canonical SI meters. These are plain frozen dataclasses (not Pydantic)
— they are engine-internal IR, never authored or serialized as source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from typehaus.model.assembly import Layer
from typehaus.model.enums import ConditionKind
from typehaus.model.plan import PlanModel
from typehaus.resolve.layout_lines import ResolvedLayoutLine

if TYPE_CHECKING:  # the IR imports this module, so the reference stays type-only
    from typehaus.model.placeables import Mount
    from typehaus.resolve.geometry_ir import GeometryModel

# A polygon ring: list of (x, y) in meters. Layer polygons are simple rings.
Ring = list[tuple[float, float]]

# One point of a swept run's 3D path, and one point of its section (→ resolve/sweep.py).
Vec3 = tuple[float, float, float]
Vec2 = tuple[float, float]


@dataclass(frozen=True)
class ResolvedLayer:
    """One assembly layer resolved to a plan polygon at a wall."""

    name: str
    material_ref: str
    function: str
    thickness_m: float
    polygon: Ring
    control: frozenset[str] = frozenset()
    # Insulation in a STRUCTURE layer's framing bays: shares that layer's polygon and adds
    # no wall depth. Consumers must not treat it as a band of its own (→ CavityFill).
    is_cavity: bool = False
    # For a cavity layer, the name of the STRUCTURE layer whose bays it fills.
    cavity_host: str | None = None
    # Absolute vertical extent of this layer, when its assembly bands it (``Layer.extent``:
    # a protection panel above grade, a splash course at the base). ``None`` means "the
    # wall's own extent", which is what every full-height layer says and what every layer
    # said before banding existed. Consumers should read :meth:`band` rather than these two
    # fields, so the fallback lives in exactly one place.
    z0_m: float | None = None
    z1_m: float | None = None
    # The split row this layer is one region of (``Layer.slot``). Layers sharing a slot are
    # regions of ONE row: they occupy a single slice of the wall depth between them, so only
    # the first of them may be counted toward the wall's thickness. ``None`` — every layer
    # in every assembly authored before slots existed — is a row of its own.
    slot: str | None = None
    # The *unresolved* ``Layer.extent`` that produced ``z0_m``/``z1_m``, as
    # ``((datum, offset_m) | None, (datum, offset_m) | None)`` — bottom, then top.
    # ``z0_m``/``z1_m`` are absolute and therefore stale the moment the wall's own extent
    # moves: ``extend_walls_to_platform`` grows a wall *after* its layers are resolved, and
    # a band frozen against the pre-lift top refused to follow, including a "run it out"
    # ``top=None`` band, which resolves to the old ``z1`` rather than staying ``None``.
    # Keeping the recipe beside the answer lets :func:`typehaus.resolve.layer_bands.reband`
    # re-resolve it against the wall's new elevations without a plan lookup.
    band_spec: tuple[tuple[str, float] | None, tuple[str, float] | None] | None = None
    # Which way the BOARDS of a board finish run — ``"horizontal"`` | ``"vertical"``, or
    # ``None`` where the question does not arise (any layer that is not a board finish, and a
    # board finish with no furring behind it to derive from).
    #
    # Boards land perpendicular to the furring they are fastened to, because that is where
    # the fastener has to reach: the sauna and plant-room liners both strap horizontally with
    # 1x4 (``FramingSpec(direction="horizontal")``) precisely so a vertical T&G board's
    # concealed flange lands on strapping rather than between studs. So this is derived, never
    # authored — the fact was already in the assembly, it just had nowhere to go. Carried on
    # the resolved layer because ``FramingSpec`` itself does not survive into ``model.json``,
    # and the viewer is where a board direction is finally visible.
    board_run: str | None = None

    def band(self, wall: ResolvedWall) -> tuple[float, float]:
        """This layer's absolute (z0, z1), falling back to the wall's where unbanded."""
        return (wall.z0_m if self.z0_m is None else self.z0_m,
                wall.z1_m if self.z1_m is None else self.z1_m)

    @property
    def is_banded(self) -> bool:
        """Whether this layer states an extent of its own rather than the wall's."""
        return self.z0_m is not None or self.z1_m is not None


@dataclass(frozen=True)
class JunctionIncident:
    """One wall endpoint participating in a resolved plan junction."""

    wall_tag: str
    endpoint: str  # "start" | "end"
    direction: tuple[float, float]  # node -> wall interior
    assembly: str
    # Absolute elevation extent (metres) of this wall. Two incidents whose extents do not
    # overlap are different bearing tiers of the same plan node — a masonry guard stacked on
    # a concrete porch wall is one plan point but two independent junctions, not a five-way.
    z0_m: float = 0.0
    z1_m: float = 0.0


@dataclass(frozen=True)
class ResolvedJunction:
    """Topology decision shared by layer geometry, framing, diagnostics, and emitters."""

    node_tag: str
    storey: str
    point: tuple[float, float]
    kind: str  # "open_end" | "collinear" | "l" | "t" | "x" | "complex"
    incidents: tuple[JunctionIncident, ...]
    through_walls: tuple[str, ...] = ()
    branch_walls: tuple[str, ...] = ()
    framing_owner: str | None = None
    supported: bool = True
    diagnostic: str | None = None


@dataclass(frozen=True)
class SeatCut:
    """A birdsmouth: where a rafter's underside is cut flat to bear on a plate.

    Replaces the string carrier ``"eave:birdsmouth-1.17in"``, which the 2D section had to
    re-parse, and the separate ``seat_cut`` member, which occupied the same volume a second
    time — the reason ``checks/structural/interference.py`` needed a clause to excuse a block
    overlapping its own rafter, and the reason the takeoff carried 56 pieces of 11-7/8"
    I-joist at 3.5" that nobody ever buys.

    ``heel`` is the plan point of the plumb heel cut; the seat runs ``seat_run_m`` from there
    toward the member's nearer end, flat at ``plate_top_z_m``. The notch depth is not a field
    because it is not independent: it is ``seat_run_m`` times the rafter's slope, which is
    why the reference's 3.5" seat and 1.17" birdsmouth are one fact written twice.
    """

    plate_top_z_m: float
    heel: tuple[float, float]
    seat_run_m: float


@dataclass(frozen=True)
class FramedMember:
    """A framing member as a lightweight record (no geometry kernel) until emit (risk 6)."""

    parent_uid: str
    child_key: str  # e.g. "stud-007", "plate-top", "header-D101"
    category: str  # "stud" | "plate" | "king" | "jack" | "cripple" | "header" | "sill"
    #                | "joist" | "rim" | "strapping" | "blocking"
    profile: str  # nominal size, e.g. "2x6"
    # Placement as a 2D segment in the plan frame + a z extent; emit builds the solid.
    p0: tuple[float, float]
    p1: tuple[float, float]
    z0_m: float
    z1_m: float
    length_m: float
    # A raked member has different lower/upper elevations at its second endpoint.
    # ``None`` preserves the ordinary prismatic member convention.
    z0_end_m: float | None = None
    z1_end_m: float | None = None
    # Plan-frame axis a vertical member (p0 == p1) is oriented along — e.g. a stud's
    # wall direction — so the UI can place its cross-section without reaching back to
    # the host wall. ``None`` for horizontal/sloped members, which carry their own
    # axis in p0->p1.
    orient: tuple[float, float] | None = None
    # Free-form connection annotation (e.g. "ridge:adjustable-slope-hanger") for the
    # 2D detail pipeline to bind later. Geometry stays a plain box; no seat cuts here.
    connection: str | None = None
    # Catalog material ref, for members that are a *skin* rather than lumber: the wall→roof
    # closure bands carry their source layer's material, the derived trim its board material.
    # Without it both emitters fall back to the category palette, which paints a standing-seam
    # cladding band the same generic grey as a plywood one. ``None`` for ordinary framing,
    # which is coloured by category as before.
    material: str | None = None
    # Visibility trade this member belongs to when its *category* alone would file it
    # elsewhere. A fascia is the case this exists for: it is envelope trim by category, but
    # it is also a board nailed to the rafter tails that the carpenter frames — so it has to
    # appear under a framing view toggle as well as with the roof skin it finishes.
    # ``None`` = the consumer's category-derived default.
    trade: str | None = None
    # A walking surface whose plan shape is not a swept board (notably a winder).  The normal
    # member axis remains for framing/bearing, while every visual/export consumer uses this
    # explicit footprint when present.
    plan_outline: Ring | None = None
    # The riser face this tread serves — the ``going * i`` line a stair plan marks. The
    # member axis is the board's *centreline*, half a going past this line, so drawing the
    # axis put a (going − nosing)/2 sliver at one end of every flight and (going + nosing)/2
    # at the other against full-going interiors: uniform steps that read as non-uniform.
    # ``None`` for anything that is not a straight tread (a winder's axis IS its fan line).
    riser_line: tuple[tuple[float, float], tuple[float, float]] | None = None
    # The birdsmouth, when this member has one. ``geometry_members.member_solid`` reads it and
    # nothing else does: its guard is a single attribute read, because it sits on the hot path.
    seat: SeatCut | None = None
    # Held up along its WHOLE length rather than reaching between supports — derived from the
    # bearings actually reaching, never assumed from a category. Two things read it and they
    # are why it names the fact rather than either consequence: the takeoff buys such a member
    # in ordinary stock lengths and splices it over a bearing point (no over-length special
    # order, no crane), and the uplift pass ties it down at a pitch instead of at two ends,
    # because it does not have two ends in any meaningful sense. Catlin's 36' ridge is the
    # case — it bears on W-A-C1/C1B/C2 end to end.
    continuously_supported: bool = False


@dataclass(frozen=True)
class ResolvedWall:
    """A wall resolved to per-layer polygons + framing + elevation extent."""

    uid: str
    tag: str
    storey: str
    assembly: str
    axis: tuple[tuple[float, float], tuple[float, float]]  # (start, end) in meters
    layers: tuple[ResolvedLayer, ...]
    z0_m: float
    z1_m: float
    is_foundation: bool = False
    members: tuple[FramedMember, ...] = ()
    # ``ToRoof`` walls retain their full bounding height in ``z1_m`` for consumers
    # that only understand prisms, while these endpoint elevations carry the actual
    # raked top for framing, sections, and the interactive model.
    top_z0_m: float | None = None
    top_z1_m: float | None = None
    # Platform framing (#43): an exterior/bearing wall runs base level → next level, so one
    # IfcWall covers the floor band and Revit/SketchUp read a continuous envelope. The
    # *framing* still stops at the double top plate — the band above it is rim board and
    # joists, not studs — so that elevation is carried separately here. ``None`` means the
    # wall is not extended and its framing tops out at ``z1_m``/``top_z*_m`` as before.
    plate_top_z_m: float | None = None
    # The mirror image, and for the mirror-image reason (#43): a framed wall's *body* —
    # sheathing, CI, WRB, cladding — runs down over the mudsill and rim board and laps the
    # foundation's protection panel, which is what is built (notes/basement_to_framed_wall
    # _detail.md) and what left ~270 SF of the basement-to-main line unclad while every
    # ``W-M-*`` started at the storey datum and the pour stopped 13 7/16" below it. Its
    # *framing* does not move: bottom plate, studs and opening sills stay on the storey
    # datum, which is the elevation kept here. ``None`` means the wall was not extended
    # down and its base is ``z0_m`` as before.
    plate_base_z_m: float | None = None

    @property
    def base_ref_z_m(self) -> float:
        """The wall's *framing* base — the datum a sill height is measured from.

        ``ResolvedOpening.sill_m`` is stated up from the room floor, and the room floor is
        where the framing starts, not where the cladding stops. Every consumer that adds a
        sill to an elevation reads this rather than ``z0_m``, so extending a wall down over
        the rim moves its skin without moving a single window (→ ``plate_base_z_m``).
        """
        return self.z0_m if self.plate_base_z_m is None else self.plate_base_z_m

    @property
    def thickness_m(self) -> float:
        """Total wall depth. Cavity layers sit inside their host and add nothing."""
        return sum(ly.thickness_m for ly in self.depth_layers())

    def depth_layers(self) -> tuple[ResolvedLayer, ...]:
        """The layers that occupy their own slice of the wall depth, interior→exterior.

        A cavity layer sits inside its host's bays. The second and later regions of a
        ``Layer.slot`` sit at a different *elevation* in a slice the first region already
        holds — a brown plinth and a lapis field are one 3 5/8" wythe, not two. Counting
        them was worth 19" of brick veneer where 3 5/8" stands, which reached far enough
        past the basement wall for ``code.energy_prescriptive`` to grade the garden's
        veneer as though it enclosed the sauna.
        """
        seen: set[str] = set()
        out: list[ResolvedLayer] = []
        for layer in self.body_layers():
            if layer.slot is not None:
                if layer.slot in seen:
                    continue
                seen.add(layer.slot)
            out.append(layer)
        return tuple(out)

    def body_layers(self) -> tuple[ResolvedLayer, ...]:
        """Every layer with a solid of its own, interior→exterior.

        The sibling of :meth:`depth_layers`, and the distinction matters. *Depth* counts a
        ``Layer.slot``'s regions once, because a brown plinth and a lapis field are one
        3 5/8" wythe. *Bodies* counts them all, because they sit at different elevations and
        each is a real course of brick: dropping them left the plinth standing alone with
        nothing above it, in the GLB, in IFC and in every section.

        Cavity fill is excluded from both — it shares its host's polygon, so a solid there
        would only z-fight (→ ``geometry_walls.layer_solids``).
        """
        return tuple(layer for layer in self.layers if not layer.is_cavity)


@dataclass(frozen=True)
class ResolvedOpening:
    uid: str
    tag: str
    host_wall: str
    type_ref: str | None
    width_m: float
    height_m: float
    sill_m: float
    center_along_m: float  # distance from wall start along the axis
    # Preserve the authored semantic category at the resolved interchange boundary.
    # `is_door` remains for existing framing/check consumers, but cannot distinguish a
    # bare rough void from a window for IFC and visualization consumers.
    kind: str  # "door" | "window" | "rough_opening"
    is_door: bool
    swing_clearance: Ring = ()
    framing_bumper: Ring = ()
    # Arched head: semicircular/segmental rise above the rectangular jamb height. 0 = square
    # head. The opening's total height_m already includes this rise (straight run = height -
    # rise), so an 8'-tall opening with a 4' rise is a 4' rectangle capped by a 4' semicircle.
    arch_rise_m: float = 0.0
    # A pocket door's leaf parks inside the wall beside the opening. ``pocket_run_m`` is how
    # far that cavity runs past the rough opening and ``pocket_sign`` which way along the
    # wall axis (+1 toward the host's end node). Both are 0 for every other operation.
    #
    # This is the first and only case where ``width_m`` is not the framed extent: the
    # framed opening is ``width_m + pocket_run_m``, roughly 2W + 1", while ``width_m``
    # stays the clear opening every daylight, egress and product consumer wants. A
    # consumer that cuts, checks or bills the *structure* must add the pocket; one that
    # measures what a person walks through must not.
    pocket_run_m: float = 0.0
    pocket_sign: int = 0


@dataclass(frozen=True)
class ResolvedConstructionReturn:
    """A pre-framing construction-rule return (#45): the physical membrane / foam / liner /
    masonry lap that closes a resolved junction, plus the overlay metadata a detail recipe
    needs.

    Emitted by :mod:`typehaus.resolve.construction` from a ``PlanModel.construction_rules``
    entry — authoring a :class:`~typehaus.model.assembly.ConstructionRule` is enough to get
    the record + BOM + overlay. It is documentation geometry, not render geometry: no
    ``ResolvedSolid`` is emitted (a correctly-placed return duplicates the mitred layer
    polygon its host wall already draws), but the record is serialized to ``model.json`` and
    emitted as an ``IfcCovering``. It bills through
    :func:`typehaus.takeoff.construction_returns_takeoff` (honouring ``takeoff_category``),
    and carries the element tags + lap / sealant / flashing / thermal-continuity an overlay
    recipe binds to. It never mutates construction geometry: a Transition *documents* it
    (via ``documents_rules``), keyed to the existing boundary condition named here.
    """

    uid: str
    tag: str  # the ConstructionRule tag, e.g. "CR-CONC-TO-FRAMED-SILL"
    storey: str
    kind: str  # rule.kind: "bearing_plate" | "blocking" | ...
    applies_to: str  # the rule.applies_to predicate that matched
    takeoff_category: str | None
    material_ref: str
    # Participating wall/junction tags — what the overlay recipe anchors to.
    element_tags: tuple[str, ...]
    outline: Ring
    z0_m: float
    z1_m: float
    thickness_m: float  # the returning material's depth (strip width in plan)
    length_m: float  # the run of the return (lineal take-off quantity)
    # Overlay metadata for the detail recipe (worker V3 binds these):
    lap_m: float  # the authored return/lap dimension
    thermal_continuity: bool = False
    air_vapor_continuity: bool = False
    sealant: str | None = None
    flashing: str | None = None
    returning_layer: str | None = None  # name of the layer that turns the corner
    # The sill-seal under a bearing plate: which product, and its compressed in-place
    # thickness. Set by ``resolve/construction_sills.py`` (which picks the product from the
    # wall — peel-and-stick where the plate joint is the air barrier's crossing, plain foam
    # where it is only a capillary break); None on every other kind of return.
    # ``takeoff/anchors.sill_gasket_rows`` bills these by the lineal foot, one row per
    # product — NOT ``construction_returns_takeoff``, whose 1:1 invariant with
    # ``model.construction_returns`` a second row would break.
    gasket_product: str | None = None
    gasket_thickness_m: float | None = None
    # The existing derived boundary-condition key this return documents (stacking /
    # assembly-change), so an overlay can join return -> condition -> Transition.
    condition_key: str | None = None


@dataclass(frozen=True)
class SolidSweep:
    """A closed section profile carried along a 3D polyline — the run *is* one solid.

    The prism IR can only extrude a plan ring straight up, so everything that rakes or
    slopes had to be chopped into level pieces: one band per 1-1/2" of a handrail's fall
    (a straight 13-ft bar came out as 292 solids), and a drain stair-stepped into three
    level stacks. A run is one thing and one purchase, so this says so directly.

    ``path`` is >= 2 project-frame points in metres with no repeats; ``profile`` is the
    section in the leg's local ``(right, up)`` frame, closed implicitly like every other
    ring in the IR. :mod:`typehaus.resolve.sweep` owns the mitre, the frame convention and
    the developed length, and ``ui/src/three/tubeGeometry.ts`` mirrors it vertex for vertex.
    """

    path: tuple[Vec3, ...]
    profile: tuple[Vec2, ...]


@dataclass(frozen=True)
class ResolvedSolid:
    """A resolved horizontal or below-grade solid with a plan outline.

    Slabs, pads, and footings all use this compact representation.  Keeping their
    outline in the shared IR makes the model.json, glTF, IFC, and energy consumers
    agree on the same geometry instead of each rebuilding it from authored inputs.
    """

    uid: str
    tag: str
    storey: str
    category: str  # "slab" | "footing" | "pad"
    outline: Ring
    z0_m: float
    z1_m: float
    assembly: str | None = None
    voids: tuple[Ring, ...] = ()
    # The material the *authored* element named, for solids that name one directly instead of
    # through an assembly (the trim-run family: gutter, drip edge, downspout, glazing trim).
    # A framed member has carried its material ref since it was introduced; a solid could only
    # say "I am category gutter", so a gutter ordered in a second coil colour had no way to
    # say so and rendered the palette's mill aluminium in both renderers.
    material: str | None = None
    # A run — a handrail, a drain, a raceway — carried as one swept solid rather than as a
    # stack of level bands. When set, ``outline``/``z0_m``/``z1_m`` still carry the plan
    # silhouette and Z extents of the *whole* run, so every consumer that has not been
    # taught about sweeps (the plan sheet's railing polylines, the take-off's centroid)
    # degrades to something honest instead of breaking.
    sweep: SolidSweep | None = None


@dataclass
class ResolvedSoffit:
    """A dropped ceiling box, carried as a record so it can be *framed*.

    The soffit's finished shape is already emitted as a ``ResolvedSolid`` (category
    "soffit") — the box a renderer draws and a room reads its clear height from. This
    record is the framing host beside it: the authored ``FramingSpec`` (``framing``,
    ``None`` when the soffit is drawn but not yet framed) and the members
    :mod:`typehaus.resolve.framing.soffit` generates from it. Mutable, because the
    framing stage fills ``members`` after the envelope stage creates the record.
    """

    uid: str
    tag: str
    storey: str
    outline: Ring
    z0_m: float  # underside of the finished soffit
    z1_m: float  # the ceiling plane it hangs from
    framing: object | None = None  # FramingSpec | None (model/floors.py Soffit.framing)
    members: list[FramedMember] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedCeiling:
    """A room's resolved ceiling construction — the layer stack checks and takeoff read.

    The room's own finished plane is also emitted as a ``ResolvedSolid`` (category
    "ceiling") when it resolves a flat extent, exactly the ``ResolvedSoffit`` /
    ``ResolvedSolid`` split above: that record is what a renderer draws, this one is what
    a check or a takeoff reads without re-deriving the layer stack (room override, else
    the covering deck's ``ceiling_below``, else the room's roof's ``default_lining``).

    ``z0_m``/``z1_m`` are None for a room whose ceiling follows a sloped/vaulted roof
    (``Room.ceiling=FollowRoof(...)``) — there is no single flat plane to state, so no
    ``ResolvedSolid`` is emitted for it either, and only the layer stack (for the roof's
    own material/BOM) is carried here.
    """

    uid: str
    tag: str
    storey: str
    room_ref: str
    outline: Ring
    z0_m: float | None
    z1_m: float | None
    layers: tuple[Layer, ...]


@dataclass(frozen=True)
class ResolvedRoof:
    """A constrained gable/shed roof derived from its bearing-wall envelope."""

    uid: str
    tag: str
    storey: str
    form: str
    footprint: Ring
    # The rafter-top (deck) plane at the footprint edge — NOT the plate top. A
    # rafter-framed roof rises ``deck_rise_m`` above its bearing (only the birdsmouth
    # sinks below the plate); a truss roof's eave is lifted by its raised heel.
    eave_z_m: float
    ridge_z_m: float
    ridge_direction: str
    assembly: str
    surface_area_m2: float
    members: tuple[FramedMember, ...] = ()
    # Top of the bearing-wall plates the roof seats on (None when bearing is unknown).
    bearing_z_m: float | None = None
    # Per-layer plan setbacks from the footprint edge, one dict per above-structure
    # layer: {"layer": name, "west": m, "east": m, "south": m, "north": m}. Computed by
    # resolve/roof_layer_setbacks.py from the golden eave detail's clip rules; consumed by BOTH
    # the glTF emitter and the three.js viewer (ui/src/three/roofGeometry.ts).
    layer_edge_setbacks: tuple = ()


@dataclass(frozen=True)
class ResolvedStair:
    """A code-sized stair and its generated framing members."""

    uid: str
    tag: str
    storey: str
    to_storey: str
    outline: Ring
    riser_count: int
    riser_height_m: float
    tread_depth_m: float
    run_direction: str
    run_reversed: bool
    layout: str
    turn_direction: str | None
    winder_count: int
    members: tuple[FramedMember, ...]
    # Physical board depth, nosing projection, and riser-to-riser going are distinct.  Older
    # synthetic tests can omit the two new fields while production resolver output always fills
    # them.
    going_depth_m: float = 0.0
    nosing_depth_m: float = 0.0
    # Where the flight actually springs from and arrives at, in the project frame. These were
    # always the two storey elevations, so every rule re-derived them from ``storey`` and
    # ``to_storey`` and was right to. A flight that states its own rise —
    # ``Stair.base_elevation`` / ``top_elevation``, for a step-down within one storey — breaks
    # that: the garage service stair runs from the slab at -2'-10" to a threshold at 0'-0"
    # with ``from_storey == to_storey``, and a rule re-deriving its rise from the storey table
    # grades it against the top of an ICF stem it has nothing to do with. ``None`` on a
    # synthetic stair built without the resolver; callers fall back to the storey table there.
    base_elevation_m: float | None = None
    arrival_elevation_m: float | None = None


@dataclass(frozen=True)
class ResolvedFloor:
    """A framed floor deck: joists generated from a FloorSystem's JoistSpec (M3).

    Matches the old catlin builder's semantics: one joist line per spacing position
    across the deck, split into spans at each bearing line."""

    uid: str
    tag: str
    storey: str
    direction: str  # joist span direction: "x" | "y"
    members: tuple[FramedMember, ...]
    # The subfloor sheet riding on top of the joists — the surface people actually stand on,
    # and until now the one part of a floor no consumer had: glTF drew joists in mid-air and
    # IFC emitted beams with nothing spanning them. Empty when the FloorSystem declares no
    # ``subfloor`` layer. ``deck_voids`` are its floor openings (stair wells), which the deck
    # is cut by and the joists were already clipped to.
    deck_outline: Ring = ()
    deck_voids: tuple[Ring, ...] = ()
    deck_z0_m: float = 0.0   # = the storey datum: joists top out there, decking rides on it
    deck_z1_m: float = 0.0
    deck_material_ref: str | None = None


@dataclass(frozen=True)
class ResolvedBrace:
    """A resolved diagonal brace: its raked wood member(s), hosted for identity.

    Framing members are always carried by a host record — a wall, floor, roof or stair —
    because every consumer needs a storey to file them under and one owning uid to make
    them pickable. A brace belongs to none of those, so it hosts itself rather than
    borrowing a floor whose ``members`` bounding box other consumers read as deck extent.
    """

    uid: str
    tag: str
    storey: str
    members: tuple[FramedMember, ...]


@dataclass(frozen=True)
class ResolvedFloorHeat:
    """A resolved radiant zone with its plan footprint and transparent wire estimate."""

    uid: str
    tag: str
    storey: str
    system: str
    zone: Ring
    spacing_m: float
    wire_length_m: float


@dataclass(frozen=True)
class ResolvedFinishZone:
    """An in-room floor-finish override — a tile inlay, a hearth pad (→ model FinishZone)."""

    outline: Ring
    material_ref: str
    area_m2: float
    # The tag of the element the zone was DERIVED from — a slab whose own top face is the
    # finished floor (``Slab.floor_finish``). None for a zone authored on the room, which is
    # its own reason. Carried so the Inspector and the takeoff can say *why* a band of a room
    # is a different finish than the room is.
    source_ref: str | None = None


@dataclass(frozen=True)
class ResolvedPaneling:
    """One wall's share of a ``WallPaneling`` band (→ model/paneling.py).

    A room-scoped paneling resolves to one record per bounding wall it covers, area
    already net of the openings that punch the band — so the takeoff sums, it never
    re-intersects. ``band_z0_m``/``band_z1_m`` are wall-local, measured up from the wall
    base (the room floor), matching ``ResolvedOpening.sill_m``.

    A *line*-scoped paneling resolves the same way, one record per member wall, and its
    band is measured from the line's base instead — so a facade band crossing a storey
    line still arrives here as per-wall records in each wall's own frame, and every
    downstream consumer sums exactly as it did.
    """

    uid: str
    tag: str
    storey: str
    # The room the band belongs to, or ``None`` when it belongs to ``layout_line``.
    room: str | None
    wall_tag: str
    material_ref: str
    area_m2: float
    band_z0_m: float
    band_z1_m: float
    run_m: float
    replaces_wall_finish: bool
    # The layout line the band belongs to, or ``None`` for the room-scoped path.
    layout_line: str | None = None
    # The band as drawable geometry: a plan rectangle on the wall's room-side face, plus the
    # absolute elevations it spans. Until 2026-08-25 this record carried area and nothing
    # else, so a wainscot billed but never appeared — in the viewer, the .glb or IFC.
    #
    # ``outline`` is empty and the elevations ``None`` only where the band could not be placed
    # (a wall whose axis is degenerate). Consumers must treat that as "no geometry", never as
    # a zero-area band: the area above is still right and still bills.
    #
    # NOTE ``area_m2`` is net of the openings that punch the band; ``outline`` is NOT. A
    # rectangle is what a band is, and the punches are already subtracted from the number
    # that gets ordered — cutting them out of the polygon too would need the opening voids
    # threaded through every downstream consumer for a hole you cannot see from inside the
    # room anyway (a door reveal covers it).
    outline: Ring = ()
    z0_m: float | None = None
    z1_m: float | None = None
    thickness_m: float = 0.0


@dataclass(frozen=True)
class ResolvedWindowStool:
    """One window's interior sill board, sized (→ model/millwork.py).

    ``depth_m`` is ``None`` when the window type authors no ``frame_depth``: the derivation
    has an unknown term, so the stool reports UNKNOWN and carries no depth rather than
    guessing one (#32). ``return_m`` and ``frame_depth_m`` are the derivation's two terms,
    carried so a schedule can show its own arithmetic instead of asserting a number.
    """

    uid: str
    tag: str
    storey: str
    window_ref: str
    wall_tag: str
    assembly: str
    material_ref: str
    thickness_m: float
    length_m: float          # finished length: rough opening width + 2 x horn
    depth_m: float | None    # finished depth, front edge to back
    overhang_m: float
    horn_m: float
    profile: str
    # Interior finish face -> window mount plane, off the host wall's own layers. This is
    # why the four host assemblies give four different stool depths, and why nothing here
    # is authored per window.
    return_m: float | None
    frame_depth_m: float | None
    # True when derived from the house's ``MillworkStandard`` rather than authored as its
    # own ``WindowStool``. An authored stool always wins for its window.
    derived: bool = True


@dataclass(frozen=True)
class ResolvedShelf:
    """One bay's worth of identical shelf boards inside a :class:`ResolvedShelfBank`."""

    bay_index: int
    width_m: float
    depth_m: float | None
    clear_height_m: float
    count: int


@dataclass(frozen=True)
class ResolvedShelfBank:
    """A run of shelves in one case, bay by bay (→ model/millwork.py).

    ``depth_m`` is ``None`` only when the bank authors none and its host resolves to
    neither a wall pocket nor a placeable footprint — UNKNOWN, not a default depth.
    """

    uid: str
    tag: str
    storey: str
    host: str
    host_kind: str  # "wall" | "placeable"
    material_ref: str
    thickness_m: float
    depth_m: float | None
    profile: str
    shelves: tuple[ResolvedShelf, ...]


@dataclass(frozen=True)
class ResolvedRoom:
    uid: str
    tag: str
    storey: str
    occupancy: str
    conditioned: bool
    clear_face: Ring  # interior face polygon (core + resolved lining)
    area_m2: float
    floor_finish: str | None
    # Authored in-room overrides of ``floor_finish``. ``Room.finish_zones`` had no field here
    # at all, so a FinishZone written in plan source was silently dropped at resolve and
    # reached no viewer, emitter or takeoff. ``area_m2`` is the zone clipped to the room, so
    # a takeoff can subtract it from the room's field finish without re-intersecting.
    finish_zones: tuple[ResolvedFinishZone, ...] = ()


@dataclass(frozen=True)
class BoundaryCondition:
    """A derived boundary condition keyed for Transition matching (→ 11b §Transitions)."""

    kind: ConditionKind
    assemblies: tuple[str, ...]
    detail: str
    element_tags: tuple[str, ...]
    key: str  # canonical string form for matching + enumeration


@dataclass(frozen=True)
class ResolvedPipeRun:
    """One validated plumbing run — a routed 3D polyline.

    ``z_m`` carries the absolute project-frame invert at every path vertex (None when the
    run was authored with no elevations at all); ``z_start_m``/``z_end_m`` remain for the
    consumers that only need the endpoints. ``length_m`` is developed 3D length —
    vertical drops (repeated plan point, different z) count."""

    uid: str
    tag: str
    storey: str
    system: str
    path: Ring
    diameter_m: float
    z_start_m: float | None
    z_end_m: float | None
    length_m: float
    # Fixture tags this run carries. Authored on ``PipeRun.serves``; carried into the IR so
    # a check can ask "which run vents/drains this fixture" without re-reading plan source.
    serves: tuple[str, ...] = ()
    z_m: tuple[float, ...] | None = None  # per-vertex absolute inverts, len == len(path)
    wall_refs: tuple[str | None, ...] = ()  # host wall per segment; () -> none declared
    material: str | None = None
    finish: str | None = None      # applied coating, e.g. "lacquered" over copper
    insulation: str | None = None  # pipe-insulation spec, billed by the foot; None -> bare
    # Self-regulating heater cable on the run, billed by the foot beside the insulation.
    # Separate from it on purpose: a traced AND lagged run is the normal outdoor spec.
    freeze_protection: str | None = None


@dataclass(frozen=True)
class ResolvedPipeAccessory:
    """One in-line supply device located on its host run.

    ``z_m`` is absolute project-frame like every other resolved z: authored elevations are
    storey-relative, and where none was authored the resolver has already substituted the
    host run's invert at the nearest path vertex, so a consumer never has to know which of
    the two it got."""

    uid: str
    tag: str
    storey: str
    kind: str
    position: tuple[float, float]
    z_m: float
    pipe_ref: str | None = None
    # The host run's system ("water_cold"/"water_hot"/…) and bore, copied at resolve so a
    # check or a schedule row does not have to re-find the run to size the device.
    system: str | None = None
    diameter_m: float | None = None
    serves: tuple[str, ...] = ()
    accessible: bool = False
    room: str | None = None
    wall_ref: str | None = None
    model: str = ""
    install_parts: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedSolarPanel:
    """One PV module as a tilted box on its roof plane.

    ``corners_bottom``/``corners_top`` are matching counter-clockwise (in plan) rings of
    four 3D points in metres — the module underside (standoff off the roof plane) and its
    face. Every emitter (IFC faceted shell, glTF triangles, viewer geometry) reads these
    same corners, so the tilt math lives in resolve/solar.py alone."""

    uid: str
    tag: str
    storey: str
    roof_ref: str
    corners_bottom: tuple[tuple[float, float, float], ...]
    corners_top: tuple[tuple[float, float, float], ...]
    watts: float
    product: str = ""
    # Electrical identity of the module, carried through unchanged from the authored
    # SolarPanel (→ model/structure.py): series string, rated and cold-corrected Voc, and
    # whether a SunSpec RSD transmitter is fitted. The solar takeoff and the 690.12 check
    # read these; the tilt math ignores them.
    string: str = ""
    voc: float | None = None
    voc_cold: float | None = None
    rsd: bool = False


@dataclass(frozen=True)
class ResolvedConduitRun:
    """One raceway trunk: plan polyline + absolute end elevations, developed length.

    ``length_m`` is the pull length — plan length plus the vertical rise between the two
    end elevations (the run rises at its last point; → model/mep.py ConduitRun)."""

    uid: str
    tag: str
    storey: str
    path: Ring
    trade_size_m: float
    z_start_m: float | None
    z_end_m: float | None
    length_m: float
    from_ref: str | None = None
    to_ref: str | None = None
    # ``Service`` value, or None for a capped spare (→ model/mep.py ConduitRun.service).
    service: str | None = None


@dataclass(frozen=True)
class ResolvedLightRun:
    """One linear luminaire run: plan polyline, mounted height, developed length.

    A ``ResolvedConduitRun`` sibling. ``z_m`` is the project-frame absolute height the
    strip sits at (resolved from the authored ``Mount`` against its storey), and
    ``length_m`` is plan length — a strip does not rise at its end the way a conduit
    trunk does, so there is nothing to add (→ model/mep.py LightRun)."""

    uid: str
    tag: str
    storey: str
    path: Ring
    z_m: float
    length_m: float
    type_ref: str
    circuit: str | None = None
    psu_ref: str | None = None
    controlled_by: tuple[str, ...] = ()
    room: str | None = None


@dataclass(frozen=True)
class ResolvedSleeve:
    """A cast-in-place sleeve, plus how far it sits from the fixture's expected drain point.

    ``host_slab`` keeps its historical name but may now be any concrete host —
    ``host_category`` says which ("slab" | "footing" | "wall"). ``axis`` is "vertical"
    for a through-slab drop, "horizontal" for a foundation-wall/rim crossing whose
    centerline sits at ``center_z_m``."""

    uid: str
    tag: str
    storey: str
    host_slab: str
    center: tuple[float, float]
    pipe_d_m: float
    sleeve_d_m: float
    z0_m: float
    z1_m: float
    serves_fixture: str | None
    expected_center: tuple[float, float] | None  # None -> UNKNOWN, not silent PASS
    offset_m: float | None
    axis: str = "vertical"
    host_category: str = "slab"
    center_z_m: float | None = None  # horizontal sleeves: absolute centerline elevation
    purpose: str = "drain"


@dataclass(frozen=True)
class ResolvedDrainTile:
    """A ``DrainTile`` spec flattened to SI, carried on the bedding that runs it.

    The bare ``drain_tile: bool`` says only that one exists, which left the take-off billing
    every tile on the project as one undifferentiated run of pipe and the perimeter-drain
    detail with nowhere to read a size from. Everything downstream groups and draws on this.
    """

    diameter_m: float
    material: str
    sock: bool
    discharge: str | None
    rock_width_m: float | None
    rock_depth_m: float | None


@dataclass(frozen=True)
class ResolvedFootingBedding:
    """Bedding prep resolved against its host — a footing solid, or the wall founded on it."""

    uid: str
    tag: str
    storey: str
    host: str  # Footing tag, or the wall tag when the bed is what the wall stands on
    outline: Ring
    z0_m: float  # bottom of excavation (compacted stone-bed underside)
    z1_m: float  # top of bedding == footing underside
    aggregate: str
    geotextile: bool
    drain_tile: bool
    perimeter_insulation_m: float | None
    cast_foam_in_aggregate: bool
    # None where the bedding only carries the bool — see ResolvedDrainTile.
    drain_tile_spec: ResolvedDrainTile | None = None
    # The authored non-frost-susceptible gradation claim — see FootingBedding. None = not
    # stated, which is not the same as False and never counts toward a frost depth.
    non_frost_susceptible: bool | None = None


@dataclass(frozen=True)
class ResolvedDuct:
    """A validated duct run — bay occupancy/bearing-crossing derived by ``resolve.mep``."""

    uid: str
    tag: str
    storey: str
    system: str
    path: Ring
    width_m: float
    depth_m: float
    routing: str
    floor_ref: str | None
    crossings: tuple[tuple[float, float], ...]  # bearing-line crossing points
    conflicts: tuple[str, ...]  # non-empty -> structural FAIL, named per conflict
    depth_ok: bool  # duct depth fits within the joist depth
    design_cfm: float | None = None  # authored intent, echoed for the duct schedule
    # Round section, when the run has one. ``width_m``/``depth_m`` are then both the
    # diameter, so every consumer that measures a duct against a bay, a soffit or a sheet
    # keeps working without asking which shape it is; this field is what the *takeoff* and
    # the sweep need, because a 6" round and a 6x6 rectangular are two different orders.
    diameter_m: float | None = None
    # Absolute project-frame centreline elevation per path vertex, mirroring
    # ``ResolvedPipeRun.z_m``. Never None: where the run authors nothing the resolver
    # derives one z from its joist bay, its soffit or the storey datum, so a consumer never
    # has to re-derive it (and never has to re-derive it *differently* — this used to live
    # in the IFC emitter alone, which is why nothing else could draw a duct).
    z_m: tuple[float, ...] = ()
    # Developed length — plan run plus every rise. The BOM bills this; the plan-only sum it
    # replaced billed a four-storey riser as the zero length it projects to.
    length_m: float = 0.0
    material: str | None = None
    insulation: str | None = None
    soffit_ref: str | None = None


@dataclass(frozen=True)
class StackEdge:
    """A derived vertical wall-line stack edge (lower ↔ upper) (#43)."""

    lower_wall: str
    upper_wall: str
    overlap_m: float
    width_change: bool


@dataclass(frozen=True)
class ResolvedCanvasObject:
    """Resolved physical-space geometry for a free or wall-attached placeable."""

    uid: str
    tag: str
    storey: str
    domain: str
    kind: str
    type_ref: str | None
    room: str | None
    position: tuple[float, float]
    z_m: float
    rotation_degrees: float
    footprint: Ring
    required_clearances: tuple[Ring, ...] = ()
    recommended_clearances: tuple[Ring, ...] = ()
    attachment_wall: str | None = None
    attachment_face: str | None = None
    # Tag of the furniture group this object belongs to — the anchor's own tag, shared by the
    # anchor and every occupant of its zone (→ resolve/placeable_groups). ``None`` when the
    # object stands alone. Group members do not encroach on each other's recommended
    # clearance, and a UI that drags a table can drag its chairs with it.
    placement_group: str | None = None
    # The circuit that feeds this object, for the placeables that consume power
    # (ElectricalDevice, Equipment, Register); ``None`` for a sofa. Carried so the UI can
    # answer "which circuit is this outlet on?" from the selection, without re-deriving the
    # panel schedule in the browser.
    circuit: str | None = None
    # The *authored* mount, carried alongside the resolved ``z_m`` it produced. An editor needs
    # both: z_m to draw the object, the mount to show (and write back) the height someone
    # actually typed — "46 in above this floor" survives a storey datum change, 2.34 m does not.
    mount: Mount | None = None


@dataclass
class ResolvedModel:
    plan: PlanModel
    walls: list[ResolvedWall] = field(default_factory=list)
    junctions: list[ResolvedJunction] = field(default_factory=list)
    openings: list[ResolvedOpening] = field(default_factory=list)
    solids: list[ResolvedSolid] = field(default_factory=list)
    construction_returns: list[ResolvedConstructionReturn] = field(default_factory=list)
    roofs: list[ResolvedRoof] = field(default_factory=list)
    stairs: list[ResolvedStair] = field(default_factory=list)
    floors: list[ResolvedFloor] = field(default_factory=list)
    soffits: list[ResolvedSoffit] = field(default_factory=list)
    braces: list[ResolvedBrace] = field(default_factory=list)
    floor_heat: list[ResolvedFloorHeat] = field(default_factory=list)
    rooms: list[ResolvedRoom] = field(default_factory=list)
    ceilings: list[ResolvedCeiling] = field(default_factory=list)
    panelings: list[ResolvedPaneling] = field(default_factory=list)
    # Interior millwork: derived stools and shelf banks (→ resolve/millwork.py).
    window_stools: list[ResolvedWindowStool] = field(default_factory=list)
    shelf_banks: list[ResolvedShelfBank] = field(default_factory=list)
    conditions: list[BoundaryCondition] = field(default_factory=list)
    stack_edges: list[StackEdge] = field(default_factory=list)
    # Derived wall-line chains (#43): collinear within a storey, stacked across them,
    # each with one origin and one direction. Built from the *authored* plan in the
    # pipeline's first stage, because ``topology`` needs a wall's line while it is
    # resolving that wall (→ resolve/layout_lines.py). Never exported as an element.
    layout_lines: list[ResolvedLayoutLine] = field(default_factory=list)
    pipe_runs: list[ResolvedPipeRun] = field(default_factory=list)
    pipe_accessories: list[ResolvedPipeAccessory] = field(default_factory=list)
    sleeves: list[ResolvedSleeve] = field(default_factory=list)
    ducts: list[ResolvedDuct] = field(default_factory=list)
    conduits: list[ResolvedConduitRun] = field(default_factory=list)
    light_runs: list[ResolvedLightRun] = field(default_factory=list)
    solar_panels: list[ResolvedSolarPanel] = field(default_factory=list)
    footing_beddings: list[ResolvedFootingBedding] = field(default_factory=list)
    canvas_objects: list[ResolvedCanvasObject] = field(default_factory=list)
    # Derived geometry: every solid the building contributes, built once by the pipeline's
    # final stage so the emitters serialize rather than re-derive it. Optional because
    # ``resolve_preview`` (the drag-overlay path) skips the stage.
    geometry: GeometryModel | None = None
    # Per-stage resolve timings in milliseconds (Phase 0 instrumentation). Not serialized
    # as source; surfaced to the UI via the `perf` payload for measurement, not correctness.
    timings: dict[str, float] = field(default_factory=dict)
    # Tag -> element, across every collection above that carries a ``tag`` (not junctions,
    # keyed by ``node_tag``, or the untagged ``conditions``/``stack_edges``). Built once by
    # ``resolve()`` as its final step (→ index_by_tag) — this dataclass is otherwise mutable,
    # so an index built any earlier would go stale the moment a later stage appended to a
    # collection; nothing mutates ``self`` after that point, so building it there is honest
    # rather than lazy-and-hopeful. 56 call sites hand-rolled
    # ``next((x for x in coll if x.tag == tag), None)`` over one collection each — this
    # covers all of them in one dict lookup instead of a linear scan.
    _tag_index: dict[str, object] = field(default_factory=dict, repr=False, compare=False)

    def index_by_tag(self) -> None:
        """Build ``_tag_index`` from every current collection. Call once, after every
        resolve stage has finished mutating ``self`` — see the field's docstring."""
        index: dict[str, object] = {}
        for collection in (
            self.walls, self.openings, self.solids, self.construction_returns, self.roofs,
            self.stairs, self.floors, self.soffits, self.braces, self.floor_heat, self.rooms,
            self.panelings, self.window_stools, self.shelf_banks,
            self.pipe_runs, self.pipe_accessories, self.sleeves, self.ducts,
            self.conduits, self.light_runs, self.solar_panels, self.footing_beddings,
            self.canvas_objects,
        ):
            for element in collection:
                tag = getattr(element, "tag", None)
                if tag is not None and tag not in index:
                    index[tag] = element
        self._tag_index = index

    def by_tag(self, tag: str) -> object | None:
        """Any tagged element, from any collection ``index_by_tag`` covers. Falls back to a
        linear scan of ``walls`` alone if the index hasn't been built yet (e.g. a hand-built
        ``ResolvedModel`` in a test) — the old ``next(...)`` behavior, not silently empty."""
        if self._tag_index:
            return self._tag_index.get(tag)
        return self.wall(tag)

    def wall(self, tag: str) -> ResolvedWall | None:
        if self._tag_index:
            element = self._tag_index.get(tag)
            return element if isinstance(element, ResolvedWall) else None
        return next((w for w in self.walls if w.tag == tag), None)

    def all_members(self) -> list[FramedMember]:
        out: list[FramedMember] = []
        for w in self.walls:
            out.extend(w.members)
        for stair in self.stairs:
            out.extend(stair.members)
        for floor in self.floors:
            out.extend(floor.members)
        for roof in self.roofs:
            out.extend(roof.members)
        for brace in self.braces:
            out.extend(brace.members)
        for soffit in self.soffits:
            out.extend(soffit.members)
        return out

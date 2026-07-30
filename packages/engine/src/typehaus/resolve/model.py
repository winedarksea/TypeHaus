"""ResolvedModel — the IR between the validated PlanModel and the emitters (→ 02).

Whole-building, not per-storey: storeys resolve in the shared project-north frame and are
placed at derived elevations, so sections/details cut across storeys (→ 02 §Pipeline).
All coordinates are canonical SI meters. These are plain frozen dataclasses (not Pydantic)
— they are engine-internal IR, never authored or serialized as source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from typehaus.model.enums import ConditionKind
from typehaus.model.plan import PlanModel

if TYPE_CHECKING:  # the IR imports this module, so the reference stays type-only
    from typehaus.model.placeables import Mount
    from typehaus.resolve.geometry_ir import GeometryModel

# A polygon ring: list of (x, y) in meters. Layer polygons are simple rings.
Ring = list[tuple[float, float]]


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

    @property
    def thickness_m(self) -> float:
        """Total wall depth. Cavity layers sit inside their host and add nothing."""
        return sum(ly.thickness_m for ly in self.layers if not ly.is_cavity)

    def depth_layers(self) -> tuple[ResolvedLayer, ...]:
        """The layers that occupy their own slice of the wall depth, interior→exterior."""
        return tuple(ly for ly in self.layers if not ly.is_cavity)


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
    # The existing derived boundary-condition key this return documents (stacking /
    # assembly-change), so an overlay can join return -> condition -> Transition.
    condition_key: str | None = None


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
class ResolvedFootingBedding:
    """Sub-footing excavation/bedding prep resolved against its host footing solid."""

    uid: str
    tag: str
    storey: str
    host_footing: str
    outline: Ring
    z0_m: float  # bottom of excavation (compacted stone-bed underside)
    z1_m: float  # top of bedding == footing underside
    aggregate: str
    geotextile: bool
    drain_tile: bool
    perimeter_insulation_m: float | None
    cast_foam_in_aggregate: bool


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
    braces: list[ResolvedBrace] = field(default_factory=list)
    floor_heat: list[ResolvedFloorHeat] = field(default_factory=list)
    rooms: list[ResolvedRoom] = field(default_factory=list)
    conditions: list[BoundaryCondition] = field(default_factory=list)
    stack_edges: list[StackEdge] = field(default_factory=list)
    pipe_runs: list[ResolvedPipeRun] = field(default_factory=list)
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
    geometry: "GeometryModel | None" = None
    # Per-stage resolve timings in milliseconds (Phase 0 instrumentation). Not serialized
    # as source; surfaced to the UI via the `perf` payload for measurement, not correctness.
    timings: dict[str, float] = field(default_factory=dict)

    def wall(self, tag: str) -> ResolvedWall | None:
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
        return out

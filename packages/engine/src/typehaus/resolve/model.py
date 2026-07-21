"""ResolvedModel — the IR between the validated PlanModel and the emitters (→ 02).

Whole-building, not per-storey: storeys resolve in the shared project-north frame and are
placed at derived elevations, so sections/details cut across storeys (→ 02 §Pipeline).
All coordinates are canonical SI meters. These are plain frozen dataclasses (not Pydantic)
— they are engine-internal IR, never authored or serialized as source.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.model.enums import ConditionKind
from typehaus.model.plan import PlanModel

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
    is_door: bool


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
    eave_z_m: float
    ridge_z_m: float
    ridge_direction: str
    assembly: str
    surface_area_m2: float
    members: tuple[FramedMember, ...] = ()


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
class ResolvedRoom:
    uid: str
    tag: str
    storey: str
    occupancy: str
    conditioned: bool
    clear_face: Ring  # interior face polygon (core + resolved lining)
    area_m2: float
    floor_finish: str | None


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
    """One validated plumbing run — a plan-frame polyline with invert elevations."""

    uid: str
    tag: str
    storey: str
    system: str
    path: Ring
    diameter_m: float
    z_start_m: float | None
    z_end_m: float | None
    length_m: float


@dataclass(frozen=True)
class ResolvedSleeve:
    """A cast-in-place sleeve, plus how far it sits from the fixture's expected drain point."""

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


@dataclass(frozen=True)
class StackEdge:
    """A derived vertical wall-line stack edge (lower ↔ upper) (#43)."""

    lower_wall: str
    upper_wall: str
    overlap_m: float
    width_change: bool


@dataclass
class ResolvedModel:
    plan: PlanModel
    walls: list[ResolvedWall] = field(default_factory=list)
    openings: list[ResolvedOpening] = field(default_factory=list)
    solids: list[ResolvedSolid] = field(default_factory=list)
    roofs: list[ResolvedRoof] = field(default_factory=list)
    stairs: list[ResolvedStair] = field(default_factory=list)
    floors: list[ResolvedFloor] = field(default_factory=list)
    floor_heat: list[ResolvedFloorHeat] = field(default_factory=list)
    rooms: list[ResolvedRoom] = field(default_factory=list)
    conditions: list[BoundaryCondition] = field(default_factory=list)
    stack_edges: list[StackEdge] = field(default_factory=list)
    pipe_runs: list[ResolvedPipeRun] = field(default_factory=list)
    sleeves: list[ResolvedSleeve] = field(default_factory=list)
    ducts: list[ResolvedDuct] = field(default_factory=list)
    footing_beddings: list[ResolvedFootingBedding] = field(default_factory=list)
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
        return out

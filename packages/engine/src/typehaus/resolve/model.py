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


@dataclass(frozen=True)
class ResolvedStair:
    """A code-sized single-flight stair and its generated framing members."""

    uid: str
    tag: str
    storey: str
    to_storey: str
    outline: Ring
    riser_count: int
    riser_height_m: float
    tread_depth_m: float
    members: tuple[FramedMember, ...]


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
    rooms: list[ResolvedRoom] = field(default_factory=list)
    conditions: list[BoundaryCondition] = field(default_factory=list)
    stack_edges: list[StackEdge] = field(default_factory=list)

    def wall(self, tag: str) -> ResolvedWall | None:
        return next((w for w in self.walls if w.tag == tag), None)

    def all_members(self) -> list[FramedMember]:
        out: list[FramedMember] = []
        for w in self.walls:
            out.extend(w.members)
        for stair in self.stairs:
            out.extend(stair.members)
        return out

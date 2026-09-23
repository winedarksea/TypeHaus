"""The analytical model: nodes, members, supports and loads, format-neutral.

One graph, four readers. The IFC structural analysis view (``emit/ifc/analytical.py``),
the RISA centreline DXF (``emit/draw/dxf_structure.py``), the per-member CSV and the PyNite
script (``emit/analytical/``) all read *this* and nothing else, so they cannot disagree
about which node a beam lands on or what a column's base is. It is the same reason the
physical IFC shares one ``IfcMaterialProfileSet`` between the geometry and the analytical
member: two definitions of one thing is how they drift apart.

**Every field here is a structural claim this engine makes and owns** (owner decision,
2026-09-12, superseding plan 31's "authored, never inferred"). A support's fixity, a
member-end release, a load and its case are all derived from the model and each carries
its ``basis`` — the prose a reviewer disagrees with — so the claim is visible where it is
made. What could not be derived is listed in :attr:`AnalyticalModel.gaps`, in words, rather
than filled with a default and left silent.

Units are SI throughout (metres, newtons, newton-metres, N/m), matching the IFC's project
units. ``analytical/pynite_map.py`` converts to pounds and inches for the US-practice
solver; nothing else converts anything.

This package is a **leaf**: it imports ``model`` / ``resolve`` / ``quantities`` /
``engineering`` / ``wind`` and never ``checks`` / ``takeoff`` / ``emit``
(``tests/test_analytical_leaf.py`` walks the AST). Emitters import it; it imports no emitter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typehaus.resolve.framing.profiles import CrossSection

#: Node coordinates snap to this before two are merged. A post top 1 mm off a beam axis is
#: the same node; 5 mm keeps float noise from doubling a node without merging two studs.
NODE_SNAP_M = 0.005


class Fixity(str, Enum):
    """What a support restrains. Only the two residential practice needs; a spring is not
    a claim this engine can make about a footing."""

    FIXED = "fixed"      # all six DOF — a cast column doweled into its pad
    PINNED = "pinned"    # translations only — a post on a base, a beam on a wall


class LoadCaseKind(str, Enum):
    """One source per case, the way the records name them. Combinations are separate."""

    DEAD = "dead"
    LIVE = "live"
    SNOW = "snow"
    WIND = "wind"
    EARTH = "earth"
    GUARD = "guard"  # IRC R301.5's 200 lb — its own case because it is never combined with wind


@dataclass(frozen=True)
class Node:
    id: str          # stable across runs: derived from what meets here, never an ordinal
    x_m: float
    y_m: float
    z_m: float

    @property
    def xyz(self) -> tuple[float, float, float]:
        return (self.x_m, self.y_m, self.z_m)


@dataclass(frozen=True)
class Releases:
    """Moment releases at the two ends (i = ``n0``, j = ``n1``). A beam bearing on a post
    top is released at that end; a rafter in a hanger likewise. Axial and shear are never
    released here — a release that would drop a member is not a modelling choice.

    A **hinge** frees bending about ONE global axis ("X" | "Y") and holds the other: a
    column top under a post cap, free in the carried beam's plane and held against the
    beam's roll. ``*_moment`` frees both bending axes; ``basis`` says why."""

    i_moment: bool = False
    j_moment: bool = False
    i_hinge: str | None = None
    j_hinge: str | None = None
    basis: str = ""

    @property
    def any(self) -> bool:
        return bool(self.i_moment or self.j_moment or self.i_hinge or self.j_hinge)

    def end_text(self, end: str) -> str:
        """One end in words, the one spelling every reader prints."""
        moment, hinge = ((self.i_moment, self.i_hinge) if end == "i"
                         else (self.j_moment, self.j_hinge))
        if moment:
            return "moment released"
        return f"hinge about global {hinge}" if hinge else "continuous"


@dataclass(frozen=True)
class Member:
    id: str                      # e.g. "BM-SG-BLC" or "FL-B-DECK:joist-012"
    tag: str                     # the physical element's tag (the parent for a framed member)
    category: str                # beam | column | post | joist | rafter | header | brace
    n0: str
    n1: str
    section: CrossSection
    material: str                # ``emit/ifc/profiles.material_name``'s vocabulary, verbatim
    e_pa: float                  # modulus actually used, Pa; ``e_basis`` says where from
    e_basis: str                 # "record roof_beam/RB-HOUSE E_adjusted" | "assumed: LVL 2.0e6 psi"
    releases: Releases = Releases()
    roll_deg: float = 0.0        # rotation of the section about the member axis
    item_ids: tuple[str, ...] = ()   # engineering items that grade this member
    physical_uid: str = ""       # the element's uid; the IFC links back through it
    physical_child_key: str | None = None  # a framed member's child key, for the child GUID
    physical_ifc_tag: str | None = None    # tag the physical IFC filed it under, when different

    @property
    def is_vertical(self) -> bool:
        return self.category in ("column", "post")


@dataclass(frozen=True)
class Support:
    node: str
    fixity: Fixity
    basis: str            # why: "lateral system — no brace, no wall (deck_post/PT-SG-BF2)"
    item_id: str | None = None
    element_tag: str = ""
    #: Rotational restraint about global X, Y, Z when the fixity alone does not say it.
    #: ``None`` = from ``fixity`` (FIXED: all three; PINNED: none). A beam END bearing on a
    #: wall or a seat is pinned for bending but cannot ROLL — the plate it sits on holds it —
    #: so its support restrains rotation about the beam's own axis and nothing else. Without
    #: that a moment-released beam between two pins is a mechanism, and every solver says so.
    rotations: tuple[bool, bool, bool] | None = None

    def restrained_rotations(self) -> tuple[bool, bool, bool]:
        if self.rotations is not None:
            return self.rotations
        return (True, True, True) if self.fixity is Fixity.FIXED else (False, False, False)


@dataclass(frozen=True)
class LoadCase:
    kind: LoadCaseKind
    description: str      # "IRC Table R301.5 deck live 40 psf" — the basis in one line

    @property
    def name(self) -> str:
        return self.kind.value


@dataclass(frozen=True)
class MemberLoad:
    """A line load on a member, in GLOBAL axes. ``w0``/``w1`` at ``x0``/``x1`` (fractions
    of length, 0..1) so a trapezoid and a partial load are both one record."""

    case: LoadCaseKind
    member: str
    direction: str        # "GX" | "GY" | "GZ"
    w0_n_m: float
    w1_n_m: float
    x0: float = 0.0
    x1: float = 1.0
    source: str = ""      # "roof_beam/RB-HOUSE uniform_load 560 plf"


@dataclass(frozen=True)
class MemberPointLoad:
    case: LoadCaseKind
    member: str
    direction: str
    p_n: float
    x: float              # fraction of length
    source: str = ""


@dataclass(frozen=True)
class NodeLoad:
    case: LoadCaseKind
    node: str
    fx_n: float = 0.0
    fy_n: float = 0.0
    fz_n: float = 0.0
    mx_nm: float = 0.0
    my_nm: float = 0.0
    mz_nm: float = 0.0
    source: str = ""


@dataclass(frozen=True)
class Plate:
    """Four-node concrete shell. Node order follows PyNite's i-j-m-n convention."""

    id: str
    tag: str
    i: str
    j: str
    m: str
    n: str
    thickness_m: float
    material: str
    e_pa: float
    poisson: float
    basis: str


@dataclass(frozen=True)
class SupportSpring:
    """Nodal support spring; direction is the permitted global displacement sign."""

    node: str
    dof: str
    stiffness_n_m: float
    direction: str | None
    basis: str


@dataclass(frozen=True)
class PlatePressure:
    case: LoadCaseKind
    plate: str
    pressure_pa: float
    source: str = ""


@dataclass(frozen=True)
class Combination:
    """An ASD combination the records actually graded against (``LimitState.combination``),
    never a full IBC 1605.3.1 set the calculation did not run."""

    name: str
    factors: dict[LoadCaseKind, float]
    source: str


@dataclass(frozen=True)
class AnalyticalModel:
    nodes: tuple[Node, ...]
    members: tuple[Member, ...]
    supports: tuple[Support, ...]
    cases: tuple[LoadCase, ...]
    member_loads: tuple[MemberLoad, ...] = ()
    member_point_loads: tuple[MemberPointLoad, ...] = ()
    node_loads: tuple[NodeLoad, ...] = ()
    plates: tuple[Plate, ...] = ()
    support_springs: tuple[SupportSpring, ...] = ()
    plate_pressures: tuple[PlatePressure, ...] = ()
    combinations: tuple[Combination, ...] = ()
    #: Keep the standard one-combination-per-case exports. Coupled nonlinear soil-contact
    #: models disable these because an earth-only case has no gravity to keep contact active.
    include_unit_case_combinations: bool = True
    #: The engineering items this model was scoped from, sorted.
    scope: tuple[str, ...] = ()
    #: Claims a reviewer is entitled to reject, one line each — the assumed moduli, the
    #: rigid-link convention at a post top, the load split. Printed in every export.
    assumptions: tuple[str, ...] = ()
    #: What the model does NOT carry, in words: "retaining walls W-SG-* not modelled as
    #: surface members", "rafter/RF-GARAGE has no analytical representation". (The example
    #: used to read ``lateral_uplift/RF-HOUSE``; that kind retired on 2026-09-14 when the
    #: roof's uplift became a published read, so there is no such id to name.)
    gaps: tuple[str, ...] = ()
    _index: dict[str, Node] = field(default_factory=dict, repr=False, compare=False)

    def node(self, node_id: str) -> Node:
        if not self._index:
            self._index.update({n.id: n for n in self.nodes})
        return self._index[node_id]

    def member(self, member_id: str) -> Member:
        for m in self.members:
            if m.id == member_id:
                return m
        raise KeyError(member_id)

    def length_m(self, member: Member) -> float:
        a, b = self.node(member.n0), self.node(member.n1)
        return ((a.x_m - b.x_m) ** 2 + (a.y_m - b.y_m) ** 2 + (a.z_m - b.z_m) ** 2) ** 0.5

    def supports_at(self, node_id: str) -> tuple[Support, ...]:
        return tuple(s for s in self.supports if s.node == node_id)

    def loads_on(self, member_id: str) -> tuple[MemberLoad, ...]:
        return tuple(load for load in self.member_loads if load.member == member_id)

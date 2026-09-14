"""Centrelines: the 3-D axis of every scoped member, and the nodes where they meet.

Two geometries feed it and neither is a centreline to start with. A standalone ``Beam`` or
``Post`` resolves to a :class:`~typehaus.resolve.model.ResolvedSolid` — a plan outline and
two elevations — so the axis is the outline's long-axis midline at mid-height, or the
``sweep`` path, which already *is* the centreline, for a tilted beam.

**The rigid-link convention, stated once because every reader inherits it.** A bearing node
lies on the axis of the member BEING SUPPORTED, and whatever supports it is drawn up to
that node: a post's top goes to the beam centreline it carries, and a beam carrying another
beam is split at the seat and reaches up to it. The supported member therefore stays
straight — it is the one carrying the span the calculation graded — at the cost of half the
two members' depths of eccentricity, which is not modelled.

**Releases are for a member's own END on another member.** A beam set on a post top at its
end is free to rotate over it; a beam running CONTINUOUS over an interior bearing is not,
and releasing there would leave the cantilever beyond it a mechanism rather than a
cantilever. At a SUPPORT node nothing is released at all — ``supports.py`` says which
rotations that node is free in, and a released end on a pinned support is a member spinning
on its own axis.

Nodes are merged incrementally within :data:`NODE_SNAP_M` and identified by *what meets
there* — never by an ordinal, which would renumber the whole model when one member moved.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from typehaus.analytical import materials
from typehaus.analytical.graph import NODE_SNAP_M, Member, Node, Releases
from typehaus.resolve.framing.profiles import CrossSection, cross_section

_Vec3 = tuple[float, float, float]
_Vec2 = tuple[float, float]

#: A bearing within this fraction of a tip IS that tip, rather than an interior support the
#: beam would be split at.
_END_FRACTION = 0.02
#: The one line every reader of this graph inherits — see the module docstring.
_RIGID_LINK = ("rigid link: a bearing node sits on the centreline of the member being "
               "SUPPORTED, and what supports it is drawn up to that node — a column's top "
               "reaches the beam it carries, a beam carrying a beam reaches its seat. The "
               "supported member stays straight; half the two members' depths of bearing "
               "eccentricity is not modelled")
#: The PLAN half of the same idealization, and the one that decides whether a joint exists
#: at all. **Members meet at WORK POINTS.** A beam that stops short of the post it bears on —
#: because another post stands on that one and the beam hangs off its face — has its
#: analytical axis run out to the post's own axis, which is where the joint is. Two beam ends
#: arriving at one column from opposite sides then share a node with the column top; left at
#: their own physical ends they are two nodes 5 1/2" apart, each carrying a single member,
#: and the solver reports that correctly as a rotational instability.
#:
#: **The node is moved by extending the AXIS, not by relocating the node.** A node placed off
#: the end of the member it belongs to is not found by ``_stations``, so the member is built
#: between the wrong pair of stations and the instability simply moves to the far end.
#:
#: Half the post's width is the whole eccentricity, and it is not modelled. Catlin's case is
#: 2 3/4" — half a 6x6 — at the two porch beam lines, where PT-SG-BF2 / PT-SG-BR2 stand on
#: PT-SG-FCOL / PT-SG-COL and the four beams hang off their faces on HU212-3 hangers. The
#: 0.5-parameter guard keeps this to a joint detail: a post half a span away from the beam it
#: is named under is a modelling error, not an eccentricity, and stretching the member to it
#: would hide that.
_WORK_POINT = ("work point: a beam that stops short of a POST it bears on is run out to that "
               "post's axis, so both beams at a column share the column's node. The plan "
               "eccentricity between the beam end and the column under it — half the post's "
               "width — is not modelled")

#: The two rules a reader of this graph has to know beyond the rigid link.
_SPLIT_RULE = ("every node on a member's interior splits that member into two continuous "
               "pieces sharing it (ids <tag>#1, <tag>#2 ...), with no release at the split "
               "and the line loads carried per unit length on each piece, so the total is "
               "unchanged. A seat node that only the seated beam knew about would be free "
               "to slide along the beam it sits on")
_SUPPORT_ROTATIONS = (
    "at a SUPPORT node the member end is NOT moment-released — the support says which "
    "rotation is free, because a released end contributes no rotational stiffness in any "
    "axis and a pin under it then holds nothing. A beam end on a wall is free in bending "
    "and held against roll about its own axis (the bearing plate). A pinned post base is "
    "free to lean in the plane of its frame, held against twist, and held against rolling "
    "with the beam it carries — that last restraint is the DECK PLANE, which this graph "
    "carries as a line load and not as members; its reaction moment is essentially zero "
    "under gravity and is the check on the claim")


@dataclass
class _NodeSet:
    """Points merged within :data:`NODE_SNAP_M`, each labelled by what meets there."""

    points: list[_Vec3] = field(default_factory=list)
    labels: list[set[str]] = field(default_factory=list)

    def add(self, xyz: _Vec3, label: str) -> int:
        for index, point in enumerate(self.points):
            if math.dist(point, xyz) <= NODE_SNAP_M:
                self.labels[index].add(label)
                return index
        self.points.append(xyz)
        self.labels.append({label})
        return len(self.points) - 1

    def ids(self) -> list[str]:
        return ["N-" + "+".join(sorted(labels)) for labels in self.labels]

    def nodes(self) -> tuple[Node, ...]:
        return tuple(Node(node_id, point[0], point[1], point[2])
                     for node_id, point in zip(self.ids(), self.points, strict=True))


@dataclass
class MemberGraph:
    """Members, their nodes, and the index the supports and loads stages read back."""

    nodes: tuple[Node, ...] = ()
    members: tuple[Member, ...] = ()
    assumptions: tuple[str, ...] = ()
    #: post tag -> its base node id.
    post_base: dict[str, str] = field(default_factory=dict)
    #: post tag -> its top node id.
    post_top: dict[str, str] = field(default_factory=dict)
    #: (beam tag, support tag) -> the node id where that bearing sits.
    bearing_node: dict[tuple[str, str], str] = field(default_factory=dict)
    #: beam tag -> its member ids, in order along the axis.
    beam_spans: dict[str, tuple[str, ...]] = field(default_factory=dict)
    #: beam tag -> its total centreline length, metres.
    beam_length_m: dict[str, float] = field(default_factory=dict)
    #: beam tag -> its unit plan direction, for the roll axis a bearing plate restrains.
    beam_axis_xy: dict[str, tuple[float, float]] = field(default_factory=dict)
    #: (beam tag, wall/footing/pad tag) -> node id, the bearings that become supports.
    wall_bearing: dict[tuple[str, str], str] = field(default_factory=dict)
    #: post tag -> the beam tags it carries, for the roll axis its base is braced about.
    post_carries: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class _Axis:
    """One member's centreline and the section carried along it."""

    p0: _Vec3
    p1: _Vec3
    section: CrossSection

    def at(self, t: float) -> _Vec3:
        return (self.p0[0] + (self.p1[0] - self.p0[0]) * t,
                self.p0[1] + (self.p1[1] - self.p0[1]) * t,
                self.p0[2] + (self.p1[2] - self.p0[2]) * t)

    def param_of(self, xy: _Vec2) -> float:
        dx, dy = self.p1[0] - self.p0[0], self.p1[1] - self.p0[1]
        denominator = dx * dx + dy * dy
        if denominator < 1e-12:
            return 0.0
        return ((xy[0] - self.p0[0]) * dx + (xy[1] - self.p0[1]) * dy) / denominator

    @property
    def length_m(self) -> float:
        return math.dist(self.p0, self.p1)


def _to_work_points(plan: Any, beam: Any, axis: _Axis,
                    assumptions: list[str]) -> _Axis:
    """Run a beam's analytical axis out to the POST axes it bears on — see ``_WORK_POINT``.

    A no-op for every beam whose posts stand under it, which is almost all of them: the
    projection of the post's centre already falls inside the span and the axis is returned
    unchanged.
    """
    from typehaus.model.structure import Post

    p0, p1 = axis.p0, axis.p1
    moved = False
    for ref in sorted(beam.bearing_refs or ()):
        support = plan.by_tag(ref)
        if not isinstance(support, Post):
            continue
        param = axis.param_of(support.position.xy_m)
        if -0.5 < param < 0.0:
            p0 = (support.position.xy_m[0], support.position.xy_m[1], p0[2])
            moved = True
        elif 1.0 < param < 1.5:
            p1 = (support.position.xy_m[0], support.position.xy_m[1], p1[2])
            moved = True
    if not moved:
        return axis
    _remember(assumptions, _WORK_POINT)
    return _Axis(p0, p1, axis.section)


def solid_axis(solid: Any, section: CrossSection) -> _Axis | None:
    """The centreline of a resolved beam solid: its sweep path, or its outline's midline."""
    sweep = getattr(solid, "sweep", None)
    if sweep is not None and len(sweep.path) >= 2:
        return _Axis(tuple(sweep.path[0]), tuple(sweep.path[-1]), section)  # type: ignore[arg-type]
    ring = list(solid.outline)
    if len(ring) < 4:
        return None
    mid_z = (solid.z0_m + solid.z1_m) / 2.0
    # The outline is the section swept along the axis, so the two SHORT opposite edges are
    # the member's ends and their midpoints are the centreline.
    edges = [(ring[i], ring[(i + 1) % 4]) for i in range(4)]
    long_first = math.dist(edges[0][0], edges[0][1]) >= math.dist(edges[1][0], edges[1][1])
    first, second = (edges[1], edges[3]) if long_first else (edges[0], edges[2])
    p0, p1 = _midpoint(*first), _midpoint(*second)
    if math.dist(p0, p1) < 1e-9:
        return None
    return _Axis((p0[0], p0[1], mid_z), (p1[0], p1[1], mid_z), section)


def build_members(ctx: Any, scope: Any) -> MemberGraph:
    """Every scoped post and beam as a curve member, with its nodes and its releases."""
    from typehaus.model.structure import Beam, Post

    plan, model = ctx.plan, ctx.model
    moduli = materials.adjusted_moduli(ctx.engineering)
    nodes = _NodeSet()
    assumptions: list[str] = []
    graph = MemberGraph()

    axes: dict[str, _Axis] = {}
    for tag in scope.beams:
        solid, beam = model.by_tag(tag), plan.by_tag(tag)
        if not isinstance(beam, Beam) or solid is None or not hasattr(solid, "outline"):
            continue  # a ridge Beam is emitted as a roof member and resolves to no solid
        axis = solid_axis(solid, cross_section(beam.size))
        if axis is not None:
            axes[tag] = _to_work_points(plan, beam, axis, assumptions)
    graph.beam_length_m = {tag: axis.length_m for tag, axis in sorted(axes.items())}
    graph.beam_axis_xy = {tag: _unit_xy(axis) for tag, axis in sorted(axes.items())}

    bearings = {tag: _bearings_on(plan, model, axes, tag) for tag in sorted(axes)}
    bearing_index: dict[tuple[str, str], int] = {}
    # A beam carrying another beam is split where it is seated, even though that node sits
    # half the two depths above its own axis: registered by PARAMETER, because proximity
    # cannot find a node the eccentricity has lifted off the line.
    extra: dict[str, list[tuple[float, int]]] = {}
    for tag in sorted(axes):
        axis = axes[tag]
        for param, ref in bearings[tag]:
            index = nodes.add(axis.at(param), f"{tag}:{ref}")
            bearing_index[(tag, ref)] = index
            carrier = axes.get(ref)
            if carrier is not None:
                seat = min(max(carrier.param_of(axis.at(param)[:2]), 0.0), 1.0)
                extra.setdefault(ref, []).append((seat, index))
        for tip, label in ((0.0, "i"), (1.0, "j")):
            if all(abs(param - tip) > _END_FRACTION for param, _ in bearings[tag]):
                nodes.add(axis.at(tip), f"{tag}:{label}")

    posts: dict[str, _Axis] = {}
    for tag in scope.posts:
        solid, post = model.by_tag(tag), plan.by_tag(tag)
        if not isinstance(post, Post) or solid is None or not hasattr(solid, "outline"):
            continue
        centre = _centroid(list(solid.outline))
        base_point: _Vec3 = (centre[0], centre[1], solid.z0_m)
        top_point: _Vec3 = (centre[0], centre[1], solid.z1_m)
        carried = sorted(t for t in axes if tag in (plan.by_tag(t).bearing_refs or ()))
        if carried:
            axis = axes[carried[0]]
            # The post's top reaches the beam it carries — but it reaches it straight UP,
            # on its own axis. Taking the beam's plan point as well would move the column
            # sideways to a beam that stops short of it, and put its top somewhere the
            # column is not (``_POST_AXIS_SNAP``).
            seat = axis.at(min(max(axis.param_of(centre), 0.0), 1.0))
            top_point = (centre[0], centre[1], seat[2])
            _remember(assumptions, _RIGID_LINK)
        graph.post_base[tag] = str(nodes.add(base_point, f"{tag}:base"))
        graph.post_top[tag] = str(nodes.add(top_point, f"{tag}:top"))
        posts[tag] = _Axis(base_point, top_point, cross_section(post.size))

    # ** EVERY node on a member's interior SPLITS it. ** A seat node that hangs only on the
    # beam that lands there leaves the supporting beam unaware of it, and the node is then
    # free to slide along the beam it sits on — a mechanism the solver reports as an
    # instability, at the one place in the model where two members actually meet.
    points = list(nodes.points)
    # (id, tag, category, i, j, section, material, e_pa, e_basis, releases)
    pending: list[tuple[str, str, str, int, int, CrossSection, str, float, str, Releases]] = []
    for tag, axis in sorted({**posts, **axes}.items()):
        element = plan.by_tag(tag)
        category = "column" if tag in posts else "beam"
        # A release belongs at a bearing on another MEMBER — a beam set on a post top is
        # free to rotate over it. At a SUPPORT node the support's own rotations say what is
        # free, and releasing there as well is what leaves the member spinning.
        released = {bearing_index[(tag, ref)] for _param, ref in bearings.get(tag, ())
                    if not _is_support(plan, ref)} if category == "beam" else set()
        material, e_pa, e_basis, assumed = _material(
            ctx, element, element.size, moduli.get(tag), scope.items_for(tag))
        _remember(assumptions, assumed)
        stations = _stations(axis, points, extra.get(tag, ()))
        pieces: list[str] = []
        for index in range(len(stations) - 1):
            (_t0, n0), (_t1, n1) = stations[index], stations[index + 1]
            member_id = tag if len(stations) == 2 else f"{tag}#{index + 1}"
            # Only the beam's OWN ends: an interior bearing is continuity, and a release
            # there strands the cantilever past it.
            releases = Releases(
                i_moment=index == 0 and n0 in released,
                j_moment=index == len(stations) - 2 and n1 in released)
            pending.append((member_id, tag, category, n0, n1, axis.section, material,
                            e_pa, e_basis, releases))
            pieces.append(member_id)
        if category == "beam":
            graph.beam_spans[tag] = tuple(pieces)
        else:
            graph.post_carries[tag] = tuple(
                sorted(t for t in axes if tag in (plan.by_tag(t).bearing_refs or ())))

    node_ids = nodes.ids()
    built = [
        Member(id=member_id, tag=tag, category=category, n0=node_ids[i], n1=node_ids[j],
               section=section, material=material, e_pa=e_pa, e_basis=e_basis,
               releases=releases, item_ids=scope.items_for(tag),
               physical_uid=getattr(plan.by_tag(tag), "uid", "") or "")
        for member_id, tag, category, i, j, section, material, e_pa, e_basis, releases
        in pending
        if node_ids[i] != node_ids[j]  # two ends that merged are not a member
    ]
    graph.nodes = nodes.nodes()
    graph.members = tuple(sorted(built, key=lambda member: member.id))
    graph.post_base = {tag: node_ids[int(i)] for tag, i in sorted(graph.post_base.items())}
    graph.post_top = {tag: node_ids[int(i)] for tag, i in sorted(graph.post_top.items())}
    graph.bearing_node = {key: node_ids[index]
                          for key, index in sorted(bearing_index.items())}
    graph.wall_bearing = {key: node_ids[index] for key, index in sorted(bearing_index.items())
                          if _is_support(plan, key[1])}
    _remember(assumptions, _SPLIT_RULE)
    _remember(assumptions, _SUPPORT_ROTATIONS)
    graph.assumptions = tuple(assumptions)
    return graph


def _stations(axis: _Axis, points: list[_Vec3],
              extra: Any = ()) -> list[tuple[float, int]]:
    """``(parameter, node index)`` for every node ON this axis, ends included, in order.

    A node within :data:`NODE_SNAP_M` of the axis is on it — the same distance two points
    merge at, so a node cannot be "nearly" on a member and be treated as elsewhere.
    """
    found: list[tuple[float, int]] = list(extra)
    length = axis.length_m
    for index, point in enumerate(points):
        param = _param_on(axis, point)
        if param is None:
            continue
        if all(index != seen for _param, seen in found):
            found.append((param, index))
    found.sort()
    # Two stations closer together than the snap distance are one station; keeping both
    # would mint a member shorter than the tolerance its own nodes were merged at.
    out: list[tuple[float, int]] = []
    for param, index in found:
        if out and abs(param - out[-1][0]) * length <= NODE_SNAP_M:
            continue
        out.append((param, index))
    return out


def _param_on(axis: _Axis, point: _Vec3) -> float | None:
    """The parameter of ``point`` on ``axis``, or ``None`` where it is not on it."""
    d = (axis.p1[0] - axis.p0[0], axis.p1[1] - axis.p0[1], axis.p1[2] - axis.p0[2])
    denominator = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
    if denominator < 1e-18:
        return None
    raw = sum(d[axis_index] * (point[axis_index] - axis.p0[axis_index])
              for axis_index in range(3)) / denominator
    param = min(max(raw, 0.0), 1.0)
    return param if math.dist(axis.at(param), point) <= NODE_SNAP_M else None


def _is_support(plan: Any, ref: str) -> bool:
    """A wall, a footing or a pad — the walk's terminals, which become support nodes."""
    from typehaus.model.elements import Wall
    from typehaus.model.structure import Footing, Pad

    return isinstance(plan.by_tag(ref), Wall | Footing | Pad)


def _unit_xy(axis: _Axis) -> _Vec2:
    dx, dy = axis.p1[0] - axis.p0[0], axis.p1[1] - axis.p0[1]
    length = math.hypot(dx, dy)
    return (0.0, 0.0) if length < 1e-9 else (dx / length, dy / length)


def _bearings_on(plan: Any, model: Any, axes: dict[str, _Axis],
                 tag: str) -> list[tuple[float, str]]:
    """``(parameter along the axis, support tag)`` for every bearing this beam declares."""
    beam = plan.by_tag(tag)
    found: list[tuple[float, str]] = []
    for ref in sorted(beam.bearing_refs or ()):
        param = _bearing_param(plan, model, axes, tag, ref)
        if param is not None:
            found.append((min(max(param, 0.0), 1.0), ref))
    return sorted(found)


def _bearing_param(plan: Any, model: Any, axes: dict[str, _Axis], tag: str,
                   ref: str) -> float | None:
    """Where along ``tag``'s axis it bears on ``ref``. ``None`` where that cannot be placed."""
    from typehaus.model.elements import Wall
    from typehaus.model.structure import Post

    axis = axes[tag]
    support = plan.by_tag(ref)
    if isinstance(support, Post):
        return axis.param_of(support.position.xy_m)
    if ref in axes:
        other = axes[ref]
        return _closest_param(axis, (other.p0[:2], other.p1[:2]))
    if isinstance(support, Wall):
        line = _wall_line(plan, ref)
        return None if line is None else _closest_param(axis, line)
    return None


def _closest_param(axis: _Axis, other: tuple[_Vec2, _Vec2]) -> float:
    """The parameter on ``axis`` whose plan point is nearest the other plan segment.

    Solved rather than sampled, and that matters: a bearing placed a centimetre off the
    supporting beam's line is a node that misses the axis it is meant to sit on, and the
    interior-split pass then never finds it. Ericson's segment-segment closest point,
    clamped to both segments.
    """
    d1 = (axis.p1[0] - axis.p0[0], axis.p1[1] - axis.p0[1])
    d2 = (other[1][0] - other[0][0], other[1][1] - other[0][1])
    r = (axis.p0[0] - other[0][0], axis.p0[1] - other[0][1])
    a = d1[0] * d1[0] + d1[1] * d1[1]
    e = d2[0] * d2[0] + d2[1] * d2[1]
    if a < 1e-18:
        return 0.0
    c = d1[0] * r[0] + d1[1] * r[1]
    if e < 1e-18:
        return min(max(-c / a, 0.0), 1.0)
    b = d1[0] * d2[0] + d1[1] * d2[1]
    f = d2[0] * r[0] + d2[1] * r[1]
    denominator = a * e - b * b
    s = min(max((b * f - c * e) / denominator, 0.0), 1.0) if abs(denominator) > 1e-15 else 0.0
    t = min(max((b * s + f) / e, 0.0), 1.0)
    return min(max((b * t - c) / a, 0.0), 1.0)


def _point_to_segment(point: _Vec2, a: _Vec2, b: _Vec2) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    if denominator < 1e-12:
        return math.dist(point, a)
    t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denominator))
    return math.dist(point, (a[0] + dx * t, a[1] + dy * t))


def _wall_line(plan: Any, ref: str) -> tuple[_Vec2, _Vec2] | None:
    wall = plan.by_tag(ref)
    nodes = {e.tag: e.position.xy_m for e in plan.all_elements()
             if e.element_kind == "Node"}
    start = nodes.get(getattr(wall, "start_node", None))
    end = nodes.get(getattr(wall, "end_node", None))
    return None if start is None or end is None else (start, end)


def _material(ctx: Any, element: Any, size: str, record_e_psi: float | None,
              items: tuple[str, ...]) -> tuple[str, float, str, str | None]:
    """``(material, E in Pa, the member's e_basis, the assumption to register)``."""
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    fc = fc_psi(concrete_spec_for(ctx.plan, element))
    material = materials.material_name(size, fc)
    e_pa, basis, assumed = materials.modulus_for(
        material, record_e_psi=record_e_psi, record_item=items[0] if items else "",
        concrete_fc_psi=fc)
    return material, e_pa, basis, assumed


def _remember(assumptions: list[str], line: str | None) -> None:
    if line and line not in assumptions:
        assumptions.append(line)


def _midpoint(a: _Vec2, b: _Vec2) -> _Vec2:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _centroid(ring: list[_Vec2]) -> _Vec2:
    if not ring:
        return (0.0, 0.0)
    return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))

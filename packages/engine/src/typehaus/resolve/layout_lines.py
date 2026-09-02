"""Layout lines: one shared origin for everything that subdivides a wall (#43).

Every subdivision of a wall resolves against one ``ResolvedWall``, which is 1:1 with an
authored ``Wall`` — one storey, one pair of nodes. Three mechanisms inherit that limit and
they are the same problem wearing three hats: a ``Layer.extent`` band is measured from the
wall's own base or top, so brick coursing restarts at every storey line; the stud module
starts at the wall's own start node, so two collinear segments split at a tee each restart
it; and a ``WallPaneling`` is scoped to a room, and a room lives on one storey. The only
lever the author had over alignment was *where to split walls*, which is why walls get
chunked to match rooms.

A **layout line** is the missing shared datum. It is a derived chain of walls — collinear
within a storey, stacked across storeys — with one origin and one direction, so a member can
be asked "where do I start along this line" (``u_offset_m``, for the stud module and the
battens that phase-lock to it) and "where does this line start and stop vertically"
(``base_z_m``/``top_z_m``, for ``LayerDatum.LINE_BASE``/``LINE_TOP``).

Named ``LayoutLine`` rather than ``WallLine`` deliberately: *braced wall line* is an IRC term
of art (R602.10.1.4) and it admits up to 4 ft of in-plane offset, where this is strictly
collinear. Conflating the two would bite, and ``WallLine``/``BracedWallLine`` stays free for
a bracing check.

Derived from the **authored** ``Wall`` + ``Node`` model rather than from ``ResolvedWall``,
which breaks a chicken-and-egg: ``topology._band`` needs the line while it is resolving the
wall, twelve stages before ``resolve_stacking`` runs. Node positions, assembly refs,
``Wall.top``, ``Storey.elevation`` and ``default_ceiling_height`` are all readable before
any wall is resolved.

The line is **not** an exported element and it never merges wall solids. Revit's own answer
to this problem — a Stacked Wall holding subwalls — is skipped by the Autodesk IFC exporter,
which writes the subwalls as separate ``IfcWall``s with no ``IfcElementAssembly`` wrapper.
Derived-and-unexported, with per-storey walls as the real elements, is exactly that shape.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.model.plan import PlanModel
from typehaus.quantities import ft, inch

# Datum-face alignment tolerance, and the minimum in-plane overlap that makes two walls on
# different storeys one line. Both are ``stacking.py``'s numbers on purpose, and ``_stacks``
# now applies them to the same *question* ``stacking._axis_match`` asks — collinear within
# ``_TOL``, overlapping by ``_MIN_OVERLAP``, and nothing about vertical adjacency.
#
# What the two passes still do not share is the geometry they feed those numbers: this pass
# measures on the **datum face** (``Storey.vertical_datum``, so a width change stacks),
# ``_axis_match`` measures on the raw **node** axis. On concrete under wood those differ by
# more than ``_TOL`` — 43.8 mm at catlin's basement, 57.0 mm at the garage — so 13 pours-
# under-framed-walls stack in one pass and not the other. Pours frame no studs, so nothing
# reads the difference today; ``plans/TODO.md`` logs the wider "four matchers, three
# tolerances" problem, and warns that unifying them is not a mechanical edit.
_TOL = inch(0.5).meters
_MIN_OVERLAP = ft(2).meters
# Two walls of one storey chain when they share a node and run the same way. The node is
# shared exactly, so this only has to absorb float noise in the datum-face offset.
_JOIN_TOL = inch(0.5).meters

#: A plan point and a plan segment, in metres.
_Point = tuple[float, float]
_Segment = tuple[_Point, _Point]


@dataclass(frozen=True)
class LayoutLineMember:
    """One wall's place on its line."""

    wall_tag: str
    storey: str
    # Signed station, along the line, of this wall's own station 0 — i.e. of the end the
    # framing solver lays out from. A consumer maps wall-local ``s`` to line station with
    # ``u_offset_m + direction_sign * s``.
    u_offset_m: float
    # +1 when the wall runs with the line, -1 when it was authored reversed. A stacked pair
    # authored in opposite directions is common and entirely legitimate — the line is what
    # lets their stud modules still agree.
    direction_sign: int
    z0_m: float
    z1_m: float


@dataclass(frozen=True)
class ResolvedLayoutLine:
    """A chain of collinear, stacked walls sharing one origin in both axes."""

    tag: str
    origin: tuple[float, float]
    direction: tuple[float, float]
    base_z_m: float
    top_z_m: float
    members: tuple[LayoutLineMember, ...]

    def member(self, wall_tag: str) -> LayoutLineMember | None:
        return next((m for m in self.members if m.wall_tag == wall_tag), None)


# --- authored geometry ------------------------------------------------------------------


def _wall_axis(nodes: dict[str, Any], wall: Any) -> _Segment | None:
    n0, n1 = nodes.get(wall.start_node), nodes.get(wall.end_node)
    if n0 is None or n1 is None:
        return None
    return n0.position.xy_m, n1.position.xy_m


def _datum_offset_m(plan: PlanModel, wall: Any, storey: Any) -> float:
    """Signed distance from the node-to-node axis out to the wall's vertical datum face.

    ``Storey.vertical_datum`` (defaulting to ``face("sheathing-ext")``) and its per-wall
    override are #43's answer to "which face do two stacked walls line up on", and nothing
    read them until now. A 2x6 wall over a 2x4 wall lines up on its sheathing, not on its
    centreline, and grouping by centreline would put them on two different lines.

    Falls back to 0.0 — the centreline — whenever the face cannot be resolved, which is the
    honest answer for an assembly with no such face and keeps an unresolvable datum from
    splitting a line that is obviously one line.
    """
    datum = getattr(wall, "vertical_datum", None) or getattr(storey, "vertical_datum", None)
    if datum is None:
        return 0.0
    assembly = plan.library.resolve_assembly(wall.assembly)
    if assembly is None:
        return 0.0
    # Imported lazily: ``topology`` imports nothing from here, and this keeps it that way.
    from typehaus.resolve.topology import (
        _added_thicknesses,
        _axis_offset_from_interior,
        _face_offset_from_interior,
    )

    stack = list(assembly.default_lining) + list(assembly.layers)
    added = _added_thicknesses(stack)
    total = sum(a for (_layer, a, _cavity) in added)
    if total <= 0.0:
        return 0.0
    axis_from_int = _axis_offset_from_interior(stack, added, wall.alignment, total)
    datum_from_int = _face_offset_from_interior(stack, added, datum, total)
    return float(datum_from_int - axis_from_int)


def _datum_axis(plan: PlanModel, wall: Any, storey: Any, nodes: dict[str, Any],
                outward_sign: float) -> _Segment | None:
    """The wall's axis translated onto its datum face."""
    axis = _wall_axis(nodes, wall)
    if axis is None:
        return None
    offset = _datum_offset_m(plan, wall, storey) * outward_sign
    if abs(offset) < 1e-12:
        return axis
    (x0, y0), (x1, y1) = axis
    span = math.hypot(x1 - x0, y1 - y0)
    if span < 1e-9:
        return axis
    nx, ny = -(y1 - y0) / span, (x1 - x0) / span
    return ((x0 + nx * offset, y0 + ny * offset), (x1 + nx * offset, y1 + ny * offset))


def _wall_elevations(plan: PlanModel, wall: Any, storey: Any) -> tuple[float, float]:
    """The wall's authored z range, read the way ``resolve_wall_geometry`` reads it."""
    z0 = storey.elevation.meters
    z1 = z0 + storey.default_ceiling_height.meters
    if wall.element_kind == "FoundationWall":
        bottom = getattr(wall, "bottom_elevation", None)
        top = getattr(wall, "top_elevation", None)
        return (bottom.meters if bottom is not None else z0,
                top.meters if top is not None else z1)
    top = getattr(wall, "top", None)
    if top is not None and hasattr(top, "meters"):
        z1 = z0 + top.meters
    return z0, z1


# --- chaining ---------------------------------------------------------------------------


def _unit(a: _Point, b: _Point) -> tuple[float, float] | None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = math.hypot(dx, dy)
    if span < 1e-9:
        return None
    return dx / span, dy / span


def _collinear(a: _Segment, b: _Segment, tol: float) -> float:
    """Overlap length of ``b`` projected on ``a``'s line, or 0 if they are not collinear.

    ``stacking._axis_match``'s rule, kept deliberately identical: parallel (reversal
    allowed), within ``tol`` of the same line, and overlapping in projection. Identical in
    the arithmetic, that is — the *segments* handed in here are datum-face axes, where
    ``_axis_match`` is handed raw node axes. See the note at ``_TOL``.
    """
    da, db = _unit(*a), _unit(*b)
    if da is None or db is None:
        return 0.0
    if abs(da[0] * db[1] - da[1] * db[0]) > 1e-3:
        return 0.0
    n = (-da[1], da[0])
    if abs((b[0][0] - a[0][0]) * n[0] + (b[0][1] - a[0][1]) * n[1]) > tol:
        return 0.0

    def proj(p: _Point) -> float:
        return float((p[0] - a[0][0]) * da[0] + (p[1] - a[0][1]) * da[1])

    la1 = math.dist(a[0], a[1])
    lb0, lb1 = sorted((proj(b[0]), proj(b[1])))
    return max(0.0, min(la1, lb1) - max(0.0, lb0))


def _shares_a_node(a: Any, b: Any) -> bool:
    return bool({a.start_node, a.end_node} & {b.start_node, b.end_node})


@dataclass
class _Seg:
    """A wall, on its datum face, with everything the chaining needs."""

    wall: Any
    storey_tag: str
    axis: _Segment
    z0_m: float
    z1_m: float


def _horizontal_groups(segs: list[_Seg]) -> list[list[_Seg]]:
    """Chain a storey's segments: collinear *and* sharing a node.

    Sharing a node is what keeps two parallel runs of one wall plane — the north wall of the
    house and the north wall of the garage on the same line — from being welded into one
    layout line with a gap in the middle. Two segments split at a tee do share their node,
    which is the case this exists for.
    """
    parents = list(range(len(segs)))

    def find(i: int) -> int:
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for i, a in enumerate(segs):
        for j in range(i + 1, len(segs)):
            b = segs[j]
            if not _shares_a_node(a.wall, b.wall):
                continue
            if _unit(*a.axis) is None or _unit(*b.axis) is None:
                continue
            if _collinear(a.axis, b.axis, _JOIN_TOL) <= 0.0 and not _touching(a, b):
                continue
            parents[find(i)] = find(j)

    groups: dict[int, list[_Seg]] = {}
    for i, seg in enumerate(segs):
        groups.setdefault(find(i), []).append(seg)
    return list(groups.values())


def _touching(a: _Seg, b: _Seg) -> bool:
    """Collinear but abutting end to end, so the projected overlap is exactly zero.

    Two segments split at a tee are the whole point of horizontal chaining and they overlap
    by nothing at all, so the overlap test above cannot be the only one.
    """
    da, db = _unit(*a.axis), _unit(*b.axis)
    if da is None or db is None:
        return False
    if abs(da[0] * db[1] - da[1] * db[0]) > 1e-3:
        return False
    n = (-da[1], da[0])
    for point in b.axis:
        if abs((point[0] - a.axis[0][0]) * n[0]
               + (point[1] - a.axis[0][1]) * n[1]) > _JOIN_TOL:
            return False
    return min(math.dist(p, q) for p in a.axis for q in b.axis) <= _JOIN_TOL


def _vertical_merge(groups: list[list[_Seg]], _plan: PlanModel) -> list[list[_Seg]]:
    """Weld horizontal chains that stack on each other into one line.

    Unlike ``stacking.resolve_stacking``, this does **not** collapse to one candidate per
    lower wall. #43 asks for edges per overlapping span, and a long wall carrying two above
    it is exactly the case a single-chain model gets wrong — so an ambiguous stack simply
    puts all of them on the same line, which is what a shared datum means, and leaves the
    ambiguity for ``integrity.stack_ambiguous`` to report.
    """
    parents = list(range(len(groups)))

    def find(i: int) -> int:
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for i, lower in enumerate(groups):
        for j in range(i + 1, len(groups)):
            upper = groups[j]
            if {s.storey_tag for s in lower} == {s.storey_tag for s in upper}:
                continue
            if _stacks(lower, upper):
                parents[find(i)] = find(j)

    merged: dict[int, list[_Seg]] = {}
    for i, group in enumerate(groups):
        merged.setdefault(find(i), []).extend(group)
    return list(merged.values())


def _stacks(lower: list[_Seg], upper: list[_Seg]) -> bool:
    """Collinear and overlapping, or authored as a stack. Deliberately *not* vertical
    adjacency: platform framing always leaves a floor between a wall's top plate and the
    base of the wall above, so a z-extent-touching gate never fires on a real house — only
    an explicit ``Wall.stacks_on`` would catch the merge.

    Asking ``stacking._axis_match``'s question and no other is what lets this find every
    real stack. A setback wall is still a line of its own — that is ``_MIN_OVERLAP``'s job,
    and it is unchanged.
    """
    for a in lower:
        for b in upper:
            if _collinear(a.axis, b.axis, _TOL) >= _MIN_OVERLAP:
                return True
            if getattr(b.wall, "stacks_on", None) == a.wall.tag:
                return True
    return False


# --- the line itself --------------------------------------------------------------------


def _orient(segs: list[_Seg]) -> tuple[_Point, tuple[float, float]]:
    """Origin and direction for a group, chosen so ``model.walls`` order cannot change it.

    The direction is the group's own axis, pointed the lexicographically smaller way, and the
    origin is the extreme member end against it. Any stable rule would do; what matters is
    that it is a rule and not an accident of iteration order.
    """
    axis = min((s.axis for s in segs), key=lambda a: (min(a), max(a)))
    direction = _unit(*axis) or (1.0, 0.0)
    if (direction[0], direction[1]) < (-direction[0], -direction[1]):
        direction = (-direction[0], -direction[1])
    points = [p for s in segs for p in s.axis]
    origin = min(points, key=lambda p: p[0] * direction[0] + p[1] * direction[1])
    return origin, direction


def _line_tag(segs: list[_Seg]) -> str:
    """Deterministic, and derived from the members rather than from a counter.

    A counter would renumber every line downstream of an inserted wall, and these tags reach
    ``model.json`` and ``haus explain``.
    """
    return "LL-" + min(str(s.wall.tag) for s in segs)


def resolve_layout_lines(plan: PlanModel) -> list[ResolvedLayoutLine]:
    """Derive every layout line in the plan, from authored walls and nodes only."""
    from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign

    per_storey: list[list[_Seg]] = []
    for storey in plan.storeys:
        nodes = {e.tag: e for e in plan.storey_elements(storey.tag)
                 if e.element_kind == "Node"}
        windings = resolve_storey_windings(plan, storey.tag)
        segs: list[_Seg] = []
        for element in plan.storey_elements(storey.tag):
            if element.element_kind not in ("Wall", "FoundationWall"):
                continue
            sign = wall_outward_sign(plan, element, storey.tag,
                                     windings.sign_for_wall(element))
            axis = _datum_axis(plan, element, storey, nodes, sign)
            if axis is None or _unit(*axis) is None:
                continue
            z0, z1 = _wall_elevations(plan, element, storey)
            segs.append(_Seg(element, storey.tag, axis, z0, z1))
        per_storey.extend(_horizontal_groups(segs))

    lines: list[ResolvedLayoutLine] = []
    for group in _vertical_merge(per_storey, plan):
        origin, direction = _orient(group)

        def station(point: _Point, origin: _Point = origin,
                    direction: tuple[float, float] = direction) -> float:
            return float((point[0] - origin[0]) * direction[0]
                         + (point[1] - origin[1]) * direction[1])

        members = []
        for seg in group:
            own = _unit(*seg.axis)
            sign = 1 if own is not None and (own[0] * direction[0]
                                             + own[1] * direction[1]) >= 0.0 else -1
            members.append(LayoutLineMember(
                wall_tag=seg.wall.tag, storey=seg.storey_tag,
                u_offset_m=station(seg.axis[0]), direction_sign=sign,
                z0_m=seg.z0_m, z1_m=seg.z1_m,
            ))
        members.sort(key=lambda m: (m.z0_m, m.u_offset_m, m.wall_tag))
        lines.append(ResolvedLayoutLine(
            tag=_line_tag(group), origin=origin, direction=direction,
            base_z_m=min(m.z0_m for m in members),
            top_z_m=max(m.z1_m for m in members),
            members=tuple(members),
        ))
    lines.sort(key=lambda line: line.tag)
    return lines


def lines_by_wall(lines: list[ResolvedLayoutLine]) -> dict[str, ResolvedLayoutLine]:
    """Wall tag -> its line, for the consumers that ask per wall."""
    return {member.wall_tag: line for line in lines for member in line.members}


def layout_phase(spec: Any, line: ResolvedLayoutLine | None, wall_tag: str,
                 spacing: float) -> float:
    """Wall-local station of the line's first module station, in ``[0, spacing)``.

    A wall-local station ``s`` is line station ``u_offset + direction_sign * s``, and the
    module sits at whole multiples of ``spacing`` from the line's origin. Solving
    ``u_offset + sign * s ≡ 0 (mod spacing)`` for ``s`` — and using ``sign² == 1`` — gives
    ``s ≡ -sign * u_offset``, so every module station on the wall is ``phase + k * spacing``
    and the whole line lays out as one grid. A wall authored *reversed* relative to the line
    is exactly the case ``direction_sign`` carries, and it drops out of the same arithmetic.

    Returns 0.0 — today's behaviour, byte for byte — for ``layout_origin="wall-start"``,
    for a wall on no line, and for a nonsensical spacing.
    """
    if getattr(spec, "layout_origin", "wall-start") != "line" or spacing <= 0.0:
        return 0.0
    if line is None:
        return 0.0
    member = line.member(wall_tag)
    if member is None:
        return 0.0
    return (-member.direction_sign * member.u_offset_m) % spacing

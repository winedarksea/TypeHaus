"""Room macros + wall-draw — geometry-aware builders that emit :class:`MutationResult`s
(→ 21b §Room macros, §Mutation contract).

These are *server-side* helpers, not new grammar: each returns ordinary ``add|update|delete``
PatchOps that ride the standard :class:`~typehaus.source.coordinator.ProjectCoordinator`
patch/undo path, so undo/redo and revision-hash write safety come for free. Geometry math
lives here (the "server owns all geometry" rule, → 21b) — the client only sends screen intent
(draw endpoints, the wall to split, the drag delta). Node positions are read from the authored
:class:`~typehaus.model.plan.PlanModel`; new coordinates are emitted as :class:`RawExpr`
``pt(...)`` so no re-encoding round-trip can lose precision.
"""

from __future__ import annotations

import math
from typing import Union

from typehaus.model.elements import Door, Node, RoughOpening, Wall, Window
from typehaus.model.enums import Occupancy
from typehaus.model.plan import PlanModel
from typehaus.model.refs import from_node
from typehaus.model.remap import MutationResult, ReferenceRemap, remap_ops_for
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Appliance, Fixture, Furniture, Room, Stair
from typehaus.model.mep import ElectricalDevice, Equipment, Register
from typehaus.model.placeables import Mount
from typehaus.model.enums import DeviceKind, DuctSystem, EquipmentKind, Service
from typehaus.resolve.mep import _PIPE_SLEEVE_SNAP_M
from typehaus.quantities import Length, deg
from typehaus.quantities.length import ft, m
from typehaus.quantities.point import pt
from typehaus.source.ops import DELETE_FIELD, PatchOp, RawExpr
from typehaus.source.serialize import element_add_op

# Node coincidence tolerance — nodes closer than this fuse (T-junction heal), in meters.
SNAP_M = 0.02
# Product rotations default to the same 15° increment in every canvas adapter. The explicit
# macro flag keeps free rotation intentional rather than an accidental floating-point drift.
ROTATION_SNAP_DEGREES = 15.0
# Collinearity tolerance for heal/merge (cross-product of unit axes), dimensionless.
COLLINEAR_TOL = 1e-3
# Room faces resolve at finish surfaces while authored nodes lie on wall axes.  This is the
# maximum practical finish/half-wall offset for identifying a room's boundary graph.
ROOM_BOUNDARY_NODE_TOLERANCE_M = 0.35

XY = tuple[Union[float, str], Union[float, str]]


class MacroError(ValueError):
    """A macro could not be built (degenerate geometry, missing element, ambiguous heal)."""


# --- coordinate helpers ------------------------------------------------------

def _as_length(v: float | str) -> Length:
    return Length.parse(v) if isinstance(v, str) else m(float(v))


def _point_expr(x: float | str, y: float | str) -> RawExpr:
    return RawExpr(f"pt({_as_length(x).to_source()}, {_as_length(y).to_source()})")


def _meters(v: float | str) -> float:
    return _as_length(v).meters


def _nodes(plan: PlanModel, storey: str) -> list[Node]:
    return [e for e in plan.storey_elements(storey) if isinstance(e, Node)]


def _walls(plan: PlanModel, storey: str) -> list[Wall]:
    return [e for e in plan.storey_elements(storey) if isinstance(e, Wall)]


def _next_tag(existing: list, prefix: str) -> str:
    used = set()
    for el in existing:
        t = el.tag
        if t.startswith(prefix) and t[len(prefix):].isdigit():
            used.add(int(t[len(prefix):]))
    n = 1
    while n in used:
        n += 1
    return f"{prefix}{n}"


def _copy_tag(plan: PlanModel, source_tag: str) -> str:
    """Return a readable unused duplicate tag without changing the original identity."""
    used = {item.tag for storey in plan.storeys for item in plan.storey_elements(storey.tag)}
    candidate = f"{source_tag}-COPY"
    index = 2
    while candidate in used:
        candidate = f"{source_tag}-COPY-{index}"
        index += 1
    return candidate


def _find_node_near(plan: PlanModel, storey: str, xy_m: tuple[float, float]) -> Node | None:
    for nd in _nodes(plan, storey):
        px, py = nd.position.xy_m
        if (px - xy_m[0]) ** 2 + (py - xy_m[1]) ** 2 <= SNAP_M ** 2:
            return nd
    return None


# --- wall-draw ---------------------------------------------------------------

def draw_wall(
    plan: PlanModel,
    storey: str,
    start: XY,
    end: XY,
    assembly: str,
    *,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Draw one wall between two points — the fundamental UI add flow (→ 21b).

    Endpoints snap to existing nodes within ``SNAP_M`` (automatic T-junction heal); otherwise
    a fresh ``Node`` is added. Emits at most two node adds + one wall add, all in one patch so
    undo removes the whole stroke atomically.
    """
    sx, sy = _meters(start[0]), _meters(start[1])
    ex, ey = _meters(end[0]), _meters(end[1])
    if (sx - ex) ** 2 + (sy - ey) ** 2 < SNAP_M ** 2:
        raise MacroError("degenerate wall: endpoints coincide")

    ops: list[PatchOp] = []
    node_list = "NODES" if any(_nodes(plan, storey)) else None
    minted_tags: list[str] = []

    def node_at(pt: XY, at_m: tuple[float, float]) -> str:
        existing = _find_node_near(plan, storey, at_m)
        if existing is not None:
            return existing.tag
        pending = _pending_nodes(plan, storey, minted_tags)
        new_tag = _next_tag(pending, "N-")
        minted_tags.append(new_tag)
        ops.append(PatchOp("add", "Node", new_tag,
                           {"position": _point_expr(pt[0], pt[1])},
                           hint_file=hint_file, hint_list=node_list))
        return new_tag

    a = node_at(start, (sx, sy))
    b = node_at(end, (ex, ey))
    wall_tag = tag or _next_tag(_walls(plan, storey), "W-")
    ops.append(PatchOp("add", "Wall", wall_tag,
                       {"start_node": a, "end_node": b, "assembly": assembly},
                       hint_file=hint_file, hint_list=_wall_list(plan, storey)))
    return MutationResult(ops=ops)


def _pending_nodes(plan: PlanModel, storey: str, minted: list[str]) -> list:
    class _T:
        def __init__(self, tag: str) -> None:
            self.tag = tag

    return [*_nodes(plan, storey), *(_T(t) for t in minted)]


def _wall_list(plan: PlanModel, storey: str) -> str | None:
    return "WALLS" if any(_walls(plan, storey)) else None


# --- opening / room placement ------------------------------------------------

def _openings(plan: PlanModel, storey: str) -> list:
    kinds = {"Window", "Door", "RoughOpening"}
    return [e for e in plan.storey_elements(storey) if e.element_kind in kinds]


def _rooms(plan: PlanModel, storey: str) -> list:
    return [e for e in plan.storey_elements(storey) if e.element_kind == "Room"]


def place_opening(
    plan: PlanModel,
    storey: str,
    *,
    host: str,
    type_ref: str,
    along: float | str,
    is_door: bool,
    sill: float | str | None = None,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Add a window or door to a wall at ``along`` metres from the wall's start node (→ 21b).

    Position is authored as ``from_node(start, offset)`` so the opening tracks the wall's
    a-node under later stretches. The whole ``Window``/``Door`` declaration is serialized to
    source and added to the storey's ``OPENINGS`` list on ``hint_file`` (the host wall's file,
    passed by the client from its provenance so the op lands on the right storey).
    """
    wall = next((w for w in _walls(plan, storey) if w.tag == host), None)
    if wall is None:
        raise MacroError(f"no wall {host!r} on storey {storey!r}")
    offset = _as_length(along)
    position = from_node(wall.start_node, offset)
    if is_door:
        new_tag = tag or _next_tag(_openings(plan, storey), "D-")
        element: object = Door(
            tag=new_tag, host=host, type_ref=type_ref, position=position,
            sill_height=_as_length(sill) if sill is not None else None,
        )
    else:
        new_tag = tag or _next_tag(_openings(plan, storey), "WIN-")
        element = Window(
            tag=new_tag, host=host, type_ref=type_ref, position=position,
            sill_height=_as_length(sill) if sill is not None else ft(3),
        )
    _validate_opening_station(plan, storey, element, wall, offset)
    op = element_add_op(element, tag=new_tag, hint_list="OPENINGS", hint_file=hint_file)
    # OpeningPosition is authored through its `from_node(...)` helper, not the bare model
    # constructor (which the plan dialect deliberately doesn't allow, → 10 §dialect).
    op.fields["position"] = RawExpr(
        f'from_node("{wall.start_node}", {offset.to_source()})'
    )
    return MutationResult(ops=[op])


def place_rough_opening(plan: PlanModel, storey: str, *, host: str, width: float | str,
                        height: float | str, along: float | str, sill: float | str | None = None,
                        hint_file: str | None = None, tag: str | None = None) -> MutationResult:
    """Place a bare framed opening with the same host and conflict checks as products."""
    wall = next((item for item in _walls(plan, storey) if item.tag == host), None)
    if wall is None:
        raise MacroError(f"no wall {host!r} on storey {storey!r}")
    offset, opening_width, opening_height = _as_length(along), _as_length(width), _as_length(height)
    new_tag = tag or _next_tag(_openings(plan, storey), "RO-")
    element = RoughOpening(tag=new_tag, host=host, position=from_node(wall.start_node, offset),
                           width=opening_width, height=opening_height,
                           sill_height=_as_length(sill) if sill is not None else m(0))
    _validate_opening_station(plan, storey, element, wall, offset)
    op = element_add_op(element, tag=new_tag, hint_list="OPENINGS", hint_file=hint_file)
    op.fields["position"] = RawExpr(f'from_node("{wall.start_node}", {offset.to_source()})')
    return MutationResult(ops=[op])


def move_opening(
    plan: PlanModel,
    storey: str,
    *,
    tag: str,
    along: float | str,
) -> MutationResult:
    """Move an opening along its existing host wall without inventing a second geometry solver.

    ``OpeningPosition`` is an authored structured value, so a normal scalar patch cannot
    safely express it.  Re-emitting ``from_node`` keeps the opening attached to the wall's
    start node as that wall is stretched later.
    """
    opening = next((item for item in _openings(plan, storey) if item.tag == tag), None)
    if opening is None:
        raise MacroError(f"no opening {tag!r} on storey {storey!r}")
    wall = next((item for item in _walls(plan, storey) if item.tag == opening.host), None)
    if wall is None:
        raise MacroError(f"opening {tag!r} hosts on missing wall {opening.host!r}")
    offset = _as_length(along)
    _validate_opening_station(plan, storey, opening, wall, offset, ignore_tag=opening.tag)
    return MutationResult(ops=[PatchOp(
        "update", opening.element_kind, tag,
        {"position": RawExpr(f'from_node("{wall.start_node}", {offset.to_source()})')},
    )])


def rehost_opening(plan: PlanModel, storey: str, *, tag: str, host: str,
                   along: float | str) -> MutationResult:
    """Atomically move an opening onto another compatible wall while retaining its UID."""
    opening = next((item for item in _openings(plan, storey) if item.tag == tag), None)
    if opening is None:
        raise MacroError(f"no opening {tag!r} on storey {storey!r}")
    target = next((item for item in _walls(plan, storey) if item.tag == host), None)
    if target is None:
        raise MacroError(f"no wall {host!r} on storey {storey!r}")
    offset = _as_length(along)
    _validate_opening_station(plan, storey, opening, target, offset, ignore_tag=opening.tag)
    return MutationResult(ops=[PatchOp("update", opening.element_kind, tag, {
        "host": host,
        "position": RawExpr(f'from_node("{target.start_node}", {offset.to_source()})'),
    })])


def _opening_width(plan: PlanModel, opening: object) -> float:
    if isinstance(opening, Door):
        item = next((candidate for candidate in plan.library.door_types if candidate.tag == opening.type_ref), None)
    elif isinstance(opening, Window):
        item = next((candidate for candidate in plan.library.window_types if candidate.tag == opening.type_ref), None)
    else:
        return float(getattr(opening, "width").meters)
    if item is None:
        raise MacroError(f"opening {opening.tag!r} references missing type")
    return item.width.meters


def _validate_opening_station(plan: PlanModel, storey: str, opening: object, wall: object,
                              offset: object, ignore_tag: str | None = None) -> None:
    """Reject out-of-bounds or overlapping host stations before an opening patch exists."""
    start = next((item for item in _nodes(plan, storey) if item.tag == wall.start_node), None)
    end = next((item for item in _nodes(plan, storey) if item.tag == wall.end_node), None)
    if start is None or end is None:
        raise MacroError(f"wall {wall.tag!r} has unresolved endpoints")
    length_m = ((start.position.x.meters - end.position.x.meters) ** 2 +
                (start.position.y.meters - end.position.y.meters) ** 2) ** 0.5
    if offset.meters < 0 or offset.meters + _opening_width(plan, opening) > length_m + 1e-9:
        raise MacroError(f"opening {opening.tag!r} does not fit on wall {wall.tag!r}")
    candidate_end = offset.meters + _opening_width(plan, opening)
    for peer in _openings(plan, storey):
        if peer.tag == ignore_tag or peer.host != wall.tag:
            continue
        peer_width = _opening_width(plan, peer)
        peer_start = _opening_start_offset(peer, wall, length_m, peer_width)
        if offset.meters < peer_start + peer_width - 1e-9 and candidate_end > peer_start + 1e-9:
            raise MacroError(f"opening {opening.tag!r} conflicts with {peer.tag!r} on wall {wall.tag!r}")


def _opening_start_offset(opening: object, wall: object, wall_length_m: float, width_m: float) -> float:
    position = opening.position
    if position.mode == "centered":
        return (wall_length_m - width_m) / 2
    offset = position.offset.meters if position.offset is not None else 0.0
    return wall_length_m - offset - width_m if position.node == wall.end_node else offset


def place_room(
    plan: PlanModel,
    storey: str,
    *,
    seed: XY,
    occupancy: str,
    floor_finish: str | None = None,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Claim a room by dropping a seed point in an enclosed area (→ 11 §Room, → 21b).

    The clear-face polygon is derived server-side from the wall graph on the next resolve;
    the macro only authors the seed + occupancy. Added to the storey's ``ROOMS`` list.
    """
    try:
        occ = Occupancy(occupancy)
    except ValueError as exc:
        raise MacroError(f"unknown occupancy {occupancy!r}") from exc
    new_tag = tag or _next_tag(_rooms(plan, storey), "RM-")
    room = Room(
        tag=new_tag, seed=pt(_as_length(seed[0]), _as_length(seed[1])), occupancy=occ,
        floor_finish=floor_finish or None,
    )
    op = element_add_op(room, tag=new_tag, hint_list="ROOMS", hint_file=hint_file)
    return MutationResult(ops=[op])


def _stairs(plan: PlanModel, storey: str) -> list:
    return [e for e in plan.storey_elements(storey) if e.element_kind == "Stair"]


def _floor_openings(plan: PlanModel, storey: str) -> list:
    return [e for e in plan.storey_elements(storey) if e.element_kind == "FloorOpening"]


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Even-odd ray cast; polygon is a list of (x_m, y_m) in the plan frame."""
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            x_cross = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < x_cross:
                inside = not inside
    return inside


def _destination_deck(plan: PlanModel, storey: str, seed: tuple[float, float]):
    """The Slab/FloorSystem of ``storey`` whose outline encloses ``seed`` (the stair's deck)."""
    decks = [e for e in plan.storey_elements(storey) if isinstance(e, (Slab, FloorSystem))]
    for deck in decks:
        outline = getattr(deck, "outline", None)
        if outline and _point_in_polygon(seed, [p.xy_m for p in outline]):
            return deck
    # A FloorSystem carries no outline to test; if the storey has a single deck, use it.
    return decks[0] if len(decks) == 1 else None


def _storey_above(plan: PlanModel, storey: str) -> str | None:
    """Tag of the next storey up by elevation, or None if this is the top storey."""
    here = plan.storey(storey)
    if here is None:
        return None
    above = [s for s in plan.storeys if s.elevation.meters > here.elevation.meters + 1e-6]
    if not above:
        return None
    return min(above, key=lambda s: s.elevation.meters).tag


# Default footprint of a freshly-placed straight stair. The run length is sized from the
# storey rise so the seeded default already clears IRC R311.7 (≥10" tread, ≤7.75" riser)
# rather than tripping a geometry error the moment it lands.
_STAIR_DEFAULT_WIDTH = ft(3)
_STAIR_MAX_RISER = ft(0, 7.5)  # 7.5" — below the 7.75" code max, with margin
_STAIR_TREAD = ft(0, 11)  # 11" — above the 10" code min, with margin


def place_stair(
    plan: PlanModel,
    storey: str,
    *,
    seed: XY,
    to_storey: str | None = None,
    hint_file: str | None = None,
    tag: str | None = None,
) -> MutationResult:
    """Drop a default straight stair from ``storey`` up to the storey above (→ 11 §Stair).

    Authors a companion :class:`FloorOpening` in the upper storey's deck (a Stair references
    one by tag and the resolver derives rise/geometry from the storey elevations), then the
    :class:`Stair` itself. Both land in the upper storey's list so the model matches how
    authored stairs are wired. The resolver owns the run geometry; this only seeds a default
    the user refines in the stair designer.
    """
    up = to_storey or _storey_above(plan, storey)
    if up is None:
        raise MacroError(f"no storey above {storey!r} to land a stair")

    sx, sy = _as_length(seed[0]), _as_length(seed[1])
    width = _STAIR_DEFAULT_WIDTH
    # Size the run from the storey rise: risers to climb it (≤ max riser), one fewer tread.
    here_st, up_st = plan.storey(storey), plan.storey(up)
    rise_m = abs(up_st.elevation.meters - here_st.elevation.meters) if here_st and up_st else 2.75
    risers = max(2, math.ceil(rise_m / _STAIR_MAX_RISER.meters))
    run = m((risers - 1) * _STAIR_TREAD.meters)
    # Rectangle along +x (run) by width in +y; matches the default run_direction="x".
    x0, y0 = sx.meters, sy.meters
    x1, y1 = x0 + run.meters, y0 + width.meters
    outline = (pt(m(x0), m(y0)), pt(m(x1), m(y0)), pt(m(x1), m(y1)), pt(m(x0), m(y1)))

    fo_tag = _next_tag(_floor_openings(plan, up), "FO-")
    stair_tag = tag or _next_tag(_stairs(plan, up), "ST-")
    floor_opening = FloorOpening(tag=fo_tag, outline=outline)
    stair = Stair(
        tag=stair_tag, floor_opening=fo_tag, from_storey=storey, to_storey=up,
        width=width, layout="straight", run_direction="x", start=pt(sx, sy),
    )
    ops = [
        element_add_op(floor_opening, tag=fo_tag, hint_list="FLOOR_OPENINGS", hint_file=hint_file),
        element_add_op(stair, tag=stair_tag, hint_list="STAIRS", hint_file=hint_file),
    ]
    # A stair's FloorOpening must be owned by the destination deck (integrity.stair_opening).
    deck = _destination_deck(plan, up, (x0, y0))
    if deck is not None:
        openings = (*deck.openings, fo_tag)
        expr = "(" + ", ".join(f'"{tag}"' for tag in openings) + ",)"
        ops.append(PatchOp("update", deck.element_kind, deck.tag, {"openings": RawExpr(expr)}))
    return MutationResult(ops=ops)


# --- shared placeable editing ------------------------------------------------

_PLACEABLE_KINDS = (Furniture, Fixture, Appliance, Equipment, Register, ElectricalDevice)


def _placeable(plan: PlanModel, storey: str, tag: str):
    return next((item for item in plan.storey_elements(storey)
                 if isinstance(item, _PLACEABLE_KINDS) and item.tag == tag), None)


def move_placeable(plan: PlanModel, storey: str, *, tag: str, position: XY) -> MutationResult:
    """Move a free object, persisting the room containing its new footprint center.

    A drained fixture is not a free object: its waste leaves through a cast-in-place
    :class:`SleevePenetration` and drops into a routed :class:`PipeRun`, and neither of
    those is derived from the fixture — both are authored plan geometry that a drag would
    otherwise leave behind (`_drain_follower_ops`).
    """
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    x, y = _meters(position[0]), _meters(position[1])
    ops = [PatchOp("update", item.element_kind, tag, {
        "position": _point_expr(position[0], position[1]), "location": DELETE_FIELD,
        "room": _containing_room(plan, storey, (x, y)),
    })]
    followers, warnings = _drain_follower_ops(plan, storey, item, (x, y))
    ops.extend(followers)
    return MutationResult(ops=ops, warnings=warnings)


# --- coupled drain followers -------------------------------------------------
#
# Dragging a floor-drained fixture moves a closet flange, and a closet flange is the top of
# a pipe that is already through the concrete: a pre-pour SleevePenetration at that point
# and a PipeRun dropping through it.  Neither is resolver-derived — both are authored plan
# geometry with their own coordinates — so a bare `position` patch silently decouples them.
# That is the 76c1871 defect: FX-M-BATH2-WC was nudged 6.46" in a drive-by edit, SP-M-WC2
# and PR-B-WC2-DRAIN stayed put, the plan still loaded and built, and only
# `mep.sleeve_alignment` (and one plumbing test) ever said so.  So the move carries them.
#
# A fixture with an authored ``drain_position`` is excluded on purpose: that field *is* the
# author saying where the waste leaves, independently of where the bowl sits, so moving the
# bowl is not a statement about the drain at all (it is how FX-M-BATH1-WC's wall-hung
# carrier stays put while its bowl slides along W-M-BAE).
#
# Followers are searched across the WHOLE plan, not the moved item's storey: the drain of a
# main-floor WC is hung from the basement ceiling, one storey down from the thing that moved.


def _placeable_type(plan: PlanModel, item: object) -> object | None:
    """The fixture/appliance catalog entry behind ``item``, for its service list."""
    return next((entry for entry in (*plan.library.fixture_types, *plan.library.appliance_types)
                 if entry.tag == getattr(item, "type_ref", None)), None)


def _convention_drain_point(plan: PlanModel, storey: str, item: object,
                            at_m: tuple[float, float]) -> tuple[float, float] | None:
    """Where ``item``'s waste would leave the floor if the unit stood at ``at_m``.

    The plan-side mirror of ``resolve/mep.py::_expected_drain_point``'s convention branch,
    and it reads the same signal for the same reason: a water closet is the only common
    fixture with no hot-water connection, which makes "no WATER_HOT" the one reliable mark
    of a floor-drained unit (drain under its own footprint) as against a wall-drained one
    (trap arm back to the wet wall it names, so the drain rides that wall's axis).

    It is stated twice rather than imported because the resolver can only answer for the
    position a fixture *has*; a move macro has to answer for the position it is about to
    have, which no resolved model holds.  The authored-``drain_position`` branch is the
    caller's (a fixture that has one never gets here).
    """
    fixture_type = _placeable_type(plan, item)
    if fixture_type is None:
        return None
    if Service.WATER_HOT not in fixture_type.needs:
        return at_m
    wall_ref = getattr(item, "wall_ref", None)
    if wall_ref is None:
        return None
    wall = next((candidate for candidate in _walls(plan, storey)
                 if candidate.tag == wall_ref), None)
    if wall is None:
        return None
    by_tag = {node.tag: node for node in _nodes(plan, storey)}
    start, end = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    if start is None or end is None:
        return None
    p0, p1 = start.position.xy_m, end.position.xy_m
    t = _project_param(p0, p1, at_m)
    return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))


def _drain_follower_ops(plan: PlanModel, storey: str, item: object,
                        new_xy: tuple[float, float]) -> tuple[list[PatchOp], tuple[str, ...]]:
    """Patches that keep a moved fixture's sleeve and drain run under its flange.

    Followers are claimed by proximity to the fixture's OLD drain point, within the same
    ``_PIPE_SLEEVE_SNAP_M`` the resolver uses to decide a routed vertex belongs to a sleeve
    — so the two agree on what "at the flange" means, and a collector that merely *serves*
    the fixture from twenty feet away (PR-B-MAIN-DRAIN serves seventeen of them) is not
    dragged along with it.  Everything found is reported either way: what followed, because
    a cast-in sleeve moving is a fact the author must see, and what did not, because a
    served run left behind is exactly the tie-in that now needs re-cutting by hand.
    """
    if not isinstance(item, (Fixture, Appliance)) or item.drain_position is not None:
        return [], ()
    sleeves = [element for element in plan.elements_of_kind("SleevePenetration")
               if element.serves_fixture == item.tag]
    runs = [element for element in plan.elements_of_kind("PipeRun")
            if item.tag in element.serves]
    if not sleeves and not runs:
        return [], ()

    old_xy = _convention_drain_point(plan, storey, item, item.position.xy_m)
    target_xy = _convention_drain_point(plan, storey, item, new_xy)
    if old_xy is None or target_xy is None:
        # No convention applies (unknown type, or a wall-drained unit naming no wall), so
        # there is no defensible delta.  Say so rather than guess: the drain is now stale.
        return [], (f"{item.tag} moved but its drain point cannot be derived — "
                    f"{', '.join(sorted(element.tag for element in (*sleeves, *runs)))} "
                    "left in place; re-point by hand",)
    dx, dy = target_xy[0] - old_xy[0], target_xy[1] - old_xy[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return [], ()  # a wall-drained unit slid off its wall: the drain point is unchanged

    ops: list[PatchOp] = []
    warnings: list[str] = []
    for sleeve in sleeves:
        gap = _dist(sleeve.position.xy_m, old_xy)
        if gap > _PIPE_SLEEVE_SNAP_M:
            warnings.append(
                f"sleeve {sleeve.tag} serves {item.tag} but sat {m(gap).fmt()} from its old "
                "drain point — left where it was; re-point it by hand")
            continue
        sx, sy = sleeve.position.xy_m
        ops.append(PatchOp("update", "SleevePenetration", sleeve.tag,
                           {"position": _point_expr_m(sx + dx, sy + dy)}))
        warnings.append(
            f"sleeve {sleeve.tag} moved {m(_dist((0, 0), (dx, dy))).fmt()} with {item.tag} — "
            "it is cast in place, so confirm the pour has not happened")
    stayed: list[str] = []
    for run in runs:
        # EVERY vertex at the old point moves, not just the first: a vertical drop is
        # authored as the same plan point repeated with two inverts (path[0] == path[1] on
        # every riser here), so rewriting one of the pair would fold the riser into a slope.
        moved = {index for index, vertex in enumerate(run.path)
                 if _dist(vertex.xy_m, old_xy) <= _PIPE_SLEEVE_SNAP_M}
        if not moved:
            # Normal and expected for most of them — a WC's supply, its vent and the house
            # collector all serve it without ever touching the flange — so these are one
            # line, not one toast each, and they name a distance so a near miss stands out.
            nearest = min((_dist(vertex.xy_m, old_xy) for vertex in run.path), default=None)
            stayed.append(run.tag + (f" ({m(nearest).fmt()} away)" if nearest is not None else ""))
            continue
        vertices: list[str] = []
        for index, vertex in enumerate(run.path):
            if index in moved:
                vx, vy = vertex.xy_m
                vertices.append(_point_expr_m(vx + dx, vy + dy).expr)
            else:
                # Untouched vertices are re-emitted in their authored units, not round-tripped
                # through meters, so a path rewrite never smears the rest of the route.
                vertices.append(f"pt({vertex.x.to_source()}, {vertex.y.to_source()})")
        ops.append(PatchOp("update", "PipeRun", run.tag,
                           {"path": RawExpr("(" + ", ".join(vertices) + ",)")}))
        warnings.append(
            f"run {run.tag} followed {item.tag} ({len(moved)} of {len(run.path)} vertices "
            "re-pointed); its inverts and slope were not re-solved")
    if stayed:
        warnings.append(
            f"{len(stayed)} run(s) serving {item.tag} had no vertex at its old drain point "
            f"and were left as routed — check the tie-ins: {', '.join(stayed)}")
    return ops, tuple(warnings)


def rotate_placeable(plan: PlanModel, storey: str, *, tag: str, degrees: float,
                     free_rotation: bool = False) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    resolved_degrees = float(degrees) if free_rotation else round(float(degrees) / ROTATION_SNAP_DEGREES) * ROTATION_SNAP_DEGREES
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"rotation": RawExpr(deg(resolved_degrees).to_source())})])


def attach_placeable(plan: PlanModel, storey: str, *, tag: str, wall: str, face: str,
                     distance: float | str, gap: float | str = 0,
                     rotation_offset: float = 0) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    if face not in {"left", "right"}:
        raise MacroError("attachment face must be 'left' or 'right'")
    if not any(candidate.tag == wall for candidate in _walls(plan, storey)):
        raise MacroError(f"no wall {wall!r} on storey {storey!r}")
    d, normal_gap = _as_length(distance), _as_length(gap)
    location = (f'Location(attachment=WallAttachment(wall_ref="{wall}", face="{face}", '
                f'distance_from_start={d.to_source()}, normal_gap={normal_gap.to_source()}, '
                f'rotation_offset={deg(rotation_offset).to_source()}))')
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"location": RawExpr(location)})])


def set_placeable_mount(plan: PlanModel, storey: str, *, tag: str,
                        elevation: float | str) -> MutationResult:
    """Raise or lower a mounted object, rewriting only the mount's elevation.

    The other three mount fields are authored intent that a height edit must not silently
    discard: ``kind`` says what surface the object hangs on, ``drop`` how far a pendant hangs
    below its ceiling, and ``recessed_into_host_surface`` whether it obstructs a neighbour's
    clear floor space. So the whole constructor is rebuilt from the current mount rather than
    replaced with a bare ``Mount(elevation=…)``.
    """
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    mount = getattr(item, "mount", None) or Mount()
    height = _as_length(elevation)
    if height.meters < 0:
        raise MacroError("mount elevation must be at or above the floor")
    fields = [f"kind=MountKind.{mount.kind.name}", f"elevation={height.to_source()}"]
    if mount.drop is not None:
        fields.append(f"drop={mount.drop.to_source()}")
    if mount.recessed_into_host_surface:
        fields.append("recessed_into_host_surface=True")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"mount": RawExpr(f"Mount({', '.join(fields)})")})])


def detach_placeable(plan: PlanModel, storey: str, *, tag: str,
                     position: XY | None = None) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    fields: dict[str, object] = {"location": DELETE_FIELD}
    if position is not None:
        fields["position"] = _point_expr(position[0], position[1])
        fields["room"] = _containing_room(plan, storey, (_meters(position[0]), _meters(position[1])))
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag, fields)])


def retype_placeable(plan: PlanModel, storey: str, *, tag: str,
                     type_ref: str) -> MutationResult:
    """Swap a placeable's product type, keeping its wall-mounted face where it was.

    A bare ``type_ref`` PATCH grows/shrinks the footprint about the authored *center*
    (position is the footprint centroid, ``resolve/placeables.py::_local_footprint``),
    which un-seats a wall-backed unit: the 2026-07-30 shower→tub-shower hand edit had to
    recompute position by hand. This macro does that arithmetic: when both types carry a
    rectangular footprint and the item names a ``wall_ref``, the position shifts by
    ``(d_old − d_new)/2`` along the *back* direction (local +y under the item's rotation
    — ``resolve/placeables.py`` defines local −y as the room-facing front), so the
    mounted back face stays exactly where it was. The along-wall center station keeps;
    re-centring in an alcove stays the author's call. Items placed by a
    ``location.attachment`` need no shift (the resolver re-derives their center from the
    wall face each build), and items with neither get a warning instead of a guess.

    Every other authored reference to the tag (``PipeRun.serves``,
    ``Sleeve.serves_fixture``, lighting ``controlled_by``, …) stays *valid* — the tag
    does not change — but sizing that was authored against the old type (drain/trap
    diameters, slice cut planes) is not rewritten; those surface as warnings for review.
    Out of scope, deliberately: tag renames, catalog/type edits, rewriting dependent
    diameters."""
    from typehaus.resolve.placeables import _TYPE_COLLECTIONS

    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    types = {entry.tag: entry for collection, _, _ in _TYPE_COLLECTIONS
             for entry in getattr(plan.library, collection)}
    new_type = types.get(type_ref)
    if new_type is None:
        raise MacroError(f"unknown product type {type_ref!r}")
    old_type = types.get(getattr(item, "type_ref", None))
    fields: dict[str, object] = {"type_ref": type_ref}
    warnings: list[str] = []

    old_fp = getattr(old_type, "footprint", None) if old_type is not None else None
    new_fp = getattr(new_type, "footprint", None)
    if old_fp is not None and new_fp is not None:
        depth_shift_m = (old_fp[1].meters - new_fp[1].meters) / 2.0
        footprint_changed = (abs(old_fp[0].meters - new_fp[0].meters) > 1e-9
                             or abs(depth_shift_m) > 1e-9)
        location = getattr(item, "location", None)
        attached = location is not None and getattr(location, "attachment", None) is not None
        if footprint_changed and not attached:
            if getattr(item, "wall_ref", None) and abs(depth_shift_m) > 1e-9:
                rotation = getattr(item, "rotation", None)
                theta = rotation.radians if rotation is not None else 0.0
                x, y = item.position.xy_m
                fields["position"] = _point_expr_m(
                    x - depth_shift_m * math.sin(theta),
                    y + depth_shift_m * math.cos(theta))
                warnings.append(
                    f"{tag} re-anchored: back face held against {item.wall_ref} "
                    f"(center moved {abs(depth_shift_m) / 0.0254:.1f}\" "
                    f"{'toward' if depth_shift_m > 0 else 'away from'} the wall)")
            elif not getattr(item, "wall_ref", None):
                warnings.append(
                    f"{tag} footprint changed ({old_fp[0].fmt()} x {old_fp[1].fmt()} → "
                    f"{new_fp[0].fmt()} x {new_fp[1].fmt()}) but it names no wall_ref — "
                    "position kept as-is; verify placement")

    for element in plan.all_elements():
        if element.tag == tag:
            continue
        referencing = sorted(
            field for field, value in element.model_dump().items()
            if value == tag or (isinstance(value, (list, tuple)) and tag in value))
        if referencing:
            warnings.append(
                f"{element.element_kind} {element.tag} references {tag} via "
                f"{', '.join(referencing)} — authored against the old type; review "
                "sizing/placement")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag, fields)],
                          warnings=tuple(warnings))


def assign_placeable_room(plan: PlanModel, storey: str, *, tag: str,
                          room: str | None) -> MutationResult:
    """Set or clear the explicit room claim; geometry containment remains resolver-owned."""
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    if room is not None and not any(candidate.tag == room for candidate in _rooms(plan, storey)):
        raise MacroError(f"no room {room!r} on storey {storey!r}")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag, {"room": room})])


def duplicate_canvas_object(plan: PlanModel, storey: str, *, tag: str) -> MutationResult:
    """Duplicate a canvas instance through the same source-backed macro path as placement.

    New instances deliberately receive a fresh mutable tag/UID.  Free placeables are offset
    by one foot so the duplicate is immediately visible; hosted openings seek the next
    non-overlapping station on their existing wall.
    """
    placeable = _placeable(plan, storey, tag)
    if placeable is not None:
        if placeable.type_ref is None:
            raise MacroError(f"placeable {tag!r} has no catalog type")
        x, y = placeable.position.xy_m
        return place_placeable(plan, storey, type_ref=placeable.type_ref,
                               position=(x + 0.3048, y + 0.3048), tag=_copy_tag(plan, tag),
                               kind=getattr(getattr(placeable, "kind", None), "value", None))
    opening = next((item for item in _openings(plan, storey) if item.tag == tag), None)
    if opening is None:
        raise MacroError(f"no canvas object {tag!r} on storey {storey!r}")
    wall = next((item for item in _walls(plan, storey) if item.tag == opening.host), None)
    if wall is None:
        raise MacroError(f"opening {tag!r} hosts on missing wall {opening.host!r}")
    start = next((item for item in _nodes(plan, storey) if item.tag == wall.start_node), None)
    end = next((item for item in _nodes(plan, storey) if item.tag == wall.end_node), None)
    if start is None or end is None:
        raise MacroError(f"wall {wall.tag!r} has unresolved endpoints")
    length = ((start.position.x.meters - end.position.x.meters) ** 2 +
              (start.position.y.meters - end.position.y.meters) ** 2) ** .5
    width = _opening_width(plan, opening)
    original = _opening_start_offset(opening, wall, length, width)
    for station in (original + width + .1524, original - width - .1524):
        try:
            if isinstance(opening, RoughOpening):
                copied = RoughOpening(tag=_copy_tag(plan, tag), host=wall.tag,
                                      position=from_node(wall.start_node, m(station)),
                                      width=opening.width, height=opening.height,
                                      sill_height=opening.sill_height, arch=opening.arch)
                _validate_opening_station(plan, storey, copied, wall, m(station))
                op = element_add_op(copied, tag=copied.tag, hint_list="OPENINGS")
                op.fields["position"] = RawExpr(f'from_node("{wall.start_node}", {m(station).to_source()})')
                return MutationResult(ops=[op])
            return place_opening(plan, storey, host=wall.tag, type_ref=opening.type_ref,
                                 along=station, is_door=isinstance(opening, Door),
                                 sill=opening.sill_height.meters if opening.sill_height is not None else None,
                                 tag=_copy_tag(plan, tag))
        except MacroError as exc:
            if "does not fit" not in str(exc) and "conflicts" not in str(exc):
                raise
    raise MacroError(f"no non-overlapping station available to duplicate opening {tag!r}")


def place_placeable(plan: PlanModel, storey: str, *, type_ref: str, position: XY,
                    hint_file: str | None = None, tag: str | None = None,
                    kind: str | None = None) -> MutationResult:
    """Instantiate a catalog type at a project position through the ordinary undo journal."""
    x, y = _as_length(position[0]), _as_length(position[1])
    collection_map = (
        ("furniture_types", Furniture, "FURNITURE", "F-"),
        ("fixture_types", Fixture, "FIXTURES", "FX-"),
        ("appliance_types", Appliance, "APPLIANCES", "APPL-"),
        ("equipment_types", Equipment, "EQUIPMENT", "EQ-"),
        ("register_types", Register, "REGISTERS", "REG-"),
        ("electrical_device_types", ElectricalDevice, "DEVICES", "ED-"),
    )
    selected = next(((cls, list_name, prefix) for collection, cls, list_name, prefix in collection_map
                     if any(product.tag == type_ref for product in getattr(plan.library, collection))), None)
    if selected is None:
        raise MacroError(f"unknown placeable type {type_ref!r}")
    cls, list_name, prefix = selected
    # Project source owns a mixed editable placeables list for each storey.  Keeping all
    # product domains together lets an imported appliance/device use the same journal path.
    list_name = f"{storey.upper()}_PLACEABLES"
    new_tag = tag or _next_tag(list(plan.storey_elements(storey)), prefix)
    common = {"tag": new_tag, "type_ref": type_ref, "position": pt(x, y),
              "room": _containing_room(plan, storey, (x.meters, y.meters))}
    if cls is Equipment:
        item = Equipment(**common, kind=EquipmentKind(kind or EquipmentKind.FURNACE.value), footprint=(ft(2), ft(2)))
    elif cls is Register:
        item = Register(**common, kind=DuctSystem(kind or DuctSystem.SUPPLY.value))
    elif cls is ElectricalDevice:
        item = ElectricalDevice(**common, kind=DeviceKind(kind or DeviceKind.RECEPTACLE.value))
    else:
        item = cls(**common)
    return MutationResult(ops=[element_add_op(item, tag=new_tag, hint_list=list_name,
                                               hint_file=hint_file)])


def _containing_room(plan: PlanModel, storey: str, position: tuple[float, float]) -> str | None:
    """Resolve room faces once at the mutation edge so authored assignment follows a drag.

    A room seed alone is not a boundary, so this deliberately uses the same resolver as the
    canvas.  If a partially authored plan cannot resolve, leaving the claim empty is safer
    than retaining a now-wrong previous room assignment; the normal resolver then reports
    any topology problem as its own finding.
    """
    try:
        from shapely.geometry import Point, Polygon
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        return next((room.tag for room in model.rooms if room.storey == storey and
                     Polygon(room.clear_face).covers(Point(position))), None)
    except Exception:  # noqa: BLE001 - macros must remain usable while a plan is mid-edit
        return None


# --- rubber-band stretch -----------------------------------------------------

def move_nodes(
    plan: PlanModel, storey: str, node_tags: list[str], dx: float | str, dy: float | str
) -> MutationResult:
    """Translate a rigid node set by (dx, dy) — the atomic op behind stretch + driven dims.

    Every connected wall stretches/shrinks for free (walls reference nodes, not coordinates).
    Anchor-pinned nodes never move (§Driven dimensions); moving *only* pinned nodes is a
    rejected op, never a silent no-op.
    """
    dxm, dym = _meters(dx), _meters(dy)
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    movable = [t for t in node_tags if not getattr(by_tag.get(t), "anchored", False)]
    pinned = [t for t in node_tags if t not in movable]
    if not movable:
        raise MacroError(
            f"all requested nodes are anchor-pinned ({', '.join(pinned)}); nothing to move"
        )
    ops: list[PatchOp] = []
    for tag in movable:
        nd = by_tag.get(tag)
        if nd is None:
            raise MacroError(f"no node {tag!r} on storey {storey!r}")
        px, py = nd.position.xy_m
        ops.append(PatchOp("update", "Node", tag,
                           {"position": _point_expr_m(px + dxm, py + dym)}))
    # A completed room-boundary translation is a rigid move; a partial boundary selection
    # is a resize and intentionally leaves contents at their project coordinates.
    translated_rooms = _rooms_with_moved_boundaries(plan, storey, set(movable))
    for room in _rooms(plan, storey):
        if room.tag not in translated_rooms:
            continue
        x, y = room.seed.xy_m
        ops.append(PatchOp("update", "Room", room.tag,
                           {"seed": _point_expr_m(x + dxm, y + dym)}))
    for item in plan.storey_elements(storey):
        if not isinstance(item, _PLACEABLE_KINDS) or getattr(item, "room", None) not in translated_rooms:
            continue
        location = getattr(item, "location", None)
        if location is not None and location.attachment is not None:
            continue
        x, y = item.position.xy_m
        ops.append(PatchOp("update", item.element_kind, item.tag,
                           {"position": _point_expr_m(x + dxm, y + dym)}))
    warnings = (f"pinned nodes held: {', '.join(pinned)}",) if pinned else ()
    return MutationResult(ops=ops, warnings=warnings)


def _rooms_with_moved_boundaries(plan: PlanModel, storey: str, moved_nodes: set[str]) -> set[str]:
    """Return rooms whose complete authored boundary node set participates in this move."""
    try:
        from shapely.geometry import Point, Polygon
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        nodes = _nodes(plan, storey)
        translated: set[str] = set()
        for room in model.rooms:
            if room.storey != storey or len(room.clear_face) < 3:
                continue
            boundary = Polygon(room.clear_face).boundary
            boundary_nodes = {node.tag for node in nodes
                              if boundary.distance(Point(node.position.xy_m)) <= ROOM_BOUNDARY_NODE_TOLERANCE_M}
            if boundary_nodes and boundary_nodes <= moved_nodes:
                translated.add(room.tag)
        return translated
    except Exception:  # noqa: BLE001 - a half-authored room must not make node edits fail
        return set()


def _point_expr_m(x_m: float, y_m: float) -> RawExpr:
    """Emit a point from meters, snapping near-round inch values to authored ft-in."""
    return RawExpr(f"pt({_round_len(x_m).to_source()}, {_round_len(y_m).to_source()})")


def _round_len(x_m: float) -> Length:
    inches = x_m / 0.0254
    nearest = round(inches * 16) / 16  # 1/16" grid
    if abs(nearest - inches) < 1e-6:
        feet, rem = divmod(nearest, 12)
        return ft(feet, rem)
    return m(x_m)


# --- split -------------------------------------------------------------------

def split_wall(plan: PlanModel, storey: str, wall_tag: str, at: XY) -> MutationResult:
    """Split a wall at a point — 1 wall → 2, the original uid staying with the a-side (#33).

    The survivor keeps ``wall_tag``; a fresh segment is added. A midnode is inserted, openings
    re-host to whichever segment their position falls in, and a :class:`ReferenceRemap` reports
    the identity change so hosted openings and stack refs carry through.
    """
    wall = next((w for w in _walls(plan, storey) if w.tag == wall_tag), None)
    if wall is None:
        raise MacroError(f"no wall {wall_tag!r} on storey {storey!r}")
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    a, b = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    if a is None or b is None:
        raise MacroError(f"wall {wall_tag!r} has an unresolved node")
    ax, ay = a.position.xy_m
    bx, by = b.position.xy_m
    px, py = _meters(at[0]), _meters(at[1])
    t = _project_param((ax, ay), (bx, by), (px, py))
    if not (SNAP_M < t < 1 - SNAP_M):
        raise MacroError("split point is at or beyond a wall end")

    mid_tag = _next_tag(_nodes(plan, storey), "N-")
    new_wall_tag = _next_tag(_walls(plan, storey), "W-")
    seg_fields = {"start_node": mid_tag, "end_node": wall.end_node, "assembly": wall.assembly}
    ops = [
        PatchOp("add", "Node", mid_tag,
                {"position": _point_expr_m(ax + t * (bx - ax), ay + t * (by - ay))},
                hint_list="NODES"),
        # survivor keeps the a-side: its end becomes the midnode
        PatchOp("update", "Wall", wall_tag, {"end_node": mid_tag}),
        PatchOp("add", "Wall", new_wall_tag, seg_fields, hint_list="WALLS"),
    ]
    remap, refit_ops, warnings = _rehost_openings(
        plan, storey, wall, wall_tag, new_wall_tag, t
    )
    ops.extend(refit_ops)
    return MutationResult(ops=ops, remap=remap, warnings=warnings)


def _rehost_openings(
    plan: PlanModel, storey: str, wall: Wall, keep_tag: str, new_tag: str, split_t: float
) -> tuple[ReferenceRemap, list[PatchOp], tuple[str, ...]]:
    """Re-host openings on the split wall onto the segment their position falls in."""
    rehost: dict[str, str] = {}
    warnings: list[str] = []
    for el in plan.storey_elements(storey):
        if getattr(el, "host", None) != wall.tag:
            continue
        along = _opening_param(el, wall, plan, storey)
        if along is not None and along > split_t:
            rehost[el.tag] = new_tag
            warnings.append(f"opening {el.tag} re-hosted to {new_tag}")
    remap = ReferenceRemap(renamed={}, rehost=rehost)
    ops: list[PatchOp] = []
    for el in plan.storey_elements(storey):
        if getattr(el, "host", None) == wall.tag:
            ops.extend(remap_ops_for(el, remap))
    return remap, ops, tuple(warnings)


def _opening_param(el: object, wall: Wall, plan: PlanModel, storey: str) -> float | None:
    """Fractional position (0..1) of an opening along its host wall, if determinable."""
    pos = getattr(el, "position", None)
    if pos is None or getattr(pos, "mode", None) != "from_node":
        return 0.5 if pos is not None else None  # centered → keeps a-side
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    a, b = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    anchor = by_tag.get(pos.node or wall.start_node)
    if a is None or b is None or anchor is None or pos.offset is None:
        return None
    length = _dist(a.position.xy_m, b.position.xy_m)
    if length == 0:
        return None
    base = 0.0 if anchor.tag == wall.start_node else 1.0
    frac = pos.offset.meters / length
    return base + frac if base == 0.0 else base - frac


# --- heal / merge ------------------------------------------------------------

def heal_walls(plan: PlanModel, storey: str, node_tag: str) -> MutationResult:
    """Fuse two collinear walls meeting at ``node_tag`` back into one edge (inverse of split).

    The survivor is the wall contributing the fused edge's a-node (#33). The shared node and
    the second wall are deleted; a :class:`ReferenceRemap` renames the absorbed wall to the
    survivor so hosted openings and refs follow.
    """
    incident = [w for w in _walls(plan, storey)
                if node_tag in (w.start_node, w.end_node)]
    if len(incident) != 2:
        raise MacroError(
            f"heal needs exactly two walls at {node_tag!r}, found {len(incident)}"
        )
    w1, w2 = incident
    by_tag = {nd.tag: nd for nd in _nodes(plan, storey)}
    if not _collinear(w1, w2, node_tag, by_tag):
        raise MacroError(f"walls at {node_tag!r} are not collinear; cannot heal")
    # Survivor is the wall whose a-node is not the shared node (keeps its start).
    survivor, absorbed = (w1, w2) if w1.start_node != node_tag else (w2, w1)
    far_end = absorbed.end_node if absorbed.start_node == node_tag else absorbed.start_node
    remap = ReferenceRemap(renamed={absorbed.tag: survivor.tag},
                           deleted=frozenset({node_tag}))
    ops = [
        PatchOp("update", "Wall", survivor.tag, {"end_node": far_end}),
        PatchOp("delete", "Wall", absorbed.tag, {}),
        PatchOp("delete", "Node", node_tag, {}),
    ]
    warnings: list[str] = []
    for el in plan.storey_elements(storey):
        if getattr(el, "host", None) == absorbed.tag:
            ops = remap_ops_for(el, remap) + ops
            warnings.append(f"opening {el.tag} re-hosted to {survivor.tag}")
    return MutationResult(ops=ops, remap=remap,
                          deleted_tags=(absorbed.tag, node_tag), warnings=tuple(warnings))


# --- geometry primitives -----------------------------------------------------

def _dist(p: tuple[float, float], q: tuple[float, float]) -> float:
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


def _project_param(
    a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]
) -> float:
    abx, aby = b[0] - a[0], b[1] - a[1]
    denom = abx * abx + aby * aby
    if denom == 0:
        return 0.0
    return ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / denom


def _collinear(w1: Wall, w2: Wall, shared: str, by_tag: dict[str, Node]) -> bool:
    def other(w: Wall) -> str:
        return w.end_node if w.start_node == shared else w.start_node

    s = by_tag.get(shared)
    e1, e2 = by_tag.get(other(w1)), by_tag.get(other(w2))
    if s is None or e1 is None or e2 is None:
        return False
    (sx, sy) = s.position.xy_m
    v1 = (e1.position.xy_m[0] - sx, e1.position.xy_m[1] - sy)
    v2 = (e2.position.xy_m[0] - sx, e2.position.xy_m[1] - sy)
    l1 = (v1[0] ** 2 + v1[1] ** 2) ** 0.5
    l2 = (v2[0] ** 2 + v2[1] ** 2) ** 0.5
    if l1 == 0 or l2 == 0:
        return False
    cross = (v1[0] * v2[1] - v1[1] * v2[0]) / (l1 * l2)
    return abs(cross) < COLLINEAR_TOL

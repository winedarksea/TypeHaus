"""Opening, room, and stair placement macros — the builders that add something *hosted*.

Split out of :mod:`typehaus.source.macros` along its own ``# --- opening / room placement``
band (→ 21b §Room macros). Everything here shares one job: authoring an element whose
position is stated against something else (a wall's start node, an enclosed area, the deck
of the storey above), so the station validation and the host lookups stay in one file.
"""

from __future__ import annotations

import math

from typehaus.model.elements import Door, RoughOpening, Window
from typehaus.model.enums import Occupancy
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.plan import PlanModel
from typehaus.model.refs import from_node
from typehaus.model.remap import MutationResult
from typehaus.model.spatial import Room, Stair
from typehaus.quantities.length import ft, m
from typehaus.quantities.point import pt
from typehaus.source.macros_common import (
    XY,
    MacroError,
    _as_length,
    _next_tag,
    _nodes,
    _openings,
    _rooms,
    _walls,
)
from typehaus.source.macros_geometry import _point_in_polygon
from typehaus.source.ops import PatchOp, RawExpr
from typehaus.source.serialize import element_add_op


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
        item = next((candidate for candidate in plan.library.door_types
                     if candidate.tag == opening.type_ref), None)
    elif isinstance(opening, Window):
        item = next((candidate for candidate in plan.library.window_types
                     if candidate.tag == opening.type_ref), None)
    else:
        # Deliberately ``getattr`` rather than ``opening.width``: the parameter is typed
        # ``object`` and this branch is the duck-typed fallback for an opening that is
        # neither a Door nor a Window, so the attribute cannot be proven to exist. B009
        # would rewrite this to a direct access, which reads better but hands mypy an
        # ``"object" has no attribute "width"`` it is right to complain about.
        return float(getattr(opening, "width").meters)  # noqa: B009
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
            raise MacroError(f"opening {opening.tag!r} conflicts with {peer.tag!r} "
                             f"on wall {wall.tag!r}")


def _opening_start_offset(opening: object, wall: object, wall_length_m: float,
                          width_m: float) -> float:
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

"""The right-angle winder: fanned winder treads, the straight flight, and the turn frame."""

from __future__ import annotations

import math

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import (
    _TREAD_THICKNESS_M,
    _newel_face_point,
    _tread_board_profile,
)

_NEWEL_PROFILE = "4x4"


def _winder_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                          risers: int, riser: float, tread: float) -> tuple[FramedMember, ...]:
    """Generate a lower quarter-turn with consistently fanned winder treads.

    ``start`` is the lower outside corner of the winder square.  The straight flight leaves
    that square in ``run_direction``; ``run_reversed`` selects west/south rather than the
    conventional east/north direction. Each tread edge shares the inside corner and fans
    across the outside of the turn, preventing the opposed-diagonal geometry two winders
    produced.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    straight_treads = risers - 1 - stair.winder_count
    step_z = lambda index: z0 + riser * (index + 1)
    out: list[FramedMember] = []
    sign = -1 if stair.run_reversed else 1
    turn_sign = 1 if stair.turn_direction != "right" else -1
    along_x = stair.run_direction == "x"
    # One parametrization for all four sign/turn_sign combinations: `a` runs along the
    # ascent (the straight flight's direction), `b` across it toward the turn. The turn
    # square's corners are then P(0,0) (the entering outer corner, == ``start``),
    # P(width,0) (the inside corner / newel), P(0,width) and P(width,width).
    run_u = (sign, 0.0) if along_x else (0.0, sign)
    cross_u = (0.0, turn_sign) if along_x else (turn_sign, 0.0)

    def offset(point: tuple[float, float], a: float = 0.0,
               b: float = 0.0) -> tuple[float, float]:
        """``point`` moved ``a`` metres along the run and ``b`` metres across it."""
        return (point[0] + run_u[0] * a + cross_u[0] * b,
                point[1] + run_u[1] * a + cross_u[1] * b)

    def P(a: float, b: float) -> tuple[float, float]:
        """Plan point ``a`` metres along the run, ``b`` metres across it, from ``start``."""
        return offset((start_x, start_y), a, b)

    # The straight flight springs off the top of the winder turn; its raked stringers run
    # from one riser above that springing up to the arrival deck.
    stringer_depth = cross_section("2x12").depth_m
    spring_top = z0 + riser * stair.winder_count + riser + _TREAD_THICKNESS_M
    arrival = z0 + riser * risers
    foot = P(0.0, 0.0)  # the entering outer corner of the turn square (== ``start``)
    inside = P(width, 0.0)  # the turn's inside corner: where the straight flight springs
    outer_corner = P(0.0, width)  # the outer corner the turn sweeps around
    turn = P(width, width)  # the departing corner, where the outer stringer takes over
    for index, cross in enumerate((0.0, width)):
        out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12",
                                offset(inside, 0.0, cross),
                                offset(inside, tread * straight_treads, cross),
                                spring_top - stringer_depth, spring_top,
                                math.hypot(tread * straight_treads, riser * risers),
                                z0_end_m=arrival - stringer_depth, z1_end_m=arrival))
    newel_half_face = cross_section(_NEWEL_PROFILE).width_m / 2.0
    for index in range(stair.winder_count):
        # ``winder_count + 1`` because ``fraction == 1`` — the departing edge of the turn
        # square — belongs to the straight flight's first tread. Dividing by the winder
        # count alone put the top winder exactly on top of ``tread-000``: a riser with
        # zero going. It also makes the carriage rake close exactly on the springing.
        fraction = (index + 1) / (stair.winder_count + 1)
        # First half follows the entering outside edge, second half the departing edge.
        nosing = (P(0.0, width * fraction * 2) if fraction <= 0.5
                  else P(width * (fraction * 2 - 1), width))
        a, b = _newel_face_point(inside, nosing, newel_half_face), nosing
        out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                a, b, step_z(index), step_z(index) + _TREAD_THICKNESS_M,
                                math.hypot(b[0] - a[0], b[1] - a[1])))
    tread_profile = _tread_board_profile(tread)
    for index in range(straight_treads):
        centre = tread * index + tread / 2.0
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", tread_profile,
                                offset(inside, centre, 0.0),
                                offset(inside, centre, width),
                                step_z(index + stair.winder_count),
                                step_z(index + stair.winder_count) + _TREAD_THICKNESS_M,
                                width))
    out.extend(_winder_turn_framing(stair, z0, riser, width, spring_top, stringer_depth,
                                    foot, inside, outer_corner, turn,
                                    (float(run_u[0]), float(run_u[1]))))
    return tuple(out)


def _winder_turn_framing(stair: Stair, z0: float, riser: float, width: float,
                         spring_top: float, stringer_depth: float,
                         foot: tuple[float, float], inside: tuple[float, float],
                         outer_corner: tuple[float, float], turn: tuple[float, float],
                         orient: tuple[float, float]) -> list[FramedMember]:
    """Frame the quarter-turn itself: newel, two raked carriages, and the turn header.

    Without this the turn is a mathematical fiction — every winder's narrow end converges
    on a bare point and the straight flight springs off nothing.

    - **The newel** carries every winder narrow end, so it must reach the *highest*
      winder's nosing, which is above the header; it therefore runs past the header up to
      the springing and picks up ``stringer-0`` too. That is how a winder newel works.
    - **The carriages** are the outer stringer carried around the turn: one straight rake
      through every winder nosing, ``top(f) = z0 + riser*(winder_count+1)*f + tread``.
      ``top(1) == spring_top``, so the departing carriage runs continuously into
      ``stringer-1`` and must end precisely at ``turn`` — an overshoot would read as a
      real interference against it. They are category ``stringer``, so the bearing pass
      picks them up against a flanking wall for free.
    - **The header** tops out at the springing's underside — exactly the stringers'
      ``z0_m`` at ``p0`` — so the flight seats on it with zero overlap. Its ends are
      carried by the newel at ``inside`` and by a second newel at ``turn``.
    """

    def carriage_top(fraction: float) -> float:
        return z0 + riser * (stair.winder_count + 1) * fraction + _TREAD_THICKNESS_M

    header_top = spring_top - stringer_depth
    out = [
        FramedMember(stair.uid, "newel-000", "newel", _NEWEL_PROFILE, inside, inside,
                     z0, spring_top, spring_top - z0, orient=orient),
        FramedMember(stair.uid, "newel-001", "newel", _NEWEL_PROFILE, turn, turn,
                     z0, header_top, header_top - z0, orient=orient),
    ]
    for index, (a, b, f0, f1) in enumerate(((foot, outer_corner, 0.0, 0.5),
                                            (outer_corner, turn, 0.5, 1.0))):
        top_a, top_b = carriage_top(f0), carriage_top(f1)
        out.append(FramedMember(
            stair.uid, f"winder-carriage-{index}", "stringer", "2x12", a, b,
            top_a - stringer_depth, top_a, math.hypot(width, top_b - top_a),
            z0_end_m=top_b - stringer_depth, z1_end_m=top_b))
    out.append(FramedMember(stair.uid, "winder-header", "header", "2-2x12", inside, turn,
                            header_top - cross_section("2-2x12").depth_m, header_top,
                            width))
    return out

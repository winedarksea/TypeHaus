"""The right-angle winder: a tiered corner box, its winder treads, and the straight flight."""

from __future__ import annotations

import math
from typing import NamedTuple

from typehaus.model.spatial import Stair
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import (
    _TREAD_THICKNESS_M,
    _notch_z,
    _tread_board_profile,
)

# A box side is ripped from 2x stock to the box's own height (one riser less the deck it
# carries), so consecutive tiers stack dead flush. ``_SPRING_RIM_PLIES`` doubles the top
# box's departing rim: that one carries the whole straight flight.
_BOX_RIM_PLY_IN = 1.5
_SPRING_RIM_PLIES = 2
# The diagonal block that splits each box into two bearing triangles.
_BOX_BLOCK_PROFILE = "2x6"


class _FanLine(NamedTuple):
    """One winder's tread line: the newel face it starts at, its nosing on the turn
    square's outside, and whether the box behind it still wraps the outer corner."""

    narrow: tuple[float, float]
    nosing: tuple[float, float]
    wraps_outer_corner: bool


def _clean_ring(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """A ring reduced to its distinct corner vertices.

    The fan construction can hand a wedge coincident consecutive points (a nosing landing
    exactly on the outer corner) and vertices collinear with their neighbours (three narrow
    ends sharing the newel line; the first wedge's entering corner doubling back along the
    entering edge). Both survive plan drawing but produce zero-area flaps and coincident
    opposite-facing side quads once the ring is extruded to a prism.
    """
    deduped: list[tuple[float, float]] = []
    for point in ring:
        if not deduped or math.hypot(point[0] - deduped[-1][0],
                                     point[1] - deduped[-1][1]) > 1e-9:
            deduped.append(point)
    if len(deduped) > 1 and math.hypot(deduped[0][0] - deduped[-1][0],
                                       deduped[0][1] - deduped[-1][1]) <= 1e-9:
        deduped.pop()
    out: list[tuple[float, float]] = []
    count = len(deduped)
    for index in range(count):
        a, b, c = deduped[index - 1], deduped[index], deduped[(index + 1) % count]
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) > 1e-9:
            out.append(b)
    return out


def _box_rim_profile(frame_depth_m: float, plies: int = 1) -> str:
    """A box side ripped to ``frame_depth_m``, in ``plies`` plies of 2x stock."""
    return (f"{_BOX_RIM_PLY_IN * plies:g}x"
            f"{frame_depth_m / inch(1).meters:g} rim")


def _winder_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                          risers: int, riser: float, tread: float,
                          tread_depth: float, nosing: float) -> tuple[FramedMember, ...]:
    """Generate a lower quarter-turn with consistently fanned winder treads.

    ``start`` is the lower outside corner of the winder square.  The straight flight leaves
    that square in ``run_direction``; ``run_reversed`` selects west/south rather than the
    conventional east/north direction. Each tread edge shares the inside corner and fans
    across the outside of the turn, preventing the opposed-diagonal geometry two winders
    produced.

    The turn is framed as a tiered corner box (see :func:`_winder_box_framing`), so a
    winder tread here is the *leading edge* of one box's deck: the fan line its riser
    board nails to, with the pie-shaped deck panel behind it.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    straight_treads = risers - 1 - stair.winder_count
    surface = lambda index: z0 + riser * (index + 1)  # noqa: E731 — finished walking face
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

    # The straight flight springs off the top box of the turn; its raked stringers run from
    # one riser above that box's deck up to the arrival deck. Both ends are *notch* lines —
    # the tread boards and the arrival subfloor sit on them (see ``_notch_z``), which is
    # what keeps the rake straight and every finished riser equal.
    stringer_depth = cross_section("2x12").depth_m
    spring_notch = _notch_z(surface(stair.winder_count))
    arrival_notch = _notch_z(z0 + riser * risers)
    # P(0, 0) — ``start`` itself — is the entering outer corner the fan sweeps away from.
    inside = P(width, 0.0)  # the turn's inside corner: where the straight flight springs
    outer_corner = P(0.0, width)  # the outer corner the turn sweeps around
    turn = P(width, width)  # the departing corner, where the box's outer rim takes over
    for index, cross in enumerate((0.0, width)):
        out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12",
                                offset(inside, 0.0, cross),
                                offset(inside, tread * straight_treads, cross),
                                spring_notch - stringer_depth, spring_notch,
                                math.hypot(tread, riser) * straight_treads,
                                z0_end_m=arrival_notch - stringer_depth,
                                z1_end_m=arrival_notch))
    # The inside ends deliberately do not converge at the newel.  Three 6" offsets around
    # the inside corner are the minimum code-sized narrow path; the earlier radial fan put
    # all three on a 6x6 post face, delivering only ~1.3" between them.
    narrow_going = inch(6).meters
    fan: list[_FanLine] = []
    for index in range(stair.winder_count):
        # ``winder_count + 1`` because ``fraction == 1`` — the departing edge of the turn
        # square — belongs to the straight flight's first tread. Dividing by the winder
        # count alone put the top winder exactly on top of ``tread-000``: a riser with
        # zero going. It also makes the box tiers close exactly on the springing.
        # Three winders have three raised walking surfaces.  Their final nosing is the
        # departing edge of the turn; reserving a fourth fractional slice made that bare
        # floor wedge read as a fourth, level "winder" in 2D and 3D.
        fraction = (index + 1) / stair.winder_count
        # First half follows the entering outside edge, second half the departing edge.
        nosing_point = (P(0.0, width * fraction * 2) if fraction <= 0.5
                        else P(width * (fraction * 2 - 1), width))
        narrow = (P(width - narrow_going, 0.0) if index == 0
                  else P(width, narrow_going * index))
        fan.append(_FanLine(narrow, nosing_point,
                            wraps_outer_corner=fraction < 0.5))
    previous_nosing = P(0.0, 0.0)
    previous_narrow = P(width, 0.0)
    for index, (narrow, nosing_point, wraps_outer_corner) in enumerate(fan):
        top = surface(index)
        # A winder is a tapered deck panel, not the 1.5"-wide line used to annotate its
        # nosing.  Carry its actual boundary through the shared member model so every view
        # sees the same three rising surfaces.
        outline = [previous_narrow, previous_nosing]
        # The outer corner belongs in a wedge only when the wedge *spans* it: previous
        # nosing still on the entering edge, this one already past the corner. Appending it
        # whenever the current line wrapped put it inside the first wedge too — whose
        # nosings both sit on the entering edge — as a zero-area excursion doubling a line
        # along the whole outer edge in plan and in the extruded prism.
        if index and fan[index - 1].wraps_outer_corner and not wraps_outer_corner:
            outline.append(outer_corner)
        outline.extend((nosing_point, narrow))
        out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                narrow, nosing_point, _notch_z(top), top,
                                math.hypot(nosing_point[0] - narrow[0], nosing_point[1] - narrow[1]),
                                plan_outline=_clean_ring(outline)))
        previous_nosing, previous_narrow = nosing_point, narrow
    tread_profile = _tread_board_profile(tread_depth)
    for index in range(straight_treads):
        centre = tread * index + (tread - nosing) / 2.0
        top = surface(index + stair.winder_count)
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", tread_profile,
                                offset(inside, centre, 0.0),
                                offset(inside, centre, width),
                                _notch_z(top), top, width,
                                riser_line=(offset(inside, tread * index, 0.0),
                                            offset(inside, tread * index, width))))
    out.extend(_winder_box_framing(stair, z0, riser, fan, P(0.0, 0.0), inside,
                                   outer_corner, turn, (float(run_u[0]), float(run_u[1]))))
    return tuple(out)


def _box_perimeter(line: _FanLine, outer_corner: tuple[float, float],
                   turn: tuple[float, float]) -> list[tuple[tuple[float, float],
                                                            tuple[float, float]]]:
    """The outside edges of the box behind ``line``: its nosing around the square to ``turn``.

    A box whose fan line still leaves the entering outside edge wraps the outer corner, so
    it takes two segments; one past the halfway sweep runs a single segment along the
    departing edge.
    """
    if line.wraps_outer_corner:
        return [(line.nosing, outer_corner), (outer_corner, turn)]
    return [(line.nosing, turn)]


def _polyline_midpoint(segments: list[tuple[tuple[float, float], tuple[float, float]]]
                       ) -> tuple[float, float]:
    """The point halfway along a run of segments, by arc length."""
    # NB plain ``zip``: the engine still runs on 3.9 here, where ``strict=`` does not exist
    # (which is what the repo's standing B905 findings are).
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segments]
    remaining = sum(lengths) / 2.0
    last = len(segments) - 1
    for index, ((a, b), length) in enumerate(zip(segments, lengths)):
        if remaining <= length or index == last:
            t = remaining / length if length > 1e-9 else 0.0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        remaining -= length
    return segments[-1][1]


def _winder_box_framing(stair: Stair, z0: float, riser: float, fan: list[_FanLine],
                        entering_corner: tuple[float, float],
                        inside: tuple[float, float], outer_corner: tuple[float, float],
                        turn: tuple[float, float],
                        orient: tuple[float, float]) -> list[FramedMember]:
    """Frame the quarter-turn as a tiered corner box — Larry Haun's winder assembly.

    Rather than cut a continuous compound-angle carriage through the turn (which the
    previous two raked "winder carriages" and their header stood in for, and which no
    framer builds), each winder step is its own platform box, stacked one riser above the
    last:

    - **A box per step, bounded by its *leading* fan line.** Box ``k`` covers everything
      ahead of fan line ``k-1`` (the riser face a walker steps up at onto its deck; the
      turn square's entering edge for box 0), so box 0 is the full corner platform and
      each later box nests inside the one below — a wedding cake, every tier fully
      carried. Framing box ``k`` ahead of its *own* fan line instead left every pie
      panel cantilevered one riser above the box that actually sat under it, and
      collapsed the top tier to two coincident rims on the departing edge.
    - **Sides ripped from 2x stock** to exactly one riser less the deck they carry, so
      box ``k`` lands dead flush on box ``k-1``'s deck and box 0 lands on the subfloor.
      The pie-shaped panel on top is the walking surface.
    - **A diagonal block** across each box, newel to the mid-point of its outside run,
      splitting the wedge into two bearing triangles under the pie panel.
    - **Ledgers and posts come for free.** The sides are category ``landing`` with
      ``landing-rim-`` keys, so ``bearing._bear_stair_on_walls`` ledgers whichever ones
      run against a flanking wall and posts every corner none reaches down to the
      subfloor — one post per plan point, carrying all the tiers stacked over it.
    - **The newel** is the assembly's inside corner post: every box's fan-line rim and
      departing rim dies into it, and the inner stringer's foot lands on it. It tops out
      at the top box's deck.
    - **The straight flight lands on the top box**, not on a header slung under it: its
      stringers' notch line springs one riser above that deck, and the departing rim
      under them is doubled (``_SPRING_RIM_PLIES``) because it carries the flight.
    """
    frame_depth = riser - _TREAD_THICKNESS_M
    rim_profile = _box_rim_profile(frame_depth)
    spring_profile = _box_rim_profile(frame_depth, _SPRING_RIM_PLIES)
    block_depth = cross_section(_BOX_BLOCK_PROFILE).depth_m
    newel_top = z0 + riser * stair.winder_count
    out = [FramedMember(stair.uid, "newel-000", "newel", stair.newel_profile, inside,
                        inside, z0, newel_top, newel_top - z0, orient=orient)]
    # Box 0's leading edge is the turn square's entering riser face.
    entering = _FanLine(inside, entering_corner, wraps_outer_corner=True)
    for index in range(len(fan)):
        deck = _notch_z(z0 + riser * (index + 1))  # the box's sides top out under its deck
        base = z0 + riser * index  # ... and land on the tier below (the subfloor at k=0)
        leading = fan[index - 1] if index else entering
        outside = _box_perimeter(leading, outer_corner, turn)
        top_tier = index == len(fan) - 1
        # Rims run to the newel's *centreline*, not the face its tread starts at: the post
        # is what carries their inside ends, and the bearing pass looks for a load path at
        # the endpoint itself. The tread above still starts at the face it can be walked
        # from — that difference is the narrow-end depth the winder rule measures.
        rims = [(inside, leading.nosing), *outside, (turn, inside)]
        for edge, (a, b) in enumerate(rims):
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            if length < 1e-9:  # a fan line landing exactly on the outer corner
                continue
            departing = edge == len(rims) - 1
            out.append(FramedMember(
                stair.uid, f"landing-rim-winder{index}-{edge}", "landing_framing",
                spring_profile if departing and top_tier else rim_profile,
                a, b, base, deck, length))
        block_end = _polyline_midpoint(outside)
        out.append(FramedMember(
            stair.uid, f"landing-joist-winder{index}-0", "landing_framing",
            _BOX_BLOCK_PROFILE,
            inside, block_end, deck - block_depth, deck,
            math.hypot(block_end[0] - inside[0], block_end[1] - inside[1])))
    return out

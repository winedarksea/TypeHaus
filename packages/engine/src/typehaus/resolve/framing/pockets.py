"""Where a pocket door's cavity actually lands, wall by wall (→ 11 §Framing).

A pocket runs roughly a leaf-width past its rough opening, so on any wall that the plan
has segmented at a tee it routinely crosses a node. That is not a modelling error. Wall
segmentation at a tee is an authoring convention — ``classify_storey_junctions`` builds
junctions from wall *endpoints*, so a partition teeing in has to split the wall it lands
on — while the wall itself is one plane, one assembly and one pair of plates. The leaf
really does travel across the node, and the framing has to say so.

Two consumers need this and must not disagree: the solver, which keeps module studs out of
the cavity on every wall it crosses, and ``integrity.opening_fits``, which refuses a pocket
with nowhere to go. Hence one walk, here.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.elements import Wall
from typehaus.model.plan import PlanModel
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import length, sub, unit
from typehaus.resolve.model import ResolvedModel

# The closed end of a pocket carries the jamb pack that ``frame_opening`` relocates there,
# outboard of the cavity itself, so the run a pocket needs is longer than the leaf. Two 2x
# members plus a half-stud of centreline slack covers the widest pack ``king_jack_counts``
# returns for a door, and comfortably exceeds the 2" edge distance a plain opening needs.
POCKET_PACK_MARGIN_M = 5.0 * M_PER_IN

_COLINEAR_TOLERANCE = 1e-3


@dataclass(frozen=True)
class PocketSegment:
    """One wall's share of a pocket cavity, in that wall's own axis coordinates."""

    wall_tag: str
    low_m: float
    high_m: float

    @property
    def center_m(self) -> float:
        return (self.low_m + self.high_m) / 2.0

    @property
    def half_m(self) -> float:
        return (self.high_m - self.low_m) / 2.0


def pocket_segments(plan: PlanModel, model: ResolvedModel,
                    opening) -> tuple[tuple[PocketSegment, ...], float]:
    """``(segments, shortfall_m)`` for ``opening``'s pocket, from the mouth outward.

    ``shortfall_m`` is how much of the required run found no wall to occupy — ``0.0`` when
    the cavity fits. A non-zero shortfall means the leaf would have to pass through a
    corner, a tee, or open air, and no amount of framing makes that work.

    A neighbour continues the run only if it shares the node, runs parallel, and carries
    the *same assembly*. A different assembly is a different wall in every way that matters
    here — a thickness change, a different stud depth, often a different trade — and a leaf
    may not slide into one.
    """
    if not opening.pocket_run_m or not opening.pocket_sign:
        return ((), 0.0)
    authored = {element.tag: element for element in plan.all_elements()
                if isinstance(element, Wall)}
    host, host_rw = authored.get(opening.host_wall), model.wall(opening.host_wall)
    if host is None or host_rw is None:
        return ((), opening.pocket_run_m)

    by_node: dict[str, list[str]] = {}
    for wall in authored.values():
        by_node.setdefault(wall.start_node, []).append(wall.tag)
        by_node.setdefault(wall.end_node, []).append(wall.tag)

    sign = 1 if opening.pocket_sign > 0 else -1
    station = opening.center_along_m + sign * opening.width_m / 2.0  # the mouth
    remaining = opening.pocket_run_m + POCKET_PACK_MARGIN_M
    wall, rw = host, host_rw
    segments: list[PocketSegment] = []
    seen: set[str] = set()

    while remaining > 1e-9 and wall.tag not in seen:
        seen.add(wall.tag)
        axis_len = length(sub(rw.axis[1], rw.axis[0]))
        available = axis_len - station if sign > 0 else station
        take = min(remaining, max(0.0, available))
        if take > 1e-9:
            low, high = ((station, station + take) if sign > 0
                         else (station - take, station))
            segments.append(PocketSegment(wall.tag, low, high))
            remaining -= take
        if remaining <= 1e-9:
            break
        node = wall.end_node if sign > 0 else wall.start_node
        step = _colinear_neighbour(plan, model, authored, by_node, wall, rw, node)
        if step is None:
            break
        wall, rw, station, sign = step

    return (tuple(segments), max(0.0, remaining))


def _colinear_neighbour(plan: PlanModel, model: ResolvedModel, authored, by_node,
                        wall: Wall, rw, node: str):
    """``(wall, resolved, entry station, travel sign)`` for the run's continuation."""
    direction = unit(sub(rw.axis[1], rw.axis[0]))
    for tag in by_node.get(node, ()):
        if tag == wall.tag:
            continue
        neighbour, n_rw = authored.get(tag), model.wall(tag)
        if neighbour is None or n_rw is None or neighbour.assembly != wall.assembly:
            continue
        n_direction = unit(sub(n_rw.axis[1], n_rw.axis[0]))
        dot = n_direction[0] * direction[0] + n_direction[1] * direction[1]
        if abs(dot) < 1.0 - _COLINEAR_TOLERANCE:
            continue  # a tee or a corner: the leaf stops at it
        n_len = length(sub(n_rw.axis[1], n_rw.axis[0]))
        # Enter at whichever end of the neighbour the shared node is, and travel inward.
        if neighbour.start_node == node:
            return (neighbour, n_rw, 0.0, 1)
        return (neighbour, n_rw, n_len, -1)
    return None


def pocket_keepouts(plan: PlanModel,
                    model: ResolvedModel) -> dict[str, list[tuple[float, float]]]:
    """Module-stud keepout bands a pocket door imposes on a *colinear neighbour* wall.

    The framing itself — header, both jamb packs, split studs — stays owned by the host
    wall and simply reaches past its axis; ``FramedMember`` positions are plan-frame
    points, and ``parent_uid`` is ownership for the takeoff and the viewer, not a bounding
    box. What a neighbour the cavity crosses into has to know is only that its module studs
    must stay out of it — a stud there is not a redundant load path but a door that will
    not open. The host wall's own share needs no entry — ``opening_exclusions`` already
    covers it from the opening itself.
    """
    keepouts: dict[str, list[tuple[float, float]]] = {}
    for op in model.openings:
        segments, _shortfall = pocket_segments(plan, model, op)
        for segment in segments:
            if segment.wall_tag == op.host_wall:
                continue
            keepouts.setdefault(segment.wall_tag, []).append(
                (segment.center_m, segment.half_m))
    return keepouts

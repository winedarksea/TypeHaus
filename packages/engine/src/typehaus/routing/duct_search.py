"""A duct searched with its fittings in the state: no two turns closer than their take-offs.

``search.shortest_route`` keeps ``(node, incoming axis)``, so it can price a turn but cannot
see how much straight lies behind it — and on catlin it proposed 4" ducts with a 1.2" jog
between two elbows, which no 4" elbow (2" take-off even at R = D/2) can be fitted into. A
duct turn takes ``R tan(theta/2)`` from each leg (``routing/duct_fittings``), so the label
here also carries the straight laid since the last turn.

**The label is a slack, not a length.** Every lattice turn is 90 degrees, so every lattice
turn on one run takes the same take-off T. ``slack = straight since the last turn - what
that turn took`` (0 at the start: a run end takes nothing). A turn taking t is admissible at
``slack >= t``; a goal accepts ``slack >= 0``. Slack is capped where no future can use more,
which is what keeps the frontier small.

**A short jog is an OFFSET, the different fitting.** Two 90s 4 7/8" apart — FS-S-WEST's two
tiers — cannot be fitted (a 4" pair needs 12"), but a 45 or 30 pair can: the first corner
slides back along the way in by ``h = j / tan(theta)`` and the jog is laid oblique, as
catlin authors its own tier changes. The SECOND corner slides on along the way out by
``h = j / tan(theta)``, so nothing behind it has to be re-opened: the first corner needs only
the offset elbow's own take-off behind it, and the straight after the slid corner starts
``h + t`` in debt. A first turn INTO A RISE with less than a 90's take-off behind it is
therefore taken *provisionally*: that label may only run straight to its second corner and
turn back to the heading it came in on, where the offset is tested — the oblique holds its
two take-offs and is clear (``space.edge_blocked``; the straight beyond is the lattice's).
Up to ``offset_jog_max_in``. Only a rise is offset: the lattice's z planes are few, its plan lines
dense, and provisional labels on every plan line ran catlin's ERV radials past 1.5 million
labels without an answer; a plan jog is laid with two 90s or not at all.

**Pareto per ``(node, heading, open corner)``.** A label dominates another when it is no
dearer, has no less slack (and no less straight behind its open corner), and is no more
provisional. The heading is SIGNED: a step back along the way in is a reversal, refused. The
heuristic is ``search``'s plus a bend per turn the heading still owes (a goal off its axis
needs one; behind it, or off both other axes, two; off both and behind, three), least over
the goals: still admissible, since every turn costs at least ``bend_in`` and the rules here
only remove edges or add cost; an offset only shortens a path the lattice already priced.

**A port lead fixes the heading at its end.** The kit's flex is a straight lead that never
bends (§8), so the search leaves its tip along the lead with no slack — the first rigid
turn is a full take-off beyond the flex — and must arrive at a goal tip along its lead.

``houses/catlin/notes/mep_duct_routing_basis.md`` §7 and §8 are the oracle.
"""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np

from typehaus.quantities import M_PER_IN
from typehaus.routing.graph import Graph
from typehaus.routing.search import Route, _heuristic, bend_price, price_route
from typehaus.routing.space import RoutingSpace

_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}
_INDEX = {"x": 0, "y": 1, "z": 2}
#: The proposal's 1/16" grid: a snapped vertex may move a straight by this much.
_TOL_M = 0.0015875

Point3 = tuple[float, float, float]

#: Bores the lattice prices for a pipe, which a duct pays this many times over: a 4-8"
#: hole through a joist or I-joist is a fabricator's-chart hole at best, and a joist-bay
#: duct may cross only an open web (``mep.duct_joist_bay``, which the lattice prices at
#: nothing). A stated weight, not a refusal — some runs have no other way out of a room. A
#: plate cut is a riser through a floor, and stays at its price.
_DUCT_CUTS = ("bore_stud_in", "bore_joist_in", "bore_engineered_in", "bore_unpublished_in")
DUCT_BORE_FACTOR = 4.0


@dataclass(frozen=True)
class DuctFittingProblem:
    """What the fittings of one duct demand of its route."""

    #: The take-off of one 90-degree lattice turn, each leg (``duct_fittings.Elbow``).
    takeoff_m: float
    #: Added to each turn's bend price: a fabricated elbow is the last resort.
    fabricated_in: float = 0.0
    #: Signed headings ("+z") a port lead fixes: the route leaves the start tip along the
    #: lead, and arrives at a goal tip heading for its port. "" leaves an end free.
    start_axis: str = ""
    goal_axis: str = ""
    #: ``(theta, take-off)`` of the elbows an offset may be made with, tried in order.
    offsets: tuple[tuple[float, float], ...] = ()
    offset_jog_max_m: float = 0.0
    #: Budgets: labels popped and wall seconds. Either one refuses with ``stopped`` set — a
    #: budget, not a proof. A refusal must come back in seconds, not CPU minutes.
    max_labels: int = 1_000_000
    max_seconds: float = 45.0



@dataclass
class DuctRefusal:
    """Why no fitted route was found — ``route_diagnose.refuse``'s report shape."""

    reached: int = 0
    #: Turns refused because the straight behind them was short of the take-offs.
    short_turns: int = 0
    #: Steps refused because they would cross the route's own lane to buy straight.
    loops: int = 0
    #: Which budget stopped the search ("labels" | "seconds"), or None if it ran out.
    stopped: str | None = None
    takeoff_in: float = 0.0
    tightest: tuple[str, float] | None = None
    notes: list[str] = field(default_factory=list)
    takeoffs: list = field(default_factory=list)

    def sentence(self) -> str:
        head = (f"no fitted duct route: {self.reached:,} label(s) expanded, "
                f"{self.short_turns:,} turn(s) refused for want of the "
                f'{2 * self.takeoff_in:.2f}" two elbows take between them')
        if self.tightest is not None:
            what, short = self.tightest
            head += f'; the tightest was {what}, short {short:.3f}"'
        if self.loops:
            head += f"; {self.loops:,} step(s) refused for crossing the route's own lane"
        return head + (". " + " ".join(self.notes) if self.notes else "")


@dataclass
class FittedRoute(Route):
    """A route whose points may hold an oblique offset leg; ``nodes`` stay the lattice's."""

    offsets: int = 0

    def polyline(self) -> list[Point3]:
        """The points with collinear interior vertices removed, by direction, not axis."""
        out = [self.points[0]]
        for a, b, c in zip(self.points, self.points[1:], self.points[2:], strict=False):
            if not _collinear(a, b, c):
                out.append(b)
        return [*out, self.points[-1]] if len(self.points) > 1 else out


class _Label(NamedTuple):
    cost: float
    slack: float
    heading: str
    #: The open corner while the leg after it is short: its node, the heading before it,
    #: and the slack held there (an offset's first elbow needs its take-off). -1: closed.
    corner: int = -1
    before: str = ""
    pre: float = 0.0
    provisional: bool = False
    #: The route's finished legs and where the current one began: a step that touches an
    #: earlier leg is refused, so no label ever loops (and none can prune one that does
    #: not). Not part of dominance.
    legs: tuple[tuple[float, ...], ...] = ()
    start: Point3 = (0.0, 0.0, 0.0)


def fitted_route(graph: Graph, space: RoutingSpace, start: int, goals: set[int],
                 problem: DuctFittingProblem, *,
                 refusal: DuctRefusal | None = None) -> Route | None:
    """The cheapest route whose every straight holds the take-offs at its ends, or None."""
    report = refusal if refusal is not None else DuctRefusal()
    report.takeoff_in = problem.takeoff_m / M_PER_IN
    if start in goals:
        node = graph.nodes[start]
        return Route(nodes=[start], points=[(node.x, node.y, node.z)], cost=0.0)
    if not goals:
        return None
    heuristic = _turning_heuristic(graph, space, goals, problem.fabricated_in)
    take = problem.takeoff_m
    least = min((t for _a, t in problem.offsets), default=take)
    jog_max = problem.offset_jog_max_m
    frontier: dict[tuple, list[tuple[_Label, int]]] = {}
    alive: dict[int, tuple[int, _Label]] = {}
    came: dict[int, int] = {}
    node_of: dict[int, int] = {}
    slid: dict[int, tuple[int, int, Point3, float]] = {}  # id -> offset geometry
    open_heap: list[tuple[float, int, int, int]] = []
    clear: dict[tuple, bool] = {}  # an offset leg's clearance, per corner pair and slide
    counter = 0

    def push(node: int, label: _Label, parent: int | None,
             offset: tuple[int, int, Point3, float] | None = None) -> None:
        nonlocal counter
        label = _closed(label, take)
        kept = frontier.setdefault((node, label.heading, label.corner, label.before), [])
        pruned = False
        for other, lid in kept:
            if _dominates(other, label):
                return
            if _dominates(label, other):
                alive.pop(lid, None)
                pruned = True
        if pruned:
            kept[:] = [entry for entry in kept if entry[1] in alive]
        counter += 1
        kept.append((label, counter))
        alive[counter] = (node, label)
        node_of[counter] = node
        if parent is not None:
            came[counter] = parent
        if offset is not None:
            slid[counter] = offset
        heapq.heappush(open_heap, (label.cost + heuristic(node, label.heading), node,
                                   _AXIS_ORDER.get(label.heading[-1:], -1), counter))

    origin = graph.nodes[start]
    push(start, _Label(0.0, 0.0, problem.start_axis,
                       start=(origin.x, origin.y, origin.z)), None)
    clock = time.monotonic()
    expanded = 0  # this search's own count: `report` may be shared across alternatives
    while open_heap:
        _f, index, _key, lid = heapq.heappop(open_heap)
        if lid not in alive:
            continue  # dominated after it was pushed
        label = alive[lid][1]
        report.reached += 1
        expanded += 1
        stopped = ("labels" if expanded > problem.max_labels else
                   "seconds" if expanded % 4096 == 0
                   and time.monotonic() - clock > problem.max_seconds else None)
        if stopped is not None:
            report.stopped = stopped
            report.notes.append(
                f"the search stopped at its {problem.max_labels:,}-label budget" if
                stopped == "labels" else
                f"the search stopped at its {problem.max_seconds:g} s budget")
            report.notes[-1] += " with no fitted arrival: a budget, not a proof"
            return None
        if index in goals and not label.provisional:
            if label.slack < -_TOL_M:
                _tight(report, "the last straight into the run's end", -label.slack)
            elif problem.goal_axis and label.heading != problem.goal_axis:
                _tight(report, "the arrival across a port lead", 0.0)
            else:
                return _rebuild(graph, space, came, node_of, slid, lid, problem,
                                expanded)
        incoming = label.heading
        for other, axis in graph.neighbours(index):
            step = graph.weights.get((index, other))
            if step is None:
                continue
            step += _bore_premium(graph.terms.get((index, other)))
            a, b = graph.nodes[index], graph.nodes[other]
            delta = (b.x - a.x, b.y - a.y, b.z - a.z)[_INDEX[axis]]
            heading = ("+" if delta > 0 else "-") + axis
            leg = abs(delta)
            if incoming[-1:] == axis and heading != incoming:
                continue  # a reversal: no fitting turns 180 degrees in place
            here, there = (a.x, a.y, a.z), (b.x, b.y, b.z)
            if not incoming or axis == incoming[-1]:
                if label.provisional and label.slack + take + leg > jog_max + _TOL_M:
                    continue  # past the longest jog an offset is drawn for
                if label.legs and _touches(here, there, label.legs, 1):
                    report.loops += 1
                    continue
                push(other, _Label(label.cost + step, label.slack + leg, heading,
                                   label.corner, label.before, label.pre,
                                   label.provisional, label.legs, label.start), lid)
                continue
            if label.legs and _touches(here, there, label.legs, 0):
                report.loops += 1
                continue
            legs = (*label.legs, _box(label.start, here))
            turn = (bend_price(graph, space, None, index, other, heading=incoming)
                    + problem.fabricated_in)
            cost = label.cost + step + turn
            if label.corner >= 0 and heading == label.before:
                made = _offset(graph, space, problem, label, index, heading, clear)
                if made is not None:
                    debt, slide = made
                    push(other, _Label(cost, leg - debt, heading, legs=legs, start=here),
                         lid, slide)
                    continue
            if label.provisional:
                continue
            if label.slack >= take - _TOL_M:
                rise = axis == "z" and bool(problem.offsets)  # a rise may close as an offset
                push(other, _Label(cost, leg - take, heading, index if rise else -1,
                                   incoming if rise else "", label.slack if rise else 0.0,
                                   legs=legs, start=here), lid)
            elif axis == "z" and problem.offsets and label.slack >= least - _TOL_M:
                push(other, _Label(cost, leg - take, heading, index, incoming,
                                   label.slack, True, legs, here), lid)
            else:
                report.short_turns += 1
                _tight(report, "a turn after too short a straight", take - label.slack)
    return None


def _turning_heuristic(graph: Graph, space: RoutingSpace, goals: set[int],
                       premium: float):
    """``(node, heading) -> h``: ``search``'s estimate plus the turns still owed, priced at
    the cheapest a turn can be. Memoised; vectorised over the goals."""
    base = _heuristic(graph, space, goals)
    bend = space.cost.bend_in if space.bend_radius_m <= 0.0 else min(
        space.cost.bend_in, space.cost.pex_bend_in)
    bend += premium
    where = np.array([(graph.nodes[g].x, graph.nodes[g].y, graph.nodes[g].z) for g in goals])
    memo: dict[tuple[int, str], float] = {}

    def estimate(index: int, heading: str) -> float:
        key = (index, heading)
        hit = memo.get(key)
        if hit is None:
            node = graph.nodes[index]
            moves = (where - (node.x, node.y, node.z)) > _TOL_M
            back = (where - (node.x, node.y, node.z)) < -_TOL_M
            needed = (moves | back)
            if not heading:
                turns = np.maximum(needed.sum(axis=1) - 1, 0)
            else:
                axis = _INDEX[heading[-1]]
                off = needed.sum(axis=1) - needed[:, axis]
                behind = (back if heading[0] == "+" else moves)[:, axis]
                turns = off + behind + (behind & (off == 0))  # U-turn: two
            hit = base(index) + bend * float(turns.min())
            memo[key] = hit
        return hit

    return estimate


def _bore_premium(terms: dict | None) -> float:
    """What a duct pays on top of the lattice's price for the bores on one edge."""
    if not terms:
        return 0.0
    return (DUCT_BORE_FACTOR - 1.0) * sum(terms.get(key, 0.0) for key in _DUCT_CUTS)


def _closed(label: _Label, take: float) -> _Label:
    """Cap the slack at one 90's take-off; close the corner once the leg after it holds
    one: past that every label has the same future."""
    if label.corner >= 0 and not label.provisional and label.slack >= take - 1e-12:
        return _Label(label.cost, take, label.heading, legs=label.legs, start=label.start)
    if label.slack > take:
        return _Label(label.cost, take, label.heading, label.corner, label.before,
                      label.pre, label.provisional, label.legs, label.start)
    return label


def _dominates(first: _Label, second: _Label) -> bool:
    """No dearer, no less slack or straight behind the corner, no more provisional. Slack is
    compared on the 1/16" grid the proposal snaps to: closer is one label, and every label
    keeps its own true slack, so this prunes near-ties without admitting a short turn."""
    return (first.cost <= second.cost + 1e-12 and first.slack >= second.slack - _TOL_M
            and first.pre >= second.pre - _TOL_M
            and (second.provisional or not first.provisional))


def _box(a: Point3, b: Point3) -> tuple[float, ...]:
    """An axis-aligned leg as ``(x0, x1, y0, y1, z0, z1)``."""
    return (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]),
            min(a[2], b[2]), max(a[2], b[2]))


def _touches(a: Point3, b: Point3, legs: tuple[tuple[float, ...], ...], skip: int) -> bool:
    """Whether the axis-aligned step ``a``-``b`` meets any of ``legs`` but the last ``skip``
    (two axis-aligned segments meet exactly when their boxes do). Unrolled: it is the
    search's innermost test."""
    x0, x1, y0, y1, z0, z1 = _box(a, b)
    e = 1e-9
    for k in range(len(legs) - skip):
        lx0, lx1, ly0, ly1, lz0, lz1 = legs[k]
        if (x0 <= lx1 + e and lx0 <= x1 + e and y0 <= ly1 + e and ly0 <= y1 + e
                and z0 <= lz1 + e and lz0 <= z1 + e):
            return True
    return False


def _offset(graph: Graph, space: RoutingSpace, problem: DuctFittingProblem, label: _Label,
            at: int, heading: str, clear: dict) -> tuple[float, tuple[int, int, Point3, float]
                                                         ] | None:
    """``(debt, (corner, far corner, slid far corner, h))`` for the jog ending at ``at``
    laid as an offset, or None: the slid corner is ``h`` on along ``heading``."""
    jog = label.slack + problem.takeoff_m
    if jog <= _TOL_M or jog > problem.offset_jog_max_m + _TOL_M:
        return None
    p, q = graph.nodes[label.corner], graph.nodes[at]
    sign = 1.0 if heading[0] == "+" else -1.0
    axis = _INDEX[heading[-1]]
    for theta, theta_take in problem.offsets:
        h = jog / math.tan(math.radians(theta))
        if (jog / math.sin(math.radians(theta)) + _TOL_M < 2.0 * theta_take
                or label.pre + _TOL_M < theta_take):
            continue
        slide = [q.x, q.y, q.z]
        slide[axis] += sign * h
        key = (label.corner, at, heading, round(h, 6))
        if key not in clear:
            clear[key] = space.edge_blocked((p.x, p.y), (slide[0], slide[1]), p.z,
                                            slide[2]) is None
        if clear[key]:
            return h + theta_take, (label.corner, at, (slide[0], slide[1], slide[2]), h)
    return None


def _tight(report: DuctRefusal, what: str, short_m: float) -> None:
    short = short_m / M_PER_IN
    if report.tightest is None or short < report.tightest[1]:
        report.tightest = (what, short)


def _rebuild(graph: Graph, space: RoutingSpace, came: dict[int, int],
             node_of: dict[int, int], slid: dict[int, tuple[int, int, Point3, float]], lid: int,
             problem: DuctFittingProblem, expansions: int) -> Route:
    chain = [lid]
    while chain[-1] in came:
        chain.append(came[chain[-1]])
    chain.reverse()
    nodes = [node_of[i] for i in chain]
    found = price_route(graph, space, nodes)
    points = list(found.points)
    # Latest first, so earlier indices hold. The far corner is the label's parent node.
    for position in sorted((k for k, i in enumerate(chain) if i in slid), reverse=True):
        corner, _far, point, h = slid[chain[position]]
        far = position - 1
        near = max(k for k in range(far) if nodes[k] == corner)
        # Drop the jog's interior and what lies between the far corner and its slid place;
        # ``nodes`` stay the lattice's chain, only the geometry slides.
        resume = position
        while resume < len(points) and math.dist(points[resume], points[far]) <= h + 1e-9:
            resume += 1  # the straight beyond holds h + t, so these are all on it
        points = [*points[:near + 1], point, *points[resume:]]
    cost, terms = found.cost, dict(found.terms)
    bores = sum(_bore_premium(graph.terms.get(edge))
                for edge in zip(nodes, nodes[1:], strict=False))
    if bores:
        cost += bores
        terms["duct_bore_in"] = bores
    if problem.fabricated_in and found.bends:
        cost += problem.fabricated_in * found.bends
        terms["fabricated_elbow_in"] = problem.fabricated_in * found.bends
    return FittedRoute(nodes=found.nodes, points=points, cost=cost, terms=terms,
                       bends=found.bends, expansions=expansions,
                       corridor_tags=found.corridor_tags, offsets=len(
                           [i for i in chain if i in slid]))


def _collinear(a: Point3, b: Point3, c: Point3) -> bool:
    ab = [y - x for x, y in zip(a, b, strict=True)]
    bc = [y - x for x, y in zip(b, c, strict=True)]
    cross = (ab[1] * bc[2] - ab[2] * bc[1], ab[2] * bc[0] - ab[0] * bc[2],
             ab[0] * bc[1] - ab[1] * bc[0])
    scale = (math.hypot(*ab) * math.hypot(*bc)) or 1.0
    return all(abs(v) / scale < 1e-9 for v in cross) and sum(
        p * q for p, q in zip(ab, bc, strict=True)) > 0

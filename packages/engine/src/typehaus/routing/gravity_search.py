"""A drain searched where it actually falls, not searched flat and lowered afterwards.

**What this replaces.** ``gravity.py`` gives a drain its elevations from a monotone
potential — ``invert = ceiling − slope × developed`` — and the CLI applied that *after* the
plan route was found. The search therefore knew nothing about the run's real height at any
point on the way: a lane could be chosen because it was cheap, and only the profile
afterwards would discover that the invert at its third bend was six inches inside a truss
chord. The refusal, when it came, named a head budget rather than the crossing that broke
it, and a route that would have fitted one bay over was never offered.

**The insight that makes it cheap.** The invert is a function of *developed length alone*,
so a search state that already carries "how far have I come" carries everything the
elevation needs. Put the developed length in the label and every constraint on the run's
height becomes testable at relaxation time, where it can actually steer the search.

**What the label carries is a BAND, not a height.** The run does not have to start at the
ceiling — ``gravity.profile_for`` deliberately builds the profile from the arrival *upward*,
because head spent early is head unavailable to whatever ties in downstream — so the real
question at a truss is not "does the ceiling-anchored profile fit" but "is there ANY legal
start elevation that fits here and everywhere else". Every constraint is linear in the start
elevation, so the set of legal starts is an interval, and a label carries it: a member window
``[w0, w1]`` at developed ``d`` says ``start ∈ [w0 + r + slope·d, w1 − r + slope·d]``, and a
tie at ``required`` says ``start ≥ required + slope·D``. Intersect as you go; empty is a
refusal, and the number to report is how far the intersection missed by.

Anchoring at the ceiling instead reports a route infeasible because a pipe that nobody would
build there does not fit — which is a true statement about the wrong run.

**Label-setting, with a Pareto frontier per state.** A label is
``(node, incoming axis, developed_ft, start band)`` with cost ``g``. At one ``(node, axis)``
a label dominates another when its cost is no greater, its developed length is no greater
**and** its band of legal starts is no narrower: cheaper is better, shorter is better and
more room is better, and none of the three implies the others on a weighted lattice — a
corridor discount buys length with money, and a detour round a truss buys head with length.
So a state keeps a frontier rather than a single best, which is what the extra dimensions
cost.

**Why dominance is valid.** Every constraint tested here is monotone in the invert once the
start ceiling is fixed: a longer route arrives lower, and lower is worse at a member window
and worse at a goal. So a label that is both cheaper and shorter can never be beaten later.

**The one non-monotone case, stated rather than papered over.** An existing run's prism is
NOT monotone — a longer route arrives lower and could in principle dive *under* the thing in
the way. Those are handled where the lattice is built, conservatively, as blocking anywhere
in the drain's possible band, and the refusal says so. A drain is not lengthened to slip
under a duct; a person decides that.

**Rises never.** A vertical edge downward lowers the ceiling for the remainder of the route
(a drop is free fall and takes no grade). A vertical edge upward is not relaxed at all.

``houses/catlin/notes/mep_drain_routing_basis.md`` §8 is the hand-worked oracle.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field

from typehaus.quantities import M_PER_IN
from typehaus.routing.graph import Graph
from typehaus.routing.search import Route, price_route
from typehaus.routing.space import RoutingSpace

#: Axis ordering for the tie-break, lowest first — the same table ``search.py`` states, and
#: for the same reason: without it A* is non-deterministic and no oracle can pin it.
_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}

#: A sixteenth of an inch of slop on every elevation comparison. Coordinates in this repo
#: are authored on that grid, and a window test that refused a run by 1e-12 of a metre would
#: be reporting float noise as a defect.
_TOL_M = 0.0015875 / 16.0

#: ``(low, high)`` the run's CENTRELINE may occupy at a fraction along one edge.
Window = tuple[float, float, float]

#: ``(from, to) -> the windows on that edge``. Lazily consulted, once per edge relaxed.
Constraints = Callable[[int, int], "list[Window]"]


@dataclass(frozen=True)
class GravityProblem:
    """Everything the elevation of a falling run depends on.

    ``required_m`` is **per goal node** rather than one number: a branch may tie onto the
    main at one invert and onto a branch already accepted at another, and grading it against
    the wrong one reads a tie twelve feet away and calls a route feasible that is not.
    """

    ceiling_m: float
    grade_in_per_ft: float
    diameter_m: float
    required_m: dict[int, float]

    def fall_over(self, developed_ft: float) -> float:
        """Metres of fall over this developed plan length, at this grade."""
        return developed_ft * self.grade_in_per_ft * M_PER_IN

    def invert_at(self, developed_ft: float, start_m: float | None = None) -> float:
        """Where the centreline sits this far along, from a given start elevation.

        Defaults to starting at the ceiling, which is the HIGHEST the run may be and is what
        §8's hand arithmetic quotes. The search itself carries a band and settles the start
        at the end; this is the reading a note or a refusal message uses.
        """
        return (self.ceiling_m if start_m is None else start_m) - self.fall_over(
            developed_ft)


@dataclass
class _Label:
    """One state's cost, its developed length, and the starts still open to it.

    ``lo_m``/``hi_m`` bound the elevation the run may START at and still satisfy every
    constraint met so far. ``drop_m`` is the free fall already taken by vertical legs, which
    shifts the whole profile down without spending any grade.
    """

    cost: float
    developed_ft: float
    lo_m: float
    hi_m: float
    drop_m: float = 0.0


@dataclass
class GravityRefusal:
    """Why no route fell. Every field is a number a person can act on.

    "No feasible route" is not actionable. "It ran out of head 14 ft in, at the truss line
    on FS-S-WEST, by 0.44 inches" is — and it is also how a caller knows whether to move the
    fixture, lower the tie or take the other lane.
    """

    reached: int = 0
    #: The deepest a label got, in developed feet, before every continuation was refused.
    furthest_ft: float = 0.0
    #: ``(what, shortfall in inches)`` for the tightest refusal seen.
    tightest: tuple[str, float] | None = None
    notes: list[str] = field(default_factory=list)

    def sentence(self) -> str:
        head = (f"no route falls: {self.reached:,} label(s) expanded, the furthest reaching "
                f"{self.furthest_ft:.2f} ft of developed run")
        if self.tightest is not None:
            what, short = self.tightest
            head += f'; the tightest refusal was {what}, short {short:.3f}"'
        return head + (". " + " ".join(self.notes) if self.notes else "")


def sloped_route(graph: Graph, space: RoutingSpace, start: int, goals: set[int],
                 problem: GravityProblem, *, constraints: Constraints | None = None,
                 refusal: GravityRefusal | None = None) -> Route | None:
    """The cheapest route whose invert is legal at every point along it, or None.

    The head budget is the **goal test**, not a post-check: a label arriving at a goal below
    that goal's own required invert is not a route that later fails, it is not a route.
    """
    if start in goals and problem.ceiling_m >= problem.required_m[start] - _TOL_M:
        node = graph.nodes[start]
        return Route(nodes=[start], points=[(node.x, node.y, node.z)], cost=0.0)

    report = refusal if refusal is not None else GravityRefusal()
    heuristic = _heuristic(graph, space, goals)
    frontier: dict[tuple[int, str], list[_Label]] = {}
    came: dict[tuple[int, str, int], tuple[int, str, int]] = {}
    counter = 0
    open_heap: list[tuple[float, int, int, float, int, str, float, int]] = []

    def push(node: int, axis: str, label: _Label, parent) -> None:
        nonlocal counter
        key = (node, axis)
        kept = frontier.setdefault(key, [])
        for other in kept:
            if _dominates(other, label):
                return
        kept[:] = [o for o in kept if not _dominates(label, o)]
        kept.append(label)
        slot = len(kept) - 1
        counter += 1
        if parent is not None:
            came[(node, axis, slot)] = parent
        heapq.heappush(open_heap, (label.cost + heuristic(node), node,
                                   _AXIS_ORDER[axis], label.developed_ft, counter, axis,
                                   label.cost, slot))

    for axis in ("x", "y", "z"):
        push(start, axis, _Label(0.0, 0.0, float("-inf"), problem.ceiling_m), None)

    while open_heap:
        (_f, index, _axis_key, developed, _seq, incoming, cost,
         slot) = heapq.heappop(open_heap)
        kept = frontier.get((index, incoming), ())
        if slot >= len(kept) or kept[slot].cost != cost:
            continue  # superseded by a label that dominated this one after it was pushed
        label = kept[slot]
        report.reached += 1
        report.furthest_ft = max(report.furthest_ft, developed)

        if index in goals:
            required = problem.required_m.get(index)
            # The tie is a FLOOR on the start: arriving at or above ``required`` after
            # falling ``slope x D`` and dropping ``drop`` means starting at least that high.
            floor_m = (float("-inf") if required is None
                       else required + problem.fall_over(developed) + label.drop_m)
            if floor_m <= label.hi_m + _TOL_M:
                return _rebuild(graph, space, came, (index, incoming, slot))
            _note(report, f"the tie at node {index}", (floor_m - label.hi_m) / M_PER_IN)
            # Not a dead end: a longer route arrives LOWER, so nothing past here helps at
            # this goal — but another goal on the same stack may still accept it.

        for other, axis in graph.neighbours(index):
            step = graph.weights.get((index, other))
            if step is None:
                continue
            node, target = graph.nodes[index], graph.nodes[other]
            rise = target.z - node.z
            if axis == "z" and rise > _TOL_M:
                # **Rises never.** A drain falls; a lattice edge upward is not a lane.
                continue
            # A vertical leg is FREE FALL: it drops the whole profile without spending any
            # grade, so it shifts the invert rather than the start band.
            next_drop = label.drop_m + (-min(rise, 0.0) if axis == "z" else 0.0)
            plan_ft = (abs(target.x - node.x) + abs(target.y - node.y)) / 0.3048
            band = _edge_band(problem, constraints, index, other, developed, plan_ft,
                              next_drop, label, report)
            if band is None:
                continue
            turn = space.cost.bend_in if incoming and axis != incoming else 0.0
            push(other, axis,
                 _Label(cost + step + turn, developed + plan_ft, band[0], band[1],
                        next_drop),
                 (index, incoming, slot))
    return None


def _dominates(first: _Label, second: _Label) -> bool:
    """Is ``first`` at least as good as ``second`` in every dimension?

    Cheaper, shorter, and with a band of legal starts that contains the other's. All three,
    because none implies the others: a corridor discount buys length with money and a detour
    round a truss buys head with length.
    """
    return (first.cost <= second.cost + 1e-12
            and first.developed_ft <= second.developed_ft + 1e-12
            and first.lo_m <= second.lo_m + _TOL_M
            and first.hi_m >= second.hi_m - _TOL_M)


def _edge_band(problem: GravityProblem, constraints: Constraints | None,
               a: int, b: int, developed_ft: float, plan_ft: float, drop_m: float,
               label: _Label, report: GravityRefusal
               ) -> tuple[float, float] | None:
    """The band of legal start elevations after crossing this edge, or None if it is empty.

    **Tested at the station, not over the leg.** A leg's high end may sit in a clear bay with
    no member in it at all; banding the whole leg against the tightest window on it is the
    shortcut that produced three false FAILs in ``mep.run_member_crossing`` and would produce
    them here as refusals, which is worse — a refusal cannot be argued with after the fact.
    """
    low, high = label.lo_m, label.hi_m
    if constraints is None:
        return (low, high)
    radius = problem.diameter_m / 2.0
    for fraction, window_low, window_high in constraints(a, b):
        shift = problem.fall_over(developed_ft + fraction * plan_ft) + drop_m
        # invert = start - shift, and the run's OUTSIDE has to fit the window:
        #     window_low <= start - shift - radius  and  start - shift + radius <= window_high
        need_low = window_low + radius + shift
        need_high = window_high - radius + shift
        if need_high < need_low - _TOL_M:
            _note(report, "a member window too shallow for this pipe",
                  (need_low - need_high) / M_PER_IN)
            return None
        low, high = max(low, need_low), min(high, need_high)
        if high < low - _TOL_M:
            _note(report, "a member window", (low - high) / M_PER_IN)
            return None
    return (low, high)


def _note(report: GravityRefusal, what: str, shortfall_in: float) -> None:
    if report.tightest is None or shortfall_in < report.tightest[1]:
        report.tightest = (what, shortfall_in)


def _heuristic(graph: Graph, space: RoutingSpace,
               goals: set[int]) -> Callable[[int], float]:
    """Manhattan plan + ``|Δz| × riser_per_ft``, scaled by the cost's own cheapest inch.

    Identical to ``search._heuristic`` and deliberately so: every penalty in ``cost.py`` is
    additive and non-negative and the one discount is capped, so this never over-estimates.
    A heuristic that also guessed at the head would stop A* being optimal without saying so.
    """
    floor = space.cost.heuristic_floor()
    riser = space.cost.riser_per_ft
    targets = [(graph.nodes[g].x, graph.nodes[g].y, graph.nodes[g].z) for g in goals]

    def estimate(index: int) -> float:
        node = graph.nodes[index]
        return min(((abs(node.x - gx) + abs(node.y - gy)) / 0.3048 * 12.0
                    + abs(node.z - gz) / 0.3048 * 12.0 * riser) * floor
                   for gx, gy, gz in targets)

    return estimate


def _rebuild(graph: Graph, space: RoutingSpace,
             came: dict[tuple[int, str, int], tuple[int, str, int]],
             state: tuple[int, str, int]) -> Route:
    chain = [state]
    while state in came:
        state = came[state]
        chain.append(state)
    chain.reverse()
    return price_route(graph, space, [index for index, _axis, _slot in chain])


def member_constraints(model, graph: Graph,
                       band: tuple[float, float] | None = None) -> Constraints:
    """The crossing windows every lattice edge meets, as a lazily-cached lookup.

    One entry per member the edge crosses: where along the edge, and the band that member's
    section gives the run's centreline. The band is ``resolve/mep_crossings.member_window``
    — the same three readings ``mep.run_member_crossing`` grades against — so a route this
    search accepts is a route that check will pass, which is the whole point of putting the
    constraint in the search rather than after it.

    ``band`` is the elevations this run can possibly occupy — its tie at the bottom, its
    ceiling at the top — and **it is not an optimisation.** A floor whose window lies wholly
    outside that band cannot constrain this run, and including it is not conservative, it is
    wrong: ``leg_crossings`` is probed at each floor's OWN window middle (the run's real z
    being exactly what is not yet known), so every floor in the model answers "yes, a run in
    me would meet this member" and a second-floor branch comes back refused by 112 inches
    against a basement joist. Omitting the band is only safe when the model has one floor.

    **Cached per undirected edge and reversed on the way back.** The same edge is relaxed
    from both ends and the geometry does not change between them, but the *fraction* does:
    a crossing a quarter of the way along A→B is three quarters of the way along B→A, and
    the developed length at it differs by half the edge. Getting that backwards would test
    the invert at the wrong station.
    """
    from typehaus.resolve.mep_crossings import leg_crossings, member_window

    floors = [(floor, member_window(floor)) for floor in model.floors]
    floors = [(floor, window) for floor, window in floors
              if window is not None
              and (band is None
                   or (window.z0_m <= band[1] and window.z1_m >= band[0]))]
    cache: dict[tuple[int, int], list[Window]] = {}

    def constraints(a: int, b: int) -> list[Window]:
        key = (a, b) if a < b else (b, a)
        found = cache.get(key)
        if found is None:
            first, second = graph.nodes[key[0]], graph.nodes[key[1]]
            found = []
            for floor, window in floors:
                # The z handed to `leg_crossings` is the window's own middle: the function
                # also tests that the run is INSIDE the floor's depth rather than passing
                # over or under it, and at search time the run's real z is exactly what is
                # not yet known. The middle is the honest probe — it asks "would a run in
                # this floor meet this member", which is the question.
                middle = (window.z0_m + window.z1_m) / 2.0
                for crossing in leg_crossings(floor, (first.x, first.y),
                                              (second.x, second.y), middle, middle):
                    found.append((crossing.t, window.z0_m, window.z1_m))
            cache[key] = found
        if a < b:
            return found
        return [(1.0 - t, low, high) for t, low, high in found]

    return constraints

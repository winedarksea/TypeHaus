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

**The one non-monotone case.** A prism that spans only part of the run's band is NOT
monotone — the run may pass over it or under it. ``gravity_band`` turns each into a
forbidden interval of start elevations per edge, and a label whose band it splits becomes
two, an "under" and an "over" (§8a).

**Rises never.** A vertical edge downward lowers the ceiling for the remainder of the route
(a drop is free fall and takes no grade). A vertical edge upward is not relaxed at all.

``houses/catlin/notes/mep_drain_routing_basis.md`` §8 is the hand-worked oracle.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from typehaus.quantities import M_PER_IN
from typehaus.routing.fitting_room import heel_clear
from typehaus.routing.graph import Graph
from typehaus.routing.gravity import drop_blocker, grid_allowance, head_floor_fn
from typehaus.routing.gravity_band import Obstacles, subtract
from typehaus.routing.search import Route, price_route, turn_price
from typehaus.routing.space import RoutingSpace

#: Axis ordering for the tie-break, as ``search.py``: without it A* is non-deterministic.
_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}

#: A sixteenth of slop on every elevation comparison: the repo's authoring grid, not noise.
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
    #: The run's real OUTSIDE (OD plus lagging), which is what a member window must hold.
    diameter_m: float
    required_m: dict[int, float]
    #: ``routing/fitting_room``: the least straight between two turns, and how far behind a
    #: corner the hub and its tool reach. Zero leaves the lattice to decide (§8's worlds).
    nipple_m: float = 0.0
    heel_m: float = 0.0
    #: UPC 1002.2, a fixture's arm (``routing/trap_vent.arm_seeds``): ``node -> (cost,
    #: developed ft, the arm's nodes)`` for each take-off the arm reaches, its cost
    #: carrying that take-off's ``h_vent``. The search starts from these and not ``start``;
    #: an empty dict is an arm with nowhere to close. None: no arm.
    seeds: dict[int, tuple[float, float, tuple[int, ...]]] | None = None
    #: Labels expanded before the search gives up: an unreachable goal walks every front.
    max_labels: int = 1_500_000

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
    #: Straight run since the last fitting; the start is a trap's outlet, not a turn.
    since_m: float = float("inf")
    #: The take-off this label's arm closed at (a seed), or -1.
    takeoff: int = -1


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
                 refusal: GravityRefusal | None = None,
                 obstacles: Obstacles | None = None) -> Route | None:
    """The cheapest route whose invert is legal at every point along it, or None.

    The head budget is the **goal test**, not a post-check: a label arriving at a goal below
    that goal's own required invert is not a route that later fails, it is not a route.
    """
    if start in goals and problem.ceiling_m >= problem.required_m[start] - _TOL_M:
        node = graph.nodes[start]
        return Route(nodes=[start], points=[(node.x, node.y, node.z)], cost=0.0)

    report = refusal if refusal is not None else GravityRefusal()
    heuristic = _heuristic(graph, space, goals)
    head_floor = head_floor_fn(graph, goals, problem.required_m, problem.grade_in_per_ft)
    # Labels have stable ids, not frontier slots: pruning shifts slots.
    frontier: dict[tuple[int, str], list[tuple[_Label, int]]] = {}
    alive: dict[int, tuple[int, str, _Label]] = {}
    came: dict[int, int] = {}
    node_of: dict[int, int] = {}  # every label ever pushed, never pruned: for the rebuild
    counter = 0
    open_heap: list[tuple[float, int, int, float, int, str, float, int]] = []
    heels: dict[tuple[int, int, int], bool] = {}  # a corner's heel is geometry: once each
    expanded = 0  # this call's labels; ``report`` may be shared by a tree's searches

    def push(node: int, axis: str, label: _Label, parent: int | None) -> None:
        nonlocal counter
        key = (node, axis)
        kept = frontier.setdefault(key, [])
        pruned = False  # one pass: a Pareto-clean frontier cannot both dominate and lose
        for other, lid in kept:
            if _dominates(other, label, problem.nipple_m):
                return
            if _dominates(label, other, problem.nipple_m):
                alive.pop(lid, None)
                pruned = True
        if pruned:
            kept[:] = [(o, lid) for o, lid in kept if lid in alive]
        counter += 1
        kept.append((label, counter))
        alive[counter] = (node, axis, label)
        node_of[counter] = node
        if parent is not None:
            came[counter] = parent
        heapq.heappush(open_heap, (label.cost + heuristic(node), node,
                                   _AXIS_ORDER[axis], label.developed_ft, counter, axis,
                                   label.cost, counter))

    seeds = {start: (0.0, 0.0, (start,))} if problem.seeds is None else problem.seeds
    for node, (seed_cost, seed_ft, _arm) in sorted(seeds.items()):
        for axis in ("x", "y", "z"):
            push(node, axis, _Label(seed_cost, seed_ft, float("-inf"), problem.ceiling_m,
                                    takeoff=-1 if problem.seeds is None else node), None)

    while open_heap:
        (_f, index, _axis_key, developed, _seq, incoming, cost,
         lid) = heapq.heappop(open_heap)
        if lid not in alive:
            continue  # superseded by a label that dominated this one after it was pushed
        label = alive[lid][2]
        report.reached += 1
        expanded += 1
        if expanded > problem.max_labels:
            report.notes.append(f"the search stopped after {problem.max_labels:,} labels "
                                "with no legal arrival: a budget, not a proof")
            return None
        report.furthest_ft = max(report.furthest_ft, developed)

        required = problem.required_m.get(index)
        if index in goals and required is not None:  # an unknown invert grades nothing
            # The tie is a FLOOR on the start: required + slope x D + drop.
            floor_m = required + problem.fall_over(developed) + label.drop_m
            if floor_m <= label.hi_m + _TOL_M:
                found = _rebuild(graph, space, came, node_of, lid, seeds, label.takeoff)
                # The 1/16" snap rounds each leg's fall UP (``route_fall._on_grid``).
                snapped = floor_m + grid_allowance(found, problem.grade_in_per_ft,
                                                    required)
                start_m = max(floor_m, label.lo_m)  # over an obstacle: its band's floor
                blocker = drop_blocker(obstacles, index, start_m - floor_m + required,
                                       required)
                if snapped <= label.hi_m + _TOL_M and blocker is None:
                    found.start_m = start_m
                    return found
                if blocker is not None:
                    _note(report, f"{blocker} across the drop into the tie", 0.0)
                else:
                    _note(report, f"the tie at node {index}",
                          (snapped - label.hi_m) / M_PER_IN)
            else:
                _note(report, f"the tie at node {index}", (floor_m - label.hi_m) / M_PER_IN)
            # Not a dead end: another goal on the same stack may still accept it.

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
            turn = turn_price(space, incoming, axis)
            if turn is None:
                continue
            leg_m = plan_ft * 0.3048 if axis != "z" else -rise
            if turn and not _fitting_fits(graph, space, problem, label, came, node_of,
                                          lid, index, other, heels):
                continue
            since = leg_m if turn else label.since_m + leg_m
            # §13: no start in the band can still reach any tie, at grade, by plan distance.
            floor_m = head_floor(other) + problem.fall_over(developed + plan_ft) + next_drop
            for low, high in _clear_of(obstacles, problem, index, other, developed,
                                       plan_ft, label.drop_m, next_drop, band, report):
                if high + _TOL_M < floor_m:
                    _note(report, "the head to any tie", (floor_m - high) / M_PER_IN)
                    continue
                push(other, axis,
                     _Label(cost + step + turn, developed + plan_ft, low, high, next_drop,
                            since, label.takeoff), lid)
    return None


#: Bands compared on the 1/16" grid the profile is snapped to (``route_fall._on_grid``):
#: two starts closer than that are one start, and 1/256" kept 1,300 labels on one state.
_BAND_GRID_M = 0.0015875


def _dominates(first: _Label, second: _Label, nipple_m: float = 0.0) -> bool:
    """Is ``first`` at least as good as ``second`` in every dimension?

    Cheaper, shorter, and with a band of legal starts that contains the other's. All three,
    because none implies the others: a corridor discount buys length with money and a detour
    round a truss buys head with length.
    """
    return (first.cost <= second.cost + 1e-12
            and first.developed_ft <= second.developed_ft + 1e-12
            # ``nipple_ok`` as a flag, never the length: at most two labels per state.
            and (first.since_m >= nipple_m - _TOL_M or second.since_m < nipple_m - _TOL_M)
            and first.lo_m <= second.lo_m + _BAND_GRID_M
            and first.hi_m >= second.hi_m - _BAND_GRID_M)


def _fitting_fits(graph: Graph, space: RoutingSpace, problem: GravityProblem,
                  label: _Label, came: dict[int, int], node_of: dict[int, int], lid: int,
                  index: int, other: int, heels: dict[tuple[int, int, int], bool]) -> bool:
    """A turn at ``index`` needs its nipple behind it and its heel clear (Phase 3)."""
    # Not ``_note``d: a lattice step a hair under the nipple is never why a route failed.
    if label.since_m < problem.nipple_m - _TOL_M:
        return False
    parent = came.get(lid)
    if parent is None or problem.heel_m <= 0.0:
        return True
    key = (node_of[parent], index, other)
    if key not in heels:
        heels[key] = heel_clear(graph, space, key[0], index, other, problem.heel_m)
    return heels[key]


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


def _clear_of(obstacles: Obstacles | None, problem: GravityProblem, a: int, b: int,
              developed_ft: float, plan_ft: float, drop_before: float, drop_after: float,
              band: tuple[float, float], report: GravityRefusal
              ) -> list[tuple[float, float]]:
    """``band`` less every start that puts the centreline inside a banded prism here.

    Over fractions ``[t0, t1]`` the centreline spans ``[start - shift(t1), start -
    shift(t0)]``; it meets ``[z0, z1]`` iff ``start`` is in ``[z0 + shift(t0), z1 +
    shift(t1)]``. A drop spans its own fall at one station. See §8a.
    """
    if obstacles is None:
        return [band]
    bands = [band]
    for t0, t1, z0, z1, tag in obstacles(a, b):
        if drop_after > drop_before:
            shift = problem.fall_over(developed_ft)
            forbidden = (z0 + shift + drop_before, z1 + shift + drop_after)
        else:
            forbidden = (z0 + problem.fall_over(developed_ft + t0 * plan_ft) + drop_before,
                         z1 + problem.fall_over(developed_ft + t1 * plan_ft) + drop_before)
        split = [piece for low_high in bands
                 for piece in subtract(low_high, forbidden, _TOL_M)]
        if not split:
            low, high = min(b[0] for b in bands), max(b[1] for b in bands)
            _note(report, f"{tag} across the fall band",
                  min(max(0.0, low - forbidden[0]), max(0.0, forbidden[1] - high))
                  / M_PER_IN)
            return []
        bands = split
    return bands


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
    floor = space.cost.heuristic_floor(rack=any(c.kind == "rack" for c in space.corridors))
    riser = space.cost.riser_per_ft
    # Vectorised over goals, memoised per node; bit-identical to the scalar form.
    gx = np.array([graph.nodes[g].x for g in goals])
    gy = np.array([graph.nodes[g].y for g in goals])
    gz = np.array([graph.nodes[g].z for g in goals])
    memo: dict[int, float] = {}

    def estimate(index: int) -> float:
        hit = memo.get(index)
        if hit is None:
            node = graph.nodes[index]
            hit = float((((np.abs(node.x - gx) + np.abs(node.y - gy)) / 0.3048 * 12.0
                          + np.abs(node.z - gz) / 0.3048 * 12.0 * riser) * floor).min())
            memo[index] = hit
        return hit

    return estimate


def _rebuild(graph: Graph, space: RoutingSpace, came: dict[int, int],
             node_of: dict[int, int], lid: int,
             seeds: dict[int, tuple[float, float, tuple[int, ...]]], takeoff: int) -> Route:
    chain = [lid]
    while chain[-1] in came:
        chain.append(came[chain[-1]])
    nodes = [node_of[i] for i in reversed(chain)]
    if takeoff >= 0:
        nodes = [*seeds[takeoff][2][:-1], *nodes]  # the arm, trap to take-off
    found = price_route(graph, space, nodes, "drain")
    found.takeoff = takeoff if takeoff >= 0 else None
    return found


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

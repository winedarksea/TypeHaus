"""Route a drain main's fixtures as one directed Steiner tree.

Each branch uses its fixture load's diameter; the shared space uses the largest radius.
Workflow: docs/routing.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.cli.route_support import (
    _storey_datum,
    _storey_of,
    branch_diameter_m,
)
from typehaus.model.spatial import Fixture

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.graph import Graph
    from typehaus.routing.proposal import RouteProposal


def _propose_tree(model: ResolvedModel, target: str, *, slope: float | None,
                  margin_ft: float, level: str | None, avoid: frozenset[str],
                  via: list[tuple[float, float]], explain: bool, cost: Any = None,
                  timing: list[str] | None = None, lift: frozenset[str] = frozenset(),
                  stats: dict | None = None
                  ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str],
                             list[Any]]:
    """Return (proposal/storey pairs, problems, notices, structured refusals).

    ``lift``: authored runs that are no obstacle to the tree (``--lift``, rip-up note §3 L1).
    ``stats`` collects every rip-up trial under ``"trials"`` (``routing/tree_ripup.Trial``).

    The whole main is the goal line, so branches may join at different stations. This is one
    coordinated tree; independent fixture searches cannot share the resulting branches."""
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]
    from typehaus.routing.timing import Timer

    problems: list[str] = []
    clock = Timer(target, enabled=timing is not None)
    runs = {r.tag: r for r in model.pipe_runs}
    main = runs.get(target)
    if main is None or main.system != "drain":
        problems.append(f"{target}: not a drain run in this model, so there is no tree "
                        "to build round it")
        return [], problems, [], []
    if not main.z_m or len(main.z_m) != len(main.path):
        problems.append(f"{target}: no resolved elevations, so there is no invert to tie "
                        "into anywhere along it")
        return [], problems, [], []

    fixtures = [tag for tag in main.serves if isinstance(model.plan.by_tag(tag), Fixture)]
    if not fixtures:
        problems.append(f"{target}: serves no fixture, so nothing feeds it. `--run "
                        f"{target}` re-routes the main itself")
        return [], problems, [], []
    # `--level` names one storey's group when the stack serves more than one: the tree is
    # then routed for those fixtures alone, which is the "each storey's group on its own"
    # the refusal below asks for.
    if level is not None:
        fixtures = [tag for tag in fixtures if _storey_of(model, tag) == level]
        if not fixtures:
            problems.append(f"{target}: no fixture it serves sits on the {level} storey")
            return [], problems, [], []

    points: dict[str, tuple[float, float]] = {}
    storeys: dict[str, str] = {}
    floors: dict[str, float] = {}
    diameters: dict[str, float] = {}
    for tag in fixtures:
        point = _expected_drain_point(model, tag)
        if point is None:
            problems.append(f"{tag}: no resolvable drain point — the same wording "
                            "mep.trap_arm_length uses, and the same cause")
            continue
        size = branch_diameter_m(model, (tag,), problems, tag)
        if size is None:
            continue
        points[tag] = (point[0], point[1])
        diameters[tag] = size
        storeys[tag] = _storey_of(model, tag)
        floors[tag] = _storey_datum(model, storeys[tag])
    if not points:
        return [], problems, [], []

    # **One storey per tree.** The branches are searched in a single plane — a drain's z is
    # a derived potential, not a free dimension — so fixtures on two floors are two trees
    # and saying so is the only honest answer. A stack serves both; a plan search does not.
    levels = sorted(set(floors.values()))
    if len(levels) > 1:
        problems.append(
            f"{target}: its fixtures sit on {len(levels)} storeys "
            f"({', '.join(sorted({storeys[t] for t in points}))}) and a branch tree is "
            "searched in one plane. Route each storey's group on its own")
        return [], problems, [], []
    floor_m = levels[0]

    # **The tie band is ``mep.fixture_drain_reach``'s**, and reusing it is the point: a
    # branch may tie in where the main passes within two feet below and six inches above
    # the fixture floor, and nowhere else. Without it a second-floor lavatory happily ties
    # into the basement leg of its own stack — the plan polyline says the two lines cross,
    # and only the invert says they are twelve feet apart.
    band = (floor_m - 2.0 * 0.3048, floor_m + 0.5 * 0.3048)
    reachable = [((x, y), z) for (x, y), z in zip(main.path, main.z_m, strict=False)
                 if band[0] <= z <= band[1]]
    if not reachable:
        problems.append(
            f"{target}: no vertex of it passes within 2 ft below and 6 in above the "
            f"{storeys[next(iter(points))]} floor, so nothing on that floor can tie into "
            "it — the same band mep.fixture_drain_reach grades against")
        return [], problems, [], []
    root_z = max(z for _p, z in reachable)
    tie_path = [p for p, _z in reachable]

    replaced = {run.tag for run in model.pipe_runs  # drains: never the basins' supplies
                if run.system == "drain" and any(tag in run.serves for tag in points)}

    # **One world per branch SIZE, widest first.** A tree used to be searched in a single
    # world inflated at one 2" literal; now every branch is sized from its own drainage
    # load and the sizes differ — catlin's suite bath is 3" / 1 1/2" / 1 1/4". Inflating
    # one shared world at the widest walls the narrow branches out of lanes they fit
    # perfectly well (the suite bath loses 1,355 of 2,508 lattice nodes at 3"), and
    # inflating it at the narrowest proposes a 3" lane verified at 1 1/4", which is the
    # dishonest direction. So each size gets its own lattice.
    #
    # RSPH still crosses the groups: a narrower branch may tie onto a wider one already
    # accepted, which is what a wye is and what §5's ordering argument turns on. What it
    # may NOT do is tie onto a branch of its own size routed in a later group, because
    # there is no later group — the sizes run widest first for exactly that reason.
    accepted: list[tuple[list[tuple[float, float]], list[float]]] = [
        (tie_path, [z for _p, z in reachable])]
    from typehaus.cli.route_tree_branches import Branches
    from typehaus.cli.route_tree_group import _route_group as route_group

    branches = Branches.of_main(target, [(x, y, z) for (x, y), z in reachable])
    proposals: list[tuple[RouteProposal, str]] = []
    notices: list[str] = []
    sizes = sorted({diameters[tag] for tag in points}, reverse=True)
    if len(sizes) > 1 and explain:
        spelled = ", ".join('%.3g"' % (d / 0.0254) for d in sizes)
        notices.append(f"{target}: {len(sizes)} branch sizes ({spelled}), so one lattice "
                       "each, widest first — a narrower branch may tie onto a wider one, "
                       "never the other way round")

    for size in sizes:
        group = sorted(tag for tag in points if diameters[tag] == size)
        made, group_problems, group_notices = route_group(
            model, target, group, points=points, floors=floors, storeys=storeys,
            size=size, root_z=root_z, accepted=accepted, branches=branches, via=via,
            slope=slope,
            margin_ft=margin_ft, level=level, avoid=avoid,
            touch=frozenset({target, *replaced, *lift}), explain=explain, cost=cost,
            clock=clock, stats=stats)
        proposals.extend(made)
        problems.extend(group_problems)
        notices.extend(group_notices)
    if timing is not None:
        timing.extend(clock.lines())
    # No refusals channel yet: a tree refusal is reported per-terminal inside the RSPH
    # loop and has no single blocked terminal to classify. The shape matches ``_propose``
    # so the caller does not branch on which proposer it called.
    return proposals, problems, notices, []



#: A tie is ON a laid line: each group's lattice has lines through every accepted vertex,
#: so this only covers the 1/16" snap. Two inches made a band of near-ties a branch could
#: chain through and a wye that missed its collector's centreline (§13).
TIE_TOLERANCE_M = 0.0032


def _line_nodes(graph: Graph, path: Any, tolerance: float = 0.05,
                z_tolerance: float | None = None) -> set[int]:
    """Nodes on a goal polyline, optionally gated by its interpolated vertex elevations.

    A supply feeder requires per-vertex z and z_tolerance: plan-only arrival could land below
    its horizontal leg. Gravity plan searches need no z gate."""
    out: set[int] = set()
    # A stack's reachable part is ONE vertex — its head — so the degenerate polyline is the
    # common case here rather than an edge case, and zipping it against its own tail would
    # silently produce no goals at all.
    segments = (list(zip(path, path[1:], strict=False)) if len(path) > 1
                else [(path[0], path[0])])
    for node in graph.nodes:
        for start, end in segments:
            (ax, ay), (bx, by) = start[:2], end[:2]
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            t = 0.0 if span <= 0 else max(0.0, min(1.0, ((node.x - ax) * dx
                                                         + (node.y - ay) * dy) / span))
            if ((ax + t * dx - node.x) ** 2
                    + (ay + t * dy - node.y) ** 2) > tolerance ** 2:
                continue
            if z_tolerance is not None and len(start) > 2 and len(end) > 2:
                # A RISER — one plan point, two elevations — holds every z between its ends;
                # interpolating at t=0 would put its whole rise at its foot.
                low, high = ((min(start[2], end[2]), max(start[2], end[2])) if span <= 0
                             else (start[2] + t * (end[2] - start[2]),) * 2)
                if not low - z_tolerance <= node.z <= high + z_tolerance:
                    continue
            out.add(node.index)
            break
    return out

"""``haus route --tree TAG --lift RUN``: a drain tree that re-lays authored blockers.

``houses/catlin/notes/mep_tree_ripup_basis.md`` §3. A lifted run is no obstacle while the
tree is searched (L1); afterwards each is re-proposed as ``--run`` would, larger outside
first, against every tree proposal and every re-laid run so far (L2). It never rips up a
drain (L3) and ends LAID or REFUSED with the proposals in its way (L4). docs/routing.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.cli.route_options import RouteOptions

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal


def propose_tree_lifted(model: ResolvedModel, tree: str, lift: tuple[str, ...],
                        opts: RouteOptions
                        ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str],
                                   list]:
    """``_propose_tree``'s return shape for drain main ``tree`` with ``lift`` (authored run
    tags, in the order given) as ``touch`` and re-laid against the tree.

    Returns (proposal/storey pairs, problems, notices, structured refusals); ``cmd_route``
    evaluates and reports them as it does a plain tree. ``--alternatives`` is already
    refused with ``--tree``. A lift that names no run is a problem, not an exception."""
    from typehaus.cli.cmd_route import _propose
    from typehaus.cli.cmd_route_tree import _propose_tree
    from typehaus.routing.campaign import proposal_prisms
    from typehaus.routing.obstacles import CLEARANCE_M

    runs = {r.tag: r for r in (*model.pipe_runs, *model.ducts, *model.conduits)}
    problems = [f"--lift {tag}: not an authored run in this model, so there is nothing "
                "to lift" for tag in lift if tag not in runs]
    known = tuple(dict.fromkeys(tag for tag in lift if tag in runs))
    if not known:
        return [], problems, [], []

    made, tree_problems, notices, refusals = _propose_tree(
        model, tree, slope=opts.slope, margin_ft=opts.margin_ft, level=opts.level,
        avoid=opts.avoid, via=list(opts.via), explain=opts.details, cost=opts.cost,
        timing=opts.timing, lift=frozenset(known))
    problems.extend(tree_problems)
    # The tree's drains stand in for the authored ones they replace: those are no obstacle
    # to a re-lay either, or it would route round both the old line and the new.
    served = {tag for proposal, _s in made for tag in proposal.serves}
    replaced = frozenset(run.tag for run in model.pipe_runs if run.tag != tree
                         and run.system == "drain" and served & set(run.serves))
    order = sorted(known, key=lambda tag: (-_outside_m(runs[tag]), tag))
    notices.append(f"{tree}: lifted {', '.join(order)} out of the tree's way; re-laid "
                   "below as runs, larger outside first, against the finished tree")
    occupancy = [prism for proposal, _s in made
                 for prism in proposal_prisms(proposal, inflate_m=CLEARANCE_M)]
    for index, tag in enumerate(order):
        got, run_problems, run_notices, run_refusals = _propose(
            model, [tag], mode="run", slope=opts.slope, margin_ft=opts.margin_ft,
            band=None, avoid=opts.avoid, via=[], explain=opts.details, cost=opts.cost,
            timing=opts.timing, extra_prisms=list(occupancy),
            lifted=frozenset(order[index + 1:]) | replaced)
        notices.extend(run_notices)
        if got:
            proposal, storey = got[0]
            made.append((proposal, storey))
            occupancy.extend(proposal_prisms(proposal, inflate_m=CLEARANCE_M))
            notices.append(f"{tag}: LAID — {_moved(runs[tag], proposal)}")
            continue
        blockers = sorted({b.tag for r in run_refusals for b in getattr(r, "blockers", ())})
        reason = (run_refusals[0].render() if run_refusals else
                  run_problems[0] if run_problems else "no route, and no reason given")
        problems.append(f"{tag}: REFUSED on re-lay — needs a hand re-lay of {tag}"
                        + (f"; in its way: {', '.join(blockers)}" if blockers else "")
                        + f". {reason}")
        problems.extend(run_problems[1:] if not run_refusals else run_problems)
        refusals.extend(run_refusals)
    return made, problems, notices, refusals


def _outside_m(run: Any) -> float:
    """The run's real outside, round or rectangular (L2's order)."""
    if hasattr(run, "width_m"):
        return max(run.width_m, getattr(run, "depth_m", 0.0) or 0.0)
    if hasattr(run, "system"):
        from typehaus.resolve.pipe_sections import pipe_outside_diameter_m

        return pipe_outside_diameter_m(run.diameter_m, run.material)
    return float(getattr(run, "trade_size_m", 0.0) or 0.0)  # a raceway: its trade size


def _moved(run: Any, proposal: RouteProposal) -> str:
    """Its developed length beside the authored one, and how far it strays from that line."""
    z = getattr(run, "z_m", None)
    authored = [(x, y, z[i] if z else None) for i, (x, y) in enumerate(run.path)]

    def length(points: list) -> float:
        return sum(sum(abs(a[k] - b[k]) for k in range(3) if a[k] is not None
                       and b[k] is not None) for a, b in zip(points, points[1:], strict=False))

    def off(point: tuple[float, float, float]) -> float:
        best = float("inf")
        for a, b in zip(authored, authored[1:], strict=False):
            dx, dy = b[0] - a[0], b[1] - a[1]
            span = dx * dx + dy * dy
            t = 0.0 if span <= 0 else max(0.0, min(1.0, ((point[0] - a[0]) * dx
                                                         + (point[1] - a[1]) * dy) / span))
            plan = ((a[0] + t * dx - point[0]) ** 2 + (a[1] + t * dy - point[1]) ** 2)
            rise = (0.0 if a[2] is None or b[2] is None
                    else a[2] + t * (b[2] - a[2]) - point[2])
            best = min(best, (plan + rise * rise) ** 0.5)
        return best

    moved = max((off(p) for p in proposal.points), default=0.0) if len(authored) > 1 else 0.0
    return (f"{length(proposal.points) / 0.3048:.2f} ft (authored "
            f"{length(authored) / 0.3048:.2f} ft), at most {moved / 0.0254:.2f}\" off its "
            "authored line")

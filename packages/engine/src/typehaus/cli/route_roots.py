"""Where a proposed run TIES IN — the root end of every route the CLI asks for.

Three questions, one module, because they are the same question asked of three topologies:
a drain lands at an invert on the run it discharges to (:func:`_discharge`); a branch lands
on the nearest main passing its own floor (:func:`_nearest_main`); and a branch vent lands
on the chase it shares with its siblings, anywhere along any of them
(:func:`_vent_siblings`). Split out of ``route_support`` when that file crossed the 500-line
rule in ``AGENTS.md``; nothing about the readings changed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


#: Two vents landing this close to one station are landing on the same thing. The plan grid
#: this repo authors on is a sixteenth of an inch; three inches is the joint tolerance every
#: other trade reading uses (``resolve/mep_soffit.DUCT_JOINT_TOLERANCE_M``) and is reused
#: here so "these two share a chase" means one thing across the engine.
_CHASE_TOLERANCE_M = 3 * 0.0254


def _vent_siblings(model: ResolvedModel, run: Any, problems: list[str]
                   ) -> tuple[tuple[float, float, float], list[str],
                              tuple[tuple[tuple[float, float], ...], ...]] | None:
    """``(the chase station, the siblings, their polylines)`` for a branch vent.

    The root is the run's own downstream end — the station it already lands on — and the
    goal set is that station plus every OTHER vent of this model that lands on it too. A
    branch vent may join any of them anywhere along its length; that is a common vent, and
    it is what ``--tree`` has always done for drains and no mode has ever done for vents.

    The siblings go into ``touch`` as well as into the goals: a run the proposal is meant to
    land ON may not also be a hard prism sitting exactly where the tie is.
    """
    end = (run.path[-1][0], run.path[-1][1])
    root = (end[0], end[1], run.z_m[-1])
    siblings: list[str] = []
    paths: list[tuple[tuple[float, float], ...]] = []
    for other in model.pipe_runs:
        if other.tag == run.tag or other.system != run.system or len(other.path) < 2:
            continue
        if min(((p[0] - end[0]) ** 2 + (p[1] - end[1]) ** 2) ** 0.5
               for p in (other.path[0], other.path[-1])) > _CHASE_TOLERANCE_M:
            continue
        siblings.append(other.tag)
        paths.append(tuple((p[0], p[1]) for p in other.path))
    if not siblings:
        problems.append(
            f"{run.tag}: nothing downstream of it is derivable and no other {run.system} "
            "run lands where it does, so there is nowhere to tie into. Name a --via, or "
            "route the parent first")
        return None
    return root, siblings, tuple(paths)


def _discharge(model: ResolvedModel, run: Any, problems: list[str]
               ) -> tuple[tuple[float, float, float], list[str],
                          tuple[tuple[float, float], ...]] | None:
    """``(root point, the whole downstream chain, the parent's plan polyline)``, or None.

    The chain, not just the parent, and that is what makes a tie reachable at all: a
    branch's root vertex usually sits ON its parent, and its parent's root sits on the
    GRANDparent, so leaving the rest of the chain hard walls the route off from the tie it
    is being routed to. ``drain_tie_ins`` derives the topology from the geometry and this
    walks it to the bottom.
    """
    from typehaus.resolve.mep_queries import drain_tie_ins

    ties = drain_tie_ins([r for r in model.pipe_runs if r.system == run.system])
    parent = ties.get(run.tag)
    if parent is None:
        problems.append(f"{run.tag}: nothing downstream of it is derivable, so there is "
                        "no root to route to. Name a --via, or route the parent first")
        return None
    chain: list[str] = []
    cursor: str | None = parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    other = next(r for r in model.pipe_runs if r.tag == parent)
    z = other.z_m or ()
    if len(z) != len(other.path):
        problems.append(f"{run.tag}: its discharge {parent} carries no resolved "
                        "elevations, so there is no invert to tie into")
        return None
    index = min(range(len(other.path)), key=lambda i: z[i])
    # The min-z vertex is the root a FALLING run needs: a drain arrives at an invert, and
    # that is one elevation at one point. It is also all a vent used to get, which is why a
    # branch vent could never be proposed into the middle of a sibling — the parent's whole
    # line comes back beside it and the caller picks by ``falls``.
    return ((other.path[index][0], other.path[index][1], z[index]), chain,
            tuple((p[0], p[1]) for p in other.path))


def _nearest_main(model: ResolvedModel, point: tuple[float, float], floor_m: float,
                  problems: list[str], target: str, *, exclude: str | None = None
                  ) -> tuple[tuple[float, float, float], str] | None:
    """The nearest drain run's vertex on this fixture's own floor.

    The vertical gate is ``mep.fixture_drain_reach``'s: a run counts only where it passes
    within two feet below and six inches above the fixture's storey datum. Without it the
    nearest main is whatever happens to lie beneath, two storeys down.

    **A run that already serves this fixture is excluded**, and that is not a nicety: asking
    for a branch to a fixture that has one means asking for a REPLACEMENT, and routing to
    the run being replaced finds its own start and reports a negative feasible slope — a
    true statement about a question nobody asked.
    """
    best = None
    for run in model.pipe_runs:
        if run.system != "drain" or not run.z_m:
            continue
        if exclude is not None and exclude in run.serves:
            continue
        for (x, y), z in zip(run.path, run.z_m, strict=False):
            if not (floor_m - 2.0 * 0.3048 <= z <= floor_m + 0.5 * 0.3048):
                continue
            distance = ((x - point[0]) ** 2 + (y - point[1]) ** 2) ** 0.5
            if best is None or distance < best[0]:
                best = (distance, (x, y, z), run.tag)
    if best is None:
        problems.append(f"{target}: no drain run passes on this fixture's own floor, so "
                        "there is nothing to route it to")
        return None
    return (best[1], best[2])

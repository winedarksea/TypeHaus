"""The sequence graph: whose dependency is whose, and whether it closes into a loop.

Split out of :mod:`typehaus.schedule.readiness` because three separate rules live here and
each of them is a decision, not a detail.

**An inspection's ``gates`` is a default for implicit visits only.** ``gates`` names a
*trade*, and a trade is not a schedulable thing: catlin's concrete is six arrivals. Stapling
every gate onto every arrival of the trade is what killed the board — ``foundation_backfill``
gates ``earth``, so excavation waited on the backfill inspection, which waits on the walls,
which wait on the footings, which wait on excavation. An authored visit therefore gets
exactly its authored ``depends_on`` and nothing else; an implicit one (nobody split the
package) still gets the gates, minus the ones :func:`dropped_gates` can show are circular.

**Package-level predecessors stop at a "late" visit.** ``TRADE_PREDECESSORS["framing"]``
names the concrete package; expanded to every concrete arrival it makes framing wait on the
driveway apron, which is authored last on purpose. A visit may declare
``blocks_successors = false`` and drop out of that expansion.

**Cycles are reported, never silently broken.** The old module docstring claimed a cycle was
impossible because inspections resolve before visits in one pass. The derivation does
terminate; the *result* was a deadlock, which is worse than an error because nothing says so.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

INSPECTION_PREFIX = "insp/"


def _reachable(start: str, edges: dict[str, tuple[str, ...]]) -> set[str]:
    seen: set[str] = set()
    stack = list(edges.get(start, ()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))
    return seen


def gate_map(specs: tuple[Any, ...]) -> dict[str, tuple[str, ...]]:
    """trade -> the inspection refs that gate it, in profile order."""
    out: dict[str, list[str]] = {}
    for spec in specs:
        for trade in spec.gates:
            out.setdefault(trade, []).append(f"{INSPECTION_PREFIX}{spec.id}")
    return {trade: tuple(refs) for trade, refs in out.items()}


def dropped_gates(specs: tuple[Any, ...]) -> dict[str, tuple[str, ...]]:
    """trade -> the implied gates the engine refuses to apply, and why they are circular.

    Two inspections that gate the same trade, one transitively ``after`` the other, cannot
    both bound the *start* of that trade's one implicit visit: the later one is an inspection
    of work the trade has not done yet. ``erosion`` bounds the start of ``earth``;
    ``foundation_backfill`` gates ``earth`` because backfill is earthwork, and on a split
    package that is the right statement — on the one undifferentiated lump it is the loop.
    So the earliest gate on each trade survives and every gate that follows it is dropped.
    """
    after: dict[str, tuple[str, ...]] = {
        f"{INSPECTION_PREFIX}{spec.id}":
            tuple(f"{INSPECTION_PREFIX}{ref}" for ref in spec.after)
        for spec in specs}
    out: dict[str, tuple[str, ...]] = {}
    for trade, refs in gate_map(specs).items():
        if len(refs) < 2:
            continue
        dropped = tuple(ref for ref in refs
                        if _reachable(ref, after).intersection(refs))
        if dropped:
            out[trade] = dropped
    return out


def implied_gates(trade: str, specs: tuple[Any, ...]) -> tuple[str, ...]:
    """The gates an *implicit* visit of this trade carries, circular ones removed."""
    dropped = set(dropped_gates(specs).get(trade, ()))
    return tuple(ref for ref in gate_map(specs).get(trade, ()) if ref not in dropped)


def expand_package_dependencies(visits: tuple[Any, ...]) -> tuple[Any, ...]:
    """Rewrite a dependency on a *package* into one on each visit derived from it.

    A package's predecessors come from ``TRADE_PREDECESSORS`` and name package slugs. The
    moment somebody splits one of those packages into arrivals, the package slug stops being
    a visit and the dependency dangles — which is exactly what "names no current visit"
    reports, and reporting it would be wrong here: the owner did not break anything, they
    split a package the engine's own predecessor map still refers to by its old name.

    A visit with ``blocks_successors = false`` is left out of the expansion. It is still a
    visit, still on the board, still blocked by its own predecessors; it simply stops being
    something the *next trade* has to wait for.
    """
    slugs = {visit.slug for visit in visits}
    by_package: dict[str, list[str]] = {}
    for visit in visits:
        if visit.slug != visit.package and visit.blocks_successors:
            by_package.setdefault(visit.package, []).append(visit.slug)
    if not by_package:
        return visits
    out: list[Any] = []
    for visit in visits:
        expanded: list[str] = []
        for dependency in visit.depends_on:
            if dependency in slugs or dependency.startswith(INSPECTION_PREFIX):
                expanded.append(dependency)
            else:
                # Every blocking arrival in the predecessor package, or the name itself when
                # it matches nothing — a genuinely stale dependency still has to be visible.
                expanded.extend(by_package.get(dependency, [dependency]))
        out.append(replace(visit, depends_on=tuple(dict.fromkeys(expanded))))
    return tuple(out)


def _node_edges(visits: tuple[Any, ...],
                inspections: tuple[Any, ...]) -> dict[str, tuple[str, ...]]:
    """One graph over both halves: a visit waits on its ``depends_on``, an inspection on
    its ``after`` and on every visit its entry ``requires``."""
    edges: dict[str, tuple[str, ...]] = {}
    for visit in visits:
        edges[visit.slug] = tuple(visit.depends_on)
    for record in inspections:
        ref = f"{INSPECTION_PREFIX}{record.id}"
        requires = tuple((record.entry or {}).get("requires") or ())
        edges[ref] = tuple(f"{INSPECTION_PREFIX}{name}" for name in record.after) + requires
    return edges


def find_cycles(visits: tuple[Any, ...],
                inspections: tuple[Any, ...]) -> tuple[tuple[str, ...], ...]:
    """Every dependency loop, each named by the nodes on it, in a stable order.

    Iterative depth-first with an explicit colour map: the graph is small, and a recursive
    walk would blow the stack on a pathological hand-edited file — which is exactly the file
    this function exists to describe.
    """
    edges = _node_edges(visits, inspections)
    colour: dict[str, int] = {}
    found: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for start in sorted(edges):
        if colour.get(start):
            continue
        path: list[str] = []
        stack: list[tuple[str, int]] = [(start, 0)]
        while stack:
            node, index = stack[-1]
            if index == 0:
                if colour.get(node):
                    stack.pop()
                    continue
                colour[node] = 1
                path.append(node)
            successors = edges.get(node, ())
            if index >= len(successors):
                colour[node] = 2
                path.pop()
                stack.pop()
                continue
            stack[-1] = (node, index + 1)
            nxt = successors[index]
            if colour.get(nxt) == 1:
                loop = tuple(path[path.index(nxt):])
                key = tuple(sorted(loop))
                if key not in seen:
                    seen.add(key)
                    found.append(loop + (nxt,))
            elif not colour.get(nxt):
                stack.append((nxt, 0))
    return tuple(found)

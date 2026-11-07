"""A drain tree size group's laid state, as ``routing/tree_ripup`` sees it.

Lines, tie owners, inverts and arrivals, with every lay recorded (its nodes, whether it ends
in a plumb drop, the inverts it added, its route) so a lift can be undone line by line, a
trial rolled back whole, and a branch re-laid one size up (P8, ``route_tree_upsize``).
``houses/catlin/notes/mep_tree_ripup_basis.md`` §1."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_PROPOSED = "-PROPOSED"


class Ledger:
    """``place(tag, route, size, lattice, arrival)`` lays a route searched in another lattice
    and returns it on this one, or None (the group's ``place``); ``widen(points, size,
    arrival, tie_tag)`` re-lays a lane at a larger size: (route, lattice) or None. Both are
    the group's to bind."""

    place: Callable[..., Any]
    widen: Callable[[list, float, float, str | None], Any]

    def __init__(self, branches: Any, owners: dict[int, int], inverts: dict[int, float],
                 reports: dict[str, Any]) -> None:
        self.branches = branches
        self.base_owners = dict(owners)  # the group's start: the main and wider lines
        self.owners = owners
        self.inverts = inverts
        self.arrivals: dict[str, float] = {}
        self.reports = reports
        #: Per search, the laid lines it found full or standing in its ties (§1 P1), and
        #: of those the full ones alone, too small for it (P8).
        self.refused_ties: dict[str, set[str]] = {}
        self.too_small: dict[str, set[str]] = {}
        self.laid: dict[str, tuple[list[int], bool, tuple[int, ...]]] = {}
        self.found: dict[str, Any] = {}
        self.size_of: dict[str, float] = {}  # a branch P8 re-laid one size up
        self.trial = False  # between a lift and its settle: every search is the trial's
        self.probed: set[str] = set()  # had its first search, a probe once siblings lie
        self.cut_short: set[str] = set()  # ...and that probe stopped at its budget
        #: A search that found a lane its profile cannot hold on the 1/16" grid: the reason.
        self.unsnapped: dict[str, str] = {}

    def settle(self) -> None:
        self.trial = False

    def cap(self, tag: str, probe: int) -> int | None:
        """A search's label budget. Inside a trial, and for a terminal's FIRST search once a
        sibling lies (a trial could answer it), a probe; otherwise the full budget."""
        if self.trial:
            return probe
        first = tag not in self.probed
        self.probed.add(tag)
        return probe if first and self.laid else None

    def searched(self, tag: str, cap: int | None, report: Any, found: bool) -> None:
        if self.trial:
            return
        stopped = any("search stopped after" in note for note in report.notes)
        (self.cut_short.add if cap and not found and stopped else self.cut_short.discard)(tag)

    def capped(self, tag: str) -> bool:
        return tag in self.cut_short

    def lay(self, tag: str, size: float, points: list, found: Any, over: bool,
            added: set[int]) -> None:
        line = self.branches.add(tag, size, points, self.owners.get(found.nodes[-1], 0))
        self.laid[tag] = (list(found.nodes), over, tuple(added))
        self.found[tag] = found
        self._own(line, found.nodes, over)

    def _own(self, line: int, nodes: list[int], over: bool) -> None:
        for index in nodes:
            self.owners.setdefault(index, line)
        if over:  # its plumb drop now stands on the tie: a later branch enters it there
            self.owners[nodes[-1]] = line

    def blockers(self, tag: str) -> list[str]:
        """The laid lines ``tag``'s refusal names: its tightest blocker when that is one of
        this tree's proposals; failing any blocker, the lines it found full or in its ties."""
        report = self.reports.get(tag)
        if tag in self.unsnapped:  # the grid refused it, not a sibling
            return []
        if report is not None and report.tightest is not None:
            what = report.tightest[0].split(" ")[0]
            return [what[:-len(_PROPOSED)]] if what.endswith(_PROPOSED) else []
        return sorted(self.refused_ties.get(tag, ()))

    def undersized(self, tag: str) -> list[str]:
        """P8's candidates: the laid lines too small for ``tag``, those its refusal names
        first, then latest laid first (P2)."""
        named, order = set(self.blockers(tag)), list(self.laid)
        small = [t for t in self.too_small.get(tag, ()) if t in self.laid]
        return sorted(small, key=lambda t: (t not in named, -order.index(t)))

    def upsize(self, tag: str) -> tuple[Any, list[str]] | None:
        from typehaus.cli.route_tree_upsize import next_size

        index = self.branches.index_of(tag)
        found = self.found.get(tag)
        if index is None or found is None:
            return None
        line = self.branches.lines[index]
        bigger = next_size(line.size_m)
        below = self.branches.lines[line.down] if line.down else None
        if bigger is None or (below is not None and below.size_m < bigger - 1e-6):
            return None  # the line it ties onto could not carry it
        points, arrival = list(line.points), line.points[-1][2]
        # Every branch laid after it was laid against its old outside: they are lifted too,
        # and re-laid in their order after the terminal (a wider line can close a sibling's
        # lane: BATH2-SH at 2" meets LAUNDRY-SINK, laid after it, by 0.139").
        order = list(self.laid)
        later = order[order.index(tag) + 1:] if tag in order else []
        lifted = self.lift(tag)
        for other in later:
            if other not in lifted:
                lifted += self.lift(other)
        lifted = [tag] + sorted((t for t in lifted if t != tag), key=order.index)
        wide = self.widen(points, bigger, arrival, below.tag if below else None)
        laid = None if wide is None else self.place(tag, wide[0], bigger, wide[1], arrival)
        if laid is None:
            return None
        self.size_of[tag] = bigger
        return laid, lifted[1:]

    def snapshot(self) -> Any:
        return (self.branches.copy(), dict(self.owners), dict(self.inverts),
                dict(self.arrivals), dict(self.reports), dict(self.laid),
                dict(self.unsnapped), dict(self.found), dict(self.size_of))

    def restore(self, state: Any) -> None:
        branches, *saved = state
        self.branches.lines = branches.lines
        for mine, back in zip((self.owners, self.inverts, self.arrivals, self.reports,
                               self.laid, self.unsnapped, self.found, self.size_of),
                              saved, strict=True):
            mine.clear()
            mine.update(back)

    def lift(self, tag: str) -> list[str]:
        self.trial = True
        index = self.branches.index_of(tag)
        if index is None:
            return []
        lifted = self.branches.remove(index)
        for gone in lifted:
            _nodes, _over, added = self.laid.pop(gone, ([], False, ()))
            for node in added:
                self.inverts.pop(node, None)
            self.arrivals.pop(gone, None)
            self.found.pop(gone, None)
            self.size_of.pop(gone, None)
        self.owners.clear()
        self.owners.update(self.base_owners)
        for laid_tag, (nodes, over, _added) in self.laid.items():  # lay order survives
            line = self.branches.index_of(laid_tag)
            if line is not None:
                self._own(line, nodes, over)
        return lifted

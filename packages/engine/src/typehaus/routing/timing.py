"""Where the time and the nodes went. The measurement Phase 7 is gated on.

Nothing here decides anything; it records. That matters because the one real performance
question about this package — is the *graph build* or the *search* the cost? — has been
answered by inspection and never by a number, and every optimisation worth doing depends on
which. A jump-point search speeds up expansions; it does nothing at all for a build that is
already ninety per cent of the wall clock.

Stated in milliseconds and counts, never as a verdict: a router that graded its own speed
would be one more thing to disbelieve.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.graph import Graph
    from typehaus.routing.search import Route


@dataclass
class Timer:
    """One target's measurements. Disabled, every method is a few nanoseconds of nothing."""

    label: str
    enabled: bool = True
    stages: list[tuple[str, float]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        started = time.perf_counter()
        try:
            yield
        finally:
            self.stages.append((name, (time.perf_counter() - started) * 1000.0))

    def lattice(self, graph: Graph) -> None:
        if not self.enabled:
            return
        self.counts["nodes"] = len(graph.nodes)
        # Halved: every edge is stored in both directions so the search can relax it from
        # either end. Reporting the stored count would double a number people compare.
        self.counts["edges"] = len(graph.weights) // 2

    def route(self, found: Route | None) -> None:
        if not self.enabled or found is None:
            return
        self.counts["expansions"] = self.counts.get("expansions", 0) + found.expansions

    def lines(self) -> list[str]:
        """One line per stage plus one for the counts, or nothing when disabled."""
        if not self.enabled or not (self.stages or self.counts):
            return []
        out = [f"{self.label}: "
               + ", ".join(f"{name} {ms:.1f} ms" for name, ms in self.stages)]
        if self.counts:
            out.append(f"{self.label}: "
                       + ", ".join(f"{key} {value:,}"
                                   for key, value in sorted(self.counts.items())))
        return out

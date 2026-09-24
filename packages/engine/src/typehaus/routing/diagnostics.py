"""Why a search found nothing — named, classified, and priced where it can be.

"No route in plan; every lane is blocked" is true and useless. A caller iterating on a
proposal needs the tag of the thing in the way, where it stands, and — the part that decides
what to do next — **whether it is the kind of thing that could move**. That is the difference
between "re-route the vent" and "the stair is where the stair is".

Phase 4's two-way street, and its three parts:

* **Named blockers with a location.** :func:`blockers` probes the lanes out of a node and
  returns the prisms standing on them with the point and elevation the probe met them at,
  not merely their tags.
* **A mobility class on every one.** :class:`Mobility` — ``fixed`` for an opening, a void or
  concrete; ``movable`` for another service run; ``priced`` for a soft prism, which is not a
  blocker at all but a cost; ``unknown`` where the geometry does not support a claim. The
  class is read off what the prism IS (``HardPrism.kind``), never guessed from its tag.
* **The distinction between a search that failed and a building that cannot be routed.**
  :class:`Refusal` carries the reachability count, what was attempted, and which limits were
  hit, and says "no route within this search" where that is what happened. Those are
  different facts and one sentence was covering both.

Nothing here searches or decides, which is why it oracles nothing. The counterfactual — "a
route exists if PR-M-WC-VENT moved" — does search, and lives in
:mod:`typehaus.routing.counterfactual` for exactly that reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typehaus.routing.graph import Graph
from typehaus.routing.space import RoutingSpace

#: How far out a probe looks for what is standing on a lane. A foot is a hand's width and
#: covers the fitting-scale congestion that produces a walled-in terminal — an ERV
#: manifold's ports sit four inches apart.
PROBE_REACH_M = 0.3048


class Mobility(str, Enum):
    """What kind of thing is in the way, and therefore what could be done about it.

    The classes are about the MODEL's freedom, not the building's. ``movable`` says "this is
    another service run, and this engine can re-route a service run" — it is emphatically
    not a claim that the run may legally or practically move, which is a judgement with a
    person on the end of it. Phase 4's counterfactual is labelled the same way and for the
    same reason.
    """

    #: Framed, poured or cut: a rough opening, a floor void, unsleeved concrete. A route
    #: does not negotiate with these.
    FIXED = "fixed"
    #: Another service run. Re-routable in principle, which is what makes a counterfactual
    #: worth running at all.
    MOVABLE = "movable"
    #: A soft prism — a finished room, in-wall travel. Never a blocker: a route may take it
    #: and be charged for it, and it appears here only when a caller asks what a lane costs.
    PRICED = "priced"
    #: The caller's own ``--avoid``, or geometry too thin to classify. Held apart from
    #: FIXED because "you told me not to" and "it is concrete" are not the same answer.
    UNKNOWN = "unknown"


#: ``HardPrism.kind`` to mobility. Read, never inferred from a tag: a tag is a name somebody
#: chose and a kind is what the resolver built.
_KIND_MOBILITY = {
    "opening": Mobility.FIXED,
    "void": Mobility.FIXED,
    "concrete": Mobility.FIXED,
    # An open-web truss's WEBS, where the deck states its fabricator's panel layout
    # (2026-09-19). FIXED in the strongest sense this table has: a web is not bored,
    # notched or moved by anybody, and lifting one in a counterfactual would be pricing a
    # truss nobody will build.
    "member": Mobility.FIXED,
    # A flight's R311.7.2 headroom and its stringers: the stair does not move for a duct.
    "stair": Mobility.FIXED,
    # A beam or girder: a carrier is not bored for a run and does not move for one.
    "beam": Mobility.FIXED,
    "run": Mobility.MOVABLE,
    "avoid": Mobility.UNKNOWN,
}


@dataclass(frozen=True)
class Blocker:
    """One thing standing on a lane, with where it was met."""

    tag: str
    kind: str
    mobility: Mobility
    x_m: float
    y_m: float
    z_m: float

    def describe(self) -> str:
        """Where the blocker was met, in feet.

        A ``run`` blocker's z is a point on a BAND: ``routing/obstacles`` bands each segment
        over its own fall, so a sloping run stands in the way anywhere between its two ends.
        ``mep.run_interference`` reads the same run differently — the real clearance at the
        station — and the two are not in disagreement: a check reads a drawn run, a router
        has to stay out of everywhere it might be.
        """
        from typehaus.quantities import M_PER_IN
        return (f"{self.tag} ({self.kind}, {self.mobility.value}) at "
                f"({self.x_m / M_PER_IN / 12:.2f}', {self.y_m / M_PER_IN / 12:.2f}', "
                f"z {self.z_m / M_PER_IN / 12:.2f}')")

    def payload(self) -> dict:
        return {"tag": self.tag, "kind": self.kind, "mobility": self.mobility.value,
                "x_m": self.x_m, "y_m": self.y_m, "z_m": self.z_m}


def mobility_of(kind: str) -> Mobility:
    return _KIND_MOBILITY.get(kind, Mobility.UNKNOWN)


def blockers(space: RoutingSpace, graph: Graph, node: int,
             reach_m: float = PROBE_REACH_M) -> list[Blocker]:
    """What stands on the lanes out of ``node``, nearest first, each classified.

    A lattice node with no edges is one whose neighbours were all dropped, and the reason
    each was dropped is a prism this can name. Probed along both plan axes in both
    directions; the first prism met on each ray is the one reported, because the second one
    behind it is not what a caller has to deal with first.
    """
    origin = graph.nodes[node]
    found: dict[str, Blocker] = {}
    for dx, dy in ((reach_m, 0.0), (-reach_m, 0.0), (0.0, reach_m), (0.0, -reach_m)):
        for step in (0.25, 0.5, 1.0):
            point = (origin.x + dx * step, origin.y + dy * step)
            prism = _prism_at(space, point, origin.z)
            if prism is None or prism.tag in found:
                continue
            found[prism.tag] = Blocker(prism.tag, prism.kind, mobility_of(prism.kind),
                                       point[0], point[1], origin.z)
            break
    return list(found.values())


def _prism_at(space: RoutingSpace, point: tuple[float, float], z: float):
    """The first hard prism covering this point — the OBJECT, where ``blocked`` gives a tag.

    ``RoutingSpace.blocked`` answers "is this point legal", which is what a graph build
    needs and is deliberately cheap. A diagnostic needs the prism's kind and band as well,
    so it repeats the query rather than widening that hot path's return type.
    """
    from shapely.geometry import Point

    if not space.hard:
        return None
    probe = Point(point)
    for index in space._index("hard").query(probe):  # noqa: SLF001 - same package
        prism = space.hard[int(index)]
        if prism.z0_m <= z <= prism.z1_m and prism.footprint.covers(probe):
            return prism
    return None


def enclosure(space: RoutingSpace, graph: Graph, node: int,
              reach_m: float = PROBE_REACH_M) -> list[str]:
    """Tags of the hard prisms standing on the lanes out of ``node``, nearest first.

    Kept as the tag-only view because two callers want exactly that and the oracle names
    this function. :func:`blockers` is the same probe with the classification attached.
    """
    return [blocker.tag for blocker in blockers(space, graph, node, reach_m)]


def reachable(graph: Graph, start: int) -> set[int]:
    """Every node the search could get to from ``start`` at any price.

    Reported as a count rather than a set by the caller: "three of thirty-three thousand
    nodes" says "walled in at the terminal", and "thirty thousand" says "the goal is the
    problem". Those are different defects and the same message was covering both.
    """
    seen = {start}
    stack = [start]
    while stack:
        for other, _axis in graph.neighbours(stack.pop()):
            if other not in seen:
                seen.add(other)
                stack.append(other)
    return seen


@dataclass
class Refusal:
    """Everything known about why one terminal was not served.

    **The point of the record is the last field.** ``established`` separates "this building
    cannot carry this run" from "this search did not find a way", and only the second one is
    a reason to try again with a wider margin or a different order. A router that reports
    both the same way teaches a caller to distrust both.
    """

    target: str
    service: str
    #: Which end the search died at: ``"origin"`` or ``"root"``.
    end: str
    reachable_nodes: int
    total_nodes: int
    blockers: list[Blocker] = field(default_factory=list)
    #: Quantified shortages, already in words: "4 1/2" of fall short", "bay is 2" narrow".
    shortages: tuple[str, ...] = ()
    #: What was tried — alternatives asked for, rounds run, limits hit.
    attempts: tuple[str, ...] = ()
    #: True only when the geometry itself forecloses it; False means "not within this
    #: search", which is a statement about the search and says so.
    established: bool = False

    def movable(self) -> list[Blocker]:
        return [b for b in self.blockers if b.mobility is Mobility.MOVABLE]

    def render(self) -> str:
        head = (f"{self.target} ({self.service}): no route. "
                f"{self.reachable_nodes:,} of {self.total_nodes:,} lattice nodes are "
                f"reachable from the origin, and the lanes off the {self.end} are blocked")
        if self.blockers:
            head += " by " + "; ".join(b.describe() for b in self.blockers)
        parts = [head + "."]
        if self.shortages:
            parts.append("Short by: " + "; ".join(self.shortages) + ".")
        if self.attempts:
            parts.append("Tried: " + "; ".join(self.attempts) + ".")
        movable = self.movable()
        parts.append(
            "This is established from the geometry: no arrangement of the movable elements "
            "opens a lane." if self.established else
            "This is a statement about THIS search, not a proof of impossibility"
            + (f" — {len(movable)} blocker(s) are movable service runs "
               f"({', '.join(b.tag for b in movable)}); see --counterfactual."
               if movable else "; nothing in the way is movable by this engine."))
        return " ".join(parts)

    def payload(self) -> dict:
        return {
            "target": self.target, "service": self.service, "end": self.end,
            "reachable_nodes": self.reachable_nodes, "total_nodes": self.total_nodes,
            "blockers": [b.payload() for b in self.blockers],
            "shortages": list(self.shortages), "attempts": list(self.attempts),
            "established": self.established,
        }


def refusal(space: RoutingSpace, graph: Graph, start: int, goals: set[int],
            *, target: str = "", service: str = "", shortages: tuple[str, ...] = (),
            attempts: tuple[str, ...] = ()) -> Refusal:
    """Build the record for a search that returned nothing.

    Which end to probe is decided by reachability, not by guessing: a terminal that can
    reach almost nothing is walled in, and one that can reach most of the lattice has a
    problem at the far end instead.
    """
    seen = reachable(graph, start)
    walled = len(seen) < max(8, len(graph.nodes) // 100)
    end, node = ("origin", start) if walled or not goals else ("root", min(goals))
    return Refusal(
        target=target, service=service, end=end,
        reachable_nodes=len(seen), total_nodes=len(graph.nodes),
        blockers=blockers(space, graph, node),
        shortages=shortages, attempts=attempts,
        # Established only where the terminal is sealed in by things that cannot move: with
        # a movable run in the way, or an unexplored lattice, "impossible" is unearned.
        established=walled and bool(space.hard) and all(
            b.mobility is Mobility.FIXED for b in blockers(space, graph, node)),
    )


def refusal_line(space: RoutingSpace, graph: Graph, start: int, goals: set[int]) -> str:
    """One sentence, for callers that want the old string."""
    return refusal(space, graph, start, goals).render()

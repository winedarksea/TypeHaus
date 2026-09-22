"""The site's drainage as ONE graph, walked to an outfall.

** EVERY SLOPE AND INVERT RULE IN THIS ENGINE WAS SCOPED TO ``PipeRun`` UNTIL 2026-09-14. **
``mep.drain_slope``, ``mep.drain_slope_margin`` and ``mep.drain_tie_in`` read real topology
out of ``resolve/mep_tie_ins``, and none of it reached site drainage: a ``FrenchDrain``
carried one scalar invert and the resolver extruded every trench dead level, a ``Drywell``
had no storage, rate or way out, a ``Sump`` had no inlet to check anything against, and
**nothing walked a discharge chain at all**. So "this drain discharges to the drywell" was a
string beside a string, and a run whose trench floor sat 28" above the stone it fed read
exactly like one that fell into it.

This module is the missing walk. It is a leaf — it imports ``model`` and nothing else, in
particular never ``checks`` — and it answers three questions the string could not:

* **does the water get anywhere?** every source followed to a terminal, cycles named rather
  than silently dropped;
* **does it get there downhill?** every hop's inverts compared, where both ends have one;
* **and if the first route fails, is there a second?** which is why an edge has a *kind*.

**Primary and overflow are two different facts and one field could never hold both.** A run
discharges somewhere in the ordinary case and somewhere else when that receiver cannot take
it — a well that has filled, a frozen outlet, a pump with no power. Collapsing them loses
exactly the question a reviewer asks about a below-grade court. ``FD-SG-OVERFLOW`` had been
doing this by hand for months, as a second authored run; the overflow edge is the general
form of it.

``"daylight"`` is a **resolved terminal**, not a short-circuit. ``drainage.discharge_
consistency`` used to return early on the string, which is how catlin's house tile sat on
``discharge="daylight"`` for months on a lot with no daylight below -7'-0" anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typehaus.model.landscape import RainGarden
from typehaus.model.mep import Sump
from typehaus.model.structure import Drywell, FootingBedding, FrenchDrain
from typehaus.model.trim import Downspout

#: The free-text discharge that names no element. A real answer on a sloping lot and a lie
#: on a flat one, and either way a TERMINAL: the walk ends here successfully, and whether
#: there is any daylight to reach is a separate question a separate rule asks.
DAYLIGHT = "daylight"

#: ``discharge="sump"`` — the other free-text answer, which names a KIND rather than a tag.
#: Resolved to the plan's only sump where there is exactly one, and reported as ambiguous
#: where there are several, because picking one would be inventing a connection.
SUMP_KEYWORD = "sump"


class EdgeKind(Enum):
    """Why this hop exists. See the module docstring on why one field could not carry both."""

    PRIMARY = "primary"
    OVERFLOW = "overflow"


@dataclass(frozen=True)
class DrainNode:
    """One thing in the network, and the levels it can be checked against.

    ``out_invert`` is where water LEAVES this node — a run's discharge end, a well's
    overflow lip. ``in_invert`` is where it ARRIVES. They are separate because a hop's
    continuity is the upstream node's out against the downstream node's in, and on a well
    those are feet apart.

    ``None`` on either is "the model does not say", never a default: an invert invented from
    a storey datum is exactly the kind of number that makes a broken gradient look checked.
    """

    tag: str
    kind: str
    in_invert_m: float | None = None
    out_invert_m: float | None = None
    #: **This node gets rid of water in the ORDINARY case**, so a primary walk that reaches
    #: it has succeeded. Three things do: daylight, a drywell (the soil takes it), and a pit
    #: with a pump (it leaves under power).
    #:
    #: Every one of those three can also stop working, which is the whole reason the graph
    #: has a second edge kind — soil saturates, power goes out, an outlet freezes. "Disposes"
    #: is therefore not "safe"; it is "the walk ends here, and the fallback rule is where the
    #: harder question is asked".
    disposes: bool = False
    #: What this node says feeds it, for the reciprocity rule. Empty is not "nothing feeds
    #: it" — it is "this node makes no claim", which is a different finding.
    inlet_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class DrainEdge:
    source: str
    target: str
    kind: EdgeKind
    #: The elevation water leaves ``source`` at on THIS edge. An overflow leaves at its own
    #: lip, which is above the run's invert by design, so the edge carries the level and not
    #: the node.
    out_invert_m: float | None = None


@dataclass
class DrainageNetwork:
    nodes: dict[str, DrainNode] = field(default_factory=dict)
    edges: list[DrainEdge] = field(default_factory=list)
    #: Discharge targets that name no element and are not a keyword. Reported, never guessed.
    unresolved: list[tuple[str, str]] = field(default_factory=list)

    def out_edges(self, tag: str, kind: EdgeKind | None = None) -> list[DrainEdge]:
        return [e for e in self.edges
                if e.source == tag and (kind is None or e.kind is kind)]

    def sources(self) -> list[str]:
        """Nodes that produce water — everything that is not purely a receiver."""
        return sorted(tag for tag, node in self.nodes.items()
                      if node.kind in {"french_drain", "footing_tile", "leader"})

    def disposal_points(self) -> list[str]:
        """Everything that gets rid of water, daylight excepted — the things that can fail.

        Daylight is out because there is no fallback to ask of it: it IS the fallback. A
        drywell and a pump are in, because a soakaway in saturated soil and a pump with no
        power are the two failures a below-grade court actually sees.
        """
        return sorted(tag for tag, node in self.nodes.items()
                      if node.disposes and tag != DAYLIGHT)

    def reaches_disposal(self, start: str, *, first_hop: EdgeKind | None = None,
                         not_being: str | None = None
                         ) -> tuple[bool, list[str], str | None]:
        """``(reached, path, problem)`` — can water leaving ``start`` get rid of itself?

        ``first_hop`` constrains only the FIRST edge, because that is what distinguishes the
        two questions. A primary walk takes primary edges throughout. A **fallback** walk
        goes over one lip and then onward by whatever route exists — "over the weir, then
        downhill" — so after the first hop every edge is fair game.

        ``not_being`` excludes one node from counting as the answer, which is what makes the
        fallback rule mean anything: a drywell whose overflow leads back to itself has no
        fallback, however many hops it takes to get there.

        **Cycles are tolerated, not an error in themselves.** Decision 6's bridge is a
        deliberate two-way tie at one level — the sump falls back to the drywell and the
        drywell's overflow comes back round to the sump — and a graph that called that a
        fault would be refusing the design it was built to check. A cycle is only reported
        when the walk exhausts itself inside one without ever reaching disposal.
        """
        seen: set[str] = set()
        best_path: list[str] = []

        def step(tag: str, kind: EdgeKind | None, path: list[str]) -> tuple[bool, str | None]:
            nonlocal best_path
            path = [*path, tag]
            if len(path) > len(best_path):
                best_path = path
            node = self.nodes.get(tag)
            if node is None:
                return False, f"{tag} is named as a discharge target but is not a node"
            if node.disposes and tag != not_being and len(path) > 1:
                return True, None
            if tag in seen:
                return False, f"a cycle with no outfall in it: {' -> '.join(path)}"
            seen.add(tag)
            candidates = self.out_edges(tag, kind)
            if not candidates:
                if kind is EdgeKind.OVERFLOW:
                    return False, (f"{tag} has no overflow — nothing says where the water "
                                   f"goes when it cannot cope")
                return False, f"{tag} discharges to nothing"
            problem = None
            for edge in candidates:
                ok, why = step(edge.target, None, path)
                if ok:
                    return True, None
                problem = problem or why
            return False, problem

        reached, problem = step(start, first_hop, [])
        return reached, best_path, problem


def _tile_discharge(spec) -> str | None:
    return spec.discharge if spec is not None else None


def build_network(plan) -> DrainageNetwork:
    """Every drainage element in the plan, as nodes and edges.

    Reads the PLAN rather than the resolved model because a discharge is an authored claim
    about another authored element; nothing here needs geometry it could only get from the
    resolver, and a leaf that stays out of ``resolve/model`` is one fewer import cycle.
    """
    network = DrainageNetwork()
    elements = list(plan.all_elements())
    by_tag = {getattr(e, "tag", None): e for e in elements}
    sumps = [e for e in elements if isinstance(e, Sump)]

    network.nodes[DAYLIGHT] = DrainNode(tag=DAYLIGHT, kind="daylight", disposes=True)

    for element in elements:
        if isinstance(element, FrenchDrain):
            start = element.invert.meters
            end = element.end_invert.meters if element.end_invert is not None else start
            network.nodes[element.tag] = DrainNode(
                tag=element.tag, kind="french_drain",
                in_invert_m=start, out_invert_m=end)
        elif isinstance(element, Drywell):
            top = element.top_elevation.meters if element.top_elevation is not None else None
            lip = (element.overflow_invert.meters
                   if element.overflow_invert is not None else top)
            network.nodes[element.tag] = DrainNode(
                # A soakaway DISPOSES: the soil takes the water and the gravity walk ends
                # there legitimately. Whether it can keep doing so when the soil is saturated
                # is the fallback rule's question, and it is why `overflow_ref` exists.
                tag=element.tag, kind="drywell", in_invert_m=top, out_invert_m=lip,
                disposes=True, inlet_refs=tuple(element.inlet_refs))
        elif isinstance(element, Sump):
            inlet = (element.inlet_invert.meters
                     if element.inlet_invert is not None else None)
            lip = (element.overflow_invert.meters
                   if element.overflow_invert is not None else inlet)
            network.nodes[element.tag] = DrainNode(
                # A pit that PUMPS is a terminal: the water leaves under power and the
                # gravity walk legitimately ends. A pit with no pump is a hole that has to
                # let go somewhere, and the walk keeps going.
                tag=element.tag, kind="sump", in_invert_m=inlet, out_invert_m=lip,
                disposes=element.pump is not None,
                inlet_refs=tuple(element.inlet_refs))
        elif isinstance(element, RainGarden):
            rim = element.rim_elevation.meters
            lip = (element.overflow_invert.meters
                   if element.overflow_invert is not None else rim)
            network.nodes[element.tag] = DrainNode(
                # Water ARRIVES anywhere up to the rim; the basin disposes by infiltration
                # and lets the excess go over its overflow lip.
                tag=element.tag, kind="rain_garden", in_invert_m=rim, out_invert_m=lip,
                disposes=True, inlet_refs=tuple(element.inlet_refs))
        elif isinstance(element, Downspout) and element.discharge_ref:
            # Only a leader that NAMES a receiver joins the graph: a splash block is not a
            # connection, and every leader authored before this field stays out.
            ext = element.extension
            network.nodes[element.tag] = DrainNode(
                tag=element.tag, kind="leader", in_invert_m=None,
                out_invert_m=ext.outlet_invert.meters if ext is not None else None)
        elif isinstance(element, FootingBedding) and element.drain_tile:
            spec = element.drain_tile_spec
            network.nodes[element.tag] = DrainNode(
                tag=element.tag, kind="footing_tile",
                in_invert_m=None, out_invert_m=None)
            del spec

    def add(source: str, target: str | None, kind: EdgeKind,
            out_invert_m: float | None) -> None:
        if not target:
            return
        resolved = _resolve_target(target, by_tag, sumps, network)
        if resolved is None:
            network.unresolved.append((source, target))
            return
        network.edges.append(DrainEdge(source, resolved, kind, out_invert_m))

    for element in elements:
        if isinstance(element, FrenchDrain):
            node = network.nodes[element.tag]
            add(element.tag, element.discharge_ref or _tile_discharge(element.tile),
                EdgeKind.PRIMARY, node.out_invert_m)
            add(element.tag, element.overflow_ref, EdgeKind.OVERFLOW,
                element.overflow_invert.meters
                if element.overflow_invert is not None else node.out_invert_m)
        elif isinstance(element, (Drywell, RainGarden)):
            add(element.tag, element.overflow_ref, EdgeKind.OVERFLOW,
                network.nodes[element.tag].out_invert_m)
        elif isinstance(element, Downspout) and element.discharge_ref:
            add(element.tag, element.discharge_ref, EdgeKind.PRIMARY,
                network.nodes[element.tag].out_invert_m)
        elif isinstance(element, Sump):
            if element.pump is not None:
                add(element.tag, element.pump.discharge, EdgeKind.PRIMARY, None)
            add(element.tag, element.overflow_ref, EdgeKind.OVERFLOW,
                network.nodes[element.tag].out_invert_m)
        elif isinstance(element, FootingBedding) and element.drain_tile:
            add(element.tag, _tile_discharge(element.drain_tile_spec),
                EdgeKind.PRIMARY, None)

    return network


def _resolve_target(target: str, by_tag: dict, sumps: list,
                    network: DrainageNetwork) -> str | None:
    """A discharge string to a node tag, or ``None`` where it names nothing resolvable.

    Three answers and they are all real: a tag, the ``"daylight"`` terminal, and
    ``"sump"`` — a KIND, resolvable only where the plan has exactly one. More than one and
    it stays unresolved, because choosing between two pits is inventing a connection.
    """
    text = target.strip()
    if text.lower() == DAYLIGHT:
        return DAYLIGHT
    if text.lower() == SUMP_KEYWORD:
        return sumps[0].tag if len(sumps) == 1 else None
    if text in network.nodes:
        return text
    if text in by_tag:
        # A real element that is not a drainage node — a pipe run, a slab. Named so the
        # caller can say WHICH kind of wrong it is.
        return None
    return None


# --- Connected bodies of stone, and whether a named connection is a real one --------------
#
# ** A NAMED CONNECTION WITH NO GEOMETRY IS THE SAME DEFECT ONE LEVEL UP. ** `drain_tile.py`
# derives a CLOSED RING per bedding — a loop of pipe around one footing, with no lead out of
# it. Nineteen of catlin's house beddings each named the radon sump, the name resolved every
# time, and not one inch of pipe ran between any of them and the pit. The court had the same
# defect and it was fixed by hand, by authoring two lead runs and reasoning in a comment
# about which beds are "ONE excavation ... a single connected body of washed stone at one
# invert". This is that reasoning, done by the engine instead of by a paragraph.
#
# Two beds are one body when their stone touches in plan AND overlaps in section. Both
# halves matter: two rings at the same level three feet apart are two bodies, and two rings
# that overlap in plan at elevations four feet apart are also two.

#: How close two beds' outlines must come to count as one body of stone, metres. 1" — an
#: abutment authored as a shared edge lands on it exactly, and a survey rounding does not
#: open a gap the water does not see.
BODY_TOUCH_TOLERANCE_M = 0.0254


def _touching(first, second) -> bool:
    from shapely.geometry import Polygon

    if len(first.outline) < 3 or len(second.outline) < 3:
        return False
    if (first.z0_m >= second.z1_m + BODY_TOUCH_TOLERANCE_M
            or second.z0_m >= first.z1_m + BODY_TOUCH_TOLERANCE_M):
        return False
    return (Polygon(first.outline).distance(Polygon(second.outline))
            <= BODY_TOUCH_TOLERANCE_M)


def stone_bodies(model) -> dict[str, frozenset[str]]:
    """``bedding tag -> the set of bedding tags its stone is continuous with``.

    Connected components over "touches in plan and overlaps in section". A bed is always in
    its own body, so a lone ring maps to a set of one — which is the answer, not a failure.
    """
    beds = [b for b in model.footing_beddings if b.drain_tile]
    parent = {bed.tag: bed.tag for bed in beds}

    def find(tag: str) -> str:
        while parent[tag] != tag:
            parent[tag] = parent[parent[tag]]
            tag = parent[tag]
        return tag

    for index, first in enumerate(beds):
        for second in beds[index + 1:]:
            if _touching(first, second):
                parent[find(second.tag)] = find(first.tag)

    bodies: dict[str, set[str]] = {}
    for bed in beds:
        bodies.setdefault(find(bed.tag), set()).add(bed.tag)
    return {tag: frozenset(members)
            for members in bodies.values() for tag in members}

"""Does site drainage actually get the water somewhere, and downhill?

``checks/mep/drainage.py`` resolves the NAMES in a discharge chain — the thing a string
beside a string can be held to. These rules walk the chain
(``resolve/drainage_network.py``) and ask what the names could never answer:

* the water gets to something that disposes of it, by a route that exists;
* the pipe **arrives** rather than ending in undisturbed ground above what it feeds;
* a run that is authored to fall, falls;
* what a run says it discharges into, says so back;
* and every disposal point — a soakaway, a pump — has somewhere to send water when it
  stops working, because a below-grade court with one outfall has none.

** WHY THESE DID NOT EXIST UNTIL 2026-09-14. ** Every slope and invert rule in this engine
was scoped to ``PipeRun``. A ``FrenchDrain`` carried one scalar invert and the resolver
extruded the whole trench dead level, a ``Drywell`` had no way out, a ``Sump`` had no inlet
level to check anything against, and nothing walked a chain. The consequences were visible
only in the drawings: catlin's field lateral ended 28 inches above the stone it feeds and
its nineteen house perimeter rings were closed loops with no lead to anything.

ADVISORY, like their siblings in ``drainage.py``, and for the same reason: a drainage chain
that does not resolve may be an incomplete drawing set rather than a building that floods.
It is still a FAIL — ``haus check`` exits 1 on one — because the alternative is a rule that
nobody has to answer.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable
from typehaus.checks._authoring import passed as _pass
from typehaus.findings import Finding, Result
from typehaus.model.mep import Sump
from typehaus.model.structure import Drywell, FrenchDrain
from typehaus.resolve.drainage_network import DAYLIGHT, EdgeKind, build_network

from typehaus.checks.mep.drainage_receivers import (  # isort: skip
    ARRIVAL_TOLERANCE_M,
    PLAN_ARRIVAL_SLACK_M,
    area_drain_arrivals,
    body_touches,
    reaches_through_stone,
    receiver_footprints,
    run_starts_in,
    soakaway_arrival,
)
from typehaus.checks.mep.landscape_drainage import leader_arrivals  # isort: skip

from typehaus.checks.registry import CheckContext, Tier, check  # isort: skip

#: Discharge targets that have no geometry to reach, so "does the stone touch it" is not a
#: question about them. Daylight is a direction, not a place.
_NON_SPATIAL_TARGETS = frozenset({DAYLIGHT})


def _elements(ctx: CheckContext):
    for storey in ctx.model.plan.storeys:
        yield from ctx.model.plan.storey_elements(storey.tag)


def _network(ctx: CheckContext):
    return build_network(ctx.model.plan)


@check(Tier.ADVISORY, "drainage.network_outfall")
def network_outfall(ctx: CheckContext) -> list[Finding]:
    """Every source of water reaches something that disposes of it.

    Disposal is daylight, a soakaway (the soil takes it) or a pit with a pump (it leaves
    under power). A walk that runs out of edges, meets a target that is not a drainage
    element, or circles without ever reaching one, is the finding — and the message carries
    the path, because "it does not drain" is useless and "FB-B-N1 -> SM-B-RADON -> nothing"
    is a work item.
    """
    cid = "drainage.network_outfall"
    network = _network(ctx)
    sources = network.sources()
    if not sources:
        return [not_applicable(cid, "this plan authors no drain tile or french drain")]

    out: list[Finding] = []
    for source, target in sorted(network.unresolved):
        out.append(advisory(
            cid, f"{source} discharges to {target!r}, which is not a drainage element — "
                 f"a tag that resolves to a wall or a pipe is not somewhere water can go",
            (source,), Result.FAIL))
    for source in sources:
        reached, path, problem = network.reaches_disposal(
            source, first_hop=EdgeKind.PRIMARY)
        if not reached:
            out.append(advisory(
                cid, f"{source} does not reach an outfall: {problem} "
                     f"(followed {' -> '.join(path)})",
                (source,), Result.FAIL))
    if not out:
        out.append(_pass(cid, f"all {len(sources)} drainage sources reach an outfall"))
    return out


@check(Tier.ADVISORY, "drainage.network_fallback")
def network_fallback(ctx: CheckContext) -> list[Finding]:
    """Every disposal point has somewhere to send water when it stops working.

    A soakaway's whole design is that the soil takes water faster than it arrives; a pump's
    is that it has power. Both assumptions fail, and a court nine feet below grade with one
    outfall and no fallback is the case where failing matters. Daylight is exempt — it *is*
    the fallback, and there is nothing to ask of it.

    The fallback must reach a **different** disposal point, which is the whole content of
    the rule: a well whose overflow leads back to itself has answered nothing.
    """
    cid = "drainage.network_fallback"
    network = _network(ctx)
    points = network.disposal_points()
    if not points:
        return [not_applicable(cid, "this plan has no soakaway and no pumped pit")]

    out: list[Finding] = []
    # Soakaway beds are graded per BODY of stone: water in one bed is in all of them, so
    # the heads are the members with an overflow, and the whole body is excluded.
    bodies = _soakaway_bodies(ctx, network)
    for body in sorted(set(bodies.values()), key=sorted):
        heads = sorted(t for t in body if network.out_edges(t, EdgeKind.OVERFLOW))
        found = None
        problem = f"no bed of {', '.join(sorted(body))} states an overflow"
        for head in heads:
            reached, path, problem = network.reaches_disposal(
                head, first_hop=EdgeKind.OVERFLOW, not_being=body)
            if reached:
                found = path
                break
        tags = tuple(sorted(body))
        if found is None:
            out.append(advisory(
                cid, f"stone body {', '.join(tags)} has no fallback outfall: {problem}",
                tags, Result.FAIL))
        else:
            out.append(_pass(cid, f"stone body of {len(tags)} bed(s) falls back to "
                                  f"{found[-1]} ({' -> '.join(found)})", tags))
    for tag in points:
        if tag in bodies:
            continue
        reached, path, problem = network.reaches_disposal(
            tag, first_hop=EdgeKind.OVERFLOW, not_being=tag)
        if not reached:
            out.append(advisory(
                cid, f"{tag} has no fallback outfall: {problem}. A soakaway in saturated "
                     f"soil and a pump with no power both stop taking water, and nothing "
                     f"says where it goes then",
                (tag,), Result.FAIL))
        else:
            out.append(_pass(
                cid, f"{tag} falls back to {path[-1]} ({' -> '.join(path)})", (tag,)))
    return out


def _soakaway_bodies(ctx: CheckContext, network) -> dict[str, frozenset[str]]:
    """``soakaway bed -> its whole body of stone`` (plain beds in it included)."""
    from typehaus.resolve.drainage_network import stone_bodies

    bodies = stone_bodies(ctx.model)
    return {tag: bodies.get(tag, frozenset({tag})) for tag, node in network.nodes.items()
            if node.kind == "soakaway"}


@check(Tier.ADVISORY, "drainage.outfall_connection")
def outfall_connection(ctx: CheckContext) -> list[Finding]:
    """A run arrives in what it discharges to, rather than ending above it.

    Two ways to miss and both have happened in this house. **In section**, the outlet sits
    above the receiver's own inlet — catlin's field lateral ended 28" over the top of the
    stone it fed, discharging into undisturbed clay, and the name resolved perfectly.
    **In plan**, the run's last vertex lands outside the receiver's footprint, which reads
    in section as a pipe that stops short.

    Only graded where both ends state a level. A receiver with no inlet invert is reported
    as such rather than assumed to be at the run's own — inventing the number is how a
    broken gradient comes to look checked.
    """
    cid = "drainage.outfall_connection"
    network = _network(ctx)
    runs = {e.tag: e for e in _elements(ctx) if isinstance(e, FrenchDrain)}
    leader_count, leader_findings = leader_arrivals(ctx, network)
    drain_count, drain_findings = area_drain_arrivals(ctx, network)
    if not runs and not leader_count and not drain_count:
        return [not_applicable(cid, "this plan authors no french drain")]

    # A drywell's diameter is its shaft and a sump's is its pit; both are the footprint a
    # run has to land inside, so one branch serves both.
    receivers = {e.tag: (e.position, e.diameter.meters / 2.0) for e in _elements(ctx)
                 if isinstance(e, (Drywell, Sump))}

    out: list[Finding] = []
    for edge in network.edges:
        run = runs.get(edge.source)
        if run is None or edge.kind is not EdgeKind.PRIMARY:
            continue
        node = network.nodes.get(edge.target)
        if node is None:
            continue
        if node.kind == "soakaway":
            why = soakaway_arrival(ctx, edge.target, run.path[-1].xy_m, edge.out_invert_m)
            if why is not None:
                out.append(advisory(cid, f"{run.tag} does not arrive in {edge.target}: {why}",
                                    (run.tag, edge.target), Result.FAIL))
            continue
        if node.in_invert_m is None:
            if edge.target in receivers:
                out.append(advisory(
                    cid, f"{run.tag} discharges to {edge.target}, which states no inlet "
                         f"level — nothing can say whether the pipe arrives in it",
                    (run.tag, edge.target), Result.UNKNOWN))
            continue
        if edge.out_invert_m is not None:
            above_m = edge.out_invert_m - node.in_invert_m
            if above_m > ARRIVAL_TOLERANCE_M:
                out.append(advisory(
                    cid, f"{run.tag} discharges at {edge.out_invert_m / 0.0254:.0f}\" and "
                         f"{edge.target} takes water at {node.in_invert_m / 0.0254:.0f}\" — "
                         f"the outlet hangs {above_m / 0.0254:.0f}\" above it, into "
                         f"undisturbed ground",
                    (run.tag, edge.target), Result.FAIL))
        placement = receivers.get(edge.target)
        if placement is not None:
            centre, radius = placement
            end = run.path[-1]
            reach = ((end.x.meters - centre.x.meters) ** 2
                     + (end.y.meters - centre.y.meters) ** 2) ** 0.5
            # A run does not have to END at the shaft. Continuous stone IS a connection —
            # it is the whole argument `tile_lead` makes for a bedding, and the court's own
            # authoring makes it by hand for FB-SG-ARCH ("it feeds the column through its
            # side and a lead would be a pipe running uphill"). Demanding that every trench
            # terminate on the receiver would refuse the way this house is actually built.
            if reach > radius + PLAN_ARRIVAL_SLACK_M and not reaches_through_stone(
                    ctx, run, edge.target):
                out.append(advisory(
                    cid, f"{run.tag} ends {reach / 0.0254:.0f}\" from {edge.target}'s "
                         f"centre, outside its {radius / 0.0254:.0f}\" radius, and its "
                         f"trench touches no stone that reaches it — the run stops short of "
                         f"the thing it discharges to",
                    (run.tag, edge.target), Result.FAIL))
    out.extend(leader_findings)
    out.extend(drain_findings)
    if not out:
        out.append(_pass(cid, f"every french drain arrives in what it discharges to "
                              f"({len(runs)} runs, {leader_count} leader extensions, "
                              f"{drain_count} area drains)"))
    return out


@check(Tier.ADVISORY, "drainage.trench_fall")
def trench_fall(ctx: CheckContext) -> list[Finding]:
    """A run authored with a fall falls the way it is drawn: start high, discharge end low.

    A LEVEL run is not a fault and is not reported as one — an interceptor trench is
    routinely dead level, and every french drain in this engine was level by construction
    until ``end_invert`` existed. What this refuses is a run whose two authored inverts say
    the water runs uphill, which is the mistake the field can neither see nor build.
    """
    cid = "drainage.trench_fall"
    runs = [e for e in _elements(ctx) if isinstance(e, FrenchDrain)]
    if not runs:
        return [not_applicable(cid, "this plan authors no french drain")]

    out: list[Finding] = []
    falling = 0
    for run in runs:
        if run.end_invert is None:
            continue
        rise_m = run.end_invert.meters - run.invert.meters
        if rise_m > 1e-9:
            out.append(advisory(
                cid, f"{run.tag} runs uphill: its discharge end is "
                     f"{rise_m / 0.0254:.1f}\" ABOVE its start",
                (run.tag,), Result.FAIL))
        else:
            falling += 1
    if not out:
        out.append(_pass(cid, f"{falling} of {len(runs)} french drains author a fall, and "
                              f"every one of them falls toward its discharge"))
    return out


@check(Tier.ADVISORY, "drainage.inlet_reciprocity")
def inlet_reciprocity(ctx: CheckContext) -> list[Finding]:
    """What a run discharges into names it back.

    One-sided naming is how a connection becomes an aspiration. Nineteen of this house's
    perimeter rings named the radon sump and nothing on the sump named them, so there was no
    way to tell an authored connection from a hope — and the sump's own capacity was being
    reasoned about without a list of what feeds it.

    A receiver that names NO inlets at all is silent rather than wrong, and reports UNKNOWN:
    it has made no claim, which is a different thing from contradicting one.
    """
    cid = "drainage.inlet_reciprocity"
    network = _network(ctx)
    out: list[Finding] = []
    claimed: dict[str, list[str]] = {}
    for edge in network.edges:
        if edge.kind is EdgeKind.PRIMARY:
            claimed.setdefault(edge.target, []).append(edge.source)

    for target, feeders in sorted(claimed.items()):
        node = network.nodes.get(target)
        if node is None or node.kind not in {"drywell", "sump", "rain_garden", "soakaway"}:
            continue
        if not node.inlet_refs:
            out.append(advisory(
                cid, f"{len(feeders)} run(s) discharge to {target} and it names no inlets "
                     f"at all — nothing distinguishes an authored connection from a hope "
                     f"({', '.join(sorted(feeders)[:6])}"
                     f"{'...' if len(feeders) > 6 else ''})",
                (target,), Result.UNKNOWN))
            continue
        orphans = sorted(set(feeders) - set(node.inlet_refs))
        if orphans:
            out.append(advisory(
                cid, f"{target} is discharged to by {', '.join(orphans)}, which it does not "
                     f"list in inlet_refs", (target, *orphans), Result.FAIL))
    if not out:
        out.append(_pass(cid, "every receiver names what discharges into it"))
    return out


@check(Tier.ADVISORY, "drainage.tile_lead")
def tile_lead(ctx: CheckContext) -> list[Finding]:
    """A footing bedding that names a receiver has a way to reach it.

    ``resolve/drain_tile.py`` derives a **closed ring** per bedding — a loop of pipe around
    one footing with no lead out of it. So a bedding's ``discharge`` is only ever a claim
    about somewhere else, and there are exactly two things that can make it true:

    * the bed's stone is **continuous with** the receiver — it abuts it in plan and overlaps
      it in section, so water in the ring is already in the thing it drains to; or
    * an authored ``FrenchDrain`` **starts in that body of stone** and discharges to the
      same receiver.

    Continuity is taken across the whole connected body, not one bed: catlin's court reasons
    exactly this way by hand ("the five wall beds are ONE excavation ... a single connected
    body of washed stone at one invert"), and a body's lead serves every ring in it.

    ** THIS IS THE RULE THAT WOULD HAVE CAUGHT NINETEEN NAMED CONNECTIONS WITH NO PIPE. **
    Every one of catlin's house perimeter rings said it discharged to the radon sump,
    ``discharge_consistency`` resolved the tag nineteen times, and no lead existed.
    """
    cid = "drainage.tile_lead"
    from typehaus.resolve.drainage_network import BODY_TOUCH_TOLERANCE_M, stone_bodies

    beds = {bed.tag: bed for bed in ctx.model.footing_beddings if bed.drain_tile}
    claiming = {tag: bed.drain_tile_spec.discharge for tag, bed in beds.items()
                if bed.drain_tile_spec is not None and bed.drain_tile_spec.discharge}
    if not claiming:
        return [not_applicable(cid, "no footing bedding names where its tile discharges")]

    bodies = stone_bodies(ctx.model)
    footprints = receiver_footprints(ctx)
    runs = [e for e in _elements(ctx) if isinstance(e, FrenchDrain)]
    network = _network(ctx)

    out: list[Finding] = []
    served: set[str] = set()
    for tag, discharge in sorted(claiming.items()):
        target = None
        for edge in network.out_edges(tag, EdgeKind.PRIMARY):
            target = edge.target
        if target is None or target in _NON_SPATIAL_TARGETS:
            continue  # daylight; drainage.network_outfall owns the unresolved case
        if target not in footprints:
            out.append(advisory(
                cid, f"{tag}'s tile discharges to {target}, whose solid does not resolve — "
                     f"nothing can say whether the stone reaches it",
                (tag, target), Result.UNKNOWN))
            continue
        body = bodies.get(tag, frozenset({tag}))
        if body_touches(ctx, body, footprints[target], BODY_TOUCH_TOLERANCE_M):
            served.add(tag)
            continue
        if any(run_starts_in(run, ctx, body)
               and any(e.target == target for e in
                       network.out_edges(run.tag, EdgeKind.PRIMARY))
               for run in runs):
            served.add(tag)
            continue
        out.append(advisory(
            cid, f"{tag}'s tile says it discharges to {discharge!r}, and nothing carries it "
                 f"there: its stone body ({len(body)} bed(s)) neither reaches {target} nor "
                 f"is served by a french drain that does. A derived ring is a CLOSED loop "
                 f"with no lead out of it",
            (tag, target), Result.FAIL))
    if not out:
        out.append(_pass(cid, f"every drained bedding reaches what it names "
                              f"({len(served)} of {len(claiming)})"))
    return out

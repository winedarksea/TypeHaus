"""``haus route --group``: one bathroom group laid in UPC 908.2 order (horizontal wet vent).

``routing/group_order`` names the roles: the dry-vented drain and its vent, then the wet arms
in flow order, the water closet last. The group's own branches and vents are lifted first and
its tie run kept; each step is searched on a model holding the steps before it
(``route_eval.candidate_plan_for_all``, re-resolved), so a wet arm finds the wet vent as an
authored drain (``route_fixture_wet``, ``mep_drain_routing_basis.md`` §14). The dry drain is
split at its vent take-off: the arm keeps its size, and the wet vent from the tee to the tie is
908.2.1.2's size its whole length. ``houses/catlin/notes/mep_group_wet_vent_basis.md``.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import typer

from typehaus.cli._shared import console
from typehaus.cli.group_ties import tie_stations
from typehaus.cli.route_options import RouteOptions
from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.group_order import GroupOrder
    from typehaus.routing.proposal import RouteProposal

#: ``mep.fixture_drain_reach``'s band round the storey datum, where a group may tie in.
_BAND_BELOW_M, _BAND_ABOVE_M = 24 * M_PER_IN, 6 * M_PER_IN
_SUBFLOOR_M = 0.75 * M_PER_IN


def route_group(model: ResolvedModel, group: str, opts: RouteOptions) -> int:
    """Lay ``group`` (a fixture-group tag or a room) and report; return the exit code.

    Owns its own reporting (``route_report.report_proposals`` with ``opts``): each laid
    step is re-resolved before the next, so no single proposal list exists up front.
    Raise ``typer.Exit(2)`` for a ``group`` that names nothing; ``opts.out_dir`` is already
    validated outside the house's plan/."""
    from typehaus.cli.route_report import report_proposals

    if group_room(model, group) is None:
        console.print(f"[red]--group {group}: names no room (a Room tag, or the end of one "
                      "such as BATH2 for RM-M-BATH2)[/red]")
        raise typer.Exit(2)
    proposals, problems, notices, refusals = group_proposals(model, group, opts)
    evaluations = []
    if proposals and opts.evaluate:
        from typehaus.cli.route_eval import evaluate_network

        network = evaluate_network(opts.directory, model, [p for p, _s in proposals])
        network.tag = f"{group} (the group together)"
        evaluations.append(network)
    report_proposals(model, opts.directory, proposals, evaluations=evaluations,
                     problems=problems, notices=notices, refusals=refusals, clock=opts.timing,
                     cost=opts.cost, explain=opts.explain, as_json=opts.as_json,
                     summary=opts.summary, out_dir=opts.out_dir)
    return 1 if not proposals and (problems or refusals) else 0


def group_room(model: ResolvedModel, group: str) -> str | None:
    """The Room tag ``group`` names: itself, or the one room whose tag ends ``-<group>``."""
    tags = [r.tag for r in model.plan.all_elements() if r.element_kind == "Room"]
    if group in tags:
        return group
    hits = [t for t in tags if t.endswith(f"-{group}")]
    return hits[0] if len(hits) == 1 else None


def group_proposals(model: ResolvedModel, group: str, opts: RouteOptions
                    ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str], list]:
    """``(proposal/storey pairs, problems, notices, refusals)`` — ``_propose``'s shape.

    A wet arm that cannot be laid (no 908.2 join in reach, or a wet vent its weir holds too
    high to find a lane), or a dry fixture whose own arm and vent find no route, is held to
    its own vent and the group laid again without it, at most twice; each such retreat is a
    notice, never silent."""
    from typehaus.routing.group_order import group_order

    problems: list[str] = []
    room = group_room(model, group)
    plan = None if room is None else _group_plan(model, room, problems)
    if plan is None:
        return [], problems or [f"{group}: names no room"], [], []
    members, storey, tie_run, band, near = plan
    own: frozenset[str] = frozenset()
    notices: list[str] = []
    passes: list[str] = []  # every pass's problems, tagged, the last early return included
    seen: list = []
    for attempt in range(3):
        order = group_order(members, own)
        if isinstance(order, str):
            return [], [*problems, *passes, f"{room}: no 908.2 group — {order}"], notices, seen
        ties = _ties(model, set(order.laying), tie_run, band, (storey, near))
        laid, tried, refusals, blame = _lay(model, room, order, storey, ties, tie_run, opts)
        done = _laid_fixtures(order, laid)
        label = _pass_label(attempt, order.dry, own)
        passes += [f"[{label}] {line}" for line in tried]
        seen += [replace(r, attempts=(f"group {label}", *r.attempts)) for r in refusals]
        if not blame or set(blame) <= own or attempt == 2:
            break
        notices.append(f"{room}: {', '.join(blame)} held to its own vent and the group laid "
                       f"again — {tried[-1] if tried else 'no wet join'}")
        own |= set(blame)
    if done:
        left = order.laying[len(done):]
        notices.append(f"{room}: {order.why}; laid {' -> '.join(done)}, tied to {tie_run}"
                       + (f"; {' -> '.join(left)} unlaid" if left else ""))
    else:
        notices.append(f"{room}: {order.why}; nothing laid")
    # The runs lifted are exactly what the laid fixtures stand in for: never the tie run by
    # serves, and never the drain of a fixture left unlaid.
    lifted = tuple(sorted(_lifted(model, set(done))))
    laid = [replace(p, replaces=lifted) for p in laid]
    notices += [f"{t}: keeps its own vent and authored tie (908.2.1.3, 908.2.1.5)"
                for t in order.own_vent if done]
    return [(p, storey) for p in laid], [*problems, *passes], notices, seen


def _laid_fixtures(order: GroupOrder, laid: list) -> tuple[str, ...]:
    """The fixtures ``laid`` holds: the dry arm, wet vent and dry vent stand for the first,
    each later proposal for the next."""
    return order.laying[:max(0, len(laid) - 2)]


def _pass_label(attempt: int, dry: str, held: frozenset[str]) -> str:
    """``pass 2: SH dry, TUB held`` — fixture tags by their last word."""
    held_words = sorted(t.rsplit("-", 1)[-1] for t in held)
    return (f"pass {attempt + 1}: {dry.rsplit('-', 1)[-1]} dry"
            + (f", {', '.join(held_words)} held" if held else ""))


def _lay(model: ResolvedModel, room: str, order: GroupOrder, storey: str, ties: list,
         tie_run: str, opts: RouteOptions) -> tuple[list, list[str], list, tuple[str, ...]]:
    """One pass in ``order``: ``(laid, problems, refusals, wet arms to blame)``."""
    problems: list[str] = []
    refusals: list = []
    laid: list[RouteProposal] = []
    work = _resolved(_without(model, _lifted(model, set(order.laying))), problems)
    for step, fixture in enumerate(order.laying):
        if work is None:
            break
        touch = frozenset({tie_run, *(p.tag for p in laid)})
        if step == 0:
            found, ties = _first_step(work, fixture, ties, touch, opts, problems, refusals)
        else:
            found = _step(work, fixture, ties[0], touch, laid[1].tag, opts, problems, refusals)
        if found is not None and step == 0:
            found = _dry(work, found, (ties, storey), touch, room, order, opts, problems,
                         refusals)
            if found is None and _ceiling(work, order, storey) is not None:
                return [], problems, refusals, order.wet
        if found is None:
            problems.append(f"{room}: {fixture} could not be laid, so the group stops "
                            f"there ({' -> '.join(order.laying[step:])} unlaid)")
            # A wet arm, or the dry fixture itself, is held to its own vent; never the WC.
            held = fixture in order.wet or (step == 0 and fixture not in order.last)
            return laid, problems, refusals, (fixture,) if held else ()
        if step == 0:
            laid = list(found)
        else:
            arm, branch, vent = laid[:3]
            laid = [arm, replace(branch, serves=(*branch.serves, fixture)),
                    replace(vent, serves=(*vent.serves, fixture)), *laid[3:], found[0]]
        if step < len(order.laying) - 1:
            work = _resolved(_with(work, laid), problems)
    return laid, problems, refusals, ()


def _first_step(work: ResolvedModel, fixture: str, ties: list, touch: frozenset[str],
                opts: RouteOptions, problems: list[str], refusals: list
                ) -> tuple[tuple | None, list]:
    """The dry fixture's drain and vent to the first tie station that takes it, and ``ties``
    with that station first (the rest follow it into ``_dry`` and the later steps). A refused
    station's problems and refusals go when a later one lays; when none does, each stays,
    its refusal tagged with the station it was searched to. At most ``len(ties)`` searches
    (``group_ties.MAX_TIES``)."""
    tried = len(problems), len(refusals)
    for i, tie in enumerate(ties):
        before = len(problems), len(refusals)
        found = _step(work, fixture, tie, touch, None, opts, problems, refusals)
        if found is not None:
            del problems[tried[0]:before[0]], refusals[tried[1]:before[1]]
            return found, [tie, *ties[:i], *ties[i + 1:]]
        x, y, z = (c / M_PER_IN for c in tie)
        label = f"tie {i + 1} of {len(ties)} at ({x:g}\", {y:g}\", z {z:.1f}\")"
        refusals[before[1]:] = [replace(r, attempts=(label, *r.attempts))
                                for r in refusals[before[1]:]]
    return None, ties


def _dry(work: ResolvedModel, found: tuple, at: tuple, touch: frozenset[str], room: str,
         order: GroupOrder, opts: RouteOptions, problems: list[str], refusals: list
         ) -> tuple[RouteProposal, ...] | None:
    """``(arm, wet vent, dry vent)``: the dry fixture's arm cut at its vent take-off, and
    the wet vent searched afresh from that tee to the tie at 908.2.1.2's size (PB0225: "its
    entire length back to the dry vent served"), the dry vent at UPC 904's size for it."""
    from typehaus.cli.route_support import Endpoints
    from typehaus.routing.trades import pipe as pipe_trade
    from typehaus.routing.trap_vent import vent_size_m

    (ties, storey), (drain, vent) = at, found
    if vent is None:
        problems.append(f"{drain.tag}: no dry vent was found to carry the group, so nothing "
                        "can be wet-vented off it")
        return None
    arm = _cut_arm(drain, vent.points[0])
    size = max(order.wet_vent_in * M_PER_IN, drain.diameter_m)
    vent = replace(vent, diameter_m=max(vent.diameter_m, vent_size_m(size)))
    model = _resolved(_with(work, [arm, vent]), problems)
    if model is None:
        return None
    ends = Endpoints(origin=arm.points[-1], root=tuple(ties[0]), kind="pipe", system="drain",
                     weir_m=_ceiling(model, order, storey),
                     radius_m=pipe_trade.radius_m(size), diameter_m=size, storey=storey,
                     cavity_radius_m=pipe_trade.cavity_radius_m(size, "drain"),
                     serves=arm.serves, falls=True, touch=touch | {arm.tag, vent.tag})
    # Each tie station in turn: the next is tried only where the one before refused.
    tried = len(problems), len(refusals)
    for tie in ties:
        made = _search(model, replace(ends, root=tuple(tie)), f"{room}-WV", (), opts,
                       problems, refusals)
        if made is not None:
            del problems[tried[0]:], refusals[tried[1]:]
            break
    if made is None:
        return None
    branch = replace(made[0], notes=[
        *made[0].notes, f"the group's wet vent from {vent.tag}'s tee to the tie, "
        f"Ø{size / M_PER_IN:g}\" its whole length for {order.dfu:g} DFU (908.2.1.2, PB0225)"])
    return arm, branch, vent


def _group_plan(model: ResolvedModel, room: str, problems: list[str]) -> tuple | None:
    """``(members, storey, tie run, band)`` measured off the authored model; flow is read
    to the tie run's highest clear point in the band, which no role assignment moves."""
    from typehaus.model.enums import Service
    from typehaus.resolve.fixture_units import fixture_units
    from typehaus.resolve.mep_sleeves import _expected_drain_point, expected_port_point
    from typehaus.resolve.mep_trap_arm import drain_parent, run_points, under_floor_weir_m
    from typehaus.routing.group_order import Member

    units = {u.tag: u for u in fixture_units(model.plan) if u.dfu}
    storey = next(s for s in model.plan.storeys
                  if any(getattr(e, "tag", None) == room
                         for e in model.plan.storey_elements(s.tag)))
    datum = storey.elevation.meters
    fixtures = [f for f in model.plan.storey_elements(storey.tag)
                if f.element_kind == "Fixture" and getattr(f, "room", None) == room
                and f.tag in units]
    points = {f.tag: p for f in fixtures if (p := _expected_drain_point(model, f.tag))}
    if not points:
        problems.append(f"{room}: no drained fixture with a resolvable drain point")
        return None
    drains = {r.tag: pts for r in model.pipe_runs
              if r.system == "drain" and (pts := run_points(r)) is not None}
    radii = {r.tag: r.diameter_m / 2.0 for r in model.pipe_runs if r.tag in drains}
    own = {t for t in _lifted(model, set(points)) if t in drains}
    parents = Counter(p[0] for t in own
                      if (p := drain_parent(drains[t][-1], t, drains, radii)) and p[0] not in own)
    if not parents:
        problems.append(f"{room}: its fixtures' drains tie into no run outside the group, so "
                        "there is no tie to lay the group to")
        return None
    tie_run = parents.most_common(1)[0][0]
    band = (datum - _BAND_BELOW_M, datum + _BAND_ABOVE_M)
    near = (sum(p[0] for p in points.values()) / len(points),
            sum(p[1] for p in points.values()) / len(points))
    ties = tie_stations(model, [], drains[tie_run], band, frozenset(own), (str(storey.tag), near))
    if not ties:
        problems.append(f"{room}: {tie_run} has no station within 2 ft below and 6 in above "
                        f"the {storey.tag} datum (mep.fixture_drain_reach's band) clear of "
                        "the wyes already on it")
        return None
    members = []
    for tag, point in sorted(points.items()):
        port = expected_port_point(model, tag, Service.DRAIN)
        members.append(Member(
            tag=tag, symbol=units[tag].symbol, dfu=units[tag].dfu,
            floor_level=under_floor_weir_m(model, tag, datum, port) is not None,
            flow_m=abs(point[0] - ties[0][0]) + abs(point[1] - ties[0][1])))
    return members, str(storey.tag), tie_run, band, near


def _ties(model: ResolvedModel, relaid: set[str], tie_run: str, band: tuple,
          site: tuple[str, tuple[float, float]]) -> list[tuple]:
    """The tie stations for the members re-laid: their own authored ties first, then the
    main's stations floor system by floor system (``group_ties``)."""
    from typehaus.resolve.mep_trap_arm import drain_parent, run_points

    drains = {r.tag: pts for r in model.pipe_runs
              if r.system == "drain" and (pts := run_points(r)) is not None}
    radii = {r.tag: r.diameter_m / 2.0 for r in model.pipe_runs if r.tag in drains}
    own = {t for t in _lifted(model, relaid) if t in drains}
    authored = sorted((drains[t][-1] for t in own
                       if (p := drain_parent(drains[t][-1], t, drains, radii)) and p[0] == tie_run),
                      key=lambda p: -p[2])
    return tie_stations(model, authored, drains[tie_run], band, frozenset(own), site)


def _lifted(model: ResolvedModel, fixtures: set[str]) -> set[str]:
    """The group's own runs: vents serving only ``fixtures``, and drains serving only them
    that start at one's drain point — never the stack or main they discharge into."""
    from typehaus.resolve.mep_sleeves import _expected_drain_point
    from typehaus.resolve.mep_trap_arm import START_TOL_M

    points = [p for t in fixtures if (p := _expected_drain_point(model, t))]
    out = set()
    for run in model.pipe_runs:
        if run.system not in ("drain", "vent") or not run.serves or not set(run.serves) <= fixtures:
            continue
        if run.system == "vent" or any(abs(run.path[0][0] - p[0]) + abs(run.path[0][1] - p[1])
                                       <= START_TOL_M for p in points):
            out.add(run.tag)
    return out


def _without(model: ResolvedModel, tags: set[str]) -> Any:
    plan = model.plan
    for storey in plan.storeys:
        current = plan.storey_elements(storey.tag)
        keep = tuple(e for e in current if getattr(e, "tag", None) not in tags
                     and getattr(e, "pipe_ref", None) not in tags)
        if len(keep) != len(current):
            plan = plan.with_elements(storey.tag, keep)
    return plan


def _with(work: ResolvedModel, laid: list[RouteProposal]) -> Any:
    """The working plan with ``laid`` in it, cleanouts left off: the next step routes round
    pipe, and a placed cleanout's access is graded on the final proposals, not here."""
    from typehaus.cli.route_eval import candidate_plan_for_all

    return candidate_plan_for_all(work, [replace(p, cleanouts=()) for p in laid])


def _resolved(plan: Any, problems: list[str]) -> ResolvedModel | None:
    from typehaus.resolve import resolve

    try:
        model, findings = resolve(plan)
    except (ValueError, TypeError, KeyError) as exc:
        problems.append(f"the group's working model would not resolve: {exc}")
        return None
    errors = [f.message for f in findings if f.severity.value == "error"]
    if errors:
        problems.append(f"the group's working model has errors: {'; '.join(errors[:2])}")
        return None
    return model


def _ceiling(model: ResolvedModel, order: GroupOrder, storey: str) -> float | None:
    """The highest the wet vent may run: half an arm diameter under the lowest floor-level
    wet arm's weir, so each meets it at or under its invert and within the one-diameter fall
    the S-trap rule allows (905.5/1002.4; ``route_fixture_wet.wet_goals``' window)."""
    from typehaus.cli.route_support import branch_diameter_m
    from typehaus.model.enums import Service
    from typehaus.resolve.mep_sleeves import expected_port_point
    from typehaus.resolve.mep_trap_arm import under_floor_weir_m

    datum = next(s.elevation.meters for s in model.plan.storeys if s.tag == storey)
    caps = [weir - (branch_diameter_m(model, (t,), [], t) or 0.0) / 2.0
            for t in order.wet
            if (weir := under_floor_weir_m(model, t, datum,
                                           expected_port_point(model, t, Service.DRAIN)))
            is not None]
    return min(caps, default=None)


def _step(model: ResolvedModel, fixture: str, tie: tuple, touch: frozenset[str],
          wet: str | None, opts: RouteOptions, problems: list[str], refusals: list
          ) -> tuple[RouteProposal, RouteProposal | None] | None:
    """One fixture's drain to the group's tie and, with no ``wet``, its vent; with ``wet``
    the only goals are 908.2 joins on that drain (the group's wet vent)."""
    from typehaus.cli.route_support import _endpoints

    ends = _endpoints(model, fixture, "fixture", problems)
    if ends is None:
        return None
    # Not ``ends.touch``: that pardons the main ``_nearest_main`` picked, which is not the tie.
    own = {r.tag for r in model.pipe_runs if r.system == "drain" and fixture in r.serves}
    onto = () if wet is None else (wet,)
    ends = replace(ends, root=tuple(tie), touch=frozenset({*own, *touch, *onto}),
                   wet_candidates=onto, weir_m=_closet_weir(model, fixture, ends))
    return _search(model, ends, fixture, ends.wet_candidates, opts, problems, refusals)


def _closet_weir(model: ResolvedModel, fixture: str, ends: Any) -> float | None:
    """Where a water closet's arm starts its grade: under the subfloor, its flange drop
    plumb above (the closet traps in its bowl, ``route_fall`` prepends the drop). Without
    it the arm is held at the flange, over the deck, and reaches no wet vent at all."""
    types = {t.tag: t.plan_symbol for t in model.plan.library.fixture_types}
    if not (types.get(getattr(model.plan.by_tag(fixture), "type_ref", None))
            or "").startswith("toilet"):
        return ends.weir_m
    datum = next(s.elevation.meters for s in model.plan.storeys if s.tag == ends.storey)
    return min(ends.origin[2], datum - _SUBFLOOR_M - (ends.cavity_radius_m or ends.radius_m))


def _search(model: ResolvedModel, ends: Any, target: str, wet: tuple[str, ...],
            opts: RouteOptions, problems: list[str], refusals: list
            ) -> tuple[RouteProposal, RouteProposal | None] | None:
    """``_propose``'s pipeline for one fixed-root falling run: space, lattice, gravity
    search, proposal, cleanouts and (for an arm) its vent."""
    from typehaus.cli.route_diagnose import refuse
    from typehaus.cli.route_duct_search import search_for
    from typehaus.cli.route_fixture_vent import vent_proposal
    from typehaus.cli.route_fixture_wet import wet_terminals
    from typehaus.cli.route_ports import terminal_refusal
    from typehaus.cli.route_proposal import one_proposal
    from typehaus.cli.route_propose import _with_cleanouts
    from typehaus.cli.route_support import _nearest, _root_nodes
    from typehaus.routing.graph import build_graph
    from typehaus.routing.gravity_band import prepare_falling
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space

    terminals = [ends.origin, ends.root, *wet_terminals(model, ends)]
    try:
        space = build_space(model, radius_m=ends.radius_m, terminals=terminals,
                            margin_ft=opts.margin_ft, avoid=opts.avoid, touch=ends.touch,
                            cost=opts.cost.for_run(ends.kind, ends.system), z_band=opts.band,
                            cavity_radius_m=ends.cavity_radius_m or None)
        space.bend_radius_m = ends.bend_radius_m
        prepare_falling(space, (min(ends.root[2], ends.origin[2]),
                                max(ends.root[2], ends.origin[2])), model)
        unreachable = terminal_refusal(space, ends, opts.band)
        if unreachable is not None:
            problems.append(f"{target}: {unreachable}")
            return None
        graph = build_graph(space, terminals, [ends.root[2]])
    except RoutingSpaceTooLarge as exc:
        problems.append(f"{target}: {exc}")
        return None
    start = _nearest(graph, ends.origin)
    goals = set() if wet else _root_nodes(graph, ends.root)
    if start is None or not (goals or wet):
        problems.append(f"{target}: no lattice node at the origin or the tie")
        return None
    search, report = search_for(model, graph, ends, opts.slope)
    found = search(graph, space, start, goals)
    if found is None:
        refused = refuse(space, graph, start, goals, target=target, ends=ends, report=report,
                         alternatives=1, margin_ft=opts.margin_ft, band=opts.band)
        refusals.append(refused)
        problems.append(refused.render())
        return None
    made = one_proposal(model, ends, found, target, "", opts.slope,
                        opts.details, problems, space=space)
    if made is None:
        return None
    made = _with_cleanouts(model, space, made)
    vent = (vent_proposal(found, made, ends, target, "")
            if getattr(found, "vent", None) is not None else None)
    return made, vent


def _cut_arm(drain: RouteProposal, tee: tuple) -> RouteProposal:
    """The drain from the trap to its vent take-off, the cleanouts on that stretch kept."""
    cut = _seg_index(tee, drain.points)
    head = [*drain.points[:cut + 1]]
    if math.dist(head[-1], tee) > 1e-6:
        head.append(tuple(tee))
    return replace(drain, points=head, cleanouts=tuple(
        c for c in drain.cleanouts if _seg_index(c.point, drain.points) < cut
        or _seg_dist(c.point, drain.points[cut], tee) < 1e-3))


def _seg_dist(p: tuple, a: tuple, b: tuple) -> float:
    d = [b[i] - a[i] for i in range(3)]
    span = sum(c * c for c in d)
    t = 0.0 if span == 0 else max(0.0, min(1.0, sum((p[i] - a[i]) * d[i]
                                                   for i in range(3)) / span))
    return math.dist(p, [a[i] + t * d[i] for i in range(3)])


def _seg_index(p: tuple, pts: list) -> int:
    return min(range(len(pts) - 1), key=lambda i: _seg_dist(p, pts[i], pts[i + 1]))

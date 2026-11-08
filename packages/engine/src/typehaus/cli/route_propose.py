"""One proposal pass per target: space, lattice, search, proposals; see docs/routing.md.

Bound into ``cmd_route`` (and its monkeypatch seams) by name; the campaign and scorecard
reach it through there too."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.cli.cmd_route_tree import _line_nodes
from typehaus.cli.route_duct_search import search_for as _search_for
from typehaus.cli.route_fixture_wet import wet_terminals
from typehaus.cli.route_ports import terminal_refusal
from typehaus.cli.route_proposal import one_proposal as _one_proposal
from typehaus.cli.route_roots import hold_upstream, reroot_supply
from typehaus.cli.route_support import _endpoints, _nearest, _root_nodes
from typehaus.routing.diagnostics import Refusal

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.proposal import RouteProposal

#: Letters an alternative is tagged with. Past 26 the caller has asked a different question
#: from "show me a few ways to do this", and `--alternatives` refuses rather than wrapping.
_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_SENTENCE = re.compile(r"(?<=[a-z)'\"])\. (?=[A-Z])")
_TAG = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")


@dataclass
class EndpointRefusal(Refusal):
    """A target whose terminals could not be derived: no lattice was built, so the search
    fields are empty and the record carries the cause, the element it names and the fix."""

    cause: str = ""
    element: str = ""
    fix: str = ""

    def render(self) -> str:
        return f"{self.target}: {self.cause}" + (f". {self.fix}" if self.fix else "")

    def payload(self) -> dict:
        return {**super().payload(), "cause": self.cause, "element": self.element,
                "fix": self.fix}


def endpoint_refusal(model: Any, target: str, lines: list[str]) -> EndpointRefusal:
    """The refusal for an ``_endpoints`` miss, read off the line it appended.

    Those lines read ``<target>: <cause>. <fix>``; the element is the last tag the cause
    names besides the target (the missing riser, the pump), else the target itself."""
    text = (lines[0].removeprefix(f"{target}: ") if lines
            else "its terminals are not derivable")
    cause, fix = ([*_SENTENCE.split(text, maxsplit=1), ""])[:2]
    cause = cause.rstrip(".")
    element = next((t for t in reversed(_TAG.findall(cause)) if t != target), target)
    service = next((str(r.system) for group in ("pipe_runs", "ducts", "conduits")
                    for r in getattr(model, group, ()) if r.tag == target and
                    hasattr(r, "system")), "")
    return EndpointRefusal(
        target=target, service=service, end="origin", reachable_nodes=0, total_nodes=0,
        attempts=("no search: the terminals are not derivable",),
        cause=cause, element=element, fix=fix.strip())


def _propose(model: ResolvedModel, targets: list[str], *, mode: str,
             slope: float | None, margin_ft: float, band: tuple[float, float] | None,
             avoid: frozenset[str], via: list[tuple[float, float]], explain: bool,
             cost: RouteCost, alternatives: int = 1, timing: list[str] | None = None,
             counterfactual: bool = False, extra_prisms: list | None = None,
             hold: int = 0, racks: list | None = None, lifted: frozenset[str] = frozenset(),
             root_lines: dict | None = None
             ) -> tuple[list[tuple[RouteProposal, str]], list[str], list[str], list]:
    """Return (proposal/storey pairs, problems, notices, structured refusals).

    ``extra_prisms`` are already-inflated campaign occupancy, appended without further
    inflation; ``racks`` the laid proposals whose level legs offer rack lanes
    (``routing/rack.py``); ``lifted`` authored runs a campaign re-lays, never obstacles;
    ``root_lines`` a re-laid feeder's new line by tag, which a supply tees onto instead.
    Every target refusal is reported; it never becomes an approximate route."""
    from typehaus.routing.alternatives import alternative_routes
    from typehaus.routing.graph import build_graph
    from typehaus.routing.space import RoutingSpaceTooLarge, build_space
    from typehaus.routing.timing import Timer

    proposals: list[tuple[RouteProposal, str]] = []
    problems: list[str] = []
    notices: list[str] = []
    refusals: list[Refusal] = []

    for target in targets:
        why: list[str] = []
        ends = _endpoints(model, target, mode, why)
        if ends is not None and root_lines:
            ends = reroot_supply(model, ends, target, root_lines)
        if ends is not None and hold:
            ends = hold_upstream(model, ends, target, hold, why)
        if ends is None:
            # A miss that reports a cause is a refusal, not just a line.
            missed = endpoint_refusal(model, target, why)
            refusals.append(missed)
            problems.append(missed.render())
            problems.extend(why[1:])
            continue
        problems.extend(why)
        if ends.fixture is not None and mode == "fixture":
            from typehaus.cli.route_fixture_vent import already_vented

            # Its authored arm already meets a vent: the drain is still proposed, alone.
            vented = already_vented(model, ends.fixture)
            if vented:
                notices.append(f"{target}: already vented ({vented}); no vent to search")
        if explain:
            notices.extend(ends.advice)
        terminals = [ends.origin, ends.root, *[(p[0], p[1], ends.root[2]) for p in via]]
        # Seed the lattice along the whole parent line where the tie may land anywhere on
        # it: a goal on a line the graph never built is worth nothing, which is the failure
        # mode `routing/corridors` exists to avoid and the same one applies here.
        # **Per-vertex z where the line carries one.** A vent chase is vertical so one
        # elevation describes its whole goal line; a supply trunk rises at both ends, and
        # seeding it at a single z builds the lattice at a height the trunk is nowhere near
        # for most of its length.
        terminals.extend((v[0], v[1], v[2] if len(v) > 2 else ends.root[2])
                         for path in ends.root_paths for v in path)
        terminals.extend(wet_terminals(model, ends))
        clock = Timer(target, enabled=timing is not None)
        try:
            try:
                with clock.stage("build-space"):
                    space = build_space(model, radius_m=ends.radius_m, terminals=terminals,
                                        margin_ft=margin_ft, avoid=avoid, touch=ends.touch | lifted,
                                        cost=cost.for_run(ends.kind, ends.system), z_band=band,
                                        cavity_radius_m=ends.cavity_radius_m or None,
                                        panel_space=ends.kind != "conduit")
                    space.bend_radius_m = ends.bend_radius_m
                    if ends.kind == "pipe" and not ends.falls and space.members is not None:
                        from typehaus.resolve.riser_cover import riser_cover

                        # A pipe riser stands in cover or a soffit, never a room's open air.
                        space.members.riser_cover = riser_cover(
                            model, space.bbox, [ends.origin, ends.root])
                    if racks and ends.kind == "pipe":
                        from typehaus.routing.rack import rack_lanes

                        space.corridors.extend(rack_lanes(
                            racks, system=str(ends.system), radius_m=ends.radius_m,
                            spacing_m=space.cost.rack_spacing_in * 0.0254))
                        space._corridor_index = None
                    if extra_prisms:
                        # Appended after the build so the space's own inflation is not
                        # applied twice: a campaign's prisms are already grown by the
                        # clearance the campaign chose.
                        space.hard.extend(extra_prisms)
                        space._hard_index = None
                    if ends.falls:
                        from typehaus.routing.gravity_band import prepare_falling

                        prepare_falling(space, (min(ends.root[2], ends.origin[2]),
                                             max(ends.root[2], ends.origin[2])), model)
            except RoutingSpaceTooLarge as exc:
                problems.append(f"{target}: {exc}")
                continue
            unreachable = terminal_refusal(space, ends, band)
            if unreachable is not None:
                problems.append(f"{target}: {unreachable}")
                continue

            # **A falling run searches in PLAN, in the plane it has to ARRIVE at.** Its z is a
            # derived monotone potential, so a 3-D search would optimise an elevation the
            # profile is about to overwrite — and would happily dive through the floor into a
            # cheap mechanical room and climb back, which flattens into a plan detour nobody
            # asked for. A pressurised run, a duct and a raceway keep the full lattice: their
            # elevation IS a choice, and it is the search's to make.
            levels = [ends.root[2]] if ends.falls else None
            try:
                # The lattice cap raises from `build_graph`, not only from `build_space` —
                # the line caps do not bound the node count, so this is the guard that
                # actually holds on a duct, whose search is genuinely three-dimensional.
                with clock.stage("build-graph"):
                    graph = build_graph(space, terminals, levels)
            except RoutingSpaceTooLarge as exc:
                problems.append(f"{target}: {exc}")
                continue
            clock.lattice(graph)
            start = _nearest(graph, ends.origin)
            # **A vent ties in ANYWHERE along its parent, a drain at its invert.** A branch
            # vent joining a common vent is ordinary IRC P3104 work, and with the root
            # modelled as one vertex the search structurally could not propose the merge —
            # on catlin PR-S-BATH1-VENT runs 18.5 ft to the chase while its origin sits 0.9
            # INCHES from PR-S-SUITEBATH-VENT's north leg. `--tree` already does this for
            # drains (`cmd_route_tree._line_nodes`); vents never reached that code.
            goals = set()
            for path in ends.root_paths:
                # The z gate applies exactly where the search is 3-D and the goal line has
                # an elevation of its own — the supply case. A vent's line carries plain
                # 2-tuples and `_line_nodes` leaves it plan-only, as it always was.
                goals |= _line_nodes(graph, path,
                                     z_tolerance=None if ends.falls else 0.05)
            if not goals:
                goals = _root_nodes(graph, ends.root, with_z=not ends.falls,
                                    exact=ends.tie_is_the_goal)
            if start is None or not goals:
                problems.append(
                    f"{target}: no lattice node at "
                    f"{'the origin' if start is None else 'the root'} — every candidate line "
                    "there is inside a hard obstacle, which is a statement about the model "
                    "rather than about the search")
                continue
            if graph.blocked_terminals:
                problems.append(
                    f"{target}: a terminal stands inside {', '.join(graph.blocked_terminals)} "
                    "— routed anyway, because a route must reach where it is told, but the "
                    "tie itself is a detail somebody has to draw")
            search, report = _search_for(model, graph, ends, slope)
            with clock.stage("search"):
                if alternatives > 1:
                    found_all = alternative_routes(search, graph, space, start, goals,
                                                   alternatives)
                else:
                    one = search(graph, space, start, goals)
                    found_all = [] if one is None else [one]
            for found in found_all:
                clock.route(found)
            if not found_all:
                from typehaus.cli.route_diagnose import refuse

                refused = refuse(space, graph, start, goals, target=target, ends=ends,
                                 report=report, alternatives=alternatives,
                                 margin_ft=margin_ft, band=band)
                refusals.append(refused)
                problems.append(refused.render())
                if counterfactual and refused.movable():
                    from typehaus.cli.route_diagnose import counterfactual_lines
                    notices.extend(counterfactual_lines(
                        model, ends, refused, margin_ft=margin_ft, band=band,
                        avoid=avoid, cost=cost, via=via, slope=slope,
                        search_for=_search_for))
                continue
            if alternatives > 1 and len(found_all) < alternatives:
                notices.append(f"{target}: {len(found_all)} distinct route(s) found of "
                               f"{alternatives} asked for — the rest were the same lane at a "
                               "higher price, which is not an alternative")

            ranked = []
            for index, found in enumerate(found_all):
                suffix = f"-{_LETTERS[index]}" if len(found_all) > 1 else ""
                made = _one_proposal(model, ends, found, target, suffix, slope, explain,
                                     problems, space=space)
                if made is None:
                    continue
                if made.system == "drain":
                    made = _with_cleanouts(model, space, made)
                pair = [made]
                if found.vent is not None:
                    from typehaus.cli.route_fixture_vent import vent_proposal

                    vent = vent_proposal(found, made, ends, target, suffix)
                    pair += [vent] if vent is not None else []
                ranked.append(pair)
            # Ranked on the whole price — cleanout access panels included — not the search's.
            for pair in sorted(ranked, key=lambda p: p[0].cost):
                proposals.extend((made, ends.storey) for made in pair)
        finally:
            # Measurements survive a refusal. A target that could not be routed is
            # exactly the one whose build-space and lattice counts say why.
            if timing is not None:
                timing.extend(clock.lines())
    return proposals, problems, notices, refusals


def _with_cleanouts(model, space, made):
    """Phase 5: the drain's UPC 707.4 cleanouts, their access panels priced into its cost."""
    from dataclasses import replace

    from typehaus.cli.route_cleanouts import place_cleanouts

    cleanouts, cost, notes = place_cleanouts(model, space, made)
    terms = dict(made.terms)
    if cost and terms:
        terms["cleanout_concealed_in"] = cost
    return replace(made, cleanouts=cleanouts, cost=made.cost + cost, terms=terms,
                   notes=[*made.notes, *notes])

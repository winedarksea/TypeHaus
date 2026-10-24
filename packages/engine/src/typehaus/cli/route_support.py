"""Loading, endpoint derivation, and gravity profiles for haus route.

Pipes derive fixture/main ties; duct and raceway reroutes keep their authored ends.
Endpoints carries kind because conduit elevations are absolute, unlike pipes and ducts.
Workflow and module map: docs/routing.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house
from typehaus.cli.route_metadata import run_metadata as _run_metadata

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.graph import Graph


@dataclass(frozen=True)
class Endpoints:
    """Search terminals, section, permitted contacts, and source metadata."""

    origin: tuple[float, float, float]
    root: tuple[float, float, float]
    radius_m: float
    kind: str  # "pipe" | "duct" | "conduit"
    system: str
    storey: str
    #: Round section, or the pipe's own outside diameter, or a raceway's trade size.
    diameter_m: float = 0.0
    #: Rectangular duct only; both zero for everything round.
    width_m: float = 0.0
    depth_m: float = 0.0
    serves: tuple[str, ...] = ()
    #: Existing runs this proposal may occupy — the one it replaces, the one it ties into.
    touch: frozenset[str] = frozenset()
    #: Whole plan polylines the tie may land ANYWHERE along, rather than at one nominated
    #: vertex. Empty for a falling run: a drain's root is the invert it has to arrive at,
    #: and that is one elevation at one point. A vent has no such constraint — two branch
    #: vents joining a common vent is ordinary IRC P3104 work — and with a single root
    #: vertex the router structurally could not propose the merge even where the two lines
    #: pass within an inch of each other.
    root_paths: tuple[tuple[tuple[float, ...], ...], ...] = ()
    #: True when the tie is the run's ORIGIN rather than its far end — the supply case. The
    #: search runs riser -> trunk because the fixture end is the fixed one; the run is
    #: authored trunk -> riser. Reversing the found polyline is the whole of the difference,
    #: and it is safe to do literally because no gravity profile is involved.
    tie_is_the_goal: bool = False
    #: Extra constructor keywords to echo, e.g. a raceway's ``from_ref``/``to_ref``.
    echo: dict[str, Any] = field(default_factory=dict)
    #: True when a gravity profile applies. Not ``system == "drain"`` at the call site,
    #: because a DuctSystem is also a string and "exhaust" does not fall.
    falls: bool = False
    #: Lines ``--explain`` prints about the terminals themselves — the derived duct size
    #: against the authored one, a terminal snapped to an exact port. Advice, never a
    #: change: an authored size wins, and saying why it is arguable is the whole service.
    advice: tuple[str, ...] = ()
    #: What pasting obliges next — the children to re-route once this run moves.
    after_paste: tuple[str, ...] = ()
    held: tuple[tuple[float, float, float], ...] = ()  #: kept ahead of origin, --hold-upstream


from typehaus.cli.route_roots import (  # noqa: E402
    _discharge,
    _nearest_main,
    _supply_children,
    _supply_trunk,
    _vent_siblings,
)

__all__ = ["_discharge", "_nearest_main", "_vent_siblings"]


def _load(house: Path | None) -> tuple[Path, Any]:
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    if errors:
        _print_findings(errors)
        raise typer.Exit(1)
    return directory, model


def _storey_datum(model: ResolvedModel, storey: str) -> float:
    return next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)


def _points(via: list[str]) -> list[tuple[float, float]]:
    out = []
    for item in via:
        try:
            x, y = (float(v) for v in item.split(","))
        except ValueError as exc:  # noqa: PERF203 - one message per bad argument
            raise typer.BadParameter(f'--via wants "X,Y" in feet, got {item!r}') from exc
        out.append((x * 0.3048, y * 0.3048))
    return out


def branch_diameter_m(model: ResolvedModel, fixtures: tuple[str, ...],
                      problems: list[str], target: str) -> float | None:
    """Size the fixture load using the same plumbing_calc reading as mep.pipe_sizing.

    Unknown fixture loads produce a refusal rather than an assumed branch diameter."""
    from typehaus.takeoff.plumbing_calc import (
        M_PER_IN,
        MINIMUM_DRAIN_IN_BY_SYMBOL,
        fixture_units,
        required_drain_diameter_in,
    )

    rows = {row.tag: row for row in fixture_units(model.plan)}
    load, floor_in = 0.0, 0.0
    for tag in fixtures:
        row = rows.get(tag)
        if row is None or row.dfu is None:
            problems.append(
                f"{target}: {tag} carries no drainage fixture-unit row, so this branch "
                "has no derivable size. Naming a size is a judgement and the proposal "
                "will not make one up")
            return None
        load += row.dfu
        floor_in = max(floor_in, MINIMUM_DRAIN_IN_BY_SYMBOL.get(row.symbol, 0.0))
    size_in = required_drain_diameter_in(load)
    if size_in is None:
        problems.append(f"{target}: {load:.0f} DFU is past the last row of the horizontal "
                        "branch table, so this is a stack or a building drain and not a "
                        "branch")
        return None
    return max(size_in, floor_in) * M_PER_IN


def _endpoints(model: ResolvedModel, target: str, mode: str,
               problems: list[str]) -> Endpoints | None:
    """The terminals for one target, or None with the reason appended to ``problems``.

    ``touch`` is the set of existing runs this proposal may occupy — see
    :func:`~typehaus.routing.obstacles.hard_prisms`.

    A fixture's origin is its derived drain point at its own floor; a run's is its first
    vertex. The root is the nearest drain run's deepest vertex — which is the honest
    reading of "where does this discharge", and is the same derivation ``drain_tie_ins``
    uses to link the load.
    """
    # Imported from the module that OWNS the derivation rather than re-derived: the same
    # point `mep.trap_arm_length` and `mep.fixture_drain_reach` measure from, so a router
    # aimed at a different point from the checks that judge it is impossible by construction.
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]

    if mode == "run":
        runs = {r.tag: r for r in model.pipe_runs}
        if target in runs:
            return _pipe_run_endpoints(model, runs[target], problems)
        duct = next((d for d in model.ducts if d.tag == target), None)
        if duct is not None:
            return _duct_endpoints(model, duct, problems)
        raceway = next((c for c in model.conduits if c.tag == target), None)
        if raceway is not None:
            return _conduit_endpoints(model, raceway, problems)

    if mode in ("fixture", "unconnected"):
        point = _expected_drain_point(model, target)
        if point is None:
            problems.append(f"{target}: no resolvable drain point — the same wording "
                            "mep.trap_arm_length uses, and the same cause")
            return None
        storey = _storey_of(model, target)
        from typehaus.model.enums import Service
        from typehaus.resolve.mep_sleeves import expected_port_point

        port = expected_port_point(model, target, Service.DRAIN)
        floor_m = _storey_datum(model, storey) + (port[2] if port is not None else 0.0)
        near = _nearest_main(model, point, floor_m, problems, target, exclude=target)
        if near is None:
            return None
        root, parent = near
        diameter_m = branch_diameter_m(model, (target,), problems, target)
        if diameter_m is None:
            return None
        # The runs that already serve this fixture are what the proposal REPLACES, so they
        # are not obstacles to it — and one of them is usually the run the tie point sits
        # on, which is why leaving them hard reports "no lattice node at the root" for a
        # root that is perfectly reachable.
        replaced = {run.tag for run in model.pipe_runs if target in run.serves}
        return Endpoints(
            origin=(point[0], point[1], floor_m), root=root, kind="pipe",
            radius_m=diameter_m / 2.0, diameter_m=diameter_m, serves=(target,),
            storey=storey, system="drain", falls=True,
            touch=frozenset({parent, *replaced}))

    problems.append(f"{target}: not a run in this model")
    return None


#: The pressurised piping systems, which tee onto a trunk rather than discharging to one.
_SUPPLY_SYSTEMS = ("water_cold", "water_hot")


def _pipe_run_endpoints(model: ResolvedModel, run: Any,
                        problems: list[str]) -> Endpoints | None:
    if not run.z_m or len(run.z_m) != len(run.path):
        problems.append(f"{run.tag}: no resolved elevations, so it cannot be routed")
        return None
    falls = run.system == "drain"
    if run.system in _SUPPLY_SYSTEMS:
        # **Supply is the mirror of a vent: the GOAL is fixed and the ORIGIN is free.** The
        # fixture riser is where the water has to come out; where it tees onto the trunk is
        # the search's to choose, anywhere along the line. So the search runs from the
        # riser, and `tie_is_the_goal` puts the printed run back the way it is authored.
        supply = _supply_trunk(model, run, problems)
        if supply is None:
            return None
        root, chain, paths = supply
        # Children tee ON this run, so they may be touched — and their tees move with it.
        children = _supply_children(model, run)
        after = (f"{', '.join(children)} tee on {run.tag} and their tees move with it: "
                 "re-route each with `haus route --run <tag>`",) if children else ()
        return Endpoints(
            origin=(run.path[-1][0], run.path[-1][1], run.z_m[-1]), root=root, kind="pipe",
            radius_m=(run.diameter_m or 0.0) / 2.0,
            # **Never branch_diameter_m here.** That is a DFU drain table and says nothing
            # about a water branch, whose size comes off WSFU and pressure.
            diameter_m=run.diameter_m,
            serves=run.serves, storey=run.storey, system=run.system, falls=False,
            touch=frozenset({run.tag, *chain, *children}), root_paths=paths,
            tie_is_the_goal=True, after_paste=after,
            echo=_run_metadata(model, run.tag, ("material", "finish", "insulation",
                                                "sanitary", "freeze_protection")))
    found = _discharge(model, run, problems if falls else [])
    if found is None and falls:
        return None
    if found is not None:
        root, chain, parent_path = found
        paths: tuple[tuple[tuple[float, ...], ...], ...] = ((), ) if falls else (parent_path,)
    else:
        # **A vent's downstream is a CHASE, not another run**, so ``drain_tie_ins`` derives
        # nothing for it: on catlin all eight vents simply end at the VentRun station and
        # none ends on a sibling. The legal tie points are that station and every sibling
        # already reaching it — which is what IRC P3104 calls a common vent.
        sibling = _vent_siblings(model, run, problems)
        if sibling is None:
            return None
        root, chain, paths = sibling
    return Endpoints(
        origin=(run.path[0][0], run.path[0][1], run.z_m[0]), root=root, kind="pipe",
        radius_m=(run.diameter_m or 0.0) / 2.0, diameter_m=run.diameter_m,
        serves=run.serves, storey=run.storey, system=run.system,
        falls=falls, touch=frozenset({run.tag, *chain}),
        root_paths=() if falls else tuple(p for p in paths if p),
        echo=_run_metadata(model, run.tag, ("material", "finish", "insulation",
                                            "sanitary", "freeze_protection")))


def _duct_endpoints(model: ResolvedModel, duct: Any,
                    problems: list[str]) -> Endpoints | None:
    """Keep the duct's authored ends and allow contacts from the shared connectivity rule.

    An authored duct size wins; equal-friction sizing is advice only."""
    from typehaus.resolve.mep_envelopes import insulation_thickness_m, joinable
    from typehaus.resolve.mep_soffit import ducts_are_joined
    from typehaus.routing.trades import duct as duct_trade

    if len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
        problems.append(f"{duct.tag}: fewer than two vertices or no resolved elevations, "
                        "so it has no two ends to route between")
        return None
    lagging = insulation_thickness_m(duct.insulation)
    if lagging is None:
        problems.append(f"{duct.tag}: insulation states no thickness, so its routing "
                        "envelope cannot be established")
        return None
    joined = {other.tag for other in model.ducts
              if other.tag != duct.tag and ducts_are_joined(model, duct.tag, other.tag)
              and joinable(model, duct.tag, other.tag)}
    width, depth = (0.0, 0.0) if duct.diameter_m else (duct.width_m, duct.depth_m)
    origin = _port_terminal(model, duct, 0)
    root = _port_terminal(model, duct, len(duct.path) - 1)
    return Endpoints(
        origin=origin, root=root, advice=_duct_size_advice(model, duct),
        kind="duct", radius_m=duct_trade.radius_m(
            diameter_m=duct.diameter_m, width_m=duct.width_m, depth_m=duct.depth_m) + lagging,
        diameter_m=duct.diameter_m or 0.0, width_m=width, depth_m=depth,
        storey=duct.storey, system=duct.system, falls=False,
        touch=frozenset({duct.tag, *joined}),
        echo=_run_metadata(model, duct.tag, ("material", "insulation", "design_cfm")))


def _conduit_endpoints(model: ResolvedModel, raceway: Any,
                       problems: list[str]) -> Endpoints | None:
    """A raceway keeps its ends too, and carries ``from_ref``/``to_ref`` through.

    Its elevations are **project-frame absolute**, so the proposal is printed at a datum of
    zero — see :func:`~typehaus.cli.cmd_route.route`. A run whose profile the model cannot
    reconstruct is refused rather than flattened: ``conduit_vertical_profile`` is the one
    reading of that, and a run it declines is a run whose z nobody authored.
    """
    from typehaus.resolve.mep_queries import conduit_vertical_profile

    profile = conduit_vertical_profile(raceway)
    if profile is None or len(raceway.path) < 2:
        problems.append(f"{raceway.tag}: no reconstructable vertical profile, so it has "
                        "no elevation to route at. Author start/end elevations on it")
        return None
    path, z = profile
    echo = {key: getattr(raceway, key) for key in ("from_ref", "to_ref")
            if getattr(raceway, key, None)}
    return Endpoints(
        origin=(path[0][0], path[0][1], z[0]), root=(path[-1][0], path[-1][1], z[-1]),
        kind="conduit", radius_m=(raceway.trade_size_m or 0.0) / 2.0,
        diameter_m=raceway.trade_size_m or 0.0, storey=raceway.storey,
        system=raceway.service or "power_120", falls=False, echo=echo,
        touch=frozenset({raceway.tag}))


def _fall(points: list[tuple[float, float, float]],
          origin: tuple[float, float, float], budget: Any, grade: float,
          target: str, problems: list[str]
          ) -> tuple[list[tuple[float, float, float]], str] | None:
    """Put a found plan route on its gravity profile, or refuse and say by how much.

    The profile comes from ``gravity.profile_for`` rather than from a start elevation, so
    it is built from the ARRIVAL upward and the route lands exactly on the tie. Then the
    flange is prepended as its own vertex at the finished floor, which makes the first leg
    the vertical drop it is: a closet bend is a fitting, not a grade.

    A refusal names the grade the route WOULD hold. "No feasible route" is not actionable;
    "this needs 0.19"/ft and the code wants 0.25"" says how much shorter, higher or lower
    the problem has to get. That second refusal — a ``--slope`` steeper than the code
    minimum, which ``HeadBudget.feasible`` does not grade because it asks about the
    minimum — is why the profile is asked rather than the budget.
    """
    from typehaus.routing.trades import pipe as pipe_trade

    fallen = pipe_trade.elevate(points, budget, grade_in_per_ft=grade)
    if fallen is None:
        feasible = budget.feasible_slope_in_per_ft()
        short = max(budget.shortfall_in(),
                    grade * budget.developed_ft - budget.available_in)
        problems.append(
            f'{target}: short {short:.2f}" of head over '
            f'{budget.developed_ft:.2f} ft. The route is feasible at '
            f'{feasible:.3f}"/ft and this asks for {grade:.3f}"/ft — raise the '
            f'start, lower the tie, or shorten the run by {short / grade:.2f} ft')
        return None
    if origin[2] > fallen[0][2] + 1e-9:
        fallen = [(fallen[0][0], fallen[0][1], origin[2]), *fallen]
    return fallen, (f'gravity: {grade:.3f}"/ft over {budget.developed_ft:.2f} ft, '
                    f'{budget.slack_in:.2f}" of head to spare; the first leg is the '
                    "flange drop and takes no grade")


def _storey_of(model: ResolvedModel, tag: str) -> str:
    for storey in model.plan.storeys:
        if any(getattr(e, "tag", None) == tag
               for e in model.plan.storey_elements(storey.tag)):
            return str(storey.tag)
    return "main"


def _nearest(graph: Graph, point: tuple[float, float, float]) -> int | None:
    if not graph.nodes:
        return None
    return int(min(graph.nodes,
                   key=lambda n: (abs(n.x - point[0]) + abs(n.y - point[1])
                                  + abs(n.z - point[2]))).index)


def _root_nodes(graph: Graph, root: tuple[float, float, float],
                *, with_z: bool = False, exact: bool = False) -> set[int]:
    """Nodes on the root's plan point; with_z also filters elevation for 3-D searches.

    Gravity searches one plane and derives its profile separately, so its root has no z gate.
    ``exact`` requires the node on a supply equipment port rather than a cheaper neighbour."""
    tolerance = 0.05
    near = {node.index for node in graph.nodes
            if abs(node.x - root[0]) < tolerance and abs(node.y - root[1]) < tolerance
            and (not with_z or abs(node.z - root[2]) < tolerance)}
    if exact:
        on = {i for i in near if max(abs(graph.nodes[i].x - root[0]),
                                     abs(graph.nodes[i].y - root[1]),
                                     abs(graph.nodes[i].z - root[2])) < 1e-4}
        return on or near
    return near


def _port_terminal(model: ResolvedModel, duct: Any, index: int) -> tuple[float, float, float]:
    """Snap a duct end to its equipment's EXACT port; leave approximate ports unchanged.

    The 0.5 m tolerance covers a case's half-diagonal, not merely a joint, so loose ends
    inside a case reach the spigot without capturing the next machine."""
    from typehaus.resolve.mep_ports import port_at

    point = duct.path[index]
    z = duct.z_m[index]
    system = duct.system.value if hasattr(duct.system, "value") else str(duct.system)
    port = port_at(model, point, z, duct_system=system, tolerance_m=0.5)
    return (point[0], point[1], z) if port is None else port.point


def _duct_size_advice(model: ResolvedModel, duct: Any) -> tuple[str, ...]:
    """Compare round-duct equal-friction sizing with the authored size without changing it.

    Rectangular equivalent diameters are outside this reading. New branches use
    resolve.duct_sizing.size_for_cfm rather than inheriting an authored size."""
    from typehaus.resolve.duct_sizing import friction_rate_in_wg_per_100ft, size_for_cfm

    cfm = getattr(duct, "design_cfm", None)
    if not cfm or not duct.diameter_m:
        return ()
    rate = _friction_rate(model)
    want, basis = size_for_cfm(model.plan.library, cfm, material=duct.material,
                               rate_in_wg_per_100ft=rate)
    if want is None:
        return (f"sizing: {basis}",)
    if abs(want.nominal_m - duct.diameter_m) <= 1e-9:
        return (f"sizing: {duct.tag} is the size {cfm:.0f} cfm wants — {basis}",)
    from typehaus.quantities import M_PER_IN
    row = next((r for r in model.plan.library.duct_product_types
                if r.material == duct.material
                and abs(r.nominal_diameter.meters - duct.diameter_m) <= 1e-6), None)
    drawn = (None if row is None else friction_rate_in_wg_per_100ft(
        cfm, row.bore_diameter.meters, row.roughness_m))
    at = "" if drawn is None else f", against {drawn:.3f} in. w.g./100 ft as drawn"
    return (f'sizing: {duct.tag} is drawn {duct.diameter_m / M_PER_IN:.3g}"; '
            f"{cfm:.0f} cfm at the {rate:.3f} in. w.g./100 ft design rate wants {basis}{at}. "
            "The authored size stands — this is the number, not a decision",)


def _friction_rate(model: ResolvedModel) -> float:
    """``[mep.routing] duct_friction_in_wg_per_100ft`` for this house, or the default."""
    from typehaus.resolve.duct_sizing import (
        DEFAULT_FRICTION_IN_WG_PER_100FT,
        friction_rate_from_preferences,
    )

    root = getattr(model.plan, "source_root", None)
    if root is None:
        return DEFAULT_FRICTION_IN_WG_PER_100FT
    from typehaus.checks import load_preferences

    return friction_rate_from_preferences(load_preferences(Path(root)).mep.routing)

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
from typehaus.cli.route_miss import miss
from typehaus.routing.trades import pipe as pipe_trade

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.cli.route_ports import PortLead
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
    #: Half what a wall cavity must hold — a DWV hub; 0 means ``radius_m``.
    cavity_radius_m: float = 0.0
    #: A bendable tube's minimum bend radius (``trades.pipe.bend_radius_m``); 0 if fitted.
    bend_radius_m: float = 0.0
    #: ``--fixture``: the fixture whose trap arm this drain starts (Phase 4's arm search).
    fixture: str | None = None
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
    #: A raceway's authored pull boxes, as 3D points: the re-route keeps those it still passes.
    pull_boxes: tuple[tuple[float, float, float], ...] = ()
    #: An exact, directed equipment port at an end: that end is moved to the lead's stub tip.
    origin_lead: PortLead | None = None
    root_lead: PortLead | None = None
    #: ``--fixture``: the trap's weir where it is not the port — a floor outlet's trap hangs
    #: under the floor (``resolve/mep_trap_arm.under_floor_weir_m``). None: the origin.
    weir_m: float | None = None
    #: ``--fixture``: bathroom-group drains the arm may end on as a 908.2 wet vent.
    wet_candidates: tuple[str, ...] = ()

    @property
    def weir(self) -> float:
        """Where a falling run's profile starts: the trap weir, else the origin."""
        return self.origin[2] if self.weir_m is None else self.weir_m


from typehaus.cli.route_endpoints_duct import (  # noqa: E402
    _conduit_endpoints,
    _duct_endpoints,
)
from typehaus.cli.route_roots import (  # noqa: E402
    _discharge,
    _nearest_main,
    _supply_children,
    _supply_trunk,
    _vent_siblings,
    sleeve_hold,
    sump_endpoints,
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
        fixture_units,
        required_drain_diameter_in,
    )

    rows = {row.tag: row for row in fixture_units(model.plan)}
    load, symbols = 0.0, []
    for tag in fixtures:
        row = rows.get(tag)
        if row is None or row.dfu is None:
            miss(problems, target, f"{tag} carries no drainage fixture-unit row, so this "
                 "branch has no derivable size", tag, "Naming a size is a judgement and the "
                 "proposal will not make one up")
            return None
        load += row.dfu
        symbols.append(row.symbol)
    size_in = required_drain_diameter_in(load, symbols)
    if size_in is None:
        miss(problems, target, f"{load:.0f} DFU is past the last row of the horizontal "
             "branch table, so this is a stack or a building drain and not a branch")
        return None
    return size_in * M_PER_IN


def _endpoints(model: ResolvedModel, target: str, mode: str,
               problems: list[str]) -> Endpoints | None:
    """:func:`_target_endpoints` with exact ports' and shower inlets' direction leads applied."""
    from typehaus.cli.route_fixture_inlet import with_inlet_lead
    from typehaus.cli.route_ports import with_port_leads

    ends = with_port_leads(model, _target_endpoints(model, target, mode, problems))
    return with_inlet_lead(model, ends)


def _target_endpoints(model: ResolvedModel, target: str, mode: str,
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
            miss(problems, target, "no resolvable drain point — the same wording "
                 "mep.trap_arm_length uses, and the same cause")
            return None
        storey = _storey_of(model, target)
        from typehaus.model.enums import Service
        from typehaus.resolve.mep_sleeves import expected_port_point

        port = expected_port_point(model, target, Service.DRAIN)
        datum_m = _storey_datum(model, storey)
        floor_m = datum_m + (port[2] if port is not None else 0.0)
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
        # Drains only: the hot and cold runs to the same basin are not replaced, and
        # touching them let the branch through its own supply lines.
        replaced = {run.tag for run in model.pipe_runs
                    if target in run.serves and run.system == "drain"}
        from typehaus.cli.route_fixture_wet import wet_candidates
        from typehaus.resolve.mep_trap_arm import under_floor_weir_m

        wet = wet_candidates(model, target, point, floor_m)
        return Endpoints(
            origin=(point[0], point[1], floor_m), root=root, kind="pipe",
            radius_m=pipe_trade.radius_m(diameter_m),
            cavity_radius_m=pipe_trade.cavity_radius_m(diameter_m, "drain"),
            diameter_m=diameter_m, serves=(target,),
            storey=storey, system="drain", falls=True,
            touch=frozenset({parent, *replaced, *wet}), fixture=target,
            weir_m=under_floor_weir_m(model, target, datum_m, port), wet_candidates=wet)

    miss(problems, target, "not a run in this model")
    return None


#: The pressurised piping systems, which tee onto a trunk rather than discharging to one.
_SUPPLY_SYSTEMS = ("water_cold", "water_hot")


def _pipe_run_endpoints(model: ResolvedModel, run: Any,
                        problems: list[str]) -> Endpoints | None:
    if not run.z_m or len(run.z_m) != len(run.path):
        miss(problems, run.tag, "no resolved elevations, so it cannot be routed")
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
            radius_m=pipe_trade.radius_m(run.diameter_m, run.material, run.insulation),
            # **Never branch_diameter_m here.** That is a DFU drain table and says nothing
            # about a water branch, whose size comes off WSFU and pressure.
            diameter_m=run.diameter_m,
            bend_radius_m=pipe_trade.bend_radius_m(run.diameter_m, str(run.system),
                                                   run.material),
            serves=run.serves, storey=run.storey, system=run.system, falls=False,
            touch=frozenset({run.tag, *chain, *children}), root_paths=paths,
            tie_is_the_goal=True, after_paste=after,
            echo=_run_metadata(model, run.tag, ("material", "finish", "insulation",
                                                "sanitary", "freeze_protection")))
    if run.system == "sump_discharge":
        # A pumped line is pressure: no grade; the pit outlet is fixed and the wye lands
        # on the receiver's riser at the authored elevation (``sump_endpoints``).
        sump = sump_endpoints(model, run, problems)
        if sump is None:
            return None
        root, riser = sump
        # Through its cast sleeve, never under the footings at pit level (UPC 314.1).
        hold = sleeve_hold(model, run)
        start = hold[0] if hold else 0
        note = (f"{run.tag}: held through {hold[1]} to vertex {start}; the tail is searched"
                if hold else f"{run.tag}: no cast sleeve is on its authored line, so the "
                "search is free to cross the foundation anywhere")
        return Endpoints(
            origin=(run.path[start][0], run.path[start][1], run.z_m[start]),
            held=tuple((p[0], p[1], z) for p, z in zip(run.path[:start], run.z_m,
                                                         strict=False)),
            root=root, kind="pipe",
            radius_m=pipe_trade.radius_m(run.diameter_m, run.material, run.insulation),
            diameter_m=run.diameter_m,
            bend_radius_m=pipe_trade.bend_radius_m(run.diameter_m, str(run.system),
                                                   run.material),
            serves=run.serves, storey=run.storey, system=run.system, falls=False,
            touch=frozenset({run.tag}),
            advice=(f"{run.tag}: roots on {riser}, the receiver's derived riser", note),
            echo=_run_metadata(model, run.tag, ("material", "finish", "insulation",
                                                "sanitary", "freeze_protection")))
    if run.system == "refrigerant":
        return _lineset_endpoints(model, run)
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
        radius_m=pipe_trade.radius_m(run.diameter_m, run.material, run.insulation),
        cavity_radius_m=pipe_trade.cavity_radius_m(run.diameter_m, str(run.system),
                                                   run.material, run.insulation),
        diameter_m=run.diameter_m,
        serves=run.serves, storey=run.storey, system=run.system,
        falls=falls, touch=frozenset({run.tag, *chain}),
        root_paths=() if falls else tuple(p for p in paths if p),
        advice=(_slope_basis(run),) if falls and getattr(run, "sanitary", True) is False else (),
        echo=_run_metadata(model, run.tag, ("material", "finish", "insulation",
                                            "sanitary", "freeze_protection")))


def _lineset_endpoints(model: ResolvedModel, run: Any) -> Endpoints:
    """A lineset: pressure, no grade, both ends fixed. The search runs from the authored
    outdoor end (``--hold-upstream`` keeps the hand-drawn outside leg) to the head's port
    pair, else to the authored head end; the bundle's radius and the coil's bend rule."""
    from typehaus.resolve.mep_ports import placed_ports

    head = run.serves[0] if run.serves else None
    pair = [p.point for p in placed_ports(model) if p.equipment_tag == head
            and p.port_tag in ("liquid", "vapor")]
    root = (tuple(sum(c) / 2.0 for c in zip(*pair, strict=True)) if len(pair) == 2
            else (run.path[-1][0], run.path[-1][1], run.z_m[-1]))
    return Endpoints(
        origin=(run.path[0][0], run.path[0][1], run.z_m[0]), root=root, kind="pipe",
        radius_m=(run.bundle_diameter_m or run.diameter_m) / 2.0,
        diameter_m=run.diameter_m,
        bend_radius_m=pipe_trade.bend_radius_m(run.diameter_m, "refrigerant", run.material),
        serves=run.serves, storey=run.storey, system=run.system, falls=False,
        touch=frozenset({run.tag}),
        advice=(f"{run.tag}: roots on {head}'s port pair" if len(pair) == 2
                else f"{run.tag}: {head} declares no port pair; roots on the authored end",),
        echo=_run_metadata(model, run.tag, ("material", "insulation", "liquid_diameter",
                                            "outdoor_port")))


def _slope_basis(run: Any) -> str:
    from typehaus.routing.gravity import CONDENSATE_SLOPE_BASIS

    return f"{run.tag}: {CONDENSATE_SLOPE_BASIS}"


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



def storey_band(model: ResolvedModel, level: str) -> tuple[float, float] | None:
    """``--level``'s z band: this storey's datum up to the next one's.

    The top storey runs to infinity, which is right: an attic run is on the top storey and
    there is no plane above it to stop at.
    """
    elevations = sorted({s.elevation.meters for s in model.plan.storeys})
    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == level), None)
    if datum is None:
        return None
    above = [e for e in elevations if e > datum + 1e-9]
    return (datum, min(above) if above else float("inf"))

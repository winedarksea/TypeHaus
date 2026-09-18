"""Loading, terminals and the gravity profile — everything ``haus route`` needs to ask.

Split out of ``cmd_route.py`` with no behaviour change but one addition: :func:`_endpoints`
now answers for **ducts and raceways** as well as pipe. It used to index ``model.pipe_runs``
alone, so ``--run DU-M-ERV-R-KITCH`` came back "not a run in this model" about a run that is
plainly in the model — a true sentence about the wrong index.

The three trades differ in what a terminal *is*, and the differences are not cosmetic:

* a **pipe** branch starts at a fixture's derived drain point and ends at the nearest main's
  deepest vertex on that fixture's own floor;
* a **duct** re-route keeps its own two ends, because a duct is not a tree onto a main —
  it leaves a machine and lands on a trunk or a boot, and both are authored;
* a **raceway** likewise, and its elevations are project-frame absolute rather than
  storey-relative (``model/mep.py::ConduitRun``), which is why :class:`Endpoints` carries
  ``kind`` and the caller does not guess from the tag prefix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.graph import Graph


@dataclass(frozen=True)
class Endpoints:
    """What one target hands the search: two points, a section, and who may be touched.

    A record rather than the seven-tuple that stood here, because the duct case needs a
    rectangular section and the conduit case needs its own datum, and a tuple that grew two
    more slots would have been unpacked wrongly somewhere within the week.
    """

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
    #: Extra constructor keywords to echo, e.g. a raceway's ``from_ref``/``to_ref``.
    echo: dict[str, str] = field(default_factory=dict)
    #: True when a gravity profile applies. Not ``system == "drain"`` at the call site,
    #: because a DuctSystem is also a string and "exhaust" does not fall.
    falls: bool = False
    #: Lines ``--explain`` prints about the terminals themselves — the derived duct size
    #: against the authored one, a terminal snapped to an exact port. Advice, never a
    #: change: an authored size wins, and saying why it is arguable is the whole service.
    advice: tuple[str, ...] = ()


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
    """The branch size this fixture load actually wants, or None with a refusal line.

    A flat 2" literal stood here and was wrong for the one fixture that matters most: a
    water closet's branch is 3" and always has been. The size comes from the **same**
    derivation ``mep.pipe_sizing`` grades against — ``takeoff/plumbing_calc`` — so a
    proposal cannot be sized against a table the check does not use.

    A fixture the table has no row for is a **refusal line**, never a 2" guess: an unknown
    load sized at the common case is exactly the confident nonsense this engine refuses.
    """
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
        floor_m = _storey_datum(model, storey)
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


def _pipe_run_endpoints(model: ResolvedModel, run: Any,
                        problems: list[str]) -> Endpoints | None:
    if not run.z_m or len(run.z_m) != len(run.path):
        problems.append(f"{run.tag}: no resolved elevations, so it cannot be routed")
        return None
    found = _discharge(model, run, problems)
    if found is None:
        return None
    root, chain = found
    return Endpoints(
        origin=(run.path[0][0], run.path[0][1], run.z_m[0]), root=root, kind="pipe",
        radius_m=(run.diameter_m or 0.0) / 2.0, diameter_m=run.diameter_m,
        serves=run.serves, storey=run.storey, system=run.system,
        falls=run.system == "drain", touch=frozenset({run.tag, *chain}))


def _duct_endpoints(model: ResolvedModel, duct: Any,
                    problems: list[str]) -> Endpoints | None:
    """A duct keeps its own two ends, and may occupy whatever it is jointed to.

    **Not a tree onto a main.** A duct leaves a machine and lands on a trunk, a boot or a
    hood, and every one of those is authored — so re-routing one is the question "same two
    ends, a better lane between them", which is a different question from a drain branch's
    and is why this does not go near ``_nearest_main``.

    What it may touch is what ``mep.duct_connectivity`` says it joins, read from
    ``resolve/mep_soffit.ducts_are_joined`` — the same predicate, so the router cannot
    propose a lane the connectivity check would then call an orphan.
    """
    from typehaus.resolve.mep_soffit import ducts_are_joined
    from typehaus.routing.trades import duct as duct_trade

    if len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
        problems.append(f"{duct.tag}: fewer than two vertices or no resolved elevations, "
                        "so it has no two ends to route between")
        return None
    joined = {other.tag for other in model.ducts
              if other.tag != duct.tag and ducts_are_joined(model, duct.tag, other.tag)}
    width, depth = (0.0, 0.0) if duct.diameter_m else (duct.width_m, duct.depth_m)
    origin = _port_terminal(model, duct, 0)
    root = _port_terminal(model, duct, len(duct.path) - 1)
    return Endpoints(
        origin=origin, root=root, advice=_duct_size_advice(model, duct),
        kind="duct", radius_m=duct_trade.radius_m(
            diameter_m=duct.diameter_m, width_m=duct.width_m, depth_m=duct.depth_m),
        diameter_m=duct.diameter_m or 0.0, width_m=width, depth_m=depth,
        storey=duct.storey, system=duct.system, falls=False,
        touch=frozenset({duct.tag, *joined}))


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


def _discharge(model: ResolvedModel, run: Any,
               problems: list[str]) -> tuple[tuple[float, float, float], list[str]] | None:
    """``(root point, the whole downstream chain)`` for a run, or None.

    The chain, not just the parent, and that is what makes a tie reachable at all: a
    branch's root vertex usually sits ON its parent, and its parent's root sits on the
    GRANDparent, so leaving the rest of the chain hard walls the route off from the tie it
    is being routed to. ``drain_tie_ins`` derives the topology from the geometry and this
    walks it to the bottom.
    """
    from typehaus.resolve.mep_queries import drain_tie_ins

    ties = drain_tie_ins([r for r in model.pipe_runs if r.system == run.system])
    parent = ties.get(run.tag)
    if parent is None:
        problems.append(f"{run.tag}: nothing downstream of it is derivable, so there is "
                        "no root to route to. Name a --via, or route the parent first")
        return None
    chain: list[str] = []
    cursor: str | None = parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    other = next(r for r in model.pipe_runs if r.tag == parent)
    z = other.z_m or ()
    if len(z) != len(other.path):
        problems.append(f"{run.tag}: its discharge {parent} carries no resolved "
                        "elevations, so there is no invert to tie into")
        return None
    index = min(range(len(other.path)), key=lambda i: z[i])
    return ((other.path[index][0], other.path[index][1], z[index]), chain)


def _nearest_main(model: ResolvedModel, point: tuple[float, float], floor_m: float,
                  problems: list[str], target: str, *, exclude: str | None = None
                  ) -> tuple[tuple[float, float, float], str] | None:
    """The nearest drain run's vertex on this fixture's own floor.

    The vertical gate is ``mep.fixture_drain_reach``'s: a run counts only where it passes
    within two feet below and six inches above the fixture's storey datum. Without it the
    nearest main is whatever happens to lie beneath, two storeys down.

    **A run that already serves this fixture is excluded**, and that is not a nicety: asking
    for a branch to a fixture that has one means asking for a REPLACEMENT, and routing to
    the run being replaced finds its own start and reports a negative feasible slope — a
    true statement about a question nobody asked.
    """
    best = None
    for run in model.pipe_runs:
        if run.system != "drain" or not run.z_m:
            continue
        if exclude is not None and exclude in run.serves:
            continue
        for (x, y), z in zip(run.path, run.z_m, strict=False):
            if not (floor_m - 2.0 * 0.3048 <= z <= floor_m + 0.5 * 0.3048):
                continue
            distance = ((x - point[0]) ** 2 + (y - point[1]) ** 2) ** 0.5
            if best is None or distance < best[0]:
                best = (distance, (x, y, z), run.tag)
    if best is None:
        problems.append(f"{target}: no drain run passes on this fixture's own floor, so "
                        "there is nothing to route it to")
        return None
    return (best[1], best[2])


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
                *, with_z: bool = False) -> set[int]:
    """Every lattice node on the root's own plan point — a vertical, not a point.

    See :func:`~typehaus.routing.search.shortest_route`: a stack accepts arrivals over a
    range of elevations, and modelling it as one node throws away exactly the margin the
    oracle note's §5 turns on.

    **Plan only by default, with no z filter**, and that is not a shortcut. A gravity route
    searches in one plane and takes its elevations from the profile afterwards, so the
    lattice has no node at the root's own invert to find. ``with_z`` is the duct and
    raceway case: their search IS three-dimensional and their far end is one point at one
    height, so accepting any elevation on that plan point would land the run a storey away
    and call it arrival.
    """
    tolerance = 0.05
    return {node.index for node in graph.nodes
            if abs(node.x - root[0]) < tolerance and abs(node.y - root[1]) < tolerance
            and (not with_z or abs(node.z - root[2]) < tolerance)}


def _port_terminal(model: ResolvedModel, duct: Any, index: int) -> tuple[float, float, float]:
    """One end of a duct, snapped to the EXACT service port it lands on if there is one.

    An authored end inside a machine's case is a claim about which machine, not about which
    spigot: the case is a couple of feet across and the ports are inches apart on it. Where
    the type dimensions its port (``PortCertainty.EXACT``) the model knows the spigot's real
    station, and terminating a foot away from it proposes a lane an installer then has to
    re-aim. An APPROXIMATE port is left alone on purpose — see ``resolve/mep_ports.port_at``.

    The tolerance is the CASE, not a joint: the whole point is to correct an end that landed
    loosely inside one. Half a metre is wider than any residential air-handling case's half
    diagonal and far narrower than the gap to the next machine.
    """
    from typehaus.resolve.mep_ports import port_at

    point = duct.path[index]
    z = duct.z_m[index]
    system = duct.system.value if hasattr(duct.system, "value") else str(duct.system)
    port = port_at(model, point, z, duct_system=system, tolerance_m=0.5)
    return (point[0], point[1], z) if port is None else port.point


def _duct_size_advice(model: ResolvedModel, duct: Any) -> tuple[str, ...]:
    """What the equal-friction rule would size this duct at, beside what it is.

    **Advice, and deliberately not a change.** An authored size is a decision — a trunk run
    up a size for the static budget, a branch held down to clear a bay — and a router that
    silently re-sized it would be overruling the design to make its own arithmetic come out.
    What the router can do is say the number, so a size nobody chose on purpose stops being
    invisible. A campaign that CREATES a branch has no authored size to defer to and calls
    ``resolve/duct_sizing.size_for_cfm`` for the real answer.

    Round ducts only: the equal-friction rule is stated on a bore, and an equivalent
    diameter for a rectangle is a second reading this does not hold.
    """
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

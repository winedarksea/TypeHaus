"""Supply tie-in roots for haus route: the feeder line a supply run tees onto.

Split from ``route_roots``. A supply searches from its fixture to any point on its derived
feeder (``resolve/mep_tie_ins.supply_tie_in_records``); ``--lift`` swaps in a re-laid
feeder's new line (``reroot_supply``). See docs/routing.md."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from typehaus.cli.route_miss import Miss, log, miss

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


def _supply_trunk(model: ResolvedModel, run: Any, problems: list[str]
                  ) -> tuple[tuple[float, float, float], list[str],
                             tuple[tuple[tuple[float, float, float], ...], ...]] | None:
    """Return (feeder point, upstream chain, feeder polyline with z), or (port, [], ()).

    The whole upstream chain may be touched because each tee lies on its parent. Per-vertex
    z keeps goals on the feeder itself rather than its plan shadow. Refusals read the
    specific missing-parent cause from supply_tie_in_records."""
    ports, records = supply_records(model)
    record = records.get(run.tag)
    ties = {tag: rec.parent for tag, rec in records.items() if rec.parent}
    if record is not None and record.reason == "equipment_port":
        # A trunk leaving a machine roots ON the port: one exact point, no line to tee onto.
        port = next((p for p in ports
                     if f"{p.equipment_tag}.{p.port_tag}" == record.port), None)
        if port is not None:
            return port.point, [], ()
        miss(problems, run.tag, f"it leaves {record.port}, an equipment port that could "
             "not be placed, so there is no point to root it on", record.port,
             "Route it with --via")
        return None
    if record is None or record.parent is None:
        log(problems, _supply_refusal(run, record))
        return None
    chain: list[str] = []
    cursor: str | None = record.parent
    while cursor is not None and cursor not in chain:
        chain.append(cursor)
        cursor = ties.get(cursor)
    parent = next(r for r in model.pipe_runs if r.tag == record.parent)
    z = parent.z_m or ()
    if len(z) != len(parent.path):
        miss(problems, run.tag, f"its feeder {record.parent} carries no resolved "
             "elevations, so there is no line to tee onto", record.parent)
        return None
    line = tuple((p[0], p[1], zz) for p, zz in zip(parent.path, z, strict=False))
    # The root POINT is the derived tee itself — the station the record names — so a
    # refusal, a report and a `--json` payload all say the same place. The whole line goes
    # beside it as the goal SET, and `falls=False` means the caller uses the line.
    root = (record.station[0], record.station[1], run.z_m[0])
    return root, chain, (line,)


def supply_records(model: ResolvedModel) -> tuple[list, dict]:
    """(placed ports, every supply run's derived tee record by child tag)."""
    from typehaus.resolve.mep_ports import placed_ports
    from typehaus.resolve.mep_tie_ins import supply_tie_in_records

    ports = placed_ports(model)
    return ports, {rec.child: rec for rec in supply_tie_in_records(model.pipe_runs, ports)}


def reroot_supply(model: ResolvedModel, ends: Any, target: str, lines: dict) -> Any:
    """``ends`` teed onto its feeder's re-laid line where ``lines`` holds one (``--lift``):
    :func:`_supply_trunk`'s goal set, the new line for the authored one."""
    record = supply_records(model)[1].get(target) if ends.tie_is_the_goal else None
    line = lines.get(record.parent) if record is not None else None
    if not line:
        return ends
    line = tuple(tuple(p) for p in line)
    root = min(line, key=lambda p: sum((p[k] - ends.root[k]) ** 2 for k in range(3)))
    return replace(ends, root=root, root_paths=(line,))


def _supply_children(model: ResolvedModel, run: Any) -> tuple[str, ...]:
    """The runs that tee off ``run`` — their tie points ride on its line."""
    return tuple(c for c, rec in supply_records(model)[1].items() if rec.parent == run.tag)


def _supply_refusal(run: Any, record: Any) -> Miss:
    """The miss a parentless supply run gets, naming which cause applies.

    Three different facts about the model want three different sentences. One about a vent
    chase — which is what every supply run got until 2026-09-19 — is false about all three.
    """
    tag = run.tag
    if record is None:
        return Miss(tag, "it carries no resolved elevations, so there is no tee to derive")
    inches = None if record.z_gap_m is None else record.z_gap_m * 39.3700787
    if record.reason == "cross_system":
        return Miss(
            tag, f"the run standing at its first vertex is {record.nearest}, which is "
            f"a {'different' if record.nearest else 'cross-system'} system", record.nearest or "",
            "Its source is a machine rather than a pipe — a water heater, a softener, a mixing "
            "valve — and this derivation names runs. Route it with --via, or route the "
            "run it leaves")
    if record.reason == "elevation":
        return Miss(
            tag, f"{record.nearest} passes under its first vertex but {abs(inches):.1f}\" "
            f"{'above' if inches > 0 else 'below'} it", record.nearest or "",
            "The riser that would feed this run is not modelled, which is a gap in the plan "
            "and not a lane the search can find")
    return Miss(
        tag, "no run of any system passes under its first vertex, so the thing that "
        "feeds it is not a run in this model — a service lateral, or a riser nobody drew",
        "", "Author it, or name a --via")

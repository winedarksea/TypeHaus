"""Where a supply connection is isolated: the valves and tees on the walk back to its source.

Shared by ``mep.fixture_control_valve`` (UPC 606.5) and ``advisory.redundant_isolation``.
A *connection* is the last vertex of a supply run that feeds nothing further: a fixture, an
appliance or a machine inlet. Walking upstream from it, the first thing met decides: a valve
isolates that connection alone; a tee to anything else means the next valve up is shared;
a run that starts on a manifold outlet ends the walk at the port. The tree is
``mep_tie_ins.supply_tie_in_records``; ``serves`` names the fixture only at the connection,
where it is one tag, because upstream it is often a superset.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from typehaus.model.enums import EquipmentKind
from typehaus.resolve.mep_ports import placed_ports
from typehaus.resolve.mep_tie_ins import supply_tie_in_records

_SUPPLY = {"water_cold", "water_hot"}
_VALVES = {"shutoff", "main_shutoff"}
# A tee within this of a run's end feeds through it, so the end is not a connection.
_END_TOL_M = 3 * 0.0254
_PORT_TOL_M = 0.0127


@dataclass(frozen=True)
class Isolation:
    """What isolates one connection, read on the walk upstream from it.

    ``valve`` is the accessory tag met before any tee, or None. ``port`` is the manifold
    outlet (``"EQ-..out-3"``) the walk reached with neither met. ``blocked_by`` is the tee
    (child run tag) met first when neither was."""

    run: str
    system: str
    target: str | None
    valve: str | None = None
    port: str | None = None
    blocked_by: str | None = None


@dataclass
class SupplyTree:
    runs: dict
    parent: dict = field(default_factory=dict)      # child -> (parent tag, station m)
    children: dict = field(default_factory=dict)    # parent -> [(station m, child tag)]
    source_port: dict = field(default_factory=dict)  # child -> "EQ.port"
    valves: dict = field(default_factory=dict)      # run -> [(station m, accessory)]


def _station(run, xyz) -> float:
    """Developed 3D distance along ``run`` to the point nearest ``xyz``."""
    best, walked, at = math.inf, 0.0, 0.0
    pts = [(p[0], p[1], z) for p, z in zip(run.path, run.z_m, strict=False)]
    for a, b in zip(pts, pts[1:], strict=False):
        seg = [b[i] - a[i] for i in range(3)]
        length_sq = sum(c * c for c in seg)
        f = 0.0 if length_sq < 1e-12 else max(0.0, min(1.0, sum(
            (xyz[i] - a[i]) * seg[i] for i in range(3)) / length_sq))
        d = math.dist(xyz, [a[i] + f * seg[i] for i in range(3)])
        if d < best:
            best, at = d, walked + f * math.sqrt(length_sq)
        walked += math.sqrt(length_sq)
    return at


def _length(run) -> float:
    pts = [(p[0], p[1], z) for p, z in zip(run.path, run.z_m, strict=False)]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:], strict=False))


def supply_tree(model) -> SupplyTree:
    runs = {r.tag: r for r in model.pipe_runs
            if r.system in _SUPPLY and r.path and r.z_m is not None}
    tree = SupplyTree(runs)
    for record in supply_tie_in_records(model.pipe_runs, placed_ports(model)):
        child = runs.get(record.child)
        if child is None:
            continue
        if record.reason == "equipment_port" and record.port:
            tree.source_port[record.child] = record.port
        elif record.accepted and record.parent in runs:
            tee = (child.path[0][0], child.path[0][1], child.z_m[0])
            station = _station(runs[record.parent], tee)
            tree.parent[record.child] = (record.parent, station)
            tree.children.setdefault(record.parent, []).append((station, record.child))
    for accessory in model.pipe_accessories:
        run = runs.get(accessory.pipe_ref or "")
        if run is not None and accessory.kind in _VALVES:
            point = (accessory.position[0], accessory.position[1], accessory.z_m)
            tree.valves.setdefault(run.tag, []).append((_station(run, point), accessory))
    return tree


def walk_up(tree: SupplyTree, run_tag: str, station: float,
            skip_valve: str | None = None) -> Isolation:
    """The first valve, tee or manifold port upstream of ``station`` on ``run_tag``."""
    run_tag0, came_from = run_tag, None
    while True:
        run = tree.runs[run_tag]
        events = [(s, "valve", a.tag) for s, a in tree.valves.get(run_tag, ())
                  if s <= station + 1e-6 and a.tag != skip_valve]
        events += [(s, "tee", c) for s, c in tree.children.get(run_tag, ())
                   if s < station - 1e-6 and c != came_from]
        if events:
            _, kind, tag = max(events, key=lambda e: (e[0], e[1] == "valve"))
            if kind == "valve":
                return Isolation(run_tag0, run.system, None, valve=tag)
            return Isolation(run_tag0, run.system, None, blocked_by=tag)
        if run_tag in tree.source_port:
            return Isolation(run_tag0, run.system, None, port=tree.source_port[run_tag])
        if run_tag not in tree.parent:
            return Isolation(run_tag0, run.system, None)
        came_from = run_tag
        run_tag, station = tree.parent[run_tag]
        # Past the tee the parent must feed nothing else, or any valve above it is shared.
        beyond = [c for s, c in tree.children.get(run_tag, ())
                  if s >= station - 1e-6 and c != came_from]
        if beyond or _length(tree.runs[run_tag]) - station > _END_TOL_M:
            return Isolation(run_tag0, tree.runs[run_tag].system, None,
                             blocked_by=beyond[0] if beyond else run_tag)


def connections(model, tree: SupplyTree) -> list[tuple[str, str | None]]:
    """``(run tag, fed element tag)`` for every run end that feeds nothing further.

    The element is the machine whose exact port the end stands on, else the run's single
    ``serves`` tag, else the nearest of several. A water manifold's inlet is a feed, not a
    connection; an end with nothing to name (a capped stub) is left out."""
    ports = placed_ports(model)
    manifolds = {e.tag for e in model.plan.all_elements() if e.element_kind == "Equipment"
                 and getattr(e, "kind", None) is EquipmentKind.WATER_MANIFOLD}
    objects = {o.tag: o for o in model.canvas_objects}
    out = []
    for tag, run in tree.runs.items():
        end_station = _length(run)
        if any(s >= end_station - _END_TOL_M for s, _ in tree.children.get(tag, ())):
            continue
        (x, y), z = run.path[-1][:2], run.z_m[-1]
        port = next((p for p in ports if p.exact and max(
            abs(p.x_m - x), abs(p.y_m - y), abs(p.z_m - z)) <= _PORT_TOL_M), None)
        if port is not None:
            if port.equipment_tag not in manifolds:
                out.append((tag, port.equipment_tag))
            continue
        serves = list(run.serves or ())
        if len(serves) > 1:
            serves = [min(serves, key=lambda name: _gap(objects.get(name), (x, y)))]
        if serves:
            out.append((tag, serves[0]))
    return out


def _gap(obj, xy) -> float:
    """Plan distance from ``xy`` to a canvas object's footprint centre (inf if none)."""
    if obj is None or not obj.footprint:
        return math.inf
    cx = sum(p[0] for p in obj.footprint) / len(obj.footprint)
    cy = sum(p[1] for p in obj.footprint) / len(obj.footprint)
    return math.dist((cx, cy), xy)


def isolation_of(tree: SupplyTree, run_tag: str, target: str | None) -> Isolation:
    found = walk_up(tree, run_tag, _length(tree.runs[run_tag]))
    return Isolation(found.run, found.system, target, found.valve, found.port,
                     found.blocked_by)

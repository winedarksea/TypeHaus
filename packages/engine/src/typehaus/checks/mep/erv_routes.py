"""Which trunks lie on each air path out of the ventilator: a walk, not a sum.

Split out of ``erv_static.py`` for size. Until 2026-11-11 every trunk on a side rode on every
path of that side, so a basement radial paid for the riser and ``DU-S-ERV-HP-FEED`` it never
crosses (note §9). Now a landing pays only the trunks between the machine and its plenum.

* The graph is trunks and equipment: a trunk joins the equipment its ends sit in
  (``equipment_at_end``) and every trunk it is joined to (``ducts_are_joined``). The walk
  starts at the machine and passes through distributing plenums only.
* A trunk ending in a hood is an outdoor leg and rides every path of its side.
* A trunk ending in other equipment (a mixing box) is a path of its own.
* A plenum no trunk reaches is charged the nearest trunk on its side, inclusive: the tap
  a feed would take (catlin's level-2 supply plenum, whose feed cannot be drawn, §9).
* A trunk the walk never reaches rides every path, the old conservative rule, so nothing
  leaves the budget silently.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from typehaus.checks.mep.erv_landings import _end_host
from typehaus.checks.registry import CheckContext
from typehaus.model.enums import EquipmentKind


@dataclass
class TrunkRoutes:
    outdoor: list[str] = field(default_factory=list)
    unrouted: list[str] = field(default_factory=list)
    to_plenum: dict[str, list[str]] = field(default_factory=dict)
    #: ``[(equipment tag, route)]`` for a trunk that lands in non-plenum equipment.
    to_equipment: list[tuple[str, list[str]]] = field(default_factory=list)

    def for_plenum(self, host: str) -> list[str]:
        return _unique(self.outdoor + self.unrouted + self.to_plenum.get(host, []))

    def for_route(self, route: list[str]) -> list[str]:
        return _unique(self.outdoor + self.unrouted + route)


def _unique(tags: list[str]) -> list[str]:
    return list(dict.fromkeys(tags))


def _segment_distance(p, a, b) -> float:
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    denom = sum(c * c for c in ab)
    t = 0.0 if denom == 0 else max(0.0, min(1.0, sum(ab[i] * ap[i] for i in range(3)) / denom))
    return math.dist(p, [a[i] + t * ab[i] for i in range(3)])


def distance_to_run(xy, z: float | None, duct) -> float:
    """Shortest distance from a point to a run's polyline; in plan where either lacks z."""
    has_z = z is not None and duct.z_m and len(duct.z_m) == len(duct.path)
    zs = duct.z_m if has_z else [0.0] * len(duct.path)
    point = (xy[0], xy[1], z if has_z else 0.0)
    pts = [(x, y, zz) for (x, y), zz in zip(duct.path, zs, strict=True)]
    if len(pts) == 1:
        return math.dist(point, pts[0])
    return min(_segment_distance(point, a, b) for a, b in zip(pts, pts[1:], strict=False))


def trunk_routes(ctx: CheckContext, machine_tag: str, trunks: list, plenums: dict,
                 kinds: dict[str, str], hosts_on_side: set[str]) -> TrunkRoutes:
    """Each side's trunk routes from ``machine_tag``; ``hosts_on_side`` are its plenums."""
    from typehaus.resolve.mep_soffit import ducts_are_joined

    out = TrunkRoutes()
    tags = [duct.tag for duct in trunks]
    ends = {duct.tag: {_end_host(ctx, duct, i)[0] for i in (0, -1)} - {None}
            for duct in trunks}
    hood = EquipmentKind.DUCT_MANIFOLD.value
    adjacency: dict[tuple[str, str], set[tuple[str, str]]] = {}

    def link(a, b):
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    for tag in tags:
        for host in ends[tag]:
            link(("T", tag), ("E", host))
        if any(kinds.get(h) == hood and h not in plenums for h in ends[tag]):
            out.outdoor.append(tag)
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            if ducts_are_joined(ctx.model, a, b):
                link(("T", a), ("T", b))

    root = ("E", machine_tag)
    parent: dict[tuple[str, str], tuple[str, str] | None] = {root: None}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if node[0] == "E" and node != root and node[1] not in plenums:
            continue  # a hood, a mixing box: a leaf, never a pass-through
        for nxt in sorted(adjacency.get(node, ())):
            if nxt not in parent and nxt != ("E", machine_tag):
                parent[nxt] = node
                queue.append(nxt)

    def route(node) -> list[str]:
        chain, up = [], node
        while up is not None:
            if up[0] == "T":
                chain.append(up[1])
            up = parent[up]
        return chain[::-1]

    outdoor = set(out.outdoor)
    out.unrouted = [t for t in tags if ("T", t) not in parent and t not in outdoor]
    for host in sorted(hosts_on_side):
        if ("E", host) in parent:
            out.to_plenum[host] = route(("E", host))
            continue
        obj = next((o for o in ctx.model.canvas_objects if o.tag == host), None)
        candidates = [d for d in trunks if d.tag not in outdoor and ("T", d.tag) in parent]
        if obj is None or not candidates:
            continue
        nearest = min(candidates, key=lambda d: (
            distance_to_run(obj.position, obj.z_m, d), d.tag))
        out.to_plenum[host] = route(("T", nearest.tag))
    for tag in tags:
        if ("T", tag) not in parent or tag in outdoor:
            continue
        for host in sorted(ends[tag]):
            if kinds.get(host) not in (None, hood, EquipmentKind.ERV.value) \
                    and host not in plenums:
                out.to_equipment.append((host, route(("T", tag))))
    return out

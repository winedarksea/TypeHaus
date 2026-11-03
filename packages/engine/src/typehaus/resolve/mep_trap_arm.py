"""The trap arm, walked in 3D to the vent that ends it — shared by the check and the router.

MN 4714 (UPC) 1002.2 measures the developed length from the trap weir to the vent, against
Table 1002.2 (``resolve/plumbing_tables.TRAP_ARM_MAX_IN``); 908 lets a legal WET VENT end it
too. ``mep.trap_arm_developed`` wraps :func:`developed_arm` in a Finding, and
``routing``'s arm-and-vent search closes an arm only where :func:`grade_wet_vent` or a true
vent tee would, so the router and the check cannot disagree.

A vent tee is a serving VENT run's endpoint on a drain segment in 3D (within
``TEE_TOL_M``). The walk starts at the fixture's most upstream serving drain, follows it
downstream into each parent where it ends, and stops at the first tee or legal wet vent.

Wet-vent data in: ``fx`` maps fixture tag -> ``(leaf drain run, DFU, plan symbol, storey)``;
``parents`` maps a run to ``(parent run, segment index, t)`` where its end stands.
``houses/catlin/notes/wet_vent_basis.md`` works a case by hand.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.plumbing_tables import (
    BATHROOM_GROUP_SYMBOLS,
    DRAIN_BRANCH_CAPACITY_DFU,
    WET_VENT_HORIZONTAL_MIN_IN,
    WET_VENT_MIN_IN,
    WET_VENT_VERTICAL_MAX_FIXTURES,
    WET_VENT_VERTICAL_MAX_IN,
    WET_VENT_VERTICAL_UPPER_DFU_MAX,
    required_drain_diameter_in,
)

Fx = tuple[str, float, str, str]
Order = tuple[int, float]  # (segment, t) where a run enters another; (-1, 0) = starts there


def _entries(leaf: str, parents: dict[str, tuple]) -> dict[str, Order]:
    """Every run this fixture's waste crosses, with where it enters each."""
    out: dict[str, Order] = {leaf: (-1, 0.0)}
    run = leaf
    while run in parents and parents[run][0] not in out:
        tag, i, t = parents[run]
        out[tag] = (i, t)
        run = tag
    return out


def _is_vertical(pts: list) -> bool:
    """UPC "vertical": 45° or steeper overall, so rise ≥ plan run."""
    rise = sum(abs(b[2] - a[2]) for a, b in zip(pts, pts[1:], strict=False))
    plan = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False))
    return rise > plan


def _length_in(pts: list) -> float:
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:], strict=False)) / M_PER_IN


def _next_size(size_in: float) -> float:
    return next((s for s, _ in DRAIN_BRANCH_CAPACITY_DFU if s > size_in + 1e-6), size_in)


def _size_in(radius_m: float) -> float:
    return round(2.0 * radius_m / M_PER_IN, 2)


def grade_wet_vent(child: str, parent: str, join: Order, drains: dict[str, list],
                   radii: dict[str, float], parents: dict[str, tuple],
                   fx: dict[str, Fx], arm_fx: str) -> tuple[bool, str]:
    """``(legal, why)`` for ``child`` wet-venting ``arm_fx`` where it joins ``parent``."""
    vertical = _is_vertical(drains[child])
    via_child: dict[str, Order] = {}
    via_parent: dict[str, Order] = {}
    for tag, (leaf, *_rest) in fx.items():
        ent = _entries(leaf, parents)
        if child in ent:
            via_child[tag] = ent[child]
        elif parent in ent:
            via_parent[tag] = ent[parent]
    members = {**via_child, **({} if vertical else via_parent)}
    dfu = sum(fx[t][1] for t in members)
    d_child, d_parent = _size_in(radii[child]), _size_in(radii[parent])
    bad: list[str] = []
    if vertical:
        sec = f"908.1 vertical, Ø{d_child:g}\" {_length_in(drains[child]):.0f}\" long"
        if arm_fx not in via_child:
            bad.append(f"{arm_fx} does not discharge into the vertical wet vent")
        if len(members) > WET_VENT_VERTICAL_MAX_FIXTURES:
            bad.append(f"{len(members)} fixtures vent through it (max "
                       f"{WET_VENT_VERTICAL_MAX_FIXTURES})")
        if len({fx[t][3] for t in members}) > 1:
            bad.append("fixtures on more than one storey")
        if _length_in(drains[child]) > WET_VENT_VERTICAL_MAX_IN:
            bad.append(f"developed {_length_in(drains[child]):.0f}\" over "
                       f"{WET_VENT_VERTICAL_MAX_IN:.0f}\"")
        lowest = max(members, key=lambda t: via_child[t], default=None)
        big = [t for t in members if t != lowest and fx[t][1] > WET_VENT_VERTICAL_UPPER_DFU_MAX]
        if big:
            bad.append(f"upper fixture {big[0]} is over {WET_VENT_VERTICAL_UPPER_DFU_MAX:g} DFU")
        # Min waste of the upper fixture: its own authored trap-arm run stands in for it.
        waste = max((_size_in(radii[fx[t][0]]) for t in members if t != lowest), default=0.0)
        need = max(_next_size(waste), _next_size(required_drain_diameter_in(dfu) or 0.0),
                   WET_VENT_MIN_IN)
        if d_child < need - 1e-6:
            bad.append(f"Ø{d_child:g}\" under the {need:g}\" 908.1 asks for {dfu:g} DFU")
    else:
        need = next(m for lim, m in WET_VENT_HORIZONTAL_MIN_IN if dfu <= lim + 1e-9)
        sec = f"908.2 horizontal, {dfu:g} DFU, Ø{min(d_child, d_parent):g}\""
        if arm_fx not in members:
            bad.append(f"{arm_fx} does not discharge into it")
        if min(d_child, d_parent) < need - 1e-6:
            bad.append(f"Ø{min(d_child, d_parent):g}\" under the {need:g}\" it needs for "
                       f"{dfu:g} DFU, whole length (PB0225)")
        off = sorted(t for t in members if fx[t][2] not in BATHROOM_GROUP_SYMBOLS)
        if off:
            bad.append(f"{off[0]} is not a bathroom-group fixture")
        if len({fx[t][3] for t in members}) > 1:
            bad.append("fixtures on more than one floor")
        upstream = [t for t in members if t not in via_child and via_parent[t] < join]
        if len(upstream) > 1:
            bad.append(f"{len(upstream)} wet-vented drains ({', '.join(sorted(upstream))}) "
                       "discharge upstream of the dry-vent connection (max 1)")
        at = {**dict.fromkeys(via_child, join), **via_parent}
        at = {t: o for t, o in at.items() if t in members}
        first = [t for t in at if fx[t][2].startswith("toilet")
                 and any(o > at[t] for o in at.values())]
        if first:
            bad.append(f"{first[0]} discharges before other connections; 908.2.4 puts a "
                       "water closet downstream of all")
    return (not bad), (f"{sec}: " + ("; ".join(bad) if bad else f"ok for {dfu:g} DFU"))


#: An inlet (vent end or child drain) meets a drain inside its bore plus this — an
#: upper-half entry is on the pipe, which ``mep.drain_tie_in`` grades on its own.
TEE_TOL_M = 0.5 * M_PER_IN
#: The fixture's arm starts at a serving run's first vertex this close to its drain point.
START_TOL_M = 12.0 * M_PER_IN

Point3 = tuple[float, float, float]


def run_points(run) -> list[Point3] | None:
    z = run.z_m
    if not z or len(z) != len(run.path) or any(v is None for v in z):
        return None
    return [(p[0], p[1], h) for p, h in zip(run.path, z, strict=True)]


def _project(p: Point3, a: Point3, b: Point3) -> tuple[float, float]:
    """``(distance from p to segment ab, parameter t along it)``."""
    ab = [b[i] - a[i] for i in range(3)]
    span = sum(c * c for c in ab)
    t = 0.0 if span == 0 else max(0.0, min(1.0, sum(ab[i] * (p[i] - a[i])
                                                   for i in range(3)) / span))
    q = [a[i] + t * ab[i] for i in range(3)]
    return math.dist(p, q), t


def drain_parent(end: Point3, own: str, drains: dict[str, list[Point3]],
            radii: dict[str, float]):
    """The drain run whose segment the child's last vertex stands on: (tag, index, t)."""
    best = None
    for tag, pts in drains.items():
        if tag == own:
            continue
        for i in range(len(pts) - 1):
            d, t = _project(end, pts[i], pts[i + 1])
            if d <= radii[tag] + TEE_TOL_M and (best is None or d < best[0]):
                best = (d, tag, i, t)
    return None if best is None else best[1:]


def _on_run(p: Point3, pts: list[Point3], reach: float) -> bool:
    return any(_project(p, a, b)[0] <= reach for a, b in zip(pts, pts[1:], strict=False))


def developed_arm(start_run: str, drains: dict[str, list[Point3]], radii: dict[str, float],
                  vent_ends: list[Point3], wet: tuple[dict, str] | None = None
                  ) -> tuple[float | None, str, float, list[str]]:
    """``(arm m or None, what vents it, nearest vent gap m, wet vents rejected)`` downstream.

    ``wet`` is ``(fixtures, arm fixture)`` for ``wet_vent.grade_wet_vent``; without it no
    wet vent can be graded, so none ends the arm. A wet vent that fails 908 is skipped."""
    vented = {tag for tag, pts in drains.items()
              if any(_on_run(v, pts, radii[tag] + TEE_TOL_M) for v in vent_ends)}
    parents = {tag: p for tag in drains
               if (p := drain_parent(drains[tag][-1], tag, drains, radii))}
    joins: dict[str, list[tuple[str, Point3]]] = {}
    for tag in vented:
        if tag in parents:
            joins.setdefault(parents[tag][0], []).append((tag, drains[tag][-1]))
    run, index, t0, walked, came = start_run, 0, 0.0, 0.0, None
    visited: set[str] = set()
    notes: list[str] = []
    while run not in visited:
        visited.add(run)
        pts, reach = drains[run], radii[run] + TEE_TOL_M
        for i in range(index, len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            start = t0 if i == index else 0.0
            hits = [(t, "a vent tee", None) for d, t in (_project(v, a, b) for v in vent_ends)
                    if d <= reach and t >= start - 1e-9]
            hits += [(t, child, child) for child, end in joins.get(run, ())
                     if child != came for d, t in [_project(end, a, b)]
                     if d <= reach and t >= start - 1e-9]
            for t, what, child in sorted(hits):
                if child is not None:
                    ok, why = (grade_wet_vent(child, run, parents[child][1:], drains, radii,
                                              parents, *wet) if wet else
                               (False, "no fixture data to grade it"))
                    if not ok:
                        notes.append(f"{child} rejected as a wet vent ({why})")
                        continue
                    what = f"{child}, wet-vented ({why})"
                return walked + (t - start) * math.dist(a, b), what, 0.0, notes
            walked += (1.0 - start) * math.dist(a, b)
        if run not in parents:
            break
        came, (run, index, t0) = run, parents[run]
    gap = min((min(_project(v, a, b)[0] for pts in drains.values()
                   for a, b in zip(pts, pts[1:], strict=False))
               for v in vent_ends), default=math.inf)
    return None, "", gap, notes


def arm_leaves(serving: list, point, drains, radii) -> list:
    """Serving drains by distance from the fixture's drain point, most upstream only:
    ``[((dist, tag), run), ...]`` — a run no other serving drain ends on."""
    fed = {p[0] for r in serving
           if (p := drain_parent(drains[r.tag][-1], r.tag, drains, radii)) is not None}
    leaves = [r for r in serving if r.tag not in fed] or serving
    return sorted(((math.hypot(drains[r.tag][0][0] - point[0],
                               drains[r.tag][0][1] - point[1]), r.tag), r) for r in leaves)


def arm_is_vented(model, fixture: str, drain_point) -> bool:
    """Whether ``fixture``'s authored arm already meets a vent within Table 1002.2.

    The check's own walk (``mep.trap_arm_developed``), wet vents ungraded: a wet-vented
    fixture reads as unvented here, so the router offers it a vent rather than skip one.
    """
    from typehaus.resolve.plumbing_tables import trap_arm_limit_in

    drains = {r.tag: pts for r in model.pipe_runs
              if r.system == "drain" and (pts := run_points(r)) is not None}
    radii = {r.tag: r.diameter_m / 2.0 for r in model.pipe_runs if r.tag in drains}
    serving = [r for r in model.pipe_runs
               if r.system == "drain" and fixture in r.serves and r.tag in drains]
    vents = [r for r in model.pipe_runs if r.system == "vent" and fixture in r.serves]
    if drain_point is None or not serving or not vents:
        return False
    starts = arm_leaves(serving, drain_point, drains, radii)
    if starts[0][0][0] > START_TOL_M:
        return False
    run = starts[0][1]
    limit_in = trap_arm_limit_in(run.diameter_m)
    ends = [p for r in vents if (pts := run_points(r)) for p in (pts[0], pts[-1])]
    arm_m, _what, _gap, _notes = developed_arm(run.tag, drains, radii, ends)
    return arm_m is not None and limit_in is not None and arm_m / M_PER_IN <= limit_in + 1e-6

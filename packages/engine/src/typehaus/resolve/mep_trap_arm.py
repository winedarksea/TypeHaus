"""The trap arm, walked in 3D to the vent that ends it — shared by the check and the router.

MN 4714 (UPC) 1002.2 measures the developed length from the trap weir to the vent, against
Table 1002.2 (``resolve/plumbing_tables.TRAP_ARM_MAX_IN``); 908 lets a legal WET VENT end it
too. ``mep.trap_arm_length`` wraps :func:`developed_arm` in a Finding; the router reads the
same walk, wet vents graded, through :func:`arm_is_vented` and :func:`grade_hypothetical_tie`,
so the router and the check cannot disagree.

A vent tee is a serving VENT run's endpoint on a drain segment in 3D (within
``TEE_TOL_M``). The walk starts at the fixture's most upstream serving drain, follows it
downstream into each parent where it ends, and stops at the first tee or legal wet vent —
including one whose dry vent connects upstream of where the arm enters (908.2.1: the wet vent
runs from that connection downstream), which ends the arm at its own entry.

Wet-vent data in: ``fx`` maps fixture tag -> ``(leaf drain run, DFU, plan symbol, storey)``;
``parents`` maps a run to ``(parent run, segment index, t)`` where its end stands.
``houses/catlin/notes/wet_vent_basis.md`` works a case by hand.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

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
    """``(legal, why)`` for ``child`` wet-venting ``arm_fx`` where it joins ``parent``.

    A child rising more than it runs is graded as a 908.1 vertical wet vent, even a
    dry-vented lavatory's own drop: whether 908.2 admits that (§5 option X) is an
    owner/AHJ question, not read into the code here."""
    via_child: dict[str, Order] = {}
    via_parent: dict[str, Order] = {}
    for tag, (leaf, *_rest) in fx.items():
        ent = _entries(leaf, parents)
        if child in ent:
            via_child[tag] = ent[child]
        elif parent in ent:
            via_parent[tag] = ent[parent]
    vertical = _is_vertical(drains[child])
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
        upstream = [t for t in members if t not in via_child and via_parent[t] < join]
        at = {**dict.fromkeys(via_child, join), **via_parent}
        bad += _group_rules(members, {t: o for t, o in at.items() if t in members},
                            upstream, fx)
    return (not bad), (f"{sec}: " + ("; ".join(bad) if bad else f"ok for {dfu:g} DFU"))


def _group_rules(members, at: dict[str, Order], upstream: list[str], fx) -> list[str]:
    """908.2.1's group-only, one-floor, one-upstream rules and 908.2.1.4's WC last."""
    bad = []
    off = sorted(t for t in members if fx[t][2] not in BATHROOM_GROUP_SYMBOLS)
    if off:
        bad.append(f"{off[0]} is not a bathroom-group fixture")
    if len({fx[t][3] for t in members}) > 1:
        bad.append("fixtures on more than one floor")
    if len(upstream) > 1:
        bad.append(f"{len(upstream)} wet-vented drains ({', '.join(sorted(upstream))}) "
                   "discharge upstream of the dry-vent connection (max 1)")
    first = [t for t in at if fx[t][2].startswith("toilet")
             and any(o > at[t] for o in at.values())]
    if first:
        bad.append(f"{first[0]} discharges before other connections; 908.2.4 puts a "
                   "water closet downstream of all")
    return bad


def grade_wet_run(host: str, tee: Order, entry: Order, drains: dict[str, list],
                  radii: dict[str, float], parents: dict[str, tuple], fx: dict[str, Fx],
                  arm_fx: str) -> tuple[bool, str]:
    """``(legal, why)`` for ``arm_fx`` entering ``host`` at ``entry``, downstream of a dry
    vent's connection on ``host`` itself at ``tee``: 908.2.1's wet vent runs "from the
    connection of the dry vent along the direction of the flow"; a fixture whose leaf is
    ``host`` is the dry-vented one, never an upstream wet arm."""
    members = {t: ent[host] for t, (leaf, *_r) in fx.items()
               if host in (ent := _entries(leaf, parents))}
    dfu = sum(fx[t][1] for t in members)
    need = next(m for lim, m in WET_VENT_HORIZONTAL_MIN_IN if dfu <= lim + 1e-9)
    size = _size_in(radii[host])
    bad: list[str] = []
    if arm_fx not in members:
        bad.append(f"{arm_fx} does not discharge into it")
    pts = drains[host]
    i, t = entry
    # A join on a corner meets both legs there; it is vertical only if both are.
    legs = [k for k in (i - (t < 1e-6), i, i + (t > 1 - 1e-6)) if 0 <= k < len(pts) - 1]
    if legs and all(_is_vertical(pts[k:k + 2]) for k in legs):
        bad.append(f"{arm_fx} joins a vertical section; 908.2.1 connects it horizontally")
    if size < need - 1e-6:
        bad.append(f"Ø{size:g}\" under the {need:g}\" it needs for {dfu:g} DFU, whole "
                   "length (PB0225)")
    stretch = [*pts[tee[0] + 1:entry[0] + 1]]
    if _is_vertical([_at(pts, tee), *stretch, _at(pts, entry)]):
        bad.append("its run from the dry vent to the arm rises more than it runs, a 908.1 "
                   "vertical wet vent this horizontal grade does not cover")
    upstream = [t for t, o in members.items() if fx[t][0] != host and _before(o, tee)]
    bad += _group_rules(members, members, upstream, fx)
    sec = f"908.2 horizontal from its dry vent, {dfu:g} DFU, Ø{size:g}\""
    return (not bad), (f"{sec}: " + ("; ".join(bad) if bad else f"ok for {dfu:g} DFU"))


def _at(pts: list, at: Order) -> tuple:
    i, t = max(at[0], 0), at[1]
    a, b = pts[i], pts[min(i + 1, len(pts) - 1)]
    return tuple(a[k] + t * (b[k] - a[k]) for k in range(3))


def _before(a: Order, b: Order) -> bool:
    return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1] - 1e-6)


#: A floor-outlet fixture's port this close over its storey datum is at the floor, and its
#: 1 1/2" P-trap hangs just under the subfloor, outlet this far under the datum (top of
#: joists): its arm lies in the bay, not through the plates (``mep_drain_routing_basis`` §14).
FLOOR_OUTLET_M = 6 * M_PER_IN
UNDER_FLOOR_WEIR_M = 3 * M_PER_IN
_FLOOR_OUTLETS = ("tub", "shower", "kohler-underscore", "floor-drain")


def under_floor_weir_m(model, fixture: str, datum_m: float, port) -> float | None:
    """A tub, shower or floor drain's under-floor trap weir, or None: the port is the weir.

    ``port`` is storey-relative. A water closet traps in its bowl and a sink in its cabinet,
    so neither is ever lowered, wherever its port is authored."""
    types = {t.tag: t.plan_symbol for t in model.plan.library.fixture_types}
    symbol = types.get(getattr(model.plan.by_tag(fixture), "type_ref", None)) or ""
    if port is None or port[2] > FLOOR_OUTLET_M or not symbol.startswith(_FLOOR_OUTLETS):
        return None
    return datum_m - UNDER_FLOOR_WEIR_M


def trap_weir_m(model, fixture: str, datum_m: float, port, arm: list[Point3]) -> float:
    """The weir a graded arm starts from, for the checks: the drain point; a floor outlet's
    under-floor trap on a framed floor (:func:`under_floor_weir_m`); and on a pour slab, where
    the trap is set in the fill at whatever depth the arm wants, the foot of the authored
    plumb drop under the drain point."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.slab_clip import floor_outline
    from typehaus.resolve.solid_categories import is_pour_slab

    weir = under_floor_weir_m(model, fixture, datum_m, port)
    if weir is None:
        return arm[0][2]
    here = Point(arm[0][:2])
    if any(is_pour_slab(s.category) and len(s.outline) >= 3
           and abs(s.z1_m - datum_m) <= FLOOR_OUTLET_M
           and Polygon(floor_outline(model, s)).contains(here) for s in model.solids):
        foot = arm[0]
        for p in arm[1:]:
            if math.dist(p[:2], foot[:2]) > 1e-6:
                break
            foot = p
        return foot[2]
    return weir


def fixture_rim_m(model, fixture: str) -> float | None:
    """The flood rim: the type's ``flood_rim_height`` over the body's base, else the body's
    top, which no rim exceeds (conservative for UPC 905.3's 6" line); None where the body
    states no height."""
    element = model.plan.by_tag(fixture)
    uid = getattr(element, "uid", None)
    obj = next((o for o in model.canvas_objects if o.uid == uid), None)
    if obj is None:
        return None
    ftype = next((t for t in model.plan.library.fixture_types
                  if t.tag == getattr(element, "type_ref", None)), None)
    rim = getattr(ftype, "flood_rim_height", None)
    return obj.body_z1_m if rim is None else obj.body_z0_m + rim.meters


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
        if came is not None and wet:
            what = _entered_wet_vent(run, (index, t0), came, vent_ends, joins, drains, radii,
                                     parents, wet, notes)
            if what is not None:
                return walked, what, 0.0, notes
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


def _entered_wet_vent(run: str, entry: Order, came: str, vent_ends: list[Point3],
                      joins: dict, drains: dict[str, list[Point3]], radii: dict[str, float],
                      parents: dict[str, tuple], wet: tuple[dict, str],
                      notes: list[str]) -> str | None:
    """908.2.1: an arm entering ``run`` downstream of a dry vent's connection to it — a vent
    end on ``run``, or a dry-vented child joining it — is vented at its own entry if that
    wet vent is legal (``mep_group_wet_vent_basis.md`` §2 F1). Nearest connection first."""
    pts, reach = drains[run], radii[run] + TEE_TOL_M
    found: list[tuple[Order, str | None]] = []
    for v in vent_ends:
        at = next(((i, t) for i in range(len(pts) - 1)
                   for d, t in [_project(v, pts[i], pts[i + 1])] if d <= reach), None)
        if at is not None and _before(at, entry):
            found.append((at, None))
    found += [(parents[child][1:], child) for child, _end in joins.get(run, ())
              if child != came and _before(parents[child][1:], entry)]
    for at, child in sorted(found, key=lambda f: f[0], reverse=True):
        ok, why = (grade_wet_vent(child, run, at, drains, radii, parents, *wet) if child
                   else grade_wet_run(run, at, entry, drains, radii, parents, *wet))
        if ok:
            return f"{child or run}, wet-vented downstream of its dry vent ({why})"
        notes.append(f"{child or run} rejected as a wet vent ({why})")
    return None


def walk_to(start_run: str, drains: dict[str, list[Point3]], radii: dict[str, float],
            length_m: float) -> Point3:
    """The point :func:`developed_arm`'s walk stands at ``length_m`` downstream: the tee."""
    run, index, t0, left = start_run, 0, 0.0, length_m
    visited: set[str] = set()
    while run not in visited:
        visited.add(run)
        pts = drains[run]
        for i in range(index, len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            start = t0 if i == index else 0.0
            span = (1.0 - start) * math.dist(a, b)
            if left <= span + 1e-9:
                t = start + (left / math.dist(a, b) if span > 0 else 0.0)
                return tuple(a[k] + t * (b[k] - a[k]) for k in range(3))
            left -= span
        parent = drain_parent(pts[-1], run, drains, radii)
        if parent is None:
            return pts[-1]
        run, index, t0 = parent
    return drains[run][-1]


def arm_leaves(serving: list, point, drains, radii) -> list:
    """Serving drains by distance from the fixture's drain point, most upstream only:
    ``[((dist, tag), run), ...]`` — a run no other serving drain ends on."""
    fed = {p[0] for r in serving
           if (p := drain_parent(drains[r.tag][-1], r.tag, drains, radii)) is not None}
    leaves = [r for r in serving if r.tag not in fed] or serving
    return sorted(((math.hypot(drains[r.tag][0][0] - point[0],
                               drains[r.tag][0][1] - point[1]), r.tag), r) for r in leaves)


@dataclass(frozen=True)
class WetVentData:
    """The model's drains read once for :func:`developed_arm` with wet vents graded.

    ``fx`` is ``grade_wet_vent``'s fixture table; ``vent_ends`` maps a fixture to the ends of
    the vents whose ``serves`` names it — the only vents the check walks for that fixture.
    """

    drains: dict[str, list[Point3]]
    radii: dict[str, float]
    fx: dict[str, Fx]
    vent_ends: dict[str, list[Point3]]
    all_vent_ends: list[Point3]


def wet_vent_data(model) -> WetVentData:
    """The check's and the router's one reading of the drains, vents and fixture loads."""
    from typehaus.resolve.fixture_units import fixture_units
    from typehaus.resolve.mep_sleeves import _expected_drain_point

    drains = {r.tag: pts for r in model.pipe_runs
              if r.system == "drain" and (pts := run_points(r)) is not None}
    radii = {r.tag: r.diameter_m / 2.0 for r in model.pipe_runs if r.tag in drains}
    units = {u.tag: u for u in fixture_units(model.plan)}
    vent_ends: dict[str, list[Point3]] = {}
    all_ends: list[Point3] = []
    for r in model.pipe_runs:
        if r.system == "vent" and (pts := run_points(r)):
            all_ends += [pts[0], pts[-1]]
            for tag in r.serves:
                vent_ends.setdefault(tag, []).extend((pts[0], pts[-1]))
    fx: dict[str, Fx] = {}
    for storey in model.plan.storeys:
        for f in model.plan.storey_elements(storey.tag):
            row, pt = units.get(f.tag), _expected_drain_point(model, f.tag)
            serv = [r for r in model.pipe_runs
                    if r.system == "drain" and f.tag in r.serves and r.tag in drains]
            if f.element_kind == "Fixture" and row and row.dfu and pt and serv:
                fx[f.tag] = (arm_leaves(serv, pt, drains, radii)[0][1].tag, row.dfu,
                             row.symbol, storey.tag)
    return WetVentData(drains, radii, fx, vent_ends, all_ends)


def whole_trap_arms(model, data: WetVentData | None = None) -> set[str]:
    """Drain runs that are wholly one fixture's trap arm: its leaf run, ending on one of its
    own vent tees. Table 703.2 note 1 leaves these out of branch capacity."""
    data = data or wet_vent_data(model)
    out = set()
    for tag, (leaf, *_rest) in data.fx.items():
        pts = data.drains.get(leaf)
        if pts and any(math.dist(pts[-1], e) <= TEE_TOL_M for e in data.vent_ends.get(tag, ())):
            out.add(leaf)
    return out


def arm_is_vented(model, fixture: str, drain_point,
                  data: WetVentData | None = None) -> tuple[bool, str]:
    """``(vented, what vents it)``: the check's own walk, wet vents graded under 908.

    A vent named in ``serves`` must also be reached within Table 1002.2; ``what`` is
    :func:`developed_arm`'s verdict ("a vent tee", or the wet vent and its 908 grade).
    """
    from typehaus.resolve.plumbing_tables import trap_arm_limit_in

    data = data or wet_vent_data(model)
    serving = [r for r in model.pipe_runs
               if r.system == "drain" and fixture in r.serves and r.tag in data.drains]
    ends = data.vent_ends.get(fixture, [])
    if drain_point is None or not serving or not ends:
        return False, ""
    starts = arm_leaves(serving, drain_point, data.drains, data.radii)
    if starts[0][0][0] > START_TOL_M:
        return False, ""
    run = starts[0][1]
    limit_in = trap_arm_limit_in(run.diameter_m)
    arm_m, what, _gap, _notes = developed_arm(run.tag, data.drains, data.radii, ends,
                                              (data.fx, fixture))
    ok = arm_m is not None and limit_in is not None and arm_m / M_PER_IN <= limit_in + 1e-6
    return ok, (f"{arm_m / M_PER_IN:.0f}\" to {what}" if ok else "")

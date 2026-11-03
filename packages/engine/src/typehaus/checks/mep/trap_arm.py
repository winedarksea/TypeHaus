"""``mep.trap_arm_developed`` — the developed trap arm, walked in 3D along the drain.

MN 4714 (UPC) 1002.2: the developed length from the trap to the vent, against Table 1002.2
(``takeoff.plumbing_calc.TRAP_ARM_MAX_IN``); for a water closet, from the closet flange.
``mep.trap_arm_length`` (``plumbing_dwv.py``) still measures a plan ``hypot`` from the drain
point to the nearest serving vent, which never asks whether the vent reaches the drain
(C6-E7). This check is its replacement, ADVISORY until every vent meets its drain in 3D:
switched before then it would put an UNKNOWN on the permit gate per unvented fixture.

**The vent must meet the drain.** A vent tee is a serving VENT run's endpoint on a drain
segment in 3D (within ``_TEE_TOL_M``). The walk starts at the fixture's most upstream serving
drain (a run no other serving drain ends on), follows it downstream into each parent where it
ends, and stops at the first tee — or at a WET VENT: another drain joining the path that
carries a serving vent tee of its own, if ``wet_vent.grade_wet_vent`` finds it legal under
UPC 908. A wet vent that fails is skipped and the walk goes on. Verticals count.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import passed as _pass
from typehaus.checks.mep.wet_vent import grade_wet_vent
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory
from typehaus.model.enums import Service
from typehaus.quantities import M_PER_IN

_CID = "mep.trap_arm_developed"
#: An inlet (vent end or child drain) meets a drain inside its bore plus this — an
#: upper-half entry is on the pipe, which ``mep.drain_tie_in`` grades on its own.
_TEE_TOL_M = 0.5 * M_PER_IN
#: The fixture's arm starts at a serving run's first vertex this close to its drain point.
_START_TOL_M = 12.0 * M_PER_IN

Point3 = tuple[float, float, float]


def _staged(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    """ADVISORY, not FAIL: the open vent work stays visible without gating (see above)."""
    return advisory(cid, msg, tags, Result.ADVISORY)


def _points(run) -> list[Point3] | None:
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


def _parent(end: Point3, own: str, drains: dict[str, list[Point3]],
            radii: dict[str, float]):
    """The drain run whose segment the child's last vertex stands on: (tag, index, t)."""
    best = None
    for tag, pts in drains.items():
        if tag == own:
            continue
        for i in range(len(pts) - 1):
            d, t = _project(end, pts[i], pts[i + 1])
            if d <= radii[tag] + _TEE_TOL_M and (best is None or d < best[0]):
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
              if any(_on_run(v, pts, radii[tag] + _TEE_TOL_M) for v in vent_ends)}
    parents = {tag: p for tag in drains if (p := _parent(drains[tag][-1], tag, drains, radii))}
    joins: dict[str, list[tuple[str, Point3]]] = {}
    for tag in vented:
        if tag in parents:
            joins.setdefault(parents[tag][0], []).append((tag, drains[tag][-1]))
    run, index, t0, walked, came = start_run, 0, 0.0, 0.0, None
    visited: set[str] = set()
    notes: list[str] = []
    while run not in visited:
        visited.add(run)
        pts, reach = drains[run], radii[run] + _TEE_TOL_M
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


def _leaves(serving: list, point, drains, radii) -> list:
    """Serving drains by distance from the fixture's drain point, most upstream only:
    ``[((dist, tag), run), ...]`` — a run no other serving drain ends on."""
    fed = {p[0] for r in serving
           if (p := _parent(drains[r.tag][-1], r.tag, drains, radii)) is not None}
    leaves = [r for r in serving if r.tag not in fed] or serving
    return sorted(((math.hypot(drains[r.tag][0][0] - point[0],
                               drains[r.tag][0][1] - point[1]), r.tag), r) for r in leaves)


@check(Tier.ADVISORY, _CID)
def trap_arm_developed(ctx: CheckContext) -> list[Finding]:
    """Developed trap arm from each fixture to its vent tee, against Table 1002.2."""
    from typehaus.resolve.mep_sleeves import _expected_drain_point
    from typehaus.takeoff.plumbing_calc import fixture_units, trap_arm_limit_in

    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    drains = {r.tag: pts for r in ctx.model.pipe_runs
              if r.system == "drain" and (pts := _points(r)) is not None}
    radii = {r.tag: r.diameter_m / 2.0 for r in ctx.model.pipe_runs if r.tag in drains}
    units = {u.tag: u for u in fixture_units(ctx.plan)}
    fx: dict[str, tuple] = {}  # tag -> (leaf drain run, DFU, symbol, storey) for wet_vent
    for storey in ctx.plan.storeys:
        for f in ctx.plan.storey_elements(storey.tag):
            row, pt = units.get(f.tag), _expected_drain_point(ctx.model, f.tag)
            serv = [r for r in ctx.model.pipe_runs
                    if r.system == "drain" and f.tag in r.serves and r.tag in drains]
            if f.element_kind == "Fixture" and row and row.dfu and pt and serv:
                fx[f.tag] = (_leaves(serv, pt, drains, radii)[0][1].tag, row.dfu, row.symbol,
                             storey.tag)
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for fixture in ctx.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or Service.DRAIN not in fixture_type.needs:
                continue
            tags = (fixture.tag,)
            point = _expected_drain_point(ctx.model, fixture.tag)
            serving = [r for r in ctx.model.pipe_runs
                       if r.system == "drain" and fixture.tag in r.serves and r.tag in drains]
            if point is None or not serving:
                out.append(_staged(_CID, f"fixture {fixture.tag} has no resolvable drain "
                                          "point or no drain run serving it", tags))
                continue
            starts = _leaves(serving, point, drains, radii)
            if starts[0][0][0] > _START_TOL_M:
                out.append(_staged(_CID, f"fixture {fixture.tag}: no serving drain starts "
                                          "at its drain point, so there is no arm to walk",
                                    tags))
                continue
            arm_run = starts[0][1]
            limit_in = trap_arm_limit_in(arm_run.diameter_m)
            size = f"Ø{arm_run.diameter_m / M_PER_IN:.2f}\""
            if limit_in is None:
                out.append(_staged(_CID, f"fixture {fixture.tag}'s trap arm {size} has no "
                                          "Table 1002.2 row", tags))
                continue
            vents = [r for r in ctx.model.pipe_runs
                     if r.system == "vent" and fixture.tag in r.serves]
            ends = [p for r in vents if (pts := _points(r)) for p in (pts[0], pts[-1])]
            arm_m, what, gap, notes = developed_arm(arm_run.tag, drains, radii, ends,
                                                    (fx, fixture.tag))
            if arm_m is None:
                why = (f"the nearest serving vent end is {gap / M_PER_IN:.1f}\" off any "
                       "drain" if ends else "no vent run serves it")
                if notes:
                    why = f"no true vent tee, and {'; '.join(notes)}"
                out.append(_staged(_CID, f"fixture {fixture.tag}: no vent meets its drain "
                                          f"in 3D downstream of the trap — {why}", tags))
                continue
            arm_in = arm_m / M_PER_IN
            skipped = f" [{'; '.join(notes)}]" if notes else ""
            said = (f"fixture {fixture.tag}'s trap arm develops {arm_in:.0f}\" from "
                    f"{arm_run.tag} to {what}, against Table 1002.2's {limit_in:.0f}\" for "
                    f"{size}{skipped}")
            out.append(_pass(_CID, said, tags) if arm_in <= limit_in + 1e-6
                       else _staged(_CID, said + " — over", tags))
    return out

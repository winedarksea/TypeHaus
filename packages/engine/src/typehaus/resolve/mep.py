"""MEP resolver: authored PipeRun/SleevePenetration/DuctRun -> validated IR
(→ Permit-ready Phases 2-3).

Authored routing only — this module never invents a run, sleeve, or duct position. It
sums pipe lengths/inverts, checks a sleeve's host slab and floor-opening clearance,
derives the expected drain-stack point a sleeve is measured against (the pre-pour
guarantee), and checks a duct run against its floor's joist bays/bearing lines.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import DuctRouting, Service
from typehaus.model.mep import ConduitRun, DuctRun, PipeRun, SleevePenetration
from typehaus.model.spatial import Appliance, Fixture
from typehaus.quantities import inch
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import (ResolvedConduitRun, ResolvedDuct, ResolvedModel,
                                    ResolvedPipeRun, ResolvedSleeve)

_JOIST_BREADTH_M = inch(1.5).meters
_DEFAULT_SPACING_M = inch(16).meters


def resolve_mep(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, PipeRun):
                findings.extend(_resolve_pipe_run(model, element, storey))
            elif isinstance(element, SleevePenetration):
                findings.extend(_resolve_sleeve(model, element, storey.tag))
            elif isinstance(element, DuctRun):
                findings.extend(_resolve_duct_run(model, element, storey.tag))
            elif isinstance(element, ConduitRun):
                findings.extend(_resolve_conduit_run(model, element, storey.tag))
    return findings


def _resolve_conduit_run(model: ResolvedModel, run: ConduitRun, storey_tag: str) -> list[Finding]:
    path = [p.xy_m for p in run.path]
    if len(path) < 2:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.conduit_run_path",
            message=f"conduit run {run.tag} needs >= 2 path points", element_tags=(run.tag,),
            result=Result.FAIL,
        )]
    plan_len = sum(length(sub(path[i], path[i + 1])) for i in range(len(path) - 1))
    # Elevations are authored project-frame absolute (trunks cross storeys, unlike pipe
    # inverts); the developed pull length includes the vertical rise at the run's end.
    z0 = run.start_elevation.meters if run.start_elevation is not None else None
    z1 = run.end_elevation.meters if run.end_elevation is not None else None
    rise = abs(z1 - z0) if z0 is not None and z1 is not None else 0.0
    model.conduits.append(ResolvedConduitRun(
        uid=run.uid, tag=run.tag, storey=storey_tag, path=path,
        trade_size_m=run.trade_size.meters, z_start_m=z0, z_end_m=z1,
        length_m=plan_len + rise, from_ref=run.from_ref, to_ref=run.to_ref,
    ))
    return []


def _resolve_pipe_run(model: ResolvedModel, run: PipeRun, storey) -> list[Finding]:
    path = [p.xy_m for p in run.path]
    if len(path) < 2:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.pipe_run_path",
            message=f"pipe run {run.tag} needs >= 2 path points", element_tags=(run.tag,),
            result=Result.FAIL,
        )]
    seg_len = sum(length(sub(path[i], path[i + 1])) for i in range(len(path) - 1))
    # Inverts are authored storey-relative; the resolved IR carries absolute project-frame
    # elevations like every other ResolvedModel z (ResolvedWall.z0_m/z1_m, etc).
    datum = storey.elevation.meters
    model.pipe_runs.append(ResolvedPipeRun(
        uid=run.uid, tag=run.tag, storey=storey.tag, system=run.system.value,
        path=path, diameter_m=run.diameter.meters,
        z_start_m=datum + run.start_elevation.meters if run.start_elevation is not None else None,
        z_end_m=datum + run.end_elevation.meters if run.end_elevation is not None else None,
        length_m=seg_len, serves=tuple(run.serves),
    ))
    return []


def _resolve_sleeve(model: ResolvedModel, sleeve: SleevePenetration,
                    storey_tag: str) -> list[Finding]:
    findings: list[Finding] = []
    host = next((s for s in model.solids if s.tag == sleeve.host_ref), None)
    if host is None or host.category != "slab":
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.sleeve_host",
            message=f"sleeve {sleeve.tag} references missing or non-slab host {sleeve.host_ref}",
            element_tags=(sleeve.tag,), result=Result.FAIL,
        )]

    from shapely.geometry import Point, Polygon

    center = sleeve.position.xy_m
    point = Point(center)
    if not Polygon(host.outline).contains(point):
        findings.append(Finding(
            severity=Severity.ERROR, check_id="integrity.sleeve_in_opening",
            message=f"sleeve {sleeve.tag} center falls outside its host slab {host.tag}",
            element_tags=(sleeve.tag, host.tag), result=Result.FAIL,
        ))
    slab = model.plan.by_tag(host.tag)
    for opening_tag in getattr(slab, "openings", ()):
        opening = model.plan.by_tag(opening_tag)
        if opening is None or len(opening.outline) < 3:
            continue
        if Polygon([p.xy_m for p in opening.outline]).contains(point):
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_in_opening",
                message=f"sleeve {sleeve.tag} falls inside floor opening {opening_tag}",
                element_tags=(sleeve.tag, opening_tag), result=Result.FAIL,
            ))

    expected = _expected_drain_point(model, sleeve.serves_fixture)
    offset = length(sub(center, expected)) if expected is not None else None
    model.sleeves.append(ResolvedSleeve(
        uid=sleeve.uid, tag=sleeve.tag, storey=storey_tag, host_slab=host.tag,
        center=center, pipe_d_m=sleeve.pipe_diameter.meters,
        sleeve_d_m=sleeve.sleeve_diameter.meters, z0_m=host.z0_m, z1_m=host.z1_m,
        serves_fixture=sleeve.serves_fixture, expected_center=expected, offset_m=offset,
    ))
    return findings


def _expected_drain_point(model: ResolvedModel,
                          fixture_tag: str | None) -> tuple[float, float] | None:
    """Decision 4: authored ``drain_position`` wins; else convention by fixture kind."""
    if fixture_tag is None:
        return None
    fixture = model.plan.by_tag(fixture_tag)
    if not isinstance(fixture, (Fixture, Appliance)):
        return None
    if fixture.drain_position is not None:
        return fixture.drain_position.xy_m
    fixture_type = next((t for t in (*model.plan.library.fixture_types,
                                     *model.plan.library.appliance_types)
                         if t.tag == fixture.type_ref), None)
    if fixture_type is None:
        return None
    # A water closet is the only common fixture with no hot-water connection — the one
    # reliable signal in this schema that a fixture is floor-drained (drain at its own
    # footprint) rather than wall-drained (trap arm back to a wet-wall stack).
    if Service.WATER_HOT not in fixture_type.needs:
        return fixture.position.xy_m
    if fixture.wall_ref is None:
        return None
    wall = model.wall(fixture.wall_ref)
    if wall is None:
        return None
    return _project_onto_line(fixture.position.xy_m, wall.axis)


def _project_onto_line(
    point: tuple[float, float], axis: tuple[tuple[float, float], tuple[float, float]]
) -> tuple[float, float]:
    (x0, y0), (x1, y1) = axis
    dx, dy = x1 - x0, y1 - y0
    denom = dx * dx + dy * dy
    if denom < 1e-12:
        return (x0, y0)
    t = ((point[0] - x0) * dx + (point[1] - y0) * dy) / denom
    return (x0 + t * dx, y0 + t * dy)


def _resolve_duct_run(model: ResolvedModel, duct: DuctRun, storey_tag: str) -> list[Finding]:
    path = [p.xy_m for p in duct.path]
    if len(path) < 2:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.duct_run_path",
            message=f"duct run {duct.tag} needs >= 2 path points", element_tags=(duct.tag,),
            result=Result.FAIL,
        )]
    width_m, depth_m = duct.width.meters, duct.depth.meters
    floor = (next((f for f in model.floors if f.tag == duct.floor_ref), None)
            if duct.floor_ref else None)
    conflicts: tuple[str, ...] = ()
    crossings: tuple[tuple[float, float], ...] = ()
    depth_ok = True
    if floor is not None:
        system = model.plan.by_tag(floor.tag)
        bearing_walls = [model.wall(tag) for tag in getattr(system.joists, "bearing_refs", ())]
        bearing_walls = [w for w in bearing_walls if w is not None]
        spacing_m = (system.joists.spacing.meters if system.joists.spacing is not None
                    else _DEFAULT_SPACING_M)
        conflict_list, crossing_list, depth_ok = duct_bay_occupancy(
            path, width_m, depth_m, duct.routing, floor, bearing_walls, spacing_m,
        )
        conflicts, crossings = tuple(conflict_list), tuple(crossing_list)
    model.ducts.append(ResolvedDuct(
        uid=duct.uid, tag=duct.tag, storey=storey_tag, system=duct.system.value,
        path=path, width_m=width_m, depth_m=depth_m, routing=duct.routing.value,
        floor_ref=duct.floor_ref, crossings=crossings, conflicts=conflicts, depth_ok=depth_ok,
    ))
    return []


def is_parallel_to_floor(path: list[tuple[float, float]], floor) -> bool:
    """Whether every segment of ``path`` runs parallel to the floor's joist axis."""
    along_x = floor.direction == "x"
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        perp_a = a[1] if along_x else a[0]
        perp_b = b[1] if along_x else b[0]
        if abs(perp_a - perp_b) >= 1e-6:
            return False
    return True


def duct_bay_occupancy(path: list[tuple[float, float]], width_m: float, depth_m: float,
                       routing: DuctRouting, floor, bearing_walls: list,
                       spacing_m: float) -> tuple[list[str], list[tuple[float, float]], bool]:
    """Validate a duct path against one floor's joist bays and bearing lines.

    Returns ``(conflicts, crossings, depth_ok)``. Conflicts are structural FAILs (a
    parallel segment straddling a joist line, too wide for the clear bay, or a
    perpendicular/oblique segment crossing joist lines outside SOFFIT/CHASE routing).
    Bearing-line crossings are always legal (the resolver lays identical perp positions
    on both sides of a bearing line) — they become a drawing note, never a conflict.
    """
    along_x = floor.direction == "x"
    joist_lines = sorted({(m.p0[1] if along_x else m.p0[0]) for m in floor.members})
    member_depth = max((m.z1_m - m.z0_m for m in floor.members), default=depth_m)
    depth_ok = depth_m <= member_depth + 1e-9

    conflicts: list[str] = []
    crossings: list[tuple[float, float]] = []
    clear_width_m = spacing_m - _JOIST_BREADTH_M
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        pa, pb = (a[1], b[1]) if along_x else (a[0], b[0])
        aa, ab = (a[0], b[0]) if along_x else (a[1], b[1])
        if abs(pa - pb) < 1e-6:
            c = pa
            lo, hi = c - width_m / 2, c + width_m / 2
            straddled = [jl for jl in joist_lines if lo + 1e-6 < jl < hi - 1e-6]
            if straddled:
                conflicts.append(
                    f"segment {i} centered at {c:.3f}m crosses joist line(s) at "
                    f"{[round(v, 3) for v in straddled]}"
                )
            if width_m > clear_width_m + 1e-9:
                conflicts.append(
                    f"segment {i} width {width_m:.3f}m exceeds the {clear_width_m:.3f}m "
                    f"clear bay at {spacing_m * 39.37007874015748:.0f}\" o.c."
                )
        else:
            crossed = [jl for jl in joist_lines if min(pa, pb) < jl < max(pa, pb)]
            if crossed and routing not in (DuctRouting.SOFFIT, DuctRouting.CHASE):
                conflicts.append(
                    f"segment {i} runs perpendicular/oblique across joist line(s) "
                    f"{[round(v, 3) for v in crossed]} — route in a soffit or chase"
                )
        for wall in bearing_walls:
            (wx0, wy0), (wx1, wy1) = wall.axis
            wc = ((wx0 + wx1) / 2) if along_x else ((wy0 + wy1) / 2)
            if min(aa, ab) - 1e-6 <= wc <= max(aa, ab) + 1e-6:
                t = 0.0 if abs(ab - aa) < 1e-12 else (wc - aa) / (ab - aa)
                perp_at = pa + t * (pb - pa)
                crossings.append((wc, perp_at) if along_x else (perp_at, wc))
    return conflicts, crossings, depth_ok

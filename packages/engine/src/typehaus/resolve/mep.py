"""MEP resolver: authored PipeRun/SleevePenetration/DuctRun -> validated IR
(→ Permit-ready Phases 2-3).

Authored routing only — this module never invents a run, sleeve, or duct position. It
sums pipe lengths/inverts, checks a sleeve's host slab and floor-opening clearance,
derives the expected drain-stack point a sleeve is measured against (the pre-pour
guarantee), and checks a duct run against its floor's joist bays/bearing lines.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import DuctRouting, LuminaireForm, Service
from typehaus.model.mep import ConduitRun, DuctRun, LightRun, PipeRun, SleevePenetration
from typehaus.model.spatial import Appliance, Fixture
from typehaus.quantities import inch
from typehaus.resolve.geometry import circle_outline, length, sub
from typehaus.resolve.round_solids import PIPE_FACETS, sloped_run_bands
from typehaus.resolve.model import (ResolvedConduitRun, ResolvedDuct, ResolvedLightRun,
                                    ResolvedModel, ResolvedPipeRun, ResolvedSleeve)
from typehaus.resolve.placeables import resolved_mount_elevation

_JOIST_BREADTH_M = inch(1.5).meters
_DEFAULT_SPACING_M = inch(16).meters


def resolve_mep(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    # Pipes resolve first, model-wide: a sleeve's expected center prefers a routed pipe
    # vertex over the fixture-projection heuristic, so every run must exist before any
    # sleeve is measured against one.
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, PipeRun):
                findings.extend(_resolve_pipe_run(model, element, storey))
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, SleevePenetration):
                findings.extend(_resolve_sleeve(model, element, storey.tag))
            elif isinstance(element, DuctRun):
                findings.extend(_resolve_duct_run(model, element, storey.tag))
            elif isinstance(element, ConduitRun):
                findings.extend(_resolve_conduit_run(model, element, storey.tag))
            elif isinstance(element, LightRun):
                findings.extend(_resolve_light_run(model, element, storey))
    return findings


def _resolve_light_run(model: ResolvedModel, run: LightRun, storey) -> list[Finding]:
    """Validate a linear-luminaire run and record its plan length at its mounted height.

    Two integrity gates, both hard: a polyline needs two points to have a length, and the
    named type must be a ``LuminaireType`` of a linear form — a run pointing at a can
    light would otherwise silently price per-foot off a per-fixture wattage.
    """
    path = [p.xy_m for p in run.path]
    if len(path) < 2:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.light_run_path",
            message=f"light run {run.tag} needs >= 2 path points", element_tags=(run.tag,),
            result=Result.FAIL,
        )]
    product = next((t for t in model.plan.library.electrical_device_types
                    if t.tag == run.type_ref), None)
    form = getattr(product, "form", None)
    if product is None or form is None:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.light_run_type",
            message=f"light run {run.tag} references {run.type_ref}, which is not a "
                    f"LuminaireType in Library.electrical_device_types",
            element_tags=(run.tag,), result=Result.FAIL,
        )]
    if form is not LuminaireForm.STRIP:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.light_run_type",
            message=f"light run {run.tag} references {run.type_ref} of form "
                    f"{form.value} — a run needs a STRIP-form luminaire type",
            element_tags=(run.tag,), result=Result.FAIL,
        )]
    plan_len = sum(length(sub(path[i], path[i + 1])) for i in range(len(path) - 1))
    model.light_runs.append(ResolvedLightRun(
        uid=run.uid, tag=run.tag, storey=storey.tag, path=path,
        z_m=resolved_mount_elevation(storey, run), length_m=plan_len,
        type_ref=run.type_ref, circuit=run.circuit, psu_ref=run.psu_ref,
        controlled_by=tuple(run.controlled_by), room=run.room,
    ))
    return []


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


def _pipe_vertex_z(run: PipeRun, path: list[tuple[float, float]],
                   datum: float) -> tuple[list[float] | None, list[Finding]]:
    """Absolute project-frame invert per path vertex.

    Authored ``elevations`` win; otherwise interpolate linearly between
    ``start_elevation``/``end_elevation`` over developed plan length — exactly the old
    two-invert behaviour, so legacy runs resolve unchanged. Both absent → None (no
    vertical information at all, matching the old None/None endpoints)."""
    if run.elevations is not None:
        if len(run.elevations) != len(path):
            return None, [Finding(
                severity=Severity.ERROR, check_id="integrity.pipe_run_elevations",
                message=(f"pipe run {run.tag} authors {len(run.elevations)} elevations "
                         f"for {len(path)} path points — one invert per vertex"),
                element_tags=(run.tag,), result=Result.FAIL)]
        z = [datum + e.meters for e in run.elevations]
        for label, authored in (("start", run.start_elevation), ("end", run.end_elevation)):
            if authored is None:
                continue
            expected = z[0] if label == "start" else z[-1]
            if abs(datum + authored.meters - expected) > 1e-6:
                return None, [Finding(
                    severity=Severity.ERROR, check_id="integrity.pipe_run_elevations",
                    message=(f"pipe run {run.tag} {label}_elevation disagrees with "
                             f"elevations[{0 if label == 'start' else -1}]"),
                    element_tags=(run.tag,), result=Result.FAIL)]
        return z, []
    if run.start_elevation is None and run.end_elevation is None:
        return None, []
    z0 = datum + (run.start_elevation or run.end_elevation).meters
    z1 = datum + (run.end_elevation or run.start_elevation).meters
    plan_cum = [0.0]
    for i in range(len(path) - 1):
        plan_cum.append(plan_cum[-1] + length(sub(path[i], path[i + 1])))
    total = plan_cum[-1] or 1.0
    return [z0 + (z1 - z0) * (c / total) for c in plan_cum], []


def _pipe_wall_refs(run: PipeRun, n_segments: int) -> tuple[tuple[str | None, ...],
                                                            list[Finding]]:
    """Per-segment host wall tags, expanding the single-wall ``wall_ref`` sugar."""
    if run.wall_refs is not None:
        if len(run.wall_refs) != n_segments:
            return (), [Finding(
                severity=Severity.ERROR, check_id="integrity.pipe_run_wall_refs",
                message=(f"pipe run {run.tag} authors {len(run.wall_refs)} wall_refs "
                         f"for {n_segments} segments — one host (or None) per segment"),
                element_tags=(run.tag,), result=Result.FAIL)]
        return tuple(run.wall_refs), []
    if run.wall_ref is not None:
        return tuple([run.wall_ref] * n_segments), []
    return (), []


def _emit_pipe_solids(model: ResolvedModel, run_uid: str, run_tag: str, storey_tag: str,
                      path: list[tuple[float, float]], z: list[float],
                      radius: float, system: str) -> None:
    """Viewer/IFC solids for a routed run: vertical drops as faceted circle prisms,
    horizontal/sloped segments as chord-band stacks (→ resolve/round_solids.py).
    Category is per-system (``pipe_drain``, ``pipe_water_hot``, …) so the viewer and
    the glTF export color-code trades the way a riser diagram does."""
    from typehaus.resolve.model import ResolvedSolid

    category = f"pipe_{system}"
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        za, zb = z[i], z[i + 1]
        if length(sub(a, b)) < 1e-6:
            if abs(zb - za) < 1e-9:
                continue  # degenerate zero-length segment
            model.solids.append(ResolvedSolid(
                uid=f"{run_uid}-s{i:02d}", tag=f"{run_tag}-S{i + 1}", storey=storey_tag,
                category=category, outline=circle_outline(a, radius, PIPE_FACETS),
                z0_m=min(za, zb), z1_m=max(za, zb)))
            continue
        for band, (outline, z0, z1) in enumerate(sloped_run_bands(a, b, radius, za, zb)):
            model.solids.append(ResolvedSolid(
                uid=f"{run_uid}-s{i:02d}b{band:02d}", tag=f"{run_tag}-S{i + 1}B{band + 1}",
                storey=storey_tag, category=category, outline=outline, z0_m=z0, z1_m=z1))


def _resolve_pipe_run(model: ResolvedModel, run: PipeRun, storey) -> list[Finding]:
    path = [p.xy_m for p in run.path]
    if len(path) < 2:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.pipe_run_path",
            message=f"pipe run {run.tag} needs >= 2 path points", element_tags=(run.tag,),
            result=Result.FAIL,
        )]
    # Inverts are authored storey-relative; the resolved IR carries absolute project-frame
    # elevations like every other ResolvedModel z (ResolvedWall.z0_m/z1_m, etc).
    datum = storey.elevation.meters
    z, findings = _pipe_vertex_z(run, path, datum)
    wall_refs, ref_findings = _pipe_wall_refs(run, len(path) - 1)
    findings.extend(ref_findings)
    if any(f.result is Result.FAIL for f in findings):
        return findings
    plan_len = sum(length(sub(path[i], path[i + 1])) for i in range(len(path) - 1))
    if z is not None:
        developed = sum(
            math.hypot(length(sub(path[i], path[i + 1])), z[i + 1] - z[i])
            for i in range(len(path) - 1))
        _emit_pipe_solids(model, run.uid or run.tag, run.tag, storey.tag, path, z,
                          run.diameter.meters / 2.0, run.system.value)
    else:
        developed = plan_len
    model.pipe_runs.append(ResolvedPipeRun(
        uid=run.uid, tag=run.tag, storey=storey.tag, system=run.system.value,
        path=path, diameter_m=run.diameter.meters,
        z_start_m=z[0] if z is not None else None,
        z_end_m=z[-1] if z is not None else None,
        length_m=developed, serves=tuple(run.serves),
        z_m=tuple(z) if z is not None else None,
        wall_refs=wall_refs, material=run.material,
    ))
    return findings


_CONCRETE_SOLID_CATEGORIES = ("slab", "footing")


def _sleeve_host(model: ResolvedModel, host_ref: str):
    """A sleeve's concrete host: (footprint, z0, z1, category, tag) or None.

    A slab or footing is a ResolvedSolid; a foundation/concrete wall is a ResolvedWall
    whose structure layer supplies the footprint."""
    solid = next((s for s in model.solids
                  if s.tag == host_ref and s.category in _CONCRETE_SOLID_CATEGORIES), None)
    if solid is not None:
        return solid.outline, solid.z0_m, solid.z1_m, solid.category, solid.tag
    wall = model.wall(host_ref)
    if wall is not None:
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        outline = structure.polygon if structure is not None else ()
        if len(outline) >= 3:
            return outline, wall.z0_m, wall.z1_m, "wall", wall.tag
    return None


def _resolve_sleeve(model: ResolvedModel, sleeve: SleevePenetration,
                    storey_tag: str) -> list[Finding]:
    findings: list[Finding] = []
    host = _sleeve_host(model, sleeve.host_ref)
    if host is None:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.sleeve_host",
            message=(f"sleeve {sleeve.tag} references {sleeve.host_ref}, which is no "
                     "slab, footing, or concrete wall"),
            element_tags=(sleeve.tag,), result=Result.FAIL,
        )]
    outline, z0, z1, category, host_tag = host

    from shapely.geometry import Point, Polygon

    center = sleeve.position.xy_m
    point = Point(center)
    if not Polygon(outline).buffer(1e-6).contains(point):
        findings.append(Finding(
            severity=Severity.ERROR, check_id="integrity.sleeve_in_opening",
            message=f"sleeve {sleeve.tag} center falls outside its host {host_tag}",
            element_tags=(sleeve.tag, host_tag), result=Result.FAIL,
        ))
    if sleeve.axis == "horizontal":
        cz = sleeve.center_elevation.meters if sleeve.center_elevation is not None else None
        if cz is None:
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_host",
                message=f"horizontal sleeve {sleeve.tag} authors no center_elevation",
                element_tags=(sleeve.tag,), result=Result.FAIL))
        elif category == "footing" and cz < z0 - 1e-6:
            # An under-footing protection sleeve (IRC P2604): the pipe passes below the
            # bearing plane inside a sleeve/relieving arch, so the centerline is legal
            # below the footing's own extent. mep.footing_clearance requires it.
            pass
        elif not (z0 - 1e-6 <= cz <= z1 + 1e-6):
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_host",
                message=(f"horizontal sleeve {sleeve.tag} centerline {cz:.3f}m falls "
                         f"outside host {host_tag} extent {z0:.3f}–{z1:.3f}m"),
                element_tags=(sleeve.tag, host_tag), result=Result.FAIL))
    host_element = model.plan.by_tag(host_tag)
    for opening_tag in getattr(host_element, "openings", ()):
        opening = model.plan.by_tag(opening_tag)
        if opening is None or len(opening.outline) < 3:
            continue
        if Polygon([p.xy_m for p in opening.outline]).contains(point):
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.sleeve_in_opening",
                message=f"sleeve {sleeve.tag} falls inside floor opening {opening_tag}",
                element_tags=(sleeve.tag, opening_tag), result=Result.FAIL,
            ))

    expected = _expected_sleeve_point(model, sleeve)
    offset = length(sub(center, expected)) if expected is not None else None
    model.sleeves.append(ResolvedSleeve(
        uid=sleeve.uid, tag=sleeve.tag, storey=storey_tag, host_slab=host_tag,
        center=center, pipe_d_m=sleeve.pipe_diameter.meters,
        sleeve_d_m=sleeve.sleeve_diameter.meters, z0_m=z0, z1_m=z1,
        serves_fixture=sleeve.serves_fixture, expected_center=expected, offset_m=offset,
        axis=sleeve.axis, host_category=category,
        center_z_m=(sleeve.center_elevation.meters
                    if sleeve.center_elevation is not None else None),
        purpose=sleeve.purpose.value,
    ))
    return findings


def _expected_sleeve_point(model: ResolvedModel,
                           sleeve: SleevePenetration) -> tuple[float, float] | None:
    """Where the sleeve should be, in a fixed precedence — three sources, most explicit
    first, so the answer never depends on what happens to be authored elsewhere:

    1. the fixture's authored ``drain_position`` (Decision 4) — a human saying *this* is
       where the waste leaves the fixture;
    2. the nearest vertex of a routed run serving that fixture — real geometry, but the
       resolver's reading of it;
    3. the fixture-convention projection — the old heuristic, a guess by fixture kind.

    Authored beats routed deliberately. If a ``drain_position`` and the routed run
    disagree, that disagreement is the defect, and ``mep.sleeve_alignment`` should say so;
    letting the run silently override the override is how a stale flange position hides
    (which is exactly what happened to SP-M-WC2 before its re-point).
    """
    authored = _authored_drain_point(model, sleeve.serves_fixture)
    if authored is not None:
        return authored
    pipe_point = _pipe_expected_point(model, sleeve)
    if pipe_point is not None:
        return pipe_point
    return _expected_drain_point(model, sleeve.serves_fixture)


_PIPE_SLEEVE_SNAP_M = 0.3  # a routed vertex within a foot of the sleeve claims it


def _pipe_expected_point(model: ResolvedModel,
                         sleeve: SleevePenetration) -> tuple[float, float] | None:
    """The nearest vertex of a routed run that *serves the sleeve's fixture*.

    The serves link is required, not just proximity — a collector bend passing near an
    unrelated sleeve must never claim its expectation. Runs that serve nothing (or a
    sleeve serving no fixture) fall through to the fixture-convention heuristic."""
    if sleeve.serves_fixture is None:
        return None
    center = sleeve.position.xy_m
    want_drain = sleeve.purpose == Service.DRAIN
    best: tuple[float, tuple[float, float]] | None = None
    for run in model.pipe_runs:
        if sleeve.serves_fixture not in run.serves:
            continue
        if want_drain != (run.system == "drain"):
            continue
        for vertex in run.path:
            d = length(sub(vertex, center))
            if d <= _PIPE_SLEEVE_SNAP_M and (best is None or d < best[0]):
                best = (d, vertex)
    return best[1] if best is not None else None


def _authored_drain_point(model: ResolvedModel,
                          fixture_tag: str | None) -> tuple[float, float] | None:
    """Just the authored override, with no fallback — the top of the precedence chain in
    `_expected_sleeve_point`, split out so "authored" can be distinguished from "derived"."""
    if fixture_tag is None:
        return None
    fixture = model.plan.by_tag(fixture_tag)
    if not isinstance(fixture, (Fixture, Appliance)):
        return None
    return fixture.drain_position.xy_m if fixture.drain_position is not None else None


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
        design_cfm=duct.design_cfm,
    ))
    return []


# --------------------------------------------------------------------------------------
# Shared derivations: imported by both checks (mep.wet_wall_occupancy, mep.sleeve_coverage)
# and the plumbing takeoff, so the reader and the finding can never disagree
# (same invariant as takeoff/hvac.py heating_zones ↔ checks/mep/hvac.py).

_PIPE_CAVITY_CLEARANCE_M = inch(0.25).meters  # boring/annular allowance inside a stud bay
_STUD_BAY_TRAVEL_M = inch(16).meters  # one standard bay: horizontal in-wall travel note


def wet_wall_occupancy(run: ResolvedPipeRun, model: ResolvedModel) -> list[dict]:
    """Validate every in-wall segment of a routed run against its declared host wall.

    Returns plain-dict problems (kind, segment, wall, message) — the check turns them
    into findings, the takeoff lists them. Kinds: ``missing_wall`` (ref resolves to no
    wall), ``outside_wall`` (segment escapes the structure footprint), ``too_shallow``
    (cavity cannot take the pipe), ``long_horizontal`` (advisory: horizontal in-wall
    travel beyond one stud bay in a single-layout wall — a staggered wall's continuous
    cavity is exempt, that is its point)."""
    from shapely.geometry import LineString, Point, Polygon

    problems: list[dict] = []
    if not run.wall_refs:
        return problems
    for i in range(len(run.path) - 1):
        wall_tag = run.wall_refs[i] if i < len(run.wall_refs) else None
        if wall_tag is None:
            continue
        seg = (run.path[i], run.path[i + 1])
        wall = model.wall(wall_tag)
        if wall is None:
            problems.append(dict(
                kind="missing_wall", segment=i, wall=wall_tag,
                message=f"{run.tag} segment {i} names missing wall {wall_tag}"))
            continue
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        if structure is None or len(structure.polygon) < 3:
            problems.append(dict(
                kind="outside_wall", segment=i, wall=wall_tag,
                message=f"{run.tag} segment {i}: wall {wall_tag} has no structure layer"))
            continue
        radius = run.diameter_m / 2.0
        footprint = Polygon(structure.polygon)
        vertical = length(sub(seg[0], seg[1])) < 1e-6
        shape = (Point(seg[0]) if vertical else LineString(seg)).buffer(radius)
        if not footprint.buffer(1e-4).contains(shape):
            problems.append(dict(
                kind="outside_wall", segment=i, wall=wall_tag,
                message=(f"{run.tag} segment {i} (Ø{run.diameter_m / 0.0254:.1f}\") leaves "
                         f"the structure footprint of {wall_tag}")))
        cavity = structure.thickness_m - _PIPE_CAVITY_CLEARANCE_M
        if run.diameter_m > cavity + 1e-9:
            problems.append(dict(
                kind="too_shallow", segment=i, wall=wall_tag,
                message=(f"{run.tag} segment {i} Ø{run.diameter_m / 0.0254:.1f}\" exceeds "
                         f"{wall_tag}'s {structure.thickness_m / 0.0254:.1f}\" cavity "
                         f"less {_PIPE_CAVITY_CLEARANCE_M / 0.0254:.2f}\" clearance")))
        if vertical:
            if run.z_m is not None:
                lo, hi = sorted((run.z_m[i], run.z_m[i + 1]))
                if lo < wall.z0_m - 1e-6 or hi > wall.z1_m + 1e-6:
                    problems.append(dict(
                        kind="outside_wall", segment=i, wall=wall_tag,
                        message=(f"{run.tag} segment {i} drop {lo:.2f}–{hi:.2f}m exceeds "
                                 f"{wall_tag}'s extent {wall.z0_m:.2f}–{wall.z1_m:.2f}m")))
        else:
            layout = _wall_layout(model, wall)
            travel = length(sub(seg[0], seg[1]))
            if layout != "staggered" and travel > _STUD_BAY_TRAVEL_M + 1e-9:
                problems.append(dict(
                    kind="long_horizontal", segment=i, wall=wall_tag,
                    message=(f"{run.tag} segment {i} runs {travel / 0.3048:.1f}' "
                             f"horizontally inside single-layout wall {wall_tag} — "
                             "every stud on the way gets bored")))
    return problems


def _wall_layout(model: ResolvedModel, wall) -> str:
    """The wall's partition layout ("single" | "staggered" | "double") off its assembly."""
    assembly = model.plan.library.assembly(wall.assembly)
    if assembly is None:
        return "single"
    for layer in assembly.layers:
        spec = getattr(layer, "framing", None)
        if spec is not None and getattr(spec, "layout", None) is not None:
            return spec.layout.value
    return "single"


def concrete_crossings(model: ResolvedModel) -> list[dict]:
    """Every point where a routed pipe passes through concrete — the pour-day list.

    Walks each resolved run with vertical information against every concrete solid
    (slab/footing) and foundation wall. Returns plain dicts: run, host, host_category,
    point (plan), z_m, matched sleeve tag or None. A run with no z information cannot be
    walked and is skipped — the check reports those runs as UNKNOWN, never silently."""
    from shapely.geometry import LineString, Point, Polygon

    hosts = [(s.tag, s.category, Polygon(s.outline), s.z0_m, s.z1_m)
             for s in model.solids
             if s.category in _CONCRETE_SOLID_CATEGORIES and len(s.outline) >= 3]
    for wall in model.walls:
        if not wall.is_foundation:
            continue
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        if structure is not None and len(structure.polygon) >= 3:
            hosts.append((wall.tag, "wall", Polygon(structure.polygon),
                          wall.z0_m, wall.z1_m))

    crossings: list[dict] = []
    for run in model.pipe_runs:
        if run.z_m is None:
            continue
        for i in range(len(run.path) - 1):
            a, b = run.path[i], run.path[i + 1]
            za, zb = run.z_m[i], run.z_m[i + 1]
            for host_tag, category, footprint, hz0, hz1 in hosts:
                hit = _segment_concrete_hit(a, b, za, zb, footprint, hz0, hz1,
                                            LineString, Point)
                if hit is None:
                    continue
                point, z_at = hit
                sleeve = _matching_sleeve(model, host_tag, point, z_at)
                crossings.append(dict(
                    run=run.tag, system=run.system, diameter_m=run.diameter_m,
                    host=host_tag, host_category=category, point=point, z_m=z_at,
                    sleeve=sleeve))
    return crossings


def _segment_concrete_hit(a, b, za, zb, footprint, hz0, hz1, LineString, Point):
    """Where (if anywhere) segment a→b at inverts za→zb passes through the host band."""
    plan_len = length(sub(a, b))
    lo, hi = sorted((za, zb))
    if hi < hz0 - 1e-6 or lo > hz1 + 1e-6:
        return None  # z ranges never meet
    if plan_len < 1e-6:
        # Vertical drop: crossing iff the drop spans the band and the point is inside.
        if lo <= hz0 + 1e-6 and hi >= hz1 - 1e-6 and footprint.buffer(1e-6).contains(Point(a)):
            return a, (hz0 + hz1) / 2.0
        return None
    # Sloped/horizontal: find where the invert crosses the band's mid-plane; a segment
    # running entirely inside the band (embedded in the pour) also counts at its midpoint
    # if the plan line enters the footprint.
    mid = (hz0 + hz1) / 2.0
    if abs(zb - za) > 1e-9 and min(za, zb) - 1e-6 <= mid <= max(za, zb) + 1e-6:
        t = (mid - za) / (zb - za)
        point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if footprint.buffer(1e-6).contains(Point(point)):
            return point, mid
        return None
    if lo >= hz0 - 1e-6 and hi <= hz1 + 1e-6:
        line = LineString((a, b))
        if line.intersects(footprint):
            inter = line.intersection(footprint)
            # Grazing a face is not a crossing: a run laid tight against a wall touches
            # its boundary with (near-)zero embedded length and casts no sleeve.
            if getattr(inter, "length", 0.0) < 0.02:
                return None
            c = inter.centroid
            if not c.is_empty:
                # Invert *at the crossing*, not the segment mean — a sloped drain's
                # invert at the wall is what the cast sleeve is set to.
                t = line.project(c) / max(line.length, 1e-9)
                return (c.x, c.y), za + t * (zb - za)
    return None


_SLEEVE_MATCH_TOL_M = 0.1  # a cast-in sleeve within 4" of the crossing claims it


def _matching_sleeve(model: ResolvedModel, host_tag: str, point: tuple[float, float],
                     z_at: float) -> str | None:
    best: tuple[float, str] | None = None
    for sleeve in model.sleeves:
        if sleeve.host_slab != host_tag:
            continue
        d = length(sub(sleeve.center, point))
        if d <= _SLEEVE_MATCH_TOL_M and (best is None or d < best[0]):
            best = (d, sleeve.tag)
    return best[1] if best is not None else None


def on_pipe_segment(point: tuple[float, float], start: tuple[float, float],
                    end: tuple[float, float], tol: float = 1e-6) -> bool:
    """True when ``point`` lies on the plan segment ``start``–``end`` (endpoints included)."""
    (px, py), (ax, ay), (bx, by) = point, start, end
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > tol:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    length_sq = (bx - ax) ** 2 + (by - ay) ** 2
    return -tol <= dot <= length_sq + tol


def pipe_invert_at(run, point: tuple[float, float], tol: float = 1e-6) -> float | None:
    """The run's invert where ``point`` sits on its plan path, or None if it doesn't.

    Takes the *deepest* match, not the first: a run's plan path can visit one point twice
    at two elevations (PR-B-MAIN-DRAIN passes (3', 15'-6") at the ceiling where the
    collector turns and again 9'-8" lower where the drop through the slab lands). The
    deeper leg is the one a buried branch actually ties into.
    """
    if run.z_m is None:
        return None
    candidates = []
    for index in range(len(run.path) - 1):
        start, end = run.path[index], run.path[index + 1]
        if not on_pipe_segment(point, start, end, tol):
            continue
        seg_len = length(sub(end, start))
        if seg_len <= tol:
            continue
        travelled = length(sub(point, start))
        fraction = travelled / seg_len
        candidates.append(run.z_m[index]
                          + (run.z_m[index + 1] - run.z_m[index]) * fraction)
    return min(candidates) if candidates else None


# Arrival may read slightly below the receiving invert at the matched vertex: authored
# inverts interpolate along whole segments, while the physical wye sits a little way
# downstream of a corner (catlin's kitchen branch arrives 0.43" under the main's invert
# at the (6', 16'-6") turn). One inch of slack keeps the *load* graph connected — grading
# slope/backflow is drain_slope's job, not the rollup's; a missed tie-in here silently
# under-sizes the pipe downstream, which is the worse failure.
_TIE_IN_INVERT_TOL_M = 0.0254


def drain_tie_ins(pipe_runs) -> dict[str, str]:
    """Child drain run tag → the drain run it discharges into, derived geometrically.

    ``PipeRun`` carries no upstream/downstream refs, so the connection is the geometry
    itself: a run ties into another when its *last* path vertex lies on a segment of the
    other's path and arrives at or above the other's invert there (a branch below the
    main it joins would not flow — the resolver-level gravity test pins the same
    relation). Runs without elevation data can't be judged and never tie in.

    A run never receives at its own terminal vertex: that point is where *it*
    discharges, so several branches all ending on one junction are siblings meeting at
    a wye on whatever continues downstream, not each other's parents (this is also what
    keeps the derivation acyclic on real junctions).
    """
    drains = [r for r in pipe_runs if r.system == "drain"]
    out: dict[str, str] = {}
    for child in drains:
        if child.z_m is None or not child.path:
            continue
        end_point, end_invert = child.path[-1], child.z_m[-1]
        best: tuple[float, str] | None = None
        for parent in drains:
            if parent.tag == child.tag or not parent.path:
                continue
            if length(sub(end_point, parent.path[-1])) <= 1e-6:
                continue  # the parent terminates here too — a sibling, not a receiver
            invert = pipe_invert_at(parent, end_point)
            if invert is None or end_invert < invert - _TIE_IN_INVERT_TOL_M:
                continue
            # Of several runs passing under the arrival point, the receiving pipe is
            # the one whose invert sits closest beneath the arrival.
            if best is None or invert > best[0]:
                best = (invert, parent.tag)
        if best is not None:
            out[child.tag] = best[1]
    return out


def accumulated_serves(pipe_runs) -> dict[str, tuple[str, ...]]:
    """Per drain run: the union of ``serves`` tags over its whole upstream subtree.

    Fixture tags are re-listed across runs by authoring convention (a fixture may appear
    on both its branch and the main), so the accumulation is a *union keyed by fixture
    tag* — summing per-branch loads would double-count. The result feeds
    ``branch_load``, which keeps its UNKNOWN-not-partial contract: one untabulated tag
    anywhere upstream makes the downstream run's load unknowable.
    """
    drains = [r for r in pipe_runs if r.system == "drain"]
    tie_ins = drain_tie_ins(drains)
    children: dict[str, list[str]] = {}
    for child_tag, parent_tag in tie_ins.items():
        children.setdefault(parent_tag, []).append(child_tag)
    by_tag = {r.tag: r for r in drains}

    def collect(tag: str, seen: set) -> set:
        if tag in seen:  # cycle guard: mutual geometric matches must not recurse forever
            return set()
        seen.add(tag)
        tags = set(by_tag[tag].serves)
        for child in children.get(tag, ()):
            tags |= collect(child, seen)
        return tags

    return {run.tag: tuple(sorted(collect(run.tag, set()))) for run in drains}


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

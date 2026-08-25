"""MEP resolver: authored PipeRun/SleevePenetration/DuctRun -> validated IR
(→ Permit-ready Phases 2-3).

Authored routing only — this module never invents a run, sleeve, or duct position. It
sums pipe lengths/inverts, checks a sleeve's host slab and floor-opening clearance,
derives the expected drain-stack point a sleeve is measured against (the pre-pour
guarantee), and checks a duct run against its floor's joist bays/bearing lines.

The shared derivations both the checks and the takeoffs ask for — wet-wall occupancy,
concrete crossings, drain roll-up, duct bay occupancy — live in ``mep_queries.py``; they
are questions about a resolved model rather than steps that build one. They are re-exported
here because ``typehaus.resolve.mep`` is the name every call site already imports.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LuminaireForm, PipeAccessoryKind, Service
from typehaus.model.mep import (
    ConduitRun,
    DuctRun,
    LightRun,
    PipeAccessory,
    PipeRun,
    SleevePenetration,
)
from typehaus.quantities import inch
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.mep_queries import (  # noqa: F401 - re-exported query API
    _CONCRETE_SOLID_CATEGORIES,
    _conduit_vertical_profile,
    accumulated_serves,
    concrete_crossings,
    drain_tie_ins,
    duct_bay_occupancy,
    is_parallel_to_floor,
    on_pipe_segment,
    pipe_invert_at,
    wet_wall_occupancy,
)
from typehaus.resolve.mep_sleeves import (  # noqa: F401 - re-exported sleeve API
    _PIPE_SLEEVE_SNAP_M,
    _expected_drain_point,
    _expected_sleeve_point,
    _pipe_expected_point,
    _resolve_sleeve,
)
from typehaus.resolve.mep_ducts import resolve_duct_run
from typehaus.resolve.mep_slope import _pipe_vertex_z  # noqa: F401 - re-exported
from typehaus.resolve.mep_soffit import (  # noqa: F401 - re-exported query API
    soffit_occupancy,
)
from typehaus.resolve.model import (
    ResolvedConduitRun,
    ResolvedLightRun,
    ResolvedModel,
    ResolvedPipeAccessory,
    ResolvedPipeRun,
    ResolvedSolid,
    SolidSweep,
)
from typehaus.resolve.placeables import resolved_mount_elevation
from typehaus.resolve.round_solids import PIPE_FACETS
from typehaus.resolve.sweep import (
    clean_path,
    round_profile,
    sweep_plan_silhouette,
    sweep_z_extent,
)

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
                findings.extend(_resolve_duct_run(model, element, storey))
            elif isinstance(element, ConduitRun):
                findings.extend(_resolve_conduit_run(model, element, storey.tag))
            elif isinstance(element, LightRun):
                findings.extend(_resolve_light_run(model, element, storey))
    # Accessories last: each one locates itself on a resolved run, so every run in the
    # model — not just this storey's — must already exist. A basement trunk carries the
    # main-storey seal at a hydrant two floors up.
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, PipeAccessory):
                findings.extend(_resolve_pipe_accessory(model, element, storey))
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
    resolved = ResolvedConduitRun(
        uid=run.uid, tag=run.tag, storey=storey_tag, path=path,
        trade_size_m=run.trade_size.meters, z_start_m=z0, z_end_m=z1,
        length_m=plan_len + rise, from_ref=run.from_ref, to_ref=run.to_ref,
        service=run.service.value if run.service is not None else None,
    )
    model.conduits.append(resolved)
    # Geometry from the same profile ``concrete_crossings`` walks, so the raceway a reader
    # sees in the viewer is the one the pour-day crossing list was derived from — one
    # derivation, not two that can disagree. A run with no elevation emits nothing, and that
    # silence is deliberate: ``_conduit_vertical_profile`` returns None precisely when there
    # is no vertical information to extrude, and a raceway drawn at an invented height would
    # be a claim about where the electrician bores that nobody authored.
    profile = _conduit_vertical_profile(resolved)
    if profile is not None:
        solid_path, solid_z = profile
        _emit_run_solids(model, run.uid or run.tag, run.tag, storey_tag,
                         solid_path, solid_z,
                         round_profile(run.trade_size.meters / 2.0, PIPE_FACETS),
                         _conduit_category(resolved.service))
    return []


#: A raceway's solid category. Two of them, because the one distinction that matters when you
#: look at a raceway is which side of NEC 800.133/725 it is on: comms may never share a run
#: with power, so "power or data" is the whole question, and the voltage is a property to read
#: off the run (``ResolvedConduitRun.service``) rather than a thing to tell apart by colour.
#: A capped spare rides with power — it is in the electrician's rough-in, and the only things
#: that will ever go in it are power or comms; a third "conduit_spare" label would name an
#: empty pipe nobody needs to distinguish on screen. (Categories are what the 3D inspector
#: *prints*, so they are named for what a person calls the thing, never for its element
#: family — "conduit run" would be as useless a heading as "pipe accessory" was.)
def _conduit_category(service: str | None) -> str:
    return "conduit_data" if service == Service.DATA.value else "conduit_power"


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


def _emit_run_solids(model: ResolvedModel, run_uid: str, run_tag: str, storey_tag: str,
                     path: list[tuple[float, float]], z: list[float],
                     profile: tuple[tuple[float, float], ...], category: str) -> None:
    """One swept solid for the whole routed run — the tube it actually is.

    A run used to be chopped up twice over: a vertical drop was a faceted circle prism, a
    horizontal leg a stack of chord bands in Z, and a *sloping* leg a stair-step of at most
    three of those stacks — an approximation ``round_solids.sloped_run_bands`` said so in its
    own docstring. Now the polyline and its per-vertex inverts go straight into a
    :class:`~typehaus.resolve.model.SolidSweep`, which mitres itself (→ resolve/sweep.py):
    a vertical drop is just a leg whose direction happens to be down, so the repeated-plan-
    point special case has nothing left to special-case.

    ``category`` is passed in rather than derived here because two trades route through this
    one geometry: a pipe run is per-system (``pipe_drain``, ``pipe_water_hot``, …) and a
    raceway is per-service (``conduit_power``/``conduit_data``). The sweep is identical — a
    round section along a polyline with per-vertex elevations — and the only thing that
    differs is the label the viewer and the glTF export colour-code by, so the label is the
    argument. (It used to be ``system: str`` with ``f"pipe_{system}"`` baked in, which is why
    conduit had no geometry at all: there was nowhere for a raceway to say what it was.)

    ``profile`` is passed in for the same reason, one trade later: a duct is round *or*
    rectangular, and ``rect_profile`` has been sitting in ``sweep.py`` unused since the
    kernel was written. A radius argument could only ever have described half of HVAC."""
    from typehaus.resolve.model import ResolvedSolid

    # ``clean_path`` rather than the raw vertices: an authored elbow repeats its plan point
    # at one invert, and two points at the same place are one point, not a zero-length leg.
    points = clean_path([(p[0], p[1], zi) for p, zi in zip(path, z)])
    if len(points) < 2:
        return
    sweep = SolidSweep(path=points, profile=profile)
    z0, z1 = sweep_z_extent(sweep)
    model.solids.append(ResolvedSolid(
        uid=f"{run_uid}-run", tag=f"{run_tag}-RUN", storey=storey_tag, category=category,
        outline=sweep_plan_silhouette(sweep), z0_m=z0, z1_m=z1, sweep=sweep))


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
        _emit_run_solids(model, run.uid or run.tag, run.tag, storey.tag, path, z,
                         round_profile(run.diameter.meters / 2.0, PIPE_FACETS),
                         f"pipe_{run.system.value}")
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
        finish=run.finish, insulation=run.insulation,
    ))
    return findings


#: The accessory box, in metres. A valve body is not a pipe and is not to scale with one —
#: it is drawn as a marker you can find in the 3D view and click, the way a sump pit is.
_ACCESSORY_BOX = (inch(4).meters, inch(4).meters, inch(6).meters)

#: A solid's category is what every consumer *labels* it with — the 3D inspector's heading,
#: the ``structural_solids`` rollup, the palette. "pipe_accessory" is the family, and a
#: family name is a useless label: clicking the hose bib on the balcony would say "pipe
#: accessory", which is true of a shutoff, a backflow preventer and a can of foam alike. So
#: each kind carries its own category, straight off the enum, and the family stays available
#: as a set (``emit/trades.py::PIPE_ACCESSORY_CATEGORIES``) for the consumers that do want
#: to treat them alike.
def _accessory_category(kind: PipeAccessoryKind) -> str:
    return kind.value


def _resolve_pipe_accessory(model: ResolvedModel, el: PipeAccessory,
                            storey) -> list[Finding]:
    """Locate an in-line device on its host run and give it a solid.

    The host run is required: an accessory's system, bore and (usually) its elevation all
    come from the pipe it sits on, and one floating in space is an authoring slip rather
    than a device — it would bill, schedule and export as real while protecting nothing.
    """
    host = next((r for r in model.pipe_runs if r.tag == el.pipe_ref), None)
    if host is None:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.pipe_accessory_host",
            message=(f"pipe accessory {el.tag} references pipe_ref={el.pipe_ref!r}, "
                     "which is not a resolved PipeRun"),
            element_tags=(el.tag,), result=Result.FAIL)]
    cx, cy = el.position.xy_m
    if el.elevation is not None:
        z = storey.elevation.meters + el.elevation.meters
    else:
        z = _host_z_at(host, (cx, cy))
        if z is None:
            return [Finding(
                severity=Severity.ERROR, check_id="integrity.pipe_accessory_elevation",
                message=(f"pipe accessory {el.tag} authors no elevation and its host run "
                         f"{host.tag} carries none either — nothing to fall back to"),
                element_tags=(el.tag, host.tag), result=Result.FAIL)]
    bx, by, bz = _ACCESSORY_BOX
    model.pipe_accessories.append(ResolvedPipeAccessory(
        uid=el.uid, tag=el.tag, storey=storey.tag, kind=el.kind.value,
        position=(cx, cy), z_m=z, pipe_ref=host.tag, system=host.system,
        diameter_m=host.diameter_m, serves=tuple(el.serves), accessible=el.accessible,
        room=el.room, wall_ref=el.wall_ref, model=el.model,
        install_parts=tuple(el.install_parts),
    ))
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-acc", tag=el.tag, storey=storey.tag,
        category=_accessory_category(el.kind),
        outline=((cx - bx / 2.0, cy - by / 2.0), (cx + bx / 2.0, cy - by / 2.0),
                 (cx + bx / 2.0, cy + by / 2.0), (cx - bx / 2.0, cy + by / 2.0)),
        z0_m=z - bz / 2.0, z1_m=z + bz / 2.0,
    ))
    return []


def _host_z_at(host: ResolvedPipeRun, point: tuple[float, float]) -> float | None:
    """The host run's invert at its vertex nearest ``point``.

    Nearest *vertex* rather than an interpolation along the segment: a valve is authored at
    a fitting, and a fitting is a vertex. Interpolating would put a shutoff at the elevation
    of the sloping leg it is beside rather than of the tee it is on."""
    if host.z_m is None:
        return None
    best = min(range(len(host.path)),
               key=lambda i: length(sub(host.path[i], point)))
    return host.z_m[best]


def _resolve_duct_run(model: ResolvedModel, duct: DuctRun, storey) -> list[Finding]:
    """Thin seam onto :mod:`typehaus.resolve.mep_ducts` — see that module's docstring.

    ``_emit_run_solids`` is handed over rather than imported there: this module owns it and
    is the one every call site imports, so the dependency runs mep -> mep_ducts and stays
    acyclic.
    """
    return resolve_duct_run(model, duct, storey, _emit_run_solids)

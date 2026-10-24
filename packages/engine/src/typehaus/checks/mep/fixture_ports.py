"""Hold authored plumbing endpoints to each fixture's declared connection stations."""

from __future__ import annotations

from math import dist, hypot

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model import Service
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_sleeves import expected_port_point

CHECK_ID = "mep.fixture_port_connection"
PLUMBING_SERVICES = (Service.DRAIN, Service.WATER_HOT, Service.WATER_COLD)


@check(Tier.INTEGRITY, CHECK_ID)
def fixture_port_connection(ctx: CheckContext) -> list[Finding]:
    """Grade plan and elevation independently; missing elevations cannot establish a joint."""
    types = {entry.tag: entry for entry in ctx.plan.library.fixture_types}
    storeys = {element.tag: storey for storey in ctx.plan.storeys
               for element in ctx.plan.storey_elements(storey.tag)}
    preferences = ctx.preferences.plumbing
    out: list[Finding] = []
    for fixture in ctx.plan.elements_of_kind("Fixture"):
        fixture_type = types.get(fixture.type_ref)
        if fixture_type is None:
            continue
        for port in fixture_type.ports:
            if port.service not in PLUMBING_SERVICES:
                continue
            point = expected_port_point(ctx.model, fixture.tag, port.service)
            if point is None:
                continue
            tags = (fixture.tag, port.tag)
            if port.service is Service.DRAIN and fixture.drain_position is not None:
                drift = dist(fixture.drain_position.xy_m, point[:2])
                if drift > preferences.fixture_port_exact_tolerance_in * M_PER_IN:
                    out.append(failed(CHECK_ID, f"{fixture.tag} authored drain_position drifts "
                                      f'{drift / M_PER_IN:.2f}" from DRAIN port {port.tag}', tags))
            runs = [run for run in ctx.model.pipe_runs
                    if fixture.tag in run.serves and run.system == port.service.value]
            if not runs:
                continue
            # Runs can be authored on another storey; compare absolute project elevations.
            point = (*point[:2], point[2] + storeys[fixture.tag].elevation.meters)
            endpoints = [(run.tag, (*run.path[index], run.z_m[index]))
                         for run in runs if len(run.path) >= 2 and len(run.z_m) == len(run.path)
                         for index in (0, len(run.path) - 1)]
            tolerance = (preferences.fixture_port_exact_tolerance_in if port.is_exact()
                         else preferences.fixture_port_approximate_tolerance_in) * M_PER_IN
            nearest = min(endpoints, key=lambda end: dist(end[1], point), default=None)
            matching = next((tag for tag, end in endpoints
                             if hypot(end[0] - point[0], end[1] - point[1]) <= tolerance
                             and abs(end[2] - point[2]) <= tolerance), None)
            detail = (f'nearest endpoint {nearest[0]} at {nearest[1]}, '
                      f'{dist(nearest[1], point) / M_PER_IN:.2f}" away'
                      if nearest is not None else "no serving endpoint has a resolved elevation")
            message = f"{fixture.tag} {port.service.value} port {port.tag} at {point}: {detail}"
            if not port.is_exact():
                out.append(unknown(CHECK_ID, message + "; approximate station", tags))
            elif matching is not None:
                out.append(passed(CHECK_ID, message + f"; connected by {matching}", tags))
            else:
                out.append(failed(CHECK_ID, message, tags))
    return out or [not_applicable(CHECK_ID, "no served fixture plumbing ports", ())]

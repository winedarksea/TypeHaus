"""Resolve an authored sanitary cleanout into its fitting, access tube, and cap."""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.mep import DrainCleanout
from typehaus.quantities import inch
from typehaus.resolve.mep_queries import pipe_invert_at
from typehaus.resolve.model import ResolvedDrainCleanout, ResolvedModel, ResolvedSolid, SolidSweep
from typehaus.resolve.round_solids import PIPE_FACETS
from typehaus.resolve.sweep import round_profile, sweep_plan_silhouette, sweep_z_extent


def _component(model: ResolvedModel, element: DrainCleanout, storey: str,
               suffix: str, category: str, path: tuple[tuple[float, float, float], ...],
               radius: float) -> None:
    sweep = SolidSweep(path=path, profile=round_profile(radius, PIPE_FACETS))
    z0, z1 = sweep_z_extent(sweep)
    model.solids.append(ResolvedSolid(
        uid=element.uid if suffix == "FIT" else f"{element.uid}-{suffix}",
        tag=element.tag if suffix == "FIT" else f"{element.tag}-{suffix}", storey=storey,
        category=category, outline=tuple(sweep_plan_silhouette(sweep)),
        z0_m=z0, z1_m=z1, sweep=sweep,
    ))


def _host_tangent(host, point):
    """Horizontal flow direction at the cleanout's station."""
    candidate = None
    for a, b in zip(host.path, host.path[1:], strict=False):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 1e-6:
            continue
        fraction = max(0.0, min(1.0, ((point[0] - a[0]) * dx
                                          + (point[1] - a[1]) * dy) / length ** 2))
        projected = (a[0] + fraction * dx, a[1] + fraction * dy)
        if math.dist(point, projected) < 1e-5:
            candidate = (dx / length, dy / length)
    return candidate


def resolve_drain_cleanout(model: ResolvedModel, element: DrainCleanout,
                           storey) -> list[Finding]:
    host = next((run for run in model.pipe_runs if run.tag == element.pipe_ref), None)
    fitting = element.position.xy_m
    cap = element.cap_position.xy_m
    fitting_z = storey.elevation.meters + element.fitting_elevation.meters
    cap_z = storey.elevation.meters + element.cap_elevation.meters
    reason = None
    if host is None or host.system != "drain" or not host.sanitary:
        reason = "does not reference a sanitary drain"
    elif element.direction not in {"one_way", "two_way"}:
        reason = "must specify one_way or two_way"
    elif element.access not in {"wall", "cabinet", "ceiling", "floor", "grade"}:
        reason = "must specify wall, cabinet, ceiling, floor, or grade access"
    elif ((host_z := pipe_invert_at(host, fitting)) is None
          or abs(host_z - fitting_z) > host.diameter_m / 2):
        reason = "fitting does not meet its host run in 3D"
    elif math.dist((*fitting, fitting_z), (*cap, cap_z)) < inch(2).meters:
        reason = "needs a physical access extension to its cap"
    elif element.access == "wall" and math.dist(fitting, cap) < inch(1.5).meters:
        reason = "wall cap needs a wallward offset"
    if reason:
        return [Finding(severity=Severity.ERROR, check_id="integrity.drain_cleanout",
                        message=f"cleanout {element.tag} {reason}",
                        element_tags=(element.tag, element.pipe_ref), result=Result.FAIL)]

    assert host is not None
    diameter = host.diameter_m
    model.drain_cleanouts.append(ResolvedDrainCleanout(
        uid=element.uid, tag=element.tag, storey=storey.tag, pipe_ref=host.tag,
        position=fitting, fitting_z_m=fitting_z, cap_position=cap, cap_z_m=cap_z,
        direction=element.direction, access=element.access, wall_ref=element.wall_ref,
        clear_width_m=element.clear_width.meters,
        clear_depth_m=element.clear_depth.meters,
        accessible=element.accessible, diameter_m=diameter,
    ))
    # Fitting body and removable cap have their own selectable identity. The access tube
    # is a real sweep between them, not a line or a marker.
    fitting_end = (fitting[0], fitting[1], fitting_z + inch(4).meters)
    _component(model, element, storey.tag, "FIT", "cleanout_fitting",
               ((fitting[0], fitting[1], fitting_z - inch(2).meters), fitting_end),
               diameter * 0.62)
    if element.direction == "two_way":
        tangent = _host_tangent(host, fitting)
        if tangent is not None:
            for suffix, sign in (("FIT-UP", -1), ("FIT-DN", 1)):
                _component(model, element, storey.tag, suffix, "cleanout_fitting",
                           ((fitting[0], fitting[1], fitting_z - inch(2).meters),
                            (fitting[0] + sign * tangent[0] * inch(6).meters,
                             fitting[1] + sign * tangent[1] * inch(6).meters,
                             fitting_z + inch(4).meters)), diameter * 0.40)
    cap_end = (cap[0], cap[1], cap_z)
    extension = ((fitting_end, (fitting[0], fitting[1], cap_z), cap_end)
                 if element.access == "wall" else (fitting_end, cap_end))
    _component(model, element, storey.tag, "EXT", "cleanout_extension",
               extension, diameter * 0.45)
    if element.access == "wall":
        dx, dy = cap[0] - fitting[0], cap[1] - fitting[1]
        distance = math.hypot(dx, dy)
        cap_start = (cap[0] - dx / distance * inch(0.375).meters,
                     cap[1] - dy / distance * inch(0.375).meters, cap_z)
        cap_tip = (cap[0] + dx / distance * inch(0.375).meters,
                   cap[1] + dy / distance * inch(0.375).meters, cap_z)
    else:
        cap_start = (cap[0], cap[1], cap_z - inch(0.375).meters)
        cap_tip = (cap[0], cap[1], cap_z + inch(0.375).meters)
    _component(model, element, storey.tag, "CAP", "cleanout_cap",
               (cap_start, cap_tip),
               diameter * 0.58)
    return []

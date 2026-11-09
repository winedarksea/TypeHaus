"""Every exposed panel rib end at an eave, from the seam register the skin itself uses.

Runs after the skin and pan ends, so it reads them and the skin never imports this module.
Rakes, ridges and eaves another roof continues across have no exposed end to record.
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.library.trim.image_ii_eave_sealing import EAVE_RIB_SEALING_BY_KIT
from typehaus.resolve.model_eave_sealing import (
    CLEAT_EAVE,
    EAVE_PAN_CONNECTIONS,
    FULL_CAVITY,
    RIPPED_CAVITY,
    SHARED_CAVITY,
    WRAPPED_EAVE,
    ResolvedEaveRibEnd,
    ResolvedEaveSealingRun,
)
from typehaus.resolve.roof_edge_geometry import (
    abutted_run_keys,
    roof_continues_at,
    roof_edge_runs,
    seam_register_roofs,
)
from typehaus.resolve.roof_image_ii import roof_edge_kit
from typehaus.resolve.roof_image_ii_pan_end import seam_path, wrapped_eave_runs
from typehaus.resolve.roof_panel_hem import cleat_eave_seat
from typehaus.resolve.roof_panel_skin import profiled_roof_layers, seam_anchor


def resolve_eave_rib_ends(model) -> None:
    model.eave_sealing_runs = [run for roof in model.roofs for run in _sealing_runs(model, roof)]


def _standing_seam_layer(model, roof):
    return next(((base, rect, profile) for _, base, rect, profile
                 in profiled_roof_layers(roof, model) if profile.key == "standing-seam"), None)


def _sealing_runs(model, roof) -> tuple[ResolvedEaveSealingRun, ...]:
    kit = roof_edge_kit(model, roof)
    layer = _standing_seam_layer(model, roof) if kit else None
    if layer is None:
        return ()
    base, rect, profile = layer
    along_x = roof.ridge_direction == "x"
    low, high = rect[:2] if along_x else rect[2:]
    anchor = seam_anchor(model, roof)
    anchor = (low + high) / 2 if anchor is None else anchor
    margin = profile.crown_width_m or profile.sheet_thickness_m
    abutted = abutted_run_keys(model, roof)
    wrapped, stack = wrapped_eave_runs(model, roof)
    wrapped_keys = {run.key for run in wrapped}
    spec = EAVE_RIB_SEALING_BY_KIT.get(kit)
    area = Polygon(seam_path(profile)).area
    runs = []
    for run in roof_edge_runs(roof):
        sign = run.normal[1] if along_x else run.normal[0]
        if not run.is_eave or run.key in abutted or (roof.form == "shed" and sign > 0):
            continue
        is_wrapped = run.key in wrapped_keys
        endpoint = (_wrapped_endpoint(run, stack, along_x) if is_wrapped
                    else _cleat_endpoint(roof, rect, base, sign, along_x))
        ends = []
        for k in range(math.ceil((low - margin - anchor) / profile.pitch_m),
                       math.floor((high + margin - anchor) / profile.pitch_m) + 1):
            station = anchor + k * profile.pitch_m
            across, z = endpoint
            xy = (station, across) if along_x else (across, station)
            cavity = _cavity(model, roof, run, station, xy, low, high, margin, abutted, along_x)
            if cavity is None:
                continue
            treated = spec is not None and cavity != RIPPED_CAVITY
            ends.append(ResolvedEaveRibEnd(
                key=f"{roof.tag}:{run.key}:rib-{k}", roof_tag=roof.tag, run_key=run.key,
                edge_name=run.edge_name, station_m=station, point_m=(*xy, z),
                outward_normal=run.normal,
                eave_condition=WRAPPED_EAVE if is_wrapped else CLEAT_EAVE, cavity=cavity,
                profile_key=profile.key, treatment=spec.treatment if treated else None,
                sealant_part=spec.sealant.part if treated else None,
                source=spec.source if treated else None))
        runs.append(ResolvedEaveSealingRun(
            roof_tag=roof.tag, run_key=run.key, edge_name=run.edge_name, kit=kit,
            eave_condition=WRAPPED_EAVE if is_wrapped else CLEAT_EAVE, rib_ends=tuple(ends),
            hem_length_m=_hem_length(roof, run), tape_length_m=high - low,
            rib_cavity_area_m2=area))
    return tuple(runs)


def _wrapped_endpoint(run, stack, along_x: bool) -> tuple[float, float]:
    """``(across, z)`` where the seam legs stop at the eave face, at the pan's underside."""
    _, u, lift = stack.seam_flats()[-1]
    edge = run.p0[1] if along_x else run.p0[0]
    outward = run.normal[1] if along_x else run.normal[0]
    return (edge + u * outward,
            run.z0_m - u * stack.slope + (stack.membrane_top_w + lift) * stack.factor)


def _cleat_endpoint(roof, rect, base: float, sign: float, along_x: bool) -> tuple[float, float]:
    across_low, across_high = rect[2:] if along_x else rect[:2]
    return cleat_eave_seat(roof, across_high if sign > 0 else across_low, sign, base)


def _cavity(model, roof, run, station, xy, low, high, margin, abutted, along_x) -> str | None:
    """The rib's state at this edge, or ``None`` when the neighbouring roof records it."""
    if low < station - margin and station + margin < high:
        return FULL_CAVITY
    side = "rake-lo" if station - margin <= low else "rake-hi"
    if not any(key.startswith(side) for key in abutted):
        return RIPPED_CAVITY
    neighbours = [other.tag for other in seam_register_roofs(model, roof)
                  if other.tag != roof.tag and roof_continues_at(roof, other, xy)]
    return SHARED_CAVITY if all(roof.tag < tag for tag in neighbours) else None


def _hem_length(roof, run) -> float:
    """The hems actually resolved on this run's side of the roof."""
    xs, ys = zip(*roof.footprint, strict=True)
    middle = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    return sum(
        math.dist(member.p0, member.p1) for member in roof.members
        if member.connection in EAVE_PAN_CONNECTIONS
        and (member.p0[0] - middle[0]) * run.normal[0]
        + (member.p0[1] - middle[1]) * run.normal[1] > 0)

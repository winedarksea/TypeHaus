"""The Image II pan's end on a wrapped Extended Eave (RDM p. 31: "bend flat pan of panel
around to accept Extended Eave Flashing", crimped closed).

The field skin stops one ramp short of the membrane strip-in (``EaveStack.pan_cut_u``). Past
it, per pan, one swept member carries the pan over the strip and the metal stack to the lip,
folds 180 deg round it and returns under. The seam legs ride the same lift in short stubs and
stop at the face line, short of the fold. Other eaves keep ``roof_panel_hem``'s cleat hem.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.resolve.metal_skin_profiles import _inset_section
from typehaus.resolve.roof_edge_geometry import abutted_run_keys, roof_edge_runs
from typehaus.resolve.roof_image_ii import edge_member, thickened_ring, wrapped_image_ii_edges
from typehaus.resolve.roof_image_ii_eave import eave_stack


def wrapped_eave_runs(model, roof):
    """The eave runs an Extended Eave wraps, and that roof's eave stack."""
    edges = wrapped_image_ii_edges(model, roof)
    stack = eave_stack(model, roof) if edges else None
    if stack is None:
        return (), None
    abutted = abutted_run_keys(model, roof)
    return tuple(run for run in roof_edge_runs(roof)
                 if run.is_eave and run.edge_name in edges and run.key not in abutted), stack


def _seam_path(profile) -> list[tuple[float, float]]:
    """One standing seam across its centre: the right leg of a pan, then the left of the next."""
    points = profile.section_points_m
    right = [(x - profile.pitch_m, w) for x, w in points[-3:]]
    return [*right, *points[1:3]]


def _flat_shaded(member):
    from typehaus.resolve.geometry_members import member_solid
    from typehaus.resolve.geometry_slice import sweep_mesh
    from typehaus.resolve.roof_panel_hem import flat_shaded

    return replace(member, surface_mesh=flat_shaded(sweep_mesh(member_solid(member))))


def image_ii_pan_ends(model, roof, rect, profile, material):
    """``(edge names handled, members)``: the pan ends and seam stubs on wrapped eaves."""
    runs, stack = wrapped_eave_runs(model, roof)
    if not runs:
        return frozenset(), ()
    along_x = roof.ridge_direction == "x"
    low, high = rect[:2] if along_x else rect[2:]
    anchor = (low + high) / 2
    margin = profile.crown_width_m or profile.sheet_thickness_m
    pan = thickened_ring([stack.uz(s, w) for s, w in stack.pan_path_sw()])
    seam = _seam_path(profile)
    seam_ring = [*seam, *reversed(_inset_section(seam, profile.sheet_thickness_m))]
    along = (1.0, 0.0) if along_x else (0.0, 1.0)
    members = []
    for run in runs:
        edge = run.p0[1] if along_x else run.p0[0]

        def at(station: float, u: float = 0.0, run=run, edge=edge):
            across = edge + u * (run.normal[1] if along_x else run.normal[0])
            return (station, across) if along_x else (across, station)

        for k in range(math.floor((low - anchor) / profile.pitch_m),
                       math.ceil((high - anchor) / profile.pitch_m)):
            center = anchor + k * profile.pitch_m
            a, b = max(low, center + margin), min(high, center + profile.pitch_m - margin)
            if b > a:
                members.append(_flat_shaded(edge_member(
                    roof.uid, f"{run.key}-pan-end-{k}", "roof_panel_hem", at(a), at(b),
                    run.z0_m, run.z0_m, run.normal, pan, "roof:pan-end", material)))
            if not (low < center - margin and center + margin < high):
                continue
            for index, (u0, u1, lift) in enumerate(stack.seam_flats()):
                ring = [(x, (stack.membrane_top_w + lift + w) * stack.factor)
                        for x, w in seam_ring]
                members.append(_flat_shaded(edge_member(
                    roof.uid, f"{run.key}-seam-end-{k}-{index}", "roof_panel_hem",
                    at(center, u0), at(center, u1), run.z0_m - u0 * stack.slope,
                    run.z0_m - u1 * stack.slope, along, ring, "roof:seam-end", material)))
    return frozenset(run.edge_name for run in runs), tuple(members)


def wrapped_eave_skin_setbacks(model, roof, entry: dict) -> dict:
    """``entry`` with each wrapped eave's skin cut at the pan's ramp onto the strip-in."""
    runs, stack = wrapped_eave_runs(model, roof)
    if not runs:
        return entry
    return {**entry, **{run.edge_name: -stack.pan_cut_u() for run in runs}}


def wrapped_eave_reach(model, roof) -> dict[str, float]:
    """Edge name -> the roofing's plan reach (``u``) on each wrapped Image II eave."""
    edges = wrapped_image_ii_edges(model, roof)
    stack = eave_stack(model, roof) if edges else None
    if stack is None:
        return {}
    return {run.edge_name: stack.lip_reach_u() for run in roof_edge_runs(roof)
            if run.is_eave and run.edge_name in edges}

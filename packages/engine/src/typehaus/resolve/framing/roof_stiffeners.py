"""I-joist bearing stiffener pairs, beveled to their rafter's roof slope."""

from __future__ import annotations

import math

from typehaus.resolve.framing.profiles import cross_section, panel_profile
from typehaus.resolve.model import FramedMember

# One member represents two 23/32" plywood plies, each ripped 4" wide for the LSSR hanger's
# stiffener requirement (catlin/notes/ridge_beam_detail.md §3). The pair remains a single
# block centered on the web, preserving its sheet-goods takeoff and plywood detail hatch.
_STIFFENER_PROFILE = panel_profile(4.0, 2 * 0.71875, "stiffener")
_STIFFENER_MATERIAL = "struct-1-plywood"
_MINIMUM_RAFTER_RUN_M = 1e-9


def bearing_stiffeners(
    rafters: tuple[FramedMember, ...], hung_at_ridge: bool,
) -> tuple[FramedMember, ...]:
    """One beveled pair per I-joist eave, and per ridge end hung on a beam.

    The 4" face runs along the rafter's web plane, with plumb sides and pitched top/bottom.
    The cut silhouette, plan endpoints and end elevations carry the same bevel into the
    shared solid, IFC, glTF and viewer without interpreting a connection label.
    """
    stiffeners: list[FramedMember] = []
    section = cross_section(_STIFFENER_PROFILE)
    for rafter in rafters:
        if cross_section(rafter.profile).shape != "i_joist":
            continue
        run = math.dist(rafter.p0, rafter.p1)
        if run < _MINIMUM_RAFTER_RUN_M:
            continue
        stiffener_run = min(section.width_m, run)
        stiffeners.append(_beveled_stiffener(rafter, "eave", 0.0, stiffener_run, run))
        if hung_at_ridge:
            stiffeners.append(_beveled_stiffener(
                rafter, "ridge", run - stiffener_run, run, run))
    return tuple(stiffeners)


def _beveled_stiffener(
    rafter: FramedMember, end: str, start_run_m: float, end_run_m: float, rafter_run_m: float,
) -> FramedMember:
    # Keep both faces inboard: centering an upright block on an end cut protruded past the
    # eave, and using ridge elevations for the entire block put its top above the roof plane.
    dx = rafter.p1[0] - rafter.p0[0]
    dy = rafter.p1[1] - rafter.p0[1]
    start_fraction = start_run_m / rafter_run_m
    end_fraction = end_run_m / rafter_run_m
    p0 = (rafter.p0[0] + dx * start_fraction, rafter.p0[1] + dy * start_fraction)
    p1 = (rafter.p0[0] + dx * end_fraction, rafter.p0[1] + dy * end_fraction)
    bottom_end = rafter.z0_m if rafter.z0_end_m is None else rafter.z0_end_m
    top_end = rafter.z1_m if rafter.z1_end_m is None else rafter.z1_end_m
    bottom_rise = bottom_end - rafter.z0_m
    top_rise = top_end - rafter.z1_m
    z0 = rafter.z0_m + bottom_rise * start_fraction
    z1 = rafter.z1_m + top_rise * start_fraction
    z0_end = rafter.z0_m + bottom_rise * end_fraction
    z1_end = rafter.z1_m + top_rise * end_fraction
    stiffener_run_m = end_run_m - start_run_m
    return FramedMember(
        rafter.parent_uid, f"{rafter.child_key}-{end}-stiffener", "bearing_stiffener",
        _STIFFENER_PROFILE, p0, p1, z0, z1, z1 - z0,
        z0_end_m=z0_end, z1_end_m=z1_end,
        connection=f"{end}:beveled-web-stiffener", material=_STIFFENER_MATERIAL,
        # Sweep the cut side silhouette across the plies. IFC's ordinary member sweep cuts
        # its ends square to the 3D axis, which would move these plumb faces into the beam.
        elevation_profile=((0.0, z0), (stiffener_run_m, z0_end),
                           (stiffener_run_m, z1_end), (0.0, z1)),
        # The panel profile's WIDTH is the rip face along the web; its DEPTH is the pair's
        # thickness across it. A horizontal-member default would put the 4" across the web.
        plan_width_m=cross_section(_STIFFENER_PROFILE).depth_m,
    )

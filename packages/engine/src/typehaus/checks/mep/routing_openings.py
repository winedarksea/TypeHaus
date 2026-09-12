"""``mep.run_through_opening`` — what a run goes THROUGH on its way.

Split out of ``checks/mep/routing.py``, unchanged. The shared vocabulary it is built on —
``run_polylines``, ``run_radii``, ``crossing_band`` — lives in ``routing_geometry.py``.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import MultiLineString, Polygon

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.mep.routing_geometry import (
    M_TO_FT,
    crossing_band,
    run_polylines,
    run_radii,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

#: A run whose surface comes within this of a rough opening's edge is not reported. A raceway
#: strapped to a jack stud shares a coordinate with the opening it is beside, and grading that
#: as "through the window" would be wrong in exactly the case the trade does on purpose. Half
#: an inch is under any framing member and over any coordinate noise.
OPENING_EDGE_M = 0.0127
#: How much of an opening a run must actually cross before it is reported. Below this it is a
#: corner clip, which is a dimension to check rather than a route to redraw.
MIN_CROSSING_FT = 0.1


def opening_prisms(
        ctx: CheckContext) -> list[tuple[str, bool, str, Any, float, float, str | None]]:
    """Each opening as ``(tag, is_door, host, footprint, z low, z high, penetration_for)``.

    The footprint is the opening's slice of its host wall through the WHOLE wall thickness,
    because that is the hole: a window buck runs the full depth of the assembly, and a run
    that crosses the opening's width anywhere in that depth is in it. The band is the host
    wall's FRAMING base plus the authored sill, which is how ``resolve`` places the buck.

    ``base_ref_z_m``, not ``z0_m``: a wall extended down over the rim keeps its floor where
    the framing is, and every other consumer that adds a sill to an elevation already reads
    it. Reading ``z0_m`` put every opening in catlin's main-storey exterior walls 13 7/16"
    below where it is built, which is exactly far enough to miss a run crossing it.
    """
    import math

    walls = {wall.tag: wall for wall in ctx.model.walls}
    out = []
    for opening in ctx.model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None or len(wall.axis) < 2:
            continue
        (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
        length = math.dist((ax, ay), (bx, by))
        if length <= 0:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        half, depth = opening.width_m / 2.0, wall.thickness_m / 2.0
        near, far = opening.center_along_m - half, opening.center_along_m + half
        corners = [(ax + ux * s + nx * depth * side, ay + uy * s + ny * depth * side)
                   for s in (near, far) for side in (1, -1)]
        prism = Polygon([corners[0], corners[1], corners[3], corners[2]])
        prism = prism.buffer(-OPENING_EDGE_M)
        if prism.is_empty or not prism.is_valid:
            continue
        low = wall.base_ref_z_m + opening.sill_m
        out.append((opening.tag, bool(opening.is_door), wall.tag, prism,
                    low, low + opening.height_m, opening.penetration_for))
    return out


@check(Tier.ADVISORY, "mep.run_through_opening")
def run_through_opening(ctx: CheckContext) -> list[Finding]:
    """A pipe, duct or raceway may not pass through a window or door rough opening.

    This is the hole the trades leave for something else. A run drawn across it is not a
    clearance question to be resolved on site — there is nothing there to strap to, the leaf
    swings through it, and in a window it stands in front of the glass. It is also the single
    easiest defect to author, because a plan drawing shows a run crossing a wall and says
    nothing about whether it crossed at the header or at the opening.

    **Nothing else in the engine looks.** ``mep.duct_joist_bay`` grades the bay a duct is in
    and never asks what its riser stands in — on catlin it PASSED a 3" extract standing 78 1/2"
    inside ``D-S-PLANT``'s rough opening and printed the station twice in its own fire-blocking
    list. ``structural.member_interference`` is wood against wood. ``mep.run_over_void`` grades
    holes in floors, not holes in walls. Before this check the argument was made by hand, in a
    comment, when it was made at all (``houses/catlin/plan/electrical.py`` reasoned about one
    door head in prose and was right; two windows and three doors elsewhere were missed).

    Two cases, because a run meets an opening in two ways:

    **Crossing** — a segment whose plan line passes through the opening's footprint within its
    elevation band. The band is taken at the crossing, not over the whole segment; see
    :func:`~typehaus.checks.mep.routing_geometry.crossing_band` for why that distinction
    decides real findings from arithmetic.

    **Standing in it** — a riser, whose plan segment has no length at all, landing inside the
    footprint with its rise overlapping the band. This is the ``D-S-PLANT`` case and a
    crossing test alone cannot see it, because a riser crosses nothing.

    **What it cannot see** is a run passing *beside* an opening's prism at the height of the
    hole — ``PR-A-STUBATH-DRAIN``'s diagonal dives through the suite bath's doorway air
    without ever entering ``D-S-SUITEBATH``'s own footprint. That is
    ``mep.run_in_finished_volume``'s half of the question.

    ADVISORY rather than CODE: no section says "do not draw a duct through a window", for the
    same reason no section says which side of a wall a light switch is on. It is a buildability
    rule, and its result is still ``FAIL`` so a clean house stays clean.
    """
    from shapely.geometry import LineString, Point

    cid = "mep.run_through_opening"
    runs = run_polylines(ctx)
    if not runs:
        return [unknown(cid, "no pipe, duct or conduit run is modeled, so there is no route "
                             "to grade", ())]
    prisms = opening_prisms(ctx)
    if not prisms:
        return [passed(cid, f"{len(runs)} runs: this model resolves no rough opening, so no "
                            "run can pass through one", ())]

    radii = run_radii(ctx)
    out: list[Finding] = []
    ungraded: list[str] = []

    for kind, tag, path, z in sorted(runs, key=lambda item: item[1]):
        if len(path) < 2:
            continue
        if len(z) != len(path):
            ungraded.append(tag)
            continue
        radius = radii.get(tag, 0.0)
        for index in range(len(path) - 1):
            a, b = path[index], path[index + 1]
            za, zb = z[index], z[index + 1]
            segment = LineString([a, b])
            standing = segment.length <= OPENING_EDGE_M
            for otag, is_door, host, prism, low, high, penetration_for in prisms:
                if penetration_for == tag:
                    # This hole exists FOR this run: it is the penetration, not an opening
                    # the run was drawn across. Only this pairing is exempt — another run
                    # through this opening, or this run through another, still reports.
                    continue
                if standing:
                    if not prism.covers(Point(a)):
                        continue
                    band = (min(za, zb), max(za, zb))
                    if band[1] - band[0] <= OPENING_EDGE_M:
                        continue
                    overlap = min(band[1], high) - max(band[0], low)
                    if overlap <= OPENING_EDGE_M:
                        # A riser that merely touches the head or the sill passes the opening,
                        # it does not stand in it — and a run has to touch one of the two to
                        # get past. Only an overlap with real height is a finding.
                        continue
                    out.append(advisory(
                        cid,
                        f"{kind} run {tag} stands {overlap * 12 * M_TO_FT:.0f}\" inside "
                        f"{otag}'s rough opening in {host} — a riser in a "
                        f"{'doorway' if is_door else 'window'} has nothing to strap to, and "
                        "the header above it is not borable",
                        (tag, otag), Result.FAIL,
                        fix="move the riser to a clear stud bay beside the opening; the "
                            "terminal it feeds usually has to move with it"))
                    continue
                piece = prism.intersection(segment)
                if piece.is_empty or piece.length <= 0:
                    continue
                crossed_ft = piece.length * M_TO_FT
                if crossed_ft < MIN_CROSSING_FT:
                    continue
                pieces = (piece.geoms if isinstance(piece, MultiLineString) else [piece])
                for part in pieces:
                    lo, hi = crossing_band(segment, za, zb, part)
                    if hi + radius < low or lo - radius > high:
                        continue
                    out.append(advisory(
                        cid,
                        f"{kind} run {tag} crosses {crossed_ft:.2f} ft of {otag}'s rough "
                        f"opening in {host}, at {(lo - low) * 12 * M_TO_FT:.0f}\" above its "
                        f"sill — the opening is {(high - low) * 12 * M_TO_FT:.0f}\" tall",
                        (tag, otag), Result.FAIL,
                        fix="carry the run over the header or under the sill, or take it to "
                            "the next stud bay; in a window there is no 'over' — the head is "
                            "usually the plate"))
                    break

    if not any(finding.result is Result.FAIL for finding in out):
        out.append(passed(cid, f"{len(runs)} runs against {len(prisms)} rough openings: no "
                               "run passes through one or stands in one", ()))
    if ungraded:
        out.append(unknown(cid, f"{len(ungraded)} run(s) carry no resolved elevations and are "
                                f"not graded: {', '.join(sorted(ungraded)[:6])}",
                           tuple(sorted(ungraded))))
    return out

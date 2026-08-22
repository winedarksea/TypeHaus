"""Nothing may occupy the cavity a pocket door's leaf slides into (→ 11 §Framing).

The wall over a pocket looks like any other partition and is not one. Between the mouth
and the closed end there is no stud to fasten to, no bay to bore, and no depth to recess a
box into — the leaf is using all of it. Every kit publishes the same warning and it is the
single most common way a pocket door is ruined after the drywall goes on.

The model could not say so before: ``mep.wet_wall_occupancy`` tests a pipe against the
*empty* cavity depth and never asks what else is in the bay, and an ``ElectricalDevice``
carries no enforced ``wall_ref`` at all, so nothing correlated a box with the wall behind
it. This check closes both by testing plan geometry against the pocket's own footprint.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.framing.pockets import pocket_segments
from typehaus.resolve.geometry import length, sub, unit

_CID = "mep.pocket_occupancy"
# A fastening or a box needs the wall's depth, so anything whose plan point lands within
# the structure band is in the leaf's way. The tolerance only forgives authoring noise.
_BAND_TOLERANCE_M = 0.01


def _pocket_bands(ctx: CheckContext):
    """``(opening, wall_tag, shapely polygon)`` for every pocket cavity in the plan."""
    from shapely.geometry import LineString

    for op in ctx.model.openings:
        if not op.pocket_run_m:
            continue
        segments, _shortfall = pocket_segments(ctx.plan, ctx.model, op)
        for segment in segments:
            wall = ctx.model.wall(segment.wall_tag)
            if wall is None:
                continue
            structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
            if structure is None:
                continue
            (sx, sy), (ex, ey) = wall.axis
            axis_len = length(sub((ex, ey), (sx, sy)))
            if axis_len <= 1e-9:
                continue
            ux, uy = unit(sub((ex, ey), (sx, sy)))
            low = (sx + ux * segment.low_m, sy + uy * segment.low_m)
            high = (sx + ux * segment.high_m, sy + uy * segment.high_m)
            half_depth = structure.thickness_m / 2.0 + _BAND_TOLERANCE_M
            # Flat caps: the band is the cavity's own length, not a rounded sweep past it.
            yield op, segment.wall_tag, LineString([low, high]).buffer(half_depth,
                                                                      cap_style=2)


@check(Tier.CODE, _CID)
def pocket_occupancy(ctx: CheckContext) -> list[Finding]:
    """A pocket's cavity must hold no pipe, no wall-mounted device, and no register."""
    from shapely.geometry import LineString, Point

    out: list[Finding] = []
    for op, wall_tag, band in _pocket_bands(ctx):
        hits: list[tuple[str, str]] = []

        for run in ctx.model.pipe_runs:
            for index in range(len(run.path) - 1):
                segment = LineString([run.path[index], run.path[index + 1]])
                if segment.intersects(band):
                    hits.append((run.tag, "pipe run"))
                    break

        for element in ctx.plan.all_elements():
            kind = element.element_kind
            if kind not in ("ElectricalDevice", "Register"):
                continue
            mount = getattr(element, "mount", None)
            mount_kind = getattr(getattr(mount, "kind", None), "value", None)
            if mount_kind != "wall":
                continue
            position = getattr(element, "position", None)
            xy = getattr(position, "xy_m", None)
            if xy is None or not Point(xy).within(band):
                continue
            hits.append((element.tag, "recessed device" if getattr(
                mount, "recessed_into_host_surface", False) else "wall-mounted device"))

        if not hits:
            out.append(_pass(
                _CID,
                f"{op.tag}'s pocket in {wall_tag} is clear — no pipe, device or register "
                f"in the leaf's travel", (op.tag, wall_tag)))
            continue
        for tag, what in sorted(set(hits)):
            out.append(_fail(
                _CID,
                f"{what} {tag} sits in {op.tag}'s pocket cavity in {wall_tag}. That run of "
                f"wall is hollow for the leaf: it has no stud to fasten to, no bay to bore "
                f"and no depth to recess into. Move it, or shorten the pocket.",
                (op.tag, wall_tag, tag)))
    return out

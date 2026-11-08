"""The pass-through window of each blocked bearing-line bay, as a level-edge rule.

``resolve/floor_blocking`` blocks every bay where a wall above stands on a floor's bearing
line, and frames a 2x6 box where a run crosses (``blocking_parts.pass_through_box``). A run
whose crown is over the box's top rail, or whose side reaches the joist or beam face closing
the bay, FAILs ``mep.run_through_blocking``. That is the same for a truss deck as for
I-joists, and the router read neither: the bays were laid after the runs.

This reproduces ``blocking_parts.crossing_runs``' reading against each run-blind
``floor_blocking.bearing_bays`` bay: the block (its width, grown by the run's radius, along
the joists) by the clear bay across them. A level edge inside it at a depth that is not a
graze must keep its whole section inside the bay and under the top rail.

An edge rule, not a hard prism, on purpose: a 3-D lattice prism blocks its nodes and every
riser through it, and a riser up a stacked wall through the bearing line is the lane the
riser-cover rule sends supply pipe to. The check skips risers too.
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.blocking_parts import BOX_T_M, FIT_TOL_M, GRAZE_M

_BUCKET_M = 0.0254


class BearingBays:
    """Every blocked bay of every floor meeting ``bbox``, bucketed by edge axis and station."""

    def __init__(self, model: Any, bbox: tuple[float, float, float, float],
                 radius_m: float) -> None:
        from typehaus.resolve.floor_blocking import bearing_bays

        self.radius_m = r = radius_m
        self.index: dict[tuple[str, int], list[tuple]] = {}
        minx, miny, maxx, maxy = bbox
        for floor in model.floors:
            for bay in bearing_bays(model, floor):
                along = "x" if bay.along_x else "y"
                across = "y" if bay.along_x else "x"
                a0 = bay.block_centre - bay.width / 2.0 - r
                a1 = bay.block_centre + bay.width / 2.0 + r
                g0, g1 = bay.gap
                box = (a0, g0, a1, g1) if bay.along_x else (g0, a0, g1, a1)
                if box[2] < minx or box[0] > maxx or box[3] < miny or box[1] > maxy:
                    continue
                row = (along, a0, a1, g0, g1, bay.z0, bay.z1, floor.tag, bay.key)
                # An edge ALONG the joists sits at a station across them, and vice versa.
                for key in range(int(g0 / _BUCKET_M), int(g1 / _BUCKET_M) + 1):
                    self.index.setdefault((along, key), []).append(row)
                for key in range(int(a0 / _BUCKET_M), int(a1 / _BUCKET_M) + 1):
                    self.index.setdefault((across, key), []).append(row)

    def refusal(self, axis: str, station: float, lo: float, hi: float,
                z: float) -> str | None:
        """``"<floor> <bay>"`` if a level edge from ``lo`` to ``hi`` along ``axis`` at
        ``station``, centreline ``z``, cannot pass that bay's box, else None."""
        r = self.radius_m
        for along, a0, a1, g0, g1, z0, z1, tag, key in self.index.get(
                (axis, int(station / _BUCKET_M)), ()):
            if z + r < z0 + GRAZE_M or z - r > z1 - GRAZE_M:
                continue  # under or over the joists
            if axis == along:  # in the bay, crossing the line
                if not (g0 <= station <= g1 and hi > a0 and lo < a1):
                    continue
                p_lo, p_hi = station - r, station + r
            else:  # along the line, through the block itself
                if not (a0 <= station <= a1 and hi > g0 and lo < g1):
                    continue
                p_lo, p_hi = max(lo, g0) - r, min(hi, g1) + r
            if (z + r > z1 - BOX_T_M + FIT_TOL_M or p_lo < g0 - FIT_TOL_M
                    or p_hi > g1 + FIT_TOL_M):
                return f"{tag} {key}"
        return None

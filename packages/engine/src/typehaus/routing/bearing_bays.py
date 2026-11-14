"""The pass-through window of each blocked bearing-line bay, as a level-edge rule.

``resolve/floor_blocking`` blocks every bay where a wall above stands on a floor's bearing
line, and frames a 2x6 box where a run crosses (``blocking_parts.pass_through_box``). A run
whose crown is over the box's top rail, or whose side reaches the joist or beam face closing
the bay, FAILs ``mep.run_through_blocking``. That is the same for a truss deck as for
I-joists, and the router read neither: the bays were laid after the runs.

This reproduces ``blocking_parts.crossing_runs``' reading against each run-blind
``floor_blocking.bearing_bays`` bay: the block (its width, grown by the run's half-width,
along the joists) by the clear bay across them. A level edge inside it at a depth that is not a
graze must keep its whole section inside the bay and under the top rail.

An edge rule, not a hard prism, on purpose: a 3-D lattice prism blocks its nodes and every
riser through it, and a riser up a stacked wall through the bearing line is the lane the
riser-cover rule sends supply pipe to. ``mep.run_through_blocking`` skips risers too, but
``mep.riser_through_deck`` does not: a riser standing on the block, or on the box's 2x6 rails
(``RAIL_W_M`` wide about ``box_centre``, wider than the block and not centred on it), lands on
a member, so :meth:`BearingBays.riser_refusal` refuses that footprint.
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.blocking_parts import BOX_T_M, FIT_TOL_M, GRAZE_M, RAIL_W_M

_BUCKET_M = 0.0254


class BearingBays:
    """Every blocked bay of every floor meeting ``bbox``, bucketed by edge axis and station."""

    def __init__(self, model: Any, bbox: tuple[float, float, float, float],
                 radius_m: float, half_h_m: float | None = None) -> None:
        from typehaus.resolve.floor_blocking import bearing_bays

        # Half-width in plan; the half-height in z is the same for a round run.
        self.radius_m = r = radius_m
        self.half_h_m = radius_m if half_h_m is None else half_h_m
        self.index: dict[tuple[str, int], list[tuple]] = {}
        self.risers: list[tuple] = []  # (x0, y0, x1, y1, z0, z1, tag): block and rails, grown by r
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
                x0 = min(a0, bay.box_centre - RAIL_W_M / 2.0 - r)
                x1 = max(a1, bay.box_centre + RAIL_W_M / 2.0 + r)
                name = f"{floor.tag} {bay.key}"
                self.risers.append((x0, g0 - r, x1, g1 + r, bay.z0, bay.z1, name)
                                   if bay.along_x else
                                   (g0 - r, x0, g1 + r, x1, bay.z0, bay.z1, name))
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
        r, h = self.radius_m, self.half_h_m
        for along, a0, a1, g0, g1, z0, z1, tag, key in self.index.get(
                (axis, int(station / _BUCKET_M)), ()):
            if z + h < z0 + GRAZE_M or z - h > z1 - GRAZE_M:
                continue  # under or over the joists
            if axis == along:  # in the bay, crossing the line
                if not (g0 <= station <= g1 and hi > a0 and lo < a1):
                    continue
                p_lo, p_hi = station - r, station + r
            else:  # along the line, through the block itself
                if not (a0 <= station <= a1 and hi > g0 and lo < g1):
                    continue
                p_lo, p_hi = max(lo, g0) - r, min(hi, g1) + r
            if (z + h > z1 - BOX_T_M + FIT_TOL_M or p_lo < g0 - FIT_TOL_M
                    or p_hi > g1 + FIT_TOL_M):
                return f"{tag} {key}"
        return None

    def riser_refusal(self, x: float, y: float, low: float, high: float) -> str | None:
        """``"<floor> <bay>"`` if a riser at ``(x, y)`` over ``low..high`` stands on a bay's
        block or box rails inside the joist depth, else None."""
        for x0, y0, x1, y1, z0, z1, tag in self.risers:
            if x0 < x < x1 and y0 < y < y1 and high > z0 + GRAZE_M and low < z1 - GRAZE_M:
                return tag
        return None

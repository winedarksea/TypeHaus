"""Where a profiled metal wall's flats are, in wall-axis stations (decision #142).

The panel skin folds on its layout line's datum (``board_batten.profile_mesh``), so a boot,
an inlet or a block can be placed against the same ribs the viewer draws. One datum
function serves both.
"""

from __future__ import annotations

import math
from typing import Any

#: A section point this far over the pan is a feature (rib or batten), not flat.
_FEATURE_RISE_M = 1e-4


def layout_datums(model: Any) -> dict[str, tuple[tuple[float, float], tuple[float, float]]]:
    """``wall tag -> (origin, origin + direction)``: the layout line each skin folds on."""
    return {
        member.wall_tag: (
            line.origin,
            (line.origin[0] + line.direction[0], line.origin[1] + line.direction[1]),
        )
        for line in model.layout_lines
        for member in line.members
    }


def cladding_layer(model: Any, wall: Any) -> Any | None:
    """The wall's profiled-metal cladding layer, or None."""
    from typehaus.resolve.board_batten import PANEL_PROFILES

    finishes = {m.tag: m.finish for m in model.plan.library.materials}
    return next((ly for ly in wall.layers if ly.function == "cladding" and not ly.is_cavity
                 and finishes.get(ly.material_ref) in PANEL_PROFILES), None)


def panel_profile(model: Any, wall: Any) -> Any | None:
    from typehaus.resolve.board_batten import PANEL_PROFILES

    layer = cladding_layer(model, wall)
    finishes = {m.tag: m.finish for m in model.plan.library.materials}
    return None if layer is None else PANEL_PROFILES.get(finishes.get(layer.material_ref))


def _section_flats(profile: Any, bridge_m: float) -> list[tuple[float, float]]:
    """Flats within one pitch, centred on the major feature, as (lo, hi) offsets."""
    sheet = profile.sheet_thickness_m
    points = profile.section_points_m
    flats, start = [], None
    for (s0, d0), (_s1, d1) in zip(points, points[1:], strict=False):
        flat = max(d0, d1) - sheet <= max(bridge_m, _FEATURE_RISE_M)
        if flat and start is None:
            start = s0
        elif not flat and start is not None:
            flats.append((start, s0))
            start = None
    if start is not None:
        flats.append((start, points[-1][0]))
    return flats


def panel_flats(model: Any, wall: Any, *, bridge_m: float = 0.0,
                datums: dict | None = None) -> list[tuple[float, float]]:
    """The wall's flats as (lo, hi) stations along its axis, those touching 0..length.

    ``bridge_m`` merges across features no taller than it (a minor rib a malleable boot or a
    block laps). Empty on a wall with no profiled-metal skin.
    """
    profile = panel_profile(model, wall)
    if profile is None:
        return []
    (ax, ay), (bx, by) = wall.axis
    length = math.hypot(bx - ax, by - ay)
    if length <= 0:
        return []
    axis_u = ((bx - ax) / length, (by - ay) / length)
    (ox, oy), (ex, ey) = (datums or layout_datums(model)).get(wall.tag, wall.axis)
    run = math.hypot(ex - ox, ey - oy)
    du = ((ex - ox) / run, (ey - oy) / run)
    # Axis station of datum station t: offset + sign * t.
    sign = 1.0 if du[0] * axis_u[0] + du[1] * axis_u[1] >= 0 else -1.0
    offset = (ox - ax) * axis_u[0] + (oy - ay) * axis_u[1]
    pitch = profile.pitch_m
    pieces = _section_flats(profile, bridge_m)
    lo_t, hi_t = sorted(((0 - offset) * sign, (length - offset) * sign))
    out: list[tuple[float, float]] = []
    for k in range(math.floor(lo_t / pitch) - 1, math.ceil(hi_t / pitch) + 2):
        for a, b in pieces:
            s0, s1 = sorted((offset + sign * (k * pitch + a), offset + sign * (k * pitch + b)))
            if out and abs(out[-1][1] - s0) < 1e-6:
                out[-1] = (out[-1][0], s1)  # a flat across the pitch seam
            else:
                out.append((s0, s1))
    out.sort()
    merged: list[tuple[float, float]] = []
    for s0, s1 in out:
        if merged and s0 <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s1))
        else:
            merged.append((s0, s1))
    # Not clipped at the wall's ends: the skin runs on across a collinear seam.
    return [(s0, s1) for s0, s1 in merged if s1 > 0 and s0 < length]


def flat_holding(flats: list[tuple[float, float]], lo: float, hi: float
                 ) -> tuple[float, float] | None:
    """The flat that holds the whole span ``lo..hi``, or None."""
    return next(((a, b) for a, b in flats if a - 1e-6 <= lo and hi <= b + 1e-6), None)


def flat_at(flats: list[tuple[float, float]], station: float) -> tuple[float, float] | None:
    return next(((a, b) for a, b in flats if a - 1e-6 <= station <= b + 1e-6), None)

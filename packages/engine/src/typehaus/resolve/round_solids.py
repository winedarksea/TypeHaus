"""Round pipe sections faceted into the prism-only solid IR (shared by vents/sumps/pipes).

``ResolvedSolid`` only extrudes a plan outline vertically, so a vertical pipe is a
faceted circle prism and a horizontal one is swept as bands stacked in Z whose plan
width tracks the circle. The band boundaries land on the *same* regular-polygon vertex
elevations the vertical risers are faceted at, so a jog reads as the identical n-gon
section rather than as a few square bands: an n-gon spans n/2 bands top to bottom.

Sloped segments are an accepted approximation: a near-horizontal run is drawn as one
band stack at its mean invert, a steeper run is stair-stepped into a few sub-stacks.
Checks never read these solids — slope/burial/clearance math runs on the true 3D
polyline — the bands are viewer/IFC presentation only.
"""

from __future__ import annotations

import math

from typehaus.resolve.geometry import rect_between

PIPE_FACETS = 12
PIPE_SWEEP_BANDS = PIPE_FACETS // 2
PIPE_BUNDLE_SPACING = 1.6  # centre-to-centre spacing of bundled risers, in diameters

# A segment dropping less than one diameter per band-stack length is drawn flat at its
# mean invert; steeper (but not vertical) segments stair-step into at most this many
# sub-stacks so long slopes do not read as a level line.
_MAX_SLOPE_STEPS = 3


def round_run_bands(start: tuple[float, float], end: tuple[float, float], radius: float,
                    center_z: float) -> list[tuple[list[tuple[float, float]], float, float]]:
    """Sweep a horizontal pipe as ``(outline, z0, z1)`` bands stacked in Z.

    Each band spans an equal arc of the circle and is as wide as the chord at that arc's
    midpoint, so the stack neither inscribes nor circumscribes the pipe and its
    silhouette stays centred on the true diameter.
    """
    bands = []
    for index in range(PIPE_SWEEP_BANDS):
        low_angle = math.pi * index / PIPE_SWEEP_BANDS
        high_angle = math.pi * (index + 1) / PIPE_SWEEP_BANDS
        half_width = radius * math.sin((low_angle + high_angle) / 2.0)
        bands.append((rect_between(start, end, -half_width, half_width),
                      center_z - radius * math.cos(low_angle),
                      center_z - radius * math.cos(high_angle)))
    return bands


def sloped_run_bands(
    start: tuple[float, float], end: tuple[float, float], radius: float,
    z_start: float, z_end: float,
) -> list[tuple[list[tuple[float, float]], float, float]]:
    """Bands for a (possibly) sloped horizontal segment.

    Flat or gently sloped (drop ≤ one diameter): one stack at the mean invert. Steeper:
    stair-stepped into ≤ ``_MAX_SLOPE_STEPS`` sub-stacks, each at its own mean invert.
    """
    drop = abs(z_end - z_start)
    if drop <= 2.0 * radius:
        return round_run_bands(start, end, radius, (z_start + z_end) / 2.0)
    steps = min(_MAX_SLOPE_STEPS, max(2, int(math.ceil(drop / (2.0 * radius)))))
    bands: list[tuple[list[tuple[float, float]], float, float]] = []
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        a = (start[0] + (end[0] - start[0]) * t0, start[1] + (end[1] - start[1]) * t0)
        b = (start[0] + (end[0] - start[0]) * t1, start[1] + (end[1] - start[1]) * t1)
        zc = z_start + (z_end - z_start) * (t0 + t1) / 2.0
        bands.extend(round_run_bands(a, b, radius, zc))
    return bands

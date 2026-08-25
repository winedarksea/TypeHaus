"""Round pipe sections faceted into the prism-only solid IR — **the legacy path**.

``ResolvedSolid`` only extruded a plan outline vertically, so a vertical pipe was a faceted
circle prism and a horizontal one was swept as bands stacked in Z whose plan width tracks
the circle. The band boundaries land on the *same* regular-polygon vertex elevations the
vertical risers are faceted at, so a jog reads as the identical n-gon section rather than as
a few square bands: an n-gon spans n/2 bands top to bottom.

Sloped runs no longer come through here at all. ``sloped_run_bands`` stair-stepped one into
at most three level stacks and its own docstring called that "an accepted approximation";
:mod:`typehaus.resolve.sweep` now carries a run as the single mitred tube it is, and
``resolve/mep.py`` builds one ``SolidSweep`` per pipe or raceway. What is left is the
callers whose geometry genuinely is level and axis-aligned — sleeve bores, drain tile,
drywell bores, vent risers — for which a band stack is exact and a sweep would be ceremony.

Checks never read these solids — slope/burial/clearance math runs on the true 3D polyline —
the bands are viewer/IFC presentation only.
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
                    center_z: float, sweep_bands: int = PIPE_SWEEP_BANDS,
                    ) -> list[tuple[list[tuple[float, float]], float, float]]:
    """Sweep a horizontal pipe as ``(outline, z0, z1)`` bands stacked in Z.

    Each band spans an equal arc of the circle and is as wide as the chord at that arc's
    midpoint, so the stack neither inscribes nor circumscribes the pipe and its
    silhouette stays centred on the true diameter.

    ``sweep_bands`` is the caller's facet budget. A drain stack is one run of one pipe and
    can afford the 12-gon; a raked handrail is *sixty* stacks — one per diameter of fall —
    and pays that budget sixty times over for a 1-1/2" bar, so it asks for fewer. The
    default is unchanged, so every existing caller is untouched.
    """
    bands = []
    for index in range(sweep_bands):
        low_angle = math.pi * index / sweep_bands
        high_angle = math.pi * (index + 1) / sweep_bands
        half_width = radius * math.sin((low_angle + high_angle) / 2.0)
        bands.append((rect_between(start, end, -half_width, half_width),
                      center_z - radius * math.cos(low_angle),
                      center_z - radius * math.cos(high_angle)))
    return bands

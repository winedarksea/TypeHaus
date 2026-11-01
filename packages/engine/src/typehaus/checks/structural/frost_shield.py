"""Does drawn horizontal frost insulation actually abut the footing it is credited to?

IRC R403.3 Figure R403.3(3): the wing is dimension A..C of insulation laid against the
foundation, so it protects the footing *beside it* and only along the length it runs.
``structural.frost_depth`` used to credit any wing within a frost depth (42") of the footing
polygon, which let a strip 32" past a wing's end ride on it.

The rule here is per station along the footing's long axis: every station the open
excavation reaches (cross-section within a frost depth of a dug floor) must have a wing
within ``SHIELD_GAP_M`` of its cross-section. A wing a bedding course and an isolation
board away still abuts; one that stops short of the reached length leaves a bare run.
"""

from __future__ import annotations

import math

#: Largest wing-to-footing gap that still counts as abutting: a 4" bedding course, a 2"
#: isolation board and 2" of tolerance.
SHIELD_GAP_M = 8 * 0.0254
_STEP_M = 0.0254  # station spacing along the footing


def _stations(footing):
    """Cross-section segments of ``footing`` every ``_STEP_M`` along its long axis."""
    from shapely.geometry import LineString

    ring = list(footing.minimum_rotated_rectangle.exterior.coords)[:4]
    a, b, c = ring[0], ring[1], ring[2]
    len_ab = math.dist(a, b)
    len_bc = math.dist(b, c)
    # Long axis runs along the longer edge; cross-sections run along the shorter one.
    (p, q), (r, s) = ((a, b), (b, c)) if len_ab >= len_bc else ((b, c), (b, a))
    length = math.dist(p, q)
    ux, uy = (q[0] - p[0]) / length, (q[1] - p[1]) / length
    across = (s[0] - r[0], s[1] - r[1])
    steps = max(1, int(length / _STEP_M))
    for i in range(steps + 1):
        t = min(length, i * _STEP_M)
        x, y = p[0] + ux * t, p[1] + uy * t
        yield LineString([(x, y), (x + across[0], y + across[1])])


def unshielded_length_m(footing, floors, protection, reach_m: float,
                        gap_m: float = SHIELD_GAP_M) -> tuple[float, list[str]]:
    """``(length of reached footing no wing abuts, tags of wings that do abut)``.

    ``floors`` is ``open_excavation_floors`` (``(tag, polygon, z)``), ``protection`` the
    ``(tag, polygon)`` wings. A footing no floor reaches is 0.0 bare.
    """
    if footing.is_empty or footing.area <= 1e-9:
        return 0.0, []
    reached_zone = [polygon for _tag, polygon, _z in floors
                    if footing.distance(polygon) <= reach_m + 1e-9]
    if not reached_zone:
        return 0.0, []
    near = [(tag, polygon) for tag, polygon in protection if footing.distance(polygon) <= gap_m]
    bare = 0
    used: set[str] = set()
    for section in _stations(footing):
        if all(section.distance(zone) > reach_m + 1e-9 for zone in reached_zone):
            continue
        hit = [tag for tag, polygon in near
               if section.distance(polygon) <= gap_m + 1e-9]
        if hit:
            used.update(hit)
        else:
            bare += 1
    return bare * _STEP_M, sorted(used)


def shielding_wings(footing, floors, protection, reach_m: float) -> tuple[float, list[str]]:
    """``(bare length, wings that credit the footing)``: none credit it if any run is bare."""
    if footing is None:
        return 0.0, []
    bare, used = unshielded_length_m(footing, floors, protection, reach_m)
    return bare, ([] if bare > 2 * _STEP_M else used)

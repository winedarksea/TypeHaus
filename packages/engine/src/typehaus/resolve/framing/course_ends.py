"""Where a horizontal furring course ends: at a seam, a butt joint, or half a board back.

At an L the FURRING band is butt-cut like sheathing (``resolve/sheathing_corner.py``): the
``sheathing_through`` wall's band runs to the corner's outer face and the other's stops on
its back. A course there runs to its band's end, past the wall's axis. Anywhere else a
non-continued end is held half a board back, so two square-cut courses meeting on a mitre
(or a band edge nothing else reaches) abut rather than lap.
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.geometry import add, normal, scale

_SQUARE_TOL_M = 1e-4  # a butt-cut end reads the same station at both faces
_FACE_INSET = 0.45  # read the faces just inside the band, clear of its edge vertices


def l_corner_ends(model: Any) -> frozenset[tuple[str, str]]:
    """Every ``(wall_tag, endpoint)`` that is an incident of an L junction."""
    return frozenset((item.wall_tag, item.endpoint)
                     for junction in model.junctions if junction.kind == "l"
                     for item in junction.incidents)


def course_extent(layer: Any, p0: tuple[float, float], direction: tuple[float, float],
                  axis_len: float, plan_face: float,
                  continuations: tuple[str | None, str | None],
                  butted: tuple[bool, bool]) -> tuple[float, float]:
    """``(first, last)`` station of a course in ``layer``'s band.

    ``butted`` marks an end at an L. It takes the UNCLAMPED band end only when the band is
    actually square there; a mitre ``butt_layers`` declined to re-cut keeps the hold-back.
    """
    first, last = band_extent(layer.polygon, p0, direction, axis_len)
    free_lo, free_hi = band_extent(layer.polygon, p0, direction, axis_len, clamp=False)
    across = normal(direction)
    inset = layer.thickness_m * _FACE_INSET
    faces = [band_extent(layer.polygon, add(p0, scale(across, side * inset)), direction,
                         axis_len, clamp=False) for side in (-1.0, 1.0)]
    square_lo = abs(faces[0][0] - faces[1][0]) < _SQUARE_TOL_M
    square_hi = abs(faces[0][1] - faces[1][1]) < _SQUARE_TOL_M
    start_cont, end_cont = continuations
    if butted[0] and square_lo and not start_cont:
        first = free_lo
    elif not start_cont:
        first += plan_face / 2.0
    if butted[1] and square_hi and not end_cont:
        last = free_hi
    elif not end_cont:
        last -= plan_face / 2.0
    return first, last


def block_span(seg_lo: float, seg_hi: float, first: float, last: float, half: float,
               continuations: tuple[str | None, str | None]) -> tuple[float, float]:
    """A course segment clipped to where its blocks may stand.

    Half a board inside the wall's clamped band extent at a non-continued end — where the
    course stopped before L ends were butted — so a course running on past the axis over
    foam keeps its end block over this wall's corner post. A no-op at every other end.
    """
    start_cont, end_cont = continuations
    return (seg_lo if start_cont else max(seg_lo, first + half),
            seg_hi if end_cont else min(seg_hi, last - half))


def band_extent(polygon, p0, direction, axis_len: float,
                clamp: bool = True) -> tuple[float, float]:
    """The band's first/last station *on its own centreline*, clamped to the wall.

    ``clamp=False`` returns the band's own ends, past the axis where a butt-cut L runs on.

    The resolved layer polygon is mitred at every junction, so this is where corner
    interference is actually resolved: the strapping stops where its band stops. On W-B-CS
    the liner band gives up its last foot to the wall it tees into, and the battens stop
    there rather than running through the neighbour's liner.

    Measured by clipping the centreline against the polygon rather than by projecting its
    vertices, because a mitre's far tip is a *corner* of the band, not a station the
    centreline ever reaches. Projecting vertices ran the sauna's two liner courses a
    half-board past each other, straight through the mitre they are cut to. A polygon the
    centreline somehow misses falls back to the projection — a short band is better than
    none.
    """
    across = normal(direction)
    offsets = [(x - p0[0]) * across[0] + (y - p0[1]) * across[1] for x, y in polygon]
    stations = [(x - p0[0]) * direction[0] + (y - p0[1]) * direction[1]
                for x, y in polygon]
    crossings: list[float] = []
    for i, offset in enumerate(offsets):
        j = (i + 1) % len(offsets)
        if abs(offset) < 1e-12:
            crossings.append(stations[i])
        elif offset * offsets[j] < 0.0:
            fraction = offset / (offset - offsets[j])
            crossings.append(stations[i] + (stations[j] - stations[i]) * fraction)
    if len(crossings) < 2:
        crossings = stations
    if not clamp:
        return min(crossings), max(crossings)
    return max(0.0, min(crossings)), min(axis_len, max(crossings))

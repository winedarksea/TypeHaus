"""A run lying IN a ceiling board, for ``mep.run_in_finished_volume``.

The air test there asks whether a run's bottom is under the finished face, and the
headroom test whether it is under a head line. Neither sees a run whose body sits in the
board's own thickness: above the face, below the board's top. That run is buried in the
gypsum. Exposed services (``Room.exposed_services``) hang below the board, and concealed
ones run above it. Nothing may run inside it.

"The board" is every solid layer of the ceiling stack: a framed layer (one with a
``FramingSpec``: strips, rips, a service cavity) is a cavity a run may use, and every other
layer (gypsum, shiplap, rigid foam, a membrane) is not. Paint is under the tolerance.

Every flat ceiling with a lining is graded, mechanical rooms included. A riser passing
straight through is a penetration, not a run in the board, so it is skipped. Sloped
(``FollowRoof``) linings are not graded here.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, MultiLineString, Point, Polygon

from typehaus.checks.mep.routing import VOID_BUFFER_M
from typehaus.checks.mep.routing_geometry import M_TO_FT, wall_cover
from typehaus.quantities import M_PER_IN

#: Overlap below this is a drawing tolerance, not a pipe in the board.
BOARD_TOLERANCE_M = M_PER_IN / 16.0


def solid_bands(ceiling: Any) -> list[tuple[float, float, str]]:
    """``(z low, z high, materials)`` for each run of solid layers, face first."""
    bands: list[tuple[float, float, str]] = []
    z = ceiling.z0_m
    for layer in ceiling.layers:
        thickness = layer.thickness.meters
        if thickness < BOARD_TOLERANCE_M:
            continue
        if layer.framing is None:
            if bands and abs(bands[-1][1] - z) < 1e-9:
                lo, _, names = bands[-1]
                bands[-1] = (lo, z + thickness, f"{names} + {layer.material_ref}")
            else:
                bands.append((z, z + thickness, layer.material_ref))
        z += thickness
    return bands


def board_rows(ctx: Any, runs: list, vertical_radii: dict[str, float],
               min_exposure_ft: float) -> dict[tuple[str, str], tuple[float, float, str]]:
    """``{(run, room): (length ft, depth into a board in, that board's description)}``."""
    from typehaus.checks.mep.routing_ceiling import _air_interval
    from typehaus.resolve.riser_cover import soffit_cover

    boards = []
    for ceiling in ctx.model.ceilings:
        if ceiling.z0_m is None or ceiling.z1_m is None or len(ceiling.outline) < 3:
            continue
        outline = Polygon(ceiling.outline)
        if outline.is_valid and not outline.is_empty:
            boards.extend((ceiling, outline, band) for band in solid_bands(ceiling)
                          if band[1] - band[0] > 2 * BOARD_TOLERANCE_M)
    covers: dict[str, Any] = {}
    found: dict[tuple[str, str], tuple[float, float, str]] = {}
    for _kind, tag, path, z in runs:
        if len(path) < 2 or len(z) != len(path):
            continue
        radius = vertical_radii.get(tag, 0.0)
        for index in range(len(path) - 1):
            segment = LineString([path[index], path[index + 1]])
            if segment.length <= VOID_BUFFER_M:
                continue  # a riser through the board is a penetration
            za, zb = z[index], z[index + 1]
            for ceiling, outline, (z0, z1, names) in boards:
                if min(za, zb) - radius >= z1 or max(za, zb) + radius <= z0:
                    continue
                piece = outline.intersection(segment)
                if piece.is_empty or piece.length <= 0:
                    continue
                if ceiling.storey not in covers:
                    walls = wall_cover(ctx, {ceiling.storey})
                    soffits = soffit_cover(ctx.model, ceiling.storey)
                    covers[ceiling.storey] = (walls if soffits is None else soffits
                                              if walls is None else walls.union(soffits))
                if covers[ceiling.storey] is not None:
                    piece = piece.difference(covers[ceiling.storey])
                for part in (piece.geoms if isinstance(piece, MultiLineString) else [piece]):
                    if part.is_empty or part.length <= 0:
                        continue
                    ts = sorted(segment.project(Point(xy)) / segment.length
                                for xy in part.coords)
                    band = _air_interval(za, zb, radius, z0 + BOARD_TOLERANCE_M,
                                         z1, z1, BOARD_TOLERANCE_M)
                    if band is None:
                        continue
                    lo, hi = max(ts[0], band[0]), min(ts[-1], band[1])
                    if hi <= lo:
                        continue
                    depth = max(z1 - max(za + (zb - za) * t - radius, z0) for t in (lo, hi))
                    key = (tag, ceiling.room_ref)
                    length, worst, board = found.get(key, (0.0, 0.0, ""))
                    if depth / M_PER_IN > worst:
                        board = f"{(z1 - z0) / M_PER_IN:.2f}\" {names}"
                    found[key] = (length + (hi - lo) * segment.length * M_TO_FT,
                                  max(worst, depth / M_PER_IN), board)
    return {key: row for key, row in found.items() if row[0] >= min_exposure_ft}

"""A run lying IN a ceiling board, for ``mep.run_in_finished_volume``.

The air test there asks whether a run's bottom is under the finished face, and the
headroom test whether it is under a head line. Neither sees a run whose body sits in the
board's own thickness: above the face, below the board's top. That run is buried in the
gypsum. Exposed services (``Room.exposed_services``) hang below the board, and concealed
ones run above it. Nothing may run inside it.

"The board" is every solid layer of the ceiling stack: a framed layer (one with a
``FramingSpec``: strips, rips, a service cavity) is a cavity a run may use, and every other
layer (gypsum, shiplap, rigid foam, a membrane) is not. Paint is under the tolerance.

Every ceiling with a lining is graded, mechanical rooms included. A riser passing
straight through is a penetration, not a run in the board, so it is skipped. A sloped
(``FollowRoof``) lining is graded in the frame of its face: the run's height less the
plane's, against bands scaled plumb by the roof's slope factor, down into the eave too.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, MultiLineString, Point, Polygon

from typehaus.checks.mep.routing import VOID_BUFFER_M
from typehaus.checks.mep.routing_geometry import M_TO_FT, wall_cover
from typehaus.quantities import M_PER_IN

#: Overlap below this is a drawing tolerance, not a pipe in the board.
BOARD_TOLERANCE_M = M_PER_IN / 16.0


def _bands_from(ceiling: Any, base: float, scale: float = 1.0) -> list[tuple[float, float, str]]:
    """``(z low, z high, materials)`` for each run of solid layers from ``base``, face first."""
    bands: list[tuple[float, float, str]] = []
    z = base
    for layer in ceiling.layers:
        thickness = layer.thickness.meters
        if thickness < BOARD_TOLERANCE_M:
            continue
        thickness *= scale
        if layer.framing is None:
            if bands and abs(bands[-1][1] - z) < 1e-9:
                lo, _, names = bands[-1]
                bands[-1] = (lo, z + thickness, f"{names} + {layer.material_ref}")
            else:
                bands.append((z, z + thickness, layer.material_ref))
        z += thickness
    return bands


def solid_bands(ceiling: Any) -> list[tuple[float, float, str]]:
    """A flat ceiling's solid bands, at their elevations."""
    return _bands_from(ceiling, ceiling.z0_m)


def _record(found: dict, key: tuple[str, str], seg: LineString, part: Any, za: float,
            zb: float, radius: float, band_z: tuple[float, float, str]) -> None:
    """Add the part of ``seg`` buried in the band (heights in the band's own frame)."""
    from typehaus.checks.mep.routing_ceiling import _air_interval

    z0, z1, names = band_z
    ts = sorted(seg.project(Point(xy)) / seg.length for xy in part.coords)
    band = _air_interval(za, zb, radius, z0 + BOARD_TOLERANCE_M, z1, z1, BOARD_TOLERANCE_M)
    if band is None:
        return
    lo, hi = max(ts[0], band[0]), min(ts[-1], band[1])
    if hi <= lo:
        return
    depth = max(z1 - max(za + (zb - za) * t - radius, z0) for t in (lo, hi))
    length, worst, board = found.get(key, (0.0, 0.0, ""))
    if depth / M_PER_IN > worst:
        board = f"{(z1 - z0) / M_PER_IN:.2f}\" {names}"
    found[key] = (length + (hi - lo) * seg.length * M_TO_FT, max(worst, depth / M_PER_IN),
                  board)


def _parts(piece: Any) -> list:
    return [p for p in (piece.geoms if isinstance(piece, MultiLineString) else [piece])
            if not p.is_empty and p.length > 0]


def board_rows(ctx: Any, runs: list, vertical_radii: dict[str, float],
               min_exposure_ft: float) -> dict[tuple[str, str], tuple[float, float, str]]:
    """``{(run, room): (length ft, depth into a board in, that board's description)}``."""
    from typehaus.checks.mep.routing_sloped import sloped_plane
    from typehaus.resolve.riser_cover import soffit_cover
    from typehaus.resolve.roof_geometry import roof_slope_factor

    boards = []  # (ceiling, outline, plane or None, band)
    for ceiling in ctx.model.ceilings:
        if len(ceiling.outline) < 3:
            continue
        outline = Polygon(ceiling.outline)
        if not outline.is_valid or outline.is_empty:
            continue
        if ceiling.z0_m is not None and ceiling.z1_m is not None:
            plane, bands = None, solid_bands(ceiling)
        else:
            plane = sloped_plane(ctx.model, ctx.plan, ceiling)
            if plane is None:
                continue
            bands = _bands_from(ceiling, 0.0, roof_slope_factor(plane.roof))
        boards.extend((ceiling, outline, plane, band) for band in bands
                      if band[1] - band[0] > 2 * BOARD_TOLERANCE_M)
    covers: dict[str, Any] = {}

    def cover(storey: str) -> Any:
        if storey not in covers:
            walls = wall_cover(ctx, {storey})
            soffits = soffit_cover(ctx.model, storey)
            covers[storey] = (walls if soffits is None else soffits
                              if walls is None else walls.union(soffits))
        return covers[storey]

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
            for ceiling, outline, plane, band in boards:
                key = (tag, ceiling.room_ref)
                if plane is None:
                    pieces = [(segment, za, zb)]
                else:
                    pieces = [(seg, pa - fa, pb - fb) for _p0, pa, pb, seg, fa, fb
                              in plane.pieces(path[index], path[index + 1], za, zb)]
                for seg, sa, sb in pieces:
                    if min(sa, sb) - radius >= band[1] or max(sa, sb) + radius <= band[0]:
                        continue
                    piece = outline.intersection(seg)
                    if piece.is_empty or piece.length <= 0:
                        continue
                    hidden = cover(ceiling.storey)
                    if hidden is not None:
                        piece = piece.difference(hidden)
                    for part in _parts(piece):
                        _record(found, key, seg, part, sa, sb, radius, band)
    return {key: row for key, row in found.items() if row[0] >= min_exposure_ft}

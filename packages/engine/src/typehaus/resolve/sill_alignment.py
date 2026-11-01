"""A sill wider than its stud wall: flush on the OUTSIDE face, the surplus on the inside.

``FramingSpec.sill_member`` (a 2x8 on a 2x6 wall) is set so the sill and the stud band share
an outside plane (the sheathing/EPS plane the wall is built to), which is what puts most of
the board on the ICF core. The 1 3/4" ledge lands inside, under the curb-cap flashing.
"""

from __future__ import annotations

from typehaus.resolve.geometry import normal, unit
from typehaus.resolve.model import ResolvedWall

_IN = 0.0254


def _offsets(rw: ResolvedWall, polygon) -> tuple[float, float]:
    (x0, y0), (x1, y1) = rw.axis
    n = normal(unit((x1 - x0, y1 - y0)))
    offs = [(p[0] - x0) * n[0] + (p[1] - y0) * n[1] for p in polygon]
    return min(offs), max(offs)


def outward_sign(rw: ResolvedWall) -> float:
    """+1 when the wall's outside lies along the axis' left normal, -1 on the right."""
    layers = [layer for layer in rw.layers if layer.polygon and layer.thickness_m > 0]
    if len(layers) < 2:
        return 1.0
    inner, outer = (sum(_offsets(rw, layer.polygon)) for layer in (layers[0], layers[-1]))
    return 1.0 if outer >= inner else -1.0


def sill_shift_m(rw: ResolvedWall, band_polygon, sill_width_m: float) -> float:
    """Signed offset (left normal) of the sill's centre from the stud band's centre."""
    lo, hi = _offsets(rw, band_polygon)
    half = (hi - lo) / 2.0
    return outward_sign(rw) * (half - sill_width_m / 2.0)


__all__ = ["outward_sign", "sill_shift_m"]

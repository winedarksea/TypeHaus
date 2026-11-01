"""Where a sill plate sits on the concrete under it (IRC R403.1.6), as cross-wall intervals.

Offsets run along the left normal of the sill run, so the sill, the stud band and the
concrete core compare as 1-D intervals. :func:`grade` is pure; the check, the anchor stations
and the S-103 note all read :func:`sill_bearing`, so the drawing and the verdict agree.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.hardware.plan_geometry import centerline_endpoints
from typehaus.resolve.model import ResolvedConstructionReturn, ResolvedModel
from typehaus.resolve.sill_alignment import outward_sign

_IN = 0.0254
#: Share of the sill's width that must sit on the concrete. A pass-through of the owner's
#: two-thirds rule (geometry review C3-E8), not a code number.
MIN_BEARING_FRACTION = 2.0 / 3.0
#: Bolt centre to the free face of the concrete core. ACI 318-19 20.5.1.3 cover for a
#: No. 5-and-smaller bar in contact with ground/weather, read across to a 1/2" cast-in bolt.
#: ACI 318-19 17.7.2's 6 d_a (3") for a torqued anchor would leave NO band on a 6" core
#: (the plate's middle third ends 0.04" short of it): the ICF maker's anchor detail governs.
MIN_BOLT_EDGE_M = 1.5 * _IN
_EPS = 1e-6


@dataclass(frozen=True)
class SillBearing:
    """Intervals in inches measured inward from the sill's OUTSIDE edge."""

    sill_in: float
    stud_in: float
    on_core_in: float
    core: tuple[float, float]
    third: tuple[float, float]
    band: tuple[float, float] | None
    sign: float  # +1 when the wall's outside is on the run's left normal

    @property
    def fraction(self) -> float:
        return self.on_core_in / self.sill_in

    @property
    def nominal_in(self) -> float | None:
        return None if self.band is None else sum(self.band) / 2.0


def grade(sill: tuple[float, float], core: tuple[float, float],
          edge_in: float = MIN_BOLT_EDGE_M / _IN):
    """``(width, on_core, middle third, bolt band | None)``, inches inward from the outside edge."""
    width = sill[1] - sill[0]
    lo, hi = max(sill[0], core[0]), min(sill[1], core[1])
    on_core = max(0.0, hi - lo)
    third = (sill[0] + width / 3.0, sill[0] + 2.0 * width / 3.0)
    band_lo, band_hi = max(third[0], core[0] + edge_in), min(third[1], core[1] - edge_in)
    band = (band_lo, band_hi) if band_lo <= band_hi + _EPS else None
    return width, on_core, third, band


def _offsets(points, n, origin) -> tuple[float, float]:
    offs = [(p[0] - origin[0]) * n[0] + (p[1] - origin[1]) * n[1] for p in points]
    return min(offs), max(offs)


def sill_bearing(model: ResolvedModel, ret: ResolvedConstructionReturn) -> SillBearing | None:
    """The cross-section of a framed-wall sill on its concrete wall; None where it has none."""
    walls = {w.tag: w for w in model.walls}
    if len(ret.element_tags) < 2:
        return None
    lower, upper = walls.get(ret.element_tags[0]), walls.get(ret.element_tags[1])
    if lower is None or upper is None:
        return None
    core_layer = next((layer for layer in lower.layers
                       if layer.material_ref == "concrete" and layer.polygon), None)
    stud_layer = next((layer for layer in upper.layers
                       if layer.function == "structure" and layer.polygon), None)
    if core_layer is None or stud_layer is None:
        return None
    start, end = centerline_endpoints(list(ret.outline))
    run = math.dist(start, end)
    d = ((end[0] - start[0]) / run, (end[1] - start[1]) / run)
    n = (-d[1], d[0])
    sill = _offsets(ret.outline, n, start)
    core = _offsets(core_layer.polygon, n, start)
    stud = _offsets(stud_layer.polygon, n, start)
    # Flip so offsets run inward from the outside edge.
    out = outward_sign(upper)
    if out > 0:
        def inward(iv):
            return (sill[1] - iv[1], sill[1] - iv[0])
    else:
        def inward(iv):
            return (iv[0] - sill[0], iv[1] - sill[0])
    sill_i, core_i, stud_i = (tuple(v / _IN for v in inward(iv)) for iv in (sill, core, stud))
    width, on_core, third, band = grade(sill_i, core_i)
    return SillBearing(sill_in=width, stud_in=stud_i[1] - stud_i[0], on_core_in=on_core,
                       core=core_i, third=third, band=band, sign=out)


def band_centre_ends(model: ResolvedModel, ret) -> tuple:
    """The sill's centreline ends moved onto the STUD band's centre.

    A sill wider than its studs is set flush outside, so its own centreline sits off the
    band's. Corner matching (derived STHDs) reads the band line, as it did for a sill the
    stud's width.
    """
    start, end = centerline_endpoints(list(ret.outline))
    walls = {w.tag: w for w in model.walls}
    upper = walls.get(ret.element_tags[1]) if len(ret.element_tags) > 1 else None
    layer = next((lyr for lyr in upper.layers if lyr.function == "structure" and lyr.polygon),
                 None) if upper is not None else None
    run = math.dist(start, end)
    if layer is None or run <= 0.0:
        return start, end
    n = (-(end[1] - start[1]) / run, (end[0] - start[0]) / run)
    sill_lo, sill_hi = _offsets(ret.outline, n, start)
    lo, hi = _offsets(layer.polygon, n, start)
    shift = (lo + hi) / 2.0 - (sill_lo + sill_hi) / 2.0
    return ((start[0] + n[0] * shift, start[1] + n[1] * shift),
            (end[0] + n[0] * shift, end[1] + n[1] * shift))


def bolt_offset_m(model: ResolvedModel, ret) -> float:
    """Signed left-normal offset from the sill's centreline to the bolt line; 0 if unknown."""
    sb = sill_bearing(model, ret)
    if sb is None or sb.nominal_in is None:
        return 0.0
    inward = sb.nominal_in - sb.sill_in / 2.0  # + toward the inside edge
    return -sb.sign * inward * _IN

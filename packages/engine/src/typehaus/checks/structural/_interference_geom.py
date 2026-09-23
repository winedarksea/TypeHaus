"""Shared readings for the interference checks: candidates, plan axes, the rafter seat.

``interference.py`` (framing vs framing), ``masonry_interference.py`` (framing vs a concrete
or masonry wall layer) and ``post_base_interference.py`` (framing vs a post base) all read
members through :func:`framing_candidates`, so the three cannot disagree about what a
member occupies.
"""

from __future__ import annotations

import math

from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.sweep import straight_sweep_band

# Minimum shared plan area (m²) for a real interference. A face/side abutment
# intersects in a zero-area line; this clears it with margin.
_TOL_AREA = 1e-4


class _Candidate:
    __slots__ = ("label", "poly", "z_lo", "z_hi", "seg", "kind", "parent",
                 "zlo0", "zhi0", "zlo1", "zhi1")

    def __init__(self, label, poly, z_lo, z_hi, seg, kind, parent=None,
                 zends=None):
        self.label = label
        self.poly = poly
        self.z_lo = z_lo  # min z over the whole member (bounding box)
        self.z_hi = z_hi  # max z over the whole member (bounding box)
        # (p0, p1) plan-frame axis (degenerate point for a vertical member/column).
        self.seg = seg
        self.kind = kind  # member/solid category: "rim", "column", "joist", "beam", …
        # Owning element uid (wall/roof); distinguishes a same-element joint (a real
        # elevation bug) from a cross-element lap/bearing (intended joinery).
        self.parent = parent
        # Per-endpoint z-band (bottom, top) at seg[0] and seg[1]. A sloped member (rafter,
        # raked plate, ridge) rises along its axis; carrying both ends lets the check test
        # the z-band *at the shared plan region* instead of the full-slope bounding box —
        # otherwise a raked top plate reads as a wall-tall box and clips every stud below.
        (self.zlo0, self.zhi0, self.zlo1, self.zhi1) = (
            zends if zends is not None else (z_lo, z_hi, z_lo, z_hi))

    def zband_at(self, point) -> tuple[float, float]:
        """The member's (z_lo, z_hi) interpolated to the plan ``point`` along its axis."""
        (ax, ay), (bx, by) = self.seg
        dx, dy = bx - ax, by - ay
        run2 = dx * dx + dy * dy
        if run2 < 1e-18:
            return self.zlo0, self.zhi0
        t = max(0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy) / run2))
        return (self.zlo0 + (self.zlo1 - self.zlo0) * t,
                self.zhi0 + (self.zhi1 - self.zhi0) * t)


def _swept_axis(solid):
    """A tilted member's plan axis and its z-band AT EACH END, or ``None``.

    ``resolve/sweep.straight_sweep_band`` is the reader; without it a 2" drainage tilt turns
    an 11 7/8" beam into a 14 1/2" box and every joist bearing on it reads as a clash.
    """
    band = straight_sweep_band(solid)
    if band is None:
        return None
    seg, depth, soffit0, soffit1 = band
    return seg, (soffit0, soffit0 + depth, soffit1, soffit1 + depth)


def _point_on_segment(pt, a, b, tol: float) -> bool:
    """True if plan point ``pt`` lies within ``tol`` of segment ``a``->``b``."""
    px, py = pt
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    run2 = dx * dx + dy * dy
    if run2 < 1e-18:
        return math.hypot(px - ax, py - ay) <= tol
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / run2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)) <= tol


def _solid_segment(solid):
    """Plan-frame axis of a beam/column solid: a beam outline's short-end midpoints, or a
    column's centroid twice (a point)."""
    o = solid.outline
    if solid.category == "beam" and len(o) == 4:
        p0 = ((o[0][0] + o[3][0]) / 2.0, (o[0][1] + o[3][1]) / 2.0)
        p1 = ((o[1][0] + o[2][0]) / 2.0, (o[1][1] + o[2][1]) / 2.0)
        return (p0, p1)
    cx = sum(x for x, _ in o) / len(o)
    cy = sum(y for _, y in o) / len(o)
    return ((cx, cy), (cx, cy))


def framing_candidates(model) -> list[_Candidate]:
    """Every framed member, plus the ``column``/``beam`` solids, as candidates.

    Slabs/footings/pads are excluded: beams legitimately bear into concrete and joists frame
    under deck slabs (``concrete_interference.py`` grades pours).
    """
    from shapely.geometry import Polygon

    out: list[_Candidate] = []
    for member in model.all_members():
        ring, z_lo, z_hi = member_footprint(member)
        poly = Polygon(ring)
        if poly.is_valid and poly.area > _TOL_AREA:
            z0e = member.z0_m if member.z0_end_m is None else member.z0_end_m
            z1e = member.z1_m if member.z1_end_m is None else member.z1_end_m
            zends = (min(member.z0_m, member.z1_m), max(member.z0_m, member.z1_m),
                     min(z0e, z1e), max(z0e, z1e))
            out.append(_Candidate(
                f"{member.parent_uid}:{member.child_key}", poly, z_lo, z_hi,
                seg=(member.p0, member.p1), kind=member.category,
                parent=member.parent_uid, zends=zends))
    for solid in model.solids:
        if solid.category not in ("column", "beam"):
            continue
        poly = Polygon(solid.outline)
        if poly.is_valid and poly.area > _TOL_AREA:
            seg, zends = _solid_segment(solid), None
            swept = _swept_axis(solid)
            if swept is not None:
                seg, zends = swept
            out.append(_Candidate(solid.tag, poly, solid.z0_m, solid.z1_m,
                                  seg=seg, kind=solid.category,
                                  parent=solid.tag, zends=zends))
    return out


def plan_angle_deg(seg_a, seg_b) -> float | None:
    """Acute plan angle between two segments, or ``None`` if either is a point."""
    (ax, ay), (bx, by) = seg_a
    (cx, cy), (dx, dy) = seg_b
    u, v = (bx - ax, by - ay), (dx - cx, dy - cy)
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu < 1e-9 or nv < 1e-9:
        return None
    cos = abs(u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    return math.degrees(math.acos(min(1.0, cos)))

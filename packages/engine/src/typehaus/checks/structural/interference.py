"""Model-wide framing interference check (→ 12 §checks/structural).

A regression guard, not an engineering calc: two wood members that share plan area
*and* interpenetrate vertically are almost always an elevation-arithmetic bug (a beam
topped at the joist datum, a post left too tall), not an intended joint. A proper
bearing/stacking joint has ~zero z-overlap; a side/face abutment has ~zero shared
area. Requiring *both* a real z-overlap and a real shared area is the core
false-positive defense.

WARN, not ERROR: it is a new geometric heuristic, matches the STRUCTURAL-tier
"advisory, not engineering" convention, and must not break ``haus build``/CI on a
tight-but-legal joint. Suppress per-check via ``Preferences.suppressed``.
"""

from __future__ import annotations

import math

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint

# Minimum shared plan area (m²) for a real interference. A face/side abutment
# intersects in a zero-area line; this clears it with margin.
_TOL_AREA = 1e-4


class _Candidate:
    __slots__ = ("label", "poly", "z_lo", "z_hi", "seg", "kind")

    def __init__(self, label, poly, z_lo, z_hi, seg, kind):
        self.label = label
        self.poly = poly
        self.z_lo = z_lo
        self.z_hi = z_hi
        # (p0, p1) plan-frame axis (degenerate point for a vertical member/column).
        self.seg = seg
        self.kind = kind  # member/solid category: "rim", "column", "joist", "beam", …


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
    """Plan-frame axis of a beam/column solid, so a post bearing at a beam end (or a
    beam seated on a post) reads as a butt joint. A beam outline is the 4 corners
    [p0+n, p1+n, p1-n, p0-n]; its centerline endpoints are the midpoints of the short
    ends. A column is a point (its centroid)."""
    o = solid.outline
    if solid.category == "beam" and len(o) == 4:
        p0 = ((o[0][0] + o[3][0]) / 2.0, (o[0][1] + o[3][1]) / 2.0)
        p1 = ((o[1][0] + o[2][0]) / 2.0, (o[1][1] + o[2][1]) / 2.0)
        return (p0, p1)
    cx = sum(x for x, _ in o) / len(o)
    cy = sum(y for _, y in o) / len(o)
    return ((cx, cy), (cx, cy))


def _butt_joint(a: _Candidate, b: _Candidate, tol: float) -> bool:
    """Intended joinery: an endpoint of one member lands on the other's axis.

    Gated by kind so it clears *intended* coplanar/bearing joints without masking the
    bug this check exists for. A joist bearing on a beam is *also* geometrically an
    endpoint-on-axis, but its elevation is what we police — so a beam is never a valid
    partner here. Cleared cases: a joist end butting a rim board (coplanar by design),
    and a post/column seated under a beam (the vertical bearing, incl. the intended 2"
    rear-row drainage poke)."""
    if not (a.kind == "rim" or b.kind == "rim"
            or a.kind == "column" or b.kind == "column"):
        return False
    for pt in a.seg:
        if _point_on_segment(pt, b.seg[0], b.seg[1], tol):
            return True
    for pt in b.seg:
        if _point_on_segment(pt, a.seg[0], a.seg[1], tol):
            return True
    return False


@check(Tier.STRUCTURAL, "structural.member_interference")
def member_interference(ctx: CheckContext) -> list[Finding]:
    """No two wood framing members should occupy the same volume (advisory)."""
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree

    tol_z = inch(ctx.preferences.framing.interference_tolerance_in).meters

    candidates: list[_Candidate] = []
    for member in ctx.model.all_members():
        ring, z_lo, z_hi = member_footprint(member)
        poly = Polygon(ring)
        if poly.is_valid and poly.area > _TOL_AREA:
            candidates.append(_Candidate(
                f"{member.parent_uid}:{member.child_key}", poly, z_lo, z_hi,
                seg=(member.p0, member.p1), kind=member.category))
    # Column/beam solids are framing too; slabs/footings/pads are excluded because
    # beams legitimately bear into concrete and joists frame under deck slabs.
    for solid in ctx.model.solids:
        if solid.category not in ("column", "beam"):
            continue
        poly = Polygon(solid.outline)
        if poly.is_valid and poly.area > _TOL_AREA:
            candidates.append(_Candidate(solid.tag, poly, solid.z0_m, solid.z1_m,
                                         seg=_solid_segment(solid), kind=solid.category))

    if len(candidates) < 2:
        return []

    polys = [c.poly for c in candidates]
    tree = STRtree(polys)

    out: list[Finding] = []
    reported: set[frozenset[str]] = set()
    for i, a in enumerate(candidates):
        for j in tree.query(a.poly):
            if j <= i:
                continue
            b = candidates[j]
            key = frozenset({a.label, b.label})
            if key in reported:
                continue
            z_overlap = min(a.z_hi, b.z_hi) - max(a.z_lo, b.z_lo)
            if z_overlap <= tol_z:
                continue  # bearing/stacking joint — cleared
            inter = a.poly.intersection(b.poly)
            if inter.area <= _TOL_AREA:
                continue  # side/face abutment — cleared
            # Near-equal footprints: laminated plies / doubled trimmers-headers.
            if a.poly.symmetric_difference(b.poly).area < _TOL_AREA:
                continue
            # An endpoint landing on the other's axis: intended butt/T joinery.
            if _butt_joint(a, b, tol_z):
                continue
            reported.add(key)
            out.append(Finding(
                severity=Severity.WARN,
                check_id="structural.member_interference",
                message=(f"[advisory, not engineering] framing members {a.label} and "
                         f"{b.label} interpenetrate: {inter.area:.4f} m² shared in plan, "
                         f"{z_overlap:.3f} m vertical overlap"),
                element_tags=(a.label, b.label),
                fix_hint=("wood should stack post → beam → joist, not overlap; check the "
                          "bearing-stack elevation arithmetic in resolve/envelope.py"),
                result=Result.FAIL,
            ))
    return out

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


# Horizontal plate categories: a wall's bottom/top/raked top plates.
_PLATE_KINDS = frozenset({"plate", "raked_plate"})
# Vertical wall members a piece of blocking legitimately nails into.
_STUD_KINDS = frozenset({"stud", "corner", "king", "jack", "cripple"})
# Stair carriage/infill categories, and the members a stair frame bears on or butts.
_STAIR_HOUSED = frozenset({"tread", "winder"})
_STAIR_SUPPORT = frozenset({"stringer", "landing", "plate", "raked_plate", "joist",
                            "blocking", "trimmer", "header"}) | _STUD_KINDS
# Wall/roof framing that legitimately interpenetrates where two walls meet at a junction
# (studs, plates, headers, T-backing blocking, and the rafters/ridge landing on a gable).
_JUNCTION_FRAMING = (_STUD_KINDS | _PLATE_KINDS
                     | frozenset({"header", "blocking", "rafter", "ridge_beam"}))


def _intended_framing_joint(a: _Candidate, b: _Candidate) -> bool:
    """Intended wood joinery the lightweight member IR cannot express as clean geometry.

    The interference check exists to catch *elevation-arithmetic* bugs — a post left too
    tall, a beam topped at the joist datum. These joints are correct-by-design but still
    read as shared-volume because the IR carries no birdsmouth notch, no half-lap, and no
    glue line:

    * **rafter bearing on a wall top plate** — a real rafter is birdsmouthed so it seats
      *over* the plate; the box IR sinks the full rafter depth into it. The plate is the
      only horizontal member under a rafter's plan span, so this never masks a stud bug.
    * **eave web stiffener bonded to its own rafter** — the ``bearing_stiffener`` is glued
      to the I-joist rafter's web (same ``parent_uid``); shared volume is the point.
    * **top/bottom plates lapping at a corner or tee** — plates of *different* walls lap
      by convention (one runs through, the neighbour laps over). A same-wall plate overlap
      is a genuine stacking bug and is deliberately *not* cleared here.
    * **blocking nailed into its own wall's studs** — solid/ladder/fire blocking (incl. the
      T-backing ladder and in-line stud blocking) is fastened face-to-face into the studs of
      the *same* element; the box IR renders that nailing as a small shared volume.
    * **stair treads bearing on their stringers** — a tread is housed in / cleated to the
      stringers it spans between; the notch/bearing is intended joinery, not a clash.
    """
    kinds = {a.kind, b.kind}
    same_parent = a.parent == b.parent
    # A roof member bearing on the wall top it lands on — the birdsmouthed rafter seat, or
    # a ridge beam pocketed into a gable wall. The box IR has no seat cut, so the rafter/
    # ridge dips into the plate or the top of the stud/king it bears on.
    wall_top_kinds = _PLATE_KINDS | _STUD_KINDS
    if kinds & {"rafter", "ridge_beam"} and kinds & wall_top_kinds:
        return True
    # eave web stiffener bonded to its own rafter.
    if "bearing_stiffener" in kinds and "rafter" in kinds and same_parent:
        return True
    # cross-wall plate lap at an L corner or T junction.
    if a.kind in _PLATE_KINDS and b.kind in _PLATE_KINDS and not same_parent:
        return True
    # blocking fastened into studs/plates (its own wall, or the intersecting wall a T-backing
    # ladder exists to back). Blocking is minor nailer/backing stock, never a structural clash.
    if "blocking" in kinds and (kinds - {"blocking"}) <= (_STUD_KINDS | _PLATE_KINDS):
        return True
    # Stair joinery: treads/winders are housed in / land on the stair frame, and a stringer
    # (or landing) bears on the plates, joists, and studs that carry the flight. All are
    # intended notch/bearing joints, not clashes.
    if kinds & _STAIR_HOUSED and (kinds - _STAIR_HOUSED) <= _STAIR_SUPPORT:
        return True
    if kinds & {"stringer", "landing"} and (kinds - {"stringer", "landing"}) <= _STAIR_SUPPORT:
        return True
    # Cut joists / trimmers bearing on a floor-opening header (the header carries them).
    if "header" in kinds and (kinds - {"header"}) <= {"joist", "trimmer", "plate", "raked_plate"}:
        return True
    return False


def _butt_joint(a: _Candidate, b: _Candidate, tol: float) -> bool:
    """Intended joinery: an endpoint of one member lands on the other's axis.

    Gated by kind so it clears *intended* coplanar/bearing joints without masking the
    bug this check exists for. A joist bearing on a beam is *also* geometrically an
    endpoint-on-axis, but its elevation is what we police — so a beam is never a valid
    partner here. Cleared cases: a joist end butting a rim board (coplanar by design),
    a post/column seated under a beam (the vertical bearing, incl. the intended 2"
    rear-row drainage poke), and two wall plates lapping where their walls meet at an
    L/T (the bottom/top plates of a branch wall run to the through wall they tee into —
    the single most common intended framing joint, resolved as a lap in real framing)."""
    if not (a.kind == "rim" or b.kind == "rim"
            or a.kind == "column" or b.kind == "column"
            or (a.kind == "plate" and b.kind == "plate")):
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
    # Plan points where walls meet. Two studs from *different* walls that share volume this
    # close to a junction are an intended corner/tee stud pack (the perpendicular walls' end
    # studs butt together); the same two studs sharing volume far from any junction would be
    # a genuine wall-overlap bug, which this proximity gate deliberately still reports.
    junction_pts = [j.point for j in getattr(ctx.model, "junctions", ())]
    junction_tol = inch(10.0).meters

    candidates: list[_Candidate] = []
    for member in ctx.model.all_members():
        ring, z_lo, z_hi = member_footprint(member)
        poly = Polygon(ring)
        if poly.is_valid and poly.area > _TOL_AREA:
            z0e = member.z0_m if member.z0_end_m is None else member.z0_end_m
            z1e = member.z1_m if member.z1_end_m is None else member.z1_end_m
            zends = (min(member.z0_m, member.z1_m), max(member.z0_m, member.z1_m),
                     min(z0e, z1e), max(z0e, z1e))
            candidates.append(_Candidate(
                f"{member.parent_uid}:{member.child_key}", poly, z_lo, z_hi,
                seg=(member.p0, member.p1), kind=member.category,
                parent=member.parent_uid, zends=zends))
    # Column/beam solids are framing too; slabs/footings/pads are excluded because
    # beams legitimately bear into concrete and joists frame under deck slabs.
    for solid in ctx.model.solids:
        if solid.category not in ("column", "beam"):
            continue
        poly = Polygon(solid.outline)
        if poly.is_valid and poly.area > _TOL_AREA:
            candidates.append(_Candidate(solid.tag, poly, solid.z0_m, solid.z1_m,
                                         seg=_solid_segment(solid), kind=solid.category,
                                         parent=solid.tag))

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
            # Cheap bounding-box reject first; then the precise, slope-aware test below.
            if min(a.z_hi, b.z_hi) - max(a.z_lo, b.z_lo) <= tol_z:
                continue  # bearing/stacking joint — cleared
            inter = a.poly.intersection(b.poly)
            if inter.area <= _TOL_AREA:
                continue  # side/face abutment — cleared
            # Slope-aware vertical overlap, measured at the shared plan region: a raked
            # plate/rafter/ridge whose bounding box spans the whole slope must be compared
            # by its z-band *where the two members actually meet*, not end to end.
            centroid = inter.representative_point()
            pt = (centroid.x, centroid.y)
            a_lo, a_hi = a.zband_at(pt)
            b_lo, b_hi = b.zband_at(pt)
            z_overlap = min(a_hi, b_hi) - max(a_lo, b_lo)
            if z_overlap <= tol_z:
                continue  # bearing/stacking joint at the shared region — cleared
            # Near-equal footprints: laminated plies / doubled trimmers-headers.
            if a.poly.symmetric_difference(b.poly).area < _TOL_AREA:
                continue
            # An endpoint landing on the other's axis: intended butt/T joinery.
            if _butt_joint(a, b, tol_z):
                continue
            # Correct-by-design bearings/laps the box IR cannot express as clean geometry
            # (birdsmouth rafter seat, bonded web stiffener, cross-wall plate lap).
            if _intended_framing_joint(a, b):
                continue
            # Cross-wall framing butting together at an L corner or T junction: perpendicular
            # walls' studs/plates lap, and a gable's rake plate/rafters/ridge meet there. A
            # same-wall overlap, or one far from any junction, is still reported.
            if (a.parent != b.parent
                    and a.kind in _JUNCTION_FRAMING and b.kind in _JUNCTION_FRAMING
                    and any(math.hypot(pt[0] - jx, pt[1] - jy) <= junction_tol
                            for jx, jy in junction_pts)):
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

"""Is a roof member's contact with a wall top a real bearing seat? (→ member_interference)

``member_interference`` used to clear every rafter/ridge vs plate/stud contact as "the
birdsmouth", which is why catlin's attic partitions stood 11 7/8" inside their rafters at
0 FAIL. The contact is now graded on its geometry:

* **rafter crossing a wall** — a birdsmouth only where the rafter still BEARS on the member
  (its underside stays above the member's underside, so the member's top is inside the
  notch, not through it) and the notch is no deeper than 1/4 of the rafter's depth: IRC
  R802.7.1 ("notches at the ends of the member shall not exceed one-fourth the depth") and
  NDS 4.4.3 for end notches in sawn bending members. The depth is read plumb at the deepest
  point of the shared plan region (the heel), and so is the rafter's depth, so the ratio is
  the same as one measured square to the slope. Manufacturer I-joist limits (flange-only
  cuts) are stricter and are not graded here.
* **ridge beam** — cleared only where one of its ENDS lands inside a wall it crosses (a
  pocket in a gable wall). A ridge passing through a wall, or sunk into a partition that
  runs along under it, has no seat at all.

* **gable end rafter** — a rafter running ALONG a wall (under 30° in plan) whose framed
  top is raked to the SAME deck plane as the rafter's top. That is the resolver's gable
  convention, not a clash: ``roof_geometry.apply_to_roof_wall_tops`` rakes a gable to the
  deck its sheathing reaches, and ``framing/roof.py`` sets the end rafter "fully inside the
  gable wall plane". What it stands for is the end rafter bearing on the gable's raked top
  plate (IRC Table R602.3(1), rafter to top plate). A rafter along a wall at any other
  height, or across one, still takes the seat rule.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.structural._interference_geom import _Candidate, plan_angle_deg

ROOF_KINDS = frozenset({"rafter", "ridge_beam"})
#: IRC R802.7.1 / NDS 4.4.3: an end notch is at most one-quarter of the member depth.
SEAT_DEPTH_LIMIT = 0.25
#: Below this plan angle a roof member runs ALONG a wall rather than across it.
_PARALLEL_DEG = 30.0
CODE_REF = "IRC R802.7.1; NDS 4.4.3"


@dataclass(frozen=True)
class SeatVerdict:
    holds: bool
    roof: _Candidate
    wall: _Candidate
    depth_m: float = 0.0  # notch depth at the heel (plumb)
    roof_depth_m: float = 0.0  # the roof member's plumb depth there
    reason: str = ""


def roof_and_wall_top(a: _Candidate, b: _Candidate, wall_top_kinds) \
        -> tuple[_Candidate, _Candidate] | None:
    """``(roof member, wall-top member)`` when this pair is one, else ``None``."""
    for roof, other in ((a, b), (b, a)):
        if roof.kind in ROOF_KINDS and other.kind in wall_top_kinds:
            return roof, other
    return None


def _sample_points(inter) -> list[tuple[float, float]]:
    geoms = getattr(inter, "geoms", None) or [inter]
    pts: list[tuple[float, float]] = []
    for g in geoms:
        ext = getattr(g, "exterior", None)
        if ext is not None:
            pts.extend((x, y) for x, y in ext.coords)
    rp = inter.representative_point()
    pts.append((rp.x, rp.y))
    return pts


def _raked_top_at(top, pt) -> float:
    """A raked wall's framed top at plan ``pt``, interpolated along its axis."""
    (a, b), z0, z1 = top
    dx, dy = b[0] - a[0], b[1] - a[1]
    run2 = dx * dx + dy * dy
    t = 0.0 if run2 < 1e-18 else max(0.0, min(1.0, (
        (pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / run2))
    return z0 + (z1 - z0) * t


def grade_seat(roof: _Candidate, wall: _Candidate, inter, walls: WallReadings,
               tol_z: float) -> SeatVerdict:
    """Grade one roof-member vs wall-top contact that shares volume."""
    from shapely.geometry import Point

    angle = plan_angle_deg(roof.seg, walls.axes.get(wall.parent, wall.seg))
    crosses = angle is None or angle >= _PARALLEL_DEG
    if roof.kind == "ridge_beam":
        body = walls.polys.get(wall.parent, wall.poly).buffer(tol_z)
        if crosses and any(body.covers(Point(pt)) for pt in roof.seg):
            return SeatVerdict(True, roof, wall, reason="pocketed")
        return SeatVerdict(False, roof, wall, reason=(
            "the ridge beam has no end pocketed in this wall, and a beam sunk into a wall "
            "top has no seat"))
    top = walls.raked_tops.get(wall.parent)
    if not crosses and top is not None and all(
            abs(_raked_top_at(top, pt) - roof.zband_at(pt)[1]) <= tol_z
            for pt in _sample_points(inter)):
        return SeatVerdict(True, roof, wall, reason="gable end rafter on its raked plate")
    depth, roof_depth, bears = 0.0, float("inf"), True
    for pt in _sample_points(inter):
        r_lo, r_hi = roof.zband_at(pt)
        w_lo, w_hi = wall.zband_at(pt)
        depth = max(depth, w_hi - r_lo)
        roof_depth = min(roof_depth, r_hi - r_lo)
        bears = bears and r_lo >= w_lo - tol_z
    if not bears:
        return SeatVerdict(False, roof, wall, depth, roof_depth, reason=(
            "the rafter's underside drops below the member's underside, so the member is "
            "inside the rafter rather than under a seat cut"))
    if depth > SEAT_DEPTH_LIMIT * roof_depth + 1e-6:
        return SeatVerdict(False, roof, wall, depth, roof_depth, reason=(
            f"a {depth / 0.0254:.2f}\" notch exceeds 1/4 of the {roof_depth / 0.0254:.2f}\" "
            f"rafter depth ({SEAT_DEPTH_LIMIT * roof_depth / 0.0254:.2f}\")"))
    return SeatVerdict(True, roof, wall, depth, roof_depth, reason="birdsmouth")


@dataclass(frozen=True)
class WallReadings:
    axes: dict  # uid -> plan axis
    polys: dict  # uid -> plan footprint
    raked_tops: dict  # uid -> (axis, top z at start, top z at end), raked walls only


def wall_readings(model) -> WallReadings:
    """What the seat rule reads off every resolved wall."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    axes, polys, tops = {}, {}, {}
    for wall in getattr(model, "walls", ()) or ():
        axes[wall.uid] = wall.axis
        z0, z1 = getattr(wall, "top_z0_m", None), getattr(wall, "top_z1_m", None)
        if z0 is not None and z1 is not None and abs(z0 - z1) > 1e-6:
            tops[wall.uid] = (wall.axis, z0, z1)
        rings = [Polygon(ly.polygon) for ly in wall.layers
                 if not ly.is_cavity and len(ly.polygon) >= 3]
        rings = [r for r in rings if r.is_valid and r.area > 0]
        if rings:
            polys[wall.uid] = union_all(rings)
    return WallReadings(axes, polys, tops)


def record_failed_seat(seats: dict, verdict: SeatVerdict) -> None:
    """Keep the worst failed contact per (roof element, wall), and count them."""
    if verdict.holds:
        return
    key = (verdict.roof.parent, verdict.wall.parent)
    worst, count = seats.get(key, (verdict, 0))
    if verdict.depth_m > worst.depth_m:
        worst = verdict
    seats[key] = (worst, count + 1)


def seat_findings(ctx, seats: dict, check_id: str) -> list:
    """One FAIL per (roof element, wall) whose roof contact is not a bearing seat."""
    from typehaus.findings import Finding, Result, Severity

    plan = getattr(ctx, "plan", None)
    tags = {el.uid: el.tag for el in plan.all_elements()} if plan is not None else {}
    out = []
    for (roof_uid, wall_uid), (verdict, count) in sorted(seats.items()):
        roof_tag = tags.get(roof_uid, roof_uid)
        wall_tag = tags.get(wall_uid, wall_uid)
        out.append(Finding(
            severity=Severity.WARN,
            check_id=check_id,
            message=(f"[advisory, not engineering] {roof_tag} sits into {wall_tag} with no "
                     f"bearing seat at {count} member contact(s) — worst "
                     f"{verdict.roof.label} in {verdict.wall.label}: {verdict.reason}"),
            element_tags=(roof_tag, wall_tag, verdict.roof.label, verdict.wall.label),
            code_ref=CODE_REF,
            fix_hint=("bring the wall top to the roof member's underside (a seat cut no "
                      "deeper than 1/4 of the rafter depth), pocket the ridge, or stop the "
                      "wall below the roof"),
            result=Result.FAIL,
        ))
    return out

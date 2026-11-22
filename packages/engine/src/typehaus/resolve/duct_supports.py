"""Duct hangers along every run, off the standard's ``DuctSupportRow`` (decision #114).

Per horizontal leg: one hanger within ``support_near_fitting`` of each end (an elbow, a
branch, a collar or a boot is at every leg end), then as many between as keep each gap
inside the row's spacing. An end hanger whose strap would pass another duct is dropped where
the next leg's hanger already holds that fitting (``resolve/duct_strap_clear.py``). A leg
shorter than a foot rides on its neighbours. Risers are carried by the wall or chase they
climb and take none here. Each hanger names the framing it hangs from: a horizontal member
over (or, in a joist bay, beside) the duct within ``HANGER_REACH_M``. With nothing overhead
the standard's fallback rows are tried: a ``saddle`` (a strap band to the deck, house
practice; SMACNA draws no bottom support) where the duct bears on a deck (or on the row's
``sleeper`` block on it), then a ``bracket`` to a parallel wall within SMACNA Fig. 4-8's 2".
A slab is never a saddle host: a duct on concrete stays UNKNOWN, on purpose. A hanger with
no host is kept, with its ``gap``, for ``mep.duct_supports`` to grade.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.ducts import DuctStandard, DuctSupportRow
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_branches import section
from typehaus.resolve.duct_strap_clear import end_is_held, other_ducts
from typehaus.resolve.model_ducts import Point3, ResolvedDuctSupport
from typehaus.resolve.sweep import clean_path

#: Member categories a hanger may be fastened to.
HANG_FROM = frozenset({
    "joist", "sister_joist", "rim", "blocking", "truss_block", "truss_blocking",
    "roof_truss", "rafter", "header", "strongback", "soffit", "landing_framing", "plate",
    "ridge_beam", "outlooker", "hanger"})
#: How far a member may sit beside the duct (plan) or above its top (drop).
HANGER_PLAN_REACH_M = 16 * M_PER_IN
HANGER_REACH_M = 48 * M_PER_IN
#: A leg shorter than this is carried by the fittings at its ends.
MIN_HUNG_LEG_M = 12 * M_PER_IN
#: A saddle's duct bears on its deck: invert at most this over the deck top.
SADDLE_BEARING_M = 0.25 * M_PER_IN
#: A bracket's wall face at most this off the duct's side (SMACNA Fig. 4-8: "against wall or
#: maximum of 2 in. away"), parallel within ``BRACKET_SKEW_DEG``.
FALLBACK_REACH_M = 2 * M_PER_IN
BRACKET_SKEW_DEG = 10.0
_SLOP_M = 1e-4


def derive_supports(model: Any, standard: DuctStandard) -> list[ResolvedDuctSupport]:
    index = _MemberIndex(model)
    others = other_ducts(model)
    out: list[ResolvedDuctSupport] = []
    for duct in sorted(model.ducts, key=lambda d: d.tag):
        if len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
            continue
        kind = ("flex" if duct.material == "flex"
                else "round" if duct.diameter_m is not None else "rectangular")
        size_m = duct.diameter_m or (duct.width_m + duct.depth_m)  # half-perimeter
        row = standard.support_for(kind, size_m)
        if row is None:
            continue
        fallbacks = [(r, kind_) for kind_ in ("saddle", "bracket")
                     if (r := standard.support_for(kind, size_m, kind_)) is not None]
        near = standard.support_near_fitting.meters
        path = clean_path([(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)])
        legs = list(zip(path, path[1:], strict=False))
        per_leg = [stations(a, b, near, row.spacing.meters) for a, b in legs]

        for i, (a, b) in enumerate(legs):
            for k, point in enumerate(per_leg[i]):
                if end_is_held(duct, legs, per_leg, i, k, near, index.over, others):
                    continue
                used = row
                member, drop = index.over(point[:2], point[2] + duct.depth_m / 2.0)
                sleeper = 0.0
                for fallback, kind_ in fallbacks:
                    if member is not None:
                        break
                    foot = duct.width_m / 2.0 + (fallback.thickness.meters
                                                 if fallback.thickness else 0.0)
                    if kind_ == "saddle":
                        member, drop = index.deck_under(point, a, b, duct.depth_m / 2.0, foot)
                        if member is None and fallback.sleeper:
                            sleeper = fallback.sleeper.meters
                            member, drop = index.deck_under(point, a, b, duct.depth_m / 2.0,
                                                            foot, sleeper)
                            sleeper = sleeper if member is not None else 0.0
                    else:
                        member, drop = index.wall_beside(point, a, b, duct.width_m / 2.0)
                    used = fallback if member is not None else row
                out.append(_record(duct, point, used, member, drop,
                                   [k for _, k in fallbacks], sleeper))
    return out


def _record(duct: Any, point: Point3, row: DuctSupportRow, member: str | None, drop: float,
            fallbacks: list[str], sleeper: float = 0.0) -> ResolvedDuctSupport:
    reach = (f"no framing within {HANGER_REACH_M / M_PER_IN:.0f}\" above or "
             f"{HANGER_PLAN_REACH_M / M_PER_IN:.0f}\" beside the duct")
    near = f"{FALLBACK_REACH_M / M_PER_IN:.0f}\""
    reach += "".join({"saddle": ", no deck it bears on under both saddle feet",
                      "bracket": f", no parallel wall within {near} of its side"}[k]
                     for k in fallbacks)
    return ResolvedDuctSupport(
        run_tag=duct.tag, storey=duct.storey, size=section(duct), point=point,
        hanger=row.hanger, spacing_m=row.spacing.meters, product_ref=row.product_ref,
        hangs_from=member, drop_m=drop, width_m=row.width.meters if row.width else None,
        thickness_m=row.thickness.meters if row.thickness else None,
        gap=None if member else reach, sleeper_m=sleeper,
        sleeper_product_ref=row.sleeper_product_ref if sleeper else None)


def needs_hangers(duct: Any) -> bool:
    """Whether any leg is level and long enough to hang; else its fittings carry the run."""
    if len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
        return True
    pts = clean_path([(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)])
    for a, b in zip(pts, pts[1:], strict=False):
        plan = math.dist(a[:2], b[:2])
        if plan > abs(b[2] - a[2]) and plan >= MIN_HUNG_LEG_M:
            return True
    return False


def stations(a: Point3, b: Point3, near_m: float, spacing_m: float) -> list[Point3]:
    """Hanger points on one leg: near each end, then evenly between within ``spacing_m``."""
    plan = math.dist(a[:2], b[:2])
    if plan <= abs(b[2] - a[2]) or plan < MIN_HUNG_LEG_M:
        return []  # a riser, or a leg its fittings carry
    length = math.dist(a, b)
    if length <= 2 * near_m:
        ts = [0.5]
    else:
        first, last = near_m / length, 1.0 - near_m / length
        gaps = max(1, math.ceil((last - first) * length / spacing_m - 1e-9))
        ts = [first + (last - first) * k / gaps for k in range(gaps + 1)]
    return [tuple(pa + t * (pb - pa) for pa, pb in zip(a, b, strict=True))  # type: ignore[misc]
            for t in ts]


class _MemberIndex:
    """Horizontal framing members in plan, for "what does this hang from"."""

    def __init__(self, model: Any) -> None:
        from shapely.geometry import LineString, Polygon
        from shapely.strtree import STRtree

        self.members = [m for m in model.all_members() if m.category in HANG_FROM
                        and abs((m.z0_end_m or m.z0_m) - m.z0_m) < 0.05]
        shapes = [Polygon(m.plan_outline) if m.plan_outline and len(m.plan_outline) > 2
                  else LineString([m.p0, m.p1]) if m.p0 != m.p1 else None
                  for m in self.members]
        keep = [i for i, s in enumerate(shapes) if s is not None and s.is_valid]
        self.members = [self.members[i] for i in keep]
        self.tree = STRtree([shapes[i] for i in keep])
        self.tags = {host.uid: host.tag for coll in (model.walls, model.floors, model.roofs,
                                                       model.soffits, model.stairs)
                     for host in coll}
        self.model = model

    def over(self, at: tuple[float, float], top_z: float,
             reach_m: float = HANGER_REACH_M) -> tuple[str | None, float]:
        """(member key, drop from its underside to the duct top), nearest above first."""
        member, drop = self.member_over(at, top_z, reach_m)
        return (None, 0.0) if member is None else (self.key(member), drop)

    def key(self, member: Any) -> str:
        return f"{self.tags.get(member.parent_uid, member.parent_uid)}:{member.child_key}"

    def member_over(self, at: tuple[float, float], top_z: float,
                    reach_m: float = HANGER_REACH_M,
                    categories: frozenset[str] | None = None) -> tuple[Any | None, float]:
        """(member, drop from its underside to ``top_z``), nearest above first; ``categories``
        narrows the hosts."""
        from shapely.geometry import Point

        best: tuple[float, float, Any] | None = None
        for i in self.tree.query(Point(at).buffer(HANGER_PLAN_REACH_M)):
            member = self.members[int(i)]
            if categories is not None and member.category not in categories:
                continue
            if member.z1_m < top_z - 0.01 or member.z0_m > top_z + reach_m:
                continue
            drop = max(0.0, member.z0_m - top_z)
            plan = Point(at).distance(self.tree.geometries[int(i)])
            if best is None or (drop, plan) < best[:2]:
                best = (drop, plan, member)
        if best is None:
            return None, 0.0
        return best[2], best[0]

    def deck_under(self, point: Point3, a: Point3, b: Point3, half_depth: float,
                   foot: float, sleeper: float = 0.0) -> tuple[str | None, float]:
        """(``FLOOR:deck``, invert-to-deck gap) for a floor deck the duct bears on (on a
        ``sleeper`` block that thick, if given), with both band feet (``foot`` either side of
        the duct, across leg a-b) on it. Slabs are never hosts."""
        from shapely.geometry import Point, Polygon

        run = math.dist(a[:2], b[:2]) or 1.0
        nx, ny = (a[1] - b[1]) / run, (b[0] - a[0]) / run
        feet = [Point(point[0] + s * foot * nx, point[1] + s * foot * ny) for s in (-1.0, 1.0)]
        invert = point[2] - half_depth
        best: tuple[float, str] | None = None
        for floor in self.model.floors:
            if len(floor.deck_outline) < 3:
                continue
            deck, voids = Polygon(floor.deck_outline), [Polygon(v) for v in floor.deck_voids
                                                        if len(v) > 2]
            if not all(deck.covers(f) and not any(v.contains(f) for v in voids) for f in feet):
                continue
            gap = invert - max(floor.deck_top_at(f.x, f.y) for f in feet)
            bears = gap - sleeper
            if -0.003 <= bears <= SADDLE_BEARING_M + _SLOP_M and (best is None or gap < best[0]):
                best = (max(gap, 0.0), f"{floor.tag}:deck")
        return (best[1], best[0]) if best else (None, 0.0)

    def wall_beside(self, point: Point3, a: Point3, b: Point3,
                    half_width: float) -> tuple[str | None, float]:
        """(``WALL:face``, side gap) for a wall parallel to leg a-b within the reach."""
        from shapely.geometry import Point

        from typehaus.resolve.soffits import wall_footprint

        leg = math.atan2(b[1] - a[1], b[0] - a[0])
        best: tuple[float, str] | None = None
        for wall in self.model.walls:
            if not wall.z0_m <= point[2] <= wall.z1_m:
                continue
            (x0, y0), (x1, y1) = wall.axis
            skew = abs(math.degrees(math.atan2(y1 - y0, x1 - x0) - leg)) % 180.0
            if min(skew, 180.0 - skew) > BRACKET_SKEW_DEG:
                continue
            length2 = (x1 - x0) ** 2 + (y1 - y0) ** 2
            along = ((point[0] - x0) * (x1 - x0) + (point[1] - y0) * (y1 - y0)) / (length2 or 1.0)
            if not 0.0 <= along <= 1.0:  # the station must face the wall, not run past its end
                continue
            gap = wall_footprint(wall).distance(Point(point[:2])) - half_width
            if -0.003 <= gap <= FALLBACK_REACH_M and (best is None or gap < best[0]):
                best = (max(gap, 0.0), f"{wall.tag}:face")
        return (best[1], best[0]) if best else (None, 0.0)

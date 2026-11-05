"""Duct hangers along every run, off the standard's ``DuctSupportRow`` (decision #114).

Per horizontal leg: one hanger within ``support_near_fitting`` of each end (an elbow, a
branch, a collar or a boot is at every leg end), then as many between as keep each gap
inside the row's spacing. A leg shorter than a foot rides on its neighbours. Risers are
carried by the wall or chase they climb and take none here. Each hanger names the framing
it hangs from: a horizontal member over (or, in a joist bay, beside) the duct within
``HANGER_REACH_M``. A hanger with nothing there is kept, with its ``gap``, for
``mep.duct_supports`` to grade.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.ducts import DuctStandard
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_branches import section
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


def derive_supports(model: Any, standard: DuctStandard) -> list[ResolvedDuctSupport]:
    index = _MemberIndex(model)
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
        near = standard.support_near_fitting.meters
        path = clean_path([(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)])
        for a, b in zip(path, path[1:], strict=False):
            for point in stations(a, b, near, row.spacing.meters):
                top = point[2] + duct.depth_m / 2.0
                member, drop = index.over(point[:2], top)
                out.append(ResolvedDuctSupport(
                    run_tag=duct.tag, storey=duct.storey, size=section(duct), point=point,
                    hanger=row.hanger, spacing_m=row.spacing.meters,
                    product_ref=row.product_ref, hangs_from=member, drop_m=drop,
                    width_m=row.width.meters if row.width else None,
                    thickness_m=row.thickness.meters if row.thickness else None,
                    gap=None if member else (
                        f"no framing within {HANGER_REACH_M / M_PER_IN:.0f}\" above or "
                        f"{HANGER_PLAN_REACH_M / M_PER_IN:.0f}\" beside the duct")))
    return out


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

    def over(self, at: tuple[float, float], top_z: float) -> tuple[str | None, float]:
        """(member key, drop from its underside to the duct top), nearest above first."""
        from shapely.geometry import Point

        best: tuple[float, float, Any] | None = None
        for i in self.tree.query(Point(at).buffer(HANGER_PLAN_REACH_M)):
            member = self.members[int(i)]
            if member.z1_m < top_z - 0.01 or member.z0_m > top_z + HANGER_REACH_M:
                continue
            drop = max(0.0, member.z0_m - top_z)
            plan = Point(at).distance(self.tree.geometries[int(i)])
            if best is None or (drop, plan) < best[:2]:
                best = (drop, plan, member)
        if best is None:
            return None, 0.0
        member = best[2]
        return f"{self.tags.get(member.parent_uid, member.parent_uid)}:{member.child_key}", best[0]

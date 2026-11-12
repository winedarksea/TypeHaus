"""In-line volume dampers at the stations a run names (``DuctRun.inline_dampers``).

A station is the damper's centre as developed length along the resolved path from the
first vertex, so it reads straight off the run however the run turns or rises. One off the
run (at or past an end) is an ``integrity.inline_damper`` ERROR and draws nothing. The part
is the ``DuctStandard``'s ``damper`` row at the run's section; no row is a ``gap``.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.findings import Finding, Result, Severity
from typehaus.model.ducts import DuctStandard
from typehaus.resolve.duct_branches import section
from typehaus.resolve.model_ducts import Point3, ResolvedDuctPart

CHECK_ID = "integrity.inline_damper"


def _points(duct: Any) -> list[Point3]:
    return [(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)]


def point_at_station(duct: Any, station_m: float) -> tuple[Point3, Point3] | None:
    """``(point, unit axis)`` ``station_m`` along the run, or None off either end."""
    if len(duct.path) < 2 or len(duct.z_m) != len(duct.path) or station_m <= 0.0:
        return None
    walked = 0.0
    pts = _points(duct)
    for a, b in zip(pts, pts[1:], strict=False):
        length = math.dist(a, b)
        if length > 1e-9 and station_m < walked + length:
            t = (station_m - walked) / length
            axis = tuple((b[i] - a[i]) / length for i in range(3))
            return tuple(a[i] + t * (b[i] - a[i]) for i in range(3)), axis  # type: ignore[return-value]
        walked += length
    return None


def damper_parts(model: Any, standard: DuctStandard) -> tuple[list[ResolvedDuctPart],
                                                               list[Finding]]:
    by_tag = {d.tag: d for d in model.ducts}
    parts: list[ResolvedDuctPart] = []
    findings: list[Finding] = []
    for run in model.plan.all_elements():
        stations = getattr(run, "inline_dampers", ())
        duct = by_tag.get(run.tag) if stations else None
        if duct is None:
            continue
        size = section(duct)
        row = standard.part("damper", size)
        for station in stations:
            hit = point_at_station(duct, station.meters)
            if hit is None:
                findings.append(Finding(
                    severity=Severity.ERROR, check_id=CHECK_ID, result=Result.FAIL,
                    message=f"{run.tag}: in-line damper at {station} is not on the run "
                            f"({duct.length_m / 0.0254:.2f}\" developed)",
                    element_tags=(run.tag,)))
                continue
            parts.append(ResolvedDuctPart(
                kind="damper", run_tag=duct.tag, storey=duct.storey, size=size,
                point=hit[0], axis=hit[1],
                product_ref=row.product_ref if row else None,
                fabricated=bool(row and row.fabricated),
                length_m=row.length.meters if row and row.length else None,
                gap=None if row else f"no damper row at {size}"))
    return parts, findings

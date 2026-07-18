"""Facade window-to-wall ratio analysis (M5 WP5.2)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.model import ResolvedModel, ResolvedWall

_M2_TO_FT2 = 10.7639104167


@dataclass(frozen=True)
class FacadeWWR:
    facade: str
    gross_wall_area_m2: float
    glazing_area_m2: float

    @property
    def ratio(self) -> float:
        return self.glazing_area_m2 / self.gross_wall_area_m2 if self.gross_wall_area_m2 else 0.0

    def as_dict(self) -> dict[str, float | str]:
        return {"facade": self.facade, "gross_wall_area_ft2": self.gross_wall_area_m2 * _M2_TO_FT2,
                "glazing_area_ft2": self.glazing_area_m2 * _M2_TO_FT2, "ratio": self.ratio}


def _wall_length(wall: ResolvedWall) -> float:
    (x0, y0), (x1, y1) = wall.axis
    return math.hypot(x1 - x0, y1 - y0)


def _facade_for_wall(wall: ResolvedWall, model: ResolvedModel) -> str:
    """Choose the normal pointing away from the resolved building centroid.

    The resolver stores an axis but not an explicit outside normal yet. For the closed
    exterior loops it already resolves, this produces the same outward normal without
    adding geometry to the authored model.
    """
    mid_x = (wall.axis[0][0] + wall.axis[1][0]) / 2
    mid_y = (wall.axis[0][1] + wall.axis[1][1]) / 2
    all_midpoints = [((w.axis[0][0] + w.axis[1][0]) / 2, (w.axis[0][1] + w.axis[1][1]) / 2)
                     for w in model.walls]
    center_x = sum(p[0] for p in all_midpoints) / len(all_midpoints)
    center_y = sum(p[1] for p in all_midpoints) / len(all_midpoints)
    dx, dy = wall.axis[1][0] - wall.axis[0][0], wall.axis[1][1] - wall.axis[0][1]
    length = math.hypot(dx, dy)
    if not length:
        return "N"
    nx, ny = -dy / length, dx / length
    if nx * (mid_x - center_x) + ny * (mid_y - center_y) < 0:
        nx, ny = -nx, -ny
    true_north = model.plan.project.site.true_north.radians
    # Plan +Y is project north. Rotate it into true-north coordinates before binning.
    true_x = nx * math.cos(true_north) - ny * math.sin(true_north)
    true_y = nx * math.sin(true_north) + ny * math.cos(true_north)
    angle = math.atan2(true_x, true_y)  # clockwise from north
    return ("N", "E", "S", "W")[int((angle + math.pi / 4) // (math.pi / 2)) % 4]


def analyze_wwr(model: ResolvedModel) -> tuple[FacadeWWR, ...]:
    buckets = {name: [0.0, 0.0] for name in ("N", "E", "S", "W")}
    wall_by_tag = {w.tag: w for w in model.walls}
    for wall in model.walls:
        facade = _facade_for_wall(wall, model)
        buckets[facade][0] += _wall_length(wall) * (wall.z1_m - wall.z0_m)
    for opening in model.openings:
        if opening.is_door:
            continue
        wall = wall_by_tag.get(opening.host_wall)
        if wall is not None:
            buckets[_facade_for_wall(wall, model)][1] += opening.width_m * opening.height_m
    return tuple(FacadeWWR(name, *buckets[name]) for name in ("N", "E", "S", "W"))


def _adequate_south_overhang(ctx: CheckContext) -> bool:
    from typehaus.model.spatial import Roof

    overhangs = []
    for element in ctx.plan.all_elements():
        if isinstance(element, Roof):
            if element.overhang is not None:
                overhangs.append(element.overhang.feet)
            overhangs.extend(length.feet for _edge, length in element.edge_overhangs)
    return bool(overhangs) and max(overhangs) >= ctx.preferences.adequate_overhang_ft


@check(Tier.BUILDING_SCIENCE, "building_science.window_to_wall_ratio")
def window_to_wall_ratio(ctx: CheckContext) -> list[Finding]:
    south = next(item for item in analyze_wwr(ctx.model) if item.facade == "S")
    if south.ratio > ctx.preferences.south_wwr_threshold and not _adequate_south_overhang(ctx):
        return [Finding(
            severity=Severity.WARN, check_id="building_science.window_to_wall_ratio",
            message=(f"south glazing is {south.ratio:.0%} of gross wall area, above the "
                     f"{ctx.preferences.south_wwr_threshold:.0%} advisory threshold without "
                     "adequate eave coverage"),
            result=Result.FAIL,
        )]
    return []

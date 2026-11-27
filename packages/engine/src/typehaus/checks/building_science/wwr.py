"""Facade window-to-wall ratio analysis (M5 WP5.2)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.resolve import compass
from typehaus.resolve.envelope_geometry import carries_a_weather_skin
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
    """The true cardinal (N/E/S/W) of the wall's outward face, from its resolved layers."""
    return compass.facade_name(compass.wall_outward_normal(wall, model), model.plan.project.site)


def wwr_summary(model: ResolvedModel) -> dict[str, object]:
    """Overall + per-facade WWR — a pure summary for the EN-1 sheet (→ Phase 7)."""
    per_facade = analyze_wwr(model)
    total_wall = sum(item.gross_wall_area_m2 for item in per_facade)
    total_glazing = sum(item.glazing_area_m2 for item in per_facade)
    return {
        "overall": total_glazing / total_wall if total_wall else 0.0,
        "per_facade": per_facade,
    }


def analyze_wwr(model: ResolvedModel) -> tuple[FacadeWWR, ...]:
    buckets = {name: [0.0, 0.0] for name in ("N", "E", "S", "W")}
    # Only walls with an outboard weather skin are facade; partitions and bare retaining or
    # bearing courses are not (an opening in one is not fenestration here either).
    wall_by_tag = {w.tag: w for w in model.walls if carries_a_weather_skin(w)}
    for wall in wall_by_tag.values():
        facade = _facade_for_wall(wall, model)
        buckets[facade][0] += _wall_length(wall) * (wall.z1_m - wall.z0_m)
    # A glazed door is fenestration (IRC R202), so a French pair belongs in the ratio the
    # same way a sash does — the three exterior French doors are 100 sf of south and east
    # glass between them. An unglazed leaf is not: it is opaque wall as far as WWR goes.
    glazed_doors = {item.tag for item in model.plan.library.door_types if item.glazed}
    for opening in model.openings:
        if opening.is_door and opening.type_ref not in glazed_doors:
            continue
        # A BLIND recess is not fenestration and not even a hole: a firebox pocket 6" into
        # the east wall has brick in front of it and sheathing behind it, and counting it
        # here would put 5 sf of "east glazing" on a facade that gained no glass.
        if opening.is_blind:
            continue
        host_wall = wall_by_tag.get(opening.host_wall)
        if host_wall is not None:
            buckets[_facade_for_wall(host_wall, model)][1] += opening.width_m * opening.height_m
    return tuple(FacadeWWR(name, *buckets[name]) for name in ("N", "E", "S", "W"))


# Outward plan normal of each rectangular-roof edge, by the project-north names that
# ``Roof.edge_overhangs`` keys use (decision #153).
_EDGE_NORMALS = {"south": (0.0, -1.0), "north": (0.0, 1.0), "east": (1.0, 0.0),
                 "west": (-1.0, 0.0)}


def _adequate_south_overhang(ctx: CheckContext) -> bool:
    """Does any roof edge that faces TRUE south project at least the preferred overhang?"""
    from typehaus.model.spatial import Roof

    site = ctx.plan.project.site
    south_edges = [edge for edge, normal in _EDGE_NORMALS.items()
                   if compass.facade_name(normal, site) == "S"]
    overhangs: list[float] = []
    for element in ctx.plan.all_elements():
        if not isinstance(element, Roof):
            continue
        per_edge = {edge.lower(): length.feet for edge, length in element.edge_overhangs}
        default = element.overhang.feet if element.overhang is not None else None
        for edge in south_edges:
            value = per_edge.get(edge, default)
            if value is not None:
                overhangs.append(value)
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

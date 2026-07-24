"""Sheet-good and framing takeoffs derived from resolved framing and authored assemblies."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from typehaus.model.enums import LayerFunction
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.resolve.geometry import length, polygon_area, sub
from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104167
_SHEET_AREA_FT2 = 32.0
_M_TO_FT = 3.280839895013123

# Stock lengths a dimensional-lumber order is placed in; a member is charged to the shortest
# stock it can be cut from, and anything past the longest stock rounds up to the next 2 ft.
_STOCK_LENGTHS_FT = (8, 10, 12, 14, 16, 20)
# ``[plies-]TxW`` — a leading built-up ply count is optional; a trailing name (LVL, rim,
# I-joist) is ignored. Board-foot rollup is only reported when this matches.
_PROFILE_RE = re.compile(r"^(?:(\d+)-)?(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)")


def _order_length_ft(length_ft: float) -> int:
    """Round a cut length up to the stock length it would be purchased in."""
    for stock in _STOCK_LENGTHS_FT:
        if length_ft <= stock + 1e-6:
            return stock
    return int(math.ceil(length_ft / 2.0)) * 2


def _board_feet_per_ft(profile: str) -> float | None:
    """Nominal board-feet per lineal foot for a dimensional/built-up profile, or None."""
    match = _PROFILE_RE.match(profile)
    if match is None:
        return None
    plies = int(match.group(1)) if match.group(1) else 1
    thickness, width = float(match.group(2)), float(match.group(3))
    return plies * thickness * width / 12.0


def framing_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Full framing bill of materials: every resolved member grouped by size AND type.

    One row per (profile, category) — e.g. ``2x6`` / ``stud`` — carrying the piece count,
    the summed cut length, the stock length that count is ordered in, and the per-stock
    length buckets a framer or estimator actually buys against. Nothing is silently dropped:
    ``model.all_members()`` is the complete resolved member set (walls, floors, roof,
    stairs), so the pieces here reconcile 1:1 with what the 3D model frames.
    """
    Group = dict[str, object]
    groups: dict[tuple[str, str], Group] = {}
    for member in model.all_members():
        cut_ft = member.length_m * _M_TO_FT
        order_ft = _order_length_ft(cut_ft)
        key = (member.profile, member.category)
        group = groups.get(key)
        if group is None:
            group = groups[key] = {"pieces": 0, "cut_length_ft": 0.0,
                                   "buckets": Counter()}
        group["pieces"] = int(group["pieces"]) + 1
        group["cut_length_ft"] = float(group["cut_length_ft"]) + cut_ft
        buckets = group["buckets"]
        assert isinstance(buckets, Counter)
        buckets[order_ft] += 1

    rows: list[dict[str, object]] = []
    for (profile, category), group in sorted(groups.items()):
        buckets = group["buckets"]
        assert isinstance(buckets, Counter)
        order_ft_total = sum(length_ft * count for length_ft, count in buckets.items())
        bf_per_ft = _board_feet_per_ft(profile)
        rows.append({
            "profile": profile,
            "category": category,
            "pieces": int(group["pieces"]),
            "cut_length_ft": round(float(group["cut_length_ft"]), 1),
            "order_length_ft": order_ft_total,
            "stock": [{"length_ft": length_ft, "count": count}
                      for length_ft, count in sorted(buckets.items())],
            "board_feet": round(bf_per_ft * order_ft_total, 1) if bf_per_ft else None,
        })
    return rows


def framing_bom_by_size(model: ResolvedModel) -> list[dict[str, object]]:
    """Roll the framing takeoff up to one row per profile (size), across all member types."""
    by_size: dict[str, dict[str, object]] = {}
    for row in framing_takeoff(model):
        profile = str(row["profile"])
        size = by_size.get(profile)
        if size is None:
            size = by_size[profile] = {"profile": profile, "pieces": 0,
                                       "cut_length_ft": 0.0, "order_length_ft": 0,
                                       "board_feet": 0.0, "types": []}
        size["pieces"] = int(size["pieces"]) + int(row["pieces"])
        size["cut_length_ft"] = round(
            float(size["cut_length_ft"]) + float(row["cut_length_ft"]), 1)
        size["order_length_ft"] = int(size["order_length_ft"]) + int(row["order_length_ft"])
        if row["board_feet"] is not None:
            size["board_feet"] = round(float(size["board_feet"]) + float(row["board_feet"]), 1)
        types = size["types"]
        assert isinstance(types, list)
        types.append(row["category"])
    for size in by_size.values():
        if not size["board_feet"]:
            size["board_feet"] = None
    return [by_size[profile] for profile in sorted(by_size)]


def sheet_goods_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Return net-area and whole-sheet quantities for wall, roof, and subfloor sheathing.

    Every row is explicitly tied to its material and thickness; this makes a 4x8-sheet
    estimate auditable instead of silently grouping unlike panel products.
    """
    areas: dict[tuple[str, str, float], float] = defaultdict(float)
    openings_by_wall: dict[str, float] = defaultdict(float)
    for opening in model.openings:
        openings_by_wall[opening.host_wall] += opening.width_m * opening.height_m

    for wall in model.walls:
        exterior = any(layer.function == "cladding" for layer in wall.layers)
        if not exterior:
            continue
        wall_area = length(sub(wall.axis[1], wall.axis[0])) * (
            ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2 - wall.z0_m
        ) - openings_by_wall[wall.tag]
        for layer in wall.layers:
            if layer.function == "sheathing":
                areas[("exterior wall", layer.material_ref, layer.thickness_m)] += max(0.0, wall_area)

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function is LayerFunction.SHEATHING:
                areas[("roof", layer.material_ref, layer.thickness.meters)] += roof.surface_area_m2

    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem) or system.subfloor is None:
                continue
            floor = next((item for item in model.floors if item.tag == system.tag), None)
            if floor is None or not floor.members:
                continue
            points = [point for member in floor.members for point in (member.p0, member.p1)]
            gross = (max(point[0] for point in points) - min(point[0] for point in points)) * (
                max(point[1] for point in points) - min(point[1] for point in points)
            )
            openings = sum(abs(polygon_area([point.xy_m for point in opening.outline]))
                           for opening in model.plan.storey_elements(storey.tag)
                           if isinstance(opening, FloorOpening) and opening.tag in system.openings)
            areas[("subfloor", system.subfloor.material_ref, system.subfloor.thickness.meters)] += gross - openings

    return [
        {"scope": scope, "material": material, "thickness_in": round(thickness / 0.0254, 3),
         "net_area_sqft": round(area * _M2_TO_FT2, 1),
         "sheets_4x8": math.ceil(area * _M2_TO_FT2 / _SHEET_AREA_FT2)}
        for (scope, material, thickness), area in sorted(areas.items())
    ]

"""Derived space-dashboard metrics for the model.json client contract (M3)."""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel


def build_space_summary(model: ResolvedModel) -> dict[str, object]:
    """Return per-storey and whole-house room-area metrics in square feet.

    Usable area is the modeled room area. Storage is a transparent subset: rooms tagged
    storage plus any future storage furniture whose footprint can be associated with a room.
    """
    rows: dict[str, dict[str, float]] = {}
    for room in model.rooms:
        row = rows.setdefault(room.storey, _empty_row())
        area = room.area_m2 * 10.7639
        row["usable_sf"] += area
        row["conditioned_sf" if room.conditioned else "unconditioned_sf"] += area
        if room.occupancy == "storage":
            row["storage_sf"] += area
    furniture_types = {item.tag: item for item in model.plan.library.furniture_types}
    for storey in model.plan.storeys:
        row = rows.setdefault(storey.tag, _empty_row())
        for furniture in model.plan.storey_elements(storey.tag):
            if furniture.element_kind != "Furniture":
                continue
            furniture_type = furniture_types.get(furniture.type_ref)
            if furniture_type is not None and furniture_type.storage:
                width, depth = (dimension.meters for dimension in furniture_type.footprint)
                row["storage_sf"] += width * depth * 10.7639
    storeys = [
        {"storey": tag, **_rounded(row), "storage_ratio": _ratio(row)}
        for tag, row in sorted(rows.items())
    ]
    total = _empty_row()
    for row in rows.values():
        for key in total:
            total[key] += row[key]
    return {"storeys": storeys, "overall": {**_rounded(total), "storage_ratio": _ratio(total)}}


def _empty_row() -> dict[str, float]:
    return {"conditioned_sf": 0.0, "unconditioned_sf": 0.0,
            "usable_sf": 0.0, "storage_sf": 0.0}


def _rounded(row: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 1) for key, value in row.items()}


def _ratio(row: dict[str, float]) -> float:
    return round(row["storage_sf"] / row["usable_sf"], 4) if row["usable_sf"] else 0.0

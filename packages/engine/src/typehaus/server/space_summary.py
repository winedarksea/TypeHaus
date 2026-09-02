"""Derived space-dashboard metrics for the model.json client contract (M3)."""

from __future__ import annotations

from typing import Any

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
    gross = gross_area_sf(model)
    storeys = [row | {"gross_sf": gross["storeys"].get(row["storey"], 0.0)} for row in storeys]
    return {"storeys": storeys,
            "overall": {**_rounded(total), "gross_sf": gross["overall"],
                        "storage_ratio": _ratio(total)}}


def _exterior_shells_by_storey(model: ResolvedModel) -> dict[str, list]:
    """Per-storey exterior (cladding-to-cladding) footprint shells, room-enclosures only.

    Derived from the wall *bodies*, not from the rooms: rooms stop at the finish face, so a
    room-sum understates the building by its whole envelope thickness — about 6% on a 36x36
    house with 12" foundation walls. Each wall layer already carries its own plan polygon;
    their union per storey is the building's plan mass, and the exterior ring of that union
    is the footprint. Interior courtyards are not filled — a ring's holes stay holes.

    Shared by :func:`gross_area_sf` (area) and :func:`exterior_footprint_dimensions_m`
    (bounding width/depth) — both need the same room-enclosed shells, not raw wall unions.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    per_storey: dict[str, list] = {}
    for wall in model.walls:
        bodies = [Polygon(layer.polygon) for layer in wall.layers
                  if layer.polygon and len(layer.polygon) >= 3]
        if bodies:
            per_storey.setdefault(wall.storey, []).extend(bodies)
    rooms_by_storey: dict[str, list] = {}
    for room in model.rooms:
        if room.clear_face and len(room.clear_face) >= 3:
            rooms_by_storey.setdefault(room.storey, []).append(Polygon(room.clear_face))
    shells_by_storey: dict[str, list] = {}
    for storey, bodies in per_storey.items():
        # ``overlay.union_all`` rather than ``shapely.ops.unary_union``: on GEOS 3.12 (what
        # the published Pyodide app runs) the floating-point noder throws a
        # ``TopologyException`` on the mitred NW basement corner, and a fatal one — it kills
        # the whole worker, so the web app never renders. See ``resolve/overlay``.
        merged = union_all([body.buffer(0) for body in bodies])
        polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
        rooms = rooms_by_storey.get(storey, [])
        kept = []
        for poly in polys:
            if poly.is_empty:
                continue
            shell = Polygon(poly.exterior)
            # **An enclosure counts only if it encloses a Room.** The retaining walls of the
            # sunken garden, the porch and balcony guards, and the breezeway posts are all
            # walls on a storey and none of them is floor area anyone builds or buys. Rooms
            # are the plan's own statement about what is a space (the garage is a Room, an
            # unconditioned one, and a builder does price garage square footage) — so this
            # tracks the plan rather than maintaining a list of structures to exclude.
            if any(shell.contains(room.representative_point()) for room in rooms):
                kept.append(shell)
        shells_by_storey[storey] = kept
    return shells_by_storey


def gross_area_sf(model: ResolvedModel) -> dict[str, object]:
    """Gross floor area per storey — the **exterior** footprint, walls included.

    The three areas this module reports are three different questions and an estimate needs
    all of them: ``usable_sf`` is what you can stand in, ``conditioned_sf`` is what the
    energy code grades, and gross is what a builder means by "$/sf". None of them was gross
    before this, so a $/sf figure had no honest denominator at all.
    """
    out = {storey: round(sum(shell.area for shell in shells) * 10.7639, 1)
           for storey, shells in _exterior_shells_by_storey(model).items()}
    return {"storeys": out, "overall": round(sum(out.values()), 1)}


def exterior_footprint_dimensions_m(model: ResolvedModel) -> list[dict[str, object]]:
    """Per-storey exterior width/depth (cladding-to-cladding), in meters.

    The bounding box of the same room-enclosed shells :func:`gross_area_sf` sums the area
    of — so the sunken garden's retaining walls and the breezeway posts are excluded here
    the same way they are excluded there, without a second list of structures to skip.
    """
    rows = []
    for storey, shells in sorted(_exterior_shells_by_storey(model).items()):
        if not shells:
            continue
        minx = min(shell.bounds[0] for shell in shells)
        miny = min(shell.bounds[1] for shell in shells)
        maxx = max(shell.bounds[2] for shell in shells)
        maxy = max(shell.bounds[3] for shell in shells)
        rows.append({"storey": storey, "width_m": round(maxx - minx, 4),
                     "depth_m": round(maxy - miny, 4)})
    return rows


def _empty_row() -> dict[str, float]:
    return {"conditioned_sf": 0.0, "unconditioned_sf": 0.0,
            "usable_sf": 0.0, "storage_sf": 0.0}


def _rounded(row: dict[str, float]) -> dict[str, float]:
    return {key: round(value, 1) for key, value in row.items()}


def _ratio(row: dict[str, float]) -> float:
    return round(row["storage_sf"] / row["usable_sf"], 4) if row["usable_sf"] else 0.0


def estimate_areas(model: Any) -> dict[str, float]:
    """The two $/sf denominators, plus a driver's addressable scalars.

    Every caller of ``estimate_costs`` that holds a resolved model passes these: a
    ``space_summary.gross_sf`` driver makes divergence load-bearing — the same house must
    price the same way through ``haus takeoff`` and ``haus tasks``, and
    ``test_work_packages`` pins those two totals together. One helper, one answer.
    """
    overall = build_space_summary(model)["overall"]
    return {"conditioned": overall["conditioned_sf"], "gross": overall["gross_sf"]}

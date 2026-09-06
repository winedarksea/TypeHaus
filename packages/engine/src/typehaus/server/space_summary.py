"""Derived space-dashboard metrics for the model.json client contract (M3)."""

from __future__ import annotations

from typing import Any

from typehaus.resolve.model import ResolvedModel


def build_space_summary(model: ResolvedModel) -> dict[str, object]:
    """Return per-storey and whole-house room-area metrics in square feet.

    Usable area is the modeled room area **with the rake taken off**: the part of a room a
    roof brings below 5'-0" of clear head is not floor anyone uses, and reporting it as
    usable was the difference between a 134 sf attic pocket and the 6 sf of it a person can
    stand in (``ResolvedRoom.head_limited_area_m2``, R304.3 / ANSI Z765). ``low_head_sf``
    carries what was subtracted so the two reconcile against ``area_m2``.

    ``conditioned_sf`` deliberately does NOT take the rake off. Every square foot under it
    is sheathed, finished and heated, and the energy code grades floor area, not headroom —
    so the conditioned figure stays the full modeled floor and only the "how much space is
    this" figures are head-limited.

    Storage is a transparent subset of usable: rooms tagged storage plus any storage
    furniture whose footprint can be associated with a room.
    """
    rows: dict[str, dict[str, float]] = {}
    for room in model.rooms:
        row = rows.setdefault(room.storey, _empty_row())
        area = room.area_m2 * 10.7639
        usable = (room.head_limited_area_m2 if room.head_limited_area_m2 is not None
                  else room.area_m2) * 10.7639
        row["usable_sf"] += usable
        row["low_head_sf"] += max(area - usable, 0.0)
        row["conditioned_sf" if room.conditioned else "unconditioned_sf"] += area
        if room.occupancy == "storage":
            row["storage_sf"] += usable
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
    from typehaus.resolve.site_earth import open_excavation_floors

    per_storey: dict[str, list] = {}
    for wall in model.walls:
        bodies = [Polygon(layer.polygon) for layer in wall.layers
                  if layer.polygon and len(layer.polygon) >= 3]
        if bodies:
            per_storey.setdefault(wall.storey, []).extend(bodies)
    # The court floors, porch pits and window wells: exterior ground at their own level.
    # Same derivation `structural.frost_depth` measures from, so the two cannot disagree
    # about which surfaces are open sky.
    open_ground = [polygon for _tag, polygon, _top in open_excavation_floors(model)]
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
            # **A hole over OPEN GROUND stays a hole.** The docstring above has always
            # promised courtyards are not filled; `Polygon(poly.exterior)` discarded every
            # interior ring, and it went unnoticed only because no outdoor enclosure had ever
            # MERGED with the house mass — the sunken court was its own disjoint polygon, so
            # its void was never one of the house's holes to fill. W-SG-BRKBM changed that: a
            # grade beam bearing on W-SG-W1/E1 to carry W-B-BRICK is one connected pour from
            # the house wall to the court's south end, and filling that ring added 610 sf of
            # "floor area" that is open sky.
            #
            # Keyed on an excavation floor rather than on "no Room in it", which was tried
            # first and is much too broad: a stair well, a chase and a vaulted void are all
            # room-less holes in a wall union that a builder absolutely does price, and
            # keeping those cost the attic 97 sf. `open_excavation_floors` is the plan's own
            # positive statement that a surface is exterior ground at its own elevation.
            #
            # ** OVERLAP, NOT `contains(representative_point())`. ** That was the first
            # spelling and it under-kept: one floor yields ONE representative point, so a
            # floor spanning several rings anchors only the ring that point happens to land
            # in and the rest get filled. The sunken court is exactly that shape —
            # `W-SG-ARCH` crosses it and splits the void into a porch bay and a field bay,
            # both of them SL-SG-FLOOR. It went unnoticed only because SL-SG-STOOP sat in
            # the other bay and anchored it; retiring the stoop on 2026-09-05 filled 281 sf
            # of open court and put it on the basement's gross area. Area overlap asks the
            # question actually meant — "is this ring open excavated ground?" — and does not
            # depend on how many elements the ground was modelled as.
            interiors = [ring for ring in poly.interiors
                         if any(Polygon(ring).intersection(floor).area > 0.0
                                for floor in open_ground)]
            shell = Polygon(poly.exterior, interiors)
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
            "usable_sf": 0.0, "low_head_sf": 0.0, "storage_sf": 0.0}


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

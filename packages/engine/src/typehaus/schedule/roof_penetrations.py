"""What goes through the roof, and what the roofer therefore has to flash.

The one handoff item on the roof visit that the model can answer and nobody can recover
afterwards: once the membrane is down, a pipe added through it is a repair. So the list is
derived from the actual solids rather than from anybody's memory of the mechanical plan.

**An empty list is itself the answer.** On catlin every vent, duct and dryer exhaust exits
through a wall, so the roofer's line reads "nothing penetrates this roof — if something
does on the day, stop and call". That is a stronger statement than no list at all, and it
is why this probe reports its evidence instead of just returning nothing.
"""

from __future__ import annotations

from typing import Any

#: Solid categories that would be a penetration if they crossed a roof plane. Pipes, ducts,
#: raceways and vents — everything the three MEP trades push through a shell.
_PENETRATING = ("pipe_", "duct_", "conduit_", "vent")


def _is_penetrating_category(category: str | None) -> bool:
    text = str(category or "").lower()
    return any(text.startswith(prefix) or text == prefix for prefix in _PENETRATING)


def _roof_planes(model: Any) -> list[Any]:
    return list(getattr(model, "roofs", []) or [])


def _xy_extent(solid: Any) -> tuple[float, float, float, float] | None:
    """The solid's plan bounding box, from whatever geometry it carries."""
    points: list[tuple[float, float]] = []
    for attribute in ("outline", "footprint", "ring"):
        ring = getattr(solid, attribute, None) or ()
        points.extend((float(p[0]), float(p[1])) for p in ring if len(p) >= 2)
    path = getattr(solid, "path", None) or getattr(solid, "points", None) or ()
    points.extend((float(p[0]), float(p[1])) for p in path if len(p) >= 2)
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _top_z(solid: Any) -> float | None:
    for attribute in ("top_z_m", "z_top_m", "max_z_m"):
        value = getattr(solid, attribute, None)
        if value is not None:
            return float(value)
    base = getattr(solid, "base_z_m", None) or getattr(solid, "z_m", None)
    height = getattr(solid, "height_m", None)
    if base is not None and height is not None:
        return float(base) + float(height)
    return float(base) if base is not None else None


def roof_penetrations(model: Any) -> tuple[list[dict[str, Any]], str]:
    """``(penetrations, evidence)`` — one entry per solid that crosses a roof plane.

    A solid counts when its plan extent falls inside a roof's footprint **and** its top
    reaches the roof's underside at that point. Both tests matter: a vent stack rising
    beside the eave is not a penetration, and a duct that stops in the joist bay under a
    roof is not one either.
    """
    from typehaus.resolve.roof_geometry import roof_height_at

    roofs = _roof_planes(model)
    candidates = [solid for solid in getattr(model, "solids", []) or []
                  if _is_penetrating_category(getattr(solid, "category", None))]
    if not roofs:
        return [], "no roof is modelled, so nothing can be shown to penetrate one"
    if not candidates:
        return [], (f"{len(roofs)} roof plane(s) modelled and no pipe, duct, conduit or "
                    "vent solid anywhere in the model")

    out: list[dict[str, Any]] = []
    for solid in candidates:
        extent = _xy_extent(solid)
        top = _top_z(solid)
        if extent is None or top is None:
            continue
        centre = ((extent[0] + extent[2]) / 2.0, (extent[1] + extent[3]) / 2.0)
        for roof in roofs:
            if not _inside(roof, centre):
                continue
            try:
                plane_z = roof_height_at(roof, centre)
            except Exception:  # noqa: BLE001 - a roof this probe cannot evaluate is skipped
                continue
            if top >= plane_z - 0.05:
                out.append({"tag": str(getattr(solid, "tag", "") or ""),
                            "category": str(getattr(solid, "category", "") or ""),
                            "roof": str(getattr(roof, "tag", "") or ""),
                            "at": [round(centre[0], 3), round(centre[1], 3)]})
                break
    if out:
        return out, f"{len(out)} of {len(candidates)} MEP solid(s) cross a roof plane"
    return [], (f"{len(candidates)} pipe/duct/conduit/vent solid(s) modelled, none of them "
                f"reaching any of the {len(roofs)} roof plane(s) — every terminal on this "
                "house exits through a wall")


def _inside(roof: Any, point: tuple[float, float]) -> bool:
    """Is the point within the roof's plan footprint?

    Ring-agnostic on purpose: a roof carries its plan outline under one of a few names
    depending on how it was resolved, and a probe that knew only one of them would report
    an empty list on a house that had penetrations.
    """
    ring = (getattr(roof, "outline", None) or getattr(roof, "footprint", None)
            or getattr(roof, "ring", None) or ())
    ring = [(float(p[0]), float(p[1])) for p in ring if len(p) >= 2]
    if len(ring) < 3:
        return False
    x, y = point
    inside = False
    j = len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside

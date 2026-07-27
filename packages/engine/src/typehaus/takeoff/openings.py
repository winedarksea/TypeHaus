"""Doors and windows by type — the schedule the BOM never had.

A-601 draws the opening schedule off ``model.openings``, so the data has been resolved and
presented all along; it simply never reached ``bill_of_materials``. Doors and windows are
usually the second-largest line on a residential order after framing, and an estimate that
silently omits them reads as complete while being wrong by a lot.

Grouped by type ref, because that is the unit an order is placed in: eight WT-2736s are one
line on a window quote whatever walls they land in. An opening with no ``type_ref`` — a bare
rough void — is reported as its own UNKNOWN row rather than dropped, for the same reason the
finishes section reports an unfinished room.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874015748


def opening_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per opening type: count, nominal size, and the tags it covers."""
    door_types = {item.tag: item for item in model.plan.library.door_types}
    window_types = {item.tag: item for item in model.plan.library.window_types}

    groups: dict[tuple[str, str, float, float], dict[str, object]] = {}
    for opening in model.openings:
        key = (opening.kind, opening.type_ref or "", round(opening.width_m * _M_TO_IN, 2),
               round(opening.height_m * _M_TO_IN, 2))
        entry = groups.setdefault(key, {"count": 0, "tags": [], "arched": False})
        entry["count"] += 1
        entry["tags"].append(opening.tag)
        # An arched head is a different product, not a trim decision, so it stays visible
        # on the row rather than being averaged away into a rectangular opening's count.
        entry["arched"] = bool(entry["arched"]) or opening.arch_rise_m > 1e-9

    rows = []
    for (kind, type_ref, width_in, height_in), entry in sorted(groups.items()):
        product = door_types.get(type_ref) or window_types.get(type_ref)
        # The operation is what is actually ordered: a 36x60 casement and a 36x60 picture
        # unit are the same hole and different products, and for a door the leaf makeup
        # (glazed vs solid) moves the price as much as the operation does. Both ride in the
        # qualifier rather than the key because the type ref already separates the rows.
        operation = getattr(getattr(product, "operation", None), "value", None)
        qualifier = operation
        if product is not None and kind == "door":
            qualifier = f"{operation} · {'glazed' if product.glazed else 'solid'}"
        rows.append({
            "kind": kind,
            "type": type_ref or None,
            "product": getattr(product, "name", None) or "UNKNOWN",
            "known": product is not None,
            "operation": operation,
            "qualifier": qualifier,
            "width_in": width_in,
            "height_in": height_in,
            "arched": entry["arched"],
            "count": int(entry["count"]),
            "tags": sorted(entry["tags"]),
        })
    return rows

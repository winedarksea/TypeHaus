"""Placeable and radiant-floor takeoffs — the engine twin of the UI's BOM sections.

The browser's bill of materials (``ui/src/model/bom.ts`` — ``placeablesSection``) already
counts every free-placed and wall-attached component from ``model.canvas_objects``; this
module gives ``bill_of_materials`` the same rows so casework, appliances, fixtures,
equipment, registers and electrical devices reach the engine BOM (and `haus takeoff`)
instead of existing only on screen. Hosted openings are deliberately excluded: they are
billed by the openings/glazing sections as the same product, and double-billing a door is
worse than omitting it.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123


def placeables_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Count every resolved placeable, one row per (catalog type, domain, storey).

    Mirrors the UI's ``placeablesSection``: the row key is the catalog ``type`` (falling
    back to the element kind for typeless objects), the basis is ``domain · storey``, and
    ``domain == "opening"`` records are skipped because hosted openings are already billed
    as products elsewhere in the BOM. Rows reconcile 1:1 with ``model.canvas_objects``
    minus that exclusion — nothing placed is silently dropped.
    """
    Row = dict[str, object]
    groups: dict[tuple[str, str, str], Row] = {}
    for item in model.canvas_objects:
        if item.domain == "opening":
            continue
        key = (item.type_ref or item.kind, item.domain, item.storey)
        row = groups.get(key)
        if row is None:
            row = groups[key] = {"type": key[0], "domain": item.domain,
                                 "storey": item.storey, "count": 0, "tags": []}
        row["count"] = int(row["count"]) + 1
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(item.tag)
    return [{**groups[key], "tags": sorted(groups[key]["tags"])} for key in sorted(groups)]


def floor_heat_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per resolved radiant zone: the wire/element length the order is placed for.

    This lived as a patch inside the `haus takeoff` CLI command; it belongs in the BOM
    payload so every consumer (CLI, server, pricing) reads the same rows.
    """
    return [{"tag": zone.tag, "storey": zone.storey, "system": zone.system,
             "wire_length_ft": round(zone.wire_length_m * _M_TO_FT, 1)}
            for zone in model.floor_heat]

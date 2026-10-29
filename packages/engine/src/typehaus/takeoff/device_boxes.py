"""Device boxes and their covers or rings, each (→ resolve/device_boxes.py, decision #93).

The device itself bills in ``[placeables]`` by its type; this is the box behind it and the
cover or ring in front, so neither is billed twice.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel


def device_box_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per box or cover Product: count, role, mounting, and the devices it serves."""
    rows: dict[str, dict[str, object]] = {}
    for box in model.device_boxes:
        for role, ref in (("box", box.box_product), ("cover", box.cover_product)):
            if ref is None:
                continue
            product = model.plan.library.product(ref)
            row = rows.setdefault(ref, {
                "product": ref, "role": role,
                "name": (product.name or product.model) if product is not None else ref,
                "mountings": set(), "count": 0, "tags": []})
            row["count"] = int(row["count"]) + 1
            mountings = row["mountings"]
            assert isinstance(mountings, set)
            mountings.add(box.mounting)
            tags = row["tags"]
            assert isinstance(tags, list)
            tags.append(box.device_tag)
    return [{**row, "mountings": sorted(row["mountings"]),  # type: ignore[arg-type]
             "tags": sorted(row["tags"])}  # type: ignore[arg-type]
            for row in (rows[key] for key in sorted(rows))]

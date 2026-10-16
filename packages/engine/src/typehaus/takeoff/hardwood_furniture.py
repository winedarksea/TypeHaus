"""Shop-built furniture in the milling schedule: each placed piece's authored cut list.

A view, like the rest of ``hardwood``: the piece is priced in placeables (``also_in_placeables``).
Parts of one size and stock across every occurrence share a row; ``location`` names the part.
"""

from __future__ import annotations

from collections.abc import Mapping

from typehaus.resolve.model import ResolvedModel


def furniture_cut_rows(model: ResolvedModel, materials: Mapping[str, object],
                       max_board_width_in: float | None) -> list[dict[str, object]]:
    from typehaus.takeoff.hardwood import _piece_row

    types = {t.tag: t for t in model.plan.library.furniture_types if t.cut_list}
    groups: dict[tuple, list[str]] = {}
    for obj in model.canvas_objects:
        product = types.get(obj.type_ref or "") if obj.kind == "Furniture" else None
        if product is None:
            continue
        for cut in product.cut_list:
            ref = cut.material_ref or product.wood_material_ref
            if not getattr(materials.get(ref or ""), "requires_custom_milling", False):
                continue
            key = (cut.part, ref, round(cut.thickness.inches, 3), round(cut.width.inches, 3),
                   round(cut.length.inches, 3))
            groups.setdefault(key, []).extend([obj.tag] * cut.count)
    rows = []
    for (part, ref, thickness, width, length), tags in groups.items():
        row = _piece_row("furniture", ref, materials, len(tags), thickness, width, length,
                         max_board_width_in, tags, {"also_in_placeables": True})
        row["location"] = part
        rows.append(row)
    return rows

"""Bench cut lists from the installed parts; an unpriced view of placeable costs."""
from __future__ import annotations

from typehaus.model.bench_parts import bench_parts
from typehaus.quantities import M_PER_IN


def bench_cut_rows(model, stock_kind: str, max_board_width_in=None) -> list[dict]:
    from typehaus.takeoff.hardwood import _piece_row

    types = {t.tag: t for t in model.plan.library.furniture_types if t.built_in_bench}
    materials = {material.tag: material for material in model.plan.library.materials}
    rows = []
    for obj in model.canvas_objects:
        product = types.get(obj.type_ref)
        if product is None or obj.kind != "Furniture":
            continue
        for part in bench_parts(product.built_in_bench):
            if part.stock_kind != stock_kind:
                continue
            thickness, width, length = (value / M_PER_IN for value in
                                         (part.thickness_m, part.width_m, part.length_m))
            material = materials[part.material_ref]
            if stock_kind == "solid wood":
                row = _piece_row("furniture", part.material_ref, materials, 1,
                                 thickness, width, length, max_board_width_in, [obj.tag],
                                 {"also_in_placeables": True})
            else:
                row = {"use": "furniture panel", "material": part.material_ref,
                       "species": material.panel_veneer_species, "pieces": 1,
                       "finished_thickness_in": round(thickness, 4),
                       "finished_width_in": round(width, 4),
                       "finished_length_in": round(length, 4), "tags": [obj.tag],
                       "panel_grade": material.panel_face_grade, "panel_core": material.panel_core,
                       "nominal_stock": f'{material.panel_nominal_thickness_in:g} in panel',
                       "panel_area_sqft": round(width * length / 144, 4),
                       "finish": material.finish, "material_source": material.source,
                       "also_in_placeables": True}
            row.update(location=part.name, stock_kind=stock_kind,
                       grain_direction=part.grain_direction, shape_note=part.shape_note)
            row["stock_note"] = "; ".join(filter(None, (row.get("stock_note"),
                                                         part.shape_note, material.source)))
            rows.append(row)
    return rows

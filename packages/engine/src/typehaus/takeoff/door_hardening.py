"""Purchased hardware sets and per-face field coatings."""
from collections import defaultdict

from typehaus.takeoff.hardware_row import hardware_row


def authored_hardware_rows(model):
    types = {item.tag: item for item in model.plan.library.door_types}
    products = {item.tag: item for item in model.plan.library.products}
    grouped = {}
    for opening in model.openings:
        spec = types.get(opening.type_ref) if opening.is_door else None
        for item in spec.hardware if spec else ():
            key = (item.product_ref, item.role, item.installation)
            entry = grouped.setdefault(key, [0, []])
            entry[0] += item.quantity
            entry[1].append(opening.tag)
    rows = []
    for (ref, role, instruction), (count, tags) in sorted(grouped.items()):
        product = products.get(ref)
        row = hardware_row(None, scope="door hardware (authored)", count=count,
                           basis=instruction, tags=tags)
        row.update(hardware_tag=ref, role=role,
                   description=product.name if product else ref,
                   manufacturer=product.brand if product else None,
                   part_number=ref,
                   source=product.url if product else None)
        rows.append(row)
    return rows


def door_field_paint_rows(model):
    types = {item.tag: item for item in model.plan.library.door_types}
    areas = defaultdict(float)
    for opening in model.openings:
        spec = types.get(opening.type_ref) if opening.is_door else None
        if spec is None or spec.field_finish is None:
            continue
        geometry = model.geometry.by_uid(opening.uid)
        # Projected leaf/frame face area, once per face; glass is never painted.
        from shapely.geometry import Polygon

        from typehaus.resolve.geometry import wall_frame

        wall = model.wall(opening.host_wall)
        origin, tangent, _normal, _run = wall_frame(wall)
        face_area = 0.0
        for part in geometry.parts:
            if part.key.split(":")[0] not in {"leaf", "frame", "jamb_liner", "mullion"}:
                continue
            if part.key.endswith(":interior"):
                continue
            if part.material_key == "glass":
                continue
            projections = []
            for solid in part.solids:
                stations = [sum((point[i] - origin[i]) * tangent[i] for i in (0, 1))
                            for point in solid.ring]
                low, high = min(stations), max(stations)
                projections.append(Polygon([(low, solid.z0_m), (high, solid.z0_m),
                                            (high, solid.z1_m), (low, solid.z1_m)]))
            from typehaus.resolve.overlay import union_all
            face_area += union_all(projections).area
        for material in spec.field_finish:
            areas[material] += face_area
    return [dict(scope="door field paint", function="finish", material=ref,
                 thickness_in=0.0, net_area_sqft=round(area / .09290304, 1),
                 also_in_sheet_goods=False) for ref, area in sorted(areas.items())]

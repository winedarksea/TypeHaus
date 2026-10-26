"""Product envelope dimensions are distinct from the framed hole around a unit."""


def opening_product_dimensions(model, opening):
    if opening.is_door:
        product = next((t for t in model.plan.library.door_types
                        if t.tag == opening.type_ref), None)
        dimensions = product.catalog_dimensions if product else None
        if dimensions:
            return dimensions.unit_width.meters, dimensions.unit_height.meters
    return opening.width_m, opening.height_m


def opening_product_area_m2(model, opening):
    width, height = opening_product_dimensions(model, opening)
    return width * height

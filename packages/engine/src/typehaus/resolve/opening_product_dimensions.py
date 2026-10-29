"""Product envelope dimensions are distinct from the framed hole around a unit."""


def opening_product_dimensions(model, opening):
    sizing = getattr(opening, "sizing", None)
    if sizing is not None and sizing.installed_unit is not None:
        return sizing.installed_unit
    return opening.width_m, opening.height_m


def opening_product_area_m2(model, opening):
    width, height = opening_product_dimensions(model, opening)
    return width * height

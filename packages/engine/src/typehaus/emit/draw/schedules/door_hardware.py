"""Readable hardware sets and installer instructions for A-601."""


def hardware_set_marks(model):
    used = {opening.type_ref for opening in model.openings if opening.is_door}
    types = sorted((spec for spec in model.plan.library.door_types
                    if spec.tag in used and spec.hardware), key=lambda spec: spec.tag)
    return {spec.tag: f"HW-{index}" for index, spec in enumerate(types, 1)}


def hardware_schedule_rows(model):
    marks = hardware_set_marks(model)
    products = {product.tag: product for product in model.plan.library.products}
    rows = []
    for spec in sorted(model.plan.library.door_types, key=lambda spec: spec.tag):
        if spec.tag not in marks:
            continue
        grouped = {}
        for item in spec.hardware:
            key = (item.role, item.product_ref, item.installation)
            count, heights = grouped.setdefault(key, [0, []])
            grouped[key][0] = count + item.quantity
            if item.height:
                heights.append(f'{item.height.inches:g}"')
        for (role, ref, installation), (quantity, heights) in grouped.items():
            product = products.get(ref)
            rows.append((marks[spec.tag], role.replace("_", " "),
                         f"{product.brand} {product.model}" if product else ref,
                         str(quantity), ", ".join(heights) if heights else "Full / kit",
                         installation))
    return rows


def hardware_tables(model):
    """A-601's hardware sets and their framing notes, as paged tables (wrapped, never cut)."""
    from typehaus.emit.draw.schedules.paged_tables import PagedTable, wrap_cells

    rows = hardware_schedule_rows(model)
    if not rows:
        return []
    types = {mark: tag for tag, mark in hardware_set_marks(model).items()}
    keyed = [(mark if index == 0 or rows[index - 1][0] != mark else "",
              types[mark] if index == 0 or rows[index - 1][0] != mark else "", *rest)
             for index, (mark, *rest) in enumerate(rows)]
    return [
        PagedTable("HARDWARE SETS — QUANTITIES PER OPENING; HEIGHTS ABOVE LEAF BOTTOM",
                   ("HW set", "Door type", "Role", "Product", "Qty", "Height", "Installation"),
                   wrap_cells(keyed, {3: 34, 6: 96})),
        PagedTable("HARDWARE NOTES", ("Note",), (
            ("Doubled kings/jacks; full-depth backing at hardware anchors.",),
            ("ccSPF in adjoining clear jamb bays; dry sheathing before spraying.",),
            ("Entry field finish: black exterior / white interior.",))),
    ]

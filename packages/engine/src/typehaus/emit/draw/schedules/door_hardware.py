"""Readable hardware sets and installer instructions for A-601."""
import textwrap


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


def draw_hardware_schedule(fig, model):
    from typehaus.emit.draw.sheet_writer import section

    rows = hardware_schedule_rows(model)
    if not rows:
        return
    section(fig, .04, .51, "HARDWARE SETS — QUANTITIES PER OPENING; HEIGHTS ABOVE LEAF BOTTOM")
    widths = (.055, .10, .18, .035, .06, .57)
    # Explicit line wrapping retains every installation instruction on the sheet.
    wraps = (10, 19, 34, 5, 16, 112)
    wrapped = [tuple("\n".join(textwrap.wrap(str(cell), width=width))
                     for cell, width in zip(row, wraps, strict=True)) for row in rows]
    ax = fig.add_axes((.04, .18, .92, .31))
    ax.axis("off")
    table = ax.table(cellText=wrapped,
                     colLabels=("HW set", "Role", "Product", "Qty", "Height", "Installation"),
                     colWidths=widths, cellLoc="left", colLoc="left", bbox=(0, 0, 1, 1))
    table.auto_set_font_size(False)
    table.set_fontsize(6)
    weights = [1] + [max(cell.count("\n")+1 for cell in row) for row in wrapped]
    for (row, _column), cell in table.get_celld().items():
        cell.set_height(weights[row]/sum(weights))
    marks = hardware_set_marks(model)
    mapping = "; ".join(f"{mark}: {tag}" for tag, mark in marks.items())
    fig.text(.04, .155, mapping, fontsize=7)
    fig.text(.04, .135, "Doubled kings/jacks; full-depth backing at hardware anchors. "
             "ccSPF in adjoining clear jamb bays; dry sheathing before spraying. "
             "Entry field finish: black exterior / white interior.", fontsize=6)

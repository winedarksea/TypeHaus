"""Track component order sheet; stock procurement differs from installed rail length.

These are component descriptions beside the placeable estimate, not a second priced
assembly. Unknown vendor prices remain quote-required, without an invented allowance.
"""

from typehaus.model.electrical import luminaire_types
from typehaus.takeoff.lighting_supplies import electrical_devices


def track_lighting_materials(model):
    types = luminaire_types(model.plan.library)
    devices = electrical_devices(model)
    device_types = {t.tag: t for t in model.plan.library.electrical_device_types}
    rows, supplies = [], set()
    for device in sorted(devices.values(), key=lambda d: d.tag):
        product = types.get(device.type_ref)
        spec = getattr(product, "track_lighting", None)
        if spec is None:
            continue
        components = [("rail_stock", spec.rail_product_ref, 1),
                      ("end_feed", spec.feed_product_ref, 1)]
        head_counts, optic_counts = {}, {}
        for head in spec.heads:
            ref = head.product.product_ref
            head_counts[ref] = head_counts.get(ref, 0) + 1
            optic = head.product.optic_product_refs.get(head.beam_degrees)
            if optic is not None:
                optic_counts[optic] = optic_counts.get(optic, 0) + 1
        components.extend(("head", ref, count) for ref, count in sorted(head_counts.items()))
        components.extend(("optic", ref, count) for ref, count in sorted(optic_counts.items()))
        if device.psu_ref and device.psu_ref not in supplies:
            supply_type = device_types.get(getattr(devices.get(device.psu_ref), "type_ref", None))
            components.append(("supply", getattr(supply_type, "product_ref", None), 1))
            supplies.add(device.psu_ref)
        for item, ref, count in components:
            rows.append({"assembly": device.tag, "type": device.type_ref,
                         "mark": product.type_mark, "item": item, "product": ref,
                         "quantity": count, "unit": "EA", "pricing": "quote_required",
                         **({"stock_length_in": round(spec.stock_length.inches, 6),
                             "installed_length_in": round(spec.rail_length.inches, 6),
                             "included": "end caps, slot covers, anchors, screws"}
                            if item == "rail_stock" and spec.system == "magnetic_24v" else
                            {"stock_length_in": round(spec.stock_length.inches, 6),
                             "installed_length_in": round(spec.rail_length.inches, 6)}
                            if item == "rail_stock" else {})})
    return rows

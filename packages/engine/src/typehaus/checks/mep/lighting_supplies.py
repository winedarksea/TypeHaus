"""Supply-fed point luminaires: voltage, branch ownership, controls, combined demand."""

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.registry import Tier, check
from typehaus.findings import Result
from typehaus.model.electrical import luminaire_types
from typehaus.takeoff.lighting_supplies import PSU_SIZING_FACTOR, electrical_devices, supply_demands


@check(Tier.ADVISORY, "electrical.point_luminaire_psu")
def point_luminaire_psu(ctx):
    cid = "electrical.point_luminaire_psu"
    types = luminaire_types(ctx.plan.library)
    device_types = {product.tag: product for product in ctx.plan.library.electrical_device_types}
    devices = electrical_devices(ctx.model)
    demand = supply_demands(ctx.model)
    out, checked, supplies = [], 0, set()

    def fail(message, *tags):
        out.append(advisory(cid, message, tags, Result.FAIL))

    for device in devices.values():
        product = types.get(device.type_ref)
        if product is None:
            if device.psu_ref:
                fail(f"{device.tag} is not a luminaire but names a lighting supply", device.tag)
            continue
        if product.voltage == 120 and device.psu_ref is None:
            continue
        checked += 1
        if product.voltage == 120:
            fail(f"{device.tag} is 120V and cannot use a DC lighting supply", device.tag)
        if device.circuit is not None:
            fail(f"{device.tag} must leave branch ownership to its supply", device.tag)
        supply = devices.get(device.psu_ref)
        if supply is None:
            fail(f"{device.tag} is {product.voltage}V and names no existing supply", device.tag)
            continue
        supplies.add(supply.tag)
        supply_type = device_types.get(supply.type_ref)
        if supply.kind.value != "junction_box" or getattr(supply_type, "output_voltage", None) \
                != product.voltage:
            fail(f"{device.tag} requires a compatible {product.voltage}V DC supply", device.tag,
                 supply.tag)
        if supply.circuit is None or supply.circuit not in {
                c.tag for c in ctx.plan.library.circuits}:
            fail(f"{supply.tag} needs an existing branch circuit", supply.tag)
        if set(device.controlled_by) != set(supply.controlled_by):
            fail(f"{device.tag} and {supply.tag} must share the same controls",
                 device.tag, supply.tag)

    for tag in sorted(supplies):
        rating = getattr(device_types.get(devices[tag].type_ref), "load_va", None)
        required = demand.get(tag, 0.0) * PSU_SIZING_FACTOR
        if rating is None:
            out.append(unknown(cid, f"{tag} states no supply rating", (tag,)))
        elif rating < required:
            fail(f"{tag} is rated {rating:g}W; combined lighting demand requires {required:g}W "
                 "at the 125% factor", tag)
    if not out:
        out.append(passed(cid, f"{checked} supply-fed point luminaires have compatible supplies")
                   if checked else unknown(cid, "no supply-fed point luminaires modeled"))
    return out

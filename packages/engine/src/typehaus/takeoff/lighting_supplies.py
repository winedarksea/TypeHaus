"""Shared supply demand and branch ownership for point lights and linear runs."""

from __future__ import annotations

from typehaus.model.electrical import luminaire_types

# The house's continuous-load sizing margin applies to the combined DC demand.
PSU_SIZING_FACTOR = 1.25
METERS_TO_FEET = 3.280839895013123


def electrical_devices(model):
    return {element.tag: element for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"}


def supplied_loads(model):
    types = luminaire_types(model.plan.library)
    for device in electrical_devices(model).values():
        product = types.get(device.type_ref)
        if product is not None and device.psu_ref:
            yield device.psu_ref, device.tag, "fixture", product.watts or 0.0, 0.0
    for run in model.light_runs:
        if run.psu_ref:
            product = types.get(run.type_ref)
            length_ft = run.length_m * METERS_TO_FEET
            watts = (product.watts_per_ft or 0.0) * length_ft if product is not None else 0.0
            yield run.psu_ref, run.tag, "run", watts, length_ft


def supply_demands(model):
    demand = {}
    for psu, _tag, _kind, watts, _length in supplied_loads(model):
        demand[psu] = demand.get(psu, 0.0) + watts
    return demand


def effective_lighting_circuit(load, devices):
    supply = devices.get(getattr(load, "psu_ref", None))
    return supply.circuit if supply is not None else getattr(load, "circuit", None)

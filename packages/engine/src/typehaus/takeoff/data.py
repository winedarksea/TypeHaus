"""Structured-cabling take-offs: the device schedule, the raceways, and the PoE budget.

The low-voltage twin of ``takeoff/lighting.py``, and a projection in exactly the same sense:
no row is hand-summed, and a device whose type states no PoE draw reports ``None`` rather
than a plausible-looking number.

The PoE budget is here rather than on the panel schedule because that is where the load
actually lives. A PoE access point names no ``circuit`` — its power arrives over the data
cable — so the panel schedule cannot see it and should not: what a reader needs to know is
whether the *switch* has headroom, which is a different question from whether the breaker
does. The switch's own draw is on its branch circuit like any other appliance.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123


def _device_types(model: ResolvedModel) -> dict:
    return {product.tag: product for product in model.plan.library.electrical_device_types}


def _data_devices(model: ResolvedModel) -> list:
    return [element for storey in model.plan.storeys
            for element in model.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"
            and element.kind.value == "data_outlet"]


def data_device_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per low-voltage device, sorted by tag — the E-603 device table."""
    types = _device_types(model)
    rows: list[dict[str, object]] = []
    for device in sorted(_data_devices(model), key=lambda d: d.tag):
        product = types.get(device.type_ref or "")
        mount = getattr(device, "mount", None)
        rows.append({
            "tag": device.tag,
            "type_ref": device.type_ref or "",
            "type_name": getattr(product, "name", None) or "",
            "room": device.room or "",
            "mount": mount.kind.value if mount is not None else "floor",
            "mount_elevation_ft": (mount.elevation.meters * _M_TO_FT
                                   if mount is not None and mount.elevation is not None
                                   else None),
            # None, not 0.0: a device with no stated PoE draw has an unknown one, and the
            # budget below reports how many rows it could not account for.
            "poe_watts": getattr(product, "poe_watts", None),
            "circuit": device.circuit or "",
        })
    return rows


def data_raceway_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Data and spare raceway by trade size — the pipe an installer actually orders.

    Power raceways are ``conduit_takeoff``'s business. A capped spare appears here rather
    than there because the question it answers ("what can I still pull, and how big is it?")
    is the low-voltage reader's, not the electrician's.
    """
    groups: dict[tuple[float, str], dict[str, object]] = {}
    for run in model.conduits:
        if run.service not in ("data", None):
            continue
        key = (run.trade_size_m, run.service or "spare")
        row = groups.setdefault(key, {
            "trade_size_in": round(run.trade_size_m / M_PER_IN, 2),
            "service": run.service or "spare",
            "runs": 0, "length_m": 0.0, "tags": []})
        row["runs"] = int(row["runs"]) + 1
        row["length_m"] = float(row["length_m"]) + run.length_m
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(run.tag)
    return [
        {"trade_size_in": row["trade_size_in"], "service": row["service"],
         "runs": int(row["runs"]),
         "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1),
         "tags": sorted(row["tags"])}
        for row in (groups[key] for key in sorted(groups))
    ]


def poe_budget(model: ResolvedModel) -> dict[str, object]:
    """Connected PoE watts against the switch — the number that decides the next switch.

    ``unknown_devices`` is the honest half: a device whose type states no ``poe_watts``
    is counted as unrated rather than as zero, so a budget that looks comfortable cannot be
    hiding an unrated camera.
    """
    types = _device_types(model)
    devices = _data_devices(model)
    if not devices:
        return {}
    rated = [getattr(types.get(d.type_ref or ""), "poe_watts", None) for d in devices]
    powered = [watts for watts in rated if watts]
    return {
        "devices": len(devices),
        "powered_devices": len(powered),
        "unknown_devices": sum(1 for d, watts in zip(devices, rated, strict=True)
                               if watts is None and d.circuit is None),
        "connected_watts": round(sum(powered), 1),
        "basis": "sum of ElectricalDeviceType.poe_watts over data devices",
    }

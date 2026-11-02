"""Dimensioned terminal inlet joints, independent of the legacy implicit-boot allowance."""

from __future__ import annotations

import math

from typehaus.quantities import inch
from typehaus.resolve.terminal_necks import terminal_inlet

TERMINAL_JOINT_TOLERANCE_M = inch(1 / 16).meters


def inlet_connection_error(model, register_tag: str) -> str | None:
    inlet = terminal_inlet(model, register_tag)
    if inlet is None:
        return "dimensioned terminal inlet could not be placed"
    centre, normal, width, height = inlet
    register = model.plan.by_tag(register_tag)
    duct = next((d for d in model.ducts if d.tag == register.duct_ref), None)
    if duct is None or len(duct.path) < 2 or not duct.z_m:
        return "feeding duct has no resolved 3D endpoint"
    endpoint = (*duct.path[-1], duct.z_m[-1])
    tolerance = TERMINAL_JOINT_TOLERANCE_M
    if max(abs(a - b) for a, b in zip(endpoint, centre, strict=True)) > tolerance:
        return "feeding duct endpoint misses the dimensioned inlet centre"
    catalog = next(t for t in model.plan.library.register_types if t.tag == register.type_ref)
    if catalog.neck.inlet.section == "round":
        if duct.diameter_m is None or abs(duct.diameter_m - width) > tolerance:
            return "feeding duct diameter does not match the round inlet"
    elif (duct.diameter_m is not None or abs(duct.width_m - width) > tolerance
          or abs(duct.depth_m - height) > tolerance):
        return "feeding duct section does not match the rectangular inlet"
    if abs(duct.z_m[-2] - duct.z_m[-1]) > tolerance:
        return "feeding duct mouth is pitched instead of square to the inlet"
    # The final leg must approach the inlet from its outward side. A pitched approach is
    # finished before the final leg, keeping the mouth square to the inlet.
    dx, dy = (duct.path[-2][i] - duct.path[-1][i] for i in (0, 1))
    length = math.hypot(dx, dy)
    if length <= tolerance or (dx * normal[0] + dy * normal[1]) / length < 1 - 1e-6:
        return "feeding duct approaches the wrong side or direction of the inlet"
    return None

"""Formed flashing sheets along an authored run's plan path."""

from __future__ import annotations

import math

from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.sheet_geometry import combine_sheets, sheet_between

_EPS = 1e-10


def formed_run_mesh(element, a, b) -> GMesh:
    section = element.section
    half = element.thickness.meters / 2
    span = math.dist(a, b)
    if span <= _EPS:
        raise ValueError(f"{element.tag}: flashing path has a repeated point")
    ux, uy = (b[0] - a[0]) / span, (b[1] - a[1]) / span
    sign = -1 if element.back_side == "left" else 1
    nx, ny = -uy * sign, ux * sign
    top = element.top_elevation.meters
    front_z = top - 2 * half * section.slope

    def point(depth, z):
        return (a[0] + nx * (depth - half), a[1] + ny * (depth - half), z)

    legs = [(point(0, top), point(2 * half, front_z))]
    if section.profile == "counter" and section.upstand.meters > 0:
        legs.append((point(0, top + section.upstand.meters), point(0, top)))
    elif section.profile == "cap" and section.drip.meters > 0:
        legs.append((point(0, top), point(0, top - section.drip.meters)))
    if section.drip.meters > 0:
        legs.append((point(2 * half, front_z), point(2 * half, front_z - section.drip.meters)))
    if section.hem.meters > 0:
        legs.append((point(2 * half, front_z - section.drip.meters),
                     point(2 * half - section.hem.meters, front_z - section.drip.meters)))
    return combine_sheets([sheet_between(p, q, (b[0] - a[0], b[1] - a[1], 0),
                                          section.sheet_thickness.meters,
                                          normal_hint=(nx, ny, 1.0)) for p, q in legs])

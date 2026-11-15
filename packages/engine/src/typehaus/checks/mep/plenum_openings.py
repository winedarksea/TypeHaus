"""A duct must cross a fabricated plenum's opening with the matching section.

Case containment is insufficient: a duct can end inside a sealed sheet, or cross
its face at the wrong station. This grades the authored design, not shop approval.
"""

import math

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import Tier, check
from typehaus.model.enums import AIR_SERVICE_DUCT_SYSTEM
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import placed_ports
from typehaus.resolve.sweep import leg_frame

CHECK_ID = "mep.plenum_openings"
SECTION_TOLERANCE_M = M_PER_IN / 16
AXIS_ALIGNMENT_TOLERANCE = 1e-6


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _matches(duct, port, local_port, rotation):
    if port.duct_system is not None and duct.system != port.duct_system:
        return False
    if (port.direction is None or local_port.direction is None
            or local_port.section_m() is None):
        return False
    normal = port.direction
    axis = max(range(3), key=lambda i: abs(local_port.direction[i]))
    cos, sin = math.cos(math.radians(rotation)), math.sin(math.radians(rotation))
    basis = [(cos, sin, 0), (-sin, cos, 0), (0, 0, 1)]
    face_axes = [basis[i] for i in range(3) if i != axis]
    centre = (port.x_m, port.y_m, port.z_m)
    points = [(*xy, z) for xy, z in zip(duct.path, duct.z_m, strict=True)]
    for first, last in zip(points, points[1:], strict=False):
        delta = tuple(b - a for a, b in zip(first, last, strict=True))
        length = math.sqrt(_dot(delta, delta))
        if length == 0:
            continue
        direction = tuple(value / length for value in delta)
        if abs(_dot(direction, normal)) < 1 - AXIS_ALIGNMENT_TOLERANCE:
            continue
        distance = _dot(tuple(c - a for c, a in zip(centre, first, strict=True)), normal)
        fraction = distance / _dot(delta, normal)
        if not 0 <= fraction <= 1:
            continue
        intersection = tuple(a + fraction * d for a, d in zip(first, delta, strict=True))
        if math.dist(intersection, centre) > SECTION_TOLERANCE_M:
            continue
        if local_port.connection_size is not None:
            if duct.diameter_m is not None and abs(
                    duct.diameter_m - local_port.connection_size.meters) <= SECTION_TOLERANCE_M:
                return True
        elif duct.diameter_m is None and duct.width_m and duct.depth_m:
            right, up = leg_frame(direction)
            spans = [abs(_dot(right, basis)) * duct.width_m
                     + abs(_dot(up, basis)) * duct.depth_m for basis in face_axes]
            if all(abs(a - b) <= SECTION_TOLERANCE_M
                   for a, b in zip(spans, local_port.section_m(), strict=True)):
                return True
    return False


@check(Tier.INTEGRITY, CHECK_ID)
def plenum_openings(ctx):
    types = {t.tag: t for t in ctx.plan.library.equipment_types
             if t.model_representation and t.model_representation.symbol == "sheet-metal-plenum"}
    placed = {(p.equipment_tag, p.port_tag): p for p in placed_ports(ctx.model)}
    findings = []
    for obj in ctx.model.canvas_objects:
        product = types.get(obj.type_ref)
        if product is None:
            continue
        for local_port in product.ports:
            if local_port.service not in AIR_SERVICE_DUCT_SYSTEM:
                continue
            port = placed[(obj.tag, local_port.tag)]
            matches = [duct.tag for duct in ctx.model.ducts
                       if _matches(duct, port, local_port, obj.rotation_degrees)]
            if not matches:
                findings.append(failed(CHECK_ID, f"{obj.tag}/{port.port_tag}: no matching duct "
                                       "crosses the declared opening at its centre and section.",
                                       (obj.tag,)))
            else:
                result = passed if port.exact else unknown
                caveat = "" if port.exact else "Shop dimensions remain provisional."
                findings.append(result(CHECK_ID, f"{obj.tag}/{port.port_tag}: {', '.join(matches)} "
                                       "crosses the design opening with matching section. "
                                       + caveat,
                                       (obj.tag, *matches)))
    return findings or [not_applicable(CHECK_ID, "No port-driven sheet-metal plenum is placed.")]

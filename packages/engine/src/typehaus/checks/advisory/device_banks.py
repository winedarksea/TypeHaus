"""ADVISORY — gang banks and the wall plates they take (→ resolve/device_banks.py).

``advisory.device_bank`` lists each bank of two or more devices: members, the snap each
took, its box and plate. ``advisory.wall_plate_clearance`` reads each derived plate's plan
ring and z band against the wall's ends, door casings, bodies, columns (posts) and other
plates; a clash that a ``standard`` plate of the same openings would clear says so.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Polygon

from typehaus.checks._authoring import not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory
from typehaus.quantities import M_PER_IN
from typehaus.resolve.box_members import box_members
from typehaus.resolve.solid_categories import SOLID_CATEGORIES

BANK_ID = "advisory.device_bank"
CLEAR_ID = "advisory.wall_plate_clearance"
_BODY_CLEAR_M = M_PER_IN / 8
_EPS_M2 = 1e-8  # plan overlap under this is two faces touching


def _tags(box: Any) -> tuple[str, ...]:
    return tuple(box.device_tags or (box.device_tag,))


@check(Tier.ADVISORY, BANK_ID)
def device_bank(ctx: CheckContext) -> list[Finding]:
    """Each bank of two or more devices: members, snaps, box and plate."""
    out: list[Finding] = []
    for box in sorted(ctx.model.device_boxes, key=lambda b: b.device_tag):
        members = box_members(box)
        if len(members) < 2:
            continue
        snaps = ", ".join(f"{m.tag} {m.shift_m / M_PER_IN:+.2f}\"" for m in members)
        plate = (f"{box.plate_product} ({box.plate_family})" if box.plate_product
                 else "no plate")
        out.append(passed(
            BANK_ID, f"{'+'.join(m.tag for m in members)}: {box.gangs}-gang "
                     f"{box.box_product} on {box.wall_tag}, {plate}; snapped {snaps}",
            _tags(box)))
    return out or [not_applicable(BANK_ID, "no devices share a gang box")]


def _span(points: list[tuple[float, float]], origin: tuple[float, float],
          axis: tuple[float, float]) -> tuple[float, float]:
    values = [(x - origin[0]) * axis[0] + (y - origin[1]) * axis[1] for x, y in points]
    return min(values), max(values)


def _band(box: Any, height_m: float) -> tuple[float, float]:
    mid = (box.z0_m + box.z1_m) / 2
    return mid - height_m / 2, mid + height_m / 2


def _standard_ring(box: Any, width_m: float) -> list[tuple[float, float]]:
    """A plate of ``width_m`` on the same centre and face as the box's own."""
    ring = list(box.plate_footprint)
    cx = sum(x for x, _ in ring) / len(ring)
    cy = sum(y for _, y in ring) / len(ring)
    nx, ny = box.normal
    tx, ty = -ny, nx
    half_t = box.plate_thickness_m / 2
    half_w = width_m / 2
    return [(cx + tx * a * half_w + nx * b * half_t, cy + ty * a * half_w + ny * b * half_t)
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _clashes(ctx: CheckContext, box: Any, ring: list[tuple[float, float]],
             band: tuple[float, float], others: list[tuple[Any, Polygon, tuple[float, float]]]
             ) -> list[str]:
    """What the plate (``ring`` over ``band``) lands on, named."""
    model = ctx.model
    poly = Polygon(ring)
    out: list[str] = []
    wall = model.wall(box.wall_tag)
    if wall is not None:
        (x0, y0), (x1, y1) = wall.axis
        length = math.hypot(x1 - x0, y1 - y0) or 1.0
        lo, hi = _span(ring, (x0, y0), ((x1 - x0) / length, (y1 - y0) / length))
        if lo < -1e-3 or hi > length + 1e-3:
            out.append(f"the end of {box.wall_tag}")
    for casing in getattr(model, "door_casings", ()):
        if casing.wall_tag != box.wall_tag:
            continue
        hit = any(p.z0_m < band[1] and p.z1_m > band[0]
                  and poly.intersection(Polygon(p.outline)).area > _EPS_M2
                  for p in casing.pieces)
        if hit:
            out.append(f"{casing.tag} casing")
    grown = poly.buffer(_BODY_CLEAR_M, join_style=2)
    mine = set(_tags(box))
    # Wall-hosted casework only (loose furniture just stands in front), and only a plate
    # that straddles its edge: one wholly inside (a sink base, a firebox pocket) is meant.
    for obj in model.canvas_objects:
        if (obj.kind == "ElectricalDevice" or obj.tag in mine or obj.storey != box.storey
                or obj.attachment_wall is None
                or obj.body_z0_m is None or obj.body_z1_m is None or len(obj.footprint) < 3
                or obj.body_z0_m >= band[1] or obj.body_z1_m <= band[0]):
            continue
        body = Polygon(obj.footprint)
        inside = (body.buffer(1e-4, join_style=2).covers(poly)
                  and obj.body_z0_m <= band[0] + 1e-4 and obj.body_z1_m >= band[1] - 1e-4)
        if not inside and grown.intersection(body).area > _EPS_M2:
            out.append(obj.tag)
    # A post or column (a timber standing in the stud line, a steel column) is never meant.
    for solid in getattr(model, "solids", ()):
        row = SOLID_CATEGORIES.get(solid.category)
        if (row is None or row.ifc_class != "IfcColumn" or solid.storey != box.storey
                or solid.z0_m >= band[1] or solid.z1_m <= band[0] or len(solid.outline) < 3):
            continue
        if grown.intersection(Polygon(solid.outline)).area > _EPS_M2:
            out.append(solid.tag)
    for other, other_poly, other_band in others:
        if (other is not box and other.storey == box.storey
                and other_band[0] < band[1] and other_band[1] > band[0]
                and poly.intersection(other_poly).area > _EPS_M2):
            out.append(f"the plate of {'+'.join(_tags(other))}")
    return out


@check(Tier.ADVISORY, CLEAR_ID)
def wall_plate_clearance(ctx: CheckContext) -> list[Finding]:
    """Each wall plate against its wall's ends, casings, bodies, columns and neighbouring plates."""
    plated = [b for b in sorted(ctx.model.device_boxes, key=lambda b: b.device_tag)
              if b.plate_product and len(b.plate_footprint) >= 3 and b.plate_size_m]
    if not plated:
        return [not_applicable(CLEAR_ID, "no device bank takes a wall plate")]
    others = [(b, Polygon(b.plate_footprint), _band(b, b.plate_size_m[1])) for b in plated]
    standard = next((el for el in ctx.plan.all_elements()
                     if el.element_kind == "BoxStandard"), None)
    out: list[Finding] = []
    for box, _poly, band in others:
        hits = _clashes(ctx, box, list(box.plate_footprint), band, others)
        if not hits:
            continue
        names = "+".join(_tags(box))
        hint = "move the bank or the obstacle"
        if box.plate_family != "standard" and standard is not None:
            slim = standard.plate_for("standard", box.plate_openings)
            if slim is not None:
                w, h = slim.size[0].meters, slim.size[1].meters
                if not _clashes(ctx, box, _standard_ring(box, w), _band(box, h), others):
                    hint = "a standard plate clears"
        width, height = box.plate_size_m
        out.append(advisory(
            CLEAR_ID, f"{names}'s {box.plate_family} plate ({width / M_PER_IN:.2f}\" x "
                      f"{height / M_PER_IN:.2f}\") runs into {', '.join(dict.fromkeys(hits))}; "
                      f"{hint}", (*_tags(box), box.wall_tag), Result.ADVISORY, fix=hint))
    return out or [passed(CLEAR_ID, f"{len(plated)} wall plate(s) clear their wall's ends, "
                                    "casings, bodies, columns and each other")]

"""The one member solid, shared by every emitter.

Three implementations of "what shape is this stick" existed, and they disagreed:

* **IFC** (``emit/ifc/roof.py``) swept the parsed rectangular section along the member's true
  3D axis, handling ``orient`` for an upright stud and ``depth_m`` for the section — correct;
* **glTF** (``emit/gltf/members.py``) used ``width_m / 2`` for *every* half-extent, ignoring
  both ``orient`` and ``depth_m``, so a 2x6 stud came out square in the exported model;
* the **viewer** (``ui/src/three/memberBox.ts``) had a third reading again.

This is the IFC one, ported to the IR: for a member, the section rides its axis through the
centroid, so the solid's faces land on exactly the planes the member record names.
"""

from __future__ import annotations

import math

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_ir import GBox, Vec3
from typehaus.resolve.model import FramedMember

# Degenerate members (a zero-length blocking, a band running out to nothing at a gable) would
# close a shell on a zero-area face, which no importer can tessellate. Matches the IFC
# emitter's own floor.
MINIMUM_EXTENT_M = 1e-4


def _unit_normal(dx: float, dy: float, run: float) -> tuple[float, float]:
    """The plan-frame left normal of the member's run, for offsetting the section width."""
    return -dy / run, dx / run


def member_box(member: FramedMember) -> GBox | None:
    """The member as eight corners, or ``None`` if it is too degenerate to draw.

    Handles the three cases that used to need three code paths:

    * **upright** (``p0 == p1``): a stud, post or king. Its section is placed across
      ``orient`` — the wall direction it stands in — which is exactly what the glTF path
      dropped, squaring off every stud in the export.
    * **raked** (``z*_end_m`` set): the ends sit at different elevations, so the top and
      bottom rings simply carry different z per corner.
    * **level**: the ordinary case.
    """
    section = cross_section(member.profile)
    width = max(section.width_m, MINIMUM_EXTENT_M)
    depth = max(section.depth_m, MINIMUM_EXTENT_M)
    (ax, ay), (bx, by) = member.p0, member.p1
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)

    if run < 1e-9:
        # Upright: the section is a width x depth rectangle in plan, laid out along `orient`
        # (defaulting to +x when the member records none).
        orient = member.orient or (1.0, 0.0)
        norm = math.hypot(orient[0], orient[1]) or 1.0
        ux, uy = orient[0] / norm, orient[1] / norm
        nx, ny = -uy, ux
        hw, hd = width / 2.0, depth / 2.0
        ring = tuple(
            (ax + ux * sw * hw + nx * sd * hd, ay + uy * sw * hw + ny * sd * hd)
            for sw, sd in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        )
        z1 = max(member.z1_m, member.z0_m + MINIMUM_EXTENT_M)
        return GBox(
            corners_bottom=tuple((x, y, member.z0_m) for x, y in ring),
            corners_top=tuple((x, y, z1) for x, y in ring),
        )

    nx, ny = _unit_normal(dx, dy, run)
    half_x, half_y = nx * width / 2.0, ny * width / 2.0
    z0_end = member.z0_m if member.z0_end_m is None else member.z0_end_m
    z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
    z1_start = max(member.z1_m, member.z0_m + MINIMUM_EXTENT_M)
    z1_end = max(z1_end, z0_end + MINIMUM_EXTENT_M)

    # Ring order matches the IFC faceted box: start-left, end-left, end-right, start-right,
    # so bottom and top correspond vertex for vertex.
    plan_and_z = (
        (ax - half_x, ay - half_y, member.z0_m, z1_start),
        (bx - half_x, by - half_y, z0_end, z1_end),
        (bx + half_x, by + half_y, z0_end, z1_end),
        (ax + half_x, ay + half_y, member.z0_m, z1_start),
    )
    bottom: tuple[Vec3, ...] = tuple((x, y, low) for x, y, low, _high in plan_and_z)
    top: tuple[Vec3, ...] = tuple((x, y, high) for x, y, _low, high in plan_and_z)
    return GBox(corners_bottom=bottom, corners_top=top)


def member_part_key(member: FramedMember) -> str:
    return f"member:{member.child_key}"


def member_uid(member: FramedMember) -> str:
    """``"<ownerUid>::<childKey>"`` — the identity the viewer's member picking already uses."""
    return f"{member.parent_uid}::{member.child_key}"

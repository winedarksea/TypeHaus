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

from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.geometry_ir import GBox, GSolid, GSweep, Vec3
from typehaus.resolve.model import FramedMember, SeatCut

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
    if member.plan_outline is not None:
        # GBox is intentionally a quadrilateral-only primitive.  Polygonal stair treads are
        # emitted by the prism-aware callers rather than quietly approximated as a box.
        return None
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
        uw, un = ux * hw, nx * hd
        vw, vn = uy * hw, ny * hd
        ring = ((ax - uw - un, ay - vw - vn), (ax + uw - un, ay + vw - vn),
                (ax + uw + un, ay + vw + vn), (ax - uw + un, ay - vw + vn))
        z1 = max(member.z1_m, member.z0_m + MINIMUM_EXTENT_M)
        return GBox(
            corners_bottom=tuple((x, y, member.z0_m) for x, y in ring),
            corners_top=tuple((x, y, z1) for x, y in ring),
        )

    # A horizontal member shows one section face in plan and stands the other one tall: the
    # wide `depth_m` across for a flat-laid plate/sill/block, the thin `width_m` for a member
    # on edge. Using `width_m` unconditionally (what this did) drew every flat member as a
    # 1.5" square rod running along the wall instead of a 1.5" x 5.5" board lying on it.
    across = max(plan_cross_section_m(section, member.z1_m - member.z0_m), MINIMUM_EXTENT_M)
    nx, ny = _unit_normal(dx, dy, run)
    half_x, half_y = nx * across / 2.0, ny * across / 2.0
    z0_end = member.z0_m if member.z0_end_m is None else member.z0_end_m
    z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
    z1_start = max(member.z1_m, member.z0_m + MINIMUM_EXTENT_M)
    z1_end = max(z1_end, z0_end + MINIMUM_EXTENT_M)

    # Ring order matches the IFC faceted box: start-left, end-left, end-right, start-right,
    # so bottom and top correspond vertex for vertex. Written out rather than zipped from a
    # packed (x, y, low, high) tuple: this function runs 15,160 times per resolve of
    # houses/catlin, and the two generator expressions that used to unpack it were 43,300
    # frame setups each.
    slx, sly = ax - half_x, ay - half_y
    elx, ely = bx - half_x, by - half_y
    erx, ery = bx + half_x, by + half_y
    srx, sry = ax + half_x, ay + half_y
    bottom: tuple[Vec3, ...] = ((slx, sly, member.z0_m), (elx, ely, z0_end),
                                (erx, ery, z0_end), (srx, sry, member.z0_m))
    top: tuple[Vec3, ...] = ((slx, sly, z1_start), (elx, ely, z1_end),
                             (erx, ery, z1_end), (srx, sry, z1_start))
    return GBox(corners_bottom=bottom, corners_top=top)


def member_solid(member: FramedMember) -> GSolid | None:
    """The member's solid — a box, or a swept profile when it carries a birdsmouth.

    The guard is ``member.seat is not None`` and **nothing else**. No ``cross_section()``
    call may precede it: this runs 15,160 times per resolve, and ``member_box`` stays
    untouched below (the parity test pins it, and it is the hot path).
    """
    if member.seat is None:
        return member_box(member)
    return _seated_sweep(member, member.seat)


def _seated_sweep(member: FramedMember, seat: SeatCut) -> GSolid | None:
    """The notched rafter as a profile in its own vertical plane, swept across its width.

    Six points: end-top, far-top, far-bottom, the plumb heel up from the seat to the
    underside, the heel's foot, and the seat's far end. The underside is the straight line
    from ``z0_m`` to ``z0_end_m``, and ``z0_m`` at the bearing end already *is* the seat
    elevation — which is why nothing about the member's elevations has to change for the
    notch to become real.
    """
    (ax, ay), (bx, by) = member.p0, member.p1
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return member_box(member)
    section = cross_section(member.profile)
    half = max(section.width_m, MINIMUM_EXTENT_M) / 2.0
    # Which end bears: the one the heel sits nearer to.
    hx, hy = seat.heel
    near_p0 = math.hypot(hx - ax, hy - ay) <= math.hypot(hx - bx, hy - by)
    near = (ax, ay) if near_p0 else (bx, by)
    far = (bx, by) if near_p0 else (ax, ay)
    z0_near = member.z0_m if near_p0 else (member.z0_end_m
                                           if member.z0_end_m is not None else member.z0_m)
    z1_near = member.z1_m if near_p0 else (member.z1_end_m
                                           if member.z1_end_m is not None else member.z1_m)
    z0_far = (member.z0_end_m if member.z0_end_m is not None else member.z0_m) if near_p0 \
        else member.z0_m
    z1_far = (member.z1_end_m if member.z1_end_m is not None else member.z1_m) if near_p0 \
        else member.z1_m
    # Unit vector from the bearing end toward the far end, and the underside's rise along it.
    ux, uy = (far[0] - near[0]) / run, (far[1] - near[1]) / run
    slope = (z0_far - z0_near) / run
    heel_point = (near[0] + ux * seat.seat_run_m, near[1] + uy * seat.seat_run_m)
    z_underside_at_heel = z0_near + slope * seat.seat_run_m
    z_seat = seat.plate_top_z_m
    if z_underside_at_heel <= z_seat + MINIMUM_EXTENT_M:
        # The underside never rises clear of the seat over the run — no notch to cut.
        return member_box(member)
    # The profile stands on one face of the member, not on its centreline, so that sweeping
    # it the full width lands the solid symmetrically about the axis.
    ox, oy = uy * half, -ux * half
    profile = tuple(
        (x + ox, y + oy, z) for (x, y, z) in (
            (near[0], near[1], z1_near),
            (far[0], far[1], z1_far),
            (far[0], far[1], z0_far),
            (heel_point[0], heel_point[1], z_underside_at_heel),
            (heel_point[0], heel_point[1], z_seat),
            (near[0], near[1], z_seat),
        )
    )
    return GSweep(profile=profile, extrude=(-2.0 * ox, -2.0 * oy, 0.0))


def member_part_key(member: FramedMember) -> str:
    return f"member:{member.child_key}"


def member_uid(member: FramedMember) -> str:
    """``"<ownerUid>::<childKey>"`` — the identity the viewer's member picking already uses."""
    return f"{member.parent_uid}::{member.child_key}"

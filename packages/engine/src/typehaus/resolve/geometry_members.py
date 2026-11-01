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

    Handles three cases:

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
    # A tapered member's vertical extent says nothing about which way it was laid, so it
    # carries its own plan width; see FramedMember.plan_width_m.
    across = max(member.plan_width_m
                 or plan_cross_section_m(section, member.z1_m - member.z0_m),
                 MINIMUM_EXTENT_M)
    nx, ny = _unit_normal(dx, dy, run)
    half_x, half_y = nx * across / 2.0, ny * across / 2.0
    z0_end = member.z0_m if member.z0_end_m is None else member.z0_end_m
    z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
    z1_start = max(member.z1_m, member.z0_m + MINIMUM_EXTENT_M)
    z1_end = max(z1_end, z0_end + MINIMUM_EXTENT_M)

    # Ring order matches the IFC faceted box: start-left, end-left, end-right, start-right,
    # so bottom and top correspond vertex for vertex. Written out rather than zipped from a
    # packed (x, y, low, high) tuple: this function runs 15,160 times per resolve of
    # houses/catlin, and unpacking on every call adds real overhead on that hot path.
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
    """The member's solid — a box, or a swept profile for a birdsmouth or a formed section.

    The guards are attribute reads for cut silhouettes, seats and formed sections. No
    ``cross_section()`` call may precede them: this runs 15,160 times per resolve,
    and ``member_box`` stays untouched below (the parity test pins it, and it is the hot path).
    """
    if member.plan_outline is not None:
        from typehaus.resolve.geometry_ir import GPrism

        return GPrism(ring=tuple(member.plan_outline), z0_m=member.z0_m, z1_m=member.z1_m)
    if member.elevation_profile is not None:
        return _elevation_sweep(member)
    if member.seat is not None:
        return _seated_sweep(member, member.seat)
    if member.section_ring is not None:
        return _ring_sweep(member, member.section_ring)
    return member_box(member)


def _elevation_sweep(member: FramedMember) -> GSweep | None:
    (ax, ay), (bx, by) = member.p0, member.p1
    run = math.hypot(bx - ax, by - ay)
    if run < 1e-9:
        return None
    ux, uy = (bx - ax) / run, (by - ay) / run
    width = member.plan_width_m or cross_section(member.profile).depth_m
    nx, ny = -uy * width / 2.0, ux * width / 2.0
    ring = member.elevation_profile
    area = sum(s0 * z1 - s1 * z0
               for (s0, z0), (s1, z1) in zip(ring, ring[1:] + ring[:1], strict=True))
    # The profile's normal must point along the extrusion, including in the mirrored bay.
    if area > 0.0:
        ring = tuple(reversed(ring))
    profile = tuple((ax + ux * s - nx, ay + uy * s - ny, z)
                    for s, z in ring)
    return GSweep(profile=profile, extrude=(2.0 * nx, 2.0 * ny, 0.0))


def _ring_sweep(member: FramedMember,
                ring: tuple[tuple[float, float], ...]) -> GSolid | None:
    """A formed section swept along the run: the ring placed at ``p0``, extruded to ``p1``.

    The ring is in the run's (left-normal, up) frame from the axis at ``z0_m``; the extrusion
    carries the run's rise (``z0_end_m - z0_m``), so a rake piece climbs with the rake. The
    ring is wound counter-clockwise about the run so the caps face outward.
    """
    (ax, ay), (bx, by) = member.p0, member.p1
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run < 1e-9 or len(ring) < 3:
        return member_box(member)
    nx, ny = _unit_normal(dx, dy, run)
    area = sum(s0 * t1 - s1 * t0
               for (s0, t0), (s1, t1) in zip(ring, ring[1:] + ring[:1], strict=True))
    points = ring if area > 0.0 else tuple(reversed(ring))
    z0 = member.z0_m
    rise = (member.z0_m if member.z0_end_m is None else member.z0_end_m) - z0
    profile = tuple((ax + nx * s, ay + ny * s, z0 + t) for s, t in points)
    return GSweep(profile=profile, extrude=(dx, dy, rise))


def _seated_sweep(member: FramedMember, seat: SeatCut) -> GSolid | None:
    """The notched rafter as a profile in its own vertical plane, swept across its width.

    The member less one triangle: plumb heel cut down from the plate top on the plate's outer
    face, flat seat inward along the plate top to where the underside meets it. Walking the
    profile: bearing-end top, far top, far bottom, the seat's inner end, the heel's foot, the
    heel's head on the underside, and the bearing-end bottom (the last two coincide when the
    tail is cut at the heel, as on a zero-overhang eave). ``ui/src/three/memberBox.ts``
    mirrors it.
    """
    (ax, ay), (bx, by) = member.p0, member.p1
    run = math.hypot(bx - ax, by - ay)
    if run < 1e-9:
        return member_box(member)
    section = cross_section(member.profile)
    half = max(section.width_m, MINIMUM_EXTENT_M) / 2.0
    hx, hy = seat.heel
    near_p0 = math.hypot(hx - ax, hy - ay) <= math.hypot(hx - bx, hy - by)
    z0_end = member.z0_m if member.z0_end_m is None else member.z0_end_m
    z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
    near, far = ((ax, ay), (bx, by)) if near_p0 else ((bx, by), (ax, ay))
    z0_near, z1_near, z0_far, z1_far = ((member.z0_m, member.z1_m, z0_end, z1_end) if near_p0
                                        else (z0_end, z1_end, member.z0_m, member.z1_m))
    ux, uy = (far[0] - near[0]) / run, (far[1] - near[1]) / run
    slope = (z0_far - z0_near) / run
    heel_s = math.hypot(hx - near[0], hy - near[1])
    end_s = heel_s + seat.seat_run_m
    z_seat = seat.plate_top_z_m
    if z0_near + slope * heel_s >= z_seat - MINIMUM_EXTENT_M or end_s >= run:
        return member_box(member)  # nothing below the plate top to cut

    def at(s: float, z: float) -> Vec3:
        return (near[0] + ux * s, near[1] + uy * s, z)

    points = [at(0.0, z1_near), at(run, z1_far), at(run, z0_far),
              at(end_s, z0_near + slope * end_s), at(end_s, z_seat), at(heel_s, z_seat),
              at(heel_s, z0_near + slope * heel_s), at(0.0, z0_near)]
    ring: list[Vec3] = []
    for point in points:
        if not ring or math.dist(point, ring[-1]) > MINIMUM_EXTENT_M:
            ring.append(point)
    if math.dist(ring[0], ring[-1]) <= MINIMUM_EXTENT_M:
        ring.pop()
    # The profile stands on one face of the member, not on its centreline, so that sweeping
    # it the full width lands the solid symmetrically about the axis.
    ox, oy = uy * half, -ux * half
    profile = tuple((x + ox, y + oy, z) for (x, y, z) in ring)
    return GSweep(profile=profile, extrude=(-2.0 * ox, -2.0 * oy, 0.0))


def member_part_key(member: FramedMember) -> str:
    return f"member:{member.child_key}"


def member_uid(member: FramedMember) -> str:
    """``"<ownerUid>::<childKey>"`` — the identity the viewer's member picking already uses."""
    return f"{member.parent_uid}::{member.child_key}"

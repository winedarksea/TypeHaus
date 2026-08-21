"""Cut framing members — floors, walls, roofs — for the section (→ 30 §Details).

Split out of ``section.py`` unchanged. A member either crosses the cut plane (draw its
section face, sized from its profile) or runs *along* it at a station (draw its elevation,
raked if it carries end elevations). The birdsmouth notch, the I-joist flange lines and the
representative-rafter pick all live on this side because they are member conventions, not
assembly ones.
"""

from __future__ import annotations

import math

from typehaus.emit.draw.palette import detail_hatch
from typehaus.emit.draw.scene import Hatch, Polyline
from typehaus.emit.draw.section_clip import (
    clip_polygon,
    clip_rect,
    clip_segment,
    profile_band,
    rect_nodes,
)
from typehaus.quantities import M_PER_IN


def emit_framing_cuts(b, model, hosts, plane, crop) -> None:
    """Slice each host's ``<uid>::framing`` element — one loop for every family of stick.

    The hand-rolled crossing math this replaces got the *section face* from a guess: a flat
    1.5" for every floor joist regardless of profile, and a bounding rectangle for a raked
    member, which loses the rake entirely. ``member_box`` is the one member solid every
    emitter already shares, so the cut face is now the same shape IFC sweeps and glTF draws
    — orient and all. A winder tread, whose plan outline is a trapezoid no box can express,
    rides through as its prism instead of being silently squared off.
    """
    from typehaus.resolve.geometry_slice import slice_part

    for host in hosts:
        element = model.geometry.by_uid(f"{host.uid}::framing")
        if element is None:
            continue
        for part in element.parts:
            catalog = part.catalog
            if catalog is None:
                continue
            material = catalog.material_ref
            pattern = (detail_hatch(material) or "metal") if material else "lumber"
            for profile in slice_part(part, plane):
                _emit_member_profile(b, profile, crop, host.uid, catalog.name,
                                     catalog.profile, pattern, material)


def _emit_member_profile(b, profile, crop, uid, tag, member_profile, pattern,
                         material) -> None:
    """One cut face of one member: its outline, its hatch and its flange datums."""
    band = profile_band(profile)
    if band is not None:
        u0, u1, z0, top_left, top_right = band
        rect = clip_rect(u0, u1, z0, max(top_left, top_right), crop)
        if rect is None:
            return
        b.extend(rect_nodes(*rect, "S-FRAM", pattern, uid, tag, material=material))
        b.extend(_member_flange_nodes(*rect, member_profile, uid, tag))
        return
    clipped = clip_polygon(profile.outline, crop)
    if len(clipped) < 3:
        return
    points = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
    b.add(Polyline(points=points, layer="S-FRAM", closed=True, lineweight=0.35,
                   uid=uid, tag=tag))
    b.add(Hatch(boundary=points, pattern=pattern, layer="A-WALL-PATT",
                uid=uid, material=material or "spf"))
    _emit_raked_flanges(b, profile, crop, uid, tag, member_profile)


def _emit_raked_flanges(b, profile, crop, uid, tag, member_profile) -> None:
    """Flange datums along a raked member's own top and bottom edges.

    An I-joist rafter is otherwise a plain parallelogram; the two lines offset inward by the
    real flange thickness are what tell it apart from a solid sawn rafter at detail scale.
    """
    from typehaus.resolve.framing.profiles import cross_section

    if not member_profile or len(profile.outline) != 4:
        return
    section = cross_section(member_profile)
    if section.shape != "i_joist" or section.flange_thickness_m is None:
        return
    thickness = section.flange_thickness_m
    ordered = sorted(profile.outline)
    (u0, za), (u0b, zb) = ordered[0], ordered[1]
    (u1, zc), (u1b, zd) = ordered[2], ordered[3]
    if abs(u0 - u0b) > 1e-9 or abs(u1 - u1b) > 1e-9:
        return
    bottom = (min(za, zb), min(zc, zd))
    top = (max(za, zb), max(zc, zd))
    if min(top[0] - bottom[0], top[1] - bottom[1]) <= 2.2 * thickness:
        return
    for (left, right) in ((bottom[0] + thickness, bottom[1] + thickness),
                          (top[0] - thickness, top[1] - thickness)):
        segment = clip_segment((u0, left), (u1, right), crop)
        if segment is None:
            continue
        (su0, sz0), (su1, sz1) = segment
        b.add(Polyline(points=((su0 / M_PER_IN, sz0 / M_PER_IN),
                               (su1 / M_PER_IN, sz1 / M_PER_IN)),
                       layer="S-FRAM", lineweight=0.13, uid=uid, tag=f"{tag}/flange"))


def _emit_floor_cut(b, floor, direction, station, crop) -> None:
    for member in floor.members:
        (x0, y0), (x1, y1) = member.p0, member.p1
        a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
        u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
        if a0 == a1:
            # member perpendicular to cut? p runs along the cut axis at a station
            if abs(a0 - station) > 1e-9:
                continue
            rect = clip_rect(min(u0, u1), max(u0, u1), member.z0_m, member.z1_m, crop)
            if rect is None:
                continue
            b.extend(rect_nodes(*rect, "S-FRAM", None, member.parent_uid,
                                 member.child_key))
            b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                          member.child_key))
            continue
        if (a0 - station) * (a1 - station) > 0:
            continue
        # member crosses the cut: draw its section (1.5" wide x depth)
        t = (station - a0) / ((a1 - a0) or 1e-12)
        u = u0 + t * (u1 - u0)
        half = 0.75 * M_PER_IN
        rect = clip_rect(u - half, u + half, member.z0_m, member.z1_m, crop)
        if rect is None:
            continue
        b.extend(rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid,
                             member.child_key))
        b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                      member.child_key))


def _emit_member_cuts(b, model, plane, crop, walls_and_floors=True) -> None:
    """Draw the framing members crossing the cut (top plates, rafters, joists).

    Generalizes the floor crossing math to raked members — a member with ``z0_end_m`` /
    ``z1_end_m`` set interpolates its elevation at the crossing station.

    ``walls_and_floors`` is the detail-mode gate. Roof members are outside it: the roof's
    assembly bands stop at the structure (``roof_parts`` builds only the layers above it),
    so the rafters *are* the roof's structure in every mode, not an extra.
    """
    if walls_and_floors:
        emit_framing_cuts(b, model, model.walls, plane, crop)
    for roof in model.roofs:
        # A birdsmouth rafter runs *along* the cut plane, so it only draws when a rafter
        # lands exactly on the station — which a wall-midpoint cut rarely does. Show the
        # single nearest one as the representative rafter so the eave detail carries its
        # seat cut, and let all other members follow the ordinary crossing/parallel rules.
        direction, station = plane.axis, plane.station_m
        parallel_rafters = []
        for member in roof.members:
            if (_birdsmouth_depth_in(member.connection) is not None
                    and _member_is_parallel(member, direction)
                    and _member_u_overlaps_crop(member, direction, crop)):
                parallel_rafters.append(member)
            else:
                _emit_one_member(b, member, direction, station, crop)
        if parallel_rafters and not any(
                abs(_member_perp(m, direction) - station) < 1e-9 for m in parallel_rafters):
            nearest = min(parallel_rafters,
                          key=lambda m: abs(_member_perp(m, direction) - station))
            _emit_one_member(b, nearest, direction, _member_perp(nearest, direction), crop)


def _member_u_overlaps_crop(member, direction: str, crop) -> bool:
    """Whether the member's in-section (u) span overlaps the crop's u-window.

    Two rafters share every y at a gable (one per roof plane); only the one whose run is
    actually under the crop is the eave the detail is about.
    """
    if crop is None:
        return True
    (x0, y0), (x1, y1) = member.p0, member.p1
    u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
    (cu0, _), (cu1, _) = crop
    lo, hi = min(cu0, cu1), max(cu0, cu1)
    return min(u0, u1) <= hi and max(u0, u1) >= lo


def _member_is_parallel(member, direction: str) -> bool:
    (x0, y0), (x1, y1) = member.p0, member.p1
    a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
    return abs(a0 - a1) < 1e-12


def _member_perp(member, direction: str) -> float:
    """The member's coordinate perpendicular to the cut (its station if parallel)."""
    (x0, y0), _ = member.p0, member.p1
    return y0 if direction == "x" else x0


def _birdsmouth_depth_in(connection: str | None) -> float | None:
    """Seat-cut depth (inches) parsed off a rafter's ``eave:birdsmouth-<d>in`` tag.

    The connection string is the only carrier of the notch depth (``resolve.model`` keeps
    the member a plain box — no seat cut in the solid), so the 2D section is where the
    birdsmouth becomes drawn linework.
    """
    if not connection:
        return None
    for token in connection.split(";"):
        token = token.strip()
        if "birdsmouth-" in token:
            tail = token.split("birdsmouth-", 1)[1]
            digits = tail[:-2] if tail.endswith("in") else tail
            try:
                return float(digits)
            except ValueError:
                return None
    return None


def _member_flange_nodes(u0, u1, z0, z1, profile, uid, tag) -> list:
    """Two thin flange-delineation lines so an I-joist reads as an I, not a solid bar.

    A cut I-joist member is otherwise a plain rectangle; the flange lines (offset from the
    top and bottom edges by the real flange thickness) are what tell it apart from sawn
    lumber at detail scale. Coordinates in metres, converted to inches like ``rect_nodes``.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    if section.shape != "i_joist" or section.flange_thickness_m is None:
        return []
    ft = section.flange_thickness_m
    if (z1 - z0) <= 2.2 * ft:
        return []
    nodes: list = []
    for z in (z0 + ft, z1 - ft):
        nodes.append(Polyline(points=((u0 / M_PER_IN, z / M_PER_IN), (u1 / M_PER_IN, z / M_PER_IN)),
                              layer="S-FRAM", lineweight=0.13, uid=uid,
                              tag=f"{tag}/flange"))
    return nodes


def _emit_raked_rafter(b, member, u0, u1, z0_a, z0_b, z1_a, z1_b, crop,
                       depth_in) -> None:
    """A raked rafter drawn as its true sloped profile with a birdsmouth seat-cut notch.

    Replaces the bounding-box rectangle the parallel-member path would draw (which loses the
    rake entirely) with the actual parallelogram, then notches the underside at the eave
    (low) end so the rafter reads as a seated, notched member. The notch is a plumb heel cut
    of ``depth_in`` plus a horizontal seat bearing on the plate.
    """
    d = depth_in * M_PER_IN
    eave_at_u0 = z1_a <= z1_b  # eave = lower-top end (zero-overhang tail bears here)
    span_u = abs(u1 - u0) or 1e-9
    slope_bot = (z0_b - z0_a) / (u1 - u0)
    run = min(3.5 * M_PER_IN, span_u * 0.35)  # seat run ~ a 2x4 plate bearing
    # The seat runs *inboard* (toward the ridge end) from the eave's plumb cut. The
    # endpoints carry no ordering guarantee — an east-half rafter's eave end is the
    # larger u — so the step direction comes from where the ridge end actually is.
    # The heel drops BELOW the member's underside, it does not raise it. The resolver
    # already seats the rafter: its eave-end ``z0`` IS the plate top, and it models the
    # notch as a separate ``seat_cut`` member spanning plate_top-d .. plate_top. Adding d
    # here as well applied the birdsmouth twice and floated the rafter a notch-depth clear
    # of the plate it is supposed to bear on — which is exactly what the drawing showed.
    # Dropping instead puts the plumb tail over the same span the seat_cut occupies.
    if eave_at_u0:
        step = math.copysign(run, u1 - u0)
        heel = (u0, z0_a - d)
        toe = (u0 + step, z0_a + slope_bot * step)
        poly = [(u0, z1_a), (u1, z1_b), (u1, z0_b), toe, heel]
    else:
        step = math.copysign(run, u0 - u1)
        heel = (u1, z0_b - d)
        toe = (u1 + step, z0_b + slope_bot * step)
        poly = [(u1, z1_b), (u0, z1_a), (u0, z0_a), toe, heel]
    clipped = clip_polygon(poly, crop)
    if len(clipped) < 3:
        return
    pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
    b.add(Polyline(points=pts, layer="S-FRAM", closed=True, lineweight=0.35,
                   uid=member.parent_uid, tag=member.child_key))
    b.add(Hatch(boundary=pts, pattern="lumber", layer="A-WALL-PATT",
                uid=member.parent_uid, material="spf"))
    # An I-joist rafter carries flange lines along its raked top/bottom edges so it reads
    # as an I-joist, not a solid rafter — offset inward from each edge by the flange depth.
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(member.profile)
    if section.shape == "i_joist" and section.flange_thickness_m is not None:
        ft = section.flange_thickness_m
        for (za, zb) in ((z0_a + ft, z0_b + ft), (z1_a - ft, z1_b - ft)):
            seg = clip_segment((u0, za), (u1, zb), crop)
            if seg is not None:
                (su0, sz0), (su1, sz1) = seg
                b.add(Polyline(points=((su0 / M_PER_IN, sz0 / M_PER_IN),
                                       (su1 / M_PER_IN, sz1 / M_PER_IN)),
                               layer="S-FRAM", lineweight=0.13,
                               uid=member.parent_uid, tag=f"{member.child_key}/flange"))


def _emit_one_member(b, member, direction, station, crop) -> None:
    (x0, y0), (x1, y1) = member.p0, member.p1
    a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
    u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
    z0_a, z1_a = member.z0_m, member.z1_m
    z0_b = member.z0_end_m if member.z0_end_m is not None else member.z0_m
    z1_b = member.z1_end_m if member.z1_end_m is not None else member.z1_m
    if abs(a0 - a1) < 1e-12:
        # member runs along the cut axis at a station (e.g. a top plate parallel to the cut)
        if abs(a0 - station) > 1e-9:
            return
        raked = member.z0_end_m is not None or member.z1_end_m is not None
        birdsmouth = _birdsmouth_depth_in(member.connection)
        if raked and birdsmouth is not None and abs(u1 - u0) > 1e-9:
            _emit_raked_rafter(b, member, u0, u1, z0_a, z0_b, z1_a, z1_b, crop,
                               birdsmouth)
            return
        rect = clip_rect(min(u0, u1), max(u0, u1), min(z0_a, z0_b), max(z1_a, z1_b), crop)
        if rect is not None:
            b.extend(_member_rect_nodes(rect, member))
            b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                          member.child_key))
        return
    if (a0 - station) * (a1 - station) > 0:
        return
    t = (station - a0) / ((a1 - a0) or 1e-12)
    u = u0 + t * (u1 - u0)
    z0 = z0_a + t * (z0_b - z0_a)
    z1 = z1_a + t * (z1_b - z1_a)
    # The cut is across the member's run, so it shows the section face the plan shows: the
    # wide `depth_m` for a flat-laid plate/sill/block, the thin `width_m` for one on edge.
    # A flat 1.5" was drawn here regardless of profile, which was right only by accident for
    # the on-edge 2x sticks and drew every plate a quarter of its real width.
    from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m

    half = plan_cross_section_m(cross_section(member.profile), z1_a - z0_a) / 2.0
    rect = clip_rect(u - half, u + half, min(z0, z1), max(z0, z1), crop)
    if rect is not None:
        b.extend(_member_rect_nodes(rect, member))
        b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                      member.child_key))


def _member_rect_nodes(rect, member) -> list:
    """A cut member's rectangle, hatched as what it is made of.

    A member that names a material is a *skin* band (the wall→roof closure, roof-edge
    cladding, derived trim), not lumber — hatch and fill it like the layer stacks hatch
    the same material, so a closure EPS band reads as foam, not as a stack of studs.
    Plain framing keeps the lumber hatch.
    """
    if member.material:
        pattern = detail_hatch(member.material) or "metal"
        return rect_nodes(*rect, "S-FRAM", pattern, member.parent_uid,
                           member.child_key, material=member.material)
    return rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid, member.child_key)

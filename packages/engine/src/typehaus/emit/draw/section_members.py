"""Cut framing members — floors, walls, roofs — for the section (→ 30 §Details).

Split out of ``section.py`` unchanged. A member either crosses the cut plane (draw its
section face, sized from its profile) or runs *along* it at a station (draw its elevation,
raked if it carries end elevations). The birdsmouth notch, the I-joist flange lines and the
representative-rafter pick all live on this side because they are member conventions, not
assembly ones.
"""

from __future__ import annotations

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
from typehaus.resolve.geometry_slice import CutPlane


def emit_framing_cuts(b, model, hosts, plane, crop, representative_roles=()) -> None:
    """Slice each host's ``<uid>::framing`` element — one loop for every family of stick.

    ``member_solid`` is the one member solid every emitter already shares, so the cut face
    is the same shape IFC sweeps and glTF draws — orient, rake, birdsmouth and all. A winder
    tread, whose plan outline is a trapezoid no box can express, rides through as its prism
    instead of being silently squared off.

    ``representative_roles`` names the roles that get the *nearest member* when none is cut.
    A rafter runs along the cut plane, so it draws only when one lands on the station — which
    a wall-midpoint cut rarely does, and an eave detail with no rafter in it is not an eave
    detail. ``nearest_station`` names and tests that logic.
    """
    from typehaus.resolve.geometry_slice import nearest_station, slice_part

    for host in hosts:
        element = model.geometry.by_uid(f"{host.uid}::framing")
        if element is None or _host_is_far(host, plane, crop):
            continue
        missed: dict[str, list] = {}
        cut: set[str] = set()
        for part in element.parts:
            catalog = part.catalog
            if catalog is None:
                continue
            profiles = slice_part(part, plane)
            if not profiles and catalog.role in representative_roles:
                if _u_span_overlaps_crop(part, plane, crop):
                    missed.setdefault(catalog.role, []).append(part)
                continue
            if profiles:
                cut.add(catalog.role)
            _emit_part_profiles(b, profiles, crop, host.uid, catalog)
        for role, parts in missed.items():
            if role in cut:
                continue  # something of this role was cut; no stand-in needed
            solids = [solid for part in parts for solid in part.solids]
            station = nearest_station(solids, plane)
            if station is None:
                continue
            stand_in = CutPlane(axis=plane.axis, station_m=station)
            for part in parts:
                _emit_part_profiles(b, slice_part(part, stand_in), crop, host.uid,
                                    part.catalog)


# How far a framing member may reach past its host's own plan outline: the wall→roof closure
# bands and the derived trim stand outboard of the wall they continue, and a rafter tail past
# the roof footprint. Generous on purpose — this is a *reject*, and a wrong reject silently
# deletes geometry from a drawing.
_HOST_MARGIN_M = 1.0


def _host_is_far(host, plane, crop) -> bool:
    """Whether every member of ``host`` is certainly outside this cut and its crop.

    One bbox test per host instead of a slice attempt per member. A detail's crop is a
    two-foot window on a sixty-foot building, so nearly every wall in the model is rejected
    here — which is what keeps the drawing stage from scaling with (details x members).
    """
    points = _host_plan_points(host)
    if not points:
        return False
    perps = [point[plane.perp_index] for point in points]
    if not (min(perps) - _HOST_MARGIN_M <= plane.station_m <= max(perps) + _HOST_MARGIN_M):
        return True
    if crop is None:
        return False
    (cu0, _z0), (cu1, _z1) = crop
    us = [point[plane.u_index] for point in points]
    return (max(us) + _HOST_MARGIN_M < min(cu0, cu1)
            or min(us) - _HOST_MARGIN_M > max(cu0, cu1))


def _host_plan_points(host):
    """The host's own plan outline: a wall's axis, a roof's footprint, a floor's deck."""
    axis = getattr(host, "axis", None)
    if axis is not None:
        return list(axis)
    for attribute in ("footprint", "deck_outline"):
        outline = getattr(host, attribute, None)
        if outline:
            return list(outline)
    return []


def _u_span_overlaps_crop(part, plane, crop) -> bool:
    """Whether the part's in-section span reaches the crop at all.

    Two rafters share every station at a gable (one per roof plane); only the one whose run
    is actually under the crop is the eave the detail is about.
    """
    if crop is None:
        return True
    (cu0, _z0), (cu1, _z1) = crop
    lo, hi = min(cu0, cu1), max(cu0, cu1)
    from typehaus.resolve.geometry_slice import perp_values

    us = [value for solid in part.solids
          for value in perp_values(solid, plane.u_index)]
    return bool(us) and min(us) <= hi and max(us) >= lo


def _emit_part_profiles(b, profiles, crop, uid, catalog) -> None:
    material = catalog.material_ref
    pattern = (detail_hatch(material) or "metal") if material else "lumber"
    for profile in profiles:
        _emit_member_profile(b, profile, crop, uid, catalog.name, catalog.profile,
                             pattern, material)


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

    An I-joist rafter is otherwise a plain outline; the two lines offset inward by the real
    flange thickness are what tell it apart from a solid sawn rafter at detail scale. The
    edges are read off the cut face itself — the highest and lowest point at each end — which
    keeps working now that a notched rafter's profile has six points rather than four.
    """
    from typehaus.resolve.framing.profiles import cross_section

    if not member_profile or len(profile.outline) < 4:
        return
    section = cross_section(member_profile)
    if section.shape not in ("i_joist", "floor_truss") or section.flange_thickness_m is None:
        return
    us = sorted({round(u, 9) for (u, _z) in profile.outline})
    if len(us) < 2:
        return
    u0, u1 = us[0], us[-1]
    left = [z for (u, z) in profile.outline if round(u, 9) == u0]
    right = [z for (u, z) in profile.outline if round(u, 9) == u1]
    if len(left) < 2 or len(right) < 2:
        return
    thickness = section.flange_thickness_m
    bottom, top = (min(left), min(right)), (max(left), max(right))
    if min(top[0] - bottom[0], top[1] - bottom[1]) <= 2.2 * thickness:
        return
    for (left_z, right_z) in ((bottom[0] + thickness, bottom[1] + thickness),
                              (top[0] - thickness, top[1] - thickness)):
        segment = clip_segment((u0, left_z), (u1, right_z), crop)
        if segment is None:
            continue
        (su0, sz0), (su1, sz1) = segment
        b.add(Polyline(points=((su0 / M_PER_IN, sz0 / M_PER_IN),
                               (su1 / M_PER_IN, sz1 / M_PER_IN)),
                       layer="S-FRAM", lineweight=0.13, uid=uid, tag=f"{tag}/flange"))


def _emit_member_cuts(b, model, plane, crop, walls_and_floors=True) -> None:
    """Draw the framing members crossing the cut (top plates, rafters, joists).

    ``walls_and_floors`` is the detail-mode gate. Roof members are outside it: the roof's
    assembly bands stop at the structure (``roof_parts`` builds only the layers above it), so
    the rafters *are* the roof's structure in every mode, not an extra.
    """
    if walls_and_floors:
        emit_framing_cuts(b, model, model.walls, plane, crop)
    emit_framing_cuts(b, model, model.roofs, plane, crop,
                      representative_roles=("rafter",))


def _member_flange_nodes(u0, u1, z0, z1, profile, uid, tag) -> list:
    """Two thin flange-delineation lines so an I-joist reads as an I, not a solid bar.

    A cut I-joist member is otherwise a plain rectangle; the flange lines (offset from the
    top and bottom edges by the real flange thickness) are what tell it apart from sawn
    lumber at detail scale. Coordinates in metres, converted to inches like ``rect_nodes``.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    if section.shape not in ("i_joist", "floor_truss") or section.flange_thickness_m is None:
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

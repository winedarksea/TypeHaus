"""Locate a KBS1Z on the exterior heel of every slat end, in either mirrored bay."""

from __future__ import annotations

import math

from typehaus.joints.model import marker_uid
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.kbs_geometry import kbs_mesh
from typehaus.resolve.model import ResolvedSolid


def resolve_slat_connectors(model, element, layout, storey: str) -> None:
    """Geometry and the hardware bill name the same two connections per slat.

    Unknown connector products retain their authored bill but get no invented shape.
    ``derived`` prevents a second volume-based steel charge beside the hardware row.
    """
    if element.connector != "KBS1Z":
        return
    (x0, y0), (x1, y1) = element.start.xy_m, element.end.xy_m
    ux, uy = (x1 - x0) / layout.length, (y1 - y0) / layout.length
    face = cross_section(element.slat).width_m
    depth = cross_section(element.slat).depth_m
    half = face / math.sqrt(2.0)
    exterior_sign = -1.0 if element.plane_offset.meters < 0.0 else 1.0
    face_offset = element.plane_offset.meters + exterior_sign * depth / 2.0
    inward = (exterior_sign * uy, -exterior_sign * ux, 0.0)
    sill = element.base_elevation.meters + layout.plate
    for slat in layout.slats:
        mirror = 1.0 if slat.bay == 0 else -1.0

        def vector(u, z, mirror=mirror):
            return (mirror * ux * u, mirror * uy * u, z)

        for end, landing, u in (('low', slat.low, slat.u0),
                                 ('high', slat.high, slat.u1)):
            z = u - slat.c
            # The heel is where the outside long edge meets the bearing face. The front
            # leaf and its return then share that edge, just as Figure 7 shows.
            if landing == "chord":
                z -= half
                support, support_face, inside = (0, -1), (-1, 0), (-1, 1)
            elif landing == "centre":
                z += half
                support, support_face, inside = (0, 1), (1, 0), (1, -1)
            elif landing == "sill":
                u -= half
                support, support_face, inside = (-1, 0), (0, -1), (1, -1)
            else:
                u += half
                support, support_face, inside = (1, 0), (0, 1), (-1, 1)
            station = layout.station(slat.bay, u)
            heel = (x0 + ux * station - uy * face_offset,
                    y0 + uy * station + ux * face_offset, sill + z)
            sign = 1.0 if end == "low" else -1.0
            root = math.sqrt(2.0)
            mesh = kbs_mesh(heel, vector(*support), vector(*support_face),
                            vector(sign / root, sign / root),
                            vector(inside[0] / root, inside[1] / root), inward)
            xs, ys, zs = zip(*mesh.positions, strict=True)
            key = f"{element.uid or element.tag}:slat-{slat.bay}{slat.j:+d}:{end}:KBS1Z"
            model.solids.append(ResolvedSolid(
                uid=marker_uid(key), tag=f"CN~KBS1Z~{element.tag}~{slat.bay}{slat.j:+d}~{end}",
                storey=storey, category="connector", product="KBS1Z", derived=True,
                outline=[(min(xs), min(ys)), (max(xs), min(ys)),
                         (max(xs), max(ys)), (min(xs), max(ys))],
                z0_m=min(zs), z1_m=max(zs), body_mesh=mesh))

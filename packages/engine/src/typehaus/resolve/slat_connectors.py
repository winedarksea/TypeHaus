"""Locate each KBS1Z on its open- or closed-bend heel, in either mirrored bay."""

from __future__ import annotations

from typehaus.joints.model import marker_uid
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.kbs_geometry import kbs_mesh
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.slat_connector_landings import slat_connector_ends


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
    exterior_sign = -1.0 if element.plane_offset.meters < 0.0 else 1.0
    sill = element.base_elevation.meters + layout.plate
    for slat in (s for s in layout.slats if s.braced):
        mirror = 1.0 if slat.bay == 0 else -1.0

        def vector(u, z, mirror=mirror):
            return (mirror * ux * u, mirror * uy * u, z)

        for placement in slat_connector_ends(slat, face):
            end = placement.end
            station = layout.station(slat.bay, placement.u)
            for face_index in range(element.connectors_per_end):
                face_sign = exterior_sign * (1 if face_index == 0 else -1)
                face_offset = element.plane_offset.meters + face_sign * depth / 2.0
                inward = (face_sign * uy, -face_sign * ux, 0.0)
                suffix = f":face-{face_index}" if element.connectors_per_end == 2 else ""
                heel = (x0 + ux * station - uy * face_offset,
                        y0 + uy * station + ux * face_offset, sill + placement.z)
                mesh = kbs_mesh(heel, vector(*placement.support), vector(*placement.support_face),
                                vector(*placement.brace_axis), vector(*placement.brace_face),
                                inward)
                xs, ys, zs = zip(*mesh.positions, strict=True)
                key = f"{element.uid or element.tag}:slat-{slat.bay}{slat.j:+d}:{end}:KBS1Z{suffix}"
                model.solids.append(ResolvedSolid(
                    uid=marker_uid(key),
                    tag=f"CN~KBS1Z~{element.tag}~{slat.bay}{slat.j:+d}~{end}{suffix}",
                    storey=storey, category="connector", product="KBS1Z", derived=True,
                    outline=[(min(xs), min(ys)), (max(xs), min(ys)),
                             (max(xs), max(ys)), (min(xs), max(ys))],
                    z0_m=min(zs), z1_m=max(zs), body_mesh=mesh))

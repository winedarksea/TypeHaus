"""A bypass set's product view: jambs and head, track, two leaves in their lanes, guide, pulls.

Both leaves are drawn closed, each in its own lane ``lane_pitch / 2`` either side of the
track's centre, lapping ``overlap`` at the middle. The track, guide and pulls carry the set's
``product_ref`` (``PartCatalogRef.name``), so a picked piece names it in the inspector.
"""

from __future__ import annotations

from math import cos, pi, sin

from typehaus.resolve.geometry_ir import GPart, GSweep, PartCatalogRef
from typehaus.resolve.model_door_products import BypassDoorPlacement

_PULL_EDGE_INSET_M = 0.0508  # pull centre 2" in from the leaf's outer edge (Johnson IN183834)
_PULL_RECESS_M = 0.003  # what of the cup reads proud of the face
_PULL_FACETS = 24
_HARDWARE_KEY = "door_hardware"


def bypass_door_parts(box, frame, placement: BypassDoorPlacement, faces, room_sign: float,
                      head_z: float, frame_key: str, leaf_key: str) -> tuple[GPart, ...]:
    """``box`` is ``_opening_parts``' box builder; ``frame`` ``(x, y, ux, uy, nx, ny)`` the
    opening centre and wall axes; ``faces`` the finish faces; ``room_sign`` the pull side."""
    p = placement
    a = p.jamb_allowance_m
    floor = p.finished_floor_z_m
    centre = (faces[0] + faces[1]) / 2.0 if faces else 0.0
    depth = (faces[1] - faces[0]) if faces else p.track_width_m
    half = p.finished_width_m / 2.0
    jamb_h = head_z - floor
    under_head = head_z - a
    parts = [GPart(key="frame", material_key=frame_key, solids=(
        box(a, jamb_h, depth, -half - a / 2.0, floor + jamb_h / 2.0, centre),
        box(a, jamb_h, depth, half + a / 2.0, floor + jamb_h / 2.0, centre),
        box(p.finished_width_m + 2 * a, a, depth, 0.0, head_z - a / 2.0, centre)))]
    catalog = PartCatalogRef(role="bypass", name=p.product_ref)
    parts.append(GPart(key="bypass_track", material_key=_HARDWARE_KEY, catalog=catalog, solids=(
        box(p.finished_width_m, p.track_height_m, p.track_width_m, 0.0,
            under_head - p.track_height_m / 2.0, centre),)))
    bottom = floor + p.floor_clearance_m
    lanes = (centre + room_sign * p.lane_pitch_m / 2.0, centre - room_sign * p.lane_pitch_m / 2.0)
    # Leaf 0 rides the room-side lane from the -along jamb; leaf 1 the back lane from +along.
    leaf_along = (-half + p.leaf_width_m / 2.0, half - p.leaf_width_m / 2.0)
    parts.append(GPart(key="leaf", material_key=leaf_key, solids=tuple(
        box(p.leaf_width_m, p.leaf_height_m, p.leaf_thickness_m, along,
            bottom + p.leaf_height_m / 2.0, lane)
        for along, lane in zip(leaf_along, lanes, strict=True))))
    gw, gd, gh = p.guide_size_m
    parts.append(GPart(key="bypass_guide", material_key=_HARDWARE_KEY, catalog=catalog,
                       solids=(box(gw, gh, gd, 0.0, floor + gh / 2.0, centre),)))
    pulls = []
    for edge, lane in ((-half, lanes[0]), (half, lanes[1])):
        along = edge - (1 if edge > 0 else -1) * _PULL_EDGE_INSET_M
        face = lane + room_sign * p.leaf_thickness_m / 2.0
        pulls.append(_disc(frame, along, bottom + p.pull_height_m, face, room_sign,
                           p.pull_diameter_m / 2.0))
    parts.append(GPart(key="bypass_pull", material_key=_HARDWARE_KEY, catalog=catalog,
                       solids=tuple(pulls)))
    return tuple(parts)


def _disc(frame, along: float, z: float, face: float, side: float, radius: float) -> GSweep:
    """A cup pull's rim: a disc on the leaf face, swept ``_PULL_RECESS_M`` out of it."""
    x, y, ux, uy, nx, ny = frame
    ring = [(radius * cos(2 * pi * i / _PULL_FACETS), radius * sin(2 * pi * i / _PULL_FACETS))
            for i in range(_PULL_FACETS)]
    if side > 0:  # (tangent, up) faces -normal; reverse for an outward sweep
        ring.reverse()
    profile = tuple((x + ux * (along + s) + nx * face, y + uy * (along + s) + ny * face, z + h)
                    for s, h in ring)
    return GSweep(profile, (nx * side * _PULL_RECESS_M, ny * side * _PULL_RECESS_M, 0.0))

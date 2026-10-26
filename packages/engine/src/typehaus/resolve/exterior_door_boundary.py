"""Locate a separate veneer reveal without making it the door's anchorage wall."""

from math import hypot

from typehaus.resolve.geometry import opening_center, wall_frame


class ExteriorDoorBoundaryError(ValueError):
    """An explicitly referenced exterior opening cannot establish this installation."""


def exterior_door_boundary(model, wall, opening, installation=None):
    from typehaus.resolve.geometry_openings import _exterior_face

    if installation is None:
        placement = opening.doorway.exterior_placement if opening and opening.doorway else None
        authored = model.plan.by_tag(opening.tag) if opening else None
        installation = (
            placement.specification
            if placement
            else getattr(authored, "exterior_installation", None)
        )
    reference = installation.exterior_opening_ref if installation else None
    if not reference:
        return _exterior_face(wall)
    reveal = next((o for o in model.openings if o.tag == reference), None)
    if reveal is None:
        raise ExteriorDoorBoundaryError(f"exterior opening {reference} does not resolve")
    veneer = model.wall(reveal.host_wall)
    if veneer is None or veneer.tag == wall.tag:
        raise ExteriorDoorBoundaryError("exterior reveal must name a separate resolved wall")
    origin, tangent, normal, _ = wall_frame(wall)
    _, other_tangent, _, _ = wall_frame(veneer)
    if abs(sum(tangent[i] * other_tangent[i] for i in (0, 1))) < 1 - 1e-6:
        raise ExteriorDoorBoundaryError(
            "exterior reveal wall is not parallel to the anchorage wall"
        )
    center, other = opening_center(wall, opening), opening_center(veneer, reveal)
    separation = sum((other[i] - center[i]) * normal[i] for i in (0, 1))
    if abs(separation) < 1e-6:
        raise ExteriorDoorBoundaryError("exterior reveal supplies no outward direction")
    if abs(sum((other[i] - center[i]) * tangent[i] for i in (0, 1))) > 0.001:
        raise ExteriorDoorBoundaryError("exterior reveal is not concentric with the door")
    if reveal.width_m + 0.001 < opening.width_m:
        raise ExteriorDoorBoundaryError("exterior reveal is narrower than the framed opening")
    sign = 1.0 if separation > 0 else -1.0
    offsets = [
        sum((p[i] - origin[i]) * normal[i] for i in (0, 1))
        for layer in veneer.depth_layers()
        for p in layer.polygon
    ]
    if not offsets or hypot(*normal) < 0.99:
        raise ExteriorDoorBoundaryError("exterior reveal wall has no resolved depth")
    return sign * max(sign * n for n in offsets), sign

"""The seat frame of a window bucked through exterior foam behind a separate veneer.

catlin's ``WIN-B-SAUNA``: its host carries no cladding layer (the brick is ``W-B-BRICK``,
a wall of its own with a concentric reveal), so ``opening_flashing_frame`` finds no
exterior face and the unit had no seat. The opening is hand-flashed (its transition sheet's
K1-K3: a buck through the foam to the waterproofing, a sloped pan with a back dam), so
nothing here meshes flashing; it only gives ``window_seat`` that buck and pan to sit on.

A door names its reveal (``ExteriorDoorInstallation.exterior_opening_ref``); a window has
no installation record, so the reveal is found here by what makes it one: a rough opening
through a parallel wythe laid against this wall's outer face, concentric with the window
and overlapping it in elevation.
"""

from __future__ import annotations

from typehaus.quantities import inch
from typehaus.resolve.framing.truss_common import BUCK_THICKNESS_IN
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.model import ResolvedModel, ResolvedOpening, ResolvedWall
from typehaus.resolve.model_window_seat import mount_layer_index

#: The ``exterior_door_boundary`` tolerances: parallel walls, concentric openings, abutting faces.
_TOLERANCE_M = 0.001


def _span(wall: ResolvedWall, opening: ResolvedOpening) -> tuple[float, float]:
    base = wall.base_ref_z_m + opening.sill_m
    return base, base + opening.height_m


def veneer_reveal(model: ResolvedModel, wall: ResolvedWall,
                  opening: ResolvedOpening) -> tuple[float, float] | None:
    """``(veneer outer face, outward sign)`` off the reveal laid against ``wall``, or None.

    Offsets are along ``wall``'s right-hand normal from its axis start, the
    ``_exterior_face`` frame. The host's outward side is its last depth layer's side.
    """
    origin, tangent, normal, length = wall_frame(wall)
    center = opening_center(wall, opening)
    layers = [layer for layer in wall.depth_layers() if layer.polygon]
    if center is None or length <= 1e-9 or len(layers) < 2:
        return None

    def offsets(layer_list) -> list[float]:
        return [(x - origin[0]) * normal[0] + (y - origin[1]) * normal[1]
                for layer in layer_list for x, y in layer.polygon]

    outer, inner = offsets(layers[-1:]), offsets(layers[:1])
    sign = 1.0 if sum(outer) / len(outer) > sum(inner) / len(inner) else -1.0
    face = sign * max(sign * value for value in outer)
    low, high = _span(wall, opening)
    for reveal in model.openings:
        if reveal.kind != "rough_opening" or reveal.is_blind or reveal.host_wall == wall.tag:
            continue
        veneer = model.wall(reveal.host_wall)
        other = opening_center(veneer, reveal) if veneer is not None else None
        if other is None or reveal.width_m + _TOLERANCE_M < opening.width_m:
            continue
        _o, other_tangent, _n, _l = wall_frame(veneer)
        if abs(tangent[0] * other_tangent[0] + tangent[1] * other_tangent[1]) < 1 - 1e-6:
            continue
        if abs((other[0] - center[0]) * tangent[0] + (other[1] - center[1]) * tangent[1]) \
                > _TOLERANCE_M:
            continue
        r_low, r_high = _span(veneer, reveal)
        if min(high, r_high) <= max(low, r_low):
            continue
        depths = [sign * value for value in offsets(veneer.depth_layers())]
        # Laid against this wall's outer face, on its outer side: the stack continues.
        if depths and abs(min(depths) - sign * face) <= _TOLERANCE_M:
            return sign * max(depths), sign
    return None


def veneer_backed_frame(model: ResolvedModel, wall: ResolvedWall, opening: ResolvedOpening):
    """An outie seat frame: mount on the foam face, back dam at the sheathing, or None.

    The mount plane is ``mount_layer_index``'s, the plane the stool's return reads.
    """
    from typehaus.resolve.opening_flashing import OpeningFlashingFrame, frame_axes

    exterior = veneer_reveal(model, wall, opening)
    if exterior is None:
        return None
    origin, along, outward, extent = frame_axes(wall, exterior[1])
    layers = wall.depth_layers()
    index = mount_layer_index(layers)
    sheaths = [layer for layer in layers if layer.function == "sheathing" and layer.polygon]
    water = [layer for layer in layers[: (index or 0) + 1]
             if "water" in layer.control and layer.polygon]
    if index is None or not layers[index].polygon or not sheaths or not water:
        return None
    sheath, wet, mount = (max(extent(layer)) for layer in (sheaths[-1], water[-1],
                                                           layers[index]))
    if mount <= wet + 1e-6:
        return None  # no foam outboard of the water plane: not a bucked unit
    return OpeningFlashingFrame(origin, along, outward, sheath, wet, mount,
                                exterior[1] * exterior[0], True,
                                inch(BUCK_THICKNESS_IN).meters, sheath)

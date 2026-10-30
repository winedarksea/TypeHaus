"""Finished millwork prisms — window stools, base runs, door casings — for every emitter.

The viewer payload, the GLB and the IFC all read these; none re-derives a board.
"""

from __future__ import annotations

from typehaus.resolve.fillet import filleted_ring
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_ir import GPrism
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import ResolvedWall, ResolvedWindowStool
from typehaus.resolve.model_trim import ResolvedBaseRun, ResolvedDoorCasing


def window_stool_ring(wall: ResolvedWall, opening,
                      stool: ResolvedWindowStool) -> tuple[tuple[float, float], ...] | None:
    """The stool's notched plan ring, square-cornered, in a fixed vertex order.

    front-left, front-right, horn-back right, shoulder right, back right, back left,
    shoulder left, horn-back left — so ``countertop_edges.STOOL_EDGE_KINDS`` names each
    edge. The horns occupy only the room-side lip. Extending them through the reveal
    would put oak inside the jamb wall and create overlapping IFC solids. Layer polygons
    establish the wall's interior side, so reversing its axis does not reverse the stool.
    """
    if (stool.depth_m is None or stool.depth_m <= stool.overhang_m
            or stool.thickness_m <= 0 or opening.kind != "window"):
        return None
    origin = opening_center(wall, opening)
    _start, tangent, normal, axis_length = wall_frame(wall)
    layers = wall.depth_layers()
    if origin is None or axis_length <= 1e-9 or not layers:
        return None

    def offsets(polygon) -> list[float]:
        return [(x - _start[0]) * normal[0] + (y - _start[1]) * normal[1]
                for x, y in polygon]

    interior_offsets = offsets(layers[0].polygon)
    exterior_offsets = offsets(layers[-1].polygon)
    if not interior_offsets or not exterior_offsets:
        return None
    exterior_sign = (1.0 if sum(exterior_offsets) / len(exterior_offsets)
                     > sum(interior_offsets) / len(interior_offsets) else -1.0)
    interior_face = (min(interior_offsets) if exterior_sign > 0
                     else max(interior_offsets))
    half_width = opening.width_m / 2.0
    notch = half_width - stool.notch_inset_m
    front = interior_face - exterior_sign * stool.overhang_m
    shoulder = interior_face
    back = interior_face + exterior_sign * (stool.depth_m - stool.overhang_m)

    def point(along: float, offset: float) -> tuple[float, float]:
        return (origin[0] + tangent[0] * along + normal[0] * offset,
                origin[1] + tangent[1] * along + normal[1] * offset)

    horn = stool.horn_m
    return (
        point(-half_width - horn, front), point(half_width + horn, front),
        point(half_width + horn, shoulder), point(notch, shoulder),
        point(notch, back), point(-notch, back),
        point(-notch, shoulder), point(-half_width - horn, shoulder),
    )


def window_stool_prism(wall: ResolvedWall, opening,
                       stool: ResolvedWindowStool) -> GPrism | None:
    """A notched board from the room face to the window's inner frame face.

    Rounded where the stool carries ``corner_radii_m`` — the arcs ``haus countertops`` cuts.
    """
    ring = window_stool_ring(wall, opening, stool)
    if ring is None:
        return None
    if len(stool.corner_radii_m) == len(ring):
        ring = filleted_ring(ring, stool.corner_radii_m)
    # Read the product's actual lower rail; a raked wall can clip its height, and a copied
    # frame-width formula here would eventually drift from the opening it must meet.
    frame = next((part for part in opening_parts(wall, opening, None)
                  if part.key == "frame"), None)
    if frame is None:
        return None
    top = frame.solids[-1].z1_m
    return GPrism(ring=ring, z0_m=top - stool.thickness_m, z1_m=top)


# The trade that sets each base kind: a board, a tile base, a flash cove, a rubber base.
_BASE_TRADE = {"trim": "millwork", "tile": "tile", "integral_cove": "flooring",
               "resilient_base": "flooring"}


def base_run_trade(run: ResolvedBaseRun) -> str:
    return _BASE_TRADE.get(run.kind, "millwork")


def base_run_prisms(run: ResolvedBaseRun) -> list[GPrism]:
    """The band of one base run: a board, a tile base or a flash cove."""
    piece = run.piece
    if len(piece.outline) < 3 or piece.z1_m <= piece.z0_m:
        return []
    return [GPrism(ring=piece.outline, z0_m=piece.z0_m, z1_m=piece.z1_m)]


def door_casing_prisms(casing: ResolvedDoorCasing) -> list[GPrism]:
    """One prism per installed casing piece (legs, head, and a hatch's sill)."""
    return [GPrism(ring=piece.outline, z0_m=piece.z0_m, z1_m=piece.z1_m)
            for piece in casing.pieces
            if len(piece.outline) >= 3 and piece.z1_m > piece.z0_m]

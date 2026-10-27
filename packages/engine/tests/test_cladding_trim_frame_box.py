"""A trimmed window's 3D frame box stops at the mount plane, so no buck shows past it."""

from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.opening_flashing import opening_flashing_frame


def _outward_extent(part, frame):
    depths = [(x - frame.origin[0]) * frame.outward[0] + (y - frame.origin[1]) * frame.outward[1]
              for prim in part.solids if hasattr(prim, "ring") for x, y in prim.ring]
    return max(depths, default=None)


def test_every_metal_window_frame_stops_at_the_mount_plane(catlin_model_ro):
    model, checked = catlin_model_ro, 0
    for opening in model.openings:
        seat = opening.window_seat
        if opening.kind != "window" or seat is None or seat.outer_m is None:
            continue
        wall = model.wall(opening.host_wall)
        frame = opening_flashing_frame(model, wall)
        for part in opening_parts(wall, opening, None):
            extent = _outward_extent(part, frame)
            if extent is None or part.key.startswith(("glass", "glaz")):
                continue
            assert extent <= frame.mount + 1e-6, (opening.tag, part.key, extent, frame.mount)
            checked += 1
    assert checked

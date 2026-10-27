"""Seat shallow metal folds over concealed opening laps within the nominal envelope."""

from typehaus.resolve.flashing_config import FLASHING, FlashingConfig
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall
from typehaus.resolve.opening_flashing import opening_flashing_frame


def panel_support_clearance_m(
    model: ResolvedModel, wall: ResolvedWall, layer: ResolvedLayer,
    cfg: FlashingConfig = FLASHING,
) -> float:
    """Reserve the head metal and strip-in at the opening's resolved support plane.

    Direct-applied panels must seat over these laps at their valleys. Rainscreen
    supports already stand outboard of them. Exposed drips and sill outlets do not
    belong to this concealed stack and must not flatten the panel's relief.
    """
    flashed = {solid.host_ref for solid in model.solids
               if solid.category == "opening_flashing_membrane"}
    clearance = 0.0
    for opening in model.openings:
        if opening.host_wall != wall.tag or opening.tag not in flashed:
            continue
        frame = opening_flashing_frame(model, wall, opening)
        if frame is None:
            continue
        support = min((x - frame.origin[0]) * frame.outward[0]
                      + (y - frame.origin[1]) * frame.outward[1] for x, y in layer.polygon)
        metal_trim = opening.window_seat and opening.window_seat.outer_m is not None
        head_plane = frame.mount if metal_trim else frame.water
        # The panel surface must stand clear of the outer membrane surface, including
        # the panel sheet itself, so it does not intersect the head strip-in.
        panel_sheet = SHEET_24_GA_M if metal_trim else 0.0
        clearance = max(clearance, head_plane + cfg.sheet_m + cfg.perimeter_membrane_m
                        + panel_sheet - support)
    return clearance

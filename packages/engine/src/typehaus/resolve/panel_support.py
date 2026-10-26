"""Seat shallow metal folds over concealed opening laps within the nominal envelope."""

from typehaus.resolve.flashing_config import FLASHING, FlashingConfig
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall
from typehaus.resolve.opening_flashing import opening_flashing_frame


def panel_support_clearance_m(
    model: ResolvedModel, wall: ResolvedWall, layer: ResolvedLayer,
    cfg: FlashingConfig = FLASHING,
) -> float:
    """Reserve the head metal and strip-in at the opening's resolved water plane.

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
        clearance = max(clearance, frame.water + cfg.sheet_m + cfg.perimeter_membrane_m - support)
    return clearance

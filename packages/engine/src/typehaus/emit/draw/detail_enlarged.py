"""Enlarged head and sill children of an opening detail (C7-E4, O5-004)."""

from __future__ import annotations

from typehaus.emit.draw.detail_derive import (
    DerivedDetail,
    _condition_opening,
    _host_wall,
    _wall_u_extent,
)
from typehaus.quantities import M_PER_IN, m, pt

#: Overlay recipes whose detail also prints an enlarged head and sill (O5-004): the cap, the
#: strip-in and the pan are unreadable at the whole-opening scale.
ENLARGED_OVERLAYS = frozenset({"outie-window-truss"})
ENLARGED_SCALE = (3.0, "3\" = 1'-0\"")
#: Crop reach off the R.O. edge (below, above) and off the wall faces (inboard, outboard),
#: inches: the head course, cap and drip above a head; the buck, pan and sill trim below.
_ENLARGED_Z_IN = {"head": (9.0, 10.0), "sill": (10.0, 14.0)}
_ENLARGED_U_IN = (3.0, 5.0)


def enlarged_details(model, derived: DerivedDetail) -> list[DerivedDetail]:
    """The enlarged head and sill of an opening detail, as cropped children of it.

    Same key, transition and cut, so the notes and keyed bubbles carry over; only the crop
    narrows to one end of the R.O. and the scale grows (``details._detail_frame``).
    """
    from typehaus.emit.draw.detail_components.geometry import outboard_is_high

    tr = derived.transition
    if derived.part is not None or getattr(tr, "overlay", None) not in ENLARGED_OVERLAYS:
        return []
    wall = _host_wall(model, derived.condition)
    opening = _condition_opening(model, derived.condition)
    if wall is None or opening is None:
        return []
    sill = wall.base_ref_z_m + opening.sill_m
    edges = {"sill": sill, "head": sill + opening.height_m}
    u_lo, u_hi = _wall_u_extent(wall, derived.direction, derived.station, 0.0)
    inboard, outboard = (v * M_PER_IN for v in _ENLARGED_U_IN)
    if outboard_is_high(wall, derived.direction, derived.station) is False:
        inboard, outboard = outboard, inboard
    out = []
    for part in ("head", "sill"):
        below, above = (v * M_PER_IN for v in _ENLARGED_Z_IN[part])
        crop = (pt(m(u_lo - inboard), m(edges[part] - below)),
                pt(m(u_hi + outboard), m(edges[part] + above)))
        view = derived.view.model_copy(update={
            "tag": f"{derived.view.tag}-{part.upper()}", "crop": crop,
            "title": f"{derived.view.title} — enlarged {part}"})
        out.append(DerivedDetail(key=derived.key, condition=derived.condition, transition=tr,
                                 view=view, direction=derived.direction,
                                 station=derived.station, part=part))
    return out


def enlarged_frame(card, center_u: float, center_z: float):
    """The card at ``ENLARGED_SCALE``, re-centred for the gutters at that scale.

    Honoured even where the 8-1/2 x 11 card overflows: the ledger sheet the permit set
    prints it on holds a 2' x 2' crop at 3" = 1'-0".
    """
    from typehaus.emit.draw.detail_card import CALLOUT_GUTTER_IN, LADDER_GUTTER_IN

    scale, label = ENLARGED_SCALE
    shift = (LADDER_GUTTER_IN - CALLOUT_GUTTER_IN) / 2.0 * 12.0 / scale
    return card.model_copy(update={"scale": scale, "scale_label": label,
                                   "center": (center_u - shift, center_z)})

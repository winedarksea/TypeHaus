"""K6 on a metal-wall window: a steel cap that floors the rainscreen cavity over the head.

The cavity above a window drains, it does not vent. The cap's upstand stands on the foam
face, stripped in; its top crosses the cavity, the head course and both jamb posts, falling
outward; its face leg runs down the girt plane over the 58114XX back leg, so water in the
cavity leaves over the head trim and the 1/2" pocket behind the course stays dry
(``notes/opening_flashing_spec.md`` §4). A custom brake from 24 ga PVDF coil.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.flashing_config import FLASHING, FlashingConfig

CAP_PRODUCT = "OPENING_HEAD_CAP"
CAP_UPSTAND_IN = 2.0
CAP_FACE_LEG_IN = 2.5
#: The face leg laps the 58114XX back leg (2-1/2" tall) by at least this much.
CAP_HEAD_LAP_IN = 1.0
HEAD_TRIM_BACK_LEG_IN = 2.5


@dataclass(frozen=True)
class HeadCap:
    start: float
    span: float
    #: (depth, z) from the face leg's foot up to the upstand's top.
    points: tuple[tuple[float, float], ...]
    course_top: float
    head_trim_top: float


def head_cap(model, wall, opening, frame, cfg: FlashingConfig = FLASHING) -> HeadCap | None:
    """The cap's section and span over a seated metal-wall window, or None."""
    from typehaus.resolve.rainscreen_closures import opening_head_spans

    seat = opening.window_seat
    if seat is None or seat.outer_m is None:
        return None
    span = next(((s0, s1, z) for o, s0, s1, z in opening_head_spans(model, wall)
                 if o.uid == opening.uid), None)
    if span is None:
        return None
    s0, s1, top = span
    head_trim_top = (wall.base_ref_z_m + opening.sill_m + opening.height_m - seat.head_drop_m
                     + HEAD_TRIM_BACK_LEG_IN * M_PER_IN)
    leg = max(CAP_FACE_LEG_IN * M_PER_IN, top - (head_trim_top - CAP_HEAD_LAP_IN * M_PER_IN))
    fall = (frame.mount - frame.water) * cfg.drainage_slope
    points = ((frame.mount, top - leg), (frame.mount, top), (frame.water, top + fall),
              (frame.water, top + fall + CAP_UPSTAND_IN * M_PER_IN))
    return HeadCap(s0, s1 - s0, points, top, head_trim_top)


def head_cap_solids(model, wall, opening, frame, material, cfg: FlashingConfig = FLASHING):
    """The cap swept from stock, with its 3/4" end dams, as billable trim."""
    from typehaus.library.trim.metal_sales import OPENING_HEAD_CAP
    from typehaus.resolve.opening_head_drip import swept_head_trim

    cap = head_cap(model, wall, opening, frame, cfg)
    if cap is None:
        return []
    _, (mount, top), (water, high), _ = cap.points
    rise = cfg.head_end_dam_m
    dam = ((water, high), (mount, top), (mount, top + rise), (water, high + rise))
    return swept_head_trim(wall, opening, frame, OPENING_HEAD_CAP, points=cap.points, dam=dam,
                           start=cap.start, span=cap.span, product=CAP_PRODUCT,
                           material=material, uid=f"{opening.uid}-headcap",
                           tag=f"{opening.tag}-HEADCAP")

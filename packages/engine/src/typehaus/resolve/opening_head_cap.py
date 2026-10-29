"""K6 on a metal-wall window: a steel cap that floors the rainscreen cavity over the head.

The cavity above a window drains, it does not vent. The cap's upstand stands on the foam
face, stripped in; its top crosses the cavity, the head course and both jamb posts, falling
outward; its face leg runs down the girt plane over the 58114XX back leg, so water in the
cavity leaves over the head trim and the 1/2" pocket behind the course stays dry
(``notes/opening_flashing_spec.md`` §4). A custom brake from 24 ga PVDF coil.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from typehaus.quantities import M_PER_IN
from typehaus.resolve.flashing_config import FLASHING, FlashingConfig
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M

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
    from typehaus.resolve.cladding_trim.members import split_stock_run
    from typehaus.resolve.cladding_trim.section import folded_section_mesh
    from typehaus.resolve.flashing_solids import flashing_solid
    from typehaus.resolve.sheet_geometry import combine_sheets

    cap = head_cap(model, wall, opening, frame, cfg)
    if cap is None:
        return []
    _, (mount, top), (water, high), _ = cap.points
    stocks = tuple(v * M_PER_IN for v in OPENING_HEAD_CAP.stock_lengths_in)
    pieces = split_stock_run(cap.span, stocks, OPENING_HEAD_CAP.min_lap_in * M_PER_IN)
    solids = []
    for index, (start, end, stock) in enumerate(pieces):
        sheets = [folded_section_mesh(cap.points, frame.point(cap.start + start, 0.0, 0.0),
                                      (*frame.outward, 0.0), (0.0, 0.0, 1.0),
                                      (*(v * (end - start) for v in frame.along), 0.0),
                                      SHEET_24_GA_M)]
        dam = cfg.head_end_dam_m
        for station, sign, first in ((cap.start, 1.0, 0), (cap.start + cap.span, -1.0, -1)):
            if (first == 0 and index == 0) or (first == -1 and index == len(pieces) - 1):
                sheets.append(frame.section(station, ((water, high), (mount, top),
                                                      (mount, top + dam), (water, high + dam)),
                                            SHEET_24_GA_M, sign))
        solid = flashing_solid(uid=f"{opening.uid}-headcap-{index}",
                               tag=f"{opening.tag}-HEADCAP-{index + 1}", storey=wall.storey,
                               category="cladding_trim", mesh=combine_sheets(sheets),
                               material=material, host_ref=opening.tag)
        solids.append(replace(solid, product=CAP_PRODUCT, trim_length_m=end - start,
                              trim_stock_length_in=stock / M_PER_IN))
    return solids

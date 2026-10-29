"""A generic Z drip flashing over a window or door head on a non-metal rainscreen.

Fiber cement over furring has no maker's metal kit, so its heads take a brake-formed Z
(IRC R703.4 item 1, R703.4.1). The section is the drip head ``head_flashing_section`` has
always drawn: an upstand on the water plane, taped under the WRB above it (the perimeter
membrane's strip-in), a leg falling outward across the cavity, the cladding and the head
casing, and a drip past the casing face. Both ends turn up 3/4" dams. It is swept from stock
as billable trim, chosen by the cladding Material's kit (``TrimCondition.OPENING_HEAD``), so a
house opts in by its siding. The cavity's foot over the head is closed by a perforated strip
under the cladding's bottom edge, 1/4" off the flashing (``rainscreen_strips``).
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.flashing_config import FLASHING, FlashingConfig
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M

DRIP_HEAD_PRODUCT = "OPENING_HEAD_DRIP_FLASHING"


def drip_head_key(model, wall, opening) -> str | None:
    """The kit's generic head flashing for this opening, or None (metal wall, no cavity)."""
    from typehaus.library.trim.metal_sales import PROFILES
    from typehaus.resolve.cladding_trim.openings import is_profiled_metal_wall
    from typehaus.resolve.cladding_trim.runs import kit_faces
    from typehaus.resolve.rainscreen_closures import rainscreen_band

    if opening.kind not in ("window", "door") or rainscreen_band(wall.layers) is None \
            or is_profiled_metal_wall(model, wall):
        return None
    condition = TrimCondition.DOOR_HEAD if opening.kind == "door" else TrimCondition.OPENING_HEAD
    key = next((key for face, key in kit_faces(model, condition)
                if face.wall.tag == wall.tag), None)
    return key if key == DRIP_HEAD_PRODUCT and key in PROFILES else None


def swept_head_trim(wall, opening, frame, profile, *, points, dam, start, span, product,
                    material, uid, tag) -> list:
    """``points`` swept along ``span`` from stock, the run's two ends closed by ``dam``.

    ``uid``/``tag`` are stems; each piece appends its index."""
    from typehaus.resolve.cladding_trim.members import split_stock_run
    from typehaus.resolve.cladding_trim.section import folded_section_mesh
    from typehaus.resolve.flashing_solids import flashing_solid
    from typehaus.resolve.sheet_geometry import combine_sheets

    stocks = tuple(v * M_PER_IN for v in profile.stock_lengths_in)
    pieces = split_stock_run(span, stocks, profile.min_lap_in * M_PER_IN)
    solids = []
    for index, (s0, s1, stock) in enumerate(pieces):
        sheets = [folded_section_mesh(points, frame.point(start + s0, 0.0, 0.0),
                                      (*frame.outward, 0.0), (0.0, 0.0, 1.0),
                                      (*(v * (s1 - s0) for v in frame.along), 0.0),
                                      SHEET_24_GA_M)]
        if index == 0:
            sheets.append(frame.section(start, dam, SHEET_24_GA_M, 1.0))
        if index == len(pieces) - 1:
            sheets.append(frame.section(start + span, dam, SHEET_24_GA_M, -1.0))
        solid = flashing_solid(uid=f"{uid}-{index}", tag=f"{tag}-{index + 1}",
                               storey=wall.storey, category="cladding_trim",
                               mesh=combine_sheets(sheets), material=material,
                               host_ref=opening.tag)
        solids.append(replace(solid, product=product, trim_length_m=s1 - s0,
                              trim_stock_length_in=stock / M_PER_IN))
    return solids


def drip_head_solids(model, wall, opening, frame, material, key,
                     cfg: FlashingConfig = FLASHING) -> list:
    """The Z swept over the head: RO plus casing and a 1" lap past each end."""
    from typehaus.library.trim.metal_sales import PROFILES
    from typehaus.resolve.opening_flashing import head_flashing_section

    head = head_flashing_section(wall, opening, frame, cfg)
    (water, bend), (front, seat) = head.points[1], head.points[2]
    rise = cfg.head_end_dam_m
    dam = ((water, bend), (front, seat), (front, seat + rise), (water, bend + rise))
    return swept_head_trim(wall, opening, frame, PROFILES[key], points=head.points, dam=dam,
                           start=head.start, span=head.span, product=key, material=material,
                           uid=f"{opening.uid}-trim-head", tag=f"{opening.tag}-TRIM-HEAD")

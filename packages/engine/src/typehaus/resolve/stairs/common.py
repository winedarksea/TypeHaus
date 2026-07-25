"""Shared stair-generator constants and small pure helpers (see package docstring)."""

from __future__ import annotations

import math

from typehaus.quantities import inch

_MAX_RISER_M = 7.75 * 0.0254  # IRC R311.7
_MIN_TREAD_M = 10.0 * 0.0254
_TREAD_THICKNESS_IN = 1.5  # a 1.5" tread/deck board
_TREAD_THICKNESS_M = inch(_TREAD_THICKNESS_IN).meters
_LANDING_JOIST_PROFILE = "2x8"
_FRAMING_SPACING_M = 0.4064  # 16" o.c.
# Two members closer than one 2x ply's thickness are one member, not two — see
# ``_grid_positions``. Below this they would interpenetrate rather than sit side by side.
_MIN_MEMBER_PITCH_M = inch(1.5).meters
# Below this a stair member only clips a wall's end; it does not bear on it.
_MIN_SHARED_RUN_M = 0.10
# A U-stair's well partition is real construction between the two flights — 2x4 studs
# finished both faces — so it consumes cross-run space. Budgeting nothing for it (the
# lanes used to butt at ``lane0 + width``) put the partition studs straight through both
# inner stringers and made "the well is N wide" mean two different things depending on
# whether you measured the flights or the finished faces.
_WELL_PARTITION_STUD_IN = 3.5
_WELL_PARTITION_FINISH_IN = 0.5  # gwb, each face
_WELL_PARTITION_THICKNESS_M = inch(
    _WELL_PARTITION_STUD_IN + 2 * _WELL_PARTITION_FINISH_IN).meters


def _tread_board_profile(going_m: float) -> str:
    """Profile string for a tread board of ``going_m`` depth.

    A ``deck WxT`` profile renders at its true plan width (see framing/profiles.py), so the
    board reads as the full-depth tread a framer nails down. Spelling a tread ``"2x12"``
    instead drew every one of them as a 1.5"-wide strip — the *thickness* face of the stock,
    which is what a member's plan footprint is built from, not its depth.
    """
    return f"deck {going_m / inch(1).meters:g}x{_TREAD_THICKNESS_IN:g}"


def _newel_face_point(newel: tuple[float, float], toward: tuple[float, float],
                      half_face_m: float) -> tuple[float, float]:
    """Where the ray ``newel`` -> ``toward`` leaves the square newel post's face.

    Every winder narrow end used to sit on the newel *centreline*, so all of them converged
    on one bare point and the narrow-end tread depth was exactly 0 (defect D2 in
    plans/TODO.md). A winder actually starts at the face the newel presents to it, which is
    what this returns. It does not by itself buy the 6" IRC R311.7.5.2.1 wants at the narrow
    end — a quarter turn taken in this few risers cannot — so
    ``structural.winder_narrow_tread_depth`` measures what the layout does deliver.
    """
    dx, dy = toward[0] - newel[0], toward[1] - newel[1]
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return newel
    ux, uy = dx / run, dy / run
    # A square footprint: the ray exits through whichever face its dominant axis points at.
    reach = half_face_m / max(abs(ux), abs(uy))
    return (newel[0] + ux * reach, newel[1] + uy * reach)


def _grid_positions(span: float, spacing: float) -> list[float]:
    """Deduplicated on-center positions ``{0, s, 2s, …, span}`` including both edges.

    Replaces the old ``ceil``/``range``/``min``-clamp pattern whose last two positions
    were coincident whenever ``span`` was an exact multiple of ``spacing``.

    Members are deduplicated at ``_MIN_MEMBER_PITCH_M``, not at floating-point equality:
    a closing edge landing an inch short of the last on-center position is the *same*
    member, and emitting both drew two 2x plies interpenetrating in plan.
    """
    if span <= 1e-9:
        return [0.0]
    positions = [spacing * index for index in range(math.ceil(span / spacing - 1e-9))]
    positions.append(span)
    out: list[float] = []
    for position in positions:
        if out and position - out[-1] < _MIN_MEMBER_PITCH_M:
            out[-1] = position  # the edge wins: it is what the member has to close on
        else:
            out.append(position)
    return out

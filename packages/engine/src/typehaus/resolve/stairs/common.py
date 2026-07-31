"""Shared stair-generator constants and small pure helpers (see package docstring)."""

from __future__ import annotations

import math

from typehaus.quantities import inch

_MAX_RISER_M = 7.75 * 0.0254  # IRC R311.7
_MIN_TREAD_M = 10.0 * 0.0254
_DEFAULT_TREAD_DEPTH_M = inch(11).meters
_DEFAULT_NOSING_DEPTH_M = inch(1).meters
_MIN_NOSING_DEPTH_M = inch(0.75).meters
_MAX_NOSING_DEPTH_M = inch(1.25).meters
# IRC R311.7.6: "every landing shall have a minimum dimension of 36 inches measured in the
# direction of travel". The *width* rule in the same section — a landing is never narrower
# than the stairway it serves — is about the cross-run dimension, which a U-stair's
# half-landing satisfies by construction (it is exactly one flight wide). Flooring the
# authored depth at the stair width instead conflated the two and silently lengthened every
# well by (width - 36") for no code reason.
_MIN_LANDING_DEPTH_M = 36.0 * 0.0254
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


def _notch_z(surface_m: float) -> float:
    """The framing elevation directly under a finished walking surface at ``surface_m``.

    Every board a foot lands on — a tread, a landing deck, a winder box's deck — is
    *dropped*: its finished face lands exactly on the step's theoretical elevation and the
    stock hangs below it. This is the "dropping the stringer" rule (Larry Haun, *The Very
    Efficient Carpenter*): the bottom of a stringer's notching is cut down by the tread
    thickness so every finished riser stays identical.

    Sitting the board *on* that elevation instead — the convention this replaces —
    stretched a stair's first riser by the board thickness and shortened its last by the
    same amount, because the springing floor and the arrival deck are finished surfaces
    already. On catlin's 7.5" design riser that was a 9" step onto the flight and a 6"
    step off it: a 3" spread against the 3/8" IRC R311.7.5.1 allows, now measured by
    ``structural.stair_riser_uniformity``.
    """
    return surface_m - _TREAD_THICKNESS_M


def _tread_board_profile(tread_depth_m: float) -> str:
    """Profile string for a tread board of ``going_m`` depth.

    A ``deck WxT`` profile renders at its true plan width (see framing/profiles.py), so the
    board reads as the full-depth tread a framer nails down. Spelling a tread ``"2x12"``
    instead drew every one of them as a 1.5"-wide strip — the *thickness* face of the stock,
    which is what a member's plan footprint is built from, not its depth.
    """
    return f"deck {tread_depth_m / inch(1).meters:g}x{_TREAD_THICKNESS_IN:g}"


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

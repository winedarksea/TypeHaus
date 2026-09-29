"""Shared stair-generator constants and small pure helpers (see package docstring)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.model.spatial import Stair

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
# finished both faces — so it consumes cross-run space. Without a budget for it, the
# partition studs would run straight through both inner stringers, and "the well is N
# wide" would mean two different things depending on whether you measured the flights
# or the finished faces.
_WELL_PARTITION_STUD_IN = 3.5
_WELL_PARTITION_FINISH_IN = 0.5  # gwb, each face
_WELL_PARTITION_THICKNESS_M = inch(
    _WELL_PARTITION_STUD_IN + 2 * _WELL_PARTITION_FINISH_IN).meters


def _tread_thickness(stair: Stair) -> float:
    """The stock thickness under this flight's walking surfaces, in metres.

    ``Stair.tread_thickness`` is how a flight says "the substrate is thinner than the
    default 1 1/2" because a finish makes up the rest" — 1" of ply under 1/2" of
    carpet-over-cushion, say. It is the *bought* thickness, so it is what the takeoff must
    bill. A declared covering is subsequently placed above this stock and the substrate
    and support are lowered by its depth, preserving the finished riser elevations.
    """
    return (stair.tread_thickness.meters if stair.tread_thickness is not None
            else _TREAD_THICKNESS_M)


def _notch_z(surface_m: float, thickness_m: float = _TREAD_THICKNESS_M) -> float:
    """The framing elevation directly under a finished walking surface at ``surface_m``.

    Every board a foot lands on — a tread, a landing deck, a winder box's deck — is
    *dropped*: its finished face lands exactly on the step's theoretical elevation and the
    stock hangs below it. This is the "dropping the stringer" rule (Larry Haun, *The Very
    Efficient Carpenter*): the bottom of a stringer's notching is cut down by the tread
    thickness so every finished riser stays identical.

    Sitting the board *on* that elevation instead stretches a stair's first riser by the
    board thickness and shortens its last by the same amount, because the springing floor
    and the arrival deck are already finished surfaces — checked against IRC R311.7.5.1's
    3/8" tolerance by ``structural.stair_riser_uniformity``.

    ``thickness_m`` is the flight's own stock (``_tread_thickness``). Every surface in one
    flight has to share it: drop the treads 1" and leave the landing deck at 1 1/2" and the
    two risers at that landing differ by the 1/2" the deck was not dropped.
    """
    return surface_m - thickness_m


def _tread_board_profile(tread_depth_m: float,
                         thickness_m: float = _TREAD_THICKNESS_M) -> str:
    """Profile string for a tread board of ``going_m`` depth.

    A ``deck WxT`` profile renders at its true plan width (see framing/profiles.py), so the
    board reads as the full-depth tread a framer nails down. Spelling a tread ``"2x12"``
    instead drew every one of them as a 1.5"-wide strip — the *thickness* face of the stock,
    which is what a member's plan footprint is built from, not its depth.
    """
    return f"deck {tread_depth_m / inch(1).meters:g}x{thickness_m / inch(1).meters:g}"


def _grid_positions(span: float, spacing: float) -> list[float]:
    """Deduplicated on-center positions ``{0, s, 2s, …, span}`` including both edges.

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


def _spacing(stair: Stair) -> float | None:
    """``Stair.stringer_spacing`` in metres, or ``None`` for two edge stringers."""
    return stair.stringer_spacing.meters if stair.stringer_spacing is not None else None


def _stringer_offsets(width: float, spacing: float | None,
                      thickness: float) -> list[float]:
    """Cross-run carriage centrelines, measured from the flight's ``0`` edge.

    ``Stair.width`` is the clear tread width (IRC R311.7.1), so the two OUTER members sit
    inside it, inset half their ``thickness``; centred on the edge they hung half a ply into
    the wall or its finish. Interior members divide the width evenly at ``spacing``
    (``Stair.stringer_spacing``) and do not move.
    """
    bays = max(1, math.ceil(width / spacing - 1e-9)) if spacing is not None else 1
    offsets = [width * index / bays for index in range(bays + 1)]
    offsets[0] += thickness / 2.0
    offsets[-1] -= thickness / 2.0
    return offsets


Line = tuple[tuple[float, float], tuple[float, float]]


def _riser_member(stair: Stair, key: str, line: Line, ascent: tuple[float, float],
                  bottom: float, top: float, behind: bool = True) -> FramedMember | None:
    """A closed riser board standing on ``line`` from ``bottom`` to ``top``, or ``None`` for
    an open-riser flight (``Stair.riser_thickness``).

    ``behind`` sets it back from the riser face along ``ascent``, under the nosing of the
    tread it carries. A riser against framing (a winder box's fan rim, a landing's edge
    joist) stands in front of it, on the step below.
    """
    if stair.riser_thickness is None or top - bottom <= 1e-6:
        return None
    thick = stair.riser_thickness.meters
    shift = thick / 2.0 if behind else -thick / 2.0
    (ax, ay), (bx, by) = line
    dx, dy = ascent[0] * shift, ascent[1] * shift
    profile = f"{thick / 0.0254:.3f}x{(top - bottom) / 0.0254:.3f}"
    return FramedMember(stair.uid, key, "riser", profile, (ax + dx, ay + dy),
                        (bx + dx, by + dy), bottom, top, math.hypot(bx - ax, by - ay),
                        orient=ascent)


def head_board(stair: Stair, finish_m: float = 0.0) -> float:
    """What a head riser puts between its line and the framing it faces: the board, plus a
    covering on its face, which ``lower_stair_substrates`` pushes the board back behind."""
    return stair.riser_thickness.meters + finish_m if stair.riser_thickness is not None else 0.0


def _ascent(tread: FramedMember) -> tuple[float, float]:
    """The unit plan direction up the flight at a straight tread: riser face to board axis."""
    (ax, ay), (bx, by) = tread.riser_line
    mx = (tread.p0[0] + tread.p1[0] - ax - bx) / 2.0
    my = (tread.p0[1] + tread.p1[1] - ay - by) / 2.0
    norm = math.hypot(mx, my)
    return (mx / norm, my / norm)


def _tread_risers(stair: Stair, treads: list[FramedMember], riser: float, going: float,
                  prefix: str = "", head: bool = True) -> list[FramedMember]:
    """A riser under every straight tread (``treads`` in ascent order), and with ``head`` one
    more a going past the last, under the landing or arrival edge.

    The head board stands like every other, face on its riser line and the board beyond it,
    so the last tread is one going deep (IRC R311.7.5.2.1). The framing it faces therefore
    sits one board past the line: the layouts set landings back and hang flights off an
    arrival header by ``head_board``."""
    out: list[FramedMember] = []
    for index, tread in enumerate(treads):
        out.append(_riser_member(stair, f"riser{prefix}-{index:03d}", tread.riser_line,
                                 _ascent(tread), tread.z1_m - riser, tread.z0_m))
    if head and treads:
        last = treads[-1]
        ux, uy = _ascent(last)
        (ax, ay), (bx, by) = last.riser_line
        line = ((ax + ux * going, ay + uy * going), (bx + ux * going, by + uy * going))
        out.append(_riser_member(stair, f"riser{prefix}-{len(treads):03d}", line, (ux, uy),
                                 last.z1_m, last.z1_m + riser - _tread_thickness(stair)))
    return [member for member in out if member is not None]

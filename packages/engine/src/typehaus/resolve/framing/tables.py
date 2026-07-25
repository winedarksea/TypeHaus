"""Framing dimension tables — one module, two consumers (solver + structural checks, → 11)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.enums import DoorOperation
from typehaus.quantities import Length, ft, inch

# Nominal → actual dressed lumber dimensions (thickness, depth) in inches.
LUMBER_ACTUAL: dict[str, tuple[float, float]] = {
    "2x4": (1.5, 3.5),
    "2x6": (1.5, 5.5),
    "2x8": (1.5, 7.25),
    "2x10": (1.5, 9.25),
    "2x12": (1.5, 11.25),
    "1x4": (0.75, 3.5),
    "4x4": (3.5, 3.5),  # dressed post (stair-landing corner posts)
    "6x6": (5.5, 5.5),  # dressed post (e.g. balcony pillars)
}

DEFAULT_SPACING = inch(16)
DEFAULT_TEE_BLOCKING_SPACING = inch(24)


def member_actual(nominal: str) -> tuple[float, float]:
    return LUMBER_ACTUAL.get(nominal, (1.5, 5.5))


def king_jack_counts(opening_width: Length) -> tuple[int, int]:
    """King + jack (trimmer) studs per side, from opening width (simplified table)."""
    w_ft = opening_width.feet
    if w_ft <= 4.0:
        return (1, 1)
    if w_ft <= 6.0:
        return (1, 1)
    if w_ft <= 8.0:
        return (1, 2)
    return (2, 2)


def header_size(opening_width: Length, bearing: bool = True) -> str:
    """Header size over an opening (simplified prescriptive lookup, R602.7)."""
    w_ft = opening_width.feet
    if not bearing:
        return "2-2x6"
    if w_ft <= 4.0:
        return "2-2x8"
    if w_ft <= 6.0:
        return "2-2x10"
    if w_ft <= 8.0:
        return "2-2x12"
    return ENGINEERED_LVL  # beyond prescriptive; structural check flags it


ENGINEERED_LVL = "engineered-LVL"

# Stocked LVL depths (inches). Beyond the prescriptive table ``header_size`` names an
# engineered member with no nominal lumber depth to look up, but the solver still has to
# place a member of a real depth — a 16 ft garage header drawn at the 2x depth of a
# bedroom door reads as a mistake in every section and takeoff.
LVL_STOCK_DEPTHS_IN = (9.25, 11.875, 14.0, 16.0, 18.0)
# Residential garage/gable header rule of thumb: depth ≈ span / 20, rounded up to stock.
LVL_DEPTH_SPAN_RATIO = 20.0


def header_depth(size: str, opening_width: Length) -> Length:
    """Actual depth of the header ``size`` names, so the solver never hardcodes one."""
    if size == ENGINEERED_LVL:
        required_in = opening_width.inches / LVL_DEPTH_SPAN_RATIO
        # Above the deepest stocked ply the member is a designed beam; the structural
        # check already flags every engineered header, so carry the deepest stock depth
        # rather than inventing a size.
        return inch(next((depth for depth in LVL_STOCK_DEPTHS_IN if depth >= required_in),
                         LVL_STOCK_DEPTHS_IN[-1]))
    # "2-2x12" → two plies of a 2x12; the depth is the ply depth, not the ply count.
    return inch(member_actual(size.split("-")[-1])[1])


@dataclass(frozen=True)
class OpeningFramingPattern:
    """How one door operation is framed beyond the shared king/jack/header pack.

    Only operations that genuinely differ get an entry; everything else is framed as a
    plain rough opening, which is what a swing, slide or pocket door actually needs.
    """

    #: Trimmer span carried per jack stud, or ``None`` to use ``king_jack_counts``.
    span_per_jack: Length | None = None
    #: Continuous jamb legs beside the trimmers, carrying the vertical door track.
    needs_track_jamb_legs: bool = False
    #: Horizontal backing over the head that the ceiling track and operator hang from.
    needs_track_backing: bool = False
    #: False → a flat nailer head instead of a bearing header (non-structural opening).
    header_is_structural: bool = True


# An overhead sectional concentrates its whole reaction on two jamb packs and additionally
# carries the door's own weight, the counterbalance spring anchor and the operator track,
# so the width-only prescriptive table (capped at 2 kings + 2 jacks past 8 ft) under-frames
# it: a 16 ft span gets the same pack as a 9 ft one. Sizing the trimmer pack from the span
# and adding the track backing is the difference between a drawn door and a buildable one.
# One trimmer per 6 ft of span keeps the header's perpendicular-to-grain bearing on the
# jamb pack inside SPF allowables (a 16 ft door → three trimmers a side).
OVERHEAD_SPAN_PER_JACK = ft(6)
# The vertical track jambs and the head backing are 2x6 regardless of the wall's stud
# size — the track brackets and the operator hangers need that face width to land on.
OVERHEAD_TRACK_MEMBER = "2x6"

# A bifold hangs entirely from its own head track inside a non-bearing partition: it needs
# a flat head nailer to screw the track to, not a bearing header and trimmer pack.
OPENING_FRAMING_PATTERNS: dict[DoorOperation, OpeningFramingPattern] = {
    DoorOperation.OVERHEAD: OpeningFramingPattern(
        span_per_jack=OVERHEAD_SPAN_PER_JACK,
        needs_track_jamb_legs=True,
        needs_track_backing=True,
    ),
    DoorOperation.BIFOLD: OpeningFramingPattern(header_is_structural=False),
}


def opening_framing_pattern(operation: DoorOperation | None) -> OpeningFramingPattern:
    """The framing pattern for a door operation (``None`` → window/rough opening)."""
    if operation is None:
        return _DEFAULT_OPENING_PATTERN
    return OPENING_FRAMING_PATTERNS.get(operation, _DEFAULT_OPENING_PATTERN)


_DEFAULT_OPENING_PATTERN = OpeningFramingPattern()


def jamb_pack_counts(opening_width: Length,
                     pattern: OpeningFramingPattern) -> tuple[int, int]:
    """King + jack studs per side for an opening framed under ``pattern``.

    Patterns without a ``span_per_jack`` fall back to the prescriptive width table; those
    with one size the trimmer pack from the actual span and match kings to jacks, since a
    jack that is not backed by a king has nothing to transfer its load into.
    """
    if pattern.span_per_jack is None:
        return king_jack_counts(opening_width)
    jacks = max(1, math.ceil(opening_width.meters / pattern.span_per_jack.meters))
    return (jacks, jacks)

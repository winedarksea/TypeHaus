"""How one opening lands on the wall's stud module (→ 11 §Framing, plans/TODO.md).

The single place that answers the two questions the framing solver, the structural check and
the plan annotation all ask about an opening: *how many stud lines does it interrupt at the
configured o.c.*, and *is its position awkward* — i.e. does it interrupt more studs than an
opening of its width has to?

An opening that interrupts nothing fits inside one stud bay: the load path over it is
uninterrupted, so it needs no structural header, only a rough sill and head nailer bearing
on the two intact bounding studs.

A stud is interrupted when its *body* falls inside the rough opening, not merely its
centreline: at 16" o.c. with 2x studs the clear bay is 14.5", which is why a 14" window fits
and a 15" one — whose edges cut 1/4" into each flanking stud — does not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# A stud face exactly on the rough-opening edge is not interrupted; this keeps that
# floating-point-exact case out of the count without loosening anything real.
_TOUCHING_CLEARANCE_M = 1e-6


def studs_interrupted(center_m: float, half_width_m: float, spacing_m: float,
                      stud_thickness_m: float = 0.0, phase_m: float = 0.0) -> int:
    """How many on-module studs an opening interrupts (0 => it fits inside a bay).

    ``phase_m`` is the wall-local station of the module's first stud. 0.0 is the wall's own
    start node, which is where the solver puts the grid unless the assembly asks to lay out
    from its layout line instead (``FramingSpec.layout_origin``) — and this arithmetic has
    to know, because it is what decides that an opening needs no jamb pack. Answering for
    the wrong grid says "it fits inside a bay" about an opening a module stud runs straight
    through, and the stud then interpenetrates the rough sill.
    """
    if spacing_m <= 0.0:
        return 0
    reach = half_width_m + stud_thickness_m / 2.0 - _TOUCHING_CLEARANCE_M
    lowest = math.ceil((center_m - reach - phase_m) / spacing_m)
    highest = math.floor((center_m + reach - phase_m) / spacing_m)
    return max(0, highest - lowest + 1)


@dataclass(frozen=True)
class OpeningStudModule:
    """Structured verdict on one opening's position relative to the stud module."""

    #: Studs the rough opening actually interrupts at the configured spacing.
    interrupted: int
    #: The fewest an opening of this width could interrupt, at its best position.
    minimum_interrupted: int
    #: Distance from the RO centre to the nearest position achieving ``minimum_interrupted``.
    offset_from_ideal_m: float
    #: Whether that best position is a stud line (0.0) or a bay centre (spacing / 2).
    ideal_is_bay_centre: bool
    spacing_m: float

    @property
    def fits_between_studs(self) -> bool:
        """True when the opening lands wholly inside one bay — no header needed."""
        return self.interrupted == 0

    @property
    def straddles_awkwardly(self) -> bool:
        """True when its position costs a stud its width does not require.

        An off-centre 30" RO that cuts two studs instead of one doubles the jack/header
        work and wastes a stud bay; the same RO shifted onto the stud line costs one.
        """
        return self.interrupted > self.minimum_interrupted

    @property
    def ideal_label(self) -> str:
        return "bay centre" if self.ideal_is_bay_centre else "stud line"

    def describe(self) -> str:
        """One-line summary for a finding message."""
        spacing_in = self.spacing_m / 0.0254
        plural = "" if self.interrupted == 1 else "s"
        text = f"interrupts {self.interrupted} stud{plural} at {spacing_in:.0f}\" o.c."
        if self.straddles_awkwardly:
            text += (f" instead of {self.minimum_interrupted}: its centre sits "
                     f"{self.offset_from_ideal_m / 0.0254:.1f}\" off the nearest "
                     f"{self.ideal_label}")
        return text


def opening_stud_module(center_m: float, width_m: float, spacing_m: float,
                        stud_thickness_m: float = 0.0,
                        phase_m: float = 0.0) -> OpeningStudModule:
    """Analyse one opening against the stud module at ``spacing_m``.

    ``phase_m`` shifts the whole grid off the wall's start node — see
    :func:`studs_interrupted`. It moves the ideal positions with it, so "on its stud line"
    and "on its bay centre" keep meaning the same thing about the studs actually framed.
    """
    half = width_m / 2.0
    interrupted = studs_interrupted(center_m, half, spacing_m, stud_thickness_m, phase_m)
    if spacing_m <= 0.0:
        return OpeningStudModule(0, 0, 0.0, True, spacing_m)
    # Symmetric framing only ever wants the RO centred on a stud line or on a bay centre;
    # evaluating both candidates is exact, and avoids a closed-form minimum drifting from
    # the counting rule above.
    candidates = []
    for is_bay_centre, ideal_offset in ((True, phase_m + spacing_m / 2.0),
                                        (False, phase_m)):
        count = studs_interrupted(ideal_offset, half, spacing_m, stud_thickness_m, phase_m)
        shifted = ((center_m - ideal_offset + spacing_m / 2.0) % spacing_m) - spacing_m / 2.0
        candidates.append((count, abs(shifted), is_bay_centre))
    minimum, offset, ideal_is_bay_centre = min(candidates)
    return OpeningStudModule(interrupted, minimum, offset, ideal_is_bay_centre, spacing_m)

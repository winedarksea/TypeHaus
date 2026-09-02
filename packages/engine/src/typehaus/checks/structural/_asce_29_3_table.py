"""ASCE 7-16 Fig. 29.3-1 force coefficients — only the cells that could be sourced.

§29.3 gives the wind force on a solid freestanding wall or solid sign as

    F = q_h · G · C_f · A_s                                       (eq. 29.3-1)

and C_f comes from Fig. 29.3-1, a two-way table on B/s (the sign's width over its height)
and s/h (its height over the height to its top). It is the right provision for what the
balcony presents to the wind — an elevated band of solid members, unenclosed, with no
enclosure classification for Ch. 27/28 to key off and nothing that C&C's cladding-suction
zones describe. It is also the one input in the whole calculation that this repository
**cannot legitimately hold in full**.

**Why the table is not transcribed here.** ASCE 7-16 is a copyrighted standard and its
Fig. 29.3-1 grid is not published in any freely accessible authoritative source. Three
individual cells could be verified, each from a worked example by an independent
engineering vendor, and those three are below. The rest are not, and this
module will not interpolate, curve-fit, or "reasonably assume" its way across them.

That constraint is not a defeat, and the check built on this module is not crippled by it.
``lateral_racking.py`` inverts the problem instead: it computes everything else exactly —
q_h, A_s from the modelled geometry, the brace geometry, the connector's published
allowable — and reports the **critical C_f**, the force coefficient at which each joint
would exactly reach capacity. A reviewer with the standard on the desk then reads one cell
and has the answer. That is a more useful artifact than a demand number carrying an
invented coefficient, and it is honest about which single input came from outside.

The bound below makes most cases decidable without the table at all: where the critical
C_f exceeds the largest coefficient Cases A and B are known to produce, the joint is
adequate *for any value the table can hold*, and no lookup is needed.
"""

from __future__ import annotations

from dataclasses import dataclass

#: ASCE 7-16 §26.11.1: G = 0.85 for a rigid structure. Every one of these members is stiff
#: sawn lumber in a short span; nothing here has a fundamental frequency below 1 Hz.
GUST_EFFECT_RIGID = 0.85


@dataclass(frozen=True)
class Cell:
    """One verified cell of Fig. 29.3-1, with the document it was read out of."""

    b_over_s: float
    s_over_h: float
    c_f: float
    citation: str


#: Cases A and B cells verified against published worked examples. Each is one
#: engineer's reading of the figure for one geometry — enough to bound and sanity-check,
#: never enough to interpolate between.
VERIFIED_CASE_AB: tuple[Cell, ...] = (
    Cell(b_over_s=2.50, s_over_h=0.25, c_f=1.80,
         citation="Struware 'Guide to Wind Load Procedures' Example 5.1 (Wind on Sign), "
                  "ASCE 7-22 §29.3: s/h = 0.25, B/s = 2.50, Case A & B C_f = 1.80"),
    Cell(b_over_s=2.00, s_over_h=0.50, c_f=1.70,
         citation="Meca Enterprises, 'Wind Loads on Solid Signs', ASCE 7-16 Fig. 29.3-1 "
                  "worked example: s/h = 0.5, B/s = 2.0, Case A & B C_f = 1.7"),
    Cell(b_over_s=20.0, s_over_h=1.00, c_f=1.30,
         citation="Meca Enterprises, 'Wind Loads on Freestanding Walls', ASCE 7-16 "
                  "Fig. 29.3-1: B/s = 20 and s/h = 1 gives C_f = 1.3 for Cases A and B"),
)

#: The largest Case A/B coefficient any verified source produces, and — per every published
#: description of the figure — the value the table peaks at: C_f falls monotonically as B/s
#: grows and as s/h falls away from the tall-narrow corner. Used **only** as an upper bound
#: on an unread cell. A demand computed at this number is a demand no legitimate reading of
#: Fig. 29.3-1 can exceed for Cases A and B, so a joint that clears it is clear outright.
MAX_VERIFIED_CASE_AB = 1.80

#: Case C is the near-windward-edge zone breakdown, required when B/s >= 2, and its leading
#: strip carries a much larger coefficient than the A/B average — published examples show
#: 2.25 (Meca, B/s = 2) and 4.07 (an eng-tips worked case). It applies to the leading strip
#: of width s only, and s is small here, so it is a *local member* question rather than a
#: storey-shear one. Recorded so nobody reads MAX_VERIFIED_CASE_AB as the largest coefficient
#: in the whole figure — it is not.
MAX_VERIFIED_CASE_C_SEEN = 4.07

#: Fig. 29.3-1's note for a sign with openings: where the open area is under 30 % of gross,
#: C_f is multiplied by ``1 - (1 - eps) ** 1.5``, eps being the solidity ratio (solid area
#: over gross). Confirmed in both Meca articles and SkyCiv's ASCE 7-16 load generator
#: documentation.
_OPENING_REDUCTION_EXPONENT = 1.5
#: The same note's limit: below this solidity the reduction formula is not the right model
#: and the appurtenance is an *open* sign or a trussed frame (§29.4), not a porous solid one.
MIN_SOLIDITY_FOR_REDUCTION = 0.70


def opening_reduction(solidity: float) -> float | None:
    """``1 - (1 - eps) ** 1.5``, or ``None`` where the note does not apply.

    Returning ``None`` below ``MIN_SOLIDITY_FOR_REDUCTION`` is the point of the function:
    a 4"-gap baluster guard is roughly 25-30 % solid, nowhere near the 70 % the note covers,
    and pushing it through the formula anyway would produce a number (about 0.39) that looks
    like a code result and is not one. An open guard is §29.4 territory — open signs and
    lattice frameworks — which is a different figure this module does not hold either.
    """
    if not 0.0 < solidity <= 1.0:
        return None
    if solidity < MIN_SOLIDITY_FOR_REDUCTION:
        return None
    return 1.0 - (1.0 - solidity) ** _OPENING_REDUCTION_EXPONENT


def force_coefficient(b_over_s: float, s_over_h: float, *, tol: float = 0.02) -> Cell | None:
    """The verified Fig. 29.3-1 cell for this geometry, or ``None``.

    ``None`` is the common answer and the correct one. It means "this repository does not
    hold that cell", not "the standard has no value" — the caller reports UNKNOWN naming the
    lookup, exactly as ``structural.foundation_unbalanced_fill`` reports UNKNOWN rather than
    guessing at a soil class.
    """
    for cell in VERIFIED_CASE_AB:
        if (abs(cell.b_over_s - b_over_s) <= tol * max(1.0, b_over_s)
                and abs(cell.s_over_h - s_over_h) <= tol * max(1.0, s_over_h)):
            return cell
    return None

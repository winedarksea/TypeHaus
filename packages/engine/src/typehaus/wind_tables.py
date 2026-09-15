"""ASCE 7-16 Fig. 29.3-1 force coefficients — only the cells that could be sourced.

**Beside ``wind.py``, not under ``checks/``, since 2026-09-07.** It was
``checks/structural/_asce_29_3_table``, and two of its three consumers are in
``engineering/`` — which is a leaf that may not import the checks tree, and whose
``__init__`` eagerly imports all of it. A copyrighted standard's data table is not a check;
it is the same kind of thing ``wind.py`` holds, and it belongs where both consumers can
reach it without dragging a package they must not depend on.

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


# ---------------------------------------------------------------------------------------
# IRC Table R802.11 — rafter/truss uplift connection force from wind
# ---------------------------------------------------------------------------------------
#
# ** THIS ONE *IS* TRANSCRIBED, AND THE DIFFERENCE FROM Fig. 29.3-1 ABOVE IS NOT A CHANGE OF
# HEART. ** The ASCE figure is not held here because ASCE 7-16 is a copyrighted standard
# with no freely accessible authoritative rendering. The IRC is adopted law: this grid was
# machine-extracted (never re-keyed by hand) from the publicly published jurisdictional
# renderings and diffed cell-for-cell across six of them — IRC 2018 as adopted by Texas,
# New Jersey and Los Angeles, plus IRC 2015 (NJ) and IRC 2021 (NJ, TX, UT). All six are
# identical, which is also a check on the extraction: a transcription error would have to
# have occurred identically six times.
#
# The table is the REQUIRED resistance, not an allowable — it is a demand a reader looks up
# rather than a capacity. That is why it lives beside the force coefficients and not in
# ``library/hardware.py``: what the connector can take is the hardware catalog's business,
# and the comparison between them belongs to whoever holds both.

#: Values in POUNDS PER CONNECTION, ASD. Keyed ``(exposure, spacing_in, span_ft)`` to a pair
#: of tuples ``(below_5_12, five_12_and_steeper)``, each indexed by ``_R802_11_SPEEDS``.
_R802_11_SPEEDS = (110.0, 115.0, 120.0, 130.0, 140.0)
_R802_11_SPANS = (12.0, 18.0, 24.0, 28.0, 32.0, 36.0, 42.0, 48.0)

_R802_11: dict = {
    ("B", 12.0): (((48, 59, 70, 95, 122), (43, 53, 64, 88, 113)),
                  ((59, 74, 89, 122, 157), (52, 66, 81, 112, 146)),
                  ((71, 89, 108, 149, 192), (62, 79, 98, 137, 178)),
                  ((79, 99, 121, 167, 216), (69, 88, 109, 153, 200)),
                  ((86, 109, 134, 185, 240), (75, 97, 120, 170, 222)),
                  ((94, 120, 146, 203, 264), (82, 106, 132, 186, 244)),
                  ((106, 135, 166, 230, 300), (92, 120, 149, 211, 278)),
                  ((118, 151, 185, 258, 336), (102, 134, 166, 236, 311))),
    ("B", 16.0): (((64, 78, 93, 126, 162), (57, 70, 85, 117, 150)),
                  ((78, 98, 118, 162, 209), (69, 88, 108, 149, 194)),
                  ((94, 118, 144, 198, 255), (82, 105, 130, 182, 237)),
                  ((105, 132, 161, 222, 287), (92, 117, 145, 203, 266)),
                  ((114, 145, 178, 246, 319), (100, 129, 160, 226, 295)),
                  ((125, 160, 194, 270, 351), (109, 141, 176, 247, 325)),
                  ((141, 180, 221, 306, 399), (122, 160, 198, 281, 370)),
                  ((157, 201, 246, 343, 447), (136, 178, 221, 314, 414))),
    ("B", 24.0): (((96, 118, 140, 190, 244), (86, 106, 128, 176, 226)),
                  ((118, 148, 178, 244, 314), (104, 132, 162, 224, 292)),
                  ((142, 178, 216, 298, 384), (124, 158, 196, 274, 356)),
                  ((158, 198, 242, 334, 432), (138, 176, 218, 306, 400)),
                  ((172, 218, 268, 370, 480), (150, 194, 240, 340, 444)),
                  ((188, 240, 292, 406, 528), (164, 212, 264, 372, 488)),
                  ((212, 270, 332, 460, 600), (184, 240, 298, 422, 556)),
                  ((236, 302, 370, 516, 672), (204, 268, 332, 472, 622))),
    ("C", 12.0): (((95, 110, 126, 161, 198), (88, 102, 118, 151, 186)),
                  ((121, 141, 163, 208, 257), (111, 131, 151, 195, 242)),
                  ((148, 173, 200, 256, 317), (136, 160, 185, 239, 298)),
                  ((166, 195, 225, 289, 358), (152, 179, 208, 269, 335)),
                  ((184, 216, 249, 321, 398), (168, 199, 231, 299, 373)),
                  ((202, 237, 274, 353, 438), (185, 219, 254, 329, 411)),
                  ((229, 269, 312, 402, 499), (210, 248, 289, 375, 468)),
                  ((256, 302, 349, 450, 560), (234, 278, 323, 420, 524))),
    ("C", 16.0): (((126, 146, 168, 214, 263), (117, 136, 157, 201, 247)),
                  ((161, 188, 217, 277, 342), (148, 174, 201, 259, 322)),
                  ((197, 230, 266, 340, 422), (181, 213, 246, 318, 396)),
                  ((221, 259, 299, 384, 476), (202, 238, 277, 358, 446)),
                  ((245, 287, 331, 427, 529), (223, 265, 307, 398, 496)),
                  ((269, 315, 364, 469, 583), (246, 291, 338, 438, 547)),
                  ((305, 358, 415, 535, 664), (279, 330, 384, 499, 622)),
                  ((340, 402, 464, 599, 745), (311, 370, 430, 559, 697))),
    ("C", 24.0): (((190, 220, 252, 322, 396), (176, 204, 236, 302, 372)),
                  ((242, 282, 326, 416, 514), (222, 262, 302, 390, 484)),
                  ((296, 346, 400, 512, 634), (272, 320, 370, 478, 596)),
                  ((332, 390, 450, 578, 716), (304, 358, 416, 538, 670)),
                  ((368, 432, 498, 642, 796), (336, 398, 462, 598, 746)),
                  ((404, 474, 548, 706, 876), (370, 438, 508, 658, 822)),
                  ((458, 538, 624, 804, 998), (420, 496, 578, 750, 936)),
                  ((512, 604, 698, 900, 1120), (468, 556, 646, 840, 1048))),
}

R802_11_CITATION = (
    "IRC Table R802.11, \"Required Strength of Truss/Rafter Connections to Resist Wind "
    "Uplift Forces\" (pounds per connection, ASD) — identical in the 2015, 2018 and 2021 "
    "editions as adopted by TX, NJ, LA and UT")

#: The footnotes a reader must apply themselves, quoted because none of them is derivable
#: from the model and every one of them moves the number.
R802_11_CONDITIONS = (
    "the tabulated force is already NET of a 15 psf roof/ceiling dead-load allowance "
    "(footnote b) — an allowance the table provides for, not a weight the assembly must "
    "reach; the value is the full CORNER-ZONE figure, and footnote d's 0.75 applies only "
    "more than 8 ft from a building corner while footnote e's 0.70 hip reduction may not "
    "be combined with it; the table is capped at a mean roof height and at a 24 in "
    "overhang, neither of which this lookup checks")


def uplift_connection_force_lb(exposure: str, spacing_in: float, span_ft: float,
                               wind_speed_mph: float, pitch_rise_per_12: float,
                               ) -> float | None:
    """IRC Table R802.11's required uplift resistance per connection, or ``None``.

    ``None`` means the lookup fell outside the table — an exposure, spacing, span or speed
    the IRC does not publish a row for. The caller reports UNKNOWN naming it rather than
    reaching for the nearest cell, on the same discipline :func:`force_coefficient` keeps.

    **No interpolation, deliberately, even though footnote f permits it** between spans and
    between speeds. A value this engine interpolated would be indistinguishable in a finding
    from one a reviewer can look up, and the whole point of a prescriptive read is that the
    reviewer can open the document and land on the same number. A span or speed off the grid
    is a question for a person.
    """
    row = _R802_11.get((exposure.strip().upper(), float(spacing_in)))
    if row is None:
        return None
    span_index = _next_row_at_or_above(_R802_11_SPANS, span_ft)
    speed_index = _next_row_at_or_above(_R802_11_SPEEDS, wind_speed_mph)
    if span_index is None or speed_index is None:
        return None
    shallow, steep = row[span_index]
    pitched = steep if pitch_rise_per_12 >= 5.0 else shallow
    return float(pitched[speed_index])


def _next_row_at_or_above(published: tuple, value: float) -> int | None:
    """The index of the first published value at or above ``value``; ``None`` past the end.

    ** ROUNDING UP IS NOT INTERPOLATION, AND THE DISTINCTION IS THE WHOLE RULE. ** A 35.6 ft
    roof read on the 36 ft row takes the heavier of the two cells that bracket it — the same
    number a reviewer lands on opening the table, and the conservative one. Interpolating to
    35.6 would produce a value that is in no edition of the IRC, cannot be checked against
    the page, and is LOWER than the row above it. Footnote f permits the interpolation; this
    engine declines it for the same reason it prints a critical C_f instead of inventing one.

    Past the largest published row there is nothing to round up TO, and the answer is
    ``None`` — the table stops, and so does the read.
    """
    for index, published_value in enumerate(published):
        if value <= published_value + 1e-9:
            return index
    return None

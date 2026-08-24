"""Prescriptive exterior-deck tables — IRC R507 / AWC DCA6 (→ 12 §checks/structural).

One table module, mirroring :mod:`typehaus.resolve.framing.tables`: the sizing rules live
here and :mod:`typehaus.checks.structural.deck` reads them, so the numbers can be reviewed
against the published tables in one place instead of being scattered through check bodies.

**What these numbers are.** Exterior decks are governed by IRC Chapter 5 Section R507 and by
AWC's *DCA6 — Prescriptive Residential Wood Deck Construction Guide*, which is the document
most jurisdictions (Minnesota included) point a deck permit at. Both are prescriptive: they
are lookup tables for the 40 psf live + 10 psf dead residential deck load case, No. 2 grade
or better, wet-service (exterior) conditions, with no cantilever beyond the tabulated span.

**What they are not.** They are not an engineered design, and the values transcribed here
are deliberately the *most restrictive* species group in each table rather than the row for
any one species. A PASS is therefore valid whichever of the common deck species is actually
supplied; a FAIL means "look up the species-specific row before you conclude anything", not
"this member is undersized". Every finding built on this module carries the engine's
``[advisory, not engineering]`` prefix for the same reason. Confirm against the edition the
AHJ has actually adopted before a permit set relies on it.
"""

from __future__ import annotations

# --- AWC DCA6 Table 3A — deck joist spans ---------------------------------------------
# Maximum joist span (feet) for the 40 psf live + 10 psf dead deck load case, joists with
# no cantilever, by nominal size and o.c. spacing. Values are the redwood / western-cedar /
# ponderosa-pine group — the lowest row of the table — so any of Southern Pine, Douglas
# Fir-Larch, Hem-Fir or SPF spans at least this far.
DECK_JOIST_SPAN_FT: dict[str, dict[float, float]] = {
    #          12" o.c.  16" o.c.  24" o.c.
    "2x6": {12.0: 8.83, 16.0: 8.00, 24.0: 7.00},
    "2x8": {12.0: 11.67, 16.0: 10.58, 24.0: 8.67},
    "2x10": {12.0: 14.92, 16.0: 13.00, 24.0: 10.58},
    "2x12": {12.0: 17.42, 16.0: 15.08, 24.0: 12.33},
}

# Spacings the table is published at. A deck framed at some other o.c. is looked up at the
# next *wider* tabulated spacing (the conservative direction), and anything wider than the
# widest published row has no answer at all.
DECK_JOIST_SPACINGS_IN: tuple[float, ...] = (12.0, 16.0, 24.0)


def deck_joist_span_limit(member: str, spacing_in: float) -> tuple[float, float] | None:
    """Allowable deck joist span (ft) for ``member`` at ``spacing_in``, with the tabulated
    spacing actually used. ``None`` when the size or the spacing is off the table."""
    row = DECK_JOIST_SPAN_FT.get(member)
    if row is None:
        return None
    wider = [s for s in DECK_JOIST_SPACINGS_IN if s >= spacing_in - 1e-9]
    if not wider:
        return None
    tabulated = min(wider)
    return row[tabulated], tabulated


# --- IRC R507.6.1 — deck joist cantilevers -------------------------------------------
# The overhang a deck joist is allowed past its outermost bearing, as a fraction of the
# adjacent (back) span. This is the rule that lets the span tables above be read as span
# tables: the cantilever is bounded here instead of being counted as span there.
MAX_JOIST_CANTILEVER_RATIO = 0.25


# --- IRC Table R507.5(1) — deck beam spans --------------------------------------------
# Maximum beam span (feet) by built-up beam size and the *joist span the beam carries*
# (i.e. the total span of the joists bearing on it, not its tributary half). Same 40+10 psf
# case and same most-restrictive-species convention as the joist table above.
DECK_BEAM_SPAN_FT: dict[str, dict[float, float]] = {
    #             carried joist span, feet:
    #              6'    8'    10'   12'   14'   16'   18'
    "2-2x6": {6.0: 5.42, 8.0: 4.75, 10.0: 4.25, 12.0: 3.83, 14.0: 3.58, 16.0: 3.33, 18.0: 3.17},
    "2-2x8": {6.0: 6.83, 8.0: 6.00, 10.0: 5.33, 12.0: 4.92, 14.0: 4.58, 16.0: 4.25, 18.0: 4.00},
    "2-2x10": {6.0: 8.17, 8.0: 7.08, 10.0: 6.33, 12.0: 5.75, 14.0: 5.33, 16.0: 5.00, 18.0: 4.75},
    "2-2x12": {6.0: 9.50, 8.0: 8.25, 10.0: 7.33, 12.0: 6.67, 14.0: 6.25, 16.0: 5.83, 18.0: 5.50},
    "3-2x8": {6.0: 8.50, 8.0: 7.42, 10.0: 6.58, 12.0: 6.00, 14.0: 5.58, 16.0: 5.25, 18.0: 5.00},
    "3-2x10": {6.0: 10.17, 8.0: 8.83, 10.0: 7.92, 12.0: 7.17, 14.0: 6.67, 16.0: 6.25, 18.0: 5.92},
    "3-2x12": {6.0: 11.83, 8.0: 10.25, 10.0: 9.17, 12.0: 8.33, 14.0: 7.75, 16.0: 7.25, 18.0: 6.83},
}

DECK_BEAM_JOIST_SPANS_FT: tuple[float, ...] = (6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0)


def deck_beam_span_limit(size: str, joist_span_ft: float) -> tuple[float, float] | None:
    """Allowable beam span (ft) for ``size`` carrying joists of ``joist_span_ft``, with the
    tabulated joist span used. A joist span between rows reads the next *longer* row (the
    conservative direction). ``None`` when the beam size or the joist span is off the table."""
    row = DECK_BEAM_SPAN_FT.get(size)
    if row is None:
        return None
    longer = [s for s in DECK_BEAM_JOIST_SPANS_FT if s >= joist_span_ft - 1e-9]
    if not longer:
        return None
    tabulated = min(longer)
    return row[tabulated], tabulated


# --- IRC R507.4 / Table R507.4 — deck posts -------------------------------------------
# R507.4 sets a minimum nominal post size for a deck; the table then caps unbraced post
# height by the tributary deck area the post carries. Below 4x4/4x6 there is no row: those
# sizes are limited outright.
MIN_DECK_POST_NOMINAL = "6x6"

# {nominal post size: ((max tributary area ft2, max height ft), ...)}, ascending by area.
DECK_POST_HEIGHT_FT: dict[str, tuple[tuple[float, float], ...]] = {
    "4x4": ((48.0, 6.75),),
    "4x6": ((48.0, 8.0),),
    "6x6": ((36.0, 14.0), (48.0, 12.0), (64.0, 10.0)),
    "6x8": ((36.0, 14.0), (48.0, 14.0), (64.0, 12.0)),
    "8x8": ((36.0, 14.0), (48.0, 14.0), (64.0, 14.0)),
}


def deck_post_height_limit(size: str, tributary_ft2: float) -> float | None:
    """Maximum unbraced deck post height (ft) for ``size`` at ``tributary_ft2``, or ``None``
    when the size is not tabulated or the tributary area is past the table's last row."""
    rows = DECK_POST_HEIGHT_FT.get(size)
    if rows is None:
        return None
    for area, height in rows:
        if tributary_ft2 <= area + 1e-9:
            return height
    return None


# --- IRC R507.3 — deck footings --------------------------------------------------------
# The deck design load the footing area is sized against: R507.1 is 40 psf live over a
# 10 psf dead allowance. Required bearing area = tributary area x this / soil bearing value.
DECK_LIVE_LOAD_PSF = 40.0
DECK_DEAD_LOAD_PSF = 10.0
DECK_TOTAL_LOAD_PSF = DECK_LIVE_LOAD_PSF + DECK_DEAD_LOAD_PSF

# R403.1 / R507.3: a footing is never smaller than this however light the load, and never
# thinner than 6". The area rule alone would happily size a 6" pad under a light deck.
MIN_DECK_FOOTING_SIDE_IN = 12.0
MIN_DECK_FOOTING_THICKNESS_IN = 6.0


def required_footing_area_ft2(tributary_ft2: float, soil_bearing_psf: float) -> float:
    """Bearing area a deck footing needs for its tributary load (IRC R507.3.1)."""
    return tributary_ft2 * DECK_TOTAL_LOAD_PSF / soil_bearing_psf


# --- IRC R312.1 — guards ---------------------------------------------------------------
# A guard is required where a walking surface is more than this above the surface below,
# and must stand at least GUARD_MIN_HEIGHT_IN above the walking surface.
GUARD_REQUIRED_ABOVE_IN = 30.0
GUARD_MIN_HEIGHT_IN = 36.0

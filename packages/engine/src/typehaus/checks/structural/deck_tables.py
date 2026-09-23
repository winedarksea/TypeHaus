"""Prescriptive exterior-deck tables — IRC R507 / AWC DCA6 (→ 12 §checks/structural).

One table module, mirroring :mod:`typehaus.resolve.framing.tables`: the sizing rules live
here and :mod:`typehaus.checks.structural.deck` reads them, so the numbers can be reviewed
against the published tables in one place instead of being scattered through check bodies.

**What these numbers are.** Exterior decks are governed by IRC Chapter 5 Section R507 and by
AWC's *DCA6 — Prescriptive Residential Wood Deck Construction Guide*, which is the document
most jurisdictions (Minnesota included) point a deck permit at. Both are prescriptive: they
are lookup tables for the 40 psf live + 10 psf dead residential deck load case, No. 2 grade
or better, wet-service (exterior) conditions, with no cantilever beyond the tabulated span.

**What they are not.** They are not an engineered design. The joist table carries its species
rows and reads one only where the deck authors ``JoistSpec.species``; otherwise it reads the
*most restrictive* row, as the beam table always does. A PASS on the restrictive row is valid
whichever common species is supplied; a FAIL there means "author the species", not "this
member is undersized". Every finding built on this module carries the engine's
``[advisory, not engineering]`` prefix for the same reason. Confirm against the edition the
AHJ has actually adopted before a permit set relies on it.
"""

from __future__ import annotations

# --- IRC 2018 Table R507.6 / AWC DCA6 Table 2 — deck joist spans ------------------
# Maximum joist span (feet) for the 40 psf live + 10 psf dead deck load case, No. 2 wet
# service, joists with no cantilever, by species group, nominal size and o.c. spacing.
# Checked against the published R507.6 2026-09-22.
_SP = "southern_pine"
_DF = "df_hf_spf"
_RW = "redwood_cedar"
DECK_JOIST_SPECIES: tuple[str, ...] = (_SP, _DF, _RW)
DECK_JOIST_SPAN_FT: dict[str, dict[str, dict[float, float]]] = {
    #                12" o.c.  16" o.c.  24" o.c.
    _SP: {"2x6": {12.0: 9.92, 16.0: 9.00, 24.0: 7.58},
          "2x8": {12.0: 13.08, 16.0: 11.83, 24.0: 9.67},
          "2x10": {12.0: 16.17, 16.0: 14.00, 24.0: 11.42},
          "2x12": {12.0: 18.00, 16.0: 16.50, 24.0: 13.50}},
    _DF: {"2x6": {12.0: 9.50, 16.0: 8.67, 24.0: 7.17},
          "2x8": {12.0: 12.50, 16.0: 11.08, 24.0: 9.08},
          "2x10": {12.0: 15.67, 16.0: 13.58, 24.0: 11.08},
          "2x12": {12.0: 18.00, 16.0: 15.75, 24.0: 12.83}},
    # redwood / western cedars / ponderosa / red pine — the lowest row of the table
    _RW: {"2x6": {12.0: 8.83, 16.0: 8.00, 24.0: 7.00},
          "2x8": {12.0: 11.67, 16.0: 10.58, 24.0: 8.67},
          "2x10": {12.0: 14.92, 16.0: 13.00, 24.0: 10.58},
          "2x12": {12.0: 17.42, 16.0: 15.08, 24.0: 12.33}},
}
SPECIES_LABEL: dict[str, str] = {
    _SP: "Southern pine", _DF: "DF-L/HF/SPF", _RW: "redwood/cedar (most restrictive)",
}

# Spacings the table is published at. A deck framed at some other o.c. is looked up at the
# next *wider* tabulated spacing (the conservative direction), and anything wider than the
# widest published row has no answer at all.
DECK_JOIST_SPACINGS_IN: tuple[float, ...] = (12.0, 16.0, 24.0)
# R507.6 is 40 psf live, and snow is not concurrent with it: a design snow at or under
# this is covered by the table, one over it is not.
DECK_TABLE_LIVE_PSF = 40.0


def _nominal(member: str) -> str:
    """The table key: a treatment suffix (``"2x12:kdat"``) says nothing about span."""
    return member.strip().split(":", 1)[0].strip()


def deck_joist_span_limit(member: str, spacing_in: float,
                          species: str | None = None) -> tuple[float, float] | None:
    """Allowable deck joist span (ft) for ``member`` at ``spacing_in``, with the tabulated
    spacing actually used. ``species=None`` reads the most restrictive row. ``None`` when
    the size, species or spacing is off the table."""
    rows = DECK_JOIST_SPAN_FT.get(species or _RW)
    row = rows.get(_nominal(member)) if rows is not None else None
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
# IRC R507.5.1, the beam sibling of R507.6.1 above and the same quarter. Separate
# constant because they are separate code sections that could diverge, not because
# they differ today.
MAX_BEAM_CANTILEVER_RATIO = 0.25


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
    row = DECK_BEAM_SPAN_FT.get(_nominal(size))
    if row is None:
        return None
    longer = [s for s in DECK_BEAM_JOIST_SPANS_FT if s >= joist_span_ft - 1e-9]
    if not longer:
        return None
    tabulated = min(longer)
    return row[tabulated], tabulated


# --- IRC R507.4 / Table R507.4 — deck posts -------------------------------------------
# 2018 IRC Table R507.4 (the edition MN adopts): one maximum height per post size, measured
# to the underside of the beam, 40 psf live, for beams sized per Table R507.5. It has no
# tributary-area rows — those arrived in 2021 (by species and snow load). The area-stepped
# rows this replaced (6x6 at 10' past 48 ft2) matched neither edition. Footnote: a 4x4 may go
# to 8' under a one- or two-ply beam; 6'-9" is the three-ply-on-cap value, kept as the floor.
MIN_DECK_POST_NOMINAL = "6x6"

# {nominal post size: ((max tributary area ft2, max height ft), ...)}, ascending by area.
# The row shape is kept for a later edition that does step by area; 2018 is one flat row.
_ANY_AREA = float("inf")
DECK_POST_HEIGHT_FT: dict[str, tuple[tuple[float, float], ...]] = {
    "4x4": ((_ANY_AREA, 6.75),),
    "4x6": ((_ANY_AREA, 8.0),),
    "6x6": ((_ANY_AREA, 14.0),),
    "8x8": ((_ANY_AREA, 14.0),),
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
#
# Re-exported from ``typehaus/loads.py``, which is where the numbers live since 2026-09-18 —
# they had three copies before, here and in ``engineering/pier_basis`` and
# ``engineering/glulam_beam``, each carrying a comment about the other two.
from typehaus.loads import (  # noqa: E402,F401  (a re-export, kept at its old name)
    DECK_DEAD_LOAD_PSF,
    DECK_LIVE_LOAD_PSF,
    DECK_TOTAL_LOAD_PSF,
)

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

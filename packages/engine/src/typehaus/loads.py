"""The code's published design loads, as data — read by ``checks`` and ``engineering`` alike.

A top-level leaf for the same reason ``typehaus/wind.py`` is one: both packages need these
numbers and neither may import the other. ``engineering`` may not import ``checks`` at all,
and ``checks`` importing a calc module for a constant would couple a prescriptive table to
a ``BASIS_VERSION``.

** THIS EXISTS BECAUSE THE DECK LOAD HAD THREE COPIES. ** ``checks/structural/deck_tables``,
``engineering/pier_basis`` and ``engineering/glulam_beam`` each declared its own 40 and 10,
each with a comment saying the others existed and to keep them in step by hand. Three copies
of one number with three "if one moves, move the other" notes is not a single source; it is
three chances to move one. They are re-exported at their old names, so every existing import
still reads, and each module's comment now points here instead of at its siblings.
"""

from __future__ import annotations

#: IRC Table R301.5 via R507.1 — the uniform live load a deck is designed for.
DECK_LIVE_LOAD_PSF = 40.0
#: IRC R507.1 — the dead-load allowance that goes with it: decking, framing, its own weight.
DECK_DEAD_LOAD_PSF = 10.0
#: The one currency IRC Table R507.3.1 sizes a bearing area in.
DECK_TOTAL_LOAD_PSF = DECK_LIVE_LOAD_PSF + DECK_DEAD_LOAD_PSF


# --- the roof and floor design loads a published header/span table is indexed at ---------
#
# ** THESE ARE ONLY VALID AT Pg = 50 psf, AND EVERY READER MUST CHECK THAT FIRST. ** ASCE
# 7-16 §7.3 flat-roof snow at this house's exposure, thermal and importance factors is
# ``Ps = 0.7 Ce Ct Is Pg = 0.7 x 50 = 35``. The engine derives no part of Ce/Ct/Is, so the
# figure is stated rather than computed and a site at any other ground snow must not reach
# it — ``checks/structural/snow.py`` refuses to run its table at any other Pg, and
# ``structural.header_prescriptive`` passes no demand at all rather than a wrong one.

#: ASCE 7-16 §7.3 flat-roof snow, at Pg = 50 psf only. See the block comment above.
ROOF_SNOW_PSF = 35.0
#: Roof dead load — the figure every published residential roof table is indexed at.
ROOF_DEAD_PSF = 15.0
#: The load basis a roof-carrying published row is compared against.
ROOF_TOTAL_LOAD_PSF = ROOF_SNOW_PSF + ROOF_DEAD_PSF

#: IRC Table R301.5 — the uniform live load on a residential floor, and the dead allowance
#: that goes with it. Distinct from the DECK pair above only in dead load history; kept
#: separate because a floor and a deck are different occupancies and a future amendment to
#: one must not silently move the other.
FLOOR_LIVE_LOAD_PSF = 40.0
FLOOR_DEAD_LOAD_PSF = 10.0
FLOOR_TOTAL_LOAD_PSF = FLOOR_LIVE_LOAD_PSF + FLOOR_DEAD_LOAD_PSF

#: What a header past IRC R602.7's table is compared against when the check cannot tell
#: whether it carries roof or floor: the LARGER of the two, which is the safe direction.
WIDE_HEADER_LOAD_PSF = max(ROOF_TOTAL_LOAD_PSF, FLOOR_TOTAL_LOAD_PSF)

#: The only ground snow the two roof figures above are derived at.
DERIVED_AT_GROUND_SNOW_PSF = 50.0

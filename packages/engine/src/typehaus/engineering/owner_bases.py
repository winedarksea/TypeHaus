"""The owner's stated bases and acceptances, as :class:`StatedBasis` data — one home.

Each is printed in section 6 of every family sheet whose records carry it, and on the
summary. The wording is read from the module that already states it (``balcony_loads``),
so the sheet and the note cannot drift apart. A kind attaches the ones it rests on with
``declare_sheet(bases=...)`` or, member by member, ``EngineeringRecord.bases``.
"""

from __future__ import annotations

from typehaus.engineering.balcony_loads import (
    CURTAIN_OWNER_BASIS,
    DECK_BASIS_STATED,
    NOT_COVERED_OWNER,
)
from typehaus.engineering.item import BasisKind, StatedBasis

DECK_SNOW = StatedBasis(
    BasisKind.OWNER_BASIS, "balcony and porch deck loads", DECK_BASIS_STATED,
    reopens_if=NOT_COVERED_OWNER.split(" ALSO NOT COVERED")[0],
    reference="owner decision 5; balanced snow compared on 01-design-criteria.md")

CURTAINS = StatedBasis(
    BasisKind.OWNER_BASIS, "porch curtains in design wind", CURTAIN_OWNER_BASIS,
    reopens_if="a curtain left closed in design wind is outside this design",
    reference="owner basis; curtain maker's stow specification")

OVERHANGS = StatedBasis(
    BasisKind.OWNER_ACCEPTED, "glulam and joist overhangs",
    "The glulam overhangs and the joists' run past the beams are accepted as drawn and "
    "graded here by statics (dead everywhere, live patterned).",
    reopens_if="an overhang growing past the quarter span of IRC R507.5.1",
    reference="owner decision 9")


def connector_reading(tie: str, source: str) -> StatedBasis | None:
    """A head connector graded on an owner's reading of its published table, if it is one."""
    if "owner reading" not in source.lower():
        return None
    return StatedBasis(
        BasisKind.OWNER_READING, f"{tie}: the published row it is graded on", source,
        reopens_if="the maker's current catalog edition printing a different row",
        reference="owner decision 8")


# --- The sunken-garden court (retaining_system, retaining_wall, thermal_break_transfer) ---
# Wording is read from the drawing notes AN-SG-SOIL and AN-SG-BACKFILL, the court free body
# note (sunken_garden_court_free_body.md §15g, §15k) and the rows' own docstrings.

def specified_court_soil(bed_friction: float, bed_friction_max: float | None,
                         native_phi_deg: float) -> StatedBasis:
    """The court's soil: specified, a site report confirms (AN-SG-SOIL)."""
    top = ("" if bed_friction_max is None else
           f", and up to {bed_friction_max:g} for the rows that friction hurts (the winter "
           f"contraction of the court on its base)")
    return StatedBasis(
        BasisKind.SPECIFIED, "the court's soil parameters",
        f"The court is designed on SPECIFIED soil parameters: design friction for concrete "
        f"on the compacted washed #57 bed {bed_friction:g}{top}, and drained phi' of the "
        f"native at the bed bottom {native_phi_deg:g} deg. The design is closed on these and "
        f"NOT YET CONFIRMED by a site report; where no report or specified value exists the "
        f"rows grade on the IBC Table 1806.2 presumptions.",
        reopens_if=f"the report returns a bed friction under {bed_friction:g} or a native "
                   f"phi' under {native_phi_deg:g} deg (the deep plane returns to the owner); "
                   + (f"a bed friction above {bed_friction_max:g} re-checks the winter-tension "
                      f"rows; " if bed_friction_max is not None else "")
                   + "a clay or silt bed bottom builds the lean-wall fallback",
        reference="drawing note AN-SG-SOIL: site report required before the first placement")


def snow_not_with_perched_water(fs: float, pcf: float) -> StatedBasis:
    """Owner decision: ground snow and perched water on the terrace are not concurrent."""
    return StatedBasis(
        BasisKind.OWNER_BASIS, "ground snow and perched water on the court's terrace",
        f"Full ground snow on the terrace and perched water at H/2 (a blinded drain) are "
        f"taken as NOT concurrent; each is graded alone. Combined they would read FS "
        f"{fs:.2f} at {pcf:.0f} pcf, printed for transparency.",
        reopens_if="the combination itself, lateral frost thrust in the top 42\" of retained "
                   "fill, and seasonal thermal ratcheting under the sustained thrust are not "
                   "covered",
        reference="owner basis; court free body note §15k")


BOARDS_AFTER_BACKFILL = StatedBasis(
    BasisKind.OWNER_BASIS, "isolation boards set after the backfill",
    "The isolation boards and the veneer ties go in after the three retained sides are "
    "backfilled, each board cut to its as-built slot. The backfill's own sliding is spent "
    "before the joint exists, so the joint row counts thermal closure plus only the "
    "increment from the backfilled court to the worst graded service case.",
    reopens_if="boards set before the backfill is complete: the whole mobilisation then "
               "counts, and the slot's construction tolerance is open",
    reference="owner decision on the court joint; court free body note §15g; drawing notes "
              "AN-SG-PLACEMENTS and AN-SG-BLOCKOUTS")

BACKFILL_CONDITIONS = StatedBasis(
    BasisKind.OWNER_BASIS, "backfill sequence the court and the soil's strut rely on",
    "(a) W-SG-W2, W-SG-S and W-SG-E2 are backfilled together in lifts: no one of the three "
    "stands more than half its height (5 ft 0 in) above any other at any time. (b) W-SG-W1 "
    "and W-SG-E1 are not backfilled until the porch beams brace their tops (IRC R404.1.7); "
    "the porch joists are the soil's strut between them, so every joist end bears tight on "
    "its ledger face (any gap shimmed in the hanger seat), and W1 and E1 are then backfilled "
    "together, neither more than 2 ft 0 in above the other. (c) No backfill before the first "
    "placement has cured and the strut is in.",
    reopens_if="a one-sided or out-of-sequence backfill would load the far stem through the "
               "strut and is outside this design",
    reference="drawing note AN-SG-BACKFILL; court free body note §13")

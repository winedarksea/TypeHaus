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


# -- LA-fill-north: lateral_system and wood_roof_post ----------------------------------------

DESIGN_SNOW_DRIFT = StatedBasis(
    BasisKind.OWNER_BASIS, "design snow on the canopy posts, drift included",
    "The posts take the house's authored design snow of 73.7 psf over their tributary: the "
    "ASCE 7 §7.7 roof-step drift from the north gable, balanced 42 psf plus the drift's "
    "average surcharge across the canopy's own 6'-0\" (31.7 psf). The calculation derives no "
    "part of drift, so it is authored. It is spread evenly over each post's tributary; the "
    "drift's south-to-north gradient is not placed on the posts.",
    reopens_if="the gradient placed on the south header posts (engineering review C-5, about "
               "+6% on those posts), or a different authored design snow",
    reference="preferences.toml [structural] roof_beam_snow_psf; north_entry_piers.md §3")

SDPWS_4_2A_READ = StatedBasis(
    BasisKind.OWNER_READING, "canopy and garage deck allowables read from SDPWS-2015",
    "Canopy (blocked): Table 4.2A, column B (wind), Structural I, 8d common, 2\" nominal "
    "framing, 3/8\" minimum nominal panel thickness (the 19/32\" deck exceeds it), 6\" at "
    "boundaries and continuous edges, 6\" at other edges, Case 1: v_w = 755 plf nominal; "
    "footnote 2 (SPF, G 0.42) [1 - (0.5 - 0.42)] = 0.92; §4.2.3 divides by 2.0: "
    "755 x 0.92 / 2.0 = 347.3 plf. Garage (unblocked): Table 4.2C, the same grade, nail and "
    "thickness, 6\" nails, Case 1: v_w = 670 plf; 670 x 0.92 / 2.0 = 308.2 plf. The decks "
    "are thicker than the credited minimum, and no increased capacity is claimed.",
    reopens_if="AWC's printed table reading differently; a secondary IBC transcription gave "
               "372 x 0.92 = 342 (744 plf nominal), which differs from the 755 read",
    reference="AWC SDPWS-2015 with Commentary, Chapter 4 (AWC's own PDF); "
              "canopy_garage_diaphragm.md §12a")

LSTA24_DRY = StatedBasis(
    BasisKind.OWNER_BASIS, "LSTA24 joint straps and their nailers graded dry",
    "The LSTA24 straps and their nailers sit on the nailer under the roof sheathing and "
    "roofing, not in the weather: the canopy's one exposure rule reads them DRY (C_M 1.0). "
    "It is stated on the joint-strap, rotation-couple and end-strap rows.",
    reopens_if="wet service (C_M 0.70) would put the end-strap row, 0.798, at 1.14",
    reference="canopy_garage_diaphragm.md §12e")

# --- deck_tie (LA-fill) ---------------------------------------------------------------------

HL43_EAST_WEST = StatedBasis(
    BasisKind.OWNER_ACCEPTED, "HL43HDG read east-west (heel vertical)",
    "Owner (2026-11-23): the HL43 catalog values may be read for the as-installed direction. "
    "Installed heel vertical, the force along the wall lies in the wall leg's plane, the "
    "catalog's F1 case (Simpson C-C-2024 p. 303, HL43 row: uplift 1,275 lb and F1 1,445 lb, "
    "DF/SP, C_D 1.6; one part per sense, footnote 6: lateral not doubled), graded wet "
    "(C_M 0.70). The figure's F1 bears along the grain; here the garage leg's lags bear "
    "across a vertical stud's grain, and that bearing may be materially lower than the row. "
    "Nothing is credited across the wall: that direction is a tension tie's.",
    reopens_if="lag bearing across the grain shown materially lower than the published F1, "
               "or the maker publishing a row for this installation",
    reference="owner decision, 2026-11-23 (north_entry_piers.md §10p)")

CANOPY_SERVICE = StatedBasis(
    BasisKind.OWNER_BASIS, "tie parts graded wet, and a wet reading outside a report",
    "The landing's ties are exposed to weather and graded WET by one exposure rule: NDS 2018 "
    "Table 11.3.3 C_M 0.70 on the dry catalog row. Where a part's evaluation report is scoped "
    "to in-service MC <= 19% (ESR-2330 DTT2 among them), the wet value is a reading outside "
    "the report, and is said so: the catalog sells the DTT2Z for deck-to-house lateral ties "
    "(C-C-2026 p. 326) but publishes no wet row.",
    reopens_if="the maker publishing a wet row, or a part's service condition authored dry "
               "with a basis",
    reference="owner decision 17 (landing tie wet throughout); canopy exposure rule")

# --- column_support (LA-fill) ----------------------------------------------------------------

DOWEL_RATIO = StatedBasis(
    BasisKind.OWNER_ACCEPTED, "dowel tension ratio, accepted as is",
    "Dowel tension is graded on the conservative C_f 1.80 for every wind band, the guard taken "
    "concurrently with full design wind and the one-bar couple on the block that force itself "
    "produces. It was owner-accepted at 0.92 (2026-11-23) when the porch curtains were a wind "
    "band; with the curtains stowed (owner basis) it is well under that.",
    reopens_if="the ratio rising above 0.92",
    reference="owner acceptance, 2026-11-23 (balcony_moment_columns.md)")

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

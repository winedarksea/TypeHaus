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

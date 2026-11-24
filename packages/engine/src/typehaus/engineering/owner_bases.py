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

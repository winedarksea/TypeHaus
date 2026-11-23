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

"""What a raceway carries besides its branch circuits, and the 310.10(C) wet-location types.

``RacewayCable`` is a conductor or cable no ``Circuit`` names: PV source wire, a Class 2 pair,
Cat 6A (Chapter 9 Notes (5), (9): a multiconductor cable is one conductor at its actual
diameter; a single conductor of a Table 5 type is its Table 5 area). Values come from the
product's datasheet, named in ``source``.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length

#: Insulation types 310.10(C) allows in a wet location (``nec-2026-paraphrase-310.md``).
WET_INSULATIONS = frozenset({
    "MTW", "RHW", "RHW-2", "TW", "THW", "THW-2", "THHW", "THWN", "THWN-2", "XHHW", "XHHW-2",
    "XHWN", "XHWN-2", "ZW"})
#: Table 5 family (``model/conductor_areas.py`` key) for each type it covers.
TABLE_5_FAMILY = {"THHN": "thhn", "THWN": "thhn", "THWN-2": "thhn", "XHHW": "xhhw",
                  "XHHW-2": "xhhw", "XHH": "xhhw", "TW": "tw", "THW": "tw", "THHW": "tw",
                  "THW-2": "tw"}


def insulation_types(marking: str | None) -> tuple[str, ...]:
    """``"THHN/THWN-2"`` -> ``("THHN", "THWN-2")``: a dual-rated marking names each type."""
    return tuple(part.strip().upper() for part in (marking or "").split("/") if part.strip())


def wet_rated(marking: str | None) -> bool:
    return any(t in WET_INSULATIONS for t in insulation_types(marking))


def table_5_family(marking: str | None) -> str | None:
    return next((TABLE_5_FAMILY[t] for t in insulation_types(marking) if t in TABLE_5_FAMILY),
                None)


class RacewayCable(HausModel):
    """``count`` identical conductors or cables. Give ``outside_diameter`` (a cable, or a
    conductor Table 5 does not list) or ``size_awg`` with a Table 5 ``insulation``."""

    count: int = 1
    size_awg: str | None = None
    insulation: str | None = None  # conductor type marking, e.g. "THHN/THWN-2", "PV"
    outside_diameter: Length | None = None
    #: NEC cable type letters on the jacket, e.g. "CMR", "CMP", "CL3" (Table 722.100(A)).
    cable_type: str | None = None
    #: Listed and marked for wet locations (722.2(B), 310.10(C)) per the datasheet.
    wet_location: bool = False
    role: str = ""  # what it serves, e.g. "PV string 1", "porch AP"
    source: str | None = None  # the datasheet read

    @model_validator(mode="after")
    def _sized(self) -> RacewayCable:
        if self.count < 1:
            raise ValueError("RacewayCable.count must be at least 1")
        if self.outside_diameter is None and (self.size_awg is None
                                              or table_5_family(self.insulation) is None):
            raise ValueError("RacewayCable needs outside_diameter, or size_awg with a "
                             "Table 5 insulation")
        return self

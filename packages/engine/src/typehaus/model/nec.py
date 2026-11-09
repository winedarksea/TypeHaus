"""Every NFPA 70 section the engine cites, on one basis: the 2026 NEC.

Minnesota adopted NFPA 70-2026 without amendment (Minn. R. 1315.0200 subp. 1a; DLI: permits
filed on or after 2026-08-17). Minn. R. 1309.0010 subp. 3.E deletes IRC ch. 34-43, so no
finding cites an IRC E-section; the ``code.E39xx_*`` check ids are opaque keys and stay.

Under ``model`` so every package that prints a citation may import it, leaves included.
Bare section strings; ``cite`` adds the "NEC " prefix. The next renumbering is this file.

Sources (read 2026-11-07): NFPA 70 second-draft reports (docinfofiles.nfpa.org, A2025 P02,
P03, P10, P17), the NEC Handbook 2026 errata page for Table 120.54, MN DLI "2026 NEC FAQ"
(rev. 2026-10-05), EC&M 2026 change summaries (Holt, Jackson, Austin). None was checked
against the printed 2026 text. ``UNCONFIRMED`` names the rows whose 2026 NUMBER no source
gives (moved or inferred, not merely "no change reported"); ``cite``/``mark`` print them
with a caveat, so the doubt reaches the finding, the permit checklist and the sheet.
120.82(C): (3) heat pump + 65% supplemental is quoted (Holt, EC&M Nov 2025) and (6) is the
40% term for four or more units (CMP-2 Annex D2(a)); (2) and the 65% (5) are inferred.
"""

from __future__ import annotations

from typing import Final


class NEC:
    """Section strings by meaning. ``EDITION`` is what a sheet prints as the basis."""

    EDITION: Final = "2026 NEC"

    # Art. 110 — working space.
    WORKING_SPACE: Final = "110.26(A)"
    WORKING_SPACE_EGRESS: Final = "110.26(C)"
    DEDICATED_SPACE: Final = "110.26(E)(1)"

    # Art. 120 (was Art. 220) — load calculations.
    LOAD_CALC: Final = "Article 120"
    FEEDER_SERVICE_STANDARD: Final = "Article 120 Part III"
    FLOOR_AREA: Final = "120.5(C)"
    NONCOINCIDENT: Final = "120.6"
    PCS_SETPOINT: Final = "120.7"
    GENERAL_LIGHTING_STANDARD: Final = "120.41"
    DRYER_STANDARD: Final = "120.54"
    OPTIONAL_DWELLING: Final = "120.82"
    OPTIONAL_GENERAL_LOADS: Final = "120.82(B)"
    OPTIONAL_FIXED_APPLIANCES: Final = "120.82(B)(3)"
    OPTIONAL_HVAC: Final = "120.82(C)"
    OPTIONAL_HEAT_PUMP: Final = "120.82(C)(2)"
    OPTIONAL_HEAT_PUMP_SUPPLEMENTAL: Final = "120.82(C)(3)"
    OPTIONAL_RESISTANCE_HEAT: Final = "120.82(C)(5)/(6)"
    OPTIONAL_EVSE: Final = "120.82(D)"

    # Art. 130 (was Art. 750) — energy management.
    PCS: Final = "Article 130 Part II"
    PCS_LISTING: Final = "130.2"

    # Art. 210 — branch circuits.
    MULTIWIRE_DISCONNECT: Final = "210.7"
    GFCI: Final = "210.8"
    GFCI_DWELLING: Final = "210.8(A)"
    GFCI_BATHROOM: Final = "210.8(A)(1)"
    GFCI_GARAGE: Final = "210.8(A)(2)"
    GFCI_ACCESSORY_BUILDING: Final = "210.8(A)(3)"
    GFCI_OUTDOORS: Final = "210.8(A)(4)"
    GFCI_BASEMENT: Final = "210.8(A)(6)"
    GFCI_KITCHEN: Final = "210.8(A)(7)"
    GFCI_SINK: Final = "210.8(A)(9)"
    GFCI_LAUNDRY: Final = "210.8(A)(12)"
    GFCI_APPLIANCES: Final = "210.8(D)"
    GFCI_SUMP: Final = "210.8(D)(6)"
    GFCI_RANGE: Final = "210.8(D)(8)"
    GFCI_DRYER: Final = "210.8(D)(11)"
    GFCI_OUTDOOR_OUTLETS: Final = "210.8(F)"
    AFCI_DWELLING: Final = "210.12(B)"
    RECEPTACLE_OUTLETS: Final = "210.52"
    WALL_SPACE_SPACING: Final = "210.52(A)(1)"
    WALL_SPACE: Final = "210.52(A)(2)"
    WALL_SPACE_FIXED_CABINETS: Final = "210.52(A)(2)(1)"
    FLOOR_RECEPTACLE: Final = "210.52(A)(3)"
    BELOW_COUNTER_WALL_SPACE: Final = "210.52(A)(5)"
    COUNTERTOP: Final = "210.52(C)"
    WALL_COUNTERTOP: Final = "210.52(C)(1)"
    ISLAND_PROVISION: Final = "210.52(C)(2)"
    COUNTERTOP_RECEPTACLE_LOCATION: Final = "210.52(C)(3)"
    BELOW_COUNTERTOP: Final = "210.52(C)(4)"
    BATHROOM_RECEPTACLE: Final = "210.52(D)"
    LAUNDRY_RECEPTACLE: Final = "210.52(F)"
    BALCONY_RECEPTACLE: Final = "210.52(E)(3)"
    GARAGE_RECEPTACLE: Final = "210.52(G)(1)"
    STORAGE_EQUIPMENT_LIGHTING: Final = "210.70(A)(3)"

    # Art. 230/240 — service and overcurrent.
    SERVICE_SPD: Final = "230.67"
    SERVICE_DISCONNECT_OUTDOOR: Final = "230.70(A)(1)"
    SMALL_CONDUCTOR_OCPD: Final = "240.4(D)"
    OCPD_HEIGHT: Final = "240.24(A)"
    SLEEVE_BONDING: Final = "250.86 Ex. 2"

    # Ch. 3 — wiring methods, boxes, raceways.
    RACEWAY_BENDS_MIXED: Final = "300.24"
    AMPACITY_TABLE: Final = "Table 310.16"
    BOX_FILL_AND_VOLUME: Final = "314.16"
    BOX_FILL: Final = "314.16(B)"
    BOX_VOLUME_TABLE: Final = "Table 314.16(A)"
    BOX_MARKED_VOLUME: Final = "314.16(A)(1)"
    CONDUCTOR_VOLUME_TABLE: Final = "Table 314.16(B)"
    BOX_SUPPORT: Final = "314.20 / 314.23"
    BOX_COVER: Final = "314.25"
    FLOOR_BOX: Final = "314.27(C)"
    NM_PROTECTION: Final = "334.15(B)"
    NM_BASEMENT: Final = "334.15(C)"
    NM_60C: Final = "334.80"
    IMC_BENDS: Final = "342.26"
    RMC_BENDS: Final = "344.26"
    PVC_BENDS: Final = "352.26"
    PVC_SUPPORT: Final = "Table 352.30"
    EMT_BENDS: Final = "358.26"
    EMT_SUPPORT: Final = "358.30"
    ENT_BENDS: Final = "362.26"
    ENT_SUPPORT: Final = "362.30"
    PVC: Final = "Article 352"
    EMT: Final = "Article 358"
    ENT: Final = "Article 362"

    # Ch. 4 — equipment.
    SWITCH_HEIGHT: Final = "404.8(A)"
    PANELBOARDS: Final = "Article 408"
    WET_LUMINAIRE_ZONE: Final = "410.10(D)"
    SPACE_HEAT_CONTINUOUS: Final = "424.5"

    # Ch. 6-7 — sources; limited energy.
    RAPID_SHUTDOWN: Final = "690.12"
    RAPID_SHUTDOWN_ARRAY: Final = "690.12(B)(2)"
    INTERCONNECTION: Final = "705.12"
    INTERCONNECTION_120PCT: Final = "705.12(B)(3)(2)"
    # Was 800.133 / 725.136; Arts. 805 and 725.136 are gone, limited energy is Arts. 720-723.
    LIMITED_ENERGY_SEPARATION: Final = "722.15(A)"

    # Ch. 9.
    CONDUIT_DIMENSIONS: Final = "Chapter 9 Table 4"
    SLEEVE_FILL: Final = "Chapter 9 Note 2"


#: Rows no source pins to the 2026 text: each is the best-supported location, not a reading.
#: TODO: confirm every one against NFPA 70-2026 before a permit set relies on it.
UNCONFIRMED: Final = frozenset({
    NEC.NONCOINCIDENT, NEC.OPTIONAL_HEAT_PUMP, NEC.OPTIONAL_RESISTANCE_HEAT,
    NEC.FEEDER_SERVICE_STANDARD, NEC.GFCI_SINK, NEC.AFCI_DWELLING, NEC.FLOOR_BOX,
    NEC.INTERCONNECTION_120PCT, NEC.LIMITED_ENERGY_SEPARATION, NEC.ISLAND_PROVISION,
    NEC.COUNTERTOP_RECEPTACLE_LOCATION, NEC.WALL_COUNTERTOP, NEC.BALCONY_RECEPTACLE,
})


_CAVEAT = " [2026 number unconfirmed]"


def mark(section: str) -> str:
    """The section, with the caveat when its 2026 number is unconfirmed."""
    return section + _CAVEAT if section in UNCONFIRMED else section


def cite(*sections: str) -> str:
    """``cite("314.20", "314.23")`` -> ``"NEC 314.20 / 314.23"``, caveated if unconfirmed."""
    text = "NEC " + " / ".join(sections)
    return text + _CAVEAT if UNCONFIRMED.intersection(sections) else text

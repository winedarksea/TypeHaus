"""Every NFPA 70 section the engine cites, on one basis: the 2026 NEC.

Minnesota adopted NFPA 70-2026 without amendment (Minn. R. 1315.0200 subp. 1a; DLI: permits
filed on or after 2026-08-17). Minn. R. 1309.0010 subp. 3.E deletes IRC ch. 34-43, so no
finding cites an IRC E-section; the ``code.E39xx_*`` check ids are opaque keys and stay.

Under ``model`` so every package that prints a citation may import it, leaves included.
Bare section strings; ``cite`` adds the "NEC " prefix. The next renumbering is this file.

Sources (read 2026-11-07): NFPA 70 second-draft reports (docinfofiles.nfpa.org, A2025 P02,
P03, P10, P17), the NEC Handbook 2026 errata page for Table 120.54, MN DLI "2026 NEC FAQ"
(rev. 2026-10-05), EC&M 2026 change summaries (Holt, Jackson, Austin); re-read 2026-11-09 with
NFPA's first- and second-draft reports and the Aug 2025 Standards Council minutes (210.12(B)'s
bathroom-lighting item was not issued). Re-read 2026-11-13 against post-publication sources
written to the published code: TIA 26-2 (690.12(C), incorporated before printing), TIA 26-8 /
Log 1875 (270.50 vs 250.50, 250.52(A) not renumbered), MN DLI BOE minutes 2025-10-14 Att. B
(250.53(A)(4), 250.64, 690.47), MN DLI NEC FAQ (250.32(B)(1)), WA L&I Elc2604 (250.53(A)(2)),
Frisco TX 2026 NEC amendments (210.52(C)(2) Island and Peninsular Countertops).
``UNCONFIRMED`` names the rows still read only in drafts or trade press, kept by the owner
until someone reads them in the printed code; ``cite``/``mark`` print them with a caveat, so
the doubt reaches the finding, the permit checklist and the sheet.
120.6, 120.82 (with Part III beside it), 210.7-210.12, 210.50-210.63, 250.24-250.112,
314.24-314.27, 705.12 and 722.15 were read in the printed code by the owner 2026-11-13. On
2026-11-14 the owner read 120.4-120.16, 120.40, 120.54-120.57, 120.61, 120.80, 120.82(A);
225.19-225.41; 230.1-230.4; 230.67-230.93; 250.30-250.64 and 250.84-250.94 (so 250.32,
250.50, 250.52(A)(3), 250.53, 250.64 and 250.86 Ex. 2 are now printed reads, no longer the
post-publication ones above); 310.1-310.6, 310.10, 310.12, 310.14 and 310.15 with the
310.16-310.21 conditions, with Tables 310.16 (coded in ``model/ampacity.py``) and 310.17;
110.14-110.16; 240.2-240.4; 250.102-250.104(A)(2) with Table 250.102(C)(1); 334.40, 334.80
and 334.100-334.116;
314.15-314.27 with Tables 314.16(A) and 314.16(B)(4); and 680.34-680.54 (Parts I/II unread). The
engine never quotes the code: ``docs/nec-2026-paraphrase*.md`` restate each rule and say
what grades it; ``tests/test_nec_120_82.py`` and ``test_nec_printed_rules.py`` pin them.
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
    NONCOINCIDENT_UNLIKELY: Final = "120.6(1)"  # feeders/services only
    NONCOINCIDENT_LISTED: Final = "120.6(2)"  # prevented by listed equipment
    PCS_SETPOINT: Final = "120.7"
    PCS_CONTROL_SETTING: Final = "120.7(B)"
    EVSE_LOAD: Final = "120.57"
    GENERAL_LIGHTING_STANDARD: Final = "120.41"
    DRYER_STANDARD: Final = "120.54"
    OPTIONAL_DWELLING: Final = "120.82"
    OPTIONAL_APPLICABILITY: Final = "120.82(A)"
    OPTIONAL_GENERAL_LOADS: Final = "120.82(B)"
    OPTIONAL_SMALL_APPLIANCE: Final = "120.82(B)(2)"
    OPTIONAL_FIXED_APPLIANCES: Final = "120.82(B)(3)"
    OPTIONAL_HVAC: Final = "120.82(C)"
    OPTIONAL_COOLING: Final = "120.82(C)(1)"
    OPTIONAL_HEAT_PUMP: Final = "120.82(C)(2)"
    OPTIONAL_HEAT_PUMP_SUPPLEMENTAL: Final = "120.82(C)(3)"
    OPTIONAL_RESISTANCE_FEW: Final = "120.82(C)(4)"
    OPTIONAL_RESISTANCE_MANY: Final = "120.82(C)(5)"
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
    GFCI_TUB_SHOWER: Final = "210.8(A)(11)"
    GFCI_LAUNDRY: Final = "210.8(A)(12)"
    GFCI_APPLIANCES: Final = "210.8(D)"
    GFCI_SUMP: Final = "210.8(D)(6)"
    GFCI_DISHWASHER: Final = "210.8(D)(7)"
    GFCI_RANGE: Final = "210.8(D)(8)"
    GFCI_WALL_OVEN: Final = "210.8(D)(9)"
    GFCI_COOKTOP: Final = "210.8(D)(10)"
    GFCI_DRYER: Final = "210.8(D)(11)"
    GFCI_MICROWAVE: Final = "210.8(D)(12)"
    GFCI_OUTDOOR_OUTLETS: Final = "210.8(F)"
    BATHROOM_BRANCH: Final = "210.11(C)(3)"
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

    # Art. 215/225/230/240 — feeders, outside supplies, service and overcurrent.
    FEEDER_SPD: Final = "215.18"
    OUTBUILDING_SUPPLIES: Final = "225.30"  # one feeder or branch circuit per building
    OUTBUILDING_DISCONNECT: Final = "225.31"
    EMERGENCY_DISCONNECT: Final = "225.41"
    SERVICE_SPD: Final = "230.67"
    SERVICE_DISCONNECT_OUTDOOR: Final = "230.70(A)(1)"
    SMALL_CONDUCTOR_OCPD: Final = "240.4(D)"
    OCPD_HEIGHT: Final = "240.24(A)"
    SLEEVE_BONDING: Final = "250.86 Ex. 2"

    # Art. 250 — grounding and bonding (decision #123); >1000 V moved to Art. 270.
    SERVICE_GROUNDING: Final = "250.24"
    SEPARATE_BUILDING: Final = "250.32"
    ELECTRODE_SYSTEM: Final = "250.50"
    CONCRETE_ENCASED: Final = "250.52(A)(3)"
    ROD_INSTALLATION: Final = "250.53"
    GEC_INSTALLATION: Final = "250.64"
    GEC_SIZE: Final = "250.66"
    INTERSYSTEM_BONDING: Final = "250.94"
    WATER_PIPE_BOND: Final = "250.104(A)"
    LIGHTNING_BOND: Final = "250.106"

    # Ch. 3 — wiring methods, boxes, raceways.
    RACEWAY_BENDS_MIXED: Final = "300.24"
    AMPACITY_TABLE: Final = "Table 310.16"  # coded in model/ampacity.py
    DWELLING_SERVICE_CONDUCTORS: Final = "310.12(A)"  # 83% of the rating, Table 310.12(A)
    DWELLING_FEEDER_CONDUCTORS: Final = "310.12(B)"  # only a feeder carrying the entire load
    BOX_FILL_AND_VOLUME: Final = "314.16"
    BOX_FILL: Final = "314.16(B)"
    BOX_VOLUME_TABLE: Final = "Table 314.16(A)"
    BOX_MARKED_VOLUME: Final = "314.16(A)(2)"
    CONDUCTOR_VOLUME_TABLE: Final = "Table 314.16(B)(4)"
    BOX_DEPTH: Final = "314.24(B)"
    BOX_FLUSH_SETBACK: Final = "314.20"
    BOX_COVER: Final = "314.25"
    FLOOR_BOX: Final = "314.27(C)"
    NM_PROTECTION: Final = "334.15(B)"
    NM_BASEMENT: Final = "334.15(C)"
    NM_AMPACITY: Final = "334.80(A)"  # 60 °C ceiling; 90 °C only to adjust and correct
    ADJUSTMENT_FACTORS: Final = "310.15(C)(1)"
    TERMINATION_TEMP: Final = "110.14(C)(1)"
    NEXT_SIZE_UP: Final = "240.4(B)"  # next standard OCPD above the ampacity (240.6(A) unread)
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

    # Ch. 6 — Art. 680 Part IV, spas and hot tubs (Parts I/II unread).
    SPA_SCOPE: Final = "680.40"
    SPA_EMERGENCY_SWITCH: Final = "680.41(A)"
    SPA_EQUIPMENT_DISTANCE: Final = "680.41(B)"
    SPA_OUTDOOR: Final = "680.42"
    SPA_BONDING_WAIVER: Final = "680.42(B)"
    SPA_INDOOR_RECEPTACLES: Final = "680.43(A)"
    SPA_INDOOR_SWITCHES: Final = "680.43(C)"
    SPA_GFCI: Final = "680.44(A)"

    # Ch. 6-7 — sources; limited energy.
    RAPID_SHUTDOWN: Final = "690.12"
    PV_GROUNDING: Final = "690.47"
    RAPID_SHUTDOWN_ARRAY: Final = "690.12(B)(2)"
    RAPID_SHUTDOWN_INITIATION: Final = "690.12(C)"
    INTERCONNECTION: Final = "705.12"
    INTERCONNECTION_100PCT: Final = "705.12(B)(1)"
    INTERCONNECTION_120PCT: Final = "705.12(B)(2)(a)"
    INTERCONNECTION_LABEL: Final = "705.12(B)(2)(b)"
    # Was 800.133 / 725.136; Arts. 805 and 725.136 are gone, limited energy is Arts. 720-723.
    LIMITED_ENERGY_SEPARATION: Final = "722.15(A)"

    # Ch. 9.
    CONDUIT_DIMENSIONS: Final = "Chapter 9 Table 4"
    SLEEVE_FILL: Final = "Chapter 9 Note 2"


#: Rows not yet read in the printed 2026 text; ``mark``/``cite`` caveat them. Empty since
#: 2026-11-13: a new row read only in drafts or trade press goes here until confirmed.
UNCONFIRMED: Final = frozenset()


class NFPA780:
    """NFPA 780 (lightning protection), not NEC: cited by advisories only. The owner read
    4.1-4.5, 4.12.8-4.15 and 4.19 in print on 2026-11-14 (2026 ed.); paraphrase and what
    grades each in ``docs/nfpa-780-paraphrase.md``. GROUND_RING is a cross-reference only."""

    EDITION: Final = "NFPA 780-2026"
    CONDUCTORS: Final = "NFPA 780 4.1.1.1 / Table 4.1.1.1.1"
    GROUND_RING: Final = "NFPA 780 4.12.4"
    DISSIMILAR_METALS: Final = "NFPA 780 4.2.2.3.1 / 4.3.4.3 (no Al within 18 in of earth)"
    COMMON_GROUNDING: Final = "NFPA 780 4.13"
    SURGE: Final = "NFPA 780 4.19.2"


_CAVEAT = " [2026 number unconfirmed]"


def mark(section: str) -> str:
    """The section, with the caveat when its 2026 number is unconfirmed."""
    return section + _CAVEAT if section in UNCONFIRMED else section


def cite(*sections: str) -> str:
    """``cite("314.20", "314.23")`` -> ``"NEC 314.20 / 314.23"``, caveated if unconfirmed."""
    text = "NEC " + " / ".join(sections)
    return text + _CAVEAT if UNCONFIRMED.intersection(sections) else text

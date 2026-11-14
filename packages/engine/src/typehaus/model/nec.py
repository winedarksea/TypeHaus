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
(250.53(A)(4), 250.64; its 690.47 is now a printed read, below), MN DLI NEC FAQ (250.32(B)(1)),
WA L&I Elc2604 (250.53(A)(2)),
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
and 334.100-334.116; 110.22-110.28, 240.4(G)-(H), 240.5, 240.6 with Table 240.6(A) (coded in
``model/ampacity.py``), and 625.17-625.102; 706.1-706.30(A)(2) and 480.2-480.14;
all of Article 440 and 445.1-445.12(B);
all of Article 424 and the end of 422.62; 404.1-404.9, 406.9(B)-406.14(B), 408.1-408.6;
314.15-314.27 with Tables 314.16(A) and 314.16(B)(4); and 680.1-680.27(A) and 680.34-680.54
(680.27(B)-680.33 unread); 690.9(A)(d)-690.13, 690.15(A), the end of 690.43 with 690.45-690.72
(690.1-690.9(A) and 690.15(B)-690.43's opening unread); 705.5-705.25 (705.1-705.4,
705.28, 705.30, 705.40 on unread); and 710.1-710.15 (710.12 on unread); see
``docs/nec-2026-paraphrase-690-705-710.md``; 300.1, 300.4-300.9 and 300.21(tail)-300.25
(renumbered in 2026: 300.4 is Limitations, physical damage is 300.6, underground 300.7;
300.2-300.3, 300.9(A)(2)-300.21 and 300.25(C) on unread), with Table 300.7(A) (coded in
``model/burial.py``), in ``docs/nec-2026-paraphrase-300.md``. The
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
    WORKING_ILLUMINATION: Final = "110.26(D)"
    DEDICATED_SPACE_OUTDOOR: Final = "110.26(E)(2)"

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
    EVSE_CIRCUIT: Final = "625.40"  # an individual branch circuit
    EVSE_CONTINUOUS: Final = "625.41"  # continuous load: breaker at 125%
    EVSE_DISCONNECT: Final = "625.43(C)"
    EVSE_RECEPTACLE_GFCI: Final = "625.54"
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
    RACEWAY_BENDS: Final = "300.24"  # 360 deg between pull points, any combination of raceways
    # Art. 300 as printed 2026 (was 300.4 physical damage, 300.5 underground, 300.21 firestop).
    WIRING_LIMITATIONS: Final = "300.4"  # voltage, 310.14(A)(3) temperature, damaged conductors
    SAME_CIRCUIT_TOGETHER: Final = "300.5(B)"  # all conductors of a circuit, one raceway
    DIFFERENT_SYSTEMS: Final = "300.5(C)"
    PHYSICAL_DAMAGE: Final = "300.6"
    DAMAGE_BORED_HOLES: Final = "300.6(A)(1)"  # 1 1/4 in. from the edge, else 1/16 in. steel
    DAMAGE_NOTCHES: Final = "300.6(A)(2)"
    DAMAGE_NM_METAL_FRAMING: Final = "300.6(B)"
    DAMAGE_PARALLEL_FRAMING: Final = "300.6(D)"
    DAMAGE_ROOF_DECKING: Final = "300.6(E)"  # 1 1/2 in. under roof decking
    DAMAGE_SHALLOW_GROOVES: Final = "300.6(F)"
    DAMAGE_FITTINGS_4AWG: Final = "300.6(G)"
    STRUCTURAL_JOINTS: Final = "300.6(H)"
    UNDERGROUND: Final = "300.7"
    BURIAL_COVER: Final = "300.7(A)"  # Table 300.7(A), coded in model/burial.py
    BURIAL_TABLE: Final = "Table 300.7(A)"
    UNDERGROUND_WET: Final = "300.7(B)"  # inside an underground raceway is a wet location
    UNDER_BUILDING: Final = "300.7(C)"  # in a raceway
    UNDERGROUND_PROTECTION: Final = "300.7(D)"
    EMERGING_FROM_GRADE: Final = "300.7(D)(1)"  # protected to 8 ft above grade
    UNDERGROUND_DAMAGE: Final = "300.7(D)(4)"
    UNDERGROUND_SPLICES: Final = "300.7(E)"
    BACKFILL: Final = "300.7(F)"
    RACEWAY_SEALS: Final = "300.7(G)"  # spare or unused raceways are sealed too
    UNDERGROUND_BUSHING: Final = "300.7(H)"
    SAME_TRENCH: Final = "300.7(I)"
    EARTH_MOVEMENT: Final = "300.7(J)"
    DIRECTIONAL_BORING: Final = "300.7(K)"
    CORROSION: Final = "300.8"
    CORROSION_FERROUS: Final = "300.8(A)"
    CORROSION_IN_EARTH: Final = "300.8(A)(3)"  # ferrous raceways in concrete or earth
    CORROSION_ALUMINUM: Final = "300.8(B)"
    CORROSION_NONMETALLIC: Final = "300.8(C)"
    CORROSION_INDOOR_WET: Final = "300.8(D)"  # 1/4 in. airspace
    RACEWAY_CONDENSATION: Final = "300.9(A)"
    INDUCED_CURRENTS: Final = "300.22"
    FIRESTOPPING: Final = "300.23"  # was 300.21
    PLENUM_WIRING: Final = "300.25"
    DUCT_DUST_VAPOR: Final = "300.25(A)"
    DUCT_ENVIRONMENTAL_AIR: Final = "300.25(B)"
    OTHER_PLENUMS: Final = "300.25(C)"
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
    NEXT_SIZE_UP: Final = "240.4(B)"  # next standard OCPD above the ampacity
    STANDARD_OCPD: Final = "240.6(A)"  # Table 240.6(A), coded in model/ampacity.py
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
    SWITCH_HEIGHT: Final = "404.10(A)(2)"  # was 404.8(A); read 2026-11-14
    SWITCH_BACKFEED_SIGN: Final = "404.8(C)"  # load terminals energizable by a backfeed
    SWITCH_TUB_SHOWER: Final = "404.6(C)"
    BATH_ZONE: Final = "406.9(C)(1)"  # no receptacle within 3 ft of a tub or shower
    WET_RECEPTACLE: Final = "406.9(B)(1)"  # weather-resistant type, extra-duty hood
    CONTROLLED_RECEPTACLE: Final = "406.11(D)"  # automatic control: "controlled" symbol
    PUSH_IN_TERMINALS: Final = "406.10(3)"  # 15 A and 14 AWG solid copper only
    RECEPTACLE_REPLACEMENT: Final = "406.12(D)"
    CIRCUIT_DIRECTORY: Final = "408.4(A)"
    SWITCHBOARD_SCCR: Final = "408.6"
    PANELBOARDS: Final = "Article 408"
    WET_LUMINAIRE_ZONE: Final = "410.10(D)"
    SPACE_HEAT_CONTINUOUS: Final = "424.5"
    SPACE_HEAT_OUTLETS: Final = "424.4(B)"  # two or more heater outlets: 30 A at most
    SPACE_HEAT_GFCI: Final = "424.45(E)"  # under a floor covering; 424.44(E), 424.99(C)(5)
    SPACE_HEAT_DISCONNECT: Final = "424.19"
    SPACE_HEAT_LABEL: Final = "424.47"
    SPACE_HEAT_WALLS: Final = "424.48"  # cables and panels in walls: up to 4 ft, GFCI and AFCI

    # Ch. 6 — Art. 680 Parts I, II and IV as they reach a spa or hot tub (via 680.42/.43).
    GFCI_150V: Final = "680.5(B)"  # Class A, <=150 V to ground, <=60 A single-phase
    SPGFCI_OVER_150V: Final = "680.5(C)"
    POOL_GROUNDING: Final = "680.7"
    POOL_CORROSIVE: Final = "680.14"
    SPA_MAINT_DISCONNECT: Final = "680.13"
    POOL_RECEPTACLES: Final = "680.22(A)"
    POOL_RECEPTACLE_REQUIRED: Final = "680.22(A)(1)"
    POOL_LUMINAIRES: Final = "680.22(B)"
    POOL_SWITCHES: Final = "680.22(C)"
    POOL_OTHER_OUTLETS: Final = "680.22(E)"
    POOL_OTHER_EQUIPMENT: Final = "680.22(F)"
    POOL_EQUIPOTENTIAL: Final = "680.26"
    POOL_EQUIPOTENTIAL_PERIMETER: Final = "680.26(B)(2)"
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
    PV_GROUNDING: Final = "690.47(A)"  # array EGCs reach the building's electrode system
    PV_EGC_SIZE: Final = "690.45"  # 250.122, on an assumed OCPD per 690.9(B) if none
    PV_ARC_FAULT: Final = "690.11"  # dc circuits at 80 V or more
    PV_DISCONNECT: Final = "690.13"  # per 705.20; lockable open; "PV SYSTEM DISCONNECT"
    PV_ISOLATING: Final = "690.15"
    RAPID_SHUTDOWN_OUTSIDE: Final = "690.12(B)(1)"  # 30 V in 30 s outside the boundary
    RAPID_SHUTDOWN_ARRAY: Final = "690.12(B)(2)"
    RAPID_SHUTDOWN_INITIATION: Final = "690.12(C)"
    RAPID_SHUTDOWN_DWELLING: Final = "690.12(C)(1)(b)"  # a dwelling's initiator is outdoors
    RAPID_SHUTDOWN_BUILDING_LABEL: Final = "690.12(D)"  # at the service equipment
    RAPID_SHUTDOWN_SWITCH_LABEL: Final = "690.12(D)(2)"  # on or within 3 ft of the switch
    PV_BATHROOM: Final = "690.4(D)"  # no PV equipment or disconnect in a bathroom
    PV_MAX_VOLTAGE_DWELLING: Final = "690.7(2)"  # 600 V on or in a one- or two-family dwelling
    PV_VOLTAGE_COEFFICIENT: Final = "690.7(A)(1)"  # Voc at the lowest ambient, listed coefficient
    PV_VOLTAGE_TABLE: Final = "Table 690.7(A)"  # coded in model/pv_voltage.py
    PV_VOLTAGE_LABEL: Final = "690.7(D)"  # maximum dc voltage label
    PV_SOURCE_CURRENT: Final = "690.8(A)(1)(a)"  # 125% of the parallel modules' Isc
    PV_OCPD_RATING: Final = "690.9(B)"  # 125% of 690.8(A), next size up; assumed for 690.45
    PV_OCPD_MARKING: Final = "690.9(D)"
    PV_ISOLATING_DEVICE: Final = "690.15(B)"
    PV_EQUIPMENT_DISCONNECT: Final = "690.15(C)"
    PV_DISCONNECT_LOCATION: Final = "690.15(D)"
    PV_DC_WIRING_BUILDING: Final = "690.31(D)(1)"  # over 30 V or 8 A inside: metal raceway
    PV_DC_MARKING: Final = "690.31(D)(2)"  # "PHOTOVOLTAIC POWER SOURCE", every 10 ft
    PV_CONNECTORS: Final = "690.33(C)"
    PV_GFDI: Final = "690.41(B)"  # dc ground-fault detection over 30 V or 8 A
    # Art. 440 — air-conditioning and refrigeration (hermetic motor-compressors).
    HVAC_LISTING: Final = "440.2(A)"
    HVAC_BATH_ZONE: Final = "440.8"  # no A/C within 3 ft x 8 ft of a tub or shower
    HVAC_DISCONNECT_ENCLOSURE: Final = "440.11"  # lock or tool where unqualified persons reach
    HVAC_DISCONNECT_RATING: Final = "440.12(A)(1)"  # 115% of RLA or branch selection current
    HVAC_NAMEPLATE: Final = "440.4(B)"  # MCA and maximum OCPD marked on the equipment
    HVAC_DISCONNECT: Final = "440.14"  # in sight, readily accessible, 110.26(A)
    HVAC_MAX_OCPD: Final = "440.22"  # branch-circuit protection, nameplate maximum governs
    HVAC_CONDUCTORS: Final = "440.32"  # single compressor: 125% of rated-load current
    HVAC_COMBINATION_CONDUCTORS: Final = "440.35"  # multimotor: at least the marked MCA
    ESS_LISTING: Final = "706.2"
    ESS_DISCONNECT: Final = "706.15"
    ESS_EMERGENCY_SHUTDOWN: Final = "706.15(B)"  # dwellings: outdoor initiation device
    BATTERY_DISCONNECT: Final = "480.7(A)"  # over 60 V dc
    BATTERY_EMERGENCY_DISCONNECT: Final = "480.7(B)"  # dwellings: outdoors, EMERGENCY DISCONNECT
    INTERCONNECTION: Final = "705.12"
    INTERCONNECTION_100PCT: Final = "705.12(B)(1)"
    INTERCONNECTION_120PCT: Final = "705.12(B)(2)(a)"
    INTERCONNECTION_LABEL: Final = "705.12(B)(2)(b)"
    INTERCONNECTION_FEEDER: Final = "705.12(A)"  # feeder at 125% of the source's current
    INTERCONNECTION_SUM: Final = "705.12(B)(3)"  # sum of OCPDs within the bus; label
    SOURCE_PLAQUE: Final = "705.10"  # at the service equipment; also 690.56, 710.10, 480.7(G)
    SUPPLY_SIDE_OCPD: Final = "705.11(C)(1)"  # dwelling: OCPD within 10 ft of conductor
    SOURCE_DISCONNECT: Final = "705.20"
    SOURCE_DISCONNECT_TYPE: Final = "705.20(C)"  # (3): remote-controlled opens on power loss
    SOURCE_DISCONNECT_WARNING: Final = "705.20(F)"  # line and load both energizable open
    DC_POLARITY_MARKING: Final = "705.25(B)"
    SOURCE_OUTPUT_CURRENT: Final = "705.28(A)"  # rounds to the nearest ampere
    SOURCE_CONDUCTOR: Final = "705.28(B)"  # larger of 125% and the adjusted-and-corrected value
    SOURCE_OCPD: Final = "705.30(B)"  # at least 125% of 705.28(A)
    SOURCE_BACKFEED_BREAKER: Final = "705.30(D)"  # not one marked line and load
    SOURCE_HOLD_DOWN: Final = "705.30(E)"  # plug-in backfed breaker: 408.36(D) fastener
    EGC_SIZE: Final = "250.122"
    EGC_TABLE: Final = "Table 250.122"  # coded in model/ampacity.py
    EGC_UPSIZED: Final = "250.122(D)"  # upsized phase conductors: EGC by circular mils
    EGC_ALUMINUM: Final = "250.120(B)"  # no Al EGC in contact with masonry, concrete or earth
    STANDALONE_PLAQUE: Final = "710.10"
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

"""The parts tying each cast lateral-system column's HEAD to its beam, quoted for the engine.

`engineering/column_head_joint.py` grades the head joint and may not read the hardware
catalog, so the allowables are quoted here from the maker's document (the
`FramingSpec.standoff_fastener_*` precedent) and `integrity.head_connector_agrees` checks
each number against the catalog row. Two joints, one module, so the ten columns cannot
drift apart. Arithmetic: `notes/north_entry_piers.md` §9.
"""

from typehaus import HeadConnector

#: ** ONE PACK, HOUSE-WIDE (geometry review C3-E13, 2026-10-31). ** Every wood beam that lands
#: on a pour stands on an SS316-SHIM-35 pack, and every such pour is cast this far below the
#: soffit, so the pack is a real ¾" solid: wood held off the concrete, a drained gap, and the
#: levelling tolerance taken in the leaves (½"-1" either way of it). The north entry's piers
#: and cast columns and the garden's four corner columns all read this one number.
STANDOFF_PACK_IN = 0.75

#: The cast-in HETA20Z pair over an SS316-SHIM-35 pack: PT-BW-E/-GE/-RE/-RNE and
#: PT-SG-B{R,F}{1,3}. FL11473 Table 3 rates the PAIR, so the numbers are the set's
#: (`set_rated`), SP because every beam here is southern pine. Lateral is the lower of
#: F1 1,350 / F2 1,430. C_D 1.6 is already in both. Replaced the HGAM10 pair 2026-09-21,
#: whose Titen Turbo screws Simpson forbids exposed to the exterior environment
#: (`notes/column_head_connector_options.md`).
HETA20Z_PAIR_HEAD = HeadConnector(
    tie="HETA20Z", tie_count=2, set_rated=True, uplift_lb=2560.0, lateral_lb=1350.0,
    load_duration_factor=1.6,
    bearing="SS316-SHIM-35", bearing_width_in=3.5, bearing_length_in=3.5,
    source="Simpson Strong-Tie FL11473 Table 3, double HETA, concrete, 2- or 3-ply, SP: "
           "uplift 2,560, F1 1,350, F2 1,430 lb for the pair; note 1 already +60% for wind",
    interaction_rule="FL11473-R4 §9 Limitations item 4: (Design Uplift / Allowable Uplift) + "
                     "(Lateral Parallel / Allowable) + (Lateral Perpendicular / Allowable) "
                     "< 1.0, for more than one direction on a single connection")

#: PT-BW-W / -GW: the head is the CBSQ66-SDS2 base under PT-BW-CW / -CNW (ABU66SS until
#: 2026-09-30), and the seat beam hangs off that 6x6 on an LUS26-2Z (`params/breezeway.py`).
CBSQ66_HEAD = HeadConnector(
    tie="CBSQ66-SDS2", tie_count=1, uplift_lb=3060.0, lateral_lb=485.0,
    load_duration_factor=1.6,
    bearing="CBSQ66-SDS2", bearing_width_in=5.5, bearing_length_in=5.5,
    source="ICC-ES ESR-3050 Table 1, CBSQ66-SDS2, Wind and SDC A & B, CRACKED uplift 3,060 lb "
           "at C_D 1.6 (4,375 uncracked); lateral F1 485 / F2 1,270 lb from Simpson C-C-2024, "
           "the lower quoted — the report publishes none",
    interaction_rule="Simpson C-C-2024 general notes: a connector loaded in more than one "
                     "direction is checked as the sum of each design load over its allowable, "
                     "<= 1.0")

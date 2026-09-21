"""The parts tying each cast lateral-system column's HEAD to its beam, quoted for the engine.

`engineering/column_head_joint.py` grades the head joint and may not read the hardware
catalog, so the allowables are quoted here from the maker's document (the
`FramingSpec.standoff_fastener_*` precedent) and `integrity.head_connector_agrees` checks
each number against the catalog row. Two joints, one module, so the ten columns cannot
drift apart. Arithmetic: `notes/north_entry_piers.md` §9.
"""

from typehaus import HeadConnector

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

#: PT-BW-W / -GW: the head is the ABU66SS under PT-BW-CW / -CNW, and the seat beam hangs off
#: that 6x6 on an HU28-2Z (`params/breezeway.py`). ESR-1622 Table 2 publishes uplift and
#: download only, so there is no lateral figure to quote and the record says so.
ABU66SS_HEAD = HeadConnector(
    tie="ABU66SS", tie_count=1, uplift_lb=2190.0, lateral_lb=None,
    load_duration_factor=1.6,
    bearing="SS316-SHIM-35", bearing_width_in=3.5, bearing_length_in=3.5,
    source="ICC-ES ESR-1622 Table 2, ABU66 row (bolted, 2,190 lb uplift at C_D 1.6), "
           "extended to ABU66SS by Simpson letter L-F-SSNAILS; no lateral value published")

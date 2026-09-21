"""The parts tying each cast lateral-system column's HEAD to its beam, quoted for the engine.

`engineering/column_head_joint.py` grades the head joint and may not read the hardware
catalog, so the allowables are quoted here from the maker's document (the
`FramingSpec.standoff_fastener_*` precedent) and `integrity.head_connector_agrees` checks
each number against the catalog row. Two joints, one module, so the ten columns cannot
drift apart. Arithmetic: `notes/north_entry_piers.md` §9.
"""

from typehaus import HeadConnector

#: The HGAM10 pair over an SS316-SHIM-35 pack: PT-BW-E/-GE/-RE/-RNE and PT-SG-B{R,F}{1,3}.
#: Lateral is the AWAY-FROM F2 (460), never the 795 INTO figure, and a pair does not double
#: it: which gusset takes the load in which sense is not something the model can say
#: (`library/hardware.py`, HGAM10_MASONRY_GUSSET). C_D 1.6 is already in both numbers.
HGAM10_PAIR_HEAD = HeadConnector(
    tie="HGAM10", tie_count=2, uplift_lb=585.0, lateral_lb=460.0,
    load_duration_factor=1.6,
    bearing="SS316-SHIM-35", bearing_width_in=3.5, bearing_length_in=3.5,
    source="Simpson Strong-Tie FL11473 Table 1, HGAM10 row, SPF/HF column: uplift 585, "
           "F1 630, F2 795 into / 460 away (fn 5); fn 1 already +60% for wind")

#: PT-BW-W / -GW: the head is the ABU66SS under PT-BW-CW / -CNW, and the seat beam hangs off
#: that 6x6 on an HU28-2Z (`params/breezeway.py`). ESR-1622 Table 2 publishes uplift and
#: download only, so there is no lateral figure to quote and the record says so.
ABU66SS_HEAD = HeadConnector(
    tie="ABU66SS", tie_count=1, uplift_lb=2190.0, lateral_lb=None,
    load_duration_factor=1.6,
    bearing="SS316-SHIM-35", bearing_width_in=3.5, bearing_length_in=3.5,
    source="ICC-ES ESR-1622 Table 2, ABU66 row (bolted, 2,190 lb uplift at C_D 1.6), "
           "extended to ABU66SS by Simpson letter L-F-SSNAILS; no lateral value published")

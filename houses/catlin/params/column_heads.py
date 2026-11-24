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

#: The cast-in HETA20Z pair over an SS316-SHIM-35 pack: PT-BW-E/-GE/-RE/-RNE (2- or 3-ply
#: beams, Table 3's 2-/3-ply row); the garden's PT-SG-B{R,F}{1,3} use the 1-ply row below.
#: Lateral is the lower of F1 / F2. C_D 1.6 is already in both. Replaced the HGAM10 pair
#: 2026-09-21, whose Titen Turbo screws Simpson forbids exposed to the exterior environment
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

#: ** THE BALCONY'S BEAMS ARE ONE PLY, WRAPPED OVER THE TOP (owner decision 8, 2026-11-22). **
#: A 3-1/2" glulam is a single member, so its pair is graded on Table 3's **1-ply** columns, not
#: the 2- or 3-ply ones: uplift 1,920, F1 1,115, F2 900 lb (the lower, 900, is the lateral).
#: Each 16" strap is NOT field-trimmed any more: it rises the beam's 11-7/8" face and the
#: 3/4" pack, then wraps 3-3/8" over the top, so no written confirmation from Simpson is
#: owed. Table 3 note 7 (F1 may add 1/16" of deflection on 2-/3-ply when the straps are not
#: wrapped over the heel) is a deflection note for an UNWRAPPED strap; these are wrapped.
#: **Note 6 of the same table reads "Lateral loads for double META, HETA, and HHETA apply
#: only to 2- or 3-ply applications with anchors spaced a minimum of 3 in apart" while the
#: table prints 1-ply F1/F2 cells; the owner's reading takes the printed row.** Read in FL11473
#: R6 (SIM202301, sealed 2023-10-17) p. 10 of 14; the catalog edition (C-C-2026) is not read.
#: **OWNER-ACCEPTED READING of a self-conflicting document (2026-11-23): grade on the PRINTED
#: 1-ply F1/F2 cells.** Notes 6 and 7 are both quoted on the source below.
HETA20Z_PAIR_HEAD_1_PLY = HeadConnector(
    tie="HETA20Z-1PLY", tie_count=2, set_rated=True, uplift_lb=1920.0, lateral_lb=900.0,
    load_duration_factor=1.6,
    bearing="SS316-SHIM-35", bearing_width_in=3.5, bearing_length_in=3.5,
    source="Simpson Strong-Tie FL11473 R6 (sealed 2023-10-17) p. 10 of 14, Table 3, double "
           "HETA, concrete, 1-PLY columns, SP: uplift 1,920, F1 1,115, F2 900 lb for the pair, "
           "10 nails 0.148x1-1/2 (5 per strap), straps wrapped over the beam top; note 1 "
           "already +60% for wind; note 7 = the 1/16\" deflection note for unwrapped straps; "
           "note 6 limits double-anchor lateral to 2-/3-ply (the table prints the 1-ply cells "
           "regardless) — owner reading, C-C-2026 not read",
    interaction_rule="FL11473 R6 §9 Limitations item 4: (Design Uplift / Allowable Uplift) + "
                     "(Lateral Parallel / Allowable) + (Lateral Perpendicular / Allowable) "
                     "< 1.0, for more than one direction on a single connection")

#: PT-BW-W / -GW: the head is the CBSTQ66Z-SDS2 base under PT-BW-CW / -CNW (C2 E10: Simpson
#: retired the CBSQ66 for it), and the seat beam hangs off that 6x6 on an LUS26-2Z
#: (`params/breezeway.py`).
CBSTQ66Z_HEAD = HeadConnector(
    tie="CBSTQ66Z-SDS2", tie_count=1, uplift_lb=3060.0, lateral_lb=485.0,
    load_duration_factor=1.6,
    bearing="CBSTQ66Z-SDS2", bearing_width_in=5.5, bearing_length_in=5.5,
    source="ICC-ES ESR-3050 (Aug 2026) Table 2, CBSTQ66Z-SDS2, Wind and SDC A & B, CRACKED "
           "uplift 3,060 lb at C_D 1.6 (4,375 uncracked); lateral F1 485 / F2 1,270 lb from "
           "Simpson C-C-2026 p. 85 fn. 5, the lower quoted — the report publishes none",
    interaction_rule="Simpson C-C-2026 p. 23 note e / p. 289 Option 1: a connector loaded in "
                     "more than one direction is checked as the sum of each design load over "
                     "its allowable, < 1.0")

"""The north-entry landing's TWO tie lines (owner, 2026-09-21; notes/north_entry_piers.md §10).

`engineering/deck_tie_basis.wall_ties` reads this hardware and DERIVES that `FS-BW-FLOOR` is
braced, so the four landing piers lean; `deck_tie/FS-BW-FLOOR` grades what the ties carry.

**Line 1, the stem (x = 7'-1 1/2" / 9'-5 1/2").** Each carrier crosses the ICF stem 3 3/4"
over its top, so it takes a KDAT 4x tie block screwed up into its soffit, stopping 1/4" off
the concrete (nothing bears on the garage). A pair of HL33HDG angles, one each block face,
heel running N-S: the wood leg through-bolted 1/2" through the block (HL fn 4: 3 1/2" member),
the concrete leg on the stem top, one 1/2" x 4" mechanically galvanized Titen HD each on the
6" core's centreline (ESR-2713 §5.20: exterior-rated). Simpson publishes no HL value on
concrete: the anchor side is `engineering/deck_tie_anchor.py`, ACI 318-19 Ch. 17.

**Line 2, the screen's own line (x = 6'-0") into `W-G-W`, wood to wood.** Two HL33HDG
stacked on the screen's north end post (east face), heel vertical, the other leg on the
garage's south face at its SW corner: lag screws >= 5" (HL fn 7) through a KDAT filler cut
flush with the corrugated into the corner pack. Collinear with the screen, so its 981 lb
goes straight into the garage's west shear wall with no couple.

`Connector.axis` is the angle's HEEL in plan ("y"); `None` is a vertical heel.
"""

from plan.storeys.garage import GARAGE_Y_SOUTH

from params.north_entry_frame import (
    BEAM_X_FT,
    DECK_JOIST_TOP_FT,
    GARAGE_CLADDING_Y_FT,
    JOIST_DEPTH_IN,
    LANDING_WEST_FT,
)
from typehaus import Connector, ConnectorKind, ft, inch, pt

#: The stem top, -1'-0" (W-GF-* `_STEM_TOP`), and the tie line over its core.
STEM_TOP_FT = -1.0
STEM_CORE_Y_FT = GARAGE_Y_SOUTH.feet + 5.5 / 12
#: Half the 3 1/2" tie block: each angle's heel is on a block face.
_BLOCK_HALF_IN = 1.75
#: An HL33's centre: half its 3 1/4" leg above the stem top.
_ANGLE_Z_FT = STEM_TOP_FT + 1.625 / 12
#: The block's centre: 1/4" gap, then half of 3 1/2".
_BLOCK_Z_FT = STEM_TOP_FT + (0.25 + 1.75) / 12
#: Line 2: the end post's east face (a half stud, then the 5/8" 303 ply), and two heights.
_SCREEN_EAST_FACE_FT = LANDING_WEST_FT + (1.75 + 0.625) / 12
_GARAGE_TIE_Z_FT = (1.0, 3.0)

assert DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12 - STEM_TOP_FT > 3.5 / 12, \
    "the carrier soffit no longer clears a 3 1/2in tie block over the stem"

LANDING_TIES = [
    Connector(uid="ARD33PDHYR", tag="CN-BW-STEMTIE-FC-A", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[0]) - inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL33HDG", axis="y",
              connects=("BM-BW-FC", "W-GF-S1")),
    Connector(uid="AJ70HT0M2D", tag="CN-BW-STEMTIE-FC-B", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[0]) + inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL33HDG", axis="y",
              connects=("BM-BW-FC", "W-GF-S1")),
    Connector(uid="0TW5SE2NX5", tag="CN-BW-STEMTIE-FE-A", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[1]) - inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL33HDG", axis="y",
              connects=("BM-BW-FE", "W-GF-S-DR")),
    Connector(uid="VNT251FTF3", tag="CN-BW-STEMTIE-FE-B", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[1]) + inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL33HDG", axis="y",
              connects=("BM-BW-FE", "W-GF-S-DR")),
    Connector(uid="B0FS509J9R", tag="CN-BW-STEMTIE-FC-BLK", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(BEAM_X_FT[0]), ft(STEM_CORE_Y_FT)), elevation=ft(_BLOCK_Z_FT),
              size="TIE-BLOCK-4X4-KDAT", connects=("BM-BW-FC",)),
    Connector(uid="QT6E9ZZ2W8", tag="CN-BW-STEMTIE-FE-BLK", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(BEAM_X_FT[1]), ft(STEM_CORE_Y_FT)), elevation=ft(_BLOCK_Z_FT),
              size="TIE-BLOCK-4X4-KDAT", connects=("BM-BW-FE",)),
    Connector(uid="CES7V86D9V", tag="CN-BW-GWTIE-LO", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_SCREEN_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_GARAGE_TIE_Z_FT[0]), size="HL33HDG",
              connects=("W-BW-SCREEN", "W-G-W")),
    Connector(uid="RDSEPP2CCP", tag="CN-BW-GWTIE-HI", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_SCREEN_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_GARAGE_TIE_Z_FT[1]), size="HL33HDG",
              connects=("W-BW-SCREEN", "W-G-W")),
    Connector(uid="VZYJM83Z1V", tag="CN-BW-GWTIE-BLK", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(_SCREEN_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(sum(_GARAGE_TIE_Z_FT) / 2), size="TIE-BLOCK-4X4-KDAT",
              connects=("W-BW-SCREEN",)),
]

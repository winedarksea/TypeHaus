"""The north-entry landing's TWO tie lines (owner, 2026-09-21; notes/north_entry_piers.md §10).

`engineering/deck_tie_basis.wall_ties` reads this hardware and DERIVES that `FS-BW-FLOOR` is
braced, so the four landing piers lean; `deck_tie/FS-BW-FLOOR` grades what the ties carry.

**Line 1, the stem (x = 7'-1 1/2" / 9'-5 1/2").** Each carrier crosses the ICF stem 3 3/4"
over its top, so it takes a KDAT 4x tie block (3 1/2" x 3 1/2" x 5" N-S) screwed up into its
soffit, stopping 1/4" off the concrete. A pair of HL35HDG angles, one each block face, heel
running N-S: the wood leg through-bolted with two 1/2" bolts through the block (HL fn 3/4),
the concrete leg on the stem top. Its two holes are 2 1/2" apart, under ESR-2713's 3" s_min,
so ONE 1/2" x 4" mechanically galvanized Titen HD per leg and the other hole EMPTY; angle and
block sit 1 1/4" north so that hole is on the core centreline — a detail flagged for the
engineer of record (`engineering/deck_tie_anchor.py`, ACI 318-19 Ch. 17).
Wet service (C_M 0.70): over the stem, under an open-jointed deck.

**Line 2, the screen's own line (x = 6'-0") into `W-G-W`, wood to wood.** Two HL33HDG
stacked on the screen's north end post (east face), heel vertical, the other leg on the
garage's south face at its SW corner: lag screws >= 5" (HL fn 7) through a KDAT filler cut
flush with the corrugated into the corner pack. A 4x KDAT filler in the end stud pack gives
the post leg a 3 1/2" face (two 2x plies give 3"; HL fn 3). Collinear with the screen, so its
981 lb goes straight into the garage's west shear wall with no couple. Graded DRY (below).

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
from typehaus import Connector, ConnectorKind, InServiceMoisture, ft, inch, pt

#: The stem top, -1'-0" (W-GF-* `_STEM_TOP`), and the tie line over its core.
STEM_TOP_FT = -1.0
STEM_CORE_Y_FT = GARAGE_Y_SOUTH.feet + 5.5 / 12
#: The stem angles and their blocks stand 1 1/4" NORTH of the core centreline (owner,
#: 2026-09-21): the HL35's first hole, D1 = 1 1/4" off its end, then lands ON the centreline,
#: 3" from each face — the hole `deck_tie_anchor` anchors (the one nearest the centreline).
#: The leg's north 3/4" oversails the core over the interior EPS: non-bearing; trim the foam
#: flush, don't crush it. North, not south: the exterior stem-top Z runs across this RO.
_ANGLE_SHIFT_IN = 1.25
_STEM_TIE_Y_FT = STEM_CORE_Y_FT + _ANGLE_SHIFT_IN / 12
#: Half the 3 1/2" tie block: each angle's heel is on a block face.
_BLOCK_HALF_IN = 1.75
#: An HL35's centre: half its 3 1/4" leg above the stem top.
_ANGLE_Z_FT = STEM_TOP_FT + 1.625 / 12
#: The block's centre: 1/4" gap, then half of 3 1/2".
_BLOCK_Z_FT = STEM_TOP_FT + (0.25 + 1.75) / 12
#: Line 2: the end post's east face (a half stud, then the 5/8" 303 ply), and two heights.
_SCREEN_EAST_FACE_FT = LANDING_WEST_FT + (1.75 + 0.625) / 12
_GARAGE_TIE_Z_FT = (1.0, 3.0)
#: Line 2's service condition: an owner judgement (2026-09-21) the EOR confirms.
_W_SERVICE = InServiceMoisture(
    condition="dry",
    basis="vertical faces under RF-BW-CANOPY, behind W-BW-SCREEN, reached only by windblown "
          "moisture: NDS 2018 §11.3.3 / Table 11.3.3 applies C_M 0.70 only where in-service "
          "MC exceeds 19%, and the NDS Commentary (C4.1.4, quoted secondhand — not read from "
          "the primary) calls members protected by a roof but occasionally wetted by "
          "windblown moisture, such as covered porches, generally dry")

assert DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12 - STEM_TOP_FT > 3.5 / 12, \
    "the carrier soffit no longer clears a 3 1/2in tie block over the stem"

LANDING_TIES = [
    Connector(uid="ARD33PDHYR", tag="CN-BW-STEMTIE-FC-A", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[0]) - inch(_BLOCK_HALF_IN), ft(_STEM_TIE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL35HDG", axis="y",
              connects=("BM-BW-FC", "W-GF-S1")),
    Connector(uid="AJ70HT0M2D", tag="CN-BW-STEMTIE-FC-B", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[0]) + inch(_BLOCK_HALF_IN), ft(_STEM_TIE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL35HDG", axis="y",
              connects=("BM-BW-FC", "W-GF-S1")),
    Connector(uid="0TW5SE2NX5", tag="CN-BW-STEMTIE-FE-A", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[1]) - inch(_BLOCK_HALF_IN), ft(_STEM_TIE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL35HDG", axis="y",
              connects=("BM-BW-FE", "W-GF-S-DR")),
    Connector(uid="VNT251FTF3", tag="CN-BW-STEMTIE-FE-B", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[1]) + inch(_BLOCK_HALF_IN), ft(_STEM_TIE_Y_FT)),
              elevation=ft(_ANGLE_Z_FT), size="HL35HDG", axis="y",
              connects=("BM-BW-FE", "W-GF-S-DR")),
    Connector(uid="B0FS509J9R", tag="CN-BW-STEMTIE-FC-BLK", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(BEAM_X_FT[0]), ft(_STEM_TIE_Y_FT)), elevation=ft(_BLOCK_Z_FT),
              size="TIE-BLOCK-4X4X5-KDAT", connects=("BM-BW-FC",)),
    Connector(uid="QT6E9ZZ2W8", tag="CN-BW-STEMTIE-FE-BLK", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(BEAM_X_FT[1]), ft(_STEM_TIE_Y_FT)), elevation=ft(_BLOCK_Z_FT),
              size="TIE-BLOCK-4X4X5-KDAT", connects=("BM-BW-FE",)),
    Connector(uid="CES7V86D9V", tag="CN-BW-GWTIE-LO", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_SCREEN_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_GARAGE_TIE_Z_FT[0]), size="HL33HDG",
              connects=("W-BW-SCREEN", "W-G-W"),
              service=_W_SERVICE),
    Connector(uid="RDSEPP2CCP", tag="CN-BW-GWTIE-HI", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_SCREEN_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_GARAGE_TIE_Z_FT[1]), size="HL33HDG",
              connects=("W-BW-SCREEN", "W-G-W"),
              service=_W_SERVICE),
    Connector(uid="VZYJM83Z1V", tag="CN-BW-GWTIE-BLK", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(_SCREEN_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(sum(_GARAGE_TIE_Z_FT) / 2), size="TIE-BLOCK-4X4-KDAT",
              connects=("W-BW-SCREEN",)),
    Connector(uid="HSFTHD5JAJ", tag="CN-BW-GWTIE-FILLER", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(LANDING_WEST_FT), ft(GARAGE_CLADDING_Y_FT) - inch(1.75)),
              elevation=ft(sum(_GARAGE_TIE_Z_FT) / 2), size="FILLER-4X4-KDAT",
              connects=("W-BW-SCREEN",)),
]

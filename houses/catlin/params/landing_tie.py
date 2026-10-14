"""The north-entry landing's TWO tie lines (owner, 2026-09-21; notes/north_entry_piers.md §10).

`engineering/deck_tie_basis.wall_ties` reads this hardware and DERIVES that `FS-BW-FLOOR` is
braced, so the four landing piers lean; `deck_tie/FS-BW-FLOOR` grades what the ties carry.

**Line 1, the east edge beam into `W-G-S` (since 2026-10-13), wood to wood.** Two 3 ga
HL43HDG stacked on `BM-BW-FE`'s east face at its tip, heel vertical, the other leg on the
garage's south face over `D-G-SERVICE`'s east jamb pack: 3/4" lag screws >= 5" (HL fn 7)
through a KDAT filler cut flush with the corrugated. The wood leg's 3/4" bolt goes through
FE (3-ply, 4 1/2") AND the deck's east rim joist beside it: 6", over fn 5's 5 1/8". FOR THE
ENGINEER OF RECORD: that bolt stands 2 3/4" (3.7D) off FE's end grain, under NDS Table
12.5.1A's 7D for full design value, and the lag lands in a two-ply jack/king pack. Wet
service: under the open-jointed deck. HL33s graded 1.11 here -- two joints 3.4' apart put
~520 lb of the screen's wind couple across this one, against one 7 ga angle's 518 lb wet. It replaced the stem tie (two HL35HDG on tie blocks
under the carriers, a Titen HD each into the ICF core), which went with the carriers when the
interior landing did; uids ARD33PDHYR, AJ70HT0M2D, 0TW5SE2NX5, VNT251FTF3, B0FS509J9R and
QT6E9ZZ2W8 are retired.

**Line 2, the screen's own line (x = 6'-0") into `W-G-W`, wood to wood.** Two HL33HDG
stacked on the screen's north end post (east face), heel vertical, the other leg on the
garage's south face at its SW corner: lag screws >= 5" (HL fn 7) through a KDAT filler cut
flush with the corrugated into the corner pack. A 4x KDAT filler in the end stud pack gives
the post leg a 3 1/2" face (two 2x plies give 3"; HL fn 3). Collinear with the screen, so its
981 lb goes straight into the garage's west shear wall with no couple. Graded DRY (below).

`Connector.axis` is the angle's HEEL in plan ("y"); `None` is a vertical heel.
"""

from params.north_entry_frame import (
    EDGE_BEAM_WIDTH_IN,
    DECK_JOIST_TOP_FT,
    EDGE_BEAM_X_FT,
    GARAGE_CLADDING_Y_FT,
    JOIST_DEPTH_IN,
    LANDING_WEST_FT,
)
from typehaus import Connector, ConnectorKind, InServiceMoisture, ft, inch, pt

#: Line 1: FE's east face, and two angle centres inside its 7 1/4" depth (3" angles, 1/4"
#: off each edge, 3/4" between them).
_FE_EAST_FACE_FT = EDGE_BEAM_X_FT + EDGE_BEAM_WIDTH_IN / 24
_FE_TIE_Z_FT = (DECK_JOIST_TOP_FT - (JOIST_DEPTH_IN - 1.75) / 12,
                DECK_JOIST_TOP_FT - 1.75 / 12)
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

LANDING_TIES = [
    Connector(uid="PYYM5Z66YC", tag="CN-BW-GSTIE-LO", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_FE_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_FE_TIE_Z_FT[0]), size="HL43HDG",
              connects=("BM-BW-FE", "W-G-S")),
    Connector(uid="91DJWZFH4H", tag="CN-BW-GSTIE-HI", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_FE_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_FE_TIE_Z_FT[1]), size="HL43HDG",
              connects=("BM-BW-FE", "W-G-S")),
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

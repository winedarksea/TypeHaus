"""The north-entry landing's two tie joints and the screen's collector strap (G5, 2026-11-23).

`engineering/deck_tie_basis.wall_ties` reads this hardware and DERIVES that `FS-BW-FLOOR` is
braced, so the four landing piers lean; `deck_tie/FS-BW-FLOOR` grades what the ties carry
(notes/north_entry_piers.md §10p). Each part carries only the direction it is published for.

**Joint W, the screen's line (N-S): one MSTA49Z collector strap** (C-C-2026 p. 290, 2,020 lb),
flat over the 7/16" ZIP on the WEST plane the screen shares with W-G-W, at the screen's top
plate (+4'-0"), run north across the joint into W-G-W. All 13 landing nails in the long top
plate south of PT-BW-CNW (>= 18"; the strap crosses the column and the 6 1/8" plate stub
un-nailed), all 13 garage nails in a continuous 2x KDAT nailer let into W-G-W at the same
height (>= 18"); HDG 0.148x2-1/2 (General Note b, over the ZIP). It takes the canopy's N-S
share straight from SB-BW-BAND to W-G-W, so the screen's chords, bases and piers carry no N-S
(`engineering/lateral_band`). Tension only: the push north bears through CN-BW-GWTIE-FILLER,
now at the strap line between the screen's end pack and the garage face.

**Joint FE, the east edge beam into W-G-S.** N-S: a DTT2Z pair on a 1/2" HDG threaded rod (the
catalog's deck-to-house lateral detail; Holdown General Note h, horizontal use), one on FE's
east face low, one inside the garage on the D-G-SERVICE east jamb framing, set BEFORE DRYWALL.
Open detail: the rod line (1 5/8" off FE's face) meets the 2-ply jamb pack, so the garage tie
wants a nailer or filler the drawing must show. E-W: one HL43HDG per face of FE, heel
vertical, high (fn 6: both sides for both senses), on its published F1 — an OWNER-ACCEPTED
reading outside the published condition (2026-11-23): the figure's F1 bears along the grain,
here the garage leg's lags bear across a vertical stud's grain, which may be materially
lower. Line 2's HL33HDG pair and tie block are gone.

All parts graded WET (C_M 0.70, NDS Table 11.3.3; decision 17). ZMAX/HDG is the catalog's
Medium class, which Wet Service on treated wood <= UC4A takes (C-C-2026 pp. 14-17).
`Connector.axis`: a tension tie's run in plan; `None` is an angle's vertical heel.
"""

from params.north_entry_frame import (
    DECK_JOIST_TOP_FT,
    EDGE_BEAM_WIDTH_IN,
    EDGE_BEAM_X_FT,
    GARAGE_CLADDING_Y_FT,
    JOIST_DEPTH_IN,
    JOIST_MEMBER_WIDTH_IN,
    SCREEN_AXIS_X_FT,
    SCREEN_PANEL_TOP_FT,
)
from typehaus import Connector, ConnectorKind, ft, inch, pt

_FE_EAST_FACE_FT = EDGE_BEAM_X_FT + EDGE_BEAM_WIDTH_IN / 24
#: The west angle sits on the deck's east rim joist, against FE's west face, so its bolt
#: passes rim + FE = 6" (HL fn 5: >= 5 1/8" for the 4-series).
_FE_WEST_FACE_FT = EDGE_BEAM_X_FT - EDGE_BEAM_WIDTH_IN / 24 - JOIST_MEMBER_WIDTH_IN / 12
#: Angles high in FE's 7 1/4", the DTT low beside them.
_FE_HIGH_Z_FT = DECK_JOIST_TOP_FT - 1.75 / 12
_FE_LOW_Z_FT = DECK_JOIST_TOP_FT - (JOIST_DEPTH_IN - 1.75) / 12
#: The DTT's rod centreline stands 1 5/8" off its mounting face (C-C-2026 p. 60, CL).
_ROD_X_FT = _FE_EAST_FACE_FT + 1.625 / 12
#: The strap's line: the screen's west framing face (over the ZIP), on its top plate.
_STRAP_X_FT = SCREEN_AXIS_X_FT - 1.75 / 12
_STRAP_Z_FT = SCREEN_PANEL_TOP_FT - 0.75 / 12

LANDING_TIES = [
    Connector(uid="PYYM5Z66YC", tag="CN-BW-GSTIE-LO", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_FE_EAST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_FE_HIGH_Z_FT), size="HL43HDG",
              connects=("BM-BW-FE", "W-G-S")),
    Connector(uid="91DJWZFH4H", tag="CN-BW-GSTIE-HI", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_FE_WEST_FACE_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_FE_HIGH_Z_FT), size="HL43HDG",
              connects=("BM-BW-FE", "W-G-S")),
    Connector(uid="PZ8324BQ2Z", tag="CN-BW-GSDTT-S", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(_ROD_X_FT), ft(GARAGE_CLADDING_Y_FT) - inch(4.0)),
              elevation=ft(_FE_LOW_Z_FT), size="DTT2Z", axis="y",
              connects=("BM-BW-FE", "W-G-S")),
    Connector(uid="6RP5ZRM8AC", tag="CN-BW-GSDTT-N", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(_ROD_X_FT), ft(GARAGE_CLADDING_Y_FT) + inch(8.0)),
              elevation=ft(_FE_LOW_Z_FT), size="DTT2Z", axis="y",
              connects=("BM-BW-FE", "W-G-S")),
    Connector(uid="15F5GM1E3J", tag="CN-BW-SCREEN-STRAP", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(_STRAP_X_FT), ft(GARAGE_CLADDING_Y_FT)),
              elevation=ft(_STRAP_Z_FT), size="MSTA49Z", axis="y",
              connects=("W-BW-SCREEN", "W-G-W")),
    Connector(uid="HSFTHD5JAJ", tag="CN-BW-GWTIE-FILLER", kind=ConnectorKind.TIE_BLOCK,
              position=pt(ft(SCREEN_AXIS_X_FT), ft(GARAGE_CLADDING_Y_FT) - inch(1.75)),
              elevation=ft(_STRAP_Z_FT), size="FILLER-4X4-KDAT",
              connects=("W-BW-SCREEN",)),
]

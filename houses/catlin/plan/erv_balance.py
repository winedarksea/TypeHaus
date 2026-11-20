"""The ERV's 210/210 balance: one constant per terminal, every ERV leg a sum of them.

Not editable, because the legs are arithmetic. The registers (``plan/mep_registers_*.py``)
and the ducts (``plan/mep_erv_*.py``) name these constants and never a number, so a
terminal and its radial cannot disagree again: before 2026-11-06 eight legs did, BENCH and
the plant extract 12 at the grille against 6/5 on the duct the static budget grades (C4 E4). The owner
took the duct split. Constant names are the element tags.

EQ-B-ERV is a BALANCED machine authored at 210 cfm, HVI-certified at 206 at 0.4" w.g.
(plan/mep_erv_types.py::EQ-T-BROAN-B210E75RT explains which number is which). Supply is
118 cfm across the six REG-*-SUP* terminals plus the 92 DU-S-ERV-HP-FEED puts into
EQ-S-ERV-MIX (2026-11-20: the sauna 20 -> 38 for Harvia's 5 ACH, BED 15 -> 20 to match its
ensuite's extract, both paid from the feed's 115). The STUDY booth runs +5 net under
D-M-STUDY: 10 in against the 5 its return takes (``mep_registers_main.py``).

MN R403.5 asks ~188 cfm (5 bedrooms); the machine delivers ~199 off its curve
(notes/erv_static_budget.md §10.30).

A shared leg carries every terminal beyond it over its whole length, the LAUNDRY
precedent: GYM carries the sauna supply, SAUNA-EXH the bench valve, BED the living supply.
A branch keeps its own terminal's constant; trunks sum the parents.

Extract is 210 on the dampers, holding every code minimum:

* The six bathroom terminals at 20 cfm each (IRC R303.3 / M1505.4.4's continuous
  local-exhaust rate) plus the sauna's 38 (Harvia 5 ACH): 158 cfm, untouchable.
* The other seven share 52: the workshop bench valve 6, the study return 5, mudroom 10,
  kitchen 13, laundry 3, the attic return 5, the stair-top pickup 10.
  2026-11-20: RM-S-VANITY (lavatories only, no code bathroom) and the BED1/BED2 5 cfm
  tokens were deleted; the stair pickup and the kitchen took their residue.

The bench valve is a token flow (solder fume is a benchtop extractor's job). The honest fix is a LARGER ERV, not a
redistribution; this arithmetic is true against the machine the house has.
"""

# --- supply terminals ---------------------------------------------------------------------
REG_B_SUP1 = 10        # RM-B-GYM
REG_B_SUP2 = 20        # RM-B-PLAY-N
REG_B_SUP3 = 38        # RM-B-SAUNA (Harvia 5 ACH on 456 ft3)
REG_M_SUP1 = 20        # RM-M-LIVING
REG_M_SUP3 = 20        # RM-M-BED (matches the sealed ensuite's 20)
REG_M_SUP4 = 10        # RM-M-STUDY-CLOSET
EQ_S_ERV_MIX = 92      # into System 1's return plenum

# --- extract terminals --------------------------------------------------------------------
REG_B_RET1 = 6         # RM-B-WORKSHOP bench valve
REG_B_EXH1 = 20        # RM-B-BATH
REG_B_EXH2 = 38        # RM-B-SAUNA
REG_M_EXH1 = 20        # RM-M-BATH1
REG_M_EXH2 = 20        # RM-M-BATH2
REG_M_RET_STUDY = 5    # RM-M-STUDY-CLOSET
REG_M_RET3 = 3         # RM-M-LAUNDRY
REG_M_RET5 = 13        # the kitchen, in RM-M-LIVING
REG_M_RET_MUD = 10     # RM-M-MUDROOM (took RM-S-PLANT's 5, 2026-11-12)
REG_S_EXH1 = 20        # RM-S-BATH1
REG_S_EXH3 = 20        # RM-S-SUITEBATH
REG_A_RET1 = 5         # RM-A-STUDIO
REG_A_STUBATH_EXH = 20  # RM-A-STUBATH
REG_A_RET_STAIR = 10   # the stair-top pickup over FO-A-HALL

# --- radials: the terminals each one serves -----------------------------------------------
DU_B_ERV_R_GYM = REG_B_SUP1 + REG_B_SUP3  # carries the sauna branch
DU_B_ERV_R_PLAY = REG_B_SUP2
DU_B_ERV_R_SAUNA_SUP = REG_B_SUP3
DU_B_ERV_R_BENCH = REG_B_RET1
DU_B_ERV_R_BATH = REG_B_EXH1
DU_B_ERV_R_SAUNA_EXH = REG_B_EXH2 + REG_B_RET1  # carries the bench-valve branch

DU_M_ERV_R_LIVING = REG_M_SUP1
DU_M_ERV_R_BED = REG_M_SUP3 + REG_M_SUP1  # carries the LIVING branch
DU_M_ERV_R_STUDY = REG_M_SUP4
DU_M_ERV_R_BATH1 = REG_M_EXH1
DU_M_ERV_R_BATH2 = REG_M_EXH2
DU_M_ERV_R_LAUNDRY = REG_M_RET_STUDY + REG_M_RET3
DU_M_ERV_R_RET3 = REG_M_RET3  # its branch off LAUNDRY
DU_M_ERV_R_KITCH = REG_M_RET5
DU_M_ERV_R_MUD = REG_M_RET_MUD
DU_M_ERV_R_SUITEBATH = REG_S_EXH3

DU_A_ERV_R_BATH1 = REG_S_EXH1
DU_A_ERV_R_ATTIC = REG_A_RET1
DU_A_ERV_R_STUBATH = REG_A_STUBATH_EXH
DU_A_ERV_R_STAIR = REG_A_RET_STAIR
DU_S_ERV_HP_FEED = EQ_S_ERV_MIX

# --- trunks and risers: the legs each one gathers -----------------------------------------
# Level 2 (the RM-M-MECH plenums): 50 supply, 91 extract.
_LEVEL2_SUPPLY = DU_M_ERV_R_BED + DU_M_ERV_R_STUDY  # BED carries LIVING
DU_M_ERV_SUP_FEED = _LEVEL2_SUPPLY  # the riser's basement tee up to EQ-M-ERV-MAN-SUP
DU_M_ERV_EXH_TRUNK = (DU_M_ERV_R_BATH1 + DU_M_ERV_R_BATH2 + DU_M_ERV_R_LAUNDRY
                      + DU_M_ERV_R_KITCH + DU_M_ERV_R_MUD + DU_M_ERV_R_SUITEBATH)
DU_M_ERV_EXH_FEED = DU_M_ERV_EXH_TRUNK
# The attic plenum: the 92 System 1 feed out, 55 extract in.
_ATTIC_EXTRACT = (DU_A_ERV_R_BATH1 + DU_A_ERV_R_ATTIC + DU_A_ERV_R_STUBATH
                  + DU_A_ERV_R_STAIR)
# The chase risers carry everything above the basement plenums (142 / 146).
DU_ERV_RISER_SUP = _LEVEL2_SUPPLY + DU_S_ERV_HP_FEED
DU_ERV_RISER_EXH = DU_M_ERV_EXH_FEED + _ATTIC_EXTRACT
# The machine's own trunks and outdoor pair: the whole 210 each way.
DU_B_ERV_SUP_TRUNK = DU_ERV_RISER_SUP + DU_B_ERV_R_GYM + DU_B_ERV_R_PLAY  # GYM: sauna
DU_B_ERV_RET_TRUNK = (DU_ERV_RISER_EXH + DU_B_ERV_R_BATH
                      + DU_B_ERV_R_SAUNA_EXH)  # SAUNA-EXH carries the bench valve
DU_ERV_OA = DU_B_ERV_SUP_TRUNK
DU_ERV_EA = DU_B_ERV_RET_TRUNK

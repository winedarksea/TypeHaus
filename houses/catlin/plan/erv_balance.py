"""The ERV's 210/210 balance: one constant per terminal, every ERV leg a sum of them.

Not editable, because the legs are arithmetic. The registers (``plan/mep_registers_*.py``)
and the ducts (``plan/mep_erv_*.py``) name these constants and never a number, so a
terminal and its radial cannot disagree again: before 2026-11-06 eight legs did, BENCH and
PLANT 12 at the grille against 6/5 on the duct the static budget grades (C4 E4). The owner
took the duct split. Constant names are the element tags.

EQ-B-ERV is a BALANCED machine authored at 210 cfm, HVI-certified at 206 at 0.4" w.g.
(plan/mep_erv_types.py::EQ-T-BROAN-B210E75RT explains which number is which). Supply is
95 cfm across the six REG-*-SUP* terminals plus the 115 DU-S-ERV-HP-FEED puts into
EQ-S-ERV-MIX (2026-11-11: PLAY 30 -> 20 and STUDY 15 -> 10, the freed 15 to System 1's
return, which reaches every second-floor room). The STUDY booth now runs +5 net under
D-M-STUDY: 10 in against the 5 its return takes (``mep_registers_main.py``).

MN R403.5 asks ~188 cfm since RM-A-STUDIO became a craft room (2026-11-11, 5 bedrooms); the
machine delivers ~200 off its curve, so the 115 feed stands and the margin is banked.

A shared leg carries every terminal beyond it over its whole length, the LAUNDRY
precedent: GYM carries the sauna supply, SAUNA-EXH the bench hood, BED the living supply,
BED2 the BED1 return. A branch keeps its own terminal's constant; trunks sum the parents.

Extract is 210 on the dampers, holding every code minimum:

* The seven bathroom terminals and the sauna at 20 cfm each (IRC M1505.4.4's continuous
  local-exhaust rate): 160 cfm, untouchable, 76% of the machine.
* The other nine share 50: RM-S-PLANT 5, the workshop bench hood 6, the study return 5,
  mudroom 5, kitchen 11, laundry 3, the BED1/BED2 pickups 5 each, the attic return 5.
  BED3's 5 went to the kitchen on 2026-11-11, when BED3 took a ducted System 1 return
  (REG-S-HP-BED3-RET) instead of a long attic radial.

PLANT and the bench hood are token flows. The honest fix is a LARGER ERV, not a
redistribution; this arithmetic is true against the machine the house has.
"""

# --- supply terminals ---------------------------------------------------------------------
REG_B_SUP1 = 10        # RM-B-GYM
REG_B_SUP2 = 20        # RM-B-PLAY-N
REG_B_SUP3 = 20        # RM-B-SAUNA
REG_M_SUP1 = 20        # RM-M-LIVING
REG_M_SUP3 = 15        # RM-M-BED
REG_M_SUP4 = 10        # RM-M-STUDY-CLOSET
EQ_S_ERV_MIX = 115     # into System 1's return plenum

# --- extract terminals --------------------------------------------------------------------
REG_B_RET1 = 6         # RM-B-WORKSHOP bench hood
REG_B_EXH1 = 20        # RM-B-BATH
REG_B_EXH2 = 20        # RM-B-SAUNA
REG_M_EXH1 = 20        # RM-M-BATH1
REG_M_EXH2 = 20        # RM-M-BATH2
REG_M_RET_STUDY = 5    # RM-M-STUDY-CLOSET
REG_M_RET3 = 3         # RM-M-LAUNDRY
REG_M_RET5 = 11        # the kitchen, in RM-M-LIVING
REG_M_RET_MUD = 5      # RM-M-MUDROOM
REG_S_RET_BED1 = 5     # RM-S-BED1
REG_S_RET_BED2 = 5     # RM-S-BED2
REG_S_EXH1 = 20        # RM-S-BATH1
REG_S_EXH3 = 20        # RM-S-SUITEBATH
REG_S_EXH4 = 20        # RM-S-VANITY
REG_S_ERV_PLANT_EXH = 5  # RM-S-PLANT
REG_A_RET1 = 5         # RM-A-STUDIO
REG_A_STUBATH_EXH = 20  # RM-A-STUBATH

# --- radials: the terminals each one serves -----------------------------------------------
DU_B_ERV_R_GYM = REG_B_SUP1 + REG_B_SUP3  # carries the sauna branch
DU_B_ERV_R_PLAY = REG_B_SUP2
DU_B_ERV_R_SAUNA_SUP = REG_B_SUP3
DU_B_ERV_R_BENCH = REG_B_RET1
DU_B_ERV_R_BATH = REG_B_EXH1
DU_B_ERV_R_SAUNA_EXH = REG_B_EXH2 + REG_B_RET1  # carries the bench-hood branch

DU_M_ERV_R_LIVING = REG_M_SUP1
DU_M_ERV_R_BED = REG_M_SUP3 + REG_M_SUP1  # carries the LIVING branch
DU_M_ERV_R_STUDY = REG_M_SUP4
DU_M_ERV_R_BATH1 = REG_M_EXH1
DU_M_ERV_R_BATH2 = REG_M_EXH2
DU_M_ERV_R_LAUNDRY = REG_M_RET_STUDY + REG_M_RET3
DU_M_ERV_R_RET3 = REG_M_RET3  # its branch off LAUNDRY
DU_M_ERV_R_KITCH = REG_M_RET5
DU_M_ERV_R_MUD = REG_M_RET_MUD
DU_M_ERV_R_BED1 = REG_S_RET_BED1
DU_M_ERV_R_BED2 = REG_S_RET_BED2 + REG_S_RET_BED1  # carries the BED1 branch
DU_M_ERV_R_SUITEBATH = REG_S_EXH3
DU_M_ERV_R_VANITY = REG_S_EXH4
DU_M_ERV_R_PLANT = REG_S_ERV_PLANT_EXH

DU_A_ERV_R_BATH1 = REG_S_EXH1
DU_A_ERV_R_ATTIC = REG_A_RET1
DU_A_ERV_R_STUBATH = REG_A_STUBATH_EXH
DU_S_ERV_HP_FEED = EQ_S_ERV_MIX

# --- trunks and risers: the legs each one gathers -----------------------------------------
# Level 2 (the RM-M-MECH plenums): 45 supply, 119 extract.
_LEVEL2_SUPPLY = DU_M_ERV_R_BED + DU_M_ERV_R_STUDY  # BED carries LIVING
DU_M_ERV_SUP_FEED = _LEVEL2_SUPPLY  # the riser's basement tee up to EQ-M-ERV-MAN-SUP
DU_M_ERV_EXH_TRUNK = (DU_M_ERV_R_BATH1 + DU_M_ERV_R_BATH2 + DU_M_ERV_R_LAUNDRY
                      + DU_M_ERV_R_KITCH + DU_M_ERV_R_MUD + DU_M_ERV_R_BED2
                      + DU_M_ERV_R_SUITEBATH + DU_M_ERV_R_VANITY
                      + DU_M_ERV_R_PLANT)  # BED2 carries BED1
DU_M_ERV_EXH_FEED = DU_M_ERV_EXH_TRUNK
# The attic plenum: the 115 System 1 feed out, 45 extract in.
_ATTIC_EXTRACT = DU_A_ERV_R_BATH1 + DU_A_ERV_R_ATTIC + DU_A_ERV_R_STUBATH
# The chase risers carry everything above the basement plenums (160 / 164).
DU_ERV_RISER_SUP = _LEVEL2_SUPPLY + DU_S_ERV_HP_FEED
DU_ERV_RISER_EXH = DU_M_ERV_EXH_FEED + _ATTIC_EXTRACT
# The machine's own trunks and outdoor pair: the whole 210 each way.
DU_B_ERV_SUP_TRUNK = DU_ERV_RISER_SUP + DU_B_ERV_R_GYM + DU_B_ERV_R_PLAY  # GYM: sauna
DU_B_ERV_RET_TRUNK = (DU_ERV_RISER_EXH + DU_B_ERV_R_BATH
                      + DU_B_ERV_R_SAUNA_EXH)  # SAUNA-EXH carries the bench hood
DU_ERV_OA = DU_B_ERV_SUP_TRUNK
DU_ERV_EA = DU_B_ERV_RET_TRUNK

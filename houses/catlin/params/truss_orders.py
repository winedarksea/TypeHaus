"""The floor-truss ORDER criteria: bearing centres, loads beyond the published uniform row.

Printed on S-001's TRUSS CRITERIA block (`emit/draw/schedules/truss_criteria.py`). Every number
is worked in `notes/main_floor_truss_basis.md` §3a/§3c (FS-M-NE) and
`notes/header_spans_r602_7.md` §4b (FS-S-WEST); statics are the engine's, not typed here.
"""

from typehaus import TrussAppliedLoad, TrussOrder, inch

# FS-M-NE, TRIFORCE OJ418S at 16" o.c.: the peninsula's three line loads (872 lb dead + 300 lb of
# stool users = 1,173 lb), a patch over the box's 84" (x 303.4"..387.4", centroid 345"), and the
# fridge/freezer's ~700 lb over lines 332-380 (~175 lb a line within 2'-3" of the x=18' seat).
_PENINSULA = (inch(303.4), inch(387.4))
_FRIDGE = (inch(219), inch(246))
NE_FLOOR_TRUSS_ORDER = TrussOrder(
    bearings=(inch(217), inch(425)),
    live_psf=40.0, dead_psf=15.0,
    deflection=("L/480 LIVE (PUBLISHED ROW)", "L/720 LIVE REQUESTED"),
    loads=(
        TrussAppliedLoad(line=inch(316), plies=2, x0=_PENINSULA[0], x1=_PENINSULA[1],
                         load_lb=616.0, source="peninsula back legs, §3a: 8.85/14.25 of 991 lb"),
        TrussAppliedLoad(line=inch(332), plies=2, x0=_PENINSULA[0], x1=_PENINSULA[1],
                         load_lb=443.0, source="peninsula, pair 328.5/332 (effective 330.25): "
                                               "0.379 x 991 + 0.372 x 181"),
        TrussAppliedLoad(line=inch(348), x0=_PENINSULA[0], x1=_PENINSULA[1], load_lb=114.0,
                         source="peninsula front legs, §3a: 0.628 x 181"),
        TrussAppliedLoad(line=inch(332), plies=2, x0=_FRIDGE[0], x1=_FRIDGE[1], load_lb=175.0,
                         source="APPL-M-FRIDGE/-FREEZER, ~700 lb over four lines"),
        TrussAppliedLoad(line=inch(348), x0=_FRIDGE[0], x1=_FRIDGE[1], load_lb=175.0,
                         source="APPL-M-FRIDGE/-FREEZER"),
        TrussAppliedLoad(line=inch(364), x0=_FRIDGE[0], x1=_FRIDGE[1], load_lb=175.0,
                         source="APPL-M-FRIDGE/-FREEZER"),
        TrussAppliedLoad(line=inch(380), x0=_FRIDGE[0], x1=_FRIDGE[1], load_lb=175.0,
                         source="APPL-M-FRIDGE/-FREEZER"),
    ),
    requests=(
        "THE 40 PSF LIVE IS ON TOP OF THE PENINSULA'S DEAD MASS; THE ROW IS UNIFORM ONLY.",
        "LINES 316 AND 332 ARE DOUBLED: CONFIRM BOTH PAIRS AND THE POINT LOADS AT THEIR STATIONS.",
        "THE STOOL LOAD (300 LB AT THE STONE'S BACK EDGE) IS AN ASSUMPTION, NOT A CODE NUMBER.",
    ),
)

# FS-S-WEST, TrimJoist J12 at 16" o.c.: W-S-SN3 is a bearing wall since 2026-11-22. Its ~240 plf
# (with the attic opening trimmer) reaches the y=272 truss through the 1 1/4" LSL strip
# (x 131"..216"); the 4x4 squash block carries the trimmer's 570 lb to x = 120".
WEST_FLOOR_TRUSS_ORDER = TrussOrder(
    bearings=(inch(3.5), inch(215)),
    live_psf=40.0, dead_psf=15.0,
    max_reaction_lb=3500.0,
    deflection=("L/480 LIVE (PUBLISHED ROW)",),
    loads=(
        TrussAppliedLoad(line=inch(272), x0=inch(131), x1=inch(216), load_lb=1700.0,
                         source="W-S-SN3 ~240 plf x 85in through the LSL strip"),
        TrussAppliedLoad(line=inch(272), x0=inch(120), x1=inch(120), load_lb=570.0,
                         source="P-S-SN3-SQUASH, the attic opening trimmer's end load"),
    ),
    requests=(
        "J12 MAX REACTION 3,000 / 3,500 / 4,000 LB AT 1 3/4 / 3 1/2 / 5 1/2 IN BEARING; "
        "3 1/2 IN USED.",
        "THE LINE-272 LOADS ARE CONCENTRATED; THE ROW IS UNIFORM ONLY, SO THE SUPPLIER "
        "CARRIES THEM.",
        "THE 15 PSF DEAD COLUMN NEEDS CONFIRMING WHERE TILE SITS ON THIS HALF.",
    ),
)

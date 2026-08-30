# haus: editable
# Catlin MEP — the ERV: the machine, its outdoor side, its risers, its radial distribution.
#
# Split out of plan/mep_hvac.py (which keeps System 1's conditioned-air chase) because the
# ERV stopped being four rectangular trunks and became a system: a real machine with four
# ports, an outdoor side that did not exist before, four risers up one shaft, three
# sub-manifolds and twenty-one semi-rigid radials. mep_hvac.py was at its page budget with
# the trunks alone.
#
# =============================== WHAT CHANGED, AND WHY ================================
#
# **The machine is real now.** EQ-T-ERV was `24x24x30, 210 cfm, SRE 0.75` with two
# `# TODO verify datasheet` markers against it. It is a **Broan B210E75RT**: 210 CFM at
# 0.2" w.g., 6" round top ports, 24.8"W x 21.6"H x 21"D, MERV 8 filter, 81% SRE at 32 F and
# **65% SRE at -13 F**. EQ-B-ERV keeps its uid (IFC GlobalId stability) and its position.
#
# The SRE goes 0.75 -> 0.65 and that is a *worse* number on purpose: -15 F is this site's
# heating design temperature (plan/site.py), so the -13 F certified figure is the honest one
# for the block load. It raises the ventilation term; `mep.heating_capacity` moves with it,
# and that movement is a fact about a real machine rather than a regression.
#
# **It is a radial install, not trunk-and-branch.** Every rectangular ERV trunk is deleted.
# What replaces them is one 75 mm (~3") semi-rigid radial per terminal off a sub-manifold,
# which is the whole labour argument: no tees to cut in, no branch takeoffs to seal, no
# sheet metal to fabricate, and every terminal balanceable at the manifold rather than at
# the grille. 6 radial supplies at ~18 cfm and 15 radial extracts at 8-25 cfm each all fit
# one 75 mm run per terminal, so nothing is doubled.
#
# **The manifolds map to CAVITIES, not storeys.** This is the finding that makes the layout
# cheap. A terminal is fed from whichever floor cavity it sits in, and there are three:
#
#   1. the basement ceiling, at the ERV in RM-B-FURNACE — the six basement terminals;
#   2. RM-M-MECH, the 15 sf shaft closet — main-storey CEILING grilles *and* second-storey
#      FLOOR boots, because both open into the one FS-S-WEST/EAST cavity;
#   3. the FS-ATTIC deck at the chase head — second-storey ceiling grilles, the attic
#      pickup, and the mixing-box feed.
#
# **Routing rule, forced by the deck construction.** Every floor system in this house runs
# its bays east-west (`direction="x"`). FS-S-WEST (x 0'-18') is open-web floor truss with an
# 8 7/8" chord-to-chord opening, so a 3" radial crosses joists there freely; FS-S-EAST and
# every I-joist field cannot be crossed. So each level-2 radial goes **north-south through
# the truss webs on the west half first, then turns east along a bay** — which is exactly
# why the level-2 manifolds belong in RM-M-MECH (x 0'-6') and not somewhere central. Bays
# continue across the x=18' split at a given y, so reaching the east half is a straight ride.
#
# Hard exclusions, all of them checked: W-M-HS4 (the laundry pocket) takes nothing ever;
# FO-S-STAIR (x 10'-3 3/8"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8") blocks every FS-S bay
# between those y values across the middle of the house; FO-A-STAIR (x 21'-2"..35'-5 3/8",
# y 5'-9 5/8"..8'-9 5/8"); FS-ATTIC's trimmers at y=5'-7"/5'-9 5/8" spoil the 6'-0" bay.
#
# **One forced deviation from the port budget: REG-S-RET-BED3.** It was to be a level-2
# floor boot like BED1 and BED2. It cannot be: FO-S-STAIR blocks EVERY FS-S bay between
# y=26'-0 3/8" and y=35'-5 3/8" across x 10'-3 3/8"..17'-8 5/8", BED3 spans y 27'-36', and
# FS-S-EAST is I-joist so there is no north-south travel on the far side of the well. It is
# fed from **level 3** instead and becomes a ceiling grille rather than a floor boot — which
# for an extract is the better end of the room anyway. Nothing else moved cavity.
#
# ================================ ROUTING DECLARATIONS ================================
#
# `routing=CHASE` on the basement and attic radials is a *declaration*, not the escape hatch
# it used to be. Since 2026-08-25 a duct inside a modeled `Soffit` says so with `soffit_ref`
# and is graded by `mep.duct_soffit_occupancy`; CHASE now means only what it has always
# honestly meant — a framed shaft that is not modeled as a `Soffit`:
#   * basement: boxed under the mixed SL-M-DECK / FS-M-* ceiling, the same status as the
#     rectangular trunks these replace;
#   * attic: a boxed floor chase along the west wall at x=1'-0" carries the north-south leg
#     on the FS-ATTIC deck, and the east-west leg rides an FS-ATTIC bay. One run cannot
#     declare two cavities, and splitting a single length of semi-rigid into two elements to
#     satisfy an enum would be modelling the checker rather than the house.
# The level-2 radials are `JOIST_BAY` with `floor_ref="FS-S-WEST"` and ARE graded.

from typehaus import (
    DuctRouting,
    DuctRun,
    DuctSystem,
    Equipment,
    EquipmentKind,
    Mount,
    MountKind,
    ft,
    inch,
    pt,
)

# The catalog — the Broan, the two manifold sizes, the mixing box, the hoods and the bench
# hood — lives in plan/mep_erv_types.py. It is NOT re-exported from here: the editable
# dialect forbids `from plan import ...` (that is why plan/mep.py exists and is not
# editable), so the aggregator imports both modules and hands both to Library(...).

# ==================================== EQUIPMENT ======================================
#
# LEVEL 1 — at the machine, RM-B-FURNACE. EQ-B-ERV itself stays in plan/electrical.py with
# the rest of the equipment schedule; only its type changed. Both manifolds hang from the
# basement ceiling just south-east of it, ports down.
#
# **They are south of y=31'-6" because EQ-B-ESS-BATT's REQUIRED separation zone starts
# there** (x 49 1/4"..145 1/4", y 378"..460", off EQ-T-ESS-BATT — `advisory.ess_clearance`
# grades it with no room-or-wall exemption). The first attempt put the supply manifold at
# (7'-0", 32'-0") and the check added it to that zone's occupant list on the spot. They are
# also east of x=5'-0" to clear the ERV's own 24.8" x 21" case, and west of x=7'-6" to stay
# out of the room's north-east notch, which is the ESS closet.

EQUIPMENT_ERV_BASEMENT = [
    Equipment(uid="QGMYDXSMKH", tag="EQ-B-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(30, 6)), footprint=(inch(24), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-MANIFOLD-6",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(28, 6)), footprint=(inch(24), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-MANIFOLD-6",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
]

# LEVEL 2 — RM-M-MECH, the shaft closet (x 0'-0 5/8"..5'-11 3/8", y 33'-4 5/8"..35'-11 3/8").
# Wall-hung at 8'-0", under the 9'-0" plate.
#
# **Both manifolds are east of x=2'-8", and that is the whole siting argument.** The closet's
# west end is not free space: the four ERV risers stand at x=5"/14"/23" (y=33'-7 1/2") and
# x=5" (y=35'-6"), the six plumbing vents and the radon riser cluster at (1'-0", 34'-6"), and
# eight conduits fill x=1'-6"..2'-6" at y=34'-6"..35'-0". What is left is a 39" x 31" bay
# along the closet's east end, and that is exactly where these hang.
#
# The supply manifold is the smaller because the main storey wants three fresh outlets while
# the extract side gathers eight wet and dry pickups off TWO storeys — the main storey's
# ceiling grilles and the second storey's floor boots open into one floor cavity, which is
# the finding that put a manifold here at all.
EQUIPMENT_ERV_MAIN = [
    Equipment(uid="NTBY655GF8", tag="EQ-M-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(3, 10), ft(34)), footprint=(inch(24), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-MANIFOLD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
    Equipment(uid="9D1KYBNJ12", tag="EQ-M-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(4, 4), ft(35)), footprint=(inch(34), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-MANIFOLD-10",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
]

# LEVEL 3 — sitting ON the FS-ATTIC deck beside the chase head at (1', 34'-6"), fully
# accessible in RM-A-POCKET.
#
# ** THE MANIFOLD MOVED x 2'-6" -> 5'-0" ON 2026-08-29, AND M1305.1.3 IS WHY. ** At 6:12 off
# a rafter plate the roof underside is `1 1/2" + x/2`, so its old station had 16 1/2" of
# clearance — the 8"-deep box fits, but the code wants a PASSAGEWAY not less than 30" high to
# reach it and a level working space in front. 5'-0" gives 31 1/2" at the box and 46 1/2" at
# the far side of a 30" working space, so a person can crawl to it and kneel at it. The four
# radials below each gained 2'-6" of run to the x=1'-0" chase head and nothing else changed. Extract only: the level's fresh-air duty is the mixing-box feed,
# which stays a full-size 6" branch off the supply riser rather than a radial, because it
# carries ~100 of the machine's 210 cfm on its own.
EQUIPMENT_ERV_ATTIC = [
    Equipment(uid="3QT1F3F01A", tag="EQ-A-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(5), ft(34, 6)), footprint=(inch(24), inch(8)),
              # RM-A-POCKET since 2026-08-29: the west loft became a guest studio and this
              # end of it was walled off as a storage pocket. The manifold did not move —
              # the room around it did, and D-A-POCKET is a door rather than a scuttle
              # precisely so this stays serviceable.
              room="RM-A-POCKET", type_ref="EQ-T-ERV-MANIFOLD-6",
              mount=Mount(kind=MountKind.FLOOR)),
]

# THE MIXING BOX — inside SF-S-DUCT, and where it sits was decided by
# `mep.duct_soffit_occupancy` rather than by arithmetic in a comment.
#
# The plan wanted it directly behind REG-S-HP-RET at (20'-8", 9'-8"). It does not go there.
# The box's clear cavity is 30 3/4" wide and, reading south to north, y 6'-0"..9'-7" is
# EQ-S-HP1-AH's 21" case, y 9'-10"..10'-8" is EQ-S-HP1-STRIP's 16" plate, and DU-S-HP-SUP
# holds x 18'-9"..19'-11" for the length of the box. What is left for a 10"-wide box is
# x 20'-1"..21'-3 3/8" (2" clear of the trunk, inside the cavity's east face) at any y north
# of the strip heater's 10'-8". So it sits at (20'-8", 11'-4"), eighteen inches north of
# where the plan put it, and the check prints the clearances instead of this comment.
EQUIPMENT_ERV_SECOND = [
    Equipment(uid="8PE9E87JX5", tag="EQ-S-ERV-MIX", kind=EquipmentKind.MIXING_BOX,
              position=pt(ft(20, 8), ft(11, 4)), footprint=(inch(10), inch(12)),
              room="RM-S-HALL", type_ref="EQ-T-ERV-MIXING-BOX",
              soffit_ref="SF-S-DUCT",
              mount=Mount(kind=MountKind.CEILING)),
]

# THE TWO EXTERIOR HOODS — north gable, mirrored about the x=18'-0" ridge.
#
# This is the plan's stated fallback, taken deliberately after the preferred west-wall pair
# failed on its own terms. Every arrangement that keeps both hoods on the main storey near
# the shaft fails IRC M1602.2's ten feet: RM-M-MECH is 5'-11" x 2'-7", so its north wall and
# its west wall are 4'-8" apart corner to corner, and carrying one hood south down the west
# facade means running a 6" insulated duct through 2x6 walls that have a 5 1/2" cavity.
# Against that, the gable costs ~30 ft of insulated riser each way and buys:
#   * 20'-0" of separation (x=8'-0" and x=28'-0", mirrored about the ridge — 12'/24' until
#     2026-08-29, when FO-A-HALL opened the deck under the OA hood's old station);
#   * 25'-10" above grade, which is not a snow question at all — the main-storey rim band
#     the plan warned about is only 20"-34" above grade and was rightly rejected;
#   * distance from EQ-M-HP3-OD's slot at (11'-3 5/8", 37'-4 5/8") and from the garage
#     4'-0" north of it, both of which are ground-level conditions;
#   * distance from VR-M-RADON-VENT, which terminates above the roof at the chase.
# The mirror about x=18'-0" is what the facade rules ask of a gable (houses/catlin/CLAUDE.md),
# and it is the reason these two are paired at all rather than sitting nearer each other.
EQUIPMENT_ERV_HOODS = [
    Equipment(uid="0NF97ZR9Z3", tag="EQ-A-ERV-HOOD-OA", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(8), ft(35, 6)), footprint=(inch(12), inch(12)),
              # ** MOVED 12'-0" -> 8'-0" ON 2026-08-29, AND THE MOVE IS THE POINT. ** At
              # x=12'-0" this hood stood INSIDE FO-A-HALL's plan footprint, with DU-ERV-OA
              # running 2'-0" west at +276" over a 10'-deep open well and no deck to service
              # either from. The house's outdoor-air INTAKE cannot live over a shaft.
              #
              # 8'-0" puts it back over the pocket's deck, reachable from D-A-POCKET, and it
              # KEEPS THE FACADE RULE that put the pair at 12'/24' in the first place: the
              # mirror about x=18'-0" holds because 8 + 28 = 36. IRC M1602.2's 10'-0"
              # intake/discharge separation goes from 12'-0" to 20'-0" — better, not merely
              # preserved. It costs +4'-0" on this duct and -4'-0" on the other: a wash.
              #
              # The cheap alternative — strut the duct off the rafters and leave the hood
              # where it was — is genuinely cheaper today and leaves this house's fresh-air
              # intake permanently over an open well. It was rejected on those terms.
              room="RM-A-POCKET", type_ref="EQ-T-ERV-HOOD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(3))),
    Equipment(uid="38M0D2FNXH", tag="EQ-A-ERV-HOOD-EA", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(28), ft(35, 6)), footprint=(inch(12), inch(12)),
              # Mirrored to 28'-0" with the OA hood's move to 8'-0" — the pair keeps its
              # mirror about x=18'-0" (8 + 28 = 36) and gains 8'-0" of M1602.2 separation.
              room="RM-A-EAST-UNFIN", type_ref="EQ-T-ERV-HOOD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(3))),
]

# ====================================== RISERS =======================================
#
# Four 6" round risers up the radon/plumbing chase at (1', 34'-6") — the house's one
# continuous basement-to-attic shaft: RM-M-MECH's floor on main, the 2'-9" x 2'-2 1/8" notch
# walled by W-S-CH-W/W-S-CH-S in RM-S-BATH1's NW corner on second, out onto the attic deck.
#
# **MEASURED, not assumed** (the plan said to measure before committing). The notch's clear
# is x 0 5/8"..30 3/4" by y 33'-3 1/8"..35'-11 3/8" — 30 1/8" wide by 32 3/8" deep. It already
# carries six plumbing vents and VR-M-RADON-VENT clustered at (1'-0", 34'-6"), and eight
# conduits between x=1'-6" and x=2'-6" at y=34'-6"..35'-0". Four 6" ducts with R-8 wrap are
# ~8" OD each; four in a row is 32" and does NOT fit the 30 1/8", so they go three-and-one:
# a row of three at y=33'-7 1/2" (x=5", 14", 23" — 1" between them, 1" off the west face,
# 3 3/4" off the east) and the fourth at (5", 35'-6"), in the free north strip, 6" clear of
# the vent cluster and well east of nothing. Total fill including the vents and the conduits
# is ~25% of the shaft's section. It fits; it is not roomy, and **nothing else should be
# added to this chase**. The fallback the plan named — a framed shaft in RM-M-MECH's dead
# corner — is not needed, and the closet's own dead corner is now the manifolds' instead.
#
# The supply and extract risers run the full height, basement manifolds to attic manifold.
# The outdoor-air and exhaust-air risers run the same way because their hoods are in the
# north gable; see EQUIPMENT_ERV_HOODS above for why.
#
# Filed on the MAIN storey so their authored elevations read as project-frame numbers
# directly (the main datum is 0'-0"). -19 7/16" is the basement manifolds' port level;
# +244" is 4" above the attic deck, the centreline of a 6" duct lying on it; +276" is the
# gable hoods' centreline, 3'-0" above that deck. Each of the two outdoor runs carries its
# hood-side vertex OUTSIDE the north wall (y=36'-6") rather than stopping at the inside face:
# `mep.erv_outdoor_terminals` decides which EXHAUST run is the machine's discharge by asking
# whether its last vertex lands outside every resolved room, which is the same probe
# `code.M1502_dryer_exhaust` uses for M1502.3 and is a fact about the geometry rather than a
# naming convention.
DUCTS_ERV_RISERS = [
    # ** IT STOPS UNDER THE DECK NOW (2026-08-30), AND ONLY THIS ONE DOES. ** +244" is the
    # centreline of a 6" duct lying on the attic deck, and it is right for the three risers
    # that surface east of x=11 1/2" — but this column is at x=0'-5", where the 6:12 underside
    # is 4" above that deck. A 6" duct cannot come up there; it was 1.4" proud of the rafters
    # and `integrity.element_above_roof` said so. So the riser tops out on FS-ATTIC's bottom
    # chord instead (231 7/8" = the deck less 8 7/8", the same datum DU-S-ERV-HP-FEED already
    # uses) and its feed jogs the 7" east in the bay before standing up — the move
    # VR-M-RADON-VENT makes for the same reason, in the same shaft, at the same rake.
    #
    # Moving the column east instead was the other option and it is not available: the chase's
    # measured clear is 30 1/8" and the three-in-a-row at x=5"/14"/23" already fills it.
    DuctRun(uid="1BMFGSMKJY", tag="DU-ERV-RISER-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(0, 5), ft(33, 7.5)), pt(ft(0, 5), ft(33, 7.5))),
            elevations=(inch(-19.4375), inch(231.875)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            insulation="R-8 wrap", design_cfm=210),
    DuctRun(uid="GFTW5CBARX", tag="DU-ERV-RISER-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(1, 2), ft(33, 7.5)), pt(ft(1, 2), ft(33, 7.5))),
            elevations=(inch(244), inch(-19.4375)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            insulation="R-8 wrap", design_cfm=210),
    # The outdoor side, which did not exist at all before this pass. Both legs carry
    # outdoor-temperature air through conditioned space, so both are insulated AND vapour
    # sealed — an uninsulated intake duct sweats all winter and rains on whatever is under
    # it, which here would be RM-S-BATH1's ceiling and RM-B-FURNACE's electrical.
    #
    # Authored hood-end first for the intake and hood-end last for the discharge:
    # `mep.erv_outdoor_terminals` reads an OUTDOOR_AIR run from its hood inward and an
    # EXHAUST run outward to its hood, which is the direction the air goes and the direction
    # a plan reader traces.
    # Follows EQ-A-ERV-HOOD-OA from x=12'-0" to x=8'-0" (2026-08-29). Its west leg at
    # y=35'-6" now runs x 1'-11"..8'-0", entirely over RM-A-POCKET's deck — it used to start
    # at x=12'-0", inside FO-A-HALL, which put 2'-0" of 6" insulated duct at +276" over a
    # 10'-deep open well with nothing to service it from. +4'-0" of duct, and DU-ERV-EA
    # gives 4'-0" back.
    # ** REROUTED 2026-08-30 — IT WAS DRAWN INSIDE THE EXHAUST TRUNK. ** Its west leg ran
    # x 8'-0"..1'-11" at y=35'-6" and +276", which is the SAME LINE, the SAME y and the SAME
    # elevation DU-ERV-EA takes east out of the chase: six feet of the house's outdoor-air
    # INTAKE and its discharge occupying one 6" cylinder. Nothing caught it — `interference`
    # grades framing, not ducts, and `mep.erv_outdoor_terminals` reads each run end to end
    # without asking what the other one is doing. Both were also proud of the 6:12 rake, and
    # fixing that is what put the two routes side by side where the clash was visible.
    #
    # It leaves the chase on the deck now and stays there, taking its OWN y — the riser's own
    # y=33'-7 1/2" — east to x=8'-0" before turning north to the hood. Nothing crosses: it
    # meets DU-ERV-EA's line once, at (8'-0", 35'-6"), and passes 12" clear UNDER it because
    # the exhaust trunk is still climbing there (see below). +4" is the same "6" duct lying on
    # the attic deck" centreline the risers are dimensioned to, and it is what the rake allows:
    # the underside is `20'-0" + 1 1/2" + x/2`, so a duct on the deck needs x >= 11 1/2" and
    # this leg never goes west of 1'-11".
    DuctRun(uid="MW0MY7GDME", tag="DU-ERV-OA", system=DuctSystem.OUTDOOR_AIR,
            path=(pt(ft(8), ft(36, 6)), pt(ft(8), ft(35, 6)), pt(ft(8), ft(33, 7.5)),
                  pt(ft(1, 11), ft(33, 7.5)), pt(ft(1, 11), ft(33, 7.5))),
            elevations=(inch(276), inch(276), inch(4), inch(4), inch(-19.4375)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
    # Follows EQ-A-ERV-HOOD-EA from x=24'-0" to x=28'-0" — the mirror move, and the -4'-0"
    # that makes the pair's relocation a wash. This run DOES still cross the void band at
    # y=35'-6", and that is fine where the OA hood's station was not: it rides at +276",
    # 6" off the north gable for its whole length, so it straps to gable framing rather than
    # spanning open air, and nothing has to be reached from a deck that is no longer there.
    # ** IT NO LONGER STANDS UP INSIDE THE CHASE, AND IT DUCKS THE OA HOOD (2026-08-30). **
    # It used to rise at x=0'-5" straight to +276" and run east from there. Neither half
    # survived the 6:12 rake: at x=5" the roof underside is 4" above the deck, so a 6" duct
    # cannot surface there at all, and the high leg was 33" proud of the rafters until it
    # reached x=5'-7". It climbs with the rake instead — out of the chase on the deck at
    # x=1'-11" (11 1/2" is the minimum a deck-laid 6" duct needs), up to +18" by the OA hood
    # and to full height at 10'-0", where the underside is 5'-1 1/2" and the trunk has a foot
    # to spare. From there east it is the run it always was: +276", 6" off the north gable, so
    # it straps to gable framing across FO-A-HALL rather than spanning open air.
    #
    # +18" at x=8'-0" is not a rounding — it is what clears EQ-A-ERV-HOOD-OA. That hood is a
    # 12" box centred on +276" at (8'-0", 35'-6"), i.e. it OCCUPIES this trunk's old line.
    # Passing under it keeps both hoods at 3'-0" and so keeps the north gable's mirror about
    # x=18'-0" (houses/catlin/CLAUDE.md), which dropping the OA hood instead would have broken.
    DuctRun(uid="BYAVBJKRS6", tag="DU-ERV-EA", system=DuctSystem.EXHAUST,
            path=(pt(ft(1, 11), ft(35, 6)), pt(ft(1, 11), ft(35, 6)), pt(ft(8), ft(35, 6)),
                  pt(ft(10), ft(35, 6)), pt(ft(28), ft(35, 6)), pt(ft(28), ft(36, 6))),
            elevations=(inch(-19.4375), inch(4), inch(18), inch(276), inch(276), inch(276)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
]

# ============================== LEVEL 1 — BASEMENT RADIALS ============================
#
# Six 75 mm radials off the two manifolds beside the machine, boxed under the basement
# ceiling. Centreline at 7'-6" above the basement floor, inside the manifolds' own 7'-2"
# to 7'-10" band and clear of the 8'-0 15/16" underside.
#
# REG-B-SUP2's radial is the short one on purpose. The play room's whole ceiling is
# SL-M-DECK's 14 3/8" solid concrete with NO cavity at all, so every foot of that run is
# surface-mounted; entering at the room's west edge and stopping just inside cuts about
# eight feet of exposed duct off the old (27', 27') position. It still throws away from
# FURN-B-PLAY-TV on the east wall.
DUCTS_ERV_BASEMENT = [
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(6, 6), ft(10, 6.6)), pt(ft(18, 10.4), ft(10, 6.6))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=18),
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(19), ft(30, 6)), pt(ft(19), ft(26))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=30),
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(6, 6), ft(8, 9)), pt(ft(9, 9.8125), ft(8, 9)),
                  pt(ft(9, 9.8125), ft(8, 9))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(7)),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=12),
    # The bench hood's pull. It drops out of the ceiling chase to the hood face at 5'-6",
    # which is the vertical leg that makes it a capture hood rather than a ceiling diffuser.
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(2), ft(28, 6)), pt(ft(2), ft(8, 6)),
                  pt(ft(2), ft(8, 6))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(6, 2)),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=25),
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(11, 8), ft(28, 6)), pt(ft(11, 8), ft(20))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=20),
    # The sauna's low pickup is 4" off the floor on the south liner, so this radial runs the
    # length of the room in the ceiling chase and then drops seven feet down the wall. The
    # drop is drawn — a repeated plan point at two elevations — which it could not be before
    # `DuctRun` carried elevations.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(9, 4.5), ft(28, 6)), pt(ft(9, 4.5), ft(1, 4)),
                  pt(ft(9, 4.5), ft(1, 4))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), inch(4)),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=20),
]

# ================= LEVEL 2 — RM-M-MECH RADIALS (FS-S-WEST JOIST BAY) =================
#
# Twelve 75 mm radials, all `JOIST_BAY` against FS-S-WEST and all graded by
# `mep.duct_joist_bay`. Each has the same three moves and no others:
#
#   1. rise out of its own manifold port at 8'-4" above the main floor, straight up into the
#      bay field overhead;
#   2. run SOUTH down its own lane — one lane per radial, at the port's own x, so no two
#      share a line — crossing the open truss webs, which is legal because the chord-to-chord
#      opening is 8 7/8" and these are 3";
#   3. turn east or west along ONE bay centre to its terminal.
#
# **FILED ON THE SECOND STOREY, NOT THE MAIN ONE, AND THAT IS NOT COSMETIC.** These ducts run
# in FS-S-WEST's cavity, which is the second storey's floor and the main storey's ceiling.
# `resolve/mep_ducts.py::_containing_floor` matches a segment to a sibling FloorSystem *on
# the duct's own storey*, so a run filed on `main` with `floor_ref="FS-S-WEST"` gets graded
# against FS-M-WEST's joist lines instead — which sit on a different 16" phase, so every
# radial reported a straddle it did not have. Elevations are therefore second-relative:
# -20" is the manifold port at 8'-4" above the main floor, -10 3/8" is the centreline of a
# 3" duct sitting on FS-S-WEST's bottom chord at 108 1/8".
#
# Bay centres are 8" + n*16". **Two of them are unusable and the check is what said so:**
# FO-S-STAIR's trimmers land at y=26'-0 3/8" and y=35'-5 3/8", so a 3" duct centred on the
# 26'-0" or 35'-4" bay straddles one. The extract manifold therefore sits at y=35'-0" rather
# than 35'-4", and everything that would naturally have used the 26'-0" bay uses 24'-8".
#
# HONEST LIMITS, both real and neither graded by anything:
#   * The twelve lanes leave the closet on 4" centres — 3" ducts with an inch between them.
#     That is what the neck of a radial bundle looks like coming off a pair of manifolds in a
#     6'-0" closet, and they stay on those centres all the way south rather than fanning out,
#     because a lane is a straight line in this model and a bundle is not.
#   * Two pairs share part of one bay: STUDY and LAUNDRY both ride 20'-8" east of x=4'-8",
#     and BATH1/VANITY/KITCH all turn on 24'-8". A 14 1/2" clear bay holds two 3" ducts side
#     by side without argument; nothing in the engine grades duct-against-duct outside a
#     modeled Soffit, so this note is the only record that it was looked at. The STUDY/
#     LAUNDRY overlap grew on 2026-08-30 — they now share the 20'-8" bay from x=4'-8" to
#     x=15'-0" rather than parting at x=10'-6" — and it is still two tubes in one bay.
_PORT_Z = inch(-20)
_BAY_Z = inch(-10.375)

DUCTS_ERV_LEVEL2 = [
    DuctRun(uid="MRH0QZT6NN", tag="DU-M-ERV-R-LIVING", system=DuctSystem.SUPPLY,
            path=(pt(ft(3, 2), ft(34)), pt(ft(3, 2), ft(34)), pt(ft(3, 2), ft(12, 8)),
                  pt(ft(27), ft(12, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=20),
    DuctRun(uid="83MA15Q308", tag="DU-M-ERV-R-BED", system=DuctSystem.SUPPLY,
            path=(pt(ft(3, 10), ft(34)), pt(ft(3, 10), ft(34)), pt(ft(3, 10), ft(6)),
                  pt(ft(9), ft(6))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=15),
    # ** IT ENDED IN A WALL FOR ONE DAY AND IS A CEILING RUN AGAIN (2026-08-30). ** The
    # 2026-08-29 version dropped a riser into W-M-LS for a 5'-0" sidewall supply; the owner
    # paired RM-M-STUDY with a LOW extract instead (DU-M-ERV-R-LAUNDRY below), which is what
    # makes a ceiling supply work in a 148 cf box, and asked for this one back overhead by
    # ED-M-STUDY-SPOT. So the riser point and the -60" elevation are gone and the run is
    # four points again, the shape every other level-2 ceiling radial has.
    #
    # ** IT RIDES THE 20'-8" BAY 3'-10" FURTHER EAST THAN IT EVER HAS, AND THAT COSTS
    # NOTHING BECAUSE IT IS THE SAME BAY. ** FS-S-WEST's joist lines are at 8" + n*16", so
    # the terminal's 20'-8" sits between the joists at 20'-0" and 21'-4" for the whole ride
    # from x=4'-6" to x=17'-2" — no jog, no crossing, one straight length of semi-rigid.
    # Stopping short of the joist at 21'-4" is also why the grille cannot sit on the
    # sconce's own 21'-5" line; the argument is on REG-M-SUP4 in plan/mep_registers.py.
    DuctRun(uid="2ZZ3MF5VAF", tag="DU-M-ERV-R-STUDY", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 6), ft(34)), pt(ft(4, 6), ft(34)), pt(ft(4, 6), ft(20, 8)),
                  pt(ft(17, 2), ft(20, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=15),
    DuctRun(uid="K04AT15S97", tag="DU-M-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(3), ft(35)), pt(ft(3), ft(35)), pt(ft(3), ft(24, 8)),
                  pt(ft(1, 2), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=20),
    DuctRun(uid="B13Y04D9BP", tag="DU-M-ERV-R-VANITY", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 4), ft(35)), pt(ft(3, 4), ft(35)), pt(ft(3, 4), ft(24, 8)),
                  pt(ft(3), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=20),
    DuctRun(uid="YEXGZK2KW2", tag="DU-M-ERV-R-KITCH", system=DuctSystem.RETURN,
            path=(pt(ft(3, 8), ft(35)), pt(ft(3, 8), ft(35)), pt(ft(3, 8), ft(24, 8)),
                  pt(ft(20, 10.7), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=8),
    DuctRun(uid="DPAS57TPCG", tag="DU-M-ERV-R-BATH2", system=DuctSystem.EXHAUST,
            # Three points, not four: this lane's x IS the terminal's, so the run rises and
            # goes straight south with no turn at the end. A fourth vertex repeating the
            # third would be a zero-length segment, and the sweep and the IFC emitter both
            # (correctly) drop one — which is a silent disagreement between the authored
            # path and the exported geometry, so it is not authored.
            path=(pt(ft(4), ft(35)), pt(ft(4), ft(35)), pt(ft(4), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=20),
    DuctRun(uid="63W84CCNE4", tag="DU-M-ERV-R-SUITEBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(4, 4), ft(35)), pt(ft(4, 4), ft(35)), pt(ft(4, 4), ft(19, 4)),
                  pt(ft(14), ft(19, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=20),
    # ** THE ONE TWO-HEADED RADIAL IN THE HOUSE (2026-08-30), AND THE PORT BUDGET IS WHY.
    # ** RM-M-STUDY asked for a stale-air pickup. It could not have its own lane:
    # EQ-M-ERV-MAN-EXH is an EQ-T-ERV-MANIFOLD-10 and all TEN of its ports are spoken for —
    # BATH1, VANITY, KITCH, BATH2, SUITEBATH, LAUNDRY, MUD, BED1, BED2, PLANT. There is no
    # -12 in the catalog, and the closet bay these hang in is 39" x 31" already holding a
    # 24" box and a 34" one, so a second extract manifold is not a thing that fits either.
    # The owner's own suggestion is the answer: give one radial two heads.
    #
    # ** REG-M-RET3 IS NOW A MID-RUN TAP, NOT THE END OF THE LANE. ** It sits on the fourth
    # vertex and the run carries on past it to RM-M-STUDY. Physically that is a two-port
    # grille plenum — the standard radial fitting, one spigot to the grille and one through
    # — not a sheet-metal tee cut into a trunk, so it costs a box and no fabrication.
    #
    # ** OF THE THREE PICKUPS THAT COULD HAVE SHARED, THE LAUNDRY IS THE RIGHT ONE, AND THE
    # REASON IS ACOUSTIC. ** DU-M-ERV-R-BATH2 already dead-ends at (4'-0", 18'-0") and would
    # have reached the study's wall along the 18'-0" bay with no jog at all — a shorter,
    # simpler route. It is the wrong one: a shared duct is a crosstalk path in both
    # directions, and the room at this end of it is a CALL BOOTH. RM-M-BATH2 is occupied and
    # wants privacy of its own; RM-M-LAUNDRY is a 4'-3" closet behind a door, unoccupied,
    # and taking a 5 cfm trickle. Fifteen feet of 3" semi-rigid and four bends to a laundry
    # closet is the cheapest neighbour this booth could have been given.
    #
    # ** THE FLOW IS WHAT CAPS THE STUDY AT 10 cfm. ** 5 + 10 = 15 cfm on the shared length,
    # ~25 m3/h, comfortably inside a 75 mm tube's ~30 m3/h. The room is 15 cfm supply / 10
    # extract on purpose (booth stays positive — see REG-M-RET-STUDY), but the headroom to
    # take it to a balanced 15/15 later is only about 2 cfm, not 5. Anything past that is a
    # second lane, and there is no port for one.
    #
    # ** AND IT IS ALREADY AT THE SMALLEST SIZE THERE IS HERE. ** The owner asked whether a
    # small room could take a smaller duct: every radial in this house is one 75 mm SKU
    # already. The step below it (51 mm) would put 10 cfm at ~450 fpm in a tube ten inches
    # from a seated occupant's feet, against ~200 fpm at 75 mm — in the one room built to be
    # quiet, downsizing is the expensive direction.
    #
    # Route: east along the 20'-8" bay to the laundry head, on east to x=15'-0", SOUTH
    # across the joists at 20'-0" and 18'-8" — legal and graded, FS-S-WEST is open-web floor
    # truss with an 8 7/8" chord-to-chord opening — then east along the 18'-0" bay, which is
    # a bay centre AND sits directly over W-M-CLN2's staggered cavity, so the last point is
    # a pure riser into the wall. x=15'-0" for the crossing is 3'-0" clear of the trusses'
    # east bearing at W-M-C2/C3, well out of the end panels; -108" is storey-relative on the
    # `second` datum (+10'-0"), i.e. 12" above the main floor.
    DuctRun(uid="ANSKB7EGDH", tag="DU-M-ERV-R-LAUNDRY", system=DuctSystem.RETURN,
            path=(pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(20, 8)),
                  pt(ft(10, 6), ft(20, 8)), pt(ft(15), ft(20, 8)), pt(ft(15), ft(18)),
                  pt(ft(16, 6), ft(18)), pt(ft(16, 6), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z,
                        inch(-108)),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=15),
    DuctRun(uid="YFDV1TGN1W", tag="DU-M-ERV-R-MUD", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(35)), pt(ft(5), ft(35)), pt(ft(5), ft(31, 4)),
                  pt(ft(4, 0.4), ft(31, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=8),
    DuctRun(uid="164777V9JK", tag="DU-M-ERV-R-BED1", system=DuctSystem.RETURN,
            path=(pt(ft(5, 4), ft(35)), pt(ft(5, 4), ft(35)), pt(ft(5, 4), ft(14)),
                  pt(ft(29), ft(14))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=5),
    DuctRun(uid="2QHYF71DBS", tag="DU-M-ERV-R-BED2", system=DuctSystem.RETURN,
            path=(pt(ft(5, 8), ft(35)), pt(ft(5, 8), ft(35)), pt(ft(5, 8), ft(22)),
                  pt(ft(29), ft(22))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=5),
    # THE PLANT ROOM'S EXTRACT, MOVED DOWN HERE FROM THE ATTIC MANIFOLD 2026-08-29 (it was
    # DU-A-ERV-R-PLANT, and before that DU-S-PLANT-EXH; it keeps the uid through both moves).
    #
    # ** IT LEFT THE ATTIC BECAUSE ITS DECK CHASE BECAME A BEDROOM. ** Off EQ-A-ERV-MAN-EXH it
    # ran the x=1'-0" chase 21'-8" down the base of RM-A-STUDIO's west knee wall — the last duct
    # on that wall, and the whole reason the wall needed a shoe. Down here it never enters the
    # attic at all.
    #
    # ** THE TRUSSES ARE WHY THIS WORKS AND FS-ATTIC IS WHY IT DID NOT. ** Both floors span x,
    # so a north-south run crosses every joist in either — but FS-S-WEST is 11 7/8" OPEN-WEB
    # TRUSS, chosen (params/second_deck.py) precisely "so every second-floor plumbing stack,
    # supply riser and the radon/plumbing chase can cross the deck through the webs instead of a
    # soffit or chase". FS-ATTIC is I-joist, where the same crossing means ~16 bored webs, all
    # of them within a foot of the joists' west bearing, which is the one place the hole chart
    # does not allow.
    #
    # ** THE x=2'-10" LANE IS CHOSEN, NOT INHERITED. ** Going south there crosses exactly ONE
    # sibling radial (DU-M-ERV-R-BATH1's westward leg at y=24'-8", x 1'-2"..3'-0"). The obvious
    # lane at the manifold's east end, x=6'-0", would have crossed EIGHT. It is the tenth and
    # LAST free port on EQ-M-ERV-MAN-EXH, which is now full at 10 of 10.
    #
    # East leg at y=4'-8" (56" = 8 + 3 x 16, a bay centre) runs ALONG the trusses and is clear
    # of everything: no sibling radial reaches south of y=6'-0" except DU-M-ERV-R-BED, which
    # terminates at (9'-0", 6'-0").
    #
    # ** IT STAYS A HIGH TERMINAL, WHICH IS THE POINT THE 2026-08-18 NOTE ARGUED. ** Humid air
    # stratifies, so the wettest air in RM-S-PLANT is the air overhead. The grille cannot be in
    # the ceiling any more — this duct is below the room now, not above it — so it rises inside
    # W-S-C1 and discharges at 8'-6", six inches under the 9'-0" ceiling. W-S-C1 is
    # PLANT_INT_2X6_BRG_HUMID at 7.43": a 5 1/2" cavity, room for a 75 mm riser AND a
    # vapour-tight boot through the liner. W-S-PS1, the room's north wall, is 2x4 and is not.
    #
    # ** IT IS LONGER, NOT SHORTER: 55'-8" against the attic route's 47'-5". ** 45'-6" of plan
    # run plus a 9'-4" rise from the truss bottom chord to the grille, which is the part an
    # eyeballed estimate misses. That is affordable and it is worth saying why: HVI certifies
    # this machine at 206 cfm net supply at 0.4" w.g. (B210E75RT, HVI 2004940), so the "0.2"
    # w.g." this file quotes elsewhere is the model-name point off the fan curve, not the rating
    # point, and the real static budget is about double what those comments assume. This is
    # still the radial whose drop the installer must check — 25 cfm, and longest again now.
    # -20" is the manifold port, -10 3/8" a 3" duct on the truss bottom chord.
    DuctRun(uid="CWMB7Q4E3W", tag="DU-M-ERV-R-PLANT", system=DuctSystem.EXHAUST,
            path=(pt(ft(2, 10), ft(35)), pt(ft(2, 10), ft(35)),
                  pt(ft(2, 10), ft(4, 8)), pt(ft(18), ft(4, 8)),
                  pt(ft(18), ft(4, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, inch(102)),
            diameter=inch(3), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="semi_rigid", design_cfm=25),
]

# ============================== LEVEL 3 — ATTIC RADIALS ==============================
#
# Four runs off the deck manifold at (2'-6", 34'-6"): three extracts and, separately below,
# the mixing-box feed. Each takes the boxed floor chase west to x=1'-0" and south along the
# west wall, then drops into its FS-ATTIC bay and rides it east to the terminal. `CHASE`,
# for the reason in the header — one run, two cavities, and the declaration is the honest
# one. FS-ATTIC is I-joist, so unlike level 2 there is no crossing the bays: all the
# north-south travel happens ON the deck, above the joists, where it costs nothing in DEPTH.
#
# ** THAT LAST CLAUSE NEEDED AMENDING ON 2026-08-29, AND THEN THE THING IT WAS APOLOGISING FOR
# WAS MOSTLY REMOVED. ** The x=1'-0" chase now runs the length of a FINISHED BEDROOM, and the
# first version of that chase carried DU-S-ERV-HP-FEED's 6" beside a 3" for 21'-8" along the
# base of a 5'-0" knee wall — roughly 12" wide by 8-9" tall, about 22 sf of the studio's 357,
# and wide enough to swallow the west wall's receptacle band. The answer then was to box it as
# a bench (FURN-A-STUDIO-PLINTH) whose `work_surface=False` broke the 210.52 wall line.
#
# ** THE 6" DID NOT HAVE TO BE THERE, AND THE BENCH IS GONE WITH IT. ** DU-S-ERV-HP-FEED turns
# east one bay sooner (y=22'-0") and reaches SF-S-DUCT down RM-A-EAST-UNFIN's deck instead —
# same developed length, and the exposed run moved from a guest bedroom to an unfinished loft.
# DU-A-ERV-R-STUBATH's east leg went into the y=19'-4" bay in the same pass, where it travels
# ALONG the joists and bores nothing. The knee wall then carried ONE 75 mm duct for a few hours,
# and now carries none — see the next paragraph. ED-A-STUDIO-RC8/RC9 stay: the wall is in the
# 210.52 test on its own merits whatever is or is not lying at its foot.
#
# ** AND THEN THE LAST ONE LEFT TOO, SO THE KNEE WALL IS BARE. ** This block used to say
# DU-A-ERV-R-PLANT could not move, on the grounds that feeding it from FS-S-WEST's trusses would
# turn its ceiling grille into a floor boot and give up the stratification argument. That was
# half right: the duct did move down to the trusses (it is DU-M-ERV-R-PLANT in DUCTS_ERV_LEVEL2
# now), but the terminal did NOT become a floor boot — it rises inside W-S-C1's 5 1/2" cavity to
# a HIGH SIDEWALL grille at 8'-6", six inches under the ceiling, still in the warm wet air at the
# top of the room. The argument was about height, not about which direction the boot arrives
# from. What is left on the studio's west knee wall is nothing at all.
#
# The remaining rejected alternative is unchanged: bore the FS-ATTIC I-joists and run
# north-south in the bays. The hole chart permits it, but at x=1'-0" every hole would fall
# within a foot of the joists' west bearing, which is the one place the chart does not — and
# that is before ~16 bored webs and a manufacturer sign-off.
#
# +4" is a 3" duct lying on the attic deck at 240"; -10 3/8" is its centreline sitting on
# FS-ATTIC's bottom chord at 228 1/8". Both are attic-relative, and negative because the
# attic datum is the deck top.
_ATTIC_DECK_Z = inch(4)
_ATTIC_BAY_Z = inch(-10.375)

DUCTS_ERV_ATTIC = [
    DuctRun(uid="4YT114ADP3", tag="DU-A-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(32, 8)),
                  pt(ft(1), ft(32, 8)), pt(ft(5), ft(32, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=20),
    # THE ATTIC'S OWN PICKUP WAS TWO FEET FROM THE MANIFOLD AND NEVER LEFT THE DECK. It does
    # now, and the reason is a wall rather than a duct: REG-A-RET1's terminal ended up inside
    # the walled storage pocket on 2026-08-29, extracting a guest bedroom's air through a
    # closed door. Both moved to the studio's NW corner together.
    #
    # It takes the x=1'-0" chase south past W-A-STU-N to the boot at (1'-0", 20'-8"). It had two
    # companions there, DU-A-ERV-R-PLANT and DU-S-ERV-HP-FEED; both left on 2026-08-29 and this
    # run's 1'-7" inside the studio is now most of what is left of that chase. All of it is ON
    # the deck: FS-ATTIC is I-joist, so there is no crossing bays here and the north-south travel
    # costs nothing in depth. Developed length goes from ~4' to about 15' — still the shortest
    # radial on this manifold, so it takes nobody's pressure headroom.
    DuctRun(uid="DYNQDC9ZMJ", tag="DU-A-ERV-R-ATTIC", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(20, 8)),
                  pt(ft(1), ft(20, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, inch(-2)),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=9),
    # THE GUEST BATH'S EXTRACT, added 2026-08-29 with the bath. Same chase south to y=19'-0",
    # then east on the deck to the W-A-STU-W axis at x=9'-7 1/2" and UP inside that wall's
    # 5 1/2" staggered cavity to REG-A-STUBATH-EXH at 7'-0". The rise is the whole reason the
    # terminal is a wall grille rather than a floor boot: this room follows the roof and has no
    # ceiling plenum, and the wet wall is the only chase between a high pickup and the deck.
    #
    # 20 cfm continuous, matching every other bath terminal in the house — and small enough
    # that the extra run costs the machine nothing measurable.
    #
    # ** ITS EAST LEG USED TO LIE ON THE DECK AND THAT WAS WRONG. ** From x=1'-0" to the wet
    # wall it crossed 8'-7" of RM-A-STUDIO's floor at y=19'-0" — a duct laid across the middle
    # of a bedroom, not against a knee wall where the rest of the chase at least has a rake to
    # hide under. It rides the FS-ATTIC bay instead, which costs nothing: the leg runs EAST, and
    # FS-ATTIC's I-joists span x, so travelling east is travelling ALONG a bay. Nothing is bored.
    #
    # y moved 19'-0" -> 19'-4" (232" = 8 + 14 x 16) to land on a bay centre, and
    # REG-A-STUBATH-EXH moved the same 4" with it so the riser still meets its grille. 19'-4" is
    # well inside RM-A-STUBATH (y 17'-4 3/4" .. 22'-3 3/8"), and it is a different bay from the
    # one PR-A-STUBATH-DRAIN takes at 20'-8", so the two do not share a cavity.
    DuctRun(uid="WCH6Z4DZX0", tag="DU-A-ERV-R-STUBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(19, 4)),
                  pt(ft(1), ft(19, 4)), pt(ft(9, 7.5), ft(19, 4)),
                  pt(ft(9, 7.5), ft(19, 4))),
            # ** THE RISER TOP FOLLOWED ITS GRILLE DOWN ON 2026-08-30. ** It stood at 84"
            # while REG-A-STUBATH-EXH moved to 4'-4" on 2026-08-29 — the register was
            # corrected and the duct that feeds it was not, so 32" of 3" duct rose past its
            # own boot and out through the rake, which at x=9'-7 1/2" is 4'-11 1/4" above the
            # deck. `integrity.element_above_roof` named it (24.6" proud); nothing else could,
            # because `mep.register_duct_match` grades the pair in plan and they agree there.
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z, inch(52)),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid",
            design_cfm=20),
    # RM-S-BED3's extract, forced up here by FO-S-STAIR — see the header. It becomes a ceiling
    # grille rather than a floor boot, which for stale air is the better end of the room anyway.
    #
    # ** REROUTED 2026-08-29, AND THERE IS NO WAY ROUND THE NORTH. ** Its bay leg crossed
    # x 10'..18' at y=31'-4", and FO-A-HALL now spans that whole band to the north gable —
    # FO-A-HALL's maxy IS W-A-N2's inside gwb face, so the strip between the void and the wall
    # is wall, not deck. EVERY west-to-east route north of the studio is severed.
    #
    # So it goes down the x=1'-0" chase to y=22'-0" (264" = 8 + 16 x 16, a bay centre, and below
    # W-A-STU-N's sole plate so the partition is irrelevant), east under the studio floor to
    # x=29', then north on the east loft's deck to the existing grille, which does not move.
    # ** 32'-8" -> ~53'-6", and for a few days that made it the longest radial in the house. **
    # It is not any more: DU-M-ERV-R-PLANT went to 55'-8" on 2026-08-29 when it moved down to the
    # FS-S-WEST trusses. Length was never the criterion anyway — BED3 carries 5 cfm (~102 fpm in
    # 75 mm, where 21 extra feet costs hundredths of an inch w.g.), while PLANT carries 25 cfm and
    # is the run whose drop the installer must check. Note the two are no longer even on the same
    # machine port: BED3 is on EQ-A-ERV-MAN-EXH, PLANT on EQ-M-ERV-MAN-EXH. The alternative —
    # re-filing BED3 onto the main-storey manifold — is still blocked by FO-S-STAIR, which is what
    # pushed it up here in the first place, and that manifold is now full at 10 of 10.
    DuctRun(uid="73FJZH564X", tag="DU-A-ERV-R-BED3", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(22)),
                  pt(ft(1), ft(22)), pt(ft(29), ft(22)),
                  pt(ft(29), ft(22)), pt(ft(29), ft(31, 4))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z,
                        _ATTIC_DECK_Z, _ATTIC_DECK_Z),
            diameter=inch(3), routing=DuctRouting.CHASE, material="semi_rigid", design_cfm=5),
]

# THE MIXING-BOX FEED — the one place fresh air enters the heat-pump loop, and the last of
# plans/TODO.md's undrawn verticals to close.
#
# It keeps DU-S-ERV-HP-FEED's tag and uid, and nothing else: the run it replaces tapped a
# joist-bay trunk at y=12'-8" that no longer exists, and its rise into the soffit was undrawn
# because `DuctRun` had nowhere to put an elevation. It now comes off the supply riser's head
# on the attic deck, takes the boxed floor chase south, rides the FS-ATTIC bay at y=11'-4"
# east, and **drops into SF-S-DUCT** onto the mixing box — a drop that is drawn, swept, and
# billed at its developed length.
#
# 6" and not a 75 mm radial: ~100 of the machine's 210 cfm goes through here, which is half
# the house's fresh air arriving in one place, and a radial would run it at ~5,000 fpm.
# -8 7/8" is a 6" duct on FS-ATTIC's bottom chord; -20 7/8" is a 6" duct on SF-S-DUCT's clear
# underside at 216 1/8".
#
# ** REROUTED 2026-08-29 SO IT NEVER ENTERS THE GUEST STUDIO, AND IT COST NOTHING. ** It used
# to run the x=1'-0" deck chase south all the way to y=11'-4" — 10'-11" of 6" duct along the
# base of a finished bedroom's knee wall, and the single item that set that chase's SECTION.
# Everything else on that wall is 75 mm.
#
# It now turns east one bay sooner, in **y=22'-0"** — the same bay DU-A-ERV-R-BED3 takes, and
# for the same reason: 264" = 8 + 16 x 16 is a bay centre, it sits under W-A-STU-N's sole plate
# so the partition is irrelevant, and it is the last bay south of FO-A-HALL, which severs every
# west-to-east route north of it. From x=20'-8" it rises back onto RM-A-EAST-UNFIN's deck and
# runs south to the same SF-S-DUCT drop it always used. An UNFINISHED loft is where a 6" duct
# lying on a deck belongs.
#
# ** THE DEVELOPED LENGTH IS UNCHANGED — 11'-7" comes off the west leg and 10'-8" goes onto the
# east one. ** So this is not a trade of pressure for joinery: the machine sees the same run,
# and DU-M-ERV-R-PLANT (25 cfm) remains the radial whose drop the installer must check.
DUCTS_ERV_MIX_FEED = [
    DuctRun(uid="CSDV02AAAA", tag="DU-S-ERV-HP-FEED", system=DuctSystem.SUPPLY,
            # ** ITS FIRST 7" WENT INTO THE BAY ON 2026-08-30. ** It came off the riser head
            # on the deck at x=0'-5", under 4" of roof. It picks the riser up on FS-ATTIC's
            # bottom chord instead and stands up at x=1'-0", where the underside is 7 1/2"
            # and a bare 6" duct on the deck clears by 1/2". The 7" east is ALONG a bay —
            # FS-ATTIC's I-joists span x — so nothing is bored; the north-south leg that
            # follows stays on the deck for exactly that reason, as it always has.
            path=(pt(ft(0, 5), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)),
                  pt(ft(1), ft(22)),
                  pt(ft(1), ft(22)), pt(ft(20, 8), ft(22)),
                  pt(ft(20, 8), ft(22)), pt(ft(20, 8), ft(11, 4)),
                  pt(ft(20, 8), ft(11, 4))),
            elevations=(inch(-8.875), inch(-8.875), inch(4), inch(4),
                        inch(-8.875), inch(-8.875),
                        inch(4), inch(4), inch(-20.875)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            design_cfm=100),
]

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
# `# TODO verify datasheet` markers against it. It is a **Broan B210E75RT**: 6" round top
# ports, 24.8"W x 21.6"H x 21"D, MERV 8 filter, 81% SRE at 32 F and **65% SRE at -13 F**.
# EQ-B-ERV keeps its uid (IFC GlobalId stability) and its position.
#
# ** THE RATING POINT IS 206 CFM AT 0.4" W.G., NOT 210 AT 0.2" (corrected 2026-09-01). **
# HVI certifies this machine at 206 cfm net supply at 0.4" w.g. (B210E75RT, HVI ID 2004940)
# — see the note at DU-S-ERV-R-PLANT below, which had it right. "210 CFM at 0.2 in. w.g." is
# the model-name point off the fan curve; it is where the number in the model number comes
# from, not where the machine is certified. Every comment in this file that treated 0.2" as
# the rating point was therefore assuming HALF the static budget the design actually has,
# which is the direction that hides a problem rather than inventing one.
# `ventilation_cfm=210` stays authored — see plan/mep_erv_types.py for why moving it is a
# separate decision with a live verdict behind it.
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
# carries ~100 of the machine's 210 authored cfm on its own (206 certified — see the header).
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

# THE MIXING BOX — now inside SF-S-HP1, in the return chamber at the air handler's return
# face, which is the one place in this loop where fresh air may legally arrive.
#
# ** IT MOVED FROM (20'-8", 11'-4") TO (24'-1", 1'-9") ON 2026-08-30, AND THE OLD SPOT
# WAS A REAL DEFECT. ** Reading south to north inside SF-S-DUCT the order used to be: air
# handler y 6'-0"..9'-7", trunk head 9'-7", return grille 9'-8", strip heater 9'-10"..10'-8",
# mixing box 11'-4". So 100 cfm of -15 F design outdoor air — half the house's fresh air —
# was injected DOWNSTREAM of both the coil and the 2 kW strip heater and reached the rooms
# untempered. It landed there because `mep.duct_soffit_occupancy` pushed it 18" north of
# where the plan wanted it: a packing outcome in a box the placeholder air handler had
# already filled, not intent. With the machine in SF-S-HP1 the return chamber is a real
# chamber, and the box sits in it, upstream of the coil, the strip heater and the unit's own
# filter-back grille.
#
# ** IT WAS ALSO NEARLY DELETED, AND THE BACKDRAFT DAMPER IS WHY IT IS STILL HERE. ** The
# element looks like a fitting once the return is a proper plenum, and a wye would do. It
# would not. `plan/mep_registers.py` has said since 2026-07-30 that the ERV enters the return
# "not a hard-coupled duct … so either machine can run alone", and this box is where that
# damper lives:
#   * AIR HANDLER RUNNING, ERV OFF — the return chamber is at negative pressure. With no
#     damper the blower pulls backwards through the 6" feed, through the attic sub-manifold
#     and out through a stopped, therefore non-recovering, ERV core and its outdoor intake.
#     A stopped ERV is not airtight. That is unrecovered -15 F air straight into the return,
#     plus depressurisation of the ERV's own ductwork.
#   * ERV RUNNING, AIR HANDLER OFF — 100 cfm enters a still chamber and leaves through
#     REG-S-HP-RET into the study, the only low-resistance path. The house still ventilates;
#     distribution to the other rooms depends on the AH fan turning. That was true of the old
#     design too and it wants a CONTROLS INTERLOCK (blower continuous, or on ERV call), which
#     the schema has no field for — so it is written here and in plans/TODO.md. It matters
#     because code.N1103_6_whole_house_ventilation is already tight, 210 cfm provided against
#     203 required. (At the 206 cfm HVI actually certifies, tighter still: 206 against 203.
#     That is the live verdict `ventilation_cfm` moves, and why the field is left at 210
#     pending a deliberate decision — see plan/mep_erv_types.py.)
# Keeping it costs the second lane past the machine, which SF-S-HP1's width already carries.
#
# x=24'-1" is the box's east lane, shared with DU-S-ERV-HP-FEED's tail: the 10" case stands
# 7/8" inside the cavity's east face and clear of the 10x6 south-branch riser lane. y=1'-9"
# puts it IN the return chamber — the 19" of SF-S-HP1 south of the cabinet — level with
# REG-S-HP-RET at the far side of it, 22" west. So the fresh air enters at one end of the
# chamber, the room air at the other, and the two mix across its width before they turn
# north into the machine's return face. Nothing about that is packing: everything upstream
# of the coil is upstream of the strip heater too, which is the whole reversal.
EQUIPMENT_ERV_SECOND = [
    Equipment(uid="8PE9E87JX5", tag="EQ-S-ERV-MIX", kind=EquipmentKind.MIXING_BOX,
              position=pt(ft(24, 1), ft(1, 9)), footprint=(inch(10), inch(12)),
              room="RM-S-STUDY2", type_ref="EQ-T-ERV-MIXING-BOX",
              soffit_ref="SF-S-HP1",
              mount=Mount(kind=MountKind.CEILING)),
]

# THE TWO EXTERIOR HOODS — west facade at the NW chase, stacked, exhaust over intake.
#
# ** BOTH HOODS CAME OFF THE NORTH GABLE ON 2026-08-30, AND THE GABLE ROUTE WAS A REAL
# DEFECT, NOT A PREFERENCE. ** DU-ERV-EA's 18'-0" horizontal leg at +23'-0" passed squarely
# through the rough openings of BOTH gable windows — WIN-A-N1 (x 10'-9"..13'-3") and
# WIN-A-N2 (x 22'-9"..25'-3"), each sill +22'-0", head +25'-0". An 8" OD wrapped duct
# centred on +23'-0" spans 22'-8"..23'-4": 8" above the sill, 100% inside the glass, across
# 2'-6" of each unit. WIN-A-N1 is the only window daylighting FO-A-HALL's double-height
# stair void (storeys/attic.py), so the duct crossed it 13'-0" above the second-storey hall,
# in full view. Nothing in the engine grades a run against an opening; see `run_through_opening`.
#
# The second half of the defect is that this leg was never "6 inches off the north gable"
# as the old note here claimed. That figure measured to the SHEATHING. Against the finished
# face it is 0.63": at y=35'-6" the 8" envelope takes 4.00" of a 5 1/2" stud cavity, eats
# the 0.625" gwb layer, and stands 3.37" proud into the room. It could not be closed in.
#
# The two claims that had kept the pair on the gable both fail on measurement, and
# houses/catlin/CLAUDE.md carries the argument: RM-M-MECH is 5'-3" x 1'-11" and not the
# 5'-11" x 2'-7" quoted (room polygons run 6" past an exterior wall's interior face), and the
# "20"-34" above grade" figure is the 13 7/16" RIM BAND, not the 10'-0" wall. The ten-foot
# separation was the real obstacle and it was only ever tested horizontally.
#
# 13'-0" of rise clears `mep.erv_outdoor_terminals`' 10'-0" on 3-D distance alone, and
# IRC M1506.3 independently waives the ten feet "where the exhaust opening is located not
# less than 3 feet above the air intake opening". EXHAUST ON TOP is therefore not arbitrary
# and must stay: the plume rises away from the intake. The 9" y-offset is only so the two are
# not perfectly co-axial; it is not what makes the pair legal.
#
# The west face is blank at the chase on both storeys (W-M-W1B, W-S-W1B carry no openings)
# and faces the open west yard rather than the 3'-8" breezeway slot the north face discharges
# into. Both hoods stay south of TR-RF-LEADER-W, the roof leader at y=35'-6".
#
# A 6" duct with R-8 wrap is ~8" OD against a 5 1/2" stud cavity, so NEITHER hood may turn and
# travel inside the wall — each is a straight through-wall penetration, wrap terminated at the
# wall line, flashed curb through the PBR-26 cladding, on the outer girt. That is the one part
# of the old west-facade objection that stands, and it only bites a run travelling ALONG the
# facade. Coming straight out of the chase, neither does.
EQUIPMENT_ERV_HOODS_MAIN = [
    Equipment(uid="0NF97ZR9Z3", tag="EQ-M-ERV-HOOD-OA", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(inch(6), ft(33, 11)), footprint=(inch(12), inch(12)),
              # The intake, and it is the LOW one deliberately: an exhaust plume rises, so
              # the intake belongs under it, not over it. +4'-0" on the main storey is
              # 6'-10" above the -2'-10" grade plane — twice `erv_terminals`' 36" rule of
              # thumb, and clear of any drift a 50 psf ground-snow site puts against a wall.
              # 25'-11" from VR-M-RADON-VENT against a 3'-0" minimum.
              room="RM-M-MECH", type_ref="EQ-T-ERV-HOOD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(4))),
]
EQUIPMENT_ERV_HOODS_SECOND = [
    Equipment(uid="38M0D2FNXH", tag="EQ-S-ERV-HOOD-EA", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(inch(6), ft(34, 8)), footprint=(inch(12), inch(12)),
              # The discharge, 13'-0" over the intake. Filed on `second`, so this mount
              # elevation is storey-relative: +7'-0" on a datum of +10'-0" is +17'-0" in the
              # project frame. Inside, it is the second-storey chase notch in RM-S-BATH1's
              # NW corner, which is capped at +19'-0" — a hood box centred on +17'-0" clears
              # that by 1'-6".
              # room=None deliberately, the way EQ-M-HP3-OD and the porch AP are authored.
              # The notch is walled off from RM-S-BATH1 by W-S-CH-W and W-S-CH-S, so it is
              # not part of that room's polygon and naming it raises
              # `integrity.placeable_room_mismatch`. This hood's inside face is in a chase,
              # not in a room, and the model should say so rather than pick the nearest name.
              room=None, type_ref="EQ-T-ERV-HOOD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
]

# ====================================== RISERS =======================================
#
# Four 6" round risers up the radon/plumbing chase at (1', 34'-6") — the house's one
# continuous basement-to-attic shaft: RM-M-MECH's floor on main, the 2'-9" x 2'-2 1/8" notch
# walled by W-S-CH-W/W-S-CH-S in RM-S-BATH1's NW corner on second, out onto the attic deck.
#
# ** RE-MEASURED 2026-08-30, AND THE OLD FIGURE WAS 6" TOO GENEROUS ON EVERY EXTERIOR FACE. **
# This note used to read "x 0 5/8"..30 3/4" by y 33'-3 1/8"..35'-11 3/8" — 30 1/8" wide by
# 32 3/8" deep", and both numbers were taken off ROOM polygons. `resolve/rooms.py` polygonizes
# from wall AXES and insets only by the lining, and these walls are `face("sheathing-ext")`,
# so their axis IS the sheathing exterior: 6" of exterior-wall stud was being counted as shaft
# on each such face. Against the resolved wall LAYERS the notch is
# **x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8" — 24" wide by 26 1/8" deep.**
#
# That matters, because the three-in-a-row below was arithmetic against the wrong west face.
# Three 8" OD ducts on 9" centres need 25" and the shaft has 24": **DU-ERV-RISER-SUP at x=0'-5"
# is 5 5/8" inside W-M-W1B / W-S-W1B's stud cavity for its whole height**, and the row is one
# inch over. That is a real, live defect and it is NOT fixed here — it belongs to the two
# risers that still run the full height, and moving either of them is its own pass. It is
# written down so the next person does not re-derive the 30 1/8" and conclude it fits.
#
# The 2026-08-30 hood move made the shaft materially emptier, which is what makes the above
# tractable rather than urgent. DU-ERV-OA now stops at the main storey and DU-ERV-EA at the
# second, so the four-in-a-shaft problem exists only below main; above the second storey the
# shaft carries two ducts, not four. DU-ERV-EA's own riser moved off y=35'-6" — which was
# inside the NORTH wall's stud cavity by 4 5/8" — to y=34'-8".
#
# The shaft also carries six plumbing vents and VR-M-RADON-VENT clustered at (1'-0", 34'-6"),
# and eight conduits between x=1'-6" and x=2'-6" at y=34'-6"..35'-0". It is not roomy, and
# **nothing else should be added to this chase**. The fallback the plan named — a framed shaft
# in RM-M-MECH's dead corner — is not needed, and the closet's own dead corner is now the
# manifolds' instead.
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
    # measured clear is 24" (see the note above — it is not the 30 1/8" this used to cite)
    # and the three-in-a-row at x=5"/14"/23" already over-fills it by an inch.
    # ** BOTH RISERS NOW REACH THE MANIFOLD THEY WERE ALWAYS DESCRIBED AS SERVING
    # (2026-09-01). ** Until this pass each stopped dead at -19 7/16" in the chase — the
    # basement manifolds' port level, and nothing else about the point — while this file's
    # own note above said "basement manifolds to attic manifold". The manifolds are at
    # x 5'-6"..7'-6", 61" and 73" of plan away, and the horizontal leg between was never
    # drawn. `mep.duct_connectivity` is the check that says so out loud now; it could not
    # have, before its equipment test grew an elevation band, because both ends "landed on"
    # EQ-M-ERV-HOOD-OA — the gable hood 67" above them, sharing a plan point the way anything
    # in one chase does.
    #
    # THE SUPPLY LEG GOES ROUND THE NORTH of EQ-B-ERV: east at y=31'-8", which is 3 1/2"
    # clear of the machine's north face (y=376 1/2") and stops at x=5'-10", 2" short of
    # RM-B-ESS's x=6'-0" wall, then south into EQ-B-ERV-MAN-SUP's west end. The room's other
    # two through-routes are both taken — x=6'-6" is DU-B-ERV-R-GYM and -SAUNA-SUP's shared
    # lane for the whole depth of the basement, and y=30'-6" east of the manifold is
    # DU-B-ERV-R-PLAY's.
    #
    # THE EXTRACT LEG DROPS TO -27" FIRST, and that is the only reason these two do not
    # collide: it has to cross the supply leg's y=31'-8" lane to get south, and 6" ducts on
    # 7 9/16" centres do not share a crossing. -27" puts 1 5/8" between the two envelopes,
    # keeps 79 3/8" of headroom under it — over R305.1.1's 76" basement projection floor —
    # and rises back to the port level over the 46" of its east run, a 9 degree rake, rather
    # than jogging at the manifold. It reaches EQ-B-ERV-MAN-EXH from the NORTH at x=5'-10"
    # because the manifold's own west approach along y=28'-6" is DU-B-ERV-R-BENCH's.
    DuctRun(uid="1BMFGSMKJY", tag="DU-ERV-RISER-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(5, 10), ft(30, 6)), pt(ft(5, 10), ft(31, 8)),
                  pt(ft(0, 5), ft(31, 8)), pt(ft(0, 5), ft(33, 7.5)),
                  pt(ft(0, 5), ft(33, 7.5))),
            elevations=(inch(-19.4375), inch(-19.4375), inch(-19.4375),
                        inch(-19.4375), inch(231.875)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            insulation="R-8 wrap", design_cfm=210),
    DuctRun(uid="GFTW5CBARX", tag="DU-ERV-RISER-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(1, 2), ft(33, 7.5)), pt(ft(1, 2), ft(33, 7.5)),
                  pt(ft(1, 2), ft(29, 3)), pt(ft(5, 0), ft(29, 3)),
                  pt(ft(5, 10), ft(29, 3)), pt(ft(5, 10), ft(28, 8))),
            elevations=(inch(244), inch(-27), inch(-27), inch(-19.4375),
                        inch(-19.4375), inch(-19.4375)),
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
    # ** BOTH OUTDOOR LEGS STOP AT THE NW CHASE NOW (2026-08-30). ** They used to climb the
    # full 24'-6" to the north gable; see EQUIPMENT_ERV_HOODS_* above for why that route was
    # a defect and not merely long. Each is now a riser out of the basement manifold and one
    # straight penetration through the west wall: the intake at +4'-0" on the main storey,
    # the discharge at +17'-0" on the second. -53 LF of R-8 wrapped 6" duct between them.
    #
    # The x=-0'-6" hood vertex on each is NOT decoration. `mep.erv_outdoor_terminals` decides
    # which EXHAUST run is the machine's discharge by asking whether the run's LAST vertex
    # lands outside every resolved room's `clear_face` — and `clear_face` sits on the wall
    # AXIS, which for these `face("sheathing-ext")` walls is x=0'-0", not the cladding at
    # x=-0'-7 1/4". A hood run that stopped at the interior face would still read as indoors,
    # the check would find no discharge at all, the 10-ft test would never run, and the whole
    # thing would degrade silently to a single PASS on hood height. -6" is outside the axis.
    DuctRun(uid="MW0MY7GDME", tag="DU-ERV-OA", system=DuctSystem.OUTDOOR_AIR,
            # Hood first, then inward and down to the basement manifold. The riser keeps its
            # x=1'-11" station in the shaft; only the top of it changed. y=33'-11" puts the
            # horizontal leg 5 5/8" north of RM-M-MECH's south face and 8'-0" under the two
            # wall-hung manifolds at +8'-0", so it crosses nothing in a 5'-3" x 1'-11" room.
            path=(pt(inch(-6), ft(33, 11)), pt(inch(6), ft(33, 11)),
                  pt(ft(1, 11), ft(33, 11)), pt(ft(1, 11), ft(33, 7.5)),
                  pt(ft(1, 11), ft(33, 7.5)), pt(ft(1, 11), ft(32, 6)),
                  pt(ft(3, 8), ft(32, 6)), pt(ft(3, 8), ft(31, 1)),
                  pt(ft(3, 8), ft(31, 1))),
            elevations=(inch(48), inch(48), inch(48), inch(48), inch(-27),
                        inch(-27), inch(-27), inch(-27), inch(-33.8375)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
    DuctRun(uid="BYAVBJKRS6", tag="DU-ERV-EA", system=DuctSystem.EXHAUST,
            # Manifold first, hood last — the direction the air goes, and the direction
            # `erv_outdoor_terminals` reads an EXHAUST run.
            #
            # ** THE RISER MOVED OFF y=35'-6", WHICH WAS INSIDE THE NORTH WALL. ** The real
            # shaft clear is x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8" — 24" x 26",
            # not the figure this file used to carry, which counted
            # 6" of exterior-wall stud as shaft on each measured face. At y=35'-6" this
            # riser's 8" envelope stood 4 5/8" inside W-M-N3B / W-S-N3B's stud cavity for its
            # whole height. y=34'-8" is 9" clear of the shaft's north face.
            path=(pt(ft(4, 7), ft(31, 1)), pt(ft(4, 7), ft(31, 1)),
                  pt(ft(4, 7), ft(34, 8)), pt(ft(1, 11), ft(34, 8)),
                  pt(ft(1, 11), ft(34, 8)), pt(inch(-6), ft(34, 8))),
            elevations=(inch(-33.8375), inch(-27), inch(-27), inch(-27),
                        inch(204), inch(204)),
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
    # ** THE MACHINE'S OWN TWO TRUNKS, DRAWN 2026-09-01. ** EQ-B-ERV had no duct to either
    # manifold — the six radials below started at boxes that nothing fed. No check could say
    # so: `mep.duct_connectivity` grades duct ENDS, and a manifold with nothing arriving at it
    # has no end to orphan. Both are 6", the machine's full 210 cfm, and both leave its top.
    #
    # THE SUPPLY TRUNK IS THE SIMPLE ONE: straight up 14 3/8" off the port to the radial
    # layer at 7'-6", then 19" east into EQ-B-ERV-MAN-SUP's west half at y=30'-4". It stays
    # 2" south of the manifold's own y=30'-6" centre so DU-B-ERV-R-PLAY's lane east of
    # x=6'-6" is untouched.
    #
    # THE RETURN TRUNK CANNOT GO STRAIGHT, and the reason is DU-B-ERV-R-BENCH: that radial
    # runs the whole width of the room at y=28'-6", which fences EQ-B-ERV-MAN-EXH off from
    # the machine at the 7'-6" layer. It leaves the manifold's east end at x=7'-0", drops to
    # 6'-10 7/16", crosses UNDER the x=6'-6" radial lane — the one DU-B-ERV-R-GYM and
    # -SAUNA-SUP share for the depth of the basement — and comes back west at y=29'-9",
    # 1 5/8" clear of the layer above it and 6 13/16" over the machine's case.
    DuctRun(uid="225MZ1YDWB", tag="DU-B-ERV-SUP-TRUNK", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 9), ft(30, 4)), pt(ft(4, 9), ft(30, 4)),
                  pt(ft(6, 4), ft(30, 4))),
            elevations=(inch(75.6), inch(90), inch(90)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            design_cfm=210),
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(ft(7), ft(28, 8)), pt(ft(7), ft(28, 8)),
                  pt(ft(7), ft(29, 9)), pt(ft(3, 8), ft(29, 9)),
                  pt(ft(3, 8), ft(29, 9))),
            elevations=(inch(90), inch(82.4375), inch(82.4375), inch(82.4375),
                        inch(75.6)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            design_cfm=210),
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
    # ** THE EAST JOG IS GONE (2026-08-30) AND THE RUN IS ~2'-6" SHORTER. ** REG-M-RET-STUDY
    # moved 16'-6" -> 14'-6" to get out from under FURN-M-STUDY-DESK-LEAF's stowed envelope
    # (the argument is on the register), and the old path only ran east to x=15'-0" and then
    # doglegged back to reach 16'-6". At 14'-6" the radial turns south once and drops: one
    # corner instead of three, on a two-headed run whose whole risk is accumulated bend loss.
    # The crossings are unchanged in kind — south from the 20'-8" bay still cuts the joists at
    # 20'-0" and 18'-8", legal because FS-S-WEST is open-web with an 8 7/8" chord opening —
    # and the drop is now 3'-6" further from those trusses' east bearing at W-M-C2/C3, not
    # nearer. -108" is storey-relative on the `second` datum (+10'-0"), i.e. 12" above the
    # main floor.
    DuctRun(uid="ANSKB7EGDH", tag="DU-M-ERV-R-LAUNDRY", system=DuctSystem.RETURN,
            path=(pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(20, 8)),
                  pt(ft(10, 6), ft(20, 8)), pt(ft(14, 6), ft(20, 8)), pt(ft(14, 6), ft(18)),
                  pt(ft(14, 6), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z,
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
    # ** THE RISER STOOD IN A DOORWAY UNTIL 2026-08-30, AND NOTHING GRADED IT. ** It came up
    # at (18'-0", 4'-8"), which is the CLEAR OPENING of D-S-PLANT: that door is centred on
    # y=4'-0" in W-S-C1 with its jacks at y=2'-8 1/4" and y=5'-3 3/4", so y=4'-8" is 7" inside
    # the north jamb. The run therefore did three impossible things in a row — through the
    # bearing wall's sole plate, then 78 1/2" of bare 3" duct standing free in the rough
    # opening with nothing to strap it to and the leaf swinging through it, then a 3" bore
    # through a solid 2-ply 2x8 header. `mep.duct_joist_bay` PASSED it and even printed the
    # station twice in its R302.11 fire-blocking list, because it grades the bay and never
    # asks what the riser stands in.
    #
    # The fix is one bay north, and it is nearly free. y=7'-4" (88" = 8 + 5 x 16) is a truss
    # bay centre AND a stud bay centre in the same wall — the coincidence this file already
    # leans on at y=4'-8" — so the duct rides the bay east and stands up between the studs at
    # y=80" and y=96", clear of the door's kings at 65 1/4" and of ED-S-PLANT-SW one bay
    # south. **It is 2'-8" SHORTER**, 53'-0" against 55'-8".
    #
    # Every argument the 2026-08-29 pass made survives intact: still W-S-C1, still the 5 1/2"
    # PLANT_INT_2X6_BRG_HUMID cavity that takes both the riser and a vapour-tight boot, still
    # a high sidewall terminal at 8'-6" for the stratification reason above. The supply/extract
    # throw across the room improves slightly, 11'-0" to 11'-7 1/2".
    #
    # The alternative bay, y=2'-0" south of the door, is 2'-8" LONGER and lands the riser in
    # the same stud bay as ED-S-PLANT-SW-TIMER's gasketed box — a 3" duct and a 2 1/2" box in
    # a 5 1/2" cavity is zero clearance, and no check in the engine grades duct against device.
    #
    # There is no legal riser at y=4'-8" at all: the jacks, the full-width header and the one
    # cripple at y=49" between them leave no station in the opening, so jogging inside the
    # cavity at +8'-6" does not rescue it either. The register had to move with the riser.
    DuctRun(uid="CWMB7Q4E3W", tag="DU-M-ERV-R-PLANT", system=DuctSystem.EXHAUST,
            path=(pt(ft(2, 10), ft(35)), pt(ft(2, 10), ft(35)),
                  pt(ft(2, 10), ft(7, 4)), pt(ft(18), ft(7, 4)),
                  pt(ft(18), ft(7, 4))),
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
# 6" and not a 75 mm radial: ~100 of the machine's 210 authored cfm goes through here (206
# certified — see the header), which is half the house's fresh air arriving in one place, and
# a radial would run it at ~5,000 fpm.
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
            # ** THE TAIL FOLLOWED THE MIXING BOX SOUTH ON 2026-08-30. ** Every attic leg
            # above, and the drop at (20'-8", 11'-4"), are UNCHANGED — the machine sees the
            # same 6" run to the same point. What is new is the 12'-2" that continues from
            # there: south inside SF-S-DUCT beside the 18x8 trunk (18 + 2 hanger gap + 6 = 26
            # against 30 3/4" clear, which is the whole reason the trunk went to 18x8 and not
            # 20x8), across the y=7'-6" seam into SF-S-HP1, east at y=5'-5 1/2" — the
            # band between the air handler's discharge plenum and ST-S2A's lowest stringer,
            # which is the only place in the box where a 6" duct may cross all three
            # lanes — and south down the east lane onto EQ-S-ERV-MIX at (24'-1", 1'-9").
            # It cannot pass the machine on the west: the cabinet is 43 1/2" wide in a
            # 72 3/4" cavity, so x=20'-8" runs straight through it, and only the east third
            # of the box is a lane. Nothing rides RM-A-STUDY's finished floor.
            #
            # ** THE JOG MAY NOT MOVE SOUTH. ** Since 2026-08-31 it clears the north edge of
            # DU-S-HP-SOUTH-RISE's take-off leg and EQ-S-HP1-STRIP's plate by 1 1/8" — the
            # tightest joint in this box, and one `mep.duct_soffit_occupancy` will not
            # report, because it compares a pair's clearance ACROSS the box and this one is
            # separated ALONG it. North it may go if something ever needs the room; south it
            # may not.
            #
            # One elevation the whole way, -24 7/8" (215 1/8" absolute): 6" above SF-S-HP1's
            # cavity floor, which came down 4" when the box went from a 17" drop to 21" for
            # the FLEXX Ultra cabinet. It was -20 7/8" against the old floor for the same 6".
            # A step would buy nothing.
            path=(pt(ft(0, 5), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)),
                  pt(ft(1), ft(22)),
                  pt(ft(1), ft(22)), pt(ft(20, 8), ft(22)),
                  pt(ft(20, 8), ft(22)), pt(ft(20, 8), ft(11, 4)),
                  pt(ft(20, 8), ft(11, 4)),
                  pt(ft(20, 8), ft(5, 5.5)),
                  pt(ft(24, 1), ft(5, 5.5)),
                  pt(ft(24, 1), ft(1, 9))),
            elevations=(inch(-8.875), inch(-8.875), inch(4), inch(4),
                        inch(-8.875), inch(-8.875),
                        inch(4), inch(4), inch(-24.875),
                        inch(-24.875), inch(-24.875), inch(-24.875)),
            # `routing` stays CHASE: the legs above are a boxed floor chase and a run on an
            # unfinished deck, and CHASE keeps its honest meaning for a shaft that is not a
            # modeled Soffit. `soffit_ref` names SF-S-HP1 so the tail's two segments in that
            # box ARE graded by `mep.duct_soffit_occupancy` against the derived cavity, beside
            # the machine, the south-branch riser and the mixing box. The check clips a run to
            # the box it names, so every attic leg clips away and only the tail is measured.
            soffit_ref="SF-S-HP1",
            diameter=inch(6), routing=DuctRouting.CHASE, material="semi_rigid",
            design_cfm=100),
]

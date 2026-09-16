# haus: editable
# Catlin MEP — the ERV: the machine, its outdoor side, its risers, its radial distribution.
#
# Split out of plan/mep_hvac.py (which keeps System 1's conditioned-air chase) because the
# ERV stopped being four rectangular trunks and became a system: a real machine with four
# ports, an outdoor side that did not exist before, three risers up one shaft and one beside
# it, five distribution plenums and twenty-three radials. mep_hvac.py was at its page budget
# with the trunks alone.
#
# =============================== THE SYSTEM, IN BRIEF ==================================
#
# **The machine** is a **Broan B210E75RT**: 6" round top ports, 24.8"W x 21.6"H x 21"D,
# MERV 8 filter, 81% SRE at 32 F and **65% SRE at -13 F**. EQ-B-ERV keeps its uid (IFC
# GlobalId stability) and its position.
#
# ** THE WHOLE FAN CURVE IS TYPED DATA NOW (2026-09-12, BLD-08), AND THE ARGUMENT IS OVER. **
# "210 at 0.2"" and "206 at 0.4"" were never two claims; they are two stations on one curve,
# and `EQ-T-BROAN-B210E75RT.fan_curve` carries all ten published points (214 @ 0.1" down to
# 176 @ 1.2", ceiling 1.3" where the core deforms). `mep.erv_static_budget` computes what
# THIS duct system costs and reads the curve at it: **0.350" w.g. worst path, 207 cfm
# delivered**, the worst path being DU-B-ERV-R-SAUNA-EXH on the EXTRACT side. The oracle is
# notes/erv_static_budget.md.
#
# ** THE 8" UPSIZE BROAN'S MANUAL ASKS FOR ABOVE 200 cfm IS NOW OBEYED IN FULL. ** Both
# outdoor legs went to 8" on 2026-09-15. DU-ERV-EA first, which moved the governing side
# from extract to supply and bought almost nothing because the two columns were 0.0086"
# apart; then DU-ERV-OA, which had been blocked on geometry rather than money until both
# hoods moved to the NORTH face and its riser left the chase. That one took 0.1318 -> 0.0315
# and handed the governing side back to extract. The delivered figure went 203 -> 205.7 ->
# 207.0 cfm against MN's 205. The note's §7 is now spent; §6 says the only large term left
# anywhere is DU-ERV-RISER-EXH, at 58% of the governing column on its own.
# `ventilation_cfm=210` stays authored — see plan/mep_erv_types.py for why moving it is a
# separate decision with a live verdict behind it. It is a design INTENT: 210 is the curve's
# value at 0.2" w.g. and no real duct system lands there. **205 (MN 1322 R403.5) is the
# number that governs**, and `code.N1103_6_whole_house_ventilation` is what grades it.
#
# The SRE goes 0.75 -> 0.65 and that is a *worse* number on purpose: -15 F is this site's
# heating design temperature (plan/site.py), so the -13 F certified figure is the honest one
# for the block load. It raises the ventilation term; `mep.heating_capacity` moves with it,
# and that movement is a fact about a real machine rather than a regression.
#
# **It is a home-run install, not trunk-and-branch, and since 2026-09-12 every part of it
# is a commodity.** Every rectangular ERV trunk is deleted. What replaces them is one **4"
# galvanized snap-lock** radial per terminal off a **fabricated galvanized plenum**, which is
# the whole labour argument: no tees to cut in, no branch takeoffs to seal, and every
# terminal balanceable at a butterfly damper on its own start collar rather than at the
# grille. Twenty-three radials at 5-30 cfm each, one run per terminal, nothing doubled.
#
# ** THE 75 mm SEMI-RIGID TUBE IS GONE AND IT WAS A SOURCING DECISION, NOT A PRESSURE ONE. **
# (plans/buildability.md BLD-08.) Radial semi-rigid at 75 mm has three US sellers — Zehnder,
# and Brink through 475 — and no Minnesota dealer for either; the owner's decision is no
# proprietary tube. The TOPOLOGY survives intact, because a home run off a dampered plenum is
# documented standard practice and needs no special part: an 8" plenum with 4" takeoffs,
# start collars with dampers, 4" bath-fan grilles, all off a shelf in Bloomington.
# ** 4" AND NOT 3" IS A CATALOGUE DECISION. ** A 3" branch carries these flows easily and 3"
# pipe, elbows and start collars are stocked — it is 3" DAMPERS and GRILLES that are a thin,
# Amazon-grade catalogue. At 4" every part is a bath-fan commodity. The lane spacing below
# did not have to change for it: `mep.duct_joist_bay_occupancy` reads the same UNKNOWN at 4"
# that it read at 3" (12 1/2" clear bay, two 4" runs leave 4 1/2"), and the check tally did
# not move by a single finding.
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
# 8 7/8" chord-to-chord opening, so a 4" radial crosses joists there freely; FS-S-EAST and
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
# `routing=CHASE` on the basement and attic radials is a *declaration*, not an escape hatch.
# A duct inside a modeled `Soffit` says so with `soffit_ref` and is graded by
# `mep.duct_soffit_occupancy`; CHASE means only a framed shaft that is not modeled as a
# `Soffit`:
#   * basement: boxed under the mixed SL-M-DECK / FS-M-* ceiling, the same status as the
#     rectangular trunks these replace;
#   * attic: a boxed floor chase along the west wall at x=1'-0" carries the north-south leg
#     on the FS-ATTIC deck, and the east-west leg rides an FS-ATTIC bay. One run cannot
#     declare two cavities, and splitting a single length of pipe into two elements to
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
    RoughOpening,
    from_node,
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
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-MANIFOLD-6-EXH",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
]

# LEVEL 2 — RM-M-MECH, the shaft closet (x 0'-0 5/8"..5'-11 3/8", y 33'-4 5/8"..35'-11 3/8").
# Wall-hung at 8'-0", under the 9'-0" plate.
#
# **Both manifolds are east of x=2'-8", and that is the whole siting argument.** The closet's
# west end is not free space. Measured off the resolved model on 2026-09-15, what stands
# there is:
#
#     DU-ERV-RISER-SUP    x  9 5/8"   y 33'-7 1/2"   full height
#     DU-S-ERV-HP-FEED    x 12"       y 33'-7 1/2"   attic standpipe off SUP's head
#     DU-ERV-RISER-EXH    x 18 5/8"   y 33'-7 1/2"   full height
#     DU-ERV-EA           x  2'-0"    y 35'-0"       full height, basement to +17'-0"
#     VR-M-RADON-VENT     x  1'-0"    y 34'-6"       radon + plumbing vent together
#     six plumbing vents  x  1'-0"    y 34'-6"       all landing on that one riser
#     nine conduits       x 1'-6"/2'-0"/2'-6", y 34'-6" (one at y=35'-3")
#
# What is left is a 39" x 31" bay along the closet's east end, and that is exactly where
# these hang. DU-ERV-OA is no longer in that list: its riser moved east to x=3'-4" on
# 2026-09-15 and now stands in the bay's own west edge, 5 1/2" clear of EQ-M-ERV-MAN-SUP's
# west end and 3'-0" below it.
#
# ** THIS BLOCK CARRIED THE PRE-REPACK ROW FOR ONE COMMIT AND IT WAS STALE THE WHOLE TIME. **
# It read "x=5", 12", 14" and 23", all on ONE line at y=33'-7 1/2"" and went on to say the
# clash between the 12" standpipe and the 14" riser "is NOT fixed here ... it is the
# re-pack's". The re-pack landed in the same session and this paragraph was never brought
# forward with it, so the file described a defect it had already corrected. The row above is
# the built one; 9 5/8"/12"/18 5/8" leaves 5/8" between HP-FEED and EXH, and HP-FEED overlaps
# SUP only across the 3/4" of z where the two are joined, which is a joint and not a clash.
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
# ** THE MANIFOLD IS AT x=5'-0", AND M1305.1.3 IS WHY. ** At 6:12 off a rafter plate the
# roof underside is `1 1/2" + x/2`, so the code's passageway (not less than 30" high, with
# a level working space in front) governs the station: 5'-0" gives 31 1/2" at the box and
# 46 1/2" at the far side of a 30" working space, so a person can crawl to it and kneel at
# it. Extract only: the level's fresh-air duty is the mixing-box feed,
# which stays a full-size 6" branch off the supply riser rather than a radial, because it
# carries ~100 of the machine's 210 authored cfm on its own (206 certified — see the header).
EQUIPMENT_ERV_ATTIC = [
    Equipment(uid="3QT1F3F01A", tag="EQ-A-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(5), ft(34, 6)), footprint=(inch(24), inch(8)),
              # RM-A-POCKET, walled off as a storage pocket in the guest studio's west loft;
              # D-A-POCKET is a door rather than a scuttle precisely so this stays
              # serviceable.
              room="RM-A-POCKET", type_ref="EQ-T-ERV-MANIFOLD-6-EXH",
              mount=Mount(kind=MountKind.FLOOR)),
]

# THE MIXING BOX — inside SF-S-HP1, in the return chamber at the air handler's return
# face, which is the one place in this loop where fresh air may legally arrive, upstream of
# the coil, the strip heater and the unit's own filter-back grille. Injecting it anywhere
# downstream of the coil and the 2 kW strip heater would deliver 100 cfm of -15 F design
# outdoor air — half the house's fresh air — untempered.
#
# ** IT LOOKS LIKE A FITTING ONCE THE RETURN IS A PROPER PLENUM, AND A WYE WOULD NOT DO. **
# `plan/mep_registers.py` states the ERV enters the return "not a hard-coupled duct … so
# either machine can run alone", and this box is where that damper lives:
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
#     205 required. (At the 206 cfm HVI actually certifies, tighter still: 206 against 205.
#     That is the live verdict `ventilation_cfm` moves, and why the field is left at 210
#     pending a deliberate decision — see plan/mep_erv_types.py.)
# Keeping it costs the second lane past the machine, which SF-S-HP1's width already carries.
#
# ** IT IS THE RETURN PLENUM NOW, NOT A BOX BESIDE THE RETURN (2026-09-04). ** It fills the
# east lane of SF-S-HP1 from the box's south end to the air handler's south face —
# x 20'-5 1/2"..21'-5 1/2", y 27'-10 1/2"..30'-4", z on the cavity floor and 18" tall — and
# REG-S-HP-RET's whole 336 in2 face is inside it. What that replaced: a 10 x 12 box with a
# 30 x 16 ceiling grille lapping it, the return duct and 120 in2 of bare soffit cavity all at
# once. A return drawing a quarter of its face out of a framed cavity is IMC 601.5's
# building-cavity-as-plenum; nothing in the engine grades it, and it was wrong.
#
# So the airflow is now what the drawing says it is: room air in through the grille, ERV
# fresh air in through the 6" drop and its damper, the two mixing across 29 1/2" of plenum,
# then north up DU-S-HP-RET past the cabinet to its return face. Still upstream of the coil
# and of EQ-S-HP1-STRIP, which is SOUTH of the cabinet in the discharge — the ordering that
# matters (fresh -> mix -> coil -> strip) is preserved end to end.
#
# ** IT IS ON THE RETURN AND NOT ON THE TRUNK, AND THAT IS FORCED. ** `_pair_is_plumbed`
# excuses only equipment<->duct pairs; a duct riser landing on another duct is always a
# clash. The ERV feed therefore has to land on a piece of EQUIPMENT, and this plenum is it.
#
# ** THE THREE DIMENSIONS ARE EACH A CLEARANCE, NOT A CHOICE. ** 12" across is the east lane
# less the 2" HANGER_GAP_M off DU-S-HP-SUP (which runs x 18'-9"..20'-3"), leaving 1/2" to the
# cavity's east face. 29 1/2" along stops it clear of the cabinet's south face at
# y=30'-4 1/2": overlap the cabinet along the box by even an inch and the pair is graded
# across it, where the gap is 7/8" and the check FAILs. 18" fills the 18 1/4" cavity.
EQUIPMENT_ERV_SECOND = [
    Equipment(uid="8PE9E87JX5", tag="EQ-S-ERV-MIX", kind=EquipmentKind.MIXING_BOX,
              position=pt(inch(251.5), inch(349.25)), footprint=(inch(12), inch(29.5)),
              room="RM-S-HALL", type_ref="EQ-T-ERV-MIXING-BOX",
              soffit_ref="SF-S-HP1",
              mount=Mount(kind=MountKind.CEILING)),
]

# THE TWO EXTERIOR HOODS — NORTH facade, stacked, exhaust over intake.
#
# ** THEY MOVED OFF THE WEST FACADE ON 2026-09-15, AND THE CLASHES ARE WHY. ** Each run had
# to sweep the NW chase to reach a west hood — DU-ERV-OA across x -0'-8"..2'-3 5/8" at
# +4'-0", DU-ERV-EA across x 1'-11"..-0'-8" at +17'-0" — and the pair carried TWELVE measured
# interpenetrations between them. Out the north wall each leaves at its own station and
# sweeps nothing. The RISERS block below has the twelve, term by term, and the argument for
# why this also bought DU-ERV-OA its 8".
#
# ** THE NORTH GABLE IS STILL NOT A VIABLE ROUTE, AND IT IS A DIFFERENT WALL. ** What
# follows rejects the ATTIC gable at +23'-0" (W-A-N*), not the main and second storey north
# walls these hoods now use. The gable objection stands unchanged; it never applied to
# W-M-N3B or W-S-N3B, which are twelve and six feet below it. A horizontal leg at +23'-0" would
# pass squarely through the rough openings of BOTH gable windows — WIN-A-N1 (x
# 10'-9"..13'-3") and WIN-A-N2 (x 22'-9"..25'-3"), each sill +22'-0", head +25'-0" — 8"
# above the sill, 100% inside the glass, across 2'-6" of each unit. WIN-A-N1 is the only
# window daylighting FO-A-HALL's double-height stair void (storeys/attic.py), so the duct
# would cross it 13'-0" above the second-storey hall, in full view. Nothing in the engine
# grades a run against an opening; see `run_through_opening`.
#
# It also could not sit inside the gable wall's cavity: against the finished face an 8"
# envelope at y=35'-6" takes 4.00" of a 5 1/2" stud cavity, eats the 0.625" gwb layer, and
# stands 3.37" proud into the room — it could not be closed in.
#
# houses/catlin/CLAUDE.md carries the rest of the argument against the gable: RM-M-MECH is
# 5'-3" x 1'-11", not 5'-11" x 2'-7" (room polygons run 6" past an exterior wall's interior
# face), and the "20"-34" above grade" figure is the 13 7/16" RIM BAND, not the 10'-0" wall.
# The ten-foot separation is the real constraint and is tested horizontally.
#
# 12'-0" of rise clears `mep.erv_outdoor_terminals`' 10'-0" on 3-D distance alone (12'-2"
# between the two boxes, the intake 1'-10" east), and IRC M1506.3 independently waives the
# ten feet "where the exhaust opening is located not less than 3 feet above the air intake
# opening". EXHAUST ON TOP is therefore not arbitrary and must stay: the plume rises away
# from the intake. The 1'-10" x-offset is only so the two are not perfectly co-axial; it is
# not what makes the pair legal. It was 13'-0" and a 9" y-offset on the west facade; the
# intake's rise to +5'-0" (NEC, see the hood) spends the extra foot.
#
# ** WHAT THE NORTH FACE COSTS, AND IT IS NOT NOTHING. ** The west face was blank and faced
# the open west yard. The north face is the slot between the house and the garage, and it is
# already occupied: EQ-M-HP3-OD's cabinet holds x 0'-0"..2'-10 3/8" with a 12" rear coil
# clearance to the cladding, ED-M-HP3-DISC holds x 3'-1"..5'-7" up to +4'-3 1/2", and
# D-M-ENTRY's rough opening holds x 6'-6"..9'-6". The intake's station is what is LEFT: the
# 32"..48" stud bay of W-M-N3B, above the disconnect. On the second storey W-S-N3B is only
# 2'-9" long (N-S-CH2 to N-S-NW) and carries nothing, so the discharge has its pick of it.
#
# Both hoods clear TR-RF-LEADER-W, the roof leader at y=35'-6" on the WEST face, by leaving
# that face entirely.
#
# An 8" duct with R-8 wrap is ~10" OD against a 5 1/2" stud cavity, so NEITHER hood may turn
# and travel inside the wall — each is a straight through-wall penetration, wrap terminated
# at the wall line, flashed curb through the board-and-batten cladding, on the outer girt.
# That is the one part of the old west-facade objection that stands, and it only bites a run
# travelling ALONG the facade. Coming straight out at its own station, neither does.
#
# ** BOTH HOOD BOXES HANG ON THE CLADDING, NOT INSIDE IT (2026-09-11, re-derived on the
# NORTH wall 2026-09-15). ** Read off the resolved layers of W-M-N3B / W-S-N3B, which carry
# the same EXT_2X6 stack the west wall does but outward in +y: paint 35'-5 3/8", gwb
# 35'-5 3/8"..35'-6", stud 35'-6"..36'-0", sheathing to 36'-0", spray foam to 36'-4", vent
# gap to 36'-4 1/2", outer girt to 36'-6", board-and-batten cladding to 36'-7 1/4".
# **The outdoor face is y = 36'-7 1/4".** `Equipment.footprint` is a PLAN rectangle centred
# on `position`, so a 12" x 12" box whose back plate lands flat on the cladding has its
# centre 6" outboard of that face: y = 36'-7 1/4" + 6" = **37'-1 1/4"**. Each box then
# occupies y 36'-7 1/4"..37'-7 1/4", clear of EQ-M-HP3-OD's cabinet (which starts at
# 37'-7 1/4", its own 12" rear clearance) by nothing at all in y — which is exactly why the
# intake is at x=3'-4" and the cabinet stops at x=2'-10 3/8". They pass each other in PLAN,
# not in depth.
#
# The mistake this replaced is worth keeping: both hoods were once authored at x=+0'-6" on
# the west wall — dead centre of the stud cavity, a foot INSIDE the house — which no more
# placed them on the facade than the -6" duct ends carried the ducts out of it.
#
# Both therefore carry `room=None`. Outdoors they are not in a room at all, and naming the
# nearest one raises `integrity.placeable_room_mismatch` — the same call EQ-M-HP3-OD and the
# porch AP make.
#
# NOT MODELLED, deliberately: the sealed hole itself. A framed-wall penetration is spelled
# `PipeAccessory(PENETRATION_SEAL)` here (PA-M-PORCH-HYD-SEAL; `SleevePenetration` is cast
# concrete only), but `resolve/mep._resolve_pipe_accessory` requires a resolved **PipeRun**
# host and raises `integrity.pipe_accessory_host` without one — there is no duct-side
# spelling of the element. Authoring one against an unrelated pipe to get the line item would
# be a lie about what it sits on. The flashed curb stays prose until the element grows a duct
# host; the take-off under-bills two escutcheon-and-foam kits, which is the honest gap.
EQUIPMENT_ERV_HOODS_MAIN = [
    Equipment(uid="0NF97ZR9Z3", tag="EQ-M-ERV-HOOD-OA", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(3, 4), inch(445.25)), footprint=(inch(12), inch(12)),
              # The intake, and it is the LOW one deliberately: an exhaust plume rises, so
              # the intake belongs under it, not over it. Still twice `erv_terminals`' 36"
              # rule of thumb off the -2'-10" grade plane, and clear of any drift a 50 psf
              # ground-snow site puts against a wall.
              #
              # ** +5'-0", AND THE EXTRA FOOT IS NEC 110.26, NOT SNOW. ** ED-M-HP3-DISC
              # stands on this wall at (4'-4", +3'-6"). Its working space is 30" wide —
              # x 3'-1"..5'-7", which this hood is inside — and runs from grade to
              # **the greater of 6'-6" above grade or the top of the equipment**. The can is
              # 9 1/2" tall on a 3'-6" base, so its top is +4'-3 1/2" and IT, not the 6'-6"
              # (= +3'-8"), sets the ceiling of the space. A 12" box centred on +4'-0" would
              # sit from +3'-6" to +4'-6", squarely in it; centred on +5'-0" it starts at
              # +4'-6" and clears by 6". An air intake is not "equipment associated with the
              # electrical installation", so 110.26(A)(3)'s 6"-overhang allowance does not
              # reach it — the box has to be wholly out.
              room=None, type_ref="EQ-T-ERV-HOOD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]
EQUIPMENT_ERV_HOODS_SECOND = [
    Equipment(uid="38M0D2FNXH", tag="EQ-S-ERV-HOOD-EA", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(2), inch(445.25)), footprint=(inch(12), inch(12)),
              # ** y=34'-0" IS A STUD BAY, AND 34'-8" WAS A STUD (2026-09-11). ** W-S-W1B
              # frames studs at y 400"/416"/430 3/4"; the hood and its duct sat at y=416"
              # dead on `stud-001`, so the 6" penetration bored the middle out of a bearing
              # 2x6 — R602.6 allows 2 1/5" in a 5 1/2" stud. Nothing in the engine grades a
              # duct against a member, so it read 0 FAIL. y=34'-0" is the centre of the
              # 400 3/4"..415 1/4" bay: a 7" rough opening clears each stud by 3 15/16".
              # The 9" offset from the intake this spends was only cosmetic — see the hood
              # note above; 13'-0" of rise is what makes the pair legal.
              # The discharge, 13'-0" over the intake. Filed on `second`, so this mount
              # elevation is storey-relative: +7'-0" on a datum of +10'-0" is +17'-0" in the
              # project frame. The duct behind it leaves the second-storey chase notch in
              # RM-S-BATH1's NW corner, which is capped at +19'-0" — a 12" hood box centred
              # on +17'-0" clears that by 1'-6", so nothing on the inside face constrains the
              # height either. room=None, as above and as EQ-M-HP3-OD is authored.
              room=None, type_ref="EQ-T-ERV-HOOD-6-EXH",
              mount=Mount(kind=MountKind.WALL, elevation=ft(7))),
]

# =============================== THE TWO WALL PENETRATIONS =============================
#
# ** THE HOLE IS NOW AN ELEMENT (2026-09-11). ** Until that pass the two outdoor legs ran
# 3/4" past the cladding and the hoods stood flat on it — and NOTHING DREW THE HOLE. An
# `Equipment` placeable resolves no solid at all, so neither hood appears in any elevation,
# section or exported GLB; the wall's own layers carried no void, so the host read as
# unbroken cladding straight across both ducts. The model asserted a hood on a facade with
# no opening under it, at 0 FAIL. Both holes moved to the NORTH wall on 2026-09-15 with
# their hoods, and both grew 7" -> 9" for the 8" ducts behind them.
#
# A `RoughOpening` is the spelling that exists: "a bare framed/cut opening (pass-through,
# future penetration host)". It resolves a real void through every layer of the wall, and
# `framing/openings.needs_jamb_pack` gives a non-door opening that fits inside one stud bay
# NO king/jack/header pack — so a 7" hole costs no phantom framing, which is also how it is
# actually built.
#
# 7", not the duct's 6": 6 5/8" of flashed curb plus 3/16" a side to set it. The R-8 wrap
# terminates at the wall line (see the hood note above), so the wrap's ~8" OD never enters
# the opening.
#
# ** NEITHER ONE CUTS ANYTHING ANY MORE, AND THAT IS NEW. ** Measured off the resolved
# strapping on 2026-09-15:
#   - `AO-M-ERV-OA` (intake, +5'-0", z 55 1/2"..64 1/2") sits in the clear between girt
#     course 003 (z 48"..51 1/2") and course 004 (z 72"..75 1/2") — 4" under and 7 1/2" over
#     — and clears the 2'-8" and 4'-0" studs by 2 3/4" and 3 3/4". **On the west wall at
#     +4'-0" it landed squarely ON course 003 and broke it in one bay**, which cost a KDAT
#     2x4 laid flat in free air with the curb screwed to its two cut ends, plus the blocks
#     carrying them. That detail is retired; the girt screw count fell 1131 -> 1130 and
#     `test_hardware_takeoff` pins the drop.
#   - `AO-S-ERV-EA` (discharge, +17'-0", z 199 1/2"..208 1/2") cuts nothing either, clearing
#     courses at z=192" and z=216" by 4" and 7 1/2" and both studs by 2 3/4".
#
# Still NOT MODELLED, deliberately, and unchanged by this: the sealed hole's PRODUCT. A
# framed-wall penetration is spelled `PipeAccessory(PENETRATION_SEAL)` here
# (PA-M-PORCH-HYD-SEAL; `SleevePenetration` is cast concrete only), but
# `resolve/mep._resolve_pipe_accessory` requires a resolved **PipeRun** host and raises
# `integrity.pipe_accessory_host` without one — there is no duct-side spelling of the
# element. Authoring one against an unrelated pipe to get the line item would be a lie about
# what it sits on. The take-off still under-bills two escutcheon-and-foam kits; the hole
# itself is no longer missing, only the kit that seals it.
PENETRATIONS_ERV_MAIN = [
    # W-M-N3B runs N-M-MECH3 (x=6'-0") west to N-M-NW (x=0'-0"), studs at x 5'-4"/4'-0"/
    # 2'-8"/1'-4"/0'-6 3/4". DU-ERV-OA leaves at x=3'-4", so the 9" opening spans
    # x 2'-11 1/2"..3'-8 1/2", clearing the 2'-8" stud by 2 3/4" and the 4'-0" stud by
    # 3 3/4" — one bay, no king/jack/header pack.
    #
    # `from_node` measures to the NEAR JAMB, not the centre: 27 1/2" + half of 9" puts
    # `center_along` at 32", i.e. x = 6'-0" - 2'-8" = 3'-4". That 32" is one of the four
    # stations `structural.door_framing_module` will accept on this wall (16" centres off an
    # 8" residue), and it is the ONLY one the duct can stand on too — see the run itself for
    # why the other three are each inside a pipe. Sill 4'-7 1/2" centres the hole on the
    # duct's +5'-0".
    RoughOpening(uid="PNDXBSMTFB", tag="AO-M-ERV-OA", host="W-M-N3B",
                 position=from_node("N-M-MECH3", inch(27.5)),
                 width=inch(9), height=inch(9), sill_height=inch(55.5),
                 penetration_for=("DU-ERV-OA",)),
]
PENETRATIONS_ERV_SECOND = [
    # W-S-N3B runs N-S-CH2 (x=2'-9") west to N-S-NW (x=0'-0"). DU-ERV-EA leaves at x=2'-0",
    # so the 9" opening spans x 1'-7 1/2"..2'-4 1/2" and its near jamb is 4 1/2" along from
    # N-S-CH2 — `center_along` 9", i.e. x = 2'-9" - 9" = 2'-0". It sits inside the
    # 16"..32" bay with 2 3/4" to each stud and takes NO jamb pack. Sill is STOREY-RELATIVE:
    # 6'-7 1/2" on a +10'-0" datum centres the hole on +17'-0" in the project frame, which is
    # where the duct and the hood are.
    #
    # ** IT SAT 1" OFF ITS OWN DUCT UNTIL THIS PASS, AND THE SILL IS NOT WHY. ** When this
    # opening grew 7" -> 9" for the 8" duct, the `from_node` distance stayed at its 7" value
    # of 1'-8 1/2". That distance is the NEAR JAMB, so the centre moves with the width: the
    # hole resolved at y=33'-11" against a duct at y=34'-0", and the duct's far edge stood
    # 1/2" outside its own opening. The sill was always right — a 9" hole on a 6'-7 1/2" sill
    # is centred on +17'-0" either way, which is exactly why only the horizontal drifted.
    # Nothing grades a duct against the opening it is declared `penetration_for`, which is
    # why a 1" error survived a full verification run.
    RoughOpening(uid="SMGEY3KGXE", tag="AO-S-ERV-EA", host="W-S-N3B",
                 position=from_node("N-S-CH2", inch(4.5)),
                 width=inch(9), height=inch(9), sill_height=inch(79.5),
                 penetration_for=("DU-ERV-EA",)),
]

# ====================================== RISERS =======================================
#
# Three round risers up the radon/plumbing chase at (1', 34'-6"), the house's one continuous
# basement-to-attic shaft: RM-M-MECH's floor on main, the 2'-9" x 2'-2 1/8" notch walled by
# W-S-CH-W/W-S-CH-S in RM-S-BATH1's NW corner on second, out onto the attic deck.
#
# ** MEASURED OFF WALL LAYERS, NOT ROOM POLYGONS. ** `resolve/rooms.py` polygonizes from
# wall AXES and insets only by the lining, and these walls are `face("sheathing-ext")`, so
# their axis IS the sheathing exterior: a room-polygon reading counts 6" of exterior-wall
# stud as shaft on each such face. Against the resolved wall LAYERS the notch is
# **x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8" — 24" wide by 26 1/8" deep.**
#
# ** IT WAS FOUR RISERS THIS MORNING AND THE FOURTH IS WHY EVERYTHING ELSE MOVED. ** The
# measured pack, envelope by envelope:
#
#     DU-ERV-RISER-SUP   x  9 5/8"    6 5/8" .. 12 5/8"   y 33'-7 1/2", flush to the west face
#     DU-S-ERV-HP-FEED   x 12"        9"     .. 15"       y 33'-7 1/2", joins SUP's head
#     DU-ERV-RISER-EXH   x 18 5/8"   15 5/8" .. 21 5/8"   y 33'-7 1/2", 5/8" clear of HP-FEED
#     DU-ERV-EA          x  2'-0"    1'-8"  .. 2'-4"      y 35'-0", 8", basement to +17'-0"
#
# Three full-height risers on 9" centres fill the 24" exactly at y=33'-7 1/2", which is why
# a fourth could never join that row: HP-FEED is a 12 7/8" STANDPIPE between FS-ATTIC's
# bottom chord and the deck, not a riser, so it overlaps SUP in plan only across the 3/4" of
# z where the two are joined. That is a joint and not a clash, and it is the whole reason
# four ducts fit where four risers could not.
#
# ============ WHAT THE WEST FACADE COST, MEASURED AND THEN PAID OFF 2026-09-15 ============
#
# ** THE TWO OUTDOOR LEGS CARRIED TWELVE INTERPENETRATIONS BETWEEN THEM. ** Not near-misses
# — shared solid, measured off the resolved model as the overlap of swept envelopes, ducts
# and pipes together:
#
#                                             segs  worst shared solid
#     DU-ERV-OA entry @ +4'-0"  x RISER-SUP     2    6     x 2 1/2 x 6"
#     DU-ERV-OA entry @ +4'-0"  x RISER-EXH     1    6     x 2 1/2 x 6"
#     DU-ERV-EA exit  @ +17'-0" x RISER-SUP     1    6     x 2 1/2 x 8"
#     DU-ERV-EA exit  @ +17'-0" x RISER-EXH     2    6     x 2 1/2 x 8"
#     DU-ERV-EA basement leg    x PR-B-KITCH-DRAIN  3    2 x 51 x 6 5/16"  <- runs INSIDE it
#     DU-ERV-EA riser y=34'-8"  x PR-B-BATH-VENT    1    8 x 1 1/2 x 2"
#     DU-ERV-EA riser y=34'-8"  x PR-B-SAUNA-VENT   1    8 x 2 x 2 1/2"
#     DU-ERV-EA riser y=34'-8"  x PR-M-WC-VENT      1    8 x 2 x 2 7/16"
#                                            ----
#                                             12
#
# Both sweeps existed for ONE reason: the hoods were on the WEST facade, and the shaft lay
# between each run and its own hood. **Moving both hoods to the north wall removed every one
# of them.** DU-ERV-OA left the chase entirely — it runs main -> basement and never needed a
# continuous shaft — and DU-ERV-EA's riser moved from y=34'-8" to y=35'-0", out of the
# six-vent bundle that crosses at y=34'-6" and skewered it at five separate elevations.
# Re-scanned after the move, **both runs are clear of every duct and pipe in the house and of
# each other**, and the NW column's total fell from 45 interpenetrating pairs to 37.
#
# ** WHAT IT BOUGHT, BESIDES BUILDABILITY. ** DU-ERV-OA's riser at x=3'-4" in the open closet
# has room for 8" where the shaft's east lane did not: an 8" envelope there overran the
# shaft's east face by an inch, and notes/erv_static_budget.md §7 had the upsize blocked on
# that for weeks. At 8" the term falls 0.1318 -> 0.0315 and the delivered figure reaches
# 207.0 cfm against MN's 205.
#
# ** NOTHING GRADES ANY OF THIS, AND THAT IS STILL TRUE. ** There is no `mep.duct_interference`;
# the plan named one and it was never built. Two things block it, and both are worth writing
# down because they outlive this change:
#   * the main-storey radial layer is deliberately schematic — every radial is drawn on one
#     z=+9'-3 5/8" plane and about forty pairs of them cross there — so a guard has to be
#     scoped to full-height runs in a chase or it reports the drawing convention;
#   * `ResolvedConduit` carries no per-vertex elevations at all, only `z_start_m`/`z_end_m`,
#     so the chase's nine conduits are two-point schematics (CD-B-ATTIC-RISER "rises" 24 ft
#     while travelling 5'-6" horizontally). A duct cannot be proven clear of a conduit whose
#     elevation the model does not hold.
#
# The 37 pairs that remain in this column are pipe-against-pipe and pipe-against-radial, and
# none of them is this system's to fix. The six vents converging on (1'-0", 34'-6") cross the
# thirteen main-storey radial lanes at four elevations; PR-B-BATH-VENT and PR-B-SAUNA-VENT
# share solid with PR-B-KITCH-DRAIN. **They are recorded here because somebody measured them,
# not because this pass touched them.**
# ======================================================================================
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
    # ** IT STOPS UNDER THE DECK, AND ONLY THIS ONE DOES. ** +244" is the
    # centreline of a 6" duct lying on the attic deck, and it is right for the three risers
    # that surface east of x=11 1/2" — but this column is at x=0'-5", where the 6:12 underside
    # is 4" above that deck. A 6" duct cannot come up there; it would be 1.4" proud of the
    # rafters, which `integrity.element_above_roof` catches. So the riser tops out on
    # FS-ATTIC's bottom chord instead (231 7/8" = the deck less 8 7/8", the same datum
    # DU-S-ERV-HP-FEED uses) and its feed jogs the 7" east in the bay before standing up — the
    # same move VR-M-RADON-VENT makes, in the same shaft, at the same rake.
    #
    # Moving the column east instead is not available: the chase's measured clear is 24" (see
    # the note above) and the three-in-a-row at x=5"/14"/23" already over-fills it by an inch.
    # ** BOTH RISERS REACH THE MANIFOLD THEY SERVE. ** The manifolds are at
    # x 5'-6"..7'-6", 61" and 73" of plan away, and the horizontal leg between is drawn.
    # `mep.duct_connectivity` is the check that grades it.
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
                  pt(inch(9.625), ft(31, 8)), pt(inch(9.625), ft(33, 7.5)),
                  pt(inch(9.625), ft(33, 7.5))),
            elevations=(inch(-19.4375), inch(-19.4375), inch(-19.4375),
                        inch(-19.4375), inch(231.875)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap", design_cfm=210),
    DuctRun(uid="GFTW5CBARX", tag="DU-ERV-RISER-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(inch(18.625), ft(34, 6)),
                  pt(inch(18.625), ft(33, 7.5)), pt(inch(18.625), ft(33, 7.5)),
                  pt(inch(18.625), ft(29, 3)), pt(ft(5, 0), ft(29, 3)),
                  pt(ft(5, 10), ft(29, 3)), pt(ft(5, 10), ft(28, 8))),
            elevations=(inch(244), inch(244), inch(244), inch(-27),
                        inch(-27), inch(-19.4375),
                        inch(-19.4375), inch(-19.4375)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
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
    # ** BOTH OUTDOOR LEGS STOP AT THE NW CHASE. ** See EQUIPMENT_ERV_HOODS_* above for why
    # the north-gable route is not viable. Each is a riser out of the basement manifold and
    # one straight penetration through the west wall: the intake at +4'-0" on the main
    # storey, the discharge at +17'-0" on the second.
    #
    # ** THE HOOD VERTEX IS x = -0'-8", AND -0'-6" WAS SHORT (corrected 2026-09-11). **
    # -6" was picked to clear `mep.erv_outdoor_terminals`, which decides which EXHAUST run is
    # the machine's discharge by asking whether the run's LAST vertex lands outside every
    # resolved room's `clear_face` — and `clear_face` sits on the wall AXIS, which for these
    # `face("sheathing-ext")` walls is x=0'-0". A run stopping at the interior face reads as
    # indoors, the check finds no discharge at all, the 10-ft test never runs, and the whole
    # thing degrades silently to a single PASS on hood height. -6" cleared the axis and the
    # check went green — but the axis is not the building. W-M-W1B / W-S-W1B resolve
    # 7 1/4" of wall outboard of it (foam, vent gap, girt, PBR-26 cladding to x=-0'-7 1/4"),
    # so BOTH ducts died 1 1/4" inside the cladding: a hood on the facade with no hole under
    # it. **Nothing in the engine grades a duct end against a wall's layers**, which is why a
    # check-driven number outlived the geometry it was standing in for.
    # -0'-8" carries each run 3/4" past the cladding, into the hood's collar.
    DuctRun(uid="MW0MY7GDME", tag="DU-ERV-OA", system=DuctSystem.OUTDOOR_AIR,
            # ** IT LEFT THE CHASE ENTIRELY ON 2026-09-15, AND THAT IS THE POINT. ** This run
            # only ever goes main -> basement; it is the one ERV leg that does NOT need a
            # continuous basement-to-attic shaft, and it was in the chase purely because its
            # hood was on the west facade and the chase was what lay between. Hood on the
            # NORTH wall, riser at x=3'-4", and it touches the chase nowhere.
            #
            # It is a straight drop, and every station is a measured clearance:
            #   x=3'-4"   — W-M-N3B's stud module. The wall frames on 16" centres off an 8"
            #               residue, so `structural.door_framing_module` takes an opening at
            #               x=2'-0", 3'-4", 4'-8" or 6'-0" and nowhere else without cutting a
            #               stud. 2'-0" is inside DU-ERV-RISER-EXH's lane; 4'-8" and 6'-0"
            #               put the riser through PR-B-KITCH-DRAIN (x 4'-5"..4'-7") and
            #               PR-B-CW-TRUNK (x 4'-11 3/8"..5'-0 5/8"). 3'-4" is the one legal
            #               station the duct can also stand on: at 8" its metal runs
            #               x 3'-0"..3'-8", 9" clear of the kitchen drain and 1'-3 3/8" of
            #               the cold-water trunk.
            #   y=33'-11" — 4 5/8" north of W-M-MECH-S's face (the wall spans y 33'-1 5/8"..
            #               33'-6 3/8"), so the duct's own edge clears it by 5/8"; and its
            #               north edge is 2" short of the y=34'-6" vent bundle, which
            #               crosses the closet at -15", -16 1/2", +112" and +117" and is
            #               what makes every other latitude in this bay unusable.
            #   +5'-0"    — NEC 110.26 over ED-M-HP3-DISC; see the hood.
            #   -2'-3"    — the basement radial layer, joined 4" short of the machine so the
            #               last leg is a straight east run onto the port.
            #
            # ** IT IS SHORTER AND STRAIGHTER THAN WHAT IT REPLACED. ** 13'-9" and four
            # elbows against the west-facade route's 14'-0" and six — which is why the 6" ->
            # 8" step buys more here than the note's §7 priced it at, and why the governing
            # side of the whole system moved back to extract when this landed.
            #
            # PR-M-S-BATH1-TUB-DRAIN looks like it is in this lane and is not: it drops at
            # (3'-3 1/4", 34'-1 1/2") but between +10'-0 3/4" and +9'-7 15/16", in the SECOND
            # storey's floor zone. It never reaches the main deck or this riser's +5'-0".
            path=(pt(ft(3, 4), ft(36, 8)), pt(ft(3, 4), ft(33, 11)),
                  pt(ft(3, 4), ft(33, 11)), pt(ft(3, 4), ft(31, 1)),
                  pt(ft(3, 8), ft(31, 1)), pt(ft(3, 8), ft(31, 1))),
            elevations=(inch(60), inch(60), inch(-27), inch(-27),
                        inch(-27), inch(-33.8375)),
            # ** 8", AND THE MOVE IS WHAT PAID FOR IT. ** notes/erv_static_budget.md §7 had
            # priced this upsize for weeks as the one remaining lever on what was then the
            # governing supply column, and it was blocked not by money but by the chase: at
            # the old x=2'-3 5/8" station an 8" envelope overran the shaft's east face by an
            # inch and no re-ordering of four risers avoided it. Out here the lane between
            # the chase conduits and PR-B-KITCH-DRAIN is 1'-10". The term fell 0.1318 ->
            # 0.0315, which took the governing side back to EXTRACT — so §7 is now spent and
            # the lever it named no longer exists.
            diameter=inch(8), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
    DuctRun(uid="BYAVBJKRS6", tag="DU-ERV-EA", system=DuctSystem.EXHAUST,
            # Manifold first, hood last — the direction the air goes, and the direction
            # `erv_outdoor_terminals` reads an EXHAUST run.
            #
            # ** y=35'-0", AND IT IS THE VENT BUNDLE THAT SETS IT, NOT THE WALL. ** The
            # shaft clear is x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8" — 24" x 26".
            # At y=35'-6" an 8" envelope would stand 4 5/8" inside W-S-N3B's stud cavity for
            # its whole height, so the north face bounds it at y=35'-1 3/8". The SOUTH bound
            # is the six-vent bundle that crosses the chase westward at y=34'-6": it is there
            # at -15", -16 1/2", +112", +117" and +232", so anything whose envelope reaches
            # y=34'-5" is skewered at five separate elevations. At y=35'-0" an 8" riser spans
            # y 34'-8"..35'-4": 1" clear of the bundle, 1 3/8" clear of the stud cavity.
            #
            # ** y=34'-8" WAS INSIDE THAT BUNDLE AND NOBODY SAID SO. ** The old station's
            # envelope reached y=34'-4", and three of the six vents run through it —
            # PR-B-BATH-VENT, PR-B-SAUNA-VENT and PR-M-WC-VENT, 8 x 1 1/2 x 2" and better.
            # The prose that chose y=34'-8" reasoned only about the north wall, because the
            # north wall is the thing a duct check looks at; nothing in this engine pairs a
            # duct against a pipe at all.
            #
            # ** THE JOG IS GONE. ** The riser used to turn south 8" at +17'-0" to reach a
            # hood on the WEST facade, and that turn is what swept x 1'-11"..-0'-8" through
            # both trunks. On the north wall the riser and its hood share one station: the
            # run goes straight up and straight out, two elbows fewer.
            #
            # ** THE BASEMENT LEG RIDES THE PORT ELEVATION, NOT THE RADIAL LAYER. ** It used
            # to rise to -2'-3" at the machine and run the radial layer; it now holds
            # -2'-9 7/8" — the port's own height — the whole way to the riser. That ducks it
            # under the vent bundle at -15", under the 4" radial field at -2'-3", and out of
            # PR-B-KITCH-DRAIN's lane, which it previously ran INSIDE for 4'-3". The cost is
            # headroom: the duct's underside sits 6'-7" over the basement floor in
            # RM-B-FURNACE, 17" below the 8'-0 15/16" ceiling. That is a mechanical room and
            # it is walkable, but it is lower than anything else down there and should be on
            # the drawing.
            path=(pt(ft(4, 7), ft(31, 1)), pt(ft(5, 2), ft(31, 1)),
                  pt(ft(5, 2), ft(35)), pt(ft(2), ft(35)),
                  pt(ft(2), ft(35)), pt(ft(2), ft(36, 8))),
            elevations=(inch(-33.8375), inch(-33.8375), inch(-33.8375), inch(-33.8375),
                        inch(204), inch(204)),
            # ** 8", NOT 6" (owner, in the measured package). ** This is the single biggest
            # lever in the static budget and the note prices it: the discharge leg is the
            # long one on the extract chain's worst path, and area goes as d^2 while friction
            # goes as V^2, so a 6" -> 8" step takes roughly two-thirds off this term. The
            # shaft was sized for THIS diameter months before it was bought.
            # `AO-S-ERV-EA` grows 7" -> 9" to match.
            diameter=inch(8), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
]

# ============================== LEVEL 1 — BASEMENT RADIALS ============================
#
# Six 4" radials off the two plenums beside the machine, boxed under the basement
# ceiling. Centreline at 7'-6" above the basement floor, inside the manifolds' own 7'-2"
# to 7'-10" band and clear of the 8'-0 15/16" underside.
#
# REG-B-SUP2's radial is the short one on purpose. The play room's whole ceiling is
# SL-M-DECK's 14 3/8" solid concrete with NO cavity at all, so every foot of that run is
# surface-mounted; entering at the room's west edge and stopping just inside cuts about
# eight feet of exposed duct off the old (27', 27') position. It still throws away from
# FURN-B-PLAY-TV on the east wall.
DUCTS_ERV_BASEMENT = [
    # ** THE MACHINE'S OWN TWO TRUNKS. ** Both are 6", the machine's full 210 cfm, and both
    # leave its top.
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
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(ft(7), ft(28, 8)), pt(ft(7), ft(28, 8)),
                  pt(ft(7), ft(29, 9)), pt(ft(3, 8), ft(29, 9)),
                  pt(ft(3, 8), ft(29, 9))),
            elevations=(inch(90), inch(82.4375), inch(82.4375), inch(82.4375),
                        inch(75.6)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(6, 6), ft(10, 6.6)), pt(ft(19), ft(10, 6.6)),
                  pt(ft(19), ft(13))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=18),
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(19), ft(30, 6)), pt(ft(19), ft(26))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=30),
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(6, 6), inch(20.5)),
                  pt(inch(199.75), inch(20.5)), pt(inch(199.75), inch(20.5))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(7)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=12),
    # The bench hood's pull. It drops out of the ceiling chase to the hood face at 5'-6",
    # which is the vertical leg that makes it a capture hood rather than a ceiling diffuser.
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(2), ft(28, 6)), pt(ft(2), ft(8, 6)),
                  pt(ft(2), ft(8, 6))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(6, 2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=6),
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(12), ft(28, 6)),
                  pt(ft(12), inch(289.625))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # The sauna's low pickup is 4" off the floor on the WEST liner (the south face went to
    # EQ-B-SAUNA-HTR when the room rotated), so this radial runs the length of the house in
    # the ceiling chase and then drops seven feet down the wall. The
    # drop is drawn — a repeated plan point at two elevations — which it could not be before
    # `DuctRun` carried elevations. The drop moved 3'-10" east with the west liner on
    # 2026-09-05: x=64" is workshop floor now, not sauna wall.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(6, 6), ft(28, 6)), pt(inch(110), ft(28, 6)), pt(inch(110), ft(3, 2)),
                  pt(inch(110), ft(3, 2))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
]

# ================= LEVEL 2 — RM-M-MECH RADIALS (FS-S-WEST JOIST BAY) =================
#
# Thirteen 4" radials, all `JOIST_BAY` against FS-S-WEST and all graded by
# `mep.duct_joist_bay`. Each has the same three moves and no others:
#
#   1. rise out of its own manifold port at 8'-4" above the main floor, straight up into the
#      bay field overhead;
#   2. run SOUTH down its own lane — one lane per radial, at the port's own x, so no two
#      share a line — crossing the open truss webs, which is legal because the chord-to-chord
#      opening is 8 7/8" and these are 4";
#   3. turn east or west along ONE bay centre to its terminal.
#
# **FILED ON THE SECOND STOREY, NOT THE MAIN ONE, AND THAT IS NOT COSMETIC.** These ducts run
# in FS-S-WEST's cavity, which is the second storey's floor and the main storey's ceiling.
# `resolve/mep_ducts.py::_containing_floor` matches a segment to a sibling FloorSystem *on
# the duct's own storey*, so a run filed on `main` with `floor_ref="FS-S-WEST"` gets graded
# against FS-M-WEST's joist lines instead — which sit on a different 16" phase, so every
# radial reported a straddle it did not have. Elevations are therefore second-relative:
# -20" is the manifold port at 8'-4" above the main floor, and -8 3/8" is the centreline of
# a 4" duct sitting on FS-S-WEST's bottom chord.
#
# ** THAT SECOND NUMBER WAS 1 1/2" LOW AND NOTHING GRADED IT UNTIL 2026-09-12. ** It read
# -9 7/8", derived against the truss's 108 1/8" bottom — which is the bottom of the bottom
# CHORD, not its top. The chord is 1 1/2" thick, so "sitting on the bottom chord" is an
# invert at **109 5/8"**, the floor of the 8 7/8" web window (the drain note's §3), and a
# centreline at 111 5/8" = -8 3/8" second-relative.
#
# For the twelve legs that ride a bay (every radial but BATH2, which has no east-west
# leg) the old number was harmless: a run travelling ALONG
# the members may use the full 108 1/8"..120" depth, because nothing is in the way along it.
# For the legs that run SOUTH ACROSS the trusses — which is every radial's first leg, and
# which the note below already says out loud — it put 1 1/2" of a 4" duct inside the bottom
# chord at every line it crossed. `mep.duct_joist_bay_occupancy` never saw it: that check
# asks whether the duct is DEEP enough to be a problem (4" <= 8 7/8", so no) and never
# where it sits. `mep.run_member_crossing` is the check that asks the second question, and
# it reported all thirteen.
#
# Bay centres are 8" + n*16". **Two of them are unusable and the check is what said so:**
# FO-S-STAIR's trimmers land at y=26'-0 3/8" and y=35'-5 3/8", so a duct centred on the
# 26'-0" or 35'-4" bay straddles one. The extract manifold therefore sits at y=35'-0" rather
# than 35'-4", and everything that would naturally have used the 26'-0" bay uses 24'-8".
#
# HONEST LIMITS, both real and neither graded by anything:
#   * The thirteen lanes leave the closet as TWO INTERLEAVED FAMILIES, NOT ONE 4" MODULE,
#     AND SEVEN PAIRS OVERLAP. Ten extract lanes: nine on a 4" module — x=36", 40", 44",
#     48", 52", 56", 60", 64", 68" — plus PLANT on its own at 34". On a 4" module 4" ducts
#     are TANGENT, zero clear, which is what the neck of a home-run bundle looks like off a
#     pair of manifolds in a 6'-0" closet. The three SUPPLY lanes are not on it:
#     LIVING/BED/STUDY at x=38", 46", 54" — the extract module's half-step, an 8" module
#     interleaved between its lanes. That puts seven pairs on 2" centres — PLANT/BATH1
#     (34/36), BATH1/LIVING (36/38), LIVING/VANITY (38/40), KITCH/BED (44/46), BED/BATH2
#     (46/48), SUITEBATH/STUDY (52/54) and STUDY/LAUNDRY (54/56) — and two 4" ducts on 2"
#     centres OVERLAP BY 2" (4" of radii less the 2" centre distance; it was 1" at 3").
#     They are drawn as straight lines because a lane is a straight line in this model and a
#     bundle is not; in the field the neck is dressed — a short 4" semi-rigid leg off each
#     start collar (DUCT-T-SEMIRIGID-4 is in the catalog for exactly this) lets the runs
#     pass each other before they go rigid, which is the whole reason the drawing is
#     tolerable rather than wrong.
#     **Nothing grades it.** `mep.duct_joist_bay_occupancy` pairs runs that share a bay
#     CENTRELINE, and these lanes run south ACROSS the bays; crossing runs are deliberately
#     not paired (a hanger-gap subtraction between them returns a meaningless number). It is
#     the along-bay case below that the check sees, and it reports that one UNKNOWN. If the
#     neck is ever to be modelled honestly rather than noted, the lever is a real Soffit or a
#     per-lane offset in the first 3'-0" — not a wider spacing all the way south, which would
#     move twelve terminals to buy clearance in one closet.
#   * Two pairs share part of one bay: STUDY and LAUNDRY both ride the 20'-8" bay from
#     x=4'-8" to x=14'-6", and BATH1/VANITY/KITCH all turn on 24'-8". The bay is 12 1/2"
#     clear (16" o.c. less a 3 1/2" chord), so two 4" ducts side by side leave 4 1/2" and
#     fit without argument. This is the one duct-against-duct case the engine does grade
#     outside a modeled Soffit: `mep.duct_joist_bay_occupancy` names STUDY and LAUNDRY on
#     FS-S-WEST and reports UNKNOWN — the bay is wide enough, but the model gives a run one
#     centreline per bay, so two lanes in one bay are necessarily drawn on top of each
#     other. UNKNOWN is the honest verdict; the prose is not the record of this any more.
_PORT_Z = inch(-20)
#: A 4" duct's centreline resting on FS-S-WEST's bottom chord: invert 109 5/8" (the web
#: window's floor), centreline 111 5/8", second-relative -8 3/8". See the derivation above.
_BAY_Z = inch(-8.375)

DUCTS_ERV_LEVEL2 = [
    DuctRun(uid="MRH0QZT6NN", tag="DU-M-ERV-R-LIVING", system=DuctSystem.SUPPLY,
            path=(pt(ft(3, 2), ft(34)), pt(ft(3, 2), ft(34)), pt(ft(3, 2), ft(12, 8)),
                  pt(ft(27), ft(12, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="83MA15Q308", tag="DU-M-ERV-R-BED", system=DuctSystem.SUPPLY,
            path=(pt(ft(3, 10), ft(34)), pt(ft(3, 10), ft(34)), pt(ft(3, 10), ft(6)),
                  pt(ft(9), ft(6))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=15),
    # ** A CEILING RUN, FOUR POINTS, THE SHAPE EVERY OTHER LEVEL-2 CEILING RADIAL HAS. **
    # RM-M-STUDY is paired with a LOW extract instead (DU-M-ERV-R-LAUNDRY below), which is
    # what makes a ceiling supply work in a 148 cf box, feeding overhead by ED-M-STUDY-SPOT.
    #
    # ** IT RIDES THE 20'-8" BAY, AND THAT COSTS NOTHING BECAUSE IT IS ONE BAY. **
    # FS-S-WEST's JOISTS are at n*16", so its BAY CENTRES are at 8" + n*16" — this line read
    # the second formula onto the first until 2026-09-15, which got the right answer for the
    # wrong reason. 20'-8" is a bay centre, sitting between the joists at 20'-0" and 21'-4"
    # for the whole ride
    # from x=4'-6" to x=17'-2" — no jog, no crossing, one straight length of snap-lock pipe.
    # Stopping short of the joist at 21'-4" is also why the grille cannot sit on the
    # sconce's own 21'-5" line; the argument is on REG-M-SUP4 in plan/mep_registers.py.
    DuctRun(uid="2ZZ3MF5VAF", tag="DU-M-ERV-R-STUDY", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 6), ft(34)), pt(ft(4, 6), ft(34)), pt(ft(4, 6), ft(20, 8)),
                  pt(ft(17, 2), ft(20, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=15),
    DuctRun(uid="K04AT15S97", tag="DU-M-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(3), ft(35)), pt(ft(3), ft(35)), pt(ft(3), ft(24, 8)),
                  pt(ft(1, 2), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="B13Y04D9BP", tag="DU-M-ERV-R-VANITY", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 4), ft(35)), pt(ft(3, 4), ft(35)), pt(ft(3, 4), ft(24, 8)),
                  pt(ft(3), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="YEXGZK2KW2", tag="DU-M-ERV-R-KITCH", system=DuctSystem.RETURN,
            path=(pt(ft(3, 8), ft(35)), pt(ft(3, 8), ft(35)), pt(ft(3, 8), ft(24, 8)),
                  pt(ft(20, 10.7), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=6),
    DuctRun(uid="DPAS57TPCG", tag="DU-M-ERV-R-BATH2", system=DuctSystem.EXHAUST,
            # Three points, not four: this lane's x IS the terminal's, so the run rises and
            # goes straight south with no turn at the end. A fourth vertex repeating the
            # third would be a zero-length segment, and the sweep and the IFC emitter both
            # (correctly) drop one — which is a silent disagreement between the authored
            # path and the exported geometry, so it is not authored.
            path=(pt(ft(4), ft(35)), pt(ft(4), ft(35)), pt(ft(4), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="63W84CCNE4", tag="DU-M-ERV-R-SUITEBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(4, 4), ft(35)), pt(ft(4, 4), ft(35)), pt(ft(4, 4), ft(19, 4)),
                  pt(ft(14), ft(19, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    # ** THE ONE TWO-HEADED RADIAL IN THE HOUSE, AND THE PORT BUDGET IS WHY.
    # ** RM-M-STUDY needs a stale-air pickup. It cannot have its own lane:
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
    # and taking a 5 cfm trickle. Fifteen feet of 4" snap-lock and four bends to a laundry
    # closet is the cheapest neighbour this booth could have been given.
    #
    # ** THE FLOW IS WHAT CAPS THE STUDY AT 10 cfm. ** 5 + 10 = 15 cfm on the shared length,
    # ~25 m3/h, and a 4" run is used to 50 cfm here (DUCT-T-GALV-4.max_cfm, a 600 fpm quiet
    # limit rather than a pressure one). The room is 15 cfm supply / 10
    # extract on purpose (booth stays positive — see REG-M-RET-STUDY), but the headroom to
    # take it to a balanced 15/15 later is only about 2 cfm, not 5. Anything past that is a
    # second lane, and there is no port for one.
    #
    # ** AND IT IS ALREADY AT THE SMALLEST SIZE THERE IS HERE. ** The owner asked whether a
    # small room could take a smaller duct: every radial in this house is one 4" SKU
    # already. The step below it (51 mm) would put 10 cfm at ~450 fpm in a tube ten inches
    # from a seated occupant's feet, against ~115 fpm at 4" — in the one room built to be
    # quiet, downsizing is the expensive direction.
    #
    # ** ONE CORNER, NOT THREE, ON A TWO-HEADED RUN WHOSE WHOLE RISK IS ACCUMULATED BEND
    # LOSS. ** REG-M-RET-STUDY sits at 14'-6" (out from under FURN-M-STUDY-DESK-LEAF's
    # stowed envelope — the argument is on the register), so the radial turns south once
    # and drops there. South from the 20'-8" bay cuts the joists at 20'-0" and 18'-8", legal
    # because FS-S-WEST is open-web with an 8 7/8" chord opening, clear of the trusses' east
    # bearing at W-M-C2/C3. -108" is storey-relative on the `second` datum (+10'-0"), i.e.
    # 12" above the main floor.
    DuctRun(uid="ANSKB7EGDH", tag="DU-M-ERV-R-LAUNDRY", system=DuctSystem.RETURN,
            path=(pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(20, 8)),
                  pt(ft(10, 6), ft(20, 8)), pt(ft(14, 6), ft(20, 8)), pt(ft(14, 6), ft(18)),
                  pt(ft(14, 6), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z,
                        inch(-108)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=8),
    DuctRun(uid="YFDV1TGN1W", tag="DU-M-ERV-R-MUD", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(35)), pt(ft(5), ft(35)), pt(ft(5), ft(31, 4)),
                  pt(ft(4, 0.4), ft(31, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    DuctRun(uid="164777V9JK", tag="DU-M-ERV-R-BED1", system=DuctSystem.RETURN,
            path=(pt(ft(5, 4), ft(35)), pt(ft(5, 4), ft(35)), pt(ft(5, 4), ft(14)),
                  pt(ft(29), ft(14))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    # ** ITS EAST LEG MOVED ONE BAY NORTH ON 2026-09-12, 22'-0" -> 23'-4", AND THE 4" RETYPE
    # IS WHY. ** A 3" duct on this lane spanned y 21'-10 1/2"..22'-1 1/2"; at 4" it spans
    # 21'-10"..22'-2", half an inch further south — and that half inch closed the only lane
    # `haus route` could find for PR-M-S-SUITE-TUB-DRAIN, whose terminal sits at
    # y=21'-9 1/8". Nothing FAILED: the authored drain is unchanged and `haus check` never
    # moved. What broke was the ROUTER's ability to re-derive that run, which is the honest
    # early warning that the corridor had no slack left in it.
    # 23'-4" (280" = 8 + 17 x 16) is a bay centre, it is free — LIVING/BED/STUDY/BATH1/
    # VANITY/KITCH/SUITEBATH/LAUNDRY/MUD/BED1/PLANT take 12'-8"/6'-0"/20'-8"/24'-8"/19'-4"/
    # 18'-0"/31'-4"/14'-0"/7'-4" and none of them is on it — and it is still well inside
    # RM-S-BED2 (y 18'-27'). REG-S-RET-BED2 moved with it; a floor boot against the east
    # wall is as good at 23'-4" as at 22'-0".
    DuctRun(uid="2QHYF71DBS", tag="DU-M-ERV-R-BED2", system=DuctSystem.RETURN,
            path=(pt(ft(5, 8), ft(35)), pt(ft(5, 8), ft(35)), pt(ft(5, 8), ft(23, 4)),
                  pt(ft(29), ft(23, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    # THE PLANT ROOM'S EXTRACT. It keeps the DU-S-PLANT-EXH/DU-A-ERV-R-PLANT uid.
    #
    # ** IT IS DOWN HERE BECAUSE THE ATTIC'S DECK CHASE IS A FINISHED BEDROOM. ** Off
    # EQ-A-ERV-MAN-EXH it would run the x=1'-0" chase 21'-8" down the base of RM-A-STUDIO's
    # west knee wall. Down here it never enters the attic at all.
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
    # ** IT IS A HIGH TERMINAL. ** Humid air
    # stratifies, so the wettest air in RM-S-PLANT is the air overhead. The grille is not in
    # the ceiling — this duct is below the room, not above it — so it rises inside
    # W-S-C1 and discharges at 8'-6", six inches under the 9'-0" ceiling. W-S-C1 is
    # PLANT_INT_2X6_BRG_HUMID at 7.43": a 5 1/2" cavity, room for a 4" riser AND a
    # vapour-tight boot through the liner. W-S-PS1, the room's north wall, is 2x4 and is not.
    #
    # ** IT IS LONGER, NOT SHORTER: 55'-8" against the attic route's 47'-5". ** 45'-6" of plan
    # run plus a 9'-4" rise from the truss bottom chord to the grille, which is the part an
    # eyeballed estimate misses. That is affordable and it is worth saying why: HVI certifies
    # this machine at 206 cfm net supply at 0.4" w.g. (B210E75RT, HVI 2004940), so the "0.2"
    # w.g." this file quotes elsewhere is the model-name point off the fan curve, not the rating
    # point, and the real static budget is about double what those comments assume. This is
    # ** NO LONGER THE RADIAL WHOSE DROP THE INSTALLER MUST CHECK (2026-09-15). ** It was,
    # at 25 cfm: 0.0301 in. of duct plus 0.0424 through the RH damper, 16% of the whole
    # extract path and the governing radial in notes/erv_static_budget.md §6. The extract side
    # was rebalanced from 265 cfm to the machine's 210 and this room went to 5 cfm — the owner
    # wants it holding its own atmosphere on a slow turnover, not flushed — and a 5x cut in
    # flow is a 25x cut in friction, so both terms fell to about a thousandth. It is still the
    # longest radial on this manifold; that was never what made it matter.
    # -20" is the manifold port, -8 3/8" a 4" duct on the truss bottom chord.
    # ** THE RISER MUST NOT STAND IN D-S-PLANT'S CLEAR OPENING, AND `mep.duct_joist_bay`
    # DOES NOT CATCH IT. ** That door is centred on y=4'-0" in W-S-C1 with its jacks at
    # y=2'-8 1/4" and y=5'-3 3/4", so a riser at y=4'-8" would stand 7" inside the north
    # jamb: through the bearing wall's sole plate, 78 1/2" of bare 4" duct standing free in
    # the rough opening with nothing to strap it to and the leaf swinging through it, then a
    # 3" bore through a solid 2-ply 2x8 header. `mep.duct_joist_bay` grades the bay and never
    # asks what the riser stands in, so it would PASS.
    #
    # The fix is one bay north, and it is nearly free. y=7'-4" (88" = 8 + 5 x 16) is a truss
    # bay centre AND a stud bay centre in the same wall — the coincidence this file already
    # leans on at y=4'-8" — so the duct rides the bay east and stands up between the studs at
    # y=80" and y=96", clear of the door's kings at 65 1/4" and of ED-S-PLANT-SW one bay
    # south, at 53'-0" developed length: still W-S-C1, still the 5 1/2"
    # PLANT_INT_2X6_BRG_HUMID cavity that takes both the riser and a vapour-tight boot, still
    # a high sidewall terminal at 8'-6" for the stratification reason above. Supply/extract
    # throw across the room is 11'-7 1/2".
    #
    # The alternative bay, y=2'-0" south of the door, is 2'-8" LONGER and lands the riser in
    # the same stud bay as ED-S-PLANT-SW-TIMER's gasketed box — a 4" duct and a 2 1/2" box in
    # a 5 1/2" cavity is worse than zero clearance, and no check in the engine grades duct against device.
    #
    # There is no legal riser at y=4'-8" at all: the jacks, the full-width header and the one
    # cripple at y=49" between them leave no station in the opening, so jogging inside the
    # cavity at +8'-6" does not rescue it either. The register had to move with the riser.
    DuctRun(uid="CWMB7Q4E3W", tag="DU-M-ERV-R-PLANT", system=DuctSystem.EXHAUST,
            path=(pt(ft(2, 10), ft(35)), pt(ft(2, 10), ft(35)),
                  pt(ft(2, 10), ft(7, 4)), pt(ft(18), ft(7, 4)),
                  pt(ft(18), ft(7, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, inch(102)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
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
# ** THE x=1'-0" CHASE RUNS THE LENGTH OF A FINISHED BEDROOM, AND THE KNEE WALL AT ITS FOOT
# IS BARE. ** DU-S-ERV-HP-FEED turns east at y=22'-0" and reaches SF-S-HP1 up
# RM-A-EAST-UNFIN's deck instead of running the knee wall's length; DU-A-ERV-R-STUBATH's
# east leg rides the y=19'-4" bay, ALONG the joists, boring nothing; DU-A-ERV-R-PLANT feeds
# from FS-S-WEST's trusses (DU-M-ERV-R-PLANT in DUCTS_ERV_LEVEL2), rising inside W-S-C1's
# 5 1/2" cavity to a HIGH SIDEWALL grille at 8'-6" — still in the warm wet air at the top of
# the room, so the stratification argument is unaffected; only the direction the boot
# arrives from changed. ED-A-STUDIO-RC8/RC9 stay: the wall is in the 210.52 test on its own
# merits whatever is or is not lying at its foot.
#
# The remaining rejected alternative is unchanged: bore the FS-ATTIC I-joists and run
# north-south in the bays. The hole chart permits it, but at x=1'-0" every hole would fall
# within a foot of the joists' west bearing, which is the one place the chart does not — and
# that is before ~16 bored webs and a manufacturer sign-off.
#
# +4" is a 4" duct lying on the attic deck at 240"; -9 7/8" is its centreline sitting on
# FS-ATTIC's bottom chord at 228 1/8". Both are attic-relative, and negative because the
# attic datum is the deck top.
_ATTIC_DECK_Z = inch(4)
_ATTIC_BAY_Z = inch(-9.875)

DUCTS_ERV_ATTIC = [
    DuctRun(uid="4YT114ADP3", tag="DU-A-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(32, 8)),
                  pt(ft(1), ft(32, 8)), pt(ft(5), ft(32, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # THE ATTIC'S OWN PICKUP, at the studio's NW corner, not the walled storage pocket —
    # REG-A-RET1 must not extract a guest bedroom's air through a closed door.
    #
    # It takes the x=1'-0" chase south past W-A-STU-N to the boot at (1'-0", 20'-8"); this
    # run's 1'-7" inside the studio is most of what remains of that chase. All of it is ON
    # the deck: FS-ATTIC is I-joist, so there is no crossing bays here and the north-south
    # travel costs nothing in depth. Developed length ~15' — the shortest radial on this
    # manifold, so it takes nobody's pressure headroom.
    DuctRun(uid="DYNQDC9ZMJ", tag="DU-A-ERV-R-ATTIC", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(20, 8)),
                  pt(ft(1), ft(20, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, inch(-2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=5),
    # THE GUEST BATH'S EXTRACT. Same chase south to y=19'-0",
    # then east on the deck to the W-A-STU-W axis at x=9'-7 1/2" and UP inside that wall's
    # 5 1/2" staggered cavity to REG-A-STUBATH-EXH at 7'-0". The rise is the whole reason the
    # terminal is a wall grille rather than a floor boot: this room follows the roof and has no
    # ceiling plenum, and the wet wall is the only chase between a high pickup and the deck.
    #
    # 20 cfm continuous, matching every other bath terminal in the house — and small enough
    # that the extra run costs the machine nothing measurable.
    #
    # ** THE EAST LEG MUST NOT LIE ACROSS THE DECK. ** From x=1'-0" to the wet
    # wall, laying it across RM-A-STUDIO's floor at y=19'-0" would put 8'-7" of duct across
    # the middle of a bedroom. It rides the FS-ATTIC bay instead, which costs nothing: the
    # leg runs EAST, and FS-ATTIC's I-joists span x, so travelling east is travelling ALONG
    # a bay. Nothing is bored.
    #
    # y=19'-4" (232" = 8 + 14 x 16) is a bay centre; REG-A-STUBATH-EXH is the same 4" over so
    # the riser meets its grille. 19'-4" is
    # well inside RM-A-STUBATH (y 17'-4 3/4" .. 22'-3 3/8"), and it is a different bay from the
    # one PR-A-STUBATH-DRAIN takes at 20'-8", so the two do not share a cavity.
    DuctRun(uid="WCH6Z4DZX0", tag="DU-A-ERV-R-STUBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(19, 4)),
                  pt(ft(1), ft(19, 4)), pt(ft(9, 7.5), ft(19, 4)),
                  pt(ft(9, 7.5), ft(19, 4))),
            # ** THE RISER TOP MUST FOLLOW ITS GRILLE. ** REG-A-STUBATH-EXH is at 4'-4"; a
            # riser topping out higher rises past its own boot and out through the rake,
            # which at x=9'-7 1/2" is 4'-11 1/4" above the deck. `integrity.element_above_roof`
            # catches that; `mep.register_duct_match` only grades the pair in plan, where they
            # agree regardless of elevation.
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z, inch(52)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=20),
    # RM-S-BED3's extract, forced up here by FO-S-STAIR — see the header. It becomes a ceiling
    # grille rather than a floor boot, which for stale air is the better end of the room anyway.
    #
    # ** THERE IS NO WAY ROUND THE NORTH. ** A bay leg crossing x 10'..18' at y=31'-4" would
    # hit FO-A-HALL, which spans that whole band to the north gable — FO-A-HALL's maxy IS
    # W-A-N2's inside gwb face, so the strip between the void and the wall is wall, not deck.
    # EVERY west-to-east route north of the studio is severed.
    #
    # So it goes down the x=1'-0" chase to y=22'-0" (264" = 8 + 16 x 16, a bay centre, and below
    # W-A-STU-N's sole plate so the partition is irrelevant), east under the studio floor to
    # x=29', then north on the east loft's deck to the existing grille. **~53'-6", not the
    # longest radial in the house** — DU-M-ERV-R-PLANT is 55'-8" on the FS-S-WEST trusses.
    # Length was never the criterion anyway — BED3 carries 5 cfm (~102 fpm in
    # 4", where 21 extra feet costs thousandths of an inch w.g.), and since the 2026-09-15
    # rebalance PLANT carries 5 cfm too and costs the same nothing. Neither is the run whose
    # drop the installer must check any more; that is DU-B-ERV-R-SAUNA-EXH, where a motorised
    # damper and not a duct is the number. The two are on different machine ports:
    # BED3 on EQ-A-ERV-MAN-EXH, PLANT on EQ-M-ERV-MAN-EXH. Re-filing BED3 onto the main-storey
    # manifold is blocked by FO-S-STAIR, and that manifold is full at 10 of 10.
    DuctRun(uid="73FJZH564X", tag="DU-A-ERV-R-BED3", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(22)),
                  pt(ft(1), ft(22)), pt(ft(29), ft(22)),
                  pt(ft(29), ft(22)), pt(ft(29), ft(31, 4))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z,
                        _ATTIC_DECK_Z, _ATTIC_DECK_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=5),
]

# THE MIXING-BOX FEED — the one place fresh air enters the heat-pump loop.
#
# It keeps DU-S-ERV-HP-FEED's tag and uid. It comes off the supply riser's head on the attic
# deck, takes the boxed floor chase south, rides the FS-ATTIC bay at y=22'-0" east, comes
# back up onto RM-A-EAST-UNFIN's deck and runs NORTH to the mixing box, dropping onto it
# through SF-S-HP1's lid.
#
# ** THE 12'-2" SOFFIT TAIL IS GONE. ** Until 2026-09-04 the box sat at the far south end of
# SF-S-HP1 in RM-S-STUDY2's ceiling, and this run had to travel the length of SF-S-DUCT
# beside the trunk, cross a seam, jog east across three lanes with 1 1/8" to spare, and come
# back south. Nine vertices now instead of twelve; the tail, both of its turns and the pinch
# are all gone. Developed ~43'-7" against ~61'-2".
#
# 6" and not a 4" radial: ~100 of the machine's 210 authored cfm goes through here (206
# certified — see the header), which is half the house's fresh air arriving in one place, and
# a radial would run it at ~5,000 fpm.
#
# ** IT NEVER ENTERS THE GUEST STUDIO. ** Running the x=1'-0" deck chase south all the way
# would put 10'-11" of 6" duct along the base of a finished bedroom's knee wall — the single
# item that would set that chase's SECTION, where everything else on that wall is 4".
# It turns east in **y=22'-0"** — the same bay DU-A-ERV-R-BED3 takes, and for the same
# reason: 264" = 8 + 16 x 16 is a bay centre, it sits under W-A-STU-N's sole plate so the
# partition is irrelevant, and it is the last bay south of FO-A-HALL, which severs every
# west-to-east route north of it.
#
# ** ROUTE EFFICIENCY: ~2.05 AGAINST `mep.run_route_efficiency`'S 2.5. WATCH IT. ** It was
# 1.54 before, and it got WORSE only because the destination moved 27 ft closer to the
# origin while the route still has to go round FO-A-HALL. The margin is 0.45, not 0.96.
DUCTS_ERV_MIX_FEED = [
    DuctRun(uid="CSDV02AAAA", tag="DU-S-ERV-HP-FEED", system=DuctSystem.SUPPLY,
            # ** ITS FIRST 7" IS IN THE BAY. ** It comes off the riser head on the deck at
            # x=0'-5", under 4" of roof. It picks the riser up on FS-ATTIC's bottom chord
            # instead and stands up at x=1'-0", where the underside is 7 1/2" and a bare 6"
            # duct on the deck clears by 1/2". The 7" east is ALONG a bay — FS-ATTIC's
            # I-joists span x — so nothing is bored; the north-south leg that follows stays
            # on the deck for the same reason.
            #
            # ** THE DECK LEG TURNS DOWN AT y=28'-9", INSIDE THE PLENUM. ** It has to land
            # within EQ-S-ERV-MIX's footprint (y 27'-10 1/2"..30'-4") for
            # `mep.duct_connectivity` to read the joint, and 28'-9" is comfortably inside it
            # rather than on an edge. It was y=27'-9" while the plenum was a 12"-deep box.
            #
            # This run names NO soffit (below), so the old "stop exactly here or the attic
            # legs get graded" constraint is gone with it — but the drop still has to land
            # IN the plenum, so moving the plenum in y means moving this vertex with it.
            #
            # -8 7/8" is a 6" duct on FS-ATTIC's bottom chord; +4" is the same duct lying on
            # the attic deck; -24 7/8" is 6" above SF-S-HP1's cavity floor, unchanged by the
            # move because the 21" drop keeps that floor at 209 1/8" absolute.
            path=(pt(inch(9.625), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)),
                  pt(ft(1), ft(22)),
                  pt(ft(1), ft(22)), pt(ft(21), ft(22)),
                  pt(ft(21), ft(22)), pt(ft(21), ft(28, 9)),
                  pt(ft(21), ft(28, 9))),
            elevations=(inch(-8.875), inch(-8.875), inch(4), inch(4),
                        inch(-8.875), inch(-8.875),
                        inch(4), inch(4), inch(-24.875)),
            # ** IT NAMES NO SOFFIT, AND THAT IS THE 2026-09-04 CHANGE THAT COSTS SOMETHING. **
            # It used to name SF-S-HP1. `duct_occupants` clips a run's extent ALONG the box
            # it names and deliberately not ACROSS it — and SF-S-HP1 now spans y
            # 27'-8"..35'-5 3/8", which is the same y band the x=1'-0" attic chase and the
            # riser head run through, twenty feet west of the box and fourteen inches above
            # its lid. Named, those three attic legs are graded as occupants of a cavity
            # they never enter: a hard FAIL against geometry that is correct.
            # What is given up is the grading of the final 12" drop, and that costs little:
            # the drop lands inside EQ-S-ERV-MIX's own 10 x 12 footprint, which IS a graded
            # occupant of the box, in the east lane with 1" to the cavity face. Nothing else
            # of this run is in the box at all — the 12'-2" tail that used to be is gone.
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=100),
]

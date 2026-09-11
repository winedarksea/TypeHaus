# haus: editable
# Garage — 24'x24' ICF stem + 2x6 wood walls, moved 2'-6" north for the gable connector.
# Wood walls sit on the ICF stem 22" above grade; the storey
# elevation is the top of the stem. Overhead door faces NORTH — the street side, which is
# what plan/site.py has always declared: SetbackSpec edge 2 (north) is "FRONT" and the water
# service enters from the north. It faced east until 2026-09-07, drawn for a south lot with
# a driveway around the east side; see notes/garage_orientation_lot.md for that premise and
# the revert recipe.
from typehaus import (
    Alarm,
    AlarmKind,
    Door,
    Downspout,
    EaveGutter,
    EaveTrim,
    FasciaBoard,
    Flashing,
    FoundationWall,
    Node,
    Occupancy,
    Pitch,
    Railing,
    RailingKind,
    Roof,
    RoofForm,
    Room,
    Stair,
    StructuralRole,
    TrimKind,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

# The garage's two N-S wall lines, published so the ICF stem (params/foundations.py), the
# slab, and the breezeway (params/breezeway.py) all derive from one number.
#
# The selected study translates both original wall lines north by 30", keeping the
# foundation quantities and wall/stem alignment. South cladding is y=43'-1 3/4", leaving
# 6'-6 1/2" clear to the house. The old four-foot polycarbonate module is retired.
# The south rake is six feet beyond this wall; its 6 1/2" house gap is the envelope joint,
# not a roof bearing. Do not independently move the ICF or recess its wall sheathing:
# their coplanar exterior faces prevent a water-catching shelf at the stem top.
GARAGE_Y_SOUTH = ft(43, 2.625)
GARAGE_Y_NORTH = ft(67, 2.625)

# The garage's two E-W wall lines, published for the same reason as the pair above: the
# stem, the footings, the slab and the service-door landing (params/foundations.py) all
# derive from these two numbers rather than restating 0'/24'.
#
# ** 6'-0"..30'-0" SINCE 2026-09-07: THE GARAGE IS CENTRED ON THE HOUSE RIDGE. ** It was
# x 0'..24' — its west wall aligned with the house's — which put its centre on x=12'-0", six
# feet west of the ridge at x=18'-0". It is x 6'..30' now, centre x=18'-0", dead on it.
#
# ** THE MOVE WAS IN 24" STEPS, AND THAT WAS THE HOUSE'S OWN CONVENTION, NOT A RULE. ** This
# file said until 2026-09-11 that `D-G-SERVICE`'s 36" RO had to sit on one of
# GARAGE_WALL_2X6's 24" stud lines. It does not: `structural.door_framing_module` grades how
# many studs an opening interrupts, and the only hard bound at the west end is the corner
# pack — the sole plate starts 5/8" inboard of the node line and the 3-stud corner takes the
# next 3", so the corner owns x 6'-0"..6'-3 5/8" and the door's king must clear it. A 36" RO
# at 6'-7"..9'-7" puts the king at 6'-4"..6'-5 1/2" (3/8" clear) and interrupts the one stud
# at 8'-0", exactly what the old station at 8'-6"..11'-6" interrupted at 10'-0".
#
# ** SO THE DOOR IS IN THE CORNER SINCE 2026-09-11, CENTRE x=8'-1", ** one inch off
# `D-M-ENTRY`'s 8'-0" — the concentric pair the 2026-09-07 move gave up. `D-M-ENTRY` still
# cannot move: its east jamb is 6" west of `N-M-N2` at x=10'-0", the tee where `W-M-STRW`'s
# bearing stack lands on the north wall and runs to the footings. The shared landing
# `FS-BW-FLOOR` is 3'-7" wide (x 6'-0"..9'-7") and covers both complete 36" patches; HP3 is
# west of the roofed connector (params/hp3_pad.py).
GARAGE_X_WEST = ft(6)
GARAGE_X_EAST = ft(30)

# ICF stem height above grade == this storey's elevation (wood walls sit on the stem top).
# Published so the storey table, the stem (params/foundations.py) and the overhead door's
# drop to grade all read one value instead of three copies of 1'-10".
GARAGE_STEM_REVEAL = ft(1, 10)

NODES = [
    Node(uid="CGN001AAAA", tag="N-G-SW", position=pt(GARAGE_X_WEST, GARAGE_Y_SOUTH)),
    Node(uid="CGN002AAAA", tag="N-G-SE", position=pt(GARAGE_X_EAST, GARAGE_Y_SOUTH)),
    Node(uid="CGN003AAAA", tag="N-G-NE", position=pt(GARAGE_X_EAST, GARAGE_Y_NORTH)),
    Node(uid="CGN004AAAA", tag="N-G-NW", position=pt(GARAGE_X_WEST, GARAGE_Y_NORTH)),
]

# 8'-4" plates, not 8'-0". The garage sits 4" down from grade while D-G-SERVICE's threshold
# stays pinned to the breezeway deck at 0'-0" — so the door climbs 4" inside its own wall,
# and its 3-ply LVL header needs that same 4" of plate above the rough head to clear the
# truss heels (structural.member_interference). The slab sits at the same grade, so the
# interior clear height is unchanged.
WALLS = [
    # ** THE BEARING PAIR IS E/W SINCE 2026-09-07. ** The ridge turned with the overhead
    # door, so the trusses now span east-west and land on W-G-E/W-G-W; W-G-S and W-G-N are
    # the gable ends. All four keep `top=ft(8, 4)` — the two gable triangles are closed by
    # resolve/roof_edge.py's wall→roof closure, whichever pair they fall on.
    Wall(uid="CGW101AAAA", tag="W-G-S", start_node="N-G-SW", end_node="N-G-SE",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
    # This wall carried Western States "Classic Green" nail-strip for part of 2026-08-26 —
    # it was the overhead-door facade then — and is back to the house white. The revert is
    # one line: drop the `layer_materials=` override and it is `GARAGE_WALL_2X6` like its
    # three neighbours. `standing-seam-nailstrip-26-green` is still in the catalog,
    # referenced by nothing — the same convention `glazed-green-brick` is kept under, so
    # going green again is a one-line change rather than a re-derivation. Note it would now
    # be the wrong wall to paint: the facade is W-G-N.
    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", end_node="N-G-NE",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW103AAAA", tag="W-G-N", start_node="N-G-NE", end_node="N-G-NW",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CGW104AAAA", tag="W-G-W", start_node="N-G-NW", end_node="N-G-SW",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
]

# --- stem-top Z-flash (2026-09-03) ------------------------------------------------------
#
# The garage's base skin is now ONE thing: the 24" `coil-ext` band on the ICF stem
# (plan/assemblies.py's GARAGE_ICF_6), 2" below grade to the stem top, on all four walls.
# The 4'-0" east wainscot that used to stand in front of it — four FoundationWalls on
# GARAGE_METAL_WAINSCOT, six local nodes, and four cap flashings at +4'-0" — was deleted
# on 2026-09-03. NOTHING REPLACES IT: the band already ran behind it, so the piers keep the
# same protection the rest of the garage has, and the east elevation reads as one uniform
# base course instead of a tall panel over a short one.
#
# WHAT DID NOT EXIST AND NOW DOES IS THIS Z. The band's top and the corrugated panel's base
# both land on the stem top, and until now that horizontal junction was modelled by nothing
# at all — it lived in a `source=` string on the material. A rainscreen's cavity water
# arrives at exactly that line, so the piece that catches it and throws it out over the band
# is real scope on all four walls, not a wainscot detail that left with the wainscot.
#
# `DRIP_FLASHING` is the right kind and not a stand-in: it resolves as a bent angle — a flat
# leg with a turn-down at the OUTBOARD end — which is a Z lapped up behind the panel and
# turned down over the band's top edge. `WRB_COUNTERFLASHING` is a flat back pan and has no
# turn-down. The one honest limitation is the same one the deleted caps carried: the inboard
# kick-out leg that runs up behind the corrugated panel cannot be a second bend on the same
# run. Do not invent a TrimKind for it.
#
# ALUMINIUM, AND THAT IS THE CORROSION RULE WRITTEN INTO THE MODEL. `corrugated-panel-26`
# above this line is 26 ga PVDF-coated STEEL and the band below it is aluminium, so the Z
# between them must be aluminium and must never lap the panel metal-to-metal — sealant or
# EPDM between, the Z's upper leg behind the corrugated. In a plowed, salted splash zone
# that contact line is where the detail fails, and nothing in the engine grades dissimilar
# metals. Naming `aluminum-flat-pvdf` here rather than the `metal-dark-exterior` steel coil
# the rest of the envelope's dark trim is ordered in is what makes the rule readable off the
# model, and it keeps band and Z one colour and one coil order.
#
# ** IT BREAKS AT THE ONE STEM GAP. ** There is no stem — and so no band and no Z — across
# the 16'-0" overhead door, where params/foundations.py drops the stem to a grade beam flush
# with grade. Five runs, 80 LF: south one unbroken 24'-0", east 24'-0", north 4'-0" twice,
# west 24'-0". The south wall was two runs (2'-3" + 18'-3") until 2026-09-11, broken at the
# service door's own stem gap; that gap is closed (the door sill is +1'-0", not the slab, so
# nothing needed the stem out of the way — see `W-GF-S-DR` in params/foundations.py) and
# `TR-G-STEMZ-S2` is retired with it (uid 8JZR6X0A4X, never reuse). The north break stations
# are the stem's own gap nodes (N-GF-N-DRE/DRW flush with the overhead door), authored as
# literals because this file is `# haus: editable` and the dialect bans arithmetic.
#
# ** `thickness` IS THE FLAT LEG AND IT IS CENTRED ON THE PATH, so the path is NOT a wall
# face. ** It is the mid-line of what the Z has to cover: from the node line (the CDX/EPS
# plane the panel's back and the stem's foam face share) out past the band's outer face,
# which stands 0.30" proud — `coil-gap` 1/4" + `coil-ext` 0.05" — plus about 1/2" of throw.
# 0.80" of leg, so the mid-line is 0.40" outboard of each wall's own node line. That is much
# tighter than the deleted caps' 2.55", which had a 1-1/2" wainscot cavity to span. The
# corrugated panel above stands 7/8" proud and therefore OVERSAILS this Z by ~1/2": correct,
# and the reason the piece is concealed flashing rather than a visible cap.
#
# `top_elevation` is PROJECT-FRAME ABSOLUTE (model/trim.py), not storey-relative, so this is
# the stem top spelled out: garage grade -2'-10" plus GARAGE_STEM_REVEAL 1'-10" = -1'-0".
# `depth` is the turn-down's visible face, 1-1/2" of lap down the band.
#
# ** AUTHORED AS ONE COUNTER-CLOCKWISE LOOP — south W->E, east S->N, north E->W, west N->S —
# AND THAT IS WHY EVERY RUN IS `back_side="left"`. ** `back_side` names the side of the path
# that faces the BUILDING, and the left-hand normal is `normal(d) = (-dy, dx)`
# (resolve/geometry.py). Walked this way each wall's left-hand normal points inboard, so the
# turn-down hangs off the outboard end on all five runs and throws water clear of the band
# instead of back behind it. Get one direction wrong and the drip points at the wall — which
# `integrity.drip_flashing_back_side` now grades, by requiring each run's back-side normal to
# aim at the centroid of the loop its siblings form. It caught four inverted rake returns in
# `params/roof_trim.py` the day it was written; these were already right.
STEM_TOP_Z_FLASHING = [
    # South: one unbroken run since the service door's stem gap closed (2026-09-11). It
    # keeps S1's uid and tag; S2 (11'-9"->30'-0") is retired.
    Flashing(uid="4Z104BJ7TV", tag="TR-G-STEMZ-S1", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(6), ft(43, 2.225)), pt(ft(30), ft(43, 2.225))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    # East: one unbroken run since the overhead door left this wall (2026-09-07).
    Flashing(uid="7PK70E7009", tag="TR-G-STEMZ-E", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(30, 0.4), ft(43, 2.625)), pt(ft(30, 0.4), ft(67, 2.625))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    # North: the two 4'-0" piers flanking the overhead door, walked E->W with the loop, so
    # N1 is the east pier (30'-0"->26'-0") and N2 the west (10'-0"->6'-0"). N2 keeps the uid
    # the retired east pier TR-G-STEMZ-E2 carried.
    Flashing(uid="CZJZNX97MB", tag="TR-G-STEMZ-N1", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(30), ft(67, 3.025)), pt(ft(26), ft(67, 3.025))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="HQQQFQ576Z", tag="TR-G-STEMZ-N2", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(10), ft(67, 3.025)), pt(ft(6), ft(67, 3.025))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="DHPT0K1FB2", tag="TR-G-STEMZ-W", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(5, 11.6), ft(67, 2.625)), pt(ft(5, 11.6), ft(43, 2.625))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
]

# Published so params/foundations.py can gap the ICF stem under the overhead door instead
# of repeating this offset/width: there is no 22"-above-grade stem wall under a vehicle
# door (it would be a curb the car has to climb), so the stem drops to a grade beam there.
#
# ** MEASURED FROM N-G-NE SINCE 2026-09-07, AND THE NUMBER IS UNCHANGED. ** The door hangs
# off W-G-N, which runs NE->NW, so 4'-0" puts the 16'-0" opening at x 4'-0"..20'-0" and its
# centre on x=12'-0" — the wall's exact midpoint, the same relationship it had to W-G-E.
#
# ** 4'-0" IS NOT DEFENDED BY A WAINSCOT, AND THAT IS AN OPEN QUESTION. ** The centre at
# 12'-0" is 12" off the 24" module and cuts 9 stud lines where 8 would do —
# `structural.door_framing_module` reports it and names 11'-0"/13'-0" as the nearest legal
# centres. The advisory is suppressed in preferences.toml's `[checks] suppress`, keyed on
# the DOOR tag (`structural.door_framing_module:D-G-OVERHEAD`), so the suppression followed
# the door across walls with no edit. Until 2026-09-03 THE REASON WAS THE WAINSCOT: moving
# the door 12" would have made its two flanking veneer piers 5'-0" and 3'-0", a visibly
# asymmetric facade bought with one stud. The wainscot is gone and that argument with it —
# the base band is uniform on all four walls and does not care where the door sits.
#
# WHAT STILL HOLDS THE CONSTANT is the chain below it, which is real but is a cost of
# moving rather than a reason not to: params/foundations.py gaps the ICF stem into a grade
# beam on this offset, so the gap nodes, two stem segments, their footings and the two
# STEM_TOP_Z_FLASHING break stations above all travel with it.
# ** DO NOT quietly re-decide this either way. ** It is an owner question now: one stud
# against a door centred on the framing module. The rotation deliberately carried the
# question across unchanged rather than settling it in passing.
OVERHEAD_DOOR_OFFSET = ft(4)
OVERHEAD_DOOR_WIDTH = ft(16)  # DT-EXT-OVERHEAD192

# Same pair for the service door. Unlike the overhead door it does NOT gap the stem: its
# sill is +1'-0" over the garage storey (0'-0" absolute, the breezeway deck), so the ICF stem
# runs continuous under it and the landing carriers pass 3 3/4" over the stem top.
#
# ** 0'-7" OFF N-G-SW SINCE 2026-09-11: THE DOOR IS HARD IN THE SW CORNER. ** 7" is the
# minimum this offset can be: the corner pack owns the first 3 5/8" of wall (see
# GARAGE_X_WEST above) and the king wants 3" before the RO, so the king at 6'-4"..6'-5 1/2"
# clears the corner by 3/8". RO 6'-7"..9'-7", centre x=8'-1", one inch off `D-M-ENTRY`'s
# 8'-0". It was 2'-6" (RO 8'-6"..11'-6", centre 10'-0") from 2026-09-07 to 2026-09-11 and
# 6'-6" off a wall at x=0'-0" before that — every one of those stations a 24" multiple,
# under a "must sit on the stud module" rule this file invented and the engine never had.
# What the corner buys: the interior landing and stair sit against `W-G-W`, so the stair's
# handrail is wall-mounted on ordinary blocking and the landing's west guard is gone; the
# exterior landing covers both door patches at 3'-7" instead of 5'-6".
#
# ** MOVING THIS CONSTANT MOVES MORE THAN A DOOR. ** params/north_entry_frame.py derives the
# interior landing, both carriers, their posts and the exterior landing's east edge from it
# (SERVICE_RO_WEST_FT / SERVICE_RO_EAST_FT); the stair, the handrail, the two backing bands
# in plan/backing.py, the three switch/light stations in plan/lighting.py and the
# SL-D-NORTH-BRIDGE cut in plan/views.py are LITERALS that follow it by hand. The stem under
# it no longer follows at all: the two nodes `N-GF-S-DRW/-DRE` are pinned where the retired
# gap left them (2'-3" and 5'-9" off `N-GF-SW`) as a fossil split, so the water service's
# sleeve `SP-GF-S-HYD` keeps its host `FT-GF-S-DR` — `integrity.sleeve_in_opening` is what
# catches a sleeve whose host moved out from under it.
SERVICE_DOOR_OFFSET = ft(0, 7)
SERVICE_DOOR_WIDTH = ft(3)  # DT-EXT-SWING36

OPENINGS = [
    # 16' opening is past the prescriptive header table, hence the named engineered beam:
    # a 2-ply 14" LVL.
    #
    # Threshold is the slab at grade, not the host wall's own floor: W-G-N starts at the
    # stem top, GARAGE_STEM_REVEAL above the slab, so the door reaches *down* past its host
    # — the plan's one negative sill_height, the exact negation of that reveal (spelled out
    # rather than computed; the dialect bans arithmetic). The tie is held by
    # test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade.
    # Head follows the threshold down to 7'-0" above the slab. params/foundations.py gaps
    # the stem to a grade beam under this opening so there's no curb for the car to climb.
    Door(uid="CGD201AAAA", tag="D-G-OVERHEAD", host="W-G-N",
         type_ref="DT-EXT-OVERHEAD192", position=from_node("N-G-NE", OVERHEAD_DOOR_OFFSET),
         sill_height=ft(-1, -10), header_spec='2-ply 14" LVL'),
    # **This door reaches up to the breezeway, not down to the slab.** The deck is the
    # landing outside this door (code.R311_3_exterior_landing, and the house rule that both
    # breezeway doors open onto it at one level), so the threshold has to stay at 0'-0"
    # absolute: +1'-0" over a garage storey that sits at -1'-0". Inside, ST-G-STEPS takes
    # the 2'-10" down to the slab.
    #
    # The head lands 8" under the top plate — 6'-8" of door in a wall whose plate is at
    # +7'-4" — which is why this opening now names a header the way the overhead door does.
    # There is 6 1/2" between the rough head and the top of wall, and the table's 2-2x8
    # (7 1/4") does not fit it: the solver grows a header up from the rough head, so an
    # oversized one pushes straight through the plates into the truss bottom chords
    # (structural.member_interference caught exactly that). A 5 1/2"-deep 3-ply LVL does
    # fit, three plies filling the 2x6 wall, and it is the ordinary answer for a tall
    # opening in a garage wall: a continuous header carried at the plate line rather than
    # dropped below it (IRC R602.7.2 lets the header take the top plate's place).
    Door(uid="CGD202AAAA", tag="D-G-SERVICE", host="W-G-S", type_ref="DT-EXT-SWING36",
         position=from_node("N-G-SW", SERVICE_DOOR_OFFSET), sill_height=ft(1),
         header_spec='3-ply 5.5" LVL'),
    # This 8' wall (vs. the house's 10') is why the 27" family is 36" tall: a 60" height at
    # this 42" sill would push the header above the top plate.
    #
    # ** THE GRID SETS THE STATION, NOT THE OTHER WAY ROUND. ** GARAGE_WALL_2X6 is 24" o.c.,
    # so W-G-W's stud lines are at 24n along the wall and its bay centres at 12 + 24n; a 14"
    # RO must land on a bay centre or `structural.window_framing_module` reports it, breaking
    # a stud and pulling in a header a 14" RO exists to avoid. 3'-0" (position 2'-5" + half
    # of the 14" RO) is that bay centre.
    Window(uid="CGX301AAAA", tag="WIN-G-N1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(2, 5)), sill_height=ft(3, 6)),
    # WIN-G-N1's mirror at the south end: 21'-0" off N-G-NW is the exact mirror of N1's
    # 3'-0" about the wall's 12'-0" midpoint, and also a bay centre (12" + 24"x10 on
    # W-G-W's grid), so the pair stays symmetric and both keep the unbroken stud bay a 14" RO
    # exists to get. Same 3'-6" sill (above a workbench).
    Window(uid="CGX302AAAA", tag="WIN-G-S1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(20, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    Room(uid="CGR401AAAA", tag="RM-GARAGE", seed=pt(ft(18), ft(62, 6)),
         occupancy=Occupancy.GARAGE, conditioned=False,
         floor_finish="sealed-concrete"),
]

# Gable roof, ridge N-S (parallel to the house's, since 2026-09-07), 16" overhangs. N/S
# walls stay flat 8' rather than `top=ToRoof`: a raked wall top must split at the ridge, but
# the 16' overhead door is centered on the ridge, so W-G-N can't be split. Both gable
# triangles are instead closed by the wall→roof closure in resolve/roof_edge.py, which reads
# its cladding material straight off the host wall's own layers — so a `Wall.layer_materials`
# override on one of these walls would carry into its gable triangle with nothing authored
# for the closure itself. None is authored today; W-G-E's green was reverted.
# Eave + rake trim is two-layer: a 2x6 wood sub-fascia (structural nailer) lapped by the
# weather face — brake-formed PVDF metal in the house's near-black `metal-dark-exterior`,
# six pieces, two eaves and four rakes, THE SAME COIL AS THE RIDGE CAP. One coil and one
# order for both: a cap in a different colour from the fascia under it reads as a
# mistake rather than as a choice. It wore "Copper Penny" metallic from 2026-08-26 until
# 2026-09-08; the garage now follows the house's ONE exterior dark like every other dark
# metal element on the envelope. The substrate stays METAL and that half is not reverted —
# a dark trim colour on cellular PVC is the classic failure (PVC's thermal movement forces
# a solar-reflective vinyl-safe coating and an LRV cap), and this colour is darker than the
# one that argument was written for. See the `metal-dark-exterior` Material comment in
# plan/assemblies.py.
# The SOFFIT stays cellular PVC and stays white: vented, out of the weather, and a white
# soffit is what keeps an overhang from reading as a shadow. A vented PVC soffit closes the
# overhang and feeds the vent channel. Elevations derive from the resolved roof plane so the
# raised-heel lift carries the trim with it.
# BOTH eaves get a 5" gutter in the house's dark exterior coil (params/roof_trim.py
# ::_CHAIN_MATERIAL — mill aluminium read as a pale band under a dark edge). The eaves are
# EAST and WEST since the ridge turned on 2026-09-07: east discharges beside the HP1 pad and
# the walk round to the house, west over the window wall and the hydrant corner, and neither
# is open ground the way the old north eave was. Declared here rather than in params/ for the
# same reason as the fascia — the raised-heel truss lifts the deck plane at the envelope
# stage, so an absolute elevation would drift off the eave.
#
# ** THE SCHEMA IS ASYMMETRIC AND THE TIE THAT MATTERS RUNS THE OTHER WAY. ** `EaveGutter.edges`
# is a tuple but `downspout_ref` is ONE string (model/trim.py), so a two-eave trough cannot
# name both leaders from here. What actually binds a leader to its trough is
# `Downspout.gutter_ref="RF-GARAGE"`, which BOTH carry; `downspout_ref` names the east one so
# the field is not left empty, and `slope` describes both falls. Do not read the single
# `downspout_ref` as "the west eave drains to nothing".
_GARAGE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="metal-dark-exterior", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
    gutter=EaveGutter(material="metal-dark-kstyle", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("east", "west"),
                      slope="1/16 in/ft north on both eaves — east to TR-G-LEADER-E, west to TR-G-LEADER-W",
                      downspout_ref="TR-G-LEADER-E"),
)

# ** THE CANOPY'S OWN EDGE, AND IT IS THE GARAGE'S EDGE CONTINUED, NOT A SECOND DETAIL. **
# RF-BW-CANOPY carried NO eave trim at all until 2026-09-10: bare sheathing edges on both
# eaves, no fascia, no soffit, no gutter — over the one walking surface between the two
# buildings. The two roof planes are ONE plane (same 4:12, same +7'-4" bearing, same 16"
# overhang), so every piece here is dimensionally identical to the garage's and is ordered
# off the same coil and the same stock.
#
# ** ONE TROUGH, AND THE CANOPY DOES NOT GET A LEADER OF ITS OWN. ** The channel runs
# continuous from the canopy's south end to the garage's north end and falls north into
# `TR-G-LEADER-E` / `-W`, which is why `downspout_ref` names the garage's east leader
# rather than inventing one here. A leader at the SOUTH end would discharge onto the entry
# landing and the four cast tiers — the exact discharge the garage's own leaders were moved
# north to avoid, and the reason that paragraph above is written the way it is.
#
# ** NO SOFFIT, AND THAT IS THE ONE PIECE THAT DOES NOT CONTINUE. ** `_soffit_member` closes
# the overhang from the fascia's inner face back to a WALL face (`wall_face_inset` reads the
# resolved cladding polygons), and this canopy has no wall under either eave — it has a
# header on columns, with open air under it. Declaring a soffit thickness here derived a
# 5'-9 5/8" panel, which is the measure running away rather than a piece anyone would cut.
# An open canopy has nothing to close anyway: the underside between the headers is exposed
# framing by design, and the garage's white PVC soffit is there to feed a VENTED ATTIC this
# roof does not have. So the tails are exposed, and the fascia and the trough — the two
# pieces the eye actually reads across the joint — are identical to the garage's.
#
# ** THE CAPACITY IS THE ONE NUMBER TO WATCH, AND IT STILL CLEARS. ** Each garage slope
# sheds ~290 sq ft; the canopy adds ~80 (13'-4" of horizontal projection over a 6'-0" run),
# so each 3" leader now takes ~370 sq ft against the ~425 sq ft it clears at the 8 in/hr
# design intensity (params/roof_trim.py works the number). Under, but no longer by much:
# lengthening the canopy, or widening the overhang, is what would force a 4" leader.
_CANOPY_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="metal-dark-exterior", thickness=inch(1), depth=inch(6))),
    gutter=EaveGutter(material="metal-dark-kstyle", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("east", "west"),
                      slope="1/16 in/ft north on both eaves — CONTINUOUS with RF-GARAGE's trough, falling to TR-G-LEADER-E / -W at the garage's north end; no leader at the canopy's south end, which would discharge onto the entry landing",
                      downspout_ref="TR-G-LEADER-E"),
)

# One leader per eave. 3" round, not the house's 4": each slope sheds ~290 sq ft against
# each house eave's 648, and 3" clears ~425 sq ft at the 8 in/hr design intensity
# (params/roof_trim.py works the number) — so the pair is two independent 3" runs, not a 3"
# and a spare. test_drainage_elements.py holds these and the EaveGutter together so a roof
# change that moves a trough fails there instead of leaving a leader hanging beside it.
#
# ** BOTH AT THE NORTH END, AND THAT IS THE FALL, NOT A HABIT. ** This paragraph said
# "both at the SOUTH end" until 2026-09-10 and described both leaders discharging into the
# passage between the house and the garage — the exact opposite of the coordinates eight
# lines below, which have put them at y = 68'-5 7/8" (north of GARAGE_Y_NORTH) since the
# north entry took the south end. The geometry is right and the prose was stale; only the
# prose moved.
#
# North is where they belong. South of the garage is the covered passage, its four cast
# tiers and the entry landing — 290 sq ft of roof per slope discharging onto the one
# walking surface between the two buildings, which freezes. North is the open front yard
# beside the driveway, falling away to the street. `TR-G-LEADER-E` keeps the uid and tag of
# the retired south-east leader rather than being retired with it, because the pipe is the
# same pipe on the same eave; the west leader mirrors it about x=18'-0".
#
# The x/y here are the trough CENTRELINE, 3/4" inboard of each eave edge: the eave edge is
# 16" of overhang off each node line (x = 31'-4" east, 4'-8" west), and the y is the
# north trough end, 16" of overhang north of GARAGE_Y_NORTH plus the same 3/4".
_GARAGE_LEADER_E = Downspout(
    uid="CGDS01AAAA", tag="TR-G-LEADER-E",
    position=pt(ft(31, 3.25), ft(68, 5.875)),   # north end, clear of the entry tiers
    # Both absolute. The trough they bracket is derived from the roof plane, so it moves on
    # its own if the roof does; these are the two numbers that have to follow it by hand.
    top_elevation=ft(7, 6),             # inside the trough floor
    bottom_elevation=ft(-1, -6),        # splash block, a foot above the apron
    diameter=inch(3), material="metal-dark-kstyle", gutter_ref="RF-GARAGE",
)
# No `uid=` on purpose: this file is `# haus: editable`, so `haus fmt` visits it and mints
# an ABSENT uid. It skips `uid=""`, which is why the field is omitted rather than blanked.
_GARAGE_LEADER_W = Downspout(
    uid="WB6YFR9QB2", tag="TR-G-LEADER-W",
    position=pt(ft(4, 8.75), ft(68, 5.875)),    # north end, clear of the west screen
    top_elevation=ft(7, 6),
    bottom_elevation=ft(-1, -6),
    diameter=inch(3), material="metal-dark-kstyle", gutter_ref="RF-GARAGE",
)

ROOFS = [
    # `edge_trim_material` names the coil the FORMED EDGE TRIM is ordered in, which on this
    # roof is the vented ridge cap and nothing else. The field drives the ridge
    # cap and the corner trim (resolve/roof_trim.py::_edge_trim_material); a 16" overhang
    # frames fascia + soffit and no corner trim, so this recolours exactly one member.
    # The fascia is NOT reached by this field — it names its own material on the FasciaBoard
    # above — so the two must be kept in step BY HAND. They are the same coil;
    # change one and change the other, or the cap and the fascia under it drift
    # apart with nothing to catch it.
    Roof(uid="CGRF01AAAA", tag="RF-GARAGE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-G-E", "W-G-W"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="y",
         # ** THE 6'-0" SOUTH EXTRUSION IS GONE, AND IT WAS NEVER AN OVERHANG. ** The ridge
         # runs north-south, so "south" is a RAKE: `resolve/framing/roof_gable.py` framed it
         # as ladder rake framing, and the backspan is ONE TRUSS BAY -- 24" at this roof's
         # spacing. That resolved to 2x4 outlookers cantilevering 88" off a 24" backspan on a
         # 2x6 barge rafter, with no truss over the passage at all. Conventional practice caps
         # a cantilevered outlooker near 24"; this was about 4x past anything a supplier will
         # seal, and nothing in `checks/` or `engineering/` graded an outlooker.
         #
         # The passage is now RF-BW-CANOPY below: three real trusses spanning 24' between two
         # headers on two columns. This roof stops at its own gable end.
         edge_overhangs=(("south", ft(0)),),
         edge_trim_material="metal-dark-exterior",
         eave_trim=_GARAGE_EAVE_TRIM),
    # ** THE PASSAGE CANOPY, AND IT IS ITS OWN `Roof` FOR A TAKEOFF REASON, NOT A FRAMING ONE. **
    # `roof_ceiling_area_m2` bills off the BEARING footprint, so extending RF-GARAGE over the
    # passage would have ordered 144 sf of R-38 blown fiberglass and 5/8" gypsum ceiling over
    # an open outdoor bay. CANOPY_ROOF is GARAGE_ROOF's structure with neither.
    #
    # ** THE SHEATHING IS STILL CONTINUOUS ACROSS THE GARAGE SOUTH WALL LINE, AND THAT
    # CONTINUITY IS THE CANOPY'S ENTIRE LATERAL SYSTEM. ** Both column bases are standoffs on
    # a 5/8" cast-in bolt -- uplift ties, not moment connections. East-west wind goes into the
    # roof sheathing and spans 6 feet north into the garage roof diaphragm; north-south wind
    # runs axially along the two headers into the garage's corner posts. Both paths die if
    # this ever becomes a structurally separate plane. Two `Roof` ELEMENTS, one diaphragm --
    # the drawings have to say so (AN-BW-ROOF does). If that joint ever becomes a real break,
    # a KBS1Z knee brace at each column is the cheap answer and is a live row in this house.
    #
    # It bears on BEAMS, which `Roof.bearing_refs` could not name until 2026-09-10 --
    # see resolve/roof_bearing.py. BM-BW-RW/RE top out at +7'-4", the same plate elevation as
    # W-G-W/W-G-E, so the two roof planes are one plane.
    Roof(uid="YX2GDZJMBV", tag="RF-BW-CANOPY", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("BM-BW-RW", "BM-BW-RE"),
         assembly="CANOPY_ROOF", overhang=ft(1, 4), ridge_direction="y",
         # North butts the garage gable; south stops flush at the house, which is the whole
         # point of the scheme -- the landing, the four tiers and the paver landing all end up
         # under roof, so none of them carries snow.
         # South oversails the pier line by 3 3/8", leaving a 7 3/8" gap to the house
         # cladding at y=36'-7 1/4" -- the joint plans/north-gable-extension.md specifies: a
         # formed, positively sloped closure fixed to the CANOPY only, dying at the house in a
         # replaceable compressible or brush seal, inspectable from below, never filled with
         # rigid foam or sealant. The two buildings move independently and the joint has to.
         edge_overhangs=(("north", ft(0)), ("south", ft(0, 3.375))),
         edge_trim_material="metal-dark-exterior",
         eave_trim=_CANOPY_EAVE_TRIM),
]

# --- NO SNOW RETENTION, AND THAT IS EARNED (2026-09-07) ---------------------------------
#
# Entry-zone snow retention is authored by params/breezeway.py. Its rail/clamp layout
# is a supplier-design allowance; north leaders keep meltwater off the east tiers.

ALARMS = [
    # A garage gets a *heat* detector, not smoke: exhaust, dust and outdoor-swing temps would
    # nuisance-trip a smoke head, which is why R315 asks for CO coverage adjacent to the
    # garage rather than a smoke alarm inside it. On CKT-LT-BACKUP because R314.4 wants an
    # unswitched circuit and CKT-RC-GARAGE (GFCI) is wrong for a life-safety device.
    Alarm(uid="CGA701AAAA", tag="AL-G-HEAT", kind=AlarmKind.HEAT, room="RM-GARAGE",
          circuit="CKT-LT-BACKUP"),
]

# --- service-door stair (ST-G-SERVICE) --------------------------------------------------
#
# Five risers from the garage slab at -2'-10" up to D-G-SERVICE's threshold at 0'-0", the
# same 5 x 6.8" risers on 11" treads at 3'-0" wide that five concrete `Slab`s used to be
# (SL-G-STEP-0..4 in params/foundations.py). SL-G-STEP-0, the 3'-0" landing at the
# threshold, is still a Slab and belongs there — a landing is a floor, not a flight. The
# four treads below it are this.
#
# PRESSURE-TREATED WOOD, not concrete (owner choice): KDAT southern yellow pine, kiln-
# dried after treatment so it is stable enough to cut and fit like framing. The garden's
# beams and the breezeway already use it (BEAM_KDAT / POST_KDAT), so it is the house's
# established exterior-wood answer. Where the stringers land on the garage slab they need a
# capillary break — a strip of the same 10-mil under-slab retarder, which is on site anyway.
# PT stops the fungus that follows wicked water; it does not stop the wicking.
#
# `Stair` used to take its rise from a pair of storey elevations through a FloorOpening in
# the storey above, and this is a step-down *within* one
# storey with no floor to open. `floor_opening` is optional now and `base_elevation` /
# `top_elevation` state the rise directly. That is what puts the flight in front of
# `structural.stair_riser_uniformity` and `code.R311_7_8_handrail`, neither of which could
# see a stack of slabs, and what RL-G-SERVICE below is the answer to.
#
# The elevations are literals because this file is `# haus: editable` and may hold only
# literals; -2'-10" is `params/foundations.SITE_GRADE`, which `plan/site.py` repeats as
# `Site.grade` and `plan/manifest.py` asserts the two agree. `start` is the foot of the
# flight — the landing's north edge at 47'-1 5/8" plus 4 x 11" of tread = 50'-9 5/8" — and
# it climbs south (`run_reversed`) back to the landing. The y literals below move with
# GARAGE_Y_SOUTH.
#
# ** x=6'-11 5/8" IS THE STEM'S FINISHED FACE, AND THE FLIGHT IS FLUSH TO IT (2026-09-11). **
# The ICF stem `W-GF-W` is 11" thick off the node line at x=6'-0" and carries a 5/8" board on
# its inside face from grade up (GARAGE_ICF_6's `gwb-stem`), so the finished face is
# 6'-11 5/8"; `params/north_entry_frame.py::GARAGE_STEM_INSIDE_X_FT` is the same number and
# the landing's east edge and both carriers derive from it. The framed wall above the stem
# is thinner — its gyp face is at 6'-6 3/4" — which leaves a 4 7/8" ledge on the stem top at
# -1'-0", accepted as-is (owner).
#
# 11" treads with NO nosing, which keeps the run at the 3'-8" the four slabs occupied and
# leaves an 11" going against R311.7.5.2's 10" minimum. A nose would shorten the run and buy
# nothing here.
STAIRS = [
    Stair(uid="X99TD38ZS3", tag="ST-G-SERVICE",
          from_storey="garage", to_storey="garage",
          base_elevation=ft(-2, -10), top_elevation=ft(0),
          width=ft(3), start=pt(ft(6, 11.625), ft(50, 9.625)),
          run_direction="y", run_reversed=True,
          tread_depth=inch(11), nosing_depth=inch(0),
          material="kdat"),
]

# R311.7.8 wants a handrail on any flight of four or more risers, and this one has five.
# Nothing was asking for it while the flight was five slabs, because both handrail rules
# iterate `model.stairs`.
#
# ** WALL-MOUNTED ON W-G-W SINCE 2026-09-11. ** The flight is flush to the west stem, so the
# rail is brackets into the framed wall above it, the way `RL-M-HANDRAIL-W` in
# plan/storeys/main.py is. `mount="wall"` makes the resolver emit a bracket per station
# instead of a 36" post on each tread; `post_spacing=48"` on a 3'-9" run puts one bracket at
# each end of the path and none between. ** THE TOP END IS ON A STUD, 1" PAST THE LANDING
# EDGE. ** W-G-W's studs are 24" o.c. from N-G-NW, so stud-010 is at y=47'-2 5/8"; the
# landing edge is 47'-1 5/8", a quarter inch off that stud's face, which would have put the
# bracket half on the stud and half over WIN-G-S1's bay. Running the rail 1" further (R311.7.8
# asks for continuity riser to riser and forbids nothing beyond) puts the bracket squarely on
# the stud and needs no blocking there. The FOOT station is 5" from a stud and gets a
# `WallBacking` band in plan/backing.py (`BK-G-W-RAIL-FOOT`) — move this path and move it.
# The rail centreline at x=6'-9" is 2 1/4" off the wall's gyp face at 6'-6 3/4": the 1 1/2"
# clearance R311.7.1.2 wants plus the bar's own 3/4" radius. It hangs over the stem ledge,
# 2 5/8" clear of the flight's west edge at 6'-11 5/8".
#
# It was post-mounted on the west side of a flight standing in the open at x 8'-6"..11'-6"
# (2026-09-07 to 2026-09-11), and before that ran x 5'..8' under a landing at 6'-6"..9'-6",
# a stale offset nothing graded. `serves_stair` rakes the rail along the nosing line and the
# rail tops out 36" above it, inside R311.7.8.1's 34"-38". The door leaf hinges EAST (the
# default) and lies along the landing's east side when open, clear of this rail.
#
# The composite landing continuation has its east guard in params/breezeway.py; its west
# edge is closed by W-G-W itself.

RAILINGS = [
    Railing(uid="CX7KN0MZE0", tag="RL-G-SERVICE",
            path=(pt(ft(6, 9), ft(50, 9.625)), pt(ft(6, 9), ft(47, 2.625))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=ft(-2, -10), post_spacing=inch(48), post_size="2x2",
            rail_count=1, mount="wall", assembly="RAILING_DARK_METAL",
            role="handrail", serves_stair="ST-G-SERVICE", top_height=inch(36),
            graspable_profile="1.5in round — Type I"),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ROOFS,
            _GARAGE_LEADER_E, _GARAGE_LEADER_W, *ALARMS, *STAIRS, *RAILINGS,
            *STEM_TOP_Z_FLASHING]

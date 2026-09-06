# haus: editable
# Garage — freestanding 24'x24' ICF stem + 2x6 wood walls, 4' north of the house
# (west walls aligned). Wood walls sit on the ICF stem 22" above grade; the storey
# elevation is the top of the stem. Overhead door faces east (driveway side).
from typehaus import (
    Alarm,
    AlarmKind,
    Connector,
    ConnectorKind,
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
# 40'-8 5/8" is set by the breezeway off the *cladding*, not the stem: the stem's exterior
# EPS face is coplanar with the wood wall's SHEATHING face (both land on this line), so the
# most-proud plane is the 7/8" corrugated panel at y = 40'-7 3/4" — what the breezeway
# deck/glazing butt against, 4'-0 1/2" north of the house's cladding face
# (y = 36'-7 1/4"): one UNCUT 4'-0" polycarbonate panel with a 1/2" reveal.
#
# Moving the wall lines with the stem (rather than aligning the stem alone) keeps the
# breezeway slot and its uncut panel unchanged — see CLAUDE.md's ICF stem/wood-wall
# coplanarity note; do not move these nodes independently of the stem.
#
# ** THIS NODE LINE TRACKS THE CLADDING FACE — every time the house's cladding at y=36'
# stands further proud, this line moves north by the same amount to give the slot back. **
# The garage's own cladding face moves it too: `GARAGE_WALL_2X6` puts a 7/8" corrugated
# exposed-fastener panel where a 1/2" nail strip stood (the Zip-R-to-CDX swap behind it
# moves nothing — both sheathings land on this node line by the wall's own `alignment`), so
# 3/8" more panel standing proud is 3/8" less clear slot, and the node line gives it back.
#
# Each move spends the breezeway's reveal exactly: the slot has to stay 4'-0" on the nose
# because an uncut 4'-0" polycarbonate sheet cannot be glazed into an opening it exactly
# fills. Ripping the sheet was the detail-scale answer and is retired; this is the
# site-scale one, and it is the better trade because the reveal is the only thing in the
# slot that was ever free.
#
# ** DO NOT INSTEAD RECESS THE SHEATHING BEHIND THE NODE LINE to hold the cladding face
# still. ** That reopens a rain-shelf defect the stem alignment was built to fix: the stem's
# exterior EPS face would then stand proud of the wall above it, and the ledge that leaves
# is exactly the shelf water sits on.
# BOTH lines move together — the garage stays 24'-0" square, the stem, footings, slab and
# breezeway all derive from these two numbers, and nothing north of the house is dimensioned
# to a property line closer than 40'. Do NOT move the stem alone: CLAUDE.md's 1/2"
# ``_axis_match`` tolerance means the whole foundation follows via ``Footing.center_on``.
GARAGE_Y_SOUTH = ft(40, 8.625)
GARAGE_Y_NORTH = ft(64, 8.625)

# ICF stem height above grade == this storey's elevation (wood walls sit on the stem top).
# Published so the storey table, the stem (params/foundations.py) and the overhead door's
# drop to grade all read one value instead of three copies of 1'-10".
GARAGE_STEM_REVEAL = ft(1, 10)

NODES = [
    Node(uid="CGN001AAAA", tag="N-G-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGN002AAAA", tag="N-G-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGN003AAAA", tag="N-G-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGN004AAAA", tag="N-G-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
]

# 8'-4" plates, not 8'-0". The garage sits 4" down from grade while D-G-SERVICE's threshold
# stays pinned to the breezeway deck at 0'-0" — so the door climbs 4" inside its own wall,
# and its 3-ply LVL header needs that same 4" of plate above the rough head to clear the
# truss heels (structural.member_interference). The slab sits at the same grade, so the
# interior clear height is unchanged.
WALLS = [
    Wall(uid="CGW101AAAA", tag="W-G-S", start_node="N-G-SW", end_node="N-G-SE",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    # The overhead-door wall carried Western States "Classic Green" nail-strip for part of
    # 2026-08-26 and is back to the house white. The revert is one line: drop the
    # `layer_materials=` override and it is `GARAGE_WALL_2X6` like its three neighbours.
    # `standing-seam-nailstrip-26-green` is still in the catalog, referenced by nothing —
    # the same convention `glazed-green-brick` is kept under, so going green again is a
    # one-line change rather than a re-derivation.
    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", end_node="N-G-NE",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CGW103AAAA", tag="W-G-N", start_node="N-G-NE", end_node="N-G-NW",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW104AAAA", tag="W-G-W", start_node="N-G-NW", end_node="N-G-SW",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
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
# ** IT BREAKS AT BOTH STEM GAPS. ** There is no stem — and so no band and no Z — across the
# 16'-0" overhead door or the 3'-0" service door, where params/foundations.py drops the stem
# to a grade beam flush with grade. Six runs, ~76 3/4 LF: south 6'-3" + 14'-3", east 4'-0"
# twice, north and west 24'-0" each. The break stations are the stem's own gap nodes
# (N-GF-S-DRW/DRE at the service door's 3" margins, N-GF-E-DRS/DRN flush with the overhead
# door), authored as literals because this file is `# haus: editable` and the dialect bans
# arithmetic.
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
# turn-down hangs off the outboard end on all six runs and throws water clear of the band
# instead of back behind it. Get one direction wrong and the drip points at the wall with no
# finding: nothing grades `back_side`. Confirm it in the viewer.
STEM_TOP_Z_FLASHING = [
    Flashing(uid="4Z104BJ7TV", tag="TR-G-STEMZ-S1", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(0), ft(40, 8.225)), pt(ft(6, 3), ft(40, 8.225))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="8JZR6X0A4X", tag="TR-G-STEMZ-S2", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(9, 9), ft(40, 8.225)), pt(ft(24), ft(40, 8.225))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="7PK70E7009", tag="TR-G-STEMZ-E1", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(24, 0.4), ft(40, 8.625)), pt(ft(24, 0.4), ft(44, 8.625))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="HQQQFQ576Z", tag="TR-G-STEMZ-E2", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(24, 0.4), ft(60, 8.625)), pt(ft(24, 0.4), ft(64, 8.625))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="CZJZNX97MB", tag="TR-G-STEMZ-N", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(24), ft(64, 9.025)), pt(ft(0), ft(64, 9.025))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
    Flashing(uid="DHPT0K1FB2", tag="TR-G-STEMZ-W", kind=TrimKind.DRIP_FLASHING,
             path=(pt(inch(-0.4), ft(64, 8.625)), pt(inch(-0.4), ft(40, 8.625))),
             top_elevation=inch(-12.0), depth=inch(1.5), thickness=inch(0.8),
             material="aluminum-flat-pvdf", back_side="left"),
]

# Published so params/foundations.py can gap the ICF stem under the overhead door instead
# of repeating this offset/width: there is no 22"-above-grade stem wall under a vehicle
# door (it would be a curb the car has to climb), so the stem drops to a grade beam there.
# ** 4'-0" IS NO LONGER DEFENDED BY A WAINSCOT, AND THAT IS AN OPEN QUESTION. ** The 16'-0"
# opening's centre is at 12'-0", 12" off the 24" module, and it cuts 9 stud lines where 8
# would do — `structural.door_framing_module` reports it and names 11'-0"/13'-0" as the
# nearest legal centres. The advisory is suppressed in preferences.toml's `[checks]
# suppress`, and until 2026-09-03 THE REASON WAS THE WAINSCOT: moving the door 12" north
# would have made the two 4'-0" veneer piers flanking it 5'-0" and 3'-0", a visibly
# asymmetric wainscot on the garage's main facade bought with one stud. The wainscot is
# gone and that argument with it — the base band is now uniform on all four walls and does
# not care where the door sits.
#
# WHAT STILL HOLDS THE CONSTANT is the chain below it, which is real but is a cost of
# moving rather than a reason not to: params/foundations.py gaps the ICF stem into a grade
# beam on this offset, so the gap nodes, two stem segments, their footings and the two
# STEM_TOP_Z_FLASHING break stations above all travel with it, and plan/mep_sleeves.py's
# water-service sleeve is pinned to the stem footing that happens to be over it.
# ** DO NOT quietly re-decide this either way. ** It is an owner question now: one stud
# against a door centred on the framing module.
OVERHEAD_DOOR_OFFSET = ft(4)
OVERHEAD_DOOR_WIDTH = ft(16)  # DT-EXT-OVERHEAD192

# Same pair for the service door: identical treatment for the identical reason — it opens
# off the slab at grade, not the stem top its host wall starts on, so the stem gaps to a
# grade beam here too.
# ** 6'-6", AND NOT TO A NEARER STATION. ** GARAGE_WALL_2X6 frames stud lines at 24n along
# W-G-S, so a 36" RO must centre on one of them; the nearest legal stations short of 6'-6"
# either run the threshold off the end of SL-BW-DECK (`code.R311_3_exterior_landing` FAILs
# outright) or land 8" off the module, cutting two studs where one will do. 96" is also the
# BETTER station rather than merely the legal one: `D-M-ENTRY` is centred on x = 8'-0" too,
# so the two doors this breezeway spans are finally concentric.
# `params/breezeway.py::_GLAZING_CENTER_X` is the midpoint of the two, taking SL-BW-DECK to
# x 6'-0"..10'-0" and leaving this 36" leaf's jambs (7'-6"/9'-6") a foot of landing clear at
# each side.
#
# Moving this constant is never just moving a door: params/foundations.py gaps the ICF stem
# into a grade beam on it, so FT-GF-S-DR travels east too, and the water service's protection
# sleeve at x=5'-0" was left standing in the wrong pour. `integrity.sleeve_in_opening` caught
# it as an ERROR the moment the constant moved; the sleeve now names FT-GF-S1, the stem
# footing that is actually over it (plan/mep_sleeves.py). Nothing about the pipe changed —
# and FT-GF-S1 only grows westward-to-eastward as this offset climbs, so x=5'-0" stays over
# it.
SERVICE_DOOR_OFFSET = ft(6, 6)
SERVICE_DOOR_WIDTH = ft(3)  # DT-EXT-SWING36

OPENINGS = [
    # 16' opening is past the prescriptive header table, hence the named engineered beam:
    # a 2-ply 14" LVL.
    #
    # Threshold is the slab at grade, not the host wall's own floor: W-G-E starts at the
    # stem top, GARAGE_STEM_REVEAL above the slab, so the door reaches *down* past its host
    # — the plan's one negative sill_height, the exact negation of that reveal (spelled out
    # rather than computed; the dialect bans arithmetic). The tie is held by
    # test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade.
    # Head follows the threshold down to 7'-0" above the slab. params/foundations.py gaps
    # the stem to a grade beam under this opening so there's no curb for the car to climb.
    Door(uid="CGD201AAAA", tag="D-G-OVERHEAD", host="W-G-E",
         type_ref="DT-EXT-OVERHEAD192", position=from_node("N-G-SE", OVERHEAD_DOOR_OFFSET),
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
    Room(uid="CGR401AAAA", tag="RM-GARAGE", seed=pt(ft(12), ft(60)),
         occupancy=Occupancy.GARAGE, conditioned=False,
         floor_finish="sealed-concrete"),
]

# Gable roof, ridge E-W (rotated 90° vs the house), 16" overhangs. E/W walls stay flat 8'
# rather than `top=ToRoof`: a raked wall top must split at the ridge, but the 16' overhead
# door is centered on the ridge, so W-G-E can't be split. Both gable triangles are instead
# closed by the wall→roof closure in resolve/roof_edge.py, which reads its cladding
# material straight off the host wall's own layers — so a `Wall.layer_materials` override
# on one of these walls would carry into its gable triangle with nothing authored for the
# closure itself. None is authored today; W-G-E's green was reverted.
# Eave + rake trim is two-layer: a 2x6 wood sub-fascia (structural nailer) lapped by the
# weather face — brake-formed PVDF metal in "Copper Penny", six pieces, two eaves and four
# rakes, THE SAME COIL AS THE RIDGE CAP. One coil and one order for both: a cap in a
# different colour from the fascia under it reads as a
# mistake rather than as a choice. The substrate changed with the colour on purpose — a
# PVDF metallic is a metal coil finish PVC cannot be ordered in, and a dark trim colour on
# cellular PVC is the classic failure (PVC's thermal movement forces a solar-reflective
# vinyl-safe coating and an LRV cap). See the `metal-copper-penny` Material comment in
# plan/assemblies.py.
# The SOFFIT stays cellular PVC and stays white: vented, out of the weather, and a white
# soffit is what keeps an overhang from reading as a shadow. A vented PVC soffit closes the
# overhang and feeds the vent channel. Elevations derive from the resolved roof plane so the
# raised-heel lift carries the trim with it.
# The SOUTH eave gets a 5" gutter in the house's dark exterior coil (params/roof_trim.py
# ::_CHAIN_MATERIAL — mill aluminium read as a pale band under a dark edge): that slope
# faces the 4' breezeway gap and the house wall people walk under, and now also catches what sheds off the breezeway roof.
# North eave stays free-draining onto open ground. Declared here rather than in params/
# for the same reason as the fascia — the raised-heel truss lifts the deck plane at the
# envelope stage, so an absolute elevation would drift off the eave.
_GARAGE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="metal-copper-penny", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
    gutter=EaveGutter(material="metal-dark-kstyle", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("south",),
                      slope="1/16 in/ft to the east downspout",
                      downspout_ref="TR-G-LEADER-E"),
)

# The leader the south gutter has always sloped to; named in the slope note but never
# authored until now, so it drained to nothing. 3" round, not the house's 4": this slope
# sheds ~290 sq ft against each house eave's 648, and 3" clears ~425 sq ft at the 8 in/hr
# design intensity (params/roof_trim.py works the number).
# test_drainage_elements.py holds this and the EaveGutter together so a roof change that
# moves the trough fails there instead of leaving a leader hanging beside it.
_GARAGE_LEADER = Downspout(
    uid="CGDS01AAAA", tag="TR-G-LEADER-E",
    position=pt(ft(25), ft(39, 5.375)),     # east end of the trough, on its centreline
    # Both absolute. The trough they bracket is derived from the roof plane, so it moves on
    # its own if the roof does; these are the two numbers that have to follow it by hand.
    top_elevation=ft(7, 6),             # inside the trough floor
    bottom_elevation=ft(-1, -6),        # splash block, a foot above the apron
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
         pitch=Pitch(4, 12), bearing_refs=("W-G-S", "W-G-N"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="x",
         edge_trim_material="metal-copper-penny",
         eave_trim=_GARAGE_EAVE_TRIM),
]

# Snow retention on the south slope: the garage roof sheds toward the breezeway's
# polycarbonate canopy (GL-BW-ROOF), which sits 3.0' below this eave in the discharge band
# (structural.sliding_snow) — a willing 4:12 standing-seam slope over an unwilling
# multiwall-polycarbonate target.
# S-5! ColorGard: a continuous crossbar on seam clamps (StructuralHardware.requires_role
# bills the clamps automatically). Row runs x 1'-4"..8'-0" — canopy width plus a full bay of
# margin each end, since snow releases at an angle. Row count/spacing at Pg = 50 psf is the
# manufacturer's calculation; the check only screens for retention being *authored*.
# Placed 4" up-slope of the eave (y = 39'-6 7/8", z = 8'-1"), deliberately close to it since
# retention holds the pack where the load lives. Both are absolute elevations tied to the
# wall line and the roof plane, not derived — move either and these must follow by hand.
# Written out, not generated: the editable dialect allows no comprehensions.
_SNOW_GUARD_Y = ft(39, 7.25)
_SNOW_GUARD_Z = ft(8, 1)
_SNOW_GUARD_SIZE = "S-5! ColorGard"
SNOW_GUARDS = [
    Connector(uid="CGSG01AAAA", tag="CN-G-SNOW-1", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(1, 4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG02AAAA", tag="CN-G-SNOW-2", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(2, 8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG03AAAA", tag="CN-G-SNOW-3", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG04AAAA", tag="CN-G-SNOW-4", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(5, 4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG05AAAA", tag="CN-G-SNOW-5", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(6, 8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG06AAAA", tag="CN-G-SNOW-6", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
]

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
# flight — GARAGE_Y_SOUTH + 3'-0" of landing + 4 x 11" of tread = 47'-2 3/8" — and it climbs
# south (`run_reversed`) back to the landing's north edge. All three y literals below
# move with GARAGE_Y_SOUTH.
#
# 11" treads with NO nosing, which keeps the run at the 3'-8" the four slabs occupied and
# leaves an 11" going against R311.7.5.2's 10" minimum. A nose would shorten the run and buy
# nothing here.
STAIRS = [
    Stair(uid="X99TD38ZS3", tag="ST-G-SERVICE",
          from_storey="garage", to_storey="garage",
          base_elevation=ft(-2, -10), top_elevation=ft(0),
          width=ft(3), start=pt(ft(5), ft(47, 3.25)),
          run_direction="y", run_reversed=True,
          tread_depth=inch(11), nosing_depth=inch(0),
          material="kdat"),
]

# R311.7.8 wants a handrail on any flight of four or more risers, and this one has five.
# Nothing was asking for it while the flight was five slabs, because both handrail rules
# iterate `model.stairs`.
#
# Post-mounted on the west side of the run, not wall-mounted: the flight stands in the
# open on the garage floor at x=5'..8', with the nearest wall 5'-0" away. The posts stand on
# the treads (`serves_stair` rakes the rail along the flight's nosing line) and the rail
# tops out 36" above them, inside R311.7.8.1's 34"-38".
#
# FLAGGED, NOT ANSWERED: the landing at 0'-0" is **34" above the garage slab**, over
# R312.1.1's 30" threshold, so its open east and north sides want a guard as well as this
# handrail. That is a design decision with a cost and a look to it, and it is the owner's,
# not this file's.
#
# **Nothing in the engine will ask.** `code.R312_1_guard_height` censuses `FloorSystem`s and
# `code.R312_1_guard` censuses `FloorOpening`s; SL-G-STEP-0 is a `Slab`, so it is in neither
# census and its 34" drop is invisible to both. That is a real coverage gap, not a pass —
# recorded in plans/TODO.md rather than papered over here, because the fix is a rule that
# walks slab edges and belongs with the guard rules, not with this stair.
RAILINGS = [
    Railing(uid="CX7KN0MZE0", tag="RL-G-SERVICE",
            path=(pt(ft(5), ft(47, 3.25)), pt(ft(5), ft(43, 7.25))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=ft(-2, -10), post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="handrail", serves_stair="ST-G-SERVICE", top_height=inch(36),
            graspable_profile="1.5in round — Type I"),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ROOFS,
            _GARAGE_LEADER, *SNOW_GUARDS, *ALARMS, *STAIRS, *RAILINGS,
            *STEM_TOP_Z_FLASHING]

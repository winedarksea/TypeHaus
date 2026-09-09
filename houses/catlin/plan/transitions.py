# haus: editable
# Catlin transition library — documentation overlays never alter resolved geometry.
# Editable so the UI's detail star toggle (Transition.star and the per-condition
# starred_conditions/unstarred_conditions overrides — the permit-set curation flags)
# round-trips to source; the geometry-free fields here are still design decisions.

from typehaus import Continuity, Transition


# The three planes every envelope crossing in this house has to carry through. `wrb-ext`
# and `ci-ext` both land on the SAME face now — closed-cell spray foam is the water plane
# and the insulation in one bonded, seamless application, which is why there is no membrane
# above it. The air plane stays on the sheathing: it is the one of the three that is
# continuous through a foundation or a stack-width crossing where there is no foam at all.
#
# The build order this implies belongs on every sheet that carries this tuple: with no WRB,
# the foam IS the water barrier, so it is sprayed AFTER the window bucks are set, never
# before. See notes/outie_window_truss_detail.md.
AIR_WATER_THERMAL = (
    Continuity(control="air", from_face="sheathing-ext", to_face="sheathing-ext"),
    Continuity(control="water", from_face="spray-foam-ext", to_face="spray-foam-ext"),
    Continuity(control="thermal", from_face="spray-foam-ext", to_face="spray-foam-ext"),
)

# A star is a claim about the SUBMITTAL, not about whether a detail is worth drawing.
# `haus print` (`--set permit`) keeps exactly the starred derived details; everything else
# still derives and still prints under `--set full`. The set carried 33 of them, which is
# where "too many sheets" came from: sixteen of those were one rim-band drawing repeated
# for every pair of assemblies that happens to meet at a floor line.
#
# The test a key has to pass to stay starred: does a plan checker or a framer open THIS
# sheet, and is it a different drawing from the one next to it?
TRANSITIONS = (
    # Two eaves in this project and they are genuinely two drawings: the house's
    # zero-overhang eave over EXT_2X6, and the garage's over a trussed roof with a raised
    # heel on a wall with no WRB. The four interior-partition-to-roof keys are unstarred —
    # a partition dying into the ceiling plane has no eave at all: no soffit, no fascia, no
    # vent, and none of the three control layers to hand off. It is framing, and it is
    # drawn on S-101.3.
    Transition(uid="CATR001AAAA", tag="TR-CATLIN-EAVE", condition_pattern="wall_roof:*",
               notes="notes/roof_wall_eave_detail.md", overlay="zero-overhang-eave",
               continuity=AIR_WATER_THERMAL, star=False,
               starred_conditions=(
                   "wall_roof:EXT_2X6|ROOF",
                   "wall_roof:GARAGE_ROOF|GARAGE_WALL_2X6",
               )),
    # The envelope crossing — concrete to framed wall, where the thermal, air and water
    # layers all have to hand off. Named keys rather than a pattern-wide star, and two of the five: the perimeter
    # basement wall meeting the framed wall above it, and the garage's ICF stem meeting
    # its own framed wall — the garage/house separation a reviewer looks for. The 8" wall
    # is the same drawing as the 12" (only the sill plate sits 4" further in), by the same
    # argument TR-CATLIN-BASEMENT-OPENING already makes for a window in either; and the
    # garden curb and the sauna liner on it are a 7-1/4" upstand in a sunken court, not an
    # envelope crossing anybody inspects. All four still derive under `--set full`.
    Transition(uid="CATR002AAAA", tag="TR-CATLIN-FOUNDATION",
               condition_pattern="wall_foundation:*",
               notes="notes/basement_to_framed_wall_detail.md",
               overlay="basement-framed-wall", continuity=AIR_WATER_THERMAL,
               documents_rules=("CR-CONC-TO-FRAMED-SILL", "CR-FOUNDATION-FOAM-RETURN"),
               star=False,
               starred_conditions=(
                   "wall_foundation:BASEMENT_12|EXT_2X6",
                   "wall_foundation:GARAGE_ICF_6|GARAGE_WALL_2X6",
               )),
    # ** UNSTARRED WHOLE. ** Sixteen conditions derived off this one pattern and every one
    # of them is the same drawing: a membrane strip lapped over the plate line, sealant at
    # the plate, and the rim bay filled. What differs between them is which two assemblies
    # happen to meet, which is a schedule fact and not a drawing. Sixteen near-identical
    # sheets in a submittal is how a reviewer learns to stop turning pages.
    #
    # The rim band still has a sheet in the permit set: TR-CATLIN-PLANT-RIM, which is the
    # one place in this house where the detail is NOT an air seal at 35% RH but the
    # continuity of a Class I vapour barrier at 70%. All sixteen still derive and still
    # print under `--set full`, which is where a builder reads them.
    Transition(uid="CATR003AAAA", tag="TR-CATLIN-RIM-BAND",
               condition_pattern="storey_stack:rim:*", overlay="rim-band-air-seal",
               continuity=AIR_WATER_THERMAL, star=False),
    # No notes= here, deliberately: this condition pattern is a wildcard over every
    # stack-width change in the house (partition-to-partition, sauna liner, plant room,
    # mudroom, and the garage's masonry-to-framed curb among them), and the garage's own
    # narrative note would land on all of them if pointed at from here. The garage curb
    # gets its narrative from TR-CATLIN-GARAGE-OPENING below instead, which is genuinely
    # scoped to GARAGE_WALL_2X6.
    Transition(uid="CATR004AAAA", tag="TR-CATLIN-STACK-SHELF",
               condition_pattern="stack_width_change:*", overlay="stack-width-shelf",
               continuity=AIR_WATER_THERMAL),
    # THE OUTIE WINDOW. The unit sits in the truss plane, 5" outboard of the sheathing, so
    # the innie `window-head-jamb-sill` recipe — which measures its head flashing and sill
    # pan from the sheathing face — draws neither piece where it now goes.
    # `outie-window-truss` is its sibling.
    Transition(uid="CATR005AAAA", tag="TR-CATLIN-FRAMED-OPENING",
               condition_pattern="opening_perimeter:EXT_*",
               notes="notes/outie_window_truss_detail.md", overlay="outie-window-truss",
               continuity=AIR_WATER_THERMAL, star=True),
    Transition(uid="CATR006AAAA", tag="TR-CATLIN-CONCRETE-OPENING",
               condition_pattern="opening_perimeter:FOUNDATION_WALL_*_INT",
               notes="notes/sauna_basement_wall_detail.md", overlay="concrete-opening"),
    # ``BASEMENT_[0-9]*`` covers every perimeter foundation assembly: the N/W wall with
    # its above-grade protection band, the 12" east wall, and the two buried ends of the
    # south wall. They differ in what covers the exterior XPS, a field condition well
    # outside an opening's perimeter, and in the pour depth — but the buck, the frame and
    # the flashing at a window in cast concrete are the same detail at 8" as at 12" (only
    # the jamb gets 4" shallower), and one sheet is what draws them.
    Transition(uid="CATR007AAAA", tag="TR-CATLIN-BASEMENT-OPENING",
               # The [0-9] is load-bearing, not decoration: a bare ``BASEMENT_*`` also
               # swallows BASEMENT_BRICK_VENEER, whose perimeter is an open segmental arch
               # that TR-CATLIN-VENEER-OPENING deliberately SUPPRESSES. Widening this glob
               # silently re-adds a detail sheet for a perimeter with no perimeter work.
               condition_pattern="opening_perimeter:BASEMENT_[0-9]*",
               notes="notes/basement_to_framed_wall_detail.md", overlay="foundation-window"),
    # Starred: the garage/breezeway threshold condition — both doors open onto the slab
    # at grade, with the ICF stem dropped to a grade beam under them, so the perimeter
    # flashing here is nothing like a standard framed opening.
    # Same reasoning as the garden arch above, one wall further north: the reveals through
    # W-B-BRICK are open arched holes in a freestanding wythe, and the flashed, bucked,
    # sealed opening is the one in the concrete/framed wall behind them (TR-CATLIN-
    # BASEMENT-OPENING already draws that). A second sheet here would detail a perimeter
    # that has no perimeter work.
    Transition(uid="CATR015AAAA", tag="TR-CATLIN-VENEER-OPENING",
               condition_pattern="opening_perimeter:BASEMENT_BRICK_VENEER",
               suppress=True,
               # (single literal: the editable dialect forbids concatenated strings)
               suppress_reason="the veneer reveal is an open segmental arch in a freestanding brick wythe standing 1-1/2\" off the basement wall — no buck, no frame, no flashing lands at its perimeter, and the opening that does get all three is the window/door in the concrete wall behind it, detailed by TR-CATLIN-BASEMENT-OPENING"),
    # The sunken garden's framed walkout. D-B-PATIO is an ordinary innie opening in a 2x6
    # wall — buck, pan, jamb flashing — standing on the 7 1/4" concrete curb.
    # `window-head-jamb-sill` rather than the `outie-window-truss` the above-grade
    # EXT_* walls take: there is no truss plane down here, the unit sits in the stud
    # plane, and the wall's water plane is the damp-proofing over the sheathing.
    # SAUNA_LINER_ON_GARDEN_FRAMED needs nothing here — WIN-B-SAUNA's perimeter is the
    # vapour-control return TR-CATLIN-SAUNA-OPENING already draws, and its `SAUNA_*`
    # pattern reaches the framed variant unchanged.
    Transition(uid="6997Z5EY26", tag="TR-CATLIN-GARDEN-FRAMED-OPENING",
               condition_pattern="opening_perimeter:GARDEN_FRAMED_2X6",
               notes="notes/basement_to_framed_wall_detail.md",
               overlay="window-head-jamb-sill", continuity=AIR_WATER_THERMAL),
    # ** IT DECLARES ITS OWN CONTINUITY, and it is not AIR_WATER_THERMAL. ** GARAGE_WALL_2X6
    # has no WRB at all — IRC R703.2's exception for an unconditioned detached accessory
    # building — so there is no `spray-foam-ext` band and no taped Zip-R face for the
    # house's tuple to name. What carries all four controls here is the 2" of ccSPF IN THE
    # BAYS (`stud-cavity`), which is why the build order on notes/garage_wall_detail_side.md
    # is bucks before foam, exactly as it is on the house. The air plane is the foam too,
    # not the sheathing: bare CDX is not taped and is not an air barrier, which is the whole
    # difference from the house's `sheathing-ext` row.
    Transition(uid="CATR009AAAA", tag="TR-CATLIN-GARAGE-OPENING",
               condition_pattern="opening_perimeter:GARAGE_WALL_2X6",
               notes="notes/garage_wall_detail_side.md", overlay="garage-opening",
               continuity=(Continuity(control="air", from_face="stud-cavity",
                                      to_face="stud-cavity"),
                           Continuity(control="water", from_face="stud-cavity",
                                      to_face="stud-cavity"),
                           Continuity(control="vapor", from_face="stud-cavity",
                                      to_face="stud-cavity"),
                           Continuity(control="thermal", from_face="stud-cavity",
                                      to_face="stud-cavity")),
               star=True),
    Transition(uid="CATR010AAAA", tag="TR-CATLIN-INTERIOR-OPENING",
               condition_pattern="opening_perimeter:INT_*", overlay="interior-opening"),
    Transition(uid="CATR011AAAA", tag="TR-CATLIN-CENTER-OPENING",
               condition_pattern="opening_perimeter:INT_2X6_BRG",
               overlay="bearing-partition-opening"),
    # D-A-STUDY's opening in the study bookcase wall. It needs its OWN binding rather than
    # falling under TR-CATLIN-INTERIOR-OPENING's `INT_*` glob, for the same reason
    # INT_2X6_BRG does: the tag starts "CATLIN_", so the glob never sees it.
    # The overlay is the interior-opening sheet, which is the right drawing — what is
    # different here is not the perimeter detail but the LEAF (a ~250 lb bookcase door) and
    # the hinge-side jamb behind it, and neither is a perimeter condition. Both are recorded
    # on DT-INT-BOOKCASE30 and on W-A-SN.
    Transition(uid="QZCDFYBATE", tag="TR-CATLIN-BOOKCASE-OPENING",
               condition_pattern="opening_perimeter:INT_2X4_BOOKCASE_12",
               overlay="interior-opening"),
    # D-S-BATH1's opening in the hall bath's east wet wall, which is BEARING and was
    # retyped with it. Its own binding, same reason as the others: the tag starts
    # "CATLIN_", so TR-CATLIN-INTERIOR-OPENING's `INT_*` glob never sees it. The overlay is
    # the bearing partition's, not the plain interior one — the jack/king studs at a door in
    # a wall carrying an attic joist field are the point of the sheet.
    Transition(uid="KNP02ZZ5WC", tag="TR-CATLIN-WETWALL-OPENING",
               condition_pattern="opening_perimeter:INT_2X6_BRG_PLUMBING",
               overlay="bearing-partition-opening"),
    # D-B-CLOSET's opening in W-B-STR3, the under-stair closet's door (2026-09-05). Its own
    # binding for the same reason as the four above: the tag starts "CATLIN_", so
    # TR-CATLIN-INTERIOR-OPENING's `INT_*` glob never sees it. `bearing-partition-opening`
    # and not the plain interior sheet — W-B-STR3 is BEARING (FS-M-MECH and FS-M-STAIR both
    # name it), so the jack/king pack at this door is exactly what the sheet is for.
    Transition(uid="4K0XA3X1TX", tag="TR-CATLIN-UNDERSTAIR-OPENING",
               condition_pattern="opening_perimeter:STAIRWALL_INT_2X6_BRG_UNDERSTAIR",
               overlay="bearing-partition-opening"),
    # D-M-BED2's opening in W-M-C1, the bedroom segment of the centreline. Same reason as
    # the others: the tag starts "CATLIN_", so TR-CATLIN-INTERIOR-OPENING's `INT_*` glob
    # never sees it. An exact binding rather than widening TR-CATLIN-CENTER-OPENING to
    # `INT_2X6_BRG*`, because that glob would also swallow
    # INT_2X6_BRG_PLUMBING above and put two transitions on one condition. Same
    # `bearing-partition-opening` overlay as the plain centreline: the jack/king pack at
    # this door is the sheet's subject and the resilient channel does not change it — a
    # channel dies into the opening's return and carries no load.
    Transition(uid="2M8HCPVAXB", tag="TR-CATLIN-CENTER-RC-OPENING",
               condition_pattern="opening_perimeter:INT_2X6_BRG_RC",
               overlay="bearing-partition-opening"),
    # Two legitimate in-plan assembly changes survive the resolver's derivation gates
    # (the sauna liner starting along the interior concrete run, and the masonry railing
    # meeting the retaining wall's 6" upstand). They are bound — covered, continuity
    # declared, construction rules documented — but deliberately sheetless.
    Transition(uid="CATR012AAAA", tag="TR-CATLIN-ASSEMBLY-JOG",
               condition_pattern="assembly_change:*",
               continuity=AIR_WATER_THERMAL,
               documents_rules=("CR-CONC-TO-FRAMED-SILL", "CR-SAUNA-LINER-RETURN",
                                "CR-PORCH-MASONRY-RETURN"),
               suppress=True,
               # (single literal: the editable dialect forbids concatenated strings)
               suppress_reason="the jog happens *along* the wall run, while a derived detail cuts perpendicular to the wall — the change of assembly is simply not in that cut plane, so any sheet here would describe a junction the drawing does not show; the returns themselves are documented by the construction rules this transition records"),
    # The sauna door breaks the hot side's vapour control layer — the foil-faced polyiso
    # has to be returned into the jamb and sealed, not just butted.
    Transition(uid="CATR014AAAA", tag="TR-CATLIN-SAUNA-OPENING",
               condition_pattern="opening_perimeter:SAUNA_*",
               notes="notes/sauna_basement_wall_detail.md", overlay="sauna-liner-opening",
               continuity=(Continuity(control="vapor", from_face="foil-polyiso",
                                      to_face="foil-polyiso"),
                           Continuity(control="air", from_face="foil-polyiso",
                                      to_face="foil-polyiso")),
               # Unstarred for the SUBMITTAL only (2026-09-08). It is a durability detail
               # inside an already-conditioned basement — no code line turns on it and no
               # inspection is run against it — and the permit set already carries the same
               # drawing at a higher RH on TR-CATLIN-PLANT-OPENING. Both still derive, and
               # `--set full` is what the installer is handed.
               star=False),
    # The plant room's rim band, and the hardest detail in the room. FS-S-WEST and FS-ATTIC
    # both run their joists in x, so the ends bear on W-S-W4 and a parallel rim bay sits
    # against W-S-S1: two direct paths from a floor cavity into the coldest part of an
    # exterior wall, and neither can take a sheet membrane — there is no continuous plane to
    # lap it onto between the joist ends. Closed-cell spray foam at the rim in BOTH floor
    # systems along both walls is the answer: bonded, monolithic, no seams, and its own
    # vapour retarder, which is the only product that is simultaneously the air barrier, the
    # vapour barrier and the insulation in a cavity shaped like that one.
    #
    # Its own sheet rather than a note on TR-CATLIN-RIM-BAND: everywhere else in this house
    # the rim band is an air-seal detail at 35% RH, and here it is the continuity of a
    # Class I barrier at 70%.
    Transition(uid="CATR017AAAA", tag="TR-CATLIN-PLANT-RIM",
               condition_pattern="storey_stack:rim:*PLANT_*",
               # Same drawn vocabulary as TR-CATLIN-RIM-BAND (membrane strip, plate-line
               # sealant, rim cavity foam), so it reuses that recipe rather than inventing a
               # near-identical one; what differs here is the SPEC on it — closed-cell,
               # full-depth, and doing the vapour barrier's job — which is what the notes
               # page and this transition's continuity carry.
               notes="notes/plant_room.md", overlay="rim-band-air-seal",
               continuity=(Continuity(control="vapor", from_face="humid-membrane",
                                      to_face="rim-foam"),
                           Continuity(control="air", from_face="humid-membrane",
                                      to_face="rim-foam")),
               star=True),
    # The plant room's openings. Cloned from TR-CATLIN-SAUNA-OPENING above for the same
    # reason and with the same shape: an opening is a hole in the only thing keeping moist
    # room air out of the stud bays, so the membrane is *returned into the jamb* and sealed
    # to the window/door frame, not butted at the panel edge. `PLANT_*` catches all three
    # assemblies at once — the exterior wall, the bearing line and the two partitions all
    # carry the same liner, so the head/jamb/sill detail is the same sheet on each.
    #
    # Starred: this is the detail the room lives or dies by, and the one a glazier and a
    # framer have to read together. It also carries the drained sill pan under every unit —
    # sloped, flashed into the wall membrane, draining to the room and never into framing —
    # which no other opening detail in this house needs.
    Transition(uid="CATR016AAAA", tag="TR-CATLIN-PLANT-OPENING",
               condition_pattern="opening_perimeter:PLANT_*",
               notes="notes/plant_room.md", overlay="humid-liner-opening",
               continuity=(Continuity(control="vapor", from_face="humid-membrane",
                                      to_face="humid-membrane"),
                           Continuity(control="air", from_face="humid-membrane",
                                      to_face="humid-membrane")),
               star=True),
    Transition(uid="CATR013AAAA", tag="TR-CATLIN-RIDGE-BEAM",
               condition_pattern="roof_ridge:*", overlay="lvl-ridge-hanger"),
)

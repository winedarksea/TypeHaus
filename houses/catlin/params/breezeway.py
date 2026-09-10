"""North entry: a real canopy structure, a piered landing, and box-framed east tiers.

Everything here used to be schematic. The landing hung off the house basement walls on
six invented "seat" connectors, the 6'-0" roof extrusion over the passage stood on
nothing, and two engine escapes kept the engine from saying so. This file now authors
the structure: three cast piers, two headers extending the garage's own truss bearing
lines south onto two KDAT columns, and a canopy roof (RF-BW-CANOPY, in
plan/storeys/garage.py) spanning between them.

**The landing touches nothing on the house.** No element below names a `W-B-*` tag; grep
and expect nothing. Its house-side bearing is two piers on the pier line at y=37'-6", not
brackets standing off the basement concrete.

See notes/north_entry_structure.md for the bearing map and notes/north_entry_piers.md for
the hand-worked pier, header and drift derivation this file's sizes come from.

**KDAT longevity, house-wide (owner, 2026-09-10).** Every treated member here is KDAT and
carries the same four-part detail, which is why it is stated once rather than on each
element: 304 stainless fasteners; butyl joist tape over every beam and rim top
(`top_protection`); AWPA M4 field treatment of every cut end, notch and drilled hole with
2% copper naphthenate (IRC R317.1.1 makes this "shall", not advice); and a pigmented
penetrating oil finish applied on installation. AN-BW-KDAT carries it onto the drawings.
"""

from typehaus import (
    Annotation, Beam, Connector, ConnectorKind, DeckLayer, Footing, FloorSystem, JoistSpec,
    Node, Post, Railing, RailingKind, SlatScreen, Stair, ft, inch, pt,
)

from params.foundations import SITE_GRADE
from plan.storeys.garage import GARAGE_Y_SOUTH

HOUSE_CLADDING_Y_FT = 36 + 7.25 / 12
GARAGE_CLADDING_Y_FT = GARAGE_Y_SOUTH.feet - 0.875 / 12
GARAGE_INSIDE_Y_FT = GARAGE_Y_SOUTH.feet + 11 / 12
LANDING_WEST_FT = 6.0  # extra west margin keeps screen/guard outside both 36in door patches
LANDING_EAST_FT = 11.5
GARAGE_LANDING_WEST_FT = 8.5
GARAGE_LANDING_END_Y_FT = GARAGE_INSIDE_Y_FT + 3
DECK_FINISH_FT = 0.0
DECK_JOIST_TOP_FT = -1 / 12
JOIST_DEPTH_IN = 7.25
MOVEMENT_GAP_IN = 0.25
DETAIL_CUT_Y_FT = (HOUSE_CLADDING_Y_FT + GARAGE_CLADDING_Y_FT) / 2

# ** THE PIER LINE IS AT y=37'-6", AND THE 3 3/8" IT MOVED NORTH IS NOT COSMETIC. **
# W-B-N2/N3 is BASEMENT_8 on an axis at y=36'-0", so its concrete face is y=36'-4" and its
# cladding face y=36'-7 1/4". At the first-drafted y=37'-2 5/8" a 12" round leaves 1 3/8"
# to the cladding and 4 5/8" to the concrete: not formable, and it means excavating hard
# against the house foam. At 37'-6" those clears become 6 3/4" and 10 3/4".
#
# ** AND IT IS A SEQUENCING NOTE BEFORE IT IS A DETAIL NOTE. ** These piers bottom at the
# same elevation as the house footing, about 10" away. Cast in the open basement
# excavation -- the owner's premise, and why reaching this depth is cheap -- that is a
# non-issue. Cast AFTER the house footing is in and backfilled, a shaft 10" away bearing at
# the same depth is undermining, and the answer becomes benching the excavation or bearing
# the pier higher and lengthening the column. It belongs on the drawings.
PIER_LINE_Y_FT = 37.5
PIER_BOTTOM_FT = -(9 + 9.4375 / 12)   # the house footing underside, -9'-9 7/16"
# 10", not 12". The garage hydrant line runs at -8'-10"; a 12" pad tops out at -8'-9 7/16"
# and swallows it, and a water line cast through a spread footing is a sleeve detail nobody
# should need here. At 10" the pad tops out at -8'-11 7/16" and the pipe passes 1 7/16" clear
# above it. 10" is still ample for a 2'-0" pad at these loads.
FOOTING_DEPTH_FT = 10 / 12
FOOTING_TOP_FT = PIER_BOTTOM_FT + FOOTING_DEPTH_FT
# Every landing bearing is cast concrete up to -0'-8 1/4" on BOTH sides, so no treated
# member lies below the deck framing. Site.grade is -2'-10", so this is 25 3/4" ABOVE
# finished grade -- the post bases are already clear of snow, splash and de-icer, and the
# once-proposed "carry the pier a foot higher" line item was based on a wrong picture of
# the site and is deleted.
# ** THE SEATS ARE DROPPED, NOT FLUSH, AND THE MODEL SETTLES THAT. ** Flush framing -- every
# beam soffit on one plane, floor beams hung off the seats -- is real construction and reads
# in the engine as fifteen `structural.member_interference` FAILs, because two beams crossing
# at one elevation DO occupy the same space in a model that has no hanger. So the floor beams
# sit ON the seats: seat top -0'-8 1/4" (the floor beams' soffit), seat soffit -1'-3 1/2".
SEAT_TOP_FT = DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12      # -0'-8 1/4"
BEARING_TOP_FT = SEAT_TOP_FT - JOIST_DEPTH_IN / 12         # -1'-3 1/2", 18 1/2" above grade

# The headers top out at the GARAGE PLATE, +7'-4" (W-G-E/W-G-W z1). That is what makes
# RF-BW-CANOPY one plane with RF-GARAGE rather than a roof stepping off it. A 3-ply 2x12 is
# 11 1/4" deep, so the soffit lands at +6'-4 3/4" -- which is also where SC-BW-WEST stops.
HEADER_TOP_FT = 7 + 4 / 12
HEADER_SOFFIT_FT = HEADER_TOP_FT - 11.25 / 12
ROOF_COLUMN_EAST_X_FT = 30.0

# The two members within the service opening continue to the interior stair. The west
# member stops outside: the two-foot door offset cannot be bridged through a solid jamb.
BEAM_WIDTH_IN = 3.0
# ** THE WEST FLOOR BEAM IS OFF THE COLUMN LINE ON PURPOSE. ** PT-BW-CW is a 6x6 standing on
# the pier at x=6'-0" and rising past the deck to the header, so it occupies the deck's own
# -1" to -8 1/4" band. A floor beam on the same line interpenetrates it outright
# (`structural.member_interference` says so). 6'-6" puts the beam's west face 3 1/4" clear of
# the post, the deck SHEET still runs to x=6'-0" past it, and the joists cantilever 6" west
# against R507.6.1's quarter of their 2'-1 1/2" back span (6 3/8"). The screen and the guard
# stay on x=6'-0", in the column line, which is where they want to be.
WEST_BEAM_X_FT = 6.5
BEAM_X_FT = (WEST_BEAM_X_FT + BEAM_WIDTH_IN / 24,
             GARAGE_LANDING_WEST_FT + BEAM_WIDTH_IN / 24,
             LANDING_EAST_FT - BEAM_WIDTH_IN / 24)
HOUSE_SEAT_Y_FT = PIER_LINE_Y_FT
# ** THE GARAGE SEAT MOVED 6" SOUTH, OFF THE STEM. ** A pedestal under it at the old
# y=42'-11 3/4" overlapped W-G-S's bottom plate and its corner post outright, and the stem's
# concrete core is north of the beam line anyway -- which is why the retired design reached it
# with brackets standing off the concrete FACE. At 42'-7 3/4" the seat and its two piers stand
# clear of the garage wall entirely, and the floor beams cantilever 5 1/4" north to the
# framing edge, inside R507.5.1's quarter of the 5'-1 3/4" back span (15 3/8").
GARAGE_SEAT_Y_FT = GARAGE_CLADDING_Y_FT - 8 / 12

# ** MOVING THE SEAT NORTH FORCES A SOUTH FRAMING EDGE, AND SKIPPING IT SETS OFF A CASCADE. **
# With the seat beam at y=37'-6" the deck sheet would run 12 1/4" to the cladding over air.
# That is past `structural.subfloor_oversail`'s 8" bound -- which is not that check's own
# number but `preferences.toml [framing] bearing_plan_tolerance_in`, the same allowance
# `takeoff/uplift.py` uses to decide whether a member's end lands on a support. Past it the
# uplift pass finds neither a derived tie nor a hanger and FAILs every member under the
# deck, reported nowhere near its cause. No composite board allows a 12" overhang either;
# 1" to 4" past the last joist is the usual limit.
#
# So the joist field itself runs south to y=36'-8 1/2" on the three floor beams, which
# cantilever 9 1/2" past the seat -- inside R507.5.1's quarter of the 5'-5 3/4" back span
# (16 3/8"). The southernmost joist IS the rim; the joists run in x, so a separate rim
# member on this edge would be a second joist in the same place.
FRAME_Y0_FT = 36 + 8.5 / 12
FRAME_Y1_FT = GARAGE_CLADDING_Y_FT - 0.75 / 12
# ** HOLD THE BOARDS OFF THE HOUSE AND LET THE GAP DRAIN. ** Boards run tight to a
# rainscreened wall dam the drainage plane and hold water against the cladding. Abutting is
# not bearing, so this does not compromise "the landing touches nothing on the house" -- but
# it has to be DRAWN, because a carpenter will otherwise close it.
DECK_SHEET_SOUTH_Y_FT = HOUSE_CLADDING_Y_FT + 0.5 / 12


def rectangle(x0, y0, x1, y1):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)),
            pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


NODES = []
BEAMS = []


def beam(number, tag, x0, y0, x1, y1, bearings, top=DECK_JOIST_TOP_FT, size="2-2x8",
         assembly="BEAM_KDAT"):
    for end, x, y in (("S", x0, y0), ("N", x1, y1)):
        NODES.append(Node(uid=f"BWNB{number:02d}{end}AAA", tag=f"N-{tag}-{end}",
                          position=pt(ft(x), ft(y))))
    result = Beam(uid=f"BWB{number:03d}AAAA", tag=tag,
                  start_node=f"N-{tag}-S", end_node=f"N-{tag}-N", size=size,
                  top_elevation=ft(top), bearing_refs=bearings, assembly=assembly,
                  top_protection="butyl-tape-beam")
    BEAMS.append(result)
    return result


# The two seat beams, both on cast concrete at -0'-8 1/4" and both spanning 5'-6" between
# two bearings. They grade the same way as a result: `structural.deck_beam_span` reads a
# real 5'-6" span off two Posts on each, rather than one falling back to a length.
# The two seat beams. Nothing could bear these before: the garage stem tops out at -1'-0",
# ABOVE this soffit and north of the beam line, which is exactly why six invented stand-off
# brackets existed. Both now land on two cast piers each, at the same elevation and on the
# same 5'-6" span, so `structural.deck_beam_span` grades them identically.
beam(1, "BM-BW-HOUSE-SEAT", LANDING_WEST_FT, HOUSE_SEAT_Y_FT,
     LANDING_EAST_FT, HOUSE_SEAT_Y_FT, ("PT-BW-W", "PT-BW-E"), SEAT_TOP_FT)
beam(2, "BM-BW-GARAGE-SEAT", LANDING_WEST_FT, GARAGE_SEAT_Y_FT,
     LANDING_EAST_FT, GARAGE_SEAT_Y_FT, ("PT-BW-GW", "PT-BW-GE"), SEAT_TOP_FT)
# The three floor beams. FW stops at the garage seat; FC and FE continue into the garage to
# carry the interior landing, and their tips are POSTED -- see INTERIOR_POSTS below.
for index, (suffix, x) in enumerate(zip(("FW", "FC", "FE"), BEAM_X_FT, strict=True), 3):
    beam(index, f"BM-BW-{suffix}", x, FRAME_Y0_FT, x,
         FRAME_Y1_FT if suffix == "FW" else GARAGE_LANDING_END_Y_FT,
         ("BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT") if suffix == "FW" else
         ("BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT", f"PT-BW-I{suffix[-1]}"))

# ** THE TWO ROOF HEADERS, AND WHERE THEIR NORTH ENDS LAND IS THE ARGUMENT FOR THIS SCHEME. **
# x=6'-0" and x=30'-0" are the garage's own southwest and southeast corners, where W-G-S
# meets W-G-W and W-G-E -- the two walls the garage trusses already bear on, directly over
# the GARAGE_ICF_6 stem and its strip footing. Each header is a southward EXTENSION of an
# existing bearing line, so its ~3,130 lb reaction lands on a corner post over concrete
# already sized for truss reactions, and nothing new is required below -1'-0" at the north end.
#
# ** PLY COUNT IS THE LEVER, NOT DEPTH. ** Each header carries a 12' half-span of a 24' truss
# over the 5'-8 3/4" bay = 72 sf, under the roof-step drift case (42 psf balanced + up to
# 50 psf drift + 10 dead), which is ~6,260 lb and a ~4,690 lb-ft moment. A 2-ply 2x10 KDAT
# at C_M 0.85 is d/c 1.40 and fails; a 2-ply 2x12 reaches d/c 1.04 in bending and 0.95 in
# SHEAR, so it fails in shear before bending. 3-ply 2x12 is d/c 0.69, deflection 0.045"
# against L/240 = 0.30". A 3-1/2"x11-7/8" treated glulam (BEAM_GLULAM_TREATED) is the
# alternative at ~4x the material rate; take it only if the exposed 3-ply seam is objectionable.
beam(6, "BM-BW-RW", LANDING_WEST_FT, PIER_LINE_Y_FT,
     LANDING_WEST_FT, GARAGE_Y_SOUTH.feet, ("PT-BW-CW", "W-G-W"), HEADER_TOP_FT, "3-2x12")
beam(7, "BM-BW-RE", ROOF_COLUMN_EAST_X_FT, PIER_LINE_Y_FT,
     ROOF_COLUMN_EAST_X_FT, GARAGE_Y_SOUTH.feet, ("PT-BW-CE", "W-G-E"), HEADER_TOP_FT,
     "3-2x12")

# --- piers, pedestals and columns -------------------------------------------------------
#
# ** SLENDERNESS IS A FALSE ALARM AND THE FOOTING IS THE REAL CHANGE. ** k*lu/r on the 12"
# shaft does exceed ACI 318-19 Sec 6.2.5's non-sway floor of 22, so it is COMPUTED rather than
# neglected -- but P_c = pi^2*EI/(k*lu)^2 is ~851 kip against a factored demand near 6.5 kip,
# so delta_ns is ~1.01 and e_min stays under Sec R22.4.2's 0.10h. Axial d/c is ~0.023. What
# does move is the pad: service load per roof pier is ~4,600 lb against the retired PR-BW-*'s
# 1,240, so on 1,500 psf presumptive soil the required area is 3.1 ft2 and the retired
# 1.78 ft2 pad no longer covers it. 2'-0" square = 4.0 ft2. See notes/north_entry_piers.md.
#
# These are `Footing`, not `Pad`: a Pad is graded prescriptively by
# `structural.deck_footing_size` against an IRC DECK table that knows nothing about roof
# load, and these carry roof snow. `engineering/spread_footing.py` grades a Footing.
#
# `bottom_elevation` is what makes these bear at depth rather than pin to the storey datum
# (-> Footing.bottom_elevation), and the shaft above each grows to suit.
PIERS = []
FOOTINGS = []
for _uid, _tag, _x, _height, _top in (
    ("BWPT01AAAA", "PT-BW-W", LANDING_WEST_FT, BEARING_TOP_FT - FOOTING_TOP_FT,
     BEARING_TOP_FT),
    ("BWPT02AAAA", "PT-BW-E", LANDING_EAST_FT, BEARING_TOP_FT - FOOTING_TOP_FT,
     BEARING_TOP_FT),
    ("BWPT03AAAA", "PT-BW-RE", ROOF_COLUMN_EAST_X_FT, BEARING_TOP_FT - FOOTING_TOP_FT,
     BEARING_TOP_FT),
):
    PIERS.append(Post(
        uid=_uid, tag=_tag, position=pt(ft(_x), ft(PIER_LINE_Y_FT)),
        # `"12 round"`. Never a nominal form like "12x12": that matches `_RE_NOMINAL` in
        # resolve/framing/profiles.py, misses LUMBER_ACTUAL and silently resolves to 1.5x5.5.
        size="12 round", height=ft(_height), assembly="PIER_CONCRETE_12",
        # A_g = 113.10 in2, so ACI 318-19 Sec 10.6.1.1's 1% floor is 1.131 in2; (4) #5 =
        # 1.24 in2 (rho 1.096%) clears it and is the Code's own four-bar minimum for a
        # circular tie (Sec 10.7.3.1(b)). Ties are #3 at the Sec 25.7.2.2 maximum, the least
        # of 16db = 10.0", 48dt = 18.0", h = 12.0". The column is at d/c ~0.023 and NONE of
        # that is why these bars are here -- the 1% floor is a creep/shrinkage/accidental-
        # moment rule, indifferent to load. Galvanized, house-wide (EXPOSED_MIX, A767).
        vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
        supported_by=f"FT-BW-{_tag.split('-')[-1]}"))
    FOOTINGS.append(Footing(
        uid=f"BWF{_uid[4:8]}AA", tag=f"FT-BW-{_tag.split('-')[-1]}", under=_tag,
        width=ft(2), depth=ft(FOOTING_DEPTH_FT), assembly="PIER_BASE_12",
        bottom_elevation=ft(PIER_BOTTOM_FT)))

# ** THE GARAGE SIDE IS THE MIRROR: TWO PIERS OF ITS OWN, NOT A PLATE ON THE STEM. **
# BM-BW-GARAGE-SEAT used to bear through brackets standing off the GARAGE_ICF_6 stem's face,
# with a continuous treated plate in the snow line -- the worst detail in the assembly. It
# collects water, it is the part that rots first, and it is unreachable once the deck is down.
# Two piers instead, at the same elevation and on the same 5'-6" span as the house side, so
# `structural.deck_beam_span` grades both seat beams identically off two Posts each.
#
# ** THEY BOTTOM WITH THE GARAGE FOUNDATION, NOT AT THE HOUSE DEPTH. ** -6'-4" is W-GF-S1's
# own underside, so these two are cast in the garage excavation exactly as the house-side
# three are cast in the basement excavation, and the same sequencing note covers both. They
# carry landing load only (~1,500 lb), so an 18" pad is ample against the roof piers' 2'-0".
# ** THE SAME DEPTH AS THE HOUSE-SIDE THREE, AND THE REASON IS THE HYDRANT, NOT FROST. **
# W-GF-S1's own underside at -6'-4" would be deep enough for frost and cheap enough to cast
# with the garage foundation. It is not deep enough to stay out of the way: the hydrant line
# runs north at x=11'-0" straight through FT-BW-GE, and a footing bearing ABOVE that invert
# puts the pipe inside its 45 degree influence line. Bearing below it removes the question
# instead of sleeving it, and these are cast in the same open excavation as the other three.
GARAGE_PIER_BOTTOM_FT = PIER_BOTTOM_FT
GARAGE_FOOTING_TOP_FT = GARAGE_PIER_BOTTOM_FT + FOOTING_DEPTH_FT
PEDESTALS = []
for _uid, _tag, _x in (("BWPT05AAAA", "PT-BW-GW", LANDING_WEST_FT),
                       ("BWPT06AAAA", "PT-BW-GE", LANDING_EAST_FT)):
    PEDESTALS.append(Post(
        uid=_uid, tag=_tag, position=pt(ft(_x), ft(GARAGE_SEAT_Y_FT)), size="12 round",
        height=ft(BEARING_TOP_FT - GARAGE_FOOTING_TOP_FT), assembly="PIER_CONCRETE_12",
        vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
        supported_by=f"FT-BW-{_tag.split('-')[-1]}"))
    FOOTINGS.append(Footing(
        uid=f"BWFG{_tag[-2:]}AAAA"[:10], tag=f"FT-BW-{_tag.split('-')[-1]}", under=_tag,
        width=inch(18), depth=ft(FOOTING_DEPTH_FT), assembly="PIER_BASE_12",
        bottom_elevation=ft(GARAGE_PIER_BOTTOM_FT)))

# The two roof columns. Pier/pedestal top -0'-8 1/4" to header soffit +6'-4 3/4" = 7'-1".
# k*lu/d = 15.5, nowhere near NDS Sec 3.7.1.4's limit of 50. Standoff base ABU66SS on a
# cast-in AB-058-10-SS, CCQ cap at the header -- all three are live rows in prices.toml, and
# the counts are DERIVED by `takeoff/uplift_joints.py::post_base_anchor_rows`, so authoring
# the posts is what makes them reappear.
#
# ** UPLIFT IS NOT A GOVERNING CASE, AND THIS IS THE NUMBER THAT SAYS SO. ** At 115 mph
# Exposure B, q_h ~ 16.4 psf; a free-roof coefficient near 1.3 gives ~1,500 lb of uplift per
# header against 720 lb of dead. Under 0.6D + 0.6W the net is ~230 lb per column, well inside
# the standoff-base-plus-cast-in-bolt detail. Stated, not left open.
COLUMN_HEIGHT_FT = HEADER_SOFFIT_FT - BEARING_TOP_FT
ROOF_COLUMNS = [
    Post(uid="BWPT07AAAA", tag="PT-BW-CW", position=pt(ft(LANDING_WEST_FT), ft(PIER_LINE_Y_FT)),
         size="6x6", height=ft(COLUMN_HEIGHT_FT), assembly="POST_KDAT",
         supported_by="PT-BW-W"),
    Post(uid="BWPT08AAAA", tag="PT-BW-CE",
         position=pt(ft(ROOF_COLUMN_EAST_X_FT), ft(PIER_LINE_Y_FT)),
         size="6x6", height=ft(COLUMN_HEIGHT_FT), assembly="POST_KDAT",
         supported_by="PT-BW-RE"),
]

# ** THE 4'-2" INTERIOR CANTILEVER IS THE REAL DEFECT AND IT IS CHEAP TO FIX. ** BM-BW-FC
# and BM-BW-FE overhang the garage seat by 4'-1 7/8" on a 6'-2 1/2" back span -- 67%, against
# IRC R507.5.1's 25% -- carrying the top landing of ST-G-SERVICE 34" above the garage slab.
# Two 6x6 KDAT posts on the slab end it. MIN_DECK_POST_NOMINAL is 6x6, so do not reach for a 4x4.
INTERIOR_POSTS = [
    Post(uid=f"BWPT{9 + _i:02d}AAAA", tag=f"PT-BW-I{_s}",
         position=pt(ft(_x), ft(GARAGE_LANDING_END_Y_FT)),
         size="6x6", height=ft(BEARING_TOP_FT - (-(2 + 10 / 12))), assembly="POST_KDAT",
         supported_by="SL-G-FLOOR")
    for _i, (_s, _x) in enumerate(zip(("C", "E"), BEAM_X_FT[1:], strict=True))
]

FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FW", "BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[0], FRAME_Y0_FT, BEAM_X_FT[-1], FRAME_Y1_FT),
    subfloor_outline=rectangle(LANDING_WEST_FT, DECK_SHEET_SOUTH_Y_FT,
                               LANDING_EAST_FT, GARAGE_Y_SOUTH.feet),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="shared upper landing on two piered seat beams; north_entry_structure.md",
)

# A narrower framing zone preserves the main landing identity while keeping the garage
# wall out of the rectangular joist field. Boards share the finish datum and direction.
GARAGE_FLOOR = FloorSystem(
    uid="BWFS02AAAA", tag="FS-BW-GARAGE",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[1], GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                      BEAM_X_FT[2], GARAGE_LANDING_END_Y_FT),
    subfloor_outline=rectangle(GARAGE_LANDING_WEST_FT,
                               GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                               LANDING_EAST_FT, GARAGE_LANDING_END_Y_FT),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="FS-BW-FLOOR continuation; 1/4in threshold joint; replaces SL-G-STEP-0",
)

STAIR_Y0_FT = HOUSE_CLADDING_Y_FT + 3 / 12
STAIR_Y1_FT = GARAGE_CLADDING_Y_FT - 3 / 12
STAIR_WIDTH_FT = STAIR_Y1_FT - STAIR_Y0_FT
# The going is 18", down from 24". Five 6.8" risers are unchanged, so the run drops from
# 8'-0" to 6'-0" and the stair foot moves west from x=19'-6" to x=17'-6". 2R + T is 31.6",
# still outside the 24"-25" comfort rule -- which is inherent to a tiered terrace and is not
# a code limit. If it reads wrong on site the lever is the going, and the paver landing in
# plan/site.py follows it again.
TREAD_DEPTH_FT = 1.5
TREAD_COUNT = 4
STAIR_FOOT_X_FT = LANDING_EAST_FT + TREAD_COUNT * TREAD_DEPTH_FT
LOWER_LANDING_END_X_FT = STAIR_FOOT_X_FT + 3
# ** 9" O.C., AND IT IS THE TREAD RATING, NOT THE DECKING RATING. ** A composite board is
# rated for a UNIFORM load as decking and a 300 lb CONCENTRATED load as a stair tread (IRC
# Table R301.5 fn. c; ICC-ES AC174 Sec 4.1.1 tests it at 1/8" of deflection under 300 lb, an
# ABSOLUTE limit, not L/288). The same board is 16" as decking and 8"-12" as a tread across
# the major brands -- ESR-3771 shows 16" and 11" on one product. `composite-deck` in this
# house names no manufacturer, so 9" is the floor of the mainstream distribution (Trex
# Enhance 9", Trex Select 9", TimberTech Premier 9", ReliaBoard 9") and survives a purchasing
# change after the boxes are built. IRC R507.2.2.5 makes the delivered board's instruction
# binding and IRC Table R507.7 excludes stairways outright: if the board's ASTM D7032 label
# says less than 9", the layout follows the board. Square-edge, face-fastened only -- Fiberon
# and TimberTech both prohibit grooved planks as stair treads outright.
TREAD_SUPPORT_SPACING_IN = 9.0

# ** BOX FRAMES, NOT CUT STRINGERS, AND A CUT STRINGER FAILS ON THREE COUNTS HERE. **
# At the old 24" going the horizontal span was 8'-0" against DCA 6 Fig. 28 / IRC R507.13.1's
# 6'-0"; the remaining throat was 4.71" against 5"; and the treads wanted supports closer
# than 12". Narrowing the going to 18" fixes the span and does NOT fix the throat: the notch
# depth R*T/hypot(R,T) is driven by the LONG going, so a flatter pitch removes MORE material,
# and holding 5" at 6.8:18 would take an 11.54"-wide member -- a 2x12 is 0.29" short and the
# next size is off every prescriptive table.
#
# Four boxes instead, each ~6'-0" x 1'-6", on footings at 42" below finished grade. That
# depth is not a range: Minn. R. 1303.1600 sets "the minimum allowable footing depth in feet
# due to freezing is five feet in Zone I and 3-1/2 feet in Zone II", and Zone II is named to
# include Hennepin. (The 60" figure is northern Minnesota, a different zone.) A deep
# washed-rock section is NOT a prescriptive alternative: IRC R403.3 applies only to buildings
# kept at 64F or warmer and says outright it "shall not be used for unheated spaces such as
# porches", and Minnesota's Rules 1309.0403 amendment carries no exceptions -- the aggregate
# route reaches it only through ASCE 32, a stamped engineered submittal.
#
# ** THE SUPPORT WAS ALWAYS WORSE THAN THE MEMBER. ** The old flight was pinned at the top to
# a 9'-9" pier and sat at the bottom on pavers on soil. Heave merely lifts a simply-supported
# member; SETTLEMENT is the failure, because it turns the span into a cantilever off
# BM-BW-FE, which nothing in that assembly can do -- and riser uniformity has only 3/8" of
# tolerance (R311.7.5.1), less than one winter gives up. DCA 6 is explicit: "Stringers shall
# not bear on new or existing concrete pads or patios that are not founded below this depth."
# Accept movement in exactly ONE place: the joint between the bottom box and the paver
# landing, where the pavers are a flexible field and no riser depends on them.
TIERS = Stair(
    uid="BWST01AAAA", tag="ST-BW-ENTRY", from_storey="main", to_storey="main",
    base_elevation=SITE_GRADE, top_elevation=ft(DECK_FINISH_FT),
    width=ft(STAIR_WIDTH_FT), start=pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y0_FT)),
    run_direction="x", run_reversed=True, tread_depth=ft(TREAD_DEPTH_FT),
    nosing_depth=inch(0), material="kdat", carriage="box",
    stringer_spacing=inch(TREAD_SUPPORT_SPACING_IN),
    tread_material="composite-deck", tread_thickness=inch(1),
)

# Four tier footings per box line, at the Zone II 42". Fine Homebuilding's box-frame footings
# sit "about 4 feet apart because the rim joist of the box can span the distance between the
# footings" -- the only span guidance published anywhere for a box tier, since no prescriptive
# table covers one. DCA 6's nearest hook is that an intermediate stair landing "must be
# designed and constructed as a non-ledger deck using the details in this document", so the
# rims and joists size off DCA 6's DECK tables and not off any stair table.
TIER_FOOTING_DEPTH_IN = 42.0
TIER_FOOTING_THICKNESS_IN = 8.0
TIER_RISE_IN = 6.8
TIER_FRAME_DROP_IN = 1.0 + 7.25   # the 1" tread board and the 2x8 under it
_TIER_FOOTING_BOTTOM_FT = SITE_GRADE.feet - TIER_FOOTING_DEPTH_IN / 12
_TIER_FOOTING_TOP_FT = _TIER_FOOTING_BOTTOM_FT + TIER_FOOTING_THICKNESS_IN / 12
TIER_PIERS = []
TIER_FOOTINGS = []
for _i in range(TREAD_COUNT):
    # Two shafts per box, ~4'-0" apart under a 6'-0" rim, per the only published span
    # guidance for a box tier. The shaft top is the box's FRAMING underside, so each tier's
    # pier is one riser taller than the one below it.
    _x = STAIR_FOOT_X_FT + _i * TREAD_DEPTH_FT + TREAD_DEPTH_FT / 2
    _top = SITE_GRADE.feet + (_i + 1) * TIER_RISE_IN / 12 - TIER_FRAME_DROP_IN / 12
    for _j, _y in enumerate((STAIR_Y0_FT + 0.5, STAIR_Y1_FT - 0.5)):
        _t = f"PT-BW-T{_i + 1}{'WE'[_j]}"
        TIER_PIERS.append(Post(
            uid=f"BWTP{_i}{_j}AAAA", tag=_t, position=pt(ft(_x), ft(_y)),
            size="12 round", height=ft(_top - _TIER_FOOTING_TOP_FT),
            assembly="PIER_CONCRETE_12", supported_by=f"FT-BW-T{_i + 1}{'WE'[_j]}"))
        TIER_FOOTINGS.append(Footing(
            uid=f"BWTF{_i}{_j}AAAA", tag=f"FT-BW-T{_i + 1}{'WE'[_j]}", under=_t,
            width=inch(24), depth=inch(TIER_FOOTING_THICKNESS_IN),
            assembly="PIER_BASE_12", bottom_elevation=ft(_TIER_FOOTING_BOTTOM_FT)))


def guard(uid, tag, path):
    return Railing(uid=uid, tag=tag, path=tuple(pt(ft(x), ft(y)) for x, y in path),
                   height=inch(36), base_elevation=ft(DECK_FINISH_FT),
                   post_spacing=inch(36), post_size="2x2", rail_count=2,
                   kind=RailingKind.METAL_SURFACE_MOUNT, mount="surface",
                   assembly="RAILING_DARK_METAL", infill="balusters", baluster_spacing=inch(3.5))


# ** THE GUARD MOVED INTO THE SCREEN LINE, WHICH IS WHY RL-BW-WEST IS GONE. **
# RL-BW-WEST stood 1 1/2" west of SC-BW-WEST -- two elements an inch apart doing one job, and
# a plan clash. The screen cannot take the guard load itself: IRC Table R301.5 puts 200 lb
# CONCENTRATED on a guard (the 50 plf line load is IBC Sec 1607.8.1, not a residential
# provision), and a 2x4 on edge cantilevered 36" off the deck is d/c 1.34 at C_D 1.6 and 1.65
# in SPF. Worse, the 2018 IRC's footnote says the 200 lb acts "in any direction", which
# permits it PARALLEL to the screen, bending a slat about its 1 1/2" face where S = 1.31 in3.
# And the base connection is worse than the member: Virginia Tech's full-scale tests behind
# DCA 6 measured 178 lb ultimate for 1/2" lag screws and 237 lb for 1/2" bolts, while
# resolving this base moment over a 5 1/4" arm needs ~1,700 lb of tension per slat -- a
# hold-down every three inches into a 1 1/2" member. Not buildable.
#
# So the guard is one element ON the screen line, anchored to the deck framing and to
# PT-BW-CW, and the slats are demoted to IN-FILL carrying only Table R301.5 footnote f's
# 50 lb over one square foot (d/c ~0.33) -- which also makes them immune to the 2018-vs-2021
# "any direction" question that would otherwise decide the whole detail.
#
# Two openings to check that are NOT the sphere between slats: the gap under the bottom of
# the slats to the deck surface, and the end gaps where the screen meets the house and the
# garage. Both are openings in a required guard and both count.
RAILINGS = [
    guard("BWRGW1AAAA", "RL-BW-SCREEN", ((LANDING_WEST_FT, FRAME_Y0_FT),
                                         (LANDING_WEST_FT, FRAME_Y1_FT))),
    guard("BWRGGWAAAA", "RL-BW-GARAGE-W", ((8.5, GARAGE_INSIDE_Y_FT),
                                          (8.5, GARAGE_LANDING_END_Y_FT))),
    guard("BWRGGEAAAA", "RL-BW-GARAGE-E", ((11.5, GARAGE_INSIDE_Y_FT),
                                          (11.5, GARAGE_LANDING_END_Y_FT))),
    Railing(uid="BWRHE1AAAA", tag="RL-BW-ENTRY",
            path=(pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y1_FT)),
                  pt(ft(LANDING_EAST_FT), ft(STAIR_Y1_FT))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=SITE_GRADE, post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="guard_and_handrail", serves_stair="ST-BW-ENTRY", top_height=inch(36),
            graspable_profile="1.5in round — Type I", infill="balusters",
            baluster_spacing=inch(3.5)),
]

NOTES = [
    Annotation(uid="BWAN03AAAA", tag="AN-BW-ROOF", position=pt(ft(22), ft(40)),
               text="CANOPY RF-BW-CANOPY: 3 trusses @24in span 24ft between BM-BW-RW/RE on PT-BW-CW/CE; sheathing CONTINUOUS across the garage south wall line — that diaphragm path IS the lateral system; design snow 42psf balanced + 50psf drift surcharge over 9.8ft from the house gable (ASCE 7 §7.7, p_g=50); truss fabricator to price the two southernmost garage trusses as drift trusses"),
    Annotation(uid="BWAN01AAAA", tag="AN-BW-STRUCTURE", position=pt(ft(7), ft(39)),
               text="LANDING: seat beams on cast concrete to -0ft 8-1/4in BOTH sides; no bearing on the house; piers cast WITH the basement excavation to -9ft 9-7/16in — casting them after backfill undermines the house footing; hold deck boards 1/2in off the cladding and let the gap drain"),
    Annotation(uid="BWAN02AAAA", tag="AN-BW-TIERS", position=pt(ft(16), ft(39)),
               text="5 equal 6.8in rises; four 18in composite box tiers on 42in footings (Minn. R. 1303.1600 Zone II); NO cut stringers; tread supports at 9in o.c. max — read the delivered board's ASTM D7032 STAIR row, not its decking row; square-edge face-fastened treads only"),
    Annotation(uid="BWAN04AAAA", tag="AN-BW-KDAT", position=pt(ft(9), ft(41)),
               text="ALL KDAT: 304 stainless fasteners (IRC R317.3.1); butyl joist tape over every beam/rim top; field-treat every cut end, notch and hole with 2% copper naphthenate per AWPA M4 (IRC R317.1.1 — required, not advisory); finish with a PIGMENTED penetrating oil on installation, recoat 2-3yr horizontal. NO silicate/'liquid glass' — it is a masonry densifier, leaches from wood and adds no UV protection"),
]

# On-edge 2x4s: 3.5in projection in x, 1.5in faces and gaps along y. The screen now runs from
# PT-BW-CW north to the garage wall — 5'-5 1/2", under the 6'-0" post spacing the prescriptive
# guidance assumes — and stops at the header soffit, so it is a simply-supported panel rather
# than an 8'-0" free-standing cantilever. That top restraint is what deletes its unsolved base
# moment, and it is free once the canopy is built. One member settles three things at once:
# PT-BW-CW holds the roof up, restrains the slat tops, and takes the guard load.
SCREEN_PITCH_IN = 3.0
SCREEN_START_Y_FT = PIER_LINE_Y_FT
SCREEN_END_Y_FT = FRAME_Y1_FT - 1.5 / 12
SCREEN_SLAT_COUNT = int((SCREEN_END_Y_FT - SCREEN_START_Y_FT) * 12 / SCREEN_PITCH_IN) + 1
SCREEN = SlatScreen(
    uid="BWSC001AAA", tag="SC-BW-WEST", start=pt(ft(LANDING_WEST_FT), ft(SCREEN_START_Y_FT)),
    end=pt(ft(LANDING_WEST_FT), ft(SCREEN_END_Y_FT)), base_elevation=ft(DECK_JOIST_TOP_FT),
    height=ft(HEADER_SOFFIT_FT - DECK_JOIST_TOP_FT),
    slat_face=inch(1.5), slat_depth=inch(3.5), clear_gap=inch(1.5),
    assembly="POST_KDAT", supported_by="BM-BW-FW",
    engineering_note="In-fill only: slats carry IRC Table R301.5 fn. f's 50 lb over 1 sqft (d/c ~0.33), NOT the 200 lb guard load, which RL-BW-SCREEN and PT-BW-CW take. Top restrained on BM-BW-RW's soffit and south end framed into PT-BW-CW, so the base moment the old free-standing cantilever could not resolve does not arise.",
)

# ** THE FOUR SEAT-BEAM BEARINGS ARE REAL HARDWARE NOW, NOT SIX INVENTED PART NUMBERS. **
# The retired CN-BW-*-SEAT connectors borrowed ConnectorKind.HOLD_DOWN with a part number in
# no catalog ("BW-ENGINEERED-FIXED-SEAT"), and `takeoff/anchors.py` priced it as a custom
# fabrication allowance -- which is how a missing structure billed $1,350-4,050 and graded
# clean. A KDAT beam landing on a cast pier is an ordinary detail and the house already has
# it at the porch columns: a stainless shim pack holding the treated soffit off the pour, so
# water cannot sit in the joint and the copper treatment never touches the concrete.
#
# Two parts per bearing, and they do different jobs. The SS316-SHIM-35 pack is the BEARING:
# it holds the treated soffit off the pour so water cannot sit in the joint and the copper
# treatment never touches the concrete, and it is where the levelling tolerance is taken. The
# HGAM10 gusset is the TIE: #14 screws into the wood leg, Titen Turbo into the concrete leg,
# 1 1/2" minimum edge distance. `structural.uplift_path_coverage` grades the second one --
# a shim pack is not a hold-down, and a beam simply resting on a pier is a break in the chain.
SEAT_BEARINGS = []
for _i, (_t, _x, _y, _beam) in enumerate((
    ("W", LANDING_WEST_FT, HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT"),
    ("E", LANDING_EAST_FT, HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT"),
    ("GW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT"),
    ("GE", LANDING_EAST_FT, GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT"),
)):
    SEAT_BEARINGS.append(Connector(
        uid=f"BWSD{_i}AAAAAA"[:10], tag=f"CN-BW-STDF-{_t}",
        kind=ConnectorKind.BEARING_STANDOFF, position=pt(ft(_x), ft(_y)),
        elevation=ft(BEARING_TOP_FT), size="SS316-SHIM-35",
        connects=(_beam, f"PT-BW-{_t}")))
    SEAT_BEARINGS.append(Connector(
        uid=f"BWSG{_i}AAAAAA"[:10], tag=f"CN-BW-TIE-{_t}",
        kind=ConnectorKind.POST_CAP, position=pt(ft(_x), ft(_y)),
        elevation=ft(BEARING_TOP_FT), size="HGAM10",
        connects=(_beam, f"PT-BW-{_t}")))

# The two header caps. A 3-ply 2x12 is 4 1/2" wide, which is the "4x beam" the CCQ46 is
# published for, on the 6x6 it names. `structural.uplift_path_coverage` would otherwise take
# a DERIVED KBS1Z strap here -- a knee brace standing in for a cap, which is not the detail.
COLUMN_CAPS = [
    Connector(uid=f"BWCC{_i}AAAAAA"[:10], tag=f"CN-BW-CAP-{_s}",
              kind=ConnectorKind.POST_CAP, position=pt(ft(_x), ft(PIER_LINE_Y_FT)),
              elevation=ft(HEADER_SOFFIT_FT), size="CCQ46SDS2.5",
              connects=(f"BM-BW-R{_s}", f"PT-BW-C{_s}"))
    for _i, (_s, _x) in enumerate((("W", LANDING_WEST_FT),
                                   ("E", ROOF_COLUMN_EAST_X_FT)))
]

# Procurement allowance at the two eaves over the entry zone. Supplier must size rail
# lengths, row spacing and clamp demand for the actual drift load and roof profile.
SNOW_RETENTION = [
    Connector(uid=f"BWNS{side}{i}AAAA", tag=f"CN-BW-SNOW-{side}-{i}",
              kind=ConnectorKind.SNOW_GUARD, position=pt(ft(x), ft(y)),
              elevation=ft(8, 2), size="S-5! ColorGard", connects=("RF-GARAGE",),
              source="north_entry_structure.md — provisional entry-zone snow-rail layout")
    for side, x in (("W", 5.5), ("E", 30.5))
    for i, y in enumerate((38.5, 42.5), 1)
]

MAIN_ELEMENTS = [*NODES, *BEAMS, *PIERS, *FOOTINGS, *PEDESTALS, *ROOF_COLUMNS,
                 *INTERIOR_POSTS, FLOOR, GARAGE_FLOOR, TIERS, *TIER_PIERS, *TIER_FOOTINGS,
                 SCREEN, *RAILINGS, *SEAT_BEARINGS, *COLUMN_CAPS, *SNOW_RETENTION, *NOTES]

"""North entry STRUCTURE — the piers, columns, headers and beams the landing stands on.

Split out of `params/breezeway.py` on 2026-09-10 (AGENTS.md's 500-line rule; the
`plan/storeys/attic_studio.py` precedent). The cut is at the seam that already existed:
**everything here is below and including the beams** — what carries load to the ground —
and `breezeway.py` authors what sits on top of it, the deck, the tiers, the guards and the
screen. Both are ordinary `params/` modules, not `# haus: editable`, which is correct:
piers and headers are structure, not a thing the UI drags.

The bearing map is `notes/north_entry_structure.md`; the arithmetic is
`notes/north_entry_piers.md`, which oracles `engineering/roof_beam.py` and the pier calcs.

**The landing touches nothing on the house, and since 2026-09-10 the canopy touches nothing
on the garage either.** Grep this file for `W-B-` or `W-G-` and expect nothing but comments.
The landing's house-side bearing is two cast piers on the pier line at y=37'-6"; the canopy
stands on four columns of its own and shares only the sheathing plane with `RF-GARAGE`.

**Two pier depths, on purpose.** The house-side three reach -9'-9 7/16" because the basement
excavation is already open to it, so the shaft is the only cost -- and they must be cast
WHILE it is open or they undermine the house footing ten inches away. The garage-side three
stop at -7'-0", the garage strip footing's own plane, and are cast with the garage
foundation. There is no excavation out there to make depth cheap.

**KDAT longevity, house-wide (owner, 2026-09-10).** Every treated member here and in
`breezeway.py` carries the same four-part detail, stated once rather than per element:
304 stainless fasteners; butyl joist tape over every beam and rim top (`top_protection`);
AWPA M4 field treatment of every cut end, notch and drilled hole with 2% copper naphthenate
(IRC R317.1.1 makes this "shall", not advice); and a pigmented penetrating oil finish
applied on installation. `AN-BW-KDAT` carries it onto the drawings.
"""

from typehaus import (
    Annotation, BarSpec, Beam, Connector, ConnectorKind, DeckLayer, Footing, FloorSystem,
    JoistSpec, Node, Post, Railing, RailingKind, ReinforcementSpec, SlatScreen, Stair,
    ft, inch, pt,
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

# ** THE TWO ROOF HEADERS, AND THE CANOPY THEY CARRY TOUCHES THE GARAGE FOR NOTHING. **
# These used to bear north on `W-G-W` / `W-G-E`, on the premise that a header landing on the
# garage's own southwest and southeast corners was a southward EXTENSION of a bearing line
# already sized for truss reactions. It is not a detail. A ~3,130 lb point reaction on the
# END of a stud wall wants a real bearing post through the plate, the stud bay, the sill and
# the ICF stem, and no such post was authored, drawn or billed -- `bearing_refs` naming a wall
# is the engine's idiom for a beam landing ALONG a wall, and it grades nothing about a beam
# landing on a wall's terminus.
#
# So the canopy is freestanding on four columns of its own (owner, 2026-09-10): PT-BW-CW/CE
# at the pier line and PT-BW-CNW/CNE at the garage-side line, each on cast concrete to
# -0'-8 1/4". x=6'-0" and x=30'-0" are still the garage's own corner lines, so the canopy
# reads as one plane with RF-GARAGE and the sheathing runs continuous across the joint -- and
# THAT continuity is the only thing the two structures share. It is the canopy's lateral
# system (AN-BW-ROOF says so) and it carries no gravity load in either direction.
#
# The headers run 8" past the north columns to y=GARAGE_Y_SOUTH so the roof plane reaches
# the garage wall. R507.5.1's quarter-of-the-back-span is a DECK table and does not reach a
# roof header; what bounds this tail is the header's own bending and shear, which
# `engineering/roof_beam.py` grades.
#
# ** PLY COUNT IS THE LEVER, NOT DEPTH. ** Each header carries a 12' half-span of a 24' truss
# over the 5'-8 3/4" bay = 72 sf, under the roof-step drift case (42 psf balanced + up to
# 50 psf drift + 10 dead), which is ~6,260 lb and a ~4,690 lb-ft moment. A 2-ply 2x10 KDAT
# at C_M 0.85 is d/c 1.40 and fails; a 2-ply 2x12 reaches d/c 1.04 in bending and 0.95 in
# SHEAR, so it fails in shear before bending. 3-ply 2x12 is d/c 0.69, deflection 0.045"
# against L/240 = 0.30". A 3-1/2"x11-7/8" treated glulam (BEAM_GLULAM_TREATED) is the
# alternative at ~4x the material rate; take it only if the exposed 3-ply seam is objectionable.
beam(6, "BM-BW-RW", LANDING_WEST_FT, PIER_LINE_Y_FT,
     LANDING_WEST_FT, GARAGE_Y_SOUTH.feet, ("PT-BW-CW", "PT-BW-CNW"), HEADER_TOP_FT,
     "3-2x12")
beam(7, "BM-BW-RE", ROOF_COLUMN_EAST_X_FT, PIER_LINE_Y_FT,
     ROOF_COLUMN_EAST_X_FT, GARAGE_Y_SOUTH.feet, ("PT-BW-CE", "PT-BW-CNE"), HEADER_TOP_FT,
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
# ** THE CAGE MUST BE STRUCTURED, NOT ONLY PROSE, OR ITS STEEL BILLS ZERO. **
# `vertical_reinforcement` is a free-text string for the drawings; `reinforcement_takeoff`
# reads `reinforcement` and nothing else. Authoring only the string added 3.18 cy of concrete
# to this house and exactly no pounds of steel, which `notes/rebar_backout.md`'s lb/cy ratio
# is what noticed. Both spellings, always, and keep them saying the same thing.
#
# Galvanized, house-wide (ASTM A767 cl. 1): these piers stand up to 18 1/2" out of the ground
# at a salted entry on an EXPOSED_MIX (ACI 318-19 class F3 + C2). Stainless was considered for
# this house and rejected; do not substitute epoxy.
ENTRY_PIER_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4, coating="hdg-a767"),
        BarSpec(role="ties", bar=3, spacing=inch(10.0), coating="hdg-a767"),
    ),
    cover=inch(2.0),
    lap_class="B",
    source=("notes/north_entry_piers.md §6 — the ACI 318-19 §10.6.1.1 1% floor, "
            "four bars per §10.7.3.1(b)"),
)

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
        reinforcement=ENTRY_PIER_CAGE,
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
# ** PAD WIDTH IS PER PIER NOW, BECAUSE THEY NO LONGER CARRY THE SAME THING. **
# PT-BW-GE carries landing load only and stays at 18" (d/c 0.86 on 2,000 psf presumptive
# soil, the tightest bearing ratio in this assembly and the first number to revisit if a
# soils report comes back lower). PT-BW-GW and PT-BW-RNE each carry a canopy column as well
# and take the roof piers' 2'-0".
#
# ** THE 2'-0" PADS LAP THE GARAGE'S OWN STRIP FOOTING, AND THAT IS A SEQUENCING NOTE. **
# `FT-GF-S1`/`-S3` run along y=43'-2 5/8" and bottom at -6'-4"; these pads reach ~8" under
# them in plan and bear 3'-5" deeper. Cast in the open excavation, deep pours first -- which
# is the same premise the house-side three already stand on -- that is a pour sequence. Cast
# after the garage foundation is backfilled it is undermining, and the answer becomes
# benching. It belongs on the drawings, and AN-BW-STRUCTURE carries it.
#
# ** THESE STOP AT THE GARAGE'S OWN FOOTING, AND THAT IS THE WHOLE REASON THEY ARE CHEAP. **
# The house-side three reach -9'-9 7/16" for one reason and it is not bearing: the basement
# excavation is already open to that depth, so the extra 2'-9" of shaft costs shaft and
# nothing else. There is no such excavation out here. The garage's own strip footings bottom
# at -7'-0" and top at -6'-4", which is 50" of cover against Minn. R. 1303.1600 Zone II's
# 42", so these are cast with the garage foundation on the same bearing plane, in the same
# formwork sequence, out of the same pour (owner, 2026-09-10).
#
# ** COPLANAR IS ALSO WHAT SETTLES THE LAP. ** PT-BW-GW's and PT-BW-RNE's 2'-0" pads reach
# about 8" under `FT-GF-S1`/`-S3` in plan. At the house-side depth that was undermining and
# a sequencing note; at the garage's own depth the two pads simply meet the strip footing
# edge to edge on one plane, which is an ordinary detail and needs no note at all.
#
# ** AND THE HYDRANT PASSES UNDER, NOT THROUGH. ** `PR-G-HYDRANT-CW` runs north at x=11'-0"
# with its invert at -8'-10", so at this depth it clears the underside of FT-BW-GE by 1'-10"
# rather than threading between a shaft and a pad. `mep.footing_clearance` grades it.
GARAGE_FOOTING_THICKNESS_FT = 8 / 12   # the garage strip's own 8", so the two tops align
GARAGE_PIER_BOTTOM_FT = -7.0
GARAGE_FOOTING_TOP_FT = GARAGE_PIER_BOTTOM_FT + GARAGE_FOOTING_THICKNESS_FT
PEDESTALS = []
for _uid, _tag, _x, _pad_in in (("BWPT05AAAA", "PT-BW-GW", LANDING_WEST_FT, 24.0),
                                ("BWPT06AAAA", "PT-BW-GE", LANDING_EAST_FT, 18.0),
                                ("BWPT04AAAA", "PT-BW-RNE", ROOF_COLUMN_EAST_X_FT, 24.0)):
    PEDESTALS.append(Post(
        uid=_uid, tag=_tag, position=pt(ft(_x), ft(GARAGE_SEAT_Y_FT)), size="12 round",
        height=ft(BEARING_TOP_FT - GARAGE_FOOTING_TOP_FT), assembly="PIER_CONCRETE_12",
        vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
        reinforcement=ENTRY_PIER_CAGE,
        supported_by=f"FT-BW-{_tag.split('-')[-1]}"))
    FOOTINGS.append(Footing(
        uid=f"BWFG{_uid[4:6]}AAAA"[:10], tag=f"FT-BW-{_tag.split('-')[-1]}", under=_tag,
        width=inch(_pad_in), depth=ft(GARAGE_FOOTING_THICKNESS_FT),
        assembly="PIER_BASE_12", bottom_elevation=ft(GARAGE_PIER_BOTTOM_FT)))

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
    Post(uid=_uid, tag=_tag, position=pt(ft(_x), ft(_y)),
         size="6x6", height=ft(COLUMN_HEIGHT_FT), assembly="POST_KDAT", supported_by=_pier)
    for _uid, _tag, _x, _y, _pier in (
        ("BWPT07AAAA", "PT-BW-CW", LANDING_WEST_FT, PIER_LINE_Y_FT, "PT-BW-W"),
        ("BWPT08AAAA", "PT-BW-CE", ROOF_COLUMN_EAST_X_FT, PIER_LINE_Y_FT, "PT-BW-RE"),
        # The two north columns, which is what makes the canopy freestanding. The west one
        # shares PT-BW-GW with the garage-side seat beam exactly as PT-BW-CW shares PT-BW-W
        # with the house-side one; the east one has PT-BW-RNE to itself, there being no
        # landing out at x=30'-0".
        ("BWPT11AAAA", "PT-BW-CNW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "PT-BW-GW"),
        ("BWPT12AAAA", "PT-BW-CNE", ROOF_COLUMN_EAST_X_FT, GARAGE_SEAT_Y_FT, "PT-BW-RNE"),
    )
]

# ** THE 4'-2" INTERIOR CANTILEVER IS THE REAL DEFECT AND IT IS CHEAP TO FIX. ** BM-BW-FC
# and BM-BW-FE overhang the garage seat by 4'-1 7/8" on a 6'-2 1/2" back span -- 67%, against
# IRC R507.5.1's 25% -- carrying the top landing of ST-G-SERVICE 34" above the garage slab.
# Two 6x6 KDAT posts on the slab end it. MIN_DECK_POST_NOMINAL is 6x6, so do not reach for a 4x4.
#
# ** THEY BEAR ON THE SLAB, AND THE THICKENING UNDER EACH IS A DRAWING NOTE, NOT AN ELEMENT. **
# A `Pad` was tried here and is the wrong element: a thickened slab is ONE pour with the slab,
# and modelling it as an isolated pad reports a concrete_interference lap with `SL-G-FLOOR`
# and a frost_depth FAIL for a pour inside a heated-adjacent garage. The model has no way to
# say "monolithic", so the honest record is the slab bearing plus AN-BW-STRUCTURE naming the
# thickening. `structural.deck_footing_size` reports NOT_APPLICABLE and says why.
INTERIOR_POSTS = [
    Post(uid=f"BWPT{9 + _i:02d}AAAA", tag=f"PT-BW-I{_s}",
         position=pt(ft(_x), ft(GARAGE_LANDING_END_Y_FT)),
         size="6x6", height=ft(BEARING_TOP_FT - SITE_GRADE.feet), assembly="POST_KDAT",
         supported_by="SL-G-FLOOR")
    for _i, (_s, _x) in enumerate(zip(("C", "E"), BEAM_X_FT[1:], strict=True))
]


FRAME_ELEMENTS = [*NODES, *BEAMS, *PIERS, *FOOTINGS, *PEDESTALS, *ROOF_COLUMNS,
                  *INTERIOR_POSTS]

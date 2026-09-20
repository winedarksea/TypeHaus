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
    Annotation, BarSpec, Beam, Connector, ConnectorKind, DeckLayer, FloorSystem, Footing,
    JoistSpec, Node, Pad, Post, Railing, RailingKind, ReinforcementSpec, SlatScreen, Stair,
    ft, inch, pt,
)

from params.foundations import SITE_GRADE
from plan.storeys.garage import (
    GARAGE_X_WEST, GARAGE_Y_SOUTH, SERVICE_DOOR_OFFSET, SERVICE_DOOR_WIDTH,
)

HOUSE_CLADDING_Y_FT = 36 + 7.25 / 12
GARAGE_CLADDING_Y_FT = GARAGE_Y_SOUTH.feet - 0.875 / 12
GARAGE_INSIDE_Y_FT = GARAGE_Y_SOUTH.feet + 11 / 12
# ** THE SERVICE DOOR SETS THE EAST EDGE OF EVERYTHING HERE (2026-09-11). ** D-G-SERVICE's
# rough opening is 6'-7"..9'-7" since it moved into the garage's SW corner
# (plan/storeys/garage.py::SERVICE_DOOR_OFFSET), and the whole landing derives from it:
# the exterior deck ends on its east jamb, the interior landing's sheet spans its RO, and
# the two carriers sit just inside it. The west edge is the canopy column line.
SERVICE_RO_WEST_FT = GARAGE_X_WEST.feet + SERVICE_DOOR_OFFSET.feet
SERVICE_RO_EAST_FT = SERVICE_RO_WEST_FT + SERVICE_DOOR_WIDTH.feet
LANDING_WEST_FT = 6.0  # the column line; also the screen panel and the west door patch's edge
# The deck used to reach 11'-6" to cover two offset door patches (`D-M-ENTRY` at 8'-0",
# `D-G-SERVICE` at 10'-0"); with the doors an inch apart the RO's east jamb covers both.
LANDING_EAST_FT = SERVICE_RO_EAST_FT
# ** THE WEST CORRUGATED PLANE, PUBLISHED SO NOTHING RE-DERIVES IT. ** `W-BW-SCREEN` carries
# `alignment=face("stud-ext", offset=inch(-1.75))` (params/breezeway.py): its 2x4s centre on
# this column line, so the west face lands a half stud + 5/8" CDX + 7/8" corrugated out.
# `W-BW-SCREEN-SKIRT` READS THIS: a drifted skirt is a 7/16" step in steel, graded by nothing.
SCREEN_CLADDING_WEST_X_FT = LANDING_WEST_FT - (1.75 + 0.625 + 0.875) / 12
# ** THE STEM'S FINISHED INSIDE FACE, NOT ITS NODE LINE. ** `W-GF-W` is 11" of ICF off the
# node line at x=6'-0" plus the 5/8" `gwb-stem` board GARAGE_ICF_6 carries on its inside
# face from grade up, so 11 5/8". The stair and the interior landing's east guard stand
# flush to this face; the framed wall above the stem is thinner (gyp face 6'-6 3/4").
GARAGE_STEM_INSIDE_X_FT = GARAGE_X_WEST.feet + 11.625 / 12
GARAGE_LANDING_WEST_FT = SERVICE_RO_WEST_FT
GARAGE_LANDING_EAST_FT = GARAGE_STEM_INSIDE_X_FT + 3
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
# Half of the 6x6 canopy columns that stand on this line and on the garage seat line.
# BM-BW-SCSILL's ends are set off the column CENTRES by this, because a 6x6 is wider
# than the 3" seat beam it shares a centreline with -- see that beam for the arithmetic.
COLUMN_HALF_FT = 2.75 / 12
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

# ** THE SLAT CLERESTORY'S SILL IS THE PANEL'S TOP PLATE, AND THERE ARE NO RAILS. **
# An earlier pass at this put two 2x6 cross rails on the column line at +1'-0" and +3'-0" to
# carry the guard load into PT-BW-CW and PT-BW-CNW, because the screen was then open slats
# for its whole height and a 2x4 slat cantilevered off the deck cannot take IRC Table
# R301.5's 200 lb (resolving that base moment over a 5 1/4" arm wants ~1,700 lb of tension
# per slat, against the 178 lb ultimate the Virginia Tech tests behind DCA 6 measured for a
# 1/2" lag). The solid panel superseded both: at +4'-0" it covers the guard zone outright,
# and two rails at +1'-0" and +3'-0" were left buried inside its own studs doing nothing the
# wall was not already doing. They are deleted, and the slats sit on the panel's top plate.
#
# They also cost something while they existed, which is worth recording: bearing on the two
# columns, they gave `engineering/pier_basis.py` two beams carrying no modelled plan area, so
# PT-BW-W and PT-BW-GW could not publish an axial demand and `structural.lateral_racking`
# went UNKNOWN on both. A member with a LINE load and no area is a real gap in that module;
# this design no longer walks into it.
SCREEN_PANEL_TOP_FT = 4.0


# ** ONE TIER OF BEAMS, NOT TWO, AND THE JOISTS SIT STRAIGHT ON IT (owner, 2026-09-10). **
# This landing was framed pier -> seat beam (east-west) -> floor beam (north-south) -> joist
# (east-west) -> board. Three tiers of framing under a 5'-6" x 4'-11 3/4" square, with beams
# running BOTH ways, which is what the owner saw and it was right: the middle tier does
# nothing. The seat beams already span pier to pier, and a joist can land on them directly.
#
# So the joists run NORTH-SOUTH now, on the two seat beams, and `BM-BW-FW` is deleted outright
# along with `WEST_BEAM_X_FT` and the 6" west cantilever that existed only to dodge PT-BW-CW.
#
# ** WHY THE SEATS ARE THE TIER THAT SURVIVES, AND NOT THE OTHER WAY ROUND. ** Putting the
# north-south beams straight on the piers instead is the obvious alternative and it does not
# fit: the pier lines are x=6'-0" and x=9'-7", and x=6'-0" is already occupied at BOTH y
# stations by a canopy column (PT-BW-CW, PT-BW-CNW) standing on that same pier and rising
# through the deck band to the header. A beam on that line interpenetrates the column
# outright. The columns own x=6'-0"; the seats get the piers.
#
# ** BM-BW-FC AND BM-BW-FE STAY, AND THEY ARE NOT A SECOND TIER. ** They run north-south in
# the joist plane, parallel to the joists and bearing on the same two seats, so they add no
# depth to the stack. What they do that no joist can is reach the interior landing: both pass
# under D-G-SERVICE's sill, over the ICF stem `W-GF-S-DR` (continuous since 2026-09-11; it
# tops out at -1'-0", 3 3/4" below the joist soffit) and carry FS-BW-GARAGE on the far side,
# posted at their tips. The west member had no such errand -- it stopped at the garage seat
# -- which is why it is the one that went.
#
# The joist field's own two edges, each a joist CENTRELINE so the rim lands where it is told.
# West: clear of the two 6x6 canopy columns on x=6'-0", whose east face is at 6'-3".
# East: clear of BM-BW-FE, whose west face is at 9'-4" -- the rim's east face touches it.
BEAM_WIDTH_IN = 3.0
JOIST_MEMBER_WIDTH_IN = 1.5
FIELD_WEST_X_FT = LANDING_WEST_FT + 3 / 12 + JOIST_MEMBER_WIDTH_IN / 24
FIELD_EAST_X_FT = LANDING_EAST_FT - BEAM_WIDTH_IN / 12 - JOIST_MEMBER_WIDTH_IN / 24
# ** THE WEST CARRIER IS SISTERED TO THE DECK'S SECOND JOIST, AND THAT IS FORCED. ** The
# joist field lays out 12" o.c. from FIELD_WEST_X_FT, so a joist stands at 7'-3 3/4" with
# its west face at 7'-3"; the stem's finished face is 6'-11 5/8". That is 3 3/8" for a 3"
# beam: the carrier's east face lands ON the joist (two members side by side, an ordinary
# bearing, and the same "touch by construction" BM-BW-FE has against the east rim) and its
# west face is 3/8" off the stem's board. Its 4x4 post is four feet north of that joist's
# end and clears the board by 1/8". East: the carrier's east face is ON the RO's east jamb,
# touching the jack. Neither derives from LANDING_EAST_FT; the deck's east edge happens to
# be the same jamb.
BEAM_X_FT = (FIELD_WEST_X_FT + 1.0 - (JOIST_MEMBER_WIDTH_IN + BEAM_WIDTH_IN) / 24,
             SERVICE_RO_EAST_FT - BEAM_WIDTH_IN / 24)
assert BEAM_X_FT[0] - 3.5 / 24 >= GARAGE_STEM_INSIDE_X_FT, "PT-BW-IC is inside the stem's board"
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


# The two seat beams, both on cast concrete at -0'-8 1/4" and both spanning 3'-7" between
# two bearings (5'-6" until 2026-09-11, when the deck's east edge came in to the door jamb).
# They grade the same way as a result: `structural.deck_beam_span` reads a real 3'-7" span
# off two Posts on each, rather than one falling back to a length.
# Nothing could bear these before: the garage stem tops out at -1'-0", ABOVE this soffit
# and north of the beam line, which is exactly why six invented stand-off brackets existed.
# Both now land on two cast piers each, at the same elevation and on the same span, so
# `structural.deck_beam_span` grades them identically.
# ** THE WEST END HANGS OFF THE COLUMN, IT DOES NOT RUN INTO IT (2026-09-15). ** Both seat
# beams are authored to the column LINE, so each ran 2 3/4" into the 6x6 standing there and
# shared 6 1/16" of height with it. That was invisible until this revision only because
# `_butt_joint` cleared any pair with a column in it — a column degenerates to a POINT in
# that test, so "an endpoint lands on its axis" was satisfied by a beam driven halfway in.
# The geometry is unchanged and cannot be: a hanger's flange has no representation, so the
# beam is carried to the joint it was authored at either way. What changed is that the joint
# is now AUTHORED (CN-BW-HGR-* below, HU28-2Z), and only an authored pair is cleared.
#
# ** bearing_refs STAYS ON THE PIERS, AND THAT IS A MEASURED DECISION. ** Re-pointing the
# west end at the column reads well -- it is the immediate support -- but it was tried and
# reverted: it takes `deck_post/PT-BW-W` and `/PT-BW-GW` from "dowel lap, class B"
# (d/c 0.30 and 0.46) to "axial, tied column" (0.024, 0.023), which is not a capacity gain,
# it is the dowel-lap limit state LEAVING the register for both piers. The column still
# stands on the pier (`supported_by`), so the load still arrives there; naming the pier is
# naming the end of that path, and it is the naming the pier_basis tributary is built on.
# The clash is cleared by the authored hanger, not by this field -- bearing_refs is a
# statement about load path, not about where the wood stops.
beam(1, "BM-BW-HOUSE-SEAT", LANDING_WEST_FT, HOUSE_SEAT_Y_FT,
     LANDING_EAST_FT, HOUSE_SEAT_Y_FT, ("PT-BW-W", "PT-BW-E"), SEAT_TOP_FT)
beam(2, "BM-BW-GARAGE-SEAT", LANDING_WEST_FT, GARAGE_SEAT_Y_FT,
     LANDING_EAST_FT, GARAGE_SEAT_Y_FT, ("PT-BW-GW", "PT-BW-GE"), SEAT_TOP_FT)
# The two garage-landing carriers. They start at the main landing's south framing edge so the
# joist field has them all the way through, and run north to the interior landing's end on a
# post apiece. Uid numbers stay 4 and 5 -- 3 was BM-BW-FW and is not reused.
for index, (suffix, x) in enumerate(zip(("FC", "FE"), BEAM_X_FT, strict=True), 4):
    beam(index, f"BM-BW-{suffix}", x, FRAME_Y0_FT, x, GARAGE_LANDING_END_Y_FT,
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
# The headers run 8 7/8" past the north columns to y=GARAGE_Y_SOUTH so the roof plane reaches
# the garage wall. R507.5.1's quarter-of-the-back-span is a DECK table and does not reach a
# roof header; what bounds this tail is the header's own bending and shear, which
# `engineering/roof_beam.py` grades.
#
# ** PLY COUNT IS THE LEVER, NOT DEPTH. ** Each header carries a 12' half-span of a 24' truss
# over the 5'-8 5/8" bay = 80 sf, under the roof-step drift case (42 psf balanced + up to
# 50 psf drift + 10 dead = 73.7 psf authored design snow), which is ~6,700 lb and a
# 4,787 lb-ft moment. A 2-ply 2x10 KDAT at C_M 0.85 is d/c 1.57 and fails outright; a 2-ply
# 2x12 reaches d/c 1.06 in bending and 0.76 in shear. 3-ply 2x12 is d/c 0.71 bending, 0.51
# shear, deflection 0.037" against L/240 = 0.286". `engineering/roof_beam.py` publishes all
# of it and notes/north_entry_piers.md Sec 5 is the hand-worked oracle.
#
# ** AND THE GLULAM ALTERNATIVE IS REFUSED (owner, 2026-09-12). ** BEAM_GLULAM_TREATED would
# carry this easily. What it would not do is stay in the register: `roof_beam.py`'s `_SECTION`
# matches a sawn N-2xM and nothing else, so a "3.5x11.875" makes both these records go
# INCOMPLETE, and nothing picks them up -- `engineering/glulam_beam.py` left the
# registered-kind tuple on 2026-09-11 and is deck-only besides, 40 psf live at C_D 1.0, which
# cannot carry this drift case. A d/c of 0.71 traded for a gap in the register is the whole
# argument, and cost only confirms it: ~$325-450 more over these 11.4 LF, at a material rate
# nearer 3x than the 4x this comment used to quote (prices.toml BEAM_GLULAM_TREATED/BEAM_KDAT).
#
# ** THE PLY SEAM, THE ONE REAL DURABILITY ARGUMENT, DOES NOT REACH THESE TWO. ** Both headers
# ARE the canopy's eave bearing lines: the trusses land on their TOPS, so both seams sit
# inside the roof assembly under the deck, 1'-4" inboard of the drip line (RF-BW-CANOPY's own
# overhang). FPInnovations' mass-timber durability guidance carves out exactly this case --
# avoid appressed parallel beams holding a capillary UNLESS the beams are preservative
# treated, and KDAT is. This is NOT the porch's 2026-09-06 refusal repeated: that one rested
# on butyl tape plus a formed cap, and the IRC commentary to R317.1.5 says outright that
# capping an exposed glulam with metal is not sufficient. Neither argument transfers, so the
# absence of a cap here is not a gap. (-> DESIGN-LOG.md, "Site and the four structures")
beam(6, "BM-BW-RW", LANDING_WEST_FT, PIER_LINE_Y_FT,
     LANDING_WEST_FT, GARAGE_Y_SOUTH.feet, ("PT-BW-CW", "PT-BW-CNW"), HEADER_TOP_FT,
     "3-2x12")
# ** THE EAST HEADER LANDS ON CONCRETE, NOT ON WOOD (owner, 2026-09-10). ** PT-BW-RE and
# PT-BW-RNE run unbroken from their footings to this soffit, so there are no 6x6 columns on
# this side at all -- see FULL_HEIGHT_COLUMNS below for why, and for what it buys.
beam(7, "BM-BW-RE", ROOF_COLUMN_EAST_X_FT, PIER_LINE_Y_FT,
     ROOF_COLUMN_EAST_X_FT, GARAGE_Y_SOUTH.feet, ("PT-BW-RE", "PT-BW-RNE"), HEADER_TOP_FT,
     "3-2x12")

# ** THE SCREEN PANEL'S SILL, WHICH IT CANNOT DO WITHOUT AND NEARLY DID. **
# W-BW-SCREEN stands on the column line at x=6'-0" and weighs 77 plf. Nothing was under it
# between the two seat beams -- the deck's westmost joist is 3 3/4" east of this line -- so
# its sill plate spanned 4'-11 3/4" carrying ~385 lb, which a flat 2x4 plate does not do
# (f_b ~2,200 psi). `structural.masonry_guard_bearing` is what said so, and it was right:
# a guard over the house's 50 plf allowance has to name its bearing line.
#
# A 2x8 between the two columns is the whole fix. Span 4'-6 1/4", w 77 plf, M 197 lb-ft,
# S 13.14 in3, f_b 180 psi -- d/c ~0.21 wet-service.
#
# ** IT SITS IN THE JOIST PLANE, NOT IN THE SEAT PLANE, AND THAT IS FORCED. ** At the seat
# top it would be at the same elevation as BM-BW-HOUSE-SEAT and BM-BW-GARAGE-SEAT, whose
# west ends are on this same line, and two beams crossing at one elevation is a clash in a
# model with no hanger (`structural.member_interference` reported it). Topped with the
# joists instead it clears both seats and doubles as the deck's west rim -- the joist field
# starts 3 3/4" east of this line to clear the columns, so without it that strip of board
# had nothing under it either.
#
# ** IT HANGS OFF BOTH COLUMNS, AND THAT IS THE ONLY BUILDABLE END (owner, 2026-09-15). **
# The 6x6 fully shadows the seat beam this sill would otherwise land on. Both are centred on
# this line, the column 5 1/2" wide and the seat beam 3", so the column faces stand at
# y 37.7292 / 42.2500 and the beam faces 1 1/4" further in at 37.625 / 42.354. No end
# condition reaches the beam without passing through the column: authored to the column
# CENTRES the sill buried 2 3/4" in each 6x6 over its full 7 1/4" depth, and shortened to the
# column FACES it stops 1 1/4" clear of its own bearing -- `test_analytical_graph` catches
# that second one as "a run of members hangs on no support". Measured both ways.
#
# So it stops at the faces and hangs there, on an HU28-2Z apiece (CN-BW-HGR-SCS-* in
# params/breezeway.py). This revises the owner's earlier "shorten, do not hang" -- that call
# assumed shortening alone left it bearing, and the arithmetic above is why it does not. It
# also puts the sill where everything else on this wall already stops: both columns carry
# `within_wall="W-BW-SCREEN"`, so the panel's three plate courses are cut at these same two
# faces, and the sill now dies into them on the same plane as the studs above it.
#
# ** bearing_refs FOLLOWS THE HANGER TO THE COLUMNS, WHICH IS THE OPPOSITE OF THE SEAT BEAMS
# ABOVE, AND DELIBERATELY. ** A seat beam's refs stay on its PIER because the pier is where
# its path ends and `pier_basis`'s tributary is built on that naming. This sill is different:
# its load is taken by the column itself, which stands on its own pier through `supported_by`,
# and the seat beams it used to name are members it no longer touches at all.
beam(10, "BM-BW-SCSILL", LANDING_WEST_FT, PIER_LINE_Y_FT + COLUMN_HALF_FT,
     LANDING_WEST_FT, GARAGE_SEAT_Y_FT - COLUMN_HALF_FT,
     ("PT-BW-CW", "PT-BW-CNW"), DECK_JOIST_TOP_FT, "2x8")

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
# ** THESE BECAME `Pad` ON 2026-09-14, AND THE ARGUMENT THEY WERE `Footing` FOR IS ANSWERED
# RATHER THAN DROPPED. ** It ran: a Pad is graded prescriptively by
# `structural.deck_footing_size` against an IRC DECK table that knows nothing about roof
# load, and these carry roof snow — so `engineering/spread_footing.py` graded a Footing
# instead, and six `spread_footing/` items went to the seal register for a flat square pad
# on presumptive soil, which is a lookup and not a design.
#
# What changed is that the check learned the roof. `checks/structural/deck.py::_roof_borne_posts`
# converts a post's roof-footprint share into the DECK currency R507.3.1 is written in —
# `(DECK_DEAD_LOAD_PSF + design snow) / DECK_TOTAL_LOAD_PSF`, **1.674** here — so the
# snow arrives at the table as equivalent area rather than being dropped. **PT-BW-RE and
# PT-BW-RNE are why that had to be built first**: they carry only `BM-BW-RE`, a roof header,
# so they were not in any deck's post list at all — not graded at zero, not graded — and
# deleting their Footing without it would have removed an item and put nothing in its place.
#
# ** THE SNOW IN THAT FACTOR IS THE DESIGN SNOW, NOT THE GROUND SNOW, SINCE 2026-09-18. **
# It read `Site.ground_snow_load_psf` (50) while `BM-BW-RE` overhead was designed at
# `preferences.toml [structural] roof_beam_snow_psf` (73.7, the ASCE 7 §7.7 roof-step drift
# off the house gable) — two answers about one roof, one storey apart, with the lighter of
# them under the heavier. The factor rose 1.2 -> 1.674 and the canopy share with it, 48 ->
# 67 ft² of equivalent deck. See `engineering/pier_basis.design_roof_snow_psf`.
#
# **The pour does not change.** `resolve/envelope.py` already drew a post-hosted Footing as a
# SQUARE of side `width`, so the same concrete is in the same place; see `_pad_outline`.
# Credited bearing area RISES 3.14 -> 4.00 ft² on a 24", because grading stops reading an
# inscribed circle that nothing was ever going to form.
#
# `bottom_elevation` is what makes these bear at depth rather than pin to the storey datum
# (-> Pad.bottom_elevation), and the shaft above each grows to suit.
# ** THE CAGE MUST BE STRUCTURED, NOT ONLY PROSE, OR ITS STEEL BILLS ZERO. **
# `vertical_reinforcement` is a free-text string for the drawings; `reinforcement_takeoff`
# reads `reinforcement` and nothing else. Authoring only the string added 3.18 cy of concrete
# to this house and exactly no pounds of steel, which `notes/rebar_backout.md`'s lb/cy ratio
# is what noticed. Both spellings, always, and keep them saying the same thing.
#
# ** THE SAME 8" CAGE THE COURT COLUMNS CARRY — ONE CROSS-SECTION, TWELVE POURS HOUSE-WIDE
# (six here, six in `params/sunken_garden.py`), LENGTHS PER POUR. ** That is the procurement
# fact: it is a fabricated part, not a field-bent detail.
#
# The durability goal is long-term performance in F3 + C2 — these stand up to 18 1/2" out of
# the ground at a salted entry. `PIER_CONCRETE_12` names EXPOSED_MIX, whose `bar_coating`
# carries the ladder (galvanized either ASTM A767 after fabrication or ASTM A1094 stock, the
# fabricator's choice named on the order; black bar at this cover and mix only as a written
# exception). NO per-bar coating here: the coating belongs to the pour, and stating it twice
# was the duplication struck on 2026-09-12. Epoxy and stainless stay refused.
ENTRY_PIER_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
    ),
    cover=inch(2.0),
    lap_class="B",
    source='8" cage, (4) #5 + #3 rings @ 10", one of twelve house-wide; notes/north_entry_piers.md §6 — the ACI 318-19 §10.6.1.1 1% floor, four bars per §10.7.3.1(b)',
)

#: The four piers that are a lateral system (fixed-base moment columns, `deck_post`'s bending
#: records) take the cage plus a #5 dowel at each vertical into their pad (decision #75 D6).
ENTRY_MOMENT_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
        BarSpec(role="dowels", bar=5, note="one per vertical, hooked into the pad"),
    ),
    cover=inch(2.0),
    lap_class="B",
    source="ENTRY_PIER_CAGE plus its base dowels; notes/north_entry_piers.md §6",
)
_MOMENT_PIERS = frozenset({"PT-BW-E", "PT-BW-RE", "PT-BW-GE", "PT-BW-RNE"})
#: ** 12" UNDER EVERY MOMENT PIER, AND THE BOTTOM GOES DOWN (owner, 2026-09-17). ** The #5 dowel
#: foot rests at 3" bottom cover, so embedment is thickness - 3": 10" gave 7.00", 8" gave 5.00",
#: against ACI 318-19 §25.4.3.1 ldh 7.11". 12" gives 9.00". Tops stay put -- pier heights, the
#: hydrant's 1 7/16" over the house-side tops, and the garage strip's aligned top all hold.
#: notes/north_entry_piers.md, 2026-09-17 addendum.
MOMENT_PAD_DEPTH_FT = 1.0

PIERS = []
def _pad_outline(x_ft, y_ft, side_in, along_in=None):
    """A square (or rectangle) pad footprint centred on the pier, in plan.

    ** THE SHAPE IS THE SAME SHAPE THE FOOTING ALREADY DREW. ** ``resolve/envelope.py``
    resolves a post-hosted ``Footing`` as a SQUARE of side ``width`` — the round the tag
    suggests was never what got built or billed — so authoring the square here changes no
    concrete volume at all. What changes is the credited BEARING AREA: ``deck_footing_size``
    stops reading the inscribed circle and reads the square, 3.14 -> 4.00 ft² on a 24".

    ``along_in`` (the y dimension) defaults to ``side_in`` and exists for the one thing a
    ``Pad`` can do that a ``Footing`` cannot: be a rectangle. ``structural.concrete_interference``
    scopes every Pad but only a wall-less Footing, so a lap that was invisible while these
    were Footings becomes a FAIL the moment they are Pads — and pulling a pad clear of a
    strip footing in one direction is what a rectangle is for.
    """
    half_x, half_y = inch(side_in) / 2.0, inch(along_in or side_in) / 2.0
    return (pt(ft(x_ft) - half_x, ft(y_ft) - half_y),
            pt(ft(x_ft) + half_x, ft(y_ft) - half_y),
            pt(ft(x_ft) + half_x, ft(y_ft) + half_y),
            pt(ft(x_ft) - half_x, ft(y_ft) + half_y))


FOOTINGS = []
#: The house-side pads run 18" north-south rather than the 24" their square drew, because
#: `FT-B-N1`..`-N4` — the basement's own north strip footing, on this same -9'-9 7/16" plane —
#: reach to y = 36'-8 1/8" and a 24" square centred on the pier line reached 2 1/8" into them.
#: That lap was there while these were Footings and was invisible: `concrete_interference`
#: scopes every `Pad` and only a wall-less `Footing`. 18" clears it by 1 1/16".
#:
#: The width makes the area back up, which is the whole reason a `Pad` is authored as an
#: outline instead of a width: 30" x 18" = 3.75 ft² carries PT-BW-W's 2.48 ft² requirement
#: with room, where a 24" square that cleared in y would have been 24 x 18 = 3.00 ft².
#:
#: ** ONE SIZE FOR ALL THREE, AND THE SHEET IS WHY. ** PT-BW-E and PT-BW-RE need 1.00 and
#: 1.60 ft² and would take a 24" x 18" pad, but three pad sizes are three rows in S-100's
#: FOUNDATION SCHEDULE and that sheet is fitted to its PLAN — one table row from the schedule
#: governing the sheet height again, which `test_schedule_columns.py` exists to catch. One
#: size is also one form, poured three times. The 0.75 ft² of concrete that buys back is
#: about $12.
_PAD_WIDE_IN = 30.0
_PAD_DEPTH_IN = 18.0

for _uid, _tag, _x, _height, _top in (
    ("BWPT01AAAA", "PT-BW-W", LANDING_WEST_FT, BEARING_TOP_FT - FOOTING_TOP_FT,
     BEARING_TOP_FT),
    ("BWPT02AAAA", "PT-BW-E", LANDING_EAST_FT, BEARING_TOP_FT - FOOTING_TOP_FT,
     BEARING_TOP_FT),
    # The east one is a COLUMN, not a pier: it does not stop at the bearing plane, it runs
    # on to the header soffit. Everything else about it -- section, cage, mix, footing -- is
    # unchanged, which is the point.
    ("BWPT03AAAA", "PT-BW-RE", ROOF_COLUMN_EAST_X_FT, HEADER_SOFFIT_FT - FOOTING_TOP_FT,
     HEADER_SOFFIT_FT),
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
        reinforcement=ENTRY_MOMENT_CAGE if _tag in _MOMENT_PIERS else ENTRY_PIER_CAGE,
        supported_by=f"PD-BW-{_tag.split('-')[-1]}"))
    FOOTINGS.append(Pad(
        uid=f"BWF{_uid[4:8]}AA", tag=f"PD-BW-{_tag.split('-')[-1]}",
        outline=_pad_outline(_x, PIER_LINE_Y_FT, _PAD_WIDE_IN, _PAD_DEPTH_IN),
        thickness=ft(MOMENT_PAD_DEPTH_FT if _tag in _MOMENT_PIERS else FOOTING_DEPTH_FT),
        assembly="PIER_BASE_12",
        bottom_elevation=ft(FOOTING_TOP_FT - MOMENT_PAD_DEPTH_FT if _tag in _MOMENT_PIERS
                            else PIER_BOTTOM_FT)))

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
# excavation and the same visit (owner, 2026-09-10). NOT out of the same pour any more: the
# strip is consolidated crushed stone as of 2026-09-15 (R403.5), so the shared thing is the
# hole and the bearing plane, and these three pads are the only concrete in it.
#
# ** COPLANAR IS ALSO WHAT SETTLES THE LAP. ** PT-BW-GW's and PT-BW-RNE's 2'-0" pads reach
# about 8" under `FT-GF-S1`/`-S3` in plan. At the house-side depth that was undermining and
# a sequencing note; at the garage's own depth the two pads simply meet the strip footing
# edge to edge on one plane, which is an ordinary detail and needs no note at all.
#
# ** AND THE HYDRANT PASSES UNDER, NOT THROUGH. ** `PR-G-HYDRANT-CW` runs north at x=11'-0"
# with its invert at -8'-10", so at this depth it clears the underside of FT-BW-GE by 1'-10"
# rather than threading between a shaft and a pad. `mep.footing_clearance` grades it.
#: ** THE GARAGE PIERS DECLARE NO POUR, AND THAT IS THE POINT. ** Each garage-side pier base
#: laps a strip footing on its own -7'-0" plane, and until 2026-09-20 it said so with
#: `Pad.cast_with`. Every `FT-GF-*` it named went to consolidated crushed stone on 2026-09-15
#: (2024 IRC R403.5, `params/foundations.py`), and nothing is cast monolithically with stone.
#: A concrete pad standing in a stone bed is not a pour in someone else's formwork: the stone
#: is placed around it in the 8" lifts R403.4.1 already requires, so there is no cold joint to
#: key and no interface steel to detail. `structural.concrete_interference` now drops a
#: footing whose `Footing.material` is not concrete before it picks its bodies, so the lap is
#: no longer a finding to declare away, and the three pads report as isolated pours instead.
#: The dangerous reading — crediting the strip's area to the pad as a combined footing — was
#: always closed elsewhere: `engineering/spread_base.pours_for` and `engineering/column_base`
#: both refuse a named pour that is not concrete, by name
#: (`notes/entry_column_base_fixity.md` 6f).
GARAGE_FOOTING_THICKNESS_FT = 8 / 12   # the garage strip's own 8", so the two tops align
GARAGE_PIER_BOTTOM_FT = -7.0
GARAGE_FOOTING_TOP_FT = GARAGE_PIER_BOTTOM_FT + GARAGE_FOOTING_THICKNESS_FT
PEDESTALS = []
for _uid, _tag, _x, _pad_in, _top in (
    ("BWPT05AAAA", "PT-BW-GW", LANDING_WEST_FT, 24.0, BEARING_TOP_FT),
    ("BWPT06AAAA", "PT-BW-GE", LANDING_EAST_FT, 18.0, BEARING_TOP_FT),
    # Again a COLUMN, the north half of the east pair (FULL_HEIGHT_COLUMNS below).
    ("BWPT04AAAA", "PT-BW-RNE", ROOF_COLUMN_EAST_X_FT, 24.0, HEADER_SOFFIT_FT),
):
    PEDESTALS.append(Post(
        uid=_uid, tag=_tag, position=pt(ft(_x), ft(GARAGE_SEAT_Y_FT)), size="12 round",
        height=ft(_top - GARAGE_FOOTING_TOP_FT), assembly="PIER_CONCRETE_12",
        vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
        reinforcement=ENTRY_MOMENT_CAGE if _tag in _MOMENT_PIERS else ENTRY_PIER_CAGE,
        supported_by=f"PD-BW-{_tag.split('-')[-1]}"))
    # ** THESE THREE LAP THE GARAGE STRIP FOOTING, AND THE LAP IS A DISPLACEMENT. ** They are
    # cast at -7'-0" on `FT-GF-S1`/`-S3`'s own plane, in the same excavation and at the same
    # time, and reach about 7 1/2" into it — which the comment above has always described as
    # meeting "edge to edge on one plane". Since 2026-09-15 the thing they reach into is
    # CONSOLIDATED STONE, not a pour: the pads go in first and the stone is compacted around
    # them, so the sequencing obligation this comment used to carry (continuous bottom steel
    # or dowels through a cold joint) is retired with the concrete that needed it.
    #
    # **They cannot be pulled clear**, and that has not changed: the pier line
    # stands 4 1/2" south of that footing's south face and the shaft is a 12" round, so the
    # COLUMN itself overhangs any pad stopping at the face. Clearing it in plan would need a
    # pad about 9" deep — 1 1/2" either side of the shaft — and making the area back up in
    # width turns it into a 40" grade beam. There is no rectangle here, and there does not
    # need to be one: monolithic is how it is built.
    #
    # The lap needs no declaration now that the strips are stone. Before `Pad.cast_with`
    # existed the only way to model it was a
    # `Footing` with an `under`, which took the base out of
    # `structural.concrete_interference`'s scope by pretending it carried a wall — and out of
    # `structural.deck_footing_size`'s prescriptive reach with it, which is what put three
    # `spread_footing/` items in the seal register for three flat square bases on presumptive
    # soil. Declared, the lap is reported by name with its numbers rather than passed over in
    # silence — and what the report now names is a pad bearing in stone, which needs no
    # interface steel because there is no cold joint to key. `concrete_interference` reaches
    # the same answer by material, so the pads are reported as isolated pours.
    #
    # **No widening was needed.** The areas were already there — 4.00 ft² under GW and RNE
    # and 2.25 under GE, against 2.48 / 1.60 / 1.00 required on the mn-2020 profile's
    # 1,500 psf — so the sizes are the sizes the Footings drew and the pour is unchanged.
    FOOTINGS.append(Pad(
        uid=f"BWFG{_uid[4:6]}AAAA"[:10], tag=f"PD-BW-{_tag.split('-')[-1]}",
        outline=_pad_outline(_x, GARAGE_SEAT_Y_FT, _pad_in),
        thickness=ft(MOMENT_PAD_DEPTH_FT if _tag in _MOMENT_PIERS
                     else GARAGE_FOOTING_THICKNESS_FT),
        assembly="PIER_BASE_12",
        # A moment pad keeps the strip's top and drops its bottom 4" below the strip's plane.
        bottom_elevation=ft(GARAGE_FOOTING_TOP_FT - MOMENT_PAD_DEPTH_FT
                            if _tag in _MOMENT_PIERS else GARAGE_PIER_BOTTOM_FT)))

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
FULL_HEIGHT_COLUMNS = ("PT-BW-RE", "PT-BW-RNE")
ROOF_COLUMNS = [
    # Both stand ON the screen panel's line, interior to its run, so the panel's plates and
    # studs are cut around them and the 2x4 infill butts the column faces (``Post
    # .within_wall``). The field is geometric only: these two still stand on their own
    # authored ABU66SS bases over cast piers, and still buy their cast-in bolts.
    Post(uid=_uid, tag=_tag, position=pt(ft(_x), ft(_y)),
         size="6x6", height=ft(COLUMN_HEIGHT_FT), assembly="POST_KDAT", supported_by=_pier,
         within_wall="W-BW-SCREEN")
    for _uid, _tag, _x, _y, _pier in (
        ("BWPT07AAAA", "PT-BW-CW", LANDING_WEST_FT, PIER_LINE_Y_FT, "PT-BW-W"),
        ("BWPT11AAAA", "PT-BW-CNW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "PT-BW-GW"),
    )
]

# ** THE 4'-2" INTERIOR CANTILEVER IS THE REAL DEFECT AND IT IS CHEAP TO FIX. ** BM-BW-FC
# and BM-BW-FE overhang the garage seat by 4'-1 7/8" on a 6'-2 1/2" back span -- 67%, against
# IRC R507.5.1's 25% -- carrying the top landing of ST-G-SERVICE 34" above the garage slab.
# Two KDAT posts on the slab end it.
#
# ** 4x4 ON 1" STANDOFF BASES, SIZED TO REACH THE BEAMS (owner, 2026-09-11). ** The first
# pass authored 6x6s at `BEARING_TOP_FT - SITE_GRADE`, the PIER top, so they stopped at
# -1'-3 1/2" under carriers whose soffit is -0'-8 1/4": a 7 1/4" gap, and nothing graded it.
# 25 3/4" from the slab at -2'-10" to the carrier soffit is the height, ABU44 on a cast-in
# AB-058-10-SS is the base (params/breezeway.py::INTERIOR_POST_BASES), and 4x4 is enough:
# `structural.deck_post_height` reads DECK_POST_HEIGHT_FT's 6'-9" for a 4x4 against 2'-1 3/4",
# and its "R507.4 wants 6x6" decoration only prints when the height is over the table.
INTERIOR_POST_HEIGHT_FT = SEAT_TOP_FT - SITE_GRADE.feet
#
# ** THEY BEAR ON THE SLAB AS CAST, AND THE THICKENING IS GONE (owner, 2026-09-11). ** This
# carried a "thicken to 10in over a 2ft square under each post, monolithic" note for a day.
# Two passes killed it:
#
#   * **The slab never needed it.** 8.1 ft2 tributary (the number `deck_post_size` prints) at
#     IRC R507.1's 50 psf is ~405 lb per post, ~600 lb with ST-G-SERVICE's top reaction. Under
#     a 3-1/2" square that is a LOWER contact pressure and a third the load of one tire of the
#     car this slab is already designed for. Spread through 3-1/2" of concrete it reaches the
#     1" under-slab XPS at roughly 5 psi against a 40 psi board, and only ~1 psi of that is
#     the sustained dead load that creep cares about.
#   * **What actually wanted the 10in was the ANCHOR BOLT.** AB-058-10-SS is 5/8" x 10" and
#     needs ~8" of embedment; the slab is 3-1/2" on foam. The bolt could not live in the slab,
#     so it dragged a thickening along to house itself. Dropping the bolt drops the thickening
#     -- see `params/breezeway.py::INTERIOR_POST_BASES`, where the base is authored
#     `anchored=False`: download crosses the plate into the pour, and the joint claims no
#     uplift and no lateral. Both are nil here.
#
# `structural.deck_footing_size` still reports NOT_APPLICABLE, and correctly: R507.3.1 sizes a
# spread footing over soil and there is no soil in this load path. A `Pad` remains the wrong
# element for any future thickening -- ONE pour with the slab has no element that says
# "monolithic", and an isolated pad reports a concrete_interference lap with `SL-G-FLOOR`.
INTERIOR_POSTS = [
    Post(uid=f"BWPT{9 + _i:02d}AAAA", tag=f"PT-BW-I{_s}",
         position=pt(ft(_x), ft(GARAGE_LANDING_END_Y_FT)),
         size="4x4", height=ft(INTERIOR_POST_HEIGHT_FT), assembly="POST_KDAT",
         supported_by="SL-G-FLOOR")
    for _i, (_s, _x) in enumerate(zip(("C", "E"), BEAM_X_FT, strict=True))
]


FRAME_ELEMENTS = [*NODES, *BEAMS, *PIERS, *FOOTINGS, *PEDESTALS, *ROOF_COLUMNS,
                  *INTERIOR_POSTS]

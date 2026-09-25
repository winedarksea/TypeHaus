# haus: editable
# Catlin MEP — the ERV's OUTDOOR side: the two north-facade hoods and the two wall
# penetrations they stand on.
#
# The legs that reach them, DU-ERV-OA and DU-ERV-EA, are in plan/mep_erv_risers.py with
# the three risers — they are one authored list because plan/mep.py spreads it whole.
# The system as a whole is documented once, in plan/mep_erv_l1.py's header.
from typehaus import (
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
from typehaus.model import Location, WallAttachment, deg
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
              footprint=(inch(12), inch(12)),
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
              mount=Mount(kind=MountKind.WALL, elevation=ft(5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-N3B", face="right", distance_from_start=inch(32),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
]
EQUIPMENT_ERV_HOODS_SECOND = [
    Equipment(uid="38M0D2FNXH", tag="EQ-S-ERV-HOOD-EA", kind=EquipmentKind.DUCT_MANIFOLD,
              footprint=(inch(12), inch(12)),
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
              mount=Mount(kind=MountKind.WALL, elevation=ft(7)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-N3B", face="right", distance_from_start=inch(8.375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
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
    # x=2'-0 5/8" since the chase was re-packed (2026-09-23): near jamb 3 7/8" from N-S-CH2.
    RoughOpening(uid="SMGEY3KGXE", tag="AO-S-ERV-EA", host="W-S-N3B",
                 position=from_node("N-S-CH2", inch(3.875)),
                 width=inch(9), height=inch(9), sill_height=inch(79.5),
                 penetration_for=("DU-ERV-EA",)),
]

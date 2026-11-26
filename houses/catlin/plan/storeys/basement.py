# haus: editable
# Basement — cast concrete walkout box, 18' center grid, sauna, stair (WP3.1).
# The perimeter is 8" except the east wall, which is 10" for the fireplace brick wythe
# (see the WALLS header below). South wall is the walkout side facing the sunken garden.
# Perimeter walls align on the concrete exterior face so the 4" of exterior XPS stacks
# directly under the framed wall's 4" polyiso+EPS (#43 control-layer continuity) — which
# is also why thinning the pour moves only the INSIDE face.
from ..ar_gypsum_band import AR_LOWER_BAND_ON_SLAB
from ..doorway_transitions import (D_B_BATH_VINYL_REDUCER, D_B_GYM_MAT_REDUCER, D_B_PLAY_MAT_ZBAR,
                                    D_B_SAUNA_MAT_REDUCER)
from typehaus import (
    Alarm,
    AlarmKind,
    BarSpec,
    ControlLayer,
    Door,
    DrainDish,
    FloorOpening,
    FoundationWall,
    FramingSpec,
    HumidityClass,
    Layer,
    LayerFunction,
    LayerMaterial,
    Node,
    Occupancy,
    Pad,
    PanelingSpan,
    PublishedSpan,
    ReinforcementSpec,
    Room,
    RoughOpening,
    SkinOverrun,
    Slab,
    SlabThermalBreak,
    StructuralRole,
    Wall,
    WallPaneling,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

# Plan datums (catlin_floorplan/"Colin House_Basement_Level 1.png") are *clear* face
# dimensions, so node lines are back-calculated from them: furnace room 8'-6" | stair
# shaft 7'-0" | playroom 16'-6" (north row); workshop 7'-6" | sauna 8'-0" | playroom
# 16'-6" (south row). The shaft was the code-minimum 7'-0" well (two 3'-3 3/4" flights +
# 4 1/2" partition) while W-B-STR at x=10' was 12" concrete, the 18' bearing grid fixing
# its east face at 17'-6".
#
# Two of those clears got 4" BIGGER on 2026-08-21 and the datums above are still the
# back-calculation, not the built number: thinning W-B-W1/W2 to 8" moved the west wall's
# inside face from x=1'-0" to 0'-8", so the furnace room reads 8'-10" and the workshop
# 7'-10". Both rooms only gain. The playroom was the architect's 16'-6" between two 12"
# walls; the east wall's 10" pour (2026-11-05) and the framed x=18' line make it larger.
#
# **The shaft is 7'-2 3/4" with 5/8" plywood**, and the furnace room 9'-1 1/8": framing
# W-B-STR/W-B-STR3 (see WALLS) put the well's west face on x=10'-3 1/4" instead of
# 10'-6", and the mechanical room took the other 3 1/8" of what the pour used to occupy.
# Both flights widened to 3'-5 1/16" in 2026; the final 1/8" is fitting clearance, so the code minimum is cleared
# by more than it was, not less.
# `clear_face` (the finish face) reports it.
#
# ================= THE WEST HALF WAS REPLANNED ON 2026-09-05 =================
#
# The south row above is history. Two doors were formed through 12" interior pours —
# D-B-GYM in W-B-CS2 and D-B-NE in W-B-CN — and they were the house's only openings
# through concrete. The dollars were small (a buck-and-blockout allowance, $500-1,200 the
# pair); the defect they bought was circulation. From the stair foot the only route to the
# furnace room was stair -> playroom -> gym -> aisle -> workshop -> furnace.
#
# Both are gone. What replaced them, on the owner's call:
#
#   * **The sauna rotated onto the south (garden) wall**, long axis east-west,
#     x 8'-10"..18'-0" by y 0'-0"..10'-0" on the node lines — an 8'-3 15/16" x 8'-10 11/16"
#     clear box against the 8'-1" x 12'-7" it was. (The north wall went to 10'-0" on
#     2026-09-05, round three; the node block below says what stopped it there.) It keeps WIN-B-SAUNA and is entered FROM
#     THE GYM through framed W-B-CS, a short walk from D-B-SUNKEN and the sunken garden,
#     which is what the brief asks the room for. (The rotation drew it x 4'-8"..18'-0", a
#     12'-2" box straddling two substrates; ROUND TWO the same afternoon pulled the west
#     wall onto N-B-S1 — see the node block below.)
#   * **The bathroom rotated** to run north-south along the framed stair wall
#     (W-B-STR3B/W-B-STR2), 3'-4 1/16" x 7'-1 1/4" clear, with its door on a new east wall.
#   * **A hall** runs west of W-B-CN2 from the stair foot south — 3'-3 15/16" clear, part
#     of RM-B-STAIR's own loop. It stopped at the y=18' line on 2026-09-05 and crossed into
#     the workshop through a cased opening; **on 2026-09-07 it runs the rest of the way to
#     the sauna's north wall at y=10'-0"** (see W-B-HALL-W in WALLS).
#
# ** THE 2026-09-05 "ACCEPTED CONSEQUENCE" IS RETIRED. ** It read: the playroom is reached
# only via the gym (stair -> hall -> workshop -> gym -> D-B-PLAY), and the workshop is the
# through-route from the stair to the gym. Running the hall south deletes W-B-CW2B and
# O-B-HALL with it and buys three things for the length of one partition:
#
#   * **D-B-GYM lands on the hall**, not on the workshop. Circulation is
#     stair -> hall -> gym -> D-B-PLAY, one room shorter than the replan left it.
#   * **The workshop is a room, not a corridor**, with a door of its own — D-B-SHOP, 3'-0",
#     in the hall's west side — and a way to shut it.
#   * **The equipment route is the hall**: 3'-0" at D-B-FURN and at D-B-SHOP, straight off
#     a 3'-5 1/16" stair flight.
#
# Nothing on the x=18' bearing grid moved and no concrete wall moved; W-B-CS2, W-B-CN and
# W-B-CN2 were pours then; they are framed since 2026-11-01 (decision #112, see below).
#
# **x=4'-8" and not the 5'-0" the plan was drawn at**, for one measured reason, and it is
# recorded because it is the trap anyone re-splitting this wall will fall into:
# `structural.frost_depth` lowers a footing's local grade by any open excavation within a
# frost depth (42") of it, and it reads the footing SOLID, not the wall. A split at 5'-0"
# leaves FT-B-S1 exactly 42.0" from SL-SG-FLOOR's rim — inside the reach, and outside
# SL-SG-FROST-W's own 42" shielding radius, which is what carried the un-split strip. 4'-8"
# was 46" from the rim, clear with 4" to spare. **The split is retired**: the sauna shrank
# east to the excavation edge the same afternoon, W-B-S1 is one segment again, and FT-B-S1
# is back inside the court's reach and back on the wings, where it started.
NODES = [
    # Perimeter (split at grid lines + partition tees)
    Node(uid="CBN001AAAA", tag="N-B-SW", position=pt(ft(0), ft(0))),
    Node(uid="CBN002AAAA", tag="N-B-S1", position=pt(ft(9, 10), ft(0))),
    Node(uid="CBN003AAAA", tag="N-B-S2", position=pt(ft(18), ft(0))),
    # ** 27'-2", NOT 28'-0", SINCE 2026-09-05. AND 28'-0" WAS NEVER THE EXCAVATION EDGE. **
    # This said "x=28'-0" is the excavation edge" for as long as it existed and it was not:
    # 28'-0" is `_x_ax_e`, the AXIS of the court's east retaining wall, whose faces are at
    # 27'-6" and 28'-6". The excavation edge is `_x_in_e` = 27'-6". So the split stood half
    # a wall INSIDE the soil, and W-B-S3-FR — a 2x6 framed wall — ran its last 6" of studs,
    # sheathing, waterproofing and outboard foam into that soil column, end-grain and foam
    # edge unclosed. Nothing grades it: `code.MN_1309_0406_waterproofing` and
    # `structural.foundation_unbalanced_fill` iterate FoundationWall, so a framed run is
    # invisible to both, and no check exists for wood against soil. The brick wythe made
    # exactly this retreat the same day (N-B-BRICK-E below); the framing did not follow.
    #
    # 27'-2" puts the framed run's whole stack 4" clear of W-SG-E1's 27'-6" face — the
    # mirror of the west end, where N-B-S1 at 8'-10" already laps 4" past W-SG-W1's 8'-6".
    # W-B-S4's concrete then covers the entire slot (27'-6"..28'-6") and gives the court's
    # closure wall a concrete bearing face over its full 12" width.
    #
    # The split is still at the one place on this line where the backfill condition changes,
    # which is what it is for; it is now at the place where that change actually happens.
    Node(uid="NW1W09NAD2", tag="N-B-S3", position=pt(ft(26, 2), ft(0))),
    # **The framed walkout's own node chain (2026-08-28).** W-B-S2-FR and W-B-S3-FR stand
    # ON W-B-S2/W-B-S3, which are 7 1/4" curbs now, so they are a second run of wall over
    # the same three stations. They cannot share those nodes: two wall edges between one
    # pair of nodes is a junction with no answer, and the solver said so — eight
    # `integrity.junction_polygon` ERRORs, one per layer, the moment they did.
    #
    # So the framed run is its own wall-graph component with its own nodes at the same
    # three x stations, both ends `open_end` — the same device W-B-BRICK uses for the
    # veneer wythe standing in front of this very wall. `open_end` is what tells
    # `integrity.wall_loop_open` that a single wall edge at a node is intended and not a
    # gap. The middle node carries two edges and needs no flag.
    #
    # A component with no closed loop resolves at outward sign +1 rather than the
    # perimeter's -1 (resolve/orientation.py), which is exactly why both framed walls
    # author `interior_room` explicitly instead of trusting the winding.
    Node(uid="QEDBCR7NYR", tag="N-B-S1F", position=pt(ft(9, 10), ft(0)), open_end=True),
    Node(uid="PGQVHV2VRH", tag="N-B-S2F", position=pt(ft(18), ft(0))),
    Node(uid="Z44TJSW6JJ", tag="N-B-S3F", position=pt(ft(26, 2), ft(0)), open_end=True),
    Node(uid="CBN004AAAA", tag="N-B-SE", position=pt(ft(36), ft(0))),
    Node(uid="CBN005AAAA", tag="N-B-E1", position=pt(ft(36), ft(18))),
    Node(uid="CBN006AAAA", tag="N-B-NE", position=pt(ft(36), ft(36))),
    Node(uid="CBN007AAAA", tag="N-B-N1", position=pt(ft(18), ft(36))),
    Node(uid="CBN008AAAA", tag="N-B-N2", position=pt(ft(10), ft(36))),
    Node(uid="CBN009AAAA", tag="N-B-NW", position=pt(ft(0), ft(36))),
    Node(uid="CBN010AAAA", tag="N-B-W1", position=pt(ft(0), ft(18))),
    # Interior grid + stair + sauna
    Node(uid="CBN011AAAA", tag="N-B-C", position=pt(ft(18), ft(18))),
    # y=13'-0" since 2026-11-25: the bath's north line, under main's N-M-C1, so W-B-CS2 and
    # W-M-C2 start on one station.
    Node(uid="CBN012AAAA", tag="N-B-C1", position=pt(ft(18), ft(13))),
    # The stair shaft runs the full north-row depth and lands on the center wall, so its
    # west wall tees into it rather than dying in the middle of the furnace room.
    Node(uid="CBN013AAAA", tag="N-B-STR", position=pt(ft(10), ft(18))),
    # ** BASEMENT REPLAN 2026-11-25: the sauna gives its north 2'-0 5/8" to a bathroom. **
    # The partition axis is y=7'-11 3/8": SAUNA_2X6 centred there leaves the sauna 81 1/2"
    # clear (south liner face y=9 1/4") and the bath 53 3/4" to W-B-BT-N (y=13'-0"), what
    # the WC's 15"/24" clearances need. The 2026-09-05 rounds (rotation onto the garden
    # wall, west wall on N-B-S1) stand; DESIGN-LOG has them. The bath band takes the old
    # D-B-GYM coupling with it: the door is on W-B-CS2 now, north of the bath.
    Node(uid="XTVNH0A54T", tag="N-B-SA-NW", position=pt(ft(9, 10), inch(95.375))),
    Node(uid="HN7GXN3ZM8", tag="N-B-SA-NE", position=pt(ft(18), inch(95.375))),
    # The bath's NW corner: W-B-BT-W meets W-B-BT-N.
    Node(uid="13TW58SQ3X", tag="N-B-BT-NW", position=pt(ft(9, 10), ft(13))),
    # Stair-foot bathroom's north partition (2026-07-30), spanning the shaft's full 7'-0"
    # clear width so it tees into both concrete walls' node lines (x=10', x=18"). y=21'-9 3/8"
    # is back-calculated: 3'-0" clear off W-B-CW2's north face (18'-6") plus half of
    # INT_2X6_STAGGERED_PLUMBING's 6 3/4" thickness.
    Node(uid="CBN015AAAA", tag="N-B-BA-W", position=pt(ft(10), ft(21, 9.375))),
    Node(uid="CBN016AAAA", tag="N-B-BA-E", position=pt(ft(18), ft(21, 9.375))),
    # **The bathroom rotated north-south on 2026-09-05** so the stair foot could keep a
    # hall east of it (x 14'..17'-6", 3'-3" clear) running south to a cased opening into
    # the workshop — the circulation the two retired concrete doors used to provide.
    # N-B-BA-W keeps its old duty (it is ``_MECH_Y``, the FS-M-WEST/FS-M-MECH split) and
    # N-B-BA-E still splits W-B-CN/W-B-CN2; both now carry only collinear edges, which is
    # fine.
    #
    # y=25'-6" is 6 3/8" south of FO-M-STAIR's west edge at 26'-0 3/8", so the well's west
    # jamb is still covered by W-B-STR3 + W-B-STR alone and `FO-M-STAIR.bearing_refs`
    # needs no edit.
    Node(uid="YW3E1CW7DT", tag="N-B-BA-NW", position=pt(ft(10), ft(25, 6))),
    #
    # ** THE WELL PARTITION'S CENTRELINE, x=14'-0" SINCE 2026-11-09. ** `inch(168)` is midway
    # between the well's faces (`resolve/stairs/common.py` reserves its 4 1/2" and builds
    # nothing in it), 1/16" off W-M-WELL above. The 6 1/2" bath and hall walls sit 1" west
    # of it (`alignment`, 2026-11-16) so their hall face, x=14'-2 1/4", is flush with the
    # 4 1/2" partition's from y=10' to the landing; the 1" step is on the bath side, inside
    # W-B-BA-N's tee. Nodes stay on the line. Everything
    # that references these two nodes rides along and needed no edit; the wet-wall risers,
    # which are absolute coordinates and not node references, did (mep_venting.py,
    # mep_supply.py, mep_supply_devices.py).
    Node(uid="ZHKG5KWP08", tag="N-B-BA-NE", position=pt(inch(168), ft(25, 6))),
    # FO-M-STAIR's south edge on the same line: W-B-WELL rises through the hole north of it.
    Node(uid="HATJTCSNNE", tag="N-B-WELL-HEAD", position=pt(inch(168), ft(26, 0.375))),
    Node(uid="R1KFP0S4NQ", tag="N-B-BA-SE", position=pt(inch(168), ft(18))),
    # The hall's south end (2026-09-07; y=13'-0" since 2026-11-25): on the x=14'-0" line, so
    # W-B-BA-E, W-B-WELL and W-B-HALL-W share one hall face. It splits the bath's north
    # wall (W-B-BT-N / -N2) so the hall partition tees into it.
    Node(uid="XE20Z4ZSS6", tag="N-B-HALL-S", position=pt(inch(168), ft(13))),
    # W-B-BA-N's east end since 2026-11-25: it splits the hall's west partition into the
    # under-stair closet's face (W-B-CL-E) and the water-heater alcove's (W-B-BA-E).
    Node(uid="S0NE2RPZXQ", tag="N-B-WH-NE", position=pt(inch(168), ft(21, 9.375))),
    # W-B-CW's east end. Keep the split so the ESS partition tees into the south wall here;
    # W-B-CW3 now continues W-B-CW's assembly at the same 2x4 stud depth. Its uid is unchanged.
    Node(uid="CBN017AAAA", tag="N-B-CW-E", position=pt(ft(6, 9), ft(18))),
    # ESS closet, NE corner of the furnace room. Two sides come free here — W-B-N3 on the
    # north (concrete, inner face y=35'-4") and W-B-STR on the east (inner face
    # x=9'-8 1/2", the framed wall's Type X leaf) — so it is two framed partitions, not
    # four. x=6'-0" and y=31'-0" leave 3'-6 1/8" x 4'-1 5/8" clear, more than the 2'-8 1/4"
    # cabinet it replaces, and clear of everything already on this side: the cold
    # trunk's riser (x=5'-0") and ED-B-SUMP-RC (x=1'-2" since 2026-10-29).
    # SP-B-STR-CD-DATA was the third of those; it went with the pour (electrical.py).
    #
    # **x=6'-0" is not a round number chosen for tidiness.** Neither concrete side of this
    # corner was split before, so both had to be, and a basement split that does not line up
    # with the storey above puts one wall over two. N-M-MECH3 already splits the main
    # storey's north wall line at exactly x=6'-0" (RM-M-MECH's shaft closet), so splitting
    # W-B-N3 there makes W-M-N3 sit over W-B-N3 and W-M-N3B over W-B-N4, one to one. The
    # east wall has no such gift — W-M-STRW runs y 26'-4"..36'-0" straight across W-B-STR's
    # y=31'-0" split — and that is called out on W-B-STR below.
    #
    Node(uid="CBN018AAAA", tag="N-B-ESS-N", position=pt(ft(6), ft(36))),
    Node(uid="BT88F385N4", tag="N-B-ESS-SW", position=pt(ft(6), ft(31))),
    Node(uid="GXJ9S72CKH", tag="N-B-ESS-SE", position=pt(ft(10), ft(31))),
    # ** W-B-WELL's north end: an OPEN END (2026-09-05), now at y=32'-1 7/8" (2026-11-20). **
    # That is P-M-STRWELL-S's north face, so the stud layer wraps both well posts and the
    # slot between them, slab to main floor. The free end takes its board, coat and beads
    # (`resolve/wall_ends.py`). The landing decks die into its faces, as the posts did.
    #
    # `open_end=True` is the honest description and not a silencer: a wall that dies in the
    # middle of a stair well has one edge at this node, which is `integrity.wall_loop_open`'s
    # whole subject, and the flag is how the model says "this end is meant to be free".
    Node(uid="SQZSP1P9DC", tag="N-B-CL-NE", position=pt(inch(168), ft(32, 1.875)),
         open_end=True),
    # The court face's brick nodes (N-B-BRICK-*, N-B-LINTEL-*) are built in params/court_face.py.
]

# The 8" perimeter's vertical steel, structured — the same `#5 @ 41" o.c.` the string
# beside it states, and IRC Table R404.1.2(8) is still where it comes from. Both spellings
# are kept: the string prints on the drawing, the struct is what `stem_flexure` grades and
# what `takeoff/reinforcement.py` bills, and `integrity.reinforcement_spec_agrees` raises an
# ERROR if they ever drift apart.
#
# Horizontals: IRC Table R404.1.2(1) places ROWS of #4, not a spacing, so `count` is rows —
# top − 6", mid-height and 6" off the base (decision #75 D8; notes/basement_wall_horizontal_
# steel.md §1). Verticals stay first: `retaining_basis.bar_for_roles` reads the first entry.
# Verticals from R404.1.2(8) sit at most 1 1/4" from the INSIDE face (R404.1.3.3.7.2), and
# the rows are tied to them there.
_B8_STEEL = ReinforcementSpec(
    bars=(BarSpec(role="vertical", bar=5, spacing=inch(41.0), face="interior"),
          BarSpec(role="horizontal", bar=4, count=3, face="interior")),
    cover=inch(1.25),
    source="IRC R404.1.2(8) verticals (the string beside it), R404.1.3.3.7.2 location; R404.1.2(1) horizontal rows",
)
# The 10" east walls read NR for verticals (R404.1.2(8) at 10"/45/8'/7'), and R404.1.2(1)'s
# horizontal rows apply regardless (notes/basement_wall_horizontal_steel.md §2).
_B10_STEEL = ReinforcementSpec(
    bars=(BarSpec(role="horizontal", bar=4, count=3),),
    cover=inch(2.0),
    source="IRC Table R404.1.2(1) horizontal rows; verticals NR per R404.1.2(8)",
)

WALLS = [
    # Perimeter foundation walls (8" or 10" + exterior XPS), CCW from SW corner.
    #
    # `lateral_support="top_and_bottom"` is the precondition for the prescriptive path, not a
    # detail: SL-B bears against the inside face at the bottom and FS-MAIN's diaphragm ties
    # the top, so IRC Table R404.1.2(8) applies (its footnote g presumes exactly this) rather
    # than R404.1.1 sending a wall retaining more than 48" to an engineered design. Stated on
    # each wall because the check refuses to assume it — assuming bracing is the unsafe
    # direction. (Horizontal steel is a separate table, R404.1.2(1) — one #4 within 12" of
    # the top and one at third points above 8' — not screened here.)
    #
    # **The row, spelled out.** GM soil is 45 psf/ft (mn-2020 profile). The wall runs
    # -13 7/16" (the bearing seat) to -9'-1 7/16" (the slab), so it is **exactly 8'-0"** of
    # pour -> the 8' row, not the 10' row a 9'-4" wall rounds up to. Grade is at
    # -2'-10" (params/site.py), so 6.29' of unbalanced fill -> the 7' row. Footnote f forbids
    # interpolating, so both round UP. At (45, 8', 7'): 12" reads NR, 10" reads NR, 8" reads
    # **#5 @ 41" o.c.**, which is where the nine 8" segments below sit. It was `#6 @ 48"` on
    # the 10' row; two feet of unsupported height is what a flat bearing seat bought, and it
    # is the cheaper bar at the tighter spacing. Re-read the cell rather than trusting this
    # comment: `checks/structural/_r404_table.VERTICAL_REINFORCEMENT[(8, 45, 8, 7)]`.
    # (Horizontal steel is a separate table, R404.1.2(1) — one #4 within 12" of the top and
    # one at third points above 8' — not screened here.)
    #
    # **Elevations are literals here and derived in ``params/main_deck.py``.** An editable
    # file may not import, so ``BEARING_SEAT`` (-13 7/16") and ``BASEMENT_DATUM``
    # (-9'-1 7/16") are transcribed onto every wall below.
    # ``integrity.basement_bearing_seat`` is what stops the two copies from drifting, the way
    # ``integrity.slab_thickness`` guards the deck's build-up. Do not edit one without the
    # other.
    #
    # **Which wall gets which thickness.** There is one flat bearing seat now, at -13 7/16"
    # all the way round, and the deck's soffit lands on the same plane the mudsill sits on.
    # Nothing competes for width there, and no wall needs extra width for bearing at all:
    # the 12" segments carried SL-M-DECK (retired 2026-11-01, now FS-M-NE trusses), and an 8"
    # wall would carry the trusses just as well.
    #
    # So the walls that are not 8" are so for reasons that are no longer about bearing
    # width, and each is worth stating.
    #
    #   W-B-E1/E2 — the east perimeter, **10" since 2026-11-05** (12" before; declined
    #     2026-10-11 on the odd form module, taken on the owner's call). FS-M-NE's truss ends
    #     land here and need no width. **W-B-E1 is held at 10" by the fireplace**: the brick
    #     wythe moved 2" east to lie tight on W-M-E1's 1/2" gwb (x 421 7/8"..425 1/2") and
    #     bears on this pour (422"..432", outer face pinned on 36'-0") bar 1/8". An 8" pour
    #     would put ~2" of it on the joists (notes/east_breast_bearing.md). E2 matches so the
    #     east wall is one section, no inside-face step at y=18'. NR either way.
    #   W-B-CS2, W-B-CN2, W-B-CN — were the centre line under the cast band; framed 2x6
    #     since 2026-11-01 (below).
    #   W-B-CS — FRAMED, and no longer on this list at all. It carried wood on both faces,
    #     so what it actually needed was a bearing wall and not a pour.
    #     The alignment trap that guarded it while it was concrete is still live and moved
    #     with it: the offset is a hardcoded HALF of the structure thickness, now
    #     `face("stud-ext", offset=inch(-2.75))`. `integrity.floor_bearing_grid` FAILs if
    #     the two ever part company, and three FloorSystems name this wall.
    #   W-B-STR — three dimensions are measured off its east face (see its own note below).
    #
    # The other nine segments — 108 LF, ~12.4 cy — are 8" carrying #5 @ 41" o.c. vertical,
    # authored on each of them below. Drop that string and the check FAILs, correctly.
    #
    # **The clear-face back-calculations above do not move.** The 2 9/16" lift is vertical
    # and the wall axes did not change, so every plan dimension in the NODES header still
    # reads as it did. What moved is the ceiling: 8'-0 15/16" clear under the joists,
    # 7'-10 7/8" under the concrete band's finished face, both over R305.1's 7'-0".
    #
    # 8" and not 10" (which also reads NR): 8" is the standard residential form module and
    # the market rate is quoted for it, whereas thickness above 8" adds concrete without
    # adding forming — so 10" would keep an odd-thickness forming premium and hand back
    # half the yardage to save ~245 LF of bar. See prices.toml's [wall_structure].
    #
    # The 8" walls also sit better than the 12" ones did: FT-B-* was a 20" strip on
    # `center_on="axis"`, so a 12" pour overhung its inside edge by 2" and an 8" one has a
    # 2" inboard toe. The footings follow the slab up 2 9/16" (params/foundations.py). Two of
    # them DO move in plan now: FT-B-S2/S3 carry a 2" `offset` since 2026-09-05, so their
    # south face is at -8" and W-SG-BRKBM's XPS isolation board occupies -8"..-10". The brick
    # plinth that used to be dimensioned off the -10" edge is retired with it.
    # **The south wall retains four different amounts of soil, and now says so.**
    # Without an authored ``unbalanced_fill``, ``structural.foundation_unbalanced_fill``
    # falls back to its documented proxy — grade (-2'-10") minus the wall bottom
    # (-9'-1 7/16") = 6.29' on every one of them,
    # rounded up to the table's 7' row. Its own docstring warns about exactly this
    # ("it over-reports a walkout wall whose exterior grade falls away ... author
    # ``unbalanced_fill`` where it matters"), and this is the walkout side: the sunken
    # garden is excavated from x=8'-10" to x=27'-6" (`_x_in_e`, the court's own clear face
    # — NOT 28'-0", which is the retaining wall's axis) with its floor flush with the
    # basement slab, so two of the four segments retain nothing at all.
    #
    #   W-B-S1   0'-0" .. 8'-10"   6'-4"  genuinely buried, west of the excavation
    #   W-B-S2   8'-10" .. 18'-0"  0      entirely inside the court
    #   W-B-S3   18'-0" .. 27'-2"  0      entirely inside the court
    #   W-B-S4   27'-2" .. 36'-0"  6'-4"  buried again, east of the excavation
    #
    # The 27'-2" break is 4" west of the court's face, so the framed run above W-B-S3 stops
    # clear of the soil column and W-B-S4's concrete carries the whole slot — see N-B-S3.
    #
    # 6'-4" is the measured 6.29' rounded UP to the nearest inch, the same direction
    # footnote f rounds the table row. It changes no grade: 6.3' still lands on the 7' row
    # and the two buried segments keep ``#5 @ 41" o.c.`` The two zero-fill segments drop
    # the bar with the load — see W-B-S2 below.
    #
    # **W-B-S1 and W-B-S4 carry BASEMENT_8**, not BASEMENT_8_GARDEN. That is
    # the same fill table read a second way: these two segments are the only south run whose
    # exposure is an ordinary grade line — 6'-4" of backfill with 2'-2 9/16" of wall standing
    # out of it — which is exactly the condition _PROTECTION_PANEL's GRADE-banded extent was
    # written for, and nothing like the nine feet of open court in between. So they buy about
    # 37 SF of panel over 16.83 LF instead of 106 SF of parge over a face that is under the
    # dirt. The court segments are not banded at all; they are bare XPS in a brick cavity.
    # See plan/assemblies.py for the whole stucco retirement.

    FoundationWall(uid="CBW101AAAA", tag="W-B-S1", start_node="N-B-SW",
                   end_node="N-B-S1", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(6, 4),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    # The sauna's south side. Since the 2026-09-05 shrink pulled the sauna's west wall onto
    # N-B-S1 this is the room's WHOLE south base: W-B-S1 west of it takes the buried wall's
    # own stack with no liner on it, W-B-S3 east of it the bare curb — but this one is a room
    # face
    # in a WET room, so it carries the liner variant of the curb (SAUNA_LINER_ON_GARDEN_CURB):
    # the vapour control has to be continuous on all four faces or it is not vapour control.
    # The liner grows 3 1/2" inward and mitres to
    # W-B-CS's at N-B-S2 — same assembly family, so no derived return there.
    # Alignment stays `face("concrete-ext")` with NO offset, unlike W-B-CS's inch(-6):
    # `_face_offset_from_interior` falls through the three liner layers (no name match) and
    # returns the concrete's outboard face, which on this wall *is* the datum, so the
    # concrete band stays at y 0"-8" exactly as the bare garden segments do. W-B-CS needs
    # its offset only to re-centre the concrete on the 18' bearing grid.
    # No vertical steel on these two: R404.1.2(8) is a table of *lateral earth pressure*,
    # and a wall standing in an open court retains none. The check stops grading them
    # either way at ``fill <= 0`` (foundation.py:146), so the bar comes out on the merits
    # and not because the check went quiet — the same reading that leaves W-B-CS2, W-B-CN
    # and the other interior cross walls bare. No dollars move with it: prices.toml notes
    # vertical steel has no line of its own, it is inside the $/cy rate.
    #
    # **W-B-S2 and W-B-S3 are 7 1/4" CURBS**, not full-height walls. The
    # 8'-0" of pour above them is a 2x6 framed wall — W-B-S2-FR and W-B-S3-FR below — for
    # the reason this comment block already gives twice over: they hold back nothing. Both
    # keep their tag, their uid and their footing, which is the whole point of putting the
    # curb on the old element rather than the framing: FT-B-S2/FT-B-S3, `_FROST_FORMED`,
    # `structural.frost_depth` and W-B-BRICK's dimensions all still name a piece of
    # concrete on a footing, and none of them moved. The balcony jamb holdowns did move
    # (2026-10-09): an STHD14 in the curb (CN-B-HD-PORCH-*) and an MSTC52 across the floor
    # band (CN-M-HD-PORCH-*), since their old +1" embedment had landed in W-B-S3-FR's studs.
    # The STHD14's 14" embed is deeper than this 7 1/4" curb, so W-B-S3 is cast monolithic
    # with FT-B-S3 (tasks.toml, the walls visit), straps set before that one pour.
    #
    # **Why the curb is kept and why it is 7 1/4".** The sunken garden is a court whose
    # floor is FLUSH with the basement slab (both -9'-1 7/16") with no way out but a drain;
    # heavy rain can stand in it. A concrete curb runs under the whole framed run so standing water
    # reaches concrete and not a bottom plate. 7 1/4" is the actual width of a 2x8, so the
    # curb is one board deep and the framed plate lands on it flat. It is also exactly
    # D-B-SUNKEN's old raised threshold — the door used to carry `sill_height=inch(7)` off
    # this same base — so the curb top IS the threshold now and the door's sill_height
    # goes to zero rather than to 7 1/4" (see D-B-SUNKEN in OPENINGS).
    #
    # `min_threshold_step` is the 7 1/4" above, stated where a checker can read it. Until
    # it was authored the curb height was a literal in two `top_elevation` values and a
    # paragraph of prose: raise the court floor, lower the curb, or split either wall, and
    # the water line moves with nothing in the engine saying so.
    # `building_science.flood_step_threshold` grades each wall's TOP against the highest
    # surface below it outside — SL-SG-FLOOR, the court floor at -109 7/16" — so both
    # curbs are held, not only the one D-B-SUNKEN happens to stand over.
    FoundationWall(uid="CBW102AAAA", tag="W-B-S2", start_node="N-B-S1",
                   end_node="N-B-S2", assembly="SAUNA_LINER_ON_GARDEN_CURB",
                   interior_room="RM-B-SAUNA",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(0),
                   top_elevation=inch(-102.1875), bottom_elevation=inch(-109.4375),
                   min_threshold_step=inch(7.25),
                   lateral_support="top_and_bottom",
                   skin_overrun=SkinOverrun(from_layer="foundation-coating", start=inch(4))),
    FoundationWall(uid="CBW103AAAA", tag="W-B-S3", start_node="N-B-S2",
                   end_node="N-B-S3", assembly="GARDEN_CURB_6",
                   interior_room="RM-B-GYM",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(0),
                   top_elevation=inch(-102.1875), bottom_elevation=inch(-109.4375),
                   min_threshold_step=inch(5.5),
                   lateral_support="top_and_bottom",
                   skin_overrun=SkinOverrun(from_layer="foundation-coating", end=inch(4))),
    # The framed run itself: base on the curb top (-102 3/16"), 88 3/4" to the same
    # -13 7/16" bearing seat every other wall in this basement stops on. `base_elevation`
    # is what lets a framed wall stand on something inside its own storey; `top` stays a
    # height measured from it, so the studs are 88 3/4" less the plates — about 7'-0 1/4",
    # not the 8'-0" they would be off the slab.
    #
    # `face("sheathing-ext")` is the deliberate mirror of the pour's `face("concrete-ext")`:
    # it pins the sheathing's outboard face on the node line, so the waterproofing and the 4"
    # of XPS continue on exactly the plane they occupy on W-B-S1 and W-B-S4 either side, and
    # W-B-BRICK's stand-off and its two arched reveals do not move (see N-B-BRICK-W
    # above).
    # The ties are W2.8 adjustable wire screwed to these studs through the foam and plywood
    # (IRC 2024 Table R703.8.4(1)); `structural.veneer_cavity_width` grades the reach.
    #
    # `interior_room` is authored on both rather than left to the storey's outward sign:
    # there are two wall edges on each of these node pairs now (the curb and the framing),
    # and an asymmetric stack should not depend on how the loop happens to wind.
    # top=90 5/16" lands the double top plate on the main floor's joists (z -11 7/8"): these are
    # BEARING walls and the floor bears on the plate. It stood at 88 3/4", 1 9/16" short, a
    # modelling gap with nothing in it (the concrete walls fill that band with a sill plate).
    # None (underside of the floor above) would stop at the finished ceiling, -12.5", 5/8" short.
    # The court face reaches the court walls (owner, 2026-11-25): each run stops 4" short, on
    # the pour's lap past W-SG-W1/E1 (N-B-S1 is the sauna wall's tee and cannot move), so the
    # vent gap, girts and LP panel run 3 3/4" on over W-B-S1/S4's XPS to the 1/4" sealant cap
    # on TB-SG-*-STEM's court edge (params/court_face.py); the curbs' coating runs to the board.
    # Girt ends then reach 4 1/2" past their end block; the panel edge takes an end nailer.
    Wall(uid="3BF9ZDQPT1", tag="W-B-S2-FR", start_node="N-B-S1F", end_node="N-B-S2F",
         assembly="SAUNA_LINER_ON_EXT_2X6_LP",
         alignment=face("sheathing-ext"),
         interior_room="RM-B-SAUNA",
         base_elevation=inch(-102.1875), top=inch(90.3125),
         structural_role=StructuralRole.BEARING,
         skin_overrun=SkinOverrun(from_layer="vent-gap", start=inch(3.75))),
    Wall(uid="Z4NRTGEDY5", tag="W-B-S3-FR", start_node="N-B-S2F", end_node="N-B-S3F",
         assembly="EXT_2X6_LP_PANEL",
         alignment=face("sheathing-ext"),
         interior_room="RM-B-GYM",
         base_elevation=inch(-102.1875), top=inch(90.3125),
         structural_role=StructuralRole.BEARING,
         skin_overrun=SkinOverrun(from_layer="vent-gap", end=inch(3.75))),
    # The east 8'-10" of the old W-B-S3, split off 4" west of the court's east face
    # (see N-B-S3 — the split used to sit on the wall AXIS, half a wall inside the soil).
    # Buried like W-B-S1, so it keeps the 7'-row bar — and it must join
    # ``params/foundations._FROST_FORMED`` with it, or FT-B-S4 loses FOOTING_EXPOSED_25
    # (the F3 exposed mix) the garden floor's low adjacent grade is the reason for.
    FoundationWall(uid="72HXFS8M11", tag="W-B-S4", start_node="N-B-S3",
                   end_node="N-B-SE", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(6, 4),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW104AAAA", tag="W-B-E1", start_node="N-B-SE",
                   end_node="N-B-E1", assembly="BASEMENT_10",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   reinforcement=_B10_STEEL),
    FoundationWall(uid="CBW105AAAA", tag="W-B-E2", start_node="N-B-E1",
                   end_node="N-B-NE", assembly="BASEMENT_10",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   reinforcement=_B10_STEEL),
    FoundationWall(uid="CBW106AAAA", tag="W-B-N1", start_node="N-B-NE",
                   end_node="N-B-N1", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW107AAAA", tag="W-B-N2", start_node="N-B-N1",
                   end_node="N-B-N2", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    # Split at N-B-ESS-N (x=6'-0") on 2026-08-23 so the ESS closet's west partition has a
    # node to tee into — `integrity.wall_loop_open` wants two edges at every node, and a
    # partition dying against the middle of an unsplit wall has one. Both halves keep
    # everything else: same assembly, same alignment, same reinforcement, one continuous
    # pour on site. W-B-N3 keeps its tag, uid and the east 4'-0" that W-M-N3 stacks on;
    # W-B-N4 is the west 6'-0" under W-M-N3B, and x=6'-0" is N-M-MECH3's line so the two
    # storeys split in the same place.
    FoundationWall(uid="CBW108AAAA", tag="W-B-N3", start_node="N-B-N2",
                   end_node="N-B-ESS-N", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="HEX0ZDQZEN", tag="W-B-N4", start_node="N-B-ESS-N",
                   end_node="N-B-NW", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW109AAAA", tag="W-B-W1", start_node="N-B-NW",
                   end_node="N-B-W1", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW110AAAA", tag="W-B-W2", start_node="N-B-W1",
                   end_node="N-B-SW", assembly="BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    # Center cross walls (12" concrete) — the 18' bearing grid. Every wall from here down is
    # an *interior* cross wall with soil on neither side, so `unbalanced_fill=ft(0)` says so
    # explicitly — without it `structural.foundation_unbalanced_fill` would read these as
    # retaining 8' of backfill apiece. R404.1.2(8) therefore decides nothing here; these are
    # 12" for the reasons set out in the WALLS header above, none of which is bearing width
    # any more.
    #
    # **W-B-CS is framed** — the last of the four 12" segments this header defends, and the
    # one it already admitted "carries wood on both faces and COULD go to 8"". It could go
    # to nothing: FS-M-WEST and FS-M-EAST land on it and W-M-C1 stacks on it, which is a
    # 2x6 bearing wall's job on every storey above. ~4.6 cy out, the same trade
    # W-B-STR/W-B-STR3 made. Keeps its tag and uid, so the IFC GlobalId does not move
    # (decision #16). FT-B-CS and its bedding need no edit, for the reason spelled out on
    # W-B-STR3 below.
    #
    # **The alignment offset is a hand-written HALF of the structure thickness and it had
    # to move in the same edit.** It was `face("concrete-ext", offset=inch(-6))` — six
    # being half of twelve — which re-centred the pour on the x=18' grid; on 5 1/2" studs
    # the same intent is `face("stud-ext", offset=inch(-2.75))`. Leaving the -6 would have
    # slid the bearing line 3 1/4" west without changing a single node.
    # `integrity.floor_bearing_grid` is the guard, and three FloorSystems name this wall.
    # The liner still grows east into the sauna, and `interior_room` still says so
    # explicitly rather than letting the component winding decide.
    #
    # **N-B-C1 USED TO READ UNKNOWN HERE, AND THAT WAS THE SOLVER BEING OVER-CONSERVATIVE.**
    # The framed run on the x=18' line is spf and W-B-CS2, collinear with it, is still 12"
    # concrete under the cast band, so `integrity.junction_fallback` saw two different
    # bearing materials in one THROUGH pair and asked for an interface rule. The old text
    # here answered "a bearing plate and dowels" — that predates the 2026-09-05 rotation and
    # describes a joint this model does not have. **Nothing bears on anything at N-B-C1.**
    #
    # W-B-CS3 (the framed segment at the node since the rotation) and W-B-CS2 both span
    # -109 7/16" to -13 7/16" — side by side over their whole height, each carrying its own
    # load straight down to its own footing. No beam or post lands at the node. What spans
    # onto the line lands on TOP of both: FS-M-WEST and FS-M-EAST run their joists in x and
    # name W-B-CS3 and W-B-CS2 alike in `bearing_refs`, and their deck is the diaphragm
    # across the joint. W-M-C2 above (y 156"..216") laps the y=166" node by 10" with
    # continuous plates. So there is no transfer between the two walls to detail, and no
    # geometry to miter either — collinear layers abut on the node plane and never overlap.
    #
    # The code agrees. R404.1.7 asks for lateral support of a foundation wall only where it
    # retains unbalanced backfill and exempts under 4 ft; W-B-CS2 is `unbalanced_fill=ft(0)`.
    # R602.10.8 sends braced-wall-panel-to-concrete connections to R403.1.6 — the sole plate
    # to the concrete BENEATH a wall, which the sill return already owns — and no braced wall
    # line runs on x=18' on any storey (they are all perimeter, plus the sauna's). Nothing in
    # the IRC governs a framed wall abutting a pour end-on where neither supports the other.
    # `resolve/topology._independent_bearing` is where that reasoning lives, guarded so that
    # a wall bearing on its neighbour still reports UNKNOWN.
    Wall(uid="CBW111AAAA", tag="W-B-CS", start_node="N-B-SA-NE",
         end_node="N-B-S2", assembly="SAUNA_LINER_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         interior_room="RM-B-SAUNA",
         structural_role=StructuralRole.BEARING),
    # The x=18' line north of the sauna, y 7'-11 3/8"..13'-0": the bath's east wall since
    # 2026-11-25 (no opening; D-B-GYM moved north onto W-B-CS2). FT-B-CS runs on under it.
    Wall(uid="NJ21M7MF6R", tag="W-B-CS3", start_node="N-B-C1",
         end_node="N-B-SA-NE", assembly="INT_2X6_BRG_HALF_DFL",
         layer_materials=(LayerMaterial(layer="gwb-b", material="gwb-mr"),), top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         structural_role=StructuralRole.BEARING),
    # ** THE REST OF THE x=18' LINE IS FRAMED TOO (2026-11-01, decision #112). ** W-B-CS2,
    # W-B-CN2 and W-B-CN were 12" pours because SL-M-DECK's cast band bore on them; that deck
    # is FS-M-NE's open-web trusses now, so they are the same 2x6 bearing wall as W-B-CS3 on
    # their existing footings (params/foundations.py `_FRAMED_WALLS`). Tags and uids kept
    # (decision #16). They still carry FS-M-WEST/-STAIR from the west and FS-M-NE from the
    # east (3 1/2" / 2" plate split, params/main_deck.py), W-M-C2/C3/C5/C5B and through them
    # RB-HOUSE, BM-M-HALL and FO-M-STAIR's east edge.
    Wall(uid="CBW112AAAA", tag="W-B-CS2", start_node="N-B-C1",
         end_node="N-B-C", assembly="INT_2X6_BRG_HALF_DFL", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         structural_role=StructuralRole.BEARING),
    # Split at N-B-BA-E so the bathroom's north partition tees onto a shared
    # node — else `integrity.wall_loop_open` reads it as a free end. W-B-CN keeps the tag,
    # uid, and the north 14'-2 5/8" that W-M-C5 stacks on, so the bearing stack is untouched.
    Wall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-BA-E",
         end_node="N-B-N1", assembly="INT_2X6_BRG_HALF_DFL", top=ft(8),
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),),
         alignment=face("stud-ext", offset=inch(-2.75)),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CBW121AAAA", tag="W-B-CN2", start_node="N-B-C",
         end_node="N-B-BA-E", assembly="INT_2X6_BRG_HALF_DFL", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         structural_role=StructuralRole.BEARING),
    # **The y=18' cross line is framed now.** All four of these were 12" cast
    # concrete for one reason: the 9" suspended deck over the basement was designed to span
    # between them. The deck is joists and an EPS-formed band since the basement-ceiling
    # overhaul, spanning 18'-0" east-west to the x=18' line like every storey above, so
    # nothing on this line carries a floor any more. Each keeps its tag and its uid — the
    # IFC GlobalIds are unchanged (decision #16) — and each picks up the assembly its own
    # use asks for rather than one thickness for all four. Their strip footings, footing
    # bedding and drain tile went with them (params/foundations.py): a stud wall stands on
    # the slab, and four runs of socked tile under an interior wall collected nothing.
    #
    # Centrelines stay on the node lines, so each room gains symmetrically — 2 5/8" a side
    # off the 2x6 walls, 3 5/8" a side off the 2x4 and steel ones.
    #
    # Tops are 8'-0" — **the bearing seat**. Everything in this basement
    # stops on one plane now: the concrete tops there, the deck's soffit lands there, the
    # mudsill sits there, and a framed partition's double top plate reaches it and no
    # further. It is the lower of the two ceiling planes, so a partition under a joisted bay
    # stops 1 9/16" short of the joist soffit and the gypsum runs continuously over it. A
    # stud wall that reaches the floor datum instead stands *inside* the joists, which is
    # what `structural.member_interference` reported on W-B-STR2 the moment it was framed.
    # Where a wall above stacks on one of these, `resolve/platform.py` grows the wall solid
    # up to meet it and leaves the double top plate here, which is what platform framing is.
    #
    # Split at the stair shaft's west wall so the shaft is a real tee, not a wall end. Also
    # split at N-B-ESS-S for the ESS closet's west partition, the same move
    # W-B-STR made for the bathroom. W-B-CW keeps tag/uid and the west 6'-9" (D-B-FURN
    # unchanged); W-B-CW3 is the 3'-3" stub forming the closet's south wall.
    #
    # W-B-CW, W-B-CW3 and W-B-CW2 now all use 2x4 studs. PR-B-WC2-DRAIN shifts 1 1/2" west
    # at its W-B-CW crossing (mep_drainage.py), landing in the clear bay at x=28 1/2". Other
    # services also cross in clear bays, so no service bores a stud on this line. The two
    # longer walls keep their painted gypsum finish in the 2x4 plumbing assembly.
    #
    # ** NONBEARING, stated (2026-09-22). ** FS-M-WEST's I-joists run east-west, parallel to
    # this wall, on the y=208"/224" lines either side of it; no floor names it in
    # `bearing_refs`, nothing `stacks_on` it, and its plate stops 3/4" under the bay's
    # blocking. Saying so is what lets D-B-FURN take R602.7.4's flat header.
    Wall(uid="CBW114AAAA", tag="W-B-CW", start_node="N-B-W1",
         end_node="N-B-CW-E", assembly="INT_2X4_PLUMBING", top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    # Former ESS-closet return; it now matches W-B-CW's stud depth and painted gypsum faces.
    Wall(uid="CBW123AAAA", tag="W-B-CW3", start_node="N-B-CW-E",
         end_node="N-B-STR", assembly="INT_2X4_PLUMBING", top=ft(8)),
    # Nothing runs in this one and nothing bears on it — a plain 2x4 partition. Keep the
    # tag: W-M-CLN and W-M-CLN2 name it in `stacks_on`.
    Wall(uid="CBW119AAAA", tag="W-B-CW2", start_node="N-B-STR",
         end_node="N-B-BA-SE", assembly="INT_2X4_PARTITION_HALF", top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    # ** W-B-CW2B IS GONE (2026-09-07) AND THE MERGE IT USED TO PREVENT IS THE POINT. **
    # It was the last 4'-1 5/16" of the y=18' line, carrying O-B-HALL, the cased opening
    # the hall crossed to reach the workshop. The note here used to say the wall had to
    # EXIST or the workshop and the stair loops would merge into one room — true, and now
    # deliberate: the hall runs south to the sauna wall instead, so this stretch of the
    # y=18' line IS the hall, RM-B-STAIR's face grows south through it, and the workshop
    # gets a door of its own (D-B-SHOP in W-B-HALL-W) rather than being walked through.
    # W-M-CLN2 no longer stacks on anything; see storeys/main.py and params/main_deck.py.
    # The playroom's south wall, 18'-0" of it, and the one that keeps D-B-PLAY (the 5'-0"
    # solid-core pair, gasketed). Staggered studs: it is the long wall between the playroom and the gym,
    # and it also runs under the concrete band, so it wants the sound break.
    Wall(uid="CBW115AAAA", tag="W-B-CE", start_node="N-B-C",
         end_node="N-B-E1", assembly="INT_2X6_STAGGERED_PLUMBING_HALF", top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    # Stair shaft's west wall — 2x6 bearing studs on x=10', full north-row depth
    # (reference: "Stairway 7' x 16' 6 1/2""). Framed, not poured: it
    # holds back no earth (`unbalanced_fill` was ft(0) the whole time it was concrete), and
    # what it actually does is carry FS-M-MECH/FS-M-STAIR's short joists — the stubs the
    # stair well leaves — and stack W-M-STRW above. That is a stud-wall job on a
    # footing, not a pour: ~9.8 cy of concrete out, and RM-B-FURNACE gains 3 1/8".
    # Split at N-B-BA-W: W-B-STR keeps tag/uid and the north 14'-2 5/8" that
    # W-M-STRW stacks on; W-B-STR2 is the 3'-9 3/8" stub alongside the bathroom,
    # carrying its three ceiling-level service crossings (plan/mep.py's WALL_SLEEVES).
    # Split again at N-B-ESS-SE (y=31'-0"), for the ESS closet's south
    # partition, exactly as it was split at N-B-BA-W for the bathroom. **Unlike the north
    # wall's split this one does NOT line up with the storey above**: W-M-STRW runs
    # y 26'-6"..36'-0" and crosses from W-B-STR onto W-B-STR3 halfway along. It keeps
    # naming W-B-STR — `resolve/stacking.py` picks it as the sole candidate on both basement
    # segments, since it is the only main-storey wall whose axis overlaps either by the 2'
    # minimum. Removing the main-storey's southern wall stub leaves this stack unchanged;
    # FO-S-STAIR's short local header replaces its opening-edge support (second.py).
    #
    # **ALIGNMENT is the whole of it**, and the two failure modes below are why it is what
    # it is. Framing this line was tried and backed out once, for one reason: that
    # attempt pinned the wall's EAST face on x=10'-6" to preserve the stair dimensions.
    #
    #   * `resolve/floors.py` bounds a floor system's span at the bearing wall's NODE axis,
    #     not at a wall face. A 6 3/4" stud line with its east face on 10'-6" runs
    #     9'-11 1/4"..10'-6" and leaves FS-M-MECH's joists 1/16" of plate to sit on —
    #     `integrity.floor_bearing_grid` wants 1 1/2" of structure each side of the axis.
    #   * Centring on the node fixed the bearing and pulled the footprint back off
    #     FO-M-STAIR's west edge at x=10'-6"; `_opening_edge_has_declared_bearing` then
    #     gave up and `structural.floor_opening_header` emitted a 9'-0" LVL, correctly.
    #
    # The way through is neither: align these studs plumb UNDER W-M-STRW's studs and move
    # the well's west face down to match the wall above (main.py's FO-M-STAIR is now at
    # x=10'-3 1/4"). `_axis_offset_from_interior` measures from the interior face, so
    # pinning the STUD layer's outboard face 2 5/8" east of the node puts the studs at
    # 9'-9 1/8"..10'-2 5/8" on both segments — the identical band W-M-STRW occupies above —
    # no matter what is added on the west, which is why both assemblies below can use the
    # same offset. That leaves 2 7/8" of structure west of the axis and 2 5/8" east, and a
    # full layer footprint reaching exactly x=10'-3 1/4", where the opening edge now stops.
    # The shaft goes 7'-0" -> 7'-2 3/4"; the thickness that came off goes to the mechanical
    # room. Set `interior_room` explicitly on both — do not let the component winding
    # decide which side layer 0 faces.
    #
    # **No plywood in the basement (owner, 2026-10-09).** The stair-line family's painted
    # ply face belongs to the mudroom above; down here W-B-STR/STR3B/STR2 swap that leaf
    # to 5/8" gwb (`layer_materials`, same thickness, no face moves) and W-B-STR3 already
    # carries Type X there.
    #
    # W-B-STR is also RM-B-ESS's west enclosure, so it takes the Type X variant:
    # `advisory.ess_enclosure` passed here on the mass of 12" of concrete and now passes on
    # a 5/8" Type X leaf on the closet face. W-B-N3 (the closet's north side) is still
    # concrete and still passes on mass.
    Wall(uid="CBW116AAAA", tag="W-B-STR", start_node="N-B-N2",
         end_node="N-B-ESS-SE", assembly="STAIRWALL_INT_2X6_BRG_TYPEX", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         layer_materials=(LayerMaterial(layer="ply-stair", material="gwb-ar"),),
         interior_room="RM-B-ESS",
         structural_role=StructuralRole.BEARING),
    # The same wall south of the closet: no Type X leaf, RM-B-FURNACE on the west face.
    # FT-B-STR / FT-B-STR3 and their beddings need no edit — `Footing.under` takes any wall
    # tag and `_resolve_footing` sets z1 from the wall's own z0, which for a framed wall on
    # the basement storey is the same -109 7/16" the pour authored (params/foundations.py
    # says so in as many words).
    # ** RETYPED 2026-09-05 to the UNDERSTAIR variant. ** Same uid, same alignment, same
    # interior_room, same BEARING role — only the finish leaf changes, from 5/8" stair
    # plywood to 5/8" Type X, because this whole run walls the storage under the arriving
    # flight and R302.7 wants gypsum on that side. See plan/assemblies.py for what it costs.
    # The closet stopped being its own `Room` later the same day (ROOMS) and the check went
    # quiet with the label; the wall does NOT go back to plywood — see ROOMS for why.
    Wall(uid="1H4KR79N9M", tag="W-B-STR3", start_node="N-B-ESS-SE",
         end_node="N-B-BA-NW", assembly="STAIRWALL_INT_2X6_BRG_UNDERSTAIR", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         interior_room="RM-B-FURNACE",
         structural_role=StructuralRole.BEARING),
    # Split again at N-B-BA-NW (y=25'-6") when the bathroom rotated: the same wall, same
    # assembly, same alignment, same bearing role, carrying the 3'-8 5/8" between the
    # bathroom's north partition and N-B-BA-W. The plywood face lands on the bathroom over
    # this stretch, which is what W-B-STR2's note below already says about its own run.
    Wall(uid="VZPMT59XVQ", tag="W-B-STR3B", start_node="N-B-BA-NW",
         end_node="N-B-BA-W", assembly="INT_2X6_BRG_EXPOSED_PLY", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         layer_materials=(LayerMaterial(layer="ply-stair", material="gwb-mr"),),
         interior_room="RM-B-FURNACE",
         structural_role=StructuralRole.BEARING),
    # The stub south of it: RM-B-BATH's west enclosure, nothing bearing on it, nothing
    # dimensioned off it. It carried the ESS closet's steel-stud Type X box before the
    # closet moved to the NE corner, and like W-B-CW3 above it is now just its neighbour
    # continued: W-B-STR3's assembly,
    # W-B-STR3's `alignment`, W-B-STR3's `interior_room`, so the studs stand in the same
    # 9'-9 1/8"..10'-2 5/8" band the whole line does and W-M-STRW is plumb over all of it.
    # `structural_role` is deliberately NOT copied: the wall type is shared, the load is not.
    #
    # Same reason as W-B-CW3: steel bearing against wood left N-B-BA-W and N-B-STR as
    # mixed-assembly junctions with no interface rule. The 5/8" plywood face now lands on the
    # bathroom rather than the stair, and the bathroom's west face moves 1" east; its three
    # ceiling-level crossings (vent, hot, cold) are bored, as they have been since the pour
    # went away.
    Wall(uid="CBW122AAAA", tag="W-B-STR2", start_node="N-B-BA-W",
         end_node="N-B-STR", assembly="INT_2X6_BRG_EXPOSED_PLY", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         layer_materials=(LayerMaterial(layer="ply-stair", material="gwb-mr"),),
         interior_room="RM-B-FURNACE"),
    # Sauna partitions — SAUNA_2X4 carries the hot-side liner (T&G/furring/foil-faced
    # polyiso) as part of the wall type, not a room finish override; the east wall (the
    # x=18' bearing line) takes it via SAUNA_LINER_INT_2X6_BRG. `interior_room` names the
    # liner face. W-B-SA-W is 2x6 so the 4" exhaust radial can drop inside its stud cavity;
    # the added depth goes to the cold/workshop side and preserves the sauna's clear face.
    Wall(uid="CBW117AAAA", tag="W-B-SA-W", start_node="N-B-S1",
         end_node="N-B-SA-NW", assembly="SAUNA_2X6", top=ft(7, 6),
         # 1/8" west of centre keeps the stud plane (and CD-B-SPA in its cavity) where it was
         # before the liner went 1" -> 3/4" (2026-10-16).
         alignment=face("center", offset=inch(-0.125)),
         interior_room="RM-B-SAUNA"),
    # The sauna/bath partition (2026-11-25): one wall, x 9'-10"..18'-0", liner south. 2x6
    # because it is the bath's wet wall (WC, lav and the vent rise in it;
    # `advisory.wet_wall_depth`), glass-mat on the bath face the whole run (the shower's
    # surround panel goes over it, the BATH2 pattern). W-B-SA-N2 retired with the hall tee.
    Wall(uid="CBW118AAAA", tag="W-B-SA-N", start_node="N-B-SA-NW",
         end_node="N-B-SA-NE", assembly="SAUNA_2X6", top=ft(7, 6),
         layer_materials=(LayerMaterial(layer="gwb-cold", material="gwb-glass-mat"),),
         interior_room="RM-B-SAUNA"),
    # The bath's north wall on y=13'-0", split at N-B-HALL-S: BT-N faces the workshop,
    # BT-N2 the hall and hosts D-B-BATH. Under W-M-BDN2, so `resolve/platform.py` lifts
    # its body to meet that wall; the framing still stops at the bearing seat.
    Wall(uid="23R8XDV8KM", tag="W-B-BT-N", start_node="N-B-BT-NW", end_node="N-B-HALL-S",
         assembly="INT_2X4_PARTITION_HALF",
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-mr"),), top=ft(8),
         interior_room="RM-B-BATH", structural_role=StructuralRole.NONBEARING),
    Wall(uid="EBNGQ671QP", tag="W-B-BT-N2", start_node="N-B-HALL-S", end_node="N-B-C1",
         assembly="INT_2X4_PARTITION_HALF",
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-mr"), LayerMaterial(layer="gwb-b", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),), top=ft(8),
         interior_room="RM-B-BATH", structural_role=StructuralRole.NONBEARING),
    # The bath's west wall, on W-B-SA-W's line: the shower's back.
    Wall(uid="E39DG7Y2XA", tag="W-B-BT-W", start_node="N-B-SA-NW", end_node="N-B-BT-NW",
         assembly="INT_2X4_PARTITION_HALF",
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-glass-mat"),), top=ft(8),
         interior_room="RM-B-BATH", structural_role=StructuralRole.NONBEARING),
    # ** THE HALL'S WEST SIDE, NEW 2026-09-07. ** Axis x=13'-11" (1" west of the node line,
    # hall face flush with W-B-WELL's) from the y=18' line south
    # to the sauna's north wall, walling the workshop off the hall and hosting D-B-SHOP.
    #
    # INT_2X6_PLUMBING and not INT_2X6_STAGGERED_PLUMBING — continuous full-depth studs —
    # for one measured reason: two services cross this line at y~10'-6", DU-B-ERV-R-GYM
    # (3" round, el 7'-6") and PR-B-SAUNA-VENT (2", el ~7'-4 1/2"). Both already bore
    # W-B-CS3's 2x6 studs at the same station, so the crossing is an established pattern
    # here; a staggered wall's 2x4 studs cannot take a 3 1/4" bore.
    # top=ft(8) is the bearing seat like every other partition in this basement.
    Wall(uid="CQRJZCM0R1", tag="W-B-HALL-W", start_node="N-B-BA-SE",
         end_node="N-B-HALL-S", assembly="INT_2X6_PLUMBING_HALF",
         alignment=face("center", offset=inch(-1)),
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),), top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    # The old stair-foot bath is gone (2026-11-25). W-B-BA-N moved south onto N-B-BA-W's
    # line (y=21'-9 3/8"): north of it the under-stair closet runs full height to the flight,
    # south of it is the water-heater alcove, open to the workshop through AO-B-WH-ALCOVE.
    Wall(uid="CBW120AAAA", tag="W-B-BA-N", start_node="N-B-BA-W",
         end_node="N-B-WH-NE", assembly="INT_2X4_PARTITION_HALF", top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    # The hall's west face north of y=18', split at N-B-WH-NE. The pocket (D-B-BATH) left
    # with the bath, so both halves are plain 2x6 like W-B-HALL-W. Axis 1" west of the node
    # line: the hall face is flush with W-B-WELL's (2026-11-16). W-B-BA-E keeps the alcove
    # half, where the water heater's grilles go.
    Wall(uid="9KNNSS9A4G", tag="W-B-CL-E", start_node="N-B-BA-NE", end_node="N-B-WH-NE",
         assembly="INT_2X6_PLUMBING_HALF",
         alignment=face("center", offset=inch(1)),
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB), LayerMaterial(layer="gwb-b", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),), top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="8BRZAXSW73", tag="W-B-BA-E", start_node="N-B-WH-NE",
         end_node="N-B-BA-SE", assembly="INT_2X6_PLUMBING_HALF",
         alignment=face("center", offset=inch(1)),
         layer_materials=(LayerMaterial(layer="gwb-b", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),), top=ft(8),
         interior_room="RM-B-WH-ALCOVE", structural_role=StructuralRole.NONBEARING),
    # ESS closet's two framed walls: UL U305 wood studs, 5/8" Type X both faces (owner,
    # 2026-10-30) — the library partitions with their gwb swapped to `gwb-x`, no new tag.
    # Steel studs and fire-retardant spray were both declined: the tested build is the cheap
    # one. Type X lid on RM-B-ESS (ROOMS). `advisory.ess_enclosure` grades walls and lid off
    # the resolved layers; the concrete north and the Type X W-B-STR leaf close the box.
    #
    # W-B-ESS-W carries D-B-ESS (it swings INTO the closet, the wall's left normal) and
    # PR-B-KITCH-DRAIN's 2" crossing at y=35'-0", 95"-97 1/2" AFF: no 3 1/2" stud takes a
    # 2 3/8" bore (R602.6 caps it at 60%), so this one is a nonbearing 2x6. PA-B-ESS-SEAL-W/-E
    # firestop that drain where it passes both closet walls (mep_supply_devices.py).
    Wall(uid="CBW124AAAA", tag="W-B-ESS-W", start_node="N-B-ESS-N",
         end_node="N-B-ESS-SW", assembly="INT_2X6_BRG", top=ft(8),
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-x"), LayerMaterial(layer="gwb-b", material="gwb-x"),),
         interior_room="RM-B-ESS", structural_role=StructuralRole.NONBEARING),
    Wall(uid="CBW125AAAA", tag="W-B-ESS-S", start_node="N-B-ESS-SW",
         end_node="N-B-ESS-SE", assembly="INT_2X4_PARTITION", top=ft(8),
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-x"), LayerMaterial(layer="gwb-b", material="gwb-x"),),
         interior_room="RM-B-ESS", structural_role=StructuralRole.NONBEARING),
    # ================= THE STAIR WELL'S PARTITION =================
    #
    # One wall, drawing a divider the model has always reserved space for and never built,
    # and putting the floor under the arriving flight to work as storage.
    #
    # ** IT USED TO BE TWO. ** W-B-CL-N closed this space off at y=31'-0" and made it a
    # 17.5 sf closet, RM-B-UNDERSTAIR; both are gone (2026-09-05, round three). The storage
    # runs the full length of the flight now — north past y=31'-0" and on under the landing
    # deck — and the volume is part of RM-B-STAIR again, reached only through D-B-CLOSET
    # from the furnace room: the north end runs on under the landing, too low to walk. See
    # ROOMS for why it is no longer a `Room`: with nothing closing it, a second seed in the
    # same face resolved the SAME 114.8 sf polygon twice, and nothing grades that.
    #
    # `resolve/stairs/common.py` budgets 4 1/2" between ST-B2M's two flights and the stair
    # frames it (u_split.py, well_wall.py), so W-B-WELL fills a RESERVED VOID with faces: it
    # is not colliding with the stair, it is the thing the stair already made room for. STAIRWELL_PARTITION_4H is 4 1/2"
    # exactly for that reason (plan/assemblies.py). It runs from N-B-BA-NE — the bathroom's
    # north-east corner — north to N-B-CL-NE. Its hall face is flush with W-B-BA-E's
    # (that wall is aligned 1" west). Its north end is free (`open_end` on N-B-CL-NE), at
    # P-M-STRWELL-S's north face: the stud layer wraps both well posts (2026-11-16).
    #
    # It stands in FO-M-STAIR's void, not under joists, so its board runs up to the main
    # floor (+1.0255906", W-M-WELL's base). Nothing lands on it and it is not BEARING.
    # W-B-WELL-HEAD is the stub still under the deck, south of the opening, at the 8'-0" seat:
    # outside the stair, so it frames itself as an ordinary 2x4 partition (2026-11-20), its
    # end stud face-to-face with the stair's stud-head.
    Wall(uid="VJPS36HCSB", tag="W-B-WELL-HEAD", start_node="N-B-BA-NE",
         end_node="N-B-WELL-HEAD", assembly="INT_2X4_PARTITION_HALF",
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB), LayerMaterial(layer="gwb-b", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),), top=ft(8),
         interior_room="RM-B-STAIR"),
    Wall(uid="9AYPA03VAE", tag="W-B-WELL", start_node="N-B-WELL-HEAD",
         end_node="N-B-CL-NE", assembly="STAIRWELL_PARTITION_4H",
         layer_materials=(LayerMaterial(layer="gwb-a", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB), LayerMaterial(layer="gwb-b", material="gwb-ar", extent=AR_LOWER_BAND_ON_SLAB),), top=inch(110.4630906),
         interior_room="RM-B-STAIR"),
    # W-B-BRICK, the court face's brick option, is built in params/court_face.py.
]

OPENINGS = [
    # Interior circulation
    # (2026-10-29: PR-B-ERV-COND left this wall for the bath lavatory on 10-17 and now runs
    # east on y=311". The pin below is history;
    # D-B-FURN has not moved.)
    # ** 3'-3", AND IT IS THE CONDENSATE LINE THAT SAYS SO (2026-09-05). ** A UI drag had
    # put this at 1'-6 1/16", and `from_node` offsets the NEAR JAMB, not the centre
    # (resolve/pipeline.py), so the 32" opening ran x 1'-6 1/16"..4'-2 1/16" — straight
    # across all three services in this wall. `mep.run_through_opening` FAILed three times:
    # CD-B-SPA at x=2'-0" and CD-B-DATA-SHOP then at x=2'-6", both 61" over the slab,
    # and PR-B-ERV-COND at x=2'-11", 49 7/8" up. The data run moved to x=10" on
    # 2026-09-29; the door's controlling condensate line has not moved.
    #
    # CD-B-SPA's south end is pinned at -4'-0" by two concrete sleeves, so it cannot be
    # lifted over the head. PR-B-ERV-COND is a gravity condensate drain that already starts
    # at 54" under an 80" head. The data run found the west-wall lane, but moving it does
    # not buy back the opening's old position: the condensate line still binds.
    #
    # So the door moves. The binding constraint is the condensate line at x=2'-11": the king
    # stud occupies [jamb-3", jamb-1 1/2"], so a jamb at 3'-3" puts the king's west face at
    # 3'-0" and clears the pipe's surface by 0.475". Both conduits clear the opening. 1" west
    # of the 3'-4" this door was authored at before the drag, which is why
    # mep_drainage.py's routing note (measured against 40") was restruck with it.
    #
    # ** WIDENED TO 36" ON 2026-09-07 ** — this is one of the two doors on the basement's
    # equipment route (stair -> hall -> D-B-SHOP / D-B-FURN), and a 32" leaf is not what a
    # water heater or an air handler passes through. The position does NOT move: the near
    # jamb is pinned west by PR-B-ERV-COND exactly as the paragraph above derives it, and
    # the far jamb only walks 5'-11" -> 6'-3", still 6" clear of N-B-CW-E.
    #
    # ** A FLAT NONBEARING HEADER, NO CRIPPLES (IRC R602.7.4, 2026-09-22). ** The 2-2x8 it
    # replaces carried nothing and had four runs through it; notes/framing_bore_limits.md §9.
    # A flat 2x4 since 2026-10-29, the 2x4 wall's own width (a flat 2x8 overhung both faces).
    # The derived RO raises it into PR-M-S-BATH1-DRAIN by 0.09": accepted (owner), 1.41" left.
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT-SWING36",
         position=from_node("N-B-W1", ft(3, 3)), header_spec="flat 2x4 nonbearing"),
    # Solid-core pair: the play room keeps the 5'-0" double opening, with flush solid
    # leaves instead of full glazing.
    # Derived RO since 2026-10-29, kept visually centred on W-B-CE (module suppressed).
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT-DOUBLE60",
         position=from_node("N-B-C", ft(6, 2)), doorway=D_B_PLAY_MAT_ZBAR),
    # **The two doors formed through 12" interior pours are gone (2026-09-05.)** This one
    # was a blockout in W-B-CS2 and D-B-NE was one in W-B-CN; between them they were the
    # house's only `openings.count[host_structure=concrete]`. The dollars were modest — a
    # buck-and-blockout allowance — and the real gain is circulation: from the stair foot
    # the furnace room used to be five rooms away (stair -> playroom -> gym -> aisle ->
    # workshop -> furnace).
    #
    # D-B-GYM is a 36" rough opening, no leaf (2026-09-09): hall and gym are one
    # circulation space. On W-B-CS2 since 2026-11-25, y 13'-7"..16'-7", north of the bath;
    # 7" clears W-B-BT-N2's face (y=13'-2 1/4") for the 4 1/2" jamb pack. FT-B-CS2 starts
    # under its south pack. `structural.door_framing_module` stays suppressed for it.
    RoughOpening(uid="CBD203AAAA", tag="D-B-GYM", host="W-B-CS2",
                 position=from_node("N-B-C1", inch(7)), width=ft(3), height=ft(6, 8),
                 doorway=D_B_GYM_MAT_REDUCER,
                 header_spec='5.25x7 LVL', header_jacks=2,
                 published_span=PublishedSpan(
                     source="Boise Cascade EWP, VERSA-LAM 1.7 2650 Header Guide (Eastern), 06/2009 r 07/21/2011, p.16, VERSA-LAM 1.7 2650 Floor Load Tables (100% Load Duration)",
                     table="5-1/4\" width, 7\" depth, 4 ft span: Allowable Total Load 3632 plf, Allowable Live Load not shown so the Total Load controls, minimum bearing 1.9\" at end",
                     member='5.25x7 LVL',
                     span=ft(4),
                     capacity_plf=3632.0,
                     min_bearing_in=1.9,
                     condition="read as a load table, not a header-type column: the guide's header columns stop at Roof + 2 Floors and this stack carries three floors; span is centre to centre of supports, read at the next tabulated span with no interpolation; Total Load limited by shear, moment or L/240, in addition to the beam's own weight, at 100% duration and compared with the governing ASD combination; 1.9\" of end bearing is the row's at its full 3632 plf, against 3\" on 2 jacks across the full 5-1/4\" width; lateral support assumed at each support and along the compression edge (plates and head cripples over it); dry use; uniform load only; see notes/header_spans_r602_7.md section 5b")),
    # The bath's door (2026-11-25): a 30" privacy swing in W-B-BT-N2 off the hall's south
    # end, swinging in and hinged east so the leaf parks on W-B-CS3 clear of the lav.
    Door(uid="CBD207AAAA", tag="D-B-BATH", host="W-B-BT-N2", type_ref="DT-INT-SWING30-PRIV",
         position=from_node("N-B-HALL-S", inch(6.5)), flip_swing=True, flip_hinge=True,
         header_spec="flat 2x4 nonbearing", doorway=D_B_BATH_VINYL_REDUCER),
    # ESS closet door: a cheap 24x80 steel leaf with a small tempered vision lite in a KD
    # frame, on spring hinges (DT-INT-STEEL24-LITE; owner 2026-10-30, not a rated door). It
    # swings into the closet. 18 7/8" off N-B-ESS-SW lands it on the wood stud module
    # (`structural.door_framing_module`) and keeps it clear of EQ-B-ESS-BATT and the post.
    Door(uid="CBD208AAAA", tag="D-B-ESS", host="W-B-ESS-W", type_ref="DT-INT-STEEL24-LITE",
         position=from_node("N-B-ESS-SW", inch(18.875))),
    # ** The under-stair storage's door, new 2026-09-05 — the thing that makes the floor
    # under the arriving flight reachable without walking the well. ** In W-B-STR3, opening
    # WEST into RM-B-FURNACE: W-B-STR3 runs north-to-south, so its default left-hand normal
    # is east — into the space under a rake, where no leaf can open. `flip_swing` sends it
    # into the mechanical room instead. It is the only way into the storage, and the
    # full-height way in to PA-B-MAIN-SHUTOFF.
    #
    # 32" leaf on the 6'-0" head (a 6'-8" head would be six inches inside the stringer); no
    # casing, standard 1/2" undercut. Kept at 32" when EQ-B-WH left the closet for the
    # workshop (2026-11-09): the fewest differences. 6 3/4" off N-B-BA-NW: the south jamb
    # clears FO-M-STAIR's corner (y=312 3/8") so its point load stays off the head, and the
    # RO cuts two studs. Opens the full 90 since EQ-B-ERV moved south to the sink (2026-11-21):
    # the case clears the sweep by 4 3/8", and the ERV lines run above the head.
    Door(uid="B43P8B5Y0T", tag="D-B-CLOSET", host="W-B-STR3", type_ref="DT-INT-CLOSET32",
         position=from_node("N-B-BA-NW", inch(6.75)), flip_swing=True, flip_hinge=True),
    # ** O-B-HALL IS GONE AND D-B-SHOP REPLACES IT (2026-09-07). ** The cased opening was
    # 2'-10" through W-B-CW2B and was justified by the workshop being the through-route
    # from the stair to the gym — "a door across a circulation spine buys nothing". The
    # hall reaching the sauna wall retires that argument: the workshop is a room at the end
    # of a branch now, not a corridor, so it gets a 36" leaf it can shut.
    #
    # Swing derivation (resolve/pipeline.py): W-B-HALL-W runs north->south, whose left-hand
    # normal is EAST, so `flip_swing` sends the leaf WEST into the workshop — where it
    # belongs, since a leaf opening east would stand in a 3'-4" hall. The hinge defaults to
    # the start-node (north) jamb, parking the open leaf against the workshop's empty north
    # strip rather than over the benches on its west wall.
    #
    # The 7" offset puts the RO's centre on D-B-GYM's (y=15'-1", 2026-11-25), so the
    # equipment route is straight through.
    # Derived RO since 2026-10-29: stays on D-B-GYM's centre (module suppressed) and
    # ED-B-WORKSHOP-SW moved north to clear it.
    Door(uid="GEVMH8HHZ9", tag="D-B-SHOP", host="W-B-HALL-W", type_ref="DT-INT-STEEL36-KEYED",
         position=from_node("N-B-HALL-S", inch(7)), flip_swing=True),
    # The sauna is entered FROM THE GYM since the rotation — the short route to D-B-SUNKEN
    # and the sunken garden, which is what the brief asks the room for. Same uid, same 24"
    # leaf, rehosted from W-B-SA-W onto W-B-CS. RO ~y 4'-2"..6'-4" since 2026-11-25 (the
    # shower left the NE corner): north of the heater, clear of D-B-SUNKEN's inswing arc.
    # Swings out into the gym on the default.
    Door(uid="CBD205AAAA", tag="D-B-SAUNA", host="W-B-CS", type_ref="DT-INT-SAUNA24",
         position=from_node("N-B-SA-NE", inch(19.375)), flip_hinge=True, doorway=D_B_SAUNA_MAT_REDUCER,
         header_spec='5.25x7 LVL', header_jacks=2,
         published_span=PublishedSpan(
             source="Boise Cascade EWP, VERSA-LAM 1.7 2650 Header Guide (Eastern), 06/2009 r 07/21/2011, p.16, VERSA-LAM 1.7 2650 Floor Load Tables (100% Load Duration)",
             table="5-1/4\" width, 7\" depth, 3 ft span: Allowable Total Load 5395 plf, Allowable Live Load not shown so the Total Load controls, minimum bearing 2.1\" at end",
             member='5.25x7 LVL',
             span=ft(3),
             capacity_plf=5395.0,
             min_bearing_in=2.1,
             condition="read as a load table, not a header-type column: the guide's header columns stop at Roof + 2 Floors and this stack carries three floors; span is centre to centre of supports, read at the next tabulated span with no interpolation; Total Load limited by shear, moment or L/240, in addition to the beam's own weight, at 100% duration and compared with the governing ASD combination; 2.1\" of end bearing is the row's at its full 5395 plf, against 3\" on 2 jacks across the full 5-1/4\" width; lateral support assumed at each support and along the compression edge (plates and head cripples over it); dry use; uniform load only; see notes/header_spans_r602_7.md section 5b")),
    # The framed-wall datum is the curb top; the rough sill is recessed 1.75 inches
    # into the curb seat while the installed threshold remains above the court.
    #
    # **It swings IN, and that is a code requirement, not a preference.** The curb makes
    # this door a 7 1/4" step down to the court, which is R311.3.2's one-riser allowance
    # for a door that is not the required egress door — and that allowance is conditioned
    # on the door NOT swinging over its landing. `flip_swing=True` used to sweep it south
    # into the court, over the very landing being measured, which voids the relief and
    # drops the limit to 1 1/2". Swinging north into the gym is what makes the 7 1/4"
    # legal. `code.R311_3_exterior_landing` now tests `swing_clearance` and will say so.
    #
    # ** ITS HEADER IS IN THE FLOOR BAND (owner, 2026-10-31). ** An 82 7/8" RO leaves 4 5/8"
    # under the plates, and the table's 2-2x10 stood 4 5/8" into them
    # (integrity.header_under_plate; geometry review C3-E2). FS-M-EAST's flush 2-ply LVL
    # (params/main_deck.py) carries the band over the opening; this wall runs its jacks to
    # the plates and takes a flat nailer at the head for the liner.
    Door(uid="CBD206AAAA", tag="D-B-SUNKEN", host="W-B-S3-FR", type_ref="DT-EXT-FRENCH60-CATALOG",
         position=from_node("N-B-S2F", inch(8.34375)), sill_height=inch(-1.75),
         header_in_band="FS-M-EAST"),
    RoughOpening(uid="CBPSEAT0001", tag="AO-B-SUNKEN-SEAT", host="W-B-S3",
                 position=from_node("N-B-S2", inch(8.34375)),
                 width=inch(63.3125), height=inch(1.75), sill_height=inch(5.5),
                 depth=inch(6), depth_from="interior"),
    # The tread's bed (2026-11-04): the curb's membrane/XPS tail cut down under D-B-SUNKEN's
    # Trex tread, stopping at concrete, and refilled with 40 psi XPS (the installation's
    # `foam-bed-course`). Its floor is that course's underside. Replaced
    # AO-B-SUNKEN-CURB-APPROACH, the AridDek approach's 6 1/2" recess.
    RoughOpening(uid="N1SP53PC4S", tag="AO-B-SUNKEN-TREAD-BED", host="W-B-S3",
                 position=from_node("N-B-S2", inch(8.34375)),
                 width=inch(63.3125), height=inch(2.75), sill_height=inch(4.5),
                 depth=inch(4.06), depth_from="exterior", framing_required=False),
    # The water-heater alcove's mouth (2026-11-25): 34", what fits with its packs between
    # W-B-STR2's studs and W-B-BA-E's (41 3/8"); flat head, the wall is nonbearing.
    RoughOpening(uid="J266MAWD85", tag="AO-B-WH-ALCOVE", host="W-B-CW2",
                 position=from_node("N-B-STR", inch(6.5)), width=inch(34), height=ft(6, 8),
                 header_spec="flat 2x4 nonbearing"),
    # WT-1424: a sauna wants a small window, less glass to lose heat through. The 14"
    # family's one appearance in a concrete wall, where the usual 16" stud-module reason for
    # that width doesn't apply — size is the point here. The retired WT-3660 type and
    # WT-3660-FIX stay in the catalog.
    # Sill 3'-8" (head 5'-8"), up three 2 2/3" brick courses from 3'-0". The reason was the
    # Ishtar registers — the sill rose with the plinth so a band would not cut across the
    # glass — and the registers are gone (assemblies.py BASEMENT_BRICK_VENEER is one flat
    # unglazed field since 2026-09-04). The elevation stays because it is a good one on its
    # own: still on the brick course, still well above the 18" bench top (placeables.py),
    # and moving it would move AO-B-BRICK-WIN with it for no gain.
    # Host and datum are the framed walkout: W-B-S2-FR's base is the curb top, 7 1/4" above
    # the slab this sill used to be measured from, so ft(3, 8) becomes inch(36.75). The
    # glass does not move — the head stays where AO-B-BRICK-WIN's arched reveal in front of
    # it expects it, and that reveal is datumed off W-B-BRICK's own base and needed no edit.
    # It sits 3'-7" off the corner (3'-3" until the court narrowed, 2026-09-22): a hole in a pour lands where you form it,
    # while a 14" RO in a stud wall wants a BAY CENTRE, where the bay's own two studs carry
    # the rough sill and head nailer and it needs no header, no jacks and no kings at all
    # (preferences.toml's `max_window_ro_unbroken_in`). W-B-S2-FR lays out from layout line
    # LL-W-A-S1 and reaches the module 6" along itself, so its bay centres are 14" + n x 16"
    # and 3'-7" puts the 14" opening on a bay centre again now N-B-S1F is at 9'-10". `structural.window_framing_module`
    # said so, at 7" off, the moment the wall stopped being concrete.
    Window(uid="CBX301AAAA", tag="WIN-B-SAUNA", host="W-B-S2-FR",
           type_ref="WT-1424-FIX-T", position=from_node("N-B-S1F", ft(3, 7)),
           sill_height=inch(36.75)),
    # The brick option's reveals (AO-B-BRICK-WIN/-DOOR) are in params/court_face.py.
]

ROOMS = [
    Room(uid="CBR401AAAA", tag="RM-B-FURNACE", seed=pt(ft(5), ft(30)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete", unpainted=True),
    # W-B-STR now separates this from the furnace room, so the stair bottom is its own
    # space instead of dumping arrivals into the mechanical room.
    # **The HALL is part of this room's loop, not a room of its own** (2026-09-05): the
    # 3'-3 15/16" slot west of W-B-CN2, from the stair foot south to the y=18' line, is inside
    # the same closed face and needs no `Room` — it is circulation on the same floor finish
    # with the same occupancy, and a second `Room` here would only split one space in two
    # for every check that walks rooms.
    # **The seed moved into the hall on 2026-09-05.** (14', 30') is inside W-B-WELL's new
    # footprint (x 13'-8 3/8"..14'-0 7/8"), which would be a guaranteed
    # `integrity.room_unclaimed`. The hall is the same room, so the seed only has to find it.
    # ** THE HALL'S CEILING IS OPEN ON PURPOSE (2026-09-13), AND SF-B-HALL IS RETIRED. **
    # DU-B-ERV-R-GYM and PR-B-SAUNA-VENT cross the hall's south end and cannot be routed
    # anywhere else; the box that hid them is gone and this sentence carries the room. Same
    # call the gym made, one wall west. `mep.run_in_finished_volume` quotes it and still
    # holds both runs to the 6'-8" headroom line — see the retirement note above SOFFITS.
    #
    # ** NOTHING CROSSES THE FLIGHT (2026-09-22). ** D3 laid GYM and PLAY stacked down
    # x=17'-0" from y=29'-6" and BATH across the north end — i.e. over ST-B2M, 1" to 17" into
    # the 6'-8" over its nosings. `code.R311_7_2_stair_headroom` counts runs now, so the
    # radials and both conduits reach the hall SOUTH of the stair foot (GYM through the
    # workshop, the rest through SF-B-BATH). The declaration below still carries the hall;
    # the flight is graded on its own sloped line, not the flat 6'-8" this room is held to.
    Room(uid="CBR406AAAA", tag="RM-B-STAIR", seed=pt(inch(186), ft(22)),
         occupancy=Occupancy.STAIR, floor_finish="sealed-concrete",
         exposed_services="owner accepts exposed services in the basement: three ERV branches and the sauna vent cross the hall in the open, painted out with the joists, the same as the gym next door"),
    # ** THE VOLUME UNDER THE ARRIVING FLIGHT IS PART OF THIS ROOM AGAIN (2026-09-05,
    # round three), AND IT IS NOT A `Room` OF ITS OWN. ** It was RM-B-UNDERSTAIR, a 17.5 sf
    # closet walled off at y=31'-0" by W-B-CL-N. That wall is gone: the storage runs the
    # length of the flight now and on under the landing deck, which is what it is for, and
    # W-B-WELL's north end is free.
    #
    # A second `Room` cannot survive that. With nothing closing the north side, both seeds
    # land in ONE face and RM-B-STAIR and RM-B-UNDERSTAIR each resolved the same 114.8 sf
    # polygon — the whole shaft counted twice, in every area, finish and load that walks
    # rooms, at 0 FAIL. So the closet gives up its label and keeps its use: D-B-CLOSET in
    # W-B-STR3 still opens it to the furnace room, ED-B-CLOSET-LT/-LT2 light it, and
    # W-B-STR3 keeps its Type X leaf.
    #
    # ** W-B-STR3 IS NOT RETYPED BACK. ** `code.R302_7_understair` now passes on "no
    # enclosed usable space" — the check keys on a room's occupancy and STAIR is not in
    # `_UNDER_STAIR_OCCUPANCIES` — but the reason for the gypsum did not go away with the
    # room label: this is still combustible framing under a flight with stored goods against
    # it. The code hook went quiet; the wall stays as built.
    #
    # ** DO NOT AUTHOR `ceiling`, AND DO NOT PUT A `Soffit` UNDER THE FLIGHT. ** The head
    # under the arriving flight rakes from 96.7" at y=25'-8" to 54.8" at y=30'-10" and lower
    # still under the landing, and no field in this engine can say that: `_clear_head`
    # (resolve/rooms.py) reads ceiling decks and ResolvedSoffits, and a raking stringer is
    # neither. An authored ceiling, or a flat soffit at 53", would be taken VERBATIM for the
    # WHOLE room and FAIL `code.R305_ceiling_height` for a stair the code measures at its
    # nosing line. The rake is recorded here, in prose, because that is the only place the
    # model can hold it.
    # The basement bath (2026-11-25): the band between the sauna and y=13'-0", entered from
    # the hall's south end. Shower, WC and lav on the south wet wall (plan/fixtures.py).
    # Sheet vinyl, as before: First Class Gatsby under a 4" rubber cove base. The ceiling
    # hangs like the sauna's, 5/8" MR board on a service cavity at 7'-0 1/16", so the runs
    # crossing the band stay above it.
    Room(uid="CBR407AAAA", tag="RM-B-BATH", seed=pt(inch(150), inch(125)),
         occupancy=Occupancy.BATHROOM, floor_finish="catlin-vinyl-gatsby",
         ceiling_lining=(
             Layer(name="gwb-ceil", material_ref="gwb-mr", thickness=inch(0.625),
                   function=LayerFunction.FINISH),
             Layer(name="service-cavity", material_ref="spf", thickness=inch(12.75),
                   function=LayerFunction.FURRING,
                   framing=FramingSpec(member="2x10", direction="horizontal",
                                       spacing=inch(16))),
         )),
    # The water heater's alcove, behind AO-B-WH-ALCOVE: its own face of the wall graph, so
    # its own Room, used as part of the workshop.
    Room(uid="5XK0HAS5CA", tag="RM-B-WH-ALCOVE", seed=pt(inch(143), inch(240)),
         occupancy=Occupancy.UTILITY, floor_finish="sealed-concrete"),
    Room(uid="CBR402AAAA", tag="RM-B-WORKSHOP", seed=pt(ft(8), ft(14)),
         occupancy=Occupancy.UTILITY, floor_finish="sealed-concrete"),
    # ** ROTATED ONTO THE GARDEN WALL 2026-09-05, THEN SHORTENED EAST THE SAME DAY ** — long
    # axis east-west, ~8'-3 7/8" x 8'-2" clear, entered from the gym. See the header for the
    # whole move and the node block for why the west wall stands on N-B-S1.
    # No wall_lining override: the liner is part of SAUNA_2X4 / SAUNA_LINER_INT_2X6_BRG /
    # SAUNA_LINER_ON_GARDEN_FRAMED /
    # SAUNA_LINER_ON_GARDEN_CURB. WET since the south wall got
    # the liner variant and the vapour control became continuous on all four faces; it stays
    # continuous through the east and south framing, which is why the curb under the south
    # run carries the liner too.
    # `design_temperature_f` stays unset on purpose — it defaults to the 70 F setpoint, which
    # is what HumidityClass prescribes: a Glaser walk screens the daily mean, not the löyly
    # peak, and authoring 175 F would turn four passing rules into noise.
    # Honest about the margin: `glazing_dew_point` clears WIN-B-SAUNA by 2.5 F at
    # centre-of-glass (55.5 F inner glass vs a 53.1 F dew point at 70 F / 55% RH), and the
    # frame runs 5-8 F colder than that, so the frame does condense at design. That is an
    # accepted condition over a sealed, drained slab in a room that dries between sessions,
    # not a hidden failure.
    # The floor is SEALED CONCRETE, not tile: the aisle dishes 1/8"/ft to FX-B-SAUNA-FD
    # (16'-4", 7'-0"; `drain_dishes`, decision #148). No shower since 2026-11-25 (it is the
    # bath's), so no tile either. `integrity.concrete_finish_needs_concrete_deck` is satisfied
    # by SL-B-FLOOR. Still BATHROOM occupancy while it has a floor drain.
    # Ceiling: the same shiplap-over-foil-polyiso liner as the walls (assemblies.py's
    # `_SAUNA_LINER`), restated rather than imported — the editable dialect cannot import
    # a sibling plan module. Keep the two in step by hand. The ceiling's boards are ASPEN
    # (`catlin-sauna-ceiling-shiplap`, 2026-10-18; willow from 2026-10-16).
    Room(uid="CBR403AAAA", tag="RM-B-SAUNA", seed=pt(ft(11), ft(5)),
         occupancy=Occupancy.BATHROOM, humidity_class=HumidityClass.WET,
         floor_finish="sealed-concrete",
         ceiling_lining=(
             Layer(name="shiplap-liner", material_ref="catlin-sauna-ceiling-shiplap", thickness=inch(0.75),
                   function=LayerFunction.FINISH),
             Layer(name="liner-furring", material_ref="struct-1-plywood", thickness=inch(0.5),
                   function=LayerFunction.FURRING,
                   framing=FramingSpec(member="1x4", direction="horizontal")),
             Layer(name="foil-polyiso", material_ref="polyiso-foil-thermax", thickness=inch(2.0),
                   function=LayerFunction.INSULATION,
                   control={ControlLayer.THERMAL, ControlLayer.VAPOR, ControlLayer.AIR}),
             # ** THE SERVICE CAVITY, NEW 2026-09-07, AND IT IS THE OUTERMOST LAYER FOR A
             # REASON. ** Runs cross this room overhead and the basement has NO plenum to
             # move them into: everywhere else on the storey the ceiling is 5/8" of gypsum
             # straight onto the joist soffit. Owner call: drop this ceiling rather than box
             # bulkheads into a 92 SF lined room. 10 1/4" of cavity (11 1/4" until 2026-11-01)
             # puts the finished face at 7'-0 1/16" — R305.1's 7'-0" for a room with a floor
             # drain (IRC R202). Over the foil (+87 5/16"): DU-B-ERV-R-SAUNA-SUP's leg to
             # REG-B-SUP3 and the bath's vent header over W-B-SA-N's plates.
             # Still a better sauna than 7'-10": a sauna stratifies, and the head space above
             # the top bench was heating nobody.
             #
             # It sits ABOVE the foil-polyiso, which is the whole point: the vapour and air
             # control stays continuous on the HOT side of the assembly and the services run
             # outboard of it. A cavity inboard of the foil would put ducts inside the sauna's
             # own vapour envelope.
             Layer(name="service-cavity", material_ref="spf", thickness=inch(10.25),
                   function=LayerFunction.FURRING,
                   framing=FramingSpec(member="2x10", direction="horizontal",
                                       spacing=inch(16))),
         )),
    Room(uid="CBR404AAAA", tag="RM-B-PLAY-N", seed=pt(ft(27), ft(27)),
         occupancy=Occupancy.MEDIA, floor_finish="catlin-theater-carpet"),
    # ** THE GYM'S SERVICES RUN EXPOSED, UNDER A CLOSED CEILING (2026-09-13; restated
    # 2026-10-30). ** The ceiling is not open: CEIL-RM-B-GYM-FS-M-EAST is 5/8" gwb on the
    # I-joists, the R302.13 membrane (`code.R302_13_floor_protection`), and it stays.
    # What the owner accepts is the pipe hung below it. mep.run_in_finished_volume reads the
    # sentence and PASSES with it quoted, and every run crossing this room is still measured
    # against the 6'-8" headroom line. SF-B-GYM was retired on the strength of it (see the
    # note below SOFFITS). `PR-B-COND` and `PR-B-HW-KITCH` cross overhead; since D3,
    # `DU-B-ERV-R-GYM` comes down the hall's x=17'-0" lane and enters on its last leg.
    #
    # Floor: 3/4" stall mats (2026-10-30). Rubber is echo-neutral; the acoustic fix is
    # absorber panels, researched and not authored (notes/gym_acoustics.md).
    Room(uid="CBR405AAAA", tag="RM-B-GYM", seed=pt(ft(27), ft(9)),
         occupancy=Occupancy.LIVING, floor_finish="catlin-rubber-stall-mat",
         exposed_services="owner accepts exposed services in the basement: the gym's painted gypsum ceiling stays, and the condensate line crossing it below the board is part of how the room looks"),
    # ESS closet: MECHANICAL like the room it's carved from, so it is not habitable space
    # (R327.3). The LID is two 5/8" Type X layers on 2x4 furring: furred down 3 1/2" so
    # PR-B-KITCH-DRAIN (95"-97 1/2" AFF along y=35'-0") runs above the lid, outside the box,
    # rather than as plastic pipe inside it. Face at 7'-8 13/16".
    Room(uid="CBR408AAAA", tag="RM-B-ESS", seed=pt(ft(8), ft(33, 6)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete", unpainted=True,
         ceiling_lining=(
             Layer(name="gwb-x-lid-a", material_ref="gwb-x", thickness=inch(0.625),
                   function=LayerFunction.FINISH),
             Layer(name="gwb-x-lid-b", material_ref="gwb-x", thickness=inch(0.625),
                   function=LayerFunction.FINISH),
             Layer(name="lid-furring", material_ref="spf", thickness=inch(3.5),
                   function=LayerFunction.FURRING,
                   framing=FramingSpec(member="2x4", direction="horizontal",
                                       spacing=inch(16))),
         )),
]

ALARMS = [
    # The storey's general smoke/CO head (R314.3, R315): on the hall ceiling at the foot of
    # ST-B2M, not in the theater, whose RC ceiling takes no box (owner, 2026-11-20).
    Alarm(uid="CBA701AAAA", tag="AL-B-COMBO", kind=AlarmKind.COMBO,
          type_ref="ED-T-ALARM-COMBO-KIDDE", room="RM-B-STAIR",
          circuit="CKT-LT-BACKUP", position=pt(inch(191.5), inch(302))),
    # 2021 IRC R328.7 (not the adopted 2018 book; `advisory.ess_detection`) wants the smoke
    # alarm; the heat alarm is the owner's standard (a cell fails as heat first). Both sit
    # INSIDE RM-B-ESS so they sense the cabinet, not the room outside the Type X.
    # CKT-LT-BACKUP so they survive an outage.
    Alarm(uid="CBA702AAAA", tag="AL-B-ESS-SMOKE", kind=AlarmKind.SMOKE,
          type_ref="ED-T-ALARM-SMOKE-KIDDE", room="RM-B-ESS",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CBA703AAAA", tag="AL-B-ESS-HEAT", kind=AlarmKind.HEAT,
          type_ref="ED-T-ALARM-HEAT-KIDDE", room="RM-B-ESS",
          circuit="CKT-LT-BACKUP"),
]

# No radiant floor in the basement. A heated floor under RM-B-SAUNA, which already runs at
# 190 °F, would be heat with nowhere to go and a stat with no honest place to read from.
# The electric radiant zones are all on the storeys above — main.py and second.py.

SLABS = [
    Slab(uid="CBS501AAAA", tag="SL-B-FLOOR", kind="pour",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(3.5), assembly="SLAB_FLOOR",
         # RM-B-SAUNA's aisle dishes to FX-B-SAUNA-FD at 1/8"/ft min, rim flush with the gym
         # (decision #148); the decks stand on flat floor west of x=179 1/4" (2026-11-25).
         # FT-B-S2 (south 11 3/4") and FT-B-CS (east 6 1/2") are cast first, flush and flat.
         drain_dishes=(DrainDish(drain_ref="FX-B-SAUNA-FD",
                                 outline=(pt(inch(179.25), inch(21)), pt(inch(203.5), inch(21)),
                                          pt(inch(203.5), inch(90.75)),
                                          pt(inch(179.25), inch(90.75))),
                                 rate_in_per_ft=0.125),),
         # FOAMULAR 1000, stated (free body §11j-§11k): the court's thrust crosses this slab to
         # the north footings; the sheet's 1/3 dead-load rule grades 0.885. Spelled out to
         # match params/foundations.SLAB_EDGE_BREAK (test_catlin_contract_m3 pins the pair).
         perimeter_thermal_break=SlabThermalBreak(
             material_ref="xps", thickness=inch(1.5), psi=100.0, modulus_psi=3700.0,
             sustained_load_fraction=0.3333,
             source="Owens Corning FOAMULAR NGX 1000, ASTM C578 Type V: 100 psi min (ASTM D1621), minimum compressive modulus 3,700 psi published (PDS 07 21 13.13.OCC); dead load <= 1/3 of rating; 1.5\" min thickness (Pub. 58307-Q, 06-2025)")),
]

# One thickened-slab pad under both stairwell posts (P-M-STRWELL-S/-SS, main.py), poured with
# SL-B-FLOOR on its capillary stone; the XPS stops at its edge and the ABU44 bolts cast into
# it. 16" x 24" x 8" from the slab top: projection (6 1/4" / 4 1/2"-6") within the thickness,
# 3,380 lb on 2.67 sf = 1,267 psf against GM's 2,000 (notes/stairwell_post_pad.md).
PADS = [
    Pad(uid="NAS34P2Q9F", tag="PD-B-WELL",
        outline=(pt(inch(160), inch(366.375)), pt(inch(176), inch(366.375)),
                 pt(inch(176), inch(390.375)), pt(inch(160), inch(390.375))),
        thickness=inch(8), bottom_elevation=inch(-117.4375), assembly="SLAB_THICKENED_PAD",
        cast_with=("SL-B-FLOOR",)),
]

FLOOR_OPENINGS = [
    # Shower recess is a finish-zone concern; the stair arrives via the slab above.
]

# RM-B-BATH's shower surround (2026-11-25; WP-B-SAUNA-SPLASH's tile retired with the sauna
# shower): the BATH2 pattern, a 1/4" solid-surface panel siliconed to the glass-mat backer
# on the pan's two closed sides, pan top (+2") to 80", a TK-105 strip capping it, painted
# board above to the 84" ceiling. W-B-SA-N runs east from x=9'-10" (pan at 2 1/4" along it),
# W-B-BT-W north from y=7'-11 3/8" (pan at 4 5/8").
PANELING = [
    WallPaneling(uid="DQNG5Z6J7P", tag="WP-B-BATH-SURR", room="RM-B-BATH",
                 material_ref="solid-surface-panel", offset=inch(2), height=inch(78),
                 replaces_wall_finish=True, thickness=inch(0.25),
                 spans=(PanelingSpan(wall_ref="W-B-SA-N", start=inch(2.25), length=ft(3)),
                        PanelingSpan(wall_ref="W-B-BT-W", start=inch(4.625), length=ft(3)))),
    WallPaneling(uid="HGZQ78TAEM", tag="WP-B-BATH-SURR-CAP", room="RM-B-BATH",
                 material_ref="swanstone-trim-strip", offset=inch(80), height=inch(3.875),
                 replaces_wall_finish=True, thickness=inch(0.25),
                 spans=(PanelingSpan(wall_ref="W-B-SA-N", start=inch(2.25), length=ft(3)),
                        PanelingSpan(wall_ref="W-B-BT-W", start=inch(4.625), length=ft(3)))),
]

# --- SF-B-BATH IS RETIRED (2026-11-25) --------------------------------------------------
# It boxed the drain, vent, hot line and play radial across the old stair-foot bath. That
# space is the water-heater alcove and the under-stair closet now, both exposed-service rooms.
# --- SF-B-HALL IS RETIRED (2026-09-13) ------------------------------------------------
#
# ** THE HALL INHERITED THE WORKSHOP'S SERVICE CEILING (2026-09-07). ** Two runs cross the
# x=13'-10 5/8"..18'-0" band at y~10'-6" on their way east: `DU-B-ERV-R-GYM` (3" round,
# el 7'-6", to the gym's register through W-B-CS3) and `PR-B-SAUNA-VENT` (2", falling from
# 7'-3 7/16" at the sauna riser). While that band was RM-B-WORKSHOP nothing graded them —
# UTILITY is in `EXPOSED_SERVICE_OCCUPANCIES` and a workshop ceiling is a service plane. The
# hall is RM-B-STAIR, which is not, and `mep.run_in_finished_volume` called both at 8.9" and
# 10.8" below the finished ceiling. Neither is reroutable: the gym register is east of the
# x=18' bearing line and the ERV is west of the hall, so ANY route between them crosses this
# hall, and the vent has to rise off the sauna's fixtures and fall west to the stack.
#
# So a bulkhead was built — x 170.0725"..212.615", y 123.8125"..133.4375", underside
# 85 15/16" (7'-1 15/16" clear). It answered the check and nothing else: the hall did not
# want a lower ceiling, the runs are 2" and 3", and the box was 28 SF of board hung to keep
# a workshop's habits out of a room that had stopped being a workshop.
#
# ** RM-B-STAIR SAYS IT INSTEAD. ** The owner accepts exposed services down here — the gym
# said so first — and this is the same service band four feet further west, in a circulation
# slot, not a room anybody sits in. `Room.exposed_services` on RM-B-STAIR (see ROOMS above)
# is the declaration, and it is evidence rather than a silence: the PASS quotes the sentence
# and names the runs it is carrying.
#
# ** IT RETIRES THE CEILING COMPARISON AND NOTHING ELSE. ** Both runs are measured again
# against the 6'-8" headroom line, and both clear it on their own numbers — the duct's bottom
# at 87 1/8" (7 1/8" of slack) and the vent's at 85 1/4" (5 1/4") where it is deepest, at the
# sauna wall. Neither moved. The band this hall's ceiling now shows is the same band it
# always carried; what changed is that the model says so.
#
# ** READ THE PASS'S RUN LIST, IT IS FOUR AND NOT TWO. ** `DU-B-ERV-R-BATH` and
# `PR-B-HW-SUITE` also dip under this ceiling, shallowly enough that the check's 3" intrusion
# allowance never reported them. A declaration is per ROOM, so they come with it: they are
# now named as the design instead of being tolerated silently, and they too are held to the
# headroom line. That is the trade a declaration makes and it is worth knowing before one is
# written on a room with a lot of ceiling.
SOFFITS = [
    # --- SF-B-GYM IS RETIRED (2026-09-13) ---------------------------------------------
    #
    # It existed for eleven days and for exactly one reason: DU-B-ERV-R-GYM at y=10'-6 5/8"
    # and PR-B-COND's collector leg at y=10'-11" were in RM-B-GYM's air, 8.4" and 10.6" under
    # its finished ceiling, and neither is reroutable. Boxing them out was the only answer the
    # engine would read. RM-B-GYM now SAYS its services run exposed — see the Room above — and
    # `mep.run_in_finished_volume` reads the sentence, so a 107 SF bulkhead built to satisfy a
    # check is 107 SF of board nobody wanted. The declaration is stronger evidence than the
    # box was: the box hid the decision, the sentence states it.
    #
    # What the retirement does NOT retire: both runs are still measured, against the 6'-8"
    # headroom line instead of the ceiling. The duct's bottom sits at 88 1/2" and the pipe's
    # at 89" at its deep west end, 8 1/2" and 9" clear of that line, so both pass on their
    # own numbers rather than on the declaration. Nothing moved to make that true.
    #
    # PR-B-COND's 2026-09-09 reroute STAYS as it is. Its head came up 2 5/8" to 7'-8" and its
    # gym leg went north onto y=10'-11" to sit beside the duct, and both of those were argued
    # from the deck soffit's own 1 5/8" usable band, not from this box — see
    # plan/mep_drainage.py. The soffit only ever covered what that reroute left exposed.
]

# The brick option's lintels and flashings (BM-B-BRICK-LINTEL-*, FL-B-BRICK-*) are in
# params/court_face.py.

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *SLABS, *PADS, *FLOOR_OPENINGS,
            *PANELING, *SOFFITS]

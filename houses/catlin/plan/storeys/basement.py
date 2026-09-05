# haus: editable
# Basement — cast concrete walkout box, 18' center grid, sauna, stair (WP3.1).
# The perimeter is 8" except the east wall, which is 12" because SL-M-DECK lands on it
# (see the WALLS header below). South wall is the walkout side facing the sunken garden.
# Perimeter walls align on the concrete exterior face so the 4" of exterior XPS stacks
# directly under the framed wall's 4" polyiso+EPS (#43 control-layer continuity) — which
# is also why thinning the pour moves only the INSIDE face.
from typehaus import (
    Alarm,
    AlarmKind,
    Arch,
    BarSpec,
    ControlLayer,
    Door,
    FloorOpening,
    FoundationWall,
    FramingSpec,
    HumidityClass,
    Layer,
    LayerFunction,
    Node,
    Occupancy,
    PanelingSpan,
    ReinforcementSpec,
    Room,
    RoughOpening,
    Slab,
    SlabThermalBreak,
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
# 7'-10". Both rooms only gain. The playroom (16'-6", between the centre line and the east
# wall, both 12") is unchanged, which is why the architect's dimension still holds.
#
# **The shaft is 7'-2 5/8" since 2026-08-24**, and the furnace room 9'-1 1/8": framing
# W-B-STR/W-B-STR3 (see WALLS) put the well's west face on x=10'-3 3/8" instead of
# 10'-6", and the mechanical room took the other 3 1/8" of what the pour used to occupy.
# Both flights widened to 3'-5 1/16" to keep the well full, so the code minimum is cleared
# by more than it was, not less.
# Note that the model does not report this: `clear_face` is inset from the wall AXIS
# network (resolve/rooms.py), and the axis did not move.
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
#     x 8'-10"..18'-0" by y 0'-0"..9'-5" on the node lines — an 8'-3 15/16" x 8'-3 11/16"
#     clear box against the 8'-1" x 12'-7" it was. It keeps WIN-B-SAUNA and is entered FROM
#     THE GYM through framed W-B-CS, a short walk from D-B-PATIO and the sunken garden,
#     which is what the brief asks the room for. (The rotation drew it x 4'-8"..18'-0", a
#     12'-2" box straddling two substrates; ROUND TWO the same afternoon pulled the west
#     wall onto N-B-S1 — see the node block below.)
#   * **The bathroom rotated** to run north-south along the framed stair wall
#     (W-B-STR3B/W-B-STR2), 3'-3 15/16" x 7'-1 1/4" clear, with its door on a new east wall.
#   * **A hall** runs west of W-B-CN2 from the stair foot south to the y=18' line —
#     3'-3 15/16" clear, part of RM-B-STAIR's own loop — and crosses that line through
#     O-B-HALL, a cased opening in W-B-CW2B, into the workshop.
#
# ACCEPTED CONSEQUENCE, stated rather than discovered: the playroom is reached only via the
# gym (stair -> hall -> workshop -> gym -> D-B-PLAY), and the workshop is the through-route
# from the stair to the gym. Nothing on the x=18' bearing grid moved and no concrete wall
# moved; W-B-CS2, W-B-CN and W-B-CN2 stay pours because they carry SL-M-DECK.
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
    Node(uid="CBN002AAAA", tag="N-B-S1", position=pt(ft(8, 10), ft(0))),
    Node(uid="CBN003AAAA", tag="N-B-S2", position=pt(ft(18), ft(0))),
    # x=28'-0" is the excavation edge (params/sunken_garden's ``_x_ax_e``), where the
    # sunken garden ends and grade comes back up to the -2'-10" site plane. It splits the
    # south wall at the one place on that line where the backfill condition changes, so
    # each segment can author the fill it actually retains instead of one wall carrying
    # two conditions. It is also W-B-BRICK's east end, which was already dimensioned to
    # this x.
    Node(uid="NW1W09NAD2", tag="N-B-S3", position=pt(ft(28), ft(0))),
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
    Node(uid="QEDBCR7NYR", tag="N-B-S1F", position=pt(ft(8, 10), ft(0)), open_end=True),
    Node(uid="PGQVHV2VRH", tag="N-B-S2F", position=pt(ft(18), ft(0))),
    Node(uid="Z44TJSW6JJ", tag="N-B-S3F", position=pt(ft(28), ft(0)), open_end=True),
    Node(uid="CBN004AAAA", tag="N-B-SE", position=pt(ft(36), ft(0))),
    Node(uid="CBN005AAAA", tag="N-B-E1", position=pt(ft(36), ft(18))),
    Node(uid="CBN006AAAA", tag="N-B-NE", position=pt(ft(36), ft(36))),
    Node(uid="CBN007AAAA", tag="N-B-N1", position=pt(ft(18), ft(36))),
    Node(uid="CBN008AAAA", tag="N-B-N2", position=pt(ft(10), ft(36))),
    Node(uid="CBN009AAAA", tag="N-B-NW", position=pt(ft(0), ft(36))),
    Node(uid="CBN010AAAA", tag="N-B-W1", position=pt(ft(0), ft(18))),
    # Interior grid + stair + sauna
    Node(uid="CBN011AAAA", tag="N-B-C", position=pt(ft(18), ft(18))),
    Node(uid="CBN012AAAA", tag="N-B-C1", position=pt(ft(18), ft(13, 10))),
    # The stair shaft runs the full north-row depth and lands on the center wall, so its
    # west wall tees into it rather than dying in the middle of the furnace room.
    Node(uid="CBN013AAAA", tag="N-B-STR", position=pt(ft(10), ft(18))),
    # Sauna box, rotated onto the south (garden) wall 2026-09-05: long axis east-west,
    # y 0'-0"..9'-5", entered from the gym instead of the workshop. N-B-SA1 (the old NW
    # corner at 8'-10", 13'-10") is gone with the north-south box.
    #
    # **Shortened east to x=8'-10" on 2026-09-05 (round two).** The west wall used to stand
    # at 4'-8", which put the sauna's south face across two substrates — the buried 8" pour
    # and the garden curb — and forced W-B-S1B, a 3'-10" third segment carrying a liner
    # variant of the pour whose inboard face did not line up with the curb's. Landing the
    # west wall on N-B-S1 instead puts the whole south face on W-B-S2, deletes W-B-S1B and
    # SAUNA_LINER_ON_BASEMENT_8 with it, returns FT-B-S1 to one unsplit strip, and hands the
    # workshop's west bay the four feet it gives up. The room is ~8'-3 7/8" x 8'-2" clear,
    # which is what EQ-T-SAUNA-HEATER's 9 kW was always sized for (see electrical.py).
    Node(uid="XTVNH0A54T", tag="N-B-SA-NW", position=pt(ft(8, 10), ft(9, 5))),
    Node(uid="HN7GXN3ZM8", tag="N-B-SA-NE", position=pt(ft(18), ft(9, 5))),
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
    # ** BOTH SLID WEST TO x=13'-10 11/16" ON 2026-09-05 (round two). ** x=14'-0" missed the
    # stair well's partition centreline by 1 5/16": `resolve/stairs/common.py` reserves
    # 4 1/2" for that partition at x 13'-8 7/16"..14'-0 15/16" and builds nothing in it, so
    # the bathroom's east wall and the flight divider were two nearly-collinear planes an
    # inch and a third apart — the kind of jog that reads as a mistake and is not one on any
    # drawing. `inch(166.6875)` IS that centreline, so W-B-BA-E, the new W-B-WELL above it
    # and W-B-CL-N's east end are one continuous plane from y=18' to y=31' now. Everything
    # that references these two nodes rides along and needed no edit; the wet-wall risers,
    # which are absolute coordinates and not node references, did (mep_venting.py,
    # mep_supply.py, mep_supply_devices.py).
    Node(uid="ZHKG5KWP08", tag="N-B-BA-NE", position=pt(inch(166.6875), ft(25, 6))),
    Node(uid="R1KFP0S4NQ", tag="N-B-BA-SE", position=pt(inch(166.6875), ft(18))),
    # W-B-CW's east end. The split here is real (W-B-CW3 carries a different assembly from
    # W-B-CW) though the room it was minted for has since moved off this corner; uid
    # unchanged.
    Node(uid="CBN017AAAA", tag="N-B-CW-E", position=pt(ft(6, 9), ft(18))),
    # ESS closet, NE corner of the furnace room. Two sides come free here — W-B-N3 on the
    # north (concrete, inner face y=35'-4") and W-B-STR on the east (inner face
    # x=9'-8 1/2", the framed wall's Type X leaf) — so it is two framed partitions, not
    # four. x=6'-0" and y=31'-0" leave 3'-6 1/8" x 4'-1 5/8" clear, more than the 2'-8 1/4"
    # cabinet it replaces, and clear of everything already on this side: SP-B-N3-HYD
    # (x=5'-0" through the north wall) and ED-B-SUMP-RC (x=4'-6"). SP-B-STR-CD-DATA was the
    # third of those; it went with the pour (electrical.py).
    #
    # **x=6'-0" is not a round number chosen for tidiness.** Neither concrete side of this
    # corner was split before, so both had to be, and a basement split that does not line up
    # with the storey above puts one wall over two. N-M-MECH3 already splits the main
    # storey's north wall line at exactly x=6'-0" (RM-M-MECH's shaft closet), so splitting
    # W-B-N3 there makes W-M-N3 sit over W-B-N3 and W-M-N3B over W-B-N4, one to one. The
    # east wall has no such gift — W-M-STRW runs y 26'-4"..36'-0" straight across W-B-STR's
    # y=31'-0" split — and that is called out on W-B-STR below.
    #
    # The corner is only available because EQ-B-WH left it — see plan/mep_hvac.py.
    Node(uid="CBN018AAAA", tag="N-B-ESS-N", position=pt(ft(6), ft(36))),
    Node(uid="BT88F385N4", tag="N-B-ESS-SW", position=pt(ft(6), ft(31))),
    Node(uid="GXJ9S72CKH", tag="N-B-ESS-SE", position=pt(ft(10), ft(31))),
    # ** RM-B-UNDERSTAIR's north-east corner, new 2026-09-05. ** x is N-B-BA-NE's — the
    # stair well's partition centreline — and y=31'-0" is N-B-ESS-SE's, so the closet's north
    # wall lands exactly on the existing W-B-STR3/W-B-STR split and needs no second node on
    # the x=10' line. Both new walls (W-B-WELL, W-B-CL-N) meet here.
    Node(uid="SQZSP1P9DC", tag="N-B-CL-NE", position=pt(inch(166.6875), ft(31))),
    # Glazed-brick veneer over the exposed south wall (W-B-BRICK): a freestanding wythe off
    # the concrete, both ends ``open_end`` like the sunken garden's N-SG-NW/NE (not part of
    # any wall loop). x runs only as far as the excavation in front of it: N-B-S1's x (8'-10")
    # to 28'-0" (params/sunken_garden.py's ``_x_ax_e``, where grade comes back up).
    # y is NOT 0'-0": the south walls' node line is the concrete face, and the south stack
    # carries 4.05" outboard of it (0.05" damp-proofing + 2x 2" XPS) — a tail that is
    # independent of the pour thickness; the veneer stands off that finished face, hence
    # the -4.55".
    #
    # The stand-off is 4.05" — the south stack's finished face, bare XPS. It was 4.55" while
    # the south wall carried a 1/2" parge, because the wall aligns on face("air-gap-int")
    # and that face sat on the parge. **When the parge was deleted the node did not follow
    # it, and that left a 0.5" void between the XPS at -4.05" and the veneer's air-gap layer
    # at -4.55" which NO layer described** — the built cavity was 1-1/2" while the model said
    # 1". Fixed 2026-09-04 by moving the node onto the foam and growing `air-gap` to 1-1/2"
    # to suit (plan/assemblies.py BASEMENT_BRICK_VENEER).
    #
    # ** THE VENEER ITSELF DOES NOT MOVE, WHICH IS THE WHOLE POINT OF FIXING IT THIS WAY. **
    # The two edits cancel at the air gap's outboard face: the wythe stays at -5.55..-9.175",
    # so the two arched reveals, the veneer's own footing and every garage-relative literal
    # downstream are all untouched. Only the 0.5" of nothing becomes something.
    Node(uid="CBN019AAAA", tag="N-B-BRICK-W", position=pt(ft(8, 10), inch(-4.05)),
         open_end=True),
    # ** 27'-6", NOT 28'-0", SINCE 2026-09-05. ** 28'-0" is W-SG-E1's AXIS, and while the
    # wythe stood at y -5.55..-9.175" that was harmless: it ended north of the retaining
    # wall's north end (-10") and the two never met in plan. Moving the veneer south to
    # -10.05..-13.675" for its 6" cavity walked its east 6" straight INSIDE that wall —
    # 4.25 SF of brick with concrete already in it, billed and drawn and unbuildable, at
    # 0 FAIL (nothing grades masonry against concrete; `structural.concrete_interference`
    # only sees pours). 27'-6" is `_x_in_e`, the court's own clear face, so the wythe now
    # dies against the retaining wall instead of into it.
    #
    # The reveals do NOT move: they are positioned `from_node("N-B-BRICK-W", ...)`, measured
    # from the WEST node, so shortening the east end leaves every station where it was.
    # `integrity.reveal_concentric` is what proves that, and it still passes.
    Node(uid="CBN020AAAA", tag="N-B-BRICK-E", position=pt(ft(27, 6), inch(-4.05)),
         open_end=True),
]

# The 8" perimeter's vertical steel, structured — the same `#5 @ 41" o.c.` the string
# beside it states, and IRC Table R404.1.2(8) is still where it comes from. Both spellings
# are kept: the string prints on the drawing, the struct is what `stem_flexure` grades and
# what `takeoff/reinforcement.py` bills, and `integrity.reinforcement_spec_agrees` raises an
# ERROR if they ever drift apart.
#
# ** VERTICAL ONLY, AND THAT IS A 1:1 MIGRATION RATHER THAN A DESIGN. ** These walls have
# horizontal temperature-and-shrinkage steel in reality and this house has never stated any,
# so none is invented here: adding a schedule nobody authored would put tonnage into the
# estimate on my judgement instead of on a decision. The gap is named in
# `notes/rebar_backout.md`, where it is part of why the billed tonnage falls short of the
# allowance register's ~5 tons.
_B8_STEEL = ReinforcementSpec(
    bars=(BarSpec(role="vertical", bar=5, spacing=inch(41.0)),),
    cover=inch(2.0),
    source="IRC Table R404.1.2(8); verbatim from the vertical_reinforcement string beside it",
)

WALLS = [
    # Perimeter foundation walls (8" or 12" + exterior XPS), CCW from SW corner.
    #
    # `lateral_support="top_and_bottom"` is the precondition for the prescriptive path, not a
    # detail: SL-B bears against the inside face at the bottom and FS-MAIN's diaphragm ties
    # the top, so IRC Table R404.1.2(8) applies (its footnote g presumes exactly this) rather
    # than R404.1.1 sending a wall retaining more than 48" to an engineered design. Stated on
    # each wall because the check refuses to assume it — assuming bracing is the unsafe
    # direction. (Horizontal steel is a separate table, R404.1.2(1) — one #4 within 12" of
    # the top and one at third points above 8' — not screened here.)
    #
    # **The row, spelled out.** GM soil is 45 psf/ft (mn-2024 profile). The wall runs
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
    # the 12" segments carry SL-M-DECK on 12" because they always did, and an 8" wall would
    # carry it just as well.
    #
    # So the three that stay 12" stay for reasons that are no longer about bearing width,
    # and each is worth stating.
    #
    #   W-B-E1/E2 — the east perimeter. SL-M-DECK is a 414 SF cast slab and its east edge
    #     lands here; 12" is not needed for the seat, but this is the one perimeter run with
    #     a cast deck on it and the extra 4" is ~2.2 cy against re-detailing the east edge of
    #     a pour that is already the model's fussiest element. Left as built, deliberately —
    #     and it is now the only place in the house where wall thickness is a judgement
    #     rather than a derivation, so it is the first candidate the next time this line is
    #     opened.
    #   W-B-CS2, W-B-CN2, W-B-CN — the centre line under the cast band, same reading.
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
    # The 8" walls also sit better than the 12" ones did: FT-B-* is a 20" strip on
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
    # garden is excavated from x=8'-10" to x=28'-0" with its floor flush with the basement
    # slab, so two of the four segments retain nothing at all.
    #
    #   W-B-S1   0'-0" .. 8'-10"   6'-4"  genuinely buried, west of the excavation
    #   W-B-S2   8'-10" .. 18'-0"  0      entirely inside the court
    #   W-B-S3   18'-0" .. 28'-0"  0      entirely inside the court
    #   W-B-S4   28'-0" .. 36'-0"  6'-4"  buried again, east of the excavation
    #
    # 6'-4" is the measured 6.29' rounded UP to the nearest inch, the same direction
    # footnote f rounds the table row. It changes no grade: 6.3' still lands on the 7' row
    # and the two buried segments keep ``#5 @ 41" o.c.`` The two zero-fill segments drop
    # the bar with the load — see W-B-S2 below.
    #
    # **W-B-S1 and W-B-S4 carry CATLIN_BASEMENT_8**, not CATLIN_BASEMENT_8_GARDEN. That is
    # the same fill table read a second way: these two segments are the only south run whose
    # exposure is an ordinary grade line — 6'-4" of backfill with 2'-2 9/16" of wall standing
    # out of it — which is exactly the condition _PROTECTION_PANEL's GRADE-banded extent was
    # written for, and nothing like the nine feet of open court in between. So they buy about
    # 37 SF of panel over 16.83 LF instead of 106 SF of parge over a face that is under the
    # dirt. The court segments are not banded at all; they are bare XPS in a brick cavity.
    # See plan/assemblies.py for the whole stucco retirement.

    FoundationWall(uid="CBW101AAAA", tag="W-B-S1", start_node="N-B-SW",
                   end_node="N-B-S1", assembly="CATLIN_BASEMENT_8",
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
    # `structural.frost_depth`, CN-M-HD-BALC-W/E's STHD embedments and W-B-BRICK's
    # dimensions all still name a piece of concrete on a footing, and none of them moved.
    #
    # **Why the curb is kept and why it is 7 1/4".** The sunken garden is a court whose
    # floor is FLUSH with the basement slab (both -9'-1 7/16") with no way out but a drain;
    # heavy rain can stand in it. A concrete curb runs under the whole framed run so standing water
    # reaches concrete and not a bottom plate. 7 1/4" is the actual width of a 2x8, so the
    # curb is one board deep and the framed plate lands on it flat. It is also exactly
    # D-B-PATIO's old raised threshold — the door used to carry `sill_height=inch(7)` off
    # this same base — so the curb top IS the threshold now and the door's sill_height
    # goes to zero rather than to 7 1/4" (see D-B-PATIO in OPENINGS).
    FoundationWall(uid="CBW102AAAA", tag="W-B-S2", start_node="N-B-S1",
                   end_node="N-B-S2", assembly="SAUNA_LINER_ON_GARDEN_CURB",
                   interior_room="RM-B-SAUNA",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(0),
                   top_elevation=inch(-102.1875), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW103AAAA", tag="W-B-S3", start_node="N-B-S2",
                   end_node="N-B-S3", assembly="CATLIN_GARDEN_CURB_6",
                   interior_room="RM-B-GYM",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(0),
                   top_elevation=inch(-102.1875), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom"),
    # The framed run itself: base on the curb top (-102 3/16"), 88 3/4" to the same
    # -13 7/16" bearing seat every other wall in this basement stops on. `base_elevation`
    # is what lets a framed wall stand on something inside its own storey; `top` stays a
    # height measured from it, so the studs are 88 3/4" less the plates — about 7'-0 1/4",
    # not the 8'-0" they would be off the slab.
    #
    # `face("sheathing-ext")` is the deliberate mirror of the pour's `face("concrete-ext")`:
    # it pins the sheathing's outboard face on the node line, so the damp-proofing and the 4"
    # of XPS continue on exactly the plane they occupy on W-B-S1 and W-B-S4 either side, and
    # W-B-BRICK's stand-off and its two arched reveals do not move (see N-B-BRICK-W
    # above).
    # The tie hardware does change in reality — corrugated ties into framing instead of
    # anchors into concrete — which is ordinary for veneer over wood, and is said out loud
    # here because the model cannot say it.
    #
    # `interior_room` is authored on both rather than left to the storey's outward sign:
    # there are two wall edges on each of these node pairs now (the curb and the framing),
    # and an asymmetric stack should not depend on how the loop happens to wind.
    Wall(uid="3BF9ZDQPT1", tag="W-B-S2-FR", start_node="N-B-S1F", end_node="N-B-S2F",
         assembly="SAUNA_LINER_ON_GARDEN_FRAMED",
         alignment=face("sheathing-ext"),
         interior_room="RM-B-SAUNA",
         base_elevation=inch(-102.1875), top=inch(88.75),
         structural_role=StructuralRole.BEARING),
    Wall(uid="Z4NRTGEDY5", tag="W-B-S3-FR", start_node="N-B-S2F", end_node="N-B-S3F",
         assembly="CATLIN_GARDEN_FRAMED_2X6",
         alignment=face("sheathing-ext"),
         interior_room="RM-B-GYM",
         base_elevation=inch(-102.1875), top=inch(88.75),
         structural_role=StructuralRole.BEARING),
    # The east 8'-0" of the old W-B-S3, split off at the excavation edge.
    # Buried like W-B-S1, so it keeps the 7'-row bar — and it must join
    # ``params/foundations._FROST_FORMED`` with it, or FT-B-S4 loses the insulated
    # FOOTING_FPSF_20 form the garden floor's low adjacent grade is the reason for.
    FoundationWall(uid="72HXFS8M11", tag="W-B-S4", start_node="N-B-S3",
                   end_node="N-B-SE", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(6, 4),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW104AAAA", tag="W-B-E1", start_node="N-B-SE",
                   end_node="N-B-E1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW105AAAA", tag="W-B-E2", start_node="N-B-E1",
                   end_node="N-B-NE", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW106AAAA", tag="W-B-N1", start_node="N-B-NE",
                   end_node="N-B-N1", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW107AAAA", tag="W-B-N2", start_node="N-B-N1",
                   end_node="N-B-N2", assembly="CATLIN_BASEMENT_8",
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
                   end_node="N-B-ESS-N", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="HEX0ZDQZEN", tag="W-B-N4", start_node="N-B-ESS-N",
                   end_node="N-B-NW", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW109AAAA", tag="W-B-W1", start_node="N-B-NW",
                   end_node="N-B-W1", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.',
                   reinforcement=_B8_STEEL),
    FoundationWall(uid="CBW110AAAA", tag="W-B-W2", start_node="N-B-W1",
                   end_node="N-B-SW", assembly="CATLIN_BASEMENT_8",
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
    # **One thing this buys, and it is on the record rather than hidden:**
    # `integrity.junction_fallback` reports N-B-C1 UNKNOWN — the framed run on the x=18'
    # line is spf and W-B-CS2, collinear with it, is still 12" concrete under the cast band,
    # so the junction's THROUGH pair is two different bearing materials and the solver has
    # no interface rule for that. (Since the 2026-09-05 rotation the framed wall AT that
    # node is W-B-CS3, not this one — same finding, same count, one assembly
    # along.) It is a real detail and not a modelling
    # artefact: a stud wall landing in line against the end of a 12" pour wants a bearing
    # plate and dowels drawn, which is exactly what the UNKNOWN is asking for. The house
    # answered the same finding at N-B-CW-E by running ONE wall type down the whole line;
    # that answer is not available here, because W-B-CS2 carries SL-M-DECK and stays a pour.
    Wall(uid="CBW111AAAA", tag="W-B-CS", start_node="N-B-SA-NE",
         end_node="N-B-S2", assembly="SAUNA_LINER_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         interior_room="RM-B-SAUNA",
         structural_role=StructuralRole.BEARING),
    # The x=18' line north of the rotated sauna, y 9'-5"..13'-10": the same 2x6 bearing
    # wall with no liner on it, because the room behind it is the workshop now. It is the
    # segment D-B-GYM moved onto — a framed host in place of the 12" pour it used to be
    # formed through — which is the whole point of the rotation.
    Wall(uid="NJ21M7MF6R", tag="W-B-CS3", start_node="N-B-C1",
         end_node="N-B-SA-NE", assembly="CATLIN_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         structural_role=StructuralRole.BEARING),
    FoundationWall(uid="CBW112AAAA", tag="W-B-CS2", start_node="N-B-C1",
                   end_node="N-B-C", assembly="FOUNDATION_WALL_12_INT", unbalanced_fill=ft(0),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375)),
    # Split at N-B-BA-E so the bathroom's north partition tees onto a shared
    # node — else `integrity.wall_loop_open` reads it as a free end. W-B-CN keeps the tag,
    # uid, and the north 14'-2 5/8" that W-M-C5 stacks on, so the bearing stack is untouched.
    FoundationWall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-BA-E",
                   end_node="N-B-N1", assembly="FOUNDATION_WALL_12_INT", unbalanced_fill=ft(0),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375)),
    FoundationWall(uid="CBW121AAAA", tag="W-B-CN2", start_node="N-B-C",
                   end_node="N-B-BA-E", assembly="FOUNDATION_WALL_12_INT", unbalanced_fill=ft(0),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375)),
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
    # W-B-CW is the furnace room's south wall and carries the 4" building drain, so it takes
    # the wet-wall 2x6 rather than a 2x4.
    Wall(uid="CBW114AAAA", tag="W-B-CW", start_node="N-B-W1",
         end_node="N-B-CW-E", assembly="INT_2X6_PLUMBING", top=ft(8)),
    # This was the ESS closet's south wall until the closet moved to the NE corner; it is
    # now simply W-B-CW continued: same INT_2X6_PLUMBING, one wall type down the whole
    # furnace-room south line.
    #
    # What forced it was `integrity.junction_fallback`. A steel stud and a wood stud are two
    # different bearing materials, so N-B-CW-E (this stub against W-B-CW) and N-B-STR (this
    # stub, W-B-CW2 and W-B-STR2) both resolved as mixed-assembly junctions the solver has no
    # interface rule for — three UNKNOWNs bought by a leftover. The stub widens 2" and the
    # furnace room's south face moves an inch north over this 3'-3" run; that is the price,
    # and it was named here before it was paid.
    Wall(uid="CBW123AAAA", tag="W-B-CW3", start_node="N-B-CW-E",
         end_node="N-B-STR", assembly="INT_2X6_PLUMBING", top=ft(8)),
    # Nothing runs in this one and nothing bears on it — a plain 2x4 partition. Keep the
    # tag: W-M-CLN and W-M-CLN2 name it in `stacks_on`.
    Wall(uid="CBW119AAAA", tag="W-B-CW2", start_node="N-B-STR",
         end_node="N-B-BA-SE", assembly="INT_2X4_PARTITION", top=ft(8)),
    # The last 4'-1 5/16" of the y=18' line (it was 4'-0" until W-B-BA-E slid west onto the
    # well-partition line on 2026-09-05), and the wall the new hall crosses to reach the
    # workshop: O-B-HALL is a cased opening (a bare RoughOpening) through it. The wall has
    # to EXIST rather than be left as a gap — delete it and the workshop and the stair
    # loops merge into one room and every room-bounded check downstream reads the wrong
    # space. W-M-CLN2 stacks on it.
    Wall(uid="SPDGAH1TTX", tag="W-B-CW2B", start_node="N-B-BA-SE",
         end_node="N-B-C", assembly="INT_2X4_PARTITION", top=ft(8)),
    # The playroom's south wall, 18'-0" of it, and the one that keeps D-B-PLAY (the 5'-0"
    # glazed double). Staggered studs: it is the long wall between the playroom and the gym,
    # and it also runs under the concrete band, so it wants the sound break.
    Wall(uid="CBW115AAAA", tag="W-B-CE", start_node="N-B-C",
         end_node="N-B-E1", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8)),
    # Stair shaft's west wall — 2x6 bearing studs on x=10', full north-row depth
    # (reference: "Stairway 7' x 16' 6 1/2""). Framed, not poured: it
    # holds back no earth (`unbalanced_fill` was ft(0) the whole time it was concrete), and
    # what it actually does is carry FS-M-MECH/FS-M-STAIR's short joists — the stubs the
    # stair well leaves — and stack W-M-STRW/W-M-STRW2 above. That is a stud-wall job on a
    # footing, not a pour: ~9.8 cy of concrete out, and RM-B-FURNACE gains 3 1/8".
    # Split at N-B-BA-W: W-B-STR keeps tag/uid and the north 14'-2 5/8" that
    # W-M-STRW/W-M-STRW2 stack on; W-B-STR2 is the 3'-9 3/8" stub alongside the bathroom,
    # carrying its three ceiling-level service crossings (plan/mep.py's WALL_SLEEVES).
    # Split again at N-B-ESS-SE (y=31'-0"), for the ESS closet's south
    # partition, exactly as it was split at N-B-BA-W for the bathroom. **Unlike the north
    # wall's split this one does NOT line up with the storey above**: W-M-STRW runs
    # y 26'-6"..36'-0" and crosses from W-B-STR onto W-B-STR3 halfway along. It keeps
    # naming W-B-STR — `resolve/stacking.py` picks it as the sole candidate on both basement
    # segments, since it is the only main-storey wall whose axis overlaps either by the 2'
    # minimum. W-M-STRW2 (trimmed to 5 3/8", south of the split, nominally
    # `stacks_on="W-B-STR3"`) never actually resolves a stack edge either way — at 5 3/8" it
    # cannot clear that 2' overlap test as upper or lower — so its `stacks_on` is honest
    # geometry, not a load path; its real job is FO-S-STAIR's bearing coverage (second.py).
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
    # x=10'-3 3/8"). `_axis_offset_from_interior` measures from the interior face, so
    # pinning the STUD layer's outboard face 2 5/8" east of the node puts the studs at
    # 9'-9 1/8"..10'-2 5/8" on both segments — the identical band W-M-STRW occupies above —
    # no matter what is added on the west, which is why both assemblies below can use the
    # same offset. That leaves 2 7/8" of structure west of the axis and 2 5/8" east, and a
    # full layer footprint reaching exactly x=10'-3 3/8", where the opening edge now stops.
    # The shaft goes 7'-0" -> 7'-2 5/8"; the thickness that came off goes to the mechanical
    # room. Set `interior_room` explicitly on both — do not let the component winding
    # decide which side layer 0 faces.
    #
    # W-B-STR is also RM-B-ESS's west enclosure, so it takes the Type X variant:
    # `advisory.ess_enclosure` passed here on the mass of 12" of concrete and now passes on
    # a 5/8" Type X leaf on the closet face. W-B-N3 (the closet's north side) is still
    # concrete and still passes on mass.
    Wall(uid="CBW116AAAA", tag="W-B-STR", start_node="N-B-N2",
         end_node="N-B-ESS-SE", assembly="CATLIN_STAIRWALL_INT_2X6_BRG_TYPEX", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         interior_room="RM-B-ESS",
         structural_role=StructuralRole.BEARING),
    # The same wall south of the closet: no Type X leaf, RM-B-FURNACE on the west face.
    # FT-B-STR / FT-B-STR3 and their beddings need no edit — `Footing.under` takes any wall
    # tag and `_resolve_footing` sets z1 from the wall's own z0, which for a framed wall on
    # the basement storey is the same -109 7/16" the pour authored (params/foundations.py
    # says so in as many words).
    # ** RETYPED 2026-09-05 to the UNDERSTAIR variant. ** Same uid, same alignment, same
    # interior_room, same BEARING role — only the finish leaf changes, from 3/4" stair
    # plywood to 5/8" Type X, because this whole run is RM-B-UNDERSTAIR's west wall now and
    # R302.7 wants gypsum on the enclosed side. See plan/assemblies.py for what it costs.
    Wall(uid="1H4KR79N9M", tag="W-B-STR3", start_node="N-B-ESS-SE",
         end_node="N-B-BA-NW", assembly="CATLIN_STAIRWALL_INT_2X6_BRG_UNDERSTAIR", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         interior_room="RM-B-FURNACE",
         structural_role=StructuralRole.BEARING),
    # Split again at N-B-BA-NW (y=25'-6") when the bathroom rotated: the same wall, same
    # assembly, same alignment, same bearing role, carrying the 3'-8 5/8" between the
    # bathroom's north partition and N-B-BA-W. The plywood face lands on the bathroom over
    # this stretch, which is what W-B-STR2's note below already says about its own run.
    Wall(uid="VZPMT59XVQ", tag="W-B-STR3B", start_node="N-B-BA-NW",
         end_node="N-B-BA-W", assembly="CATLIN_STAIRWALL_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
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
    # mixed-assembly junctions with no interface rule. The 3/4" plywood face now lands on the
    # bathroom rather than the stair, and the bathroom's west face moves 1" east; its three
    # ceiling-level crossings (vent, hot, cold) are bored, as they have been since the pour
    # went away.
    Wall(uid="CBW122AAAA", tag="W-B-STR2", start_node="N-B-BA-W",
         end_node="N-B-STR", assembly="CATLIN_STAIRWALL_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         interior_room="RM-B-FURNACE"),
    # Sauna partitions — SAUNA_2X4 carries the hot-side liner (T&G/furring/foil-faced
    # polyiso) as part of the wall type, not a room finish override; the east wall (the
    # x=18' bearing line) takes it via SAUNA_LINER_INT_2X6_BRG. Both are interior walls, so
    # `interior_room` is what names which side the liner lands on.
    Wall(uid="CBW117AAAA", tag="W-B-SA-W", start_node="N-B-S1",
         end_node="N-B-SA-NW", assembly="SAUNA_2X4", top=ft(7, 6),
         interior_room="RM-B-SAUNA"),
    # The sauna's cold north face, x 8'-10"..18'-0" at y=9'-5" since the shrink. It used
    # to sit on y=13'-10", where W-M-BDN1 at y=13'-4" fell inside `resolve/platform.py`'s
    # same-wall-line tolerance and topped it out at the deck instead of its authored 7'-6";
    # that partition moved to 13'-0" then and this wall is now four feet clear of it.
    Wall(uid="CBW118AAAA", tag="W-B-SA-N", start_node="N-B-SA-NW",
         end_node="N-B-SA-NE", assembly="SAUNA_2X4", top=ft(7, 6),
         interior_room="RM-B-SAUNA"),
    # ** RETYPED AND RE-NODED 2026-09-05, AND IT IS DRY NOW. ** This was the stair-foot
    # bathroom's only framed wall and it carried the whole room's plumbing — it was
    # INT_2X6_STAGGERED_PLUMBING because it was the one stud cavity a room otherwise walled
    # in concrete had. The rotation gave the room a real east wall (W-B-BA-E below), the
    # vent and both supplies went with it, and what is left here is the bathroom's north
    # end: a plain 2x4 partition running x 10'-0"..13'-10 11/16" at y=25'-6" — 1 5/16"
    # shorter since W-B-BA-E slid onto the well-partition line.
    # Top=8'-0" is the bearing seat, like every other partition in this basement.
    Wall(uid="CBW120AAAA", tag="W-B-BA-N", start_node="N-B-BA-NW",
         end_node="N-B-BA-NE", assembly="INT_2X4_PARTITION", top=ft(8),
         interior_room="RM-B-BATH"),
    # The rotated bathroom's one WET wall, and the only stud cavity it has: the lavatory's
    # and WC's shared 1 1/2" vent rises here before turning west (PR-B-BATH-VENT), and both
    # fixtures name it in `wall_ref` — venting reads that, not geometry.
    # `advisory.wet_wall_depth` needs 5 1/2" and this is where it comes from, which is why
    # W-B-BA-N above could drop to a dry 2x4 when the plumbing moved off it.
    # Top=8'-0" is the bearing seat, like every other partition here; the vent turns west
    # over the plate at y=19'-3", along a joist bay rather than across one.
    Wall(uid="8BRZAXSW73", tag="W-B-BA-E", start_node="N-B-BA-NE",
         end_node="N-B-BA-SE", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8),
         interior_room="RM-B-BATH"),
    # ESS closet's two framed walls (moved to the NE corner, same uids, so the enclosure is
    # the same two walls relocated rather than a new pair).
    # INT_ESS_CLOSET_STEEL (steel studs, 5/8" Type X both faces) is an owner standard, not a
    # code-rated assembly, hence `advisory.ess_enclosure` being advisory (see
    # plan/assemblies.py). `interior_room` on both keeps the Type X face unambiguous; the
    # other two sides of the closet are concrete and satisfy the same check by being mass
    # noncombustible.
    #
    # W-B-ESS-N runs north-to-south down the closet's west side and carries D-B-ESS, which
    # is the change of habit from the old corner: there the door was in the long north wall,
    # here the west wall is the one facing the room's open floor. The south partition cannot
    # take it — EQ-B-ERV stands 10 1/4" south of it and a 2'-0" leaf needs 2'-0".
    Wall(uid="CBW124AAAA", tag="W-B-ESS-W", start_node="N-B-ESS-N",
         end_node="N-B-ESS-SW", assembly="INT_ESS_CLOSET_STEEL", top=ft(8),
         interior_room="RM-B-ESS"),
    Wall(uid="CBW125AAAA", tag="W-B-ESS-S", start_node="N-B-ESS-SW",
         end_node="N-B-ESS-SE", assembly="INT_ESS_CLOSET_STEEL", top=ft(8),
         interior_room="RM-B-ESS"),
    # ================= THE STAIR WELL'S PARTITION, AND THE CLOSET UNDER THE FLIGHT
    # =================
    #
    # Two walls that between them turn 17.5 sf of unreachable floor into a closet, and draw
    # a divider the model has always reserved space for and never built.
    #
    # `resolve/stairs/common.py` budgets 4 1/2" between ST-B2M's two flights and emits no
    # member, so W-B-WELL fills a RESERVED VOID: it is not colliding with the stair, it is
    # the thing the stair already made room for. CATLIN_STAIRWELL_PARTITION_4H is 4 1/2"
    # exactly for that reason (plan/assemblies.py). It runs from N-B-BA-NE — the bathroom's
    # north-east corner, slid onto this same centreline in the same edit — north to
    # N-B-CL-NE, so W-B-BA-E and this wall are ONE PLANE 13 feet long.
    #
    # top=ft(8) is the basement's bearing seat, like every other partition down here. Above
    # it is FO-M-STAIR's void, not joists, so nothing lands on it and it is not BEARING.
    # It carries no framing of its own — see the assembly.
    Wall(uid="9AYPA03VAE", tag="W-B-WELL", start_node="N-B-BA-NE",
         end_node="N-B-CL-NE", assembly="CATLIN_STAIRWELL_PARTITION_4H", top=ft(8),
         interior_room="RM-B-UNDERSTAIR"),
    # The closet's north wall, and **it is NOT full height.** Two things are overhead: the
    # arriving flight, whose stringer underside on this line is 52.9" over the slab, and —
    # 1 1/2" of the way along it — `ledger-W-B-STR-landing-rim-upper-0`, the 2x10 carrying
    # the upper landing off W-B-STR, which occupies 47.6"..56.9". The ledger is the binding
    # one and it is the lower: **47" tops out 5/8" under it**. (52" would have cleared the
    # stringer by 1.2" and driven straight into the ledger; the first build said so.)
    # Ordinary INT_2X4_PARTITION: this wall is not in the stair's reserved slot, nothing
    # else frames it, and it needs its own studs. It does make N-B-ESS-SE a four-way — a
    # 2x6 bearing wall running through, a steel-stud ESS partition west, this one east —
    # and `_through_pair` used to pick its through run alphabetically, which chose the two
    # partitions and called the node mixed-assembly. That was an engine bug and is fixed in
    # resolve/topology.py; the node classifies off the bearing pair now.
    Wall(uid="3GQXK314FQ", tag="W-B-CL-N", start_node="N-B-ESS-SE",
         end_node="N-B-CL-NE", assembly="INT_2X4_PARTITION", top=inch(47),
         interior_room="RM-B-UNDERSTAIR"),
    # Unglazed buff brick veneer over the exposed run of W-B-S2/W-B-S3, where the sunken
    # garden is dug against them — everywhere else this wall is buried and the parge is a
    # below-grade coating nobody sees; here it's the house's most-looked-at elevation.
    #
    # ** IT STANDS ON W-SG-BRKBM, AND NOT ON THE HOUSE FOOTING. ** This wythe is 129 SF of
    # masonry exposed on BOTH faces at the bottom of an open court, so it runs at outdoor
    # temperature all winter. Until 2026-09-05 it bore on FT-B-BRICK, a plinth cast on
    # FT-B-S2/S3's own projecting toe, which put that cold directly in series with the house
    # footing — the footing whose underside is level with the court floor and whose frost
    # cover is the R403.3 wings. The break meant to interrupt it was authored twice and
    # drawn never (see SG_VENEER_BEAM_14 in plan/assemblies.py for both spellings and why
    # neither existed). It now bears on a grade beam spanning to W-SG-W1 and W-SG-E1, so
    # its whole load and heat path goes into the court's own structure, which is already
    # broken from the house at DW-SG-W1/E1-FOAM.
    #
    # Bottom stays at -8'-9", now because that is the beam's top rather than a plinth's: it
    # still has to clear D-B-PATIO's raised threshold, and a base course should not sit in
    # standing water whatever the brick is.
    #
    # ** THE WYTHE MOVED 4 1/2" SOUTH, AND NOT FROM HERE. ** The 6" cavity is authored as
    # BASEMENT_BRICK_VENEER's `air-gap` thickness, not as a node position, precisely so the
    # two arched reveals below — positioned `from_node` along the wall AXIS — do not move
    # with it. N-B-BRICK-W/-E are untouched at -4.05".
    #
    # Authored EAST->WEST — opposite W-B-S2/W-B-S3 — deliberately: this wythe is its own
    # wall-graph component (two open ends, no loop), so resolve/orientation.py hands it
    # outward sign +1 instead of the perimeter's -1. Reversing the direction is what keeps
    # its exterior layers building south into the garden instead of north into the concrete.
    #
    # The reveals below still measure from N-B-BRICK-W: ``from_node`` counts back from the
    # far end, so naming the west node still works when it's where the run finishes.
    FoundationWall(uid="CBW126AAAA", tag="W-B-BRICK", start_node="N-B-BRICK-E",
                   end_node="N-B-BRICK-W", assembly="BASEMENT_BRICK_VENEER",
                   alignment=face("air-gap-int"),
                   unbalanced_fill=ft(0),
                   top_elevation=ft(0), bottom_elevation=inch(-102.4375)),
]

OPENINGS = [
    # Interior circulation
    # ** 3'-3", AND IT IS THE CONDENSATE LINE THAT SAYS SO (2026-09-05). ** A UI drag had
    # put this at 1'-6 1/16", and `from_node` offsets the NEAR JAMB, not the centre
    # (resolve/pipeline.py), so the 32" opening ran x 1'-6 1/16"..4'-2 1/16" — straight
    # across all three services in this wall. `mep.run_through_opening` FAILed three times:
    # CD-B-SPA at x=2'-0" and CD-B-DATA-SHOP at x=2'-6", both 61" over the slab, and
    # PR-B-ERV-COND at x=2'-11", 49 7/8" up.
    #
    # None of the three can move. `ConduitRun` carries ONE flat elevation for its whole
    # polyline (model/mep.py), and CD-B-SPA's south end is pinned at -4'-0" by two concrete
    # sleeves, so it cannot be lifted over the head. PR-B-ERV-COND is a gravity condensate
    # drain that already starts at 54" under an 80" head. And the bay west of the opening is
    # 5 9/16" clear, which takes two of the three and not all three.
    #
    # So the door moves. The binding constraint is the condensate line at x=2'-11": the king
    # stud occupies [jamb-3", jamb-1 1/2"], so a jamb at 3'-3" puts the king's west face at
    # 3'-0" and clears the pipe's surface by 0.475". Both conduits clear by 6"-12". 1" west
    # of the 3'-4" this door was authored at before the drag, which is why
    # mep_drainage.py's routing note (measured against 40") was restruck with it.
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT-SWING32",
         position=from_node("N-B-W1", ft(3, 3))),
    # Solid-core pair: the play room keeps the 5'-0" double opening, with flush solid
    # leaves instead of full glazing.
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT-DOUBLE60",
         position=from_node("N-B-C", ft(6, 2))),
    # **The two doors formed through 12" interior pours are gone (2026-09-05.)** This one
    # was a blockout in W-B-CS2 and D-B-NE was one in W-B-CN; between them they were the
    # house's only `openings.count[host_structure=concrete]`. The dollars were modest — a
    # buck-and-blockout allowance — and the real gain is circulation: from the stair foot
    # the furnace room used to be five rooms away (stair -> playroom -> gym -> aisle ->
    # workshop -> furnace).
    #
    # D-B-GYM keeps its uid and its 32" leaf and moves onto W-B-CS3, the framed 4'-4" of
    # the x=18' line between the rotated sauna and the y=18' cross wall. ``from_node``
    # offsets the opening's near *edge*, so 6" leaves half a foot of wall at the sauna end
    # and 1'-3" at the north — and that 1'-3" is spent: ED-B-GYM-RC8 stands in it, because
    # everything north of N-B-C1 on this line is W-B-CS2's 12" pour.
    # It swings east into the gym on the default (left-hand normal of W-B-CS3's
    # north-to-south direction).
    Door(uid="CBD203AAAA", tag="D-B-GYM", host="W-B-CS3", type_ref="DT-INT-SWING32",
         position=from_node("N-B-C1", ft(0, 7.8125)), flip_swing=False, flip_hinge=False),
    # Used to be D-B-STAIR, opening into the workshop through W-B-CW2's concrete; on
    # 2026-07-30 the shaft's south 3'-0" became RM-B-BATH, and on 2026-09-05 the bathroom
    # rotated north-south, so this leaf (same uid, same 32" width) is on the room's east
    # wall now, opening into the new hall. It still swings OUT — the left-hand normal of
    # W-B-BA-E's north-to-south direction is east — because an inswing in a 3'-3 15/16" room
    # sweeps the WC clearance zone, the lavatory and the receptacle, all
    # `integrity.door_swing_conflict` violations. Jambs resolve to y 22'-8 1/16"..20'-0 1/16"
    # (the "23'-2"..20'-6"" this comment claimed was already 6" out before the wall moved)
    # and clear both fixtures' footprints; hinge at the south jamb, latch at the north where
    # ED-B-BATH-SW is.
    Door(uid="CBD207AAAA", tag="D-B-BATH", host="W-B-BA-E", type_ref="DT-INT-SWING32",
         position=from_node("N-B-BA-NE", ft(2, 9.9375)), flip_hinge=True, flip_swing=True),
    # ESS closet door, opening west into the furnace room. DT-INT-SWING24: a 2'-0" leaf is
    # what a closet this size takes with jamb both sides. 10" offset from the corner, not
    # the original 4": at 4" the opening's king stud clashed with the wall's corner post
    # (`structural.member_interference` against CBW125AAAA); 10" clears it, and the same 10"
    # is carried over to the new corner for the same reason. Measured from N-B-ESS-SW so the
    # leaf sits in the closet's south half and EQ-B-ESS-BATT, hung on the north concrete,
    # stands clear of the swing.
    Door(uid="CBD208AAAA", tag="D-B-ESS", host="W-B-ESS-W", type_ref="DT-INT-SWING24",
         position=from_node("N-B-ESS-SW", ft(1, 4))),
    # ** RM-B-UNDERSTAIR's door, new 2026-09-05 — the thing that makes 17.5 sf of floor
    # reachable. ** In W-B-STR3, opening WEST into RM-B-FURNACE: W-B-STR3 runs
    # north-to-south, so its default left-hand normal is east — into 17.5 sf under a rake,
    # where no leaf can open. `flip_swing` sends it into the mechanical room instead.
    #
    # 10" off N-B-BA-NW, not 4", for exactly D-B-ESS's reason two lines up: at 4" the king
    # stud clashes with the corner post. That puts the leaf at y 26'-4"..28'-4", and the far
    # jamb is what sizes the door — see DT-INT-CLOSET24 in storeys/main.py. A 6'-8" head
    # would be six inches inside the stringer.
    Door(uid="B43P8B5Y0T", tag="D-B-CLOSET", host="W-B-STR3", type_ref="DT-INT-CLOSET24",
         position=from_node("N-B-BA-NW", inch(10)), flip_swing=True),
    # **The hall's cased opening into the workshop** — a bare `RoughOpening` with no
    # `type_ref`, the `O-S-VANITY` idiom (second.py); `structural.door_module` already
    # reads a typeless RoughOpening as cased. No leaf: this is the through-route from the
    # stair foot to the gym now that both concrete doors are gone, and a door across a
    # circulation spine buys nothing.
    # 2'-10" and not 3'-0": on a 4'-1 5/16" segment with a 5" offset it keeps a king and a
    # jack at both ends, with 4 5/16" to spare at the east one.
    RoughOpening(uid="ZCY1ZX6VRA", tag="O-B-HALL", host="W-B-CW2B",
                 position=from_node("N-B-BA-SE", inch(5)),
                 width=ft(2, 10), height=ft(6, 8)),
    # The sauna is entered FROM THE GYM since the rotation — the short route to D-B-PATIO
    # and the sunken garden, which is what the brief asks the room for. Same uid, same 24"
    # leaf, rehosted from W-B-SA-W onto W-B-CS. y 4'-10"..2'-10": far enough north to clear
    # D-B-PATIO's inswing arc and the shower pan in the sauna's NE corner, far enough south
    # to keep clear of D-B-GYM. Swings out into the gym on the default.
    Door(uid="CBD205AAAA", tag="D-B-SAUNA", host="W-B-CS", type_ref="DT-INT-SWING24",
         position=from_node("N-B-SA-NE", ft(4, 3.3125)), flip_hinge=True),
    # Raise the exterior threshold above the basement floor to resist sunken-garden flooding.
    # Hosted on the framed wall, and `sill_height` is inch(0) — NOT because the threshold
    # dropped, but because the datum did. A sill is measured from the host wall's own base,
    # and W-B-S3-FR's base is the top of the 7 1/4" curb. The threshold is at the same
    # absolute elevation it always was, a quarter inch higher: the door now sits ON the curb
    # rather than 7" up a pour with a quarter inch of concrete still above it.
    #
    # **It swings IN, and that is a code requirement, not a preference.** The curb makes
    # this door a 7 1/4" step down to the court, which is R311.3.2's one-riser allowance
    # for a door that is not the required egress door — and that allowance is conditioned
    # on the door NOT swinging over its landing. `flip_swing=True` used to sweep it south
    # into the court, over the very landing being measured, which voids the relief and
    # drops the limit to 1 1/2". Swinging north into the gym is what makes the 7 1/4"
    # legal. `code.R311_3_exterior_landing` now tests `swing_clearance` and will say so.
    Door(uid="CBD206AAAA", tag="D-B-PATIO", host="W-B-S3-FR", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-B-S2F", inch(10)), sill_height=inch(0)),
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
    # It sits 3'-3" off the corner: a hole in a pour lands where you form it,
    # while a 14" RO in a stud wall wants a BAY CENTRE, where the bay's own two studs carry
    # the rough sill and head nailer and it needs no header, no jacks and no kings at all
    # (preferences.toml's `max_window_ro_unbroken_in`). W-B-S2-FR lays out from layout line
    # LL-W-A-S1 and reaches the module 6" along itself, so its bay centres are 14" + n x 16"
    # and 3'-3" puts the 14" opening on the 46" one. `structural.window_framing_module`
    # said so, at 7" off, the moment the wall stopped being concrete.
    Window(uid="CBX301AAAA", tag="WIN-B-SAUNA", host="W-B-S2-FR",
           type_ref="WT-1424-T", position=from_node("N-B-S1F", ft(3, 3)),
           sill_height=inch(36.75)),
    # --- reveals through the brick veneer -------------------------------------------
    # WIN-B-SAUNA and D-B-PATIO stay on the concrete walls; these are RoughOpenings for the
    # holes the wythe in front of them needs, each with its own segmental brick arch — not a
    # duplicate Window/Door, which would double the schedule and takeoff.
    # Positioned off N-B-BRICK-W (shares N-B-S1's x). Segmental, not semicircular: the
    # rise is ~1/7 of clear width, and ``height`` includes it, so the springline is
    # ``height - rise``. ``sill_height`` is re-datumed off W-B-BRICK's own base
    # (-8'-5", not -9'): the window's 3'-8" becomes 3'-1", the door's 7" threshold becomes 0.
    # 3'-3" follows WIN-B-SAUNA onto its stud bay centre. The reveal and the window it
    # reveals must stay concentric — `integrity.reveal_concentric` FAILs if they are more
    # than 1" apart — and only the offset moved; the elevations did not (both sills still
    # land at -65 7/16").
    RoughOpening(uid="CBO601AAAA", tag="AO-B-BRICK-WIN", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", ft(3, 3)),
                 width=inch(14), height=inch(20), sill_height=inch(37),
                 arch=Arch(rise=inch(2))),
    # 78" is a HEIGHT WITH NO CONSTRAINT LEFT ON IT, and that is worth saying plainly. It
    # was struck to leave 10" of lapis between the arch crown and the gold register at 88";
    # the registers went away on 2026-09-04 and the field is now one flat unglazed brick, so
    # nothing above the crown is fixed any more. 78" is kept because it still looks right and
    # still springs the arch at 70" — not because anything requires it. If more of the door
    # head should be covered, 84" is now available; the register was the only thing that was
    # ever stopping it.
    #
    # Both reveals are SHORTER than the openings they front, and that is the point, not a
    # defect: a masonry reveal in front of a rectangular hole is meant to overlap it. The
    # door's head is covered across its full width and the sauna window loses its top 6".
    # Neither is a daylight or egress subject — WIN-B-SAUNA is not an emergency escape
    # opening and `egress.py` already excludes these arches by name — but if the sauna ever
    # wants that glass back, this height is the line to move, not the window.
    #
    # WIDTH AND POSITION ARE NOT FREE THE WAY HEIGHT IS. This reveal drifted 6" east of
    # D-B-PATIO between 2026-08-30 and 2026-09-04, because the door moved off its own node
    # on its own wall and nothing carried the reveal with it. `integrity.reveal_concentric`
    # grades that now, and test_catlin_contract_m3 pins both pairs. Edit the two together.
    RoughOpening(uid="CBO602AAAA", tag="AO-B-BRICK-DOOR", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", ft(10)),
                 width=ft(5), height=inch(78), sill_height=ft(0),
                 arch=Arch(rise=inch(8))),
]

ROOMS = [
    Room(uid="CBR401AAAA", tag="RM-B-FURNACE", seed=pt(ft(5), ft(30)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete"),
    # W-B-STR now separates this from the furnace room, so the stair bottom is its own
    # space instead of dumping arrivals into the mechanical room.
    # **The HALL is part of this room's loop, not a room of its own** (2026-09-05): the
    # 3'-3 15/16" slot west of W-B-CN2, from the stair foot south to the y=18' line, is inside
    # the same closed face and needs no `Room` — it is circulation on the same floor finish
    # with the same occupancy, and a second `Room` here would only split one space in two
    # for every check that walks rooms.
    # **The seed moved into the hall on 2026-09-05.** (14', 30') is inside W-B-WELL's new
    # footprint (x 13'-8 7/16"..14'-0 15/16"), which would be a guaranteed
    # `integrity.room_unclaimed`. The hall is the same room, so the seed only has to find it.
    Room(uid="CBR406AAAA", tag="RM-B-STAIR", seed=pt(inch(186), ft(22)),
         occupancy=Occupancy.STAIR, floor_finish="sealed-concrete"),
    # ** RM-B-UNDERSTAIR, new 2026-09-05: 17.5 sf that nobody could reach until this edit. **
    # The volume under ST-B2M's arriving flight was inside RM-B-STAIR's polygon, so the model
    # counted it as floor, but the bathroom is south of it, the well partition east,
    # W-B-STR3 west and the flight overhead: no way in and no check that could say so,
    # because the well partition was not a wall. It is one now (W-B-WELL above), the closet's
    # north wall closes the last side, and D-B-CLOSET in W-B-STR3 opens it to the furnace
    # room. x 10'-3 3/8"..13'-8 7/16" (3'-5 1/16") by y 25'-8 3/8"..30'-9 3/4" (5'-1 3/8").
    #
    # ** DO NOT AUTHOR `ceiling`, AND DO NOT PUT A `Soffit` UNDER THE FLIGHT. ** The real
    # head here rakes from 96.7" at the south end to 54.8" at the north, and no field in this
    # engine can say that: `_clear_head` (resolve/rooms.py) reads ceiling decks and
    # ResolvedSoffits, and a raking stringer is neither, so `clear_height_m` resolves to the
    # main-floor deck at ~96.9" and passes R305.1.1's 80" basement minimum. An authored 53"
    # ceiling, or a flat soffit at 53", would be taken VERBATIM and FAIL
    # `code.R305_ceiling_height` for a storage closet the code does not measure. The rake is
    # recorded here, in prose, because that is the only place the model can hold it.
    #
    # STORAGE is in `_UNDER_STAIR_OCCUPANCIES` (checks/code/mn_residential/illumination.py),
    # which is what puts this closet in front of R302.7 — see W-B-STR3's retype in WALLS.
    Room(uid="R58W0DMTJ5", tag="RM-B-UNDERSTAIR", seed=pt(ft(12), ft(28)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
    # Stair-foot bathroom, ROTATED NORTH-SOUTH 2026-09-05: it runs down the framed stair
    # wall (x 10'-3 3/8"..13'-7 5/16", y 18'-2 3/8"..25'-3 5/8", 3'-3 15/16" x 7'-1 1/4"
    # between finish faces) rather than across the shaft's south 3'-0". It is still under
    # ST-B2M's flight (bottom riser at y=26'-0 3/8"), and it is still one fixture at each
    # end so each one's depth runs across the room's short dimension: WC north, vanity
    # south (plan/fixtures.py). What the rotation bought is the HALL east of it — the room
    # gave up the shaft's east half so the stair foot could reach the workshop without
    # going through a door in a pour.
    #
    # Sheet vinyl, not tile, joining the house's washable spine — RM-M-BATH1 and
    # RM-M-LAUNDRY, RM-2-BATH on the second storey and the attic studio's bath took the
    # same move. 30.2 sf with no radiant zone under it, which is the
    # whole test: tile earns its cost where it is the emitter's mass (RM-M-BATH2 keeps its
    # tile for exactly that reason, at 98% of FH-M-BATH2's load). Here it buys grout to
    # keep, a backer board, a membrane and a threshold at the door, for a floor three feet
    # wide under a stair. Heat-welded sheet with a 6" integral flash cove that laps the wall
    # and dies behind the wall finish: floor and wall are one tray with no base joint, and
    # the cove IS the waterproofing — nothing impermeable goes under it.
    Room(uid="CBR407AAAA", tag="RM-B-BATH", seed=pt(ft(12), ft(22)),
         occupancy=Occupancy.BATHROOM, floor_finish="vinyl-sheet"),
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
    # The floor is SEALED CONCRETE, not tile. SL-B-FLOOR already runs flat and
    # sloped 1/8"/ft to FX-B-SAUNA-FD (13'-6", 7'-7 3/16") under the whole room, and
    # FX-B-SAUNA-SH is a curbed
    # liner pan — the pan brings its own waterproof floor, so nothing outside it needs a
    # tile bed. `integrity.concrete_finish_needs_concrete_deck` is satisfied by SL-B-FLOOR.
    # The tile that remains in this room is WP-B-SAUNA-SPLASH, the pan's two closed wall
    # sides; see the PANELING note below.
    # Ceiling: the same T&G-over-foil-polyiso liner as the walls (assemblies.py's
    # `_SAUNA_LINER`), restated rather than imported — the editable dialect cannot import
    # a sibling plan module. Keep the two in step by hand.
    Room(uid="CBR403AAAA", tag="RM-B-SAUNA", seed=pt(ft(11), ft(5)),
         occupancy=Occupancy.BATHROOM, humidity_class=HumidityClass.WET,
         floor_finish="sealed-concrete",
         ceiling_lining=(
             Layer(name="shiplap-liner", material_ref="sauna-shiplap", thickness=inch(1.0),
                   function=LayerFunction.FINISH),
             Layer(name="liner-furring", material_ref="struct-1-plywood", thickness=inch(0.5),
                   function=LayerFunction.FURRING,
                   framing=FramingSpec(member="1x4", direction="horizontal")),
             Layer(name="foil-polyiso", material_ref="polyiso-foil", thickness=inch(2.0),
                   function=LayerFunction.INSULATION,
                   control={ControlLayer.THERMAL, ControlLayer.VAPOR, ControlLayer.AIR}),
         )),
    Room(uid="CBR404AAAA", tag="RM-B-PLAY-N", seed=pt(ft(27), ft(27)),
         occupancy=Occupancy.MEDIA, floor_finish="carpet"),
    Room(uid="CBR405AAAA", tag="RM-B-GYM", seed=pt(ft(27), ft(9)),
         occupancy=Occupancy.LIVING, floor_finish="rubber"),
    # ESS closet: MECHANICAL like the room it's carved from — STORAGE would
    # trigger habitability rules a battery cabinet has no use for. R327.4 permits an ESS in
    # a utility closet, which is exactly what this is.
    Room(uid="CBR408AAAA", tag="RM-B-ESS", seed=pt(ft(8), ft(33, 6)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete"),
]

ALARMS = [
    Alarm(uid="CBA701AAAA", tag="AL-B-COMBO", kind=AlarmKind.COMBO, room="RM-B-PLAY-N",
          circuit="CKT-LT-BACKUP"),
    # IRC R327.7 wants both smoke and heat: a lithium cell's failure announces itself as
    # heat before smoke reaches outside the cabinet. Both alarms sit inside RM-B-ESS, not
    # just within `code.R327_ess_detection`'s 6' allowance in RM-B-FURNACE, so the heat
    # alarm actually senses the cabinet and not the room outside the Type X membrane.
    # CKT-LT-BACKUP so they survive an outage.
    Alarm(uid="CBA702AAAA", tag="AL-B-ESS-SMOKE", kind=AlarmKind.SMOKE, room="RM-B-ESS",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CBA703AAAA", tag="AL-B-ESS-HEAT", kind=AlarmKind.HEAT, room="RM-B-ESS",
          circuit="CKT-LT-BACKUP"),
]

# No radiant floor in the basement. A heated floor under RM-B-SAUNA, which already runs at
# 190 °F, would be heat with nowhere to go and a stat with no honest place to read from.
# The electric radiant zones are all on the storeys above — main.py and second.py.

SLABS = [
    Slab(uid="CBS501AAAA", tag="SL-B-FLOOR",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(3.5), assembly="CATLIN_SLAB_FLOOR",
         perimeter_thermal_break=SlabThermalBreak(material_ref="xps", thickness=inch(1))),
]

FLOOR_OPENINGS = [
    # Shower recess is a finish-zone concern; the stair arrives via the slab above.
]

# The sauna's corner-shower splash walls (plans/TODO.md §Hardwood): the 36"x36" pan's two
# closed sides are tile for the full 7'-6" liner height, not basswood T&G — an override
# that bills as tile and is subtracted from the SAUNA assemblies' sauna-shiplap liner area.
# W-B-CS runs from N-B-SA-NE (the shower corner) south, so its splash is the first 3';
# W-B-SA-N runs west→east into that same corner, so its splash is the last 3' of its run —
# re-datumed to 5'-10" when the 2026-09-05 shrink took that run from 13'-4" to 9'-2".
PANELING = [
    WallPaneling(uid="CBK901AAAA", tag="WP-B-SAUNA-SPLASH", room="RM-B-SAUNA",
                 material_ref="tile", height=ft(7, 6), replaces_wall_finish=True,
                 spans=(PanelingSpan(wall_ref="W-B-CS", start=ft(0), length=ft(3)),
                        PanelingSpan(wall_ref="W-B-SA-N", start=ft(5, 10), length=ft(3)))),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *SLABS, *FLOOR_OPENINGS,
            *PANELING]

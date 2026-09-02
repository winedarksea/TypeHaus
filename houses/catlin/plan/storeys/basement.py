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
    Node(uid="CBN014AAAA", tag="N-B-SA1", position=pt(ft(8, 10), ft(13, 10))),
    # Stair-foot bathroom's north partition (2026-07-30), spanning the shaft's full 7'-0"
    # clear width so it tees into both concrete walls' node lines (x=10', x=18"). y=21'-9 3/8"
    # is back-calculated: 3'-0" clear off W-B-CW2's north face (18'-6") plus half of
    # INT_2X6_STAGGERED_PLUMBING's 6 3/4" thickness.
    Node(uid="CBN015AAAA", tag="N-B-BA-W", position=pt(ft(10), ft(21, 9.375))),
    Node(uid="CBN016AAAA", tag="N-B-BA-E", position=pt(ft(18), ft(21, 9.375))),
    # W-B-CW's east end. Named N-B-ESS-S until 2026-08-23, when the ESS closet left the SE
    # corner for the NE one: the split it was minted for is still real (W-B-CW3 carries a
    # different assembly from W-B-CW here) but it has nothing to do with the battery any
    # more, and a node tagged for a room it no longer touches is how a plan starts lying.
    # The uid is unchanged, so nothing in the IFC moved.
    Node(uid="CBN017AAAA", tag="N-B-CW-E", position=pt(ft(6, 9), ft(18))),
    # ESS closet, NE corner of the furnace room (2026-08-23; was the SE corner, 2026-08-02).
    # Two sides come free here as they did there — W-B-N3 on the north (concrete, inner
    # face y=35'-4") and W-B-STR on the east (inner face x=9'-8 1/2" since 2026-08-24,
    # when that wall was framed and took the Type X leaf the closet needs) — so it is
    # still two framed partitions, not four. x=6'-0" and y=31'-0" leave 3'-6 1/8" x
    # 4'-1 5/8" clear (3'-3 5/8" while the east side was the pour's face at x=9'-6"; the
    # Type X leaf lands 2 1/2" further east), more than the 2'-8 1/4" cabinet it replaces,
    # and clear of everything already on this side: SP-B-N3-HYD (x=5'-0" through the north
    # wall) and ED-B-SUMP-RC (x=4'-6"). SP-B-STR-CD-DATA was the third of those; it went
    # with the pour (electrical.py).
    #
    # **x=6'-0" is not a round number chosen for tidiness.** Neither concrete side of this
    # corner was split before, so both had to be, and a basement split that does not line up
    # with the storey above puts one wall over two. N-M-MECH3 already splits the main
    # storey's north wall line at exactly x=6'-0" (RM-M-MECH's shaft closet, 2026-07-28), so
    # splitting W-B-N3 there makes W-M-N3 sit over W-B-N3 and W-M-N3B over W-B-N4, one to
    # one. The east wall has no such gift — W-M-STRW runs y 26'-4"..36'-0" straight across
    # W-B-STR's new y=31'-0" split — and that is called out on W-B-STR below.
    #
    # The corner is only available because EQ-B-WH left it — see plan/mep_hvac.py.
    Node(uid="CBN018AAAA", tag="N-B-ESS-N", position=pt(ft(6), ft(36))),
    Node(uid="BT88F385N4", tag="N-B-ESS-SW", position=pt(ft(6), ft(31))),
    Node(uid="GXJ9S72CKH", tag="N-B-ESS-SE", position=pt(ft(10), ft(31))),
    # Glazed-brick veneer over the exposed south wall (W-B-BRICK): a freestanding wythe off
    # the concrete, both ends ``open_end`` like the sunken garden's N-SG-NW/NE (not part of
    # any wall loop). x runs only as far as the excavation in front of it: N-B-S1's x (8'-10")
    # to 28'-0" (params/sunken_garden.py's ``_x_ax_e``, where grade comes back up).
    # y is NOT 0'-0": the south walls' node line is the concrete face, and the south stack
    # carries 4.05" outboard of it (0.05" damp-proofing + 2x 2" XPS) — a tail that is
    # independent of the pour, which is why thinning the wall to 8" in 2026-08-21 did not
    # move this number; the veneer stands off that finished face, hence the -4.55".
    #
    # The stand-off is 4.55" and NOT 4.05" because it was struck against the parge coat the
    # south wall carried until 2026-09-02, when the stucco was deleted house-wide (it was
    # 273.7 SF of finish of which ~29 SF was ever visible; see plan/assemblies.py). The node
    # is deliberately left where it is: moving the veneer 1/2" inboard would move its two
    # arched reveals, its own footing and every garage-relative literal downstream of it, to
    # buy nothing. What the deletion changes is the cavity, which opens from 1" to 1-1/2" —
    # still over IRC R703.8.4's 1" minimum, and better-draining. Wall aligns on
    # face("air-gap-int"), which now begins on bare XPS.
    Node(uid="CBN019AAAA", tag="N-B-BRICK-W", position=pt(ft(8, 10), inch(-4.55)),
         open_end=True),
    Node(uid="CBN020AAAA", tag="N-B-BRICK-E", position=pt(ft(28), inch(-4.55)),
         open_end=True),
]

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
    # **The row, spelled out.** GM soil is 45 psf/ft (mn-2024 profile). Since 2026-08-23 the
    # wall runs -13 7/16" (the bearing seat) to -9'-1 7/16" (the slab), so it is **exactly
    # 8'-0"** of pour -> the 8' row, not the 10' row a 9'-4" wall rounded up to. Grade is at
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
    # **Which wall gets which thickness.** It used to be one physical rule — "12" is earned
    # only where a cast concrete deck lands on the wall top beside the sill plate" — and
    # that rule is **obsolete as of 2026-08-23.** It described a wall top where a cast deck
    # and a mudsill competed for width: the deck needed its own seat *inboard* of the plate,
    # so the wall had to be wide enough for both. There is one flat seat now, at
    # -13 7/16" all the way round, and the deck's soffit lands on the same plane the mudsill
    # sits on. Nothing competes, and no wall needs extra width for bearing at all: the 12"
    # segments carry SL-M-DECK on 12" because they always did, and an 8" wall would carry it
    # just as well.
    #
    # So the three that stay 12" stay for reasons that are no longer about bearing width,
    # and each is worth stating. (It was four until 2026-08-28: W-B-CS, the one this list
    # already admitted "COULD go to 8"", is a 2x6 bearing stud wall now — see its own note.)
    #
    #   W-B-E1/E2 — the east perimeter. SL-M-DECK is a 414 SF cast slab and its east edge
    #     lands here; 12" is not needed for the seat, but this is the one perimeter run with
    #     a cast deck on it and the extra 4" is ~2.2 cy against re-detailing the east edge of
    #     a pour that is already the model's fussiest element. Left as built, deliberately —
    #     and it is now the only place in the house where wall thickness is a judgement
    #     rather than a derivation, so it is the first candidate the next time this line is
    #     opened.
    #   W-B-CS2, W-B-CN2, W-B-CN — the centre line under the cast band, same reading.
    #   W-B-CS — FRAMED since 2026-08-28, and no longer on this list at all. It carried
    #     wood on both faces, so what it actually needed was a bearing wall and not a pour.
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
    # 2" inboard toe. The footings follow the slab up 2 9/16" (params/foundations.py) but do
    # not move in plan — the brick plinth FT-B-BRICK is dimensioned off the strip's -10" edge.
    # **The south wall retains four different amounts of soil, and now says so.**
    # None of these segments authored ``unbalanced_fill`` until 2026-08-28, so
    # ``structural.foundation_unbalanced_fill`` fell back to its documented proxy —
    # grade (-2'-10") minus the wall bottom (-9'-1 7/16") = 6.29' on every one of them,
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
    # **W-B-S1 and W-B-S4 joined CATLIN_BASEMENT_8 on 2026-09-02**, off the
    # CATLIN_BASEMENT_8_GARDEN they had carried since the south wall was split. That is the
    # same fill table read a second way: these two segments are the only south run whose
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
                   vertical_reinforcement='#5 @ 41" o.c.'),
    # The sauna's south side. W-B-S1 takes the buried wall's own stack and W-B-S3 the bare
    # curb — they bound the workshop and the patio side — but this one segment is a room face
    # in a WET room, so it carries the liner variant of the curb (SAUNA_LINER_ON_GARDEN_CURB,
    # SAUNA_LINER_ON_BASEMENT_8_GARDEN before the 2026-08-28 curb split): the vapour control
    # has to be continuous on all four faces or it is not vapour control. The liner grows 3 1/2" inward and mitres to
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
    # **W-B-S2 and W-B-S3 are 7 1/4" CURBS since 2026-08-28**, not full-height walls. The
    # 8'-0" of pour above them is a 2x6 framed wall — W-B-S2-FR and W-B-S3-FR below — for
    # the reason this comment block already gives twice over: they hold back nothing. Both
    # keep their tag, their uid and their footing, which is the whole point of putting the
    # curb on the old element rather than the framing: FT-B-S2/FT-B-S3, `_FROST_FORMED`,
    # `structural.frost_depth`, CN-M-HD-BALC-W/E's STHD embedments and W-B-BRICK's
    # dimensions all still name a piece of concrete on a footing, and none of them moved.
    #
    # **Why the curb is kept and why it is 7 1/4".** The sunken garden is a court whose
    # floor is FLUSH with the basement slab (both -9'-1 7/16" since 2026-08-23) with no way
    # out but a drain; heavy rain can stand in it. A concrete curb runs under the whole framed run so standing water
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
    # W-B-BRICK's 4.55" stand-off and its two arched reveals do not move. (The parge used to
    # be third on that list; it was deleted house-wide on 2026-09-02, and W-B-S1/S4 now carry
    # a GRADE-banded protection panel that stops well below this run. The plane the veneer
    # was struck against is 1/2" thinner everywhere, which is a wider cavity and not a
    # moved face — see N-B-BRICK-W above.)
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
    # The east 8'-0" of the old W-B-S3, split off at the excavation edge on 2026-08-28.
    # Buried like W-B-S1, so it keeps the 7'-row bar — and it must join
    # ``params/foundations._FROST_FORMED`` with it, or FT-B-S4 loses the insulated
    # FOOTING_FPSF_20 form the garden floor's low adjacent grade is the reason for.
    FoundationWall(uid="72HXFS8M11", tag="W-B-S4", start_node="N-B-S3",
                   end_node="N-B-SE", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   unbalanced_fill=ft(6, 4),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.'),
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
                   vertical_reinforcement='#5 @ 41" o.c.'),
    FoundationWall(uid="CBW107AAAA", tag="W-B-N2", start_node="N-B-N1",
                   end_node="N-B-N2", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.'),
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
                   vertical_reinforcement='#5 @ 41" o.c.'),
    FoundationWall(uid="HEX0ZDQZEN", tag="W-B-N4", start_node="N-B-ESS-N",
                   end_node="N-B-NW", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.'),
    FoundationWall(uid="CBW109AAAA", tag="W-B-W1", start_node="N-B-NW",
                   end_node="N-B-W1", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.'),
    FoundationWall(uid="CBW110AAAA", tag="W-B-W2", start_node="N-B-W1",
                   end_node="N-B-SW", assembly="CATLIN_BASEMENT_8",
                   alignment=face("concrete-ext"),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375),
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#5 @ 41" o.c.'),
    # Center cross walls (12" concrete) — the 18' bearing grid. Every wall from here down is
    # an *interior* cross wall with soil on neither side, so `unbalanced_fill=ft(0)` says so
    # explicitly — without it `structural.foundation_unbalanced_fill` would read these as
    # retaining 8' of backfill apiece. R404.1.2(8) therefore decides nothing here; these are
    # 12" for the reasons set out in the WALLS header above, none of which is bearing width
    # any more.
    #
    # **W-B-CS is framed since 2026-08-28** — the last of the four 12" segments this header
    # defends, and the one it already admitted "carries wood on both faces and COULD go to
    # 8"". It could go to nothing: FS-M-WEST and FS-M-EAST land on it and W-M-C1 stacks on
    # it, which is a 2x6 bearing wall's job on every storey above. ~4.6 cy out, the same
    # trade W-B-STR/W-B-STR3 made on 2026-08-24. Keeps its tag and uid, so the IFC
    # GlobalId does not move (decision #16). FT-B-CS and its bedding need no edit, for the
    # reason spelled out on W-B-STR3 below.
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
    # `integrity.junction_fallback` reports N-B-C1 UNKNOWN now — W-B-CS is spf and
    # W-B-CS2, collinear with it on the x=18' line, is still 12" concrete under the cast
    # band, so the junction's THROUGH pair is two different bearing materials and the
    # solver has no interface rule for that. It is a real detail and not a modelling
    # artefact: a stud wall landing in line against the end of a 12" pour wants a bearing
    # plate and dowels drawn, which is exactly what the UNKNOWN is asking for. The house
    # answered the same finding at N-B-CW-E in 2026-08-25 by running ONE wall type down
    # the whole line; that answer is not available here, because W-B-CS2 carries
    # SL-M-DECK and stays a pour.
    Wall(uid="CBW111AAAA", tag="W-B-CS", start_node="N-B-C1",
         end_node="N-B-S2", assembly="SAUNA_LINER_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.75)),
         interior_room="RM-B-SAUNA",
         structural_role=StructuralRole.BEARING),
    FoundationWall(uid="CBW112AAAA", tag="W-B-CS2", start_node="N-B-C1",
                   end_node="N-B-C", assembly="FOUNDATION_WALL_12_INT", unbalanced_fill=ft(0),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375)),
    # Split at N-B-BA-E (2026-07-30) so the bathroom's north partition tees onto a shared
    # node — else `integrity.wall_loop_open` reads it as a free end. W-B-CN keeps the tag,
    # uid, and the north 14'-2 5/8" that W-M-C5 stacks on, so the bearing stack is untouched.
    FoundationWall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-BA-E",
                   end_node="N-B-N1", assembly="FOUNDATION_WALL_12_INT", unbalanced_fill=ft(0),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375)),
    FoundationWall(uid="CBW121AAAA", tag="W-B-CN2", start_node="N-B-C",
                   end_node="N-B-BA-E", assembly="FOUNDATION_WALL_12_INT", unbalanced_fill=ft(0),
                   top_elevation=inch(-13.4375), bottom_elevation=inch(-109.4375)),
    # **The y=18' cross line is framed now (2026-08-21).** All four of these were 12" cast
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
    # Tops are 8'-0" — **the bearing seat**, since 2026-08-23. Everything in this basement
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
    # split at N-B-ESS-S (2026-08-02) for the ESS closet's west partition, the same move
    # W-B-STR made for the bathroom. W-B-CW keeps tag/uid and the west 6'-9" (D-B-FURN
    # unchanged); W-B-CW3 is the 3'-3" stub forming the closet's south wall.
    #
    # W-B-CW is the furnace room's south wall and carries the 4" building drain, so it takes
    # the wet-wall 2x6 rather than a 2x4.
    Wall(uid="CBW114AAAA", tag="W-B-CW", start_node="N-B-W1",
         end_node="N-B-CW-E", assembly="INT_2X6_PLUMBING", top=ft(8)),
    # Steel studs and Type X until 2026-08-25, because this was the ESS closet's south wall
    # until the closet moved to the NE corner on 2026-08-23. Now simply W-B-CW continued:
    # same INT_2X6_PLUMBING, one wall type down the whole furnace-room south line.
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
         end_node="N-B-C", assembly="INT_2X4_PARTITION", top=ft(8)),
    # The playroom's south wall, 18'-0" of it, and the one that keeps D-B-PLAY (the 5'-0"
    # glazed double). Staggered studs: it is the long wall between the playroom and the gym,
    # and it also runs under the concrete band, so it wants the sound break.
    Wall(uid="CBW115AAAA", tag="W-B-CE", start_node="N-B-C",
         end_node="N-B-E1", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8)),
    # Stair shaft's west wall — 2x6 bearing studs on x=10', full north-row depth
    # (reference: "Stairway 7' x 16' 6 1/2""). Framed, not poured, since 2026-08-24: it
    # holds back no earth (`unbalanced_fill` was ft(0) the whole time it was concrete), and
    # what it actually does is carry FS-M-MECH/FS-M-STAIR's short joists — the stubs the
    # stair well leaves — and stack W-M-STRW/W-M-STRW2 above. That is a stud-wall job on a
    # footing, not a pour: ~9.8 cy of concrete out, and RM-B-FURNACE gains 3 1/8".
    # Split at N-B-BA-W (2026-07-30): W-B-STR keeps tag/uid and the north 14'-2 5/8" that
    # W-M-STRW/W-M-STRW2 stack on; W-B-STR2 is the 3'-9 3/8" stub alongside the bathroom,
    # carrying its three ceiling-level service crossings (plan/mep.py's WALL_SLEEVES).
    # Split again at N-B-ESS-SE (y=31'-0") on 2026-08-23, for the ESS closet's south
    # partition, exactly as it was split at N-B-BA-W for the bathroom. **Unlike the north
    # wall's split this one does NOT line up with the storey above**: W-M-STRW runs
    # y 26'-6"..36'-0" and crosses from W-B-STR onto W-B-STR3 halfway along. It keeps
    # naming W-B-STR — `resolve/stacking.py` picks it as the sole candidate on both basement
    # segments, since it is the only main-storey wall whose axis overlaps either by the 2'
    # minimum. W-M-STRW2 (trimmed to 5 3/8" on 2026-08-30, south of the split, nominally
    # `stacks_on="W-B-STR3"`) never actually resolves a stack edge either way — at 5 3/8" it
    # cannot clear that 2' overlap test as upper or lower — so its `stacks_on` is honest
    # geometry, not a load path; its real job is FO-S-STAIR's bearing coverage (second.py).
    #
    # **ALIGNMENT is the whole of it**, and the two failure modes below are why it is what
    # it is. Framing this line was tried and backed out on 2026-08-23, for one reason: that
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
    Wall(uid="1H4KR79N9M", tag="W-B-STR3", start_node="N-B-ESS-SE",
         end_node="N-B-BA-W", assembly="CATLIN_STAIRWALL_INT_2X6_BRG", top=ft(8),
         alignment=face("stud-ext", offset=inch(-2.625)),
         interior_room="RM-B-FURNACE",
         structural_role=StructuralRole.BEARING),
    # The stub south of it: RM-B-BATH's west enclosure, nothing bearing on it, nothing
    # dimensioned off it. It carried the ESS closet's steel-stud Type X box until 2026-08-25
    # — it was the closet's east wall before the closet moved to the NE corner on 2026-08-23
    # — and like W-B-CW3 above it is now just its neighbour continued: W-B-STR3's assembly,
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
         end_node="N-B-SA1", assembly="SAUNA_2X4", top=ft(7, 6),
         interior_room="RM-B-SAUNA"),
    # Topped out at the deck instead of its authored 7'-6" until 2026-08-15: W-M-BDN1 at
    # y=13'-4" was within `resolve/platform.py`'s same-wall-line tolerance of this axis
    # (SAUNA_2X4's own depth), a false read. Moving that partition to 13'-0" fixed it; bills
    # ~13.7 sf less basswood (test_wood_surfaces).
    Wall(uid="CBW118AAAA", tag="W-B-SA-N", start_node="N-B-SA1",
         end_node="N-B-C1", assembly="SAUNA_2X4", top=ft(7, 6),
         interior_room="RM-B-SAUNA"),
    # The stair-foot bathroom's only framed wall (2026-07-30); the other three sides are
    # already cast concrete. INT_2X6_STAGGERED_PLUMBING (non-bearing, not a 2x4) because
    # this is the room's *only* stud cavity: the lavatory's and WC's shared 1 1/2" vent rises
    # here before turning west (PR-B-BATH-VENT) — `advisory.wet_wall_depth` needs 5 1/2",
    # exactly this cavity. Runs node line to node line so it tees into both concrete walls.
    # Top=8'-0" is the bearing seat, like every other partition here; the vent turns north
    # over the plate inside the joist bay above it (the joists run east-west, parallel to
    # this wall, so the turn is along a bay rather than across one).
    Wall(uid="CBW120AAAA", tag="W-B-BA-N", start_node="N-B-BA-W",
         end_node="N-B-BA-E", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8),
         interior_room="RM-B-BATH"),
    # ESS closet's two framed walls (2026-08-02; moved to the NE corner 2026-08-23, same
    # uids, so the enclosure is the same two walls relocated rather than a new pair).
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
    # Glazed forest-green brick veneer over the exposed run of W-B-S2/W-B-S3, where the
    # sunken garden is dug against them — everywhere else this wall is buried and the parge
    # is a below-grade coating nobody sees; here it's the house's most-looked-at elevation.
    #
    # Bottom at -8'-9", NOT -9' with the concrete it faces: (1) there's no ground left for a
    # footing at -9' — FT-B-S2/FT-B-S3 already project 10" south, so the veneer bears on the
    # house footing's own toe via a shallow plinth (FT-B-BRICK) cast on it, not poured
    # beside it; (2) that plinth has to clear D-B-PATIO's raised threshold, which is also
    # the better detail — a glazed veneer's base course should not sit in standing water.
    # The plinth runs -9'-2" to -8'-9" and shows **7"** above the garden slab (-9'-4") as a
    # concrete water table.
    #
    # (Both numbers were stale, corrected 2026-08-22 against the resolved model: this read
    # "-8'-5"" and "3.5" above the garden slab (-8'-8.5")". The garden floor is at -9'-4",
    # not -8'-8.5" — it went down with the soil on 2026-08-21 and this comment did not.)
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
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT-SWING32",
         position=from_node("N-B-W1", ft(3, 4))),
    # Solid-core pair since 2026-08-21 (was DT-INT-FRENCH60): the play room keeps the
    # 5'-0" double opening, but flush solid leaves instead of full glazing.
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT-DOUBLE60",
         position=from_node("N-B-C", ft(6, 2))),
    # Centred in the 3'-4" aisle the sauna's north wall leaves against the center wall.
    # ``from_node`` offsets the opening's near *edge*, so 8" leaves ~4" of concrete jamb
    # at each end of the 4'-2" W-B-CS2 segment.
    Door(uid="CBD203AAAA", tag="D-B-GYM", host="W-B-CS2", type_ref="DT-INT-SWING32",
         position=from_node("N-B-C1", inch(8)), flip_swing=False, flip_hinge=False),
    # Pushed 6" north on 2026-07-30 (was ft(4), a near edge at y=22'-0"): the stair-foot
    # bathroom's north partition resolves to a 22'-0 3/4" north face, which would have landed
    # 3/4" inside this opening's south jamb. At 22'-6" the door keeps 5 1/4" of concrete jamb
    # south of it, and the flight it faces still springs 1'-4" further north at 26'-0 3/8".
    Door(uid="CBD204AAAA", tag="D-B-NE", host="W-B-CN", type_ref="DT-INT-SWING32",
         position=from_node("N-B-BA-E", inch(8.625)), flip_hinge=False, flip_swing=True),
    # Used to be D-B-STAIR, opening into the workshop through W-B-CW2's concrete; on
    # 2026-07-30 the shaft's south 3'-0" became RM-B-BATH, so this leaf (same uid, same
    # 32" width — wheelchair-usable in a 3'-deep room) was rehung on the bathroom's north
    # partition instead. It swings OUTWARD by default on this wall (left-hand normal of
    # W-B-BA-N's west-to-east direction): inswing would sweep through the WC clearance zone,
    # the lavatory and the receptacle, all `integrity.door_swing_conflict` violations.
    # Positioned so jambs (x 12'-8"..15'-4") clear both fixtures' footprints.
    Door(uid="CBD207AAAA", tag="D-B-BATH", host="W-B-BA-N", type_ref="DT-INT-SWING32",
         position=from_node("N-B-BA-W", ft(3, 1.875)), flip_hinge=True),
    # ESS closet door, opening west into the furnace room. DT-INT-SWING24: a 2'-0" leaf is
    # what a closet this size takes with jamb both sides. 10" offset from the corner, not
    # the original 4": at 4" the opening's king stud clashed with the wall's corner post
    # (`structural.member_interference` against CBW125AAAA); 10" clears it, and the same 10"
    # is carried over to the new corner for the same reason. Measured from N-B-ESS-SW so the
    # leaf sits in the closet's south half and EQ-B-ESS-BATT, hung on the north concrete,
    # stands clear of the swing.
    Door(uid="CBD208AAAA", tag="D-B-ESS", host="W-B-ESS-W", type_ref="DT-INT-SWING24",
         position=from_node("N-B-ESS-SW", ft(1, 4))),
    Door(uid="CBD205AAAA", tag="D-B-SAUNA", host="W-B-SA-W", type_ref="DT-INT-SWING24",
         position=from_node("N-B-S1", ft(11))),
    # Raise the exterior threshold above the basement floor to resist sunken-garden flooding.
    # Hosted on the framed wall since 2026-08-28, and `sill_height` went inch(7) -> inch(0)
    # in the same edit — NOT because the threshold dropped, but because the datum did. A
    # sill is measured from the host wall's own base, and W-B-S3-FR's base is the top of
    # the 7 1/4" curb. The threshold is at the same absolute elevation it always was, a
    # quarter inch higher: the door now sits ON the curb rather than 7" up a pour with a
    # quarter inch of concrete still above it.
    Door(uid="CBD206AAAA", tag="D-B-PATIO", host="W-B-S3-FR", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-B-S2F", inch(10)), sill_height=inch(0), flip_swing=True),
    # WT-1424, down from WT-3660 (2026-07-30): a sauna wants a small window, less glass to
    # lose heat through. The 14" family's one appearance in a concrete wall, where the usual
    # 16" stud-module reason for that width doesn't apply — size is the point here. Retires
    # the last WT-3660 instance; the type and WT-3660-FIX stay in the catalog.
    # Sill 3'-8" (head 5'-8") as of 2026-08-21, up three 2 2/3" brick courses from 3'-0":
    # the veneer in front of it grew its cheap brown plinth from 9 courses to 12
    # (assemblies.py BASEMENT_BRICK_VENEER), and the window goes up with its reveal rather
    # than let the register band cut across the glass. Still well above the 18" bench top
    # (placeables.py).
    # Host and datum both moved 2026-08-28 with the framed walkout: W-B-S2-FR's base is
    # the curb top, 7 1/4" above the slab this sill used to be measured from, so ft(3, 8)
    # becomes inch(36.75). The glass does not move — the head stays where AO-B-BRICK-WIN's
    # arched reveal in front of it expects it, and that reveal is datumed off W-B-BRICK's
    # own base and needed no edit.
    # It also moved 9" east, 2'-6" -> 3'-3" off the corner, and that is the framed wall
    # asking rather than the design changing: a hole in a pour lands where you form it,
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
    # 3'-3" since 2026-08-28, following WIN-B-SAUNA onto its stud bay centre. The reveal
    # and the window it reveals must stay concentric; only the offset moved, and the
    # elevations did not (both sills still land at -65 7/16").
    RoughOpening(uid="CBO601AAAA", tag="AO-B-BRICK-WIN", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", ft(3, 3)),
                 width=inch(14), height=inch(20), sill_height=inch(37),
                 arch=Arch(rise=inch(2))),
    # Both reveals were taken down 6" at the head on 2026-08-21, on the eye rather than on a
    # rule: the door read 88" -> 84" -> 78", the window 26" -> 20". At 88" the door's crown
    # landed exactly on the gold register and its springline exactly on D-B-PATIO's 80 1/4"
    # head, so the arch had no brick above it and no haunch below it and read as one someone
    # had sawn off. 78" leaves 10" — nearly four courses — of lapis between crown and
    # register, and springs the arch at 70".
    #
    # Both reveals are therefore now SHORTER than the openings they front, and that is the
    # point, not a defect: a masonry reveal in front of a rectangular hole is meant to overlap
    # it. The door's head is covered across its full width and the sauna window loses its top
    # 6". Neither is a daylight or egress subject — WIN-B-SAUNA is not an emergency escape
    # opening and `egress.py` already excludes these arches by name — but if the sauna ever
    # wants that glass back, this height is the line to move, not the window.
    RoughOpening(uid="CBO602AAAA", tag="AO-B-BRICK-DOOR", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", ft(10, 6)),
                 width=ft(5), height=inch(78), sill_height=ft(0),
                 arch=Arch(rise=inch(8))),
]

ROOMS = [
    Room(uid="CBR401AAAA", tag="RM-B-FURNACE", seed=pt(ft(5), ft(30)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete"),
    # W-B-STR now separates this from the furnace room, so the stair bottom is its own
    # space instead of dumping arrivals into the mechanical room.
    Room(uid="CBR406AAAA", tag="RM-B-STAIR", seed=pt(ft(14), ft(30)),
         occupancy=Occupancy.STAIR, floor_finish="sealed-concrete"),
    # Stair-foot bathroom (2026-07-30): the shaft's south 3'-0", below the flight (ST-B2M's
    # bottom riser is at y=26'-0 3/8"). Clear face 7'-0" x 3'-0" (21 sf). Fixtures run
    # east-west, not facing the long wall: 3'-0" of depth can't fit a WC facing N/S (needs
    # 40"+ for bowl + IRC P2705.1 clearance), but fits one sideways in 36" — hence WC west,
    # lavatory east (plan/fixtures.py).
    #
    # Sheet vinyl, not tile (2026-09-02), joining the house's washable spine — RM-M-BATH1
    # and RM-M-LAUNDRY took the same move on 2026-08-25, RM-2-BATH on the second storey and
    # the attic studio's before that. 30.2 sf with no radiant zone under it, which is the
    # whole test: tile earns its cost where it is the emitter's mass (RM-M-BATH2 keeps its
    # tile for exactly that reason, at 98% of FH-M-BATH2's load). Here it buys grout to
    # keep, a backer board, a membrane and a threshold at the door, for a floor three feet
    # wide under a stair. Heat-welded sheet with a 6" integral flash cove that laps the wall
    # and dies behind the wall finish: floor and wall are one tray with no base joint, and
    # the cove IS the waterproofing — nothing impermeable goes under it.
    Room(uid="CBR407AAAA", tag="RM-B-BATH", seed=pt(ft(14), ft(20)),
         occupancy=Occupancy.BATHROOM, floor_finish="vinyl-sheet"),
    Room(uid="CBR402AAAA", tag="RM-B-WORKSHOP", seed=pt(ft(5), ft(8)),
         occupancy=Occupancy.UTILITY, floor_finish="sealed-concrete"),
    # No wall_lining override: the liner is part of SAUNA_2X4 / SAUNA_LINER_INT_2X6_BRG /
    # SAUNA_LINER_ON_GARDEN_FRAMED / SAUNA_LINER_ON_GARDEN_CURB. WET as of 2026-08-18, once
    # the south wall got the liner variant and the vapour control became continuous on all
    # four faces; it stayed continuous through the 2026-08-28 framing of the east and south
    # walls, which is why the curb under the south run carries the liner too.
    # `design_temperature_f` stays unset on purpose — it defaults to the 70 F setpoint, which
    # is what HumidityClass prescribes: a Glaser walk screens the daily mean, not the löyly
    # peak, and authoring 175 F would turn four passing rules into noise.
    # Honest about the margin: `glazing_dew_point` clears WIN-B-SAUNA by 2.5 F at
    # centre-of-glass (55.5 F inner glass vs a 53.1 F dew point at 70 F / 55% RH), and the
    # frame runs 5-8 F colder than that, so the frame does condense at design. That is an
    # accepted condition over a sealed, drained slab in a room that dries between sessions,
    # not a hidden failure.
    # The floor is SEALED CONCRETE, not tile (2026-08-25). SL-B-FLOOR already runs flat and
    # sloped 1/8"/ft to FX-B-SAUNA-FD under the whole room, and FX-B-SAUNA-SH is a curbed
    # liner pan — the pan brings its own waterproof floor, so nothing outside it needs a
    # tile bed. `integrity.concrete_finish_needs_concrete_deck` is satisfied by SL-B-FLOOR.
    # The tile that remains in this room is WP-B-SAUNA-SPLASH, the pan's two closed wall
    # sides; see the PANELING note below.
    # Ceiling: the same T&G-over-foil-polyiso liner as the walls (assemblies.py's
    # `_SAUNA_LINER`), restated rather than imported — the editable dialect cannot import
    # a sibling plan module. Keep the two in step by hand.
    Room(uid="CBR403AAAA", tag="RM-B-SAUNA", seed=pt(ft(14), ft(6)),
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
    # ESS closet (2026-08-02): MECHANICAL like the room it's carved from — STORAGE would
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

# No radiant floor in the basement. RM-B-SAUNA had FH-B-SAUNA until 2026-07-25: a heated
# floor under a room that already runs at 190 °F is heat with nowhere to go, and its stat
# had no honest place to read from (see the note that used to sit on ED-B-SAUNA-FH-STAT).
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
# W-B-CS runs from N-B-C1 (the shower corner), so its splash is the first 3'; W-B-SA-N
# runs west→east into that corner, so its splash is the last 3' of its 9'-2" run.
PANELING = [
    WallPaneling(uid="CBK901AAAA", tag="WP-B-SAUNA-SPLASH", room="RM-B-SAUNA",
                 material_ref="tile", height=ft(7, 6), replaces_wall_finish=True,
                 spans=(PanelingSpan(wall_ref="W-B-CS", start=ft(0), length=ft(3)),
                        PanelingSpan(wall_ref="W-B-SA-N", start=ft(6, 2), length=ft(3)))),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *SLABS, *FLOOR_OPENINGS,
            *PANELING]

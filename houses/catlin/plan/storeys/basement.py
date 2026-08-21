# haus: editable
# Basement — 12" concrete walkout box, 18' center grid, sauna, stair (WP3.1).
# South wall is the walkout side facing the sunken garden. Perimeter walls align on the
# concrete exterior face so the 4" of exterior XPS stacks directly under the framed
# wall's 4" polyiso+EPS (#43 control-layer continuity).
from typehaus import (
    Alarm,
    AlarmKind,
    Arch,
    Door,
    FloorOpening,
    FoundationWall,
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
# 16'-6" (south row). The 7'-0" shaft is the code-minimum well (two 3'-3 3/4" flights +
# 4 1/2" partition); W-B-STR at x=10' as 12" concrete satisfies both rows at once, since
# the 18' bearing grid fixes the shaft's east face at 17'-6".
NODES = [
    # Perimeter (split at grid lines + partition tees)
    Node(uid="CBN001AAAA", tag="N-B-SW", position=pt(ft(0), ft(0))),
    Node(uid="CBN002AAAA", tag="N-B-S1", position=pt(ft(8, 10), ft(0))),
    Node(uid="CBN003AAAA", tag="N-B-S2", position=pt(ft(18), ft(0))),
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
    # ESS closet (2026-08-02, notes/backup_power.md): takes the furnace room's SE corner, so
    # W-B-STR2/W-B-CW are already its east/south walls, and its north partition reuses
    # y=21'-9 3/8" (N-B-BA-W). x=6'-9" clears D-B-FURN's leaf (ends x=5'-8") and the last
    # W-B-CW sleeve (x=6'-6"), fixing the closet at 2'-8 1/4" clear — a cabinet, not a room.
    Node(uid="CBN017AAAA", tag="N-B-ESS-S", position=pt(ft(6, 9), ft(18))),
    Node(uid="CBN018AAAA", tag="N-B-ESS-N", position=pt(ft(6, 9), ft(21, 9.375))),
    # Glazed-brick veneer over the exposed south wall (W-B-BRICK): a freestanding wythe off
    # the concrete, both ends ``open_end`` like the sunken garden's N-SG-NW/NE (not part of
    # any wall loop). x runs only as far as the excavation in front of it: N-B-S1's x (8'-10")
    # to 28'-0" (params/sunken_garden.py's ``_x_ax_e``, where grade comes back up).
    # y is NOT 0'-0": the south walls' node line is the concrete face, and CATLIN_BASEMENT_12
    # carries 4.55" outboard of it (damp-proofing + 2" XPS + parge); the veneer stands off
    # that finished face, hence the -4.55". Wall aligns on face("air-gap-int") so the 1"
    # cavity begins exactly on the parge.
    Node(uid="CBN019AAAA", tag="N-B-BRICK-W", position=pt(ft(8, 10), inch(-4.55)),
         open_end=True),
    Node(uid="CBN020AAAA", tag="N-B-BRICK-E", position=pt(ft(28), inch(-4.55)),
         open_end=True),
]

WALLS = [
    # Perimeter foundation walls (12" + exterior XPS), CCW from SW corner.
    #
    # `lateral_support="top_and_bottom"` is the precondition for the prescriptive path, not a
    # detail: SL-B bears against the inside face at the bottom and FS-MAIN's diaphragm ties
    # the top, so IRC Table R404.1.2(8) applies (its footnote g presumes exactly this) rather
    # than R404.1.1 sending a wall retaining more than 48" to an engineered design. Stated on
    # each wall because the check refuses to assume it — assuming bracing is the unsafe
    # direction. With it, 12" at 45 psf/ft on a 9' storey retaining 9' reads NR: no vertical
    # reinforcement required at all. (Horizontal steel is a separate table, R404.1.2(1) —
    # one #4 within 12" of the top and one at third points above 8' — not screened here.)
    FoundationWall(uid="CBW101AAAA", tag="W-B-S1", start_node="N-B-SW",
                   end_node="N-B-S1", assembly="CATLIN_BASEMENT_12_GARDEN",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    # The sauna's south side. W-B-S1 and W-B-S3 stay on the bare garden wall deliberately —
    # they bound the workshop and the patio side — but this one segment is a room face in a
    # WET room, so it carries the liner variant of the same stack
    # (SAUNA_LINER_ON_BASEMENT_12_GARDEN): the vapour control has to be continuous on all
    # four faces or it is not vapour control. The liner grows 3 1/2" inward and mitres to
    # W-B-CS's at N-B-S2 — same assembly family, so no derived return there.
    # Alignment stays `face("concrete-ext")` with NO offset, unlike W-B-CS's inch(-6):
    # `_face_offset_from_interior` falls through the three liner layers (no name match) and
    # returns the concrete's outboard face, which on this wall *is* the datum, so the
    # concrete band stays at y 0"-12" exactly as the bare garden segments do. W-B-CS needs
    # its offset only to re-centre the concrete on the 18' bearing grid.
    FoundationWall(uid="CBW102AAAA", tag="W-B-S2", start_node="N-B-S1",
                   end_node="N-B-S2", assembly="SAUNA_LINER_ON_BASEMENT_12_GARDEN",
                   alignment=face("concrete-ext"),
                   interior_room="RM-B-SAUNA",
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW103AAAA", tag="W-B-S3", start_node="N-B-S2",
                   end_node="N-B-SE", assembly="CATLIN_BASEMENT_12_GARDEN",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW104AAAA", tag="W-B-E1", start_node="N-B-SE",
                   end_node="N-B-E1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW105AAAA", tag="W-B-E2", start_node="N-B-E1",
                   end_node="N-B-NE", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW106AAAA", tag="W-B-N1", start_node="N-B-NE",
                   end_node="N-B-N1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW107AAAA", tag="W-B-N2", start_node="N-B-N1",
                   end_node="N-B-N2", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW108AAAA", tag="W-B-N3", start_node="N-B-N2",
                   end_node="N-B-NW", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW109AAAA", tag="W-B-W1", start_node="N-B-NW",
                   end_node="N-B-W1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    FoundationWall(uid="CBW110AAAA", tag="W-B-W2", start_node="N-B-W1",
                   end_node="N-B-SW", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4),
                   lateral_support="top_and_bottom"),
    # Center cross walls (12" concrete) — the 18' bearing grid. Every wall from here down is
    # an *interior* cross wall with soil on neither side, so `unbalanced_fill=ft(0)` says so
    # explicitly — without it `structural.foundation_unbalanced_fill` would read these eight
    # as retaining 9' of backfill apiece.
    #
    # This segment is the sauna's east boundary, carrying the liner stack directly on the
    # concrete. Aligned on the concrete's far face so the bearing grid stays put and the
    # liner grows into the sauna.
    FoundationWall(uid="CBW111AAAA", tag="W-B-CS", start_node="N-B-C1",
                   end_node="N-B-S2", assembly="SAUNA_LINER_ON_CONCRETE", unbalanced_fill=ft(0),
                   alignment=face("concrete-ext", offset=inch(-6)),
                   interior_room="RM-B-SAUNA",
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4)),
    FoundationWall(uid="CBW112AAAA", tag="W-B-CS2", start_node="N-B-C1",
                   end_node="N-B-C", assembly="CATLIN_CONC_12_INT", unbalanced_fill=ft(0),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4)),
    # Split at N-B-BA-E (2026-07-30) so the bathroom's north partition tees onto a shared
    # node — else `integrity.wall_loop_open` reads it as a free end. W-B-CN keeps the tag,
    # uid, and the north 14'-2 5/8" that W-M-C5 stacks on, so the bearing stack is untouched.
    FoundationWall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-BA-E",
                   end_node="N-B-N1", assembly="CATLIN_CONC_12_INT", unbalanced_fill=ft(0),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4)),
    FoundationWall(uid="CBW121AAAA", tag="W-B-CN2", start_node="N-B-C",
                   end_node="N-B-BA-E", assembly="CATLIN_CONC_12_INT", unbalanced_fill=ft(0),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4)),
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
    # Tops are the basement's own 8'-2 3/4" clear, not the 0'-0" the concrete ran to: a stud
    # wall that reaches the floor datum stands *inside* the joists, which is what
    # `structural.member_interference` reported on W-B-STR2 the moment it was framed. Where
    # a wall above stacks on one of these, `resolve/platform.py` grows the wall solid up to
    # meet it and leaves the double top plate here, which is what platform framing is.
    #
    # Split at the stair shaft's west wall so the shaft is a real tee, not a wall end. Also
    # split at N-B-ESS-S (2026-08-02) for the ESS closet's west partition, the same move
    # W-B-STR made for the bathroom. W-B-CW keeps tag/uid and the west 6'-9" (D-B-FURN
    # unchanged); W-B-CW3 is the 3'-3" stub forming the closet's south wall.
    #
    # W-B-CW is the furnace room's south wall and carries the 4" building drain, so it takes
    # the wet-wall 2x6 rather than a 2x4.
    Wall(uid="CBW114AAAA", tag="W-B-CW", start_node="N-B-W1",
         end_node="N-B-ESS-S", assembly="INT_2X6_PLUMBING", top=ft(8, 2.75)),
    # Matched to the ESS closet's other two walls (W-B-ESS-N/W-B-ESS-W), which are the
    # steel-stud, type-X box the battery enclosure asks for.
    Wall(uid="CBW123AAAA", tag="W-B-CW3", start_node="N-B-ESS-S",
         end_node="N-B-STR", assembly="INT_ESS_CLOSET_STEEL", top=ft(8)),
    # Nothing runs in this one and nothing bears on it — a plain 2x4 partition. Keep the
    # tag: W-M-CLN and W-M-CLN2 name it in `stacks_on`.
    Wall(uid="CBW119AAAA", tag="W-B-CW2", start_node="N-B-STR",
         end_node="N-B-C", assembly="INT_2X4_PARTITION", top=ft(8, 2.75)),
    # The playroom's south wall, 18'-0" of it, and the one that keeps D-B-PLAY (the 5'-0"
    # glazed double). Staggered studs: it is the long wall between the playroom and the gym,
    # and it also runs under the concrete band, so it wants the sound break.
    Wall(uid="CBW115AAAA", tag="W-B-CE", start_node="N-B-C",
         end_node="N-B-E1", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8, 2.75)),
    # Stair shaft's west wall — 12" concrete on x=10', full north-row depth (reference:
    # "Stairway 7' x 16' 6 1/2""). 12" (not 8") puts the shaft's west face at 9'-6", giving
    # both the furnace room's 8'-6" clear and the shaft's 7'-0" off the same wall.
    # Split at N-B-BA-W (2026-07-30): W-B-STR keeps tag/uid and the north 14'-2 5/8" that
    # W-M-STRW/W-M-STRW2 stack on; W-B-STR2 is the 3'-9 3/8" stub alongside the bathroom,
    # carrying its three ceiling-level service crossings (plan/mep.py's WALL_SLEEVES).
    #
    # **This one stayed concrete through the 2026-08-21 overhaul**, alone on the interior.
    # Three things are measured off its east face at x=10'-6" and all three break if the
    # wall narrows to a 6 3/4" stud line on the same node: the shaft's 7'-0" (two 3'-3 3/4"
    # flights plus the 4 1/2" well partition, exactly), ST-B2M's own flight width, and
    # FO-M-STAIR's west edge — which since the deck became joists is a real bearing edge,
    # and off this wall would take a 9'-0" engineered header instead
    # (structural.floor_opening_header). It is also a two-storey bearing line
    # (W-M-STRW/W-M-STRW2 stack on it) and keeps FT-B-STR either way, so framing it would
    # have bought only its own ~4.9 cy and cost the stair its dimensions.
    FoundationWall(uid="CBW116AAAA", tag="W-B-STR", start_node="N-B-N2",
                   end_node="N-B-BA-W", assembly="CATLIN_CONC_12_INT", unbalanced_fill=ft(0),
                   top_elevation=ft(0), bottom_elevation=ft(-9, -4)),
    # The stub south of it is a different job: RM-B-BATH's west enclosure, nothing bearing
    # on it, nothing dimensioned off it. It is *also* the ESS closet's east wall, and that
    # is what picks the assembly — `advisory.ess_enclosure` wants 5/8" Type X on the closet
    # face, which 12" of concrete satisfied by being concrete and a staggered-stud wet wall
    # would not. So it joins its two neighbours (W-B-ESS-W/W-B-ESS-N) in the steel-stud
    # Type X box instead of matching W-B-BA-N: a battery closet's rating beats a sound break
    # between a bathroom and an unoccupied cupboard. Its three ceiling-level crossings
    # (vent, hot, cold) are bored, not cast, now that there is no pour to cast into.
    Wall(uid="CBW122AAAA", tag="W-B-STR2", start_node="N-B-BA-W",
         end_node="N-B-STR", assembly="INT_ESS_CLOSET_STEEL", top=ft(8)),
    # Sauna partitions — SAUNA_2X4 carries the hot-side liner (T&G/furring/foil-faced
    # polyiso) as part of the wall type, not a room finish override; the east wall (center
    # concrete) takes it via SAUNA_LINER_ON_CONCRETE. Both are interior partitions, so
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
    # Top=8'-0" is SL-M-DECK's 8'-3" underside less 3" for the vent to turn over the plate.
    Wall(uid="CBW120AAAA", tag="W-B-BA-N", start_node="N-B-BA-W",
         end_node="N-B-BA-E", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8),
         interior_room="RM-B-BATH"),
    # ESS closet's two framed walls (2026-08-02). INT_ESS_CLOSET_STEEL (steel studs, 5/8"
    # Type X both faces) is an owner standard, not a code-rated assembly, hence
    # `advisory.ess_enclosure` being advisory (see plan/assemblies.py). `top=ft(8)` matches
    # W-B-BA-N's plate line on the other side of the concrete so the two partitions read as
    # one line in section; `interior_room` on both keeps the Type X face unambiguous.
    Wall(uid="CBW124AAAA", tag="W-B-ESS-W", start_node="N-B-ESS-S",
         end_node="N-B-ESS-N", assembly="INT_ESS_CLOSET_STEEL", top=ft(8),
         interior_room="RM-B-ESS"),
    Wall(uid="CBW125AAAA", tag="W-B-ESS-N", start_node="N-B-ESS-N",
         end_node="N-B-BA-W", assembly="INT_ESS_CLOSET_STEEL", top=ft(8),
         interior_room="RM-B-ESS"),
    # Glazed forest-green brick veneer over the exposed run of W-B-S2/W-B-S3, where the
    # sunken garden is dug against them — everywhere else this wall is buried and the parge
    # is a below-grade coating nobody sees; here it's the house's most-looked-at elevation.
    #
    # Bottom at -8'-5", NOT -9' with the concrete it faces: (1) there's no ground left for a
    # footing at -9' — FT-B-S2/FT-B-S3 already project 10" south, so the veneer bears on the
    # house footing's own toe via a shallow plinth (FT-B-BRICK) cast on it, not poured
    # beside it; (2) that plinth has to clear D-B-PATIO's 7" raised threshold, which is also
    # the better detail — a glazed veneer's base course should not sit in standing water.
    # The plinth shows 3.5" above the garden slab (-8'-8.5") as a concrete water table.
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
                   top_elevation=ft(0), bottom_elevation=ft(-8, -9)),
]

OPENINGS = [
    # Interior circulation
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT-SWING32",
         position=from_node("N-B-W1", ft(3))),
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT-FRENCH60",
         position=from_node("N-B-C", ft(6))),
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
         position=from_node("N-B-BA-E", inch(8.625))),
    # Used to be D-B-STAIR, opening into the workshop through W-B-CW2's concrete; on
    # 2026-07-30 the shaft's south 3'-0" became RM-B-BATH, so this leaf (same uid, same
    # 32" width — wheelchair-usable in a 3'-deep room) was rehung on the bathroom's north
    # partition instead. It swings OUTWARD by default on this wall (left-hand normal of
    # W-B-BA-N's west-to-east direction): inswing would sweep through the WC clearance zone,
    # the lavatory and the receptacle, all `integrity.door_swing_conflict` violations.
    # Positioned so jambs (x 12'-8"..15'-4") clear both fixtures' footprints.
    Door(uid="CBD207AAAA", tag="D-B-BATH", host="W-B-BA-N", type_ref="DT-INT-SWING32",
         position=from_node("N-B-BA-W", ft(2, 8))),
    # ESS closet door, opening into the furnace room. DT-INT-SWING24: a 2'-0" leaf is what
    # the 2'-8 1/4" clear closet can take with jamb both sides. 10" offset, not the original
    # 4": at 4" the opening's king stud clashed with the wall's corner post
    # (`structural.member_interference` against CBW125AAAA); 10" clears it.
    Door(uid="CBD208AAAA", tag="D-B-ESS", host="W-B-ESS-N", type_ref="DT-INT-SWING24",
         position=from_node("N-B-ESS-N", inch(10))),
    Door(uid="CBD205AAAA", tag="D-B-SAUNA", host="W-B-SA-W", type_ref="DT-INT-SWING24",
         position=from_node("N-B-S1", ft(10, 10.4375))),
    # Raise the exterior threshold above the basement floor to resist sunken-garden flooding.
    Door(uid="CBD206AAAA", tag="D-B-PATIO", host="W-B-S3", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-B-S2", ft(1, 4)), sill_height=inch(7), flip_swing=True),
    # WT-1424, down from WT-3660 (2026-07-30): a sauna wants a small window, less glass to
    # lose heat through. The 14" family's one appearance in a concrete wall, where the usual
    # 16" stud-module reason for that width doesn't apply — size is the point here. Sill
    # stays 3'-0" (head 8'-0" -> 5'-0"), well above the 18" bench top (placeables.py). Retires
    # the last WT-3660 instance; the type and WT-3660-FIX stay in the catalog.
    Window(uid="CBX301AAAA", tag="WIN-B-SAUNA", host="W-B-S2",
           type_ref="WT-1424-T", position=from_node("N-B-S1", ft(2, 6)),
           sill_height=ft(3)),
    # --- reveals through the brick veneer -------------------------------------------
    # WIN-B-SAUNA and D-B-PATIO stay on the concrete walls; these are RoughOpenings for the
    # holes the wythe in front of them needs, each with its own segmental brick arch — not a
    # duplicate Window/Door, which would double the schedule and takeoff.
    # Positioned off N-B-BRICK-W (shares N-B-S1's x). Segmental, not semicircular: the
    # rise is ~1/7 of clear width; ``height`` includes that rise so the springline
    # lands on the real head. ``sill_height`` is re-datumed off W-B-BRICK's own base
    # (-8'-5", not -9'): the window's 3'-0" becomes 2'-5", the door's 7" threshold becomes 0.
    RoughOpening(uid="CBO601AAAA", tag="AO-B-BRICK-WIN", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", ft(2, 6)),
                 width=inch(14), height=inch(26), sill_height=inch(29),
                 arch=Arch(rise=inch(2))),
    # 84", not the 88" this was authored at (2026-08-21). At 88" the crown landed exactly on
    # the gold register at 88" and the springline exactly on D-B-PATIO's 80 1/4" head, so the
    # arch had no brick above it and no haunch below it and read as an arch someone had sawn
    # off. Dropping 4" puts the crown 4" (1 1/2 courses) clear under the register and springs
    # the arch at 76", which does cross D-B-PATIO's top corners — accepted: a masonry reveal
    # in front of a rectangular door is meant to overlap it, and the alternative is either a
    # flattened arch or a register band that no longer sits on the door head line.
    RoughOpening(uid="CBO602AAAA", tag="AO-B-BRICK-DOOR", host="W-B-BRICK",
                 position=from_node("N-B-BRICK-W", ft(10, 6)),
                 width=ft(5), height=inch(84), sill_height=ft(0),
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
    Room(uid="CBR407AAAA", tag="RM-B-BATH", seed=pt(ft(14), ft(20)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CBR402AAAA", tag="RM-B-WORKSHOP", seed=pt(ft(5), ft(8)),
         occupancy=Occupancy.UTILITY, floor_finish="sealed-concrete"),
    # No wall_lining override: the liner is part of SAUNA_2X4 / SAUNA_LINER_ON_CONCRETE /
    # SAUNA_LINER_ON_BASEMENT_12_GARDEN. WET as of 2026-08-18, once W-B-S2 got the liner
    # variant and the vapour control became continuous on all four faces.
    # `design_temperature_f` stays unset on purpose — it defaults to the 70 F setpoint, which
    # is what HumidityClass prescribes: a Glaser walk screens the daily mean, not the löyly
    # peak, and authoring 175 F would turn four passing rules into noise.
    # Honest about the margin: `glazing_dew_point` clears WIN-B-SAUNA by 2.5 F at
    # centre-of-glass (55.5 F inner glass vs a 53.1 F dew point at 70 F / 55% RH), and the
    # frame runs 5-8 F colder than that, so the frame does condense at design. That is an
    # accepted condition over a tiled, drained floor in a room that dries between sessions,
    # not a hidden failure.
    Room(uid="CBR403AAAA", tag="RM-B-SAUNA", seed=pt(ft(14), ft(6)),
         occupancy=Occupancy.BATHROOM, humidity_class=HumidityClass.WET,
         floor_finish="tile"),
    Room(uid="CBR404AAAA", tag="RM-B-PLAY-N", seed=pt(ft(27), ft(27)),
         occupancy=Occupancy.MEDIA, floor_finish="carpet"),
    Room(uid="CBR405AAAA", tag="RM-B-GYM", seed=pt(ft(27), ft(9)),
         occupancy=Occupancy.LIVING, floor_finish="rubber"),
    # ESS closet (2026-08-02): MECHANICAL like the room it's carved from — STORAGE would
    # trigger habitability rules a battery cabinet has no use for. R327.4 permits an ESS in
    # a utility closet, which is exactly what this is.
    Room(uid="CBR408AAAA", tag="RM-B-ESS", seed=pt(ft(8, 6), ft(20)),
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
# that bills as tile and is subtracted from the SAUNA assemblies' sauna-tg liner area.
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

# haus: editable
# Main floor — 36'x36' at sheathing, 16" o.c. module, east half open living (WP3.1).
# Exterior walls: CATLIN_EXT_2X6, sheathing exterior face on the 0/36 lines.
# Bearing lines: west wall, center N-S wall (x=18), east wall (18' I-joist spans, E-W).
# Windows follow the stud-bay rules: WT-1424 fits one bay unbroken; WT-3048 breaks two
# studs (non-bearing walls only, RO centred on a bay centre); WT-2736 adds jacks on
# bearing walls (RO centred on a stud line).
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    Connector,
    ConnectorKind,
    Door,
    DoorType,
    FloorHeat,
    FloorOpening,
    Node,
    Occupancy,
    RadiantSystem,
    Railing,
    RailingKind,
    Room,
    Slab,
    Stair,
    StructuralRole,
    Wall,
    WallPaneling,
    Window,
    WindowType,
    face,
    from_node,
    ft,
    in_slab,
    inch,
    pt,
    u_us,
)

# --- library-of-the-house types ----------------------------------------------
DOOR_TYPES = [
    DoorType(tag="DT-EXT-SWING36", width=ft(3), height=ft(6, 8), exterior=True,
             u_factor=u_us(0.20)),
    # Every glazed door in the house is tempered (2026-08-01, code.R308_4_safety_glazing).
    # R308.4.1 has no location test to fail: glazing *in a door* is a hazardous location by
    # definition, so this is a property of the product wherever it is hung — which is why it
    # is set on the four glazed types below and needs no tempered variant of any of them.
    DoorType(tag="DT-EXT-FRENCH60", width=ft(5), height=ft(6, 8), exterior=True,
             operation="double_swing", glazed=True, tempered=True, u_factor=u_us(0.20)),
    DoorType(tag="DT-EXT-SLIDE60", width=ft(5), height=ft(6, 8), exterior=True,
             operation="slide", glazed=True, tempered=True, u_factor=u_us(0.25)),
    DoorType(tag="DT-INT-SWING32", width=ft(2, 8), height=ft(6, 8)),
    DoorType(tag="DT-INT-SWING30", width=ft(2, 6), height=ft(6, 8)),
    DoorType(tag="DT-INT-SWING30-GLAZED", width=ft(2, 6), height=ft(6, 8), glazed=True,
             tempered=True),
    # Frameless jamb system (no applied casing — drywall return jamb), flush with the gwb.
    DoorType(tag="DT-INT-SWING30-TRIMLESS", width=ft(2, 6), height=ft(6, 8), trimless=True),
    DoorType(tag="DT-INT-SWING24", width=ft(2), height=ft(6, 8)),
    DoorType(tag="DT-INT-BIFOLD60", width=ft(5), height=ft(6, 8), operation="bifold"),
    DoorType(tag="DT-INT-BIFOLD56", width=ft(4, 8), height=ft(6, 8), operation="bifold"),
    # RM-M-MUD-CLOSET's bypass pair (2026-08-02): no floor for a swing, same reasoning as
    # FURN-WARDROBE-48. 48" is the largest standard bypass whose RO (50") still fits the
    # partition's 63 1/8" framed span with jamb packs to spare — 60" would leave 1 1/8" total.
    DoorType(tag="DT-INT-BYPASS48", width=ft(4), height=ft(6, 8), operation="slide"),
    DoorType(tag="DT-INT-FRENCH60", width=ft(5), height=ft(6, 8),
             operation="double_swing", glazed=True, tempered=True),
    DoorType(tag="DT-EXT-OVERHEAD192", width=ft(16), height=ft(7), exterior=True,
             operation="overhead"),
]
# One size per width family: every placement shares one height, the tallest that still
# fits the family's most constrained wall in the house. The 42" family (old WT-4242 twin
# for the raked gables) is gone as of 2026-08-01, replaced by WT-1424 there and by WT-3048
# for the south glazing. WT-1864 (18") is a deliberate fifth family, added 2026-07-31 for
# the attic's south juliet pair — no committed height gives that tall/narrow proportion.
#
# Two deliberate exceptions to "one height per family", both 2026-08-01, each because a
# fresh width family costs more than a second height does: WT-1448 (the 4:12 rake forbids
# any width over 14", which takes a header that hits the rake — see WT-1448's own note) and
# WT-3048 (the 30" family's committed 36" height would drop the south head off the shared
# 6'-8" door-head line).
WINDOW_TYPES = [
    # 14" RO — falls between studs on the 16" grid without breaking a stud line, so it
    # frames with no header, no jacks and no kings. 24" tall because the 5' attic knee
    # walls (WIN-A-W-S/W-N, WIN-A-E-S/E-N) have only that much room under the top plate
    # — the same 24" is what lets this size duck under the 4:12 south rake as well.
    # That combination makes it the house's fallback wherever a bigger unit will not go.
    WindowType(tag="WT-1424", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="awning"),
    # 14" RO, 48" tall — the south gable's flanker size (2026-08-01), and the one deliberate
    # break of "one height per family". WT-1864 (18") doesn't fit: it breaks a stud, taking a
    # 5.5"-deep header that at the nearest usable stud line (x 8'-0"/28'-0") clashes with the
    # 4:12 roof underside by 1.8". 14" lands wholly inside a bay so no header forms, and the
    # 6'-8" head (the main storey's head line) clears the rake by 2'-0". Casement, not
    # WT-1424's awning: a 48"-tall leaf is past what an awning projects.
    WindowType(tag="WT-1448", width=inch(14), height=ft(4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 18" RO — the attic gable's juliet size (2026-07-31, narrowed from a 32" tilt-turn the
    # same day). One stud broken, centred on a STUD LINE (cheap frame, and what lets the
    # pair sit 32" apart instead of 48"). 64" tall is a proportion choice, not a clearance
    # one — head lands at 8'-0" with the storey's 2'-8" sill, well clear of the rake.
    # Casement, not tilt-turn: 18" is below tilt-turn hardware's minimum frame width.
    WindowType(tag="WT-1864", width=inch(18), height=ft(5, 4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 27" RO — bearing-wall size (N*2-9): one stud broken, jacks added. 36" tall
    # because the garage's 8' wall can't take a 60" height at a 42" sill (header would
    # land above the top plate). 27x36 still clears R310 egress (6.75 sf > 5.7).
    WindowType(tag="WT-2736", width=inch(27), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 30" RO — non-load-bearing size (N*2-6): one stud broken. 36" tall keeps the
    # attic-gable heads below the cathedral-roof framing. Since the 2026-07-30 south
    # enlargement this is the north-side size (attic gable pair, hall).
    WindowType(tag="WT-3036", width=inch(30), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 30" RO — the south-glazing size, narrowed from the 42" WT-4248 (2026-08-01). One stud
    # broken, not two: the module's ideal position moves with RO width, so the four facade
    # columns moved 8" inboard with it (3'-4"/8'-8" -> 4'-0"/9'-4", 28'-0"/33'-4" ->
    # 27'-4"/32'-8"); head line and storey stacking are untouched. Second deliberate break of
    # "one height per family" (see WT-1448) — WT-3036's 36" would drop the head off the
    # shared 6'-8" door-head line. Non-bearing walls only (preferences [framing]).
    WindowType(tag="WT-3048", width=inch(30), height=ft(4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 36" RO — concrete basement wall only (no stud module to respect down there).
    # Catalog-only since 2026-07-30: WIN-B-SAUNA was its last instance and took WT-1424.
    # Kept as an available product for the next basement opening rather than deleted.
    WindowType(tag="WT-3660", width=ft(3), height=ft(5), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # Same unit, same glass, no sash: a picture window for the openings that are there for
    # daylight and view only. It is a separate *type* rather than a note on WT-3660 because
    # a fixed unit is a different product on the quote and carries no ventilation or egress
    # credit — the existing tags stay as they are, since they are referenced house-wide.
    WindowType(tag="WT-3660-FIX", width=ft(3), height=ft(5), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="fixed"),
    # The mudroom's picture unit: same 14" RO / 24" tall glass as WT-1424 (still the one
    # size that clears a 16" stud bay unbroken), no sash — it is there for daylight over
    # the bench, not ventilation. A separate type for the same reason WT-3660-FIX is
    # separate from WT-3660: fixed vs. operable is a different product on the schedule.
    WindowType(tag="WT-1424-FIX", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="fixed"),
    # --- tempered twins (2026-08-01, code.R308_4_safety_glazing) ----------------------
    # Four types, identical to their parent but for the glass — R308.4 makes a *location*
    # hazardous (wet room, within 24" of a door, within 60" of a stair), so only the unit
    # that lands there gets tempered. Not new width families; no facade/framing rule sees
    # them. Adding a tempered unit is a retype, never a move.
    WindowType(tag="WT-1424-T", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="awning", tempered=True),
    WindowType(tag="WT-2736-T", width=inch(27), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement", tempered=True),
    WindowType(tag="WT-3036-T", width=inch(30), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement", tempered=True),
    WindowType(tag="WT-3048-T", width=inch(30), height=ft(4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement", tempered=True),
    # --- high-performance twins (2026-08-18, building_science.glazing_dew_point) -------
    # Three types for the plant room, identical in every dimension to their parents and
    # differing only in the glass package: triple/low-e at U-0.14 with a warm-edge spacer
    # and a thermally broken frame. Exactly the `-T` precedent one line up — adding a
    # better unit is a RETYPE, never a move, so no facade column, no header, no framing
    # module and no stud line changes.
    #
    # This is not gold-plating, it is the room's only way to have glass at all. At 75 F /
    # 70% RH the dew point is 64.4 F. A U-0.25 unit's centre of glass sits at 59.7 F at the
    # -15 F design temperature and condenses below about +13 F outdoors — most of a
    # Minnesota winter. U-0.14 puts it at 66.4 F, dry to roughly -35 F, which narrows the
    # residual problem to the frame and the edge of glass (5-8 F colder than centre) —
    # which is what the warm-edge spacer, the glass-wash throw off REG-S-HP-PLANT and the
    # drained sill pans are there to handle.
    #
    # SHGC is deliberately unchanged at 0.35: this room is south-glazed for plants, and a
    # triple unit that bought its U with a low SHGC would take the light the room exists
    # for. VT likewise.
    WindowType(tag="WT-2736-HP", width=inch(27), height=ft(3), u_factor=u_us(0.14),
               shgc=0.35, vt=0.5, operation="casement",
               source="notes/plant_room.md — WT-2736 dimensions, triple/low-e warm-edge thermally broken frame at U-0.14 for RM-S-PLANT"),
    WindowType(tag="WT-3048-HP", width=inch(30), height=ft(4), u_factor=u_us(0.14),
               shgc=0.35, vt=0.5, operation="casement",
               source="notes/plant_room.md — WT-3048 dimensions at U-0.14 for RM-S-PLANT"),
    # WIN-S-PLANT2 sits within 24" of D-S-DECK-W, so R308.4 makes its location hazardous
    # regardless of what the glass costs: it needs the tempered pane AND the U-0.14 package,
    # which is a fourth product, not a choice between the two.
    WindowType(tag="WT-3048-HP-T", width=inch(30), height=ft(4), u_factor=u_us(0.14),
               shgc=0.35, vt=0.5, operation="casement", tempered=True,
               source="notes/plant_room.md — WT-3048-HP with tempered glazing for WIN-S-PLANT2 (R308.4, within 24\" of D-S-DECK-W)"),
]

NODES = [
    # Perimeter (splits mirror the basement + partition tees)
    Node(uid="CMN001AAAA", tag="N-M-SW", position=pt(ft(0), ft(0))),
    Node(uid="CMN002AAAA", tag="N-M-S1", position=pt(ft(18), ft(0))),
    Node(uid="CMN003AAAA", tag="N-M-SE", position=pt(ft(36), ft(0))),
    Node(uid="CMN004AAAA", tag="N-M-E1", position=pt(ft(36), ft(18))),
    Node(uid="CMN005AAAA", tag="N-M-NE", position=pt(ft(36), ft(36))),
    Node(uid="CMN006AAAA", tag="N-M-N1", position=pt(ft(18), ft(36))),
    Node(uid="CMN007AAAA", tag="N-M-N2", position=pt(ft(10), ft(36))),
    Node(uid="CMN008AAAA", tag="N-M-NW", position=pt(ft(0), ft(36))),
    Node(uid="CMN009AAAA", tag="N-M-W1", position=pt(ft(0), ft(26, 4))),
    # W-M-HS1..4 pushed 6" north to y=22'-2" (2026-07-29) for BATH2 shower/tub depth.
    # Both west-wall tees moved again 2026-08-15 for the residue rule: W-M-W4/W-M-W3 lay
    # studs out from N-M-W3/N-M-W2, and at 13'-4"/22'-2" that grid was 4"/2" out of phase
    # (mod 16") with the second storey's tees at 9'-0"/22'-4". Moving to 13'-0"/22'-4"
    # (both 12" mod 16") lets four windows column between storeys (WIN-M-BED-W1/W2/BATH2
    # below). Every node on each partition line must move together or it kinks — including
    # boxes/risers that hang on them, checked only by
    # test_wall_mounted_devices_resolve_against_a_wall_face. Cost: RM-M-BED loses 4" depth,
    # RM-M-BATH2 gains 6", hall goes 3'-8" -> 3'-6" (still clear of R311.6).
    Node(uid="CMN010AAAA", tag="N-M-W2", position=pt(ft(0), ft(22, 4))),
    Node(uid="CMN011AAAA", tag="N-M-W3", position=pt(ft(0), ft(13))),
    # Center bearing line ties
    Node(uid="CMN012AAAA", tag="N-M-C1", position=pt(ft(18), ft(13))),
    Node(uid="CMN013AAAA", tag="N-M-C2", position=pt(ft(18), ft(22, 4))),
    # N-M-C3 moved south to the stair wall's line (2026-07-28): with W-M-C4/C4B gone, it's
    # now BM-M-HALL's north bearing and W-M-C5's south end. `open_end` is honest here since
    # BM-M-HALL, not another wall, carries the centre line south of it.
    Node(uid="CMN014AAAA", tag="N-M-C3", position=pt(ft(18), ft(25, 10)), open_end=True),
    # Interior tees
    # N-M-STR1 and N-M-C3B moved north from y=25'-0" to y=25'-10" with W-M-STRS (2026-07-28),
    # and N-M-C3B then retired into N-M-C3: with the centre line open between them they were
    # two names for the same point. 25'-10" is as far north as the stair wall can go — see
    # FLOOR_OPENINGS.
    Node(uid="CMN015AAAA", tag="N-M-STR1", position=pt(ft(10), ft(25, 10))),
    # W-M-STRS's east end (2026-07-30): the stair well partition's east face, which is also
    # ST-B2M's and ST-M2S's east-lane west edge. The wall stops here so it frames the
    # partition and D-M-STAIR and no further.
    Node(uid="EPWDU4M7Y2", tag="N-M-STR2", position=pt(ft(14, 2.25), ft(25, 10)),
         open_end=True),
    # W-M-STOS2's tee into the stair wall line, and therefore the W-M-STRW/W-M-STRW2 split.
    Node(uid="CMN024AAAA", tag="N-M-STRJ", position=pt(ft(10), ft(26, 4))),
    # W-M-BAE shifts 2' east (2026-07-28); the mudroom door remains at its existing
    # 6" tee clearance.
    Node(uid="CMN016AAAA", tag="N-M-BA1", position=pt(ft(6), ft(26, 4))),
    Node(uid="CMN017AAAA", tag="N-M-BA2", position=pt(ft(6), ft(22, 4))),
    Node(uid="CMN018AAAA", tag="N-M-D1", position=pt(ft(8), ft(22, 4))),
    # The closet/laundry line moved north 8" (y 17'-4" -> 18'-0", 2026-08-03), taking
    # W-M-CLN/CLN2 with it. Costs 8" each off RM-M-LAUNDRY and RM-M-STUDY; bounded by
    # FX-M-LAUNDRY (40" deep, room now 48 3/4" clear). Bonus: y=18'-0" is also where the
    # basement's 12" cast wall W-B-CW2 runs, so the partition now lands on solid concrete.
    Node(uid="CMN019AAAA", tag="N-M-D2", position=pt(ft(8), ft(18))),
    Node(uid="CMN020AAAA", tag="N-M-D3", position=pt(ft(8), ft(13))),
    Node(uid="CMN021AAAA", tag="N-M-E2", position=pt(ft(13, 4), ft(18))),
    Node(uid="CMN022AAAA", tag="N-M-E3", position=pt(ft(13, 4), ft(22, 4))),
    Node(uid="CMN023AAAA", tag="N-M-E4", position=pt(ft(18), ft(18))),
    # RM-M-MECH: the framed MEP shaft closet in the house's NW corner (2026-07-28),
    # replacing FURN-M-MUD-CLOSET-N. 6' wide (west wall to 6" shy of D-M-ENTRY's far
    # jamb at 6'-6") x 2'-8" deep — the radon+plumbing chase rides its SW corner, aligned
    # with the matching notch moved into RM-S-BATH1's NW corner directly above it.
    Node(uid="CMN025AAAA", tag="N-M-MECH1", position=pt(ft(0), ft(33, 4))),
    Node(uid="CMN026AAAA", tag="N-M-MECH2", position=pt(ft(6), ft(33, 4))),
    Node(uid="CMN027AAAA", tag="N-M-MECH3", position=pt(ft(6), ft(36))),
    # RM-M-MUD-CLOSET: framed south mudroom closet (2026-08-02), replacing
    # FURN-M-MUD-CLOSET-S. Axis y=29'-7 1/2" satisfies two constraints at once: interior
    # depth of 34 3/4" (inside the 32"-36" reach-in band) and clearing FURN-M-MUD-BENCH's
    # south end by 1/8". East end reuses N-M-BA1's x=6' line to tee into the existing
    # W-M-STOS/STOS2 junction.
    Node(uid="N9H36K3W70", tag="N-M-MUDC1", position=pt(ft(0), ft(29, 7.5))),
    Node(uid="T374Q35GT9", tag="N-M-MUDC2", position=pt(ft(6), ft(29, 7.5))),
]

WALLS = [
    # --- exterior loop (CCW), sheathing-ext on the line -----------------------
    Wall(uid="CMW101AAAA", tag="W-M-S1", start_node="N-M-SW", end_node="N-M-S1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW102AAAA", tag="W-M-S2", start_node="N-M-S1", end_node="N-M-SE",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW103AAAA", tag="W-M-E1", start_node="N-M-SE", end_node="N-M-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CMW104AAAA", tag="W-M-E2", start_node="N-M-E1", end_node="N-M-NE",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CMW105AAAA", tag="W-M-N1", start_node="N-M-NE", end_node="N-M-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW106AAAA", tag="W-M-N2", start_node="N-M-N1", end_node="N-M-N2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    # Split at N-M-MECH3, where RM-M-MECH's east wall tees into the north wall
    # (2026-07-28, MEP shaft closet). corner_style_end moves to W-M-N3B, which now
    # carries the actual NW building corner.
    Wall(uid="CMW107AAAA", tag="W-M-N3", start_node="N-M-N2", end_node="N-M-MECH3",
         assembly="CATLIN_EXT_2X6",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N3"),
    Wall(uid="CMW135AAAA", tag="W-M-N3B", start_node="N-M-MECH3", end_node="N-M-NW",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N3"),
    # Split at N-M-MECH1, where RM-M-MECH's south wall tees into the west wall
    # (2026-07-28, MEP shaft closet).
    Wall(uid="CMW136AAAA", tag="W-M-W1B", start_node="N-M-NW", end_node="N-M-MECH1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    # Split again at N-M-MUDC1, where RM-M-MUD-CLOSET's north partition tees into the
    # west wall (2026-08-02) — the same endpoint-only junction rule that forced the
    # N-M-MECH1 split above. WIN-M-MUD (RO y 30'-9"..31'-11") stays on this, the northern
    # segment, and the segment's start node (N-M-MECH1) is unchanged, so its stud grid
    # and the window's bay position do not move.
    Wall(uid="CMW108AAAA", tag="W-M-W1", start_node="N-M-MECH1", end_node="N-M-MUDC1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="WM8EB2TX38", tag="W-M-W1C", start_node="N-M-MUDC1", end_node="N-M-W1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW109AAAA", tag="W-M-W2", start_node="N-M-W1", end_node="N-M-W2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW110AAAA", tag="W-M-W3", start_node="N-M-W2", end_node="N-M-W3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W2"),
    Wall(uid="CMW111AAAA", tag="W-M-W4", start_node="N-M-W3", end_node="N-M-SW",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W2"),
    # --- center bearing wall (2x6), stacks on the basement concrete line ------
    Wall(uid="CMW112AAAA", tag="W-M-C1", start_node="N-M-S1", end_node="N-M-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS"),
    Wall(uid="CMW113AAAA", tag="W-M-C2", start_node="N-M-C1", end_node="N-M-E4",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS2"),
    Wall(uid="CMW114AAAA", tag="W-M-C3", start_node="N-M-E4", end_node="N-M-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS2"),
    # y 21'-8" .. 25'-10" IS NOT A WALL — it is the BM-M-HALL flitch of LVL, the main-storey
    # twin of BM-S-HALL directly above it. W-M-C4 / W-M-C4B used to stand here; the whole
    # 4'-2" is now open so the hall and the living room read as one room (2026-07-28), the
    # way the second storey already does under its own beam. The bearing stack is unbroken
    # because the beam is *in* it: see BEAMS below.
    Wall(uid="CMW116AAAA", tag="W-M-C5", start_node="N-M-C3", end_node="N-M-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CN"),
    # --- stair / storage block --------------------------------------------------
    # This wall line carries the cut second-floor joists and stacks over the basement
    # concrete stair wall. Split at two tees, N-M-STRJ and N-M-STR1 (6" apart, = W-M-STRW2):
    # `resolve/topology.py` builds junctions from wall *endpoints* only, so a tee needs its
    # own segment or the branch gets no framing.
    #
    # Both segments are CATLIN_MUDROOM_INT_2X6_EXPOSED, appearance-grade DF studs open to the
    # mudroom (coat nooks) with 3/4" cabinet plywood on the stair face — `interior_room` picks
    # the mudroom side as layer 0. Until 2026-07-30 the mudroom segment was plain
    # CATLIN_INT_2X6_BRG (spf vs. df-select-s4s), which `integrity.junction_fallback` flagged
    # at N-M-STRJ; it now flags the softer mixed-assembly L at N-M-STR1 instead, where the
    # 2x4 partition W-M-STRS dies into this wall's end stud — an acceptable finish detail.
    #
    # ALIGNMENT: this stack is 6 1/4" vs. CATLIN_INT_2X6_BRG's 6 3/4". The axis is pinned
    # 3 3/8" inboard of the plywood's stair face (not centred) because FO-S-STAIR's west edge
    # and both flights' stringers are authored off that exact face (second.py) — the 1/2"
    # thickness change is taken entirely out of the mudroom side (9'-8 5/8" -> 9'-9 1/8").
    #
    # MEP: keep wiring/plumbing out — a bored stud shows. One exception: REG-M-XFER-MUD, a
    # 12" transfer-louver cut centred y=34'-0" in the clear bay between studs at 33'-4" and
    # 34'-8", so no stud is cut and no header is needed.
    Wall(uid="CMW117AAAA", tag="W-M-STRW", start_node="N-M-N2",
         end_node="N-M-STRJ", assembly="CATLIN_MUDROOM_INT_2X6_EXPOSED", top=ft(9),
         alignment=face("ply-stair-ext", offset=inch(-3.375)),
         interior_room="RM-M-MUDROOM",
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR"),
    # Only 1 1/4" of this segment's west face is ever seen — between W-M-STOS2's south face
    # and W-M-STRS's north face — so the exposed studs it now carries read as the corner
    # return of the mudroom wall rather than as bare framing in the hall. `interior_room`
    # still names the mudroom: the field only picks which side layer 0 faces, and the
    # mudroom seed is on the correct (west) side of this segment's midpoint too.
    Wall(uid="CMW134AAAA", tag="W-M-STRW2", start_node="N-M-STRJ",
         end_node="N-M-STR1", assembly="CATLIN_MUDROOM_INT_2X6_EXPOSED", top=ft(9),
         alignment=face("ply-stair-ext", offset=inch(-3.375)),
         interior_room="RM-M-MUDROOM",
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR"),
    # The wall at the top of the stairs, pushed north to y=25'-10" (2026-07-28) to close
    # against the wells; D-M-STAIR opens onto ST-B2M's top nosing in the west lane.
    # Shortened 2026-07-30: it now dies flush into the well partition's east face
    # (x=14'-2 1/4") instead of running the full 8' with a cased RO-1, leaving the east lane
    # (ST-M2S's full 3'-6 3/8") open to the living room. Nothing structural bore on the
    # removed length, and no guard is needed — ST-M2S's first tread is at floor level there.
    Wall(uid="CMW118AAAA", tag="W-M-STRS", start_node="N-M-STR1",
         end_node="N-M-STR2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW119AAAA", tag="W-M-STOS", start_node="N-M-W1",
         end_node="N-M-BA1", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW120AAAA", tag="W-M-STOS2", start_node="N-M-BA1",
         end_node="N-M-STRJ", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- powder bath west of hallway -------------------------------------------
    Wall(uid="CMW121AAAA", tag="W-M-BAE", start_node="N-M-BA1",
         end_node="N-M-BA2", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    # --- hallway south wall band ------------------------------------------------
    Wall(uid="CMW122AAAA", tag="W-M-HS1", start_node="N-M-W2",
         end_node="N-M-BA2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW123AAAA", tag="W-M-HS2", start_node="N-M-BA2",
         end_node="N-M-D1", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW124AAAA", tag="W-M-HS3", start_node="N-M-D1",
         end_node="N-M-E3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW125AAAA", tag="W-M-HS4", start_node="N-M-E3",
         end_node="N-M-C2", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- bath2 / laundry / study / closet block ---------------------------------
    Wall(uid="CMW126AAAA", tag="W-M-BA2E", start_node="N-M-D1",
         end_node="N-M-D2", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CMW127AAAA", tag="W-M-BA2E2", start_node="N-M-D2",
         end_node="N-M-D3", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CMW128AAAA", tag="W-M-LS", start_node="N-M-E2",
         end_node="N-M-E3", assembly="INT_2X4_PARTITION", top=ft(9)),
    # The closet's north line, y=18'-0" since 2026-08-03 (was 17'-4"). See the NODES note
    # over N-M-D2: the 8" came out of RM-M-LAUNDRY and RM-M-STUDY, and the laundry's 40"
    # stacked pair is what says it could not be more.
    # Both name W-B-CW2 explicitly: the basement's y=18' line is actually two walls
    # (W-B-CW3 and W-B-CW2), so `integrity.stack_ambiguous` needs a pick. Non-structural
    # either way — these partitions sit on the 9" cast deck.
    Wall(uid="CMW129AAAA", tag="W-M-CLN", start_node="N-M-D2",
         end_node="N-M-E2", assembly="INT_2X4_PARTITION", top=ft(9), stacks_on="W-B-CW2"),
    Wall(uid="CMW130AAAA", tag="W-M-CLN2", start_node="N-M-E2",
         end_node="N-M-E4", assembly="INT_2X4_PARTITION", top=ft(9), stacks_on="W-B-CW2"),
    # --- bedroom north wall ------------------------------------------------------
    Wall(uid="CMW131AAAA", tag="W-M-BDN1", start_node="N-M-W3",
         end_node="N-M-D3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW132AAAA", tag="W-M-BDN2", start_node="N-M-D3",
         end_node="N-M-C1", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- RM-M-MECH: framed MEP shaft closet, NW corner (2026-07-28) -------------
    Wall(uid="CMW137AAAA", tag="W-M-MECH-S", start_node="N-M-MECH1",
         end_node="N-M-MECH2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW138AAAA", tag="W-M-MECH-E", start_node="N-M-MECH2",
         end_node="N-M-MECH3", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- RM-M-MUD-CLOSET: framed south mudroom closet (2026-08-02) --------------
    # Replaces FURN-M-MUD-CLOSET-S (plan/furniture_types.py, now empty). The north
    # partition carries the closet's opening — the bypass slider in D-M-MUDC — and the
    # east return dies into the existing N-M-BA1 tee, so the room closes against
    # W-M-W1C (west), W-M-STOS (south) and these two.
    Wall(uid="KKVYSAJKZF", tag="W-M-MUDC-N", start_node="N-M-MUDC1", end_node="N-M-MUDC2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="21GE85HJDT", tag="W-M-MUDC-E", start_node="N-M-MUDC2", end_node="N-M-BA1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
]

OPENINGS = [
    # Exterior
    # Pushed east to N-M-N2 (2026-07-28, mudroom conversion): near jamb 6" off the tee
    # where W-M-STRW's bearing stack ties into this wall — as tight as the header's jack
    # studs and the stair wall's own king studs both want — so the closet run west of the
    # door reaches the west wall almost whole. See RM-M-MUDROOM below.
    Door(uid="CMD201AAAA", tag="D-M-ENTRY", host="W-M-N3", type_ref="DT-EXT-SWING36",
         position=from_node("N-M-N2", ft(0, 6))),
    Door(uid="CMD202AAAA", tag="D-M-BALC", host="W-M-S2", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-M-S1", ft(1, 4)), flip_swing=True),
    # Interior
    # x 10'-8 1/16"..13'-4 1/16": the west lane, which since ST-B2M was mirrored is the one
    # the basement flight arrives in — so this is the door onto the basement stairs. The way
    # onto ST-M2S beside it was RO-1, a cased opening in the same wall, until the wall was
    # shortened past it (2026-07-30); that lane is open now.
    Door(uid="CMD203AAAA", tag="D-M-STAIR", host="W-M-STRS", type_ref="DT-INT-SWING32",
         position=from_node("N-M-STR1", ft(0, 8.0625)), flip_swing=True),
    # Pushed east to N-M-STRJ (2026-07-28, mudroom conversion): same 6" tee clearance as
    # D-M-ENTRY above it, off the bearing stair wall's jack studs. Renamed with the room.
    Door(uid="CMD204AAAA", tag="D-M-MUD", host="W-M-STOS2", type_ref="DT-INT-SWING32",
         position=from_node("N-M-STRJ", ft(0, 6))),
    Door(uid="CMD205AAAA", tag="D-M-BATH1", host="W-M-BAE", type_ref="DT-INT-SWING24",
         position=from_node("N-M-BA1", ft(1))),
    # RM-M-MECH's hinged utility door (2026-07-28), not the mudroom closets' bypass style.
    # Pulled 2" west of its original 3'-2 15/16" (2026-07-29): at that offset the king stud
    # punched into W-M-MECH-E's corner stud pack. This clears it with margin to spare.
    Door(uid="CMD211AAAA", tag="D-M-MECH", host="W-M-MECH-S", type_ref="DT-INT-SWING30",
         position=from_node("N-M-MECH1", ft(3, 0.9375)), flip_swing=True, flip_hinge=True),
    # RM-M-MUD-CLOSET's bypass slider, no swing to clear. Near jamb 1'-1" off N-M-MUDC1
    # centres the 50" RO in the partition's framed span, leaving both corner stud packs clear
    # (the D-M-MECH king-stud lesson).
    Door(uid="QBTZNWG6AG", tag="D-M-MUDC", host="W-M-MUDC-N", type_ref="DT-INT-BYPASS48",
         position=from_node("N-M-MUDC1", ft(1, 1))),
    Door(uid="CMD206AAAA", tag="D-M-BATH2", host="W-M-BDN1", type_ref="DT-INT-SWING30",
         position=from_node("N-M-W3", ft(2)), flip_swing=True, flip_hinge=True),
    Door(uid="CMD207AAAA", tag="D-M-LAUN", host="W-M-HS3", type_ref="DT-INT-BIFOLD56",
         position=from_node("N-M-D1", ft(0, 4))),
    # Offset 6 11/16" off N-M-E4, not the 1'-2 11/16" it was: N-M-E4 moved north 8" with the
    # closet line (2026-08-03), and this offset moved the same 8" so the door itself did not
    # move. 6 11/16" clears the corner stud pack (the D-M-MECH margin); the wall is only
    # 4'-2" long now, so the door cannot move further south.
    Door(uid="CMD208AAAA", tag="D-M-STUDY", host="W-M-C3", type_ref="DT-INT-SWING30",
         position=from_node("N-M-E4", ft(0, 6.6875)), flip_swing=True),
    Door(uid="CMD210AAAA", tag="D-M-BED", host="W-M-BDN2", type_ref="DT-INT-SWING32",
         position=from_node("N-M-D3", ft(5)), flip_hinge=False, flip_swing=True),
    # Second bedroom <-> living connection, straight through the centre bearing wall.
    # Trimless (drywall return jamb, no casing) so it reads as a slot in the wall from
    # both rooms. W-M-C1 is BEARING, so the solver's framing tables put a structural
    # header over the 2'-6" opening on their own — nothing extra to author here.
    Door(uid="CMD212AAAA", tag="D-M-BED2", host="W-M-C1", type_ref="DT-INT-SWING30-TRIMLESS",
         position=from_node("N-M-S1", ft(5))),
    # O-M-HALL (the old cased pass-through) retired 2026-07-28 with its host wall W-M-C4:
    # the full 4'-2" is open now. Sills raised 2'-0" -> 3'-0" (2026-07-30 facade pass) so
    # every main/second head on the west face lands on one shared 6'-0" line (27" units at
    # 3'-0" sill, 14" units at 4'-0"). Both moved 4" south on 2026-08-15 with W-M-W4's stud
    # grid (see NODES); offsets are authored off the wall's far node so they don't move
    # automatically and had to be rewritten by hand.
    #
    # W1 columns at 5'-0" (under WIN-S-PLANT3). W2 cannot column with WIN-S-SUITE1 above it:
    # the only two shared stud lines in the overlap (124"/140" from the wall start) each leave
    # only 16" of clear wall where the jamb pack needs ~16 1/2", so either choice puts a king
    # stud sharing 83% of a 2x6 with W-M-W3's end stud (structural.member_interference).
    # Three columns is the answer instead: 5'-0" (here), 19'-8" (WIN-M-BATH2), 31'-4"
    # (WIN-M-MUD), all on the shared 6'-0" head line.
    Window(uid="CMX301AAAA", tag="WIN-M-BED-W1", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(3, 10.5)),
           sill_height=ft(3)),                                                # y 5'-0"
    Window(uid="CMX302AAAA", tag="WIN-M-BED-W2", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(9, 2.5)),
           sill_height=ft(3)),                                               # y 10'-4"
    # South pair: centres 4'-0" and 9'-4" are STUD LINES on W-M-S1's grid, stacking exactly
    # under WIN-S-PLANT1/2. Sill 2'-8" puts heads at 6'-8" with the doors. Moved 8" east off
    # the old 3'-4"/8'-8" bay centres when units narrowed 42" -> 30" (WT-3048, 2026-08-01) —
    # a 30" RO wants a stud line, not a bay centre (structural.window_framing_module, held
    # by test_catlin_contract_m3).
    Window(uid="CMX303AAAA", tag="WIN-M-BED-S1", host="W-M-S1",
           type_ref="WT-3048", position=from_node("N-M-SW", ft(2, 9)),
           sill_height=ft(2, 8)),
    Window(uid="CMX304AAAA", tag="WIN-M-BED-S2", host="W-M-S1",
           type_ref="WT-3048", position=from_node("N-M-SW", ft(8, 1)),
           sill_height=ft(2, 8)),
    # Offset bumped 4'-5" -> 4'-11" (2026-07-29) when N-M-W2 pushed 6" north, keeping the
    # window on the same bay. Retyped WT-1424-T -> WT-2736-T and moved to 19'-8" on
    # 2026-08-15 for the west face's third column (WIN-S-SUITE2 above it): a 14" RO
    # centres on a bay centre, a 27" on a stud line — 8" apart, so 14" can never column
    # with 27" (the 8" rule). Also a code gain: 27x36 delivers 6.75/3.375 sf against
    # R303.3's 3/1.5 sf where 14x24 gave 2.33/1.17. Sill drops to 3'-0" for the shared
    # 6'-0" head line; `-T` stays since R308.4.5 tempers any bathroom sill under 60".
    Window(uid="CMX305AAAA", tag="WIN-M-BATH2", host="W-M-W3",
           type_ref="WT-2736-T", position=from_node("N-M-W3", ft(5, 6.5)),
           sill_height=ft(3)),                                               # y 19'-8"
    # Picture unit centred y=31'-4", the bench/aisle centreline (FURN-M-MUD-BENCH,
    # plan/placeables.py). Re-authored off N-M-MECH1 (2026-08-02): a `from_node` offset is
    # measured from the host's *start* node, so when the 2026-07-28 MECH split made
    # N-M-MECH1 the start, the window silently slid 2'-8" south. 1'-5" off N-M-MECH1 restores
    # y=31'-4" — a bay centre, so the 14" RO stays inside a stud bay. Sill raised to 4'-0"
    # (2026-07-30) puts its head on the shared 6'-0" line.
    Window(uid="CMX306AAAA", tag="WIN-M-MUD", host="W-M-W1",
           type_ref="WT-1424-FIX", position=from_node("N-M-MECH1", ft(1, 5)),
           sill_height=ft(4)),
    # South pair: centres 27'-4" and 32'-8" are stud lines on W-M-S2's grid, stacking exactly
    # under WIN-S-STUDY1/2. Moved 8" west off the old 28'-0"/33'-4" bay centres with the
    # WT-3048 narrowing (see WIN-M-BED-S1/2). The two south segments are 8" out of phase, so
    # this pair carries the same phase miss off the bedroom pair's mirror as it always has.
    # D-M-BALC's french-door RO stays clear by 1'-9".
    Window(uid="CMX307AAAA", tag="WIN-M-LIV-S1", host="W-M-S2",
           type_ref="WT-3048", position=from_node("N-M-SE", ft(2, 1)),
           sill_height=ft(2, 8)),
    Window(uid="CMX308AAAA", tag="WIN-M-LIV-S2", host="W-M-S2",
           type_ref="WT-3048-T", position=from_node("N-M-SE", ft(7, 5)),
           sill_height=ft(2, 8)),
    # East row respaced (2026-07-30 facade pass): the facade favors within-storey rhythm
    # over between-storey stacking here, so this row runs as even as its own grid allows —
    # 4'-0" / 12'-0" / 19'-4" (the true-even 11'-8" middle isn't a stud line on W-M-E1).
    # The kitchen stretch north of WIN-M-DIN-E2 stays deliberately blank. Both sills stay
    # 2'-6": the BESTA run tops out at 29 3/4" (placeables.py), clearing the countertop
    # by 1/4".
    Window(uid="CMX309AAAA", tag="WIN-M-LIV-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(2, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX310AAAA", tag="WIN-M-LIV-E2", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(10, 10.5)),
           sill_height=ft(2, 6)),
    # WIN-M-DIN-E1 was retired in the 2026-07-30 east restack: every candidate position
    # either sat over a kitchen counter (forcing an awkward sill) or collided with
    # WIN-M-LIV-E2's RO. WIN-M-KITCH covers the kitchen instead. E2 also can't take the
    # fourth second-floor column (WIN-S-BED3 at 32'-4") — that stretch of wall now carries
    # the range/hood/cooking run — so it sits at 19'-4" instead, clear of that column band.
    Window(uid="CMX312AAAA", tag="WIN-M-DIN-E2", host="W-M-E2",
           type_ref="WT-2736", position=from_node("N-M-E1", ft(0, 2.5)),
           sill_height=ft(2, 6)),
    # Moved to the north wall 2026-07-30 with the sink (plan/placeables.py's kitchen header),
    # then re-centred the same day when the sink flipped with the dishwasher toward the
    # middle of the run: still directly in front of the sink, still 42" sill = counter
    # height, centred at x=28'-0" — 7" off FURN-M-KIT-SINKBASE's x=28'-7" so the RO lands on
    # a stud line instead. Host is W-M-N1.
    Window(uid="CMX313AAAA", tag="WIN-M-KITCH", host="W-M-N1",
           type_ref="WT-2736", position=from_node("N-M-NE", ft(6, 10.5)),
           sill_height=ft(3, 6)),
    # Relocated to the NE corner 2026-07-30 with the range/sink wall swap. Kept as a small
    # corner window rather than dropped: centre x=34'-0" is a bay centre off N-M-NE, clear
    # of WIN-M-KITCH by 20 1/2" and of the corner face by 10 3/8".
    Window(uid="82WVR597PA", tag="WIN-M-KITCH-N", host="W-M-N1", type_ref="WT-1424",
           position=from_node("N-M-NE", ft(1, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    # RM-M-HALL (2026-07-28) and RM-M-STAIR (2026-07-30) were both retired into this claim:
    # opening the centre line and shortening W-M-STRS leaves one polygonized face spanning
    # living room, old hall band and stair well, so a second seed in the same face would
    # bill the floor twice. 768 sf is the honest walkable area, stair included.
    # Main-floor finishes revised 2026-08-02 (plans/TODO.md §Hardwood): solid oak is the
    # studies' floor (RM-A-STUDY + RM-S-STUDY2) — living/study here go LVP, bed/closet carpet.
    Room(uid="CMR401AAAA", tag="RM-M-LIVING", seed=pt(ft(27), ft(12)),
         occupancy=Occupancy.LIVING, floor_finish="lvp"),
    Room(uid="CMR402AAAA", tag="RM-M-BED", seed=pt(ft(9), ft(6)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CMR403AAAA", tag="RM-M-BATH1", seed=pt(ft(2), ft(24, 6)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CMR404AAAA", tag="RM-M-BATH2", seed=pt(ft(4), ft(18)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CMR405AAAA", tag="RM-M-LAUNDRY", seed=pt(ft(10, 6), ft(20)),
         occupancy=Occupancy.LAUNDRY, floor_finish="tile"),
    Room(uid="CMR406AAAA", tag="RM-M-STUDY", seed=pt(ft(15, 8), ft(20)),
         occupancy=Occupancy.OFFICE, floor_finish="lvp"),
    Room(uid="CMR407AAAA", tag="RM-M-CLOSET", seed=pt(ft(13), ft(15, 4)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet"),
    # Retagged from RM-M-STORAGE with the mudroom conversion (2026-07-28): entry vestibule
    # now, not bulk storage, but still Occupancy.STORAGE — there is no MUDROOM occupancy in
    # the closed enum and STORAGE is the closer fit of what exists (unheated-adjacent,
    # hard-finish floor) than LIVING or HALLWAY would be.
    Room(uid="CMR409AAAA", tag="RM-M-MUDROOM", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
    # Framed MEP shaft closet, replacing FURN-M-MUD-CLOSET-N (2026-07-28): the
    # radon+plumbing riser rides its SW corner. STORAGE is the closed enum's closest fit
    # for a mechanical closet, same reasoning as RM-M-MUDROOM above.
    Room(uid="CMR411AAAA", tag="RM-M-MECH", seed=pt(ft(3), ft(34, 6)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
    # Framed south mudroom closet, replacing FURN-M-MUD-CLOSET-S (2026-08-02): the last
    # furniture closet becomes a real reach-in — 34 3/4" deep clear, bypass slider in its
    # north partition. Tagged RM-M-MUD-CLOSET because RM-M-CLOSET (CMR407AAAA) already
    # names the dressing corridor. STORAGE + sealed-concrete match its parent mudroom,
    # the same closed-enum reasoning as RM-M-MUDROOM/RM-M-MECH above.
    Room(uid="G01HFSH967", tag="RM-M-MUD-CLOSET", seed=pt(ft(3), ft(28)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
]

ALARMS = [
    Alarm(uid="CMA701AAAA", tag="AL-M-BED", kind=AlarmKind.COMBO, room="RM-M-BED",
          circuit="CKT-LT-BACKUP"),
    # The R314.3 "outside each separate sleeping area" alarm. Hosted by RM-M-LIVING (the
    # space it's open to) but positioned explicitly, since that room's seed is ~13' away in
    # the dining end: the position below is the dressing corridor, directly outside D-M-BED,
    # clear of the closet's sliding doors.
    Alarm(uid="CMA702AAAA", tag="AL-M-HALL", kind=AlarmKind.COMBO, room="RM-M-LIVING",
          circuit="CKT-LT-BACKUP", position=pt(ft(14, 4), ft(15, 8))),
]

# Electric radiant floor — the two main-storey comfort zones (2026-07-25). Not a heating
# system (the heat pumps carry the house); these just warm two barefoot floors. Mat at
# 12 W/ft2 (the working rate for a 3" serpentine 120V cable); `in_slab(1/2")` is the setting
# bed in the thinset above SL-M-DECK's cured 9" concrete, not cast structure. Zones are drawn
# 4" off every clear face since mat can't run to a wall. `stat` is the slab sensor point;
# line-voltage thermostats are ED-M-BATH2-FH-STAT / ED-M-DINING-FH-STAT (plan/electrical.py).
FLOOR_HEAT = [
    # RM-M-BATH2's floor: an L around WC/shower/tub with >=1" clearance at each fixture
    # footprint, so `advisory.floor_heat_fixture_keepout` can verify the actual loop
    # geometry. Polygon tightened 2026-07-29 with the BATH2 wall move — the old one ran
    # under FX-M-BATH2-SH's whole footprint and clipped FX-M-BATH2-SINK's.
    FloorHeat(uid="CMH801AAAA", tag="FH-M-BATH2", room_ref="RM-M-BATH2",
              zone=(pt(ft(0, 5), ft(13, 9)), pt(ft(4, 7.2), ft(13, 9)),
                    pt(ft(4, 7.2), ft(15, 6)), pt(ft(3, 10), ft(15, 6)),
                    pt(ft(3, 10), ft(21, 5)), pt(ft(3, 6), ft(21, 5)),
                    pt(ft(3, 6), ft(15, 6)), pt(ft(0, 5), ft(15, 6))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3), embed=in_slab(inch(0.5)),
              # 41.5 ft2 at the 12 W/ft2 of plan/circuits.py -> 498 W, carried at 500.
              watts=500,
              stat=pt(ft(2), ft(17, 6))),
    # Under the dining table. FURN-M-DINING covers x 22'-11"..30'-11", y 15'-7"..19'-1"; the
    # zone takes the table's exact width and runs y 13'-9"..21'-0" so it reaches under both
    # chair rows (FURN-M-CHAIR-S* at y=14'-6", -N* at y=20'-2") — feet, not the table legs,
    # are what this is for. 8'-0" x 7'-3" = 58.0 ft2, free-standing in RM-M-LIVING with no
    # room_ref, since the living room is 642 ft2 and only this patch of it is heated.
    FloorHeat(uid="CMH802AAAA", tag="FH-M-DINING",
              zone=(pt(ft(22, 11), ft(13, 9)), pt(ft(30, 11), ft(13, 9)),
                    pt(ft(30, 11), ft(21)), pt(ft(22, 11), ft(21))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3), embed=in_slab(inch(0.5)),
              # 58.0 ft2 at 12 W/ft2 -> 696 W, carried at 700.
              watts=700,
              stat=pt(ft(26, 11), ft(17, 4))),
]

# Structural deck of the main floor: 9" concrete over the basement.
SLABS = [
    Slab(uid="CMS501AAAA", tag="SL-M-DECK",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(9), openings=("FO-M-STAIR",), assembly="CATLIN_DECK_9_INT"),
]

# Drawn to the *finished* well, not the wall centrelines — the shaft the stair actually
# climbs; the u-split resolver anchors flights to its near corner. West/east are the
# basement's 12" concrete faces (narrower than the 2x6 walls above, so they size the
# flights). North (2026-07-28) is W-B-N2's inside face at y=35'-0", which the main deck
# bears on. South (26'-0 3/8") is fixed by FO-S-STAIR's south edge one storey up — ST-M2S's
# springing point — so both wells share that same south edge. Run here is 8'-11 5/8": IRC
# R311.7.6's 36" landing plus six 11 15/16" treads, well inside R311.7.5.2's 10" minimum.
FLOOR_OPENINGS = [
    FloorOpening(uid="CMF601AAAA", tag="FO-M-STAIR",
                 outline=(pt(ft(10, 6), ft(26, 0.375)), pt(ft(17, 6), ft(26, 0.375)),
                          pt(ft(17, 6), ft(35)), pt(ft(10, 6), ft(35))),
                 bearing_refs=("W-M-STRW", "W-M-STRW2")),
]

# 7'-0" well = 3'-3 3/4" + 4 1/2" well partition + 3'-3 3/4", each flight clearing IRC
# R311.7.1's 36" minimum above the handrail; landing is R311.7.6's 36" minimum.
# `turn_direction="left"` (2026-07-28): the basement flight springs in the east lane and
# arrives in the west (D-M-STAIR's lane); ST-M2S is mirrored so the east lane carries the
# flight up to second. No guard is authored at the head — W-M-STRS closes the west lane and
# ST-M2S's first tread sits at floor level on the east, so both are a flight to step onto,
# not a drop.
STAIRS = [
    Stair(uid="CST701AAAA", tag="ST-B2M", floor_opening="FO-M-STAIR",
          from_storey="basement", to_storey="main", width=ft(3, 3.75),
          layout="u_split_landing", run_direction="y", turn_direction="left",
          start=pt(ft(10, 6), ft(26, 0.375)), landing_depth=ft(3)),
]

# ST-B2M handrails (R311.7.8): one wall-mounted rail per flight, `serves_stair` rakes each
# to its flight's nosing line and code.R311_7_8_handrail grades `top_height` (34"-38"),
# continuity and graspability. Same authoring as ST-M2S one storey up (second.py
# STAIR_HANDRAILS): each rail sits 2" off its lane's wall face and runs the flight's span.
STAIR_HANDRAILS = [
    Railing(
        uid="CMRL01AAAA", tag="RL-M-HANDRAIL-E", path=(
            pt(ft(17, 4), ft(26, 0.375)),
            pt(ft(17, 4), ft(31, 0.375)),
        ),
        kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
        base_elevation=ft(-9), post_spacing=inch(48), post_size="2x2", rail_count=1,
        mount="wall", assembly="RAILING_DARK_METAL",
        role="handrail", serves_stair="ST-B2M", top_height=inch(36),
        graspable_profile="1.5in round — Type I",
    ),
    Railing(
        uid="CMRL02AAAA", tag="RL-M-HANDRAIL-W", path=(
            pt(ft(10, 8), ft(31, 0.375)),
            pt(ft(10, 8), ft(26, 10.375)),
        ),
        kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
        base_elevation=ft(0), post_spacing=inch(48), post_size="2x2", rail_count=1,
        mount="wall", assembly="RAILING_DARK_METAL",
        role="handrail", serves_stair="ST-B2M", top_height=inch(36),
        graspable_profile="1.5in round — Type I",
    ),
]

# The beam that lets the main-storey centre line be open between hall and living room
# (2026-07-28) — twin of BM-S-HALL one storey up. Per CLAUDE.md, x=18' is a bearing line
# footings-to-ridge; this LVL *is* that bearing line for its 4'-2" span, not a break in it.
#
# Load: FS-SECOND's 18' tributary (~990 plf) plus a point load — BM-S-HALL above has no
# centre wall either, so everything above (attic floor, RB-HOUSE, second-storey plate)
# arrives as that beam's end reaction (~8.1 k) landing 8" north of this beam's own south
# bearing. Over the 4'-2" clear span: M = 5.7 ft-k, V = 8.9 k. Three plies of 1.75x11.875
# LVL give Sx = 123 in^3 (26.7 ft-k) and 62 in^2 shear area (11.8 k) — shear, not moment,
# governs. Same section/ply count as BM-S-HALL and RB-HOUSE (one LVL depth on the job).
#
# Bears on the ends of the walls it replaced (W-M-C3/W-M-C5), each stacking onto W-B-CN and
# the footings. Framed FLUSH (`top_elevation` at the joist datum) so FS-SECOND hangs off it
# and the 9' ceiling stays unbroken — a dropped beam would hang its full 11-7/8" into it.
BEAMS = [
    Beam(uid="CMBM01AAAA", tag="BM-M-HALL", start_node="N-M-C2", end_node="N-M-C3",
         size="3-1.75x11.875 LVL", bearing_refs=("W-M-C3", "W-M-C5"),
         top_elevation=ft(10)),
]

# The first-floor study's walnut wainscot (plans/TODO.md §Hardwood): every bounding wall
# to 36" above the floor, D-M-STUDY's punch subtracted by the resolver. Board feet come
# off the walnut-tg material's 4/4 stock (bf = sf) in the wood_surfaces takeoff.
PANELING = [
    WallPaneling(uid="CMK901AAAA", tag="WP-M-STUDY-WAINSCOT", room="RM-M-STUDY",
                 material_ref="walnut-tg", height=ft(3)),
]


# --- exterior door-jamb hold-downs -------------------------------------------
# The two exterior doors each punch a hole in what is otherwise the continuous shear line
# from basement concrete to roof; `strap_holdown_rows` only derives STHDs at sill-plate
# *ends*, not at mid-run openings, so these four fill the gap: embedded strap-tie
# holdowns, one per jamb, cast into the foundation and nailed up onto the framing above.
#
# Geometry: 3" outboard of each RO edge is the king stud's outer face, where the strap
# lies clear of the pack it restrains. `_JAMB_Y_*` centres them 3 1/4" into the 5 1/2"
# stud layer (measured from CATLIN_EXT_2X6's sheathing-ext plane); the dialect allows no
# arithmetic, so each offset is written as the number it lands on. Elevation is
# sill-plate mid-height.
#
# D-G-SERVICE is deliberately excluded: it's in the garage's ICF stem, which needs a
# different embedded part, not a foundation-wall strap.
_JAMB_Y_NORTH = ft(35, 8.75)
_JAMB_Y_SOUTH = inch(3.25)
_JAMB_Z = inch(1)
CONNECTORS = [
    Connector(uid="RYMM0XWNBM", tag="CN-M-HD-ENTRY-E", kind=ConnectorKind.HOLD_DOWN,
              position=pt(ft(9, 9), _JAMB_Y_NORTH), elevation=_JAMB_Z,
              size="STHD", connects=("W-M-N3", "W-B-N3")),
    Connector(uid="V5HNZ3S6Q1", tag="CN-M-HD-ENTRY-W", kind=ConnectorKind.HOLD_DOWN,
              position=pt(ft(6, 3), _JAMB_Y_NORTH), elevation=_JAMB_Z,
              size="STHD", connects=("W-M-N3", "W-B-N3")),
    # W-M-S2 carries no `stacks_on`, but the foundation wall under x 19'-1"..24'-7" at
    # y = 0 is W-B-S3 (N-B-S2 at x=18' east to N-B-SE) — not W-B-S2, which stops at 18'.
    Connector(uid="5D80PTSEWM", tag="CN-M-HD-BALC-W", kind=ConnectorKind.HOLD_DOWN,
              position=pt(ft(19, 1), _JAMB_Y_SOUTH), elevation=_JAMB_Z,
              size="STHD", connects=("W-M-S2", "W-B-S3")),
    Connector(uid="PJMETCQPK0", tag="CN-M-HD-BALC-E", kind=ConnectorKind.HOLD_DOWN,
              position=pt(ft(24, 7), _JAMB_Y_SOUTH), elevation=_JAMB_Z,
              size="STHD", connects=("W-M-S2", "W-B-S3")),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SLABS,
            *FLOOR_OPENINGS, *STAIRS, *STAIR_HANDRAILS, *BEAMS, *PANELING,
            *CONNECTORS]

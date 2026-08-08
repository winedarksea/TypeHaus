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
    # RM-M-MUD-CLOSET's opening (2026-08-02): a 48" sliding bypass pair, keeping the
    # replaced FURN-M-MUD-CLOSET-S's no-swing intent — the closet aisle has no floor to
    # spare for a swing, same reasoning as library's FURN-WARDROBE-48. "slide" is the
    # closed DoorOperation vocabulary's bypass form and is handled end to end: coplanar
    # panel pair + track in resolve/geometry_openings.py, the door-sliding plan symbol
    # in emit/draw/door_symbols.py, and SLIDING_TO_LEFT in the IFC emitter. 48" is the
    # largest standard bypass whose RO (50") fits the partition's 63 1/8" framed span
    # with jamb packs to spare; 60" would leave 1 1/8" total.
    DoorType(tag="DT-INT-BYPASS48", width=ft(4), height=ft(6, 8), operation="slide"),
    DoorType(tag="DT-INT-FRENCH60", width=ft(5), height=ft(6, 8),
             operation="double_swing", glazed=True, tempered=True),
    DoorType(tag="DT-EXT-OVERHEAD192", width=ft(16), height=ft(7), exterior=True,
             operation="overhead"),
]
# One size per width family, no exceptions: every placement of a family shares one
# height, chosen as the tallest that still fits the family's most constrained wall
# anywhere in the house. The 42" family used to carry a shorter WT-4242 twin for the
# attic's raked gables; the 2026-07-30 facade pass retired it by giving those gables
# WT-1424 instead, which is what the rake could always actually take. The 42" family
# itself is gone as of 2026-08-01, when the south glazing narrowed to WT-3048.
#
# The 18" family (WT-1864) is a deliberate fifth family, added 2026-07-31 for the attic's
# south juliet pair, and it is the same shape of argument that retired WT-4242 — one
# height per family, so a unit the committed heights cannot express needs its own family
# rather than a second height on an existing one. No committed height gives the tall narrow
# proportion the pair is for (the 30" family is 36" tall, little more than half of it).
#
# "No exceptions" now has two, both 2026-08-01, and neither is a drift — each is a case
# where the escape hatch the previous paragraph offers (give it its own width family) costs
# more than the second height does:
#
#   - WT-1448, because the 4:12 rake forbids the hatch outright. Any width above 14" breaks
#     a stud and takes a header, and it is the *header*, not the glass, that hits the rake;
#     see WT-1448's own note for the 1.8" that closes WT-1864 out of the position.
#   - WT-3048, because the 30" family's committed height (WT-3036's 36") would drop the
#     south head off the 6'-8" door-head line the whole south facade is built on, and a
#     fresh width family for the same glass is a width the facade columns cannot take.
#
# Read the rule as: one height per width family, unless a second height is the only way to
# keep a fact the roof or the facade already committed to.
WINDOW_TYPES = [
    # 14" RO — falls between studs on the 16" grid without breaking a stud line, so it
    # frames with no header, no jacks and no kings. 24" tall because the 5' attic knee
    # walls (WIN-A-W-S/W-N, WIN-A-E-S/E-N) have only that much room under the top plate
    # — the same 24" is what lets this size duck under the 4:12 south rake as well.
    # That combination makes it the house's fallback wherever a bigger unit will not go.
    WindowType(tag="WT-1424", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="awning"),
    # 14" RO, 48" tall — the south gable's flanker size (2026-08-01 facade pass), and the
    # one place the "one height per family" rule above is broken on purpose. The gable's
    # two survivors (WIN-A-S2/S3, after the 3'-4"/33'-8" corner pair was retired) needed a
    # unit tall enough to belong with the 18x64 juliet pair, and every alternative is closed:
    #
    #   - WT-1424's 24" is what made them read as vents beside the juliets in the first place.
    #   - WT-1864, the obvious "own family" answer the rule prescribes, does not fit. An 18"
    #     RO breaks a stud, so it takes the jamb pack — and on a NONBEARING gable wall
    #     framing/tables.py header_size(..., bearing=False) is a 2-2x6, 5.5" deep. At the
    #     nearest stud line the pair can use (x 8'-0" / 28'-0") the header's outer end lands
    #     at x 7'-0", where the 4:12 roof underside is 8'-3.7" and the header top wants
    #     8'-5.5": short by 1.8". The rake closes the 18" family out of this position.
    #
    # 14" is the only width that ducks it, and for the reason WT-1424's note already gives:
    # it lands wholly inside a bay, so framing/openings.py needs_jamb_pack skips the pack
    # entirely and there is no header to collide with the rake — only the RO head, which at
    # 6'-8" clears the underside by 2'-0" at the outer jamb. 48" is not a new height in the
    # house either (the south glazing, WT-3048, is 48"), and the 6'-8" head is the main
    # storey's own head line.
    # Casement rather than WT-1424's awning: a 48"-tall leaf is far past what a bottom-hinged
    # awning projects, and it puts the pair on the juliets' operation.
    WindowType(tag="WT-1448", width=inch(14), height=ft(4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 18" RO — the attic gable's juliet size (2026-07-31, narrowed from a 32" tilt-turn the
    # same day). One stud broken, so the centre sits on a STUD LINE, not a bay centre: at
    # 16" o.c. with 1-1/2" studs anything from 16" to 30" wide clears the two flanking stud
    # lines when it is centred on one, which is the cheap frame (a single header on a jack
    # and king each side) and, more to the point here, the one that lets the pair sit 32"
    # apart instead of 48". 64" tall: with the storey-wide 2'-8" south sill the head lands
    # at 8'-0", and the 4:12 rake is nowhere near it (roof underside is 11'-4" at the outer
    # jamb), so the height is a proportion decision rather than a clearance one — 18x64
    # keeps a door-like slot without the pair dominating the gable. Casement, not tilt-turn:
    # 18" is below the ~500 mm minimum frame any tilt-turn hardware line is made in, and an
    # in-swing casement leaf is what a juliet unit is anyway.
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
    # 30" RO — the south-glazing size, narrowed from the 42" WT-4248 the 2026-07-30 pass
    # introduced (2026-08-01). One stud broken, not two: the module's ideal position moves
    # with the RO width, so where 42" had to take a bay centre these take the stud line,
    # and the four facade columns moved 8" inboard with them (3'-4"/8'-8" -> 4'-0"/9'-4",
    # 28'-0"/33'-4" -> 27'-4"/32'-8"). The 6'-8" head line and the main-over-second
    # stacking are untouched.
    #
    # A second height in the 30" family, and the second deliberate break of "one height per
    # width family" (see WT-1448). The alternative — putting these on WT-3036 — would drop
    # the head from 6'-8" to 5'-8" with the 2'-8" sill, off the door-head line the south face
    # is built on, and the head line is the fact the facade rules protect. Narrower glass on
    # the same head is a proportion change; a head 12" lower is a different facade.
    # Non-bearing walls only (preferences [framing]).
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
    #
    # Four types, each identical to its parent but for the glass. R308.4 makes a *location*
    # hazardous — in a wet room, within 24" of a door, within 60" of a stair — and it is the
    # unit that lands there that has to be ordered tempered, not the size. So this is the
    # WT-3660-FIX/WT-1424-FIX precedent one more time: a different product on the quote gets
    # its own tag, and the twelve units of these sizes that sit in ordinary locations keep
    # ordinary glass rather than paying the tempering adder for nothing.
    #
    # These are *not* new width families and no facade or framing rule sees them: same RO,
    # same height, same operation, same ideal position on the 16" module as their parents.
    # Adding a tempered unit is a retype, never a move.
    WindowType(tag="WT-1424-T", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="awning", tempered=True),
    WindowType(tag="WT-2736-T", width=inch(27), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement", tempered=True),
    WindowType(tag="WT-3036-T", width=inch(30), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement", tempered=True),
    WindowType(tag="WT-3048-T", width=inch(30), height=ft(4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement", tempered=True),
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
    # W-M-HS1..4 (hall/bath2-laundry-study partition) pushed 6" north to y=22'-2"
    # (2026-07-29): the hall was a flat 4'-2", more than R311.7's minimum, and BATH2
    # needed the depth to separate the shower from the tub. Leaves the hall at 3'-8",
    # still 8" clear of the 3' minimum.
    Node(uid="CMN010AAAA", tag="N-M-W2", position=pt(ft(0), ft(22, 2))),
    Node(uid="CMN011AAAA", tag="N-M-W3", position=pt(ft(0), ft(13, 4))),
    # Center bearing line ties
    Node(uid="CMN012AAAA", tag="N-M-C1", position=pt(ft(18), ft(13, 4))),
    Node(uid="CMN013AAAA", tag="N-M-C2", position=pt(ft(18), ft(22, 2))),
    # N-M-C3 came south from y=26'-4" to the stair wall's line on 2026-07-28. It used to be
    # the W-M-C4B/W-M-C5 split; with W-M-C4/C4B gone it is BM-M-HALL's north bearing and
    # W-M-C5's south end. It stays on y=25'-10" now that W-M-STRS no longer reaches it —
    # the beam and the wall above it are what fix this point, not the stair wall. That does
    # make it a one-wall node: BM-M-HALL, not another wall, is what carries the centre line
    # south of here, so `open_end` is the honest description.
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
    Node(uid="CMN017AAAA", tag="N-M-BA2", position=pt(ft(6), ft(22, 2))),
    Node(uid="CMN018AAAA", tag="N-M-D1", position=pt(ft(8), ft(22, 2))),
    # The closet/laundry line moved north 8" — y 17'-4" -> 18'-0" — on 2026-08-03, taking
    # W-M-CLN and W-M-CLN2 (and with them the north edge of RM-M-CLOSET) with it. All three
    # nodes below move together or the line kinks; N-M-D2 and N-M-E4 are only split points on
    # the x=8' and x=18' runs, so nothing but the split moves there. What it costs is 8" of
    # RM-M-LAUNDRY and 8" of RM-M-STUDY, and what bounds it is the laundry: FX-M-LAUNDRY is
    # 40" deep against a room that was 56 3/4" and is now 48 3/4" nominal clear, so the tower
    # still stands free of D-M-LAUN's plane with room to spare (see plan/fixtures.py).
    # y=18'-0" is also where W-B-CW2 runs below — the basement's 12" cast wall is on that same
    # axis, so the partition now lands over solid concrete rather than mid-span of the deck.
    Node(uid="CMN019AAAA", tag="N-M-D2", position=pt(ft(8), ft(18))),
    Node(uid="CMN020AAAA", tag="N-M-D3", position=pt(ft(8), ft(13, 4))),
    Node(uid="CMN021AAAA", tag="N-M-E2", position=pt(ft(13, 4), ft(18))),
    Node(uid="CMN022AAAA", tag="N-M-E3", position=pt(ft(13, 4), ft(22, 2))),
    Node(uid="CMN023AAAA", tag="N-M-E4", position=pt(ft(18), ft(18))),
    # RM-M-MECH: the framed MEP shaft closet in the house's NW corner (2026-07-28),
    # replacing FURN-M-MUD-CLOSET-N. 6' wide (west wall to 6" shy of D-M-ENTRY's far
    # jamb at 6'-6") x 2'-8" deep — the radon+plumbing chase rides its SW corner, aligned
    # with the matching notch moved into RM-S-BATH1's NW corner directly above it.
    Node(uid="CMN025AAAA", tag="N-M-MECH1", position=pt(ft(0), ft(33, 4))),
    Node(uid="CMN026AAAA", tag="N-M-MECH2", position=pt(ft(6), ft(33, 4))),
    Node(uid="CMN027AAAA", tag="N-M-MECH3", position=pt(ft(6), ft(36))),
    # RM-M-MUD-CLOSET: the framed south mudroom closet (2026-08-02), replacing
    # FURN-M-MUD-CLOSET-S the way RM-M-MECH replaced its north twin. The partition axis
    # at y=29'-7 1/2" is computed from both of its constraints at once: the interior
    # depth from W-M-STOS's north face (26'-6 3/8") to the partition's south face
    # (29'-5 1/8") lands at 34 3/4" — inside the 32"-36" reach-in band — and the
    # partition's north face (29'-9 7/8") stops 1/8" shy of FURN-M-MUD-BENCH's south end
    # at y=29'-10". The east end reuses N-M-BA1's x=6' line so the return wall tees into
    # the existing W-M-STOS/W-M-STOS2 junction; its east face at 6'-2 3/8" keeps 5 5/8"
    # clear of D-M-MUD's near jamb at 6'-8".
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
    # This wall line carries the cut second-floor joists and stacks directly over the
    # basement concrete stair wall. It is split at the two tees on it: the mudroom's south
    # wall at N-M-STRJ and the stair wall at N-M-STR1, 6" apart. W-M-STRW2 is that 6" — the
    # jog between RM-M-MUDROOM's south wall and the head of the stairs. The split is not a
    # choice: `resolve/topology.py` builds junction incidents from wall *endpoints* only, so
    # a wall running through a tee node contributes nothing there and the branch gets no
    # framing. One wall line, one segment per tee.
    #
    # Both segments carry the same assembly and the same alignment as of 2026-07-30. The jog
    # used to be plain CATLIN_INT_2X6_BRG, which left its mudroom face 1/2" proud of the
    # exposed-stud wall's and split the bearing line's material (spf vs. df-select-s4s,
    # which is what `integrity.junction_fallback` was reporting at N-M-STRJ). It is one
    # continuous plane now, and the tee resolves on matching assemblies.
    #
    # `integrity.junction_fallback` did not vanish, it moved: N-M-STR1, where W-M-STRS's 2x4
    # spf partition dies into the end of this 2x6 df-select-s4s wall, is now the mixed-
    # assembly L. That is the better place for it — an L where a partition butts a bearing
    # wall's end stud is a finish detail, where the old one was the solver declining to call
    # the bearing line itself continuous through a tee.
    # The mudroom coat wall (plans/TODO.md): no drywall on the mudroom face, so the open
    # 2x6 bays between appearance-grade DF studs are the coat nooks, and the stair face is
    # 3/4" cabinet plywood that hooks screw straight into. `interior_room` is what points
    # layer 0 (the exposed studs) at the mudroom — the assembly is asymmetric, and without
    # it the storey's outward sign would put the plywood on the mudroom side.
    #
    # ALIGNMENT: the new stack is 6 1/4" (5.5 + 0.75) where CATLIN_INT_2X6_BRG was 6 3/4"
    # (5.5 + 2 × 0.625). Left centred, both faces would have crept 1/4" and the stair face
    # would have landed at 10'-3 1/8". That face is constrained geometry, not a result:
    # FO-S-STAIR's west edge is authored at 10'-3 3/8" off it (second.py) and both flights'
    # stringers bear on it. So the axis is pinned 3 3/8" inboard of the plywood's stair face,
    # holding that face exactly where it was; the whole 1/2" of thickness change is taken out
    # of the mudroom side, whose face moves east from 9'-8 5/8" to 9'-9 1/8".
    #
    # MEP: keep wiring and plumbing out of this wall — a bored stud shows. The one deliberate
    # exception is EQ-M-HP3-STAIR's recess (plan/electrical.py), the stair mini-split, which
    # is a designed cutout in the plywood face and stays.
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
    # The wall at the top of the stairs, pushed north 10" to y=25'-10" (2026-07-28) so it
    # closes against the wells again after they moved. Its north face at 26'-0 3/8" is the
    # wells' south edge, and D-M-STAIR in it opens onto ST-B2M's top nosing in the west lane.
    #
    # Shortened 2026-07-30: it used to run the whole 8' to N-M-C3 with RO-1, a 3'-0" cased
    # opening, standing in front of the east lane. The wall is only structurally and
    # spatially needed as far as the well partition — it frames D-M-STAIR and dies flush
    # into the partition's east face at x=14'-2 1/4" — so the east lane is simply open to
    # the living room now, the full 3'-6 3/8" of ST-M2S's width rather than RO-1's 3'-0".
    # Nothing bore on the removed length: FO-S-STAIR's south edge runs parallel to FS-SECOND's
    # E-W joists (a trimmer, not a header) and FO-M-STAIR's is cast concrete in SL-M-DECK.
    # No guard is needed where the wall went: ST-M2S's first tread is at floor level right
    # at that edge, so you step onto a flight, not over a drop.
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
    # Both name W-B-CW2 explicitly. Landing on y=18'-0" put them over the basement's own
    # y=18' line, and that line is two walls — W-B-CW3 (x 6'-9"..10') and W-B-CW2 (x 10'..18')
    # — so `integrity.stack_ambiguous` asked which. W-B-CW2 is the answer for both: it carries
    # all of W-M-CLN2 and 3'-4" of W-M-CLN's 5'-4". Nothing structural rides on the choice —
    # these are non-bearing partitions on a 9" cast deck, and the deck is what holds them up.
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
    # RM-M-MECH's single utility door, on the closet's east (right, as seen from the
    # mudroom) wall — a hinged door for the mechanical/shaft closet, not the sliding
    # bypass style of the mudroom's own storage closets (2026-07-28).
    # Pulled 2" west of its original 3'-2 15/16" (2026-07-29): at that offset the door's
    # own king stud landed inside N-M-MECH2's corner square and punched into W-M-MECH-E's
    # corner stud pack (the N-M-C2-class overlap). This clears it with margin to spare.
    Door(uid="CMD211AAAA", tag="D-M-MECH", host="W-M-MECH-S", type_ref="DT-INT-SWING30",
         position=from_node("N-M-MECH1", ft(3, 0.9375)), flip_swing=True, flip_hinge=True),
    # RM-M-MUD-CLOSET's bypass slider, opening north into the mudroom aisle — no swing,
    # so nothing to clear against the bench or D-M-MUD. Near jamb 1'-1" off N-M-MUDC1
    # centres the 50" RO in the partition's framed span (W-M-W1C's inner face at 6 1/2"
    # to W-M-MUDC-E's corner at 5'-9 5/8"): 6 1/2" of wall west of the RO and 6 5/8"
    # east — both clear of the corner stud packs (the D-M-MECH king-stud lesson).
    Door(uid="QBTZNWG6AG", tag="D-M-MUDC", host="W-M-MUDC-N", type_ref="DT-INT-BYPASS48",
         position=from_node("N-M-MUDC1", ft(1, 1))),
    Door(uid="CMD206AAAA", tag="D-M-BATH2", host="W-M-BDN1", type_ref="DT-INT-SWING30",
         position=from_node("N-M-W3", ft(2)), flip_swing=True, flip_hinge=True),
    Door(uid="CMD207AAAA", tag="D-M-LAUN", host="W-M-HS3", type_ref="DT-INT-BIFOLD56",
         position=from_node("N-M-D1", ft(0, 4))),
    # Near jamb 6 11/16" off N-M-E4, not the 1'-2 11/16" it was: the node moved north 8"
    # with the closet line (2026-08-03) and this offset came off it by the same 8" so the
    # door itself did not move — same leaf, same swing, same spot in the hall's east wall.
    # 6 11/16" is what is left between the RO and the corner, which is the D-M-MECH margin
    # (6 1/2") and clears the N-M-E4 corner stud pack; the wall is 4'-2" long now and the
    # 30" leaf plus its jacks is 3'-8" of it, so the door cannot move any further south.
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
    # O-M-HALL, the 2'-8" cased pass-through from the living room into the hall, retired
    # 2026-07-28 with its host wall W-M-C4: the whole 4'-2" it stood in is the opening now.
    # Cased pass-through: living room → dressing corridor (per floorplan).
    # Sills raised 2'-0" -> 3'-0" (2026-07-30 facade pass): the west facade's 27" units
    # all sit on the 3'-0" sill (with WIN-S-SUITE1/2 above) and its 14" units on 4'-0",
    # so every main/second head on that face lands on one 6'-0" line.
    Window(uid="CMX301AAAA", tag="WIN-M-BED-W1", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(4, 2.5)),
           sill_height=ft(3)),
    Window(uid="CMX302AAAA", tag="WIN-M-BED-W2", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(9, 6.5)),
           sill_height=ft(3)),
    # South pair: centres 4'-0" and 9'-4" are STUD LINES on W-M-S1's grid (one stud broken
    # each), stacking exactly under WIN-S-PLANT1/2 above — main and second share the wall
    # start, so the columns line up to the inch. Sill 2'-8" puts the heads at 6'-8" with
    # the doors.
    #
    # Moved 8" east off the 3'-4"/8'-8" bay centres when the units narrowed 42" -> 30"
    # (WT-3048, 2026-08-01), because the module's ideal position is a property of the RO
    # width, not of the wall: a 42" RO breaks 3 studs on a stud line and 2 on a bay centre,
    # so the bay centre was right for it; a 30" RO breaks 1 on the line and 2 off it, so
    # the same position is now the wasteful one (structural.window_framing_module, held by
    # test_catlin_contract_m3). Both south segments moved *inboard* — this pair east, the
    # W-M-S2 pair west — which keeps every RO further from a corner than it was and leaves
    # the two segments' 8" phase miss exactly where it was.
    Window(uid="CMX303AAAA", tag="WIN-M-BED-S1", host="W-M-S1",
           type_ref="WT-3048", position=from_node("N-M-SW", ft(2, 9)),
           sill_height=ft(2, 8)),
    Window(uid="CMX304AAAA", tag="WIN-M-BED-S2", host="W-M-S1",
           type_ref="WT-3048", position=from_node("N-M-SW", ft(8, 1)),
           sill_height=ft(2, 8)),
    # Offset bumped 4'-5" -> 4'-11" (2026-07-29) when N-M-W2 pushed 6" north for the
    # hall/bath2 wall move: W-M-W3's stud grid anchors off N-M-W2, so the window has
    # to move with it to stay on the same bay it was already sitting in.
    Window(uid="CMX305AAAA", tag="WIN-M-BATH2", host="W-M-W3",
           type_ref="WT-1424-T", position=from_node("N-M-W3", ft(4, 11)),
           sill_height=ft(4)),
    # Picture unit centred y=31'-4", the bench/aisle centreline (see FURN-M-MUD-BENCH in
    # plan/placeables.py). Re-authored off N-M-MECH1 (2026-08-02): the offset was written
    # as from_node("N-M-NW", 4'-1") when N-M-NW was still this wall's start, but the
    # resolver measures a from_node offset from the host's *start* node unless the named
    # node is its end node — so when the 2026-07-28 MECH split made N-M-MECH1 the start,
    # the window silently slid 2'-8" south to centre y=28'-8", out of line with the bench
    # and behind the then-furniture closet's 8' carcass. 1'-5" off N-M-MECH1 puts the
    # centre 2'-0" down the wall — a bay centre on this wall's grid (8"+16n from the
    # start node), so the 14" RO stays inside a stud bay — which is y=31'-4" exactly,
    # back on the northern segment after the N-M-MUDC1 split below it.
    # Sill raised 3'-0" -> 4'-0" (2026-07-30 facade pass) onto the west facade's 14"-unit
    # sill line, putting its head on the shared 6'-0" line with WIN-M-BATH2 and the
    # 27" units; it clears FURN-M-MUD-BENCH's 18" seat by even more than it used to.
    Window(uid="CMX306AAAA", tag="WIN-M-MUD", host="W-M-W1",
           type_ref="WT-1424-FIX", position=from_node("N-M-MECH1", ft(1, 5)),
           sill_height=ft(4)),
    # South pair: centres 27'-4" and 32'-8" are stud lines on W-M-S2's grid (16n off
    # N-M-S1), stacking exactly under WIN-S-STUDY1/2. Moved 8" west off the old
    # 28'-0"/33'-4" bay centres with the WT-3048 narrowing — see WIN-M-BED-S1/2 for why a
    # 30" RO wants the line the 42" RO could not use. The mirror of the bedroom pair about
    # x=18' would be 28'-8" and 34'-0", but the two south segments lay studs from their own
    # starts and sit 8" out of phase, so an 8" miss is as close as on-module windows can
    # mirror — the same miss this pair has always carried, in the same direction.
    # D-M-BALC's french-door RO (ends 24'-4") stays clear by 1'-9".
    Window(uid="CMX307AAAA", tag="WIN-M-LIV-S1", host="W-M-S2",
           type_ref="WT-3048", position=from_node("N-M-SE", ft(2, 1)),
           sill_height=ft(2, 8)),
    Window(uid="CMX308AAAA", tag="WIN-M-LIV-S2", host="W-M-S2",
           type_ref="WT-3048-T", position=from_node("N-M-SE", ft(7, 5)),
           sill_height=ft(2, 8)),
    # East row respaced (2026-07-30 facade pass): the facade favors within-storey
    # rhythm over between-storey stacking on this side now — the second storey runs
    # its own exact 9'-0" beat and this row runs as even as its own grid allows:
    # 4'-0" / 12'-0" / 19'-4" (8'-0" then 7'-4"; the true-even 11'-8" middle is not
    # a stud line on W-M-E1). The kitchen stretch north of WIN-M-DIN-E2 stays
    # deliberately blank. The fireplace that stood across the 4'-0" band dropped to
    # a 7" hearth mount below the sill (electrical.py). Both sills stay 2'-6": the
    # BESTA run lining this wall tops out at 29 3/4" on its 2x4 frame (placeables.py),
    # so the 30" sill line clears the countertop by 1/4" and E2 can cross the run.
    Window(uid="CMX309AAAA", tag="WIN-M-LIV-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(2, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX310AAAA", tag="WIN-M-LIV-E2", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(10, 10.5)),
           sill_height=ft(2, 6)),
    # WIN-M-DIN-E1 (CMX311AAAA) was retired in the 2026-07-30 east restack. Its two
    # candidate homes both fought the kitchen swap: stacked under survey-pinned
    # WIN-S-BED2 at 23'-4" it sat over FURN-M-KIT-N1's counter, forcing a 3'-6" sill
    # (then a shortened WT-2724) that never sat right against the row's 2'-6"/5'-6"
    # lines, and every station nearer its old 16'-0" collides with WIN-M-LIV-E2's new
    # RO. The kitchen keeps WIN-M-KITCH on the north wall; the east facade reads as a
    # three-window row with two of the three stacked exactly under the storey above.
    #
    # E2 cannot take the fourth second-floor column either: WIN-S-BED3 at 32'-4" is
    # unreachable down here — the kitchen swap put the range, hood and cooking run on
    # that stretch of wall, and every stud-line station near 32'-4" lands behind them.
    # It sits at 19'-4" (1 bay up W-M-E2) rather than its old 20'-8" so its king pack
    # keeps clear of the 23'-4" column band it used to crowd.
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
    # Relocated to the NE corner 2026-07-30 with the range/sink wall swap: it lost its old job
    # (clearing a scorched pan next to the range — the range is on the east wall now) and its
    # old spot (over the cabinet that's now FURN-M-KIT-E2/the sink run). Kept as a small
    # corner window rather than dropped: centre x=34'-0" is a bay centre on the same 16"
    # module measured off N-M-NE, clear of WIN-M-KITCH by 20 1/2" and of the corner face
    # (35'-5 3/8") by 10 3/8".
    Window(uid="82WVR597PA", tag="WIN-M-KITCH-N", host="W-M-N1", type_ref="WT-1424",
           position=from_node("N-M-NE", ft(1, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    # RM-M-HALL (CMR408AAAA) was retired into this claim on 2026-07-28, the way the second
    # storey retired RM-S-LANDING and RM-S-STAIR into RM-S-HALL when *its* centre line
    # opened. Taking W-M-C4/C4B out under BM-M-HALL leaves one polygonized face spanning the
    # living room and the old hall band, and two seeds in one face bill the floor twice.
    #
    # RM-M-STAIR (CMR410AAAA) followed it on 2026-07-30, for exactly the same reason: with
    # W-M-STRS stopped at the well partition, the up-flight's lane is open to this room and
    # the well is inside the same polygonized face. Two seeds in one face billed the 62 sf of
    # stair well twice — both claims resolved to the identical 768 sf. The 768 sf is the
    # honest area of the room you can now walk around; the stair is part of it.
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
    # The R314.3 "outside each separate sleeping area, in the immediate vicinity of the
    # bedrooms" head. It is hosted by RM-M-LIVING because that is the space it is open to,
    # but the living room's seed is out at (27', 12') in the middle of the dining end, ~13'
    # from the bedroom door — nowhere near where the detector actually goes. The position
    # below is the dressing corridor (the RM-M-CLOSET band, x 8'..18' × y 13'-4"..18'-0"),
    # centred on the corridor and directly outside D-M-BED, whose leaf runs x 13'..15'-8" in
    # W-M-BDN2. Clear of the closet's sliding doors, which take the corridor's west end.
    # y follows the corridor's centre north to 15'-8" with the 2026-08-03 wall move.
    Alarm(uid="CMA702AAAA", tag="AL-M-HALL", kind=AlarmKind.COMBO, room="RM-M-LIVING",
          circuit="CKT-LT-BACKUP", position=pt(ft(14, 4), ft(15, 8))),
]

# Electric radiant floor — the two main-storey comfort zones (2026-07-25). Neither is a
# heating system: the heat pumps carry the house and these warm the two floors people stand
# on barefoot, both of which sit just south of the 18' midline.
#
# Sizing is one number applied twice: mat at 12 W/ft2, which is what a 120V floor cable
# delivers at the `spacing=3"` serpentine authored here (12 W/ft2 over 4 lineal feet of
# cable per square foot = 3 W/ft, the working range for floor cable). The circuits in
# plan/circuits.py carry the resulting VA. `in_slab(1/2")` is the setting bed, not the
# structure: SL-M-DECK is 9" of concrete and nothing is cast into it — the mat is laid on
# the cured deck and buried in the thinset/self-leveller under the finish.
#
# Zones are drawn 4" in from every clear face, because mat cannot run to a wall. `stat` is
# the *slab sensor* point; the line-voltage thermostats are ED-M-BATH2-FH-STAT and
# ED-M-DINING-FH-STAT in plan/electrical.py.
FLOOR_HEAT = [
    # RM-M-BATH2's floor. The zone is an L around the WC, shower and tub: radiant cable
    # stays in the open south strip and the narrow centre aisle, with a deliberate 2"+
    # installation gap at every fixture footprint. Keeping the keepouts in this authored
    # polygon makes `advisory.floor_heat_fixture_keepout` verify the actual loop geometry.
    # South strip's east edge pulled in from 7'-7" to 4'-7.2", its north edge from 15'-8"
    # to 15'-6", and the centre aisle shifted west from 3'-8"..4'-0" to 3'-6"..3'-10"
    # (2026-07-29, with the BATH2 wall move): the old polygon actually ran under
    # FX-M-BATH2-SH's whole footprint, grazed FX-M-BATH2-TUB's, and clipped a sliver of
    # FX-M-BATH2-SINK's — which is what `advisory.floor_heat_fixture_keepout` was
    # catching; it just hadn't been checked against the fixtures' real footprints before.
    # All three keep >=1" clearance now.
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

# The opening is drawn to the *finished* well, not to the wall centrelines: it is the
# shaft a stair actually climbs, and the u-split resolver anchors its flights to the
# opening's near corner. West/east are W-B-STR's and W-B-CN's basement concrete faces —
# 12" concrete is thicker than the 2x6 walls stacked on it, so the basement is the
# narrowest point of the shaft and the one that sizes the flights.
#
# Run, north to south (2026-07-28): the well now *ends* on the wall instead of starting on
# one. North is W-B-N2's inside concrete face at y=35'-0", which the main deck bears on —
# the well used to stop 11 7/8" short of it and leave a slab sliver nothing could use.
#
# South is W-M-STRS's stair-side face at 26'-0 3/8", which is where the *second* storey's
# stair puts it and not a free choice. FO-S-STAIR's south edge is ST-M2S's springing point —
# its first tread starts there — so any wall north of that line would stand on that tread.
# The two wells therefore share one south edge, the stair wall's north face, and each takes
# whatever run its own north limit leaves.
#
# For this one that is 8'-11 5/8": the IRC R311.7.6 36" landing plus six 11 15/16" treads.
# Deeper than the 11" the shorter well used to give and deliberately not trimmed back to it
# — trimming would only reopen the ledge in front of D-M-STAIR. 11 15/16" against a 7 11/16"
# riser is a slow, comfortable basement flight, well inside R311.7.5.2's 10" minimum.
FLOOR_OPENINGS = [
    FloorOpening(uid="CMF601AAAA", tag="FO-M-STAIR",
                 outline=(pt(ft(10, 6), ft(26, 0.375)), pt(ft(17, 6), ft(26, 0.375)),
                          pt(ft(17, 6), ft(35)), pt(ft(10, 6), ft(35))),
                 bearing_refs=("W-M-STRW", "W-M-STRW2")),
]

# 7'-0" well = 3'-3 3/4" + 4 1/2" well partition + 3'-3 3/4". Each flight clears the
# IRC R311.7.1 36" minimum above the handrail with room for the rail to project; the
# landing is the R311.7.6 36" minimum measured in the direction of travel.
#
# `turn_direction="left"` mirrors the pair across the well (2026-07-28): the flight springs
# from the basement in the *east* lane (x 14'-2 1/4"..17'-6") and arrives on the main floor
# in the *west* one (x 10'-6"..13'-9 3/4"), which is D-M-STAIR's lane. ST-M2S is mirrored
# with it, so the east lane is now the flight *up* to the second floor, behind RO-1. Each
# arriving flight therefore lands behind D-M-STAIR and the springing one stands in the open
# lane east of the well partition, which is the arrangement it always had — the mirror
# swapped which stair each side serves.
#
# No guard is authored at the head. W-M-STRS closes the west lane and D-M-STAIR in it opens
# onto ST-B2M's top nosing; east of the well partition the edge is open to the living room,
# but ST-M2S's first tread is at floor level right on that line. Both lanes are a flight to
# step onto, not a drop to fall down.
STAIRS = [
    Stair(uid="CST701AAAA", tag="ST-B2M", floor_opening="FO-M-STAIR",
          from_storey="basement", to_storey="main", width=ft(3, 3.75),
          layout="u_split_landing", run_direction="y", turn_direction="left",
          start=pt(ft(10, 6), ft(26, 0.375)), landing_depth=ft(3)),
]

# ST-B2M handrails (R311.7.8): one wall-mounted rail per flight, `serves_stair` rakes each
# along its flight's nosing line at resolve and code.R311_7_8_handrail grades `top_height`
# (34"-38" above the nosings), continuity and graspability. Same authoring as ST-M2S's
# rails one storey up (storeys/second.py STAIR_HANDRAILS): the lower flight springs in the
# east lane (x 14'-2 1/4"..17'-6"), rail 2" off the well's east wall face, first riser at
# y 26'-0 3/8" to the lower-landing edge at 31'-0 3/8"; the upper flight climbs back south
# in the west lane (x 10'-6"..13'-9 3/4"), rail 2" off the west wall (W-M-STRW's stair
# face), landing edge down to one going past the top riser (y 26'-10 3/8").
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

# The beam that lets the main-storey centre line be open between the hall and the living
# room (2026-07-28) — the twin of BM-S-HALL one storey up, and authored the same way.
#
# CLAUDE.md's house fact is that x=18' is a bearing line from the footings to RB-HOUSE.
# This does not open it up: the LVL is the bearing line for these 4'-2", and the wall lands
# back on the stack either side.
#
# Load, per foot of beam:
#   FS-SECOND    18' tributary (half of each 18' I-joist span either side of the centre
#                line), 40 psf LL + 15 psf DL                              ~ 990 plf
# plus one point load, not a line: over this stretch the storey above has no centre wall at
# all — BM-S-HALL replaced it — so everything above (attic floor, RB-HOUSE, the second-storey
# plate) arrives as that beam's end reactions rather than as a uniform run. Its south
# reaction, ~8.1 k, lands at y=22'-4", 8" north of this beam's own south bearing.
#
# Over the 4'-2" clear span that is M = 5.7 ft-k and V = 8.9 k at the south end, most of the
# latter being that reaction going almost straight into the jack pack 8" away. Three plies
# of 1.75x11.875 LVL give Sx = 123 in^3 (26.7 ft-k at Fb = 2,600 psi) and 62 in^2 of shear
# area (11.8 k), and deflect well inside L/360 = 0.14". Same section and ply count as
# BM-S-HALL and RB-HOUSE — one LVL depth on the job — and it is the shear, not the moment,
# that sizes it.
#
# It bears on the ends of the wall segments it replaced — W-M-C3 south, W-M-C5 north — each
# of which needs a jack pack under it, and both stack onto the basement concrete centre wall
# W-B-CN and down to the footings, so the reaction has somewhere to go.
# Framed FLUSH, not dropped: `top_elevation` pins its top to the second-storey datum, which
# is top-of-joist, so FS-SECOND's I-joists hang off it in face-mount hangers and its soffit
# lands on the 9'-0" plate line of the walls either side. That keeps the 9' ceiling unbroken
# across the opening — a dropped beam would hang its full 11-7/8" into it.
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
# The two exterior doors on this storey each punch a 3'-0"/5'-0" hole in a wall that is
# otherwise the continuous shear line between the basement concrete and the roof. The
# jamb studs beside a hole that wide are where the wall's uplift and overturning collect,
# and until now nothing carried that load past the sill plate: `strap_holdown_rows`
# derives STHDs at the *ends* of each sill-plate run, not at openings in the middle of one.
#
# These four are the missing link — embedded strap-tie holdowns cast into the foundation
# wall below and nailed up onto the first-floor exterior-wall framing, one at each jamb.
# `size="STHD"` merges into the existing `[hardware]` price key rather than adding a part.
#
# Geometry. `from_node` measures to the opening *start*, so each RO is the door type's
# width run along the wall from that point:
#   D-M-ENTRY  on W-M-N3 (N-M-N2 x=10' running west): RO x 6'-6"..9'-6"
#   D-M-BALC   on W-M-S2 (N-M-S1 x=18' running east): RO x 19'-4"..24'-4"
# A jamb pack is a 1 1/2" jack plus a 1 1/2" king, so 3" outboard of the RO edge is the
# outer face of the king stud — where the strap lies, clear of the pack it restrains.
# `_JAMB_Y_*` puts them on the stud-layer centre line: CATLIN_EXT_2X6 aligns its sheathing
# exterior face to the wall line, so the 5 1/2" stud layer starts 1/2" in and centres 3 1/4"
# in — 35'-8 3/4" on the north wall (inward is -y), 3 1/4" on the south (+y). The dialect
# allows no arithmetic here, so every offset above is written out as the number it lands on.
# Elevation is mid-height of the sill plate, which sits on its 1/4" gasket at the storey
# datum — the plane the strap crosses on its way from the concrete to the studs.
#
# D-G-SERVICE is deliberately not in this list. It stands in the garage's ICF stem wall,
# not on a poured foundation wall, and an ICF-embedded holdown is a different part with a
# different embedment; that door is deferred rather than strapped with the wrong hardware.
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

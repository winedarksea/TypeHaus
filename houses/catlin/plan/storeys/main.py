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
    Post,
    RadiantSystem,
    Railing,
    RailingKind,
    Room,
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
    # is set on the three glazed types below and needs no tempered variant of any of them.
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
    # RM-M-PANTRY's bypass pair (2026-08-24). The 60" leaf the mudroom closet could not
    # have: W-M-PAN-S offers a 71 1/2" framed span, so a 62" RO leaves 4 3/4" of jamb pack
    # at each end. ** THE MUDROOM CANNOT FOLLOW IT ** — the arithmetic three lines up still
    # holds, and D-M-MUDC stays at 48".
    # Bypass and not a bifold (a bifold's leaves fold out into the cold-storage run) and not
    # a pocket (a 24" leaf would have to park inside a 30"-deep reach-in).
    DoorType(tag="DT-INT-BYPASS60", width=ft(5), height=ft(6, 8), operation="slide"),
    # D-B-PLAY's pair. Solid-core, unglazed (2026-08-21): the play room wanted the acoustic
    # separation a solid leaf gives more than it wanted borrowed light, so this is a flush
    # double-swing pair rather than a French pair — hence DOUBLE60, not FRENCH60. With no
    # glazing there is no R308.4.1 tempering to state.
    DoorType(tag="DT-INT-DOUBLE60", width=ft(5), height=ft(6, 8),
             operation="double_swing", core="solid"),
    DoorType(tag="DT-EXT-OVERHEAD192", width=ft(16), height=ft(7), exterior=True,
             operation="overhead"),
]
# One size per width family: every placement shares one height, the tallest that still
# fits the family's most constrained wall in the house. The 42" family (old WT-4242 twin
# for the raked gables) is gone as of 2026-08-01, replaced by WT-1424 there and by WT-3048
# for the south glazing. WT-2464 (24", an 18" family until 2026-08-24) is a deliberate fifth
# family, added 2026-07-31 for the attic's south juliet pair — no committed height gives that
# tall/narrow proportion.
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
    # break of "one height per family". The juliet family doesn't fit: it breaks a stud, taking a
    # 5.5"-deep header that at the nearest usable stud line (x 8'-0"/28'-0") clashes with the
    # 4:12 roof underside by 1.8". 14" lands wholly inside a bay so no header forms, and the
    # 6'-8" head (the main storey's head line) clears the rake by 2'-0". Casement, not
    # WT-1424's awning: a 48"-tall leaf is past what an awning projects.
    WindowType(tag="WT-1448", width=inch(14), height=ft(4), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 24" RO — the attic gable's juliet size (2026-07-31 as an 18x64, narrowed that day from
    # a 32" tilt-turn; widened 18" -> 24" on 2026-08-24). Still one stud broken, but the pair
    # no longer centres on the stud lines: each unit grew OUTWARD only, since the 14" pier
    # between them is bearing (see WIN-A-S-JUL-W/E in plan/storeys/attic.py). 64" tall is a
    # proportion choice, not a clearance one — head lands at 8'-0" with the storey's 2'-8"
    # sill, well clear of the rake. Casement stays: 24" is workable as a tilt-turn where 18"
    # was under the hardware's minimum frame width, but the family is casement throughout.
    # 24" also clears Andersen 400's 20-11/16" narrowest casement, which 18" did not — see
    # the "BELOW A STOCK LINE'S MINIMUM SIZE" note in prices.toml.
    WindowType(tag="WT-2464", width=inch(24), height=ft(5, 4), u_factor=u_us(0.25),
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
    # two names for the same point. It was the tee where the stair wall branched off
    # W-M-STRW2; with W-M-STRS removed (2026-08-24) it is W-M-STRW2's free south end, hence
    # `open_end` — one wall edge, and honestly so. The y stays at 25'-10" rather than pulling
    # back to the well's south edge (26'-0 3/8"): the 2 3/8" of wall past the opening is the
    # jamb return the stair face wants, and moving it would drag W-M-STRW2's alignment and
    # the exposed-stud corner detail with it for no gain.
    Node(uid="CMN015AAAA", tag="N-M-STR1", position=pt(ft(10), ft(25, 10)), open_end=True),
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
    # RM-M-PANTRY: the framed reach-in pantry in the kitchen's NW corner (2026-08-24),
    # replacing four scattered cabinets — FURN-M-KIT-PANTRY-E (48"), -TALL-N (12"),
    # -TALL-S (18") and the east run's N1/N2 bases. It closes against W-M-C5B (west) and
    # W-M-N1B (north), so only these two partitions are new.
    #
    # ** x=24'-4" IS NOT ON THE 16" MODULE, AND THAT IS FINE HERE. ** 36' - 24'-4" = 140" =
    # 8x16 + 12. It costs nothing because W-M-N1's EASTERN segment keeps
    # ``start_node="N-M-NE"`` through the split, and ``resolve/framing/stud_module.py``
    # lays a segment out from its OWN start node — so its grid cannot move no matter where
    # the far end is cut, and WIN-M-KITCH's three-storey x=28'-0" column survives.
    # 24'-4" is chosen for two reasons of its own: the partition's EAST face lands at
    # 24'-6 3/8", 5/8" of scribe off FURN-M-KIT-E1's carcass at x=24'-7", and x=24'-0"
    # would drop the framed span to 66 1/4" and kill the 60" bypass.
    #
    # y=32'-9" is what the cold-storage run can pay: the partition's south face at
    # 32'-6 5/8" takes 4 3/4" off the north end of that run, which is exactly what deleting
    # FURN-M-KIT-COLDSTORE-FILL's 6 1/4" gives back, less the 1 1/2" PANTRYC nets north.
    Node(uid="BVTKY7EE89", tag="N-M-PAN1", position=pt(ft(18), ft(32, 9))),
    Node(uid="4B6ND7KATA", tag="N-M-PAN2", position=pt(ft(24, 4), ft(32, 9))),
    Node(uid="HTWHAAG4SF", tag="N-M-PAN3", position=pt(ft(24, 4), ft(36))),
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
    # W-M-E1/W-M-E2 merged into one wall (2026-08-24) so WIN-M-EAST-MID could land inside
    # a single host instead of straddling the old N-M-E1 tee at y=18'-0" (the exact
    # midpoint between WIN-S-BED1/BED2 above). The split had mirrored the basement's
    # W-B-E1/E2 boundary and given the second storey's four east segments two distinct
    # stacking partners (W-S-E1/E2 -> here, W-S-E3/E4 -> the old W-M-E2). Both still stack
    # here now (see second.py), but the resolver links only one upper wall per lower wall,
    # so W-S-E3/E4's own stacking/foundation boundary condition is gone — accepted, not
    # fixed; re-splitting the second storey's own east wall to restore it would undo the
    # 2026-08-15 mirror-rhythm tuning that keeps WIN-S-BED1/BED2 on their stud lines.
    Wall(uid="CMW103AAAA", tag="W-M-E1", start_node="N-M-SE", end_node="N-M-NE",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    # Split at N-M-PAN3, where RM-M-PANTRY's east partition tees into the north wall
    # (2026-08-24) — ``resolve/topology.py`` builds junctions from wall ENDPOINTS only, the
    # same rule that forced the N-M-MECH* and N-M-MUDC* splits.
    #
    # ** THIS SEGMENT KEEPS ITS TAG, ITS UID AND ITS ``start_node="N-M-NE"``. THAT IS THE
    # POINT OF THE SPLIT. ** A segment's stud grid is a property of its start node, so
    # holding N-M-NE holds WIN-M-KITCH (x=28'-0", the north face's three-storey column) and
    # WIN-M-KITCH-N (x=34'-0") exactly where they are. Both ROs are east of 24'-4", so both
    # stay on this segment.
    #
    # ** BOTH SEGMENTS MUST AUTHOR ``stacks_on="W-B-N1"``, WHICH THIS WALL NEVER HAD. **
    # The basement's north wall is unsplit, so after the split it sees two main-storey
    # candidates over it and ``resolve/stacking.py`` calls that ``integrity.stack_ambiguous``
    # — an ERROR, not an advisory. An authored tiebreaker on the upper wall is what it asks
    # for. Second storey: W-S-N1B is re-pointed to W-M-N1B for the same reason (second.py).
    Wall(uid="CMW105AAAA", tag="W-M-N1", start_node="N-M-NE", end_node="N-M-PAN3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N1"),
    Wall(uid="R0STSQM95Y", tag="W-M-N1B", start_node="N-M-PAN3", end_node="N-M-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N1"),
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
    # stacks_on W-B-N4, not W-B-N3: the basement's north wall was split at this same
    # x=6'-0" line on 2026-08-23 (the ESS closet's west partition tees in there), so the
    # two storeys now break in the same place and each main segment has one wall under it.
    Wall(uid="CMW135AAAA", tag="W-M-N3B", start_node="N-M-MECH3", end_node="N-M-NW",
         assembly="CATLIN_EXT_2X6", corner_style_end="4-stud",
         alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-B-N4"),
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
    # Split at N-M-PAN1 for RM-M-PANTRY's south partition (2026-08-24), same endpoint rule
    # as W-M-N1 above. ** THE SOUTHERN HALF KEEPS THE TAG AND THE UID **: BM-M-HALL names
    # W-M-C5 in ``bearing_refs`` and bears at N-M-C3, which is this segment's start node, so
    # moving the tag to the northern half would move the beam's named support. Splitting a
    # bearing line is safe here because stacking is per-segment and W-B-CN beneath it is
    # untouched — both halves are the same assembly, the same role and the same
    # ``stacks_on``, so the load path is unchanged and only the junction framing is new.
    Wall(uid="CMW116AAAA", tag="W-M-C5", start_node="N-M-C3", end_node="N-M-PAN1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CN"),
    Wall(uid="A5K4RVWPWW", tag="W-M-C5B", start_node="N-M-PAN1", end_node="N-M-N1",
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
    # at N-M-STRJ; it then flagged the mixed-assembly L at N-M-STR1, where the 2x4 partition
    # W-M-STRS died into this wall's end stud. That L went with W-M-STRS on 2026-08-24 —
    # N-M-STR1 is a free end now and the finding is gone with the junction.
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
    # This segment's west face used to show only 1 1/4" — between W-M-STOS2's south face and
    # W-M-STRS's north face. W-M-STRS is gone (2026-08-24) and the face now runs a full 6" to
    # the free end at N-M-STR1, in the open at the head of the stairs. The exposed
    # appearance-grade studs still read as the mudroom wall's corner return turning into the
    # stairwell, which is the reason this assembly runs the whole line. `interior_room`
    # still names the mudroom: the field only picks which side layer 0 faces, and the
    # mudroom seed is on the correct (west) side of this segment's midpoint too.
    # stacks_on W-B-STR3 since 2026-08-23: W-B-STR was split at y=31'-0" for the ESS
    # closet's south partition, and this 6" segment sits wholly south of that line.
    Wall(uid="CMW134AAAA", tag="W-M-STRW2", start_node="N-M-STRJ",
         end_node="N-M-STR1", assembly="CATLIN_MUDROOM_INT_2X6_EXPOSED", top=ft(9),
         alignment=face("ply-stair-ext", offset=inch(-3.375)),
         interior_room="RM-M-MUDROOM",
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR3"),
    # The wall at the top of the stairs is gone (2026-08-24), and with it D-M-STAIR and node
    # N-M-STR2. It had been shortened twice already — to y=25'-10" in 2026-07-28 and to the
    # well partition's east face in 2026-07-30 — until the only thing left of it was a 4'-2"
    # partition that was almost entirely a 32" door leaf. Removing the door meant removing
    # the wall: it was the sole way onto ST-B2M, so a doorless wall there would have sealed
    # the basement flight off. Nothing structural bore on it (non-bearing 2x4, top 9'-0",
    # nothing stacked on it), and no guard replaces it: ST-B2M's top nosing is at main-floor
    # level on the well's south edge, so the west lane is a flight to step onto rather than a
    # drop — the same argument already made for ST-M2S's lane in the STAIRS comment below.
    # Both lanes now read open to RM-M-LIVING.
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
    # --- RM-M-PANTRY: framed reach-in pantry, kitchen NW corner (2026-08-24) ----
    # Interior clear 5'-10 1/4" (E-W) x 2'-6" (N-S): west face is W-M-C5B's east gwb at
    # 18'-3 3/8", north face W-M-N1B's at 35'-5 3/8", and these two partitions' inner faces
    # at 32'-11 3/8" and 24'-1 5/8". All three junctions are precedented — two
    # 2x4-into-host tees (as at N-M-MECH1 / N-M-MECH3) and one 2x4/2x4 L (as at N-M-MECH2).
    Wall(uid="QY8YCE6XV3", tag="W-M-PAN-S", start_node="N-M-PAN1", end_node="N-M-PAN2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="HGVY43DYQH", tag="W-M-PAN-E", start_node="N-M-PAN2", end_node="N-M-PAN3",
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
    # Centre 21'-4" (2026-08-24, was 21'-10"): D-S-DECK-E moved to 21'-4" when the two
    # balcony doors slid 1'-0" inward, and this door stands directly under it, so the south
    # face reads as one column of French pairs rather than a 6" jog. 10" of wall to the
    # inside corner at N-M-S1, the same remnant D-S-DECK-E leaves above it.
    Door(uid="CMD202AAAA", tag="D-M-BALC", host="W-M-S2", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-M-S1", ft(0, 10)), flip_swing=True),
    # Interior
    # D-M-STAIR was here — the 32" swing in the west lane, onto the flight ST-B2M arrives in.
    # Retired 2026-08-24 with its host wall W-M-STRS; see WALLS. The stair head is open.
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
    # RM-M-PANTRY's bypass pair. W-M-PAN-S's framed span is 71 1/2" (W-M-C5B's stud face at
    # 18'-2 3/4" to W-M-PAN-E's at 24'-2 1/4"), so a 62" real RO at 18'-7 1/2"..23'-9 1/2"
    # leaves 4 3/4" of framing at EACH end and clears both corner stud packs by 1 3/4" —
    # the D-M-MECH king-stud lesson applied at both ends rather than one.
    # ``integrity.opening_fits`` sees edge distances of 7 1/2"/8 1/2" against a 1.97" min.
    Door(uid="MSJJGJTJ42", tag="D-M-PANTRY", host="W-M-PAN-S", type_ref="DT-INT-BYPASS60",
         position=from_node("N-M-PAN1", inch(7.5))),
    Door(uid="CMD206AAAA", tag="D-M-BATH2", host="W-M-BDN1", type_ref="DT-INT-SWING30",
         position=from_node("N-M-W3", ft(2)), flip_swing=True, flip_hinge=True),
    # Pocket, not the 56" bifold it was (2026-08-21). The leaf parks east inside W-M-HS4,
    # which hosts nothing and now never may: `mep.pocket_occupancy` refuses a pipe, a
    # register or a wall-mounted device anywhere in the cavity, and nothing hangs on that
    # 4'-8" of hallway wall again. The uid is kept through the retype so the IFC GlobalId
    # survives, the same way the ED-*-LT luminaires were re-typed in place.
    #
    # The cavity crosses N-M-E3, where W-M-LS tees in, and that is legal here rather than
    # in general: a pocket only occupies floor to 6'-8", so this wall's double top plate
    # runs continuously above it and its bottom plate below. W-M-LS ties to both, plate to
    # plate, and only its vertical edge floats against the split jamb — a floating drywall
    # corner. Nothing over the pocket takes a fastener longer than 1"
    # (`tables.POCKET_MAX_FASTENER`) or it reaches the leaf.
    #
    # 4'-0" is the widest leaf that fits. The pocket runs 49" east of the RO and its closed
    # end carries the relocated jamb pack, which has to clear N-M-C2 — where the BEARING
    # W-M-C3 corners in and BM-M-HALL starts. Strike jamb at 8'-4" puts the closed end at
    # 16'-5", 1'-7" clear of that corner. It is also a real product size: the commodity kit
    # ladder stops at 36"/125 lb, so this one is a heavy-duty frame (DT-POCKET-INT-48).
    #
    # Clear width barely moves. The 4-leaf bifold lost ~6" to its own stacked leaves and
    # track, so it really gave ~50"; this gives 48", and hands back the 8 3/4" of floor the
    # bifold track needed (see plan/fixtures.py). The cost is ~9" of the utility tub's east
    # end sitting behind fixed wall — shifting the RO east only hides the stack instead.
    Door(uid="CMD207AAAA", tag="D-M-LAUN", host="W-M-HS3", type_ref="DT-POCKET-INT-48",
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
    # Two columns are the answer instead: 5'-0" (here) and 19'-8" (WIN-M-BATH2), on the
    # shared 6'-0" head line. There were three until 2026-08-21: WIN-M-MUD at 31'-4"
    # columned with WIN-S-BATH-W until the second-floor chase's south corners moved 3 1/8"
    # and re-phased W-S-W1's grid out from under it (plan/storeys/second.py, NODES).
    Window(uid="CMX301AAAA", tag="WIN-M-BED-W1", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(3, 10.5)),
           sill_height=ft(3)),                                                # y 5'-0"
    Window(uid="CMX302AAAA", tag="WIN-M-BED-W2", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(9, 2.5)),
           sill_height=ft(3)),                                               # y 10'-4"
    # South face, bedroom: centres 4'-0" and 14'-8", both STUD LINES on W-M-S1's grid.
    # S1 stacks under WIN-S-PLANT1; S2 stacks under D-S-DECK-W, the balcony's west French
    # pair, which moved 1'-0" inward on 2026-08-24 to share this stud line (see
    # plan/storeys/second.py). Sill 2'-8" puts heads at 6'-8" with the doors. Moved 8" east
    # off the old 3'-4"/8'-8" bay centres when units narrowed 42" -> 30" (WT-3048,
    # 2026-08-01) — a 30" RO wants a stud line, not a bay centre
    # (structural.window_framing_module, held by test_catlin_contract_m3).
    #
    # S2 was at 9'-4" until 2026-08-24. It moved 5'-4" east (four stud bays, so the grid
    # phase is unchanged) to column with D-S-DECK-W instead of with WIN-S-PLANT2.
    Window(uid="CMX303AAAA", tag="WIN-M-BED-S1", host="W-M-S1",
           type_ref="WT-3048", position=from_node("N-M-SW", ft(2, 9)),
           sill_height=ft(2, 8)),
    Window(uid="CMX304AAAA", tag="WIN-M-BED-S2", host="W-M-S1",
           type_ref="WT-3048", position=from_node("N-M-SW", ft(13, 5)),
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
    #
    # It stopped columning with WIN-S-BATH-W on 2026-08-21 and stays here anyway: the bench
    # centreline is what fixes this window, and N-M-MECH1 is on 33'-4" where it has always
    # been. It was the second storey's chase that moved.
    Window(uid="CMX306AAAA", tag="WIN-M-MUD", host="W-M-W1",
           type_ref="WT-1424-FIX", position=from_node("N-M-MECH1", ft(1, 5)),
           sill_height=ft(4)),
    # South face, living room: one unit at 32'-8", a stud line on W-M-S2's grid, stacking
    # exactly under WIN-S-STUDY1. Moved 8" west off the old 33'-4" bay centre with the
    # WT-3048 narrowing (see WIN-M-BED-S1/2). The two south segments are 8" out of phase, so
    # it carries the same phase miss off the bedroom pair's mirror as it always has.
    # D-M-BALC's french-door RO (18'-10"..23'-10") stays clear by 8'-10".
    #
    # Its partner WIN-M-LIV-S2 (27'-4", WT-3048-T, under WIN-S-STUDY2) was deleted
    # 2026-08-24: the south face reads as a column now, not a pair of pairs — see
    # WIN-M-BED-S2, which moved east to 13'-8" to stand under D-S-DECK-W.
    Window(uid="CMX307AAAA", tag="WIN-M-LIV-S1", host="W-M-S2",
           type_ref="WT-3048", position=from_node("N-M-SE", ft(2, 1)),
           sill_height=ft(2, 8)),
    # East row respaced (2026-07-30 facade pass): the facade favors within-storey rhythm
    # over between-storey stacking here, so this row runs as even as its own grid allows —
    # 4'-0" / 12'-0" (the true-even 11'-8" middle isn't a stud line on W-M-E1). Both sills
    # stay 2'-6": the BESTA run tops out at 29 3/4" (placeables.py), clearing the
    # countertop by 1/4".
    Window(uid="CMX309AAAA", tag="WIN-M-LIV-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(2, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX310AAAA", tag="WIN-M-LIV-E2", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(10, 10.5)),
           sill_height=ft(2, 6)),
    # WIN-M-LIV-E2 (old, 12'-0") and WIN-M-DIN-E2 (19'-4") retired 2026-08-24, replaced by
    # one WT-3048 unit centred as close as the 16" module allows to y=18'-0" — the exact
    # midpoint between WIN-S-BED1 (13'-0") and WIN-S-BED2 (23'-0") above. True centre falls
    # on a bay centre (residue 8" off W-M-E1's own start-node grid), and a 30" RO needs a
    # stud line, so the nearest legal station is 18'-8", 8" north of centre. W-M-E1/E2 were
    # merged into one wall (above) so this RO wouldn't straddle the old tee at y=18'-0".
    #
    # ** THIS IS NO LONGER THE ROW'S NORTH END (2026-08-24). ** The retirement note above
    # left the kitchen stretch north of here blank on purpose, and CLAUDE.md's Rows bullet
    # said so. WIN-M-KIT-E ends it at y=34'-0" — a 14" unit at a 3'-6" sill, joining neither
    # this row's beat nor its head line, deliberately. See that window at the end of this
    # list, and the rewritten Rows bullet, before reading the blank as still intended.
    Window(uid="QPNDT7TF6G", tag="WIN-M-EAST-MID", host="W-M-E1",
           type_ref="WT-3048", position=from_node("N-M-SE", ft(17, 5)),
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
    # The kitchen's second small window (2026-08-24), around the corner from
    # WIN-M-KITCH-N on the east wall, over FURN-M-KIT-N4's counter. Centre y=34'-0": 408"
    # off N-M-SE, 408 mod 16 = 8, so it is a BAY CENTRE on W-M-E1's own grid — a 14" RO
    # falls wholly inside one bay, breaks no stud and takes no header, the framing the four
    # attic WT-1424s already use. ``from_node`` is the NEAR jamb, so 33'-5" + 7" = 34'-0".
    # Sill 3'-6" (counter + 6" backsplash) and head 5'-6", matching both existing kitchen
    # units.
    #
    # ** WT-1424, NOT -FIX **: it is an operable awning, which is what answers "one of these
    # should open". WIN-M-KITCH-N beside it is already the same unit, so the corner pair is
    # two operable awnings. ** Plain glass, not -T **: no door on this wall, no stair, not a
    # wet room — R308.4 names no clause.
    #
    # ** TWO OTHER BAYS WERE CONSIDERED AND SPENT. ** y=32'-8" is also a legal bay centre,
    # and it is behind the induction cooktop under APPL-M-HOOD. y=35'-4" leaves 1 3/8" of
    # wall to the inside corner face. 34'-0" is the only bay over N4's counter — and the
    # 5 5/8" it leaves to the hood's north end is real clearance, not a lap.
    #
    # It was 33'-4" while the plan for this work was being written, on W-M-E2's grid off
    # N-M-E1. That wall no longer exists: W-M-E1/E2 were merged for WIN-M-EAST-MID
    # (2026-08-24, see its note above), and on the merged wall's own grid — which starts at
    # N-M-SE — 33'-4" is a STUD LINE. The bay centres moved 8", not the window.
    Window(uid="G0Y75W9ZS1", tag="WIN-M-KIT-E", host="W-M-E1", type_ref="WT-1424",
           position=from_node("N-M-SE", ft(33, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    # RM-M-HALL (2026-07-28) and RM-M-STAIR (2026-07-30) were both retired into this claim:
    # opening the centre line and shortening W-M-STRS left one polygonized face spanning
    # living room, old hall band and stair well, so a second seed in the same face would
    # bill the floor twice. Removing W-M-STRS outright (2026-08-24) only widens that same
    # face — the seed and the claim are unchanged. 768 sf is the honest walkable area, stair included.
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
    #
    # 2026-08-21, the floor: this and the two closets below read "sealed-concrete" until the
    # basement-ceiling overhaul put FS-M-WEST's I-joists and 3/4" plywood under all three.
    # A sealer needs a slab to seal. vinyl-sheet is already the house's answer for exactly
    # this condition (RM-S-PLANT) — homogeneous sheet, heat-welded seams, 6" integral flash
    # cove — and it is the right one for a wet entry over a wood deck.
    # integrity.concrete_finish_needs_concrete_deck fails the build if this drifts again.
    Room(uid="CMR409AAAA", tag="RM-M-MUDROOM", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.STORAGE, floor_finish="vinyl-sheet"),
    # Framed MEP shaft closet, replacing FURN-M-MUD-CLOSET-N (2026-07-28): the
    # radon+plumbing riser rides its SW corner. STORAGE is the closed enum's closest fit
    # for a mechanical closet, same reasoning as RM-M-MUDROOM above.
    Room(uid="CMR411AAAA", tag="RM-M-MECH", seed=pt(ft(3), ft(34, 6)),
         occupancy=Occupancy.STORAGE, floor_finish="vinyl-sheet"),
    # Framed south mudroom closet, replacing FURN-M-MUD-CLOSET-S (2026-08-02): the last
    # furniture closet becomes a real reach-in — 34 3/4" deep clear, bypass slider in its
    # north partition. Tagged RM-M-MUD-CLOSET because RM-M-CLOSET (CMR407AAAA) already
    # names the dressing corridor. STORAGE + the mudroom's own floor, the same closed-enum
    # reasoning as RM-M-MUDROOM/RM-M-MECH above — and the same wood deck under it.
    Room(uid="G01HFSH967", tag="RM-M-MUD-CLOSET", seed=pt(ft(3), ft(28)),
         occupancy=Occupancy.STORAGE, floor_finish="vinyl-sheet"),
    # The kitchen's framed reach-in pantry (2026-08-24), replacing FURN-M-KIT-PANTRY-E,
    # -TALL-N and -TALL-S. STORAGE for the same closed-enum reason as RM-M-MECH and
    # RM-M-MUD-CLOSET above; 14.6 SF clear, 5'-10 1/4" x 2'-6".
    #
    # ** ``floor_finish`` IS INERT HERE AND THAT IS NOT AN OVERSIGHT. ** This room stands
    # entirely on SL-M-DECK (params/main_deck.py outlines it x 18'-36', y 13'-36'), and the
    # cast cap's top IS the finished floor, so the whole 14.6 SF derives POLISHED-CONCRETE
    # regardless of the string below — the same rule that makes RM-M-LIVING's "lvp" the
    # wood-bay field finish only. Plank in here is an SL-M-DECK outline change, not a
    # string change. "lvp" is written so the intent survives if that outline ever moves.
    Room(uid="M3YNPA0YPJ", tag="RM-M-PANTRY", seed=pt(ft(21, 3), ft(34, 2)),
         occupancy=Occupancy.STORAGE, floor_finish="lvp"),
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
# bed in the thinset, not cast structure — over SL-M-DECK's cured concrete cap under the
# dining zone, and over FS-M-WEST's plywood subfloor under the bathroom, where the same 1/2"
# is an uncoupling membrane and its bed rather than thinset straight onto a slab. The two
# substrates differ; the mat, its depth and its output do not. Zones are drawn
# 4" off every clear face since mat can't run to a wall. `stat` is the slab sensor point;
# line-voltage thermostats are ED-M-BATH2-FH-STAT / ED-M-DINING-FH-STAT (plan/electrical.py).
FLOOR_HEAT = [
    # RM-M-BATH2's floor is over FS-M-WEST's I-joists since 2026-08-21, not over concrete:
    # the tile wants an uncoupling membrane over the 3/4" subfloor, and `embed` still reads
    # 1/2" because that membrane plus its bed is the same half inch the thinset was.
    # Deflection is the real difference — L/360 under an 18'-0" joist span against a slab
    # that barely moves — and `advisory.floor_finish_over_radiant` grades what sits on it.
    #
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

# The main floor's structure — two wood bays and one concrete band — lives in
# ``params/main_deck.py``, not here. It has to: the deck's depth is arithmetic (the EPS
# form plus its cap has to equal the I-joist plus its subfloor), and an editable file may
# hold only literals. Nothing about it is UI-movable, so nothing is lost by the move.
# SL-M-DECK keeps its tag and uid there; FO-M-STAIR below is now an opening in
# FS-M-WEST's joists rather than a hole in a pour.

# Drawn to the *finished* well, not the wall centrelines — the shaft the stair actually
# climbs; the u-split resolver anchors flights to its near corner. East is the basement's
# 12" concrete face (W-B-CW/CW2 at x=17'-6", which stayed 12" through the 2026-08-21
# thinning precisely because things are dimensioned off it; narrower than the 2x6 wall
# above, so it sizes the flights). West came down to x=10'-3 3/8" on 2026-08-24, when
# W-B-STR/W-B-STR3 stopped being 12" pours and became 2x6 bearing studs plumb under
# W-M-STRW's (basement.py): the well's west face is now the plywood face of that framed
# wall, one continuous plane from the basement floor to the main-storey ceiling, and the
# shaft reads 7'-2 5/8" rather than 7'-0". The edge lands *exactly* on the layer
# footprint's east limit, which is what `_opening_edge_has_declared_bearing` tests to a
# 1e-9 tolerance; if a header ever emits here, back it off to ft(10, 3.25) — 1/8" of deck
# lip is framing, not a design change. North
# (2026-07-28) is y=35'-0" — it *was* W-B-N2's inside face, and the 12" -> 8" thinning moved
# that face to 35'-4". The opening deliberately stays at 35'-0": a 4" strip of deck against
# the wall is ordinary framing, and chasing the face would perturb a stair tuned to
# 11 15/16" treads and R311.7.6's landing for no gain. South (26'-0 3/8") is fixed by FO-S-STAIR's south edge one storey up — ST-M2S's
# springing point — so both wells share that same south edge. Run here is 8'-11 5/8": IRC
# R311.7.6's 36" landing plus six 11 15/16" treads, well inside R311.7.5.2's 10" minimum.
FLOOR_OPENINGS = [
    FloorOpening(uid="CMF601AAAA", tag="FO-M-STAIR",
                 outline=(pt(ft(10, 3.375), ft(26, 0.375)), pt(ft(17, 6), ft(26, 0.375)),
                          pt(ft(17, 6), ft(35)), pt(ft(10, 3.375), ft(35))),
                 # The basement walls *under* the two long edges, not the main-storey walls
                 # that stand on them. W-M-STRW/W-M-STRW2 were named here while this hole
                 # was cut in a concrete pour and nothing framed it, so the wrong tags were
                 # harmless; since 2026-08-21 the hole is in FS-M-WEST's joists and these
                 # refs decide whether the edges are carried or get a 9'-0" LVL header
                 # (structural.floor_opening_header). W-B-STR's east face and W-B-CN's west
                 # face are the shaft's own 7'-0" faces, which is what the well is drawn to.
                 #
                 # W-B-STR3 joined the list on 2026-08-23: the ESS closet's relocation split
                 # W-B-STR at y=31'-0", and this edge runs y 26'-0 3/8"..35'-0", so the north
                 # segment alone stopped covering it. `_opening_edge_has_declared_bearing`
                 # walks the named walls' footprints and wants the WHOLE edge carried with no
                 # gap; one segment short and the resolver quietly emits a 9'-0" LVL header
                 # here instead — which it did, and `structural.floor_opening_header` FAILed
                 # it, exactly as this comment's last sentence predicted. The pour never
                 # changed; only the number of tags describing it did — and on 2026-08-24
                 # the pour became framing, which this list also does not have to notice:
                 # `_opening_edge_has_declared_bearing` reads the named walls' full layer
                 # footprints either way, and the west edge moved with them.
                 bearing_refs=("W-B-STR", "W-B-STR3", "W-B-CN")),
]

# 7'-2 5/8" well = 3'-5 1/16" + 4 1/2" well partition + 3'-5 1/16", each flight clearing
# IRC R311.7.1's 36" minimum above the handrail; landing is R311.7.6's 36" minimum.
# It read 7'-0" = two 3'-3 3/4" flights until 2026-08-24, when W-B-STR/W-B-STR3 stopped
# being 12" pours and the well's west face came down to x=10'-3 3/8" (basement.py). The
# 2 5/8" is absorbed into the two flights rather than left as a slot beside the west wall
# or handed to the partition: the flights are still the well's full width, they are wider
# than they were, and the shaft now reads exactly as FO-S-STAIR does one storey up — same
# west face, same anchor corner, 3'-1/4" narrower only because W-M-C5 is 2x6 where W-B-CN
# is 12" concrete.
# `turn_direction="left"` (2026-07-28): the basement flight springs in the east lane and
# arrives in the west (D-M-STAIR's lane until 2026-08-24; the lane is open now); ST-M2S is
# mirrored so the east lane carries the flight up to second. The head carries no guard across
# either lane and does not need one: ST-B2M's top nosing is at floor level on the west and
# ST-M2S's first tread is at floor level on the east, so both are a flight to step onto, not
# a drop. Only the 4 1/2" of well partition between them is a real edge — see STAIR_GUARDS.
STAIRS = [
    Stair(uid="CST701AAAA", tag="ST-B2M", floor_opening="FO-M-STAIR",
          from_storey="basement", to_storey="main", width=ft(3, 5.0625),
          layout="u_split_landing", run_direction="y", turn_direction="left",
          start=pt(ft(10, 3.375), ft(26, 0.375)), landing_depth=ft(3)),
]

# ST-B2M handrails (R311.7.8): one wall-mounted rail per flight, `serves_stair` rakes each
# to its flight's nosing line and code.R311_7_8_handrail grades `top_height` (34"-38"),
# continuity and graspability. Same authoring as ST-M2S one storey up (second.py
# STAIR_HANDRAILS): each rail sits 2" off its lane's wall face and runs the flight's span.
# The west rail moved 2 5/8" west on 2026-08-24 with the wall face it is mounted to
# (x=10'-3 3/8" now); the east one is on W-B-CN's concrete and did not move.
# The well partition's south end, capped (2026-08-24).
#
# W-M-STRS used to close the head of the stairs; when it and D-M-STAIR came out, both
# lanes opened to RM-M-LIVING and `code.R312_1_guard` immediately named what the wall had
# been covering by accident: FO-M-STAIR's south edge from 13'-9 3/4" to 14'-2 1/4". West of
# that is ST-B2M's throat (you step onto the flight), east of it is ST-M2S's first tread at
# floor level — but the 4 1/2" between them is the well partition's reservation, and that
# strip is open from the basement slab to the second floor. Nothing can fall *through* 4 1/2",
# but it is more than R312.1.3's 4" sphere and it is a foot-catcher at the top of a flight.
#
# So it gets closed the way its twin one storey up is: same family, same faces. This is
# RL-S-STAIRHEAD's west end continued down a floor — that guard starts at x=13'-9 3/4", the
# partition's west face, and this one runs the partition's own 4 1/2" width to 14'-2 1/4",
# where ST-M2S's throat takes over. In the field it is a newel: a post either side of a
# 4 1/2" infill panel, bolted to the trimmer closing FO-M-STAIR's south edge.
STAIR_GUARDS = [
    Railing(
        uid="QXKXMWEX1W", tag="RL-M-STAIRHEAD", type_ref="RAILING-INT-STAIR-GUARD", path=(
            pt(ft(13, 9.75), ft(26, 0.375)),
            pt(ft(14, 2.25), ft(26, 0.375)),
        ),
        kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
        base_elevation=ft(0), post_spacing=inch(60), post_size="2x2", rail_count=2,
        mount="fascia", assembly="RAILING_DARK_METAL",
        # `infill="panel"`, not the balusters its twin upstairs carries: 4 1/2" between two
        # 2x2 posts leaves no bay to picket, and authoring balusters here made
        # `code.R312_1_guard_opening` UNKNOWN — it holds a drawn gap against the authored one
        # and there is no drawn gap to hold. A solid lite admits no sphere by construction,
        # which is both what the rule wants and what gets built at this width.
        infill="panel",
    ),
]

STAIR_HANDRAILS = [
    Railing(
        uid="CMRL01AAAA", tag="RL-M-HANDRAIL-E", path=(
            pt(ft(17, 4), ft(26, 0.375)),
            pt(ft(17, 4), ft(31, 0.375)),
        ),
        kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
        base_elevation=ft(-9, -4), post_spacing=inch(48), post_size="2x2", rail_count=1,
        mount="wall", assembly="RAILING_DARK_METAL",
        role="handrail", serves_stair="ST-B2M", top_height=inch(36),
        graspable_profile="1.5in round — Type I",
    ),
    Railing(
        uid="CMRL02AAAA", tag="RL-M-HANDRAIL-W", path=(
            pt(ft(10, 5.375), ft(31, 0.375)),
            pt(ft(10, 5.375), ft(26, 10.375)),
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
# Load: the second floor's 18' tributary (~990 plf, FS-S-WEST/FS-S-EAST since 2026-08-21,
# unchanged: both still span 18' either side of this line at the same depth) plus a point
# load — BM-S-HALL above has no
# centre wall either, so everything above (attic floor, RB-HOUSE, second-storey plate)
# arrives as that beam's end reaction (~8.1 k) landing 8" north of this beam's own south
# bearing. Over the 4'-2" clear span: M = 5.7 ft-k, V = 8.9 k. Three plies of 1.75x11.875
# LVL give Sx = 123 in^3 (26.7 ft-k) and 62 in^2 shear area (11.8 k) — shear, not moment,
# governs. Same section/ply count as BM-S-HALL and RB-HOUSE (one LVL depth on the job).
#
# Bears on the ends of the walls it replaced (W-M-C3/W-M-C5), each stacking onto W-B-CN and
# the footings. Framed FLUSH (`top_elevation` at the joist datum) so FS-S-WEST and
# FS-S-EAST both hang off it and the 9' ceiling stays unbroken — a dropped beam would hang
# its full 11-7/8" into it.
BEAMS = [
    Beam(uid="CMBM01AAAA", tag="BM-M-HALL", start_node="N-M-C2", end_node="N-M-C3",
         size="3-1.75x11.875 LVL", bearing_refs=("W-M-C3", "W-M-C5"),
         assembly="BEAM_LVL", top_elevation=ft(10)),
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

# **The two columns under ST-M2S's half-landing (2026-08-21).**
#
# ST-M2S's landing is a pair of half-width platforms half a step apart, each ledgered to
# the shaft wall on its outer edge (W-M-STRW at x=10', W-M-C5 at x=18') and closed by a rim
# on the well line at x=14'-0". Those two inner rims meet no wall, so the stair resolver
# stands a 4x4 under each of their four ends — and the deck it stands them on, at the head
# of the basement stairwell, is FO-M-STAIR's hole. They were in mid-air.
#
# That was true while the deck was a 9" pour too; nobody saw it because
# `structural.landing_post_bearing` read the slab's *outline*, which does not carry its
# floor openings, as their bearing. Framing the shaft's ceiling in joists took the outline
# away and the finding surfaced.
#
# These carry them properly: two 4x4 columns on the well-partition line, top at the main
# floor and standing the basement's full height to the slab, inside the 4 1/2" the shaft's
# 7'-0" has always reserved between the two flights (see plan/storeys/basement.py's header
# note). They are hidden in the partition and clear both 3'-3 3/4" walking lanes.
#
# The y-positions are the landing rims' own ends, which the u-split resolver derives from
# the stair's start point and going. Moving ST-B2M or ST-M2S moves those ends and these
# have to move with them — `structural.landing_post_bearing` is what will say so.
#
# The north one is pulled 1 1/2" south of its rim end, to 34'-8.9": at the end itself its
# 3 1/2" section runs into the trimmer closing FO-M-STAIR's north edge (y 34'-10 3/4" to
# 35'-1 1/4"). Shifted, its north face clears that trimmer by 1/10" and the rim end is
# still 1/4" inside the post — the column carries the corner and the trimmer stays a
# separate member, which is what the framer would build.
POSTS = [
    Post(uid="A9J80KK6AE", tag="P-M-STRWELL-S", position=pt(ft(14), ft(31, 10.374)), size="4x4",
         height=ft(9, 4), assembly="POST_WHITE_PAINT"),
    Post(uid="CZE3N5C14R", tag="P-M-STRWELL-N", position=pt(ft(14), ft(34, 8.9)), size="4x4",
         height=ft(9, 4), assembly="POST_WHITE_PAINT"),
    # ST-M2S's lower landing gained a THIRD corner post on 2026-08-24, and it is a direct
    # consequence of splitting W-M-C5 for RM-M-PANTRY.
    #
    # ``resolve/stairs/bearing.py`` ledgers a landing rim to ONE host wall — the segment it
    # shares the longest run with — and marks only the rim ends that host actually reaches
    # as supported. landing-rim-lower-1 runs y 31'-10 3/8"..34'-10 3/8" against the centre
    # line; before the split one W-M-C5 covered all 36" of it. Now W-M-C5B covers the north
    # 25 3/8" and W-M-C5 the south 10 5/8", the longer one wins the ledger, and the SOUTH
    # end falls out of the interval — so the resolver stands landing-post-002 there.
    # ** There is no pantry depth that avoids this ** (the rim occupies y 31'-10 3/8"..
    # 34'-10 3/8" and a split anywhere inside that range cuts it), and moving the split
    # south of the rim would push FURN-M-KIT-PANTRYC 19 3/4" past the end of the wall it
    # backs onto — a worse trade than a 4x4.
    #
    # ** IT IS BLOCKING, NOT A COLUMN, WHICH IS WHY IT IS 13 3/8" AND NOT 9'-4". ** The two
    # P-M-STRWELL posts above stand the basement's full height because FO-M-STAIR's hole is
    # under them. This corner is not over the hole: FO-M-STAIR stops at x=17'-6" and the
    # post lands at 17'-8 5/8", on FS-M-WEST's joists — which
    # ``structural.landing_post_bearing`` deliberately refuses as a load path, since a 4x4
    # set down mid-bay is a point load on a member sized for a uniform one. So this fills
    # the joist bay from the deck datum down to W-B-CN's top at -1'-1 7/16" and delivers the
    # corner reaction straight into the 12" concrete, which is the "block the joist bay
    # under it" the check's own hint asks for.
    #
    # x=17'-7 1/2" puts its EAST face on W-M-C5's stud face (17'-9 1/4") — it laps only the
    # 5/8" gypsum, which is scribed to it, and touches no stud — while still containing the
    # rim end at 17'-8 5/8". Move ST-M2S and this moves with it, exactly as the note above
    # says of the other two.
    Post(uid="0Q6WK11T26", tag="P-M-STRLAND-SE", position=pt(ft(17, 7.5), ft(31, 10.374)),
         size="4x4", height=inch(13.4), assembly="POST_WHITE_PAINT"),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT,
            *FLOOR_OPENINGS, *STAIRS, *STAIR_GUARDS, *STAIR_HANDRAILS, *BEAMS, *PANELING,
            *POSTS, *CONNECTORS]

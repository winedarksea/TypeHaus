"""Catlin authored detail slices — A-401+.

Cut stations/crops below were verified against the resolved model (joist lines, wall
segment boundaries, ridge elevation).
"""

from typehaus import ExaggerationSpec, Slice, SliceKind, ft, inch, m, pt

from params.north_entry_frame import DETAIL_CUT_Y_FT

DETAIL_SLICES = [
    # West basement wall + footing + slab edge (cut at y=18', the mid-height bearing
    # tie-in) — crop isolates the west perimeter, away from the sunken garden.
    Slice(uid="CVD901AAAA", tag="SL-D-FNDN", kind=SliceKind.DETAIL, title="Foundation detail",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(-2), ft(-12)), pt(ft(3), ft(1))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(2))),
    # 9" SL-M-DECK seated on the 12" basement concrete cross-wall (INT_2X6_BRG
    # above) — same y=18' cut, cropped to the center bearing line at x=18'.
    Slice(uid="CVD902AAAA", tag="SL-D-DECKBRG", kind=SliceKind.DETAIL,
         title="Deck bearing detail",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(15), ft(-2)), pt(ft(21), ft(1, 6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(2))),
    # Typical exterior wall section — south wall, full height (cut x=9', away from the
    # sunken garden's x-extent). Since the sauna rotated it passes W-B-SA-N (y=10'-0")
    # rather than W-B-SA-W; the section goldens moved with it.
    # The crop's south edge was -6" until 2026-09-05 and now reaches -2'-0". W-B-BRICK moved
    # 4 1/2" south that day (its cavity grew to 6" to meet the grade beam W-SG-BRKBM), which
    # carried the wythe past -6" and silently took the veneer, its cavity and its new bearing
    # out of the "typical exterior wall" section altogether — the one drawing whose whole job
    # is to show that stack. -2'-0" holds the brick (-13 5/8"), the beam (-8"..-22") and the
    # isolation board between the beam and FT-B-S2/S3, with room to spare.
    Slice(uid="CVD903AAAA", tag="SL-D-WALLTYP", kind=SliceKind.DETAIL,
         title="Typical exterior wall section",
         cut_origin=pt(ft(9), ft(0)), cut_direction="y",
         crop=(pt(ft(-2), ft(-10)), pt(ft(6), ft(30)))),
    # Ridge beam connection — cut perpendicular to the N-S ridge (direction="x" at
    # y=18') so the section shows the ridge's peak, cropped past the beam band at
    # 31'-32' (ridge_z_m = 9.7652 m = 32.04'). The beam's soffit is at 30.87', well inside
    # the 26'-33' crop.
    Slice(uid="CVD904AAAA", tag="SL-D-RIDGE", kind=SliceKind.DETAIL,
         title="Ridge beam connection",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(10), ft(26)), pt(ft(26), ft(33)))),
    # Sauna room section — transverse cut across the sauna at y=6'. The room rotated onto
    # the garden wall on 2026-09-05 and is now 12'-2" east-west (x 5'-3 13/16"..17'-5 3/4"),
    # so the crop widens to x 4'-0"..19'-6" to keep both liner faces in the frame. y=6' is
    # still clean interior: D-B-SAUNA is on the east wall now (y 2'-10"..4'-10") and this
    # cut runs north of it.
    # This documentation-only crop reaches the floor slab, so the sauna liner base, slab
    # thermal break and room-scale vocabulary (two-tier benches, heater clearance, floor
    # slope to drain, hung drop ceiling below the main-floor deck) all render. The crop runs
    # floor-to-ceiling: z from ~9" below the floor up past the deck underside.
    Slice(uid="CVD905AAAA", tag="SL-D-SAUNA", kind=SliceKind.DETAIL,
         title="Sauna room section",
         cut_origin=pt(ft(14), ft(6)), cut_direction="x",
         crop=(pt(ft(8), inch(-116)), pt(ft(19, 6), inch(6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(1))),
    # Hall bath shower section — cut plane x=5' through FX-S-BATH1-SH so the recess,
    # tile-on-backer sides, glass panel, and (once authorable) the HRV takeoff render.
    Slice(uid="CVD906AAAA", tag="SL-D-SHOWER", kind=SliceKind.DETAIL,
         title="Hall bath shower section",
         cut_origin=pt(ft(5), ft(32, 10)), cut_direction="y",
         crop=(pt(m(8.4), m(2.7)), pt(m(11.3), m(5.8)))),
    # Breezeway cross section — the one detail that captures the whole enclosure. Cut
    # transversely (direction="x", so the plane is x-z) on the breezeway's *south frame
    # line* (``DETAIL_CUT_Y_FT``, published by params/north_entry_frame.py rather than typed here):
    # pad, pier, both floor beams, a joist, the decking, both standing polycarbonate sheets,
    # both roof beams, a rafter and its two drainage wedges, and the roof sheet.
    #
    # It does NOT cross the 6x6 post, and no station can cross both any more: the posts sit
    # 4 11/32" inboard of this line so their pier pads clear the two buildings' foundations,
    # while the joists and rafters stay on the frame line where the sheets need bearing.
    # See the post-line block in params/north_entry_frame.py.
    #
    # The crop runs from below the frost-depth pads (-4') to above the crown (+8'-6"), and
    # 9" past the 4'-6" glazing envelope (x = 6'-9" to 11'-3") on each side. **It was
    # x = 1'-6"..7'-6" until 2026-09-03 and x = 5'-0"..11'-0" until 2026-09-09** — and each
    # time the enclosure moved, this crop was the thing that did not, so the drawing quietly
    # cropped off part of its own subject. The 2026-09-09 widening to 4'-6" put GL-BW-WALL-E
    # and its sill and hatch trim 3" OUTSIDE the old x=11'-0" edge, and the section goldens
    # recorded three elements simply vanishing. The enclosure and its `_EW_FT` /
    # `_GLAZING_CENTER_X` are themselves retired now — the extruded garage gable replaced
    # them — so what this crop must follow today is the north-entry frame:
    # ** IF `params/north_entry_frame.py`'s FRAME_Y0_FT/FRAME_Y1_FT OR THE COLUMN LINE
    # MOVES, MOVE THIS TOO ** — nothing links them and no check grades a crop against the
    # thing it is meant to show.
    Slice(uid="BWD901AAAA", tag="SL-D-BREEZEWAY", kind=SliceKind.DETAIL,
         title="North entry: gable, bridge landing and east tiers",
         cut_origin=pt(ft(0), ft(DETAIL_CUT_Y_FT)), cut_direction="x",
         crop=(pt(ft(4), ft(-4)), pt(ft(32), ft(16))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(1))),
    # Cut on D-G-SERVICE's centreline: x=8'-1" since the door moved into the garage's SW
    # corner (2026-09-11; it was 10'-0"). Nothing links this to SERVICE_DOOR_OFFSET.
    Slice(uid="BWD902AAAA", tag="SL-D-NORTH-BRIDGE", kind=SliceKind.DETAIL,
         title="North entry longitudinal foundation and threshold section",
         cut_origin=pt(ft(8, 1), ft(0)), cut_direction="y",
         crop=(pt(ft(34), ft(-11)), pt(ft(52), ft(16)))),
    # ** THE DRAWING THAT PROVES THE ATTIC CHANGE, AND THE ONE THAT WOULD CATCH IT COMING
    # UNDONE. ** FO-A-HALL takes the attic deck away over x 10'-0"..18'-0", so the stair
    # hall runs open from the second floor to the roof underside. Nothing about that is
    # visible in plan — a hole in a deck and a deck look identical from above — and a
    # single number in `FS-ATTIC.openings` is all that stands between this volume and a
    # gypsum lid at 9'-0". This cut is where that shows.
    #
    # y=30'-0" is chosen, not rounded to: it is inside the void (y 22'-6 3/8"..35'-5 3/8")
    # and clear of both trimmer pairs, north of BM-S-HALL's end at 30'-10" and south of the
    # north gable, so the cut crosses open air rather than framing at both x=10' and x=18'.
    #
    # The crop spans x 6'-0"..22'-0" and z 8'-0"..33'-0", and every bound earns its place:
    # west of the void it takes in W-A-BA-E and the storage pocket's deck, so the section
    # shows the deck STOPPING rather than simply being absent; east of it, W-A-C2B and
    # RB-HOUSE at the ridge (soffit ~30'-10"). The bottom at 8'-0" reaches below the second
    # floor so the full 9'-0"-to-roof height of the volume reads at once.
    #
    # ** WHAT TO LOOK FOR: NO CEILING PLANE ACROSS x 10'..18' AT z ~19'-11". ** One drawn
    # there means `resolve/ceilings.py` has stopped subtracting deck openings, or
    # FO-A-HALL has fallen out of `FS-ATTIC.openings`.
    Slice(uid="CVD907AAAA", tag="SL-D-STAIRVOID", kind=SliceKind.DETAIL,
         title="Stair hall void section",
         cut_origin=pt(ft(0), ft(30)), cut_direction="x",
         crop=(pt(ft(6), ft(8)), pt(ft(22), ft(33)))),
]

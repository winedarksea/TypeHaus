"""Catlin authored detail slices — A-401+.

Cut stations/crops below were verified against the resolved model (joist lines, wall
segment boundaries, ridge elevation).
"""

from typehaus import ExaggerationSpec, Slice, SliceKind, ft, inch, m, pt

from params.breezeway import DETAIL_CUT_Y_FT

DETAIL_SLICES = [
    # West basement wall + footing + slab edge (cut at y=18', the mid-height bearing
    # tie-in) — crop isolates the west perimeter, away from the sunken garden.
    Slice(uid="CVD901AAAA", tag="SL-D-FNDN", kind=SliceKind.DETAIL, title="Foundation detail",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(-2), ft(-12)), pt(ft(3), ft(1))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(2))),
    # 9" SL-M-DECK seated on the 12" basement concrete cross-wall (CATLIN_INT_2X6_BRG
    # above) — same y=18' cut, cropped to the center bearing line at x=18'.
    Slice(uid="CVD902AAAA", tag="SL-D-DECKBRG", kind=SliceKind.DETAIL,
         title="Deck bearing detail",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(15), ft(-2)), pt(ft(21), ft(1, 6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(2))),
    # Typical exterior wall section — south wall, full height (cut x=9', away from the
    # sunken garden's x-extent).
    Slice(uid="CVD903AAAA", tag="SL-D-WALLTYP", kind=SliceKind.DETAIL,
         title="Typical exterior wall section",
         cut_origin=pt(ft(9), ft(0)), cut_direction="y",
         crop=(pt(ft(0, -6), ft(-10)), pt(ft(6), ft(30)))),
    # Ridge beam connection — cut perpendicular to the N-S ridge (direction="x" at
    # y=18') so the section shows the ridge's peak, cropped past the beam band at
    # 31'-32' (ridge_z_m = 9.7652 m = 32.04'). The beam's soffit is at 30.87', well inside
    # the 26'-33' crop.
    Slice(uid="CVD904AAAA", tag="SL-D-RIDGE", kind=SliceKind.DETAIL,
         title="Ridge beam connection",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(10), ft(26)), pt(ft(26), ft(33)))),
    # Sauna room section — transverse cut across the 8'-wide sauna (x=10'→18') at y=6',
    # below the door (D-B-SAUNA sits high on the west wall) so the cut is clean interior.
    # This documentation-only crop reaches the floor slab, so the sauna liner base, slab
    # thermal break and room-scale vocabulary (two-tier benches, heater clearance, floor
    # slope to drain, hung drop ceiling below the main-floor deck) all render. The crop runs
    # floor-to-ceiling: z from ~9" below the floor up past the deck underside.
    Slice(uid="CVD905AAAA", tag="SL-D-SAUNA", kind=SliceKind.DETAIL,
         title="Sauna room section",
         cut_origin=pt(ft(14), ft(6)), cut_direction="x",
         crop=(pt(ft(9), inch(-116)), pt(ft(19, 6), inch(6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(1))),
    # Hall bath shower section — cut plane x=5' through FX-S-BATH1-SH so the recess,
    # tile-on-backer sides, glass panel, and (once authorable) the HRV takeoff render.
    Slice(uid="CVD906AAAA", tag="SL-D-SHOWER", kind=SliceKind.DETAIL,
         title="Hall bath shower section",
         cut_origin=pt(ft(5), ft(32, 10)), cut_direction="y",
         crop=(pt(m(8.4), m(2.7)), pt(m(11.3), m(5.8)))),
    # Breezeway cross section — the one detail that captures the whole enclosure. Cut
    # transversely (direction="x", so the plane is x-z) on the breezeway's *south frame
    # line*, which is the only station that crosses the entire stack at once: pad, pier,
    # 6x6 post, both floor beams, a joist, the decking, both standing polycarbonate sheets,
    # both roof beams, a rafter, and the roof sheet with its crown. The crop runs from below
    # the frost-depth pads (-4') to above the crown (+8'-6"), and 1'-0" past the 4'-0"
    # glazing envelope (x = 2'-6" to 6'-6") on each side, which also takes in the 2'-square
    # pads under the posts.
    Slice(uid="BWD901AAAA", tag="SL-D-BREEZEWAY", kind=SliceKind.DETAIL,
         title="Breezeway cross section",
         cut_origin=pt(ft(0), ft(DETAIL_CUT_Y_FT)), cut_direction="x",
         crop=(pt(ft(1, 6), ft(-4)), pt(ft(7, 6), ft(8, 6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(1))),
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

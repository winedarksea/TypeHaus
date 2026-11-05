"""Catlin authored detail slices — A-401+.

Cut stations/crops below were verified against the resolved model (joist lines, wall
segment boundaries, ridge elevation).
"""

from typehaus import ExaggerationSpec, Slice, SliceDimension, SliceKind, ft, inch, m, pt

from params.cladding import HOUSE_EW_OUTBOARD_IN
from params.north_entry_frame import DETAIL_CUT_Y_FT
from params.roof_panel import EAVE_DECK_IN

#: The east eave's cladding face (== RF-HOUSE's footprint edge) and its deck plane, inches.
_EAVE_FACE_E_IN = 36 * 12 + HOUSE_EW_OUTBOARD_IN


def _z(start, end, at, text=None, offset=None):
    """A vertical (elevation) string; anchors are ``TAG:face`` or ``storey:<tag>``."""
    return SliceDimension(start=start, end=end, axis="z", at=at, text=text, offset=offset)


def _u(start, end, at, text=None, offset=None):
    """A horizontal string across the cut."""
    return SliceDimension(start=start, end=end, axis="u", at=at, text=text, offset=offset)


def _risers(anchors, at, overall_at, which):
    """Equal risers: riser ``which`` (one whose label clears the slabs), and the overall
    rise with the riser count. A chain of 6" risers cannot hold a label per riser below
    1/2" = 1'-0"."""
    count = len(anchors) - 1
    return (_z(anchors[which], anchors[which + 1], at, "{} riser"),
            _z(anchors[0], anchors[-1], overall_at, "{} (" + str(count) + " EQ.)"))


def _chain(axis, anchors, at, texts=(), offset=None):
    """Consecutive strings on one line — they chain, and their labels stagger."""
    make = _z if axis == "z" else _u
    labels = list(texts) + [None] * len(anchors)
    return tuple(make(anchors[i], anchors[i + 1], at, labels[i], offset)
                 for i in range(len(anchors) - 1))


#: A-508's tier stair (S2-004): risers walk -> four tiers -> deck, goings deck edge -> walk,
#: read off the slabs themselves. A-509's service stair by its own risers.
_TIERS = ("SL-WK-C", "SL-BW-TIER1", "SL-BW-TIER2", "SL-BW-TIER3", "SL-BW-TIER4")
_TIER_RISERS = _risers(tuple(t + ":top" for t in _TIERS) + ("FS-BW-FLOOR:top",), inch(194),
                       inch(202), 2)
_TIER_GOINGS = _chain("u", ("FS-BW-FLOOR:right",) + tuple(t + ":right" for t in _TIERS[:0:-1]),
                      inch(4))
_SERVICE_RISERS = _risers(tuple("ST-G-SERVICE:riser:" + str(i) for i in range(6)),
                          inch(578), inch(586), 3)

DETAIL_SLICES = [
    # West basement wall + footing + slab edge (cut at y=18', the mid-height bearing
    # tie-in) — crop isolates the west perimeter, away from the sunken garden.
    Slice(uid="CVD901AAAA", tag="SL-D-FNDN", kind=SliceKind.DETAIL, title="Foundation detail",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         dimensions=(
             _z("storey:basement", "storey:main", inch(30), "{} fl. to fl."),
             _z("W-B-W1:bottom", "W-B-W1:top", inch(14), "{} fdn wall")),
         crop=(pt(ft(-2), ft(-12)), pt(ft(3), ft(1))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(2))),
    # FS-M-NE's open-web trusses seated on W-B-E1 (decision #112): the 3" seat, the PT
    # mudsill and gasket on the pour, the MASA anchor and the A35Z seat tie. Cut on the
    # y=15'-8" truss line (lines at 156 + 16k", decision #112), cropped to the east bearing.
    # Tag and uid kept from the BuildDeck bearing detail it replaces.
    Slice(uid="CVD902AAAA", tag="SL-D-DECKBRG", kind=SliceKind.DETAIL,
         title="Floor truss bearing detail",
         cut_origin=pt(ft(0), ft(15, 8)), cut_direction="x",
         dimensions=(
             _z("FS-M-NE:bottom", "FS-M-NE:top", inch(408), "{} truss"),) + _chain(
             "u", ("W-B-E1:left", "W-B-E1:right"), inch(-20), ("{} fdn wall",)),
         crop=(pt(ft(33), ft(-2)), pt(ft(38, 6), ft(1, 6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(2))),
    # Typical exterior wall section — south wall, full height (cut x=10', through
    # WIN-S-PLANT2; it was x=9' until the court narrowed on 2026-09-22, which put that line on W-SG-W1's axis and west of the brick
    # and the framed walkout, both of which now start at 9'-10"). Since the sauna rotated it passes W-B-SA-N (y=10'-0")
    # rather than W-B-SA-W; the section goldens moved with it.
    # The crop's south edge was -6" until 2026-09-05 and now reaches -2'-0". W-B-BRICK moved
    # 4 1/2" south that day (its cavity grew to 6" to meet the grade beam W-SG-BRKBM), which
    # carried the wythe past -6" and silently took the veneer, its cavity and its new bearing
    # out of the "typical exterior wall" section altogether — the one drawing whose whole job
    # is to show that stack. -2'-0" holds the brick (-13 5/8"), the beam (-8"..-22") and the
    # isolation board between the beam and FT-B-S2/S3, with room to spare.
    Slice(uid="CVD903AAAA", tag="SL-D-WALLTYP", kind=SliceKind.DETAIL,
         title="Typical exterior wall section",
         cut_origin=pt(ft(10), ft(0)), cut_direction="y",
         dimensions=_chain(
             "z", ("storey:basement", "storey:main", "storey:second", "storey:attic",
                   "W-A-S2:top"), inch(40),
             ("{} bsmt", "{} main", "{} second", "{} to plate")),
         crop=(pt(ft(-2), ft(-10)), pt(ft(6), ft(30)))),
    # Ridge beam connection — cut perpendicular to the N-S ridge (direction="x" at
    # y=18') so the section shows the ridge's peak, cropped past the beam band at
    # 31'-32' (ridge_z_m = 9.7652 m = 32.04'). The beam's soffit is at 30.87', well inside
    # the 26'-33' crop.
    Slice(uid="CVD904AAAA", tag="SL-D-RIDGE", kind=SliceKind.DETAIL,
         title="Ridge beam connection",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         dimensions=(
             _z("W-A-C2M:top", "RF-HOUSE:top", inch(232), "{} plate to ridge"),),
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
         dimensions=_chain("z", ("storey:basement", "FURN-B-SAUNA-STEP:top",
                                  "FURN-B-SAUNA-LOWER:top", "FURN-B-SAUNA-UPPER:top",
                                  "CEIL-RM-B-SAUNA:bottom"), inch(196)) + (
             _z("storey:basement", "CEIL-RM-B-SAUNA:bottom", inch(204), "{} headroom"),
             _u("FURN-B-SAUNA-UPPER:left", "FURN-B-SAUNA-UPPER:right",
                "FURN-B-SAUNA-UPPER:top", offset=inch(3)),
             _u("FURN-B-SAUNA-LOWER:left", "FURN-B-SAUNA-LOWER:right",
                "FURN-B-SAUNA-LOWER:top", offset=inch(3)),
             _u("FURN-B-SAUNA-STEP:left", "FURN-B-SAUNA-STEP:right",
                "FURN-B-SAUNA-STEP:top", offset=inch(3))),
         crop=(pt(ft(8), inch(-116)), pt(ft(19, 6), inch(6))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(1))),
    # Through the reading platform and heater: the back points west, feet east.
    Slice(uid="RP18WM2C5X", tag="SL-D-SAUNA-READING", kind=SliceKind.DETAIL,
         title="Sauna window-side reading recliner",
         cut_origin=pt(ft(14), inch(24)), cut_direction="x",
         dimensions=(
             _z("storey:basement", "FURN-B-SAUNA-READING:top", inch(187), "{} deck"),
             _z("EQ-B-SAUNA-HTR:top", "CEIL-RM-B-SAUNA:bottom", inch(204),
                "{} htr to clg"),
             _u("FURN-B-SAUNA-READING:right", "EQ-B-SAUNA-HTR:left",
                "EQ-B-SAUNA-HTR:top", "{} to htr", inch(-10))),
         crop=(pt(ft(9, 6), inch(-116)), pt(ft(19, 6), inch(6))),
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
    # The crop must follow the north-entry frame (the breezeway enclosure is retired, and
    # this tag was renamed off it in C7-E6):
    # ** IF `params/north_entry_frame.py`'s FRAME_Y0_FT/FRAME_Y1_FT OR THE COLUMN LINE
    # MOVES, MOVE THIS TOO ** — nothing links them and no check grades a crop against the
    # thing it is meant to show.
    Slice(uid="BWD901AAAA", tag="SL-D-NORTH-ENTRY", kind=SliceKind.DETAIL,
         title="North entry: gable, bridge landing and east tiers",
         cut_origin=pt(ft(0), ft(DETAIL_CUT_Y_FT)), cut_direction="x",
         dimensions=_TIER_RISERS + _TIER_GOINGS,
         crop=(pt(ft(4), ft(-4)), pt(ft(32), ft(16))),
         exaggeration=ExaggerationSpec(min_draw_thickness=inch(1))),
    # Cut on D-G-SERVICE's centreline: x=8'-3" with the 32in leaf and 11in offset
    # (2026-10-25; east jamb remains x=9'-7"). Nothing links this to SERVICE_DOOR_OFFSET.
    Slice(uid="BWD902AAAA", tag="SL-D-NORTH-BRIDGE", kind=SliceKind.DETAIL,
         title="North entry longitudinal foundation and threshold section",
         cut_origin=pt(ft(8, 3), ft(0)), cut_direction="y",
         dimensions=_SERVICE_RISERS,
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
         dimensions=_chain(
             "z", ("storey:second", "storey:attic", "W-A-C2B:top"), inch(196),
             ("{} 2nd fl. to attic", "{} to ridge beam")) + (
             _u("W-A-BA-E:right", "W-A-C2B:left", inch(250), "{} void"),),
         crop=(pt(ft(6), ft(8)), pt(ft(22), ft(33)))),
    # ** THE FIREPLACE BREAST, AND THE ONLY SliceKind.SECTION IN THE HOUSE. ** Every other
    # slice here is a DETAIL and lands in the A-5xx block; a SECTION joins the A-301 series
    # straight after the auto centre section (`emit/draw/sheets.py`), so this prints as
    # A-301.1 with no engine change at all.
    #
    # W-M-FIRE is five walls chained by hand — each base_elevation is the one below plus
    # that one's top — and `integrity.wall_stack_continuous` now grades that chain. This is
    # the same chain DRAWN, which is the other half of trusting it: a reviewer can see the
    # courses land on each other instead of taking a PASS on faith.
    #
    # y=8'-8" is derived, not rounded to. The panel runs y 6'-9 1/4"..10'-6 3/4" and the
    # two jambs stop at 7'-5 1/4" and restart at 9'-10 3/4", so the firebox is y 7.438..
    # 9.896 ft and its mid-station is 8.667 ft. The cut therefore passes THROUGH the
    # opening — catching STUB, PLINTH and HEAD, which span the full panel, and missing both
    # jambs, which is exactly what puts the 20 5/8" firebox on the paper as a void.
    #
    # Verified against the resolved model at this station, bottom to top: FT-B-E1
    # (-9'-9 1/2"..-9'-1 1/2"), SL-B-FLOOR, the gym ceiling at -1'-0 1/2", W-B-E1/W-M-E1
    # carrying the breast, then STUB (-1'-1 7/16"..0'-0 15/16"), PLINTH (..2'-0 15/16"),
    # the firebox, BM-M-FIRE-LINTEL (3'-9 5/8"..4'-1 1/8") and HEAD (..5'-4 15/16"), with
    # CEIL-RM-M-LIVING closing the volume at 9'-0 1/8". The crop's -10'-6" reaches under the
    # footing and its 10'-0" clears that ceiling, so the whole load path reads at once.
    #
    # ** ONE THING THIS SHEET WILL NOT SHOW, AND IT IS NOT A BUG. ** `build_section` never
    # draws placeables, so EQ-M-FIREPLACE and FURN-M-FIRE-MANTEL are absent — the masonry is
    # the subject and the appliance is not.
    #
    # ** IT IS ANNOTATED SINCE 2026-09-20, AND THIS BLOCK SAID THE OPPOSITE. ** It read: "an
    # AUTHORED section is not annotated: only `build_center_section` adds datum lines and
    # room names, so this one carries its geometry unlabelled. Do not 'fix' either by
    # reaching for the centre-section path." That was true and it was a gap, not a decision —
    # a drawing a reader cannot take a dimension off is not a construction document.
    # `build_annotated_section` is one path now, serving both this sheet (A-301.1) and
    # `haus render --view section --slice SL-S-FIRE`, and nothing in the annotation was ever
    # specific to the house centre: it takes a cut plane, and an authored cut has one. What
    # it did not have is this slice's CROP, which the room names and the detail callouts need
    # — they walk the MODEL rather than the drawing, and lettered eight rooms and hung four
    # bubbles out in open sheet before they were clipped to it.
    Slice(uid="CVD908AAAA", tag="SL-S-FIRE", kind=SliceKind.SECTION,
         title="Fireplace breast section",
         cut_origin=pt(ft(0), ft(7, 4)), cut_direction="x",
         # ft(-10, 6) would be -10*12+6 = -9'-6", not -10'-6" — ft(f, i) is f*12+i and the
         # sign does not distribute. Written as a single negative foot value on purpose.
         crop=(pt(ft(30), ft(-10.5)), pt(ft(38), ft(10)))),
    # ** THE CROP IS LOAD-BEARING TWICE OVER NOW. ** It has always bounded the geometry; since
    # the annotation arrived it also bounds the room names and the detail callouts. Widen it
    # and this sheet starts lettering RM-M-LIVING and bubbling details from the far side of
    # the house; narrow it and the load path stops reading. -10'-6" reaches under the footing
    # and 10'-0" clears CEIL-RM-M-LIVING at 9'-0 1/8", which is the whole span worth showing.
    # The RF-HOUSE east eave enlarged (3" = 1'-0"): Image II Extended Eave, pan hem, strip-in,
    # box gutter. y=17'-4" is MID-PAN — the pans are 16" on seams at 16'-8" and 18'-0", so the
    # cut shows the pan's hem around the eave's hook rather than a seam stub. The crop is
    # 16 1/2" x 14": 7" inboard of the cladding face (the strip-in's lap onto the field
    # membrane) to 9 1/2" out (past the gutter front), 9" below the deck plane at the eave
    # (under the trough) to 5" above. Leaders come from the
    # zero-overhang eave overlay, run for any authored detail whose crop holds an eave.
    Slice(uid="PWAJW7KF6Y", tag="SL-D-EAVE", kind=SliceKind.DETAIL,
         title="East eave: Image II eave, pan hem and box gutter",
         cut_origin=pt(ft(0), ft(17, 4)), cut_direction="x",
         dimensions=(
             _u("RF-HOUSE:right", "TR-RF-GUTTER-E-1:right", "TR-RF-GUTTER-E-1:top",
                "{} gutter proj.", inch(2.5)),),
         crop=(pt(inch(_EAVE_FACE_E_IN - 7), inch(EAVE_DECK_IN - 9)),
               pt(inch(_EAVE_FACE_E_IN + 9.5), inch(EAVE_DECK_IN + 5))),
         scale="3\"=1'"),
]

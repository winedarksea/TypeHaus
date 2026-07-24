"""Catlin authored detail slices — A-401+ (→ Permit-ready plan set Phase 6).

The section/detail machinery (emit/draw/section.py) already fully supports authored
Slices with crop + exaggeration; the permit set just never used it for details before
this phase. Cut stations/crops below were verified against the resolved model (joist
lines, wall segment boundaries, ridge elevation) — see the module docstring notes.
"""

from typehaus import ExaggerationSpec, Slice, SliceKind, ft, inch, pt

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
    # y=18') so the section shows the ridge's peak, cropped around ridge_z_m (~29').
    Slice(uid="CVD904AAAA", tag="SL-D-RIDGE", kind=SliceKind.DETAIL,
         title="Ridge beam connection",
         cut_origin=pt(ft(0), ft(18)), cut_direction="x",
         crop=(pt(ft(10), ft(26)), pt(ft(26), ft(31)))),
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
]

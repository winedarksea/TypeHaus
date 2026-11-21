"""The second floor's deck, split at the centre bearing line: trusses west, joists east.

Every second-floor service that has to cross the joist run — the plumbing stacks and
supply risers serving ``RM-S-PLANT``/the suite bath cluster, the radon/plumbing chase, the
hydrant distribution, the data conduits — is west of x=18', so that half is where open-web
trimmable floor trusses pay for themselves: services cross *through* the webs (8 7/8" clear
chord-to-chord) instead of being bored, soffited or chased. The east half is bedrooms and a
study with only incidental crossings, so it keeps the cheaper TJI 230 I-joist.

Both members are the same 11 7/8" depth, deliberately — the deck plane, the finished floor
and the ceiling below all stay flat across the split, exactly as the wood/wood halves of
``params/main_deck.py`` do. Unlike that module's concrete/wood boundary, this one needs
**no movement joint and no finish break**: same depth, same stiffness class, one
continuous ceiling plane. ``notes/mixed_deck_movement_joint.md`` does not apply here.

**Why two FloorSystems and not one.** Same reasoning as ``main_deck.py``:
``FloorSystem.outline`` scopes only the perpendicular extent, and span boundaries come
from the bearing refs' axis midpoints — one system naming all three bearing lines would
frame joists straight through the material change at x=18'. ``BM-M-HALL``'s axis midpoint
in x is 18', the same as ``W-M-C2``, so including it in both halves' bearing_refs injects
no third span boundary.

**Why a params module and not the editable storey file.** Same reason as
``main_deck.py`` (its own docstring, lines 43-47): the shared depth wants to be one
constant, and an editable file may hold only literals and cannot import from ``params/``.
FloorSystems are not UI-movable, so nothing is lost by keeping this out of
``plan/storeys/second.py`` — and it lets ``main_deck.py`` import the depth from here
instead of restating it, since the concrete band's depth derivation matches whatever this
module's members share.

**Known cost of the west/trusses choice.** ``FO-S-STAIR`` (x 10'-3⅜"..17'-8⅝",
y 26'-0⅜"..35'-5⅜") lands in the west half. Five joist lines clip to about 10'-0¾" there
and are cut from 12' stock, 11.65" off each end, inside TrimJoist's 12" limit
(``OpenWebShape``). The opening's parallel edges (running
with the joist direction) resolve to doubled truss members — the correct real detail, a
girder-truss pair; its perpendicular edges already resolve to multi-ply LVL headers via
``opening_header_profile``.

**Stock, and what the truss is built to.** TrimJoist J12 stock runs 4'-24' in 2' increments,
each end trimmable up to 12" (an OSB TrimEnd). The west field's *bearing grid* is 18'-0";
the truss is **17'-11"** —
``resolve/floor_ends.py`` cuts it to where it stops, behind the 1 1/4" rim at the west
framing face and 3 1/2" onto the x=18' plate. Clear span 17'-3 1/4". An 18' blank trimmed
1" in all still covers it (``takeoff/framing.py::_order_length_ft``), but 17'-11" is the number on
the fabricator's order, which ``haus takeoff``'s fabrication schedule states.
"""

from typehaus.geometry import rect
from plan.framing_standards import SUBFLOOR_FASTENING
from params.sill_seat_backers import BALCONY_SEAT_BACKERS
from typehaus import (DeckLayer, FloorSystem, JoistSpec, JoistReinforcement, Layer,
                      LayerFunction, PublishedSpan, PublishedWebOpenings, ft, inch, pt)

# Both members share one depth, deliberately — see the module docstring. ``main_deck.py``
# imports ``_DEPTH``/``_SUBFLOOR`` from here rather than restating them, so the concrete
# band's depth derivation can never drift from what this deck actually frames.
_TRUSS = "11.875 floor truss"
# TJI 230 house-wide (owner, 2026-11-01, C3-E4): the roof's series, so one flange (2 5/16")
# and one hanger (IUS2.37/11.88). The generic "11.875 I-joist" was a 2 1/2" flange no
# maker sells.
_JOIST = "11.875 TJI 230"
_DEPTH = inch(11.875)
_OC = inch(16)
# 23/32" plywood, modelled at its 3/4" nominal on every deck (notes/floor_heights.md).
_SUBFLOOR = inch(0.75)

# Every TJI floor field in the house reads this one row (main_deck.py, FS-S-EAST; FS-ATTIC
# restates it, being editable). The 40/20 column covers tile and mortar beds; L/480 is
# Weyerhaeuser's recommendation over the code's L/360 (21'-11").
TJI_230_FLOOR_SPAN = PublishedSpan(
    source="Weyerhaeuser TJ-4000 Trus Joist TJI Joist Specifier's Guide (July 2025) p.7, \"Floor Span Tables\"",
    table="L/480 live load deflection, 40 PSF live / 20 PSF dead, 11-7/8\" TJI 230 at 16\" o.c.: 19'-10\"",
    member=_JOIST,
    span=ft(19, 10),
    load_psf=40.0,
    spacing=_OC,
    edition="July 2025",
    page="7",
    condition="clear distance between supports, uniform loads, the more restrictive of simple or continuous span; single layer of 24\" o.c. span-rated GLUE-NAILED floor panels (reduce 6\" if nailed only); 1 3/4\" minimum end bearing without web stiffeners, 3 1/2\" intermediate; long-term creep under dead load not considered; point loads (the RM-M-BATH2 tub, the WashTower) are outside the row and answered by the JoistReinforcement blocking",
)

# FS-M-NE's open-web trusses at 16" o.c. (decision #112). The 17.92' tip-to-tip blank is
# inside the 18'-0" row; the peninsula's point load is answered by a doubled truss
# (``params/main_deck.py``), and the bounce by two strongbacks.
TRIFORCE_OJ418S_FLOOR_SPAN = PublishedSpan(
    source="TRIFORCE (Open Joist) U.S. Specifier Guide, \"Maximum Allowable Spans\" floor table",
    table="L/480 live load deflection, 40 PSF live / 25 PSF dead, 11-7/8\" OJ418S (18' stock) at 16\" o.c.: 18'-0\"",
    member=_TRUSS,
    span=ft(18),
    load_psf=40.0,
    spacing=_OC,
    edition="2023-05-11",
    page="5",
    condition="glue-nailed 23/32\" floor panels; 1 1/2\" minimum end bearing; uniform load only; OJ418S as the basis of design (any fabricator's 11 7/8\" truss to the same row); the 25 psf dead-load column; point loads (the peninsula) are outside the row and answered by the doubled truss; L/720 live is on the order for a stiffer floor",
)

# TRIFORCE's published web opening (p.19, read 2026-11-06): 7 1/4" round, 5 3/4" square or
# 3 x 13 through the diagonal webs of an 11 7/8" joist. p.4 draws 2x2 diagonals "24" o.c. typ."
# and ONE 34 1/8" OSB end panel (trimmable to 24", either end; one <= 1 1/2" hole in it, else
# TRIFORCE Analyzer). Where the panel and the end posts land is not modelled, so the pockets'
# stations stay assumed (``panel_pitch_assumed``): mep.open_web_panel reads UNKNOWN on them.
TRIFORCE_OJ_WEB_OPENINGS = PublishedWebOpenings(
    source="TRIFORCE (Open Joist) U.S. Specifier Guide, U.S. Edition 2023-05-11 "
           "(BAR0145UA_20230511_V3), p.19 \"Mechanical Clearances\"; p.4 web layout",
    table="Maximum Size of Pipes, Ducts and Cable Trays Through Diagonal Web Members, "
          "11 7/8\": round D 7 1/4\"",
    member=_TRUSS,
    round_diameter=inch(7.25),
    panel_pitch=inch(24), panel_pitch_assumed=True,
    condition="the round column only (5 3/4\" square and 3\" x 13\" rectangle not modelled); "
              "the 34 1/8\" OSB end panel (one hole <= 1 1/2\") and its end are not placed, "
              "so a pocket within ~35\" of either end may be OSB; the 24\" o.c. diagonals are "
              "p.4's typical spacing, the stations the shop drawing's",
)

# How the x=18' plate is split. ``W-M-C2`` is a 2x6: 5 1/2" of seat, both decks landing on
# it from opposite sides. Both products ask 1 3/4" minimum, but J12's published reaction
# rises with the seat (3,000 / 3,500 / 4,000 lb at 1 3/4 / 3 1/2 / 5 1/2"), so the truss takes
# the larger share: 3 1/2" truss, 2" I-joist, both clear of their minimum with the plate
# exactly spent. The two must sum to 5 1/2" or the halves do not meet, which is why they are stated together;
# ``integrity.floor_end_bearing`` grades the result.
_TRUSS_BEARING = inch(3.5)
_JOIST_BEARING = inch(2.0)

# The main floor's ceiling below both halves — 5/8" gypsum board, room side (and only
# layer). The living room's resilient channel (``CR-LIVING-CEIL-RC`` in
# ``plan/assemblies.py``) still bills separately as a ``ConstructionRule`` return.
_CEILING_GWB = (Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),)
_CENTRE_X = ft(18)
_HOUSE = ft(36)
_ZERO = ft(0)


_rect = rect


# ** FS-S-WEST IS TRIMJOIST J12 (11 7/8"). ** The published openings are authored as data
# (``PublishedWebOpenings``) and ``resolve/open_web.py`` places them on every truss:
#   * D = 5" round through a web pocket (the 2018 guide said 6").
#   * R1 = 8 x 16 rectangle, only at the centreline of the STOCK length, inside a framed
#     18" duct chase. R2 = 4 x 9, "s" openings for small pipe and wire.
#   * a 12" OSB TrimEnd at each end of the stock (trimmed in place); stock 4'-24' by 2'.
# NOT published: the panel pitch (it is on TrimJoist's shop layout). 24" Warren panels are
# this house's working figure and ``panel_pitch_assumed`` says so; the stock remainder is
# absorbed in the end diagonal and the trim split evenly (``OpenWebShape.assumptions``).
# Replace the pitch with the shop layout when it arrives.
J12_WEB_OPENINGS = PublishedWebOpenings(
    source="TrimJoist Load & Opening Charts (trimjoist.com, 2026); DrJ report 2205-03; "
           "Technical Guide Rev 4",
    table="11 7/8\" J12 web openings: D round, R1 and R2 rectangles; TrimEnd and stock",
    member=_TRUSS,
    round_diameter=inch(5),
    r1_width=inch(16), r1_height=inch(8), r1_at_stock_centreline=True,
    chase_width=inch(18),
    r2_width=inch(9), r2_height=inch(4),
    trim_end=inch(12), stock_increment=ft(2), stock_min=ft(4), stock_max=ft(24),
    panel_pitch=inch(24), panel_pitch_assumed=True,
    condition="a chase moves no more than 12\" off the stock centre, even custom; chords "
              "3 1/2\" #1 SYP, webs SYP metal-plated (ANSI/TPI 1-2022); no R2 or D opening "
              "in the shaded panels beside R1; shaded 's' openings are for small pipe and wire",
)

# What J12 publishes for the floor: 16" o.c., 40 psf live, L/480 23'-2" (L/600 21'-6").
J12_FLOOR_SPAN = PublishedSpan(
    source="TrimJoist Load & Opening Charts (trimjoist.com, 2026); DrJ report 2205-03; "
           "Technical Guide Rev 4",
    table="11 7/8\" J12 at 16\" o.c., 40 psf live / 15 psf dead, L/480: 23'-2\" (L/600: 21'-6\")",
    member=_TRUSS,
    span=ft(23, 2),
    load_psf=40.0,
    spacing=_OC,
    edition="Technical Guide Rev 4",
    condition="L/480 deflection; clear span only, simple span, uniform load; 1 3/4\" minimum "
              "bearing; no concentrated loads without consulting TrimJoist; max reaction 3,000 / 3,500 / 4,000 lb at 1 3/4 / 3 1/2 / "
              "5 1/2\" of bearing; the 15 psf DEAD column needs TrimJoist's confirmation "
              "wherever tile sits on this half (a tile bed runs above 15 psf)",
)

# ** TWO TRUSS LINES MOVED OFF THE 16" MODULE. **
# (laid station, new station) in y (owner, 2026-09-23). The fabricator's layout replaces
# the whole field; these say only where a line must NOT stand.
#   * 26'-8" -> 27'-0": clears the shifted hot riser, stack and basin vent (2026-10-21).
#   * 34'-8" -> 34'-5 3/4": clears the radon/plumbing chase (VR-M-STACK, now at
#     y=35'-1.3") and the ERV exhaust risers in FO-M-ERV-EA.
_LINE_MOVES = ((inch(320), inch(324)), (inch(416), inch(413.75)))

# West half: open-web trusses, so every second-floor plumbing stack, supply riser and the
# radon/plumbing chase can cross the deck through the webs instead of a soffit or chase.
WEST_FLOOR = FloorSystem(
    uid="1JXQ975X9E", tag="FS-S-WEST",
    joists=JoistSpec(member=_TRUSS, spacing=_OC, direction="x",
                     bearing_refs=("W-M-W2", "W-M-C2", "BM-M-HALL"),
                     web_openings=J12_WEB_OPENINGS,
                     line_overrides=_LINE_MOVES,
                     # The south gable-end edge line is a 1 1/4" LSL rim board, as on every
                     # TJI field (owner, 2026-11-18); the north one is opening trimmer packs.
                     edge_rims=("lo",),
                     end_bearing=(("W-M-C2", _TRUSS_BEARING),)),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR,
                       nailing=SUBFLOOR_FASTENING),
    ceiling_below=_CEILING_GWB,
    published_span=J12_FLOOR_SPAN,
    outline=_rect(_ZERO, _ZERO, _CENTRE_X, _HOUSE),
    openings=("FO-S-STAIR", "FO-S-ERV-CHASE", "FO-S-ERV-LAUNDRY", "FO-S-BATH1-WC-DRAIN", "FO-S-BATH1-TUB-DRAIN",
              "FO-S-ERV-SUITEBATH"),
    source="catlin second floor, west half — 11 7/8\" open-web floor trusses at 16\" o.c. "
           "spanning 18'-0\" from W-M-W2 to the x=18' bearing line south of FO-S-STAIR, "
           "and 10'-3 1/4\" to that opening's west header north of it, chosen for the "
           "plumbing/HVAC crossings this half carries",
)

# East half: keeps FS-SECOND's original specification and uid — the half whose IFC
# GlobalId should survive (decision #16).
EAST_FLOOR = FloorSystem(
    uid="CSF603AAAA", tag="FS-S-EAST",
    joists=JoistSpec(member=_JOIST, spacing=_OC, direction="x",
                     bearing_refs=("W-M-C2", "W-M-E1", "BM-M-HALL"),
                     # FURN-M-LIV-TRACK-S's ceiling track screws up into this line; it runs
                     # parallel to the joists, 6 1/2" off the y=16" line.
                     extra_lines=(inch(9.5),),
                     # The gable-end edge lines are a 1 1/4" LSL rim boards (owner, 2026-11-18).
                     edge_rims=("lo", "hi"),
                     end_bearing=(("W-M-C2", _JOIST_BEARING),)),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR,
                       nailing=SUBFLOOR_FASTENING),
    # The main floor's ceiling: this deck's underside *is* that ceiling (unchanged from
    # the old FS-SECOND). Plain board, not type X: R302.13 doesn't reach this floor.
    ceiling_below=_CEILING_GWB,
    outline=_rect(_CENTRE_X, _ZERO, _HOUSE, _HOUSE),
    published_span=TJI_230_FLOOR_SPAN,
    reinforcements=(
        JoistReinforcement(at=pt(inch(374.375), inch(66.875)), plies=3, blocking=True,
                           source="ST-S2A departing-rim reactions: sister the supporting I-joist and block both adjacent bays to the main-storey bearing walls"),
        # D-S-BALCONY's jamb packs stand on the y=0 LSL edge rim, which TJ-8000 rates for
        # vertical load: the squash plies a TJI needed are gone (note §5, 2026-11-18).
        *BALCONY_SEAT_BACKERS,
    ),
    source="catlin second floor, east half — 11 7/8\" TJI 230 joists at 16\" o.c. spanning "
           "18'-0\" from the x=18' bearing line to W-M-E1, unchanged from the old "
           "whole-floor FS-SECOND",
)

SECOND_ELEMENTS = [WEST_FLOOR, EAST_FLOOR]

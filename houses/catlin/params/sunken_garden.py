"""Sunken garden / porch / balcony structure — parametric module (WP3.1, redesign).

One freestanding concrete + wood structure immediately south of the house (5" gap from
the house cladding face). It is fully independent of the house — the two share only a
compacted footing bed, with the footings doweled together through a fiberglass-rebar +
40 psi XPS foam thermal break (see FOOTING_BEDDING / the dowel note below).

Vertical stack (project-north frame; +X east, +Y north, +Z up):
- Sunken garden floor at the basement storey (-9'): a U-shaped cantilever-T retaining
  wall (open to the north) on a 42" compacted-aggregate base down to frost. The wall
  footings reach frost depth by soil replacement (that drained non-frost-susceptible
  section, ASCE 32 / IRC R403.1.4.1); the two porch columns, since 2026-08-29, reach it by
  excavation instead — bell-bottom piers augered 42" below the garden floor.
- The north 8' of that U is the *porch*: two 12" side walls and, on both the north (house)
  and south (front) edges, NO concrete wall. Each of those edges is carried the same way —
  one column at midspan plus two 3-ply KDAT beams hung into the side walls: a 12" sonotube
  at the back, a 20" round cast column at the front. The back line sits a SPEC south-offset
  inside the north edge (so the tube and its bell footing clear the house) and the deck
  cantilevers over it. **Both beam lines are DROPPED — the joists bear on top of all four**
  (2026-08-29; the front pair was flush-framed until then, and unpinning it is what lowers
  PT-SG-FCOL onto the same soffit as PT-SG-COL). PT 2x8 joists span N-S between the two
  lines; composite decking is the walking surface. Porch floor = main (0').
- A metal fascia-mounted guard (RL-SG-PORCH) rails the porch's three open edges, matching
  RL-SG-BALCONY one storey up — which is 12" further south, outboard of it. Four balcony
  post bases land on the concrete wall tops, PT-SG-BF2's on the front column's top, and
  PT-SG-BR2's on the porch decking itself.
- The *balcony* one storey up (second, ~9-10') rides six 6x6 pillars (10' o.c. E-W, 8'
  o.c. N-S; rear row 2" taller for drainage slope) carrying three N-S triple-2x12 beams,
  2x8 joists @ 16" o.c., and aluminum (Wahoo AridDeck-style) decking. Its FRONT plane is
  12" south of the porch's (2026-08-29), so the balcony oversails the porch floor by a foot
  and its drip and gutter hang clear of it. That move is what puts PT-SG-BF2 — the centre
  front pillar, a third of the balcony — on the concrete column instead of through a single
  2x8 porch joist; PT-SG-BR2 at the back is still deck-borne and takes squash blocks.

Everything here is generated — these elements carry no editable-source location. Both decks
are FloorSystems outright, joists plus the plank as the deck sheet: FS-SG-PORCH (composite)
since 3bf2f48, FS-SG-DECK (aluminium) since 2026-08-22. Each used to carry a second Slab
element standing in for the surface beside the framing, which meant two elements claiming
one floor and a plank billing by the cubic yard.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import (
    Beam,
    Connector,
    ConnectorKind,
    DeckLayer,
    Dowel,
    DrainTile,
    Downspout,
    Drywell,
    Fascia,
    Flashing,
    FloorSystem,
    Footing,
    FootingBedding,
    FoundationWall,
    Gutter,
    JoistReinforcement,
    JoistSpec,
    KneeBrace,
    Node,
    Post,
    Railing,
    RailingKind,
    Slab,
    TrimKind,
    from_node,
    ft,
    inch,
    pt,
)

from typehaus.resolve.framing.profiles import cross_section


@dataclass(frozen=True)
class SunkenGardenSpec:
    clear_width_ft: float = 19.0  # E-W between wall inner faces (widened for the 6x6 grid)
    clear_length_ft: float = 28.0  # N-S between wall inner faces
    porch_clear_depth_ft: float = 8.0  # N-S inside the porch box
    gap_to_house_in: float = 5.0  # house cladding face -> north edge (insulation gap)
    wall_thickness_in: float = 12.0  # side + retaining walls
    # The cast column near the porch's front edge. A 16" SQUARE until 2026-08-28, a 16"
    # round until 2026-08-29, a 20" round since: it is now a SHARED bearing, seating both
    # front beams (on `_y_ax_front`) and PT-SG-BF2 (12" further south, on
    # `_y_balcony_front`) on one pour. See FRONT_COLUMN for the sizing table — 16" and 18"
    # have no solution at a 12" pillar overhang, 20" leaves +0.49".
    front_column_size_in: float = 20.0
    # How far south of the porch's inside face the front BEAM axis sits. This used to be
    # `front_column_size_in / 24` — the old column's half-width, because the column was
    # centred on the beam line. It no longer is, so the beam plane needed its own number
    # rather than one that would drift 2" every time the column changed diameter.
    #
    # The value is unchanged at 8", and holding it is the point: `_y_ax_front` lands on
    # -9.5', which gives the four porch beams a 10.00' span against `deck_beam_span`'s
    # 10.25' limit. Any move south past 8.00' of back span drops the R507.5(1) lookup to
    # the 10' row (9.17') and fails all four at once.
    porch_front_edge_offset_in: float = 8.0
    # How far south of the porch's front BEAM plane the balcony's front pillar row stands,
    # since 2026-08-29. The row used to sit on the beam plane itself, which made PT-SG-BF2
    # a 6x6 bearing through one 2x8 porch joist onto BM-SG-FRW/FRE — ~315 psi of cross-grain
    # bearing at the base and ~385 psi where the joist crossed the beam, against an Fc-perp
    # of 425 psi (SPF). Moving the row out puts BF2 straight onto the concrete column
    # instead (~105 psi), and the balcony gains a 12" drip overhang past the porch floor.
    balcony_front_overhang_ft: float = 1.0
    footing_width_in: float = 84.0  # 36" toe + 12" wall + 36" heel
    footing_thickness_in: float = 12.0
    # The MN profile's design frost depth (``checks/code/mn_residential/profile.py``:
    # ``frost_depth_in=42.0``), transcribed here because this module has to derive two
    # different things from it and a house may not import a jurisdiction profile. Both of
    # the numbers below ARE this number, for the same reason, and neither is a coincidence
    # to be tidied into one field: the wall footings reach frost by *soil replacement*
    # (42" of stone, see FOOTING_BEDDING), the two column piers reach it by *excavation*
    # (a 42" augered shaft, see _pier_bell_bottom_ft).
    frost_depth_in: float = 42.0
    aggregate_bedding_depth_in: float = 42.0
    # The nominal levelling / drainage course under a footing that already bears where it
    # is meant to bear. 7" is the house's own bearing-prep depth (``params/foundations.py``,
    # every FT-B-* bedding) and is what the two belled piers take now that their bells
    # bottom out on undisturbed soil at frost depth rather than on a replacement section.
    pier_levelling_bedding_in: float = 7.0
    house_size_ft: float = 36.0
    house_ext_layers_in: float = 5.0  # polyiso+EPS+furring+cladding beyond sheathing
    # 9'-1 7/16" since 2026-08-23, 9'-4" before it, 9'-0" before that. The 2026-08-21 lift
    # took the house up 4" for the deeper basement ceiling and grade went down with it, so
    # the garden floor stayed where it was in the soil and moved in the project frame to say
    # so. The 2026-08-23 flat-bearing-seat rework is the opposite move: grade did NOT change,
    # the basement slab came up 2 9/16" to meet the deck's soffit, and this floor comes up
    # with it — because ``SL-SG-FLOOR`` and ``SL-B-FLOOR`` top out on exactly the same plane
    # and that flush plane IS the walkout at D-B-PATIO. 109.4375" is
    # ``params/main_deck.BASEMENT_DATUM``; this module may import, but it is one house-wide
    # number transcribed rather than a second derivation, and
    # ``integrity.basement_bearing_seat`` checks the two agree.
    #
    # The court gets 2 9/16" shallower with it: the retained height on W-SG-E2/S/W2 reads
    # 7.09' where it read 7.3'. Both are well past the 48" that sends R404.1.1 to an
    # engineered design, so those three walls stay engineered either way and
    # ``structural.foundation_unbalanced_fill`` keeps reporting them UNKNOWN, unchanged.
    basement_depth_ft: float = 109.4375 / 12.0
    slab_thickness_in: float = 3.5
    porch_top_ft: float = 0.0  # top of the porch concrete walls = porch floor / railing base
    railing_height_ft: float = 3.5  # 42" guard above the porch walking surface
    retaining_top_ft: float = 0.5
    # porch framing
    column_diameter_in: float = 12.0  # sonotube back-beam support
    # Sonotube centre set south of the deck's north-edge line. Centred on that line, the 12"
    # tube would poke 6" into the house cladding and its 30" bell footing would run 15" into
    # FT-B-S2, whose south face lands exactly on this north-edge line. 15" (bell reach) + 2"
    # = 17". Cannot shrink. The 2" was sized as the 40 psi XPS thermal-break block the
    # dowels crossed; that block went with DW-SG-COL when the bell was augered to frost
    # depth (2026-08-29), and the 2" stays as what it now is — plain clearance between the
    # bell's north face and the house footing's excavation face. Same number, and the
    # column does NOT move: the whole back-beam line, the deck edge and the pockets are
    # anchored to this offset.
    column_south_offset_in: float = 17.0
    porch_joist: str = "2x8"
    porch_joist_oc_in: float = 16.0
    # Three-ply KDAT 2x12 (2026-08-23), 11 1/4" deep — the same depth as every member this
    # position has carried, so no derived elevation moves.
    #
    # It replaces a two-ply LVL that was described in this file as "treated LVL", which is a
    # product that does not exist. Treated Parallam Plus PSL is the real article and it is
    # made in 9 1/4", 11 7/8", 14" and 16" depths only, at 3 1/2" and 5 1/4" widths;
    # Weyerhaeuser forbids resawing it in depth. So the 11 1/4" this whole porch is derived
    # from cannot be bought treated in an engineered member at all. A 2x12 is exactly
    # 11 1/4" sawn, and KDAT is a stocked treatment.
    #
    # It is also a strict improvement on the check: three plies of 2x12 clear IRC Table
    # R507.5(1) on this span, so `structural.deck_beam_span` grades the member PASS instead
    # of reporting UNKNOWN against a member outside the table's scope. Treated, same depth,
    # and prescriptively checkable for the first time.
    back_beam: str = "3-2x12"
    porch_deck_thickness_in: float = 1.0  # composite plank
    # The two side walls run this far PAST the porch's front edge before handing off to the
    # retaining run. Without it the W1/W2 (and E1/E2) junction node landed exactly on
    # `_y_ax_front`, which is also the balcony's front pillar line — so PT-SG-BF1/BF3
    # straddled the joint, half over each wall, and the bearing map had to pick one. It
    # picked the retaining wall, which put those two pillars up on the +6" curb rather than
    # on the porch walls carrying the rest of the frame. It clears the 5 1/2" pillar's south
    # face by 3 3/8" — the side cover a square post base wants — and leaves the front-beam
    # pockets (CN-SG-HGR-FW/FE, on `_y_ax_front`) well in from the end of the wall instead
    # of right at it.
    #
    # 18", not 6", since 2026-08-29: the balcony's front pillar row moved 12" south to
    # `_y_balcony_front`, so PT-SG-BF1/BF3 would have run off the south end of W-SG-W1/E1
    # and onto W-SG-W2/E2 — the +6" curb, `lateral_support="unsupported"` R404.4 engineered
    # walls — reversing exactly the 2026-08-21 decision this field exists to record. The
    # extension follows the pillars, so the map above still says the true thing. W-SG-W2/E2
    # shorten by 12" and their footings follow.
    side_wall_south_extension_in: float = 18.0
    # The porch's two joist ends are not alike, so it cannot share the balcony's symmetric
    # cantilever: the south end hangs flush *in* the front beams (nothing to oversail) and
    # the north end runs the column's south-offset out to the deck edge. This is the *south*
    # value; the north one is that offset (see PORCH_JOISTS).
    porch_joist_cantilever_in: float = 0.0
    # balcony framing
    pillar_size: str = "6x6"
    rear_pillar_rise_in: float = 2.0  # rear row taller for drainage slope
    # Three-ply KDAT 2x12 (2026-08-23), 11 1/4" deep. Same member as `back_beam` below the
    # porch, and for the same two reasons: "treated LVL" is not a product, and three plies
    # of 2x12 is the deepest row IRC Table R507.5(1) publishes.
    #
    # This was briefly a 3-2x10, on the reading that no sawn size could answer the span:
    # R507.5(1) stops at 7'-2" for a 3-2x10 and 8'-4" for a 3-2x12 at the *12'* joist-span
    # row, and the beams span 8'-8". But the 12' row was never the right one. These joists
    # span 10'-0" beam to beam and then overhang the outer beams by `joist_cantilever_in`;
    # `structural.deck_joist_span` was reading the 10'-6" MEMBER and rounding that up to
    # the 12' row, counting the cantilever as span. A cantilever is not span — R507.6.1
    # bounds it separately, at a quarter of the back span — and the check reads the back
    # span now (`structural.deck_joist_cantilever` is where the 6" overhang is graded).
    #
    # At the 10' row a 3-2x12 reaches 9'-2", so the 8'-8" span clears it by 6". The three
    # balcony beams PASS the prescriptive table; nothing here is engineered any more, and
    # the consultant scoped for the E-W bracing and the `FT-SG-*` frost design (R404.4) is
    # no longer carrying these as well.
    #
    # The 2" of extra depth is real and it moves things: `_balcony_beam_depth_ft` is
    # derived from this string now, so the beam soffit, the pillar tops, the brace rails and
    # both knee-brace families drop 2" with it. Clear height from the porch deck to the balcony
    # beam soffit goes 8'-7 1/2" -> 8'-5 1/2", and the walking surface at `balcony_level_ft`
    # has not moved.
    #
    # Worth keeping straight while reading this file: the balcony beams sit under a
    # DRY-BELOW surface — `FS-SG-DECK`'s plank is `aluminum-deck`, a Wahoo AridDeck-style
    # watertight system with a drip trough and leader (see the deck's own comment) — while
    # the porch beams sit under GAPPED composite. That asymmetry is the real ESR-1387 5.3
    # exposure story, and it is why the two pairs were never the same problem.
    balcony_beam: str = "3-2x12"
    # Carries no gravity load — the deck's joists span E-W onto the three N-S beams only.
    # This is the E-W lateral collector: the only E-W load path on a freestanding deck with
    # pinned ABU66SS bases, and the strut the corner knee braces rise into. Also what ties
    # the two unbraced centre pillars into the two braced end bays, which is why they can
    # stay unbraced. 2x8 because it only wants face width for two 1/2" through-bolts per
    # post (face-bolted, not seated — nothing bears on it, so it need not match the beam
    # depth). See BALCONY_RAILS.
    balcony_brace_rail: str = "2x8"
    balcony_joist: str = "2x8"
    balcony_joist_oc_in: float = 16.0
    balcony_deck_thickness_in: float = 1.5  # aluminum plank
    joist_cantilever_in: float = 6.0  # deck joist tips overhang the outer beams
    balcony_level_ft: float = 10.0  # second storey


SPEC = SunkenGardenSpec()

_t = SPEC.wall_thickness_in / 12.0
_half = _t / 2.0

# E-W: garden centered on the house centerline. Side-wall axes land 20' apart (19' clear
# + 2x 6" half-walls) so the balcony pillars sit on a clean 10' o.c. E-W grid.
_cx = SPEC.house_size_ft / 2.0  # 18.0
_x_in_w = _cx - SPEC.clear_width_ft / 2.0  # 8.5
_x_in_e = _cx + SPEC.clear_width_ft / 2.0  # 27.5
_x_ax_w = _x_in_w - _half  # 8.0
_x_ax_e = _x_in_e + _half  # 28.0

# N-S: the whole structure's north face sits gap_to_house south of the house cladding face
# (a 5" insulation gap). With the north wall removed there is no wall thickness to inset —
# the side-wall north-end nodes, the porch deck edge, and the back-beam/column line all land
# on that one north-edge line so the deck actually reaches to within 5" of the house.
_y_out_n = -(SPEC.house_ext_layers_in + SPEC.gap_to_house_in) / 12.0  # -0.833'
_y_ax_n = _y_out_n  # side-wall north-end nodes (open ends terminate here → face at the gap)
_y_in_n = _y_out_n  # porch deck north edge (back beams + column sit a SPEC offset south)
# The porch's front edge: the axis of the two front beams, of RL-SG-PORCH's south run and
# of the porch deck itself. It used to be the 16" arched cross-wall's axis and lands on
# exactly the same -9.5'.
#
# It is NO LONGER the balcony's front plane and no longer the front column's axis. Until
# 2026-08-29 all three were one number, derived off the column's half-width; the column is
# now a 20" round set 7 1/8" south of here and the balcony's pillar row a foot south of
# that, so the porch plane holds its own SPEC offset (see `porch_front_edge_offset_in` for
# why this number in particular must not drift).
_y_ax_front = _y_in_n - SPEC.porch_clear_depth_ft - SPEC.porch_front_edge_offset_in / 12.0
# The BALCONY's front plane, 12" south of the porch's since 2026-08-29: the balcony's front
# pillar row, its deck outline, RL-SG-BALCONY, TR-SG-FASCIA, TR-SG-DRIP and TR-SG-GUTTER.
# The overhang is what the balcony gains by moving PT-SG-BF2 off the porch framing and onto
# concrete — a 12" drip past the porch floor, which is also why the gutter is out here and
# not over the porch deck.
_y_balcony_front = _y_ax_front - SPEC.balcony_front_overhang_ft
# Where the porch side walls stop and the free retaining walls take over. NOT the porch's
# front edge: the side walls carry on past it so the balcony's front pillars land on them
# (see ``side_wall_south_extension_in``). Everything else that used to read `_y_ax_front`
# for this — the front beams and the porch's own deck outline and guard — still does. The
# front column, the balcony's pillar row, its guard and its deck outline all left in 2026-08-29
# (see `_y_front_col` and `_y_balcony_front`); this offset was 6" then and is 18" now.
_y_ax_mid = _y_ax_front - SPEC.side_wall_south_extension_in / 12.0  # -11.0'
_y_in_s = _y_in_n - SPEC.clear_length_ft
_y_ax_s = _y_in_s - _half

_wall_bottom = ft(-(SPEC.basement_depth_ft + 0.75))
# The two porch side walls stop 1" higher than the free retaining run, and the 1" comes out
# of the wall, not out of the ground (2026-08-23). At the old bottom they resolved 10'-1"
# tall, and IRC Table R404.1.2(8) stops at 10'-0", so `structural.foundation_unbalanced_fill`
# could not answer them: not because anything about the wall was in doubt but because it was
# an inch past the published maximum. Trimming to exactly 10'-0" puts them ON the table's
# last row, which is also the row their reinforcement was already carried up from.
#
# It is a SEPARATE constant rather than a change to `_wall_bottom` on purpose. The three
# retaining walls south of here (W2/E2/S) are not the subject of the decision, they are not
# graded against that table (they are `lateral_support="unsupported"` → IRC R404.4,
# engineered), and raising their bottoms would take an inch of frost cover off FT-SG-W2/E2/S
# for nothing. `_PORCH_FOOTING_THICKNESS_IN` below then puts the inch straight back into
# FT-SG-W1/E1, so the two footing UNDERSIDES do not move either — which is what keeps their
# 21" of cover, and the whole R403.3 frost design under this garden, exactly where it was.
_porch_wall_bottom = ft(-(SPEC.basement_depth_ft + 8.0 / 12.0))
_porch_top = ft(SPEC.porch_top_ft)  # storey datum = top of joist; the masonry bears here
_ret_top = ft(SPEC.retaining_top_ft)
# Top of wall to underside of footing — the true unbalanced fill on the three free retaining
# walls, because the raised garden's apron holds a terrace against them at their own top
# elevation. See the long note in WALLS below; this is `_ret_top - _wall_bottom` written so it
# cannot drift from either.
_ret_unbalanced_fill = ft(SPEC.retaining_top_ft + SPEC.basement_depth_ft + 0.75)
# W-SG-ARCH, the buried grade beam closing the court's north end. Both ends are DERIVED so
# the beam cannot drift off the two planes that define it: its top is the garden floor's
# underside (so it is never underfoot and SL-SG-FLOOR is untouched), its underside is the
# retaining footings' underside (so the excavation has one bottom and the strut engages
# them). 17 1/2" deep, which is what those two planes leave.
_grade_beam_top = ft(-SPEC.basement_depth_ft) - inch(SPEC.slab_thickness_in)
_grade_beam_bottom = _wall_bottom - inch(SPEC.footing_thickness_in)
# Vertical steel on the three retaining walls' stems, on the RETAINED face — that is
# where a cantilever puts its tension, and getting it on the wrong face is the classic
# way a correctly-sized wall falls over. Sized in
# `notes/sunken_garden_court_free_body.md` §6: Mu = 1.6 x 11,151 = 17,841 ft-lb/ft at
# at-rest against phi-Mn 21,639 at #6 @ 10" (d/c 0.82). #6 @ 12" is the arithmetic
# minimum at d/c 0.98 and is too thin a margin for a screening; the `#6 @ 38"` the
# braced porch walls carry is nowhere near. 2" cover per ACI 318-19 Table 20.5.1.3.1
# (earth and weather, #6 and larger), which is also IRC Table R404.1.2(8) footnote i's
# outside-face figure for bars larger than #5.
_RET_REBAR = '#6 @ 10" o.c.'
# Top of the composite boards laid over FS-SG-PORCH: the joist tops are the 0' storey datum
# and the plank sits on them. This is the surface underfoot — what RL-SG-PORCH's 42" is
# measured from, and what the two centre balcony pillars bear on.
_porch_walking_surface = inch(SPEC.porch_deck_thickness_in)
_balcony = ft(SPEC.balcony_level_ft)

# Self-adhered butyl over every framing top in this structure — both decks' joists, all
# seven built-up beams, both brace rails. One tag because it is one product and one order;
# the BOM splits it by member width, which is the number that decides which roll to buy.
#
# The reason it is here and not in a note: a site-built multi-ply beam has an open seam
# running its whole length between each pair of plies, and that seam holds water and the
# grit that stops it drying. Every beam in this structure is three plies of 2x12 standing
# in weather over open ground, so there are fourteen such seams, none of which anything in
# the model could see or bill before this. Butyl also self-seals around the fasteners
# driven through it, which is what a joist top mostly is.
_BEAM_TAPE = "butyl-tape"
# The same butyl in the roll width a 3-ply beam actually needs. A 3-2x12 is 4 1/2" across,
# so the 1 5/8" joist roll and even the common 3 1/8" "double joist" roll leave the outer
# plies — and both ply seams — uncovered. Two tags rather than one because these are two
# SKUs at a 2-3x difference in price per foot, and the BOM's own width column is what says
# which member takes which: 1.5" and 1.25" members take ``_BEAM_TAPE``, the 4.5" ones this.
_BEAM_TAPE_WIDE = "butyl-tape-beam"

# ============================================================================
# Basement: garden retaining walls, footings, back + front columns.
# ============================================================================
NODES = [
    Node(uid="SGN001AAAA", tag="N-SG-NW", position=pt(ft(_x_ax_w), ft(_y_ax_n)),
         open_end=True),  # north wall removed — side wall terminates here (freestanding)
    Node(uid="SGN002AAAA", tag="N-SG-NE", position=pt(ft(_x_ax_e), ft(_y_ax_n)),
         open_end=True),
    Node(uid="SGN003AAAA", tag="N-SG-MW", position=pt(ft(_x_ax_w), ft(_y_ax_mid))),
    Node(uid="SGN004AAAA", tag="N-SG-ME", position=pt(ft(_x_ax_e), ft(_y_ax_mid))),
    Node(uid="SGN005AAAA", tag="N-SG-SW", position=pt(ft(_x_ax_w), ft(_y_ax_s))),
    Node(uid="SGN006AAAA", tag="N-SG-SE", position=pt(ft(_x_ax_e), ft(_y_ax_s))),
]

WALLS = [
    # Porch box: two 12" side walls only, topping at the porch floor. Both cross-edges are
    # column-and-beam (the balcony above rides on 6x6 pillars, not a concrete box).
    #
    # W-SG-W1/E1 are SUPPORTED TOP AND BOTTOM (settled 2026-08-22). The question stood open
    # for a while and it was a real one: whether a porch deck counts as *permanent lateral
    # support* at the head of a wall holding 9'-9" of fill is a judgment about the real
    # structure, not something the model can read off its own geometry. It does here, and
    # the reason is that this head is not a deck edge resting alongside a wall — it is a
    # beam pocket cast INTO it. Both back beams and both front beams die into these two
    # walls in HUCQ410-SDS concealed-flange hangers (CN-SG-HGR-W/E, -FW/-FE), the porch
    # joists span between those beams, and FS-SG-PORCH's plank sheet ties the whole
    # diaphragm together. The bottom is the garden slab bearing at their foot. That is a
    # continuous load path in both directions at both ends, which is what R404.1.2(8)
    # presumes and what the free retaining walls south of here (W2/E2/S) do not have.
    #
    # These walls resolve EXACTLY 10'-0" tall over 7'-2" of unbalanced fill (2026-08-23),
    # which is the last row IRC Table R404.1.2(8) publishes. Until that trim they stood
    # 10'-1" and the check reported UNKNOWN — not because anything about the wall was in
    # doubt, but because one inch put it past the published maximum. The 10' row is the row
    # now, R404.1.3's no-seal prescriptive path reaches it, and
    # `structural.foundation_unbalanced_fill` PASSES both walls.
    #
    # The inch came out of the WALL and not out of the ground: `_porch_wall_bottom` raised
    # the bearing and FT-SG-W1/E1 went 12" -> 13" thick to hold their undersides at the same
    # -11'-1", so the 21" of frost cover the R403.3 wing insulation is sized against did not
    # move. Verified before and after.
    #
    # `#6 @ 38" o.c.` is kept, and it is now MORE than the table asks: at 10' x 8' backfill
    # a 12" wall of 4,000 psi concrete needs no vertical reinforcement at all under footnote
    # l, and the check says so in its PASS. The schedule stays because it was carried up from
    # the same row, because these two walls also carry the porch's four beam pockets, and
    # because taking steel out of a retaining wall to match a table minimum is the engineer's
    # call, not this file's.
    FoundationWall(uid="SGW103AAAA", tag="W-SG-W1", start_node="N-SG-NW",
                   end_node="N-SG-MW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_porch_top, bottom_elevation=_porch_wall_bottom,
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#6 @ 38" o.c.'),
    # East wall runs ME→NE (south→north), opposite the west wall, so both side walls wind
    # the same way around the garden. Retiring the arched cross-wall broke this component's
    # only closed loop — the five survivors are now one open chain NW→MW→SW→SE→ME→NE, whose
    # signed area is zero — so ``resolve_storey_windings`` can no longer recover a winding
    # and returns ``UNRECOVERABLE_WINDING_OUTWARD_SIGN`` (+1) instead of the -1 it used to.
    # That is latent and was measured: every SUNKEN_GARDEN_WALL is one centred concrete
    # layer, so the flip only reverses the vertex order of two layer polygons (W1/E1) and
    # moves no face. It would stop being latent the moment one of these walls took a second
    # layer — which is exactly what the retired masonry railing above them was.
    FoundationWall(uid="SGW104AAAA", tag="W-SG-E1", start_node="N-SG-ME",
                   end_node="N-SG-NE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_porch_top, bottom_elevation=_porch_wall_bottom,
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#6 @ 38" o.c.'),
    # ============================================================================
    # W-SG-ARCH IS BACK, AND IT IS A BURIED GRADE BEAM — NOT THE ARCH (2026-08-30).
    # ============================================================================
    # `a160812` retired a 16" cast cross-wall with two semicircular arches carrying a 42"
    # masonry parapet and three balcony pillars — "the heaviest and most expensive element
    # of the structure". **None of that comes back.** What comes back is a strut on the same
    # node pair, 12" x 17 1/2", entirely below the garden floor, invisible, doing one job:
    # closing the loop that makes W-SG-W2 and W-SG-E2 face each other instead of standing as
    # two free cantilevers. It reuses the retired uid, which is exactly what the
    # `_WALL_FOOTING_UID` literal-map pattern below was built for.
    #
    # **Why a beam and not the garden slab.** A slab strut is cheaper and does not work:
    # the walls would stand as free cantilevers at FS 0.73 until the floor cures, and
    # BACKFILL IS WHAT LOADS THEM. Table R404.1.2(8) footnote g says the same thing about
    # its own walls — "laterally supported at the top and bottom BEFORE backfilling". This
    # beam is cast with the walls, so the loop is closed before any soil goes in. It also
    # needs no control joints, closes no shrinkage gap, does not bear on the compressible
    # FPSF wing foam, and leaves SL-SG-FLOOR free to be saw-cut for ever.
    #
    # **No Footing under it, deliberately.** It carries its own weight (219 plf) over 12" of
    # bearing — 219 psf against 3,000 allowable — so a strip footing would be concrete spent
    # on nothing. `FootingBedding.host_ref` takes a FoundationWall directly (the five
    # `W-RG-*` beds are the precedent), and `structural.frost_depth` iterates footing and pad
    # SOLIDS, so a `FT-SG-ARCH` would land inside the excavation and reopen the frost
    # question that ASCE 32 soil replacement closed on 2026-08-29. FB-SG-ARCH below carries
    # the same 42" undercut, the same NFS claim and the same tile to DRW-SG-MAIN.
    #
    # **The underside is flush with the retaining footings' at -10'-10 7/16"**, which is one
    # excavation level and one stone plane rather than two, and lets the strut engage those
    # footings directly instead of hanging above them. The top is the garden floor's
    # UNDERSIDE, so nothing of it is ever underfoot and SL-SG-FLOOR does not move.
    #
    # `unbalanced_fill=inch(0)` is authored and is not a formality: without it
    # `_unbalanced_fill_ft`'s grade-plane proxy invents a retained height for a wall buried
    # inside the excavation, and this beam retains nothing — the court is on one side of it
    # and the porch box on the other, both at the same level.
    FoundationWall(uid="SGW102AAAA", tag="W-SG-ARCH", start_node="N-SG-MW",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_grade_beam_top, bottom_elevation=_grade_beam_bottom,
                   unbalanced_fill=inch(0),
                   lateral_support="top_and_bottom"),
    # Garden retaining run (to just above grade), the U south of the porch.
    #
    # ** THE FILL AGAINST THESE THREE IS AUTHORED, AND IT IS A CORRECTNESS FIX (2026-08-30). **
    # Left derived, `structural.foundation_unbalanced_fill` measured from the single global
    # `Site.grade` (-2'-10") down to the footing and reported **7.0'**. That number is wrong
    # here, and the model already contained everything needed to see it: `params/
    # raised_garden.py` builds an SRW apron whose `TOP = ft(RETAINING_WALL_TOP_FT)` — level
    # with these walls' own tops at +0'-6" — standing 3'-0" out from their outer faces and
    # holding a terrace of soil at that level *against them*. Grade is a plane, and a plane
    # cannot describe a terrace sitting 3'-4" above it. The real retained height is the wall's
    # full top-to-footing dimension, **10.37'**.
    #
    # It is deliberately written as the same arithmetic `_wall_bottom` and `_ret_top` are
    # built from rather than as a literal, so it moves with either. There is no separate
    # "terrace top" number and there must not be: `SPEC.retaining_top_ft` IS the terrace top,
    # because `raised_garden.py` reads that very constant to place its own apron. A second
    # copy would be exactly the divergence the "publish, do not re-derive" note further down
    # this file exists to prevent.
    #
    # **This changes no verdict, and that was checked before and after.** All three were
    # UNKNOWN — engineered before, and are UNKNOWN — engineered after; only the fill number in
    # the message moves. Both figures are far past the 48" at which R404.1.1 sends a wall to
    # an engineered design, so the correction cannot flip anything — but it changes what the
    # engineer is asked to design for by nearly half again, which is the whole point.
    # `notes/sunken_garden_retaining_screening.md` works the consequences.
    #
    # ** `lateral_support="base"`, NOT "unsupported" (2026-08-30). ** This block argued the
    # opposite in detail until the court was closed, and the old argument was right about
    # every wall EXCEPT the free body it drew around them.
    #
    # What it said: these three are free retaining walls, open to the sky along their whole
    # top, holding 10'-4" of fill with nothing bracing the head — IRC R404.4's case exactly.
    # All of that is still true, and `"base"` still routes to the same R404.4 engineered
    # handoff (`checks/structural/foundation.py::_grade_one`); Table R404.1.2(8), a
    # *basement* wall table whose footnote g presumes bracing top AND bottom, still must not
    # be read against them.
    #
    # What was wrong: they were graded as three ISOLATED cantilevers, each resisting by its
    # own base friction, and reached FS 0.73 against 1.5. That is the arithmetic of a wall
    # nobody built. W-SG-W2 (axis x=8'-0") and W-SG-E2 (axis x=28'-0") face each other across
    # a 19'-0" court, same height, same 18'-4" length, cast into W-SG-S at their south ends
    # through monolithic corners — **their thrusts cancel through the concrete between
    # them.** Only the 20'-0" south wall is unopposed. The U was open at its NORTH end and
    # that was the real defect; W-SG-ARCH above closes it, and
    # `engineering/retaining_system.py` sums the whole court as ONE free body.
    #
    # The price of citing the restraint is that these are graded at AT-REST (60 psf/ft)
    # rather than active (45): you cannot hold a wall's base with a permanent strut and also
    # claim it moves enough to shed to the active wedge. Worked in
    # `notes/sunken_garden_court_free_body.md`, which supersedes the screening note's
    # CONCLUSION and not its arithmetic.
    #
    # `base_restraint_ref` is authored and never derived, and naming it GRANTS nothing:
    # `retaining_system._verify` goes and checks that W-SG-ARCH is a real FoundationWall, on
    # a real cycle of the wall graph, on the SAME cycle as this wall, cast in concrete, and
    # with a section that carries the strut force. Break any one and the record is
    # INCOMPLETE, never PASS.
    #
    # `vertical_reinforcement` is NEW and it is the other half of the fix. The stem was plain
    # concrete and always had been: 465 psi of flexural tension at at-rest, on a section ACI
    # 318 R22.6.3 does not even COVER as plain concrete ("the Code does not cover walls
    # without horizontal support ... such walls are to be designed as reinforced concrete
    # members"). A base restraint acts inches from the stem's base and relieves NONE of it,
    # so fixing sliding alone would have turned the report green over a louder uncomputed
    # failure. The schedule is sized in the note, not invented here.
    #
    # `engineering_spec` is STILL deliberately unset. The screening note's §6 reasoning is
    # unchanged: an authored spec says "an engineer designed this wall", and none has. What
    # changed is that the engine now computes a court that checks out — a draft verdict,
    # not a stamp.
    FoundationWall(uid="SGW105AAAA", tag="W-SG-W2", start_node="N-SG-MW",
                   end_node="N-SG-SW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   unbalanced_fill=_ret_unbalanced_fill,
                   vertical_reinforcement=_RET_REBAR,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
    FoundationWall(uid="SGW106AAAA", tag="W-SG-E2", start_node="N-SG-SE",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   unbalanced_fill=_ret_unbalanced_fill,
                   vertical_reinforcement=_RET_REBAR,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
    FoundationWall(uid="SGW107AAAA", tag="W-SG-S", start_node="N-SG-SW",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL",
                   unbalanced_fill=_ret_unbalanced_fill,
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   vertical_reinforcement=_RET_REBAR,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
]

# --- public geometry for structures that build on this one ------------------------------
# The raised garden bears on the south retaining wall's top, so it needs that wall's axis,
# span and section. Publish them rather than let a second module re-derive the same
# arithmetic off SPEC — two derivations silently diverge the next time a dimension moves.
SOUTH_RETAINING_WALL_TAG = "W-SG-S"
SOUTH_RETAINING_WALL_AXIS_Y_FT = _y_ax_s
SOUTH_RETAINING_WALL_NODES = ("N-SG-SW", "N-SG-SE")
RETAINING_WALL_SPAN_X_FT = (_x_ax_w, _x_ax_e)
RETAINING_WALL_TOP_FT = SPEC.retaining_top_ft
RETAINING_WALL_THICKNESS_IN = SPEC.wall_thickness_in
# The porch's front edge — the plane the two front beams and RL-SG-PORCH's south run sit
# on. Published because a second module must not re-derive it.
#
# It carried BOTH meanings until 2026-08-29 ("porch front edge" AND "balcony front edge"),
# which was harmless only while the two planes were the same one. They are 12" apart now,
# so they are two constants. A consumer that wants the outermost thing this structure
# presents — the balcony fascia, its guard, its drip — wants the BALCONY one.
PORCH_FRONT_AXIS_Y_FT = _y_ax_front
# The balcony's front edge, 12" south. `raised_garden.Y_NORTH` consumes THIS one: its two
# short returns close the apron U against the balcony railing's side faces, so they have to
# reach the plane that railing is actually on.
BALCONY_FRONT_AXIS_Y_FT = _y_balcony_front

# Sonotube column (12" round) at midspan, offset south of the deck's north-edge line (see
# ``column_south_offset_in``). The whole back-beam line re-anchors to the same offset —
# nodes, hangers, tie all at ``_y_col`` — so the beams stay collinear and the deck edge
# cantilevers over them to the house gap. Column top lands on the back-beam soffit (one
# beam depth below the 0' porch deck); base at the bell top, 2'-6" under the garden floor
# (see _pier_bell_bottom_ft).
_back_beam_depth_ft = 11.25 / 12.0  # 2x12 actual depth
_y_col = _y_in_n - SPEC.column_south_offset_in / 12.0
# The porch's two beam-line elevations, derived once here because three unrelated blocks
# below need them: the connector elevations (CN-SG-HGR-*, CN-SG-TIE-*), the beam caps, and
# — since 2026-08-29 — ``_WALL_UNDER_PILLAR``, where PT-SG-BF2 bears on the front column's
# top. Both porch beam pairs frame the same way now (joists ON TOP), so there is ONE soffit
# and one mid-depth, not the two derivations this file carried while the front pair was
# flush.
_porch_joist_depth_ft = cross_section(SPEC.porch_joist).depth_m / 0.3048
_back_beam_soffit = _porch_top - ft(_porch_joist_depth_ft + _back_beam_depth_ft)  # -18.5"
_back_beam_mid = _porch_top - ft(_porch_joist_depth_ft + _back_beam_depth_ft / 2.0)
_col_footing_width_in = 30.0  # bell diameter under the 12" sonotube
_front_footing_width_in = 36.0  # bell diameter under the 20" round front column

# --- the two porch piers are BELL-BOTTOM PIERS, augered to frost depth (2026-08-29) ------
#
# The owner's call, verbatim: "We can perhaps do 'bell bottom' piers as part of the
# sonotube installation, so going to 42" here (with an auger) is likely easier and less of
# a concern." What that buys is the whole point of the change: **these two reach frost
# depth by EXCAVATION rather than by relying on the aggregate section**. Every other
# footing in this structure stands short in concrete (21") and is frost-protected because
# the 42" of drained non-frost-susceptible stone under it counts as soil replacement under
# ASCE 32 — a real and admitted path (see FOOTING_BEDDING below), but one that rests on a
# gradation and a drainage claim staying true for the life of the building. A bell bearing
# on undisturbed soil 42" down needs neither claim: ``structural.frost_depth`` grades it on
# cover, the way it grades a footing in an ordinary trench.
#
# What a belled augered pier is, since the model has no single element for one: a 12"
# (20" at the front) hole augered to 42" below the garden floor, its base under-reamed out
# to the bell diameter, a fibre tube dropped in the shaft and the whole thing poured
# monolithically. So it is TWO elements here — the ``Footing`` is the bell (the bearing
# element, 12" thick at the bottom of the hole) and the ``Post`` is the shaft above it.
#
# **The bell MOVED DOWN; the bell did not GROW.** Deepening the ``Footing`` instead — the
# only lever this file had before ``Footing.bottom_elevation`` landed — would have drawn a
# 30"x30"x42" (and 36"x36"x42") prism of concrete: 1.41 cy against the ~0.25 cy of extra
# 12"/20" shaft the real pour adds, a ~7x over-bill, and a foundation schedule printing a
# 30" footing where a 12" auger hole gets drilled. Quantities are the product; a bell in
# the wrong place is a wrong quantity, not a drafting nicety.
_pier_bell_bottom_ft = -(SPEC.basement_depth_ft + SPEC.frost_depth_in / 12.0)
_pier_bell_top_ft = _pier_bell_bottom_ft + SPEC.footing_thickness_in / 12.0
# How much further down the bell top sits than the old one, which was flush with the garden
# floor. Every shaft above a bell grows by exactly this, so no column top moves — the beam
# soffit (-1'-6 1/2", both pairs since 2026-08-29) is a load-bearing elevation for the porch
# frame and is asserted in test_catlin_outdoor_structures.py.
_pier_shaft_extension_ft = -SPEC.basement_depth_ft - _pier_bell_top_ft
COLUMN = Post(uid="SGP001AAAA", tag="PT-SG-COL",
              position=pt(ft(_cx), ft(_y_col)), size="12 round",
              height=ft(SPEC.basement_depth_ft - _back_beam_depth_ft
                        + _pier_shaft_extension_ft),
              assembly="PIER_CONCRETE_12",
              supported_by="FT-SG-COL")

# The front column: a 20" round cast-concrete pier on its own belled footing, replacing the
# 16" arched cross-wall that used to close this edge. Its top is the *soffit* of the two
# front beams, exactly as PT-SG-COL's is the soffit of the back pair — and that is not a
# style choice. A 16"-o.c. joist grid cannot miss a column this size, so a column topping
# out at the deck datum reads as three clashes in ``structural.member_interference``, and
# neither a CHASE opening nor an outline notch can clear them: the resolver never passes
# opening boxes to ``_reinforcement_members``. Stopping at the soffit puts the whole pour
# below every floor member's underside.
#
# ** IT IS A SHARED BEARING SINCE 2026-08-29, AND THAT IS WHAT SETS ITS SIZE AND ITS AXIS. **
# One column seats three things: BM-SG-FRW and BM-SG-FRE, whose axis is `_y_ax_front`
# (-9.5'), and PT-SG-BF2, the centre pillar of the balcony's front row. Two faces bound the
# pour, and everything below is measured south of the beam axis:
#
#     beam north face   2 1/4" NORTH   (half of the 4 1/2" 3-2x12)
#     BF2 south face      12"   SOUTH  (= `_y_balcony_front`; see `_y_front_pillar`)
#     ------------------------------------------------------------------
#     must span         14 1/4"
#
# Centring on that span puts the axis 4 7/8" south — `_y_front_col`, -9.90625' — and leaves
# the slack split evenly. Sizing against a ~4 5/8" anchor edge distance for the ABU66SS at
# BF2 (the anchor sits on the pillar axis, 9 1/4" south, so 4 3/8" off the column axis):
#
#     dia    edge cover    anchor edge    verdict
#     16"      0.875"        3.625"       no — anchor 1" inside its edge distance
#     18"      1.875"        4.625"       exactly at the ABU66SS minimum, no margin
#     20"      2.875"        5.625"       chosen
#     22"      3.875"        6.625"       more tube than the joint asks for
#
# Bearing is not what governs and never was: ~30 psi under the two beam ends and ~56 psi
# under BF2, on 4,000 psi concrete. 20" is a standard sonotube, 18" is not stocked
# everywhere, and the 18" row has no margin to spend on a form that drifts half an inch off
# its layout — which fibre tubes do. Note that 18" only became feasible at all when the
# front pillars came 2 3/4" north on 2026-08-30; before that the span was 17" and neither
# 16" nor 18" had a solution. The two decisions are coupled and neither is free.
#
# ``size="20 round"``. Never a nominal form like "20x20": that matches ``_RE_NOMINAL`` in
# resolve/framing/profiles.py, misses LUMBER_ACTUAL and silently resolves to 1.5x5.5. The
# round spelling sidesteps the trap entirely and is the same one the five 12" sonotubes use.
#
# Detailing that the model has no field for, so it lives here and in the assembly's
# ``source``: a >=15 degree wash struck on the top (BIA Technical Note 36A) with the beam
# bearing set on a level non-shrink-grout island; mix 4,000-4,500 psi, w/cm <= 0.45,
# 6.0-6.5% air at 3/4" aggregate (Minn. R. 1309.0402 plus ACI 318-19 class F2); broom or
# float finish, never steel-trowelled (troweling drives the entrained air out of exactly the
# layer that scales — NRMCA CIP 2); silane/siloxane repellent. Bearing was never the
# question: a 6x6 at Fc-parallel 1,000 psi is ~30 kip, long before the concrete governs.
#
# **It was square until 2026-08-28, and the reason it stopped being square is cost.** The
# square earned its keep on connector SIDE COVER — a CBSQ66 wants 3" and an MPB66Z 5", and a
# centred 6" plate leaves 5.00" at its corners in a 16" square, 3.76" in a 16" round, 2.1"
# in a 12" round. But that cover was being bought at $478-1,327 against $304-633 for a
# disposable fibre tube of the same height, because a square column is formed in built
# panels with chamfer strips and rubbed and patched after strip. The 20" round the shared
# bearing now asks for gives 5.76" at a centred 6" plate's corners — MORE than the square
# had — and still costs a fibre tube rather than built panels. The option the 2026-08-28
# change deliberately foreclosed came back as a side effect of a decision made for other
# reasons; plans/TODO.md's MPB66Z arithmetic is stale for it. See notes/uplift_load_path.md.
_front_beam_depth_ft = _back_beam_depth_ft  # same member (SPEC.back_beam), same soffit drop
# 4 7/8" south of the beam axis: the midpoint of the 14 1/4" the pour has to span, so the
# 20" tube keeps 2 7/8" of cover past the beam's north face AND past BF2's south face
# rather than 5/8" at one end and 2 3/8" at the other. It was 7 1/8" until 2026-08-30, when
# the front pillar row came north by half a post (`_y_front_pillar`) and the south face
# stopped being the binding constraint it had been. NOT a SPEC field: it is a solved
# consequence of `balcony_front_overhang_ft`, `_pillar_face_ft` and `front_column_size_in`,
# not an input any of them can be set against.
_front_column_south_offset_in = 4.875
_y_front_col = _y_ax_front - _front_column_south_offset_in / 12.0  # -9.90625'
# Belled to frost depth on the same terms as PT-SG-COL, and the shaft grows by the same
# ``_pier_shaft_extension_ft``. The authored height is IDENTICAL to PT-SG-COL's, and that is
# now load-bearing rather than incidental: with the front beams unpinned (see FRONT_BEAMS)
# ``_bearing_stack_drops`` propagates the 7 1/4" joist drop through ``Beam.bearing_refs`` to
# this post, so its resolved top falls from -0'-11 1/4" to -1'-6 1/2" — the same
# ``_back_beam_soffit`` PT-SG-COL lands on, by exactly the same path. Do not "correct" the
# height to compensate; the resolver has already done it.
FRONT_COLUMN = Post(uid="SGP002AAAA", tag="PT-SG-FCOL",
                    position=pt(ft(_cx), ft(_y_front_col)), size="20 round",
                    height=ft(SPEC.basement_depth_ft - _front_beam_depth_ft
                              + _pier_shaft_extension_ft),
                    supported_by="FT-SG-FCOL",
                    assembly="SUNKEN_GARDEN_COLUMN_20")

# Wall footing uids are a literal map keyed on the wall tag, not ``enumerate(WALLS)``.
# They used to be minted by position, so retiring W-SG-ARCH (which was index 1) would have
# shifted every surviving footing's uid — and therefore its IFC GlobalId — by one. The map
# keeps SGF102..SGF106 on the walls they have always belonged to; a new wall takes the next
# free number rather than renumbering its neighbours. Same reasoning for the beds below.
_WALL_FOOTING_UID = {"W-SG-W1": "SGF102AAAA", "W-SG-E1": "SGF103AAAA",
                     "W-SG-W2": "SGF104AAAA", "W-SG-E2": "SGF105AAAA",
                     "W-SG-S": "SGF106AAAA"}
# FT-SG-W1/E1 are 13" thick, not the 12" the other three carry. That extra inch is the one
# the porch walls gave up when they were trimmed to 10'-0" (see `_porch_wall_bottom`): a
# footing's top follows the wall bottom above it, so without this the two footings would
# have RISEN an inch and lost an inch of the 21" of cover that IRC R403.3 wing insulation
# under SL-SG-FLOOR is sized against. Thickening instead of raising keeps every underside,
# every bedding undercut and every cover figure where the frost design left them.
_PORCH_FOOTING_THICKNESS_IN = {"W-SG-W1": 13.0, "W-SG-E1": 13.0}
# ============================================================================
# THE THREE RETAINING FOOTINGS GROW INBOARD ONLY: 7'-0" -> 8'-0", OFFSET 6" (2026-08-30).
# ============================================================================
# At at-rest the resultant on a 7'-0" base falls OUTSIDE the middle third — e = 1.30' against
# a kern of 1.17' — so the heel lifts and the trapezoidal bearing distribution the record
# reports stops describing anything. That is a real limit state and it is the one thing the
# grade beam does not fix: closing the loop answers sliding, and eccentricity is a moment
# question about one wall's own footing.
#
# **Widening symmetrically is what you would reach for and it is the one thing that does not
# fit.** `params/raised_garden.py` measures its apron's 3'-0" clear offset — the owner's own
# figure, from the brief — so the legs' inner faces land EXACTLY on these footings' outboard
# edges at x = 4.5 / 31.5 and y = -32.833. Tangent, no overlap, and
# `test_catlin_outdoor_structures.py` asserts it. Any symmetric widening walks the outboard
# edge under the apron and moves a wall the brief pins.
#
# The court side is free, so the concrete goes there instead. `Footing.offset` slides the
# strip 6" toward the toe, which leaves the OUTBOARD edge exactly where the 7'-0" strip left
# it — 4.0' + 0.5' half-stem + 3.0' heel = 4.5 on the west, and the mirror east and south —
# and puts the extra 12" of width entirely under the garden floor where nothing is. Toe
# 4'-0" / heel 3'-0". The apron does not move, its assertion does not change, and the heel —
# the term that carries the stabilising column of soil — is untouched at 3'-0".
#
# +2.10 CY over the three runs. FT-SG-W1/E1 keep the shared 84": they are braced top and
# bottom, the prescriptive table answers them, and neither has an eccentricity question.
_RETAINING = ("W-SG-W2", "W-SG-E2", "W-SG-S")
_RETAINING_FOOTING_WIDTH_IN = 96.0
# Positive along the LEFT-hand normal of each wall's own start->end direction, which is the
# frame `resolve/geometry.rect_between` lays the strip out in. All three wind the same way
# around the court (W2 runs MW->SW, E2 runs SE->ME, S runs SW->SE), so +6" is "into the
# court" for every one of them — checked, not assumed: see the footing-edge assertions in
# `test_retaining_court.py`.
_RETAINING_FOOTING_OFFSET_IN = 6.0
FOOTINGS = [
    Footing(uid=_WALL_FOOTING_UID[w.tag], tag=f"FT-{w.tag[2:]}", under=w.tag,
            width=inch(_RETAINING_FOOTING_WIDTH_IN if w.tag in _RETAINING
                       else SPEC.footing_width_in),
            offset=inch(_RETAINING_FOOTING_OFFSET_IN) if w.tag in _RETAINING else None,
            depth=inch(_PORCH_FOOTING_THICKNESS_IN.get(w.tag, SPEC.footing_thickness_in)))
    # W-SG-ARCH is deliberately absent: the buried grade beam carries 219 plf over its own
    # 12" of bearing and bears straight on FB-SG-ARCH. See its own block in WALLS.
    for w in WALLS if w.tag in _WALL_FOOTING_UID
]
# The two porch piers' BELLS. FT-SG-COL keeps SGF199AAAA; the front column's is appended
# after it, so nothing already in the IFC moves.
#
# ``bottom_elevation`` is what makes these bells rather than plinths: a post-hosted footing
# tops out on its storey datum unless it says otherwise, which put both of these flush with
# the garden floor on 12" of cover. Authored, the UNDERSIDE is the fixed end — the bell
# bears at ``_pier_bell_bottom_ft`` and is ``depth`` thick above it — which is exactly how
# a hole is dug. Width and thickness are untouched: only the elevation changed.
FOOTINGS.append(
    Footing(uid="SGF199AAAA", tag="FT-SG-COL", under="PT-SG-COL",
            width=inch(_col_footing_width_in),
            depth=inch(SPEC.footing_thickness_in),
            bottom_elevation=ft(_pier_bell_bottom_ft))
)
FOOTINGS.append(
    Footing(uid="SGF198AAAA", tag="FT-SG-FCOL", under="PT-SG-FCOL",
            width=inch(_front_footing_width_in),
            depth=inch(SPEC.footing_thickness_in),
            bottom_elevation=ft(_pier_bell_bottom_ft))
)

# The five WALL footings bear on a shared 42" compacted-aggregate section, and that section
# is their frost design — see ``non_frost_susceptible`` below. The two column BELLS do not:
# they were augered to frost depth on 2026-08-29 and bear on undisturbed soil there, so
# what goes under them is a levelling course, not a replacement section (see
# ``_PIER_BELL`` at the undercut).
#
# The footings adjacent to the house (the two porch side walls, along the north edge) are
# additionally doweled to the house footing with fiberglass rebar across a 40 psi XPS foam
# block that breaks the thermal bridge; ``cast_foam_in_aggregate`` records that foam in the
# resolved geometry / IFC (the dowels themselves are annotation-only — see plans/TODO.md).
#
# **FT-SG-COL LEFT THIS SET WHEN ITS BELL WENT TO FROST DEPTH (2026-08-29), and there is
# nothing to replace it with.** A dowel-and-foam joint needs two concretes meeting at one
# plane: it broke a bridge that existed because the garden bell and FT-B-S2 sat at the same
# elevation, 2" apart, with the block between them. The bell bears 2'-6" lower now, so its
# top is 1'-10" below FT-B-S2's underside and the two pours no longer face each other at
# all — there is no joint to dowel and no bridge to break, because the separation itself is
# the break. Leaving the flag on would cast a foam block into aggregate with nothing on the
# far side of it. The two side walls are unchanged and keep theirs; their footings never
# moved. See DOWELS below, where DW-SG-COL went for the same reason.
_HOUSE_ADJACENT = {"FT-SG-W1", "FT-SG-E1"}
# The two bells reach frost depth on their own, so their beds are levelling courses. A
# footing bearing where it is meant to bear still wants a few inches of clean stone under
# it — a flat, free-draining seat at the bottom of an augered hole, and the host for the
# tile that has to get water out of these two excavations — but 42" of soil REPLACEMENT
# under a bell that is already at 42" is stone bought twice for one result. It is also
# stone that does not fit: 42" under the new bell underside would bottom the excavation at
# -16'-1 7/16", which is 1'-9" BELOW _SG_DRYWELL_TOP, so the bearing bed and the soakaway
# it is supposed to sit on top of would swap places and intersect. Measured, not assumed —
# the old bed bottomed at -13'-7 7/16" and cleared the well's stone by 9".
_PIER_BELL = {"FT-SG-COL", "FT-SG-FCOL"}
_BEDDING_UID = {"FT-SG-W1": "SGB002AAAA", "FT-SG-E1": "SGB003AAAA",
                "FT-SG-W2": "SGB004AAAA", "FT-SG-E2": "SGB005AAAA",
                "FT-SG-S": "SGB006AAAA", "FT-SG-COL": "SGB007AAAA",
                "FT-SG-FCOL": "SGB008AAAA"}
FOOTING_BEDDING = [
    FootingBedding(
        uid=_BEDDING_UID[f.tag],
        tag=f"FB-{f.tag[3:]}",
        host_ref=f.tag,
        undercut=inch(SPEC.pier_levelling_bedding_in if f.tag in _PIER_BELL
                      else SPEC.aggregate_bedding_depth_in),
        # **This flag is what makes the garden's WALL footings frost-protected**, and it is
        # an authored claim about the stone, not a derived property of it. It says the
        # ``aggregate`` above — ASTM C33 #57 washed crushed stone — is non-frost-
        # susceptible: an open-graded single-size (nominal 1" to #4) washed coarse
        # aggregate carries essentially nothing through a #200 sieve, far inside the <6%
        # by mass that ASTM D422 gradation analysis sets for NFS. Washed is load-bearing
        # in that sentence; the same stone unwashed is not the same claim.
        #
        # Why it matters here: every footing in this structure stands INSIDE the court it
        # helps retain, so its cover is measured from SL-SG-FLOOR 9' down, not from the
        # site plane, and the five WALL footings have 21" of concrete against a 42"
        # minimum. What reaches the minimum is the excavation: a 42" section of drained
        # NFS stone under a 12-13" footing bottoms out 63" below that same floor. ASCE 32
        # counts a *well-drained* NFS layer's thickness toward the design frost depth —
        # soil replacement — and IRC R403.1.4.1 admits a foundation built to ASCE 32 as one
        # of its listed frost-protection methods, which MN Rules 1309.0403 keeps. The
        # drainage half of "well-drained" is the tile below and the DRW-SG-MAIN discharge
        # it runs to; drop either and the claim is not ASCE 32's and
        # ``structural.frost_depth`` stops counting the section.
        #
        # The two BELLS keep the flag and no longer need it: they carry 42" of true cover
        # since 2026-08-29 and pass on depth, in the check's plain ``covered`` bucket. It
        # stays because it is still a true statement about the stone under them, and
        # because the levelling course is drained to the same well — an authored fact
        # should not blink out because a second, better one arrived.
        #
        # Scoped deliberately to this structure. The house's own beddings
        # (params/foundations.py) are the same order of stone but have not been reasoned
        # about here, and an unstated section is worth nothing rather than being assumed.
        non_frost_susceptible=True,
        cast_foam_in_aggregate=f.tag in _HOUSE_ADJACENT,
        # Same 4" sock-wrapped tile as the house footings (params/foundations.py). Unlike
        # the house's, this tile cannot daylight — the garden floor is 9' down with no grade
        # to run out to — so it discharges to DRW-SG-MAIN instead.
        drain_tile_spec=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    )
    for f in FOOTINGS
]
# W-SG-ARCH's bed, appended rather than swept up by the comprehension above because it is
# hosted on the WALL and not on a Footing — the grade beam has none (see WALLS). Same 42"
# undercut, same NFS claim about the same stone, same 4" sock-wrapped tile to DRW-SG-MAIN,
# so it joins the existing takeoff group rather than starting a second one. It is NOT
# `cast_foam_in_aggregate`: that is for the house-adjacent footings' thermal break, and this
# beam is 11'-0" south of the house with unconditioned court on both faces.
#
# `width` is authored because a wall-hosted bed defaults to the wall's own thickness, and a
# 12" trench is not something anyone can dig, compact or lay tile in. 24" is the beam plus 6"
# of working room each side.
#
# `GARDEN_DRYWELL.inlet_refs` derives from FOOTING_BEDDING wholesale, so the well picks this
# bed up with nothing authored for it, and the well's top already sits on the wall beds'
# underside — which is this bed's underside too, the beam being flush with them.
FOOTING_BEDDING.append(
    FootingBedding(
        uid="SGB009AAAA", tag="FB-SG-ARCH", host_ref="W-SG-ARCH",
        width=inch(24),
        undercut=inch(SPEC.aggregate_bedding_depth_in),
        non_frost_susceptible=True,
        drain_tile_spec=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    )
)

# The sunken garden's own soakaway — a hole dug to take water and give it to the soil,
# below (not part of) the 42" bearing bed. The garden floor sits 9' down with no downhill
# side, so everything landing here (perimeter tile, the slab itself) has nowhere to go but
# down. The balcony leader used to be on that list; it hangs outside the east wall now and
# discharges to the terrace, so the well is left carrying only the water it cannot avoid.
# Top of stone sits at the WALL beds' underside so the two stack rather than intersect —
# and it is derived from the wall beds on purpose, ``SPEC.aggregate_bedding_depth_in``
# being their number: the two column bells took a 7" levelling course on 2026-08-29 and
# their beds now stop 2'-9" short of this plane, which is clearance, not a gap to close.
# 6' of fabric-wrapped stone below (unwrapped, this clay silts its voids shut in a
# season). Tagged DRW-, not DW-, because DW- is the dowel prefix and the two collided.
_SG_DRYWELL_TOP = ft(-(SPEC.basement_depth_ft + 0.75)
                     - SPEC.footing_thickness_in / 12.0
                     - SPEC.aggregate_bedding_depth_in / 12.0)
GARDEN_DRYWELL = Drywell(
    uid="SGDR01AAAA", tag="DRW-SG-MAIN",
    position=pt(ft(_cx), ft((_y_in_s + _y_in_n) / 2.0)),
    diameter=ft(5), depth=ft(6), geotextile=True,
    top_elevation=_SG_DRYWELL_TOP,
    inlet_refs=tuple(b.tag for b in FOOTING_BEDDING),
)

# --- garden slab (basement floor of the sunken garden) ---------------------------
GARDEN_SLAB = Slab(
    uid="SGS501AAAA", tag="SL-SG-FLOOR",
    outline=(pt(ft(_x_in_w), ft(_y_in_s)), pt(ft(_x_in_e), ft(_y_in_s)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.slab_thickness_in),
)

# --- FPSF wing insulation under the garden slab, along the house ------------------------
#
# IRC R403.3, Figure R403.3(3): the heated-building-adjoining-an-unheated-slab case, which is
# what a heated basement beside an open sunken court is. Table R403.3(1) at design AFI 2500
# (Minneapolis-St Paul) wants R-1.7 over B = 24" along the wall and R-4.9 over C = 40" at the
# corners; SG_FROST_WING_XPS1/2 in plan/assemblies.py carry R-5 and R-10 and the citation.
#
# WHY THIS EXISTS: `structural.frost_depth` measured every footing against one global grade
# plane until 2026-08-22 and therefore passed all 35 of them — including FT-B-S1/S2/S3 with
# 8" of cover below the garden floor, and FT-B-BRICK with 2" of NEGATIVE cover. Frost depth
# is measured from the lowest adjacent grade, and beside these footings that is the garden
# floor at -9'-4", not the -2'-10" site plane six and a half feet above it.
#
# WHY SLABS: a horizontal band of foam has no other element kind to be. `Layer.extent`
# measures from WALL_BASE / WALL_TOP / GRADE — all vertical — so it cannot describe a skirt
# reaching sideways under a floor. These are thin `Slab`s with a single-INSULATION-layer
# assembly, which bills by the square foot through `envelope_layer_takeoff` like any other
# insulation. `resolve/site_earth._is_a_floor` keeps them from being read as excavation
# floors in their own right (they are buried, not stood on), and prices.toml carries a zero
# qualified key so `structural_solids_takeoff` does not also bill them by the cubic yard.
#
# The wings sit directly under SL-SG-FLOOR: garden slab top -9'-4" less its own 3 1/2" is
# -9'-7 1/2", which is the wings' top.
_WING_TOP = inch(-(SPEC.basement_depth_ft * 12.0) - SPEC.slab_thickness_in)
_WING_ALONG_FT = 24.0 / 12.0   # Table R403.3(1) dimension B
_WING_CORNER_FT = 40.0 / 12.0  # Table R403.3(1) dimension C

FROST_WINGS = [
    # The two re-entrant corners, where the garden's own east and west retaining walls meet
    # the house and frost drives in from two directions at once: C = 40" each way, 2" XPS.
    Slab(uid="SGFW01AAAA", tag="SL-SG-FROST-W", assembly="SG_FROST_WING_XPS2",
         outline=(pt(ft(_x_in_w), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_x_in_w + _WING_CORNER_FT), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_x_in_w + _WING_CORNER_FT), ft(_y_in_n)),
                  pt(ft(_x_in_w), ft(_y_in_n))),
         thickness=inch(2.0), top_elevation=_WING_TOP),
    Slab(uid="SGFW02AAAA", tag="SL-SG-FROST-E", assembly="SG_FROST_WING_XPS2",
         outline=(pt(ft(_x_in_e - _WING_CORNER_FT), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_x_in_e), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_x_in_e), ft(_y_in_n)),
                  pt(ft(_x_in_e - _WING_CORNER_FT), ft(_y_in_n))),
         thickness=inch(2.0), top_elevation=_WING_TOP),
    # The run between them, along the wall: B = 24", 1" XPS.
    Slab(uid="SGFW03AAAA", tag="SL-SG-FROST-N", assembly="SG_FROST_WING_XPS1",
         outline=(pt(ft(_x_in_w + _WING_CORNER_FT), ft(_y_in_n - _WING_ALONG_FT)),
                  pt(ft(_x_in_e - _WING_CORNER_FT), ft(_y_in_n - _WING_ALONG_FT)),
                  pt(ft(_x_in_e - _WING_CORNER_FT), ft(_y_in_n)),
                  pt(ft(_x_in_w + _WING_CORNER_FT), ft(_y_in_n))),
         thickness=inch(1.0), top_elevation=_WING_TOP),
]

# ============================================================================
# Main (porch, 0'): back + front beams on their columns, composite deck.
# ============================================================================
# The back-beam line rides at the column's south-offset (``_y_col``), not on the deck's
# north-edge line: the beams stay collinear through the column and the deck edge
# cantilevers the offset over them toward the house gap. The front line has no such offset
# — nothing to clear down there — so it sits on the deck's south edge itself.
MAIN_NODES = [
    Node(uid="SGNM01AAAA", tag="N-SGM-NW", position=pt(ft(_x_ax_w), ft(_y_col)),
         open_end=True),
    Node(uid="SGNM02AAAA", tag="N-SGM-NE", position=pt(ft(_x_ax_e), ft(_y_col)),
         open_end=True),
    Node(uid="SGNM03AAAA", tag="N-SGM-COL", position=pt(ft(_cx), ft(_y_col))),
    Node(uid="SGNM04AAAA", tag="N-SGM-FW", position=pt(ft(_x_ax_w), ft(_y_ax_front)),
         open_end=True),
    Node(uid="SGNM05AAAA", tag="N-SGM-FE", position=pt(ft(_x_ax_e), ft(_y_ax_front)),
         open_end=True),
    Node(uid="SGNM06AAAA", tag="N-SGM-FCOL", position=pt(ft(_cx), ft(_y_ax_front))),
]

# Two treated LVL back beams: sonotube column -> side-wall hangers (two ~9'6" spans).
BACK_BEAMS = [
    Beam(uid="SGBM01AAAA", tag="BM-SG-BKW", start_node="N-SGM-COL", end_node="N-SGM-NW",
         size=SPEC.back_beam, assembly="BEAM_KDAT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-COL", "W-SG-W1")),
    Beam(uid="SGBM02AAAA", tag="BM-SG-BKE", start_node="N-SGM-COL", end_node="N-SGM-NE",
         size=SPEC.back_beam, assembly="BEAM_KDAT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-COL", "W-SG-E1")),
]

# The matching front pair, DROPPED (2026-08-29). They were flush-framed — an authored
# ``top_elevation`` pinned them at the 0' joist datum and the porch joists hung into their
# north face in hangers. Deleting that pin is the single edit the whole change turns on:
# unpinned, ``_bearing_stack_drops`` (resolve/envelope.py) propagates the joists' 7 1/4"
# through ``bearing_refs`` to PT-SG-FCOL, whose top falls to ``_back_beam_soffit``, which is
# what puts PT-SG-BF2 on concrete instead of on a 2x8. Both porch beam lines frame the same
# way now — joists bearing on top — which is also why there is one soffit derivation above
# rather than two.
#
# The joists do NOT move and the porch does not grow: ``porch_joist_cantilever_in`` stays
# 0.0 and ``_PORCH_OUTLINE`` stays on `_y_ax_front`. They already ran to the beam axis, so
# they simply gain 2 1/4" of bearing on the 4 1/2" beam (IRC R507.6 wants 1 1/2"). **Do not
# add a south cantilever here.** An oversail past ``bearing_plan_tolerance_in`` (8") yields
# neither derived ties nor hangers and ``uplift_load_path`` FAILs all 32 joist members at
# once.
#
# What this costs: clear height under the front beam over the sunken garden goes
# 8'-2 3/16" -> 7'-6 15/16".
#
# ``structural.member_interference``'s ``_flush_framed_pairs`` simply loses its porch
# subject — the joist and beam boxes no longer overlap, so the clause never fires. It stays
# exercised by BM-S-HALL, BM-M-HALL, BM-S-BATH-E and its own unit test.
#
# Both runs end on the side-wall axes, exactly mirroring BM-SG-BKW/BKE: the 6" pocket inside
# the 12" wall band is the modelled hanger detail already in use at the back.
# BEAM_WHITE_PAINT, not BEAM_KDAT: this pair faces the garden in the same plane as the six
# white pillars, so it is painted with them (2026-08-27). Same KDAT stock, same section —
# see plan/assemblies.py::BEAM_WHITE_PAINT. The BACK pair keeps BEAM_KDAT: it is behind the
# porch deck against the house and nobody sees it.
FRONT_BEAMS = [
    Beam(uid="SGBM03AAAA", tag="BM-SG-FRW", start_node="N-SGM-FCOL", end_node="N-SGM-FW",
         size=SPEC.back_beam, assembly="BEAM_WHITE_PAINT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-FCOL", "W-SG-W1")),
    Beam(uid="SGBM04AAAA", tag="BM-SG-FRE", start_node="N-SGM-FCOL", end_node="N-SGM-FE",
         size=SPEC.back_beam, assembly="BEAM_WHITE_PAINT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-FCOL", "W-SG-E1")),
]

# The porch floor's footprint. Used to be a separate ``SL-SG-PORCH`` Slab standing in for
# the framing while FS-SG-PORCH drew the joists under it — two elements claiming one floor.
# The floor system is the floor now; the outline lives here so joists, pillar bearings, etc.
# share one source.
_PORCH_OUTLINE = (pt(ft(_x_in_w), ft(_y_ax_front)), pt(ft(_x_in_e), ft(_y_ax_front)),
                  pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n)))

# The porch guard: the same metal fascia-mounted rail as RL-SG-BALCONY one storey up, in
# place of the 42" brick/CMU parapet that used to ride the retired cross-wall and the two
# side walls. A pair of LVL beams cannot carry ~420 plf of masonry the way 16" of concrete
# could, so the guard had to become light when the wall did.
#
# West / south / east only — the north edge is the 5" house gap. ``base_elevation`` is the
# walking surface, not the joist tops: the 42" is measured from what a person stands on.
# The front corners are flush now, not stepped: W-SG-W1/E1 run 18" past this line at the
# porch top so the balcony's front pillars bear on them, so the +6" curb that used to meet
# the guard here (W-SG-W2/E2 standing proud of the deck, hidden behind 42" of brick before
# the parapet was retired) starts 18" further south and the guard runs out over the side
# walls' own tops. RL-SG-BALCONY is on a different plane entirely now — 12" south of this
# one — so the two guards read as two edges rather than one.
_PORCH_GUARD_PATH = (pt(ft(_x_in_w), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_ax_front)),
                     pt(ft(_x_in_e), ft(_y_ax_front)), pt(ft(_x_in_e), ft(_y_in_n)))
PORCH_GUARD = Railing(
    uid="SGRA02AAAA", tag="RL-SG-PORCH", type_ref="RAILING-EXT-ALUMINUM-FASCIA",
    path=_PORCH_GUARD_PATH, kind=RailingKind.METAL_FASCIA_MOUNT,
    height=ft(SPEC.railing_height_ft),
    base_elevation=_porch_walking_surface,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="fascia",
    assembly="RAILING_DARK_METAL",
    # R312.1.3: vertical balusters between the 60" posts at a 4" clear gap.
    infill="balusters", baluster_spacing=inch(4))

# ============================================================================
# Second (balcony, ~10'): 6x6 pillars, three 3-ply 2x12 beams, aluminum deck.
# ============================================================================
# Six pillars. Four land on the two porch side walls at 0'-0"; PT-SG-BF2 lands on the front
# column's top at -1'-6 1/2" (2026-08-29); only PT-SG-BR2 stands on the porch decking. Until the
# masonry guard was retired, five of the six started 42" higher, on top of it; now each is
# that much longer, and the pillar *tops* are unchanged because height is measured back from
# the beam soffit. Rear row is 2" taller overall so the deck crowns and drains south, away
# from the house. Beam soffit = balcony level minus the beam depth, read off the size.
_balcony_beam_depth_ft = cross_section(SPEC.balcony_beam).depth_m / 0.3048
_balcony_joist_depth_ft = 7.25 / 12.0  # 2x8 deck joist
# Pillar-height *input* only — the resolver drops beam + post by the deck joist depth
# (resolve/envelope.py::_bearing_stack_drops), so the wood doesn't actually land here (see
# _balcony_beam_soffit below). Subtracting the joist depth here too would double-count it.
_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_beam_depth_ft)
# The *resolved* soffit: the pillar-top plane the beams sit on, and the plane the N-S brace
# family rises to. The E-W family rises to the rail's own (lower) soffit instead — see
# `_rail_soffit` below.
_balcony_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_joist_depth_ft
                          - _balcony_beam_depth_ft)  # 8.458'
# The rail's TOP is bolted to the pillar-top plane, not seated on it, so the rail hangs
# below the beam soffit rather than riding flush with the beam tops the way the old girts
# did.
_rail_depth_ft = cross_section(SPEC.balcony_brace_rail).depth_m / 0.3048
_rail_top = _balcony_beam_soffit  # 8.458' — the pillar-top plane
_rail_soffit = _balcony_beam_soffit - ft(_rail_depth_ft)  # 7.854'
# Both rails sit at the same top elevation even though the rear posts run 2" proud
# (rear_pillar_rise_in) — face-bolted, not bearing, so the drainage crown doesn't need to
# propagate, which is why all four E-W braces become geometrically identical and the old
# rear-row hanger-saddle detail goes away.
# _RAIL_FACE_OFFSET_FT is defined below, once _pillar_face_ft exists.
_PILLAR_X = (_x_ax_w, _cx, _x_ax_e)
# (row, x index) -> (the concrete wall top that pillar bears on, its elevation). Anything
# not in the map bears on the porch decking instead.
#
# All four outer pillars bear on the two porch side walls at `_porch_top`. The front pair
# used to be handed to W-SG-W2/E2 at the retaining top, 6" higher, because the wall junction
# sat on their own axis and they overhung it — a pillar half on a wall whose head is
# unbraced (R404.4) and half on one the porch frames into. `side_wall_south_extension_in`
# runs W1/E1 past the pillars so the map can say the true thing; the two front pillars are
# longer for it and their ABU66SS bases came down with them, but the beam soffit they rise
# to has not moved. That extension went 6" -> 18" on 2026-08-29 to follow the front row's
# 12" move south — without it the same failure would have come straight back.
#
# ``("F", 2)`` is not a wall at all: PT-SG-BF2 stands on the CONCRETE COLUMN (2026-08-29),
# on the same ``_back_beam_soffit`` the two front beams land on. That one entry drives the
# pillar's ``supported_by``, its base elevation, its length AND ``CN-SG-BASE-F2``'s
# ``connects`` and elevation, because the bases are generated from ``PILLAR_BEARINGS``
# below. **Post-on-post is a supported path** — ``resolve_columns_and_beams`` republishes
# each post's resolved top as it goes (envelope.py), precisely so a post can stand on a
# concrete pier; ``breezeway.py``'s Pad -> PR-BW-* -> PT-BW-* is the live precedent.
# Ordering holds because PT-SG-FCOL is in ``BASEMENT_ELEMENTS`` and PT-SG-BF2 in
# ``SECOND_ELEMENTS``.
_WALL_UNDER_PILLAR = {
    ("R", 1): ("W-SG-W1", _porch_top), ("R", 3): ("W-SG-E1", _porch_top),
    ("F", 1): ("W-SG-W1", _porch_top), ("F", 3): ("W-SG-E1", _porch_top),
    ("F", 2): ("PT-SG-FCOL", _back_beam_soffit),
}
# The rear pillar row rides on the *back-beam* line, not on the deck's north edge
# (2026-08-28). It used to sit at ``_y_in_n``, which put PT-SG-BR2 on the cantilevered tip
# of the porch joists — a 6x6 carrying a third of the balcony, standing on the free end of
# one 1 1/2" ply. That was mitigated (3-ply sisters + blocking + an uplift tie) rather than
# deleted. Moving the row south to the beam line deletes it: PT-SG-BR2 now lands directly
# over PT-SG-COL, on the shared bearing of BM-SG-BKW/BKE, so the load runs plank -> joist
# -> back beam -> cast column -> footing. That mirrors PT-SG-BF2 over PT-SG-FCOL, and the
# design is symmetric in kind for the first time. BR1/BR3 stay on W-SG-W1/E1 (those walls
# run _y_in_n -> _y_ax_s), so ``_WALL_UNDER_PILLAR`` is unchanged and they gain edge cover.
#
# The 3" south of the beam axis is deliberate and is NOT slop. ``_band`` in
# checks/structural/cantilever.py tests ``post_axis >= axis_hi - end - _EPS``, so a pillar
# landed exactly on the bearing line still reads as inside the overhang and reports a 0"
# overhang with ``past_m = 0.0`` — a finding about a joint that no longer exists. 3" into
# an 87" back span is structurally indistinguishable and lets the check go silent honestly.
# **Do not widen ``_EPS`` instead**; the offset is the statement, not a workaround.
#
# What moves with the row: RAIL_NODES' two rear nodes and ``_ROW_Y["R"]`` (the knee-brace
# origins). What does NOT move: SECOND_NODES, the deck outline, guard, fascia, gutter and
# rear counter-flashing, all keyed to ``_y_in_n``. So the three balcony beams keep their
# full length and gain a north cantilever past the rear pillars:
#
#     back span   = _y_rear_pillar - _y_balcony_front = -2.5 - (-10.5) = 8.00' = 96"
#     overhang    = _y_in_n - _y_rear_pillar         = -0.833 - (-2.5) = 1.667' = 20.0"
#     R507.5.1 limit = back span / 4                 = 96" / 4         = 24.0"  -> OK by 4"
#
# That arithmetic is written down because nothing checks it: checks/structural/deck.py
# grades beam *span* only and has no beam-cantilever rule, so this overhang would pass
# silently either way. See notes/beam_water_protection.md, which carries the missing check
# as an open item. IRC Table R507.5(1) is keyed on the JOIST span, which is unchanged at
# FS-SG-DECK's 10.00' (limit 9.17' for a 3-2x12), so what this buys is margin: the three
# balcony beams go from 8.667' against 9.17' — 6" of headroom — to 8.00' against 9.17',
# 14". (It was 7.00' between 2026-08-28 and 2026-08-29, when the FRONT row moved 12" south
# in turn; the front move spends 12" of what the rear move bought.) That still retires the
# knife-edge: at 8.00' these beams pass even on the 12' row (8.33'), which is what any
# further increase in the deck's joist span would drop the lookup to.
_REAR_PILLAR_SOUTH_OF_COL_IN = 3.0
_y_rear_pillar = _y_col - _REAR_PILLAR_SOUTH_OF_COL_IN / 12.0  # -2.5'
_pillar_face_ft = 2.75 / 12.0  # half the 5.5" actual 6x6
# The rail's own centreline offset from the row's pillar axis: half the post plus half the
# rail (2.75" + 0.75" = 3.5"). Used by both the rail nodes and the E-W knee brace positions.
_RAIL_FACE_OFFSET_FT = (_pillar_face_ft
                        + cross_section(SPEC.balcony_brace_rail).width_m / 2 / 0.3048)

# The FRONT row stands 2 3/4" north of `_y_balcony_front`, and the rear row does not, and
# the asymmetry is a weather detail rather than a structural one (2026-08-30).
#
# BM-SG-BLW/BLC/BLE END on the front pillar line — N-SGB-SW/SC/SE are the beams' south
# nodes. A beam that stops on its post's AXIS covers the north half of that post's top and
# leaves the south half, 2 3/4" of end grain across the full 5 1/2", open to the sky. That
# is the classic exposed-post-top detail: water sits in the re-entrant corner against the
# beam face, wicks down the end grain, and no amount of paint on a 6x6 keeps it out for
# thirty years. Nobody frames it that way. The beam gets pushed out flush with the post's
# south face, so the post top is roofed by the member it carries.
#
# Modelled the other way round — the beam ends stay put on `_y_balcony_front` (they are the
# deck edge, the fascia line and the gutter line, none of which should move) and the POSTS
# come north by half their own width. Same joint, and it keeps every dimension that a
# drawing would carry off the deck edge.
#
# The rear row needs none of this: at `_y_rear_pillar` the beams run 20" further north to
# `_y_in_n`, so PT-SG-BR1/2/3 are mid-span under a continuous member and their tops are
# already covered. Only a post at a beam's END has this problem.
#
# What moves with the row, because it is the row: the two front RAIL_NODES, `_ROW_Y["F"]`
# (the knee-brace origins), the ABU66SS bases, and PT-SG-FCOL's axis under BF2 (see
# `_front_column_south_offset_in`, which is re-solved for the new pillar line). What does
# NOT move: the beam ends themselves, `_DECK_OUTLINE`, the guard, fascia, drip and gutter
# paths, and `BALCONY_FRONT_AXIS_Y_FT` — the published contract raised_garden.py reads.
_y_front_pillar = _y_balcony_front + _pillar_face_ft  # -10.270833'
_PILLAR_ROWS = (("R", _y_rear_pillar, inch(SPEC.rear_pillar_rise_in)),
                ("F", _y_front_pillar, ft(0)))
PILLARS = []
PILLAR_BEARINGS = {}  # pillar tag -> (bearing tag, base elevation) — reused by the bases
for _i, _x in enumerate(_PILLAR_X, start=1):
    for _row_index, (_row, _y, _rise) in enumerate(_PILLAR_ROWS):
        _bears_on, _base = _WALL_UNDER_PILLAR.get(
            (_row, _i), ("FS-SG-PORCH", _porch_walking_surface))
        _tag = f"PT-SG-B{_row}{_i}"
        PILLAR_BEARINGS[_tag] = (_bears_on, _base)
        PILLARS.append(Post(uid=f"SGPB{_i}{_row_index}AAAA", tag=_tag,
                            position=pt(ft(_x), ft(_y)), size=SPEC.pillar_size,
                            height=_beam_soffit - _base + _rise,
                            supported_by=_bears_on,
                            assembly="POST_WHITE_PAINT"))

# The two CENTRE pillars are no longer alike, and that asymmetry is the point of the
# 2026-08-29 change.
#
# **PT-SG-BF2 stands on CONCRETE.** It names ``PT-SG-FCOL`` in ``supported_by`` and bears on
# that column's top at ``_back_beam_soffit``, 19 1/2" below the porch walking surface, so it
# is 19 1/2" longer than the four wall-borne pillars' geometry would suggest and there is no
# pedestal and no plank cut-out under it. ``structural.deck_post_size``'s limit at its 33.8
# ft^2 tributary is 14.00' against the resolved 10.604' — 3.4' of margin, and it still
# passes on the next table row down. Bearing on the pour is ~105 psi.
#
# **Post-on-post is a supported path**, and the prohibition that stood in this comment until
# 2026-08-29 was half stale. ``resolve_columns_and_beams`` (resolve/envelope.py) republishes
# each post's resolved top into ``solid_top`` as it goes, precisely so a post can stand on a
# concrete pier; ``breezeway.py``'s Pad -> PR-BW-* -> PT-BW-* is the live precedent, and
# ordering holds here because PT-SG-FCOL is a BASEMENT element and PT-SG-BF2 a SECOND one.
# What IS still true, and what the old note was really about: **do not retarget a Post to a
# BEAM.** Beams are resolved in the same loop but are never published into ``solid_top``, so
# a post naming one falls back to hanging below its storey datum — silently, and inside the
# beam band that ``structural.member_interference`` then FAILs on.
#
# **PT-SG-BR2 still stands on the porch decking**, names ``FS-SG-PORCH``, and keeps every
# word of the detail below. It sits 3" south of BM-SG-BKW/BKE over PT-SG-COL, so its load
# path is plank -> joist -> back beam -> cast column -> footing, and the joist it crosses is
# blocked under it (see ``FS-SG-PORCH.reinforcements``).
#
# A field detail the model has no field for, so it lives here and in POST_WHITE_PAINT's
# ``source``: **cut a 4"-square hole through the composite plank at PT-SG-BR2 so the ABU66SS
# bears on the framing below, not on the plank.** Trex's own specification says composite
# decking "cannot be used as structural material; any load bearing area will need to be
# framed and supported before the composite material can be attached". Strength is not the
# issue — the base spreads ~50 psi on the plank. The two that are:
#   * CREEP. Sustained load at the 140-160 degF summer surface temperature of a dark
#     composite plank settles this pillar relative to the five that bear on concrete, and
#     that differential takes the balcony's watertight aluminium plank out of plane.
#     Nothing in the model would see it.
#   * REPLACEABILITY. The plank is a wear layer. You cannot pull a board out from under a
#     6x6 carrying a balcony without shoring the balcony first.
#
# The aluminium-cap conflict that used to be recorded at BF2 is gone with the move: the
# pillar is 12" south of TR-SG-CAP-FRW/FRE now and lands on the pour beside them. The rule
# it stated stands for anything that ever does cross a cap — a 304-stainless base bearing on
# 0.019" aluminium coil in a wet exterior location pits the aluminium (it is anodic), and
# anchoring through it penetrates the butyl tape that IS the dielectric between that coil
# and the copper-treated KDAT. Such a base needs an EPDM or HDPE isolator pad and a written
# detail.

SECOND_NODES = [
    Node(uid="SGNB01AAAA", tag="N-SGB-NW", position=pt(ft(_x_ax_w), ft(_y_in_n))),
    Node(uid="SGNB02AAAA", tag="N-SGB-SW", position=pt(ft(_x_ax_w), ft(_y_balcony_front))),
    Node(uid="SGNB03AAAA", tag="N-SGB-NC", position=pt(ft(_cx), ft(_y_in_n))),
    Node(uid="SGNB04AAAA", tag="N-SGB-SC", position=pt(ft(_cx), ft(_y_balcony_front))),
    Node(uid="SGNB05AAAA", tag="N-SGB-NE", position=pt(ft(_x_ax_e), ft(_y_in_n))),
    Node(uid="SGNB06AAAA", tag="N-SGB-SE", position=pt(ft(_x_ax_e), ft(_y_balcony_front))),
]

# Three N-S three-ply 2x12 beams over the west / center / east pillar lines.
#
# The two OUTER beams are white-painted (BEAM_WHITE_PAINT, 2026-08-27): they are the balcony's
# west and east elevations, seen in profile from either side of the garden, in the same plane
# as the pillars under them and the rim band that closes the joists over them. BM-SG-BLC is
# the centre beam — it sits inside the deck with a joist bay either side of it and reads only
# as a shadow line from below, so it stays bare KDAT with the rest of the hidden frame.
BALCONY_BEAMS = [
    Beam(uid="SGBB01AAAA", tag="BM-SG-BLW", start_node="N-SGB-NW", end_node="N-SGB-SW",
         size=SPEC.balcony_beam, assembly="BEAM_WHITE_PAINT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-BR1", "PT-SG-BF1")),
    Beam(uid="SGBB02AAAA", tag="BM-SG-BLC", start_node="N-SGB-NC", end_node="N-SGB-SC",
         size=SPEC.balcony_beam, assembly="BEAM_KDAT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-BR2", "PT-SG-BF2")),
    Beam(uid="SGBB03AAAA", tag="BM-SG-BLE", start_node="N-SGB-NE", end_node="N-SGB-SE",
         size=SPEC.balcony_beam, assembly="BEAM_WHITE_PAINT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-BR3", "PT-SG-BF3")),
]

# E-W brace rails, hung off the pillar tops in the same band as the N-S beams — they carry
# zero gravity load (the deck's joists span E-W onto the three N-S beams only) and exist
# purely so the balcony has a lateral load path in its second direction: this is a
# freestanding structure on pinned ABU66SS bases with no other E-W load path, and an E-W
# knee brace needs an E-W member at the pillar tops to rise into.
#
# Each rail runs the full 20'-0" through all three posts in its row, on the post AXES (one
# stocked stick, no splice) rather than butting the beam faces the old girts did — it is
# face-bolted to the row's inboard face (2 x 1/2" HDG through-bolts per post), never
# notched or seated, so a housing on an exposed post face is never a water trap. That also
# ties the two centre pillars (PT-SG-BR2, PT-SG-BF2) into the two braced end bays, which is
# what lets them stay unbraced today — the rationale changes from "thrust would hit BR2"
# (false since PT-SG-BR2 moved onto the back-beam/column line) to "the rail already reaches
# them". bearing_refs=() is deliberate: the rail doesn't bear, and an empty tuple keeps
# takeoff/uplift_joints.py::post_beam_strap_rows from billing a strap at a joint that isn't
# real beam-on-post bearing.
#
# Spent uids, not reused: SGBG01AAAA/SGBG02AAAA/SGBG03AAAA/SGBG04AAAA (the four girts) and
# SGNG01..08AAAA (their eight nodes).
RAIL_NODES = [
    Node(uid="9VBVMD4AR6", tag="N-SGR-RW",
         position=pt(ft(_x_ax_w), ft(_y_rear_pillar - _RAIL_FACE_OFFSET_FT))),
    Node(uid="EQERKG45X9", tag="N-SGR-RE",
         position=pt(ft(_x_ax_e), ft(_y_rear_pillar - _RAIL_FACE_OFFSET_FT))),
    Node(uid="GMEZET9T9W", tag="N-SGR-FW",
         position=pt(ft(_x_ax_w), ft(_y_front_pillar + _RAIL_FACE_OFFSET_FT))),
    Node(uid="20Q9XQFSV9", tag="N-SGR-FE",
         position=pt(ft(_x_ax_e), ft(_y_front_pillar + _RAIL_FACE_OFFSET_FT))),
]
BALCONY_RAILS = [
    Beam(uid="XYQFW1YGXG", tag="BM-SG-RAIL-R", start_node="N-SGR-RW", end_node="N-SGR-RE",
         size=SPEC.balcony_brace_rail, top_elevation=_rail_top, assembly="BEAM_KDAT",
         top_protection=_BEAM_TAPE, bearing_refs=()),
    Beam(uid="VWWMCZ1TBG", tag="BM-SG-RAIL-F", start_node="N-SGR-FW", end_node="N-SGR-FE",
         size=SPEC.balcony_brace_rail, top_elevation=_rail_top, assembly="BEAM_KDAT",
         top_protection=_BEAM_TAPE, bearing_refs=()),
]

# Aluminum decking walking surface (framing = 2x8 joists, E-W @ 16" o.c., on the 3 beams).
# The joists cantilever 6" past the outer (west/east) beam axes, so the decking reaches to
# those tips (beam axis ± cantilever), not just to the inner-face line the beams sit inboard of.
_cant_ft = SPEC.joist_cantilever_in / 12.0
_deck_x_w = _x_ax_w - _cant_ft
_deck_x_e = _x_ax_e + _cant_ft
# The plank outline, kept as a constant now that no Slab draws it: TR-SG-FASCIA and the two
# flashings are dimensioned off this deck edge, and so is _FRONT_PATH / _REAR_PATH below.
_DECK_OUTLINE = (pt(ft(_deck_x_w), ft(_y_balcony_front)),
                 pt(ft(_deck_x_e), ft(_y_balcony_front)),
                 pt(ft(_deck_x_e), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_in_n)))

# --- joist framing under the two decks (rendered members beneath the surface slabs) ---
# Porch: PT 2x8 @ 16" o.c. running N-S between the two beam lines — hung flush in the front
# pair, bearing on the back pair and cantilevering the column's offset past it.
PORCH_JOISTS = FloorSystem(
    uid="SGFS01AAAA", tag="FS-SG-PORCH",
    joists=JoistSpec(member=SPEC.porch_joist, spacing=inch(SPEC.porch_joist_oc_in),
                     direction="y",
                     # South (start) end: no cantilever. The joists run to the front-beam
                     # AXIS and stop there, so the deck stops on that axis and each joist
                     # takes 2 1/4" of bearing on the 4 1/2" beam (R507.6 wants 1 1/2").
                     # They hung *in* those beams until 2026-08-29; the beams dropped, the
                     # joists did not move. Do not add an oversail here — past the 8"
                     # ``bearing_plan_tolerance_in`` the uplift check finds neither a
                     # derived tie nor a hanger and FAILs all 32 members.
                     # North (end): the joists run the column's south-offset past the
                     # back-beam line to the deck edge, which is the porch's real overhang.
                     # One symmetric value cannot say both.
                     cantilever=inch(SPEC.porch_joist_cantilever_in),
                     cantilever_end=inch(SPEC.column_south_offset_in),
                     # Four boundaries with two duplicate pairs: front and back are each two
                     # collinear beams meeting over their column, so the span solver sees
                     # the same two cut lines twice and drops the degenerate segment.
                     # Member count is unchanged from the single-wall bearing.
                     bearing_refs=("BM-SG-FRW", "BM-SG-FRE",
                                   "BM-SG-BKW", "BM-SG-BKE")),
    # SQUASH BLOCKS under PT-SG-BR2, and nothing else (2026-08-29).
    #
    # The 2026-08-28 note that removed the old 3-ply cluster from here was right about the
    # reason it gave: the pillar row had moved onto the back-beam line, so the CANTILEVER
    # reason for reinforcement was gone and ``structural.cantilever_point_load`` went
    # honestly silent. But rollover and cross-grain bearing under a 6x6 point load are a
    # DIFFERENT reason and they survived the move. BR2 still bears through one 1 1/2" ply of
    # 2x8: ~315 psi under the ABU66SS and ~385 psi where that joist crosses the beam, against
    # an Fc-perp of 425 psi (SPF) with no duration factor. Nothing grades it —
    # ``structural.landing_post_bearing`` is the rule that would, and it is scoped to stair
    # landing posts (see plans/TODO.md).
    #
    # Its opposite number PT-SG-BF2 stopped needing this on the same day, by bearing on
    # PT-SG-FCOL outright (~105 psi on concrete). BR2 cannot follow it: PT-SG-COL's top is
    # 3" north of the pillar and the back beams are what stand between them.
    #
    # ``plies=1`` is load-bearing, exactly as it is on FS-SG-DECK's heat-pump hosts below:
    # ``_reinforcement_members`` lays ``range(plies - 1)`` sisters, i.e. NONE, and only the
    # two blocks. What this needs is a bearing block against rollover, not a stiffened joist,
    # and it keeps ``test_no_catlin_deck_sisters_a_joist`` green.
    reinforcements=(
        JoistReinforcement(
            at=pt(ft(_cx), ft(_y_rear_pillar)), plies=1, blocking=True,
            source="squash blocks under PT-SG-BR2 — a 6x6 carrying a third of the balcony "
                   "bears through one 2x8 ply here; the blocks take the cross-grain load "
                   "into the back beams instead of into the joist's web"),
    ),
    outline=_PORCH_OUTLINE,
    # The composite plank *is* this deck's sheet: with SL-SG-PORCH gone the boards are the
    # floor system's own surface layer, which is both what a person stands on (the balcony
    # pillar that misses the masonry railing bears here) and what the sheet-goods take-off
    # bills. This is the deleted slab's one-inch PORCH_DECK_COMPOSITE layer, in place.
    subfloor=DeckLayer(material_ref="composite-deck",
                       thickness=inch(SPEC.porch_deck_thickness_in)),
    # Butyl over every joist, rim and block top. This deck is the one that needs it most in
    # the whole house: the composite plank above it is GAPPED, so rain reaches the framing
    # tops directly, and it does so on a deck that is a roof over occupied space.
    top_protection=_BEAM_TAPE,
    # ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
    # 40-psf floor table — see checks/structural/deck.py.
    service="deck",
    source="porch floor — PT 2x8 joists bearing on the front and back beam lines",
)

# Balcony: 2x8 @ 16" o.c. running E-W across the three N-S beams.
#
# SL-SG-DECK, a `datum="walking_surface"` Slab holding the aluminium plank, used to sit on
# top of this and was deleted on 2026-08-22 — the same conversion SL-SG-PORCH had in
# 3bf2f48, and for the same reason. A plank laid over joists is a floor system's SURFACE
# LAYER, not a slab: as a Slab it resolved into `structural_solids` with category "slab",
# where it could only be billed by the cubic yard out of a table named [concrete], and it
# read as a second floor plane sitting on the deck in section and in the GLB. As a
# `subfloor` it is a sheet over the joist field, bills by the square foot in
# [sheet_goods] beside the porch's composite plank, and there is one floor here again.
#
# The area survives the move EXACTLY, which is why this one is safe: `resolve/floors.py`
# draws the deck sheet bearing-line to bearing-line PLUS both cantilevers, by the joists'
# perpendicular extent — that is _x_ax_w - 6" to _x_ax_e + 6" by the balcony's front plane
# to _y_in_n, which was the deleted slab's outline term for term. (Both moved 12" south
# together on 2026-08-29; the identity is between the outline and the joists, not with any
# fixed number.)
# ============================================================================
# Heat-pump stands on the balcony deck (2026-08-28).
# ============================================================================
# EQ-M-HP1-OD and EQ-M-HP2-OD (authored in plan/electrical.py) stand on this deck, 12" clear
# of the plank on a small aluminium frame. The frame has to be BOLTED DOWN — Gree's service
# manual §8.6 requires the foot holes fixed and the support rated to four times unit weight,
# and IRC M1401.4 makes a manufacturer instruction mandatory — so eight fasteners pass
# through a watertight plank that is also the roof of an occupied porch. Everything below is
# about where those eight holes land.
#
# ** THE ANCHORS LAND IN BLOCKING, NEVER IN A JOIST AND NEVER IN A BEAM. ** That is the whole
# rule, and it is the opposite of the instinct. Both units sit within an inch of the rear
# pillar line, so a 3-ply beam directly over a pillar and its footing is right there and is
# the stiffest thing on the deck. It is also the one member here that cannot be replaced, it
# carries `TR-SG-CAP-BL*` and the butyl under it, and its ply seams are exactly the wet joint
# `notes/beam_water_protection.md` exists to close. A fastener that penetrates the waterproof
# plane goes into something we can cut out from below and put back. Blocking is that thing.
#
# ** THE ANCHORS SIT AT BAY CENTRES, AND THE REINFORCEMENT SITS ON THE JOIST LINE. **
# ``_reinforcement_members`` (resolve/floors.py) snaps each reinforcement to the NEAREST
# joist line and lays one block in the bay either side of it, at the load's own x. So the
# reinforcement and the anchor are deliberately NOT the same point: put the reinforcement on
# a joist line and it hands you two blocks, one either side; put an anchor at the centre of
# each of those blocks and both holes are 8" from any joist. Authoring a reinforcement AT
# each anchor instead — which is what this file did until 2026-08-28 — costs twice the
# reinforcements for the same eight holes, and where two of them straddle one bay it emits
# the same block twice, at the same x, and bills the lumber and the butyl for both.
#
# ** THE JOIST GRID IS LAID OUT FROM THE DECK'S SOUTH RIM, so it MOVED when the balcony's
# front plane did (2026-08-29). ** The lines fall at -0'-10" (north rim), -1'-2", -2'-6",
# -3'-10", -5'-2", -6'-6", -7'-10", -9'-2", -10'-6" (south rim) — every interior line 4"
# north of where it was before the 12" move, because 12" is not a whole number of 16"
# bays. One reinforcement per x-line at y = -2'-6" therefore blocks the bays
# -1'-2"..-2'-6" and -2'-6"..-3'-10", and the two anchors go at their centres, -1'-10"
# and -3'-2". Both units moved 4" north with them, to stay centred over their own legs
# (params/../plan/electrical.py) — a bay centre is not adjustable, so the cabinet is what
# gives. Nothing here can be left on a remembered number: ``mep.deck_equipment_support``
# measures every anchor against the RESOLVED joist lines and failed all eight the moment
# the deck grew.
#
# The first cut of this put every anchor 3" off a joist line — inside the bay, but with only
# 2 1/4" of clear to the joist face, which is not room for a sealed base plate and is one
# layout error from the joist itself. Nothing caught it, because
# ``mep.deck_equipment_support`` tested only that the anchor fell inside a BLOCK's bounding
# box — and a block spans the full bay, so an anchor sitting on a joist line is inside it
# too. The check now measures the distance to the joist lines directly. Both mistakes were
# the same mistake: proving a host exists is not proving the anchor found it.
#
# ** AND CLEAR OF THE THREE BEAM BANDS. ** A 3-2x12 is 4 1/2" wide, so BM-SG-BLW/BLC/BLE
# occupy x 7'-9 3/4"..8'-2 1/4", 17'-9 3/4"..18'-2 1/4" and 27'-9 3/4"..28'-2 1/4". Six
# inches from a beam AXIS is the floor, not four: the first cut put three legs 4" off a
# centreline, which is 1 3/4" of clear to the face of a 3-ply, and the check failed them. A
# base plate that has to seal against the plank needs room for the plate and its butyl
# gasket, and a plate lapping onto the beam puts the next fastener back where this whole
# detail is trying not to be.
#
# ** THE LEGS ARE NOT UNDER THE FEET, AND THE FRAME IS WHAT RECONCILES THEM. ** These are the
# numbers this file got wrong for a day, so they are written out. Gree publishes a foot-hole
# pattern per capacity, and it is not adjustable in the depth direction — the cast foot's
# obround slot runs the WIDTH way, so width has about 1/4" of travel and depth has none:
#
#   EQ-M-HP1-OD  VIR24HP230V1R32AO   feet 22 7/16" (width) x 14 39/64" (depth)   92.6 lb
#   EQ-M-HP2-OD  MUL30HP230V1R32AO   feet 25"      (width) x 15 19/32" (depth)  145.5 lb
#
# The legs below are on NEITHER of those patterns, and that is correct rather than sloppy:
# leg positions are decided by the deck (bay centres, beam clearance) and foot positions by
# the cabinet, and the two cannot both be satisfied by one set of points — HP1's west foot
# line lands on BM-SG-BLW. The frame is the part that spans between them, so it is sized to
# reach the feet and land on the legs, and each frame's real size is recorded on
# ``EQUIP_STAND_ALUM`` in plan/assemblies.py:
#
#   HP1 frame 14 5/8" (depth) x 22 7/16" (width) — legs 14" x 16", feet essentially over them
#   HP2 frame 24"     (depth) x 25"      (width) — legs 24" x 16", feet inboard of the legs
#
# A 12" leg spacing, which is what this file carried first, is SHORTER than either foot
# pattern: HP2's feet would have missed a 12"-spaced pair of rails outright.
#
# Both units moved to centre their own mass over their legs (2026-08-28). HP1 went 6" east
# and both went 3" south; the alternative was a frame 4" eccentric under a bolted-down
# cabinet, and moving a condenser on an open balcony costs nothing.
_HP_STAND_LEG_X = {"A": (103.0 / 12.0, 117.0 / 12.0),   # EQ-M-HP1-OD, centred on x = 9'-2"
                   "B": (198.0 / 12.0, 222.0 / 12.0)}   # EQ-M-HP2-OD, centred on x = 17'-6"
# Bay centres, 8" clear of the joist lines either side, symmetric about y = -2'-6" — which
# is both the units' own centreline and the joist line the reinforcements sit on.
_HP_STAND_LEG_Y = (-22.0 / 12.0, -38.0 / 12.0)
#: The joist line each frame's two blocks straddle. One reinforcement per x-line, here.
_HP_BLOCK_LINE_Y = -30.0 / 12.0
_HP_STAND_HEIGHT_IN = 12.0
# Which unit each frame carries, for the reinforcement `source` and the check's cross-ref.
_HP_STAND_UNIT = {"A": "EQ-M-HP1-OD", "B": "EQ-M-HP2-OD"}
_HP_STAND_AT = tuple(
    (key, index, x, y)
    for key in ("A", "B")
    for index, (x, y) in enumerate(
        ((lx, ly) for lx in _HP_STAND_LEG_X[key] for ly in _HP_STAND_LEG_Y), start=1))
#: One reinforcement per (unit, x-line) — four, not eight. See the block comment above.
_HP_BLOCK_AT = tuple((key, x) for key in ("A", "B") for x in _HP_STAND_LEG_X[key])

BALCONY_JOISTS = FloorSystem(
    uid="SGFS02AAAA", tag="FS-SG-DECK",
    joists=JoistSpec(member=SPEC.balcony_joist, spacing=inch(SPEC.balcony_joist_oc_in),
                     direction="x", cantilever=inch(SPEC.joist_cantilever_in),
                     # The two rim bands close the joist tips on the garden's front and rear
                     # faces, at eye level from the walk below and in the same plane as the
                     # white pillars and knee braces — so they are painted with them
                     # (2026-08-27). The joists behind them stay bare KDAT: nothing sees a
                     # joist once the band and the fascia are on.
                     rim_material="post-paint-white",
                     bearing_refs=("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE")),
    outline=_DECK_OUTLINE,
    subfloor=DeckLayer(material_ref="aluminum-deck",
                       thickness=inch(SPEC.balcony_deck_thickness_in)),
    # Butyl here is doing the SECOND job in ``FloorSystem.top_protection``'s docstring more
    # than the first: the plank over these joists is watertight, but it is aluminium laid
    # straight onto copper-treated pine, which AWC DCA6 warns against outright. The tape is
    # the dielectric. That it also keeps the fastener penetrations sealed is the bonus.
    top_protection=_BEAM_TAPE,
    # One block per heat-pump stand leg — the sacrificial member every anchor lands in, and
    # the reason the eight penetrations are survivable. FOUR reinforcements make those eight
    # blocks, not eight: each sits ON the y = -2'-10" joist line and lays a block in the bay
    # either side, and the anchors go at those blocks' centres. See ``_HP_BLOCK_AT`` above
    # for why authoring one per anchor instead double-emits a block.
    # ``plies=1`` is load-bearing: it makes
    # ``_reinforcement_members`` lay ZERO sister joists (``range(plies - 1)`` is empty) and
    # only the two blocks, because what this needs is a fastener host, not a stiffened joist.
    # The blocks inherit ``top_protection`` above — "blocking" is in
    # ``takeoff/member_protection._TAPED_CATEGORIES`` — so each one tapes and bills itself
    # with no further wiring, and the butyl is under the base plate by construction.
    reinforcements=tuple(
        JoistReinforcement(
            at=pt(ft(_hx), ft(_HP_BLOCK_LINE_Y)), plies=1, member=SPEC.balcony_joist,
            source=f"anchor host for the {_HP_STAND_UNIT[_hk]} stand's x={_hx * 12:.0f}in "
                   f"leg pair — one block either side of this joist line, an anchor at the "
                   f"centre of each. Sacrificial: replaceable from the porch below without "
                   f"touching a joist or a beam")
        for _hk, _hx in _HP_BLOCK_AT),
    # ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
    # 40-psf floor table — see checks/structural/deck.py.
    service="deck",
    source="balcony — 2x8 joists on three beams, Wahoo aluminium plank laid over them",
)

# ============================================================================
# Fiberglass (GFRP) rebar dowels + 40 psi XPS foam thermal break between the shared
# house/garden footings. The two house-adjacent footings (the porch side walls, along the
# north edge) pin to the house footing across a 2" XPS block so the joint transfers shear
# without a thermal bridge. Bars at mid-footing (-9.25'), on the north-edge line.
#
# **DW-SG-COL was the third and is retired (2026-08-29), with its bell.** It crossed the
# joint between FT-SG-COL and FT-B-S2 while the two sat at the same elevation 2" apart.
# The bell now bears 2'-6" lower — its top is 1'-10" under FT-B-S2's underside — so the
# bars would have spanned open ground at -9'-4 7/16" with no garden concrete at that
# height to develop into, and the foam block would have had one face and no joint. A
# separated pier does not need a thermal break; it IS one. Nothing renumbered: COL was the
# LAST entry, so W1 keeps SGDW01AAAA and E1 keeps SGDW02AAAA and no IFC GlobalId moves —
# which is the only reason removing an ``enumerate``-minted uid was safe to do in place
# (compare _WALL_FOOTING_UID above, where it was not).
# ============================================================================
_dowel_z = ft(-(SPEC.basement_depth_ft + 0.75) + SPEC.footing_thickness_in / 24.0)
_DOWEL_AT = (("W1", _x_ax_w, _y_in_n), ("E1", _x_ax_e, _y_in_n))
DOWELS = [
    Dowel(uid=f"SGDW0{i}AAAA", tag=f"DW-SG-{name}", position=pt(ft(x), ft(y)),
          axis="y", length=inch(24), diameter=inch(0.625), elevation=_dowel_z,
          count=3, spacing=inch(8),
          connects=(f"FT-SG-{name}", "FT-B-S2"),
          foam_thickness=inch(2), foam_height=inch(SPEC.footing_thickness_in), foam_psi=40.0)
    for i, (name, x, y) in enumerate(_DOWEL_AT, start=1)
]

# ============================================================================
# Connector hardware as modeled geometry (was text/notes only). Standoff post bases under
# the six 6x6 balcony pillars, plus joist hangers / hurricane ties at the porch back-beam
# pockets. The knee braces are their own elements — see KNEE_BRACES below.
# ============================================================================
CONNECTORS = []
for _i, _x in enumerate(_PILLAR_X, start=1):
    for _row, _y, _rise in _PILLAR_ROWS:
        # ABU66SS: the stainless ABU66 standoff base, anchored into the concrete wall top
        # (or, at the two centre pillars, through the porch decking). It rides at that
        # pillar's own bearing top, so the base draws where the post actually starts.
        #
        # The 1" standoff is what IRC R317.1.4 Exception 1/3 asks for — a wood column on
        # concrete stands on a pedestal projecting 1" above the floor. Note Simpson's
        # counter-instruction ("for higher downloads, pack grout solid under the 1" standoff
        # plate"): do NOT grout these solid. It eliminates the drainage gap that is the
        # whole point of a standoff at an exposed base.
        _bearing_tag, _bearing_top = PILLAR_BEARINGS[f"PT-SG-B{_row}{_i}"]
        CONNECTORS.append(Connector(
            uid=f"SGCB{_i}{_row}AAAA", tag=f"CN-SG-BASE-{_row}{_i}",
            kind=ConnectorKind.POST_BASE, position=pt(ft(_x), ft(_y)), elevation=_bearing_top,
            size="ABU66SS", connects=(f"PT-SG-B{_row}{_i}", _bearing_tag)))
# Porch beam pockets, back and front: a hanger into each side wall + a hurricane tie over
# each column.
#
# Every one of these used to author ``elevation=_porch_top``, the storey datum. A Connector
# resolves to a marker box centred on its elevation (accessories.py::_resolve_connector,
# +/-3"), so at the datum a back-beam hanger drew ~11" above the beam it hangs — floating in
# the joist band and poking up through the 1" composite plank, which is what made these read
# as deck-level objects rather than the under-deck hardware they are. Each now sits at its
# own joint: a hanger on the mid-depth of the beam whose end it carries, a tie on the
# bearing plane it holds down (the beam soffit = the column top).
#
# BOTH pairs hang from the bearing stack now (2026-08-29) — neither authors a
# ``top_elevation``, so the resolver drops both a porch-joist depth below the datum and
# there is one soffit and one mid-depth for all four pockets. ``_back_beam_soffit`` /
# ``_back_beam_mid`` are derived up beside ``_back_beam_depth_ft``, because
# ``_WALL_UNDER_PILLAR`` needs the soffit long before this point in the file.
CONNECTORS += [
    # HUCQ410-SDS, not LUS210 (2026-08-22). Both back-beam ends land in a pocket cast in a
    # 12" SUNKEN_GARDEN_WALL — concrete, not a wood ledger — and LUS210 is a wood-to-wood
    # hanger with an exposed face flange and 10d-into-lumber nailing that has nothing to
    # bite here. HUCQ is the concealed-flange hanger Simpson publishes for exactly this
    # joint (library/hardware.py, ROLE_CONCRETE_FACE_MOUNT_HANGER); the front pair below
    # has carried it since the front beams went flush, and the back pair being different
    # was an oversight, not a detail. uid, tag, position and elevation are unchanged, so
    # the IFC GlobalIds survive the retype.
    Connector(uid="SGCH01AAAA", tag="CN-SG-HGR-W", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_col)), elevation=_back_beam_mid,
              size="HUCQ410-SDS", connects=("BM-SG-BKW", "W-SG-W1")),
    Connector(uid="SGCH02AAAA", tag="CN-SG-HGR-E", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_col)), elevation=_back_beam_mid,
              size="HUCQ410-SDS", connects=("BM-SG-BKE", "W-SG-E1")),
    # HGAM10, not H2.5A (2026-08-28) — the OPEN item recorded here since the connectors
    # were first modeled, now closed. An H2.5A is a wood-to-wood tie; library/hardware.py's
    # own record says "rafter/joist-to-plate" and its published values are nails into lumber
    # on BOTH legs. At this joint one leg has the 3-ply KDAT beam and the other has a cast
    # column top it cannot nail to, so as drawn the tie spliced the two beam ends across the
    # pour rather than holding either down to it. The HGAM masonry gusset angle is the part
    # that actually reaches: #14 screws into the wood leg, Titen Turbo into the concrete,
    # 1 1/2" minimum edge distance — which both rounds satisfy as cast (a 12" round gives
    # 6" to its centre, a 16" round 8"). It is catalogued now under ROLE_MASONRY_GUSSET_ANGLE
    # and priced in prices.toml, which is what the old note was waiting for.
    #
    # This is a CORRECTNESS change, not a check improvement: ``takeoff/uplift.py`` keys the
    # beam-to-post link on ``ConnectorKind``, never on ``size``, so every uplift finding is
    # byte-identical afterward. What moves is the BOM — ``authored_connector_rows`` groups by
    # ``(kind, size)``, and before the catalog entry existed ``hardware_by_model("HGAM10")``
    # would have returned None and dropped the row into ``unpriced`` with ``role=None``.
    #
    # NOT the CCQM/CCTQM embedded column-cap family: Simpson publish its loads for solid
    # concrete piers a minimum of 14" SQUARE with (4) #7 verticals. PT-SG-COL is a 12" round
    # (113 in^2) and the price basis carries a 4-bar #4 cage. And do NOT delete these two
    # Connectors instead — ``_is_concrete(seat)`` is true here and "12 round"/"16 round" are
    # not stocked post sizes, so with no ``_POST_TOP_KINDS`` connector at the joint all four
    # beam-end links go ``hardware=None`` and the check reports four FAILs.
    # Same part at CN-SG-TIE-FCOL below. See notes/uplift_load_path.md.
    Connector(uid="SGCT01AAAA", tag="CN-SG-TIE-COL", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_cx), ft(_y_col)), elevation=_back_beam_soffit, size="HGAM10",
              connects=("BM-SG-BKW", "BM-SG-BKE", "PT-SG-COL")),
    # CN-SG-TIE-BR2 (uid J6XRAXQG5T) was retired 2026-08-28 with the joist reinforcement
    # above. It held the *front* bearing of PT-SG-BR2's joist line down against the prying
    # a loaded cantilever tip put there; with the pillar row moved onto the back-beam line
    # there is no cantilever tip to load. The uid is spent — do not reuse it.
    # Front-beam pockets, the same concrete-face-mount detail as the back pair above.
    Connector(uid="SGCH03AAAA", tag="CN-SG-HGR-FW", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_ax_front)), elevation=_back_beam_mid,
              size="HUCQ410-SDS", connects=("BM-SG-FRW", "W-SG-W1")),
    Connector(uid="SGCH04AAAA", tag="CN-SG-HGR-FE", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_ax_front)), elevation=_back_beam_mid,
              size="HUCQ410-SDS", connects=("BM-SG-FRE", "W-SG-E1")),
    Connector(uid="SGCT02AAAA", tag="CN-SG-TIE-FCOL", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_cx), ft(_y_ax_front)), elevation=_back_beam_soffit,
              size="HGAM10",
              connects=("BM-SG-FRW", "BM-SG-FRE", "PT-SG-FCOL")),
]

# ============================================================================
# Knee braces at the balcony pillar tops: 2x6 wood diagonals with a 3' leg, through-bolted,
# **Simpson KBS1Z at each end of each brace** (16 pieces over the eight braces).
#
# ** THE CONNECTOR CHANGED ON 2026-08-30, AND IT IS A LOAD-PATH FIX, NOT A PREFERENCE. **
# These joints carried `APVKB45-6`, Simpson's Outdoor Accents Avant decorative knee brace,
# from the day the balcony was framed. It has no published allowable load. That was traced
# through the reports rather than assumed: IAPMO UES ER-102 (the stamped-connector index,
# rev. 08/21/2026) enumerates the whole AP/APV series it covers — post bases, ledgers, tees,
# angles, joist ties, hangers — and APVKB is not among them; ER-280, the report ER-102 points
# that series at, has no APVKB section, table or figure. Simpson's own Outdoor Accents load
# tables print uplift and download for the Avant POST BASES and no load row for the brace.
#
# These eight braces are the **entire** lateral system of a freestanding deck at storey
# height on pinned standoff bases. An unrated connector there is a hole in the load path,
# not a documentation gap. `KBS1Z` is Simpson's purpose-built structural knee-brace
# stabilizer, is already in this house's catalog and price file for the breezeway beams, and
# is the only knee-brace connector anywhere in the catalog with a code-report allowable —
# published BY BRACE ANGLE, which is exactly the capacity a 45-degree brace needs
# (ER-280 Table 7, connection type 2: 540 lbf F1 at 45 degrees in SPF/HF).
#
# `structural.lateral_racking` computes the demand these have to carry and reports the
# margin; the full worked chain, and what the swap costs, is in
# `notes/balcony_lateral_bracing_design.md`.
#
# ** THE FOUR E-W BRACE FEET ARE LAPS, NOT BUTT JOINTS (2026-08-30, second pass). ** The
# connector swap left the geometry alone, and the geometry was wrong: a brace coplanar with
# a face-bolted rail has no pillar in front of its end, and the four E-W feet were resolving
# onto the pillars' corners with zero contact area. They now lap the pillar face and bolt
# through it. The block above `_EW_PLANE_OFFSET` below carries the reasoning; what changes
# here is that only their HEADS are connector joints, and their bolts are 8" rather than the
# Outdoor Accents 6" (7" of wood to cross). The four N-S braces are untouched.
#
# The four corner pillars are braced in both plan directions; the two centre pillars
# (PT-SG-BR2/BF2) are deliberately left as leaning columns. This is a freestanding deck
# on ABU66SS standoff bases (base + beam bearing both pins), so the braces are the only
# lateral resistance and need both directions — hence the E-W brace rails, for the "x"
# braces to reach. Bracing the outer bays each direction is enough with the deck as
# diaphragm; leaving the centre pillars unbraced is defensible for a different reason than
# it used to be — not because thrust would land on PT-SG-BR2 (that pillar bears on concrete
# now, not porch decking), but because the rails run continuous through all six posts and
# already tie the centre pillars into the two braced end bays. One brace per pillar per
# direction: the second brace at a corner is the E-W one against the rail (at its own
# soffit, a rail depth below the beams', and in the rail's own plane rather than the
# pillar's) — the old "matched pair per joint" rule billed 12 unbuildable braces.
# ============================================================================
# (row, pillar index, N-S lean, E-W lean). Rear posts brace south toward the beam's midspan
# and front posts brace north; the west pillar of each row braces east, the east one west.
_BRACED_CORNERS = (("R", 1, -1, +1), ("R", 3, -1, -1),
                   ("F", 1, +1, +1), ("F", 3, +1, -1))
_BRACE_LEG = ft(3.0)
# See the 2026-08-30 note at the head of this block. `KneeBrace.connector` is the model
# string `structural.lateral_racking` looks the allowable up by, so it has to be the part
# that is actually installed, not the family the brace was first drawn with.
_BRACE_CONNECTOR = "KBS1Z"
# The N-S brace uid is the one the retired Connector carried at this same pillar, so the
# brace keeps its IFC GlobalId across this change.
_NS_BRACE_UID = {("R", 1): "SGCK1RAAAA", ("R", 3): "SGCK3RAAAA",
                 ("F", 1): "SGCK1FAAAA", ("F", 3): "SGCK3FAAAA"}
_EW_BRACE_UID = {("R", 1): "SGKX1RAAAA", ("R", 3): "SGKX3RAAAA",
                 ("F", 1): "SGKX1FAAAA", ("F", 3): "SGKX3FAAAA"}
_ROW_Y = {"R": _y_rear_pillar, "F": _y_front_pillar}
_NS_BEAM = {1: "BM-SG-BLW", 3: "BM-SG-BLE"}
# The rail is continuous, so both pillars in a row rise into the same member — keyed by
# row only, not by pillar index the way the girts were.
_EW_RAIL = {"R": "BM-SG-RAIL-R", "F": "BM-SG-RAIL-F"}
# ---------------------------------------------------------------------------
# THE E-W BRACE PLANE, and why it laps rather than bears (2026-08-30, second pass).
#
# The rail is face-bolted to the row's inboard face, so its plane is `_RAIL_FACE_OFFSET_FT`
# = 3 1/2" off the pillar axis. A brace can be COPLANAR with that rail or it can BEAR on the
# pillar's east/west face, and it cannot be both: reaching from one plane to the other means
# a brace skewed 3 1/2" over its 3'-0" run — 5.6 degrees crooked in plan, compound cuts at
# both ends, and a KBS1Z is a flat factory-formed 45-degree strap with one permitted field
# bend that cannot wrap a skewed joint.
#
# Coplanar wins, for a structural reason and not just a buildable one: the brace's thrust
# then lands IN the rail's plane, bending it about its 7 1/4" strong axis with no
# eccentricity, where a brace offset from that plane would twist a member that
# notes/balcony_lateral_bracing_design.md §6 already reports at l_e/d 80 about its weak one.
#
# The cost of coplanar is the foot: 3 1/2" off the axis there is no pillar in front of the
# brace end to bear on. Until this fix the geometry said the brace started at the pillar's
# east/west FACE anyway, which put its end on the pillar's corner with a plan overlap of
# exactly one line — zero contact area, nothing to bear on and nothing to bolt through. The
# brace floated. `foot_lap` is the fix: the foot runs the pillar's full 5 1/2" back across
# its inboard face and through-bolts there, which is the same connection the rail itself
# makes at all six posts. The head is unchanged and gains from being read honestly — a 2x6
# butting a 2x8 soffit is EQUAL WIDTH, ER-280 connection type 1 (two KBS1Z, one each side,
# 1,010 lbf SPF), not the type 2 the N-S braces take.
_EW_PLANE_OFFSET = {"R": ft(-_RAIL_FACE_OFFSET_FT), "F": ft(_RAIL_FACE_OFFSET_FT)}
# Lap the whole pillar face. Anything less is bolt-spacing arithmetic — NDS 12.5.1 wants
# 7D = 3 1/2" of end distance behind a 1/2" bolt in tension — and the full width is what
# leaves room for it without inventing a schedule this model has no standing to set.
_EW_FOOT_LAP = inch(5.5)
KNEE_BRACES = []
for _row, _i, _ns, _ew in _BRACED_CORNERS:
    _post = f"PT-SG-B{_row}{_i}"
    _at = pt(ft(_PILLAR_X[_i - 1]), ft(_ROW_Y[_row]))
    KNEE_BRACES.append(KneeBrace(
        uid=_NS_BRACE_UID[(_row, _i)], tag=f"KB-SG-{_row}{_i}-NS", position=_at,
        soffit_elevation=_balcony_beam_soffit, leg=_BRACE_LEG, axis="y", direction=_ns,
        member="2x6", post_size=SPEC.pillar_size, assembly="POST_WHITE_PAINT",
        connector=_BRACE_CONNECTOR, connects=(_post, _NS_BEAM[_i])))
    KNEE_BRACES.append(KneeBrace(
        uid=_EW_BRACE_UID[(_row, _i)], tag=f"KB-SG-{_row}{_i}-EW", position=_at,
        soffit_elevation=_rail_soffit, leg=_BRACE_LEG, axis="x", direction=_ew,
        plane_offset=_EW_PLANE_OFFSET[_row], foot_lap=_EW_FOOT_LAP,
        member="2x6", post_size=SPEC.pillar_size, assembly="POST_WHITE_PAINT",
        connector=_BRACE_CONNECTOR, connects=(_post, _EW_RAIL[_row])))

# ============================================================================
# Balcony guard + edge trim. The metal fascia-mounted guardrail is a first-class Railing
# (not a parapet). PVC fascia closes the joist ends; a front gutter catches the south-
# draining deck via a front-edge drip flashing; the rear (house) edge gets a counter-
# flashing tucked up into the house WRB. Deck drains SOUTH (rear pillars 2" taller).
# ============================================================================
_deck_top = ft(SPEC.balcony_level_ft)  # 10' — storey datum = top of joist
# Guard height is measured from the surface a person stands on, which is the top of the
# aluminum boards, not the joists they sit on. Basing the guard on _deck_top instead would
# make the authored 42" measure 40.5" in the field and fail the guard-height rule.
_deck_walking_surface = _deck_top + inch(SPEC.balcony_deck_thickness_in)
# Guard the three open edges (west, front/south, east); the north edge abuts the house.
_GUARD_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_balcony_front)),
               pt(ft(_deck_x_e), ft(_y_balcony_front)), pt(ft(_deck_x_e), ft(_y_in_n)))
BALCONY_GUARD = Railing(
    uid="SGRA01AAAA", tag="RL-SG-BALCONY", type_ref="RAILING-EXT-ALUMINUM-FASCIA",
    path=_GUARD_PATH,
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
    base_elevation=_deck_walking_surface,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="fascia",
    assembly="RAILING_DARK_METAL",
    # R312.1.3: vertical balusters between the 60" posts at a 4" clear gap — the largest
    # opening the 4"-sphere rule admits.
    infill="balusters", baluster_spacing=inch(4))

BALCONY_FASCIA = Fascia(
    uid="SGFC01AAAA", tag="TR-SG-FASCIA", kind=TrimKind.FASCIA, path=_GUARD_PATH,
    top_elevation=_deck_top, depth=inch(9), thickness=inch(1), material="PVC",
    host_ref="FS-SG-DECK")
# Front (south, low) edge only — the drip flashing follows the deck edge itself.
_FRONT_PATH = (pt(ft(_deck_x_w), ft(_y_balcony_front)),
               pt(ft(_deck_x_e), ft(_y_balcony_front)))
# Where the leader hangs is what sets the trough's east end, so it is decided here. The
# leader has to hang *outside* the structure. Its old position (`_deck_x_e - 0.5`, which is
# the east beam axis) put a 3" pipe dead centre in two solids at once: the 6x6 pillar
# PT-SG-BF3 stands on that axis, and W-SG-E1's 12" band (x 27.5-28.5) runs the whole drop
# below it. There is no room inboard either — the front rail and the front beam both sit on
# the trough line, and SL-SG-FLOOR stops at the wall's inner face. So the trough oversails
# the deck edge and the pipe drops just clear of the wall's *outer* face, into the 6" slot
# between that face and the raised garden's east return (raised_garden.py stands that leg
# 3' out, at x = 29.0). 1.5" of clearance each side, about what a leader strap wants anyway.
_SG_LEADER_OUTSET = 0.25   # ft outboard of the deck edge, which IS the east wall's face
_SG_GUTTER_OVERSAIL = 0.5  # ft of trough past that edge, to carry the outlet
_SG_LEADER_X = _deck_x_e + _SG_LEADER_OUTSET
_GUTTER_PATH = (pt(ft(_deck_x_w), ft(_y_balcony_front)),
                pt(ft(_deck_x_e + _SG_GUTTER_OVERSAIL), ft(_y_balcony_front)))
# Gutter rim meets the drip flashing's lower edge, so water shedding off the drip lands in
# the trough. Hung 9" down (an earlier value) it cleared the drip by 6" and overshot it.
_drip_depth_in = 3.0
BALCONY_GUTTER = Gutter(
    uid="SGGT01AAAA", tag="TR-SG-GUTTER", kind=TrimKind.GUTTER, path=_GUTTER_PATH,
    top_elevation=_deck_top - inch(_drip_depth_in), depth=inch(4), thickness=inch(5),
    material="aluminum", host_ref="TR-SG-FASCIA", slope="1/16 in/ft to SE downspout",
    downspout_ref="TR-SG-LEADER-SE",
    # The last 6" oversails TR-SG-FASCIA (and the drip above it): that bay exists only to
    # put the outlet outboard of the pillar and the wall, and it hangs off the end hanger.
    # The run goes west→east, so its left-hand normal (resolve/geometry.py::normal) points
    # north (+y) — the porch/house side. The channel's back sheet rides the fascia there.
    back_side="left")
# The leader TR-SG-GUTTER slopes to — previously named in prose only, so the trough had no
# authored downspout and just stopped at the east end.
#
# 3" round, not the roof's 4": catches only the balcony deck (~200 sf) vs. 648 sf per house
# eave. It no longer drops into the sunken garden — hanging outboard of the east wall there
# is no garden underneath it — so it discharges 6" above the raised terrace, whose surface
# is level with that wall top at +0'-6" (raised_garden.TOP). DRW-SG-MAIN stops naming it as
# an inlet for the same reason, and that is the better half of the trade: the soakaway
# serves a 9'-deep pit with no outlet of its own, and 200 sf of balcony runoff is the one
# contribution it does not have to swallow.
_SG_LEADER_BOTTOM = _ret_top + inch(6)
BALCONY_LEADER = Downspout(
    uid="SGDS01AAAA", tag="TR-SG-LEADER-SE",
    position=pt(ft(_SG_LEADER_X), ft(_y_balcony_front)),
    top_elevation=_deck_top - inch(_drip_depth_in) - inch(4),  # the trough floor
    bottom_elevation=_SG_LEADER_BOTTOM,
    diameter=inch(3), material="aluminum", gutter_ref="TR-SG-GUTTER",
)

BALCONY_DRIP = Flashing(
    uid="SGFF01AAAA", tag="TR-SG-DRIP", kind=TrimKind.DRIP_FLASHING, path=_FRONT_PATH,
    top_elevation=_deck_top, depth=inch(_drip_depth_in), thickness=inch(3),
    material="aluminum", host_ref="TR-SG-GUTTER")
# Rear (north, house-side) counter-flashing tucked up into the house WRB.
_REAR_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_e), ft(_y_in_n)))
BALCONY_REAR_FLASH = Flashing(
    uid="SGFF02AAAA", tag="TR-SG-WRB-FLASH", kind=TrimKind.WRB_COUNTERFLASHING,
    path=_REAR_PATH, top_elevation=_deck_top + inch(6), depth=inch(8), thickness=inch(2),
    material="aluminum", host_ref="FS-SG-DECK")

# ============================================================================
# Beam cap flashing — formed metal over the top of all seven built-up beams.
# ============================================================================
# The tape (``_BEAM_TAPE``, on every beam's ``top_protection``) is the primary defence and
# the cap is the second one. Both, not either: they fail differently. The tape is a bonded
# membrane that seals the fastener holes and cannot be dislodged; the cap is a shed surface
# that keeps UV and standing debris off the tape, which is what ages a butyl membrane.
#
# ** THE CAP IS BEDDED ON THE TAPE, AND THAT ORDER IS STRUCTURAL TO THE DETAIL. ** Aluminium
# laid directly on copper-treated pine corrodes — AWC DCA6 says not to do it — so an
# aluminium cap on bare KDAT would be a new defect rather than a fix. The tape under it is
# the dielectric. Anything that removes the tape from these beams must change this metal too.
#
# ** FIVE OF THE SEVEN GO ON BEFORE THE JOISTS DO, AND THAT IS NOT A PREFERENCE. ** The
# balcony's three beams and the porch's back pair carry their joists ON TOP; only the porch's
# front pair is flush-framed with an unobstructed top (see FRONT_BEAMS). A cap over a beam
# that will be joisted has to be laid while the beam top is still open, and the joists then
# bear on it — which is fine for a 0.019" coil cap under a 2x8's bearing area, and impossible
# to retrofit without pulling the deck. That sequencing is the whole labour half of the
# `beam_cap` price row in prices.toml; it is not a return-visit trade.
#
# The run is authored the way ``BALCONY_DRIP`` is: ``top_elevation`` is the surface the metal
# laps — here the beam's own top — and ``depth`` runs DOWNWARD from it. So the resolved band
# occupies the beam's top 1 1/2", which is where the turn-down legs are, and reads in section
# as "this beam's top is clad". Authored the other way up (top + leg) it drew a 1 1/2" slab
# of aluminium in the joist bearing plane, which is both wrong and the kind of wrong that
# looks right in plan. The cap's top sheet is ~1/16" and is elided, exactly as the fascia's is.
#
# Section: the cap laps 1/2" past each beam face and turns down 1 1/2", so ``thickness`` is
# the beam's own width plus the two laps and is read off ``SPEC`` rather than written down —
# a beam that gains a ply widens its cap instead of leaving its outer plies uncapped.
_CAP_LAP_IN = 0.5          # cap overhang past each beam face, before the turn-down
_CAP_LEG_IN = 1.5          # turn-down leg depth
_porch_beam_width_ft = cross_section(SPEC.back_beam).width_m / 0.3048
_balcony_beam_width_ft = cross_section(SPEC.balcony_beam).width_m / 0.3048
_porch_cap_thickness = ft(_porch_beam_width_ft) + inch(2 * _CAP_LAP_IN)
_balcony_cap_thickness = ft(_balcony_beam_width_ft) + inch(2 * _CAP_LAP_IN)

# Each beam's resolved TOP — the plane the cap sits on. Three different derivations, because
# the three beam families hang three different ways, and a cap authored on the storey datum
# would float above the beam exactly the way the porch hangers did before 2026-08-25.
_back_beam_top = _porch_top - ft(_porch_joist_depth_ft)   # joists bear on top
_front_beam_top = _back_beam_top                          # joists bear on top (2026-08-29)
# Same numeric value as before (9.3958333'), just no longer derived from a member (the
# girt) that no longer exists.
_balcony_beam_top = _balcony_beam_soffit + ft(_balcony_beam_depth_ft)

# (uid, tag, node pair, top, section width). The paths are the beams' own node coordinates,
# so a cap cannot drift off the beam it caps.
_BEAM_CAP_AT = (
    ("SGCP01AAAA", "TR-SG-CAP-BKW", (_cx, _y_col), (_x_ax_w, _y_col),
     _back_beam_top, _porch_cap_thickness, "BM-SG-BKW"),
    ("SGCP02AAAA", "TR-SG-CAP-BKE", (_cx, _y_col), (_x_ax_e, _y_col),
     _back_beam_top, _porch_cap_thickness, "BM-SG-BKE"),
    ("SGCP03AAAA", "TR-SG-CAP-FRW", (_cx, _y_ax_front), (_x_ax_w, _y_ax_front),
     _front_beam_top, _porch_cap_thickness, "BM-SG-FRW"),
    ("SGCP04AAAA", "TR-SG-CAP-FRE", (_cx, _y_ax_front), (_x_ax_e, _y_ax_front),
     _front_beam_top, _porch_cap_thickness, "BM-SG-FRE"),
    # The balcony's three run N-S on the deck's own 2"-in-8'-8" southward fall (the rear
    # pillars are ``rear_pillar_rise_in`` taller), so each cap sheds to its south end — which
    # is the front edge, where TR-SG-GUTTER already hangs. The caps discharge into the
    # trough rather than onto the pillar tops and the front rail below them.
    ("SGCP05AAAA", "TR-SG-CAP-BLW", (_x_ax_w, _y_in_n), (_x_ax_w, _y_balcony_front),
     _balcony_beam_top, _balcony_cap_thickness, "BM-SG-BLW"),
    ("SGCP06AAAA", "TR-SG-CAP-BLC", (_cx, _y_in_n), (_cx, _y_balcony_front),
     _balcony_beam_top, _balcony_cap_thickness, "BM-SG-BLC"),
    ("SGCP07AAAA", "TR-SG-CAP-BLE", (_x_ax_e, _y_in_n), (_x_ax_e, _y_balcony_front),
     _balcony_beam_top, _balcony_cap_thickness, "BM-SG-BLE"),
)
BEAM_CAPS = [
    Flashing(uid=uid, tag=tag, kind=TrimKind.BEAM_CAP,
             path=(pt(ft(p0[0]), ft(p0[1])), pt(ft(p1[0]), ft(p1[1]))),
             top_elevation=top, depth=inch(_CAP_LEG_IN),
             thickness=thickness, material="aluminum", host_ref=host)
    for uid, tag, p0, p1, top, thickness, host in _BEAM_CAP_AT
]
PORCH_BEAM_CAPS = [c for c in BEAM_CAPS if c.host_ref in
                   ("BM-SG-BKW", "BM-SG-BKE", "BM-SG-FRW", "BM-SG-FRE")]
BALCONY_BEAM_CAPS = [c for c in BEAM_CAPS if c not in PORCH_BEAM_CAPS]

# ============================================================================
# The heat-pump stands themselves — legs and through-deck anchors.
# ============================================================================
# Geometry, and the reasoning for every coordinate, is at ``_HP_STAND_AT`` above; the
# blocking each anchor lands in is on ``FS-SG-DECK.reinforcements``. This block is only the
# metal.
#
# Twelve inches, an owner decision (2026-08-28) against the 18"-24" a cold-climate guide
# would ask for. The trade is recorded rather than argued: the guidance is written for a
# unit at grade, and this balcony is swept by wind that keeps its snow depth low in a way a
# ground-level stand cannot rely on. What 12" already buys, and what the taller number was
# mostly for anyway, is airflow: a 12" stand under a 32"/34" cabinet puts the coil at
# 44"/46", clear of the 42" guard, so neither unit sits in the stagnation pocket behind it.
#
# The legs are aluminium and that is not a finish choice — see ``EQUIP_STAND_ALUM`` in
# plan/assemblies.py. They stand on an aluminium plank and are lagged through it into
# copper-treated blocking, which is the one place in this structure where three metals and a
# treated wood meet. Aluminium on aluminium is no couple; the butyl under each base plate is
# what keeps the stand off the KDAT; the lag is 316 stainless for the same reason.
_hp_stand_height = inch(_HP_STAND_HEIGHT_IN)
HP_STAND_LEGS = [
    Post(uid=f"SGHP{_hk}{_hi}AAAA", tag=f"PT-SG-HP{_hk}{_hi}",
         position=pt(ft(_hx), ft(_hy)), size="2.0x2.0", height=_hp_stand_height,
         supported_by="FS-SG-DECK", assembly="EQUIP_STAND_ALUM")
    for _hk, _hi, _hx, _hy in _HP_STAND_AT
]
# One anchor per leg, at the walking surface — the plank's top, which is the plane the base
# plate is bedded on and the plane the lag crosses. NOT ``_deck_top``: that is the joist
# tops, 1 1/2" of plank below where this connection actually happens.
#
# ``connects`` names the BLOCKING's host deck rather than a joist or a beam, which is the
# whole point of the detail and is what ``mep.deck_equipment_support`` reads.
#
# ``EQUIPMENT_ANCHOR``, not ``POST_BASE`` — these were filed as post bases until 2026-08-28
# and the BOM printed "8 modeled post base connector(s)" against a lag screw's part number,
# three lines under ten real ABU66SS. Nobody could order from that and no framer could build
# it: a post base is a formed stirrup you set the post into, and what is actually here is a
# 3/8" lag through a bonded washer, chosen for its seal and its alloy rather than for the
# section above it. The part is ``SS316-LAG-38x4-EPDM`` in library/hardware.py.
HP_STAND_ANCHORS = [
    Connector(uid=f"SGHC{_hk}{_hi}AAAA", tag=f"CN-SG-HP{_hk}{_hi}",
              kind=ConnectorKind.EQUIPMENT_ANCHOR, position=pt(ft(_hx), ft(_hy)),
              elevation=_deck_walking_surface, size="SS316-LAG-38x4-EPDM",
              connects=(f"PT-SG-HP{_hk}{_hi}", "FS-SG-DECK"))
    for _hk, _hi, _hx, _hy in _HP_STAND_AT
]

# ============================================================================
# Per-storey exports (spliced into plan/manifest.py).
# ============================================================================
BASEMENT_ELEMENTS = [*NODES, *WALLS, COLUMN, FRONT_COLUMN, *FOOTINGS,
                     *FOOTING_BEDDING, GARDEN_DRYWELL, GARDEN_SLAB, *FROST_WINGS, *DOWELS]
# Every remaining connector is porch hardware at the deck (post bases, hangers, the column
# tie), so main takes them whole; the knee braces are the only second-storey hardware.
MAIN_ELEMENTS = [*MAIN_NODES, *BACK_BEAMS, *FRONT_BEAMS, PORCH_JOISTS, PORCH_GUARD,
                 *CONNECTORS, *PORCH_BEAM_CAPS]
SECOND_ELEMENTS = [*SECOND_NODES, *RAIL_NODES, *BALCONY_BEAMS, *BALCONY_RAILS, *PILLARS,
                   BALCONY_JOISTS, *KNEE_BRACES, BALCONY_GUARD, BALCONY_FASCIA,
                   BALCONY_GUTTER, BALCONY_LEADER, BALCONY_DRIP, BALCONY_REAR_FLASH,
                   *BALCONY_BEAM_CAPS, *HP_STAND_LEGS, *HP_STAND_ANCHORS]

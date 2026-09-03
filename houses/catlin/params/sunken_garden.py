"""Sunken garden / porch / balcony structure — parametric module (WP3.1, redesign).

One freestanding concrete + wood structure immediately south of the house (5" gap from
the house cladding face). It is fully independent of the house — the two share only a
compacted footing bed, with the footings doweled together through a fiberglass-rebar +
40 psi XPS foam thermal break (see FOOTING_BEDDING / the dowel note below).

Vertical stack (project-north frame; +X east, +Y north, +Z up):
- Sunken garden floor at the basement storey (-9'): a U-shaped cantilever-T retaining
  wall (open to the north) on a 42" compacted-aggregate base down to frost. The wall
  footings reach frost depth by soil replacement (that drained non-frost-susceptible
  section, ASCE 32 / IRC R403.1.4.1); the two porch columns reach it by excavation
  instead — bell-bottom piers augered 42" below the garden floor.
- The north 8' of that U is the *porch*: two 12" side walls and, on both the north (house)
  and south (front) edges, NO concrete wall. Each of those edges is carried the same way —
  one column at midspan plus two 3-ply KDAT beams hung into the side walls: a 12" sonotube
  at the back, a second 12" round cast column at the front (it was 20" until 2026-09-03). The back line sits a SPEC south-offset
  inside the north edge (so the tube and its bell footing clear the house) and the deck
  cantilevers over it. **Both beam lines are DROPPED — the joists bear on top of all four**,
  which puts PT-SG-FCOL at the same soffit as PT-SG-COL. PT 2x8 joists span N-S between the
  two lines; composite decking is the walking surface. Porch floor = main (0').
- A metal guard (RL-SG-PORCH) rails the porch's three open edges, matching RL-SG-BALCONY
  one storey up — which is 12" further south, outboard of it. Both are Williams
  Architectural Products, ICC-ES ESR-3485, 42" black (Fortress Al13 Home is the alternate),
  and the two MOUNT DIFFERENTLY: the porch's is SURFACE-mounted, because its side legs run
  along 12" concrete wall tops that take the baseplate anchors directly; the balcony's stays
  FASCIA-mounted, because its aluminium plank is the porch roof and carries no penetrations
  at all. Only the two centre balcony pillars take a post base now, both on the porch
  decking; the four corners are cast columns doweled into the wall tops.
- The *balcony* one storey up (second, ~9-10') rides six pillars (10' o.c. E-W, 8' o.c.
  N-S; rear row 2" taller for drainage slope) carrying three N-S treated-glulam beams,
  2x8 joists @ 16" o.c., and aluminum (Wahoo AridDeck-style) decking. **The four CORNER
  pillars are 12" round reinforced concrete columns FIXED at the base** and doweled into the
  wall tops under them; they are the balcony's entire lateral system, and the eight knee
  braces and two E-W brace rails they replaced are deleted (2026-09-03,
  notes/balcony_moment_columns.md). The two CENTRE pillars stay wood 6x6, both bearing on
  the porch decking 3" inside their own beam line with squash blocks and a plank cut-out.
  Its FRONT plane is 12" south of the porch's, so the balcony oversails the porch floor by a
  foot and its drip and gutter hang clear of it.

Everything here is generated — these elements carry no editable-source location. Both decks
are FloorSystems outright, joists plus the plank as the deck sheet: FS-SG-PORCH (composite),
FS-SG-DECK (aluminium).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus import (
    BarSpec,
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
    Node,
    Post,
    Railing,
    RailingKind,
    ReinforcementSpec,
    Slab,
    Stair,
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
    # The cast column near the porch's front edge: a SHARED bearing, seating both front
    # beams (on `_y_ax_front`) and PT-SG-BF2 (12" further south, on `_y_balcony_front`) on
    # one pour. See FRONT_COLUMN for the sizing table — 16" and 18" have no solution at a
    # 12" pillar overhang, 20" leaves +0.49".
    front_column_size_in: float = 20.0
    # How far south of the porch's inside face the front BEAM axis sits — independent of
    # the column, so the beam plane does not drift when the column's diameter changes.
    #
    # Holding it at 8" is the point: `_y_ax_front` lands on -9.5', which gives the four
    # porch beams a 10.00' span against `deck_beam_span`'s 10.25' limit. Any move south
    # past 8.00' of back span drops the R507.5(1) lookup to the 10' row (9.17') and fails
    # all four at once.
    porch_front_edge_offset_in: float = 8.0
    # How far south of the porch's front BEAM plane the balcony's front pillar row stands.
    # Landing the row on the beam plane itself would make PT-SG-BF2 a 6x6 bearing through
    # one 2x8 porch joist onto BM-SG-FRW/FRE — ~315 psi of cross-grain bearing at the base
    # and ~385 psi where the joist crosses the beam, against an Fc-perp of 425 psi (SPF).
    # Moving the row out puts BF2 straight onto the concrete column instead (~105 psi), and
    # the balcony gains a 12" drip overhang past the porch floor.
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
    # 109.4375" is ``params/main_deck.BASEMENT_DATUM``; this module may import, but it is one
    # house-wide number transcribed rather than a second derivation, and
    # ``integrity.basement_bearing_seat`` checks the two agree. ``SL-SG-FLOOR`` and
    # ``SL-B-FLOOR`` top out on exactly the same plane, which IS the walkout at D-B-PATIO.
    #
    # The retained height on W-SG-E2/S/W2 is 7.09', well past the 48" that sends R404.1.1 to
    # an engineered design, so those three walls stay engineered and
    # ``structural.foundation_unbalanced_fill`` keeps reporting them UNKNOWN.
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
    # = 17". Cannot shrink. The 2" is plain clearance between the bell's north face and the
    # house footing's excavation face. The column does NOT move: the whole back-beam line,
    # the deck edge and the pockets are anchored to this offset.
    column_south_offset_in: float = 17.0
    porch_joist: str = "2x8"
    porch_joist_oc_in: float = 16.0
    # Three-ply KDAT 2x12, 11 1/4" deep — the same depth as every member this position has
    # carried, so no derived elevation moves.
    #
    # Not "treated LVL": that product does not exist. Treated Parallam Plus PSL is made in
    # 9 1/4", 11 7/8", 14" and 16" depths only, at 3 1/2" and 5 1/4" widths, and Weyerhaeuser
    # forbids resawing it in depth — so 11 1/4" cannot be bought treated in an engineered
    # member at all. A 2x12 is exactly 11 1/4" sawn, and KDAT is a stocked treatment.
    #
    # Three plies of 2x12 clear IRC Table R507.5(1) on this span, so `structural.
    # deck_beam_span` grades the member PASS instead of reporting UNKNOWN against a member
    # outside the table's scope.
    back_beam: str = "3-2x12"
    porch_deck_thickness_in: float = 1.0  # composite plank
    # The two side walls run this far PAST the porch's front edge before handing off to the
    # retaining run. Without it the W1/W2 (and E1/E2) junction node would land exactly on
    # `_y_ax_front`, which is also the balcony's front pillar line — so PT-SG-BF1/BF3 would
    # straddle the joint, half over each wall, forcing the bearing map to pick one (the
    # retaining wall's +6" curb rather than the porch wall carrying the rest of the frame).
    # It clears the 12" round's south face (y -10'-4") by 8" and leaves the front-beam
    # pockets (CN-SG-HGR-FW/FE, on `_y_ax_front`) well in from the end of the wall instead
    # of right at it. That was 3 3/8" to a 5 1/2" square post base before the corners became
    # cast rounds and the row came north; the 18" is unchanged and now has slack.
    #
    # 18", not 6": the balcony's front pillar row sits 4" south of the porch's front edge
    # (`_y_front_pillar`), and it is a 12" round, so the extension must reach past it or
    # PT-SG-BF1/BF3 would run off the south end of W-SG-W1/E1 onto W-SG-W2/E2 — the +6" curb,
    # `lateral_support="unsupported"` R404.4 engineered walls. The extension follows the
    # pillars. W-SG-W2/E2 shorten by 12" and their footings follow.
    side_wall_south_extension_in: float = 18.0
    # The porch's two joist ends are not alike, so it cannot share the balcony's symmetric
    # cantilever: the south end hangs flush *in* the front beams (nothing to oversail) and
    # the north end runs the column's south-offset out to the deck edge. This is the *south*
    # value; the north one is that offset (see PORCH_JOISTS).
    porch_joist_cantilever_in: float = 0.0
    # balcony framing
    pillar_size: str = "6x6"
    rear_pillar_rise_in: float = 2.0  # rear row taller for drainage slope
    # **Treated SYP structural glulam, 3-1/2" x 11-7/8"** (Anthony Power Preserved / Boise
    # 24F-V5M1/SP, ~$35/LF, stocked through Boise Cascade Lakeville). These were three
    # site-built 3-ply KDAT 2x12s until 2026-09-03; a glulam is one manufactured member with
    # published engineered values instead of three sticks and a nail schedule, it has no
    # ply seams to hold water, and it is what makes the braceless frame below buildable at
    # a sane depth.
    #
    # **The decimal spelling is the parser's tell.** "3.5x11.875" resolves through
    # LUMBER_ACTUAL; a nominal-looking "4x12" would match ``_RE_NOMINAL`` in
    # resolve/framing/profiles.py and silently become 3-1/2" x 11-1/4". Same trap the round
    # column sizes sidestep.
    #
    # 11-7/8" over the slimmer 9-1/2" option is the owner's planter margin: ~31% bending
    # against ~48% at the centre beam's 500 plf over 8'-8", deflection ~L/1200 either way.
    # notes/balcony_moment_columns.md records both, and the arithmetic behind them.
    #
    # These beams no longer PASS a prescriptive table and are not asked to: IRC Table
    # R507.5(1) publishes sawn and built-up rows only, so `structural.deck_beam_span` hands
    # them to `engineering/glulam_beam.py` as ENGINEERED items (decision #65).
    #
    # `_balcony_beam_depth_ft` is derived from this string, so the beam soffit and the
    # pillar/column tops follow it — the tops drop 5/8" against the old 3-2x12. Clear height
    # from the porch deck to the balcony beam soffit is 8'-4 7/8", and the walking surface
    # at `balcony_level_ft` is unaffected.
    #
    # Worth keeping straight while reading this file: the balcony beams sit under a
    # DRY-BELOW surface — `FS-SG-DECK`'s plank is `aluminum-deck`, a Wahoo AridDeck-style
    # watertight system with a drip trough and leader (see the deck's own comment) — while
    # the porch beams sit under GAPPED composite. That asymmetry is the real ESR-1387 5.3
    # exposure story, and it is why the two pairs were never the same problem.
    balcony_beam: str = "3.5x11.875"
    # The four CORNER pillars are 12" round reinforced concrete columns, FIXED at the base,
    # and they are the balcony's entire lateral system — the eight knee braces and two E-W
    # brace rails they replaced are deleted (2026-09-03). The two CENTRE pillars stay wood
    # 6x6 on pinned ABU66SS bases, leaning columns tied in by the deck diaphragm.
    #
    # 12" is what 2" of cover needs (a 6-5/8" bar circle on a #5 cage inside #3 ties), which
    # is the hundred-year number rather than ACI's 1-1/2" minimum. It is also the same tube
    # as PT-SG-COL and PT-SG-FCOL, so ONE assembly serves all five cast columns. Centred on
    # the 12" wall axis the round is flush with both wall faces: no ledge, no interference.
    #
    # The round spelling is mandatory — see `balcony_beam` above for the same trap.
    corner_column_size: str = "12 round"
    # Hot-dip galvanized bar (ASTM A767 class 1 chromate-passivated, or A1094 continuous),
    # the owner's 2026-09-02 call over epoxy (delaminates) and stainless (4-6x, and an
    # austenitic thermal coefficient that fights the concrete). Parsed by
    # `engineering/deck_post.py::parse_cage`; the words around the four numbers are for the
    # drawing. As 1.24 in2 on a 113.1 in2 gross is rho 1.10%, just over §10.6.1.1's 1% floor.
    # The word order matters: ``parse_cage`` reads the tie group as "#<n> ties @ <spacing>"
    # and an adjective wedged between the bar and the word "ties" makes the whole string
    # unreadable — which it treats as NO STEEL, the conservative reading, so the column
    # silently reports INCOMPLETE instead of failing loudly. Galvanizing rides at the end.
    corner_column_cage: str = ('(4) #5 vertical, #3 ties @ 10" o.c., 2" cover, '
                               'hot-dip galvanized (ASTM A767 cl. 1 or A1094)')
    balcony_joist: str = "2x8"
    balcony_joist_oc_in: float = 16.0
    balcony_deck_thickness_in: float = 1.5  # aluminum plank
    # ** 9", AND IT IS THE ALUMINIUM PLANK'S NUMBER, NOT THE JOIST'S. ** The deck's WIDTH is
    # 2 x cantilever + 20'-0" between the outer beam axes, and Wahoo's AridDek is a 6" main
    # board: its own installation guide's rule is that a width "not evenly divisible by 6"
    # costs a RIPPED finish board, which on a watertight tongue-and-groove plank means
    # cutting the tongue and the integral gutter channel off the last row. So the deck width
    # is only ever allowed to move in whole 6" steps, and the cantilever in 3" ones.
    #
    #     6"  ->  21'-0" = 252" = 42 boards      9"  ->  21'-6" = 258" = 43 boards
    #
    # 9" was taken on 2026-09-03 for the same reason PT-SG-BF1/BF3 came north: at 6" the deck
    # edge, and TR-SG-FASCIA's drip with it, landed exactly on the outer face of the 12"
    # rounds (x 7'-6" / 28'-6"), so the balcony shed its water down the column faces. 3" of
    # plank past each face is a drip line clear of the concrete, and it costs one more full
    # board and no rip.
    #
    # ** IT ALSO MOVES W-RG-WEST/EAST-BALCONY. ** The 6" slot between the balcony's railing
    # face and those two SRW returns is what TR-SG-LEADER-SE's 3" pipe threads; growing the
    # deck into it without shortening the returns leaves the leader nowhere to hang. Both
    # return nodes went 3'-0" -> 2'-9" the same day (params/raised_garden.py) so the whole
    # SE detail translates 3" east unchanged.
    #
    # 2.5' is R507.6.1's limit here (a quarter of the 10'-0" back span between beams), so
    # the joist is nowhere near governing. The plank module is.
    joist_cantilever_in: float = 9.0  # deck joist tips overhang the outer beams
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
# of the porch deck itself, at -9.5'.
#
# It is NOT the balcony's front plane and not the front column's axis: the column is a 20"
# round set 7 1/8" south of here and the balcony's pillar row a foot south of that, so the
# porch plane holds its own SPEC offset (see `porch_front_edge_offset_in` for why this
# number in particular must not drift).
_y_ax_front = _y_in_n - SPEC.porch_clear_depth_ft - SPEC.porch_front_edge_offset_in / 12.0
# The BALCONY's front plane, 12" south of the porch's: the balcony's front pillar row, its
# deck outline, RL-SG-BALCONY, TR-SG-FASCIA, TR-SG-DRIP and TR-SG-GUTTER. The overhang is
# what the balcony gains by having PT-SG-BF2 off the porch framing and onto concrete — a
# 12" drip past the porch floor, which is also why the gutter is out here and not over the
# porch deck.
_y_balcony_front = _y_ax_front - SPEC.balcony_front_overhang_ft
# Where the porch side walls stop and the free retaining walls take over. NOT the porch's
# front edge: the side walls carry on past it so the balcony's front pillars land on them
# (see ``side_wall_south_extension_in``, 18"). The front beams and the porch's own deck
# outline and guard still read `_y_ax_front`; the front column, the balcony's pillar row,
# its guard and its deck outline read `_y_front_col` / `_y_balcony_front` instead.
_y_ax_mid = _y_ax_front - SPEC.side_wall_south_extension_in / 12.0  # -11.0'
_y_in_s = _y_in_n - SPEC.clear_length_ft
_y_ax_s = _y_in_s - _half

_wall_bottom = ft(-(SPEC.basement_depth_ft + 0.75))
# The two porch side walls stop 1" higher than the free retaining run, and the 1" comes out
# of the wall, not out of the ground. At the untrimmed bottom they resolved 10'-1" tall, and
# IRC Table R404.1.2(8) stops at 10'-0"; trimming to exactly 10'-0" puts them ON the table's
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
# at-rest against phi-Mn 22,131 at #6 @ 10" (d/c 0.81, on the 5,000 psi mix
# `SUNKEN_GARDEN_WALL` states). #6 @ 12" is the arithmetic minimum at d/c 0.96 and is too
# thin a margin for a screening on presumptive soil values; the `#6 @ 38"` the braced porch
# walls carry is nowhere near. 2" cover per ACI 318-19 Table 20.5.1.3.1 (earth and weather,
# #6 and larger), which is also IRC Table R404.1.2(8) footnote i's outside-face figure for
# bars larger than #5.
#
# ** AUTHORED TWICE, AND THAT IS THE MIGRATION CONTRACT. ** The string is what prints on the
# drawing; the struct is what `stem_flexure` grades and what `takeoff/reinforcement.py`
# bills. Where both exist the STRUCT governs and the parser is not called at all, and
# `integrity.reinforcement_spec_agrees` raises an ERROR if the two ever drift apart. The
# horizontal steel was never stated in the string and is stated here: ACI 318-19 §11.6.1
# asks 0.0020 of the gross section for #5 and smaller, i.e. 0.288 in2/ft on a 12" wall,
# and `#4 @ 8"` is 0.300.
# The five cast columns' cage, structured — the same four bars and #3 ties @ 10" the string
# states. Both spellings are kept: the string prints on the drawing and holds the prose the
# struct cannot (the galvanizing callout), the struct is what `deck_post.cage_for` grades and
# what `takeoff/reinforcement.py` bills, and `integrity.reinforcement_spec_agrees` raises an
# ERROR if they drift apart. A COUNT and not a spacing, because ACI 318-19 §10.6.1.1 bounds a
# column's steel by 0.01Ag and §10.7.3.1(b) sets its floor at four bars within circular ties,
# and neither question can be asked of a spacing.
_CAST_COLUMN_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
    ),
    cover=inch(2.0),
    lap_class="B",
    source="verbatim from the cage string beside it; notes/sunken_garden_piers.md §4",
)

# ** THE SAME CAGE, GALVANIZED — AND THE COATING IS ON THE BARS RATHER THAN ON THE MIX. **
# A coating normally belongs to the pour (`ConcreteSpec.bar_coating`), because it is a
# property of the bar you buy for a pour and not of a role within it. It is stated per-bar
# here for a reason worth writing down: `SUNKEN_GARDEN_COLUMN_12` does not yet carry a
# `ConcreteSpec` at all — attaching one means giving it the real 5,000 psi F3+C2 mix, which
# re-oracles `notes/balcony_moment_columns.md`, `notes/breezeway_piers.md` and
# `test_pier_calcs.py`. Until that happens the galvanizing is an authored fact with nowhere
# else to live, and leaving it unsaid would under-report the house's galvanized tonnage in
# the estimate. Move it to the mix when the mix lands.
_CAST_COLUMN_CAGE_HDG = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4, coating="hdg-a767"),
        BarSpec(role="ties", bar=3, spacing=inch(10.0), coating="hdg-a767"),
    ),
    cover=inch(2.0),
    lap_class="B",
    source="verbatim from SPEC.corner_column_cage, including its ASTM A767 cl. 1 callout",
)

# The two BRACED porch walls' vertical steel, structured. `#6 @ 38"` is IRC Table
# R404.1.2(8) for a 12" wall braced top and bottom — a different row and a much lighter
# schedule than the three retaining runs' `#6 @ 10"`, because these two have a floor
# diaphragm at the head and no cantilever to carry.
_BRACED_STEM_STEEL = ReinforcementSpec(
    bars=(BarSpec(role="vertical", bar=6, spacing=inch(38.0)),),
    cover=inch(3.0),
    source="IRC Table R404.1.2(8), braced top and bottom; 3\" cover with the rest of the court (see _RET_STEM_STEEL)",
)

_RET_REBAR = '#6 @ 10" o.c.'
_RET_STEM_STEEL = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=6, spacing=inch(10.0),
                note="RETAINED face — that is where the cantilever puts the tension"),
        BarSpec(role="horizontal", bar=4, spacing=inch(8.0),
                note="ACI 318-19 §11.6.1 temperature and shrinkage, both faces"),
    ),
    # ** 3", AND IT IS BOUGHT WITH SECTION RATHER THAN FOUND LYING AROUND. **
    # ACI 318-19 Table 20.5.1.3.1 asks 2" of a #6 on a formed face exposed to weather, and
    # `structural.concrete_cover_meets_minimum` grades against that. This is 3" — a
    # durability decision, not a code one, and the reason is class C2: these six walls take
    # deicing salt off the drive above and hold it against their faces in a court that
    # cannot drain to daylight. Cover is the only term in the whole chloride problem that
    # buys DISTANCE; every other lever (w/cm 0.40, the galvanizing, the fly ash) buys time.
    #
    # It costs 1" straight off `d`, which is ~11% of the stem's flexural capacity: the
    # #6 @ 10" section goes from d/c 0.81 to 0.90 (notes/sunken_garden_court_free_body.md
    # §6). That is a real spend of margin and it is why this number is authored on the
    # SCHEDULE and not on the mix — the mix pours the footings too, and a 3" default there
    # is free where here it is not.
    cover=inch(3.0),
    lap_class="B",
    source="sized in notes/sunken_garden_court_free_body.md §6",
)
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
# The same butyl in the roll width a wide beam actually needs. A 3-2x12 is 4 1/2" across and
# the balcony's glulams are 3 1/2", so the 1 5/8" joist roll and even the common 3 1/8"
# "double joist" roll leave the outer arrises — and, on the ply beams, both seams —
# uncovered. Two tags rather than one because these are two SKUs at a 2-3x difference in
# price per foot, and the BOM's own width column is what says which member takes which:
# 1.25" and 1.5" members take ``_BEAM_TAPE``, the 3.5" and 4.5" ones this.
#
# The three balcony beams keep this tag through the 2026-09-03 glulam swap even though a
# glulam has no ply seam to close. The seam was never the only reason — an exposed framing
# top in weather wants a bonded membrane whatever the member is made of — and the width
# still rules out the narrow roll.
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
    # W-SG-W1/E1 are SUPPORTED TOP AND BOTTOM. Whether a porch deck counts as *permanent
    # lateral support* at the head of a wall holding 9'-9" of fill is a judgment about the
    # real structure: this head is not a deck edge resting alongside a wall — it is a beam
    # pocket cast INTO it. Both back beams and both front beams die into these two walls in
    # HUCQ410-SDS concealed-flange hangers (CN-SG-HGR-W/E, -FW/-FE), the porch joists span
    # between those beams, and FS-SG-PORCH's plank sheet ties the whole diaphragm together.
    # The bottom is the garden slab bearing at their foot. That is a continuous load path in
    # both directions at both ends, which is what R404.1.2(8) presumes and what the free
    # retaining walls south of here (W2/E2/S) do not have.
    #
    # These walls resolve EXACTLY 10'-0" tall over 7'-2" of unbalanced fill, which is the
    # last row IRC Table R404.1.2(8) publishes; R404.1.3's no-seal prescriptive path reaches
    # it, and `structural.foundation_unbalanced_fill` PASSES both walls.
    #
    # The inch that keeps them at 10'-0" (rather than 10'-1") came out of the WALL and not
    # out of the ground: `_porch_wall_bottom` raised the bearing and FT-SG-W1/E1 went
    # 12" -> 13" thick to hold their undersides at the same -11'-1", so the 21" of frost
    # cover the R403.3 wing insulation is sized against did not move. Verified before and
    # after.
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
                   vertical_reinforcement='#6 @ 38" o.c.',
                   reinforcement=_BRACED_STEM_STEEL),
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
                   vertical_reinforcement='#6 @ 38" o.c.',
                   reinforcement=_BRACED_STEM_STEEL),
    # ============================================================================
    # W-SG-ARCH IS A BURIED GRADE BEAM — NOT AN ARCH.
    # ============================================================================
    # A strut on the MW-ME node pair, 12" x 17 1/2", entirely below the garden floor,
    # invisible, doing one job: closing the loop that makes W-SG-W2 and W-SG-E2 face each
    # other instead of standing as two free cantilevers. It reuses a retired uid, which is
    # exactly what the `_WALL_FOOTING_UID` literal-map pattern below was built for.
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
    # question ASCE 32 soil replacement closes. FB-SG-ARCH below carries the same 42"
    # undercut, the same NFS claim and the same tile to DRW-SG-MAIN.
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
    # ** THE FILL AGAINST THESE THREE IS AUTHORED. ** Left derived,
    # `structural.foundation_unbalanced_fill` measures from the single global `Site.grade`
    # (-2'-10") down to the footing and reports **7.0'** — wrong here, because `params/
    # raised_garden.py` builds an SRW apron whose `TOP = ft(RETAINING_WALL_TOP_FT)` — level
    # with these walls' own tops at +0'-6" — standing 3'-0" out from their outer faces and
    # holding a terrace of soil at that level *against them*. Grade is a plane, and a plane
    # cannot describe a terrace sitting 3'-4" above it. The real retained height is the
    # wall's full top-to-footing dimension, **10.37'**.
    #
    # It is deliberately written as the same arithmetic `_wall_bottom` and `_ret_top` are
    # built from rather than as a literal, so it moves with either. There is no separate
    # "terrace top" number and there must not be: `SPEC.retaining_top_ft` IS the terrace top,
    # because `raised_garden.py` reads that very constant to place its own apron. A second
    # copy would be exactly the divergence the "publish, do not re-derive" note further down
    # this file exists to prevent.
    #
    # Both 7.0' and 10.37' are far past the 48" at which R404.1.1 sends a wall to an
    # engineered design, so the correction cannot flip the verdict — all three stay UNKNOWN,
    # engineered — but it changes what the engineer is asked to design for by nearly half
    # again, which is the whole point. `notes/sunken_garden_retaining_screening.md` works
    # the consequences.
    #
    # ** `lateral_support="base"`, NOT "unsupported". ** These three are free retaining
    # walls, open to the sky along their whole top, holding 10'-4" of fill with nothing
    # bracing the head — IRC R404.4's case exactly. `"base"` routes to the same R404.4
    # engineered handoff (`checks/structural/foundation.py::_grade_one`); Table R404.1.2(8),
    # a *basement* wall table whose footnote g presumes bracing top AND bottom, must not be
    # read against them.
    #
    # Graded as three ISOLATED cantilevers, each resisting by its own base friction, they
    # reach FS 0.73 against 1.5 — the arithmetic of a wall nobody built. W-SG-W2
    # (axis x=8'-0") and W-SG-E2 (axis x=28'-0") face each other across a 19'-0" court, same
    # height, same 18'-4" length, cast into W-SG-S at their south ends through monolithic
    # corners — **their thrusts cancel through the concrete between them.** Only the 20'-0"
    # south wall is unopposed. The U was open at its NORTH end and that was the real defect;
    # W-SG-ARCH above closes it, and `engineering/retaining_system.py` sums the whole court
    # as ONE free body.
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
    # `vertical_reinforcement` is the other half of the fix. The stem is otherwise plain
    # concrete: 465 psi of flexural tension at at-rest, on a section ACI 318 R22.6.3 does not
    # even COVER as plain concrete ("the Code does not cover walls without horizontal
    # support ... such walls are to be designed as reinforced concrete members"). A base
    # restraint acts inches from the stem's base and relieves NONE of it, so fixing sliding
    # alone would turn the report green over a louder uncomputed failure. The schedule is
    # sized in the note, not invented here.
    #
    # `engineering_spec` is deliberately unset: an authored spec says "an engineer designed
    # this wall", and none has. The engine computes a court that checks out — a draft
    # verdict, not a stamp.
    FoundationWall(uid="SGW105AAAA", tag="W-SG-W2", start_node="N-SG-MW",
                   end_node="N-SG-SW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   unbalanced_fill=_ret_unbalanced_fill,
                   vertical_reinforcement=_RET_REBAR,
                   reinforcement=_RET_STEM_STEEL,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
    FoundationWall(uid="SGW106AAAA", tag="W-SG-E2", start_node="N-SG-SE",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   unbalanced_fill=_ret_unbalanced_fill,
                   vertical_reinforcement=_RET_REBAR,
                   reinforcement=_RET_STEM_STEEL,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
    FoundationWall(uid="SGW107AAAA", tag="W-SG-S", start_node="N-SG-SW",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL",
                   unbalanced_fill=_ret_unbalanced_fill,
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   vertical_reinforcement=_RET_REBAR,
                   reinforcement=_RET_STEM_STEEL,
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
# It is NOT the balcony's front edge: the two planes are 12" apart, so they are two
# constants. A consumer that wants the outermost thing this structure presents — the
# balcony fascia, its guard, its drip — wants the BALCONY one.
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
# ``_WALL_UNDER_PILLAR``, where PT-SG-BF2 bears on the front column's top. Both porch beam
# pairs frame the same way (joists ON TOP), so there is ONE soffit and one mid-depth.
_porch_joist_depth_ft = cross_section(SPEC.porch_joist).depth_m / 0.3048
_back_beam_soffit = _porch_top - ft(_porch_joist_depth_ft + _back_beam_depth_ft)  # -18.5"
_back_beam_mid = _porch_top - ft(_porch_joist_depth_ft + _back_beam_depth_ft / 2.0)
_col_footing_width_in = 30.0  # bell diameter under the 12" sonotube
# Bell diameter under PT-SG-FCOL. It stayed 36" when the column above it shrank from a
# 20" round to a 12" one on 2026-09-03: the bell answers to the SOIL, not to the shaft,
# and the shrink took the bearing from 1,477 to 1,159 psf against a 2,000 psf
# presumptive. Narrowing it to PT-SG-COL's 30" would put it back at ~1,671 psf, which
# is worse than the pier this house is now tightest on (notes/sunken_garden_piers.md §3c).
_front_footing_width_in = 36.0

# --- the two porch piers are BELL-BOTTOM PIERS, augered to frost depth -------------------
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
# How much further down the bell top sits than the garden floor it is flush with in plan.
# Every shaft above a bell grows by exactly this, so no column top moves — the beam soffit
# (-1'-6 1/2", both pairs) is a load-bearing elevation for the porch frame and is asserted
# in test_catlin_outdoor_structures.py.
_pier_shaft_extension_ft = -SPEC.basement_depth_ft - _pier_bell_top_ft
COLUMN = Post(uid="SGP001AAAA", tag="PT-SG-COL",
              position=pt(ft(_cx), ft(_y_col)), size="12 round",
              height=ft(SPEC.basement_depth_ft - _back_beam_depth_ft
                        + _pier_shaft_extension_ft),
              assembly="PIER_CONCRETE_12",
              # ** THE CAGE IS THE MINIMUM ACI PERMITS, AND IT IS NOT OPTIONAL. **
              # A_g = 113.10 in2, so §10.6.1.1's 1% floor is 1.131 in2; (4) #5 = 1.24 in2
              # (rho 1.096%) clears it by 9.6% and is the Code's own four-bar minimum for a
              # circular tie (§10.7.3.1(b) — SIX is the spiral case, not this one). The only
              # other cage that clears is 6-#4 at 1.20 in2: a nickel less steel and two more
              # bars to cut, bend and tie. Ties are #3 (§25.7.2.1, verticals #10 or smaller)
              # at the §25.7.2.2 maximum, the least of 16db = 10.0", 48dt = 18.0", h = 12.0".
              # The column is at d/c 0.04 and NONE of that is why these bars are here — the
              # 1% floor is a creep/shrinkage/accidental-moment rule, indifferent to load.
              # See notes/sunken_garden_piers.md §4. Do not thin it to "save concrete".
              vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
              reinforcement=_CAST_COLUMN_CAGE,
              supported_by="FT-SG-COL")

# The front column: a 12" round cast-concrete column on its own belled footing. Its top is
# the *soffit* of the two front beams, exactly as PT-SG-COL's is the soffit of the back
# pair — and that is not a style choice. A 16"-o.c. joist grid cannot miss a column this
# size, so a column topping out at the deck datum reads as three clashes in
# ``structural.member_interference``, and neither a CHASE opening nor an outline notch can
# clear them: the resolver never passes opening boxes to ``_reinforcement_members``.
# Stopping at the soffit puts the whole pour below every floor member's underside.
#
# ** IT SEATS TWO BEAM ENDS, AND THAT IS ALL IT SEATS NOW. ** It was a 20" round centred
# 4-7/8" SOUTH of the beam axis, sized to span from the beams' north face to PT-SG-BF2's
# south face because the balcony's centre front pillar stood on its top. **BF2 has moved
# north onto the porch deck** (see the pillar block below, `_BF2_NORTH_OF_FRONT_AXIS_IN`),
# the exact mirror of PT-SG-BR2 over PT-SG-COL, so this column carries the two front beams
# and nothing else. With the shared bearing gone the whole 20" sizing essay retires with
# it: `_front_column_south_offset_in` is 0 and the column sits ON the beam axis, which is
# where a column carrying two collinear beam ends belongs.
#
# **12", not 10".** 12" matches PT-SG-COL and the four new balcony corner columns, so ONE
# assembly (SUNKEN_GARDEN_COLUMN_12) and one price row serve all five. It also leaves
# 3-3/4" of concrete beside each beam end for the HGAM10's Titen Turbo screws against
# Simpson's 1-1/2" minimum, where a 10" round would leave 2-3/4". Bearing was never what
# governed and still is not: ~30 psi under the two beam ends on 5,000 psi concrete.
#
# ``size="12 round"``. Never a nominal form like "12x12": that matches ``_RE_NOMINAL`` in
# resolve/framing/profiles.py, misses LUMBER_ACTUAL and silently resolves to 1.5x5.5. The
# round spelling sidesteps the trap entirely and is the same one the other four columns use.
#
# Detailing lives in SUNKEN_GARDEN_COLUMN_12's ``source``, with the four corner columns it
# now shares a product with: the F3/C2 mix (5,000 psi, w/cm <= 0.40, 6% air) rather than the
# 20" column's F2 one, a galvanized cage at 2" cover, the >=15 degree wash with its drip
# lip, and a beam seat CAST TO LINE with a stainless standoff and NO grout island.
#
# **Round, not square.** Connector SIDE COVER is the test, and nothing at this top is
# bolted through the column: two beam ends land on the pour and an authored HGAM10 masonry
# gusset (CN-SG-TIE-FCOL) holds them down. See notes/uplift_load_path.md.
_front_beam_depth_ft = _back_beam_depth_ft  # same member (SPEC.back_beam), same soffit drop
# ZERO, since 2026-09-03: the column seats two collinear beam ends and nothing else, so its
# axis is the beams' axis. It was 4 7/8" while PT-SG-BF2 stood on this top and the pour had
# to span from the beams' north face to that pillar's south face; BF2 now bears on the porch
# framing north of the beams instead. Kept as a named constant rather than folded away
# because `_y_front_col` is read in several places and a bare `_y_ax_front` there would lose
# the fact that an offset is a choice this column is allowed to make.
_front_column_south_offset_in = 0.0
_y_front_col = _y_ax_front - _front_column_south_offset_in / 12.0  # -9.5'
# Belled to frost depth on the same terms as PT-SG-COL, and the shaft grows by the same
# ``_pier_shaft_extension_ft``. The authored height is IDENTICAL to PT-SG-COL's, and that is
# now load-bearing rather than incidental: with the front beams unpinned (see FRONT_BEAMS)
# ``_bearing_stack_drops`` propagates the 7 1/4" joist drop through ``Beam.bearing_refs`` to
# this post, so its resolved top falls from -0'-11 1/4" to -1'-6 1/2" — the same
# ``_back_beam_soffit`` PT-SG-COL lands on, by exactly the same path. Do not "correct" the
# height to compensate; the resolver has already done it.
FRONT_COLUMN = Post(uid="SGP002AAAA", tag="PT-SG-FCOL",
                    position=pt(ft(_cx), ft(_y_front_col)),
                    size=SPEC.corner_column_size,
                    height=ft(SPEC.basement_depth_ft - _front_beam_depth_ft
                              + _pier_shaft_extension_ft),
                    supported_by="FT-SG-FCOL",
                    # A_g = 113.10 in2, so the 1% floor is 1.131 in2; (4) #5 = 1.24 in2
                    # (rho 1.097%). Ties #3 at 10", inside §25.7.2.2's least of 16db =
                    # 10.0", 48dt = 18.0", h = 12.0". This is the MINIMUM legal cage on a
                    # 12" round and there is nothing to trim: (4) #4 = 0.80 in2 is 29%
                    # SHORT of the floor, and four bars is already §10.7.3.1(b)'s minimum
                    # within circular ties, so the count cannot come down either. Check any
                    # substitution against 1.131 in2 AND against four bars.
                    vertical_reinforcement=SPEC.corner_column_cage,
                    reinforcement=_CAST_COLUMN_CAGE_HDG,
                    assembly="SUNKEN_GARDEN_COLUMN_12")

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
# THE THREE RETAINING FOOTINGS GROW INBOARD ONLY: 7'-0" -> 8'-0", OFFSET 6".
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

# ** THE 4'-0" TOE IS A CANTILEVER, AND IT WAS UNREINFORCED UNTIL 2026-09-03. **
#
# `_RET_REBAR` above is the STEM's steel, and until `engineering/retaining_basis.py` grew
# `footing_states` nothing in this repo ever asked what the FOOTING carried. It carries a
# lot: 1,275 psf of bearing pressure on a 4'-0" cantilever is 14,176 ft-lb/ft factored, and
# a 12" PLAIN strip is good for 3,536 — **d/c 4.01**, with the heel 2.63 over. That was a
# real gap in the design, not a reporting artifact, and
# `notes/sunken_garden_court_free_body.md` §7 is its oracle.
#
# `#6 @ 10"` both faces is the answer, and it is deliberately the SAME bar and spacing the
# stem already uses: one bar size on this pour is one bundle to order, one bender's setup
# and one thing for an inspector to count. Bottom (toe) 0.72, top (heel) 0.47, shear 0.51.
#
# 3" cover is ACI 318-19 Table 20.5.1.3.1(a) — cast against and permanently in contact with
# ground — and it is the cover this whole footing is designed on, not a durability upgrade
# bolted onto a `d` sized against something looser.
_RETAINING_FOOTING_MAT = ReinforcementSpec(
    bars=(
        BarSpec(role="bottom-x", bar=6, spacing=inch(10.0),
                note="transverse, resists the 4'-0\" toe cantilever; hook the toe end"),
        BarSpec(role="top-x", bar=6, spacing=inch(10.0),
                note="transverse, resists the 3'-0\" heel carrying 10.37' of soil"),
        BarSpec(role="bottom-y", bar=4, spacing=inch(18.0),
                note="longitudinal distribution steel; carries no graded limit state"),
    ),
    cover=inch(3.0),
    lap_class="B",
    source="sized in notes/sunken_garden_court_free_body.md §7, at-rest 110 pcf",
)

FOOTINGS = [
    Footing(uid=_WALL_FOOTING_UID[w.tag], tag=f"FT-{w.tag[2:]}", under=w.tag,
            width=inch(_RETAINING_FOOTING_WIDTH_IN if w.tag in _RETAINING
                       else SPEC.footing_width_in),
            offset=inch(_RETAINING_FOOTING_OFFSET_IN) if w.tag in _RETAINING else None,
            reinforcement=_RETAINING_FOOTING_MAT if w.tag in _RETAINING else None,
            assembly="CATLIN_RETAINING_FOOTING_96" if w.tag in _RETAINING else None,
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
# they are augered to frost depth and bear on undisturbed soil there, so what goes under
# them is a levelling course, not a replacement section (see ``_PIER_BELL`` at the
# undercut).
#
# The footings adjacent to the house (the two porch side walls, along the north edge) are
# additionally doweled to the house footing with fiberglass rebar across a 40 psi XPS foam
# block that breaks the thermal bridge; ``cast_foam_in_aggregate`` records that foam in the
# resolved geometry / IFC (the dowels themselves are annotation-only — see plans/TODO.md).
#
# **FT-SG-COL IS NOT IN THIS SET, and there is nothing to replace it with.** A dowel-and-
# foam joint needs two concretes meeting at one plane, and the garden bell bears 2'-6" lower
# than FT-B-S2's underside — 1'-10" below it — so the two pours no longer face each other:
# there is no joint to dowel and no bridge to break, because the separation itself is the
# break. Leaving the flag on would cast a foam block into aggregate with nothing on the far
# side of it. The two side walls are unchanged and keep theirs; their footings never moved.
# See DOWELS below, where DW-SG-COL is retired for the same reason.
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
        # and pass on depth, in the check's plain ``covered`` bucket. It stays because it is
        # still a true statement about the stone under them, and because the levelling
        # course is drained to the same well — an authored fact should not blink out
        # because a second, better one arrived.
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
# down. The balcony leader hangs outside the east wall and discharges to the terrace, so
# the well is left carrying only the water it cannot avoid.
# Top of stone sits at the WALL beds' underside so the two stack rather than intersect —
# and it is derived from the wall beds on purpose, ``SPEC.aggregate_bedding_depth_in``
# being their number: the two column bells take a 7" levelling course and their beds stop
# 2'-9" short of this plane, which is clearance, not a gap to close.
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
    uid="SGS501AAAA", tag="SL-SG-FLOOR", assembly="CATLIN_GARDEN_SLAB",
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
# WHY THIS EXISTS: measuring every footing against one global grade plane would pass FT-B-
# S1/S2/S3 with only 8" of cover below the garden floor, and FT-B-BRICK with 2" of NEGATIVE
# cover. Frost depth is measured from the lowest adjacent grade, and beside these footings
# that is the garden floor at -9'-4", not the -2'-10" site plane six and a half feet above
# it.
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
# Heat-pump equipment pad, in the yard pocket east of the porch.
# ============================================================================
# EQ-M-HP1-OD and EQ-M-HP2-OD (authored in plan/electrical.py) stood on FS-SG-DECK at +10'
# until 2026-09-02. They stand on the ground now, and the whole detail this file used to
# carry — eight lags through a watertight plank, sixteen sacrificial blocks, four
# reinforcements, two traced condensate runs — went with them. See
# notes/heat_pump_ground_pad.md; notes/heat_pump_deck_mounting.md is SUPERSEDED and kept
# for the reasoning, because the balcony rule (decision #64) still governs any future deck.
#
# ** THE POCKET IS THE SITE, AND IT WAS ALREADY EMPTY. ** West is the porch's east wall
# W-SG-E1 (faces x 27'-6"/28'-6", top 0'-0"); north is the house's south wall; south is the
# W-RG-EAST-BALCONY apron return at y = -10'-6"; east is open side yard. The house is
# gable-ended here, so nothing sheds onto it, and the only neighbour is TR-SG-LEADER-SE at
# (28'-9", -10'-6"), well south of the pad.
#
# ** THE POCKET DOES NOT STOP AT THE HOUSE'S EAST FACE. ** The 2026-09-02 siting read the
# yard as 90" of usable y bounded east by x 36'-0", and concluded a row facing SOUTH did not
# fit. It does: east of the SE corner is open side yard and the EAST (SIDE) setback line is
# x 58'-0" (`plan/site.py`), 19'-5" away, so letting a cabinet stand past the corner costs
# nothing. Both units face SOUTH in one east-west row (2026-09-03).
#
# ** THE ROW IS AGAINST THE HOUSE AND THE FLIGHT IS SOUTH OF IT (2026-09-04). ** It was the
# other way round for one day, and PT-SG-BR3 is why it could not stay: the flight springs
# from W-SG-E1's top, and that top is a 12" wall carrying two 12" ROUND columns, so it is
# walkable only between them — y -9'-9"..-3'-0". A row in the pocket's south half sits
# inside exactly that window. Nothing reported it, because the threshold board is trim
# rather than an element and the column's east face is EXACTLY tangent to the stair's head
# at x 28'-6": no solid overlapped, and the check that would have cared cannot see a
# walking surface that was never modelled. The rule this hands forward is in
# plans/TODO.md — a stair whose head lands on a wall TOP has to be read against what stands
# on that top, and no check does that yet.
#
# ** TWO PADS NOW, NOT ONE. ** The single pour was right while the flight and the cabinets
# shared a band; they are 2'-8" apart in y now, and a rectangle spanning both would be 94 sf
# of concrete to serve 40. HP_PAD carries the row, STAIR_PAD (down with PORCH_STAIR) carries
# the flight and its landing, and between them they are 39.8 sf / 0.49 cy against the one
# pad's 56.9 / 0.70. Two forms for less concrete and less hardscape is the trade, and at
# this size the forms are the cheaper half.
#
# ** HP_PAD: x 29'-0"..36'-10", y -3'-4"..-0'-10" — 19.6 sf, 0.24 cy at 4". ** The north
# edge stops 3" short of the cladding rather than butting it: there is no isolation joint to
# detail if the pad never touches the house, and a 3" gap sheds the wall's runoff into
# gravel instead of against a lip. The west edge is HP2's own cabinet face, 6" clear of
# W-SG-E1 — the row is tucked as far west as 40 5/32" + 12" + 39" allows (owner, 2026-09-04:
# a condenser behind the SE corner is quieter down the whole east side yard than one out
# past it, and the living room takes the difference). It does not tuck all the way; the row
# is 7'-7 1/6" and the porch wall to the corner is 7'-6", so HP1 oversails by 7 1/6" with
# 19'-5" to the setback. The east edge runs 2 3/4" past HP1's cabinet.
#
# ** THE DISCONNECTS PAID FOR THE TUCK. ** At x 31'-0" the row left a 30" band of the house's
# south face for them at NEC 110.26(A) working space; tucked, it does not, and they hang on
# W-SG-E1's east face at 2'-2" above grade instead of the house's at 6'-4". plan/electrical.py
# argues that trade where it is made.
_HP_PAD_X0, _HP_PAD_X1 = 29.0, 36.833333
_HP_PAD_Y0, _HP_PAD_Y1 = -3.333333, -0.833333
#: Two inches proud of the -2'-10" site grade — Gree's "install 2 in above the expected snow
#: line", and the first two of the ~20" the 18" stands on top of it then add. STAIR_PAD is
#: poured to the same top, so the flight's authored base and the cabinets' base are one
#: number and cannot drift apart.
_HP_PAD_TOP = ft(-2, -8)

HP_PAD = Slab(
    uid="SGHPADAAAA", tag="SL-SG-HPPAD", assembly="HP_PAD_ON_GRADE",
    outline=(pt(ft(_HP_PAD_X0), ft(_HP_PAD_Y0)), pt(ft(_HP_PAD_X1), ft(_HP_PAD_Y0)),
             pt(ft(_HP_PAD_X1), ft(_HP_PAD_Y1)), pt(ft(_HP_PAD_X0), ft(_HP_PAD_Y1))),
    thickness=inch(4.0), top_elevation=_HP_PAD_TOP)

# ** ON A PAD THE LEGS ARE THE FEET. ** This is the one thing the move to grade simplifies
# outright. On the balcony the leg positions belonged to the DECK — bay centres, six inches
# off every beam axis — and the cabinets' own foot patterns could not be honoured at the
# same time, so each stand needed a frame that spanned two different grids (decision #64).
# A flat slab has no grid, so each leg stands directly under a published foot hole and the
# rails carry no cantilever at all. Gree's patterns, width x depth, from the submittals:
#
#   EQ-M-HP1-OD  FXU24HP230V1R32AO   29 3/4"  x 15 9/16"   187.4 lb
#   EQ-M-HP2-OD  MUL30HP230V1R32AO   25"      x 15 19/32"  145.5 lb
#
# Both cabinets sit SQUARE to the plan (`rotation=deg(0)`, discharge facing south) since
# 2026-09-03 — they were rotated 90 degrees and facing east before that. The long axis runs
# in x now, so the WIDTH pitch is in x and the DEPTH pitch in y, and the four leg patterns
# transpose with them. The rotation did NOT change on 2026-09-04; only the centres did, when
# the row crossed the pocket to sit against the house and the flight took the south half.
# The centres are the units' own, authored in plan/electrical.py — the two files cannot
# import each other, so a unit that moves must move here too.
#
# The published foot pattern is WIDER than the cabinet across the depth on both units
# (15 9/16" of feet under a 14 9/16" casing), so the north legs stand half an inch PROUD of
# the north face — 2 3/4" from the pad edge, not 3 1/4". That half inch is why the pad's
# north edge is a derived number rather than "the cabinet line plus a bit".
# `test_catlin_outdoor_structures.py` is what holds the two together now that the deck check
# no longer does.
_HP_STAND_AT = (
    ("A", 1, 34.97166667 - 29.75 / 24.0, -1.7109375 - 15.5625 / 24.0),
    ("A", 2, 34.97166667 - 29.75 / 24.0, -1.7109375 + 15.5625 / 24.0),
    ("A", 3, 34.97166667 + 29.75 / 24.0, -1.7109375 - 15.5625 / 24.0),
    ("A", 4, 34.97166667 + 29.75 / 24.0, -1.7109375 + 15.5625 / 24.0),
    ("B", 1, 30.67333333 - 25.0 / 24.0, -1.80458333 - 15.59375 / 24.0),
    ("B", 2, 30.67333333 - 25.0 / 24.0, -1.80458333 + 15.59375 / 24.0),
    ("B", 3, 30.67333333 + 25.0 / 24.0, -1.80458333 - 15.59375 / 24.0),
    ("B", 4, 30.67333333 + 25.0 / 24.0, -1.80458333 + 15.59375 / 24.0),
)
#: 18", against the 12" the balcony stands carried. The owner's 12" was a balcony number —
#: a deck swept by wind keeps its snow depth low in a way ground never does. At grade the
#: cold-climate guidance (18"-24") applies as written, and 18" puts the coil bottom about
#: 20" above grade, past both the drift and Gree's own 2"-above-the-snow-line rule.
_HP_STAND_HEIGHT_IN = 18.0

# ``supported_by`` naming the pad is what stands these up FROM its top rather than hanging
# them below the storey datum: ``_resolve_post`` (resolve/envelope.py) reads any tag in
# ``solid_top``, and a Slab is in that map as one of ``model.solids``. Filed on `main` with
# the pad, so "main + 18\" above a -2'-8" pad top" is the base the units then sit on.
HP_STAND_LEGS = [
    Post(uid=f"SGHP{_hk}{_hi}AAAA", tag=f"PT-SG-HP{_hk}{_hi}",
         position=pt(ft(_hx), ft(_hy)), size="2.0x2.0",
         height=inch(_HP_STAND_HEIGHT_IN),
         supported_by="SL-SG-HPPAD", assembly="EQUIP_STAND_ALUM")
    for _hk, _hi, _hx, _hy in _HP_STAND_AT
]
# One wedge anchor per leg, at the pad top — the plane the base plate bears on and the plane
# the anchor is set through. ``EQUIPMENT_ANCHOR`` for the same reason it always was: the
# part is selected by the joint, not by the section above it, and filing it as a post base
# would print a 3/8" wedge anchor's part number under "modeled post base connector(s)".
# The part is ``SS316-WEDGE-38x3`` in library/hardware.py — 316 because an aluminium leg on
# a de-iced pad at grade is in the splash zone all winter.
HP_STAND_ANCHORS = [
    Connector(uid=f"SGHC{_hk}{_hi}AAAA", tag=f"CN-SG-HP{_hk}{_hi}",
              kind=ConnectorKind.EQUIPMENT_ANCHOR, position=pt(ft(_hx), ft(_hy)),
              elevation=_HP_PAD_TOP, size="SS316-WEDGE-38x3",
              connects=(f"PT-SG-HP{_hk}{_hi}", "SL-SG-HPPAD"))
    for _hk, _hi, _hx, _hy in _HP_STAND_AT
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

# The matching front pair, DROPPED: no authored ``top_elevation``, so
# ``_bearing_stack_drops`` (resolve/envelope.py) propagates the joists' 7 1/4" through
# ``bearing_refs`` to PT-SG-FCOL, whose top falls to ``_back_beam_soffit``, which is what
# puts PT-SG-BF2 on concrete instead of on a 2x8. Both porch beam lines frame the same
# way — joists bearing on top — which is also why there is one soffit derivation above
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
# white pillars, so it is painted with them. Same KDAT stock, same section — see
# plan/assemblies.py::BEAM_WHITE_PAINT. The BACK pair keeps BEAM_KDAT: it is behind the
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

# The porch floor's footprint. The floor system is the floor — no separate slab standing in
# for the framing — so the outline lives here and joists, pillar bearings, etc. share one
# source.
# A local mirror of ``resolve/railings/frame.py::railing_post_stations``, so the blocking
# under a guard's posts can be authored at the stations the resolver will actually frame
# them at rather than at a hand-counted rhythm that drifts when a path moves. Same rule:
# every authored vertex is a station, each segment is divided into ``ceil(seg / spacing)``
# EVEN bays so no bay exceeds the spacing, and the final vertex closes the run.
#
# Deliberately a copy and not an import: this module authors a plan, and reaching into
# ``typehaus.resolve`` from a params file would make the house's geometry depend on the
# resolver's import graph. If that walk ever changes, ``test_joist_reinforcement.py``'s
# station count is what catches the drift.
def _guard_post_stations(path_ft, spacing_ft):
    placed = []
    for (ax, ay), (bx, by) in zip(path_ft[:-1], path_ft[1:], strict=True):
        seg = math.hypot(bx - ax, by - ay)
        bays = max(int(math.ceil(seg / spacing_ft - 1e-9)), 1) if seg > 1e-9 else 1
        for k in range(bays):
            t = k / bays
            placed.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    placed.append(path_ft[-1])
    return placed


_PORCH_OUTLINE = (pt(ft(_x_in_w), ft(_y_ax_front)), pt(ft(_x_in_e), ft(_y_ax_front)),
                  pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n)))

# The porch guard: the same product as RL-SG-BALCONY one storey up, SURFACE-mounted where
# the balcony's is fascia-mounted. A pair of LVL beams cannot carry the ~420 plf a masonry
# parapet would, so the guard is light framing rather than concrete.
#
# **THE PRODUCT IS WILLIAMS ARCHITECTURAL PRODUCTS, ICC-ES ESR-3485, 42" BLACK** (Menards;
# made in Eagan MN at the Ultralox factory), with Fortress Al13 Home as the alternate. It
# replaced Trex Signature on 2026-09-02: the same 6063/6005A alloys and an AAMA-grade
# powder coat at ~$30-45/LF material against $72-98, because Signature's premium buys
# sightline, not life. ESR-3485's maximum post spacing at 42" is 91.3"; the 60" authored
# below already complies with room to spare. A China import lands at $45-60/LF after
# Section 232 (50%) + 301 (25%) and carries no evaluation report: rejected.
#
# **THE TWO GUARDS MOUNT DIFFERENTLY, AND THE SUBSTRATE IS WHY** (owner, 2026-09-02: top
# mount is cheaper, so it is taken wherever the substrate allows). This one is SURFACE:
# the west and east legs run along the inner face of W-SG-W1/E1, so each 5x5 baseplate
# lands on a 12" concrete wall top and takes ESR-3485's concrete-baseplate row — four 1/4"
# x 3" corrosion-resistant anchors, no bracket and no through-bolt. RL-SG-BALCONY stays
# fascia-mounted because its deck is a WATERPROOF PLANE over occupied space; see its own
# block for that.
#
# The SOUTH leg has no wall under it: it runs over BM-SG-FRW/FRE, whose tops carry
# TR-SG-CAP-FRW/FRE and their butyl tape. Anchoring through a cap is the one thing this
# house does not do — it pits the aluminium and pierces the dielectric — so those posts
# bolt through the composite plank into solid blocking set in the joist bay just NORTH of
# the beam (the plank bears nothing; Trex's own specification), authored in
# ``FS-SG-PORCH.reinforcements`` below at the stations ``_guard_post_stations`` reports.
# The baseplates are set that 3" inboard of the deck edge onto the blocks; the guard's
# authored path stays on the edge, which is what the code clearances and the drawings are
# dimensioned from.
#
# **``type_ref`` is the house-local RAILING-EXT-ALUMINUM-SURFACE**, not the library's
# fascia type. The two are the same alloy and the same run and are NOT the same order: a
# fascia guard is bought with a bracket kit per post and a surface guard is bought with its
# post welded to a baseplate. One type_ref for both would bill fascia brackets on a wall
# top where none exist.
#
# West / south / east only — the north edge is the 5" house gap. ``base_elevation`` is the
# walking surface, not the joist tops: the 42" is measured from what a person stands on.
# The front corners are flush, not stepped: W-SG-W1/E1 run 18" past this line at the porch
# top so the balcony's front columns bear on them, and the +6" curb of W-SG-W2/E2 starts
# 18" further south, so the guard runs out over the side walls' own tops. RL-SG-BALCONY is
# on a different plane — 12" south of this one — so the two guards read as two edges rather
# than one.
#
# ** THE EAST LEG OPENS 3'-0" IN ITS MIDDLE, AND THAT COSTS A SECOND RAILING (2026-09-04). **
# PORCH_STAIR comes off the porch's east edge into the yard pocket and the guard has to open
# for it. For one day the opening was at the leg's north END and the path just got its last
# point moved; the flight then had to move south of the condenser row (see PT-SG-BR3, up at
# HP_PAD), and an opening in the MIDDLE of a run is not something one `path` can say. So the
# leg is two elements: PORCH_GUARD carries the west leg, the south leg and the east leg up
# to the flight's south side, and PORCH_GUARD_NE carries the 5'-2" stub from the flight's
# north side to the porch's north edge. Same uid on the long one — it is the same element,
# shortened — and one new uid for the stub.
#
# ** NOTHING IN THE ENGINE WILL ASK ABOUT THE OPENING. ** `code.R312_1_guard_height` tests a
# guard against a deck edge with a plain LineString distance from the edge SEGMENT
# (`_railing_runs_edge`, checks/code/mn_residential/fall_protection.py). Splitting the run
# has not made that better: the two pieces together still cover the segment's midpoint, so
# the 3'-0" gap reports PASS either way, and it would report PASS if the gap were 9'. The
# guard return at the opening is on the author. Recorded in plans/TODO.md, same shape as the
# SL-G-STEP-0 gap already there.
#
# The four constants are shared with the stair, its pad and its rails below precisely so
# they cannot drift: the opening's south edge, the flight's south side, the south rail and
# the stair pad's south edge are one line, and the opening's north edge, the flight's north
# side and the north rail are another.
#
# ** WHY y -6'-0"..-9'-0" AND NOT SOMEWHERE ELSE ON THE WALL. ** W-SG-E1's top is walkable
# only between its two 12" round columns — PT-SG-BR3 (y -3'-0"..-2'-0") and PT-SG-BF3
# (y -10'-9 1/4"..-9'-9 1/4") — which leaves 6'-9 1/4". Inside that, the flight is pushed as
# far south as the discharge wants and no further: -6'-0" is 3'-8" clear of HP2's cabinet
# face against its published 24", and -9'-0" leaves 9 1/4" to BF3 for the south rail's
# baseplates. Sliding it north crowds the machines; sliding it south crowds the column.
_PORCH_STAIR_X0 = _x_in_e + 1.0  # 28.5' — W-SG-E1's east face, where the stringers land
_PORCH_STAIR_X1 = _PORCH_STAIR_X0 + 4 * 11.0 / 12.0  # 32.167' — four 11" treads east of it
_PORCH_STAIR_Y0 = -6.0   # the flight's NORTH side, and the opening's north edge
_PORCH_STAIR_Y1 = -9.0   # its SOUTH side — a 36" flight

# ** THE TWO FRONT CORNERS HAVE NO BASEPLATE — THEY DIE INTO PT-SG-BF1 / BF3. ** The path's
# two front vertices are at (`_x_in_w` / `_x_in_e`, `_y_ax_front`), which is the west/east
# tangent of the two 12" cast rounds in x, and the rounds came 5 1/4" north on 2026-09-03
# (see `_y_front_pillar`) to get the balcony beams cantilevered over their tops. The
# modelled 1 1/2" post still clears the round by 3/4", so nothing here fails — but a real
# 5x5 surface baseplate at those two stations lands inside the concrete. **Set no baseplate
# at the two front corners; land the rail ends on the columns**, Titen Turbo at >=3" edge
# distance, the same fastener and edge rule the HGAM10 beam seat above uses. The engine
# models no baseplate and will never ask about this.
_PORCH_GUARD_PATH = (pt(ft(_x_in_w), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_ax_front)),
                     pt(ft(_x_in_e), ft(_y_ax_front)), pt(ft(_x_in_e), ft(_PORCH_STAIR_Y1)))
PORCH_GUARD = Railing(
    uid="SGRA02AAAA", tag="RL-SG-PORCH", type_ref="RAILING-EXT-ALUMINUM-SURFACE",
    path=_PORCH_GUARD_PATH, kind=RailingKind.METAL_SURFACE_MOUNT,
    height=ft(SPEC.railing_height_ft),
    base_elevation=_porch_walking_surface,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="surface",
    assembly="RAILING_DARK_METAL",
    # R312.1.3: vertical balusters between the 60" posts at a 4" clear gap.
    infill="balusters", baluster_spacing=inch(4))

# The north stub of the east leg, from the flight's north side to the porch's north edge —
# 5'-2" over W-SG-E1's top, everything about it identical to PORCH_GUARD but its path. It is
# a separate element only because a `path` cannot carry a hole; it is bought, built and
# billed as part of the same run, which is why it shares the type_ref and the assembly.
PORCH_GUARD_NE = Railing(
    uid="SGRA07AAAA", tag="RL-SG-PORCH-NE", type_ref="RAILING-EXT-ALUMINUM-SURFACE",
    path=(pt(ft(_x_in_e), ft(_PORCH_STAIR_Y0)), pt(ft(_x_in_e), ft(_y_in_n))),
    kind=RailingKind.METAL_SURFACE_MOUNT,
    height=ft(SPEC.railing_height_ft),
    base_elevation=_porch_walking_surface,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="surface",
    assembly="RAILING_DARK_METAL",
    infill="balusters", baluster_spacing=inch(4))

# The south leg's post stations, in feet — the run over BM-SG-FRW/FRE that has no wall top
# under it and therefore needs blocking. Taken as the middle segment of the guard path so
# the two corner posts (which DO land on W-SG-W1/E1's tops) are excluded.
_PORCH_GUARD_SOUTH_STATIONS = [
    x for x, y in _guard_post_stations(
        [(_x_in_w, _y_ax_front), (_x_in_e, _y_ax_front)], 60.0 / 12.0)
    if _x_in_w + 0.01 < x < _x_in_e - 0.01
]
# The blocking sits one cap-width north of the beam axis, in the first joist bay — same 3"
# as PT-SG-BF2 and for the same reason.
_y_porch_guard_block = _y_ax_front + 3.0 / 12.0

# ============================================================================
# PORCH_STAIR — the porch's only way down to grade (2026-09-03).
# ============================================================================
# The porch floor is at 0'-0" and grade east of it at -2'-10"; until now the only way onto
# the porch was D-M-BALC, the French pair at x 21'-4". The flight goes east off the porch's
# east edge into the yard pocket, from the clear stretch of W-SG-E1's top between its two
# columns, landing on STAIR_PAD below. See notes/porch_stair.md.
#
# 5 risers at 6 3/5", 4 treads at 11" and NO nosing, 36" wide, KDAT — the ST-G-SERVICE
# pattern (plan/storeys/garage.py), which is the same 0'-0"-to-grade five-riser flight and is
# already priced and tested. `start` is the FOOT, on the pad at the east end; the flight
# climbs west (`run_reversed`) to the wall top, and `width` runs +y from `start`, so
# `_PORCH_STAIR_Y1` is the south side and `_PORCH_STAIR_Y0` the north, in that order.
#
# ** BOTH ELEVATIONS ARE STATED, because neither is a storey datum. ** `from_storey` and
# `to_storey` are both `main` — this is a step-down within one storey, the case
# `floor_opening=None` exists for — so the rise is the authored pair: the pad top at -2'-8"
# to the porch's WALKING surface at +0'-1" (the composite plank over the joists, not the 0'
# joist top). 33" over five risers is 6.60" each, inside R311.7.5.1, and the 11" going leaves
# R311.7.5.2's 10" minimum with an inch to spare.
#
# ** THE 12" WALL TOP IS A THRESHOLD, NOT A TREAD. ** W-SG-E1's top is 0'-0", one inch BELOW
# the porch plank, so a flight springing from x 27'-6" would want its first tread 5 3/5"
# below the concrete it has to cross. The flight therefore starts at the wall's EAST face and
# the wall top is decked flush at +0'-1" with a 3'-0" x 12" board of the porch's own
# composite plank. That is 3 sf of trim over concrete with nothing to frame: it is NOT
# MODELLED, it is priced with the plank in prices.toml [framing] and written down in
# notes/porch_stair.md — the same call the framed-wall line-set sleeve got.
#
# ** AND AN UNMODELLED THRESHOLD IS WHY THE FIRST TRY LANDED ON A COLUMN. ** Drawn against
# the pocket's north strip, this board ran straight through PT-SG-BR3 — a 12" round on a 12"
# wall, so it filled the top edge to edge and left 10" of passage one side and 14" the other.
# Nothing failed: the column's east face is exactly tangent to the stair's head at x 28'-6",
# so no solid overlapped, and the board that would have overlapped is trim. Read the wall
# top's occupants by hand before moving this flight along it.
#
# The stringers bear on that wall top at the head and on the pad at the foot. No
# `bearing_refs`: the flight hosts itself between two solids, and a tag there that names no
# wall on `from_storey` is an `integrity.stair_bearing` error rather than a permission.
#
# ** STAIR_PAD: x 28'-6"..35'-3", y -9'-0"..-6'-0" — 20.3 sf, 0.25 cy at 4". ** Its own pour,
# poured to `_HP_PAD_TOP` so the flight's authored base is the pad it actually lands on. The
# west edge is W-SG-E1's east face, where the stringers foot; the flight itself covers x
# 28'-6"..32'-2"; and the 3'-1" east of that is R311.7.6's bottom landing, which wants 36"
# in the direction of travel and gets 37". It is 2'-8" clear of HP_PAD in y, so the two are
# separate rectangles and not one L — a single pour spanning both would be 94 sf to serve 40.
_STAIR_PAD_X1 = _PORCH_STAIR_X1 + 37.0 / 12.0  # 35.25' — 37" of landing past the bottom riser

STAIR_PAD = Slab(
    uid="SGSPADAAAA", tag="SL-SG-STAIRPAD", assembly="HP_PAD_ON_GRADE",
    outline=(pt(ft(_PORCH_STAIR_X0), ft(_PORCH_STAIR_Y1)),
             pt(ft(_STAIR_PAD_X1), ft(_PORCH_STAIR_Y1)),
             pt(ft(_STAIR_PAD_X1), ft(_PORCH_STAIR_Y0)),
             pt(ft(_PORCH_STAIR_X0), ft(_PORCH_STAIR_Y0))),
    thickness=inch(4.0), top_elevation=_HP_PAD_TOP)

PORCH_STAIR = Stair(
    uid="SGST01AAAA", tag="ST-SG-PORCH",
    from_storey="main", to_storey="main",
    base_elevation=_HP_PAD_TOP, top_elevation=_porch_walking_surface,
    width=ft(3), start=pt(ft(_PORCH_STAIR_X1), ft(_PORCH_STAIR_Y1)),
    run_direction="x", run_reversed=True,
    tread_depth=inch(11), nosing_depth=inch(0),
    material="kdat")

# ** A GUARD ON EACH SIDE, AND EACH ONE IS ALSO THE HANDRAIL. ** The total rise is 33", over
# R312.1.1's 30" trigger, so both open sides want a guard; five risers is over R311.7.8's
# four, so the flight wants a graspable handrail. One 36" run with a graspable top rail
# answers both, which is what `role="guard_and_handrail"` says. 36" clears R312.1.2's 34"
# stair minimum measured off the nosing line, and R311.7.8.1's 34"-38" for the rail top.
#
# BOTH sides are open yard now — the flight sits in the middle of the pocket, 5'-2" south of
# the house and 1'-6" north of the W-RG-EAST-BALCONY apron — so neither side has a wall that
# `code.R312_1_1_stair_open_side` could credit even in principle. While the flight ran along
# the house this same pair was authored for a subtler reason (W-M-S2's band starts at 0'-0"
# and every nosing but the last runs below it), and the pair is unchanged.
#
# A 36" tread past two 1 1/2" sections leaves 33" clear against R311.7.1's 27" for two rails.
#
# These two stop at the flight — x 28'-6", the head — and the threshold beyond it is guarded
# by PORCH_STAIR_THRESHOLD_RAILS below rather than by extending these. A `serves_stair`
# Railing is RAKED along the nosing line for its whole authored path, so a foot of level
# wall top on the end of one resolves at 0" above the (absent) nosings and fails
# R311.7.8.1's 34"-38" outright. Two elements is not a workaround here, it is the true
# statement: one raked handrail-guard on the flight, one level guard on the wall top.
#
# Same product as RL-SG-PORCH (Williams ESR-3485 black, surface-mounted), so they read as one
# system from the porch. `mount="surface"` is honest at the head, where the baseplates land on
# the wall top; along the rake the posts stand on the stringers instead, which is the
# RL-G-SERVICE condition and is what the price row's own note has to say (a raked post on a
# wood stringer is not the 5x5-on-concrete the surface row's rate is built from).
PORCH_STAIR_RAILS = [
    Railing(uid=f"SGRA0{_si}AAAA", tag=f"RL-SG-PSTAIR-{_sh}",
            type_ref="RAILING-EXT-ALUMINUM-SURFACE",
            path=(pt(ft(_PORCH_STAIR_X1), ft(_sy)), pt(ft(_PORCH_STAIR_X0), ft(_sy))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=_HP_PAD_TOP, post_spacing=inch(36), post_size="2x2",
            rail_count=2, mount="surface", assembly="RAILING_DARK_METAL",
            role="guard_and_handrail", serves_stair="ST-SG-PORCH", top_height=inch(36),
            graspable_profile="1.5in round — Type I",
            infill="balusters", baluster_spacing=inch(4))
    for _si, _sh, _sy in ((3, "S", _PORCH_STAIR_Y1), (4, "N", _PORCH_STAIR_Y0))
]

# ** THE THRESHOLD'S TWO CHEEKS. ** The 12" of W-SG-E1 wall top between the porch plank and
# the head of the flight (x 27'-6"..28'-6") is decked flush at +0'-1" and is 33" above the
# pad on BOTH its north and south sides. Nothing in the engine asks for a guard there:
# `code.R312_1_1_stair_open_side` measures the FLIGHT, whose top tread is only 26 2/5" over
# the pad, and `code.R312_1_guard_height` tests RL-SG-PORCH against the deck edge SEGMENT,
# whose midpoint stays guarded, so the 3'-0" opening reports PASS with or without a return
# (plans/TODO.md). The guard return at an opening is on the author, and this is it.
#
# Level, not raked — they stand on the wall top, not on a flight — so 42" to match
# RL-SG-PORCH, whose south cheek they run out of at its new terminus. Same product, same
# baseplate-on-concrete condition, which is exactly what the surface row's rate is built for.
PORCH_STAIR_THRESHOLD_RAILS = [
    Railing(uid=f"SGRA0{_ti}AAAA", tag=f"RL-SG-PTHRESH-{_th}",
            type_ref="RAILING-EXT-ALUMINUM-SURFACE",
            path=(pt(ft(_x_in_e), ft(_ty)), pt(ft(_PORCH_STAIR_X0), ft(_ty))),
            kind=RailingKind.METAL_SURFACE_MOUNT,
            height=ft(SPEC.railing_height_ft),
            base_elevation=_porch_walking_surface,
            post_spacing=inch(60), post_size="2x2", rail_count=2, mount="surface",
            assembly="RAILING_DARK_METAL",
            infill="balusters", baluster_spacing=inch(4))
    for _ti, _th, _ty in ((5, "S", _PORCH_STAIR_Y1), (6, "N", _PORCH_STAIR_Y0))
]

# ============================================================================
# Second (balcony, ~10'): 6x6 pillars, three 3-ply 2x12 beams, aluminum deck.
# ============================================================================
# Six pillars. Four land on the two porch side walls at 0'-0"; PT-SG-BF2 lands on the front
# column's top at -1'-6 1/2"; only PT-SG-BR2 stands on the porch decking. The pillar *tops*
# are level because height is measured back from the beam soffit. Rear row is 2" taller
# overall so the deck crowns and drains south, away from the house. Beam soffit = balcony
# level minus the beam depth, read off the size.
_balcony_beam_depth_ft = cross_section(SPEC.balcony_beam).depth_m / 0.3048
_balcony_joist_depth_ft = 7.25 / 12.0  # 2x8 deck joist
# Pillar-height *input* only — the resolver drops beam + post by the deck joist depth
# (resolve/envelope.py::_bearing_stack_drops), so the wood doesn't actually land here (see
# _balcony_beam_soffit below). Subtracting the joist depth here too would double-count it.
_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_beam_depth_ft)
# The *resolved* soffit: the plane every pillar top and every cast column top lands on, and
# the plane the three balcony beams bear at.
_balcony_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_joist_depth_ft
                          - _balcony_beam_depth_ft)  # 8.458'
_PILLAR_X = (_x_ax_w, _cx, _x_ax_e)
# (row, x index) -> (the concrete wall top that pillar bears on, its elevation). Anything
# not in the map bears on the porch decking instead.
#
# All four outer pillars bear on the two porch side walls at `_porch_top`. Handing the
# front pair to W-SG-W2/E2 at the retaining top (6" higher) instead would put a pillar half
# on a wall whose head is unbraced (R404.4) and half on one the porch frames into, because
# the wall junction sits on their own axis. `side_wall_south_extension_in` runs W1/E1 past
# the pillars so the map can say the true thing; the two front pillars are longer for it and
# their ABU66SS bases came down with them, but the beam soffit they rise to has not moved.
#
# ``("F", 2)`` is not a wall at all: PT-SG-BF2 stands on the CONCRETE COLUMN, on the same
# ``_back_beam_soffit`` the two front beams land on. That one entry drives the
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
}
# The rear pillar row rides on the *back-beam* line, not on the deck's north edge. At
# `_y_in_n` PT-SG-BR2 would land on the cantilevered tip of the porch joists — a 6x6
# carrying a third of the balcony, standing on the free end of one 1 1/2" ply, which would
# need mitigation (3-ply sisters + blocking + an uplift tie). On the beam line PT-SG-BR2
# lands directly over PT-SG-COL, on the shared bearing of BM-SG-BKW/BKE, so the load runs
# plank -> joist -> back beam -> cast column -> footing — mirroring PT-SG-BF2 over
# PT-SG-FCOL, symmetric in kind. BR1/BR3 stay on W-SG-W1/E1 (those walls run
# _y_in_n -> _y_ax_s), so ``_WALL_UNDER_PILLAR`` is unchanged and they gain edge cover.
#
# The 3" south of the beam axis is deliberate and is NOT slop. ``_band`` in
# checks/structural/cantilever.py tests ``post_axis >= axis_hi - end - _EPS``, so a pillar
# landed exactly on the bearing line still reads as inside the overhang and reports a 0"
# overhang with ``past_m = 0.0`` — a finding about a joint that no longer exists. 3" into
# an 87" back span is structurally indistinguishable and lets the check go silent honestly.
# **Do not widen ``_EPS`` instead**; the offset is the statement, not a workaround.
#
# Nothing else moves with the row now that the brace rails and their nodes are gone.
# What does NOT move: SECOND_NODES, the deck outline, guard, fascia, gutter and
# rear counter-flashing, all keyed to ``_y_in_n``. So the three balcony beams keep their
# full length and gain a north cantilever past the rear pillars:
#
#     back span   = _y_rear_pillar - _y_front_pillar = -2.5 - (-9.833) = 7.33' = 88"
#     overhang    = _y_in_n - _y_rear_pillar         = -0.833 - (-2.5) = 1.667' = 20.0"
#     R507.5.1 limit = back span / 4                 = 88" / 4         = 22.0"  -> OK by 2"
#
# ** THE BACK SPAN IS THE FRONT ROW'S TO SPEND, AND 8" OF IT IS GONE. ** It was 96" while
# the front row sat on `_y_balcony_front` itself; the row came 8" north so the beams would
# cantilever over the 12" rounds (`_y_front_pillar`), and the limit fell 24" -> 22" against
# an overhang that did not move. **The front row cannot go north again without taking
# PT-SG-BR1/2/3 north with it**, and at that point `_WALL_UNDER_PILLAR` and the back-beam
# line come into it.
#
# That arithmetic is written down because nothing checks it: checks/structural/deck.py
# grades beam *span* only and has no beam-cantilever rule, so this overhang would pass
# silently either way — and so would the 8" one at the south end, against the same 22".
# See notes/beam_water_protection.md, which carries the missing check as an open item.
# IRC Table R507.5(1) is keyed on the JOIST span, which is unchanged at FS-SG-DECK's 10.00'
# (limit 9.17' for a 3-2x12), so what this buys is margin: the three balcony beams are at
# 7.33' against 9.17' span, 22" of headroom. They pass even on the 12' row (8.33'), which is
# what any further increase in the deck's joist span would drop the lookup to.
_REAR_PILLAR_SOUTH_OF_COL_IN = 3.0
_y_rear_pillar = _y_col - _REAR_PILLAR_SOUTH_OF_COL_IN / 12.0  # -2.5'
# Half the cast round, read off SPEC rather than written down, so the front row's offset
# cannot drift from the member standing on it. "12 round" -> 6.0.
_corner_column_radius_in = float(SPEC.corner_column_size.split()[0]) / 2.0
# How far the balcony beams oversail that face. 2" is a drip, not a structural number.
_FRONT_COLUMN_CANTILEVER_IN = 2.0

# The FRONT row stands 8" north of `_y_balcony_front`, and the rear row does not, and the
# asymmetry is a weather detail rather than a structural one.
#
# BM-SG-BLW/BLC/BLE END on the front pillar line — N-SGB-SW/SC/SE are the beams' south
# nodes. A beam that stops on its post's AXIS covers the north half of that post's top and
# leaves the south half open to the sky. That is the classic exposed-post-top detail: water
# sits in the re-entrant corner against the beam face, wicks down the end grain, and on the
# 12" cast rounds it also ponds on the crescent of concrete south of the beam. The beam
# gets pushed out PAST the column's south face instead, so the top is roofed by the member
# it carries and the beam end drips into air.
#
# ** 2026-09-03: THE ROW CAME 5 1/4" FURTHER NORTH, AND THE OFFSET IS NOW THE ROUND'S. **
# This was `_balcony_front + 2 3/4"` — half of the 5 1/2" actual 6x6 — which had been right
# while the front corners were wood posts and went stale the day they became 12" cast
# rounds. A 6" radius on a 2 3/4" offset puts the column's south face at -10'-9 1/4", 3 1/4"
# SOUTH of the beam end: the beam no longer roofed the top at all, it sat on the north half
# of a shelf that collected water against its own end grain and against the HGAM10.
#
# The offset is therefore derived from the member that stands here — half the round, plus a
# deliberate 2" of beam past the face:
#
#     axis     = _y_balcony_front + (6" + 2")     = -9'-10"
#     column   = -10'-4" .. -9'-4"
#     beam end = -10'-6"  ->  2" of glulam cantilevered past the column's south face
#
# ** ONLY PT-SG-BF1 AND BF3 READ THIS. ** PT-SG-BF2 is a wood 6x6 and takes `_y_bf2` below.
# Its beam BM-SG-BLC has cantilevered 15" past it since BF2 moved onto the porch deck, so
# the centre bay has never had this problem.
#
# ** WHAT IT COSTS, AND IT IS NOT THE STAIR. ** PORCH_STAIR's south side is -9'-0", so the
# column's north face keeps 4" — tight, and the reason `_PORCH_STAIR_Y1` is a shared
# constant. The binding constraint is RL-SG-PORCH's corner post: it stands at (`_x_in_e` /
# `_x_in_w`, `_y_ax_front`), tangent to the round in x already, and at 5 1/4" north the
# modelled 1 1/2" post clears the column by 3/4" but a real 5x5 surface baseplate lands
# INSIDE the 12" round. **The guard's two front corners die into the columns**: the south
# leg's rail ends and the east/west legs' land on the concrete with the same Titen Turbo at
# >=3" edge distance the HGAM10 uses, and no baseplate is set at those two stations. The
# engine cannot see a baseplate, so nothing will fail if this is forgotten — it is written
# here and in PORCH_GUARD's own comment, and on RAILING_DARK_METAL in prices.toml.
#
# ** AND IT SPENDS 2" OF THE BEAMS' NORTH OVERHANG. ** The back span shortens with the row:
#
#     back span      = _y_rear_pillar - axis = -2.5 - (-9.8333) = 7.333' = 88"  (was 96")
#     north overhang = _y_in_n - _y_rear_pillar                 = 20"      (unchanged)
#     R507.5.1 limit = back span / 4                            = 22"      (was 24")
#
# 20" against 22" still passes, with 2" left rather than 4". Nothing checks it (checks/
# structural/deck.py grades beam SPAN only) — that missing check is the open item in
# notes/beam_water_protection.md. The south overhang is the new 8" against the same 22".
# **The row cannot go north again without moving PT-SG-BR1/2/3 with it.**
#
# Modelled the other way round from how it builds — the beam ends stay put on
# `_y_balcony_front` (they are the deck edge, the fascia line and the gutter line, none of
# which should move) and the COLUMNS come north. Same joint, and it keeps every dimension
# that a drawing would carry off the deck edge.
#
# The rear row needs none of this: at `_y_rear_pillar` the beams run 20" further north to
# `_y_in_n`, so PT-SG-BR1/2/3 are mid-span under a continuous member and their tops are
# already covered. Only a post at a beam's END has this problem.
#
# What moves with the row, because it is the row: the two corner columns' bases. What does
# NOT move: the beam ends themselves, `_DECK_OUTLINE`, the guard, fascia, drip and gutter
# paths, and `BALCONY_FRONT_AXIS_Y_FT` — the published contract raised_garden.py reads.
_y_front_pillar = _y_balcony_front + (
    _corner_column_radius_in + _FRONT_COLUMN_CANTILEVER_IN) / 12.0  # -9.833333'
_PILLAR_ROWS = (("R", _y_rear_pillar, inch(SPEC.rear_pillar_rise_in)),
                ("F", _y_front_pillar, ft(0)))
# PT-SG-BF2 moves NORTH onto the porch deck, 3" inside the front beam axis — the exact
# mirror of PT-SG-BR2's 3" south of the back beam line, and for the same two reasons. It
# used to stand on PT-SG-FCOL's top, 19 1/2" below the porch walking surface, which made it
# 19 1/2" longer than its five neighbours and forced that column to 20" round so one pour
# could span from the beams' north face to the pillar's south face. Standing it on the deck
# instead makes all six pillars the same member and lets the column shrink to the 12" every
# other cast column in this garden is.
#
# **3" is the minimum, not slop.** The porch outline ENDS on the front beam axis, so any
# less and the 5 1/2" post hangs off the deck; and ``_band`` in
# checks/structural/cantilever.py tests ``post_axis >= axis_hi - end - _EPS``, so a pillar
# landed exactly on the bearing line still reads as inside the overhang and reports a 0"
# overhang about a joint that no longer exists.
_BF2_NORTH_OF_FRONT_AXIS_IN = 3.0
_y_bf2 = _y_ax_front + _BF2_NORTH_OF_FRONT_AXIS_IN / 12.0
# The four CORNER pillars became 12" cast concrete columns on 2026-09-03 and the two CENTRE
# pillars did not. That split is the whole redesign in one loop: four columns FIXED at the
# base (doweled into the 12" wall tops of W-SG-W1/E1, whose axis they stand on, so the round
# is flush with both wall faces) are the balcony's entire lateral system, which is what let
# the eight knee braces and two E-W brace rails be deleted outright. The centres stay wood
# 6x6 on pinned ABU66SS bases — leaning columns, tied in by the deck diaphragm — because
# nothing asks them to carry moment and a 6x6 is a third the cost of a formed column.
#
# Same tags and same uids throughout: these are the same six elements, re-sized.
_CORNER_PILLAR_INDICES = (1, 3)
PILLARS = []
PILLAR_BEARINGS = {}  # pillar tag -> (bearing tag, base elevation) — reused by the bases
for _i, _x in enumerate(_PILLAR_X, start=1):
    for _row_index, (_row, _y, _rise) in enumerate(_PILLAR_ROWS):
        _bears_on, _base = _WALL_UNDER_PILLAR.get(
            (_row, _i), ("FS-SG-PORCH", _porch_walking_surface))
        _tag = f"PT-SG-B{_row}{_i}"
        _is_corner = _i in _CORNER_PILLAR_INDICES
        if _row == "F" and _i == 2:
            _y = _y_bf2
        PILLAR_BEARINGS[_tag] = (_bears_on, _base)
        PILLARS.append(Post(uid=f"SGPB{_i}{_row_index}AAAA", tag=_tag,
                            position=pt(ft(_x), ft(_y)),
                            size=(SPEC.corner_column_size if _is_corner
                                  else SPEC.pillar_size),
                            height=_beam_soffit - _base + _rise,
                            supported_by=_bears_on,
                            vertical_reinforcement=(SPEC.corner_column_cage
                                                    if _is_corner else None),
                            reinforcement=(_CAST_COLUMN_CAGE_HDG if _is_corner else None),
                            assembly=("SUNKEN_GARDEN_COLUMN_12" if _is_corner
                                      else "POST_WHITE_PAINT")))

# The two CENTRE pillars are now alike again, and that is the point.
#
# **PT-SG-BF2 stands on the porch decking**, the exact mirror of PT-SG-BR2: plank -> joist
# -> BM-SG-FRW/FRE -> PT-SG-FCOL -> footing, 3" inside the front beam axis where BR2 is 3"
# inside the back one. It stood on PT-SG-FCOL's top until 2026-09-03, 19 1/2" below the
# walking surface and 19 1/2" longer than its five neighbours, which is what forced that
# column to 20" round. Moving it north makes all six pillars one member and lets the column
# be the 12" every other cast column here is; both centre posts now take squash blocks and
# a plank cut-out, and both bear on framing rather than on a pour.
#
# **Post-on-post is still a supported path** and the note is kept because the four CORNER
# columns now use it in spirit: ``resolve_columns_and_beams`` (resolve/envelope.py)
# republishes each post's resolved top into ``solid_top`` as it goes, precisely so a post
# can stand on a concrete pier; ``breezeway.py``'s Pad -> PR-BW-* -> PT-BW-* is the live
# precedent. **Do not retarget a Post to a BEAM**: beams are resolved in the same loop but
# are never published into ``solid_top``, so a post naming one falls back to hanging below
# its storey datum — silently, and inside the beam band that
# ``structural.member_interference`` then FAILs on.
#
# A field detail the model has no field for, so it lives here and in POST_WHITE_PAINT's
# ``source``: **cut a 4"-square hole through the composite plank at PT-SG-BR2 and at
# PT-SG-BF2 so each ABU66SS bears on the framing below, not on the plank.** Trex's own
# specification says composite decking "cannot be used as structural material; any load
# bearing area will need to be framed and supported before the composite material can be
# attached". Strength is not the issue — the base spreads ~50 psi on the plank. The two
# that are:
#   * CREEP. Sustained load at the 140-160 degF summer surface temperature of a dark
#     composite plank settles these two pillars relative to the four that bear on concrete,
#     and that differential takes the balcony's watertight aluminium plank out of plane.
#     Nothing in the model would see it.
#   * REPLACEABILITY. The plank is a wear layer. You cannot pull a board out from under a
#     6x6 carrying a third of a balcony without shoring the balcony first.
#
# **BF2's 3" is also what keeps it off the beam cap.** At the front beam AXIS the pillar
# would land square on TR-SG-CAP-FRW/FRE; 3" north it bears on the joists behind the cap's
# north turn-down. That rule is not decorative — a 304-stainless base bearing on 0.019"
# aluminium coil in a wet exterior location pits the aluminium (it is anodic), and
# anchoring through it penetrates the butyl tape that IS the dielectric between that coil
# and the copper-treated KDAT. A base that ever does cross a cap needs an EPDM or HDPE
# isolator pad and a written detail.

SECOND_NODES = [
    Node(uid="SGNB01AAAA", tag="N-SGB-NW", position=pt(ft(_x_ax_w), ft(_y_in_n))),
    Node(uid="SGNB02AAAA", tag="N-SGB-SW", position=pt(ft(_x_ax_w), ft(_y_balcony_front))),
    Node(uid="SGNB03AAAA", tag="N-SGB-NC", position=pt(ft(_cx), ft(_y_in_n))),
    Node(uid="SGNB04AAAA", tag="N-SGB-SC", position=pt(ft(_cx), ft(_y_balcony_front))),
    Node(uid="SGNB05AAAA", tag="N-SGB-NE", position=pt(ft(_x_ax_e), ft(_y_in_n))),
    Node(uid="SGNB06AAAA", tag="N-SGB-SE", position=pt(ft(_x_ax_e), ft(_y_balcony_front))),
]

# Three N-S treated-glulam beams over the west / center / east column lines.
#
# **All three are the same product now**, where the two outer ones used to be white-painted
# KDAT (BEAM_WHITE_PAINT) and the centre one bare KDAT. A glulam is a manufactured member
# with laminations that read as the thing it is, and painting the two you can see while
# leaving the one you cannot would be buying a finish to hide a better member. The white
# paint stays where it still means something: the two centre 6x6 pillars (POST_WHITE_PAINT)
# and the porch's front beam pair (BEAM_WHITE_PAINT).
#
# `top_protection=_BEAM_TAPE_WIDE` is unchanged and still correct: the roll width derives
# from the section's own width, so the 3-1/2" glulam takes the same wide roll the 4-1/2"
# 3-2x12 did. The formed aluminium caps (TR-SG-CAP-BL*) likewise size themselves off
# `SPEC.balcony_beam` and follow the new width without a literal moving.
BALCONY_BEAMS = [
    Beam(uid="SGBB01AAAA", tag="BM-SG-BLW", start_node="N-SGB-NW", end_node="N-SGB-SW",
         size=SPEC.balcony_beam, assembly="BEAM_GLULAM_TREATED",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-BR1", "PT-SG-BF1")),
    Beam(uid="SGBB02AAAA", tag="BM-SG-BLC", start_node="N-SGB-NC", end_node="N-SGB-SC",
         size=SPEC.balcony_beam, assembly="BEAM_GLULAM_TREATED",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-BR2", "PT-SG-BF2")),
    Beam(uid="SGBB03AAAA", tag="BM-SG-BLE", start_node="N-SGB-NE", end_node="N-SGB-SE",
         size=SPEC.balcony_beam, assembly="BEAM_GLULAM_TREATED",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-BR3", "PT-SG-BF3")),
]

# ** THE TWO E-W BRACE RAILS ARE GONE, AND SO ARE THE EIGHT KNEE BRACES. ** They were the
# balcony's entire lateral system while all six pillars were wood on pinned standoff bases.
# The four corner pillars are now 12" cast concrete columns FIXED at the base, doweled into
# the wall tops they stand on, and four fixed columns ARE the lateral system in both plan
# directions — so the rails have nothing to collect and the braces have nothing to rise
# into. See notes/balcony_moment_columns.md for the base moments they carry instead.
#
# Spent uids, not reused: the two rails XYQFW1YGXG / VWWMCZ1TBG, their four nodes
# 9VBVMD4AR6 / EQERKG45X9 / GMEZET9T9W / 20Q9XQFSV9, the eight braces SGCK1RAAAA /
# SGCK3RAAAA / SGCK1FAAAA / SGCK3FAAAA / SGKX1RAAAA / SGKX3RAAAA / SGKX1FAAAA / SGKX3FAAAA,
# and before them the four girts SGBG01..04AAAA with nodes SGNG01..08AAAA.

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
# Guard the three open edges (west, front/south, east); the north edge abuts the house.
# Defined here rather than beside BALCONY_GUARD below because FS-SG-DECK's rim blocking is
# authored at this path's own post stations — the blocks and the posts cannot be allowed to
# drift apart.
_GUARD_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_balcony_front)),
               pt(ft(_deck_x_e), ft(_y_balcony_front)), pt(ft(_deck_x_e), ft(_y_in_n)))
# THE BLOCKING GOES UNDER THE SOUTH LEG'S POSTS ONLY, and which leg gets it is decided by
# which way the joists run rather than by where the guard is.
#
# FS-SG-DECK's joists run E-W. So:
#   * the WEST and EAST legs stand over the joist TIPS — a fascia bracket there bolts through
#     the PVC and the rim band into the ends of the joists themselves, which is backing
#     already and cannot roll;
#   * the SOUTH leg runs PARALLEL to the joists, over the front rim, with the first joist
#     16" behind it. That rim is what a 200 lb load at 42" tries to roll, and blocking
#     between the two is what stops it.
#
# The stations are INSET 2" off the guard line, and the inset is not cosmetic: a guard path
# is the deck EDGE, and a JoistReinforcement authored exactly on the edge falls outside the
# joist field the resolver lays blocks in — it is silently dropped. The model would then
# show a guard with backing at some posts and none at others, at 0 FAIL. 2" also happens to
# be where the block physically sits: against the rim, in the first bay behind it.
_GUARD_BLOCK_INSET_FT = 2.0 / 12.0
_BALCONY_GUARD_STATIONS = [
    (_gx, _y_balcony_front + _GUARD_BLOCK_INSET_FT)
    for _gx, _gy in _guard_post_stations(
        [(_deck_x_w, _y_balcony_front), (_deck_x_e, _y_balcony_front)], 60.0 / 12.0)
    if _deck_x_w + 0.01 < _gx < _deck_x_e - 0.01]

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
                     # Do not add an oversail here — past the 8"
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
    # SQUASH BLOCKS under PT-SG-BR2, and nothing else.
    #
    # The pillar row sits on the back-beam line, so the CANTILEVER reason for reinforcement
    # is gone and ``structural.cantilever_point_load`` goes honestly silent. But rollover and
    # cross-grain bearing under a 6x6 point load are a DIFFERENT reason. BR2 still bears
    # through one 1 1/2" ply of
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
        # BF2's pair, added 2026-09-03 when that pillar came north off PT-SG-FCOL's top
        # onto the deck. Identical reasoning to BR2's above, mirrored about the deck: a
        # 6x6 carrying a third of the balcony bears through one 1 1/2" ply of 2x8, at
        # ~315 psi under the ABU66SS and ~385 psi where that joist crosses the front beam,
        # against an Fc-perp of 425 psi (SPF) with no duration factor. Nothing grades it —
        # ``structural.landing_post_bearing`` is the rule that would and it is scoped to
        # stair landing posts (see plans/TODO.md).
        JoistReinforcement(
            at=pt(ft(_cx), ft(_y_bf2)), plies=1, blocking=True,
            source="squash blocks under PT-SG-BF2 — the mirror of BR2's, added when the "
                   "front centre pillar moved off the cast column onto the porch framing"),
        # The porch guard's south-leg posts. A surface-mounted 42" guard takes the R301.5
        # 200 lb concentrated load at its top, which arrives at the baseplate as a couple
        # the 5x5 plate spreads over two joists — and nothing under it but a 1" composite
        # plank that Trex says bears nothing. The block is what the through-bolts land in
        # and what stops the joists rolling under the overturning. The west and east legs
        # need none of this: their baseplates sit on W-SG-W1/E1's 12" concrete tops and
        # take ESR-3485's four 1/4" x 3" anchors straight into the pour.
        #
        # ``plies=1`` throughout, exactly as BR2's is: ``_reinforcement_members`` lays
        # ``range(plies - 1)`` sisters, i.e. NONE, and only the two blocks. What this needs
        # is a bearing and roll block, not a stiffened joist, and it keeps
        # ``test_no_catlin_deck_sisters_a_joist`` green.
        *(JoistReinforcement(
            at=pt(ft(_gx), ft(_y_porch_guard_block)), plies=1, blocking=True,
            source="solid blocking under an RL-SG-PORCH south-leg guard post — the "
                   "baseplate bolts through the plank into this block, never through "
                   "TR-SG-CAP-FRW/FRE and its butyl")
          for _gx in _PORCH_GUARD_SOUTH_STATIONS),
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
# The aluminium plank is this deck's own `subfloor`, not a separate Slab standing in for
# the framing: a plank laid over joists is a floor system's SURFACE LAYER, not a slab — as a
# Slab it would resolve into `structural_solids` with category "slab", billable only by the
# cubic yard out of a table named [concrete], and read as a second floor plane sitting on
# the deck in section and in the GLB. As a `subfloor` it is a sheet over the joist field,
# bills by the square foot in [sheet_goods] beside the porch's composite plank, and there is
# one floor here.
#
# `resolve/floors.py` draws the deck sheet bearing-line to bearing-line PLUS both
# cantilevers, by the joists' perpendicular extent — _x_ax_w - 6" to _x_ax_e + 6" by the
# balcony's front plane to _y_in_n.
BALCONY_JOISTS = FloorSystem(
    uid="SGFS02AAAA", tag="FS-SG-DECK",
    joists=JoistSpec(member=SPEC.balcony_joist, spacing=inch(SPEC.balcony_joist_oc_in),
                     direction="x", cantilever=inch(SPEC.joist_cantilever_in),
                     # The two rim bands close the joist tips on the garden's front and rear
                     # faces, at eye level from the walk below and in the same plane as the
                     # white pillars and knee braces — so they are painted with them. The
                     # joists behind them stay bare KDAT: nothing sees a joist once the band
                     # and the fascia are on.
                     rim_material="post-paint-white",
                     bearing_refs=("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE")),
    # RIM BLOCKING UNDER THE GUARD'S SOUTH LEG, and it is the only reinforcement on this
    # deck. The two heat-pump hosts that used to be here went to grade on 2026-09-02
    # (notes/heat_pump_ground_pad.md), which left this plank with ZERO penetrations — and
    # that is exactly why the balcony's guard stays FASCIA-mounted while the porch's goes
    # surface: FS-SG-DECK's aluminium plank is the porch roof, and ~36 surface baseplates
    # would be the only holes in the one waterproof plane in this structure.
    #
    # What a fascia bracket needs instead is something behind the rim. Ultralox's own
    # fascia-mount instructions (the accepted basis under IRC R106/R301.1.3 — ESR-3485's
    # fascia row is written for concrete, and no PE letter is needed to follow the
    # manufacturer) call for four 5/16" x 4" through-bolts per bracket with washers and
    # nuts, the bracket top 1/2" below the rim top, and a foot block mid-panel. The bolts
    # cross the PVC fascia and the 2x8 rim; the nuts land on the rim's inside face, which
    # is reachable from the open joist bays below. A solid block between that rim and the
    # first joist at each post is what stops the rim rolling under the R301.5 200 lb load
    # at 42".
    #
    # ``plies=1``: ``_reinforcement_members`` lays ``range(plies - 1)`` sisters, i.e. NONE,
    # and only the blocks. These inherit the deck's ``top_protection`` tape with every other
    # framing top.
    reinforcements=tuple(
        JoistReinforcement(
            at=pt(ft(_gx), ft(_gy)), plies=1, blocking=True,
            source="rim block behind an RL-SG-BALCONY fascia bracket — the four 5/16\" "
                   "through-bolts land in this block so the 2x8 rim cannot roll under the "
                   "guard's 200 lb top load")
        for _gx, _gy in _BALCONY_GUARD_STATIONS),
    outline=_DECK_OUTLINE,
    subfloor=DeckLayer(material_ref="aluminum-deck",
                       thickness=inch(SPEC.balcony_deck_thickness_in)),
    # Butyl here is doing the SECOND job in ``FloorSystem.top_protection``'s docstring more
    # than the first: the plank over these joists is watertight, but it is aluminium laid
    # straight onto copper-treated pine, which AWC DCA6 warns against outright. The tape is
    # the dielectric. That it also keeps the fastener penetrations sealed is the bonus.
    top_protection=_BEAM_TAPE,
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
# **DW-SG-COL, the third, is retired, with its bell.** It would have crossed the joint
# between FT-SG-COL and FT-B-S2 if the two sat at the same elevation 2" apart, but the bell
# bears 2'-6" lower — its top is 1'-10" under FT-B-S2's underside — so the bars would span
# open ground at -9'-4 7/16" with no garden concrete at that height to develop into, and the
# foam block would have one face and no joint. A separated pier does not need a thermal
# break; it IS one. Nothing renumbered: COL was the LAST entry, so W1 keeps SGDW01AAAA and
# E1 keeps SGDW02AAAA and no IFC GlobalId moves — which is the only reason removing an
# ``enumerate``-minted uid was safe to do in place (compare _WALL_FOOTING_UID above, where
# it was not).
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
# pockets. The four corner columns are concrete on concrete and take no base connector.
# ============================================================================
# ONLY THE TWO CENTRE PILLARS TAKE A POST BASE. The four corners are 12" cast concrete
# standing on 12" cast concrete: the joint is a lapped doweled splice made in the pour, not
# a connector, and authoring a base there would bill four standoffs that do not exist and
# claim a pinned joint where the whole redesign turns on a FIXED one.
CONNECTORS = []
for _row, _y, _rise in _PILLAR_ROWS:
    # ABU66SS: the stainless ABU66 standoff base. Both centre pillars now bear through the
    # porch decking onto the framing below (BF2 came north off PT-SG-FCOL's top on
    # 2026-09-03), so both sit at ``_porch_walking_surface`` with a 4"-square plank cut-out
    # under them. It rides at that pillar's own bearing top, so the base draws where the
    # post actually starts.
    #
    # The 1" standoff is what IRC R317.1.4 Exception 1/3 asks for — a wood column on
    # concrete stands on a pedestal projecting 1" above the floor. Note Simpson's
    # counter-instruction ("for higher downloads, pack grout solid under the 1" standoff
    # plate"): do NOT grout these solid. It eliminates the drainage gap that is the
    # whole point of a standoff at an exposed base.
    _bearing_tag, _bearing_top = PILLAR_BEARINGS[f"PT-SG-B{_row}2"]
    CONNECTORS.append(Connector(
        uid=f"SGCB2{_row}AAAA", tag=f"CN-SG-BASE-{_row}2",
        kind=ConnectorKind.POST_BASE,
        position=pt(ft(_cx), ft(_y_bf2 if _row == "F" else _y)),
        elevation=_bearing_top,
        size="ABU66SS", connects=(f"PT-SG-B{_row}2", _bearing_tag)))
# Spent post-base uids, not reused: SGCB1RAAAA / SGCB3RAAAA / SGCB1FAAAA / SGCB3FAAAA, the
# four corner ABU66SS bases retired when those pillars became cast columns.

# THE FOUR CORNER BEAM SEATS. Each 12" column top carries ONE balcony beam end (the west
# and east beams' two ends each), held down by an HGAM10 masonry gusset angle — the same
# part and the same detail the two porch columns already carry at CN-SG-TIE-COL and
# CN-SG-TIE-FCOL. #14 screws to the wood, Titen Turbo to the concrete at >=3" edge distance
# on the 12" round (Simpson's minimum is 1-1/2"), and an EPDM or HDPE isolator between the
# gusset and the stainless standoff under the beam soffit.
#
# ``elevation`` is the beam SOFFIT — the bearing plane the gusset holds down — for the same
# reason the porch ties are authored there: a Connector resolves to a marker box centred on
# its elevation, so authoring the storey datum would draw the gusset floating in the joist
# band above the joint it makes.
_CORNER_SEAT_BEAM = {("R", 1): "BM-SG-BLW", ("F", 1): "BM-SG-BLW",
                     ("R", 3): "BM-SG-BLE", ("F", 3): "BM-SG-BLE"}
_CORNER_SEAT_UID = {("R", 1): "SGCG1RAAAA", ("R", 3): "SGCG3RAAAA",
                    ("F", 1): "SGCG1FAAAA", ("F", 3): "SGCG3FAAAA"}
for _row, _y, _rise in _PILLAR_ROWS:
    for _i in _CORNER_PILLAR_INDICES:
        CONNECTORS.append(Connector(
            uid=_CORNER_SEAT_UID[(_row, _i)], tag=f"CN-SG-SEAT-{_row}{_i}",
            kind=ConnectorKind.POST_CAP,
            position=pt(ft(_PILLAR_X[_i - 1]), ft(_y)),
            elevation=_balcony_beam_soffit, size="HGAM10",
            connects=(_CORNER_SEAT_BEAM[(_row, _i)], f"PT-SG-B{_row}{_i}")))

# THE TWO CENTRE POST CAPS. A 3-1/2" glulam landing on a 6x6 is a CCQ46SDS2.5 (ESR-2604) —
# the column cap sized for a 4x beam on a 6x post, with SDS screws both ways. The corners
# take the HGAM10 above instead because their post is concrete and a wood-to-wood cap has
# nothing to screw into.
#
# These close ``checks/structural/uplift_path``'s post-to-beam leg at the two joints where
# the base is still pinned: the four cast columns get their hold-down from the doweled lap
# in the pour, and these two get it from an authored cap.
_CENTRE_CAP_UID = {"R": "SGCC2RAAAA", "F": "SGCC2FAAAA"}
for _row, _y, _rise in _PILLAR_ROWS:
    CONNECTORS.append(Connector(
        uid=_CENTRE_CAP_UID[_row], tag=f"CN-SG-CAP-{_row}2",
        kind=ConnectorKind.POST_CAP,
        position=pt(ft(_cx), ft(_y_bf2 if _row == "F" else _y)),
        elevation=_balcony_beam_soffit, size="CCQ46SDS2.5",
        connects=("BM-SG-BLC", f"PT-SG-B{_row}2")))
# Porch beam pockets, back and front: a hanger into each side wall + a hurricane tie over
# each column.
#
# A Connector resolves to a marker box centred on its elevation
# (accessories.py::_resolve_connector, +/-3"), so authoring ``elevation=_porch_top`` (the
# storey datum) would draw a back-beam hanger ~11" above the beam it hangs — floating in the
# joist band and poking up through the 1" composite plank, reading as a deck-level object
# rather than the under-deck hardware it is. Each sits at its own joint instead: a hanger on
# the mid-depth of the beam whose end it carries, a tie on the bearing plane it holds down
# (the beam soffit = the column top).
#
# BOTH pairs hang from the bearing stack — neither authors a ``top_elevation``, so the
# resolver drops both a porch-joist depth below the datum and there is one soffit and one
# mid-depth for all four pockets. ``_back_beam_soffit`` / ``_back_beam_mid`` are derived up
# beside ``_back_beam_depth_ft``, because ``_WALL_UNDER_PILLAR`` needs the soffit long
# before this point in the file.
CONNECTORS += [
    # HUCQ410-SDS, not LUS210. Both back-beam ends land in a pocket cast in a
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
    # HGAM10, not H2.5A. An H2.5A is a wood-to-wood tie; library/hardware.py's
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
    # CN-SG-TIE-BR2 (uid J6XRAXQG5T) is retired, with the joist reinforcement above. It held
    # the *front* bearing of PT-SG-BR2's joist line down against the prying
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
# ``_GUARD_PATH`` is hoisted up beside ``_DECK_OUTLINE``, because FS-SG-DECK's rim
# blocking is authored at this guard's own post stations.
# **THE PRODUCT IS WILLIAMS ARCHITECTURAL PRODUCTS, ICC-ES ESR-3485, 42" BLACK** — the
# same guard as RL-SG-PORCH below it, and see that block for why it replaced Trex Signature
# and what the alternate is.
#
# **THIS ONE STAYS FASCIA-MOUNTED, and that is a roofing decision rather than a railing
# one.** FS-SG-DECK's aluminium plank is the porch roof, and since 2026-09-02 it carries NO
# penetrations at all — the two heat-pump stands went to grade. Surface posts would put
# ~36 holes through the only waterproof plane in this structure to save bracket money. The
# brackets through-bolt the PVC fascia and the 2x8 rim per Ultralox's own fascia-mount
# instructions (four 5/16" x 4" bolts, nuts on the rim's inside face, reachable from the
# open bays below), landing in the rim blocking authored in ``FS-SG-DECK.reinforcements``.
# ``type_ref`` stays the library's fascia type for exactly that reason.
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
# leader has to hang *outside* the structure: on the east beam axis (`_deck_x_e - 0.5`) a
# 3" pipe would sit dead centre in two solids at once — the 6x6 pillar PT-SG-BF3 stands on
# that axis, and W-SG-E1's 12" band (x 27.5-28.5) runs the whole drop below it. There is no
# room inboard either — the front rail and the front beam both sit on the trough line, and
# SL-SG-FLOOR stops at the wall's inner face. So the trough oversails the deck edge and the
# pipe drops just clear of the wall's *outer* face, into the 6" slot between that face and
# the raised garden's east return (raised_garden.py stands that leg 3' out, at x = 29.0).
# 1.5" of clearance each side, about what a leader strap wants anyway.
_SG_LEADER_OUTSET = 0.25   # ft outboard of the deck edge, which IS the east wall's face
_SG_GUTTER_OVERSAIL = 0.5  # ft of trough past that edge, to carry the outlet
_SG_LEADER_X = _deck_x_e + _SG_LEADER_OUTSET
_GUTTER_PATH = (pt(ft(_deck_x_w), ft(_y_balcony_front)),
                pt(ft(_deck_x_e + _SG_GUTTER_OVERSAIL), ft(_y_balcony_front)))
# Gutter rim meets the drip flashing's lower edge, so water shedding off the drip lands in
# the trough.
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
# would float above the beam instead.
_back_beam_top = _porch_top - ft(_porch_joist_depth_ft)   # joists bear on top
_front_beam_top = _back_beam_top                          # joists bear on top
_balcony_beam_top = _balcony_beam_soffit + ft(_balcony_beam_depth_ft)  # 9.3958333'

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
# Per-storey exports (spliced into plan/manifest.py).
# ============================================================================
BASEMENT_ELEMENTS = [*NODES, *WALLS, COLUMN, FRONT_COLUMN, *FOOTINGS,
                     *FOOTING_BEDDING, GARDEN_DRYWELL, GARDEN_SLAB, *FROST_WINGS, *DOWELS]
# Every remaining connector is porch hardware at the deck (post bases, hangers, the column
# ties and the four corner beam-seat gussets), so main takes them whole. With the knee
# braces retired there is no second-storey hardware at all.
MAIN_ELEMENTS = [*MAIN_NODES, *BACK_BEAMS, *FRONT_BEAMS, PORCH_JOISTS,
                 PORCH_GUARD, PORCH_GUARD_NE,
                 *CONNECTORS, *PORCH_BEAM_CAPS,
                 HP_PAD, *HP_STAND_LEGS, *HP_STAND_ANCHORS,
                 STAIR_PAD, PORCH_STAIR, *PORCH_STAIR_RAILS,
                 *PORCH_STAIR_THRESHOLD_RAILS]
SECOND_ELEMENTS = [*SECOND_NODES, *BALCONY_BEAMS, *PILLARS,
                   BALCONY_JOISTS, BALCONY_GUARD, BALCONY_FASCIA,
                   BALCONY_GUTTER, BALCONY_LEADER, BALCONY_DRIP, BALCONY_REAR_FLASH,
                   *BALCONY_BEAM_CAPS]

"""Sunken garden / porch / balcony structure — parametric module (WP3.1, redesign).

One freestanding concrete + wood structure immediately south of the house (5" gap from
the house cladding face). It is fully independent of the house — the two share only a
compacted footing bed, with the footings doweled together through a fiberglass-rebar +
40 psi XPS foam thermal break (see FOOTING_BEDDING / the dowel note below).

Vertical stack (project-north frame; +X east, +Y north, +Z up):
- Sunken garden floor at the basement storey (-9'): a U-shaped cantilever-T retaining
  wall (open to the north) on a 42" compacted-aggregate base down to frost.
- The north 8' of that U is the *porch*: two 12" side walls and, on both the north (house)
  and south (front) edges, NO concrete wall. Each of those edges is carried the same way —
  one column at midspan plus two LVL beams hung into the side walls: a 12" sonotube at the
  back, a 16" square cast column at the front. The back line sits a SPEC south-offset
  inside the north edge (so the tube and its bell footing clear the house) and the deck
  cantilevers over it; the front beams are flush-framed, so the joists hang into their
  north face rather than bearing on top. PT 2x8 joists span N-S between the two beam
  lines; composite decking is the walking surface. Porch floor = main (0').
- A metal fascia-mounted guard (RL-SG-PORCH) rails the porch's three open edges, matching
  RL-SG-BALCONY one storey up. The balcony post bases land on the concrete wall tops, and
  at the two centre pillars on the porch decking itself.
- The *balcony* one storey up (second, ~9-10') rides six 6x6 pillars (10' o.c. E-W, 8'
  o.c. N-S; rear row 2" taller for drainage slope) carrying three N-S triple-2x12 beams,
  2x8 joists @ 16" o.c., and aluminum (Wahoo AridDeck-style) decking.

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
    front_column_size_in: float = 16.0  # square cast column on the porch's front edge
    footing_width_in: float = 84.0  # 36" toe + 12" wall + 36" heel
    footing_thickness_in: float = 12.0
    aggregate_bedding_depth_in: float = 42.0
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
    # (clearance for the 40 psi XPS thermal-break block the dowels cross) = 17". Cannot shrink.
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
    # on the porch walls carrying the rest of the frame. 6" clears the 5 1/2" pillar's south
    # face by 3 3/8" — the side cover a square post base wants — and leaves the front-beam
    # pockets (CN-SG-HGR-FW/FE, on `_y_ax_front`) 6" in from the end of the wall instead of
    # right at it.
    side_wall_south_extension_in: float = 6.0
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
    # derived from this string now, so the beam soffit, the pillar tops, the girts and both
    # knee-brace families drop 2" with it. Clear height from the porch deck to the balcony
    # beam soffit goes 8'-7 1/2" -> 8'-5 1/2", and the walking surface at `balcony_level_ft`
    # has not moved.
    #
    # Worth keeping straight while reading this file: the balcony beams sit under a
    # DRY-BELOW surface — `FS-SG-DECK`'s plank is `aluminum-deck`, a Wahoo AridDeck-style
    # watertight system with a drip trough and leader (see the deck's own comment) — while
    # the porch beams sit under GAPPED composite. That asymmetry is the real ESR-1387 5.3
    # exposure story, and it is why the two pairs were never the same problem.
    balcony_beam: str = "3-2x12"
    # The four E-W girts share the beams' depth by construction: both ride ON the pillar
    # tops, so a girt of any other depth would finish its top out of plane with the beam
    # tops the deck joists cross. It followed `balcony_beam` from 2x10 to 2x12 for that
    # reason, not for a span one — a girt carries no joists (see BALCONY_GIRTS).
    balcony_girt: str = "2x12"
    balcony_joist: str = "2x8"
    balcony_joist_oc_in: float = 16.0
    balcony_deck_thickness_in: float = 1.5  # aluminum plank
    joist_cantilever_in: float = 6.0  # deck joist tips overhang the outer beams
    balcony_level_ft: float = 10.0  # second storey


SPEC = SunkenGardenSpec()

_t = SPEC.wall_thickness_in / 12.0
_half = _t / 2.0
_front_half = SPEC.front_column_size_in / 24.0

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
# The porch's front edge: the axis of PT-SG-FCOL and its two flush beams, and the plane the
# balcony's front pillar row, RL-SG-BALCONY and the deck outline all sit on. It used to be
# the 16" arched cross-wall's axis and lands on exactly the same -9.5' — re-derived off the
# column's half-width rather than the retired wall's, so the number is still owned by the
# thing that makes it.
_y_ax_front = _y_in_n - SPEC.porch_clear_depth_ft - _front_half
# Where the porch side walls stop and the free retaining walls take over. NOT the porch's
# front edge: the side walls carry on past it so the balcony's front pillars land on them
# (see ``side_wall_south_extension_in``). Everything else that used to read `_y_ax_front`
# for this — the front column, its beams, the pillar row, the guard, the deck outline —
# still does; only the four wall nodes moved.
_y_ax_mid = _y_ax_front - SPEC.side_wall_south_extension_in / 12.0
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
# Top of the composite boards laid over FS-SG-PORCH: the joist tops are the 0' storey datum
# and the plank sits on them. This is the surface underfoot — what RL-SG-PORCH's 42" is
# measured from, and what the two centre balcony pillars bear on.
_porch_walking_surface = inch(SPEC.porch_deck_thickness_in)
_balcony = ft(SPEC.balcony_level_ft)

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
    # Garden retaining run (to just above grade), the U south of the porch.
    #
    # `lateral_support="unsupported"` is the honest statement of what these three are: free
    # retaining walls, open to the sky along their whole top, holding 9'-9" of fill with
    # nothing bracing the head. That is IRC R404.4's case exactly — a retaining wall not
    # laterally supported at the top holding more than 48" of unbalanced fill — so it wants
    # an engineered design to a 1.5 safety factor against sliding and overturning, and Table
    # R404.1.2(8) (a *basement* wall table, presuming bracing top and bottom) must not be
    # read against them. The check reports them UNKNOWN — engineered, which is the true
    # reading and the one that keeps an invented rebar schedule out of the permit set.
    FoundationWall(uid="SGW105AAAA", tag="W-SG-W2", start_node="N-SG-MW",
                   end_node="N-SG-SW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   lateral_support="unsupported"),
    FoundationWall(uid="SGW106AAAA", tag="W-SG-E2", start_node="N-SG-SE",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   lateral_support="unsupported"),
    FoundationWall(uid="SGW107AAAA", tag="W-SG-S", start_node="N-SG-SW",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   lateral_support="unsupported"),
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
# The porch's front edge — the plane PT-SG-FCOL, its two flush beams and RL-SG-BALCONY all
# sit on, and the north limit anything wrapping this structure runs up to. Published for the
# raised garden's legs, which stop here rather than continuing past the balcony.
PORCH_FRONT_AXIS_Y_FT = _y_ax_front

# Sonotube column (12" round) at midspan, offset south of the deck's north-edge line (see
# ``column_south_offset_in``). The whole back-beam line re-anchors to the same offset —
# nodes, hangers, tie all at ``_y_col`` — so the beams stay collinear and the deck edge
# cantilevers over them to the house gap. Column top lands on the back-beam soffit (one
# beam depth below the 0' porch deck); base at the footing top (-9').
_back_beam_depth_ft = 11.25 / 12.0  # 2x12 actual depth
_y_col = _y_in_n - SPEC.column_south_offset_in / 12.0
_col_footing_width_in = 30.0  # spread footing (bell) under the sonotube
_front_footing_width_in = 36.0  # spread footing under the 16" square front column
COLUMN = Post(uid="SGP001AAAA", tag="PT-SG-COL",
              position=pt(ft(_cx), ft(_y_col)), size="12 round",
              height=ft(SPEC.basement_depth_ft - _back_beam_depth_ft),
              assembly="PIER_CONCRETE_12",
              supported_by="FT-SG-COL")

# The front column: 16" square cast concrete on its own spread footing, replacing the 16"
# arched cross-wall that used to close this edge. Its top is the *soffit* of the two front
# beams, exactly as PT-SG-COL's is the soffit of the back pair — and that is not a style
# choice. A 16"-o.c. joist grid cannot miss a 16" column (the nearest line is at most 8"
# away and the column's half-width is 8"), so a column topping out at the deck datum reads
# as three clashes in ``structural.member_interference``, and neither a CHASE opening nor an
# outline notch can clear them: the resolver never passes opening boxes to
# ``_reinforcement_members``, so PT-SG-BR2's sister plies run straight through anything cut
# here. Stopping at the soffit puts the whole pour below every floor member's underside.
#
# ``size="16.0x16.0"``, never "16x16": the nominal form matches ``_RE_NOMINAL`` in
# resolve/framing/profiles.py, misses LUMBER_ACTUAL and silently resolves to 1.5x5.5. The
# decimal form hits ``_RE_ACTUAL`` first and yields a true 16" square.
#
# Detailing that the model has no field for, so it lives here and in the assembly's
# ``source``: 3/4" chamfer on the four arrises; a >=15 degree wash struck on the top (BIA
# Technical Note 36A) with the beam bearing set on a level non-shrink-grout island; mix
# 4,000-4,500 psi, w/cm <= 0.45, 6.0-6.5% air at 3/4" aggregate (Minn. R. 1309.0402 plus
# ACI 318-19 class F2); broom or float finish, never steel-trowelled (troweling drives the
# entrained air out of exactly the layer that scales — NRMCA CIP 2); silane/siloxane
# repellent. The square earns its keep on connector side cover, not bearing: a 6x6 at
# Fc-parallel 1,000 psi is ~30 kip, long before the concrete governs, but a CBSQ66 wants 3"
# of side cover and an MPB66Z 5", and a 12" round leaves ~2.1" at a square connector's
# corners.
_front_beam_depth_ft = _back_beam_depth_ft  # same member (SPEC.back_beam), same soffit drop
FRONT_COLUMN = Post(uid="SGP002AAAA", tag="PT-SG-FCOL",
                    position=pt(ft(_cx), ft(_y_ax_front)), size="16.0x16.0",
                    height=ft(SPEC.basement_depth_ft - _front_beam_depth_ft),
                    supported_by="FT-SG-FCOL",
                    assembly="SUNKEN_GARDEN_COLUMN_16")

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
FOOTINGS = [
    Footing(uid=_WALL_FOOTING_UID[w.tag], tag=f"FT-{w.tag[2:]}", under=w.tag,
            width=inch(SPEC.footing_width_in),
            depth=inch(_PORCH_FOOTING_THICKNESS_IN.get(w.tag, SPEC.footing_thickness_in)))
    for w in WALLS
]
# Spread footings under the two porch columns. FT-SG-COL keeps SGF199AAAA; the front
# column's is appended after it, so nothing already in the IFC moves.
FOOTINGS.append(
    Footing(uid="SGF199AAAA", tag="FT-SG-COL", under="PT-SG-COL",
            width=inch(_col_footing_width_in), depth=inch(12))
)
FOOTINGS.append(
    Footing(uid="SGF198AAAA", tag="FT-SG-FCOL", under="PT-SG-FCOL",
            width=inch(_front_footing_width_in), depth=inch(12))
)

# All footings bear on a shared 42" compacted-aggregate section. The footings adjacent to
# the house (the two porch side walls + the column, along the north edge) are additionally
# doweled to the house footing with fiberglass rebar across a 40 psi XPS foam block that
# breaks the thermal bridge; ``cast_foam_in_aggregate`` records that foam in the resolved
# geometry / IFC (the dowels themselves are annotation-only — see plans/TODO.md).
_HOUSE_ADJACENT = {"FT-SG-W1", "FT-SG-E1", "FT-SG-COL"}
_BEDDING_UID = {"FT-SG-W1": "SGB002AAAA", "FT-SG-E1": "SGB003AAAA",
                "FT-SG-W2": "SGB004AAAA", "FT-SG-E2": "SGB005AAAA",
                "FT-SG-S": "SGB006AAAA", "FT-SG-COL": "SGB007AAAA",
                "FT-SG-FCOL": "SGB008AAAA"}
FOOTING_BEDDING = [
    FootingBedding(
        uid=_BEDDING_UID[f.tag],
        tag=f"FB-{f.tag[3:]}",
        host_ref=f.tag,
        undercut=inch(SPEC.aggregate_bedding_depth_in),
        cast_foam_in_aggregate=f.tag in _HOUSE_ADJACENT,
        # Same 4" sock-wrapped tile as the house footings (params/foundations.py). Unlike
        # the house's, this tile cannot daylight — the garden floor is 9' down with no grade
        # to run out to — so it discharges to DRW-SG-MAIN instead.
        drain_tile_spec=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    )
    for f in FOOTINGS
]

# The sunken garden's own soakaway — a hole dug to take water and give it to the soil,
# below (not part of) the 42" bearing bed. The garden floor sits 9' down with no downhill
# side, so everything landing here (perimeter tile, the slab itself) has nowhere to go but
# down. The balcony leader used to be on that list; it hangs outside the east wall now and
# discharges to the terrace, so the well is left carrying only the water it cannot avoid. Top of stone sits at the bearing bed's underside so the two stack
# rather than intersect; 6' of fabric-wrapped stone below (unwrapped, this clay silts its
# voids shut in a season). Tagged DRW-, not DW-, because DW- is the dowel prefix and the
# two collided.
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
         bearing_refs=("PT-SG-COL", "W-SG-W1")),
    Beam(uid="SGBM02AAAA", tag="BM-SG-BKE", start_node="N-SGM-COL", end_node="N-SGM-NE",
         size=SPEC.back_beam, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-COL", "W-SG-E1")),
]

# The matching front pair, FLUSH: ``top_elevation`` pins them at the 0' joist datum so the
# porch joists hang into their north face in hangers rather than bearing on top. Flush is
# what lets PT-SG-FCOL stop at the beam soffit and stay clear of the joist band (see the
# column's comment). That authored pin is also what clears the joint in
# ``structural.member_interference``: the check reads exactly this pair — the deck names the
# beam in ``bearing_refs`` *and* the beam pins its own top (``_flush_framed_pairs``).
#
# Both runs end on the side-wall axes, exactly mirroring BM-SG-BKW/BKE: the 6" pocket inside
# the 12" wall band is the modelled hanger detail already in use at the back.
FRONT_BEAMS = [
    Beam(uid="SGBM03AAAA", tag="BM-SG-FRW", start_node="N-SGM-FCOL", end_node="N-SGM-FW",
         size=SPEC.back_beam, top_elevation=_porch_top, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-FCOL", "W-SG-W1")),
    Beam(uid="SGBM04AAAA", tag="BM-SG-FRE", start_node="N-SGM-FCOL", end_node="N-SGM-FE",
         size=SPEC.back_beam, top_elevation=_porch_top, assembly="BEAM_KDAT",
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
# The front corners are flush now, not stepped: W-SG-W1/E1 run 6" past this line at the
# porch top so the balcony's front pillars bear on them, so the +6" curb that used to meet
# the guard here (W-SG-W2/E2 standing proud of the deck, hidden behind 42" of brick before
# the parapet was retired) starts 6" further south and the guard runs out over the side
# walls' own tops.
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
# Six pillars. Four land on concrete wall tops — the rear outer pair on the porch side walls
# at 0'-0", the front outer pair on the retaining walls' +0'-6" (the 6" step at the front
# corners). The two centre pillars miss every wall and stand on the porch decking. Until the
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
# The *resolved* soffit: the pillar-top plane the beams and E-W girts sit on, and the
# plane both brace families rise to.
_balcony_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_joist_depth_ft
                          - _balcony_beam_depth_ft)  # 8.458'
# Same depth as the beams by design (see SPEC.balcony_girt), so the tops finish flush.
_girt_depth_ft = cross_section(SPEC.balcony_girt).depth_m / 0.3048
# Girts ride ON the pillar tops (not bolted to the faces a girt-depth lower), so their
# soffit IS the resolved pillar-top/beam-soffit plane — E-W and N-S knee braces land at the
# same soffit.
_girt_soffit = _balcony_beam_soffit  # 8.458'
_girt_top = _balcony_beam_soffit + ft(_girt_depth_ft)  # 9.396' — flush with the beam tops
_PILLAR_X = (_x_ax_w, _cx, _x_ax_e)
# (row, x index) -> (the concrete wall top that pillar bears on, its elevation). Anything
# not in the map bears on the porch decking instead.
#
# All four outer pillars now bear on the two porch side walls at `_porch_top`. The front
# pair used to be handed to W-SG-W2/E2 at the retaining top, 6" higher, because the wall
# junction sat on their own axis and they overhung it — a pillar half on a wall whose head
# is unbraced (R404.4) and half on one the porch frames into. `side_wall_south_extension_in`
# runs W1/E1 past the pillars so the map can say the true thing; the two front pillars are
# 6" longer for it and their ABU66SS bases came down with them, but the beam soffit they
# rise to has not moved.
_WALL_UNDER_PILLAR = {
    ("R", 1): ("W-SG-W1", _porch_top), ("R", 3): ("W-SG-E1", _porch_top),
    ("F", 1): ("W-SG-W1", _porch_top), ("F", 3): ("W-SG-E1", _porch_top),
}
_PILLAR_ROWS = (("R", _y_in_n, inch(SPEC.rear_pillar_rise_in)), ("F", _y_ax_front, ft(0)))
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

# PT-SG-BR2 (rear-centre) misses every wall and bears on the porch decking, on the
# *cantilevered* tip of the porch joists (they run the column's 17" south-offset past the
# back-beam line). That load path is what the joist reinforcement below answers; read the
# post's authored point back off the loop so the two can't drift apart.
_BR2_AT = next(p for p in PILLARS if p.tag == "PT-SG-BR2").position

SECOND_NODES = [
    Node(uid="SGNB01AAAA", tag="N-SGB-NW", position=pt(ft(_x_ax_w), ft(_y_in_n))),
    Node(uid="SGNB02AAAA", tag="N-SGB-SW", position=pt(ft(_x_ax_w), ft(_y_ax_front))),
    Node(uid="SGNB03AAAA", tag="N-SGB-NC", position=pt(ft(_cx), ft(_y_in_n))),
    Node(uid="SGNB04AAAA", tag="N-SGB-SC", position=pt(ft(_cx), ft(_y_ax_front))),
    Node(uid="SGNB05AAAA", tag="N-SGB-NE", position=pt(ft(_x_ax_e), ft(_y_in_n))),
    Node(uid="SGNB06AAAA", tag="N-SGB-SE", position=pt(ft(_x_ax_e), ft(_y_ax_front))),
]

# Three N-S three-ply 2x12 beams over the west / center / east pillar lines.
BALCONY_BEAMS = [
    Beam(uid="SGBB01AAAA", tag="BM-SG-BLW", start_node="N-SGB-NW", end_node="N-SGB-SW",
         size=SPEC.balcony_beam, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BR1", "PT-SG-BF1")),
    Beam(uid="SGBB02AAAA", tag="BM-SG-BLC", start_node="N-SGB-NC", end_node="N-SGB-SC",
         size=SPEC.balcony_beam, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BR2", "PT-SG-BF2")),
    Beam(uid="SGBB03AAAA", tag="BM-SG-BLE", start_node="N-SGB-NE", end_node="N-SGB-SE",
         size=SPEC.balcony_beam, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BR3", "PT-SG-BF3")),
]

# E-W girts, up ON the pillar tops in the same band as the N-S beams — they carry no
# joists (deck spans E-W onto the beams beside them) and exist purely so the balcony has a
# lateral load path in its second direction: with standoff post bases pinned top and
# bottom, an E-W knee brace needs an E-W member at the pillar tops to reach.
#
# Can't run the full 20' (would pass through the three N-S beams), so each row is two
# segments: front row butts the beam faces directly; rear row's pillars run 2" proud
# (drainage rise), so those segments stop at the pillar faces and a hanger saddle closes
# the rest of the gap to the beam.
#
# Front-row half-width is read off ``SPEC.balcony_beam`` rather than hardcoded — it was a
# literal 1.5" for a long-gone 3"-wide double-2x10, and the 2026-07-31 LVL swap (3 1/2")
# would have driven the girts 1/4" into the beams if left hardcoded
# (`structural.member_interference` is what catches this class of bug).
_beam_face_ft = cross_section(SPEC.balcony_beam).width_m / 2 / 0.3048
_pillar_face_ft = 2.75 / 12.0  # half the 5.5" actual 6x6
GIRT_NODES = [
    Node(uid="SGNG01AAAA", tag="N-SGG-RW1", position=pt(ft(_x_ax_w + _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG02AAAA", tag="N-SGG-RW2", position=pt(ft(_cx - _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG03AAAA", tag="N-SGG-RE1", position=pt(ft(_cx + _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG04AAAA", tag="N-SGG-RE2", position=pt(ft(_x_ax_e - _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG05AAAA", tag="N-SGG-FW1", position=pt(ft(_x_ax_w + _beam_face_ft), ft(_y_ax_front))),
    Node(uid="SGNG06AAAA", tag="N-SGG-FW2", position=pt(ft(_cx - _beam_face_ft), ft(_y_ax_front))),
    Node(uid="SGNG07AAAA", tag="N-SGG-FE1", position=pt(ft(_cx + _beam_face_ft), ft(_y_ax_front))),
    Node(uid="SGNG08AAAA", tag="N-SGG-FE2", position=pt(ft(_x_ax_e - _beam_face_ft), ft(_y_ax_front))),
]
BALCONY_GIRTS = [
    Beam(uid="SGBG01AAAA", tag="BM-SG-GIRT-RW", start_node="N-SGG-RW1", end_node="N-SGG-RW2",
         size=SPEC.balcony_girt, top_elevation=_girt_top, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BR1", "PT-SG-BR2")),
    Beam(uid="SGBG03AAAA", tag="BM-SG-GIRT-RE", start_node="N-SGG-RE1", end_node="N-SGG-RE2",
         size=SPEC.balcony_girt, top_elevation=_girt_top, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BR2", "PT-SG-BR3")),
    Beam(uid="SGBG02AAAA", tag="BM-SG-GIRT-FW", start_node="N-SGG-FW1", end_node="N-SGG-FW2",
         size=SPEC.balcony_girt, top_elevation=_girt_top, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BF1", "PT-SG-BF2")),
    Beam(uid="SGBG04AAAA", tag="BM-SG-GIRT-FE", start_node="N-SGG-FE1", end_node="N-SGG-FE2",
         size=SPEC.balcony_girt, top_elevation=_girt_top, assembly="BEAM_KDAT",
         bearing_refs=("PT-SG-BF2", "PT-SG-BF3")),
]

# Aluminum decking walking surface (framing = 2x8 joists, E-W @ 16" o.c., on the 3 beams).
# The joists cantilever 6" past the outer (west/east) beam axes, so the decking reaches to
# those tips (beam axis ± cantilever), not just to the inner-face line the beams sit inboard of.
_cant_ft = SPEC.joist_cantilever_in / 12.0
_deck_x_w = _x_ax_w - _cant_ft
_deck_x_e = _x_ax_e + _cant_ft
# The plank outline, kept as a constant now that no Slab draws it: TR-SG-FASCIA and the two
# flashings are dimensioned off this deck edge, and so is _FRONT_PATH / _REAR_PATH below.
_DECK_OUTLINE = (pt(ft(_deck_x_w), ft(_y_ax_front)), pt(ft(_deck_x_e), ft(_y_ax_front)),
                 pt(ft(_deck_x_e), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_in_n)))

# --- joist framing under the two decks (rendered members beneath the surface slabs) ---
# Porch: PT 2x8 @ 16" o.c. running N-S between the two beam lines — hung flush in the front
# pair, bearing on the back pair and cantilevering the column's offset past it.
PORCH_JOISTS = FloorSystem(
    uid="SGFS01AAAA", tag="FS-SG-PORCH",
    joists=JoistSpec(member=SPEC.porch_joist, spacing=inch(SPEC.porch_joist_oc_in),
                     direction="y",
                     # South (start) end: no cantilever — the joists hang *in* the front
                     # beams (flush-framed, in hangers), so the deck stops on that axis.
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
    # Three plies (the authored joist + two sisters) and solid blocking under PT-SG-BR2.
    # The pillar lands on the cantilever, so the single 2x8 under it is both over-stressed
    # in bending and free to roll; the cluster runs the joist's whole length back to the
    # front-beam hangers, and the blocking ties it to the lines either side so the load
    # is shared rather than hung on one member. Paired with CN-SG-TIE-BR2 below, which
    # holds the back-span bearing down against the uplift the overhang puts there
    # (~0.45 kip). ``structural.cantilever_point_load`` reads all three.
    reinforcements=(JoistReinforcement(
        at=_BR2_AT, plies=3,
        source="PT-SG-BR2 lands on the porch cantilever — 3-ply PT 2x8 + solid blocking"),),
    outline=_PORCH_OUTLINE,
    # The composite plank *is* this deck's sheet: with SL-SG-PORCH gone the boards are the
    # floor system's own surface layer, which is both what a person stands on (the balcony
    # pillar that misses the masonry railing bears here) and what the sheet-goods take-off
    # bills. This is the deleted slab's one-inch PORCH_DECK_COMPOSITE layer, in place.
    subfloor=DeckLayer(material_ref="composite-deck",
                       thickness=inch(SPEC.porch_deck_thickness_in)),
    # ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
    # 40-psf floor table — see checks/structural/deck.py.
    service="deck",
    source="porch floor — PT 2x8 joists, flush in the front beams -> back beams",
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
# perpendicular extent — that is _x_ax_w - 6" to _x_ax_e + 6" by _y_ax_front to _y_in_n,
# which is the deleted slab's outline term for term.
BALCONY_JOISTS = FloorSystem(
    uid="SGFS02AAAA", tag="FS-SG-DECK",
    joists=JoistSpec(member=SPEC.balcony_joist, spacing=inch(SPEC.balcony_joist_oc_in),
                     direction="x", cantilever=inch(SPEC.joist_cantilever_in),
                     bearing_refs=("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE")),
    outline=_DECK_OUTLINE,
    subfloor=DeckLayer(material_ref="aluminum-deck",
                       thickness=inch(SPEC.balcony_deck_thickness_in)),
    # ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
    # 40-psf floor table — see checks/structural/deck.py.
    service="deck",
    source="balcony — 2x8 joists on three beams, Wahoo aluminium plank laid over them",
)

# ============================================================================
# Fiberglass (GFRP) rebar dowels + 40 psi XPS foam thermal break between the shared
# house/garden footings. The three house-adjacent footings (two porch side walls + the
# sonotube column, along the north edge) pin to the house footing across a 2" XPS block so
# the joint transfers shear without a thermal bridge. Bars at mid-footing (-9.25').
# ============================================================================
_dowel_z = ft(-(SPEC.basement_depth_ft + 0.75) + SPEC.footing_thickness_in / 24.0)
# Side-wall dowels sit on the north-edge line; the column's follow to its bell footing's
# north face, the plane that actually abuts FT-B-S2 (whose south face sits ON the
# north-edge line). At the 17" column offset the bell's north face lands 2" south of it,
# so the bars cross exactly the 2" XPS block — the old 15" offset left no room for the foam.
_col_joint_y = _y_col + _col_footing_width_in / 24.0
_DOWEL_AT = (("W1", _x_ax_w, _y_in_n), ("E1", _x_ax_e, _y_in_n), ("COL", _cx, _col_joint_y))
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
# The back pair hang from the bearing stack — no authored ``top_elevation``, so the resolver
# drops them a porch-joist depth below the datum — while the front pair are flush-framed and
# pinned at the datum itself. Two different soffits, so two derivations.
_porch_joist_depth_ft = cross_section(SPEC.porch_joist).depth_m / 0.3048
_back_beam_soffit = _porch_top - ft(_porch_joist_depth_ft + _back_beam_depth_ft)
_back_beam_mid = _porch_top - ft(_porch_joist_depth_ft + _back_beam_depth_ft / 2.0)
_front_beam_soffit = _porch_top - ft(_front_beam_depth_ft)
_front_beam_mid = _porch_top - ft(_front_beam_depth_ft / 2.0)
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
    Connector(uid="SGCT01AAAA", tag="CN-SG-TIE-COL", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_cx), ft(_y_col)), elevation=_back_beam_soffit, size="H2.5A",
              connects=("BM-SG-BKW", "BM-SG-BKE", "PT-SG-COL")),
    # Uplift tie at the *front* bearing of the sistered joist line. Loading the cantilever
    # tip (PT-SG-BR2) pries the far end of that joist up out of its front-beam hanger;
    # nothing but its own weight holds it there. H2.5A is ~455 lb of uplift against a
    # ~0.45 kip demand — the same part already used over the column, so no new hardware.
    # It shares the reinforced line's x, at the south bearing rather than the north edge.
    # Same datum correction as its neighbours: this one holds a *joist* into a beam, so it
    # rides the joist's mid-depth rather than a beam soffit.
    Connector(uid="J6XRAXQG5T", tag="CN-SG-TIE-BR2", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(_BR2_AT.x, ft(_y_ax_front)),
              elevation=_porch_top - ft(_porch_joist_depth_ft / 2.0), size="H2.5A",
              connects=("FS-SG-PORCH", "BM-SG-FRW", "BM-SG-FRE")),
    # Front-beam pockets, the same concrete-face-mount detail as the back pair above.
    Connector(uid="SGCH03AAAA", tag="CN-SG-HGR-FW", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_ax_front)), elevation=_front_beam_mid,
              size="HUCQ410-SDS", connects=("BM-SG-FRW", "W-SG-W1")),
    Connector(uid="SGCH04AAAA", tag="CN-SG-HGR-FE", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_ax_front)), elevation=_front_beam_mid,
              size="HUCQ410-SDS", connects=("BM-SG-FRE", "W-SG-E1")),
    Connector(uid="SGCT02AAAA", tag="CN-SG-TIE-FCOL", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_cx), ft(_y_ax_front)), elevation=_front_beam_soffit, size="H2.5A",
              connects=("BM-SG-FRW", "BM-SG-FRE", "PT-SG-FCOL")),
]

# ============================================================================
# Knee braces at the balcony pillar tops: 2x6 wood diagonals with a 3' leg, through-bolted,
# Simpson Outdoor Accents APVKB45-6 at each joint.
#
# The four corner pillars are braced in both plan directions; the two centre pillars
# (PT-SG-BR2/BF2) are deliberately left as leaning columns. This is a freestanding deck
# on ABU66SS standoff bases (base + beam bearing both pins), so the braces are the only
# lateral resistance and need both directions — hence the E-W girts, for the "x" braces to
# reach. Bracing the outer bays each direction is enough with the deck as diaphragm; bracing
# the centre pillars too would push thrust into PT-SG-BR2, the one pillar bearing on porch
# decking rather than masonry — the worst place to load laterally. One brace per pillar per
# direction: the second brace at a corner is the E-W one against the girt segment (now at
# the same soffit as the beams) — the old "matched pair per joint" rule billed 12 unbuildable
# braces.
# ============================================================================
# (row, pillar index, N-S lean, E-W lean). Rear posts brace south toward the beam's midspan
# and front posts brace north; the west pillar of each row braces east, the east one west.
_BRACED_CORNERS = (("R", 1, -1, +1), ("R", 3, -1, -1),
                   ("F", 1, +1, +1), ("F", 3, +1, -1))
_BRACE_LEG = ft(3.0)
# The N-S brace uid is the one the retired Connector carried at this same pillar, so the
# brace keeps its IFC GlobalId across this change.
_NS_BRACE_UID = {("R", 1): "SGCK1RAAAA", ("R", 3): "SGCK3RAAAA",
                 ("F", 1): "SGCK1FAAAA", ("F", 3): "SGCK3FAAAA"}
_EW_BRACE_UID = {("R", 1): "SGKX1RAAAA", ("R", 3): "SGKX3RAAAA",
                 ("F", 1): "SGKX1FAAAA", ("F", 3): "SGKX3FAAAA"}
_ROW_Y = {"R": _y_in_n, "F": _y_ax_front}
_NS_BEAM = {1: "BM-SG-BLW", 3: "BM-SG-BLE"}
# The west pillar of each row braces east into its row's west girt segment; the east
# pillar braces west into the east segment.
_EW_GIRT = {("R", 1): "BM-SG-GIRT-RW", ("R", 3): "BM-SG-GIRT-RE",
            ("F", 1): "BM-SG-GIRT-FW", ("F", 3): "BM-SG-GIRT-FE"}
KNEE_BRACES = []
for _row, _i, _ns, _ew in _BRACED_CORNERS:
    _post = f"PT-SG-B{_row}{_i}"
    _at = pt(ft(_PILLAR_X[_i - 1]), ft(_ROW_Y[_row]))
    KNEE_BRACES.append(KneeBrace(
        uid=_NS_BRACE_UID[(_row, _i)], tag=f"KB-SG-{_row}{_i}-NS", position=_at,
        soffit_elevation=_balcony_beam_soffit, leg=_BRACE_LEG, axis="y", direction=_ns,
        member="2x6", post_size=SPEC.pillar_size, assembly="POST_WHITE_PAINT",
        connects=(_post, _NS_BEAM[_i])))
    KNEE_BRACES.append(KneeBrace(
        uid=_EW_BRACE_UID[(_row, _i)], tag=f"KB-SG-{_row}{_i}-EW", position=_at,
        soffit_elevation=_girt_soffit, leg=_BRACE_LEG, axis="x", direction=_ew,
        member="2x6", post_size=SPEC.pillar_size, assembly="POST_WHITE_PAINT",
        connects=(_post, _EW_GIRT[(_row, _i)])))

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
_GUARD_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_ax_front)),
               pt(ft(_deck_x_e), ft(_y_ax_front)), pt(ft(_deck_x_e), ft(_y_in_n)))
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
_FRONT_PATH = (pt(ft(_deck_x_w), ft(_y_ax_front)), pt(ft(_deck_x_e), ft(_y_ax_front)))
# Where the leader hangs is what sets the trough's east end, so it is decided here. The
# leader has to hang *outside* the structure. Its old position (`_deck_x_e - 0.5`, which is
# the east beam axis) put a 3" pipe dead centre in two solids at once: the 6x6 pillar
# PT-SG-BF3 stands on that axis, and W-SG-E1's 12" band (x 27.5-28.5) runs the whole drop
# below it. There is no room inboard either — the front girt and the front beam both sit on
# the trough line, and SL-SG-FLOOR stops at the wall's inner face. So the trough oversails
# the deck edge and the pipe drops just clear of the wall's *outer* face, into the 6" slot
# between that face and the raised garden's east return (raised_garden.py stands that leg
# 3' out, at x = 29.0). 1.5" of clearance each side, about what a leader strap wants anyway.
_SG_LEADER_OUTSET = 0.25   # ft outboard of the deck edge, which IS the east wall's face
_SG_GUTTER_OVERSAIL = 0.5  # ft of trough past that edge, to carry the outlet
_SG_LEADER_X = _deck_x_e + _SG_LEADER_OUTSET
_GUTTER_PATH = (pt(ft(_deck_x_w), ft(_y_ax_front)),
                pt(ft(_deck_x_e + _SG_GUTTER_OVERSAIL), ft(_y_ax_front)))
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
    position=pt(ft(_SG_LEADER_X), ft(_y_ax_front)),
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
# Per-storey exports (spliced into plan/manifest.py).
# ============================================================================
BASEMENT_ELEMENTS = [*NODES, *WALLS, COLUMN, FRONT_COLUMN, *FOOTINGS,
                     *FOOTING_BEDDING, GARDEN_DRYWELL, GARDEN_SLAB, *FROST_WINGS, *DOWELS]
# Every remaining connector is porch hardware at the deck (post bases, hangers, the column
# tie), so main takes them whole; the knee braces are the only second-storey hardware.
MAIN_ELEMENTS = [*MAIN_NODES, *BACK_BEAMS, *FRONT_BEAMS, PORCH_JOISTS, PORCH_GUARD,
                 *CONNECTORS]
SECOND_ELEMENTS = [*SECOND_NODES, *GIRT_NODES, *BALCONY_BEAMS, *BALCONY_GIRTS, *PILLARS,
                   BALCONY_JOISTS, *KNEE_BRACES, BALCONY_GUARD, BALCONY_FASCIA,
                   BALCONY_GUTTER, BALCONY_LEADER, BALCONY_DRIP, BALCONY_REAR_FLASH]

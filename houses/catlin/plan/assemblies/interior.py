# haus: editable
# Catlin assemblies — accent lining, sauna walls and the stair-line bearing walls.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    Substitution,
    inch,
    inside_of,
    layers,
)
from library import (
    STUD_BEARING,
)


# Named face roles the junction solver binds mixed-assembly corners/tees to (#44). The
# ``bearing`` role names the load-bearing layer whose face carries structural continuity
# through a return, so two walls are "continuous" when they publish the same bearing
# material (concrete↔concrete, SPF↔SPF) regardless of the finish/insulation around it —
# never by layer name or index. Variants inherit these from their base assembly.
# Painted gypsum lining (PAINT_FINISH, GWB_LINING) and the bearing interfaces come from the
# library. Colour lives on the `latex-paint` material, not on the Layer (no colour slot): a
# different wall colour is a different Material. `latex-paint-accent` + `ACCENT_GWB_LINING`
# below are that mechanism's accent-wall instance, swapped in per room/wall via
# `Room.wall_lining`/`wall_lining_exceptions` (see RM-S-BED1 in storeys/second.py).

# The accent film. Same name ("paint"), same thickness, same Class III vapour job — only the
# material (and so the colour) differs, which is what keeps an accent wall's Glaser walk and
# lining inset identical to its neighbours'.
_PAINT_FINISH_ACCENT = Layer(name="paint", material_ref="latex-paint-accent",
                             thickness=inch(0.01), function=LayerFunction.FINISH,
                             control={ControlLayer.VAPOR})

# The accent-wall lining: `GWB_LINING` with the accent film in place of the off-white one.
# Same gypsum sheet, same total thickness, so swapping it via `Room.wall_lining` /
# `wall_lining_exceptions` moves no face and changes no clear-floor inset — only the colour.
ACCENT_GWB_LINING = (
    _PAINT_FINISH_ACCENT,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# --- interior ------------------------------------------------------------------
# These partitions carry gypsum in `layers` (not a lining), so paint is authored face by
# face as `paint-a`/`paint-b`. Both faces separate conditioned rooms, so there's no vapour
# drive to control — the paint is here purely for the finish takeoff. Deliberately unpainted
# elsewhere: SAUNA_* (T&G/foil-polyiso is already the vapour/air control, no paint in a
# löyly room), INT_2X6_BRG_EXPOSED_PLY (exposed wood faces, already hardwax-oil
# finished), the masonry/concrete/deck/glazing assemblies (no gypsum face), POST_WHITE_PAINT
# (its own exterior-paint material), and INT_2X4_PARTITION (a tested STC assembly — see
# library/assemblies/ for why it doesn't get layers added). A gypsum face left bare and
# facing a room is still billed paint, by takeoff/derived_paint.py.
# LAYOUT_ORIGIN, INTERIOR. The five bearing assemblies below join the four
# facades on ``layout_origin="line"``. The facades were done first because they are what you
# look at; the centreline is the one that actually matters structurally. `W-M-C1..C5B`,
# `W-S-C1..C4B` and `W-A-C1..C2` are the x=18'-0" line that carries the ridge beam
# continuously to the footings, and until now each of those twelve walls restarted the 16"
# module at its own start node — three storeys, three phases, on the house's primary load
# path. Stacking them is an APA Advanced Framing technique, **not** an IRC mandate: R602.3.3
# is the *bearing-stud* rule (a joist, truss or rafter landing within 5" of a stud, and only
# where both runs are 24" o.c., with three exceptions), and R602.3.2's single-top-plate
# exception turns on rafters/joists centred over studs within 1" — neither says studs stack
# over studs. See ``model/assembly.py``'s note on ``layout_origin``. Worth doing anyway, and
# worth doing here first: a continuous load path is the whole argument for the centreline.
#
# STRUCTURE spec only, unlike the exterior pair: an interior wall has no vertical FURRING
# band to phase-lock to the studs. Both liner bands here are `direction="horizontal"`, and
# `furring._layout_horizontal` takes no phase, so there is nothing else to keep in step.
#
# Not opted in, deliberately: `INT_2X4_PARTITION` and the other non-bearing partitions
# (~46 walls — bearing lines first), and the staggered assemblies, which have a live
# rounding trap in `solver.py`'s face-parity rule that a non-zero phase would wake. See
# plans/TODO.md.


# --- the bedroom half of the centreline -------------------------------------
#
# ** W-M-C1 ONLY, AND IT IS THE SAME BEARING WALL. ** RM-M-BED on the west, RM-M-LIVING on
# the east, and a living room on the other side of a sleeping wall is the one place on the
# x=18'-0" centreline where the plain `INT_2X6_BRG` is not enough. Two additions and
# nothing else: a resilient channel on the BEDROOM face, and the fibreglass this family has
# never carried. `W-M-C2`..`C5B` above and below stay on the plain assembly — this is a
# portion of the line, not a retype of it.
#
# **Still 2x6, still BEARING, still `layout_origin="line"`, and all three are load-bearing
# facts rather than tidiness.** The centreline is what carries `RB-HOUSE` continuously to
# the footings and it is the one grid in the house that must run basement-to-attic on one
# module (see houses/catlin/CLAUDE.md, ONE GRID PER FACADE / the interior round). A channel
# is a FINISH furring screwed to the studs; it carries no vertical load and changes no span,
# so the wall bears exactly as it did. Two second-storey BEARING walls stack on this one.
#
# ** `alignment` IS NOT OPTIONAL, FOR THE SAME REASON INT_2X4_RC's IS NOT. ** Adding the
# channel makes the stack ASYMMETRIC — 0.01 paint + 0.625 gwb + 0.5 channel + 5.5 stud +
# 0.625 gwb + 0.01 paint = 7.27", against the plain wall's symmetric 6.77" — so a default
# centred alignment would put the axis 0.25" off the stud centre and slide every stud on
# this segment off the line. `face("stud-ext", offset=inch(-2.75))` is half the 2x6 stud,
# putting the axis at the stud's own centre: the studs stay at x 213.250-218.750 and the
# axis stays at x=216.000 exactly where the symmetric wall already had it. That matters
# beyond framing — `resolve/stacking.py::_axis_match` works to 1/2" and W-S-C1/W-S-C1B both
# name this wall in `stacks_on`, so an axis that moved could silently drop the stack.
#
# ** WHAT MOVES: the bedroom face, 1/2" west, and nothing else. ** The living-room face
# stays at x=219.385". RM-M-BED loses 1/2" of real width that the model does not record
# (`resolve/rooms.py` polygonises from wall AXES and insets by lining only), so no area,
# glazing or egress verdict changes. `D-M-BED2` is `DT-INT-SWING36-TRIMLESS` — a drywall
# return jamb, no casing — so its reveal simply gets 1/2" deeper on the bedroom side; there
# is no casing to re-cut and nothing else is hosted on either face.
#
# ** NO `stc` IS CLAIMED, DELIBERATELY. ** Same rule the library's presets are held to and
# `INT_2X4_STAGGERED_GWB` already follows here: a rating is a published test result, never
# an estimate, and no test of THIS build — 2x6 studs, channel one side, insulated — could be
# sourced. For scale, the library's `INT_2X4_RC` (2x4, channel one side, fibreglass, one
# 5/8" layer each face) is a tested STC 48 against the uninsulated partition's 34, and a 2x6
# bay is a deeper cavity than that test had, not a shallower one. Treat 48 as the floor of
# what this build is worth and do not write a number into the model without a test.
#
# The batt is FIBREGLASS, per the sweep (see the note above EXT_2X6_SWINBURNE):
# nothing about this cavity is damp, and the acoustic work here is done by the channel's
# decoupling, not by which wool sits behind it.
# A VARIANT of INT_2X6_BRG (#70): the channel and the batt are the whole difference, and
# the substitution says exactly that. The cold face, the paint, the interfaces and the
# bearing stud's layout line track the base.

# INT_2X6_PLUMBING and INT_2X6_STAGGERED_PLUMBING (generic wet-wall partitions, no
# house-specific geometry or owner data) were promoted to library/assemblies/
# (CONTRIBUTING §Promotion flow) and are imported above. The staggered
# variant's non-bearing rationale — same 5.5" pipe cavity as the bearing wall above, but
# decoupled staggered studs so a stack never needs a stud bored on the way through —
# lives with it there now.

# --- the bearing wet wall ---------------------------------------------------------
# W-S-BA-E, W-S-BA-E1B and W-S-BD-N1B, and nothing else. Opening the stair hall to the roof
# (plan/storeys/stair_hall_void.py) made the x=10'-0\" line on the second storey pick up the
# cut ends of FO-A-HALL's attic joists, so those three walls had to be declared BEARING.
#
# ** THE ROLE KWARG ALONE IS NOT ENOUGH — THE ASSEMBLY HAS TO CHANGE WITH IT. ** All three
# were INT_2X6_STAGGERED_PLUMBING, whose own `source=` reads "wet wall, non-bearing", and
# `structural.wet_wall_bearing` (checks/mep/plumbing_dwv.py) FAILs any BEARING wall framed
# with staggered studs: neither face's studs carry the plates' load. The fix is a
# continuous-stud wall, and the cost is the staggered wall's uninterrupted cavity — studs
# get bored where FX-S-BATH1-LAV's stack passes. That is the real, honest price of making
# this line bearing, and it is why the swap is stated here rather than hidden in a kwarg.
#
# WHY NOT PLAIN INT_2X6_PLUMBING, WHICH IS ALREADY IMPORTED. It has no `CavityFill`, so the
# swap would silently strip these walls' 3.5" batt as well as their decoupling — and they
# now separate RM-S-BATH1 from a DOUBLE-HEIGHT hall, which is acoustically worse than what
# they separated before, not better. Five lines of fiberglass buys most of it back. It is
# NOT a substitute for the retype: the staggered LAYOUT is what fails the check, not the
# insulation.
#
# Total thickness is identical either way — 0.01 + 0.625 + 5.5 + 0.625 + 0.01 = 6.77" — so
# NO FACE MOVES, no room area changes, no fixture moves, and FX-S-BATH1-LAV's `wall_ref` is
# untouched. `plan/fixtures.py`'s comment already described this wall AS INT_2X6_PLUMBING;
# the swap makes that true rather than aspirational.
#
# `layout_origin` is deliberately left at its default, unlike INT_2X6_BRG: this is a
# 5.5" cavity a 3" stack runs down, and phase-locking its studs to a global line is the one
# thing that could put a stud where the drain has to go.
# A VARIANT of INT_2X6_BRG (#70): only the stud differs, and it differs in exactly the two
# ways the note above argues for — the batt, and no `layout_origin`.

# --- wet walls that had to grow, 2026-09-20 --------------------------------------
# Three walls in this house carried a 2" vent (2 3/8" outside) or a 3" drain (3 1/2")
# through studs that R602.6 will not let anyone drill that far, and `mep.run_through_stud`
# was suppressed BY RUN in `preferences.toml` for every one of them. The file said what the
# fix was: "the fix is the wall assembly rather than the pipe" and "the honest fixes are a
# 2x8 wet wall or a furred chase". These are those assemblies.

# W-A-STU-W's replacement. INT_2X6_STAGGERED_PLUMBING's 2x4 studs allow a 2.10" bore and the
# studio's two 2" vents wanted 2.38" through eleven of them; continuous 2x6 studs allow
# 3.30". The thickness is identical — 0.01 + 0.625 + 5.5 + 0.625 + 0.01 = 6.77" — so no face
# moves, no fixture moves and no `clear_face` moves. This is the same trade
# INT_2X6_BRG_PLUMBING above made on the second storey, and it keeps the batt for the same
# reason that one did: plain INT_2X6_PLUMBING carries no `CavityFill`, so retyping to it
# would silently strip a bath/studio party wall's 3 1/2" sound batt on top of its
# decoupling. Same 3 1/2" fiberglass the staggered assembly had — like for like, not an
# upgrade, so the `fiberglass` price row's 3 1/2" band still governs.

# W-B-CW's replacement, and the one assembly here that is a real thickening. A 3" drain is
# 3.500" outside and 60% of a 2x6's 5.50" is 3.300" — over by two tenths of an inch, which
# is where a 3" drain sits in a 2x6 in every house. 60% of a 2x8's 7.25" is 4.350", so the
# drain clears with an inch to spare and so does the one 4" ERV radial that crosses this
# wall (DU-B-ERV-R-SAUNA-SUP, 4.00"), which `preferences.toml` had filed as unfixable by
# routing. The furnace room's south face moves ~7/8" north and the corridor's ~7/8" south.
# A VARIANT of INT_2X6_PLUMBING (#70): only the stud depth differs, so the paint/gypsum
# leaves and the bearing interface track the base forever.

# --- energy storage closet -------------------------------------------------------
# The ESS closet's partitions (notes/backup_power.md), an owner decision not a
# code requirement (IRC R327 permits an ESS in an ordinary utility closet; that's why
# `advisory.ess_enclosure`, not the code check, grades it): steel studs (no combustible
# framing around the 14 kWh lithium pack), 5/8" Type X both faces (R302.6-style fire
# membrane, both directions — the fire may start *inside* this closet). No cavity fill on
# purpose: heat should reach AL-B-ESS-HEAT outside, not be insulated away from it.
# The "INT" tag token is load-bearing: `mn_energy._is_interior_assembly` and the IFC
# emitter's IsExternal both key off it to keep this out of the R-21 exterior-wall table.

# The same closet standard on a 6 in. C-stud, for W-B-ESS-W — the one ESS partition a pipe
# crosses. PR-B-SAUNA-VENT's 2" vent (2 3/8" outside) passes king-0-l0 beside D-B-ESS, and
# a 3 1/2" web has nowhere to put that hole under EITHER rule: IRC R602.6 allows 2.10" and
# cold-formed steel's own R603.2.5 allows half the web depth, 1.75". A 6" web allows 3.00"
# under R603.2.5, and R602.6's 2x6 row (which is what `mep.run_through_stud` actually reads,
# since it grades by member size and not by material) allows 3.30".
#
# ** STEEL, STILL. ** The point of this closet is no combustible framing around a 14 kWh
# lithium pack and 5/8" Type X both faces; a variant keeps both and changes only the web.
# Retyping to wood would have thrown the standard away to clear a bore, and would also have
# made this a mixed-material junction against W-B-ESS-S — the `integrity.junction_fallback`
# trap W-B-CW3 was widened to avoid (see plan/storeys/basement.py).
#
# W-B-ESS-S stays 3 1/2": nothing bores it. Only the plates are crossed, and
# `mep.run_through_plate` is suppressed house-wide for a reason `preferences.toml` states
# (no PlateTie vocabulary), not for anything this retype could fix.

# --- sauna ---------------------------------------------------------------------
# The hot side of a sauna is its own wall type, not a lining override on a partition:
# the foil-faced polyiso is the vapour/air control layer and the T&G liner is a
# low-conductivity species chosen so the boards stay touchable at löyly temperatures.
# Per notes/sauna_basement_wall_detail.md.
# **The sauna's ceiling is 7'-6" over the basement slab**, and the liner bands to it so the
# takeoff does not buy basswood, furring and foil-faced polyiso for the space above a
# ceiling. It is one band on the liner itself, not a per-wall extent: the ceiling is one
# plane and every wall in the room meets it at the same elevation.
#
# LINE_BASE, and that is what makes one band enough. The three walls carrying the liner
# start at three different elevations — the curb at the slab, the framed walkout 7 1/4"
# up on top of it, the east wall at the slab — but all three belong to layout lines based
# at the slab (LL-W-A-C1, LL-W-A-S1, LL-W-B-S1 all read -2.7797 m), so 90" above the LINE
# base is the ceiling on all of them. WALL_BASE could not do this: it needed 90" on one
# wall and 82 3/4" on the wall standing on the curb, which is two constants for one plane.
#
# Not WALL_TOP either, and the reason is that the wall top is a STOREY datum, not this
# room's. ``layer_bands.clamp_to_plates`` now stops an unbanded layer at the top plate, so
# a band hung off the top would run the liner to the plate — which on W-B-CS is -13 7/16",
# a full 6" above the sauna's own 7'-6" ceiling at -19 7/16". Six inches of basswood,
# strapping and foil-faced polyiso bought for the space over a ceiling. A band is clamped
# to its host wall (``layer_bands.py``), so the curb — whose top is below the band's —
# simply stays fully lined, and SAUNA_2X4's partitions, which top out at the ceiling, band
# to their own top and change not at all.
#
# PROVISIONAL: if the basement ever goes to a joist ceiling running the full width, the
# liner would run the wall's whole height and this extent should come off.
_SAUNA_CEILING = LayerExtent(
    top=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(90.0)))

_SAUNA_LINER = (
    Layer(name="shiplap-liner", material_ref="catlin-sauna-shiplap", thickness=inch(1.0),
          function=LayerFunction.FINISH, extent=_SAUNA_CEILING),
    Layer(name="liner-furring", material_ref="struct-1-plywood", thickness=inch(0.5),
          function=LayerFunction.FURRING,
          framing=FramingSpec(member="1x4", direction="horizontal"),
          extent=_SAUNA_CEILING),
    Layer(name="foil-polyiso", material_ref="polyiso-foil-thermax", thickness=inch(2.0),
          function=LayerFunction.INSULATION,
          control={ControlLayer.THERMAL, ControlLayer.VAPOR, ControlLayer.AIR},
          extent=_SAUNA_CEILING),
)

# Sauna partition: hot side liner, 2x4 framing, gwb on the cold side.
SAUNA_2X4 = Assembly(
    tag="SAUNA_2X4",
    layers=(
        *_SAUNA_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-cold", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    interfaces=(STUD_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py + notes/sauna_basement_wall_detail.md",
)

# The same sauna partition on 2x6 studs, for W-B-SA-N2 — the sauna's face onto the hall's
# dead end, which PR-B-SAUNA-VENT crosses at 2 3/8". 60% of a 2x4's 3 1/2" is 2.10" and the
# vent was over it; 2x6 allows 3.30". The liner stack is untouched, so the HOT face does not
# move at all — the whole 2" goes to the cold (hall) side, which is where there is room for
# it. The cavity keeps its mineral wool (unspecified thickness, as SAUNA_2X4 has it) because
# this is the wall between a 190 F room and a corridor.
# A VARIANT of SAUNA_2X4 (#70): only the stud differs, so the liner, its ceiling band and the
# bearing interface track the base.
SAUNA_2X6 = Assembly(
    tag="SAUNA_2X6",
    variant_of="SAUNA_2X4",
    substitute=(
        Substitution(
            span=layers("stud", "stud"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6"),
                      cavity=CavityFill(material_ref="mineral-wool")),
            ),
        ),
    ),
    source="catlin-house sauna partition on 2x6 studs: SAUNA_2X4 with a 5.5 in. stud so PR-B-SAUNA-VENT's 2.375 in. bore clears IRC R602.6's 60% of 5.50 in. = 3.30 in.",
)

# W-B-CS, the sauna's east face on the x=18' bearing line — **framed**, where it was 12"
# of cast concrete (``SAUNA_LINER_ON_CONCRETE``, retired with it). Since the sauna rotated
# onto the garden wall (2026-09-05) this wall is the room's east face for y 0'-0"..10'-0"
# only; INT_2X6_BRG carries the same line north of it as W-B-CS3.
#
# basement.py's WALLS header had already written the argument down: this segment "carries
# wood on both faces and COULD go to 8"". The honest reading is that it needs no concrete
# at all. What it carries is FS-M-WEST and FS-M-EAST — two 18' I-joist spans landing on
# the line — and the W-M-C1 -> W-S-C1/C2 -> W-A-C1 -> RB-HOUSE stack down to the footing,
# and a 2x6 bearing wall carries exactly that on every storey above this one. ~4.6 cy of
# ready-mix out. It is the same move W-B-STR/W-B-STR3 made, and the detail is already
# drawn: notes/basement_to_framed_wall_detail.md.
#
# What is paid for it, so it is not discovered later: 12" of concrete between a sauna and
# RM-B-PLAY-N is real acoustic and thermal mass, and the sauna's vapour control moves from
# liner-on-pour to a framed stack. Both are the trade W-B-STR already made.
#
# **"INT" in the tag is load-bearing.** ``_is_interior_assembly`` in mn_energy.py is
# literally ``"INT" in tag.split("_")``, so an interior assembly without the token is
# graded against the R-21 exterior wall row. SAUNA_LINER_ON_CONCRETE carried no such token
# and never needed one — a 12" interior pour is not in that table's population — which is
# exactly the kind of thing that only bites on the day the assembly changes.
#
# A VARIANT of INT_2X6_BRG (#35, #70) rather than a copy of it: this wall IS the centreline
# bearing wall with the sauna's hot side hung on it, and the shared half — the cold face,
# the interfaces, ``layout_origin="line"`` so the studs on the x=18' line stack
# basement-to-attic — tracks the base forever instead of drifting from it. The substitution
# takes the whole room-side leaf (paint, gypsum) and the stud, because the stud here is not
# the base's: it is at a stated 16" o.c., on a gasketed sill, with mineral wool in the bay.
#
# What that changes on the cold face: it is the base's ``gwb-b`` + ``paint-b`` now, where
# it was an unpainted ``gwb-cold``. Same 5/8" of board, plus 0.01" of paint on the
# RM-B-PLAY-N side, which is the paint every other face of that room already has.
SAUNA_LINER_INT_2X6_BRG = Assembly(
    tag="SAUNA_LINER_INT_2X6_BRG",
    variant_of="INT_2X6_BRG",
    substitute=(
        Substitution(
            span=layers("paint-a", "stud"),
            replacement=(
                *_SAUNA_LINER,
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6", spacing=inch(16),
                                          sill_gasket=inch(0.0625),
                                          layout_origin="line"),
                      cavity=CavityFill(material_ref="mineral-wool")),
            ),
        ),
    ),
    source="catlin basement sauna east wall (W-B-CS), framed 2026-08-28: INT_2X6_BRG with SAUNA_2X4's liner in place of its room-side leaf and 2x6 spf bearing studs at 16 in. o.c. on a PT sill, per notes/sauna_basement_wall_detail.md and notes/basement_to_framed_wall_detail.md",
)

# --- the stair-line bearing wall, exposed studs one face and plywood the other --------
# W-M-STRW/W-M-STRW2 (mudroom, main) and W-B-STR3B/W-B-STR2 (basement) are ONE wall: 2x6
# bearing studs at 16" o.c. on a gasketed sill, 3/4" cabinet plywood on the stair face. It
# was authored twice, as MUDROOM_INT_2X6_EXPOSED and STAIRWALL_INT_2X6_BRG, and the only
# difference between the two stacks was the stud species. That is a material, not a wall
# (#70), so the mudroom's exposed Select Structural DF is `Wall.layer_materials` on those
# two walls and the tag is neutral about where it stands.
#
# No default_lining, deliberately (like SAUNA_2X4): the mudroom face is a finished face made
# of the framing itself, not drywall left off. The open 2x6 bays are the coat nooks, so no
# cavity fill either — insulating them would fill the nooks, and both sides are conditioned
# anyway. The plywood is stair finish and screw-anywhere hook backing at once, and it runs
# as one plane from the basement floor to the main-storey ceiling.
#
# "INT" in the tag is load-bearing (see FOUNDATION_WALL_12_INT, INT_2X6_PLUMBING,
# _is_interior_assembly in mn_energy.py) — without it the uninsulated bays would fail as an
# exterior wall against R-21.
#
# `layout_origin="line"`: the main-storey walls stand on the basement ones, so the module
# has to run through the storey split. The exposed studs are the ones you can see from the
# mudroom, so they were always the ones a broken module showed up on.
INT_2X6_BRG_EXPOSED_PLY = Assembly(
    tag="INT_2X6_BRG_EXPOSED_PLY",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", spacing=inch(16),
                                  sill_gasket=inch(0.0625),
                                  layout_origin="line")),
        Layer(name="ply-stair", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
    ),
    interfaces=(STUD_BEARING,),
    source="catlin stair-line bearing wall (W-B-STR2/STR3B basement, W-M-STRW/STRW2 main): 2x6 bearing studs at 16 in. o.c. on a gasketed PT sill, 3/4 in. cabinet-grade plywood on the stair face. The mudroom pair carries exposed Select Structural S4S DF studs (open bays = coat nooks) via Wall.layer_materials; everything below is plain spf, where nothing is exposed to a finished room.",
)

# ** The same wall where it walls the under-stair storage (2026-09-05). ** W-B-STR3's
# whole 5'-6" run is that closet now, and R302.7 asks for gypsum on the ENCLOSED side of an
# enclosed usable space under a stair — which is precisely where this family puts its 3/4"
# cabinet plywood. A layer cannot be added over it: the wall pins `face("stud-ext",
# offset=inch(-2.625))`, so the ply already finishes at x=123 3/8", which IS the flight's
# west edge, and another 1/2" goes into the stringer. So the leaf is SWAPPED, not stacked:
# 5/8" Type X in place of the ply, the stud band held by the alignment, the face retreating
# to 123 1/4" and clearing the stringer by 1/8".
#
# ** What this costs: the exposed-plywood stair face, on this segment only. ** A triangular
# strip of ply — about 32" tall at the landing end, dying out around y=27'-1" where the
# stringer top meets the wall's 8'-0" head — was visible from the upper flight. A `Wall`
# carries one leaf, so protecting the closet below and exposing ply above is not authorable.
# W-B-STR (north of N-B-ESS-SE) and W-B-STR2/W-B-STR3B keep theirs; only the closet's own
# segment changes.
#
# `code.R302_7_under_stair_protection` PASSED before this retype and would pass after
# reverting it — it screens for gypsum on ANY bounding wall, and the closet has four other
# gypsum-lined faces. This is the rule read properly rather than the check satisfied.
STAIRWALL_INT_2X6_BRG_UNDERSTAIR = Assembly(
    tag="STAIRWALL_INT_2X6_BRG_UNDERSTAIR",
    variant_of="INT_2X6_BRG_EXPOSED_PLY",
    substitute=(
        Substitution(
            span=layers("ply-stair", "ply-stair"),
            replacement=(
                Layer(name="gwb-x", material_ref="gwb-x", thickness=inch(0.625),
                      function=LayerFunction.FINISH),
            ),
        ),
    ),
    source="catlin basement stair wall where it encloses the under-stair storage (W-B-STR3), 2026-09-05: INT_2X6_BRG_EXPOSED_PLY with 5/8 in. Type X on the closet face in place of the 3/4 in. stair plywood, per IRC R302.7",
)

# The same wall where it forms RM-B-ESS's west side: one 5/8" Type X leaf ADDED on the
# closet face, which is what `advisory.ess_enclosure` sums for now that the mass of 12" of
# concrete is no longer there to satisfy it. Same `gwb-x` material as INT_ESS_CLOSET_STEEL.
# `inside_of("stud")` on a stack whose first layer IS the stud is a pure insert: nothing is
# replaced, the plywood face is untouched.
STAIRWALL_INT_2X6_BRG_TYPEX = Assembly(
    tag="STAIRWALL_INT_2X6_BRG_TYPEX",
    variant_of="INT_2X6_BRG_EXPOSED_PLY",
    substitute=(
        Substitution(
            span=inside_of("stud"),
            replacement=(
                Layer(name="gwb-x", material_ref="gwb-x", thickness=inch(0.625),
                      function=LayerFunction.FINISH),
            ),
        ),
    ),
    source="catlin basement stair wall (W-B-STR) where it is also RM-B-ESS's west enclosure: INT_2X6_BRG_EXPOSED_PLY with a 5/8 in. Type X leaf on the closet face (notes/backup_power.md)",
)

# ** THE U-STAIR'S WELL PARTITION, GIVEN FACES AND A ROOM SIDE 2026-09-05. **
# `resolve/stairs/common.py` budgets 4 1/2" of cross-run space between the two flights —
# 3 1/2" of stud and 1/2" of gwb each face — and `resolve/stairs/u_split.py` FRAMES IT: two
# 2x4 plates and four studs, slab to arrival deck, generated members on ST-B2M and not an
# authored Wall. What it does not have is faces, a room side, or anything a check can walk,
# which is why the volume under the arriving flight read as open floor for as long as it did.
#
# So W-B-WELL is a Wall that supplies exactly the two things the generated partition lacks,
# and **its structure layer carries NO FramingSpec on purpose**: `framing/solver.py` skips a
# layer whose `framing is None`, so the wall emits no stick and does not double the stair's.
# Author one here and every stud interpenetrates its generated twin —
# `structural.member_interference` said so, twelve times, on the first build.
#
# The thickness IS the specification and must stay locked to `_WELL_PARTITION_THICKNESS_M`:
# INT_2X4_PARTITION is 4 3/4" on its 5/8" leaves and would push 1/8" into each inner
# stringer. 1/2" gwb is already precedented in the library.
#
# Honest about the seam: the generated partition is inset 0.20 m from each flight end
# (u_split.py), so it runs y 26'-8 1/4"..30'-4 1/2" while this wall runs 25'-6"..31'-0".
# About 8" at each end is board with no generated stud behind it. The framer blocks it; the
# model cannot say so, because the engine owns the sticks and the house owns the faces.
STAIRWELL_PARTITION_4H = Assembly(
    tag="STAIRWELL_PARTITION_4H",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
    ),
    interfaces=(STUD_BEARING,),
    source="catlin basement stair-well partition (W-B-WELL), 2026-09-05: 1/2 in. board each face of the 2x4 studs resolve/stairs/u_split.py already generates, so the built thickness is exactly the 4 1/2 in. resolve/stairs/common.py reserves between the flights",
)

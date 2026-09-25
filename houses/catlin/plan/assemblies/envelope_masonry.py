# haus: editable
# Catlin assemblies — the brick veneer, fibre-cement screen and fireplace wythe.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    Layer,
    LayerFunction,
    inch,
)
from .mixes import _WASH_FILM


# Brick veneer over the exposed basement wall (sunken garden excavated against it).
# There is no CMU backer wythe here, because the existing basement concrete
# (waterproofing + 4" XPS already outboard) IS the backer — this wall stands 1-1/2" off
# it on masonry ties. A fictional backer would double-count concrete already modeled by
# W-B-S2/W-B-S3. No `interfaces`: non-bearing.
#
# **One flat field of unglazed buff/brown brick** (2026-09-04). This wythe carried the
# Ishtar scheme from 2026-08-20 — a lapis glazed field with golden-yellow register bands
# over an unglazed brown plinth, five regions sharing one `slot="wythe"` — and before that
# one flat field of glazed-green-brick. The glaze is simply not wanted. What replaces it is
# the plinth's own brick run full height: ordinary ASTM C216 Grade SW face brick, the
# cheapest face that was ever on this wall, stocked by every Twin Cities yard.
#
# The swap also settles a spec conflict the banded scheme only just cleared. BIA Tech Note
# 13 says glazed brick "should not be used in locations where they are likely to be
# saturated"; the Ishtar scheme complied only because the unglazed plinth kept the glaze
# above the splash line. An all-unglazed SW field is unconditionally right for a sunken
# court in Minnesota, which is a rain sump with walls.
#
# `glazed-lapis-brick`, `glazed-gold-brick` and `glazed-green-brick` all stay in the
# catalog, unreferenced, on the convention documented at `glazed-green-brick` — reverting
# any of the three schemes is a material_ref edit, not an archaeology exercise.
#
# No `slot`, no `extent`: with one region there is nothing to co-locate at a shared depth
# and nothing to band, so this is the ordinary case — a plain full-height layer that takes
# the wall's own base and top. (The `slot="wythe"` machinery is intact and still tested; see
# packages/engine/tests/test_emitter_band_parity.py, which now carries its own fixture
# because catlin no longer supplies a live multi-region wall.)
#
# STRUCTURE, not CLADDING: this wythe has nothing behind it in this assembly (the backer is
# a *different wall*), so it has to be the structure layer or integrity.assembly_layers
# finds none. Same precedent as RETAINING_BLOCK_12.
_VENEER_WYTHE = inch(3.625)
BASEMENT_BRICK_VENEER = Assembly(
    tag="BASEMENT_BRICK_VENEER",
    layers=(
        # ** 4" OF OPEN CAVITY, AND THE OTHER 2" IS NOW FOAM ON THE BACKUP WALL. **
        # The 6" between this wall's finished face and the brick is FIXED and always was:
        # W-SG-BRKBM's north face can reach y=-10" and no further (FT-B-S2/S3 hold the 2"
        # isolation joint north of it), and the wythe bears on the beam, so the brick sits
        # at **-10.06..-13.685"** and cannot move north. (This read "-10.05..-13.675" until
        # 2026-09-15: it was struck off a -6.05" node and N-B-BRICK-W/-E are at -6.06".
        # -13.685" is the resolved south face, and it is the line the porch deck stops
        # 1" clear of — see `_y_porch_deck_n` in params/sunken_garden.py.) The only question was ever how to
        # SPLIT that 6", and the answer is 2" of EPS on the backup (see _GARDEN_CURB_CORE
        # and _GARDEN_FRAMED_OUTBOARD, which carry the two bounds that set that 2") plus 4"
        # of drained air here.
        #
        # **Why the split and not 6" of air.** A drainage cavity is not optional — brick is
        # a reservoir cladding and IRC R703.8.4 asks 1" minimum — but 6" of it bought
        # nothing except an unbraced anchor. 4" is well past the 1" minimum and is generous
        # drainage; the 2" that comes out of the cavity does not disappear, it goes onto the
        # wall, where it insulates and braces the inboard third of the anchor.
        #
        # **Do not read the 4-1/2" prescriptive airspace as settled.** 4.0" is inside it,
        # but the anchor still spans ~10" brick-to-stud through 6" of foam and that is past
        # what the tables contemplate. notes/sunken_garden_veneer_beam.md Sec. 5 keeps the
        # tie an engineered item and says why; what changed is that it is now a designable
        # one instead of a 6" unbraced strut.
        #
        # This layer's inboard face IS the node line (the wall aligns on
        # ``face("air-gap-int")``), so N-B-BRICK-W/-E moved to -6.05" with the backup's new
        # face rather than this thickness absorbing the change — the reverse of the
        # 2026-09-04 edit. Either way the brick does not move and the two arched reveals,
        # positioned ``from_node`` along the wall AXIS, stay concentric.
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(4.0),
              function=LayerFunction.AIRGAP),
        # The field: unglazed brown face brick, base to wall top, 8'-5" of it.
        Layer(name="brick", material_ref="brown-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE),
    ),
    source="basement south veneer over the sunken garden (2026-09-04) — one flat field of ordinary unglazed buff/brown face brick, ASTM C216 Grade SW, running modular coursing full height; one 3 5/8\" wythe, 6\" ventilated airgap on the grade beam W-SG-BRKBM (not the house footing toe), TMS 402 engineered ties back to the existing south basement wall (no CMU backer: the basement concrete is the backer). Was the Ishtar scheme (2026-08-20 to 2026-09-04): a glazed-lapis field with glazed-gold register bands over this same brown plinth, banded by Layer.slot; and before that one flat field of glazed-green-brick. All three glazed materials stay in the catalog, so any of the schemes is a material_ref away",
)

# Cost/design alternate for the same walkout face. The panel is represented as the skin's
# structural layer because this is a freestanding cladding element whose backup is a separate
# wall; the installed price row includes horizontal treated girts, panel-edge support,
# corrosion-resistant fasteners, flashings and the drained cavity. Unlike the masonry wythe,
# this light screen needs no gravity grade beam.
BASEMENT_FIBER_CEMENT_SCREEN = Assembly(
    tag="BASEMENT_FIBER_CEMENT_SCREEN",
    layers=(
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(4.0),
              function=LayerFunction.AIRGAP),
        Layer(name="fiber-cement-panel", material_ref="fiber-cement",
              thickness=inch(0.3125), function=LayerFunction.STRUCTURE),
    ),
    source="sunken-garden walkout alternate: exterior fiber-cement panels on horizontal treated girts fastened to verified wall framing, with continuous head/base and opening flashing, drained cavity, supported panel edges, corrosion-resistant fasteners, and manufacturer-required clearance above the wet court",
)

# --- RM-M-LIVING's fireplace surround --------------------------------------------------
#
# One 3 5/8" wythe of face brick standing IN FRONT OF W-M-E1, in the pier between
# WIN-M-LIV-E1 and WIN-M-LIV-E2. Full brick, not slips (owner's call): it starts on
# W-B-E1's pour at -1'-1 7/16", rises 13 7/16" through FS-M-EAST's joist zone and stops at
# 5'-4", where the walnut mantel caps it. notes/east_breast_bearing.md carries the load
# path and the floor-opening framing.
#
# ** ONE LAYER, 3 5/8", AND THE THINNESS IS LOAD-BEARING ON THE CHECKS. **
# `checks/building_science/condensation.py::_nearest_along_each_face` keeps, per room face,
# only the NEAREST candidate wall — so a surround authored as one thick wall aligned to the
# room face would sit close enough to the face to become RM-M-LIVING's east bounding wall
# and DROP W-M-E1 for the whole 36' elevation. The room's east assembly would then be bare
# brick: no vapour retarder, no insulation, and `energy_scope` following it. At 3 5/8" the
# axis lands ~3 11/16" off the finish face against a 1 13/16" half-thickness, so
# `resolve/room_walls.bounding_walls` never picks it up and W-M-E1 survives untouched.
# BASEMENT_BRICK_VENEER above is the existing freestanding-wythe precedent.
#
# STRUCTURE, not CLADDING, for BASEMENT_BRICK_VENEER's reason: the backer is a *different
# wall*, so this layer has to be the structure layer or `integrity.assembly_layers` finds
# none. CLADDING would also drag the surround into the Glaser scope
# (`condensation` screens on `any(layer.function == "cladding")`), and a brick panel
# standing inside a conditioned room is not an envelope assembly to grade.
#
# No MasonrySpec: BASEMENT_BRICK_VENEER carries none either, and the unit takeoff a
# MasonrySpec turns on would replace the $/SF `white-brick` row this house already prices.
# Modular coursing is 2 2/3" (three courses to 8") and every datum in the elevation lands on
# a whole course — see the surround's note in plan/storeys/main.py.
# ** ONE BRICK BLEND HOUSE-WIDE SINCE 2026-09-13: THIS PANEL IS `brown-brick` AND IS WASHED
# WHITE. ** It ordered `white-brick` until then, and the white was never a designed choice —
# the Material was sourced to the retired porch parapet and brief.md says only "white metal
# skin", never white brick. What that second colour cost was real and off-model: a THIRD cube
# of special-order brick against ~21 SF of need (a cube is 480-534 units, 71-79 SF at 6.75
# units/SF), ~53 SF of which is never laid, plus the 1.5-2x special-order premium and its lead
# time, plus a second colour for the mason to lay to a line. Consolidated, the court's 131 SF
# and this panel's 21 SF come off the same two cubes.
#
# ** THE ESTIMATE MOVES $0 ON BRICK AND MUST. ** Both rows price $/SF of FACE LAID, so the cube
# arithmetic above is not in this model at all. Do NOT re-rate the material half down to book
# the saving — that would move the total and misdescribe where the money went. See prices.toml.
#
# ** THE WASH IS THE LAST LAYER, AND THIS IS THE TRAP. ** `resolve/topology.py` places layer 0
# on the `-outward_sign * normal(start->end)` side — the LEFT normal `(-dy, dx)`. These five
# walls sit on their own `open_end` node pairs, find no closed walk, and so take
# `UNRECOVERABLE_WINDING_OUTWARD_SIGN = +1.0`; they are authored S->N, so `normal` points WEST
# and layer 0 lands EAST, against W-M-E1's studs. The room face is therefore the LAST layer.
# Nothing grades this — `advisory.cladding_side_mismatch` inspects CLADDING layers and this
# assembly deliberately has none — so a wash at index 0 would silently paint the BACK of the
# panel at 0 FAIL. `test_masonry_finish.py` pins the wash west of the brick for all five walls,
# and that test is the only guard there is.
#
# ** FINISH, NOT CLADDING, AND FOR THIS ASSEMBLY'S OWN REASON. ** `_PROTECTION_PANEL`'s "must
# stay CLADDING" warning is about the foundation band, where CLADDING is what keeps it in
# Glaser scope. Here the note above says the opposite: CLADDING would drag the surround INTO
# that scope, and a brick panel standing inside a conditioned room is not an envelope assembly
# to grade. Both functions are in `takeoff/envelope.py::_BILLABLE`, so billing is identical.
#
# ** NO ControlLayer.VAPOR. ** A silicate wash is ~25 perms — the opposite of a retarder. See
# `silicate-wash-white` in library/materials/ for the derivation.
#
# Geometry: the stack totals 3 3/4" rather than 3 5/8", so the centred panel drifts 1/16" west
# and the overhang past W-B-E1's pour goes 1/8" -> 3/16". Below every tolerance in
# notes/east_breast_bearing.md, whose numbers all stand (both bricks are 1,920 kg/m3).
_FIREPLACE_WYTHE = inch(3.625)
FIREPLACE_BRICK_WYTHE = Assembly(
    tag="FIREPLACE_BRICK_WYTHE",
    layers=(
        Layer(name="brick", material_ref="brown-brick", thickness=_FIREPLACE_WYTHE,
              function=LayerFunction.STRUCTURE),
        Layer(name="wash", material_ref="silicate-wash-white-brick", thickness=_WASH_FILM,
              function=LayerFunction.FINISH),
    ),
    source="RM-M-LIVING fireplace surround (2026-09-06) — one 3 5/8\" wythe of face brick with grey mortar, ASTM C216, running modular coursing (2 2/3\" per course) off W-B-E1's pour at -1'-1 7/16\" and stopping at 5'-4\" under the walnut mantel. Full brick, not slips (owner's call). Ties back to W-M-E1's studs through the 1 7/8\" behind the wythe; the load path is brick to concrete and is worked in notes/east_breast_bearing.md. Laid BARE in the court's own brown blend 2026-09-13 (one blend house-wide) and washed white by the coating trade on a later arrival — the brick is not a white brick and must not be substituted with one",
)

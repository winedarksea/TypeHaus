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
    Annotation,
    BarSpec,
    Beam,
    Connector,
    ConnectorKind,
    DeckLayer,
    Dowel,
    Downspout,
    DrainTile,
    Drywell,
    face,
    Fascia,
    Flashing,
    FloorOpening,
    FloorOpeningPurpose,
    FloorSystem,
    Footing,
    FootingBedding,
    FoundationWall,
    FrenchDrain,
    from_node,
    ft,
    Gutter,
    inch,
    JoistReinforcement,
    JoistSpec,
    Node,
    Pad,
    PipeRun,
    PipeSystem,
    Post,
    pt,
    PublishedSpan,
    Railing,
    RailingKind,
    ReinforcementSpec,
    Service,
    Slab,
    SleevePenetration,
    Stair,
    TrimKind,
)

from typehaus.resolve.framing.profiles import cross_section
from params.sunken_garden_options import OPTION

# ** THE POUR DOES NOT MOVE WHEN THE WASH IS ADDED, AND THIS IS WHAT HOLDS THAT. **
# `SUNKEN_GARDEN_WALL` carries a 1/8" white mineral silicate wash at layer 0 (the court face).
# Without an alignment the resolver centres the WHOLE stack on the node line, so a 12" pour
# becomes 12 1/8" of stack and the concrete slides 1/16" away from the court — which is not what
# gets built. What gets built is a 12" pour on the grid with a film painted onto its court face.
#
# That 1/16" is not cosmetic. It broke three things at once and only one of them was caught by a
# check: `SP-SG-W1-CD-SPA` fell out of its own host (`integrity.sleeve_in_opening`, a FAIL), and
# the corner columns stopped being flush with the wall faces they stand on while the raised
# garden stopped closing on the court walls — both of those only by test, at 0 FAIL.
#
# `_axis_offset_from_interior` measures the axis from the INTERIOR face outward, and its own
# docstring names this exact case: the offset "is what lets a layer be added to one side of an
# existing wall without moving the layer that actually holds the datum". Interior here is the
# wash's outer face, so the stack reads wash 0..1/8", concrete 1/8"..12 1/8"; the concrete's
# centre is 6 1/8" from the interior face where the default axis is 6 1/16". Hence +1/16" —
# HALF THE WASH — and the pour lands back on 90"..102" exactly as before.
#
# ** IT IS NO LONGER HALF THE WASH, BECAUSE THE RETAINED FACE GREW A STACK (2026-09-14). **
# The rule was always the same and the number was a special case of it:
#
#     offset = (the concrete's centre, measured from the interior face)
#              − (half the whole stack, which is where the default axis lands)
#
# With two layers that was `(w + c/2) − (w + c)/2 = w/2` — half the wash, +1/16". Owner
# decision 5 put a 0.06" waterproofing membrane and a 0.4" drainage composite on the
# OUTBOARD face (`SUNKEN_GARDEN_WALL`, plan/assemblies.py), so the stack is 12.585" and the
# same rule gives `(0.125 + 6) − 12.585/2 = -0.1675"`. The sign FLIPS: there is now more
# outboard of the pour than inboard of it.
#
# ** LEFT AT +1/16" THE POUR WOULD HAVE SLID 0.23" AND NOTHING WOULD HAVE SAID SO. ** The
# last time this stack moved 1/16" it broke three things and a check caught exactly one:
# `SP-SG-W1-CD-SPA` fell out of its host (a FAIL), while the corner columns stopped being
# flush with the wall faces they stand on and the raised garden stopped closing on the court
# walls — both only by test, at 0 FAIL. The faces of these walls are NOT `axis ±
# thickness/2`, and `test_masonry_finish.py::test_court_wash_faces_the_court` plus
# `test_catlin_outdoor_structures.py`'s `_pour_faces` are what hold them.
#
# ** WRITTEN AS THE ARITHMETIC, NOT AS A NUMBER, SO THE NEXT LAYER CANNOT DO THIS AGAIN. **
# The layer thicknesses are transcribed rather than imported because a params module cannot
# import the plan that imports it — the same constraint `SPEC.site_grade_in` lives under —
# and `test_retaining_court` asserts the two agree.
# ** TWO SHIFTS, BECAUSE THE FIVE WALLS ARE NO LONGER ONE ASSEMBLY. ** `W-SG-W1`/`E1` are
# the porch box's side walls, exposed above the yard and carrying wall devices on that face;
# `W-SG-W2`/`E2`/`S` are the free retaining U, buried for their whole height and drained. The
# first pair keeps `SUNKEN_GARDEN_WALL` and the second takes `SUNKEN_GARDEN_WALL_DRAINED`.
#
# ** PUTTING THE DRAINED LAYERS ON ALL FIVE MOVED THE PORCH WALLS' EXPOSED FACE 0.46" AND
# BURIED TWO DEVICES. ** `ED-M-HP2-DISC` and `ED-M-STAIR-LT` hang on W-SG-E1's east face at
# -0'-8", 32" clear of the yard; `test_catlin_contract_m3` caught them buried 0.65" and
# 0.50". That is the same blast radius the note above records for the 1/16" wash, at seven
# times the distance. A face here is NOT `axis ± thickness/2`.
_WASH_FILM_IN = 0.125
_SG_POUR_IN = 12.0
_SG_RETAINED_FACE_IN = 0.06 + 0.4      # waterproofing + drainage composite


def _pour_on_grid_offset(outboard_in: float):
    """The alignment that keeps the 12" pour centred on its own node line.

    One rule, both assemblies, and the number is a consequence of it rather than a literal:

        offset = (the concrete's centre, measured from the INTERIOR face)
                 − (half the whole stack, which is where the default axis lands)

    With nothing outboard that is `+w/2` — half the wash, +1/16", which is what this file
    carried from the day the wash arrived. With 0.46" outboard it is −0.1675": the sign
    FLIPS, because there is now more outboard of the pour than inboard of it.

    ** THE THICKNESSES ARE TRANSCRIBED, NOT IMPORTED. ** A params module cannot import the
    plan that imports it — the same constraint `SPEC.site_grade_in` lives under — and
    `test_retaining_court` asserts the two agree.
    """
    return face("center", offset=inch(
        (_WASH_FILM_IN + _SG_POUR_IN / 2.0)
        - (_WASH_FILM_IN + _SG_POUR_IN + outboard_in) / 2.0))


_WASH_AXIS_SHIFT = _pour_on_grid_offset(0.0)
_DRAINED_AXIS_SHIFT = _pour_on_grid_offset(_SG_RETAINED_FACE_IN)


@dataclass(frozen=True)
class SunkenGardenSpec:
    clear_width_ft: float = 19.0  # E-W between wall inner faces (widened for the 6x6 grid)
    clear_length_ft: float = 26.0  # N-S between wall inner faces
    porch_clear_depth_ft: float = 8.0  # N-S inside the porch box
    gap_to_house_in: float = 5.0  # house cladding face -> north edge (insulation gap)
    # The house's real BELOW-GRADE outboard face, on the south run: 0.06" waterproofing +
    # 2" + 2" XPS + 0.125" acrylic foundation coating over BASEMENT_8's pour
    # (FOUNDATION_WALL_XPS4_OUTBOARD, plan/assemblies.py). Transcribed, not imported, the
    # same way `basement_depth_ft` is. `house_ext_layers_in = 5.0` above is the
    # ABOVE-GRADE stack (polyiso + EPS + furring + cladding) and is why `_y_ax_n` landed
    # on -10" rather than on this plane: the porch deck clears the cladding, but the court
    # wall meets the foundation.
    house_below_grade_face_in: float = 4.185
    # The XPS isolation board between the court's side walls and the house — same 2" and
    # same 40 psi as SG_VENEER_BEAM_14's `xps-break` and the DW-SG-* footing blocks.
    #
    # ** IT IS `THERMAL_BREAK_IN` NOW. ** The 2" was stated three independent times in two
    # files and the 40 psi twice, once outright and once only in prose, because `Layer` has
    # no compressive field. `THERMAL_BREAK_IN` / `THERMAL_BREAK_PSI` below are the one
    # statement of each, and `test_catlin_contract_m3` pins every site against them. This
    # field stays as the name the geometry above reads, and simply takes its value from the
    # published constant — a comment is what let the retaining top's spot elevations rot
    # for two revisions.
    closure_break_in: float = 2.0
    wall_thickness_in: float = OPTION.stem_thickness_in  # side + retaining walls
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
    # This is about BF1/BF3 only — the CORNER pillars. PT-SG-BF2 reads `_y_bf2` and stands
    # on the front beam axis, bearing on the porch's 3-ply joist pack; what that costs is
    # computed by `engineering/post_bearing.py` and worked by hand in
    # notes/centre_pillar_bearing.md, not estimated here.
    # The overhang itself is a weather detail: the balcony gains a 12" drip past the porch
    # floor, so the deck edge sheds clear of the beam and column tops below it.
    balcony_front_overhang_ft: float = 1.0
    # ** THE ONE WIDTH, AND `_RETAINING_FOOTING_WIDTH_IN` READS IT. ** There were two 84s
    # here for two revisions meaning different things — this one retired, and the live
    # strip at 96" — which is exactly the shape a stale number takes. All five court strips
    # are this, centred on the wall axis with a zero offset. See the banner above
    # `_RETAINING` for why the 96" was a fossil of a taller wall.
    footing_width_in: float = OPTION.footing_width_in
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
    # ``integrity.basement_bearing_seat`` checks the two agree. This is the BASEMENT floor
    # plane, and ``SL-SG-FLOOR`` tops out on it again: ``court_step_down_in`` is back to 0,
    # SL-SG-STOOP is retired, and D-B-PATIO takes its single 7 1/4" riser off the court
    # itself. W-B-S2/W-B-S3 are 7 1/4" curbs (``storeys/basement.py``); W-B-S3-FR stands on
    # one at ``base_elevation=inch(-102.1875)`` and carries the door at
    # ``sill_height=inch(0)``.
    #
    # The retained height on W-SG-E2/S/W2 is 9.1198', far past the 48" that sends R404.1.1 to
    # an engineered design, so those three walls stay engineered — PASS with a d/c, not
    # UNKNOWN, since ``engineering/retaining.py`` started grading them.
    basement_depth_ft: float = 109.4375 / 12.0
    slab_thickness_in: float = 3.5
    # ** THE FLOOD STEP IS BACK TO ZERO (2026-09-05), AND THE CURB IS NOW THE WHOLE DAM. **
    # The court surface is FLUSH with the basement floor plane again. Owner's call, taken on
    # a stated trade: the court reads as ONE surface with a single 7 1/4" riser at
    # D-B-PATIO, instead of a 23.7 sf landing perched a riser above 508 sf of floor.
    #
    # **What it costs is half the freeboard, and that is the whole cost.** Water in the
    # court now climbs 7 1/4" to the threshold instead of 14 1/2". Over the court's 494 sf
    # that is 298 cf of ponding rather than 597 cf — against roughly 177 cf of direct
    # 100-year/24-hour rainfall (NOAA Atlas 14, ~4.3" for the Twin Cities), so the margin
    # with the drywell assumed FULLY FAILED goes from about 3.4x to about 1.7x. Still over
    # unity, and the curb is still a dam; but the case to watch is not summer rain, it is
    # **snowmelt onto a frozen court over a frozen grate**, where the drywell contributes
    # nothing by definition. DRW-SG-MAIN's grate is now the single line of defence it was
    # only half of before. Do not let anything raise the court above this plane.
    #
    # The threshold does NOT move: it is W-B-S2/W-B-S3's 7 1/4" curb top at -102 3/16" and
    # always was. What moved is the ground in front of it, from -7 1/4" back up to 0".
    # 7 1/4" is also the largest step R311.3.2 allows without a landing (7 3/4" is
    # `_MAX_NONREQUIRED_STEP_DOWN`), so this plane is not a preference — it is the ONLY
    # court elevation from which one riser reaches this door. Lower it and the step becomes
    # two risers with no landing, which is a hard R311.3 FAIL.
    court_step_down_in: float = 0.0
    # The rim pour is the same 3 1/2" it always was; only its top elevation changed. Named
    # separately from ``slab_thickness_in`` because that one still sets the frost wings'
    # datum arithmetic and the grade beam's top, and the two must be free to differ.
    rim_thickness_in: float = 3.5
    # The open centre's build-up, a USGA putting-green profile (``GARDEN_PUTTING_GREEN``):
    # 12" rootzone / 2" intermediate choker sand / 4" bridging gravel / subgrade fabric.
    #
    # ** 18", not 12", and the extra 6" is all excavated DOWNWARD. ** USGA's cut is 16" when
    # the gravel bridges the rootzone directly and 18-20" when an intermediate layer is used
    # — and one is used here, because no gravel sold in this market bridges against a USGA
    # rootzone. The field's TOP does not move: it stays on the rim's plane, which is what
    # keeps the court one excavation floor and one R311.3 landing.
    #
    # ** The number the next depth change must respect is 3". ** At 18" the field bottoms at
    # -127 7/16"; the grade beam bottoms at -130 7/16". That is 3" of subgrade between them,
    # and the underdrain trench (FD-SG-FIELD) is cut into it. Deepening this profile past
    # 21" undermines the beam.
    field_depth_in: float = 18.0
    porch_top_ft: float = 0.0  # top of the porch concrete walls = porch floor / railing base
    railing_height_ft: float = 3.5  # 42" guard above the porch walking surface
    # ``plan/site.py`` authors ``grade=ft(-2, -10)``. Transcribed rather than imported for
    # the same reason ``basement_depth_ft`` is: this file is a params module and the plan
    # imports it, not the other way round. If site grade ever moves, this moves with it.
    #
    # ** THE GUARD IS IN ``plan/manifest.py``, AND IT DID NOT EXIST UNTIL 2026-09-10. **
    # This comment used to say ``test_retaining_court`` asserted the two agreed. No such
    # assertion was ever written, and the claim stood through two grade moves — a comment
    # that names a guard is not a guard. The real one is the ``assert`` beside the
    # ``SITE_GRADE`` one in the manifest, which is where the plan and the params modules
    # are the same program and can be compared.
    site_grade_in: float = -34.0
    # ** ALL FIVE COURT WALLS TOP OUT ON THE PORCH DATUM. ONE FORM HEIGHT. **
    # 2026-09-10. The retaining run stood at +0'-2" and the two porch walls at 0'-0", a
    # 2-inch jog in the top line at the porch corner that bought nothing: two form heights,
    # two strip-and-sets, and a step a concrete crew has to hit in the middle of a
    # continuous pour. Flush, the five walls are one line.
    #
    # ** IT IS EXPRESSED AGAINST THE DATUM THAT GOVERNS, NOT AS A LITERAL. ** Written as
    # ``0.0`` the two would agree today and drift the first time the porch floor moved.
    # Written this way they are the same number by construction. The terrace name stays
    # separate from the porch-floor name deliberately: they are different ideas that happen
    # to share an elevation, and keeping both makes a future divergence a one-line change
    # rather than an untangling.
    #
    # ** THE 36" IS NOW DERIVED, AND IT WAS RECORDED AS THE WRONG KIND OF CONSTRAINT. **
    # The owner's 2026-09-05 call was that the run stand *around* 36" out of the yard, up
    # to about 48", because a wall this tall may be read as a guard. It was recorded here
    # as a MAXIMUM — ``(site_grade_in + 36) / 12`` — which is the opposite constraint, and
    # under it any further cut in the yard elevation would have pulled the wall tops down
    # with it. The exposure is a RESULT now: see ``RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN``
    # below, which is pinned against the authored yard and reports a band, because local
    # grade is local and the side legs run from 10 to 34 feet out.
    #
    # ** THE APRON DROP FOLLOWED IT, AND THAT IS NOT INCIDENTAL. ** ``raised_garden.py``
    # reads this through ``RETAINING_WALL_TOP_FT`` as its apron TOP and derives its BASE as
    # ``TOP - drop_ft``. Under the old flat-plane model a 3'-0" drop landed the base on
    # -34", site grade exactly. Now that the yard is authored at -3'-4" rather than assumed
    # at the global datum, a 3'-0" drop off a top at 0'-0" would put the base 4" ABOVE the
    # ground it springs from. The drop grew to 4'-0" — eight whole 6" courses — which
    # buries the base course 8". Nothing grades a freestanding wall's base against the
    # ground plane, so this arithmetic is the only thing watching it.
    retaining_top_ft: float = porch_top_ft
    # porch framing
    column_diameter_in: float = 12.0  # sonotube back-beam support
    # Sonotube centre set south of the deck's north-edge line. Centred on that line, the 12"
    # tube would poke 6" into the house cladding and its bell footing would run into
    # FT-B-S2, whose south face lands exactly on this north-edge line. Cannot shrink. The
    # residue is plain clearance between the bell's north face and the house footing's
    # excavation face, and the bell went 30" -> 36" on 2026-09-10, which spends 3" of it:
    # 8" of plan gap becomes 5". Still clear, and the two never meet in section (the bell
    # bears 34" below the house strip) — but the 17" is now doing more work than it was,
    # and a further bell increase reaches the house footing. The column does NOT move: the
    # whole back-beam line,
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
    # retaining wall rather than the porch wall carrying the rest of the frame). The two
    # tops are flush since 2026-09-10, so the pick would be invisible rather than wrong —
    # which is worse, not better, and the 18" extension is what keeps it from arising.
    # It clears the 12" round's south face (y -10'-4") by 8" and leaves the front-beam
    # pockets (CN-SG-HGR-FW/FE, on `_y_ax_front`) well in from the end of the wall instead
    # of right at it. That was 3 3/8" to a 5 1/2" square post base before the corners became
    # cast rounds and the row came north; the 18" is unchanged and now has slack.
    #
    # 18", not 6": the balcony's front pillar row sits 4" south of the porch's front edge
    # (`_y_front_pillar`), and it is a 12" round, so the extension must reach past it or
    # PT-SG-BF1/BF3 would run off the south end of W-SG-W1/E1 onto W-SG-W2/E2 —
    # `lateral_support="unsupported"` R404.4 engineered walls. The extension follows the
    # pillars. W-SG-W2/E2 shorten by 12" and their footings follow.
    #
    # ** ⚠ FLUSH TOPS ARE NOT A LICENCE TO DELETE THESE 18 INCHES. ** Part of the argument
    # for this extension used to be the elevation step: W-SG-W2/E2 stood +0'-6", then
    # +0'-2", above the porch walls, so a pillar straddling the joint sat half on a curb.
    # That step is gone — all five court walls top out on the porch datum since
    # 2026-09-10 — and the surviving reason is the stronger one and is easy to miss:
    # **W-SG-W2/E2 are unbraced at the head and ENGINEERED** (R404.4, `retaining_wall/
    # W-SG-E2`), while W-SG-W1/E1 are braced by the arch and the porch frame. A 12" round
    # column sitting half on one and half on the other is not a bearing this model can
    # honestly describe: the bearing map must pick one wall, and whichever it picks is a
    # lie about where half the load goes. Level tops make the two walls look
    # interchangeable. They are not.
    side_wall_south_extension_in: float = 18.0
    # The porch's two joist ends are not alike, so it cannot share the balcony's symmetric
    # cantilever: the south end hangs flush *in* the front beams (nothing to oversail) and
    # the north end runs the column's south-offset out to the deck edge. This is the *south*
    # value; the north one is that offset (see PORCH_JOISTS).
    porch_joist_cantilever_in: float = 0.0
    # balcony framing
    pillar_size: str = "6x6"
    #: The balcony's drainage FALL, in inches per foot of southward run — the rear
    #: (house-side) pillar row stands this much per foot above the front row. Authored as
    #: a slope rather than as the rise it used to be (``rear_pillar_rise_in = 2.0``,
    #: retired 2026-09-14) because a slope is the thing that is actually specified: the
    #: rise it produces then follows the bearing rows wherever they go, and moving a row
    #: cannot silently change the fall. See ``_rear_pillar_rise_in``.
    balcony_fall_in_per_ft: float = 0.25
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
    # 6x6 in DF-L bearing directly on the porch framing, held down by an MSTA12Z strap on
    # the flush west face plus L50Z angles on the pack faces — leaning columns, tied in by
    # the deck diaphragm. (It was an inverted CCQ4.62-5.50SDS column cap for one day; that
    # part does not fit at either pillar. See the CONNECTORS loop.)
    #
    # 12" is what 2" of cover needs (a 6-5/8" bar circle on a #5 cage inside #3 ties), which
    # is the hundred-year number rather than ACI's 1-1/2" minimum. It is also the same tube
    # as PT-SG-COL and PT-SG-FCOL, so ONE assembly serves all five cast columns. Centred on
    # the 12" wall axis the round is flush with both wall faces: no ledge, no interference.
    #
    # The round spelling is mandatory — see `balcony_beam` above for the same trap.
    corner_column_size: str = "12 round"
    # ** THE GOAL IS LONG-TERM DURABILITY IN F3 + C2, AND THE COATING IS THE MARGIN. ** The
    # mix meets the Code on its own (w/cm <= 0.40, f'c 5,000, 6% +/-1.5 air, 2" cover);
    # galvanizing is the owner's margin on top (2026-09-02, ladder restated 2026-09-12):
    # galvanized either standard — ASTM A767 (galvanize AFTER fabrication, A780 at any field
    # cut, and a WELDED cage leaves A767 for A123) or ASTM A1094 (coated stock, bends after
    # coating) — the fabricator's choice, NAMED ON THE ORDER; black bar at this cover and mix
    # accepted only as a written exception when neither route can be supplied on schedule;
    # epoxy (psi_e 1.2-1.5 lengthens every lap ~50%, and it delaminates) and stainless (4-6x,
    # an austenitic thermal coefficient that fights the concrete) stay REFUSED.
    #
    # Parsed by `engineering/deck_post.py::parse_cage`; the words around the four numbers are
    # for the drawing. As 1.24 in2 on a 113.1 in2 gross is rho 1.10%, just over §10.6.1.1's
    # 1% floor. The word order matters: ``parse_cage`` reads the tie group as "#<n> ties @
    # <spacing>" and an adjective wedged between the bar and the word "ties" makes the whole
    # string unreadable — which it treats as NO STEEL, the conservative reading, so the column
    # silently reports INCOMPLETE instead of failing loudly. The coating rides at the end.
    corner_column_cage: str = ('(4) #5 vertical, #3 ties @ 10" o.c., 2" cover, '
                               'galvanized (ASTM A767 after fabrication, or A1094)')
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
    # ** IT NO LONGER MOVES W-RG-WEST/EAST-BALCONY (2026-09-12). ** It did for nine days:
    # the returns stopped one leader slot short of this edge, so growing the deck shortened
    # them. The returns run to the court wall's outer face now and the slot is gone with
    # them — the deck edge may move in x without touching them, and TR-SG-LEADER-SE's
    # outlet is a shoe over the return's cap rather than a pipe threading a gap.
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
# ============================================================================
# ** THE SIDE WALLS RUN NORTH PAST THE DECK EDGE AND CLOSE THE SLOT (2026-09-05). **
# ============================================================================
# `_y_ax_n` is the PORCH's north line, set by the above-grade cladding face. The side walls
# used to terminate on it, which left a 5.8" x 12" plan slot, ~9 ft tall, between each wall
# end and the basement wall behind it — full of the 6'-4" of backfill W-B-S1/W-B-S4 retain,
# with nothing holding it. It sloughed into the court and carried water with it.
#
# The walls now run north to the house's own below-grade face less the 2" isolation board.
# Written as that arithmetic and not as a literal so the board thickness and the face it
# bears against can never drift apart. -6.175", which is 3.825" more concrete per wall.
#
# **`_y_ax_n`, `_y_in_n` and `_y_out_n` DO NOT MOVE.** The porch deck edge, the back beams,
# the front column and the veneer grade beam all read those, and N-SG-NW/-NE are referenced
# by nothing but W-SG-W1/W-SG-E1. That is what makes this a surgical node move with no porch
# blast radius, and it must stay that way.
#
# Both nodes keep `open_end=True`: the closure must NOT share a node with a house wall. A
# shared node is a junction, and the whole point is that these two structures are separately
# founded and only ever meet through foam — see DW-SG-*-STEM at the bottom of this file.
#
# The hosted footings FT-SG-W1/E1 follow the wall (``Footing.under``), so their north ends
# come with it. FT-B-S1/FT-B-S4 give them the room: those two strips carry a 6" south-toe
# trim since this change (params/foundations._GARDEN_END_TOE_TRIM), which puts their south
# face on -4" and leaves the board its full 2" at footing level as well as at stem level.
# Re-derive both before trusting it: without that trim the house strips reach -10" and the
# extended garden footings would lap them by nearly 4".
_y_wall_end = -(SPEC.house_below_grade_face_in + SPEC.closure_break_in) / 12.0  # -6.175"
# The isolation board's own mid-thickness, which is where a `Dowel` wants its position:
# the foam block resolves CENTRED on it, so this is 1" north of the concrete end face.
_y_closure_break = _y_wall_end + SPEC.closure_break_in / 24.0  # -5.175"
# The veneer grade beam's isolation board, and the axis that places it.
#
# The beam's CONCRETE north face has to land exactly on `_y_ax_n` (-10"), the line
# FT-B-S2/S3's south face used to hold: any further south and W-B-BRICK cannot reach a 6"
# cavity, any further north and the two pours touch. The 2" break therefore sits NORTH of
# -10", in the 2" those footings give up (their `offset` in params/foundations.py), which
# puts the 14" section at -8"..-22" and its axis at -15". Both derived off `_y_ax_n`, so
# trimming the footing and moving the beam can never drift apart.
_break_in = 2.0
_y_ax_brkbm = _y_ax_n - (SPEC.wall_thickness_in - _break_in) / 24.0  # -1.25' = -15"
_brkbm_half = (SPEC.wall_thickness_in + _break_in) / 24.0  # half the 14" section
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

# ============================================================================
# ** THE PORCH DECK'S NORTH EDGE IS `_y_in_n`, OVER THE BRICK (2026-09-16). **
# ============================================================================
# The deck reaches the cladding line so D-M-BALC's 36" R311.3 patch is covered (~89%;
# pulled 1" off the brick face at -14.685" it was 78%, a FAIL). The joists clear
# `W-B-BRICK` VERTICALLY: its top is -8", their soffit -7 1/4". Nothing grades that gap —
# `structural.member_interference` ignores wall layers — so hold the two numbers together.
# Kept as its own name for what stands ON the deck: `_PORCH_OUTLINE`, the guard path and
# its NE stub, and the joists' north cantilever.
_y_porch_deck_n = _y_in_n

# ** THE COURT SURFACE. ** -109 7/16": the basement floor plane less the flood step,
# which is now zero.
# Everything that is walked on, or measured down from, inside this court reads this and not
# ``basement_depth_ft`` — the rim's top, the field's top, the frost wings, the pier bells.
_court_top_in = -(SPEC.basement_depth_ft * 12.0) - SPEC.court_step_down_in  # -109.4375
_court_top = inch(_court_top_in)
# The rim pour's underside, -112 15/16". Since 2026-09-05 it no longer laps the three
# RETAINING toes at all: their tops are the court plane 3 1/2" above this, and
# The five `FO-SG-TOE-*` openings void the rim over all five wall footings, so no two of
# them share a cubic inch: the three retaining strips take W/E/S, and the two porch strips
# take N-W/N-E now that they top out on this plane as well. The net rim polygon's
# intersection with each of those five footprints is 0.000 sf — **asserted since 2026-09-10
# by `test_retaining_court.py::test_the_net_rim_laps_no_footing`**, where it was a hand
# measurement before. It matters because ``structural.concrete_interference`` grades only
# ISOLATED pours and every FT-SG-* carries ``under=``: a lap reads as 0 FAIL and bills
# twice. (PD-SG-COL / PD-SG-FCOL are excluded and always were: those two belled bases top
# out 2'-6" under this slab and their shafts pass through it, so a plan lap is not a lap.)
_rim_underside_in = _court_top_in - SPEC.rim_thickness_in  # -112.9375

# ** THE THREE RETAINING FOOTINGS ARE THE COURT'S WALKING SURFACE (2026-09-05). **
#
# This constant was -118 7/16" for as long as the court existed, which put the strips' TOPS
# 5 1/2" below the rim slab's underside with nothing but fill in between — the design intent
# was always that the footings double as the floor, and 5 1/2" of dirt said otherwise. It is
# now `_court_top` exactly: the strips top out ON the court plane, and `FO-SG-TOE-W/E/S`
# below void the rim over them so the two do not occupy the same 3 1/2".
#
# ** RAISING THE TOP *IS* RAISING THIS CONSTANT, and that is not a stylistic choice. **
# `resolve/envelope.py` sets a wall-hosted footing's `z1 = wall.z0_m` and lets `depth` push
# only `z0` down; `bottom_elevation` is explicitly IGNORED on that branch. There is no way to
# lift a wall-hosted footing's top without lifting the wall bottom above it. So the walls
# shorten, their footing undersides rise 9" from -130 7/16" to -121 7/16", and the
# excavation under the whole footprint falls 9" with them. That saving is the reason this is
# worth doing, and as of the second pass it is taken on all five walls rather than three.
#
# ** WHAT DOES *NOT* FOLLOW IT: the grade beam. ** See `_grade_beam_bottom` below, which is
# now decoupled and held.
_wall_bottom = _court_top
# ** THE TWO PORCH SIDE WALLS NOW BOTTOM OUT HERE TOO (2026-09-05, second pass). **
# They were held back when the three retaining strips rose, on the reading that IRC Table
# R404.1.2(8)'s last published row (10'-0") was a height they had to KEEP. It is a ceiling,
# not a target: a shorter braced wall over less unbalanced fill sits further inside the same
# table, not outside it. Holding them left the whole under-porch stack — wall foot, the two
# 13"-thick footings, and FB-SG-W1/E1's 42" beds — sitting 9" deeper than the identical
# stack 10 feet south of it, for nothing.
#
# So there is no separate porch bottom any more: all five walls in this court bear on
# `_wall_bottom`, their footings are all `SPEC.footing_thickness_in` thick, and the two
# porch strips become the porch bay's walking surface exactly as the three retaining strips
# became the court's — `FO-SG-TOE-N-W/E` below void the rim over them.
#
# What it costs to check, and what was checked: the walls shorten 9'-9 7/16" -> 9'-1 7/16"
# and their unbalanced fill falls with the footing underside, so R404.1.2(8) can only get
# happier (`structural.foundation_unbalanced_fill` still PASSES both). The footing
# undersides rise 9" from -11'-1" to -10'-4", and the frost design at the house edge is
# unchanged in kind: these two were never on cover, they are on ASCE 32 soil replacement
# through FB-SG-W1/E1's 42" of drained NFS stone, and 42" of stone under a raised footing
# is the same 42" of stone.
_porch_top = ft(SPEC.porch_top_ft)  # storey datum = top of joist; the masonry bears here
_ret_top = ft(SPEC.retaining_top_ft)
# Top of wall to underside of footing — the true unbalanced fill on the three free retaining
# walls, because the raised garden's apron holds a terrace against them at their own top
# elevation. See the long note in WALLS below; this is `_ret_top - _wall_bottom` written so it
# cannot drift from either.
# ** DO NOT ADD THE COURT'S STEP-DOWN TO THE UNBALANCED FILL HERE. ** The obvious reading
# — "the court dropped 7 1/4", so H grew 7 1/4"" — is wrong. H is `_ret_top - _wall_bottom`
# and NEITHER end moved: the walls' tops and bottoms are where they always were. The low
# side has never entered the retaining engineering at all (`retaining_basis.py` never reads
# it and `toe_embedment_ft` is hardcoded 0.0), so dropping the court only REMOVES toe
# overburden the model never credited. The design got more conservative, not less; "fixing"
# this constant would silently inflate every moment in
# `notes/sunken_garden_court_free_body.md`.
_ret_unbalanced_fill = _ret_top - _wall_bottom
# W-SG-ARCH, the grade beam closing the court's north end. Its underside is the retaining
# footings' underside, so the excavation has one bottom and the strut engages them; its top
# is the garden-floor underside, -112 15/16". With the court flush again (2026-09-05,
# `court_step_down_in` back to 0) that expression and `_rim_underside_in` are the SAME
# number, so the beam is fully buried and the rim slab bears directly on it — one bearing
# plane, no cut, and the 3 3/4" proud mow strip it briefly was (while the court sat at
# -116 11/16") is gone along with FO-SG-ARCH.
#
# ** IT CANNOT FOLLOW THE COURT DOWN — AND THE REASON CHANGED ON 2026-09-10. ** Drop the
# top to the rim underside and the section is 10 1/4". That USED to fail outright: phi-Pn
# 60,712 lb against Pu 62,051 at the thrust of the day, d/c 1.02. Three height cuts took Pu
# to 49,157 lb, and the 2026-09-14 correction to the strut reaction takes it to 40,145 lb —
# **the 10 1/4" section now passes at d/c 0.66**, so the arithmetic no longer rejects it and
# this comment must not be read as though it does.
#
# What holds the section is the SEQUENCING argument, which did not move:
# `notes/sunken_garden_court_free_body.md` §8 exists because the loop must be closed before
# any backfill, and a strut whose bottom is tied to whatever surface happens to be under it
# is a residue rather than a chosen depth — it gets shaved again the next time the court
# floor or the footing plane moves, which is exactly what these two shallower sections
# were. Plus: 2% is the margin at 8 1/2" on the one member with no redundancy, and the
# whole saving is ~1.1 CY. Read §8's three-reason block before shrinking this beam.
#
# Holding 17 1/2" by lowering the bottom instead lands its 42" bed 7 1/4" below
# `_SG_DRYWELL_TOP`, so the bed and the soakaway swap places. 17 1/2" at this elevation is
# the version of this beam that gets built.
_grade_beam_top = ft(-SPEC.basement_depth_ft) - inch(SPEC.slab_thickness_in)
# ** DECOUPLED FROM `_wall_bottom` AND HELD AT -130 7/16" (2026-09-05). ** It used to read
# `_wall_bottom - footing_thickness`, and when the retaining footings rose 9" to become the
# court's walking surface this expression would have dragged the beam up with them — cutting
# the section from 12" x 17 1/2" to 12" x 8 1/2", Ag 210 in² to ~102 in², and taking the
# strut check from d/c 0.60 to about 1.23, which FAILED at the thrust of that day.
#
# ** IT NO LONGER FAILS, AND THE DECOUPLING IS STILL RIGHT. ** At today's Pu 40,145 lb the
# 8 1/2" section reads d/c 0.80 — it passes comfortably. That is the point of decoupling rather
# than an argument against it: a section arrived at by subtraction between two surfaces
# that both move is not a design, and the margin it happens to land on this revision is not
# a reason to accept it.
#
# W-SG-ARCH is the court's only real strut: `notes/sunken_garden_court_free_body.md` §8
# rejects a slab strut for it in as many words ("the beam needs nothing from it", "laterally
# supported at the top and bottom before backfilling"), and W-SG-W2/E2 cancel their thrusts
# through it. Nothing about the court floor is a reason to shrink it, so the two numbers are
# now separate and this one is written as the arithmetic it always was rather than as a
# reference to a constant that has moved on.
#
# The cost is that the beam is no longer flush with the retaining footings' undersides —
# it sits 9" proud below them — and `test_retaining_court` says so deliberately.
_grade_beam_bottom = ft(-(SPEC.basement_depth_ft + 0.75)) - inch(SPEC.footing_thickness_in)
# W-SG-BRKBM's two faces, and neither is a new number: the top IS W-B-BRICK's authored
# underside and the bottom IS the garden slab's, so the beam exactly fills the void already
# between them. If either moves, this beam has to be re-derived rather than nudged.
_veneer_beam_top = inch(-102.4375)          # = W-B-BRICK.bottom_elevation
# ** THE BOTTOM IS HELD, NOT DERIVED, SINCE THE COURT CAME BACK UP (2026-09-05). ** It used
# to read `_court_top - rim_thickness_in`, which was the garden slab's underside; with the
# court flush again that expression gives -112 15/16" and a 10 1/2" beam. This beam spans
# 19'-0" and ACI 318-19 Table 9.3.1.1 wants L/16 = 14 1/4" minimum depth on a simple span
# before deflection has to be computed, so 10 1/2" is not a shallower beam, it is a
# different design. 17 3/4" is what notes/sunken_garden_veneer_beam.md Sec. 3 actually
# grades. The beam is now buried 7 1/4" below the court rather than forming its north edge.
_veneer_beam_bottom = inch(-120.1875)
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
# ** ONE STRUCT FOR ALL SIX COURT COLUMNS, AND THE CAGE IS A PART. ** The same four bars and
# #3 ties @ 10" the string states. Both spellings are kept: the string prints on the drawing
# and holds the prose the struct cannot (the coating ladder), the struct is what
# `deck_post.cage_for` grades and what `takeoff/reinforcement.py` bills, and
# `integrity.reinforcement_spec_agrees` raises an ERROR if they drift apart. A COUNT and not
# a spacing, because ACI 318-19 §10.6.1.1 bounds a column's steel by 0.01Ag and §10.7.3.1(b)
# sets its floor at four bars within circular ties, and neither question can be asked of a
# spacing.
#
# ** NO PER-BAR COATING HERE, AND THE GALVANIZED TWIN IS GONE (2026-09-12). ** A second spec
# carried `coating=` on both roles, for one reason only: the column assembly had no
# `ConcreteSpec` for a coating to live on. It has one now — `SUNKEN_GARDEN_COLUMN_12` names
# `EXPOSED_MIX`, whose `bar_coating` is what `takeoff/reinforcement.py::_pour_coating` reads
# — so the BOM key is identical and the twin was pure duplication. A per-bar coating is for
# the one case that is real: a dowel lapped into a black-bar pour below.
_CAST_COLUMN_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
    ),
    cover=inch(2.0),
    lap_class="B",
    source='8" cage, (4) #5 + #3 rings @ 10", one of twelve house-wide; notes/sunken_garden_piers.md §4, balcony_moment_columns.md §7',
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
    # durability decision, not a code one, and the reason is class C2.
    #
    # ** THE C2 ARGUMENT IS RIGHT AND THE SENTENCE THAT CARRIED IT WAS WRONG. ** It said
    # these walls take "deicing salt off the drive above". The drive is x 12'..24', y
    # 67'-2 5/8"..105' — north of the GARAGE, on the far side of the house, about 96 feet
    # from this court. Nothing washes off it to here.
    #
    # What is true is worse, and it is why the class does not change: salt reaches this
    # court on boots, on a shovel and on the dog, from the north walk and the entry tiers —
    # and once here it **cannot leave**. There is no grade to daylight. The only outlet is
    # DRW-SG-MAIN, a soakaway inside the excavation, so every chloride that arrives stays
    # in the stone against these faces and cycles through them with each thaw. A drive
    # sheds its salt to a ditch; a sunken court concentrates it.
    #
    # Cover is the only term in the whole chloride problem that buys DISTANCE; every other
    # lever (w/cm 0.40, the galvanizing, the fly ash) buys time.
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
    # `_y_wall_end`, NOT `_y_ax_n`: these two run north past the porch's deck line to close
    # the slot against the house across the 2" board. See `_y_wall_end` above for why they
    # stay `open_end` and why no porch geometry follows them.
    Node(uid="SGN001AAAA", tag="N-SG-NW", position=pt(ft(_x_ax_w), ft(_y_wall_end)),
         open_end=True),  # north wall removed — side wall terminates here (freestanding)
    Node(uid="SGN002AAAA", tag="N-SG-NE", position=pt(ft(_x_ax_e), ft(_y_wall_end)),
         open_end=True),
    Node(uid="SGN003AAAA", tag="N-SG-MW", position=pt(ft(_x_ax_w), ft(_y_ax_mid))),
    Node(uid="SGN004AAAA", tag="N-SG-ME", position=pt(ft(_x_ax_e), ft(_y_ax_mid))),
    Node(uid="SGN005AAAA", tag="N-SG-SW", position=pt(ft(_x_ax_w), ft(_y_ax_s))),
    Node(uid="SGN006AAAA", tag="N-SG-SE", position=pt(ft(_x_ax_e), ft(_y_ax_s))),
    # The veneer grade beam's ends, landing on the two side-wall AXES so the beam is cast
    # into W-SG-W1 and W-SG-E1 rather than butted against them. Clear span is therefore the
    # court's own 19'-0", not the 20'-0" axis distance.
    # `open_end` for the same reason N-SG-NW/-NE carry it: the beam dies INTO the side
    # walls 6" past their inside faces rather than meeting them at a shared node, so this
    # run terminates here and closes no loop.
    Node(uid="SGN007AAAA", tag="N-SG-BMW", position=pt(ft(_x_ax_w), ft(_y_ax_brkbm)),
         open_end=True),
    Node(uid="SGN008AAAA", tag="N-SG-BME", position=pt(ft(_x_ax_e), ft(_y_ax_brkbm)),
         open_end=True),
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
    # These walls resolve 9'-1 7/16" tall over 6.3' of unbalanced fill, which the check
    # answers on Table R404.1.2(8)'s 10' wall x 7' backfill row — the last one it publishes,
    # reached from BELOW. R404.1.3's no-seal prescriptive path gets there and
    # `structural.foundation_unbalanced_fill` PASSES both walls.
    #
    # ** THE 10'-0" WAS A CEILING, NOT A TARGET, AND HOLDING THEM AT IT COST 9". ** They
    # stood at 9'-9 7/16" on a 13"-thick footing for one day, expressly to keep the table's
    # last row and the footing undersides where the frost design had left them. Both
    # arguments were weaker than they looked: a SHORTER wall over LESS fill sits further
    # inside the same row, and the frost answer at this edge was never cover — it is ASCE 32
    # soil replacement through FB-SG-W1/E1's 42" of drained NFS stone, which is the same 42"
    # of stone whatever elevation the footing above it starts at. Meanwhile the whole
    # under-porch excavation — wall foot, footing, and a 42" bed — sat 9" deeper than the
    # identical stack ten feet south. It does not any more.
    #
    # `#6 @ 38" o.c.` is kept, and it is now MORE than the table asks: at 10' x 8' backfill
    # a 12" wall of 4,000 psi concrete needs no vertical reinforcement at all under footnote
    # l, and the check says so in its PASS. The schedule stays because it was carried up from
    # the same row, because these two walls also carry the porch's four beam pockets, and
    # because taking steel out of a retaining wall to match a table minimum is the engineer's
    # call, not this file's.
    # ** ONE POUR, TWO SCHEDULES. ** The four side-wall segments are TWO continuous pours
    # on two axes, x = 8.0 (W1+W2) and x = 28.0 (E1+E2): same 12" SUNKEN_GARDEN_WALL
    # section, same top (the porch datum) and same bottom, cast at one form height in
    # placement 2 (`AN-SG-PLACEMENTS`). Each is split into two elements at `N-SG-MW` /
    # `N-SG-ME` only because the restraint condition changes there — braced top-and-bottom
    # north of it, base-restrained and R404.4 engineered south of it.
    #
    # The buildability consequence, and the thing a crew gets wrong: **the vertical bar
    # spacing changes mid-pour at y = -11'-0" (`_y_ax_mid`) — #6 @ 38" north of it,
    # #6 @ 10" on the retained face south of it, in one form.**
    FoundationWall(uid="SGW103AAAA", tag="W-SG-W1", start_node="N-SG-NW",
                   end_node="N-SG-MW", assembly="SUNKEN_GARDEN_WALL", alignment=_WASH_AXIS_SHIFT,
                   top_elevation=_porch_top, bottom_elevation=_wall_bottom,
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#6 @ 38" o.c.',
                   reinforcement=_BRACED_STEM_STEEL),
    # East wall runs ME→NE (south→north), opposite the west wall, so both side walls wind
    # the same way around the garden.
    #
    # ** THAT CONSISTENCY IS NOW LOAD-BEARING, BECAUSE THESE WALLS TOOK A SECOND LAYER
    # (2026-09-13). ** SUNKEN_GARDEN_WALL carries a white mineral silicate wash at layer 0 and
    # layer 0 must land on the COURT face, so the component's winding is no longer latent.
    #
    # The court's winding (-1, `court-low`) comes from the closed walk ME→SE→SW→MW→ME, whose
    # MW–ME leg is the cast grade beam W-SG-ARCH (GRADE_BEAMS below): `resolve/orientation`
    # counts a concrete Beam between wall nodes as a loop edge. Delete or move that beam and
    # the sign falls to +1, putting the wash on the buried face of all five walls at 0 FAIL.
    # `test_masonry_finish::test_court_wash_faces_the_court` pins it.
    FoundationWall(uid="SGW104AAAA", tag="W-SG-E1", start_node="N-SG-ME",
                   end_node="N-SG-NE", assembly="SUNKEN_GARDEN_WALL", alignment=_WASH_AXIS_SHIFT,
                   top_elevation=_porch_top, bottom_elevation=_wall_bottom,
                   lateral_support="top_and_bottom",
                   vertical_reinforcement='#6 @ 38" o.c.',
                   reinforcement=_BRACED_STEM_STEEL),
    # ============================================================================
    # W-SG-BRKBM — the SECOND buried grade beam, and the whole answer to the veneer's
    # thermal bridge.
    # ============================================================================
    # W-B-BRICK used to stand on FT-B-BRICK, a 10"x5" plinth cast on FT-B-S2/S3's own
    # projecting toe. That put 129 SF of brick — exposed on BOTH faces in an open court, so
    # running at outdoor temperature all winter — in series with the house footing through
    # 2" of washed stone. The intended break was `cast_foam_in_aggregate`, a bool that emits
    # no solid and bills nothing; the take-off ordered the stone and not the foam. The path
    # was ~R-0.4 over 16.0 SF where R-10 was meant, into a footing whose underside is level
    # with the court floor and whose frost protection is the R403.3 wings.
    #
    # **Why a beam and not a better bed.** A strip bearing on soil cannot be had: the wythe
    # sits inside FT-B-S2/S3's 10" toe, and a separate pour bottoming on the wing plane has
    # to stay outside the 45 deg line off their bearing edge — y = -12.76" — which pushes the
    # brick to -15.95" and opens an 11.9" slot between it and the house. A beam SPANNING to
    # W-SG-W1 and W-SG-E1 needs no soil bearing at all, so that constraint simply does not
    # apply, and the wythe lands at -10.05" for a 6" cavity.
    #
    # **It reinforces nothing, and that is worth saying.** The obvious hope is that a north
    # strut helps the side walls. It does not: W-SG-W1/E1 are already restrained top and
    # bottom (porch beams pocketed in HUCQ410-SDS hangers, deck diaphragm, garden slab at
    # their feet) and PASS `structural.foundation_unbalanced_fill` on the last row of
    # IRC Table R404.1.2(8). This beam earns its 1.0 cy on the thermal argument alone.
    #
    # **17 3/4" deep, between two surfaces that were already there**: its top IS W-B-BRICK's
    # underside (-8'-6 7/16") and its bottom IS the garden slab's (-10'-0 3/16"), so it drops
    # into the void the court already had. The wings stay CONTINUOUS underneath — the beam
    # bears on the side walls at its ends, not on the compressible foam, which is the same
    # care W-SG-ARCH takes for the same reason.
    #
    # **The wythe sits off centre on purpose.** Brick at -10.05..-13.675" against a beam
    # centred at -15" is 4.1" of eccentricity, ~162 ft-lb/ft of torsion over the span. The
    # section is cast into both side walls and the garden slab bears on its south face, so
    # it is restrained at both ends and along its length; see
    # notes/sunken_garden_veneer_beam.md. Centring the brick instead would have cost the 6".
    #
    # No Footing, same as W-SG-ARCH and for the same reason — it spans, so a strip under it
    # would be concrete spent on nothing, and a `FT-SG-BRKBM` solid would land inside the
    # excavation and reopen the frost question ASCE 32 closes.
    # ** WHICH FACE THE BOARD LANDS ON IS NOT OBVIOUS, AND IT IS THE WHOLE POINT. ** This
    # beam is its own open wall-graph chain (both ends `open_end`), so
    # `resolve/orientation.py` hands it the fallback outward sign rather than a winding's,
    # and that sign plus the assembly's layer ORDER is what decides whether the 2"
    # `xps-break` builds north or south. Get either wrong and the concrete lands hard against
    # FT-B-S2/S3 — the exact contact this beam exists to remove — at 0 FAIL, because nothing
    # grades a thermal break for continuity. The face is pinned by
    # `test_the_veneer_beam_isolates_the_house_footing`; do not trust the sign.
    FoundationWall(uid="SGW108AAAA", tag="W-SG-BRKBM", start_node="N-SG-BMW",
                   end_node="N-SG-BME", assembly="SG_VENEER_BEAM_14",
                   top_elevation=_veneer_beam_top, bottom_elevation=_veneer_beam_bottom,
                   unbalanced_fill=inch(0),
                   lateral_support="top_and_bottom"),
    # Garden retaining run (to just above grade), the U south of the porch.
    #
    # ** THE FILL AGAINST THESE THREE IS AUTHORED. ** Left derived,
    # `structural.foundation_unbalanced_fill` measures from the single global `Site.grade`
    # (-2'-10") down to the footing and reports the fill below that plane — wrong here,
    # because `params/raised_garden.py` builds an SRW apron whose `TOP =
    # ft(RETAINING_WALL_TOP_FT)` — level with these walls' own tops at **0'-0"**, the porch
    # datum, which is **40"** over the authored yard at -3'-4" — standing 3'-0" out from
    # their outer faces and
    # holding a terrace of soil at that level *against them*. Grade is a plane, and a plane
    # cannot describe a terrace sitting 3'-0" above it. The real retained height is the
    # wall's full top-to-footing dimension, **9.1198'** — 10.37' until 2026-09-05, when these
    # three footings rose 9" to become the court's walking surface (9.62') and the run was
    # then capped at 40" above the authored yard, taking the top to 0'-0".
    #
    # It is deliberately written as the same arithmetic `_wall_bottom` and `_ret_top` are
    # built from rather than as a literal, so it moves with either — and both ends HAVE
    # moved: the bottom rose 9" when the footings became the court floor, and the top fell
    # when the run was capped out of the yard. Stem 10.37' -> 9.62' -> **9.1198'**;
    # engineered retained height H 11.37' -> 10.62' -> **10.1198'**. (9.29'/10.29' stood in
    # these lines until 2026-09-14 and had never been the resolved value; the live pair is
    # `_ret_top - _wall_bottom` and that plus the 12" strip. Do not quote either from
    # memory — `haus engineering houses/catlin --item retaining_wall/W-SG-E2` prints them.)
    # There is no separate
    # "terrace top" number and there must not be: `SPEC.retaining_top_ft` IS the terrace top,
    # because `raised_garden.py` reads that very constant to place its own apron. A second
    # copy would be exactly the divergence the "publish, do not re-derive" note further down
    # this file exists to prevent.
    #
    # Both 7.0' and 9.1198' are far past the 48" at which R404.1.1 sends a wall to an
    # engineered design, so the correction cannot flip the verdict — all three stay UNKNOWN,
    # engineered — but it changes what the engineer is asked to design for by nearly half
    # again, which is the whole point. `notes/sunken_garden_retaining_screening.md` works
    # the consequences.
    #
    # ** `lateral_support="base"`, NOT "unsupported". ** These three are free retaining
    # walls, open to the sky along their whole top, holding 9'-7" of fill with nothing
    # bracing the head — IRC R404.4's case exactly. `"base"` routes to the same R404.4
    # engineered handoff (`checks/structural/foundation.py::_grade_one`); Table R404.1.2(8),
    # a *basement* wall table whose footnote g presumes bracing top AND bottom, must not be
    # read against them.
    #
    # Graded as three ISOLATED cantilevers, each resisting by its own base friction, they
    # reach FS 0.73 against 1.5 — the arithmetic of a wall nobody built. W-SG-W2
    # (axis x=8'-0") and W-SG-E2 (axis x=28'-0") face each other across a 19'-0" court, same
    # height, same 16'-4" length, cast into W-SG-S at their south ends through monolithic
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
    # `retaining_system._verify` goes and checks that W-SG-ARCH is a real cast member, on
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
                   end_node="N-SG-SW", assembly="SUNKEN_GARDEN_WALL_DRAINED",
                   alignment=_DRAINED_AXIS_SHIFT,
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   unbalanced_fill=_ret_unbalanced_fill,
                   vertical_reinforcement=_RET_REBAR,
                   reinforcement=_RET_STEM_STEEL,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
    FoundationWall(uid="SGW106AAAA", tag="W-SG-E2", start_node="N-SG-SE",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL_DRAINED",
                   alignment=_DRAINED_AXIS_SHIFT,
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   unbalanced_fill=_ret_unbalanced_fill,
                   vertical_reinforcement=_RET_REBAR,
                   reinforcement=_RET_STEM_STEEL,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
    FoundationWall(uid="SGW107AAAA", tag="W-SG-S", start_node="N-SG-SW",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL_DRAINED",
                   alignment=_DRAINED_AXIS_SHIFT,
                   unbalanced_fill=_ret_unbalanced_fill,
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom,
                   vertical_reinforcement=_RET_REBAR,
                   reinforcement=_RET_STEM_STEEL,
                   lateral_support="base", base_restraint_ref="W-SG-ARCH"),
]

# W-SG-ARCH: a BURIED GRADE BEAM (strut), not a wall and not an arch. 12" x 17 1/2" on the
# MW–ME pair, wholly below the garden floor, closing the loop so W-SG-W2/E2's thrusts cancel
# through it (`engineering/retaining_system.py`, `notes/sunken_garden_court_free_body.md`
# §8). It is a `Beam` so plans draw it as a hidden grade beam rather than a cut wall; the
# uid and tag are the wall's, so `retaining_system/W-SG-ARCH` and its GlobalId survive.
#
# - Cast WITH the walls, so the loop closes before backfill loads them. A slab strut would
#   leave them free cantilevers at FS 0.73 until the floor cured.
# - No Footing: 219 plf on its own 12" of bearing. FB-SG-ARCH beds it directly.
# - Section is held, not derived: see `_grade_beam_top` / `_grade_beam_bottom`. The size
#   string keeps a decimal point so `cross_section` reads it as actual dimensions.
# - SUNKEN_GARDEN_GRADE_BEAM_12 carries no wash: nothing of it shows.
_GRADE_BEAM_DEPTH_IN = _grade_beam_top.inches - _grade_beam_bottom.inches
GRADE_BEAMS = [
    Beam(uid="SGW102AAAA", tag="W-SG-ARCH", start_node="N-SG-MW", end_node="N-SG-ME",
         size=f"12.0x{_GRADE_BEAM_DEPTH_IN:g}", assembly="SUNKEN_GARDEN_GRADE_BEAM_12",
         top_elevation=_grade_beam_top),
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

# ** HOW FAR THIS RUN STANDS OUT OF THE YARD — COMPUTED, NOT COMMANDED. **
# The owner's figure is a BAND: around 36" out of the yard, up to about 48", because a
# freestanding wall this tall may be read as a guard and a guard has a height. It used to
# be recorded as a maximum, baked into `retaining_top_ft` as `(site_grade_in + 36) / 12`,
# which is the opposite constraint — under it a lower yard would have pulled the five wall
# tops down rather than letting the exposure grow into the band.
#
# It is a result now. `plan/site.py` authors the south yard as a flat plane at -3'-4"
# (three stations, read by `resolve/site_earth.local_grade_elevation_m`'s station branch),
# and the wall tops sit on the porch datum at 0'-0", so the run stands 40" out of it.
#
# ** PINNED, SO A CHANGE IS LOUD. ** `test_retaining_court` asserts this number. Do not
# replace it with an inequality against `SITE_GRADE` — the -2'-10" global plane is the
# near-house bench, not the yard these walls stand in, and grading the exposure against it
# would report 34" for a wall that is really 40" out of the ground beside it.
#
# One figure and not a range today only because the authored yard is one plane. Local grade
# IS local: the side legs run from 10 to 34 feet out from the house, and the first station
# to be authored at a different elevation makes this a range along the wall. Widen it to a
# (min, max) pair when that happens rather than picking one end.
RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN = 40.0
LOCAL_YARD_GRADE_IN = -RETAINING_EXPOSURE_ABOVE_LOCAL_GRADE_IN
RETAINING_EXPOSURE_BAND_IN = (36.0, 48.0)
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
# ** ONE BELL DIAMETER, 36", ON BOTH PORCH PIERS SINCE 2026-09-10. **
# These were 30" and 36", and neither number was chosen. The 36" is a fossil: it was sized
# for a 20" round column and stayed put when the column above it shrank to 12" on
# 2026-09-03 — correctly, because a bell answers to the SOIL and not to the shaft, but the
# result was a diameter nothing was any longer setting. The 30" was never set by anything
# at all; it was simply the other one.
#
# What one diameter buys: one under-reamer setting instead of two on a two-pier job, one
# schedule row, and one number for the driller to hit. What it costs is about 0.09 cy of
# concrete, ~$27-43. And it lifts the tightest pier in the house: PD-SG-COL's bearing falls
# as the square of the diameter, (30/36)^2 = 0.694, taking its d/c from 0.83 to 0.60.
#
# ** THE BELL GROWS 3" PER SIDE AND THAT REACHES TOWARD THE HOUSE FOOTING — CHECKED. **
# PD-SG-COL is centred at y = -2'-3", so its north face goes from -12" to -9". FT-B-S2/S3's
# south face is at -4". The plan gap closes 8" -> 5", and the two do not touch. They also
# do not overlap vertically: the bell's TOP is at -139 7/16" and the house strip bottoms at
# -117 7/16", 22" above it (the bell bears another 12" down, at -151 7/16").
#
# **What that 22" means is a SEQUENCING constraint, not a clearance one, and it was already
# true at 30".** A 1:1 influence line down and out from the house footing's south bottom
# edge reaches y = -2'-2" at the bell's top elevation, and the bell's north face is inside
# it either way. So the bell is in the house strip's load path and always was — auger these
# two shafts with the open basement excavation, before or with the house footings, never
# after. `structural.concrete_interference` grades ISOLATED pours only and will not catch
# this; nothing else looks at it.
_col_footing_width_in = 36.0
_front_footing_width_in = 36.0

# --- the two porch piers reach frost depth by EXCAVATION, on formed square pads ----------
#
# ** 2026-09-14: THE BELLS BECAME FORMED 30" SQUARE PADS, AND ONLY THE SHAPE CHANGED. **
# Owner's call, and the whole of the reason is grading: IRC Table R507.3.1 publishes
# FLAT-PAD rows, a bell has no row, and `engineering/spread_footing.py` therefore carried
# `spread_footing/PT-SG-COL` and `-FCOL` to the seal register for a bearing question that a
# 30" square closes by lookup. **The DEPTH is untouched** — `bottom_elevation` is still the
# derived `_pier_bell_bottom_ft`, still 42" below the court, still bearing on undisturbed
# soil — so everything the paragraphs below say about frost cover, about the levelling bed
# rather than a replacement section, and about digging with the open basement excavation is
# as true of a formed pad as it was of a bell. What is no longer true is the METHOD: there is
# no auger and no under-reamer on this job now, the pit is dug and the pad is formed in the
# bottom of it, and `_col_footing_width_in` / `_front_footing_width_in` above are the
# retired bell diameters, kept for the revert. See `_PIER_PAD_SIDE_IN` below for what it
# costs (the three section limit states `spread_footing` graded on the bell go with the
# record, because nothing grades a `Pad`'s own section).
#
# The paragraphs below are the 2026-09-10 pass, kept because the frost argument is the live
# one and is what a reader has to follow to see why these two are different from the five
# wall footings beside them.
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
# What it WAS, and what a reader restoring it needs: a belled augered pier is a 12" (20" at
# the front) hole augered to 42" below the garden floor, its base under-reamed out to the
# bell diameter, a fibre tube dropped in the shaft and the whole thing poured monolithically.
# It was TWO elements here — the ``Footing`` was the bell (the bearing element, 12" thick at
# the bottom of the hole) and the ``Post`` the shaft above it. It is a ``Pad`` and a ``Post``
# now, and the pair still pours as one placement; what changed is that the bottom is formed
# square rather than reamed round.
#
# **The bell MOVED DOWN; the bell did not GROW.** Deepening the ``Footing`` instead — the
# only lever this file had before ``Footing.bottom_elevation`` landed — would have drawn a
# 30"x30"x42" (and 36"x36"x42") prism of concrete: 1.41 cy against the ~0.25 cy of extra
# 12"/20" shaft the real pour adds, a ~7x over-bill, and a foundation schedule printing a
# 30" footing where a 12" auger hole gets drilled. Quantities are the product; a bell in
# the wrong place is a wrong quantity, not a drafting nicety.
# 42" below the COURT surface, not below the basement floor plane. Pinned to
# `basement_depth_ft` this would have lost the whole flood step: cover drops 42.0" -> 34.75",
# the 7" levelling bed leaves a 41.75" ASCE section, and PD-SG-FCOL FAILs outright — its
# ``under`` is a Post, so it misses the R404.4 branch and the nearest frost wing is 62" away.
# PD-SG-COL would have passed for the wrong reason, shielded at distance 0 by a foam board it
# happens to sit under. Re-derived, cover is exactly 42.0" again.
# ** DERIVED AGAIN, AND BACK ON 42" EXACTLY (2026-09-05, second pass). **
# It was pinned at -13'-2 11/16" for one day, on the argument that 49 1/4" of cover is more
# conservative than 42" and that re-opening notes/porch_pier_*.md was not worth the 0.1 cy
# of shaft it saves. Owner's call reverses that: the bells come back up to the rule they
# exist to satisfy. A pinned literal here is also the kind of number that goes quietly
# wrong the next time the court moves — which is precisely how it got to 49 1/4".
#
# So it is the rule again, written as the rule: `frost_depth_in` below the court surface,
# which is what `structural.frost_depth` measures cover against for a footing standing
# inside this excavation. 42" below -9'-1 7/16" is -12'-7 7/16".
#
# The consequence to keep an eye on is the clearance BELOW, not the cover above — see
# `_pier_bell_top_ft`, where it is worked out against a well that rose 9" the same day.
_pier_bell_bottom_ft = (_court_top_in - SPEC.frost_depth_in) / 12.0
# ** THE CLEARANCE TO WATCH. ** The bells' 7" levelling beds bottom at -13'-2 7/16" against
# `_SG_DRYWELL_TOP` at -13'-7 7/16": 5" clear. Both ends of that gap moved this pass — the
# bells rose 7 1/4" to 42" cover and the well rose 9" onto the wall beds — so it is smaller
# than either change alone suggests. It is the exact collision the FOOTING_BEDDING block
# below warns about, asserted in test_catlin_outdoor_structures.py so it cannot close
# silently, and the two bodies are 4'-3" apart in plan in any case.
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
              # ** SUNKEN_GARDEN_COLUMN_12, NOT PIER_CONCRETE_12, SINCE 2026-09-10. **
              # PT-SG-FCOL is the same 12" round at the same 120 15/16" height over the
              # same z range four feet away, holding the other end of the same frame, and
              # it was on the other type. The split was also printing this column's partner
              # as the weaker of the two — the garden type stated its 5,000 psi mix in prose
              # only, so every calc on PT-SG-FCOL fell back to the presumptive 3,000 while
              # this one was graded on the real mix. Both come off the same truck. The
              # retype also drops the grout island PIER_CONCRETE_12 carried and the garden
              # type refuses -- but it did NOT close that follow-up: the island rode the
              # assembly to PT-BW-RE/-RNE and was struck at the source on 2026-09-12. Both
              # types say NO GROUT ISLAND now (see plan/assemblies.py).
              assembly="SUNKEN_GARDEN_COLUMN_12",
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
              # Reads SPEC.corner_column_cage like the other five, so all six court columns
              # spell ONE string and the drawing names ONE part to order.
              vertical_reinforcement=SPEC.corner_column_cage,
              reinforcement=_CAST_COLUMN_CAGE,
              supported_by="PD-SG-COL")

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
# assembly (SUNKEN_GARDEN_COLUMN_12) and one price row serve all five.
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
# bolted through the column: PT-SG-BF2 stands on it through an ABU66SS, and the two beams
# hang off that pillar (HU212-3). See notes/uplift_load_path.md.
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
                    supported_by="PD-SG-FCOL",
                    # A_g = 113.10 in2, so the 1% floor is 1.131 in2; (4) #5 = 1.24 in2
                    # (rho 1.097%). Ties #3 at 10", inside §25.7.2.2's least of 16db =
                    # 10.0", 48dt = 18.0", h = 12.0". This is the MINIMUM legal cage on a
                    # 12" round and there is nothing to trim: (4) #4 = 0.80 in2 is 29%
                    # SHORT of the floor, and four bars is already §10.7.3.1(b)'s minimum
                    # within circular ties, so the count cannot come down either. Check any
                    # substitution against 1.131 in2 AND against four bars.
                    vertical_reinforcement=SPEC.corner_column_cage,
                    reinforcement=_CAST_COLUMN_CAGE,
                    assembly="SUNKEN_GARDEN_COLUMN_12")

# Wall footing uids are a literal map keyed on the wall tag, not ``enumerate(WALLS)``.
# They used to be minted by position, so retiring W-SG-ARCH (which was index 1) would have
# shifted every surviving footing's uid — and therefore its IFC GlobalId — by one. The map
# keeps SGF102..SGF106 on the walls they have always belonged to; a new wall takes the next
# free number rather than renumbering its neighbours. Same reasoning for the beds below.
_WALL_FOOTING_UID = {"W-SG-W1": "SGF102AAAA", "W-SG-E1": "SGF103AAAA",
                     "W-SG-W2": "SGF104AAAA", "W-SG-E2": "SGF105AAAA",
                     "W-SG-S": "SGF106AAAA"}
# ** ALL FIVE WALL FOOTINGS ARE 12" (2026-09-05, second pass). ** FT-SG-W1/E1 used to be
# 13": the odd inch was the one the porch walls gave up when they were trimmed to 10'-0",
# put back into the footing so its UNDERSIDE would not move. With the porch walls now
# bearing on `_wall_bottom` like everything else there is no trimmed inch to give back, and
# a one-off thickness on two of five footings is a dimension a detailer has to notice.
# ============================================================================
# ALL FIVE COURT STRIPS ARE 7'-0" CENTRED: THE 8'-0" WAS A FOSSIL (2026-09-10).
# ============================================================================
# The strip went 7'-0" -> 8'-0" because the resultant fell outside the middle third — e
# 1.30' against a kern of 1.17'. That was true, at a retained height of 11.3698'. Three
# height cuts have since brought this wall to 10.1198', and §3's own discipline of adding
# a table row after each cut was applied to the stem bar schedule and never here. At 7'-0"
# centred the resultant now lands 0.800' off centre against a kern of 1.167' — a 31 percent
# margin, the same crossed-sides rejection §6 made of `#6 @ 16"` and `#5 @ 10"`.
#
# ** THE OUTBOARD EDGE DOES NOT MOVE, WHICH IS THE ONE THING THAT MAY NOT. **
# `params/raised_garden.py` measures its apron's 3'-0" clear off that edge — the owner's own
# figure, from the brief — and `test_catlin_outdoor_structures.py` asserts it. At 96" with a
# 6" inboard offset the outboard reach is 96/24 - 6/12 = 3.5'; at 84" centred it is
# 84/24 = 3.5'. Identical. The whole 12" comes off the TOE, on the court side, where the
# garden floor is — so the planted field GROWS as the strip narrows.
#
# ** NEVER CUT THE HEEL. ** The heel is held at 3'-0" and carries the stabilising column of
# soil: a foot of toe costs 150 plf out of 5,578, a foot of heel costs four times the
# system factor of safety for the same yard of concrete. -2.10 CY over the three runs,
# exactly reversing the widening.
#
# ** THE MAT AND THE WIDTH ARE ONE DECISION, NOT TWO. ** Narrowing removes 22 percent of the
# toe moment, which is what lets the mat drop from `#6 @ 10"` to `#5 @ 12"`: at 8'-0" a
# `#5 @ 12"` mat reads 0.90 on the toe, at 7'-0" it reads 0.70. `#4 @ 12"` is NOT the next
# step down — it fails flexure and falls below ACI 318-19 §7.6.1.1 minimum steel.
#
# ** FT-SG-W1/E1 NARROW WITH THEM, AND THAT IS CORRECT. ** The porch strips were widened to
# 96" on 2026-09-10 for a continuous form line, not for a limit state, and a continuous line
# at 7'-0" is just as continuous. What they were NOT bought for the form line is the mat,
# and they keep it: nothing in this engine grades a footing's own flexure except on the
# retaining set, so a 3'-0" PLAIN concrete cantilever under the two walls carrying the
# balcony's four moment-fixed columns had never been run at all. It does not pass plain:
#
#   plain phi*Mn on a 12" strip cast against soil (h-2 = 10", 5,000 psi)   3,536 ft-lb/ft
#   toe 3'-0", as built     Mu  8,319-10,376   d/c 2.35-2.94   FAILS
#   HEEL 3'-0", either way  Mu  8,303          d/c 2.35        FAILS
#
# (The toe range brackets 0 to 2,000 plf of superstructure line load at the stem, and reads
# the wall as a free cantilever — the conservative bound for the toe, since crediting the
# bracing walks the resultant back toward the heel. **The HEEL row needs no such bracket**:
# §7c's convention drops the upward pressure under the heel entirely, so that number is
# geometry and soil alone and does not move with the bracing credit. It is the row that
# settles this.)
#
# All five strips are 7'-0" x 1'-0" centred on the wall axis, zero offset, so the outboard
# edge runs unbroken at x = 4.500 / 31.500 and the inboard at 11.500 / 24.500.
_RETAINING = ("W-SG-W2", "W-SG-E2", "W-SG-S")
_RETAINING_FOOTING_WIDTH_IN = SPEC.footing_width_in  # 84.0
# Zero since 2026-09-10, with the strip back at 7'-0": the offset existed only to keep the
# 12" of widening on the court side, and there is no widening to keep there. The field kept
# it as a named constant rather than dropping `Footing.offset` altogether because the sign
# convention is the non-obvious part and is worth one place to read it — positive is along
# the LEFT-hand normal of each wall's own start->end direction, the frame
# `resolve/geometry.rect_between` lays the strip out in, and all three retaining walls wind
# the same way around the court (W2 runs MW->SW, E2 runs SE->ME, S runs SW->SE), so a
# positive offset would be "into the court" for every one of them. Checked, not assumed:
# see the footing-edge assertions in `test_retaining_court.py`.
_RETAINING_FOOTING_OFFSET_IN = (
    OPTION.footing_toe_in
    - (_RETAINING_FOOTING_WIDTH_IN - SPEC.wall_thickness_in) / 2.0
)

# ** THE 3'-0" TOE IS A CANTILEVER, AND IT WAS UNREINFORCED UNTIL 2026-09-03. **
#
# `_RET_REBAR` above is the STEM's steel, and until `engineering/retaining_basis.py` grew
# `footing_states` nothing in this repo ever asked what the FOOTING carried. It carries a
# lot: a 12" PLAIN strip is good for 3,536 ft-lb/ft and the cantilever asks several times
# that at either width. That was a real gap in the design, not a reporting artifact, and
# `notes/sunken_garden_court_free_body.md` §7 is its oracle.
#
# `#5 @ 12"` both faces is the answer at a 3'-0" toe, and it is one bar size on this pour:
# one bundle to order, one bender's setup and one thing for an inspector to count. Bottom
# (toe) 0.70, top (heel) 0.70. It was `#6 @ 10"` while the toe was 4'-0"; narrowing the
# strip removed 22 percent of the toe moment and the mat came down with it. `#5 @ 12"`
# gives 0.310 in2/ft against ACI 318-19 §7.6.1.1's 0.0018 Ag = 0.259, and 12" clears
# §24.4.3.3's 18" maximum. `#4 @ 12"` is not available: it fails flexure AND minimum steel.
#
# 3" cover is ACI 318-19 Table 20.5.1.3.1(a) — cast against and permanently in contact with
# ground — and it is the cover this whole footing is designed on, not a durability upgrade
# bolted onto a `d` sized against something looser.
_RETAINING_FOOTING_MAT = ReinforcementSpec(
    bars=(
        BarSpec(role="bottom-x", bar=5, spacing=inch(12.0),
                note="transverse, resists the 3'-0\" toe cantilever; hook the toe end"),
        BarSpec(role="top-x", bar=5, spacing=inch(12.0),
                note="transverse, resists the 3'-0\" heel carrying 9.12' of soil"),
        BarSpec(role="bottom-y", bar=4, spacing=inch(18.0),
                note="longitudinal distribution steel; carries no graded limit state"),
    ),
    cover=inch(3.0),
    lap_class="B",
    source="sized in notes/sunken_garden_court_free_body.md §7, at-rest 110 pcf",
)

FOOTINGS = [
    Footing(uid=_WALL_FOOTING_UID[w.tag], tag=f"FT-{w.tag[2:]}", under=w.tag,
            # ONE WIDTH, ONE OFFSET, ONE MAT, ALL FIVE STRIPS (2026-09-10). The
            # `_RETAINING` branch that used to decide all three is gone: the porch strips
            # took the mat, because their plain 3'-0" heel is 2.35 times over as plain
            # concrete and nothing was grading it. See the block above
            # `_RETAINING` for the arithmetic. `_RETAINING` itself survives and still
            # matters — it is what `lateral_support` and the R404.4 engineered analysis key
            # on, and those two walls are still braced and still not cantilevers.
            width=inch(_RETAINING_FOOTING_WIDTH_IN),
            offset=inch(_RETAINING_FOOTING_OFFSET_IN),
            reinforcement=_RETAINING_FOOTING_MAT,
            # One type for all five strips since 2026-09-10: the two cards were identical
            # (12" of EXPOSED_MIX) and the porch one declared 13", an inch no footing here
            # has been built at for revisions. Width is plan geometry, not an assembly.
            assembly="COURT_FOOTING_12",
            depth=inch(SPEC.footing_thickness_in))
    # W-SG-ARCH is deliberately absent: the buried grade beam carries 219 plf over its own
    # 12" of bearing and bears straight on FB-SG-ARCH. See its own block in WALLS.
    for w in WALLS if w.tag in _WALL_FOOTING_UID
]
# The two porch piers' BELLS. PD-SG-COL keeps SGF199AAAA; the front column's is appended
# after it, so nothing already in the IFC moves.
#
# ``bottom_elevation`` is what makes these bells rather than plinths: a post-hosted footing
# tops out on its storey datum unless it says otherwise, which put both of these flush with
# the garden floor on 12" of cover. Authored, the UNDERSIDE is the fixed end — the bell
# bears at ``_pier_bell_bottom_ft`` and is ``depth`` thick above it — which is exactly how
# a hole is dug. Width and thickness are untouched: only the elevation changed.
# ** 2026-09-14: THE BELLS BECAME FORMED SQUARE PADS, AND THE FROST COVER IS KEPT BY DEPTH. **
# Owner's call. These two were 36" belled bottoms on a 12" augered shaft, and the bell was
# what put `spread_footing/PT-SG-COL` and `-FCOL` in the seal register: IRC Table R507.3.1
# publishes FLAT-PAD rows, so a bell has no row and its bearing is a design against the
# site's own allowable pressure. A 30" square pad has a row, and the question closes.
#
# **What does NOT change is the depth.** `bottom_elevation` stays `_pier_bell_bottom_ft` —
# the DERIVED expression and never a pinned number, which is the trap `houses/catlin/CLAUDE.md`
# warns about and which this house has already sprung once. These pads still bear at 42"
# below the court on undisturbed soil, and their frost protection is still excavation rather
# than the aggregate section the five WALL footings rely on. The levelling bed under each
# (`FB-SG-COL` / `-FCOL`, `_PIER_BELL` below) is unchanged for the same reason.
#
# **What IS lost, and it belongs in the open-items list rather than in silence:** a `Footing`
# carried `spread_footing`'s flexure, one-way shear and punching-shear states on the bell
# section, and **nothing grades a `Pad`'s own section**. Those three states go with the
# record. They were at d/c 0.15, 0.03 and 0.07 on a 36" bell — the section was never close —
# and a 30" x 12" pad under a 12" round is squatter still, with a shorter cantilever and the
# same thickness. But the engine no longer says so, and `notes/sunken_garden_piers.md` §5
# carries that as the price of the retirement.
#
# 30" square = 6.25 ft² against 3.97 ft² required at the mn-2020 profile's 1,500 psf, d/c
# 0.64. Volume falls 0.10 cy each: the 36" Footing DREW as a 36" square (9.00 ft²), which is
# what `resolve/envelope.py` does with a post-hosted footing, so the pour was always square
# and this is 6" off each side of it rather than a shape change.
_PIER_PAD_SIDE_IN = 30.0


def _pier_pad_outline(post_tag):
    """A square pad centred on the column it carries, read off the column's own position."""
    half = inch(_PIER_PAD_SIDE_IN) / 2.0
    x, y = (_cx, _y_col) if post_tag == "PT-SG-COL" else (_cx, _y_front_col)
    return (pt(ft(x) - half, ft(y) - half), pt(ft(x) + half, ft(y) - half),
            pt(ft(x) + half, ft(y) + half), pt(ft(x) - half, ft(y) + half))


FOOTINGS.append(
    Pad(uid="SGF199AAAA", tag="PD-SG-COL",
        outline=_pier_pad_outline("PT-SG-COL"),
        thickness=inch(SPEC.footing_thickness_in),
        assembly="PIER_BASE_12",
        bottom_elevation=ft(_pier_bell_bottom_ft))
)
FOOTINGS.append(
    Pad(uid="SGF198AAAA", tag="PD-SG-FCOL",
        outline=_pier_pad_outline("PT-SG-FCOL"),
        thickness=inch(SPEC.footing_thickness_in),
        assembly="PIER_BASE_12",
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
# **PD-SG-COL IS NOT IN THIS SET, and there is nothing to replace it with.** A dowel-and-
# foam joint needs two concretes meeting at one plane, and the garden bell bears 2'-10"
# lower than FT-B-S2's underside — its top is 1'-10" below it — so the two pours do not
# face each other:
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
# stone that does not fit: 42" under the bell underside would bottom the excavation at
# -16'-1 7/16", 2'-6" BELOW _SG_DRYWELL_TOP, so the bearing bed and the soakaway it is
# supposed to sit on top of would swap places. Measured, not assumed. At 7" the bed bottoms
# at -13'-2 7/16" and clears the well's top of stone by 5" — the two do not overlap in plan
# at all, so the clearance is belt and braces rather than the thing holding them apart, but
# it is asserted because it is the number that would close first.
_PIER_BELL = {"PD-SG-COL", "PD-SG-FCOL"}
_BEDDING_UID = {"FT-SG-W1": "SGB002AAAA", "FT-SG-E1": "SGB003AAAA",
                "FT-SG-W2": "SGB004AAAA", "FT-SG-E2": "SGB005AAAA",
                "FT-SG-S": "SGB006AAAA", "PD-SG-COL": "SGB007AAAA",
                "PD-SG-FCOL": "SGB008AAAA"}
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
# ** THE ONE EXCAVATION PLANE — THE COURT'S BEDS ALL BOTTOM HERE. **
# Every wall bed in this court bottoms at `_SG_WALL_BED_BOTTOM`, the footing underside less
# the 42" ASCE 32 section. The grade beam's bed is derived to land on the SAME plane rather
# than carrying its own 42" undercut below a beam that hangs 9" lower than the footings do.
_SG_WALL_BED_BOTTOM = (_wall_bottom
                       - inch(SPEC.footing_thickness_in)
                       - inch(SPEC.aggregate_bedding_depth_in))

# W-SG-ARCH's bed, appended rather than swept up by the comprehension above because it is
# hosted on the Beam and not on a Footing — the grade beam has none (see GRADE_BEAMS). Same NFS
# claim about the same stone, same 4" sock-wrapped tile to DRW-SG-MAIN, so it joins the
# existing takeoff group rather than starting a second one.
#
# ** THE UNDERCUT IS 33", NOT 42", SINCE 2026-09-10, AND THAT CLOSES THE 9" STEP IN THE
# DIG. ** It read `aggregate_bedding_depth_in` — the footings' 42" — copied because every
# bed in this court once shared one plane. When `_grade_beam_bottom` was decoupled and HELD
# 9" below the footings (the section §8 will not give up), the copied 42" went down with it
# and the excavation grew a second floor along the beam line: one more laser setting, one
# more compaction schedule, one more tile plane, and the side-feed detail into the drywell
# that existed only because this bed reached below the well's top.
#
# **The 42" is not required here and never was.** It is an ASCE 32 soil-replacement section
# and this beam is not in the frost population at all: it has no `Footing`, so
# `structural.frost_depth` — which iterates footing and pad SOLIDS — never sees it, and the
# reason it has none is that it carries 219 plf over its own 12" of bearing, 219 psf against
# 3,000 allowable. What the bed is actually for is a compacted, drained, non-frost-
# susceptible plane to cast a 20' beam on. 33" of it still puts the beam's underside 33"
# above undisturbed clay, which clears the 42" frost requirement measured from the court
# floor by 21" on its own.
#
# Derived off the wall-bed plane rather than pinned at 33", so it follows if either end
# moves. If `_grade_beam_bottom` ever rises to the footing plane this goes to 42" on its
# own — and then the whole question reopens, correctly. It is NOT
# `cast_foam_in_aggregate`: that is for the house-adjacent footings' thermal break, and this
# beam is 11'-0" south of the house with unconditioned court on both faces.
#
# `width` is authored because a beam-hosted bed defaults to the beam's own width, and a
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
        undercut=_grade_beam_bottom - _SG_WALL_BED_BOTTOM,
        non_frost_susceptible=True,
        drain_tile_spec=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    )
)

# The sunken garden's own soakaway — a hole dug to take water and give it to the soil,
# below (not part of) the 42" bearing bed. The garden floor sits 9' down with no downhill
# side, so everything landing here (perimeter tile, the slab itself) has nowhere to go but
# down. The balcony leader hangs outside the east wall and discharges to the terrace, so
# the well is left carrying only the water it cannot avoid.
# Top of stone sits at the DEEPEST wall bed's underside so the two stack rather than
# intersect. ``SPEC.aggregate_bedding_depth_in`` is their number: the two column bells take
# a 7" levelling course and their beds stop well short of this plane, which is clearance,
# not a gap to close.
#
# ** IT SITS ON THE SIX BEDS, AND THE ONE-PLANE PROPERTY IS BACK. ** Until the retaining
# footings rose, every bed in this court shared one underside and the well's top of stone
# WAS that plane: the whole bearing system stood on the soakaway and drained into it by
# falling into it. Lifting the wall footings 9" left their beds at -13'-7 7/16" with the
# well still pinned to the beam's at -14'-4 7/16", so the five tiles that feed this well
# ended 9" above the top of it, discharging into undisturbed clay.
# `drainage.discharge_consistency` resolves the NAME and never asks where the pipe goes, so
# it passed; the plan drawings are where it shows, and it showed.
#
# The well was moved onto the WALL beds, which are the ones that feed it, and FB-SG-ARCH
# was left as the one bed reaching 9" BELOW it, feeding the stone column through its side.
# **On 2026-09-10 that last step closed from the other end**: the beam's bed undercut went
# 42" -> 33" so it bottoms on this same plane. All six beds, the well's top and the two
# lead runs are now one elevation, which is one laser setting and one compaction schedule,
# and the side-feed detail is gone. The beam itself still hangs 9" lower — that is §8's
# held section and it does not move — but its bed no longer hangs with it.
#
# 6' of fabric-wrapped stone below (unwrapped, this clay silts its voids shut in a
# season). Tagged DRW-, not DW-, because DW- is the dowel prefix and the two collided.
_SG_DRYWELL_TOP = _SG_WALL_BED_BOTTOM
# ** PINNED OFF THE GRADE BEAM, NOT OFF THE COURT'S MIDPOINT (2026-09-10). ** It was
# `(_y_in_s + _y_in_n) / 2`, written out twice, and the 2'-0" court shortening walked it
# 1'-0" north — putting the north edge of the 5'-0" shaft at -11.3333, INSIDE FB-SG-ARCH's
# 24" bed band and 1'-8" from the beam's south face. Nothing grades that:
# `structural.concrete_interference` sees isolated pours and every court footing is
# `under=`-hosted, and `drainage.discharge_consistency` resolves tags and never asks where
# the pipe goes. So the well now measures a STATED clearance south of the beam's axis and
# cannot drift on any future length change. 3'-10" holds the well exactly where it is
# today, 3'-4" south of the beam's south face, with the shaft's north edge 10" clear of it.
_WELL_SOUTH_OF_ARCH_FT = 3.0 + 10.0 / 12.0
_sg_well_y = _y_ax_mid - _WELL_SOUTH_OF_ARCH_FT  # -14.8333
GARDEN_DRYWELL = Drywell(
    uid="SGDR01AAAA", tag="DRW-SG-MAIN",
    position=pt(ft(_cx), ft(_sg_well_y)),
    diameter=ft(5), depth=ft(6), geotextile=True,
    top_elevation=_SG_DRYWELL_TOP,
    # Every FT-SG-* bearing bed, plus the field's own underdrain. FD-SG-FIELD is named as a
    # string rather than swept up, because the field's plan coordinates are derived below
    # this point and the well is what they are derived towards.
    inlet_refs=tuple(b.tag for b in FOOTING_BEDDING)
    + ("FD-SG-FIELD", "FD-SG-LEAD-W", "FD-SG-LEAD-E", "FD-SG-COL-LEAD"),
    # ** THE WELL'S OWN WAY OUT, WHICH IT DID NOT HAVE (2026-09-14). ** `FD-SG-OVERFLOW` is
    # the PLANTING FIELD's overflow, not the well's: it tees off the field at -127 7/16" and
    # runs north to the sump. When the WELL filled past its own top of stone there was no
    # modelled route at all — the water backed up into the connected wall-bed stone and left,
    # if it left, implicitly through that stone into the field lateral. Nothing drew it and
    # nothing checked it.
    #
    # Naming it makes the implicit route the authored one and puts a level on it. The well
    # spills at -127 7/16" — `FD-SG-OVERFLOW`'s own invert, the profile underside, which is
    # the elevation the overflow note already argues for: storage in a soakaway is only the
    # volume BENEATH its inlet, so the well must fill and spill rather than back up into the
    # rootzone gravel. One number, stated once, on the run that already carries it.
    overflow_ref="FD-SG-OVERFLOW",
    overflow_invert=_court_top - inch(SPEC.field_depth_in),
)

# --- garden floor: a concrete RIM around an open gravel field ---------------------
#
# ** ONE SLAB WITH A HOLE, NOT FOUR RECTANGLES, AND THAT IS THE WHOLE TRICK. **
# `Slab.openings` resolves into `ResolvedSolid.voids`, and voids ARE subtracted by
# `structural_solids_takeoff` and `envelope_layer_takeoff` — so the rim bills net concrete.
# But `resolve/site_earth` and `checks/code/mn_residential/egress._landing_surfaces` both
# read `solid.outline` and ignore voids, so the court still reads as ONE excavation floor
# and ONE R311.3 landing across all 494 sf. Both of those are TRUE, because the field tops
# out on exactly the same plane as the rim.
#
# Keeping the tag and the uid matters just as much. `_below_grade_floors` iterates sorted by
# uid and `local_grade_elevation_m` skips ties (`if top_m >= lowest: continue`), so with
# SL-SG-FIELD at the same z1 and a LATER uid, SL-SG-FLOOR always wins and stays the
# `source_tag` in every frost finding. Four separate rim rectangles would have renamed the
# governing surface in a dozen messages. If a frost message ever says SL-SG-FIELD, the two
# `top_elevation`s have drifted apart — that is an elevation bug, not a test bug.
#
# The rim is what the toes and the porch bay leave: the retaining strips project 3'-6"
# inboard on three sides and the porch roofs the north bay, so the open field is
# ~160 sf of the court's 494. (It was 147 of 532 while the strips reached 4'-6" and the
# court ran 28'-0": shortening the court and narrowing the strips on 2026-09-10 moved those
# two the OPPOSITE way, and the field grew as the court shrank.)
#
# The court-side edge of every strip, derived so it cannot drift from the footing: wall
# axis, half the 7'-0" strip, plus whatever the strip is offset INTO the court (zero now).
#
# ** ONE REACH FOR ALL FIVE, AND IT IS BACK TO 3'-6". ** It was 3'-6" while all five strips
# were 84" centred, went to 4'-6" for the 96"-plus-6"-offset day, and is 3'-6" again. The
# expression is what matters, not the figure: `FO-SG-TOE-N-W/N-E` void the rim over the
# porch strips and read this number, so a reach that disagrees with the strip by 12" laps
# 12" of rim slab over 12" of footing in whichever direction it disagrees. The invariant is
# that the net rim polygon's intersection with each of the five WALL footprints is 0.000 sf,
# and `structural.concrete_interference` grades ISOLATED pours only and would not catch it.
# Asserted since 2026-09-10 — `test_the_net_rim_laps_no_footing` — because the court's
# length and this reach are its two inputs and that pass moved both at once.
_ret_toe_reach_ft = _RETAINING_FOOTING_WIDTH_IN / 24.0 + _RETAINING_FOOTING_OFFSET_IN / 12.0
_field_x_w = (_x_in_w - _half) + _ret_toe_reach_ft   # 12.5
_field_x_e = (_x_in_e + _half) - _ret_toe_reach_ft   # 23.5
_field_y_s = (_y_in_s - _half) + _ret_toe_reach_ft   # -23.833
# The grade beam's south face. North of it is the porch bay, which stays paved.
_field_y_n = _y_ax_mid - _half                       # -11.5
_field_x_mid = (_field_x_w + _field_x_e) / 2.0       # 18.0

# --- the field's underdrain, and the court's overflow leg --------------------------
#
# ** THE ASSEMBLY SAID "draining to DRW-SG-MAIN" AND NOTHING IMPLEMENTED IT. ** Until
# 2026-09-05 that was prose in a `source=` string with no element behind it — the exact
# failure `checks/mep/drainage.py`'s own docstring was written about. These two runs are
# the claim made real.
#
# `FrenchDrain` and not a `FootingBedding`'s derived tile: a bedding's tile follows the
# excavation under a footing, while this is "a run somebody put where the water goes".
#
# ** ONE LATERAL, AND THAT IS THE CHEAPEST ANSWER THAT IS ALSO THE RIGHT ONE. ** USGA caps
# lateral spacing at 15'-0". The field is 13'-0" wide E-W, so a single centre lateral leaves
# 6'-6" of reach each side — an effective spacing of 13'-0", inside the cap with room over.
# USGA wants >=0.5% fall, which over the lateral's 12'-4" is 0.74" — trivial against the
# drop into the well.
#
# ** THE FIELD'S PROPORTIONS FLIPPED ON 2026-09-10 AND THE LATERAL DID NOT MOVE. ** It was
# 11'-0" E-W x 13'-4" N-S, and this run was on the LONG axis; the court shortening and the
# strip narrowing took it to 13'-0" x 12'-4", so the run is now on the shorter one. The
# check that matters is the REACH (half the perpendicular width) against the 15'-0" cap, and
# it went 5'-6" -> 6'-6", still well inside. A second lateral would be owed only past
# 15'-0" of E-W width, which this field cannot reach inside a 19'-0" court.
#
# ** NO PERIMETER "SMILE" DRAIN, DELIBERATELY. ** USGA's trench is 6" wide x 8" deep cut
# INTO the subgrade, which here bottoms at -135 7/16" — 5" below W-SG-ARCH's underside. Run
# hard against the walls, as USGA's perimeter detail wants, it would undermine the grade
# beam that is the court's only real strut. Down the centre it is clear of everything. The
# omission is a decision, not an oversight.
#
# ** NO WICKING BARRIER, AND THAT IS EARNED. ** USGA's optional perimeter membrane exists to
# stop a porous rootzone bleeding sideways into a fine-textured native surround. This field
# is bounded on all four sides by concrete — three retaining strips and the grade beam. The
# concrete IS the barrier.
#
# ** `sock=False`, AND IT IS THE ONLY TILE IN THIS HOUSE THAT CARRIES IT. ** USGA is
# explicit that "any piping encased in geotextile sleeves are not recommended", and PNW 675
# agrees: a sock in a sand profile clogs with fines and seals the line. The FT-SG-* and
# FB-* beds keep `sock=True` — a bearing course in clay is a different job, and there the
# sock is what stops the clay entering the pipe. Here the graded sand above IS the filter.
#
# uid minted by hand, deliberately: `haus fmt` does not visit `params/*.py`.
GARDEN_UNDERDRAIN = FrenchDrain(
    uid="SGFD01AAAA", tag="FD-SG-FIELD",
    # South end of the field to the well, on the field's own centreline, derived off the
    # `_field_*` names so it cannot drift from the field it drains.
    path=(pt(ft(_field_x_mid), ft(_field_y_s)),
          pt(ft(_field_x_mid), ft((_y_in_s + _y_in_n) / 2.0))),
    # The trench floor AT THE SOUTH END: 8" into the subgrade below the profile's underside,
    # derived from the court plane and the profile depth. NEVER a literal —
    # `SPEC.field_depth_in` moves.
    invert=_court_top - inch(SPEC.field_depth_in) - inch(8),
    # ** IT FALLS INTO THE WELL, AND UNTIL 2026-09-14 IT DID NOT. ** `FrenchDrain` carried
    # ONE invert and the resolver extruded the whole trench dead level, so this run ended at
    # -135 7/16" — **28" above `_SG_DRYWELL_TOP`**, discharging into undisturbed clay above
    # the stone it is drawn to feed. `drainage.discharge_consistency` resolved the name and
    # never asked where the pipe went, exactly as it did for the five wall-bed tiles that
    # ended 9" over this same well before it was moved onto their plane. The precedent for
    # the fix is `_WELL_LEAD` below: write the far end as **the same expression the well's
    # top is**, so the two cannot drift into a run that ends in the air.
    #
    # 28" over the run's 10'-0" is 2.3 in/ft. Steep against USGA's 0.5% minimum and that is
    # the right direction — a lateral outfall dropping into a soakaway wants fall, and only
    # too flat is a defect. `drainage.trench_fall` refuses the reverse.
    end_invert=_SG_WALL_BED_BOTTOM,
    trench_width=inch(6), trench_depth=inch(8),
    tile=DrainTile(diameter=inch(4), sock=False, discharge="DRW-SG-MAIN"),
    discharge_ref="DRW-SG-MAIN",
)

# ** THE OVERFLOW LEG: THE COURT'S SECOND WAY OUT. ** DRW-SG-MAIN is a soakaway in glacial
# till, and MPCA's own numbers say that is a detention structure rather than an infiltration
# one (HSG D, 0.06 in/hr design rate). The case the freeboard note names as the one to watch
# is snowmelt onto a frozen court over a frozen grate, where the well contributes nothing by
# definition — and that note currently answers it by assuming the well FULLY FAILED. This
# leg raises that margin instead of restating it.
#
# ** Its invert is ABOVE FD-SG-FIELD's tee and AT the profile underside. ** -127 7/16": 8"
# above the underdrain's trench floor. Storage in a
# soakaway is only the volume beneath its inlet, so the well must fill and SPILL — never
# back up into the gravel, which would drown the rootzone from below.
#
# ** THE TRENCH STOPS AT THE GRADE BEAM'S NORTH FACE, AND THAT IS THE POINT. ** The leg from
# the well north to here is a 4" pipe SLEEVED through W-SG-ARCH at mid-depth, not an
# excavation: a stone trench crossing the beam at this invert would undermine the strut the
# free-body note holds the whole court together with. `FrenchDrain` has no way to say
# "sleeve", so the modelled trench is only the part that really is one; the cast opening is
# `SP-SG-ARCH-OVERFLOW` below. North of the court it ties into the house collector, which as of
# today falls to the same sump.
# ** THE TWO LEADS THAT MAKE "discharges to DRW-SG-MAIN" A RUN AND NOT A STRING. **
# Seven `FootingBedding` tiles in this court name DRW-SG-MAIN, the well names all seven
# back in `inlet_refs`, and until now not one inch of pipe ran between them: the check
# resolves tags, `resolve/drain_tile.py` derives a ring per bed and never a lead, and the
# well is a bare cylinder 3'-0" away from the nearest ring in plan. Six named connections
# with no geometry is the same defect as the field's "draining to DRW-SG-MAIN" prose, one
# level up.
#
# ** TWO, NOT SEVEN. ** The five wall beds are ONE excavation: FB-SG-W1's stone abuts
# FB-SG-W2's at y = -11.0' where the footings meet, and W2's abuts FB-SG-S's through a
# 4'-10" square corner lap — measured, not assumed — so the west ring, the south ring and
# the porch ring are a single connected body of washed stone at one invert, and the east
# side mirrors it. One lead per side takes the lot. FB-SG-ARCH takes none: its bed bottoms
# 9" BELOW the well's top and stops 2" from the shaft in plan, so it feeds the column
# through its side and a lead would be a pipe running uphill.
#
# Each run is 6'-6" of trench from the strips' court face at `_field_x_*` to the well's own
# centre — 4'-0" of it in open ground and the last 2'-6" inside the shaft. Drawn to the
# CENTRE rather than to the face for the same reason FD-SG-FIELD is: a band that stops on
# the cylinder's edge reads in section as a pipe that does not arrive.
#
# The invert IS `_SG_WALL_BED_BOTTOM`, the same expression the well's top is, so the two
# cannot drift apart into a lead that runs uphill — which is exactly what happened to the
# well itself when the footings rose.
_WELL_LEAD = dict(invert=_SG_WALL_BED_BOTTOM, trench_width=inch(12), trench_depth=inch(8),
                  discharge_ref="DRW-SG-MAIN")
GARDEN_LEAD_W = FrenchDrain(
    uid="SGFD03AAAA", tag="FD-SG-LEAD-W",
    # The retaining strips' court-side face out to the well's own centre — the same two
    # names FD-SG-FIELD is drawn between, so all three runs share one geometry.
    path=(pt(ft(_field_x_w), ft(_sg_well_y)), pt(ft(_cx), ft(_sg_well_y))),
    # `sock=True`, unlike the field's. This lead leaves a bearing bed in clay and the sock
    # is what keeps the clay out of the pipe; the field's run is filtered by the graded
    # sand above it and USGA says a sleeve there seals the line.
    tile=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    **_WELL_LEAD,
)
GARDEN_LEAD_E = FrenchDrain(
    uid="SGFD04AAAA", tag="FD-SG-LEAD-E",
    path=(pt(ft(_field_x_e), ft(_sg_well_y)), pt(ft(_cx), ft(_sg_well_y))),
    tile=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    **_WELL_LEAD,
)

# ** THE THIRD LEAD, AND IT EXISTS FOR THE SAME REASON THE OTHER TWO DO (2026-09-14). **
# `FB-SG-COL` names DRW-SG-MAIN, the well names it back, and its stone reached nothing:
# `drainage.tile_lead` walks the connected body of stone under this court and finds the rear
# pier's levelling course **alone in a body of one**, 8'-10" from the well in plan with
# nothing between. Its twin `FB-SG-FCOL` needs no lead only because `FB-SG-ARCH`'s 33"
# section happens to run between it and the shaft — an accident of position, not a design,
# and the rear pier simply sits too far north to catch it.
#
# The bedding comment above already says these two courses are "the host for the tile that
# has to get water out of these two excavations". This is the pipe that does it.
#
# It FALLS: 5" from the bell's levelling course at -13'-2 7/16" to `_SG_WALL_BED_BOTTOM` at
# -13'-7 7/16", over 11'-4" — 0.44 in/ft, comfortably over any minimum and comfortably
# under anything that would need a drop structure. Both ends are written as the expressions
# the bed and the well are built from, so neither can drift into a run that ends in the air.
#
# It passes UNDER W-SG-ARCH at -13'-2 7/16" to -13'-7 7/16", below the beam's own underside
# at -10'-10 7/16" and inside `FB-SG-ARCH`'s own 33" bed for the last of its length — the
# same stone, not a second excavation crossing the strut. Compare `FD-SG-OVERFLOW`, which
# crosses the beam ABOVE its underside and is therefore a sleeve rather than a trench.
#
# uid minted by hand, deliberately: `haus fmt` does not visit `params/*.py`.
GARDEN_LEAD_COL = FrenchDrain(
    uid="SGFD05AAAA", tag="FD-SG-COL-LEAD",
    path=(pt(ft(_cx), ft(_y_col) - inch(_PIER_PAD_SIDE_IN) / 2.0 - inch(6)),
          pt(ft(_cx), ft(_sg_well_y))),
    invert=ft(_pier_bell_bottom_ft) - inch(SPEC.pier_levelling_bedding_in),
    end_invert=_SG_WALL_BED_BOTTOM,
    trench_width=inch(12), trench_depth=inch(8),
    tile=DrainTile(diameter=inch(4), sock=True, discharge="DRW-SG-MAIN"),
    discharge_ref="DRW-SG-MAIN",
)

# ** IT NOW REACHES THE HOUSE STONE, AND IT USED TO STOP SIX INCHES SHORT. ** The trench
# ended at `_y_in_n` (-0'-10"), which is the porch deck's north edge and not a drainage
# elevation at all — the run stopped there because that is where the court's own geometry
# stops, and the sentence above ("North of the court it ties into the house collector") was
# the whole of the connection. `FB-B-S2`/`FB-B-S3`'s bedding stone starts 6" further north
# at -0'-4", so what lay between the two was six inches of undisturbed clay, and
# `drainage.outfall_connection` says so.
#
# `_HOUSE_BED_FACE_Y_FT` is that face, measured. Six inches is a trivial amount of digging
# and the defect it fixes is not trivial: this is the court's SECOND way out, and the leg
# that was missing is the one at the far end of it.
_HOUSE_BED_FACE_Y_FT = -4.0 / 12.0
GARDEN_OVERFLOW = FrenchDrain(
    uid="SGFD02AAAA", tag="FD-SG-OVERFLOW",
    path=(pt(ft(_field_x_mid), ft(_field_y_n + 1.0)),
          pt(ft(_field_x_mid), ft(_HOUSE_BED_FACE_Y_FT))),
    invert=_court_top - inch(SPEC.field_depth_in),
    trench_width=inch(6), trench_depth=inch(8),
    tile=DrainTile(diameter=inch(4), sock=False, discharge="SM-B-RADON"),
    discharge_ref="SM-B-RADON",
)

# The overflow crosses the grade beam as a pipe, not as a stone trench. Authoring its cast
# sleeve keeps the opening visible to reinforcement coordination and concrete takeoff.
GARDEN_OVERFLOW_SLEEVE = SleevePenetration(
    uid="SGSP01AAAA", tag="SP-SG-ARCH-OVERFLOW", host_ref="W-SG-ARCH",
    position=pt(ft(_field_x_mid), ft(_y_ax_mid)),
    pipe_diameter=inch(4), sleeve_diameter=inch(6),
    purpose=Service.DRAIN,
    axis="horizontal", center_elevation=GARDEN_OVERFLOW.invert + inch(2),
)
GARDEN_OVERFLOW_BEAM_PIPE = PipeRun(
    uid="SGPR01AAAA", tag="PR-SG-ARCH-OVERFLOW", system=PipeSystem.DRAIN,
    path=(pt(ft(_field_x_mid), ft(_y_ax_mid - 1.0)),
          pt(ft(_field_x_mid), ft(_y_ax_mid + 1.0))),
    diameter=inch(4), material="pvc",
    # A half-inch fall over this two-foot crossing supplies the minimum 1/4 in/ft slope;
    # its midpoint remains concentric with the sleeve above.
    elevations=(GARDEN_OVERFLOW.invert - _court_top + inch(0.25),
                GARDEN_OVERFLOW.invert - _court_top - inch(0.25)),
    serves=(),
)

GARDEN_SLAB = Slab(
    uid="SGS501AAAA", tag="SL-SG-FLOOR", assembly="GARDEN_COURT_SLAB",
    outline=(pt(ft(_x_in_w), ft(_y_in_s)), pt(ft(_x_in_e), ft(_y_in_s)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.rim_thickness_in),
    top_elevation=_court_top,
    openings=("FO-SG-FIELD", "FO-SG-BRKBM",
              "FO-SG-TOE-W", "FO-SG-TOE-E", "FO-SG-TOE-S",
              "FO-SG-TOE-N-W", "FO-SG-TOE-N-E"),
)

# `FloorOpeningPurpose.CHASE` on all five, and it is load-bearing rather than descriptive:
# CHASE is the one purpose `checks/mep/electrical._floor_opening_intervals` opts OUT of, and
# any other purpose would subtract the field's 11'-0", the beam's 19'-0" and the three toes'
# runs from the NEC 210.52 wall space a court still has its full perimeter to serve.
GARDEN_FLOOR_OPENINGS = [
    # The open centre.
    FloorOpening(uid="SGO001AAAA", tag="FO-SG-FIELD", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_field_x_w), ft(_field_y_s)),
                          pt(ft(_field_x_e), ft(_field_y_s)),
                          pt(ft(_field_x_e), ft(_field_y_n)),
                          pt(ft(_field_x_w), ft(_field_y_n)))),
    # ** FO-SG-ARCH IS RETIRED (2026-09-05). uid SGO002AAAA MUST NOT BE REUSED. ** It cut
    # the rim so W-SG-ARCH could stand 3 3/4" proud of the dropped court as a mow strip.
    # With the court flush again, `_grade_beam_top` (-112 15/16") IS `_rim_underside_in`
    # exactly — the same expression on both sides — so the beam is fully buried and the rim
    # pours straight over it and bears on it. There is nothing left to cut around, and a
    # chase here would open a 19'-0" slot in the court floor over a solid beam.
    # And the same cut around W-SG-BRKBM at the north end. The beam drops through the rim's
    # full 3 1/2" (its underside IS the rim's), so the slab cannot pour through it either —
    # it dies into the beam's south face and the beam becomes the court floor's north edge.
    # The full 14" section, not just the concrete: the 2" XPS break is north of the rim
    # anyway, and cutting the section as one keeps this outline derived off one number.
    FloorOpening(uid="SGO003AAAA", tag="FO-SG-BRKBM", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_x_in_w), ft(_y_ax_brkbm - _brkbm_half)),
                          pt(ft(_x_in_e), ft(_y_ax_brkbm - _brkbm_half)),
                          pt(ft(_x_in_e), ft(_y_ax_brkbm + _brkbm_half)),
                          pt(ft(_x_in_w), ft(_y_ax_brkbm + _brkbm_half)))),
    # --- the three retaining toes: the footings ARE the walking surface ------------
    #
    # ** ONE SLAB WITH FIVE HOLES, AND THE SLAB IS STILL THE THING THAT MATTERS. ** The rim
    # was pouring 5 1/2" above the footings it was meant to bear on, with fill in the gap;
    # `_wall_bottom` now tops the three strips out on the court plane, and these three voids
    # are what stops the rim occupying the same 3 1/2" of air. The rim's own pour drops from
    # ~3.96 cy to ~2.0 cy — only the porch bay and the beam's own line are left.
    #
    # ** DELETING `SL-SG-FLOOR` INSTEAD WOULD BE A DISASTER, AND SILENTLY. ** A `Footing`
    # resolves to `category == "footing"`, and `resolve/site_earth`,
    # `checks/code/mn_residential/egress._landing_surfaces`, `server/space_summary` and
    # `_frost_protection_footprints` ALL gate on `category == "slab"`. Take the rim away and
    # `open_excavation_floors()` returns nothing for this court: FT-B-S2's frost cover reads
    # ~86" instead of 8" and PASSES FOR THE WRONG REASON at 0 FAIL; `code.R311_3_exterior_
    # landing` loses D-B-PATIO's landing, which has only ~2 points of coverage margin;
    # `space_summary` puts 610 sf of open sky onto the basement's gross area. A north-bay
    # fragment does not rescue it either — `local_grade_elevation_m` measures
    # `here.distance(polygon) <= reach_m`, and a fragment over the porch bay leaves FT-SG-S
    # ~28' away, outside the 42" reach, with no excavation grade at all.
    #
    # Voids are the mechanism that gets both: `Slab.openings` resolves into
    # `ResolvedSolid.voids`, which `structural_solids_takeoff` and `envelope_layer_takeoff`
    # DO subtract, while `site_earth` and `_landing_surfaces` read `solid.outline` and ignore
    # them. So the rim bills net concrete and the court still reads as ONE excavation floor
    # and ONE R311.3 landing across all 494 sf.
    #
    # The three rectangles partition the court south of the beam exactly, with the field:
    # each runs from the wall's court face (`_x_in_*` / `_y_in_s`) out to that strip's own
    # `_field_*` edge, which is the same `_ret_toe_reach_ft` the field is derived from — so a
    # change to the footing width moves the toe and the field together or neither.
    #
    # ** THE NORTH EDGE IS `_y_ax_mid`, NOT `_field_y_n`, AND THE 6" DIFFERENCE WAS A REAL
    # LEAK. ** FT-SG-W2/E2 run north to `_y_ax_mid` (-11.0'); the FIELD stops 6" short of
    # that, at the grade beam's south face. Cut to the field's edge, each of these two left
    # a 4'-0" x 0'-6" tongue of footing under 3 1/2" of rim — 2.0 sf of concrete billed
    # twice and cast into itself, at 0 FAIL, because `structural.concrete_interference`
    # grades only ISOLATED pours and every FT-SG-* carries `under=`. The toes are cut to
    # the FOOTING now, which is what they were always for.
    FloorOpening(uid="SGO004AAAA", tag="FO-SG-TOE-W", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_x_in_w), ft(_field_y_s)),
                          pt(ft(_field_x_w), ft(_field_y_s)),
                          pt(ft(_field_x_w), ft(_y_ax_mid)),
                          pt(ft(_x_in_w), ft(_y_ax_mid)))),
    FloorOpening(uid="SGO005AAAA", tag="FO-SG-TOE-E", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_field_x_e), ft(_field_y_s)),
                          pt(ft(_x_in_e), ft(_field_y_s)),
                          pt(ft(_x_in_e), ft(_y_ax_mid)),
                          pt(ft(_field_x_e), ft(_y_ax_mid)))),
    # The south toe takes the full court width, so the two corner laps — where the west and
    # east strips run past the south one — fall inside it and are not double-cut.
    FloorOpening(uid="SGO006AAAA", tag="FO-SG-TOE-S", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_x_in_w), ft(_y_in_s)),
                          pt(ft(_x_in_e), ft(_y_in_s)),
                          pt(ft(_x_in_e), ft(_field_y_s)),
                          pt(ft(_x_in_w), ft(_field_y_s)))),
    # ** THE PORCH BAY'S TWO TOES (2026-09-05, second pass). ** FT-SG-W1/E1 rose to the
    # court plane with the other three, so the rim has to be cut off them the same way.
    #
    # They are 3'-0" of reach, not the retaining strips' 4'-0": the porch footings are the
    # shared 84" wide and centred on their wall (no `offset`), so they project
    # `footing_width/2` from the axis and only `footing_width/2 - _half` past the wall's
    # court face. Derived from the same field, so a footing-width change moves the cut.
    #
    # The north end stops on the veneer beam's south face rather than on the court's own
    # north edge, because `FO-SG-BRKBM` already voids the full width of that last 1'-0" and
    # two openings over one piece of floor is a hole cut twice.
    FloorOpening(uid="SGO007AAAA", tag="FO-SG-TOE-N-W", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_x_in_w), ft(_y_ax_mid)),
                          pt(ft(_x_ax_w + _ret_toe_reach_ft), ft(_y_ax_mid)),
                          pt(ft(_x_ax_w + _ret_toe_reach_ft), ft(_y_ax_brkbm - _brkbm_half)),
                          pt(ft(_x_in_w), ft(_y_ax_brkbm - _brkbm_half)))),
    FloorOpening(uid="SGO008AAAA", tag="FO-SG-TOE-N-E", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_x_ax_e - _ret_toe_reach_ft), ft(_y_ax_mid)),
                          pt(ft(_x_in_e), ft(_y_ax_mid)),
                          pt(ft(_x_in_e), ft(_y_ax_brkbm - _brkbm_half)),
                          pt(ft(_x_ax_e - _ret_toe_reach_ft), ft(_y_ax_brkbm - _brkbm_half)))),
]

# ** THE OPEN CENTRE IS A USGA PUTTING-GREEN PROFILE, ISOLATED BEHIND ONE ASSEMBLY. **
# 18" deep, topping out on the rim's own plane; the whole build-up lives in
# `GARDEN_PUTTING_GREEN` and changing what the court's middle is remains a one-line
# `assembly=` change.
#
# `GARDEN_PUTTING_GREEN` is authored `role="band"`, the same as the frost wings, and the
# reasoning is written out at the assembly. In short: a band carries no STRUCTURE layer,
# which `integrity.assembly_layers` requires of an `enclosure` and this build-up has none of;
# and a band is invisible to `resolve/site_earth._is_a_floor`, which is free here because
# SL-SG-FLOOR's outline already spans the whole court, and which removes the hazard of a
# frost finding ever naming SL-SG-FIELD instead of SL-SG-FLOOR.
GARDEN_FIELD = Slab(
    uid="SGS502AAAA", tag="SL-SG-FIELD", assembly="GARDEN_PUTTING_GREEN",
    outline=(pt(ft(_field_x_w), ft(_field_y_s)), pt(ft(_field_x_e), ft(_field_y_s)),
             pt(ft(_field_x_e), ft(_field_y_n)), pt(ft(_field_x_w), ft(_field_y_n))),
    thickness=inch(SPEC.field_depth_in),
    top_elevation=_court_top,
)

# ** SL-SG-STOOP IS RETIRED (2026-09-05). uid SGS503AAAA MUST NOT BE REUSED. **
#
# It existed for exactly one reason: when the court dropped 7 1/4" it left D-B-PATIO's
# threshold 14 1/2" above the floor in front of it — past `_MAX_NONREQUIRED_STEP_DOWN`
# (7 3/4") by nearly a riser, with no landing, which is a hard R311.3 FAIL. So a 23.7 sf
# block of the OLD flush floor was left standing where the door needed it, and the court
# fell away from it on three sides.
#
# The court is flush again, so the whole 494 sf floor IS that plane. The landing is not
# deleted — it is everywhere. `_landing_patch` projects x 18'-10"..23'-10",
# y -3'-5 3/8"..-0'-5 3/8" and `_LANDING_COVERAGE` wants 85% of it; the court's north 5"
# strip (the insulation gap to the house) can never be covered by anything, which caps any
# surface here at 87%, and the rim slab covers the patch's full width the way the stoop did.
#
# `GARDEN_STOOP` goes unreferenced with it. Kept in plan/assemblies.py on the
# EXT_2X6_SWINBURNE precedent — an unreferenced assembly saves no test churn, it
# preserves the reasoning — and its prices.toml row falls to 0 SF.

# --- FPSF wing insulation under the garden slab, along the house ------------------------
#
# IRC R403.3, Figure R403.3(3): the heated-building-adjoining-an-unheated-slab case, which is
# what a heated basement beside an open sunken court is. Table R403.3(1) at design AFI 2500
# (Minneapolis-St Paul) wants R-1.7 over B = 24" along the wall and R-4.9 over C = 40" at the
# corners; SG_FROST_WING_XPS1/2 in plan/assemblies.py carry R-5 and R-10 and the citation.
#
# WHY THIS EXISTS: measuring every footing against one global grade plane would pass FT-B-
# S1/S2/S3 with only 8" of cover below the garden floor. (It also passed the veneer plinth
# FT-B-BRICK, which had 2" of NEGATIVE cover, until that plinth was retired 2026-09-05.) Frost depth is measured from the lowest adjacent grade, and beside these footings
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
# The wings sit directly under the SL-SG-FLOOR rim, so they followed the court down:
# rim top -9'-8 11/16" less its own 3 1/2" is -10'-0 3/16", which is the wings' top.
_WING_TOP = inch(_rim_underside_in)
_WING_ALONG_FT = 24.0 / 12.0   # Table R403.3(1) dimension B
_WING_CORNER_FT = 40.0 / 12.0  # Table R403.3(1) dimension C
# ** THE WINGS RETRACT TO THE PORCH TOES, AND THIS IS NOT A DETAIL. ** They used to start at
# the wall inner faces (8'-6"/27'-6"). At the old level that was air; at -10'-0 3/16" it is
# 2 3/4" INSIDE FT-SG-W1/E1, whose 7'-0" strips reach x 11'-6"/24'-6" — nothing fits over a
# toe whose top is 3/4" below the finished surface. `_frost_protection_footprints` tests
# plan overlap ONLY, never elevation, so foam left at the old x would have passed every
# check while lying about where it is. Start at the toe instead.
#
# Table R403.3(1)'s B and C dimensions are UNCHANGED — the wings are the same 40" and 24"
# skirts, just begun 3'-0" further in — and the R403.3 argument gets better rather than
# worse: outboard of x 11'-6"/24'-6" the re-entrant corner is protected by FT-SG-W1/E1's own
# strip bearing on 42" of drained NFS stone, which is soil replacement, not foam.
_WING_X_W = (_x_in_w - _half) + SPEC.footing_width_in / 24.0   # 11.5, FT-SG-W1's court edge
_WING_X_E = (_x_in_e + _half) - SPEC.footing_width_in / 24.0   # 24.5, FT-SG-E1's

FROST_WINGS = [
    # The two re-entrant corners, where the garden's own east and west retaining walls meet
    # the house and frost drives in from two directions at once: C = 40" each way, 2" XPS.
    Slab(uid="SGFW01AAAA", tag="SL-SG-FROST-W", assembly="SG_FROST_WING_XPS2",
         outline=(pt(ft(_WING_X_W), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_WING_X_W + _WING_CORNER_FT), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_WING_X_W + _WING_CORNER_FT), ft(_y_in_n)),
                  pt(ft(_WING_X_W), ft(_y_in_n))),
         thickness=inch(2.0), top_elevation=_WING_TOP),
    Slab(uid="SGFW02AAAA", tag="SL-SG-FROST-E", assembly="SG_FROST_WING_XPS2",
         outline=(pt(ft(_WING_X_E - _WING_CORNER_FT), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_WING_X_E), ft(_y_in_n - _WING_CORNER_FT)),
                  pt(ft(_WING_X_E), ft(_y_in_n)),
                  pt(ft(_WING_X_E - _WING_CORNER_FT), ft(_y_in_n))),
         thickness=inch(2.0), top_elevation=_WING_TOP),
    # The run between them, along the wall: B = 24", 1" XPS.
    Slab(uid="SGFW03AAAA", tag="SL-SG-FROST-N", assembly="SG_FROST_WING_XPS1",
         outline=(pt(ft(_WING_X_W + _WING_CORNER_FT), ft(_y_in_n - _WING_ALONG_FT)),
                  pt(ft(_WING_X_E - _WING_CORNER_FT), ft(_y_in_n - _WING_ALONG_FT)),
                  pt(ft(_WING_X_E - _WING_CORNER_FT), ft(_y_in_n)),
                  pt(ft(_WING_X_W + _WING_CORNER_FT), ft(_y_in_n))),
         thickness=inch(1.0), top_elevation=_WING_TOP),
]

# ============================================================================
# Heat-pump equipment pad, in the yard pocket east of the porch.
# ============================================================================
# EQ-M-HP1-OD and EQ-M-HP2-OD (authored in plan/electrical.py) stood on FS-SG-DECK at +10'
# until 2026-09-02. They stand on the ground now, and the whole detail this file used to
# carry — eight lags through a watertight plank, sixteen sacrificial blocks, four
# reinforcements, two traced condensate runs — went with them. See
# notes/heat_pump_ground_pad.md; notes/superseded/heat_pump_deck_mounting.md is SUPERSEDED and kept
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
# ** HP_PAD: x 29'-0"..32'-7", y -3'-4"..-0'-10" — 8.96 sf, 0.11 cy at 4". ** The north
# edge stops 3" short of the cladding rather than butting it: there is no isolation joint to
# detail if the pad never touches the house, and a 3" gap sheds the wall's runoff into
# gravel instead of against a lip. The west edge is HP2's own cabinet face, 6" clear of
# W-SG-E1 — the row is tucked as far west as 40 5/32" + 12" + 39" allows (owner, 2026-09-04:
# a condenser behind the SE corner is quieter down the whole east side yard than one out
# past it, and the living room takes the difference).
#
# ** IT SHRANK ON 2026-09-04 WHEN HP1 CROSSED TO THE NORTH FACE. ** It was 19.6 sf carrying
# a two-unit row that oversailed the pocket's SE corner by 7 1/6"; the east edge is now
# 2 3/4" past HP2's cabinet by the same rule that set the old one, and there is no oversail
# left at all — HP2 alone stops 3'-7 27/32" short of the corner. What the pocket keeps is
# one condenser under WIN-M-LIV-S1 instead of two, and 10.6 sf less concrete.
#
# ** THE DISCONNECTS PAID FOR THE TUCK. ** At x 31'-0" the row left a 30" band of the house's
# south face for them at NEC 110.26(A) working space; tucked, it does not, and they hang on
# W-SG-E1's east face at 2'-2" above grade instead of the house's at 6'-4". plan/electrical.py
# argues that trade where it is made.
_HP_PAD_X0, _HP_PAD_X1 = 29.0, 32.583333
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
#   EQ-M-HP2-OD  MUL30HP230V1R32AO   25"      x 15 19/32"  145.5 lb
#
# (EQ-M-HP1-OD's FXU24HP230V1R32AO pattern, 29 3/4" x 15 9/16", now lives in
# params/hp1_north_pad.py with the unit.)
#
# The cabinet sits SQUARE to the plan (`rotation=deg(0)`, discharge facing south) since
# 2026-09-03 — it was rotated 90 degrees and facing east before that. The long axis runs
# in x now, so the WIDTH pitch is in x and the DEPTH pitch in y, and the leg pattern
# transposes with it. The rotation did NOT change on 2026-09-04; only the centre did, when
# the row crossed the pocket to sit against the house and the flight took the south half.
# The centre is the unit's own, authored in plan/electrical.py — the two files cannot
# import each other, so a unit that moves must move here too.
#
# The published foot pattern is WIDER than the cabinet across the depth (15 19/32" of feet
# under a 16 13/16" casing on this one; it was 15 9/16" under 14 9/16" on HP1), so a leg can
# stand proud of a face — which is why the pad's north edge is a derived number rather than
# "the cabinet line plus a bit".
# `test_catlin_outdoor_structures.py` is what holds the two together now that the deck check
# no longer does.
# ** THE "A" STAND IS GONE (2026-09-04). ** EQ-M-HP1-OD crossed to the north face with its
# air handler (params/hp1_north_pad.py), taking PT-SG-HPA1..4 and CN-SG-HPA1..4 with it —
# both are comprehensions over this table, so deleting four rows deletes eight elements.
# What is left in the pocket is HP2 alone.
_HP_STAND_AT = (
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
#: Half the dressed 6x6 the two centre pillars are, read off ``SPEC.pillar_size`` rather
#: than written down, so the beam ends and the hanger stations cannot drift from the member
#: they land on. Used by MAIN_NODES below and by the base/hanger connectors.
_half_pillar_in = cross_section(SPEC.pillar_size).width_m / 0.0254 / 2.0  # 2.75

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
    # ** THE FOUR BEAM ENDS CAME OFF THE COLUMN AXIS ON 2026-09-14. ** Each porch beam used
    # to run to N-SGM-COL / N-SGM-FCOL — the column's own axis — because its end BORE on the
    # 12" pour. The centre pillar now stands on that pour (see ``_WALL_UNDER_PILLAR``), so
    # the two beams at each line stop at the pillar's east and west FACES instead and hang
    # from it (CN-SG-HGR-C*, HU212-3). 2 3/4" is half the 5 1/2" post, which is why it is
    # written as the post's half-width rather than as a number.
    #
    # N-SGM-COL and N-SGM-FCOL are KEPT. Nothing frames to them now, but they are the two
    # column axes and the beam ends are authored as offsets FROM them; deleting them would
    # leave the offsets measured off nothing. Their uids stay spent either way.
    Node(uid="SGNM07AAAA", tag="N-SGM-COLW",
         position=pt(ft(_cx) - inch(_half_pillar_in), ft(_y_col))),
    Node(uid="SGNM08AAAA", tag="N-SGM-COLE",
         position=pt(ft(_cx) + inch(_half_pillar_in), ft(_y_col))),
    Node(uid="SGNM09AAAA", tag="N-SGM-FCOLW",
         position=pt(ft(_cx) - inch(_half_pillar_in), ft(_y_ax_front))),
    Node(uid="SGNM10AAAA", tag="N-SGM-FCOLE",
         position=pt(ft(_cx) + inch(_half_pillar_in), ft(_y_ax_front))),
]

# Two 3-ply KDAT 2x12 back beams: cast column -> side-wall pockets (two ~9'6" spans).
# **Not "treated LVL"** — that product does not exist at this depth, and ``SPEC.back_beam``
# has read "3-2x12" with BEAM_KDAT since 2026-08-23.
BACK_BEAMS = [
    Beam(uid="SGBM01AAAA", tag="BM-SG-BKW", start_node="N-SGM-COLW", end_node="N-SGM-NW",
         size=SPEC.back_beam, assembly="BEAM_KDAT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-COL", "W-SG-W1")),
    Beam(uid="SGBM02AAAA", tag="BM-SG-BKE", start_node="N-SGM-COLE", end_node="N-SGM-NE",
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
    Beam(uid="SGBM03AAAA", tag="BM-SG-FRW", start_node="N-SGM-FCOLW", end_node="N-SGM-FW",
         size=SPEC.back_beam, assembly="BEAM_WHITE_PAINT",
         top_protection=_BEAM_TAPE_WIDE,
         bearing_refs=("PT-SG-FCOL", "W-SG-W1")),
    Beam(uid="SGBM04AAAA", tag="BM-SG-FRE", start_node="N-SGM-FCOLE", end_node="N-SGM-FE",
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
                  pt(ft(_x_in_e), ft(_y_porch_deck_n)), pt(ft(_x_in_w), ft(_y_porch_deck_n)))

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
# top so the balcony's front columns bear on them, and W-SG-W2/E2 start 18" further south,
# so the guard runs out over the side walls' own tops. (Those two carried a +0'-6" and then
# a +0'-2" curb above this plane; the tops are flush since 2026-09-10 and the guard's own
# base elevation never read that curb.) RL-SG-BALCONY is
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
_PORCH_GUARD_PATH = (pt(ft(_x_in_w), ft(_y_porch_deck_n)), pt(ft(_x_in_w), ft(_y_ax_front)),
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
    path=(pt(ft(_x_in_e), ft(_PORCH_STAIR_Y0)), pt(ft(_x_in_e), ft(_y_porch_deck_n))),
    kind=RailingKind.METAL_SURFACE_MOUNT,
    height=ft(SPEC.railing_height_ft),
    base_elevation=_porch_walking_surface,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="surface",
    assembly="RAILING_DARK_METAL",
    infill="balusters", baluster_spacing=inch(4))

# A planter placed directly against the retaining wall leaves only 10 inches of concrete
# above its 30-inch soil surface.  The existing 42-inch surface-mounted metal system is
# therefore continued around the court edge for that variant.  Keeping this as authored
# geometry makes the extra guard visible in drawings and measurable by the takeoff engine.
RAISED_BED_GUARDS = []
if OPTION.needs_court_guard:
    RAISED_BED_GUARDS.append(Railing(
        uid="SGRA08AAAA", tag="RL-SG-COURT", type_ref="RAILING-EXT-ALUMINUM-SURFACE",
        path=(pt(ft(_x_in_w), ft(_y_ax_mid)),
              pt(ft(_x_in_w), ft(_y_in_s)),
              pt(ft(_x_in_e), ft(_y_in_s)),
              pt(ft(_x_in_e), ft(_y_ax_mid))),
        kind=RailingKind.METAL_SURFACE_MOUNT,
        height=inch(42), base_elevation=_ret_top,
        post_spacing=inch(60), post_size="2x2", rail_count=2, mount="surface",
        assembly="RAILING_DARK_METAL", infill="balusters", baluster_spacing=inch(4)))

# The south leg's post stations, in feet — the run over BM-SG-FRW/FRE that has no wall top
# under it and therefore needs blocking. Taken as the middle segment of the guard path so
# the two corner posts (which DO land on W-SG-W1/E1's tops) are excluded.
# ``_cx`` is excluded as well, and that exclusion is a STRUCTURE, not a gap: PT-SG-BF2 —
# a 5 1/2" white-painted 6x6 carrying a third of the balcony — stands on that station, on
# this axis, since it came onto the beam line. The guard's rails frame into the pillar and
# there is no 2x2 post there and no blocking under one, because the thing they would be
# backing is already a column. Same idiom as ``_BALCONY_GUARD_STATIONS``: derive the run,
# then say out loud which station the structure already occupies.
_PORCH_GUARD_SOUTH_STATIONS = [
    x for x, y in _guard_post_stations(
        [(_x_in_w, _y_ax_front), (_x_in_e, _y_ax_front)], 60.0 / 12.0)
    if _x_in_w + 0.01 < x < _x_in_e - 0.01 and abs(x - _cx) > 0.01
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
# Second (balcony, ~10'): four 12" cast columns + two 6x6 pillars, three 3-1/2" x
# 11-7/8" treated glulam beams, aluminum deck.
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
# BM-SG-BLC is FLUSH (2026-09-16): its top is the deck datum and the joists hang in it, so
# its soffit — and the two centre pillar tops — sit a joist depth above the outer pair's.
_balcony_centre_beam_top = ft(SPEC.balcony_level_ft)
_balcony_centre_beam_soffit = _beam_soffit  # 9.010'
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
# ``("F", 2)`` and ``("R", 2)`` are not walls at all: the two CENTRE pillars stand on the
# CONCRETE COLUMNS, on the same ``_back_beam_soffit`` all four porch beams land on. Those
# two entries drive each pillar's ``supported_by``, its base elevation, its length AND its
# base connector's ``connects`` and elevation, because the bases are generated from
# ``PILLAR_BEARINGS`` below. **Post-on-post is a supported path** — ``resolve_columns_and_beams``
# republishes each post's resolved top as it goes (envelope.py), precisely so a post can
# stand on a concrete pier; ``breezeway.py``'s Pad -> PR-BW-* -> PT-BW-* is the live
# precedent. Ordering holds because PT-SG-FCOL / PT-SG-COL are in ``BASEMENT_ELEMENTS`` and
# the pillars in ``SECOND_ELEMENTS``.
#
# ** 2026-09-14: BOTH CENTRE PILLARS CAME BACK DOWN ONTO CONCRETE. ** See
# ``_DECK_BORNE_PILLAR_BEARINGS`` below for the arrangement this reverses and why. The whole
# of the retirement is here: ``engineering/post_bearing.py`` enumerates on exactly one
# predicate — a ``Post`` whose ``supported_by`` names a ``FloorSystem`` — so wood-on-wood
# Fc-perp crushing stops being a question the moment these two name a post instead. What
# makes it buildable rather than a longer column is that the four porch beams now HANG off
# the pillar's east and west faces (HU212-3) instead of being seated beside it, so the pour
# never has to span from a beam face to a pillar face and PT-SG-FCOL stays 12" round.
_WALL_UNDER_PILLAR = {
    ("R", 1): ("W-SG-W1", _porch_top), ("R", 3): ("W-SG-E1", _porch_top),
    ("F", 1): ("W-SG-W1", _porch_top), ("F", 3): ("W-SG-E1", _porch_top),
    ("R", 2): ("PT-SG-COL", _back_beam_soffit),
    ("F", 2): ("PT-SG-FCOL", _back_beam_soffit),
}
#: REVERT RECORD, 2026-09-14 — the deck-borne arrangement this replaced, kept in place and
#: referenced by nothing, the ``EXT_2X6_SWINBURNE`` convention. Restoring these two lines
#: (i.e. dropping the ("R", 2) / ("F", 2) entries above so the ``.get()`` default applies)
#: puts both centre pillars back on the porch framing and brings
#: ``post_bearing/PT-SG-BF2`` and ``post_bearing/PT-SG-BR2`` back into the engineering
#: register. The ``JoistReinforcement`` packs that went with it are
#: ``_DECK_BORNE_PILLAR_REINFORCEMENTS`` beside FS-SG-PORCH's own; the five-part base tie is
#: recorded at ``_DECK_BORNE_BASE_TIE``.
_DECK_BORNE_PILLAR_BEARINGS = {
    ("R", 2): ("FS-SG-PORCH", _porch_walking_surface),
    ("F", 2): ("FS-SG-PORCH", _porch_walking_surface),
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
#: The rear row's rise, DERIVED from the fall and the run between the two bearing rows.
#:
#: ** 2026-09-14: 2" BECAME 1 27/32", AND THE SLOPE IS NOW THE AUTHORED THING. ** The rise
#: was a flat 2" and the fall was whatever that worked out to over whatever run the rows
#: happened to be at — 0.27 in/ft. Owner's call: the number that should be held is 1/4" per
#: foot, which is the trade standard for a walking deck and still 2x AridDek's published
#: 1/8 in/ft minimum. Over the 7'-4" between the rows that is 1.833", 5/32" less post than
#: the flat 2" was.
#:
#: **That 5/32" is load-bearing, and not only for drainage.** PT-SG-BR2 is the tallest of
#: the six pillars and since it came down onto PT-SG-COL it is graded against IRC Table
#: R507.4, which caps a 6x6 at 10'-0" for this deck's 48.3 ft2 tributary. At the flat 2"
#: the wood came out at 120.016" — 1/64" over, with the ABU66SS standoff and the
#: CCQ46SDS2.5 seat already taken off it (resolve/envelope.py::_post_connector_insets).
#: At 1/4 in/ft it is 119.85", inside by 5/32". **A reader raising the fall again has to
#: check that limit**: every 1/64 in/ft of extra fall is another 1/64" of post, and there
#: is 5/32" of room.
_rear_pillar_rise_in = SPEC.balcony_fall_in_per_ft * (_y_rear_pillar - _y_front_pillar)
_PILLAR_ROWS = (("R", _y_rear_pillar, inch(_rear_pillar_rise_in)),
                ("F", _y_front_pillar, ft(0)))

# ** THE DRAINAGE SLOPE, AND WHERE THE ENGINE USED TO THROW HALF OF IT AWAY. **
#
# `_rear_pillar_rise_in` raises the rear pillar row so the deck falls south, away from the
# house. It is `SPEC.balcony_fall_in_per_ft` — 1/4" per foot since 2026-09-14 — times the
# run between the two bearing rows, against AridDek's recommended minimum of 1/8 in/ft:
# twice the minimum, and the trade's own number for a deck that has to shed rather than
# pond. It was a flat 2" until then, which over this run was 0.27 in/ft.
#
# Until 2026-09-12 the rise reached the POSTS and stopped there. ``_resolve_post``'s
# docstring is explicit that it shortens the authored height rather than overriding the top
# precisely so this offset survives — but ``_resolve_beam`` emitted a flat prism, so the
# beams never tilted. Measured off out/model.json at the time: PT-SG-BR1/2/3 topped out at
# 102.875" and the three beam soffits sat flat at 100.875". **Every rear column ran 2" up
# inside the beam it carries, and `haus check` reported nothing** —
# `structural.concrete_interference` is scoped to isolated pours and nothing grades a column
# tangent to a beam.
#
# Two answers the old TODO line asked for, so they are not asked again:
#   * **A chamfer cannot produce slope.** A chamfer is a corner bevel. The fall runs N-S,
#     ALONG the beams.
#   * **Sleepers are a dead end both ways.** On the joists they would run N-S, parallel to
#     the AridDek plank, and the plank would lose its perpendicular bearing. On the beam
#     tops they move the same interference from column-into-beam to joist-into-beam,
#     because ``FloorSystem.top_elevation`` is a single value too.
#
# What fixes it is ``Beam.top_rise_end``: the beam is one member out of level, which is what
# it is on site. Rise per inch of northward run, measured between the two BEARING rows (not
# the beam ends — the beam oversails both, 20" north and 8" south, and taking the slope off
# the ends would mis-state it by a quarter of an inch).
_BEAM_RISE_PER_IN = _rear_pillar_rise_in / ((_y_rear_pillar - _y_front_pillar) * 12.0)


def _balcony_rise_at(y_ft):
    """Beam soffit at plan ``y``, relative to the FRONT bearing plane.

    The front row is the datum because it is the low end and the one that did not move:
    ``_balcony_beam_soffit`` is where PT-SG-BF1/2/3 top out, and the rear row is exactly
    ``_rear_pillar_rise_in`` above it.
    """
    return inch((y_ft - _y_front_pillar) * 12.0 * _BEAM_RISE_PER_IN)

# PT-SG-BF2 moves NORTH onto the porch deck, 3" inside the front beam axis — the exact
# mirror of PT-SG-BR2's 3" south of the back beam line, and for the same two reasons. It
# used to stand on PT-SG-FCOL's top, 19 1/2" below the porch walking surface, which made it
# 19 1/2" longer than its five neighbours and forced that column to 20" round so one pour
# could span from the beams' north face to the pillar's south face. Standing it on the deck
# instead makes all six pillars the same member and lets the column shrink to the 12" every
# other cast column in this garden is.
#
# ** 2026-09-03 (later the same day): THE OFFSET IS ZERO. BF2 SITS ON THE FRONT BEAM AXIS. **
# It was 3", and the two reasons it was 3" have both been answered rather than deleted:
#
#   * **The cap's butyl.** At the axis the pillar lands square on TR-SG-CAP-FRW/FRE, and a
#     stainless part bearing on 0.019" aluminium coil in a wet exterior location pits the
#     coil (it is anodic) while anchoring through it penetrates the butyl that IS the
#     dielectric between that coil and the copper-treated KDAT. The answer is the EPDM or
#     HDPE isolator the detail below already prescribes for exactly this case — "a base that
#     ever does cross a cap needs an EPDM or HDPE isolator pad and a written detail". This is
#     that case, and this is that detail.
#   * **``cantilever.py::_band``'s epsilon.** A pillar landed exactly on the bearing line
#     reads as inside the overhang and reports a 0" overhang about a joint that does not
#     exist. That is still true — but it reports it about BR2 too, which has been on the
#     bearing line all along, and the finding it produces is silent here.
#
# ** WHAT 3" COST, AND IT IS THE WHOLE REASON THIS MOVED. ** The porch joists used to END
# on the front beam axis with 2-1/4" of bearing; the beam's north face is 2-1/4" north of
# it. At 3" north, BF2 stood 3/4" PAST that face, on joists whose only contact with the beam
# was those 2-1/4". ``post_bearing/PT-SG-BF2`` grades that plane at 672 psi against a wet
# Fc-perp of 285 — d/c 2.36, the worst number in the garden frame, and nothing in the model
# saw it until that calc existed. On the axis the post is over the bearing itself, the joist
# ply pack takes the load into the beam it already lands on, and the same limit state came
# back at d/c 0.76.
#
# ** AND A THIRD ANSWER, THE SAME DAY: THE JOISTS NOW CROSS THE BEAM. ** ``JoistSpec``
# carries ``cantilever_start = 2 3/4"``, so the joists run past the front beam's north face
# instead of dying on its centreline. That is not a tweak to the number above, it changes
# which case the NDS is in: ``_beam_bearing_in`` measures the overlap of the beam's plan
# width with the JOIST FIELD's extent, so the contact goes 2-1/4" -> 4-1/2" and BOTH planes
# at this pillar stop being END bearings, so §3.10.4's C_b applies at each (1.068 on the
# joist top, 1.083 on the beam). d/c 0.76 -> **0.35**, with the pillar not moving an inch.
# A joist should bear ACROSS its beam rather than stop on its axis; that this also halves
# the governing ratio is the check agreeing with the framing rather than a second effect.
#
# ** IT ALSO MAKES THE PILLAR A GUARD POST. ** x = 18'-0" is an RL-SG-PORCH south-leg post
# station, and at the axis the pillar coincides with it exactly. The guard's rails frame
# into the 6x6 rather than into a 2x2 standing 3" away from it — see
# ``_PORCH_GUARD_SOUTH_STATIONS``, which now excludes that station, and the merged
# JoistReinforcement below, which was two blocks 3" apart on one joist line.
#
# Kept as a named constant at 0.0 rather than deleted: the offset was a decision, the
# reasoning above is what replaced it, and a future reader moving this pillar needs both.
_BF2_NORTH_OF_FRONT_AXIS_IN = 0.0
_y_bf2 = _y_ax_front + _BF2_NORTH_OF_FRONT_AXIS_IN / 12.0
# ** 2026-09-14: PT-SG-BR2 CAME BACK ONTO THE COLUMN AXIS, AND THE 3" IS SPENT. **
# ``_REAR_PILLAR_SOUTH_OF_COL_IN`` bought one thing: it kept a DECK-BORNE pillar out of
# ``cantilever.py::_band``'s epsilon, which reports a 0" overhang about a joint that does
# not exist. That pillar is not deck-borne any more — it stands on PT-SG-COL — so
# ``structural.cantilever_point_load`` never reaches it and the offset buys nothing.
#
# What it COSTS once the pillar is on concrete is real, and is why this is not cosmetic:
# a 5 1/2" post centred 3" off the axis of a 12" round puts two of its corners at
# sqrt(2.75^2 + 5.75^2) = 6.37" from the centre, 3/8" OUTSIDE the pour, while its north 2"
# laps BM-SG-BKW/BKE's south 2". On the axis the post is square on the round with 1/2" of
# edge all the way about, and the two back beams hang off its east and west faces exactly
# as the two front beams hang off PT-SG-BF2's.
#
# BR1/BR3 do NOT move: they bear on W-SG-W1/E1 and ``_REAR_PILLAR_SOUTH_OF_COL_IN`` is
# still theirs. The rear row is therefore 3" out of line at its centre, which costs
# nothing — the three balcony beams are three separate members, each with its own pair of
# bearings, and BM-SG-BLC simply gains 3" of back span (88" -> 91") and loses 3" of north
# overhang (20" -> 17") against an R507.5.1 limit that rises with it (22" -> 22.75").
_y_br2 = _y_col
# The four CORNER pillars became 12" cast concrete columns on 2026-09-03 and the two CENTRE
# pillars did not. That split is the whole redesign in one loop: four columns FIXED at the
# base (doweled into the 12" wall tops of W-SG-W1/E1, whose axis they stand on, so the round
# is flush with both wall faces) are the balcony's entire lateral system, which is what let
# the eight knee braces and two E-W brace rails be deleted outright. The centres stay wood
# 6x6 bearing wood-on-wood, strapped and angled down onto the joists — leaning columns,
# tied in by the deck
# diaphragm — because nothing asks them to carry moment and a 6x6 is a third the cost of a
# formed column.
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
        if _i == 2:
            _y = _y_bf2 if _row == "F" else _y_br2
        PILLAR_BEARINGS[_tag] = (_bears_on, _base)
        PILLARS.append(Post(uid=f"SGPB{_i}{_row_index}AAAA", tag=_tag,
                            position=pt(ft(_x), ft(_y)),
                            size=(SPEC.corner_column_size if _is_corner
                                  else SPEC.pillar_size),
                            height=_beam_soffit - _base + _rise,
                            supported_by=_bears_on,
                            vertical_reinforcement=(SPEC.corner_column_cage
                                                    if _is_corner else None),
                            reinforcement=(_CAST_COLUMN_CAGE if _is_corner else None),
                            assembly=("SUNKEN_GARDEN_COLUMN_12" if _is_corner
                                      else "POST_WHITE_PAINT_DF")))

# The two CENTRE pillars are now alike again, and that is the point.
#
# **PT-SG-BF2 stands on the porch framing**, the exact mirror of PT-SG-BR2: joist ->
# BM-SG-FRW/FRE -> PT-SG-FCOL -> footing. It sits ON the front beam axis (see
# `_BF2_NORTH_OF_FRONT_AXIS_IN`), and since the joists were given a 2 3/4"
# ``cantilever_start`` they CROSS that beam rather than stopping on it, so the post is over
# a full 4-1/2" of bearing at both planes. It stood on PT-SG-FCOL's top until 2026-09-03,
# 19 1/2" below the walking surface and 19 1/2" longer than its five neighbours, which is
# what forced that column to 20" round. Moving it north makes all six pillars one member and
# lets the column be the 12" every other cast column here is; both centre posts now take
# squash blocks and a plank cut-out, and both bear on framing rather than on a pour.
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
# ``source``: **cut a ~9"-square hole through the composite plank at PT-SG-BR2 and at
# PT-SG-BF2 so each POST bears on the 3-ply joist pack below, not on the plank.** ~9", not
# the 4" this note said until 2026-09-03: the post alone is 5-1/2" square, and the cut has
# to pass the L50Z angle legs lying on the pack beside it as well. Trex's own
# specification says composite decking "cannot be used as structural material; any load
# bearing area will need to be framed and supported before the composite material can be
# attached". Strength is not the issue — a 6x6 spreads ~85 psi on the plank. The two
# that are:
#   * CREEP. Sustained load at the 140-160 degF summer surface temperature of a dark
#     composite plank settles these two pillars relative to the four that bear on concrete,
#     and that differential takes the balcony's watertight aluminium plank out of plane.
#     Nothing in the model would see it.
#   * REPLACEABILITY. The plank is a wear layer. You cannot pull a board out from under a
#     6x6 carrying a third of a balcony without shoring the balcony first.
#
# **BF2 LANDS ON THE BEAM CAP, AND THAT STILL NEEDS THE ISOLATOR.** Its 3" offset used to
# keep it north of TR-SG-CAP-FRW/FRE's north turn-down; on the beam axis it sits square on
# the cap. The hazard is unchanged: a galvanised part bearing on 0.019" aluminium coil in a
# wet exterior location drives a dissimilar-metal couple, and anchoring through it
# penetrates the butyl tape that IS the dielectric between that coil and the copper-treated
# KDAT. **An EPDM or HDPE isolator pad goes between the connector steel and the cap, and
# every fastener penetration is sealed.** The base tie is now an MSTA12Z strap on the west
# face and an L50Z angle on the north face rather than a cap channel wrapping the joint, so
# the pad is smaller and the penetration count is lower — but the detail is the same detail,
# and the ~9" plank cut-out is where it gets installed. See
# `_BF2_NORTH_OF_FRONT_AXIS_IN` for why the crossing is worth making.

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
# 3-2x12 did. (The glulams carry no aluminium cap since 2026-09-16; butyl only.)
# The published row that answers all three balcony beams' spans — a PRESCRIPTIVE read
# (2026-09-11; they were engineering items before). Anthony/Canfor tabulate this exact
# section against this exact joist span, and a reviewer opens the guide and closes the
# question. The guide's values are DRY-use, which is why `structural.deck_beam_span` prints
# the NDS wet-service arithmetic beside the row as an advisory rather than dropping it:
# see notes/balcony_moment_columns.md §5.
_BALCONY_BEAM_PUBLISHED = PublishedSpan(
    source="Anthony Forest Products / Canfor Power Preserved Glulam Deck Guide (2020), Table 2 \"Beam Spans\" (maximum 2' cantilever)",
    table="40 psf live + 10 psf dead, 10' joist span, 10' beam span: 3-1/2\" x 11-7/8\" Power Preserved Glulam",
    member="3.5x11.875",
    span=ft(10),
    carried_span=ft(10),
    load_psf=50.0,
    condition="the guide's values are DRY-USE and these beams stand in weather, so the NDS wet-service cross-check beside this row is the governing arithmetic, not a duplicate; cantilevers are within the table's 2' maximum (1'-8\" here, and graded separately by R507.5.1); 3\" bearing on the cast columns; the columns' own base moments are a separate engineered item")

# ** THE THREE BEAMS ARE TILTED, AND THEY ARE AUTHORED SOUTH-END-FIRST ON PURPOSE. **
#
# ``Beam.top_rise_end`` raises the END node relative to the START, and the START is the end
# the beam's top elevation is answered at — here the derived one, `elevation - joist_drop`
# from ``_bearing_stack_drops``. So the LOW (south) end has to lead: N-SGB-S* -> N-SGB-N*.
# Nothing reads the node pair as a direction (every consumer treats it as a segment), so the
# swap costs nothing, and putting the high end second is what makes the rise read as a rise.
#
# ** ONLY BM-SG-BLC AUTHORS ``top_elevation`` — IT IS FLUSH-FRAMED (2026-09-16). ** The
# joists hang either side of it on LUS28Z hangers, the way a flat roof frames, and the two
# outer glulams keep the joists ON TOP so the 9" drip cantilever and the four cast columns
# stay exactly as they were. Pinning a beam takes it out of ``_bearing_stack_drops``, so
# PT-SG-BR2/BF2 grow the joist depth (~10.6'/10.4', inside 2018 IRC Table R507.4's 14' for a
# 6x6) with no edit to their heights. The outer pair stays derived on purpose: `deck_post`
# reads the corner columns' `Post.height` as the moment arm, hand-worked at 108.125" in
# notes/balcony_moment_columns.md, and that sealed demand does not move.
#
# The datum at the south NODE is the deck's own walking surface. For the outer pair it stays
# derived and lands at the south NODE, which is 8" south of the front
# bearing (`_FRONT_COLUMN_CANTILEVER_IN` + the round's radius). At 0.0227 in/in that is
# **0.18" of seat gap, identical at all six columns** — the slope between the bearings is
# exact, and the uniform 3/16" is taken up in the 1/2"-1" SS316-SHIM-35 standoff pack that is
# already at every one of these seats and exists for precisely this tolerance. Before this
# change the rear three columns ran **2" INSIDE** their beams. See
# notes/balcony_differential_movement.md §2.
_balcony_beam_rise = _balcony_rise_at(_y_in_n) - _balcony_rise_at(_y_balcony_front)
BALCONY_BEAMS = [
    Beam(uid="SGBB01AAAA", tag="BM-SG-BLW", start_node="N-SGB-SW", end_node="N-SGB-NW",
         size=SPEC.balcony_beam, assembly="BEAM_GLULAM_TREATED",
         published_span=_BALCONY_BEAM_PUBLISHED,
         top_protection=_BEAM_TAPE_WIDE,
         top_rise_end=_balcony_beam_rise,
         bearing_refs=("PT-SG-BR1", "PT-SG-BF1")),
    Beam(uid="SGBB02AAAA", tag="BM-SG-BLC", start_node="N-SGB-SC", end_node="N-SGB-NC",
         size=SPEC.balcony_beam, assembly="BEAM_GLULAM_TREATED",
         published_span=_BALCONY_BEAM_PUBLISHED,
         top_protection=_BEAM_TAPE_WIDE,
         top_elevation=_balcony_centre_beam_top,
         top_rise_end=_balcony_beam_rise,
         bearing_refs=("PT-SG-BR2", "PT-SG-BF2")),
    Beam(uid="SGBB03AAAA", tag="BM-SG-BLE", start_node="N-SGB-SE", end_node="N-SGB-NE",
         size=SPEC.balcony_beam, assembly="BEAM_GLULAM_TREATED",
         published_span=_BALCONY_BEAM_PUBLISHED,
         top_protection=_BEAM_TAPE_WIDE,
         top_rise_end=_balcony_beam_rise,
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
# Porch: PT 2x8 @ 16" o.c. running N-S across the two beam lines — bearing on top of both
# pairs, oversailing the front pair and cantilevering the column's offset past the back.
#: The porch joists' SOUTH oversail past the front beam axis, and the BF2 chase's own south
#: edge — one number, because the chase has to reach the joist tips exactly. See
#: ``PORCH_JOISTS`` for what the oversail buys and ``PILLAR_CHASES`` for why the chase ends
#: on it rather than past it.
_PORCH_JOIST_START_CANT_IN = 4.25

# ** THE TWO PILLAR CHASES (2026-09-14). ** Both centre pillars now rise from the concrete
# column tops at -1'-6 1/2", which is BELOW this deck, so each passes THROUGH the joist
# plane on its way to the balcony. The joist line at x = 18'-0" is the one they pass
# through, and a post and a joist cannot occupy the same 7 1/4".
#
# A 9" square is the framed answer and it is the same 9" the field detail already called
# for in the composite plank. The 5 1/2" pillar sits dead-centre in it with 1 3/4" clear on
# all four sides, and the joist line the pillar lands on — x = 17'-10", the 16" module's
# nearest, whose 1 1/2" width is entirely inside the pillar's footprint — is cut over the
# opening and headed. At 9" the opening is inside R502.10.1's short-opening allowance, so
# the header and trimmers are single-ply joist stock rather than a designed beam.
#
# ** WHAT IS BUILT IS A SLEEVE ON THE BEAM, NOT A TRIMMER PAIR ON THE 16" LINES. ** This
# comment claimed the latter until 2026-09-15 and the resolver never did it: ``resolve/
# floors.py`` frames the AUTHORED opening's own edges, so the trimmers stand on the
# opening's two x edges (17'-7 1/2" and 18'-4 1/2") and run only the opening's 9" of y.
# The claim was checked against the resolved model rather than repaired, and the framing
# turns out to be the better of the two: **each of the four trimmers crosses its beam and
# takes the full 4 1/2" of it** (BR2's pair onto BM-SG-BKW/BKE, BF2's onto BM-SG-FRW/FRE),
# so the cage is a box bearing directly on the beam — which is how a post penetration
# beside a beam is actually blocked out — and the headers land on the trimmers.
#
# **Widening the opening to the 198"/230" lines was considered and REJECTED**, though it
# would have made the old sentence literally true. ``_subtract_interval`` fires on any line
# with ``opening_perp0 <= perp <= opening_perp1``, so the two neighbouring joists would
# each lose a 9" bite for no reason, and the header would grow from 9" to 32" — two sound
# full-length joists cut and a longer header, to move framing off a beam and into the air.
#
# ** NO HANGER ON THE POST'S NORTH OR SOUTH FACES, AND THAT IS THE REASON FOR THE HEADER. **
# Four connectors will not fit on a 5 1/2" face: the two beams already take the east and
# west faces (CN-SG-HGR-C*, HU212-3), and hanging the header off the remaining two would
# put four hangers on one post at one elevation. The header is carried by the two
# neighbouring joists instead, and the post carries nothing of this deck at all.
#
# ``bearing_refs`` names the beam each opening sits on — the header's own ends land on the
# trimmers, but the trimmers land on these.
PILLAR_CHASES = [
    FloorOpening(uid="SGO009AAAA", tag="FO-SG-BF2", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_cx) - inch(4.5), ft(_y_bf2) - inch(_PORCH_JOIST_START_CANT_IN)),
                          pt(ft(_cx) + inch(4.5), ft(_y_bf2) - inch(_PORCH_JOIST_START_CANT_IN)),
                          pt(ft(_cx) + inch(4.5), ft(_y_bf2) + inch(4.5)),
                          pt(ft(_cx) - inch(4.5), ft(_y_bf2) + inch(4.5))),
                 bearing_refs=("BM-SG-FRW", "BM-SG-FRE")),
    FloorOpening(uid="SGO010AAAA", tag="FO-SG-BR2", purpose=FloorOpeningPurpose.CHASE,
                 outline=(pt(ft(_cx) - inch(4.5), ft(_y_br2) - inch(4.5)),
                          pt(ft(_cx) + inch(4.5), ft(_y_br2) - inch(4.5)),
                          pt(ft(_cx) + inch(4.5), ft(_y_br2) + inch(4.5)),
                          pt(ft(_cx) - inch(4.5), ft(_y_br2) + inch(4.5))),
                 bearing_refs=("BM-SG-BKW", "BM-SG-BKE")),
]

PORCH_JOISTS = FloorSystem(
    uid="SGFS01AAAA", tag="FS-SG-PORCH",
    joists=JoistSpec(member=SPEC.porch_joist, spacing=inch(SPEC.porch_joist_oc_in),
                     direction="y",
                     # South (start) end: the joists CROSS the front beam and stop 2 3/4"
                     # past its far face, so each takes the beam's full 4 1/2" of bearing
                     # instead of dying on its centreline at 2 1/4". That is the whole
                     # reason for the number: a joist should bear ACROSS its beam. It also
                     # takes the front bearing plane out of NDS §3.10.4's END case, so C_b
                     # applies at both planes and PT-SG-BF2's d/c falls 0.76 -> ~0.35.
                     # Keep any oversail well inside the 8" ``bearing_plan_tolerance_in``:
                     # past it the uplift check finds neither a derived tie nor a hanger
                     # and FAILs all 32 members.
                     # North (end): the joists run past the back-beam line to the deck
                     # edge, which is the porch's real overhang. One symmetric value cannot
                     # say both.
                     # Derived off the deck edge, so the tip and the front board cannot
                     # disagree. The tips pass OVER W-B-BRICK (top -8"); see `_y_porch_deck_n`.
                     cantilever=inch(SPEC.porch_joist_cantilever_in),
                     cantilever_start=inch(_PORCH_JOIST_START_CANT_IN),
                     cantilever_end=ft(_y_porch_deck_n - _y_col),
                     # The NORTH band (rim-0, y = -9'-8 3/4") is the porch's exposed front
                     # edge: it closes the joist tips over the garden walk, in the same plane
                     # as the white pillars and knee braces above it, and no fascia covers it
                     # the way TR-SG-FASCIA covers the balcony's. So it is painted with them,
                     # exactly as FS-SG-DECK's bands are.
                     # ** IT PAINTS BOTH BANDS. ** `rim_material` is a JoistSpec field, not a
                     # per-band one, so the NORTH band takes the same paint and the same
                     # qualified price key — and that one sits over the brick cavity, where
                     # nothing will ever see it. 19 LF of paint on a hidden board is the
                     # honest cost of saying the front one is white.
                     # The joists behind both stay bare PT.
                     rim_material="post-paint-white",
                     # Four boundaries with two duplicate pairs: front and back are each two
                     # collinear beams meeting over their column, so the span solver sees
                     # the same two cut lines twice and drops the degenerate segment.
                     # Member count is unchanged from the single-wall bearing.
                     bearing_refs=("BM-SG-FRW", "BM-SG-FRE",
                                   "BM-SG-BKW", "BM-SG-BKE")),
    # ** THE TWO CENTRE PILLARS' BEARING PACKS WERE RETIRED ON 2026-09-14. **
    # Both pillars bear on the concrete column tops now, not on this deck (see
    # ``_WALL_UNDER_PILLAR``), so there is no pillar load in these joists to spread and no
    # cross-grain plane here to grade: ``engineering/post_bearing.py`` enumerates a post
    # whose ``supported_by`` names a FloorSystem, and neither does. What stands at x = 18'-0"
    # instead is ``PILLAR_CHASES`` — a framed 9" opening at each pillar, its cut joist line
    # headed onto a trimmer pair that bears on the beam below (see PILLAR_CHASES; this read
    # "headed off the two joist lines 16\" either side" until 2026-09-15, which the resolver
    # never did and which would be the worse detail if it had).
    #
    # **The guard post needs no blocking here either, and that is not an oversight.** The
    # RL-SG-PORCH south-leg station at x = 18'-0" is PT-SG-BF2 itself, and the R301.5 200 lb
    # couple at the top of that guard now runs 6x6 -> ABU66SS -> PT-SG-FCOL -> PD-SG-FCOL,
    # entirely in members that bear on concrete. It never reaches a joist, so there is
    # nothing for a block to take it into. The nine other south-leg stations keep theirs
    # below — their posts really do stand on the plank.
    #
    # The retired specs are kept, in place and referenced by nothing, as
    # ``_DECK_BORNE_PILLAR_REINFORCEMENTS`` below.
    reinforcements=(
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
    # ``outline`` scopes the PERPENDICULAR (x) extent only — resolve/floors.py takes the
    # along-span extent from the joists' own ends, cantilevers included. So the 2 3/4"
    # ``cantilever_start`` above grows the SHEET south with the framing, to y = -116'-8 3/4"
    # in inches, while this tuple does not move. **The consequence is deliberate: the plank
    # now ends 2 3/4" south of RL-SG-PORCH's guard line**, which stays on `_y_ax_front`.
    # Do NOT chase the guard south to the new edge — `_y_porch_guard_block` puts its
    # blocking in the bay NORTH of the beam, and a guard on the new edge would bolt into
    # cantilevered joist tips instead. A guard set back from a deck edge is ordinary
    # construction; 2 3/4" is a small setback, not a landing. TR-SG-DRIP / `_FRONT_PATH`
    # are unaffected — they are the BALCONY's front edge (`_y_balcony_front`), not this one.
    outline=_PORCH_OUTLINE,
    #: The two pillar chases — see ``PILLAR_CHASES`` above.
    openings=("FO-SG-BF2", "FO-SG-BR2"),
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

#: REVERT RECORD, 2026-09-14 — the two ``JoistReinforcement`` packs that carried the centre
#: pillars while they bore on this deck. Kept in place and referenced by nothing, the
#: ``EXT_2X6_SWINBURNE`` convention: restoring ``_DECK_BORNE_PILLAR_BEARINGS`` without
#: restoring these would put two 6x6s carrying a third of a balcony each onto a single
#: 1 1/2" ply, at 311 and 380 psi against a wet Fc-perp of 285. The ``at`` points are the
#: two beam centrelines; ``plies=3`` is what took those planes to 104 and 127 psi.
_DECK_BORNE_PILLAR_REINFORCEMENTS = (
    JoistReinforcement(
        at=pt(ft(_cx), ft(_y_col)), plies=3, blocking=True,
        source="3-ply bearing pack + squash blocks under PT-SG-BR2 — a 6x6 carrying a "
               "third of the balcony lands here; the plies spread 2,566 lb across 4 1/2\" "
               "of stock and the blocks take the cross-grain load into the back beams "
               "instead of into the joist's web"),
    JoistReinforcement(
        at=pt(ft(_cx), ft(_y_ax_front)), plies=3, blocking=True,
        source="3-ply bearing pack + squash blocks under PT-SG-BF2, which is also the "
               "RL-SG-PORCH south-leg guard post at this station — the joists END on "
               "the front beam with 2 1/4\" of bearing, so the plies are what spread "
               "2,267 lb over it and the blocks are what the guard's overturning lands "
               "in, never TR-SG-CAP-FRW/FRE and its butyl"),
)

# --- the porch enclosure's flank blocking (2026-09-03) --------------------------------
# The bug path nobody would have seen. FS-SG-DECK's joists run E-W and the enclosure's two
# FLANK tracks run N-S at x = 9'-0"/27'-0" (plan/placeables.py), so the curtain plane crosses
# EVERY 16" joist bay perpendicular. Above the track each bay is open inside<->outside — a
# continuous 7 1/4" x 16" hole every 16" along both flanks, straight past a sealed curtain.
# The two FRONT runs need none of this: they lie ALONG a joist line (see below), so there is
# 1 1/2" of continuous KDAT over them for their whole length.
#
# ``plies=1``: ``_reinforcement_members`` lays ``range(plies - 1)`` sisters, i.e. NONE, and
# only the blocks — the same idiom as the guard's rim blocks above, and what keeps
# ``test_no_catlin_deck_sisters_a_joist`` green. A stray ``plies=3`` here would silently add
# sisters and their lumber. The blocks resolve at the joists' full depth, land flush with the
# soffit the track screws to, and inherit FS-SG-DECK's ``top_protection`` butyl.
_ENCLOSURE_TRACK_X = (9.0, 27.0)
# ** EVERY SECOND JOIST LINE, AND THAT IS THE WHOLE TRAP. ** One ``JoistReinforcement`` lays
# a block in the bay on EACH side of its line. Lines 1,3,5,7 counted from the front rim fill
# bays 1..8 exactly once; author 1..8 instead and every bay gets two blocks, which is a real
# ``structural.member_interference`` FAIL. 1/3/5/7 and not 2/4/6/8 because index 8 is the
# rear rim at ``max(joist y)`` and every authored ``at`` must sit STRICTLY inside the joist
# field (``test_a_guard_block_authored_on_the_deck_edge_would_be_dropped``).
# The cost, stated rather than hidden: the line-1 entry's second block lands in bay 0-1,
# which is the balcony's front overhang SOUTH of the front track — one per flank, doing
# nothing for the enclosure. Eight entries, sixteen blocks, ~17.3 lf.
_ENCLOSURE_BLOCK_LINES = [_y_balcony_front + _k * SPEC.balcony_joist_oc_in / 12.0
                          for _k in (1, 3, 5, 7)]   # -9'-2", -6'-6", -3'-10", -1'-2"

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
    # ** THE FIELD FOLLOWS THE BEAMS. ** The three balcony beams tilt (`_balcony_beam_rise`),
    # and a flat joist field on tilted beams is the model disagreeing with itself about where
    # the bearing is — the beam tops come up THROUGH the joists they carry, which
    # `structural.member_interference` reports and which is not a drafting complaint. The two
    # rises are the same number over the same run, and they are the same expression here so
    # they cannot drift apart: this field's perpendicular extent is `_y_balcony_front` to
    # `_y_in_n`, which is exactly the beams' node-to-node span.
    #
    # Each joist stays LEVEL at its own height — a staircase of ~1/4" steps across the 16"
    # o.c. field, which is how a sloped deck frames. The two rim bands run along the fall and
    # rake; the resolver gives them their far-end elevations.
    #
    # **The deck PLANE does not tilt**, and the divergence is deliberate:
    # `ResolvedFloor.deck_z0_m`/`deck_z1_m` are single values that the room, energy, section
    # and guard consumers read, so the model's 10'-0" walking surface is this deck's SOUTH
    # (low) edge and the built north edge stands 2 5/8" above it.
    # notes/balcony_differential_movement.md §2.
    top_rise=_balcony_beam_rise,
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
    reinforcements=(
        *(JoistReinforcement(
            at=pt(ft(_gx), ft(_gy)), plies=1, blocking=True,
            source="rim block behind an RL-SG-BALCONY fascia bracket — the four 5/16\" "
                   "through-bolts land in this block so the 2x8 rim cannot roll under the "
                   "guard's 200 lb top load")
        for _gx, _gy in _BALCONY_GUARD_STATIONS),
        *(JoistReinforcement(
            at=pt(ft(_ex), ft(_ey)), plies=1, blocking=True,
            source="joist-bay closure under the porch enclosure's flank track — the "
                   "curtain plane crosses this bay perpendicular, so without the block "
                   "the bay is open inside<->outside above a sealed curtain")
          for _ex in _ENCLOSURE_TRACK_X for _ey in _ENCLOSURE_BLOCK_LINES)),
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
# without a thermal bridge. Bars at mid-JOINT (-9'-5 7/16"), on the north-edge line.
#
# **DW-SG-COL, the third, is retired, with its bell.** It would have crossed the joint
# between PD-SG-COL and FT-B-S2 if the two sat at the same elevation 2" apart, but the bell
# bears 2'-6" lower — its top is 1'-10" under FT-B-S2's underside — so the bars would span
# open ground at -9'-4 7/16" with no garden concrete at that height to develop into, and the
# foam block would have one face and no joint. A separated pier does not need a thermal
# break; it IS one. Nothing renumbered: COL was the LAST entry, so W1 keeps SGDW01AAAA and
# E1 keeps SGDW02AAAA and no IFC GlobalId moves — which is the only reason removing an
# ``enumerate``-minted uid was safe to do in place (compare _WALL_FOOTING_UID above, where
# it was not).
# ============================================================================
# ** THE BARS WERE ABOVE THE FOOTING THEY DOWEL INTO. FIXED 2026-09-05. **
# This read `ft(-(basement_depth_ft + 0.75) + footing_thickness/24)` — mid-height of a
# garden footing whose underside was -118 7/16", which is where FT-SG-W1/E1 sat before the
# court was ever re-levelled. Two elevation changes later the bars resolved at -112 7/16"
# and the garden footing's TOP was -117 7/16": three #5 GFRP bars 5" of open air above the
# concrete they claim to develop into, and a 12" foam block straddling a joint that was not
# there. Nothing grades a dowel against the two footings it names, so it read fine.
#
# Derived now, off the joint itself. The two footings share a face from FT-B-S2's underside
# up to the plane they both top out on — 8", the house footing's own depth — and the bars
# sit at the middle of it with 4" to each face. `_HOUSE_FOOTING_DEPTH_IN` is transcribed
# from `params/foundations.HOUSE_FOOTINGS` (`depth=inch(8)`) rather than imported, the same
# way `basement_depth_ft` is, and the foam block is that same 8" so it fills the joint
# exactly instead of standing proud of it into the slab bed.
_HOUSE_FOOTING_DEPTH_IN = 8.0
_dowel_z = _wall_bottom - inch(_HOUSE_FOOTING_DEPTH_IN / 2.0)
# ** THE BLOCK IS ON THE JOINT PLANE, AND THE OPPOSING FOOTING IS NAMED CORRECTLY. **
# Both fixed 2026-09-05, on the same pass that extended the walls.
#
# The y was `_y_in_n` (-10"), the porch's deck line, with NO house concrete opposite it:
# FT-B-S1/FT-B-S4's south face stood there too, so the block straddled a butt joint rather
# than filling one. It is now `_y_closure_break` — the isolation board's own mid-thickness —
# so this block and the stem block above it are coplanar and read as one continuous 2" board
# from the house footing's underside to the wall top.
#
# And `connects` said "FT-B-S2" on BOTH. FT-B-S2 runs x 8'-10"..18'-0" and faces neither of
# these: at x 8'-0" the opposing strip is FT-B-S1, at x 28'-0" it is FT-B-S4 (which reaches
# west to 27'-2" since the framed run was pulled clear of the court — storeys/basement.py).
# The tag is carried in the tuple now, so a third literal cannot drift from the geometry.
# ** AND THE BLOCK WAS 21" LONG IN AN 84" JOINT. FIXED 2026-09-05 (second pass). **
# `foam_length` is authored, and it is the FOOTING's width. Without it
# `resolve/accessories._resolve_dowel` derives the block's length along the joint from the
# BAR ROW — `max(row_span + 8*dia, 12")` = max(16 + 5, 12) = 21" — which is the right rule
# for the stem block below (a 12" wall's end face, where the bars really are the joint) and
# the wrong one here. The stem block was sized against the WALL and this one inherited its
# reasoning, but the pour it separates is not the wall: it is the 84"-wide strip footing
# under it. 21" of board in an 84" joint left **63" of footing-to-footing concrete** with no
# break in it at all, running straight from a heated basement footing into a wall that
# stands in an open court — and NOTHING in this engine grades a thermal break for
# continuity, so it read as a designed detail.
#
# `SPEC.footing_width_in`, not a literal: the block is the joint, and the joint is as wide
# as the footing. Widen the footing and the board follows it.
# ** THE BREAK IS ONE PRODUCT AND THESE TWO CONSTANTS ARE THE ONLY PLACE IT IS STATED. **
# `THERMAL_BREAK_IN` is the board thickness and `THERMAL_BREAK_PSI` its compressive rating,
# and they are published here because **the break cannot go on one purchase order today**.
# That is a takeoff fact rather than an opinion: the two closure blocks resolve as foam
# solids and bill by VOLUME into the concrete trade, while the veneer beam's board is a
# `Layer` on `SG_VENEER_BEAM_14` and bills by AREA into insulation. Nothing reconciles the
# two, so the only thing holding them to one product is that every site reads one number.
#
# `Layer` has no compressive field at all, which is why the beam's board carried the 40 psi
# in prose and the blocks carried it in a keyword. Both read `THERMAL_BREAK_PSI` now, the
# beam's through its `source` text, and `test_catlin_contract_m3` asserts the sites agree —
# a comment alone is what let the retaining top's spot elevations rot for two revisions.
#
# ** 40 psi (ASTM C578 Type VII), not the slab's 25. ** The board is a FORM FACE here: it
# takes the fresh concrete head of a 12" pour against it with nothing behind it but a
# cured house footing, and a board that dishes under the head is a board the two pours
# have found each other around.
THERMAL_BREAK_IN = SPEC.closure_break_in
THERMAL_BREAK_PSI = 40.0

# ** ONE BAR ARRANGEMENT ON THE WHOLE PLANE. ** The two blocks carried `count=3 @ 8"` and
# `count=2 @ 6"`, on one continuous board, and **neither was required by any computed limit
# state** — no check and no engineered item grades these bars at all. Two counts and two
# spacings on one plane is two field instructions for one board and two things to miscount.
#
# One size (#5 GFRP, 0.625"), one spacing (8" o.c., the coarser of the two that existed —
# no new number is invented here), and the COUNT derived from the board it holds. The
# footing block is 84" wide and takes 10 bars on a 76" row, 4" clear of each end — see
# `_break_bar_count`, whose docstring works the 84" tie out bar by bar; the stem
# block is 12" and takes the minimum 2 on an 8" row. **Three bars over eight feet was the
# old footing figure**, which held the middle of the board and left 44" of it either side
# free to float and rack against the head of a 12" pour — with no check anywhere that would
# notice.
#
# ** ⚠ THE BARS ARE WHY THE BOARD EXISTS AT ALL. ** A `Dowel`'s foam block is the only way
# this engine resolves a real XPS solid at a joint (`resolve/accessories._resolve_dowel`),
# so `count=0` does not thin the detail — it DELETES the board from the model, from the
# bill and from every drawing. `_resolve_dowel` lays `range(max(count, 1))`, so a zero is
# silently a one. Never reduce these to nothing; if the tie is ever not wanted, the board
# needs a different element first.
THERMAL_BREAK_BAR_IN = 0.625
THERMAL_BREAK_BAR_SPACING_IN = 8.0

# ** FOUR SEQUENCING TRAPS ON THIS BOARD. EVERY IMPROVEMENT TO THIS DETAIL RESTS ON
# COMMENTS AND ONE TAKEOFF ROW, SO THEY ARE WRITTEN HERE RATHER THAN ASSUMED. **
#
# 1. **The butt joint between the two blocks lands on the court floor plane.** The footing
#    block runs -117 7/16"..-109 7/16" and the stem block -109 7/16"..0, and -109 7/16" is
#    exactly `SL-SG-FLOOR` — the wettest, saltiest, most trafficked surface in a court that
#    drains only to a soakaway and cannot shed chloride at all (§6a of
#    notes/sunken_garden_court_free_body.md). A butt joint there is a wick straight into
#    the one plane the whole C2 case is about. **Lap the upper board past the joint**; the
#    model cannot express a lap, so the drawing and this note are the instruction.
#
# 2. **The garden pour cannot lead the house.** The STEM dowels are drilled and epoxied
#    into cured house wall with roughly an inch of tolerance before they blow through 8" of
#    concrete and 4 3/16" of foam and coating. The basement wall must be poured, cured and
#    SURVEYED first — surveyed, because an epoxied dowel has no adjustment. `AN-SG-PLACEMENTS`
#    carries this as placement (2)'s precondition.
#
# 3. **The beam's board depends on a footing trim that is a HOLD POINT.** `FT-B-S2`/`S3`
#    give up 2" of south toe (via `offset`, keeping all 20" of bearing) so
#    `SG_VENEER_BEAM_14`'s board has somewhere to bear. Poured full width, the beam has
#    nowhere to go and the board nothing to bear against, and nobody finds out until the
#    garden pour. **Sign the trim off before the HOUSE footing pour, not after.**
#
# 4. **The longest board is the only one with no positive tie.** `SG_VENEER_BEAM_14`'s is
#    20'-0" of 2" XPS against the fresh head of a 12" pour, held by nothing — it is a
#    `Layer`, not a `Dowel`, so it has no bars at all. Fine for crushing at 40 psi; it must
#    still be held against FLOATING and RACKING, and **no check will notice** either. The
#    two closure blocks are tied (§ the bars above); this one is on the formwork.


def _break_bar_count(board_width_in: float) -> int:
    """Bars across a closure board — one rule, both blocks. Minimum two.

    ** 84" LANDS ON AN EXACT HALF AND ROUNDS DOWN. ** `84 / 8 = 10.5`, and Python's `round`
    is banker's rounding, so this returns 10 (8.4" o.c.) rather than 11 (7.6"). Either is a
    fine field spacing and neither is required by any graded limit state — nothing in this
    engine sizes these bars — so the rule is left alone rather than nudged to win a tie.
    Worth knowing before reading a bar count that looks one short.
    """
    return max(2, round(board_width_in / THERMAL_BREAK_BAR_SPACING_IN))


# ** THE BOARD IS CENTRED ON THE FOOTING, NOT ON THE WALL AXIS. ** `Dowel.foam_length`
# centres the block on `position`, and the two coincide again now that the strips are 84"
# centred with a zero offset — but the expression stays, because it is what makes them
# coincide rather than an assumption that they do. They did NOT for one revision: the strips
# carried a 6" inboard offset, the joint ran x 4.500..12.500 against a wall axis of 8.000,
# and a board written on the axis would have covered 4.000..12.000 — 6" hanging past the
# footing into nothing outboard, and **6" of bare footing-to-footing concrete at the court
# end**. The third sign (+1 into the court, -1 on the east leg) is what keeps the board on
# the pour it separates whenever the offset is not zero.
_DOWEL_AT = (("W1", _x_ax_w, "FT-B-S1", +1.0), ("E1", _x_ax_e, "FT-B-S4", -1.0))
DOWELS = [
    Dowel(uid=f"SGDW0{i}AAAA", tag=f"DW-SG-{name}",
          position=pt(ft(x + court * _RETAINING_FOOTING_OFFSET_IN / 12.0),
                      ft(_y_closure_break)),
          axis="y", length=inch(24), diameter=inch(THERMAL_BREAK_BAR_IN),
          elevation=_dowel_z,
          count=_break_bar_count(_RETAINING_FOOTING_WIDTH_IN),
          spacing=inch(THERMAL_BREAK_BAR_SPACING_IN),
          connects=(f"FT-SG-{name}", house_footing),
          foam_thickness=inch(THERMAL_BREAK_IN),
          foam_height=inch(_HOUSE_FOOTING_DEPTH_IN),
          # ** THE JOINT IS AS WIDE AS THE FOOTING, WHATEVER THE FOOTING IS. ** This read a
          # separate literal once, and a board narrower than the joint leaves bare
          # footing-to-footing concrete running straight from a heated basement strip into a
          # wall standing in an open court — the defect this authored length exists to fix,
          # and one that reopens silently every time the footing width moves. Written as
          # `_RETAINING_FOOTING_WIDTH_IN` so it cannot. (The 84" -> 96" widening this
          # paragraph used to narrate was reverted; the strips are 84" and
          # `SPEC.footing_width_in` is the one place that says so.)
          # Nothing grades a thermal break for continuity.
          foam_length=inch(_RETAINING_FOOTING_WIDTH_IN), foam_psi=THERMAL_BREAK_PSI)
    for i, (name, x, house_footing, court) in enumerate(_DOWEL_AT, start=1)
]

# --- the stem-level board, and the two bars that hold it captive (2026-09-05) ----------
# The closure's isolation board above the footings. It is a VERTICAL plane on the wall's
# END face, which `Layer` cannot express — layers run parallel to the axis — so it is
# modelled the one way this engine resolves a real XPS solid at a joint: as a `Dowel`'s
# foam block (resolve/accessories._resolve_dowel), 2" thick along the bar axis and
# `foam_height` tall, centred on `position`.
#
# It stacks directly on the footing block declared just above (DW-SG-W1/E1-FOAM), which
# sits BELOW it in the building: footing block -117 7/16"..-109 7/16",
# stem block -109 7/16"..0. Together they are ONE continuous board from the house footing's
# underside to the top of the porch wall, on one plane (-6 3/16"..-4 3/16").
#
# ** count=2 @ 6" IS NOT ARBITRARY, AND THIS BLOCK IS THE ONE THAT KEEPS THE DERIVED
# LENGTH. ** `max(row_span + 8*dia, 12")` = max(6 + 5, 12) = 12", i.e. exactly the wall's
# own thickness, so the foam lands flush with both faces of the 12" pour. The footing rows'
# `count=3 @ 8"` would resolve to 21" and throw 4 1/2" past each face — which is why they
# now author `foam_length` outright and stop reading the bar row at all. Here the bars
# really ARE the joint, so the derivation is the right one and is left alone. Do not
# "tidy" the two blocks into one rule: they are sized against different pours.
#
# ** Two GFRP bars is a detail decision, not a rounding. ** They hold the board captive
# during the pour and give the closure a positive tie into the house wall — without a
# thermal bridge (fiberglass, not steel) and without a vertical bond, which is the same
# argument the footing blocks already make. `count=0` is not available: `_resolve_dowel`
# lays `range(max(count, 1))`. The bars run 24" centred on the board, so ~11" is embedded in
# the garden stem and ~6 3/4" reaches into the 8" house pour past 4 3/16" of foam and
# coating — a drilled-and-epoxied dowel across a break, cover 1 1/4" on the far face.
_STEM_DOWEL_AT = (("W1", _x_ax_w, "W-B-S1"), ("E1", _x_ax_e, "W-B-S4"))
_stem_height = _porch_top - _wall_bottom
STEM_DOWELS = [
    Dowel(uid=uid, tag=f"DW-SG-{name}-STEM",
          position=pt(ft(x), ft(_y_closure_break)),
          axis="y", length=inch(24), diameter=inch(THERMAL_BREAK_BAR_IN),
          elevation=_wall_bottom + _stem_height / 2.0,
          count=_break_bar_count(SPEC.wall_thickness_in),
          spacing=inch(THERMAL_BREAK_BAR_SPACING_IN),
          connects=(f"W-SG-{name}", house_wall),
          foam_thickness=inch(THERMAL_BREAK_IN),
          # ** AUTHORED, NOT DERIVED, SINCE 2026-09-10 — AND THE VALUE DOES NOT CHANGE. **
          # `max(row_span + 8*dia, 12")` = max(6 + 5, 12) = 12" is the right answer here
          # and the paragraph above explains why. It is written down anyway, because a
          # length that happens to come out right is not the same as a length somebody
          # chose: move these two bars 4" apart and the derivation silently returns 16",
          # throwing 2" of foam past each face of the 12" pour. The two blocks now state
          # their lengths the same way and differ only in the number, which is the whole
          # point — they are sized against different pours and must not be merged.
          foam_length=inch(SPEC.wall_thickness_in),
          foam_height=_stem_height, foam_psi=THERMAL_BREAK_PSI)
    for uid, (name, x, house_wall) in zip(("SGDW03AAAA", "SGDW04AAAA"),
                                          _STEM_DOWEL_AT, strict=True)
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
#: REVERT RECORD, 2026-09-14 — the five-part base tie the two centre pillars carried while
#: they bore on the porch framing: an MSTA12Z strap on the one flush vertical pair (the
#: post's west face and the joist pack's, both at x = 213 1/4") plus L50Z angles wherever
#: there was pack to screw into (BR2 north and south, BF2 north alone). Totals 1,408 lbf at
#: BR2 and 1,033 lbf at BF2 against a 300-600 lbf demand. Kept in place and referenced by
#: nothing, beside ``_DECK_BORNE_PILLAR_BEARINGS`` and
#: ``_DECK_BORNE_PILLAR_REINFORCEMENTS``, because the reasoning it encodes — why nothing
#: that WRAPS this joint can be built at a T, and why ABU66SS was the wrong part on a deck —
#: is the reasoning a reader restoring that arrangement needs. The three ratings and the
#: species argument are still in ``library/hardware.py``.
#:
#: ``TENSION_TIE`` was the kind, and the kind is the whole difference: ``model/enums.py``
#: reads TENSION_TIE as "a post on FRAMING" and POST_BASE as "a stirrup on CONCRETE". These
#: two pillars stand on concrete now, so they take a POST_BASE.
_DECK_BORNE_BASE_TIE = (
    ("CN-SG-BASE-R2-W", "MSTA12Z"), ("CN-SG-BASE-R2-N", "L50Z"),
    ("CN-SG-BASE-R2-S", "L50Z"),
    ("CN-SG-BASE-F2-W", "MSTA12Z"), ("CN-SG-BASE-F2-N", "L50Z"),
)

# ** THE TWO CENTRE PILLAR BASES — ABU66SS ON THE POUR, SINCE 2026-09-14. **
#
# Both centre pillars stand on a 12" cast column top now (``_WALL_UNDER_PILLAR``), so the
# joint this connector makes is the one every published ABU number is measured at: a wood
# post standing off CONCRETE through a cast-in 5/8" anchor. That is the reversal of the note
# kept at ``_DECK_BORNE_BASE_TIE`` above, and it is a kind change rather than a size change
# — ``ConnectorKind.POST_BASE`` is "a stirrup on concrete" and ``TENSION_TIE`` is "a post on
# framing" (model/enums.py). Authoring the old kind here would have drawn the right part
# against the wrong joint.
#
# **ABU66SS, not ABU66Z**: these two stirrups stand in the open at the head of a sunken
# garden, in the same run-off the other ten stainless bases on this house were specified
# for, and the stainless carries the galvanised part's published numbers (L-F-SSNAILS — see
# ``library/hardware.py::ABU66SS_POST_BASE``). ``anchored=True`` says the 5/8" bolt is cast
# into the column rather than drilled after: these two pours are placed with the garden's
# own excavation and the bolt is set wet.
#
# **The 1" standoff is the point of the part, not a detail of it.** IRC R317.1.4 Exception
# 1/3 lets an untreated post end stand clear of concrete instead of being treated for
# ground contact, and an ABU is what makes that standoff a countable thing rather than a
# sentence in an assembly's ``source``. It is also 1" of the two pillars' modelled length —
# see ``SPEC.pillar_size`` and the post-length note on ``PILLARS``.
#
# ``elevation`` is the column top the stirrup is bolted to, which is also the pillar's own
# base: ``PILLAR_BEARINGS`` carries both, so the two cannot drift apart.
CONNECTORS = []
for _row, _y, _rise in _PILLAR_ROWS:
    _bearing_tag, _bearing_top = PILLAR_BEARINGS[f"PT-SG-B{_row}2"]
    _post_y = _y_bf2 if _row == "F" else _y_br2
    CONNECTORS.append(Connector(
        uid=f"SGCB2{_row}AAAA", tag=f"CN-SG-BASE-{_row}2",
        kind=ConnectorKind.POST_BASE,
        position=pt(ft(_cx), ft(_post_y)),
        elevation=_bearing_top, anchored=True,
        # ** THE STIRRUP'S SIDE PLATES RUN NORTH-SOUTH, AND THAT IS NOT A PREFERENCE. ** An
        # ABU is a U: two side plates stand ~3-5/8" up off the 1 3/16" standoff on TWO
        # OPPOSITE faces of the post, and the other two faces are open. Put those plates on
        # the pillar's WEST and EAST faces and they occupy the very wood the four HU212-3
        # beam hangers are nailed to — each hanger's back flange rises from the beam soffit
        # (= the column top) 10-5/16" up those same two faces, so the overlap is total in z
        # and the joint cannot be built. North/south, the plates clear every hanger: nothing
        # else lands on those two faces at all. ``axis`` is how the model says so
        # (accessories.py::_resolve_connector turns the marker by it).
        axis="y",
        source="ABU66SS set with its side plates N-S. The W and E faces of PT-SG-B*2 are "
               "the HU212-3 back-flange faces (CN-SG-HGR-C*2-W/E) and the flange occupies "
               "the soffit-to-10-5/16 band the stirrup plates also want.",
        size="ABU66SS", connects=(f"PT-SG-B{_row}2", _bearing_tag)))
    # ** AND THE FOUR PORCH BEAMS HANG OFF THE PILLAR. ** Each beam used to run to the
    # column's own axis and BEAR on the pour; the pillar stands on that pour now, so the
    # beam stops at the pillar's face (N-SGM-COLW/COLE, N-SGM-FCOLW/FCOLE) and is carried
    # by a face-mount hanger instead.
    #
    # **HU212-3, not HUC212-3.** The HUC is the CONCRETE-face-mount part the four wall
    # pockets take (CN-SG-HGR-W/E below), and its one advantage over the HU is a concealed
    # flange that lets the end sit in a 6" pocket. A 5 1/2" post cannot host a concealed
    # flange at all — there is nothing for it to disappear into — and the HUC's published
    # loads are Titen-into-concrete loads, which is not this joint. The HU is the same
    # 4 11/16" x 10 5/16" seat for the same three plies of 2x12, nailed into wood.
    # Write the plain model string: ``hardware_by_model`` is exact-match and a stray "Z"
    # silently yields no allowable.
    #
    # ``elevation`` is the beam's mid-depth, as the four pocket hangers are authored: a
    # Connector draws as a marker box centred on its elevation, and the soffit would hang
    # the marker below the joint.
    for _side, _dx, _beam in (("W", -1.0, f"BM-SG-{'BK' if _row == 'R' else 'FR'}W"),
                              ("E", 1.0, f"BM-SG-{'BK' if _row == 'R' else 'FR'}E")):
        CONNECTORS.append(Connector(
            uid=f"SGCHC{_row}{_side}AAA", tag=f"CN-SG-HGR-C{_row}2-{_side}",
            kind=ConnectorKind.JOIST_HANGER,
            position=pt(ft(_cx) + inch(_dx * _half_pillar_in), ft(_post_y)),
            elevation=_back_beam_mid,
            size="HU212-3", connects=(_beam, f"PT-SG-B{_row}2")))
# Spent post-base uids, not reused: SGCB1RAAAA / SGCB3RAAAA / SGCB1FAAAA / SGCB3FAAAA, the
# four corner ABU66SS bases retired when those pillars became cast columns, and
# SGCBWRAAAA / SGCBNRAAAA / SGCBSRAAAA / SGCBWFAAAA / SGCBNFAAAA, the five parts of the
# deck-borne base tie retired on 2026-09-14 (see ``_DECK_BORNE_BASE_TIE``).
#
# ``SGCB2RAAAA`` / ``SGCB2FAAAA`` are BACK IN USE, and deliberately so: they were the two
# inverted-CCQ bases at these same two joints, and the part standing there now is a base at
# the same two pillars. The uid is the element's identity, and the element — "the thing that
# holds PT-SG-B*2 down at its bottom" — never went away; only the part did. Reusing them
# keeps both IFC GlobalIds continuous across the whole history of this joint.

# THE FOUR CORNER BEAM SEATS. Each 12" column top carries ONE balcony beam end (the west
# and east beams' two ends each), held down by an HGAM10 masonry gusset angle. #14 screws to the wood, Titen Turbo to the concrete at >=3" edge distance
# on the 12" round (Simpson's minimum is 1-1/2"), and an EPDM or HDPE isolator between the
# gusset and the stainless standoff under the beam soffit.
#
# ``elevation`` is the beam SOFFIT — the bearing plane the gusset holds down — for the same
# reason the porch ties are authored there: a Connector resolves to a marker box centred on
# its elevation, so authoring the storey datum would draw the gusset floating in the joist
# band above the joint it makes.
_CORNER_SEAT_BEAM = {("R", 1): "BM-SG-BLW", ("F", 1): "BM-SG-BLW",
                     ("R", 3): "BM-SG-BLE", ("F", 3): "BM-SG-BLE"}
#
# ** TWO GUSSETS PER COLUMN, ONE EACH SIDE OF THE BEAM, SINCE 2026-09-14. ** A single angle
# restrains the beam end against rotation from one face only, and that is an ECCENTRIC
# restraint: NDS 3.3.3 requires beam ends to be restrained against rotation, and a one-sided
# gusset leaves the joint free to roll away from it. FL11473 footnote 4 contemplates the
# two-sided install directly and states its condition — a minimum 2-1/2" member "where
# anchors are installed on each side" — and the balcony beams are 3-1/2" glulam.
#
# The edge distance still works on both sides, and it is the gate that could have cut this
# back to the two porch joints. Anchors must sit outside the beam (>=1-3/4" off the axis for
# a 3-1/2" beam) and keep >=3" to the edge of the 12" round (so <=3" off the axis). Both
# sides get the same 1-1/4" band, because a circle is symmetric about its own diameter.
#
# Authored at the beam FACES rather than both on the centreline: the gusset's wood leg screws
# to the beam side, so the face is where the part is, and two markers at one point would draw
# as a single box.
_CORNER_SEAT_UID = {("R", 1): "SGCG1RAAAA", ("R", 3): "SGCG3RAAAA",
                    ("F", 1): "SGCG1FAAAA", ("F", 3): "SGCG3FAAAA"}
#: The second of each pair. New uids, minted here as every other uid in this file is — `haus
#: fmt` does not visit `params/*.py` and an empty uid is skipped, not filled.
_CORNER_SEAT_UID_B = {("R", 1): "SGCG1RBAAA", ("R", 3): "SGCG3RBAAA",
                      ("F", 1): "SGCG1FBAAA", ("F", 3): "SGCG3FBAAA"}
for _row, _y, _rise in _PILLAR_ROWS:
    for _i in _CORNER_PILLAR_INDICES:
        # The balcony beams run NORTH-SOUTH, so their faces are east and west: the offset is
        # in x. 1-3/4" is half the 3-1/2" glulam.
        for _uids, _side, _dx in ((_CORNER_SEAT_UID, "", -1.75),
                                  (_CORNER_SEAT_UID_B, "B", 1.75)):
            CONNECTORS.append(Connector(
                uid=_uids[(_row, _i)], tag=f"CN-SG-SEAT-{_row}{_i}{_side}",
                kind=ConnectorKind.HURRICANE_TIE,
                position=pt(ft(_PILLAR_X[_i - 1]) + inch(_dx), ft(_y)),
                elevation=_balcony_beam_soffit + _rise, size="HGAM10",
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
        elevation=_balcony_centre_beam_soffit + _rise, size="CCQ46SDS2.5",
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
    # HUC212-3, not HUCQ410-SDS and not LUS210. All four pockets carry one member — the
    # 3-ply KDAT 2x12 back/front beams, 4 1/2" wide x 11 1/4" deep — into a pocket cast in
    # a 12" SUNKEN_GARDEN_WALL.
    #
    # LUS210 was rejected first and correctly: a wood-to-wood face hanger with an exposed
    # flange and 10d-into-lumber nailing has nothing to bite in a pour. **HUCQ410-SDS
    # replaced it on 2026-08-22 and was wrong two further ways**, which nothing in the
    # engine can see — no check validates a ``Connector.size`` against the member it carries:
    #
    #   * **Wrong substrate.** The C-C masonry/concrete hanger table (p. 280) lists HU and
    #     HUC models only. Its concrete loads come from substituting the wood table's FACE
    #     NAILS with 1/4" Titen screws, and an HUCQ has no nail holes to substitute — it is
    #     fastened with Strong-Drive SDS wood screws that ship with the hanger. HUCQ is on
    #     no page of that catalog that publishes a load into concrete.
    #   * **Wrong seat.** HUCQ410-SDS is W 3 9/16" — the "410" is a 4x seat and 4x is
    #     3 1/2". Three plies of 2x12 are 4 1/2". The beam was 15/16" wider than its hanger.
    #
    # HUC212-3 is the exact seat: W 4 11/16" x H 10 5/16", 14 ga, and it IS on p. 280, at
    # 1,800 lbf uplift / 5,085 lbf download into concrete through (22) 1/4" x 2 3/4" Titen 2.
    # HUC rather than HU for the reason LUS210 was rejected: the end sits in a 6" pocket
    # inside a 12" wall and an exposed face flange has nowhere to go.
    #
    # **What the hanger is actually for here.** Each pocket is 6" deep, so 4 1/2" x 6" =
    # 27 sq in of the three-ply bears DIRECTLY on the cast sill; gravity is carried by that
    # bearing whatever the hanger is. These four take uplift and lateral restraint, and the
    # 5,085 lbf download is headroom, not the load path. That, and p. 280 footnote 5 — "Titen
    # screws are not exposed to weather", which a pocket in an open garden wall satisfies only
    # because it is flashed, back-sloped and sealed — are both worked in
    # notes/balcony_differential_movement.md and notes/beam_water_protection.md.
    #
    # uid, tag, position and elevation are unchanged, so the IFC GlobalIds survive the
    # retype.
    Connector(uid="SGCH01AAAA", tag="CN-SG-HGR-W", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_col)), elevation=_back_beam_mid,
              size="HUC212-3", connects=("BM-SG-BKW", "W-SG-W1")),
    Connector(uid="SGCH02AAAA", tag="CN-SG-HGR-E", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_col)), elevation=_back_beam_mid,
              size="HUC212-3", connects=("BM-SG-BKE", "W-SG-E1")),
    # CN-SG-TIE-COL/-COLB (SGCT01AAAA/SGCT01BAAA) are RETIRED, 2026-09-16: HGAM10 gussets
    # from when these beams bore on the pour. They hang off PT-SG-BR2 now (HU212-3, above),
    # which stands on the column through its ABU66SS — nothing left for a gusset to hold.
    # Spent uids, do not reuse.
    # CN-SG-TIE-BR2 (uid J6XRAXQG5T) is retired, with the joist reinforcement above. It held
    # the *front* bearing of PT-SG-BR2's joist line down against the prying
    # a loaded cantilever tip put there; with the pillar row moved onto the back-beam line
    # there is no cantilever tip to load. The uid is spent — do not reuse it.
    # Front-beam pockets, the same concrete-face-mount detail as the back pair above.
    Connector(uid="SGCH03AAAA", tag="CN-SG-HGR-FW", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_ax_front)), elevation=_back_beam_mid,
              size="HUC212-3", connects=("BM-SG-FRW", "W-SG-W1")),
    Connector(uid="SGCH04AAAA", tag="CN-SG-HGR-FE", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_ax_front)), elevation=_back_beam_mid,
              size="HUC212-3", connects=("BM-SG-FRE", "W-SG-E1")),
    # CN-SG-TIE-FCOL/-FCOLB (SGCT02AAAA/SGCT02BAAA): retired with the pair above.
]

# THE FOUR BEAM STANDOFF SHIM PACKS — every wood beam soffit in this garden that lands on a
# pour. They existed as prose inside SUNKEN_GARDEN_COLUMN_12.source and PIER_CONCRETE_12
# .source ("tolerance taken in a 1/2\"-1\" stainless standoff shim pack") and nowhere else:
# a real purchased part at a real joint with nothing in the BOM, nothing in 3D and nothing a
# reviewer could click. SS316-SHIM-35 carries the detailing now — no grout island, 316
# stainless or HDG with an isolator, EPDM/HDPE where the pack meets an HGAM10 — and these
# four make it countable.
#
# One per column top, beside the gusset that holds the beam down to it. The four balcony
# corners land on `_balcony_beam_soffit` PLUS THEIR ROW'S RISE — the rear row's two seats are
# 2" above the front row's, because the beams tilt (see `_balcony_rise_at`). PT-SG-COL and
# PT-SG-FCOL take none: no beam bears on them, their pillars stand on ABU66SS.
#
# ** THE FOUR BALCONY PACKS ARE LAPPED, NOT FLAT, AND THE SHAPE IS THE SPEC. ** A tilted beam
# on a level cast seat bears on a LINE: at 0.0227 in/in the uphill edge of a 6" bearing stands
# 1/8" off. The pack's leaves are lapped to form that taper — full leaves at the low edge,
# progressively short ones toward the high — over the EPDM isolator the seat detail already
# prescribes, which conforms the rest under load. **Do NOT spec a custom tapered metal shim**:
# tapered stainless shims are laser-cut/CNC specialist items, not a stock construction part,
# and a pack is already a stack of leaves. SJI requires no sloped seat below 3/8 in per foot
# and bridge practice taper-shims sloped girders to the nearest 1/16 in, so this slope is
# inside the range a conforming pad handles. notes/balcony_differential_movement.md §3.
#
# ``elevation`` is the SOFFIT LESS HALF THE PACK, for the same reason the seat connectors'
# elevation comment gives above: a Connector draws as a marker box CENTRED on its elevation
# (accessories.py::_resolve_connector), so authoring the soffit itself would draw a 1" pack
# half inside the beam it holds up. Half a pack down puts the box in the gap it occupies,
# which is the one thing about this part a drawing has to show.
_STANDOFF_SHIM_IN = 1.0
_shim_drop = inch(_STANDOFF_SHIM_IN / 2.0)
_STANDOFF_UID = {("R", 1): "SGSD1RAAAA", ("R", 3): "SGSD3RAAAA",
                 ("F", 1): "SGSD1FAAAA", ("F", 3): "SGSD3FAAAA"}
for _row, _y, _rise in _PILLAR_ROWS:
    for _i in _CORNER_PILLAR_INDICES:
        CONNECTORS.append(Connector(
            uid=_STANDOFF_UID[(_row, _i)], tag=f"CN-SG-STDF-{_row}{_i}",
            kind=ConnectorKind.BEARING_STANDOFF,
            position=pt(ft(_PILLAR_X[_i - 1]), ft(_y)),
            elevation=_balcony_beam_soffit + _rise - _shim_drop, size="SS316-SHIM-35",
            connects=(_CORNER_SEAT_BEAM[(_row, _i)], f"PT-SG-B{_row}{_i}")))
CONNECTORS += [
    Connector(uid="SGSDCLAAAA", tag="CN-SG-STDF-COL",
              kind=ConnectorKind.BEARING_STANDOFF,
              position=pt(ft(_cx), ft(_y_col)),
              elevation=_back_beam_soffit - _shim_drop, size="SS316-SHIM-35",
              connects=("BM-SG-BKW", "BM-SG-BKE", "PT-SG-COL")),
    Connector(uid="SGSDFCAAAA", tag="CN-SG-STDF-FCOL",
              kind=ConnectorKind.BEARING_STANDOFF,
              position=pt(ft(_cx), ft(_y_ax_front)),
              elevation=_back_beam_soffit - _shim_drop, size="SS316-SHIM-35",
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
# pipe drops just clear of the wall's *outer* face at x = 29.0, on the balcony's front
# plane. ** IT HANGS OVER W-RG-EAST-BALCONY SINCE 2026-09-12, NOT BESIDE IT. ** The return
# used to stop 6" short and the pipe threaded that slot with 1.5" of strap clearance each
# side; the notch that slot left in the retaining wall was closed instead, so the block now
# runs under the pipe, 6" below its outlet. Nothing touches and no check grades the pair.
# The outlet takes a cast elbow and a 1'-0" shoe south to discharge past the cap at
# y = -11'-3", onto the same terrace stone — keeping a 200 sf deck's whole discharge off
# the crest of a dry-stacked wall is the point, and the shoe is not modelled.
_SG_LEADER_OUTSET = 0.25   # ft outboard of the deck edge, which IS the east wall's face
_SG_GUTTER_OVERSAIL = 0.5  # ft of trough past that edge, to carry the outlet
_SG_LEADER_X = _deck_x_e + _SG_LEADER_OUTSET
_SG_LEADER_DIA_IN = 3.0
_GUTTER_PATH = (pt(ft(_deck_x_w), ft(_y_balcony_front)),
                pt(ft(_deck_x_e + _SG_GUTTER_OVERSAIL), ft(_y_balcony_front)))
# Gutter rim meets the drip flashing's lower edge, so water shedding off the drip lands in
# the trough.
_drip_depth_in = 3.0
BALCONY_GUTTER = Gutter(
    uid="SGGT01AAAA", tag="TR-SG-GUTTER", kind=TrimKind.GUTTER, path=_GUTTER_PATH,
    top_elevation=_deck_top - inch(_drip_depth_in), depth=inch(4), thickness=inch(5),
    material="metal-dark-kstyle", host_ref="TR-SG-FASCIA", slope="1/16 in/ft to SE downspout",
    downspout_ref="TR-SG-LEADER-SE",
    # The last 6" oversails TR-SG-FASCIA (and the drip above it): that bay exists only to
    # put the outlet outboard of the pillar and the wall, and it hangs off the end hanger.
    # The run goes west→east, so its left-hand normal (resolve/geometry.py::normal) points
    # north (+y) — the porch/house side. The channel's back sheet rides the fascia there.
    back_side="left")
# 3" round, not the roof's 4": catches only the balcony deck (~200 sf) vs. 648 sf per house
# eave. It no longer drops into the sunken garden — hanging outboard of the east wall there
# is no garden underneath it — so it discharges 6" above the raised terrace, whose surface
# is level with that wall top at +0'-2" (raised_garden.TOP). DRW-SG-MAIN stops naming it as
# an inlet for the same reason, and that is the better half of the trade: the soakaway
# serves a 9'-deep pit with no outlet of its own, and 200 sf of balcony runoff is the one
# contribution it does not have to swallow.
_SG_LEADER_BOTTOM = _ret_top + inch(6)
BALCONY_LEADER = Downspout(
    uid="SGDS01AAAA", tag="TR-SG-LEADER-SE",
    position=pt(ft(_SG_LEADER_X), ft(_y_balcony_front)),
    top_elevation=_deck_top - inch(_drip_depth_in) - inch(4),  # the trough floor
    bottom_elevation=_SG_LEADER_BOTTOM,
    diameter=inch(_SG_LEADER_DIA_IN), material="metal-dark-kstyle",
    gutter_ref="TR-SG-GUTTER",
)

# ** THE SLOT IS GONE, AND SO IS ITS PUBLISHED CONTRACT (2026-09-12). ** For nine days the
# raised garden's two returns were derived from a `BALCONY_LEADER_SLOT_FT` exported here, so
# that a change to `joist_cantilever_in`, to the leader's bore or to its strap allowance
# moved the returns with the pipe. The returns close on the court wall's outer face now —
# the notch the slot left in a retaining wall outranked the pipe's clearance — so there is
# nothing left to publish and nothing left to keep in step. The leader's own numbers are
# `_SG_LEADER_X`, `_SG_LEADER_DIA_IN` and `_SG_LEADER_BOTTOM`, above, and its outlet shoe is
# a drawing note in `params/raised_garden.py`.

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
# Beam cap flashing — formed metal over the four porch beams.
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
# ** NO CAPS ON THE BALCONY GLULAMS (2026-09-16); butyl only. ** BM-SG-BLC is flush: the plank
# covers it. BM-SG-BLW/BLE carry 2x8s at 16" o.c. that cantilever 9" past them, so a cap
# would be cut into short bits between joists that the plank above already shelters.
#
# ** ALL FOUR GO ON BEFORE THE JOISTS DO, AND THAT IS NOT A PREFERENCE. ** The porch beams
# carry their joists ON TOP. A cap over a beam
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
_porch_cap_thickness = ft(_porch_beam_width_ft) + inch(2 * _CAP_LAP_IN)

# Each beam's resolved TOP — the plane the cap sits on. A cap authored on the storey datum
# would float above the beam instead.
_back_beam_top = _porch_top - ft(_porch_joist_depth_ft)   # joists bear on top
_front_beam_top = _back_beam_top                          # joists bear on top

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
)
BEAM_CAPS = [
    Flashing(uid=uid, tag=tag, kind=TrimKind.BEAM_CAP,
             path=(pt(ft(p0[0]), ft(p0[1])), pt(ft(p1[0]), ft(p1[1]))),
             top_elevation=top, depth=inch(_CAP_LEG_IN),
             thickness=thickness, material="aluminum", host_ref=host)
    for uid, tag, p0, p1, top, thickness, host in _BEAM_CAP_AT
]
PORCH_BEAM_CAPS = BEAM_CAPS

# ============================================================================
# Per-storey exports (spliced into plan/manifest.py).
# ============================================================================
# ** THE COURT'S SEQUENCING AND PROCUREMENT NOTES (2026-09-10). **
# Everything below is a field instruction, not geometry. It is here rather than in prose
# because the model has no element that says "one pour" or "before November", and the three
# things these say are each worth more than any dimension on this drawing.
#
# uid prefix SGAN — `haus fmt` does not visit `params/*.py`, so these are hand-minted and
# must stay unique by hand; a collision is a load-time ERROR.
SEQUENCE_NOTES = [
    Annotation(
        uid="SGAN01AAAA", tag="AN-SG-PLACEMENTS", position=pt(ft(_cx), ft(-20)),
        text="THREE PLACEMENTS, NOT FOUR — AND THE ORDER IS THE DESIGN. (1) FOOTINGS AND PIERS: the five strip footings FT-SG-W1/E1/W2/E2/S and BOTH column pads in one placement. THE PADS ARE FORMED, NOT UNDER-REAMED, SINCE 2026-09-14: 30in square by 12in thick, bearing at -12ft 7-7/16in, with the 12in round cast on top of each. There is no auger and no under-reamer on this job any more — the excavation is dug and the pad is formed in the bottom of it, which is why the levelling bed under each (FB-SG-COL/-FCOL) is still 7in of washed stone and not a 42in replacement section. Dig both pits WITH THE OPEN BASEMENT EXCAVATION: PD-SG-COL reaches to within 8in of FT-B-S2/S3 in plan and bears 34in below them, inside their 1:1 influence line, so excavating after backfill undermines the house footing. (2) WALLS AND GRADE BEAM: all five court walls, W-SG-ARCH and W-SG-BRKBM, one form height (every wall top is the porch datum 0ft 0in), one strip-and-set. W-SG-BRKBM IS CAST MONOLITHIC WITH THE TWO SIDE WALLS, NOT DOWELLED INTO THEM (settled 2026-09-14): it is a blockout inside this same form between -8ft 6-7/16in and -10ft 0-3/16in, its 3 #5 top and bottom lapping into W-SG-W1/W-SG-E1s vertical steel. It was named in NO placement until now, while notes/sunken_garden_veneer_beam.md called it cast in one section and chipped-and-dowelled in another - and there is no existing pour to chip, because this placement is where those side walls are themselves cast. THE HOUSE BASEMENT WALL MUST BE POURED, CURED AND SURVEYED FIRST — the upper thermal-break dowels are epoxied into it with about 1in of drill tolerance. (3) RIM SLAB AND COLUMNS: SL-SG-FLOOR with all six 12in cast rounds in the same placement, the four balcony corners braced off the court floor and the wall tops rather than off porch framing that does not exist yet. EVERY COURT PLACEMENT NEEDS THE BOOM PUMP and the pumping allowance is already recorded as probably short. This saves one mobilisation and one below-minimum load against the four-pour sequence it replaces"),
    Annotation(
        uid="SGAN02AAAA", tag="AN-SG-MIX", position=pt(ft(_cx), ft(-23)),
        text="MIX SUBSTITUTION, PERMITTED: the court comes off ONE ticket. PIER_BASE_12 (the two belled pier bases) specifies BURIED_MIX and everything else here specifies EXPOSED_MIX. Both are 5,000 psi at w/cm <= 0.40; EXPOSED_MIX adds class F3+C2 air entrainment and SCM caps, so it satisfies every requirement BURIED_MIX states and is the richer of the two. SUPPLY THE WHOLE COURT WITH EXPOSED_MIX. Do not read this as an assembly change — PIER_BASE_12 is shared with the north entry's pads, where the buried mix is correct and cheaper, and retyping it would move concrete that is not in this court. This note is the substitution; the schedule is not wrong"),
    Annotation(
        uid="SGAN03AAAA", tag="AN-SG-COLDWEATHER", position=pt(ft(_cx), ft(-26)),
        text="MILESTONE, HARD: the court's LAST placement (3) is before 1 NOVEMBER. Cold-weather protection is priced at zero on a summer-pour assumption and is worth $8,000-21,000 if it slips — heated enclosure, blankets, admixture and extended cure over a 9ft hole with no drainage, which is the expensive end of that range. This placement sits at the end of the longest dependency chain of any concrete in the house: house basement wall poured, cured and surveyed, then the footing trim at FT-B-S2/S3 signed off, then placements (1) and (2), then this. Pulling the six columns forward into (3) rather than leaving them to a fourth pour behind the porch carpentry is as much a schedule hedge as a saving"),
]

BASEMENT_ELEMENTS = [*NODES, *WALLS, *GRADE_BEAMS, COLUMN, FRONT_COLUMN, *FOOTINGS,
                     *FOOTING_BEDDING, GARDEN_DRYWELL, GARDEN_UNDERDRAIN, GARDEN_OVERFLOW,
                     GARDEN_OVERFLOW_SLEEVE, GARDEN_OVERFLOW_BEAM_PIPE,
                     GARDEN_LEAD_W, GARDEN_LEAD_E, GARDEN_LEAD_COL, *SEQUENCE_NOTES,
                     *GARDEN_FLOOR_OPENINGS, GARDEN_SLAB,
                     GARDEN_FIELD, *FROST_WINGS, *DOWELS, *STEM_DOWELS]
# --- the porch enclosure's north deck-slot closure (2026-09-03) -----------------------
# ** THE VERTICAL BUG PATH, AND THE ONE THE CURTAIN CANNOT CLOSE. ** `_y_out_n` (-0'-10")
# is the porch deck edge; the house cladding face is at -0'-5". The 5" between them
# (`SPEC.gap_to_house_in`) is a deliberate insulation gap and it is open down to grade for
# the whole 19' — an insect route from the garden straight up into the enclosure, past a
# curtain that seals perfectly. The enclosure's flank panels stop at the deck; this closes
# the slot they stop over.
#
# ** IT FASTENS TO THE GARDEN AND NOTHING ELSE. ** Screws into the porch deck's north rim
# only; the piece cantilevers 4" north and dies on the cladding through a compressible foam
# or brush lip that BEARS on it without penetrating it. Sloped south to drain back over the
# deck. That lip, and the weighted flap on the flank panels' north vertical edge, are what
# the north end is: **high bug reduction, not hermetic.** With a designed 5" gap and no
# permission to fasten into the house wall assembly, a contact sweep is the ceiling of what
# is achievable — and it is also the right wind-chill answer, since a compressible seal
# tolerates the differential movement a rigid one would tear itself apart on.
#
# `TrimKind.BUG_SCREEN` rather than a new kind: the enum is "vented insect closure", which
# is exactly this piece's job, and minting a kind that means the same thing would split one
# $/LF rate across two price keys. It is not a rainscreen base (the case the enum comment
# was written for), so it does NOT collide with the derived `bug_screen:EXT_2X6`
# rows in [openings] — those come off wall layers, this is an authored `_EdgeRun` billed by
# the foot in [edge_trim].
#
# `top_elevation=_porch_top` is the top of the JOISTS, which is where a piece screwed to the
# rim lands: the composite plank's north edge laps over it.
_SLOT_CLOSURE_REACH_IN = 4.0
_slot_closure_y = _y_out_n + (_SLOT_CLOSURE_REACH_IN / 2.0) / 12.0  # band centre
PORCH_SLOT_CLOSURE = Flashing(
    uid="SGFF03AAAA", tag="TR-SG-SLOT", kind=TrimKind.BUG_SCREEN,
    # `_x_in_w`/`_x_in_e` (8'-6"/27'-6") is the porch's clear width — the inner faces of
    # W-SG-W1/E1, which is where the deck's north rim is reachable to screw into. 19'-0".
    path=(pt(ft(_x_in_w), ft(_slot_closure_y)),
          pt(ft(_x_in_e), ft(_slot_closure_y))),
    top_elevation=_porch_top, depth=inch(2), thickness=inch(_SLOT_CLOSURE_REACH_IN),
    material="aluminum", host_ref="FS-SG-PORCH",
    # West→east, so the left-hand normal points north — the house side, which is the end
    # carrying the lip rather than the fastener line.
    back_side="left")

# Every remaining connector is porch hardware at the deck (post bases, hangers, the column
# ties and the four corner beam-seat gussets), so main takes them whole. With the knee
# braces retired there is no second-storey hardware at all.
MAIN_ELEMENTS = [*MAIN_NODES, *BACK_BEAMS, *FRONT_BEAMS, PORCH_JOISTS, *PILLAR_CHASES,
                 PORCH_SLOT_CLOSURE,
                 PORCH_GUARD, PORCH_GUARD_NE, *RAISED_BED_GUARDS,
                 *CONNECTORS, *PORCH_BEAM_CAPS,
                 HP_PAD, *HP_STAND_LEGS, *HP_STAND_ANCHORS,
                 STAIR_PAD, PORCH_STAIR, *PORCH_STAIR_RAILS,
                 *PORCH_STAIR_THRESHOLD_RAILS]
SECOND_ELEMENTS = [*SECOND_NODES, *BALCONY_BEAMS, *PILLARS,
                   BALCONY_JOISTS, BALCONY_GUARD, BALCONY_FASCIA,
                   BALCONY_GUTTER, BALCONY_LEADER, BALCONY_DRIP, BALCONY_REAR_FLASH]

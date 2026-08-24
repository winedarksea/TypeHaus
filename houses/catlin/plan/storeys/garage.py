# haus: editable
# Garage — freestanding 24'x24' ICF stem + 2x6 wood walls, 4' north of the house
# (west walls aligned). Wood walls sit on the ICF stem 22" above grade; the storey
# elevation is the top of the stem. Overhead door faces east (driveway side).
from typehaus import (
    Alarm,
    AlarmKind,
    Connector,
    ConnectorKind,
    Door,
    Downspout,
    EaveGutter,
    EaveTrim,
    FasciaBoard,
    Node,
    Occupancy,
    Pitch,
    Railing,
    RailingKind,
    Roof,
    RoofForm,
    Room,
    Stair,
    StructuralRole,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

# The garage's two N-S wall lines, published so the ICF stem (params/foundations.py), the
# slab, and the breezeway (params/breezeway.py) all derive from one number.
#
# 40'-6 7/8" is set by the breezeway off the *cladding*, not the stem: the stem's exterior
# EPS face is coplanar with the wood wall's zip-R face (both land on this line), so the
# most-proud plane is the 7/8" of rainscreen + standing seam at y = 40'-6" — what the
# breezeway deck/glazing butt against, 4'-0 1/2" north of the house's cladding face
# (y = 36'-5 1/2"): one UNCUT 4'-0" polycarbonate panel with a 1/2" reveal.
#
# Moved 5 5/8" south from 41'-0" on 2026-08-15 when the stem was aligned to it and dropped
# from an 8" core to 6". Moving the wall lines with the stem (rather than aligning the stem
# alone) keeps the breezeway slot and its uncut panel unchanged — see CLAUDE.md's ICF
# stem/wood-wall coplanarity note; do not move these nodes independently of the stem.
#
# ** MOVED 1/2" NORTH ON 2026-08-23, and the whole 24'x24' went with it. ** The truss wall
# put the house's cladding face 1/2" further out (5.02" -> 5.5" proud of the y=36' sheathing
# plane), which spent the breezeway's reveal exactly: the slot closed to 4'-0" on the nose
# and an uncut 4'-0" sheet cannot be glazed into an opening it exactly fills. Ripping the
# sheet 1/2" was the detail-scale answer and is retired; this is the site-scale one, and it
# is the better trade because the reveal is the only thing in the slot that was ever free.
# BOTH lines move together — the garage stays 24'-0" square, the stem, footings, slab and
# breezeway all derive from these two numbers, and nothing north of the house is dimensioned
# to a property line closer than 40'.
GARAGE_Y_SOUTH = ft(40, 6.875)
GARAGE_Y_NORTH = ft(64, 6.875)

# ICF stem height above grade == this storey's elevation (wood walls sit on the stem top).
# Published so the storey table, the stem (params/foundations.py) and the overhead door's
# drop to grade all read one value instead of three copies of 1'-10".
GARAGE_STEM_REVEAL = ft(1, 10)

NODES = [
    Node(uid="CGN001AAAA", tag="N-G-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGN002AAAA", tag="N-G-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGN003AAAA", tag="N-G-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGN004AAAA", tag="N-G-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
]

# 8'-4" plates, not 8'-0" (2026-08-21). The garage went down 4" with grade while
# D-G-SERVICE's threshold stayed pinned to the breezeway deck at 0'-0" — so the door climbed
# 4" inside its own wall and its 3-ply LVL header pushed straight through the top plate into
# the truss heels (structural.member_interference caught it). Growing the plates by the same
# 4" puts the garage roof back at the absolute elevation it had before the lift and restores
# the 8" the header needs above the rough head. The slab went down with grade too, so the
# interior clear height is unchanged.
WALLS = [
    Wall(uid="CGW101AAAA", tag="W-G-S", start_node="N-G-SW", end_node="N-G-SE",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", end_node="N-G-NE",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CGW103AAAA", tag="W-G-N", start_node="N-G-NE", end_node="N-G-NW",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW104AAAA", tag="W-G-W", start_node="N-G-NW", end_node="N-G-SW",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
]

# Published so params/foundations.py can gap the ICF stem under the overhead door instead
# of repeating this offset/width: there is no 22"-above-grade stem wall under a vehicle
# door (it would be a curb the car has to climb), so the stem drops to a grade beam there.
OVERHEAD_DOOR_OFFSET = ft(4)
OVERHEAD_DOOR_WIDTH = ft(16)  # DT-EXT-OVERHEAD192

# Same pair for the service door (2026-08-01): identical treatment for the identical
# reason — it opens off the slab at grade, not the stem top its host wall starts on, so
# the stem gaps to a grade beam here too. Previously stood 1'-10" above the slab and the
# breezeway deck, a "known, deferred mismatch" that code.R311_3_exterior_landing eventually
# failed outright.
SERVICE_DOOR_OFFSET = ft(5)
SERVICE_DOOR_WIDTH = ft(3)  # DT-EXT-SWING36

OPENINGS = [
    # 16' opening is past the prescriptive header table, hence the named engineered beam:
    # a 2-ply 14" LVL.
    #
    # Threshold is the slab at grade, not the host wall's own floor: W-G-E starts at the
    # stem top, GARAGE_STEM_REVEAL above the slab, so the door reaches *down* past its host
    # — the plan's one negative sill_height, the exact negation of that reveal (spelled out
    # rather than computed; the dialect bans arithmetic). It stays -1'-10" through the
    # 2026-08-18 lift: the slab is still at grade and the stem top is still 1'-10" over it,
    # and both simply moved down together. The tie is held by
    # test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade.
    # Head follows the threshold down to 7'-0" above the slab. params/foundations.py gaps
    # the stem to a grade beam under this opening so there's no curb for the car to climb.
    Door(uid="CGD201AAAA", tag="D-G-OVERHEAD", host="W-G-E",
         type_ref="DT-EXT-OVERHEAD192", position=from_node("N-G-SE", OVERHEAD_DOOR_OFFSET),
         sill_height=ft(-1, -10), header_spec='2-ply 14" LVL'),
    # **This door no longer reaches down to the slab; it reaches up to the breezeway.**
    # Until 2026-08-18 it carried D-G-OVERHEAD's negative sill for the same reason — both
    # thresholds and the breezeway deck were one plane at 0'-0". Then grade dropped 2'-6"
    # and took the garage with it while the house and the breezeway deck stayed. The deck is
    # still the landing outside this door (code.R311_3_exterior_landing, and the house rule
    # that both breezeway doors open onto it at one level), so the threshold has to stay at
    # 0'-0" absolute: +1'-0" over a garage storey that now sits at -1'-0" (it was +0'-8"
    # over -0'-8" until the house rose 4" on 2026-08-21 and the garage went down with grade).
    # Inside, ST-G-STEPS takes the 2'-10" down to the slab.
    #
    # The head lands 8" under the top plate — 6'-8" of door in a wall whose plate is at
    # +7'-4" — which is why this opening now names a header the way the overhead door does.
    # There is 6 1/2" between the rough head and the top of wall, and the table's 2-2x8
    # (7 1/4") does not fit it: the solver grows a header up from the rough head, so an
    # oversized one pushes straight through the plates into the truss bottom chords
    # (structural.member_interference caught exactly that). A 5 1/2"-deep 3-ply LVL does
    # fit, three plies filling the 2x6 wall, and it is the ordinary answer for a tall
    # opening in a garage wall: a continuous header carried at the plate line rather than
    # dropped below it (IRC R602.7.2 lets the header take the top plate's place).
    Door(uid="CGD202AAAA", tag="D-G-SERVICE", host="W-G-S", type_ref="DT-EXT-SWING36",
         position=from_node("N-G-SW", SERVICE_DOOR_OFFSET), sill_height=ft(1),
         header_spec='3-ply 5.5" LVL'),
    # This 8' wall (vs. the house's 10') is why the 27" family is 36" tall: a 60" height at
    # this 42" sill would push the header above the top plate. Nudged to 1'-5" (2026-07-29):
    # at 1'-4 5/8" the RO missed the bay centre by 3/8", enough to break two studs and pull
    # in a header a 14" RO should never need
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    Window(uid="CGX301AAAA", tag="WIN-G-N1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(1, 5)), sill_height=ft(3, 6)),
    # WIN-G-N1's mirror at the south end (2026-07-30): 22'-0" off N-G-NW is the exact mirror
    # of N1's 2'-0", and also a bay centre (8" + 16"x16 on W-G-W's grid), so the pair stays
    # symmetric and both keep the unbroken stud bay a 14" RO exists to get. Same 3'-6" sill
    # (above a workbench).
    Window(uid="CGX302AAAA", tag="WIN-G-S1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(21, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    Room(uid="CGR401AAAA", tag="RM-GARAGE", seed=pt(ft(12), ft(60)),
         occupancy=Occupancy.GARAGE, conditioned=False,
         floor_finish="sealed-concrete"),
]

# Gable roof, ridge E-W (rotated 90° vs the house), 16" overhangs. E/W walls stay flat 8'
# rather than `top=ToRoof`: a raked wall top must split at the ridge, but the 16' overhead
# door is centered on the ridge, so W-G-E can't be split. Both gable triangles are instead
# closed by the wall→roof closure in resolve/roof_edge.py.
# Eave + rake trim is two-layer: a 2x6 wood sub-fascia (structural nailer) lapped by a 5/4
# cellular-PVC fascia (weather face). A vented PVC soffit closes the overhang and feeds the
# vent channel. Elevations derive from the resolved roof plane so the raised-heel lift
# carries the trim with it.
# The SOUTH eave gets a 5" aluminum gutter: that slope faces the 4' breezeway gap and the
# house wall people walk under, and now also catches what sheds off the breezeway roof.
# North eave stays free-draining onto open ground. Declared here rather than in params/
# for the same reason as the fascia — the raised-heel truss lifts the deck plane at the
# envelope stage, so an absolute elevation would drift off the eave.
_GARAGE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="pvc-cellular", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
    gutter=EaveGutter(material="aluminum", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("south",),
                      slope="1/16 in/ft to the east downspout",
                      downspout_ref="TR-G-LEADER-E"),
)

# The leader the south gutter has always sloped to; named in the slope note but never
# authored until now, so it drained to nothing. 3" round, not the house's 4": this slope
# sheds ~290 sq ft against each house eave's 648, and 3" clears ~425 sq ft at the 8 in/hr
# design intensity (params/roof_trim.py works the number).
# test_drainage_elements.py holds this and the EaveGutter together so a roof change that
# moves the trough fails there instead of leaving a leader hanging beside it.
_GARAGE_LEADER = Downspout(
    uid="CGDS01AAAA", tag="TR-G-LEADER-E",
    position=pt(ft(25), ft(39, 5)),     # east end of the trough, on its centreline
    # Both absolute, and both dropped 2'-6" on 2026-08-18 when grade did and the garage
    # went down with it. The trough they bracket is derived from the roof plane, so it moved
    # on its own; these are the two numbers that had to follow it by hand.
    top_elevation=ft(7, 6),             # inside the trough floor
    bottom_elevation=ft(-1, -6),        # splash block, a foot above the apron
    diameter=inch(3), material="aluminum", gutter_ref="RF-GARAGE",
)

ROOFS = [
    Roof(uid="CGRF01AAAA", tag="RF-GARAGE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-G-S", "W-G-N"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="x",
         eave_trim=_GARAGE_EAVE_TRIM),
]

# Snow retention on the south slope: the garage roof sheds toward the breezeway's
# polycarbonate canopy (GL-BW-ROOF), which sits 3.0' below this eave in the discharge band
# (structural.sliding_snow) — a willing 4:12 standing-seam slope over an unwilling
# multiwall-polycarbonate target.
# S-5! ColorGard: a continuous crossbar on seam clamps (StructuralHardware.requires_role
# bills the clamps automatically). Row runs x 1'-4"..8'-0" — canopy width plus a full bay of
# margin each end, since snow releases at an angle. Row count/spacing at Pg = 50 psf is the
# manufacturer's calculation; the check only screens for retention being *authored*.
# Placed 4" up-slope of the eave (y = 39'-6 7/8", z = 8'-1"), deliberately close to it since
# retention holds the pack where the load lives. (Position moved 5 5/8" south with the wall
# line on 2026-08-15; height didn't, since the wall didn't get taller. It dropped 2'-6" on
# 2026-08-18, when the garage followed grade down and the roof it clamps to went with it —
# an absolute elevation on a structure that moved.)
# Written out, not generated: the editable dialect allows no comprehensions.
_SNOW_GUARD_Y = ft(39, 6.875)
_SNOW_GUARD_Z = ft(8, 1)
_SNOW_GUARD_SIZE = "S-5! ColorGard"
SNOW_GUARDS = [
    Connector(uid="CGSG01AAAA", tag="CN-G-SNOW-1", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(1, 4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG02AAAA", tag="CN-G-SNOW-2", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(2, 8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG03AAAA", tag="CN-G-SNOW-3", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG04AAAA", tag="CN-G-SNOW-4", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(5, 4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG05AAAA", tag="CN-G-SNOW-5", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(6, 8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG06AAAA", tag="CN-G-SNOW-6", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
]

ALARMS = [
    # A garage gets a *heat* detector, not smoke: exhaust, dust and outdoor-swing temps would
    # nuisance-trip a smoke head, which is why R315 asks for CO coverage adjacent to the
    # garage rather than a smoke alarm inside it. On CKT-LT-BACKUP because R314.4 wants an
    # unswitched circuit and CKT-RC-GARAGE (GFCI) is wrong for a life-safety device.
    Alarm(uid="CGA701AAAA", tag="AL-G-HEAT", kind=AlarmKind.HEAT, room="RM-GARAGE",
          circuit="CKT-LT-BACKUP"),
]

# --- service-door stair (ST-G-SERVICE) --------------------------------------------------
#
# Five risers from the garage slab at -2'-10" up to D-G-SERVICE's threshold at 0'-0", the
# same 5 x 6.8" risers on 11" treads at 3'-0" wide that five concrete `Slab`s used to be
# (SL-G-STEP-0..4 in params/foundations.py). SL-G-STEP-0, the 3'-0" landing at the
# threshold, is still a Slab and belongs there — a landing is a floor, not a flight. The
# four treads below it are this.
#
# PRESSURE-TREATED WOOD, not concrete (owner, 2026-08-22): KDAT southern yellow pine, kiln-
# dried after treatment so it is stable enough to cut and fit like framing. The garden's
# beams and the breezeway already use it (BEAM_KDAT / POST_KDAT), so it is the house's
# established exterior-wood answer. Where the stringers land on the garage slab they need a
# capillary break — a strip of the same 10-mil under-slab retarder, which is on site anyway.
# PT stops the fungus that follows wicked water; it does not stop the wicking.
#
# `Stair` could not express this until 2026-08-22: it took its rise from a pair of storey
# elevations through a FloorOpening in the storey above, and this is a step-down *within* one
# storey with no floor to open. `floor_opening` is optional now and `base_elevation` /
# `top_elevation` state the rise directly. That is what puts the flight in front of
# `structural.stair_riser_uniformity` and `code.R311_7_8_handrail`, neither of which could
# see a stack of slabs, and what RL-G-SERVICE below is the answer to.
#
# The elevations are literals because this file is `# haus: editable` and may hold only
# literals; -2'-10" is `params/foundations.SITE_GRADE`, which `plan/site.py` repeats as
# `Site.grade` and `plan/manifest.py` asserts the two agree. `start` is the foot of the
# flight — GARAGE_Y_SOUTH + 3'-0" of landing + 4 x 11" of tread = 47'-2 3/8" — and it climbs
# south (`run_reversed`) back to the landing's north edge. All three y literals below
# went up 1/2" on 2026-08-23 with GARAGE_Y_SOUTH.
#
# 11" treads with NO nosing, which keeps the run at the 3'-8" the four slabs occupied and
# leaves an 11" going against R311.7.5.2's 10" minimum. A nose would shorten the run and buy
# nothing here.
STAIRS = [
    Stair(uid="X99TD38ZS3", tag="ST-G-SERVICE",
          from_storey="garage", to_storey="garage",
          base_elevation=ft(-2, -10), top_elevation=ft(0),
          width=ft(3), start=pt(ft(5), ft(47, 2.875)),
          run_direction="y", run_reversed=True,
          tread_depth=inch(11), nosing_depth=inch(0),
          material="kdat"),
]

# R311.7.8 wants a handrail on any flight of four or more risers, and this one has five.
# Nothing was asking for it while the flight was five slabs, because both handrail rules
# iterate `model.stairs`.
#
# Post-mounted on the west side of the run, not wall-mounted: the flight stands in the
# open on the garage floor at x=5'..8', with the nearest wall 5'-0" away. The posts stand on
# the treads (`serves_stair` rakes the rail along the flight's nosing line) and the rail
# tops out 36" above them, inside R311.7.8.1's 34"-38".
#
# FLAGGED, NOT ANSWERED: the landing at 0'-0" is **34" above the garage slab**, over
# R312.1.1's 30" threshold, so its open east and north sides want a guard as well as this
# handrail. That is a design decision with a cost and a look to it, and it is the owner's,
# not this file's.
#
# **Nothing in the engine will ask.** `code.R312_1_guard_height` censuses `FloorSystem`s and
# `code.R312_1_guard` censuses `FloorOpening`s; SL-G-STEP-0 is a `Slab`, so it is in neither
# census and its 34" drop is invisible to both. That is a real coverage gap, not a pass —
# recorded in plans/TODO.md rather than papered over here, because the fix is a rule that
# walks slab edges and belongs with the guard rules, not with this stair.
RAILINGS = [
    Railing(uid="CX7KN0MZE0", tag="RL-G-SERVICE",
            path=(pt(ft(5), ft(47, 2.875)), pt(ft(5), ft(43, 6.875))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=ft(-2, -10), post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="handrail", serves_stair="ST-G-SERVICE", top_height=inch(36),
            graspable_profile="1.5in round — Type I"),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ROOFS, _GARAGE_LEADER,
            *SNOW_GUARDS, *ALARMS, *STAIRS, *RAILINGS]

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
    Roof,
    RoofForm,
    Room,
    StructuralRole,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

# The garage's two N-S wall lines, published so the ICF stem under them
# (params/foundations.py), the slab inside them, and the breezeway that spans to the house
# (params/breezeway.py) all derive from one number instead of four copies of it.
#
# 41.0' is set by the breezeway, and by the *stem* rather than the wall above it: the 13"
# ICF section is wider than the 7 7/8" wood wall, so its exterior face stands 5 5/8" proud
# of the cladding, at y = 40'-5 1/2". That face — not the cladding — is what the breezeway
# deck and its glazing actually butt against. It sits 4'-0 1/2" north of the house's own
# cladding face (y = 36'-5.02"), which is one 4'-0" polycarbonate panel with a 1/2" reveal.
GARAGE_Y_SOUTH = ft(41)
GARAGE_Y_NORTH = ft(65)

# How far the ICF stem stands above grade — which is the same number as this storey's
# elevation, because the wood walls sit on the stem top. Published so the storey table
# (plan/manifest.py), the stem itself (params/foundations.py) and the overhead door's
# drop to grade below all read one value instead of three copies of 22".
GARAGE_STEM_REVEAL = ft(1, 10)

NODES = [
    Node(uid="CGN001AAAA", tag="N-G-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGN002AAAA", tag="N-G-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGN003AAAA", tag="N-G-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGN004AAAA", tag="N-G-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
]

WALLS = [
    Wall(uid="CGW101AAAA", tag="W-G-S", start_node="N-G-SW", end_node="N-G-SE",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", end_node="N-G-NE",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CGW103AAAA", tag="W-G-N", start_node="N-G-NE", end_node="N-G-NW",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW104AAAA", tag="W-G-W", start_node="N-G-NW", end_node="N-G-SW",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.NONBEARING),
]

# Published so params/foundations.py can gap the ICF stem under the overhead door instead
# of repeating this offset/width: there is no 22"-above-grade stem wall under a vehicle
# door (it would be a curb the car has to climb), so the stem drops to a grade beam there.
OVERHEAD_DOOR_OFFSET = ft(4)
OVERHEAD_DOOR_WIDTH = ft(16)  # DT-EXT-OVERHEAD192

# The same pair for the service door (2026-08-01). It needs the identical treatment for the
# identical reason: it opens off the slab at grade, not off the stem top its host wall
# starts on, so the stem gaps to a grade beam under it too. A person will not climb a 22"
# curb any more happily than a car does — this door stood 1'-10" above both the garage slab
# inside it and the breezeway deck outside it, which the breezeway module recorded as a
# "known, deferred mismatch" and code.R311_3_exterior_landing eventually failed outright.
SERVICE_DOOR_OFFSET = ft(5)
SERVICE_DOOR_WIDTH = ft(3)  # DT-EXT-SWING36

OPENINGS = [
    # The 16' opening is past the prescriptive header table, so the engineered beam
    # is named on the instance: a 2-ply 14" LVL across the overhead door.
    #
    # A car drives in off the slab, so this door's threshold is the slab at grade — not the
    # base of the wall hosting it. Every other opening in the house sits on its host wall's
    # own floor, but W-G-E starts at the stem top, one GARAGE_STEM_REVEAL above the slab
    # inside it, so the door reaches *down* past its host: the one negative sill_height in
    # this plan, and the exact negation of that reveal. The dialect bans arithmetic here, so
    # the two cannot be spelled as one expression — the tie is held instead by a contract
    # test asserting the resolved threshold lands on SL-G-FLOOR's top
    # (test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade).
    # The head follows the threshold down to 7'-0" above the slab (a 7' door is 7' of clear
    # opening wherever it sits), leaving the LVL and its cripples in the wall's top 2'-10".
    # params/foundations.py gaps the stem to a grade beam under exactly this opening, so
    # there is no curb left across the threshold for the car to climb.
    Door(uid="CGD201AAAA", tag="D-G-OVERHEAD", host="W-G-E",
         type_ref="DT-EXT-OVERHEAD192", position=from_node("N-G-SE", OVERHEAD_DOOR_OFFSET),
         sill_height=ft(-1, -10), header_spec='2-ply 14" LVL'),
    # Reaches down to the slab exactly as D-G-OVERHEAD does, and for the same reason — see
    # SERVICE_DOOR_OFFSET above. Same negation of GARAGE_STEM_REVEAL, spelled out for the
    # same dialect reason (no arithmetic in an editable file), and the head follows the
    # threshold down so a 6'-8" door is 6'-8" of clear opening off the floor it opens onto.
    Door(uid="CGD202AAAA", tag="D-G-SERVICE", host="W-G-S", type_ref="DT-EXT-SWING36",
         position=from_node("N-G-SW", SERVICE_DOOR_OFFSET), sill_height=ft(-1, -10)),
    # This 8' wall (vs. the house's 10') is why the whole 27" family is 36" tall: a
    # 60" height at this 42" sill would push the header above the top plate.
    # Nudged to 1'-5" (2026-07-29): at 1'-4 5/8" the RO missed the 16" module bay's
    # center by 3/8", enough to break two studs and pull in a header/jacks a 14" RO
    # should never need (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    Window(uid="CGX301AAAA", tag="WIN-G-N1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(1, 5)), sill_height=ft(3, 6)),
    # WIN-G-N1's mirror at the south end of the same wall (2026-07-30): the west wall is
    # 24'-0" node-to-node and N1's centre sits 2'-0" off the north corner, so 22'-0" off
    # it — 2'-0" off the south corner — is the exact mirror. It is also a bay centre
    # (22'-0" = 8" + 16"x16 on W-G-W's grid, which lays out from N-G-NW), so the pair is
    # symmetric AND both keep the unbroken stud bay a 14" RO exists to get. Same 3'-6"
    # sill: above a workbench, and the one head line this wall has.
    Window(uid="CGX302AAAA", tag="WIN-G-S1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(21, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    Room(uid="CGR401AAAA", tag="RM-GARAGE", seed=pt(ft(12), ft(60)),
         occupancy=Occupancy.GARAGE, conditioned=False,
         floor_finish="sealed-concrete"),
]

# Gable roof, ridge E-W (rotated 90° vs the house), 16" overhangs. The gable ends are the
# E/W walls; they stay flat 8' walls rather than `top=ToRoof` because a raked wall top is a
# straight line between its two endpoints, so a gable wall must be split at the ridge — and
# the 16' overhead door is centered exactly on the ridge, so W-G-E cannot be split. Both
# gable triangles (and the raised-heel band on the eave walls) are instead closed by the
# wall→roof closure in resolve/roof_edge.py, which carries each wall's zip-r/rainscreen/
# cladding skin up to the roof underside and splits at the ridge itself.
# Eave + rake trim is two-layer: a 2x6 wood sub-fascia nailed to the truss tails and barge
# rafters (the structural nailer), lapped by a 5/4 cellular-PVC fascia (the weather face,
# which never rots at a drip edge). A vented PVC soffit closes the overhang underside and
# feeds the eave-to-ridge vent channel. Elevations are derived from the resolved roof plane,
# so the raised-heel lift carries the trim with it.
# The SOUTH eave gets a 5" aluminum gutter: that slope faces the 4' breezeway gap and the
# house wall across it, so its run-off is the only one that lands on somewhere people walk
# — and it now also catches what sheds off the breezeway roof tucked under this eave.
# The north eave sheds onto open ground and stays free-draining. The channel is declared
# here rather than authored in params/ for the same reason the fascia is — the raised-heel
# truss lifts the deck plane in the envelope stage, and an absolute elevation would drift off
# the eave it drains. Its top sits 1/2" below the plane so its back closes the fascia face
# and its bottom lands on the sub-fascia's underside.
_GARAGE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="pvc-cellular", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
    gutter=EaveGutter(material="aluminum", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("south",),
                      slope="1/16 in/ft to the east downspout",
                      downspout_ref="TR-G-LEADER-E"),
)

# The leader the south gutter has always sloped to. It was named in the slope note and never
# authored, so the garage gutter drained to nothing — the same gap the house eaves had.
#
# 3" round, not the house's 4": this slope sheds about 290 sq ft (half of 24'x24' plus the
# overhang) against each house eave's 648, and a 3" leader clears roughly 425 sq ft at the
# 8 in/hr design intensity (params/roof_trim.py works the number).
#
# Its position and top are read off the *resolved* eave rather than derived here, which the
# EaveGutter above deliberately is not: a raised-heel truss lifts the deck plane during the
# envelope stage. test_drainage_elements.py holds the two together, so a change to the roof
# that moves the trough fails there instead of leaving a leader hanging beside it.
_GARAGE_LEADER = Downspout(
    uid="CGDS01AAAA", tag="TR-G-LEADER-E",
    position=pt(ft(25), ft(39, 4.5)),   # east end of the trough, on its centreline
    top_elevation=ft(10),               # inside the trough floor
    bottom_elevation=ft(1),             # splash block, a foot above the apron
    diameter=inch(3), material="aluminum", gutter_ref="RF-GARAGE",
)

ROOFS = [
    Roof(uid="CGRF01AAAA", tag="RF-GARAGE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-G-S", "W-G-N"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="x",
         eave_trim=_GARAGE_EAVE_TRIM),
]

# Snow retention on the south slope. The garage roof sheds toward the breezeway, whose
# polycarbonate canopy (GL-BW-ROOF, x 2'-6"..6'-6", top at 7'-5 3/8") sits 3.0' below this
# eave and squarely in the discharge band — see structural.sliding_snow. A 4:12 standing-seam
# slope is about the most willing shedding surface there is, and 4' x 8' multiwall
# polycarbonate is about the least willing receiving one.
#
# S-5! ColorGard: a continuous 1"x1" aluminum crossbar carried on seam clamps, so the take-off
# bills the clamps under it automatically (StructuralHardware.requires_role). The row runs
# x 1'-4"..8'-0" — the canopy's width plus a full bay of margin at each end, because snow
# releases at an angle and the canopy edge is not the edge of the problem. Row count and
# spacing at Pg = 50 psf are the manufacturer's calculation, not this model's: the check
# screens for retention being *authored*, not for it being sufficient.
#
# Placed at y = 40'-0", 4" up-slope of the eave. The eave is at y = 39'-8" — the wall line at
# y = 41'-0" less the 1'-4" overhang — so 4" of run on the 4:12 plane lifts the bar 1 3/8"
# above the 10'-5 5/8" eave, i.e. z = 10'-7". That is deliberately close to the eave: snow
# retention holds the pack at the bottom of the slope, where the load it resists lives.
# Written out rather than generated: the editable-plan dialect allows no comprehensions, and
# six clamps at 1'-4" o.c. read fine as six lines.
_SNOW_GUARD_Y = ft(40)
_SNOW_GUARD_Z = ft(10, 7)
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
    # A garage gets a *heat* detector, not a smoke alarm: exhaust, dust and a space that runs
    # to outdoor temperature would nuisance-trip a smoke head, which is why R315 asks for CO
    # coverage adjacent to the garage rather than a smoke alarm inside it. This is the
    # rate-of-rise/fixed-temperature head, at the room seed like every other Alarm (the
    # element carries no position of its own).
    #
    # On CKT-LT-BACKUP because R314.4 wants an unswitched circuit and the Shelly backup
    # subsystem is the only thing here that survives an outage. CKT-RC-GARAGE is GFCI, which
    # is wrong for a life-safety device, and there is no spare 1-pole.
    Alarm(uid="CGA701AAAA", tag="AL-G-HEAT", kind=AlarmKind.HEAT, room="RM-GARAGE",
          circuit="CKT-LT-BACKUP"),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ROOFS, _GARAGE_LEADER,
            *SNOW_GUARDS, *ALARMS]

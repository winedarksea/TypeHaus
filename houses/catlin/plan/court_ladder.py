# haus: editable
from typehaus import Furniture, Location, Mount, MountKind, WallAttachment
from typehaus.model import deg, inch

# The sunken garden's way out for D-B-SUNKEN (owner, 2026-11-27): a fixed ladder on W-SG-E1's
# court face at the porch's south-east corner. Court floor to porch plank is 110 3/8", over
# R310.3.2.1's 44", so a permanently affixed ladder is the route up. The user climbs facing
# the wall and side-steps NORTH onto FS-SG-PORCH through RL-SG-PORCH-GATE (a self-closing leaf
# that swings onto the porch, so a push from the ladder opens it with no tool or key), then
# crosses the plank and E1's top to ST-SG-PORCH's head.
# Centre y = -10'-5" is 7" north of W-SG-E1's south node (y -11'-0"), which puts the north rail's
# outer edge 0.46" south of the plank edge (-9'-6"): no plank notch, no rail through the deck.
# The body hangs on the finish face. Oracle: notes/court_escape_ladder.md.
COURT_LADDER = [
    Furniture(uid="HDAN6KPMYC", tag="LAD-SG-ESCAPE", type_ref="FT-COURT-LADDER-WLA6SS",
              location=Location(attachment=WallAttachment(
                  wall_ref="W-SG-E1", face="left", distance_from_start=inch(7),
                  rotation_offset=deg(180))),
              mount=Mount(kind=MountKind.WALL, elevation=inch(0))),
]

# haus: editable
from typehaus import Furniture, Mount, MountKind, SuspensionAnchor
from typehaus.model import ft, inch, pt

# The court's hanging daybed, under the porch outside WIN-B-SAUNA, centred in the west bay
# between W-SG-W1 and D-B-PATIO (owner, 2026-10-13: twin, four ropes, 500 lb). Long axis
# east-west.
#
# Four ropes, four anchors at the type's hang_points (76 x 36 in). They land exactly on
# FS-SG-PORCH's lines 003 and 006, which build up to three plies of 2x12 KDAT
# (resolve/suspension_anchors.py), graded wet. Not 48" apart on 003/007: a line moved off
# its station puts its hanger 2" from a ledger Titen HD (CN-SG-LDG*), behind its flange.
# A rope carries half the rated load: one occupant sitting on a long edge puts the whole
# 500 lb on one line. The saddle bolts sit
# 2 1/2" below the line's top, not at mid-depth: the west ropes are 32" off the ledger, inside
# NDS 3.4.3.3's 5d, and only the depth above a hung bolt counts there.
# notes/court_daybed_anchor.md works the load path by hand. Delete this file and its
# manifest line and the porch is as authored.
COURT_DAYBED = [
    Furniture(uid="47A9FPW1T4", tag="FURN-SG-DAYBED", type_ref="FURN-HANGING-DAYBED-TWIN",
              position=pt(ft(15, 5), inch(-59.25)),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(18))),
    SuspensionAnchor(uid="5SCTBXWCA9", tag="HA-SG-DAYBED-SW", carries="FURN-SG-DAYBED",
                     offset=pt(inch(-38), inch(-18)), design_load_lb=250.0,
                     framing_member="3-2x12:kdat", member_grade="southern-pine-no2-2x12-wet",
                     hardware=("fabricated-joist-saddle-58-hdg", "crosby-g-209-shackle-12"),
                     bolt_top_distance=inch(2.5), floor_ref="FS-SG-PORCH",
                     source="owner 2026-10-13: half the 500 lb rating per rope"),
    SuspensionAnchor(uid="H4QAQ08SYP", tag="HA-SG-DAYBED-SE", carries="FURN-SG-DAYBED",
                     offset=pt(inch(38), inch(-18)), design_load_lb=250.0,
                     framing_member="3-2x12:kdat", member_grade="southern-pine-no2-2x12-wet",
                     hardware=("fabricated-joist-saddle-58-hdg", "crosby-g-209-shackle-12"),
                     bolt_top_distance=inch(2.5), floor_ref="FS-SG-PORCH",
                     source="owner 2026-10-13: half the 500 lb rating per rope"),
    SuspensionAnchor(uid="PSAR1GEW7Z", tag="HA-SG-DAYBED-NE", carries="FURN-SG-DAYBED",
                     offset=pt(inch(38), inch(18)), design_load_lb=250.0,
                     framing_member="3-2x12:kdat", member_grade="southern-pine-no2-2x12-wet",
                     hardware=("fabricated-joist-saddle-58-hdg", "crosby-g-209-shackle-12"),
                     bolt_top_distance=inch(2.5), floor_ref="FS-SG-PORCH",
                     source="owner 2026-10-13: half the 500 lb rating per rope"),
    SuspensionAnchor(uid="APBY2MA1CM", tag="HA-SG-DAYBED-NW", carries="FURN-SG-DAYBED",
                     offset=pt(inch(-38), inch(18)), design_load_lb=250.0,
                     framing_member="3-2x12:kdat", member_grade="southern-pine-no2-2x12-wet",
                     hardware=("fabricated-joist-saddle-58-hdg", "crosby-g-209-shackle-12"),
                     bolt_top_distance=inch(2.5), floor_ref="FS-SG-PORCH",
                     source="owner 2026-10-13: half the 500 lb rating per rope"),
]

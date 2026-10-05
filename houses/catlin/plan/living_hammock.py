# haus: editable
from typehaus import Furniture, Mount, MountKind, SuspensionAnchor
from typehaus.model import deg, ft, inch, pt

# The living-room hammock chair, centred on the south wall where FURN-M-MEDIA stood
# (retired 2026-10-05: no TV in this room). Its back is to the wall (rotation 180).
#
# The hang point is y = 4'-0", 41.4" off the south finish face (y = 6 5/8") against the
# chair's 35.5", and exactly on FS-S-EAST's joist line 003. The anchor upgrades that line
# to a 2-ply LVL (resolve/suspension_anchors.py); nothing in params/second_deck.py
# changes. Delete this file and its manifest line and the floor is as authored.
# notes/hanging_seat_anchor.md works the load path by hand.
LIVING_HAMMOCK = [
    Furniture(uid="8HVN2582Y0", tag="FURN-M-HAMMOCK", type_ref="FURN-HAMMOCK-CHAIR-MEDIUM",
              room="RM-M-LIVING",
              position=pt(ft(26, 10), ft(4)), rotation=deg(180),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(12))),
    SuspensionAnchor(uid="D1T1X3T0TZ", tag="HA-M-HAMMOCK", carries="FURN-M-HAMMOCK",
                     design_load_lb=360.0,
                     framing_member="2-1.75x11.875 LVL", member_grade="microllam-lvl-2.0e",
                     hardware=("fabricated-joist-saddle-58", "crosby-3-s-5-swivel"),
                     source="owner 2026-10-05: two occupants, 360 lb rated"),
]

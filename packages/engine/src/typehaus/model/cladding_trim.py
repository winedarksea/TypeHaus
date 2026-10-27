"""Cladding edge conditions and material-level trim kit assignments."""

from enum import Enum


class TrimCondition(str, Enum):
    BASE = "base"
    OUTSIDE_CORNER = "outside_corner"
    HORIZONTAL_JOINT = "horizontal_joint"
    EAVE_TOP = "eave_top"
    RAKE_TOP = "rake_top"
    SCREEN_END = "screen_end"
    OPENING_HEAD = "opening_head"
    OPENING_JAMB = "opening_jamb"
    OPENING_SILL = "opening_sill"
    DOOR_HEAD = "door_head"
    DOOR_JAMB = "door_jamb"


# At dissimilar exterior faces one corner covers both panels; it must be
# selected for the pair rather than independently by either panel's kit.
CORNER_PROFILE_BY_KIT_PAIR = {
    frozenset(("WIDE_OUTSIDE_CORNER", "CORRUGATED_OUTSIDE_CORNER")): "WIDE_OUTSIDE_CORNER",
}

WIDE_CORNER_KIT = {TrimCondition.OUTSIDE_CORNER: "WIDE_OUTSIDE_CORNER"}

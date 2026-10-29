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

PBR_KIT = {
    TrimCondition.OUTSIDE_CORNER: "WIDE_OUTSIDE_CORNER",
    TrimCondition.BASE: "PBR_BASE",
    TrimCondition.EAVE_TOP: "6460800",
}
BBD_KIT = {
    TrimCondition.OUTSIDE_CORNER: "WIDE_OUTSIDE_CORNER",
    TrimCondition.BASE: "BBD_BASE",
    TrimCondition.RAKE_TOP: "6411499",
    TrimCondition.HORIZONTAL_JOINT: "BBD_TRANSITION",
    TrimCondition.DOOR_HEAD: "DOOR_HEAD_CUSTOM",
    TrimCondition.DOOR_JAMB: "BBD_PANEL_STARTER",
}
#: Fiber cement has no maker's metal kit: its heads take the generic Z drip flashing.
FIBER_CEMENT_KIT = {
    TrimCondition.OPENING_HEAD: "OPENING_HEAD_DRIP_FLASHING",
    TrimCondition.DOOR_HEAD: "OPENING_HEAD_DRIP_FLASHING",
}
CORRUGATED_KIT = {
    TrimCondition.OUTSIDE_CORNER: "CORRUGATED_OUTSIDE_CORNER",
    TrimCondition.BASE: "CORRUGATED_BASE",
    TrimCondition.EAVE_TOP: "CORRUGATED_SILL_TO_SOFFIT",
    TrimCondition.RAKE_TOP: "corrugated-outside-closure",
    TrimCondition.SCREEN_END: "CORRUGATED_JAMB",
    TrimCondition.DOOR_HEAD: "DOOR_HEAD_CUSTOM",
    TrimCondition.DOOR_JAMB: "CORRUGATED_JAMB",
}

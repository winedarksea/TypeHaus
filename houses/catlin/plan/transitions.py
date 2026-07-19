"""Catlin transition library — documentation overlays never alter resolved geometry."""

from typehaus import Continuity, Transition


AIR_WATER_THERMAL = (
    Continuity(control="air", from_face="sheathing-ext", to_face="sheathing-ext"),
    Continuity(control="water", from_face="wrb-ext", to_face="wrb-ext"),
    Continuity(control="thermal", from_face="ci-ext", to_face="ci-ext"),
)

TRANSITIONS = (
    Transition(uid="CATR001AAAA", tag="TR-CATLIN-EAVE", condition_pattern="wall_roof:*",
               notes="notes/roof_wall_eave_detail.md", overlay="zero-overhang-eave",
               continuity=AIR_WATER_THERMAL),
    Transition(uid="CATR002AAAA", tag="TR-CATLIN-FOUNDATION",
               condition_pattern="wall_foundation:*",
               notes="notes/basement_to_framed_wall_detail.md",
               overlay="basement-framed-wall", continuity=AIR_WATER_THERMAL),
    Transition(uid="CATR003AAAA", tag="TR-CATLIN-RIM-BAND",
               condition_pattern="storey_stack:rim:*", overlay="rim-band-air-seal",
               continuity=AIR_WATER_THERMAL),
    Transition(uid="CATR004AAAA", tag="TR-CATLIN-STACK-SHELF",
               condition_pattern="stack_width_change:*", overlay="stack-width-shelf",
               continuity=AIR_WATER_THERMAL),
    Transition(uid="CATR005AAAA", tag="TR-CATLIN-FRAMED-OPENING",
               condition_pattern="opening_perimeter:CATLIN_EXT_*",
               notes="notes/roof_wall_eave_detail.md", overlay="window-head-jamb-sill",
               continuity=AIR_WATER_THERMAL),
    Transition(uid="CATR006AAAA", tag="TR-CATLIN-CONCRETE-OPENING",
               condition_pattern="opening_perimeter:CATLIN_CONC_*",
               notes="notes/sauna_basement_wall_detail.md", overlay="concrete-opening"),
    Transition(uid="CATR007AAAA", tag="TR-CATLIN-BASEMENT-OPENING",
               condition_pattern="opening_perimeter:CATLIN_BASEMENT_12",
               notes="notes/basement_to_framed_wall_detail.md", overlay="foundation-window"),
    Transition(uid="CATR008AAAA", tag="TR-CATLIN-GARDEN-ARCH",
               condition_pattern="opening_perimeter:SUNKEN_GARDEN_WALL",
               notes="notes/basement_to_framed_wall_detail.md", overlay="concrete-arch"),
    Transition(uid="CATR009AAAA", tag="TR-CATLIN-GARAGE-OPENING",
               condition_pattern="opening_perimeter:GARAGE_WALL_2X6",
               notes="notes/garage_wall_detail_side.md", overlay="garage-opening"),
    Transition(uid="CATR010AAAA", tag="TR-CATLIN-INTERIOR-OPENING",
               condition_pattern="opening_perimeter:INT_*", overlay="interior-opening"),
    Transition(uid="CATR011AAAA", tag="TR-CATLIN-CENTER-OPENING",
               condition_pattern="opening_perimeter:CATLIN_INT_2X6_BRG",
               overlay="bearing-partition-opening"),
    Transition(uid="CATR012AAAA", tag="TR-CATLIN-ASSEMBLY-JOG",
               condition_pattern="assembly_change:*", overlay="assembly-change-jog",
               continuity=AIR_WATER_THERMAL),
)

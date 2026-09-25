# haus: editable
# Catlin assemblies — the ordered ASSEMBLIES list and the construction rules.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    ConstructionRule,
    inch,
)
from library import (
    FOOTING_STONE_20,
    BEAM_LVL,
    BEAM_KDAT,
    POST_KDAT,
    BEAM_GLULAM_TREATED,
    RETAINING_BLOCK_12,
    FROST_WING_XPS_1IN,
    FROST_WING_XPS_2IN,
    INT_2X6_BRG,
    INT_2X6_BRG_RC,
    INT_2X6_BRG_PLUMBING,
    INT_2X6_PLUMBING_BATT,
    INT_2X8_PLUMBING,
    INT_ESS_CLOSET_STEEL,
    INT_ESS_CLOSET_STEEL_6,
    FOUNDATION_WALL_12_INT,
    INT_2X4_PARTITION,
    INT_2X4_RC,
    INT_2X4_STAGGERED_DOUBLE_GWB,
    INT_2X4_STAGGERED_GWB,
    INT_2X6_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
)
from .envelope_masonry import (
    BASEMENT_BRICK_VENEER,
    BASEMENT_FIBER_CEMENT_SCREEN,
    FIREPLACE_BRICK_WYTHE,
)
from .envelope_roofs import CANOPY_ROOF, GARAGE_ROOF, ROOF
from .envelope_walls import EXT_2X6, EXT_2X6_SWINBURNE, GARAGE_WALL_2X6, RAFTER_PLATE
from .footings import (
    COURT_FOOTING_12,
    FOOTING_20,
    FOOTING_EXPOSED_20,
    PIER_BASE_12,
    PIER_CONCRETE_12,
)
from .foundation import BASEMENT_12, BASEMENT_8, DECK_EPS_INT, GARAGE_ICF_6, SLAB_FLOOR
from .interior import (
    INT_2X6_BRG_EXPOSED_PLY,
    SAUNA_2X4,
    SAUNA_2X6,
    SAUNA_LINER_INT_2X6_BRG,
    STAIRWALL_INT_2X6_BRG_TYPEX,
    STAIRWALL_INT_2X6_BRG_UNDERSTAIR,
    STAIRWELL_PARTITION_4H,
)
from .interior_wet import (
    PLANT_EXT_2X6_HUMID,
    PLANT_INT_2X4_HUMID,
    PLANT_INT_2X6_BRG_HUMID,
    TUBDECK_INT_2X4,
    TUBDECK_INT_PLY_CAP,
)
from .members import (
    BEAM_WHITE_PAINT,
    ELM_TIMBER,
    EQUIP_STAND_ALUM,
    POST_WHITE_PAINT,
    POST_WHITE_PAINT_DF,
)
from .site import (
    ENTRY_STEP_TIER,
    GARAGE_STEP_6,
    GARDEN_COURT_SLAB,
    GARDEN_PUTTING_GREEN,
    GARDEN_STOOP,
    SG_VENEER_BEAM_14,
    SUNKEN_GARDEN_COLUMN_12,
    SUNKEN_GARDEN_GRADE_BEAM_12,
    SUNKEN_GARDEN_WALL,
    SUNKEN_GARDEN_WALL_DRAINED,
)
from .site_hardscape import (
    BALCONY_DECK_ALUMINUM,
    DRIVEWAY_FRC_CLASS5,
    ENTRY_SCREEN_SKIRT,
    ENTRY_SCREEN_WALL,
    GARAGE_SLAB_ON_GRADE,
    HP_PAD_ON_GRADE,
    PORCH_DECK_COMPOSITE,
    RAILING_DARK_METAL,
    RETAINING_BLOCK_12_WASHED,
    SIDEWALK_FRC_CLASS5,
)
from .walkout import (
    GARDEN_CURB_6,
    GARDEN_FRAMED_2X6,
    SAUNA_LINER_ON_GARDEN_CURB,
    SAUNA_LINER_ON_GARDEN_FRAMED,
)


# --- construction rules: pre-resolve returns at mixed-assembly junctions (#45) ----------
# Typed declarations of the physical returns the junction solver leaves for framing/takeoff
# (documented via a Transition overlay, never drawn; none mutate construction geometry):
# a PT sill where framed walls land on concrete, the sauna liner wrapping the center wall,
# foundation foam turning the corner, the masonry guard's corner return.
#
# ``wall:framed_on_concrete`` means what it says and not "on a concrete wall": it also
# finds a framed wall standing on a concrete *slab*, which is every basement partition in
# this house and is the same IRC R317.1 detail — treated plate, sill gasket, capillary
# break. Matching only wall-on-wall would leave the sauna, ESS-closet and bathroom
# partitions ordering no treated plate at all.
CONSTRUCTION_RULES = [
    ConstructionRule(
        tag="CR-CONC-TO-FRAMED-SILL",
        applies_to="wall:framed_on_concrete",
        kind="bearing_plate",
        dimension=inch(1.5),
        takeoff_category="pt-sill-plate",
    ),
    ConstructionRule(
        tag="CR-SAUNA-LINER-RETURN",
        applies_to="wall:sauna_liner_return",
        kind="blocking",
        dimension=inch(3.5),
        takeoff_category="sauna-liner-return",
    ),
    ConstructionRule(
        tag="CR-FOUNDATION-FOAM-RETURN",
        applies_to="wall:foundation_foam_return",
        kind="blocking",
        dimension=inch(24.0),
        takeoff_category="foundation-foam-return",
    ),
    # Named for the porch parapet it was written for, but that was never its only host: it
    # binds every masonry-to-masonry corner, and with the porch parapet retired its eight
    # remaining returns are all on the raised garden's dry-stacked SRW block
    # corners (N-RG-NE/NW/SE/SW). Kept under the old tag on purpose — the returns are stable
    # GlobalIds, and renaming the rule would reissue every one of them.
    ConstructionRule(
        tag="CR-PORCH-MASONRY-RETURN",
        applies_to="wall:porch_masonry_return",
        kind="blocking",
        dimension=inch(7.625),
        takeoff_category="masonry-corner-return",
    ),
    # The plant room's rim bands. FS-S-WEST (the truss half) and FS-ATTIC both run their
    # joists in x, so their ends bear on W-S-W4 and a parallel
    # rim bay sits against W-S-S1 — two
    # direct paths from a floor cavity into the coldest part of an exterior wall, and neither
    # can take a sheet membrane, because there is no continuous plane to lap one onto between
    # joist ends. Closed-cell foam is the only product that is the insulation, the air
    # barrier and the vapour retarder at once in a cavity that shape.
    #
    # It is a ConstructionRule and not just a Transition because a Transition documents and
    # cannot bill (#45): TR-CATLIN-PLANT-RIM draws the detail, this puts the foam in the
    # takeoff. 3" is the specified depth — deep enough to be the retarder (about 0.53 perm)
    # rather than only the air seal.
    #
    # `scope_ref` because which rooms are run wet is a room decision, not a property of the
    # deck or the wall type — the same reasoning CR-LIVING-CEIL-RC's scope carries.
    ConstructionRule(
        tag="CR-PLANT-RIM-FOAM",
        applies_to="wall:rim_cavity_foam",
        kind="blocking",
        dimension=inch(3.0),
        takeoff_category="rim-spray-foam",
        scope_ref="RM-S-PLANT",
    ),
    # Resilient channel under the living room only: bedrooms sit directly over it, and 5/8"
    # gypsum screwed straight to the I-joists would carry footfall as impact noise. Scoped
    # to RM-M-LIVING (a room decision, not FS-S-EAST's, the half above it) — the rest of
    # that ceiling is screwed direct. A full layered-ceiling assembly is deliberately
    # deferred; this just bills the channel (gypsum comes via FS-S-EAST's `ceiling_below`).
    # `construction_returns` is a priced section: the channel itself is PRICED —
    # prices.toml [construction_returns] `resilient-channel`, 522.2 LF at $1.35-2.25/LF
    # installed. The sill plate is the row that is deliberately blank, because a PT sill is
    # lumber [framing] already bought. Channel is not — nothing else in the file buys it.
    ConstructionRule(
        tag="CR-LIVING-CEIL-RC",
        applies_to="floor:ceiling_channel",
        kind="furring",
        dimension=inch(16),
        takeoff_category="resilient-channel",
        scope_ref="RM-M-LIVING",
    ),
]

ASSEMBLIES = [
    EXT_2X6,
    RAFTER_PLATE,
    EXT_2X6_SWINBURNE,
    ROOF,
    BASEMENT_12,
    BASEMENT_8,
    SLAB_FLOOR,
    DECK_EPS_INT,
    FOUNDATION_WALL_12_INT,
    SUNKEN_GARDEN_WALL,
    SUNKEN_GARDEN_GRADE_BEAM_12,
    SUNKEN_GARDEN_WALL_DRAINED,
    SG_VENEER_BEAM_14,
    SUNKEN_GARDEN_COLUMN_12,
    BASEMENT_BRICK_VENEER,
    BASEMENT_FIBER_CEMENT_SCREEN,
    FIREPLACE_BRICK_WYTHE,
    RETAINING_BLOCK_12,
    RETAINING_BLOCK_12_WASHED,
    PORCH_DECK_COMPOSITE,
    BALCONY_DECK_ALUMINUM,
    POST_WHITE_PAINT,
    POST_WHITE_PAINT_DF,
    EQUIP_STAND_ALUM,
    ELM_TIMBER,
    BEAM_LVL,
    BEAM_KDAT,
    BEAM_WHITE_PAINT,
    BEAM_GLULAM_TREATED,
    POST_KDAT,
    PIER_CONCRETE_12,
    RAILING_DARK_METAL,
    GARAGE_ICF_6,
    GARAGE_WALL_2X6,
    GARAGE_SLAB_ON_GRADE,
    HP_PAD_ON_GRADE,
    SIDEWALK_FRC_CLASS5,
    DRIVEWAY_FRC_CLASS5,
    FROST_WING_XPS_1IN,
    FROST_WING_XPS_2IN,
    FOOTING_EXPOSED_20,
    FOOTING_20,
    FOOTING_STONE_20,
    COURT_FOOTING_12,
    PIER_BASE_12,
    GARDEN_COURT_SLAB,
    GARDEN_PUTTING_GREEN,
    GARDEN_STOOP,
    ENTRY_STEP_TIER,
    ENTRY_SCREEN_SKIRT,
    ENTRY_SCREEN_WALL,
    GARAGE_STEP_6,
    GARAGE_ROOF,
    CANOPY_ROOF,
    INT_2X6_BRG,
    INT_2X6_BRG_RC,
    INT_2X6_BRG_PLUMBING,
    INT_2X6_PLUMBING,
    INT_2X6_PLUMBING_BATT,
    INT_2X8_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
    INT_2X4_PARTITION,
    INT_2X4_RC,
    # Kept, referenced by nothing — W-M-LS/CLN/CLN2 retyped to the
    # single-gwb INT_2X4_STAGGERED_GWB below for the material cost, same convention
    # glazed-green-brick is kept under.
    INT_2X4_STAGGERED_DOUBLE_GWB,
    INT_2X4_STAGGERED_GWB,
    INT_ESS_CLOSET_STEEL,
    INT_ESS_CLOSET_STEEL_6,
    SAUNA_2X4,
    SAUNA_2X6,
    SAUNA_LINER_INT_2X6_BRG,
    GARDEN_CURB_6,
    SAUNA_LINER_ON_GARDEN_CURB,
    GARDEN_FRAMED_2X6,
    SAUNA_LINER_ON_GARDEN_FRAMED,
    PLANT_EXT_2X6_HUMID,
    PLANT_INT_2X6_BRG_HUMID,
    PLANT_INT_2X4_HUMID,
    INT_2X6_BRG_EXPOSED_PLY,
    STAIRWALL_INT_2X6_BRG_TYPEX,
    STAIRWALL_INT_2X6_BRG_UNDERSTAIR,
    STAIRWELL_PARTITION_4H,
    TUBDECK_INT_2X4,
    TUBDECK_INT_PLY_CAP,
]

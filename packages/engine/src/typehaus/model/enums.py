"""Closed enums shared across the element model."""

from __future__ import annotations

from enum import Enum, auto


class LayerFunction(Enum):
    """The role a layer plays in an assembly stack (ordered outboard-ish)."""

    STRUCTURE = "structure"
    SHEATHING = "sheathing"
    MEMBRANE = "membrane"
    INSULATION = "insulation"
    AIRGAP = "airgap"
    FURRING = "furring"
    CLADDING = "cladding"
    FINISH = "finish"


class ControlLayer(Enum):
    """Which building control layer(s) a layer provides (→ 11b continuity checks)."""

    AIR = "air"
    WATER = "water"
    VAPOR = "vapor"
    THERMAL = "thermal"


class JunctionPolicy(Enum):
    """How layers meet at a plan junction (→ 11 §Junction policy)."""

    STRUCTURE_BUTTS_FINISH_WRAPS = auto()
    FINISH_BUTTS = auto()


class Occupancy(Enum):
    """Room occupancy — closed enum (feeds R310 egress + future ventilation, #41)."""

    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    LIVING = "living"
    DINING = "dining"
    UTILITY = "utility"
    MECHANICAL = "mechanical"
    GARAGE = "garage"
    STORAGE = "storage"
    HALLWAY = "hallway"
    STAIR = "stair"
    MEDIA = "media"
    OFFICE = "office"
    LAUNDRY = "laundry"
    UNCONDITIONED = "unconditioned"


# Occupancy classes used by the acoustic-adjacency advisory (#50).
QUIET_OCCUPANCIES = frozenset({Occupancy.BEDROOM, Occupancy.OFFICE})
NOISY_OCCUPANCIES = frozenset(
    {Occupancy.BATHROOM, Occupancy.MECHANICAL, Occupancy.MEDIA, Occupancy.LAUNDRY}
)
# Sleeping rooms for R310 egress applicability.
SLEEPING_OCCUPANCIES = frozenset({Occupancy.BEDROOM})


class Service(Enum):
    """Services a fixture/furniture type may require (→ 10 §Element model)."""

    WATER_HOT = "water_hot"
    WATER_COLD = "water_cold"
    DRAIN = "drain"
    GAS = "gas"
    POWER_240 = "power_240"
    VENT = "vent"


class AlarmKind(Enum):
    """Residential life-safety alarm types (R314/R315)."""

    SMOKE = "smoke"
    CO = "co"
    COMBO = "combo"


class StructuralRole(Enum):
    """Authored bearing intent — the derived load path never guesses (#27)."""

    BEARING = "bearing"
    NONBEARING = "nonbearing"
    UNKNOWN = "unknown"


class SliceKind(Enum):
    PLAN = "plan"
    SECTION = "section"
    DETAIL = "detail"
    ELEVATION = "elevation"


class FloorOpeningPurpose(Enum):
    STAIR = "stair"
    CHASE = "chase"
    HATCH = "hatch"


class RadiantSystem(Enum):
    ELECTRIC = "electric"
    HYDRONIC = "hydronic"


class PartitionLayout(Enum):
    """Framing layout for a STRUCTURE layer (#50 acoustic partitions)."""

    SINGLE = "single"
    STAGGERED = "staggered"
    DOUBLE = "double"


class RoofForm(Enum):
    GABLE = "gable"
    SHED = "shed"


class ConditionKind(Enum):
    """Derived boundary-condition kinds keyed for Transition matching (→ 11b)."""

    ASSEMBLY_CHANGE = "assembly_change"
    WALL_FOUNDATION = "wall_foundation"
    WALL_SLAB = "wall_slab"
    WALL_ROOF = "wall_roof"
    OPENING_PERIMETER = "opening_perimeter"
    STOREY_STACK = "storey_stack"
    STACK_WIDTH_CHANGE = "stack_width_change"

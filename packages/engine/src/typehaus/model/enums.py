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
    POWER_120 = "power_120"
    POWER_240 = "power_240"
    SUPPLY_AIR = "supply_air"
    RETURN_AIR = "return_air"
    VENT = "vent"


class DoorOperation(str, Enum):  # noqa: UP042 — StrEnum needs 3.11; the toolchain is 3.9
    """How a door leaf moves — drives the plan symbol, framing pattern and IFC export.

    The ``str`` mixin is deliberate: this value crosses three untyped boundaries (the
    plan/model JSON, the UI catalog, the glTF emitter) where it is compared against and
    serialized as a bare string, so widening ``DoorType.operation`` from ``str`` to this
    enum stays backward compatible in both directions.
    """

    SWING = "swing"
    DOUBLE_SWING = "double_swing"  # French pair: two leaves, each single-swing
    SLIDE = "slide"
    POCKET = "pocket"
    BIFOLD = "bifold"
    OVERHEAD = "overhead"  # sectional garage door, panels running up onto ceiling track


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


class PipeSystem(Enum):
    """Plumbing systems an authored ``PipeRun`` carries (→ MEP Phase 2)."""

    DRAIN = "drain"
    VENT = "vent"
    WATER_HOT = "water_hot"
    WATER_COLD = "water_cold"
    GAS = "gas"
    RADON = "radon"  # passive soil-gas vent, routed alongside the plumbing vent


class DuctSystem(Enum):
    """HVAC air-side system a ``DuctRun``/``Register`` belongs to (→ MEP Phase 3)."""

    SUPPLY = "supply"
    RETURN = "return"


class DuctRouting(Enum):
    """How a duct run is concealed — ``JOIST_BAY`` is checked against framing."""

    JOIST_BAY = "joist_bay"
    SOFFIT = "soffit"
    CHASE = "chase"
    EXPOSED = "exposed"


class EquipmentKind(Enum):
    FURNACE = "furnace"
    AIR_HANDLER = "air_handler"
    WATER_HEATER = "water_heater"
    ERV = "erv"


class DeviceKind(Enum):
    """Electrical symbols-only vocabulary (panel/circuit schedule deferred, decision 1)."""

    RECEPTACLE = "receptacle"
    RECEPTACLE_GFCI = "gfci"
    RECEPTACLE_240 = "receptacle_240"
    SWITCH = "switch"
    LIGHT = "light"
    PANEL = "panel"
    JUNCTION_BOX = "junction_box"  # NEMA 3R weatherproof exterior box (blank/gasketed)


class ConnectorKind(Enum):
    """Modeled connection hardware (→ IfcMechanicalFastener / IfcDiscreteAccessory)."""

    JOIST_HANGER = "joist_hanger"          # e.g. Simpson LUS/HUS face-mount hanger
    HURRICANE_TIE = "hurricane_tie"        # e.g. Simpson H2.5A rafter/joist-to-plate tie
    KNEEBRACE = "kneebrace"                # e.g. Simpson APVKB angled knee brace
    POST_BASE = "post_base"                # standoff post base (e.g. Simpson ABU/CBSQ)
    STANDING_SEAM_CLAMP = "standing_seam_clamp"  # S-5!-style seam clamp on the siding


class RailingKind(Enum):
    """Guard-rail construction the resolver frames into posts/rails."""

    METAL_FASCIA_MOUNT = "metal_fascia_mount"  # aluminum guard, fascia-mounted brackets
    METAL_SURFACE_MOUNT = "metal_surface_mount"  # aluminum guard, deck-surface base plates
    MASONRY = "masonry"                          # solid masonry parapet guard


class TrimKind(Enum):
    """Envelope edge trim/roofing accessory kinds along a deck or roof edge."""

    FASCIA = "fascia"                    # PVC/wood fascia board
    SOFFIT = "soffit"                    # panel closing the underside of an overhang
    GUTTER = "gutter"                    # hung gutter channel
    DRIP_FLASHING = "drip_flashing"      # front-edge drip flashing into the gutter
    WRB_COUNTERFLASHING = "wrb_counterflashing"  # rear flashing tucked into the house WRB


class UtilityKind(Enum):
    """Site utility service kinds (→ Permit-ready plan set Phase 4)."""

    WATER = "water"
    SEWER = "sewer"
    GAS = "gas"
    POWER = "power"


class ConditionKind(Enum):
    """Derived boundary-condition kinds keyed for Transition matching (→ 11b)."""

    ASSEMBLY_CHANGE = "assembly_change"
    WALL_FOUNDATION = "wall_foundation"
    WALL_SLAB = "wall_slab"
    WALL_ROOF = "wall_roof"
    OPENING_PERIMETER = "opening_perimeter"
    STOREY_STACK = "storey_stack"
    STACK_WIDTH_CHANGE = "stack_width_change"
    ROOF_RIDGE = "roof_ridge"

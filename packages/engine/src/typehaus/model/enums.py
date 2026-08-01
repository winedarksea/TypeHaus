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


class WindowOperation(str, Enum):  # noqa: UP042 — StrEnum needs 3.11; the toolchain is 3.9
    """How a window sash moves — drives the plan symbol, the schedule and the IFC export.

    The ``str`` mixin is deliberate, for the same reason ``DoorOperation`` carries one: the
    value crosses the plan/model JSON, the UI catalog and the drawing emitters as a bare
    string, so widening ``WindowType.operation`` from ``str`` to this enum is backward
    compatible in both directions.

    ``FIXED`` is a picture window — no sash, no hardware, and no ventilation or egress
    credit — which is why it must be a distinct type from an operable unit of the same size
    rather than a trim note on one.

    ``TILT_TURN`` is the European dual-axis unit: one sash on hardware that swings it
    bottom-hung for trickle ventilation or side-hung for a full door-like leaf. The second
    mode is what separates it from ``AWNING``, which is bottom-hung only — a tilt-turn opens
    the *entire* rough opening, so it carries full ventilation and egress credit.
    """

    FIXED = "fixed"
    CASEMENT = "casement"
    DOUBLE_HUNG = "double_hung"
    SLIDER = "slider"
    AWNING = "awning"
    TILT_TURN = "tilt_turn"


class AlarmKind(Enum):
    """Residential life-safety alarm types (R314/R315).

    ``HEAT`` is a rate-of-rise/fixed-temperature detector, not a smoke alarm: it is what a
    garage gets, where exhaust, dust and cold would nuisance-trip a smoke head. It is a kind
    of ``Alarm`` rather than a ``DeviceKind`` because a detector is life-safety equipment
    keyed to a room, and ``DeviceKind``'s docstring argues for keeping that enum flat and
    differentiating by ``type_ref``. R314's bedroom rule filters on (SMOKE, COMBO), so a HEAT
    detector is correctly invisible to it.
    """

    SMOKE = "smoke"
    CO = "co"
    COMBO = "combo"
    HEAT = "heat"


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
    # The stale-air side of a balanced HRV/ERV pair (and any dedicated exhaust pull, e.g.
    # a shower takeoff). No separate HRV member: an HRV/ERV is modeled as its SUPPLY and
    # EXHAUST sides.
    EXHAUST = "exhaust"


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
    HEAT_PUMP = "heat_pump"  # minisplit outdoor condenser
    # The indoor half of a split system, split in two because they are different products a
    # plan reader places differently: a wall-mount head hangs high on a wall and blows into
    # the room it is in, a concealed ducted air handler sits above a ceiling and feeds a
    # duct system. Both pair back to a HEAT_PUMP condenser via ``Equipment.outdoor_ref``.
    INDOOR_HEAD = "indoor_head"
    DUCTED_AIR_HANDLER = "ducted_air_handler"
    # Hard-wired electric sauna heater. Equipment rather than Appliance because it takes no
    # receptacle — the circuit lands in a junction box at the heater — and ``Equipment`` is
    # the placeable that carries a ``circuit`` reference for exactly that case.
    SAUNA_HEATER = "sauna_heater"
    # Fixed electric resistance space heating that is not a floor zone: a wall-mount
    # fireplace, a garage unit heater, a baseboard run. One member rather than several
    # because the product is named by the ``type_ref`` (the same rule ``DeviceKind`` uses
    # for EV receptacles), and because every ``Equipment`` kind emits as an
    # IfcBuildingElementProxy regardless. The service-load takeoff reads this kind to put
    # the load under NEC 220.82(C) instead of the fixed-appliance bucket in (B)(3).
    SPACE_HEATER = "space_heater"


class DeviceKind(Enum):
    """Electrical device vocabulary — symbols plus the service-entrance kinds.

    EV chargers are ``RECEPTACLE_240`` distinguished by their device *type* (NEMA
    configuration lives on ``ElectricalDeviceType.nema``), not a kind of their own.
    """

    RECEPTACLE = "receptacle"
    RECEPTACLE_GFCI = "gfci"
    RECEPTACLE_240 = "receptacle_240"
    SWITCH = "switch"
    LIGHT = "light"
    PANEL = "panel"
    JUNCTION_BOX = "junction_box"  # NEMA 3R weatherproof exterior box (blank/gasketed)
    METER = "meter"  # utility meter, separate from the panel (200A service)
    DISCONNECT = "disconnect"  # equipment disconnect (heat pump, hot tub, WH)


class LuminaireForm(Enum):
    """The physical form of a light fixture — drives its plan glyph and its schedule row.

    Deliberately *not* ten new ``DeviceKind`` members. E-sheet markers key off
    ``DeviceKind.value`` and three mirrored IFC/diff maps do the same, so ten more kinds
    would ripple through all of them for no IFC gain: every form below exports as one
    ``IfcLightFixture``. This is the EV-charger precedent (``DeviceKind`` docstring) —
    the kind stays flat, the product *type* differentiates.

    ``STRIP`` is the one form with no point instance: it is authored as a ``LightRun``
    polyline and priced per lineal foot off ``LuminaireType.watts_per_ft``.
    """

    RECESSED_CAN = "recessed_can"
    PANEL = "panel"
    STRIP = "strip"
    SCONCE = "sconce"
    PENDANT = "pendant"
    CHANDELIER = "chandelier"
    LINEAR_TUBE = "linear_tube"
    WALL_LAMP = "wall_lamp"
    MIRROR_LIGHT = "mirror_light"
    CEILING_FAN_LIGHT = "ceiling_fan_light"


class ConnectorKind(Enum):
    """Modeled connection hardware (→ IfcMechanicalFastener / IfcDiscreteAccessory)."""

    JOIST_HANGER = "joist_hanger"          # e.g. Simpson LUS/HUS face-mount hanger
    HURRICANE_TIE = "hurricane_tie"        # e.g. Simpson H2.5A rafter/joist-to-plate tie
    KNEEBRACE = "kneebrace"                # e.g. Simpson APVKB angled knee brace
    POST_BASE = "post_base"                # standoff post base (e.g. Simpson ABU/CBSQ)
    HOLD_DOWN = "hold_down"                # beam-to-post uplift strap (e.g. Simpson KBS/LSTA)
    STANDING_SEAM_CLAMP = "standing_seam_clamp"  # S-5!-style seam clamp on the siding
    SNOW_GUARD = "snow_guard"              # e.g. S-5! ColorGard snow-retention rail


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
    DOWNSPOUT = "downspout"              # vertical leader carrying a gutter down to grade
    DRIP_FLASHING = "drip_flashing"      # front-edge drip flashing into the gutter
    WRB_COUNTERFLASHING = "wrb_counterflashing"  # rear flashing tucked into the house WRB
    # Multiwall-glazing extrusions. A panel edge is never left open: an open flute end wicks
    # water and grows algae, so every edge is capped by one of these.
    GLAZING_CHANNEL = "glazing_channel"  # U / H / F extrusion capping a panel edge
    GLAZING_BAR = "glazing_bar"          # capped bar joining or closing panel edges
    # A rainscreen cavity must stay open at its base to drain and to draw ventilation air,
    # which makes it an insect route straight up behind the cladding unless the opening is
    # screened. The closure is a lineal run, not a piece of hardware, so it lives here with
    # the other edge runs rather than in ``ConnectorKind``.
    BUG_SCREEN = "bug_screen"            # vented insect closure at a rainscreen cavity base


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

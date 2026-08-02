"""Library types: openings, placeables, and structural product catalogs."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import HausModel
from typehaus.model.enums import DoorOperation, LuminaireForm, Service, WindowOperation
from typehaus.model.placeables import (ClearanceZone, Footprint2D, ModelRepresentation,
                                       Mount, PlacementStrategy, PlanRepresentation, ServicePort)
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, UFactor


class DoorType(HausModel):
    """A door product type. Drives schedules, energy checks, and opening appearance."""

    tag: str
    width: Length
    height: Length
    u_factor: UFactor | None = None
    operation: DoorOperation = DoorOperation.SWING
    exterior: bool = False
    # A glazed leaf is transparent in 3D exports and the live viewer. Kept separate from
    # operation because a swinging, sliding, or French door can each be glazed.
    glazed: bool = False
    # No applied casing — drywall return jamb: the gwb wraps into the opening and dies
    # against a concealed jamb, so 3D exports and the live viewer draw no frame boxes.
    trimless: bool = False
    # Type-level engineered-header default (e.g. '2-ply 14" LVL') for openings wide enough
    # that the solver's dimensional-lumber header tables don't apply; a Door instance's
    # own header_spec wins over this.
    header_spec: str | None = None
    # --- R302.5.1: the door between a garage and the dwelling ---------------------------
    # The code offers three ways to comply and names two of them by construction: a 1-3/8"
    # solid-wood or solid/honeycomb-steel door, or a 20-minute fire-rated assembly. Both
    # are properties of the product, so both live on the type.
    #
    # ``self_closing`` is separate because it is a property of the *installation* that the
    # product must support (and Minnesota amends R302.5.1 to require it). None/False means
    # "not stated", which the check reports as UNKNOWN rather than as a deficiency — an
    # interior passage door that never touches a garage has no business claiming a rating.
    core: Literal["solid", "hollow"] | None = None
    fire_rating_minutes: int | None = None
    self_closing: bool = False
    # Safety glazing in the leaf — R308.4.1 requires it of every glazed door, with no
    # location test to derive. Meaningful only where ``glazed`` is true.
    tempered: bool = False
    source: str | None = None


class WindowType(HausModel):
    """A window product type. Carries SHGC and VT (#41) for the M5 load estimator."""

    tag: str
    width: Length
    height: Length
    u_factor: UFactor | None = None
    shgc: float | None = None  # solar heat gain coefficient
    vt: float | None = None  # visible transmittance
    # A closed vocabulary, like a door's: the operation picks the plan symbol and is what
    # separates a picture unit from an operable one of identical size on the schedule.
    operation: WindowOperation = WindowOperation.FIXED
    # Safety (tempered or laminated) glazing. R308.4 lists the *locations* that require it —
    # in a door, beside a door, near a tub, near a stair, low and large — and the check
    # derives every one of those from geometry. What geometry cannot tell you is whether the
    # unit that landed there was ordered tempered, which is exactly what this states.
    tempered: bool = False
    # R312.2 fall protection: an opening control device, a fall-prevention device, or a
    # guard at the window. "none" is the honest default — most windows have nothing, and
    # most windows do not need anything.
    fall_protection: Literal["none", "limiter", "guard", "screen_rated"] = "none"
    source: str | None = None


class MeshRef(HausModel):
    """Reference to a .glb sidecar under the house dir (written by `haus import`, #49)."""

    path: str


class FurnitureType(HausModel):
    """An IKEA-scale design-reference type (#49). Footprint/height derived from mesh."""

    tag: str
    name: str
    footprint: tuple[Length, Length]  # (width, depth)
    height: Length
    storage: bool = False
    # NEC 210.52(A)(2)(1) breaks wall space at "fixed cabinets that do not have countertops
    # or similar work surfaces", so a run of tall pantry is not somewhere a receptacle is
    # required and a run of base cabinet is. ``None`` means the question does not arise: the
    # type is not fixed cabinetry standing on the floor, and a bookcase you can pull away
    # from the wall breaks nothing whatever its top is made of.
    work_surface: bool | None = None
    clearance: tuple[Length, Length, Length, Length] | None = None  # front/back/L/R
    mesh: MeshRef | None = None
    source: str | None = None
    # Project-local imports retain their source facts separately from the read-only library
    # source label, so IFC handoff can identify a visual asset without parsing a JSON sidecar.
    import_provenance: dict[str, object] | None = None
    placement: PlacementStrategy = PlacementStrategy.FREE_PLACED
    footprint_shape: Footprint2D | None = None
    clearances: tuple[ClearanceZone, ...] = ()
    ports: tuple[ServicePort, ...] = ()
    plan_representation: PlanRepresentation | None = None
    model_representation: ModelRepresentation | None = None
    mount: Mount = Mount()
    # Names a generated glyph + massing from ``model/placeable_symbols`` (see SYMBOL_NAMES).
    # An imported ``plan_representation``/``model_representation`` still wins over it.
    plan_symbol: str | None = None


class RailingType(HausModel):
    """A railing product identity, separate from its resolved guard geometry."""

    tag: str
    name: str
    mesh: MeshRef | None = None
    source: str | None = None


class FixtureType(HausModel):
    """A plumbing/equipment fixture type — needs services, has clearances (M3)."""

    tag: str
    name: str
    footprint: tuple[Length, Length]
    height: Length
    needs: frozenset[Service] = frozenset()
    clearance: tuple[Length, Length, Length, Length] | None = None
    source: str | None = None
    import_provenance: dict[str, object] | None = None
    placement: PlacementStrategy = PlacementStrategy.FREE_PLACED
    footprint_shape: Footprint2D | None = None
    clearances: tuple[ClearanceZone, ...] = ()
    ports: tuple[ServicePort, ...] = ()
    plan_representation: PlanRepresentation | None = None
    model_representation: ModelRepresentation | None = None
    mount: Mount = Mount()
    plan_symbol: str | None = None


class ApplianceType(FurnitureType):
    """A product requiring services but not a plumbing fixture (for example a washer)."""

    needs: frozenset[Service] = frozenset()
    # A listed condensing (ductless) appliance — the heat-pump dryer that throws its moisture
    # down a condensate line instead of out a wall. M1502.1 exempts exactly these from the
    # whole of M1502, and there is no other way to tell one from a vented dryer: both are
    # 28x40 boxes named "dryer" with a 240V port. False is the safe default — an unstated
    # dryer is a vented dryer and owes the code a duct.
    ductless: bool = False


class EquipmentType(FurnitureType):
    needs: frozenset[Service] = frozenset()
    # Rated heating output (Btu/h at the AHRI 47 °F point), for heat-producing equipment.
    heating_capacity_btuh: float | None = None
    # Heating output at the *site* heating design temperature. The authored number IS the
    # derate — no performance-curve modeling; leave None when the datasheet doesn't say.
    heating_capacity_at_design_btuh: float | None = None
    # Rated sensible cooling output (Btu/h at the AHRI 95 °F point). Advisory only: the
    # block load's cooling side is a UA + solar sum, not a Manual J latent split.
    cooling_capacity_btuh: float | None = None
    # Ventilation equipment (ERV/HRV) only: the continuous balanced airflow it moves, and
    # the datasheet sensible recovery effectiveness (0..1) at that flow. Both feed the
    # ventilation term of the block load — never defaulted, because a guessed SRE moves
    # the load by thousands of Btu/h.
    ventilation_cfm: float | None = None
    sensible_recovery_effectiveness: float | None = None
    # Lowest outdoor temperature the unit is rated to operate at (cold-climate heat pumps).
    # Compared against the site heating design temperature by the HVAC schedule.
    min_operating_temp_f: float | None = None
    # True for resistance heat that *supplements* a zone rather than carrying it: an electric
    # fireplace, a radiant mat. It never claims a zone of its own however it is rated — but
    # its output does count toward the zone that contains its room, because at design temp
    # it is real heat the heat pump doesn't have to make.
    supplemental_heat: bool = False


class RegisterType(FurnitureType):
    needs: frozenset[Service] = frozenset({Service.SUPPLY_AIR})
    # A ventilation terminal (the ERV's fresh-air/stale-air grilles) rather than a
    # conditioned-air register. Same product family, different sizing basis — a ventilation
    # terminal is sized for the whole-house rate, a supply register for a heating CFM — and
    # the plan set/IFC handoff has to tell a reader which one it is looking at.
    ventilation_terminal: bool = False


class ElectricalDeviceType(FurnitureType):
    needs: frozenset[Service] = frozenset({Service.POWER_120})
    # NEMA configuration (e.g. "5-20R", "14-50R") — typed data the panel schedule reads,
    # instead of parsing it out of the display name. Voltage stays derivable from ports.
    nema: str | None = None
    # Connected load in volt-amps; summed per circuit by the panel-schedule takeoff.
    load_va: float | None = None
    # Breaker spaces in the enclosure (panel kinds only) — what electrical.panel_spaces
    # reconciles the circuit slots against.
    spaces: int | None = None
    # How a SWITCH device controls what it feeds: "dimmer" | "timer" | "smart" | None
    # (a plain toggle). Read by the lighting-controls check and printed in the E-602
    # control schedule; a product attribute, not a kind, for the same reason NEMA is.
    control: str | None = None


class LuminaireType(ElectricalDeviceType):
    """A light-fixture product type: form, photometrics, and the ratings a schedule prints.

    Lives in ``Library.electrical_device_types`` alongside its parent — the same pattern
    ``ApplianceType``/``EquipmentType`` use against ``FurnitureType``. Pydantic keeps an
    already-constructed subclass instance intact in a parent-typed tuple field, so the
    extra fields survive the round trip; ``tests/test_lighting_schema.py`` pins that.

    Photometrics are optional throughout: a fixture whose lumens are unknown should say
    so on the schedule rather than carry an invented number.
    """

    form: LuminaireForm
    type_mark: str | None = None  # schedule letter — "A", "B", … unique per house
    lamp: str | None = None  # "LED integrated" | "T8 LED" | "E26" — what gets replaced
    watts: float | None = None
    lumens: float | None = None
    cct_k: int | None = None  # correlated colour temperature, kelvin
    cri: int | None = None  # colour rendering index
    voltage: int = 120  # 120 line voltage, or 24 for a driver-fed LED strip
    dimmable: bool = False
    damp_rated: bool = False  # UL damp: covered porch, bath outside the shower zone
    wet_rated: bool = False  # UL wet: shower/tub zone, open exterior
    # A fixture switched at the fixture itself (a pull chain, a sconce paddle). Exempt
    # from the controls check — there is no wall switch to name.
    integral_switch: bool = False
    # Linear forms only: the load per lineal foot a ``LightRun`` multiplies by its length
    # to get connected VA and to size its 24V supply.
    watts_per_ft: float | None = None


for _name, _obj in (
    ("DoorType", DoorType),
    ("WindowType", WindowType),
    ("FurnitureType", FurnitureType),
    ("RailingType", RailingType),
    ("FixtureType", FixtureType),
    ("ApplianceType", ApplianceType),
    ("EquipmentType", EquipmentType),
    ("RegisterType", RegisterType),
    ("ElectricalDeviceType", ElectricalDeviceType),
    ("LuminaireType", LuminaireType),
    ("MeshRef", MeshRef),
):
    register_constructor(_name, _obj)

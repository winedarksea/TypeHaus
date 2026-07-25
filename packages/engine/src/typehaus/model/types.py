"""Library types: DoorType, WindowType, FurnitureType, FixtureType (→ 10 §Element model)."""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.enums import DoorOperation, Service
from typehaus.model.placeables import (ClearanceZone, Footprint2D, ModelRepresentation,
                                       Mount, PlacementStrategy, PlanRepresentation, ServicePort)
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, UFactor


class DoorType(HausModel):
    """A door product type. Drives schedules and energy checks."""

    tag: str
    width: Length
    height: Length
    u_factor: UFactor | None = None
    operation: DoorOperation = DoorOperation.SWING
    exterior: bool = False
    # Type-level engineered-header default (e.g. '2-ply 14" LVL') for openings wide enough
    # that the solver's dimensional-lumber header tables don't apply; a Door instance's
    # own header_spec wins over this.
    header_spec: str | None = None
    source: str | None = None


class WindowType(HausModel):
    """A window product type. Carries SHGC and VT (#41) for the M5 load estimator."""

    tag: str
    width: Length
    height: Length
    u_factor: UFactor | None = None
    shgc: float | None = None  # solar heat gain coefficient
    vt: float | None = None  # visible transmittance
    operation: str = "fixed"  # fixed | casement | double_hung | slider | awning
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


class EquipmentType(FurnitureType):
    needs: frozenset[Service] = frozenset()


class RegisterType(FurnitureType):
    needs: frozenset[Service] = frozenset({Service.SUPPLY_AIR})


class ElectricalDeviceType(FurnitureType):
    needs: frozenset[Service] = frozenset({Service.POWER_120})


for _name, _obj in (
    ("DoorType", DoorType),
    ("WindowType", WindowType),
    ("FurnitureType", FurnitureType),
    ("FixtureType", FixtureType),
    ("ApplianceType", ApplianceType),
    ("EquipmentType", EquipmentType),
    ("RegisterType", RegisterType),
    ("ElectricalDeviceType", ElectricalDeviceType),
    ("MeshRef", MeshRef),
):
    register_constructor(_name, _obj)

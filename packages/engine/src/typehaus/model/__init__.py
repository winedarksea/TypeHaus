"""The element model — the typed heart of the product (→ 10 §Element model).

Importing this package populates the constructor registry (the dialect allowlist) with
every element/library constructor, plus the quantity and reference constructors.
"""

from __future__ import annotations

from typehaus.model.assembly import (
    Assembly,
    AssemblyInterface,
    CavityFill,
    ConstructionRule,
    FramingSpec,
    Layer,
    MasonrySpec,
    Substitution,
)
from typehaus.model.base import Element, HausModel
from typehaus.model.elements import Door, Node, RoughOpening, Wall, Window
from typehaus.model.enums import (
    AlarmKind,
    ConditionKind,
    ConnectorKind,
    ControlLayer,
    DeviceKind,
    DuctRouting,
    DuctSystem,
    EquipmentKind,
    FloorOpeningPurpose,
    JunctionPolicy,
    LayerFunction,
    LuminaireForm,
    Occupancy,
    PartitionLayout,
    PipeSystem,
    RadiantSystem,
    RailingKind,
    RoofForm,
    Service,
    SliceKind,
    StructuralRole,
    TrimKind,
    UtilityKind,
)
from typehaus.model.floors import (
    DeckLayer,
    FinishZone,
    FloorHeat,
    FloorOpening,
    FloorSystem,
    JoistSpec,
    Slab,
    SlabThermalBreak,
    Soffit,
)
from typehaus.model.electrical import Circuit, LoadManagement
from typehaus.model.materials import Material
from typehaus.model.mep import (
    ConduitRun,
    DuctRun,
    LightRun,
    ElectricalDevice,
    Equipment,
    PipeRun,
    Register,
    SleevePenetration,
    Sump,
    VentRun,
)
from typehaus.model.trim import (
    Downspout, EaveGutter, EaveSoffit, EaveTrim, Fascia, FasciaBoard, Flashing,
    GlazingTrim, Gutter,
)
from typehaus.model.plan import Library, PlanModel
from typehaus.model.project import Building, Project, Site, Storey
from typehaus.model.refs import (
    Arch,
    Embed,
    FaceRef,
    FollowRoof,
    LayerSpan,
    OpeningPosition,
    ToRoof,
    centered,
    face,
    from_node,
    in_slab,
    inside_of,
    layers,
    outside_of,
    under_subfloor,
)
from typehaus.model.registry import (
    constructor_names,
    element_kinds,
    register_constructor,
)
from typehaus.model.site import (
    Basemap,
    Contour,
    ImperviousSurface,
    MonthlyNormal,
    SetbackSpec,
    SpotElevation,
    UtilityLine,
    load_basemap_geojson,
)
from typehaus.model.structure import (
    Beam,
    Connector,
    Dowel,
    DrainTile,
    Footing,
    FootingBedding,
    FoundationWall,
    GlazingPanel,
    KneeBrace,
    Pad,
    Post,
    Railing,
    SolarPanel,
)
from typehaus.model.spatial import (
    Annotation,
    Alarm,
    Fixture,
    Furniture,
    Appliance,
    GridAxis,
    Roof,
    Room,
    Stair,
    WallLiningException,
)
from typehaus.model.types import (
    DoorType,
    ApplianceType,
    ElectricalDeviceType,
    EquipmentType,
    FixtureType,
    FurnitureType,
    LuminaireType,
    MeshRef,
    WindowType,
    RegisterType,
    RailingType,
)
from typehaus.model.placeables import (
    ClearancePolicy, ClearanceZone, Footprint2D, Location, ModelRepresentation, Mount,
    MountKind, PlacementStrategy, PlanRepresentation, ServicePort, WallAttachment,
)
from typehaus.model.views import (
    Continuity,
    DetailAnnotation,
    ExaggerationSpec,
    LayerJoin,
    Slice,
    Transition,
)
from typehaus.quantities import (
    Angle,
    Area,
    Length,
    Pitch,
    Point2D,
    RValue,
    Temperature,
    UFactor,
    deg,
    degC,
    degF,
    ft,
    inch,
    m,
    mm,
    pt,
    r_us,
    rad,
    rsi,
    sqft,
    sqm,
    u_us,
)

# Register quantity + reference constructors so the dialect allowlist includes them.
for _name, _obj in (
    ("ft", ft), ("inch", inch), ("mm", mm), ("m", m),
    ("deg", deg), ("rad", rad), ("Pitch", Pitch),
    ("sqft", sqft), ("sqm", sqm),
    ("r_us", r_us), ("rsi", rsi), ("u_us", u_us),
    ("degC", degC), ("degF", degF), ("pt", pt),
    ("face", face), ("outside_of", outside_of), ("inside_of", inside_of),
    ("layers", layers), ("from_node", from_node), ("centered", centered),
    ("in_slab", in_slab), ("under_subfloor", under_subfloor),
    ("ToRoof", ToRoof), ("FollowRoof", FollowRoof), ("Arch", Arch),
    ("Library", Library), ("PlanModel", PlanModel),
    ("Footprint2D", Footprint2D), ("ClearanceZone", ClearanceZone), ("ServicePort", ServicePort),
    ("PlanRepresentation", PlanRepresentation), ("ModelRepresentation", ModelRepresentation),
    ("Location", Location), ("WallAttachment", WallAttachment), ("Mount", Mount),
):
    register_constructor(_name, _obj)

__all__ = [
    "PlanModel", "Library", "Project", "Site", "Building", "Storey",
    "Element", "HausModel",
    "Node", "Wall", "Door", "Window", "RoughOpening",
    "FoundationWall", "Footing", "Pad", "FootingBedding", "DrainTile", "Post", "Beam",
    "Dowel", "Connector", "KneeBrace", "Railing", "Fascia", "Gutter", "Flashing",
    "EaveSoffit", "FasciaBoard", "EaveGutter", "EaveTrim", "GlazingPanel", "GlazingTrim",
    "Downspout",
    "SolarPanel",
    "Assembly", "Layer", "CavityFill", "FramingSpec", "MasonrySpec", "AssemblyInterface",
    "ConstructionRule", "Substitution", "Material",
    "DoorType", "WindowType", "FurnitureType", "FixtureType", "ApplianceType", "EquipmentType",
    "RegisterType", "RailingType", "ElectricalDeviceType", "LuminaireType", "MeshRef",
    "JoistSpec", "DeckLayer", "FloorSystem", "FloorOpening", "Slab", "SlabThermalBreak",
    "Soffit",
    "FloorHeat", "FinishZone",
    "Room", "Stair", "Roof", "GridAxis", "Annotation", "Fixture", "Furniture", "Appliance",
    "Alarm",
    "WallLiningException",
    "Slice", "Transition", "Continuity", "ExaggerationSpec",
    "DetailAnnotation", "LayerJoin",
    "FaceRef", "face", "ToRoof", "FollowRoof", "Arch", "LayerSpan", "OpeningPosition",
    "Embed", "outside_of", "inside_of", "layers", "from_node", "centered",
    "in_slab", "under_subfloor",
    "PipeRun", "SleevePenetration", "DuctRun", "Register", "Equipment", "ElectricalDevice",
    "Circuit", "LoadManagement", "ConduitRun", "LightRun",
    "Sump", "VentRun",
    "MonthlyNormal", "SetbackSpec", "SpotElevation", "ImperviousSurface", "UtilityLine",
    "Contour", "Basemap",
    "load_basemap_geojson",
    "LayerFunction", "ControlLayer", "JunctionPolicy", "Occupancy", "Service", "AlarmKind",
    "StructuralRole", "SliceKind", "FloorOpeningPurpose", "RadiantSystem",
    "PartitionLayout", "RoofForm", "ConditionKind",
    "PipeSystem", "DuctSystem", "DuctRouting", "EquipmentKind", "DeviceKind", "LuminaireForm", "UtilityKind",
    "ConnectorKind", "RailingKind", "TrimKind",
    "PlacementStrategy", "MountKind", "ClearancePolicy", "Footprint2D", "ClearanceZone",
    "ServicePort", "PlanRepresentation", "ModelRepresentation", "Location", "WallAttachment", "Mount",
    "Length", "Area", "Angle", "Pitch", "RValue", "UFactor", "Temperature", "Point2D",
    "ft", "inch", "mm", "m", "deg", "rad", "sqft", "sqm", "r_us", "rsi", "u_us",
    "degC", "degF", "pt",
    "constructor_names", "element_kinds", "register_constructor",
]

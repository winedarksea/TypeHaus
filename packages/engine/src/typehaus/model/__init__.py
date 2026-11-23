"""The element model — the typed heart of the product (→ 10 §Element model).

Importing this package populates the constructor registry (the dialect allowlist) with
every element/library constructor, plus the quantity and reference constructors.
"""

from __future__ import annotations

from typehaus.model.air_handler_installation import AirHandlerInstallation, DrainFittings
from typehaus.model.assembly import (
    Assembly,
    AssemblyInterface,
    CavityFill,
    ConcreteSpec,
    ConstructionRule,
    FiberSpec,
    FramingSpec,
    Layer,
    LayerBound,
    LayerExtent,
    MasonrySpec,
    RainscreenBaseFlashing,
    Substitution,
)
from typehaus.model.backing import WallBacking
from typehaus.model.base import Element, HausModel
from typehaus.model.braced_wall import BracedWallPanel
from typehaus.model.braces import SlatBrace, StrapBrace
from typehaus.model.built_in_bench import BuiltInBenchSpec
from typehaus.model.bypass_door import BypassDoorSpec
from typehaus.model.clear_zones import ClearZone
from typehaus.model.concrete_materials import AsrSpec, CementSpec, ScmFractions
from typehaus.model.curtain_track import CurtainStack, CurtainTrackSpec
from typehaus.model.diaphragm_attachment import (
    CollectorBlocking,
    JointNailing,
    PanelEdgeBlocking,
)
from typehaus.model.door_hardware import DoorHardwareItem, JambFraming
from typehaus.model.door_undercut import DoorUndercut
from typehaus.model.doorway import DoorwayProductSpec, DoorwaySectionPart, DoorwayTreatment
from typehaus.model.drain_column import DrainColumn
from typehaus.model.drywall import DrywallStandard, ShadowGapProfile, TerminationBead
from typehaus.model.ducts import (
    DuctElbowRow,
    DuctInsulationRow,
    DuctPartRow,
    DuctStandard,
    DuctSupportRow,
    PortKit,
    RectElbowRow,
    RoundGaugeRow,
)
from typehaus.model.electrical import (
    BoxRow,
    BoxStandard,
    BoxSupport,
    Circuit,
    LoadManagement,
    PlateRow,
)
from typehaus.model.electrical_labels import LabelStandard
from typehaus.model.elements import Door, Node, RoughOpening, Wall, Window
from typehaus.model.enums import (
    AlarmKind,
    BackupTier,
    ConditionKind,
    ConnectorKind,
    ControlLayer,
    DeviceKind,
    DuctRouting,
    DuctSystem,
    EquipmentKind,
    FloorOpeningPurpose,
    HumidityClass,
    JunctionPolicy,
    LayerDatum,
    LayerFunction,
    LuminaireForm,
    Occupancy,
    PartitionLayout,
    PipeAccessoryKind,
    PipeSystem,
    RacewayMaterial,
    RadiantSystem,
    RailingKind,
    RatingBasis,
    RoofForm,
    Service,
    ShelfProcurement,
    SliceKind,
    StructuralRole,
    TrimKind,
    UtilityKind,
)
from typehaus.model.equipment_hangers import EquipmentHangers
from typehaus.model.excavation import Excavation, SideSlope, SoilFactor
from typehaus.model.exterior_door import (
    ApproachBearing,
    ExteriorDoorCatalogInstallation,
    ExteriorDoorInstallation,
    ExteriorDoorSillDesign,
)
from typehaus.model.flashing import FormedFlashingSection
from typehaus.model.floors import (
    DeckLayer,
    FillerBlock,
    FinishZone,
    FloorHeat,
    FloorOpening,
    FloorOpeningEdgeInterval,
    FloorOpeningLid,
    FloorOpeningPocketClosure,
    FloorSystem,
    JoistReinforcement,
    JoistSpec,
    PlyFastening,
    Slab,
    SlabThermalBreak,
    Soffit,
    SoffitOpening,
    Strongback,
)
from typehaus.model.framing_standards import HeaderStandard
from typehaus.model.furniture_cut import FurnitureCut
from typehaus.model.grounding import (
    BondingConductor,
    GroundingElectrode,
    GroundingStandard,
    ServiceEntrance,
)
from typehaus.model.joist_flange import JoistFlangeAllowance
from typehaus.model.joist_holes import JoistHoleChart
from typehaus.model.landscape import (
    AccentRule,
    GridLayout,
    Plant,
    PlantingBed,
    PlantType,
    PocketLayout,
    RainGarden,
    Trellis,
)
from typehaus.model.led import LedCable, LedChannel, LedController, LedStandard, LedStrip
from typehaus.model.linesets import LinesetStandard, RefrigerantLimits
from typehaus.model.materials import Material
from typehaus.model.mep import (
    ConduitRun,
    DrainCleanout,
    DuctDrain,
    DuctRun,
    ElectricalDevice,
    Equipment,
    LightRun,
    PipeAccessory,
    PipeRun,
    Register,
    SleevePenetration,
    Sump,
    SumpPump,
    VentRun,
)
from typehaus.model.millwork import (
    Countertop,
    DoorTrim,
    MillworkStandard,
    RoomTrim,
    ShelfBank,
    ShelfBay,
    StairLandingMillwork,
    StairSkirt,
    TrimStandard,
    TrimStock,
    WindowStool,
)
from typehaus.model.opening_size import OpeningSize
from typehaus.model.opening_supports import OpeningFrameEndSupports
from typehaus.model.paint import PaintSpec, PaintStandard
from typehaus.model.paneling import BoardAndBatten, PanelingSpan, PanelingSubstrate, WallPaneling
from typehaus.model.penetrations import (
    BondSleeveRow,
    BootRow,
    LinesetInletRow,
    MountBlockRow,
    PenetrationSleeveRow,
    PenetrationStandard,
    StrapBlockRow,
    StrutRow,
)
from typehaus.model.placeables import (
    ClearancePolicy,
    ClearanceZone,
    CountertopHole,
    Footprint2D,
    Location,
    ModelRepresentation,
    Mount,
    MountKind,
    PlacementStrategy,
    PlanRepresentation,
    PortCertainty,
    ServicePort,
    WallAttachment,
)
from typehaus.model.plan import Library, PlanModel
from typehaus.model.product import Product
from typehaus.model.project import Building, Project, Site, Storey
from typehaus.model.published_cladding import PublishedCladdingLoad
from typehaus.model.published_web import PublishedWebOpenings
from typehaus.model.raceway_cables import RacewayCable
from typehaus.model.rebar import BarSpec, HookConfinement, ReinforcementSpec, RibLayout
from typehaus.model.refs import (
    Arch,
    DiaphragmDelivery,
    DiaphragmSpec,
    Embed,
    FaceRef,
    FollowRoof,
    HeadConnector,
    InServiceMoisture,
    LayerMaterial,
    LayerSpan,
    OpeningPosition,
    PublishedCapacity,
    PublishedHole,
    PublishedReaction,
    PublishedSpan,
    ReceivingLine,
    ShearPanelSpec,
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
from typehaus.model.screens import SlatScreen
from typehaus.model.sheathing_nailing import SheathingNailing
from typehaus.model.sheet_layout import SheetLayoutStandard
from typehaus.model.shower_assembly import (
    ShowerAssemblySpec,
    ShowerComponent,
    ShowerValveDimensions,
    ShowerValvePocket,
)
from typehaus.model.sill_course import SillCourseFastening
from typehaus.model.site import (
    Basemap,
    Benchmark,
    ConcreteServiceTemperature,
    Contour,
    Easement,
    ErosionControl,
    ImperviousSurface,
    MonthlyNormal,
    SetbackSpec,
    SoilBasis,
    SpotElevation,
    StreetFrontage,
    SubgradeModulus,
    UtilityLine,
    WindowWell,
    load_basemap_geojson,
)
from typehaus.model.slab_fall import DrainDish, SlabFall
from typehaus.model.snow_retention import SnowRetentionSpec
from typehaus.model.spatial import (
    Alarm,
    Annotation,
    Appliance,
    Fixture,
    Furniture,
    GridAxis,
    Roof,
    Room,
    Stair,
    WallLiningException,
)
from typehaus.model.srw_chart import SrwChartSection, SrwDrain
from typehaus.model.stair_winders import WinderFramingSpec, WinderTurnSpec
from typehaus.model.stormwater import AreaDrain
from typehaus.model.structure import (
    Beam,
    Connector,
    CrushedStoneSpec,
    Dowel,
    DrainTile,
    Drywell,
    EndRestraint,
    Footing,
    FootingBedding,
    FoundationWall,
    FrenchDrain,
    GlazingPanel,
    IsolationBoard,
    KneeBrace,
    Pad,
    PlateTie,
    Post,
    Railing,
    SegmentalWallSpec,
    SolarPanel,
    SrwDrainageZone,
    Wedge,
)
from typehaus.model.suspension import HangingSeatType, SuspensionAnchor
from typehaus.model.track_lighting import TrackHeadProduct, TrackHeadSpec, TrackLightingSpec
from typehaus.model.trim import (
    DischargeExtension,
    Downspout,
    EaveDripEdge,
    EaveGutter,
    EaveSoffit,
    EaveTrim,
    Fascia,
    FasciaBoard,
    Flashing,
    GlazingTrim,
    Gutter,
    MovementJoint,
)
from typehaus.model.trim_fastening import TrimFastening
from typehaus.model.truss_order import SpecifiedReaction, TrussAppliedLoad, TrussOrder
from typehaus.model.tub_enclosure import TubEnclosureSpec
from typehaus.model.types import (
    ApplianceType,
    BookcaseDoorSpec,
    BuiltInBookcaseBay,
    BuiltInBookcaseSpec,
    DoorCatalogDimensions,
    DoorType,
    DuctProductType,
    ElectricalDeviceType,
    EquipmentType,
    FasciaMountSpec,
    FixtureType,
    FurnitureType,
    HeatPumpRating,
    LuminaireType,
    MeshRef,
    ProductPart,
    RailingType,
    RegisterType,
    SurfaceMountSpec,
    SurfacePostMount,
    TerminalNeck,
    TerminalNeckComponent,
    TerminalNeckInlet,
    WindowType,
)
from typehaus.model.vent_run import VentIncreaser
from typehaus.model.views import (
    Continuity,
    DetailAnnotation,
    ExaggerationSpec,
    LayerJoin,
    Slice,
    SliceDimension,
    Transition,
)
from typehaus.model.wall_mount import WallMountSpec
from typehaus.model.window_install import WindowInstallFastening
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
    ("face", face), ("LayerMaterial", LayerMaterial),
    ("outside_of", outside_of), ("inside_of", inside_of),
    ("layers", layers), ("from_node", from_node), ("centered", centered),
    ("in_slab", in_slab), ("under_subfloor", under_subfloor),
    ("OpeningFrameEndSupports", OpeningFrameEndSupports), ("OpeningSize", OpeningSize),
    ("ToRoof", ToRoof), ("FollowRoof", FollowRoof), ("Arch", Arch),
    ("PublishedSpan", PublishedSpan), ("PublishedCapacity", PublishedCapacity),
    ("PublishedReaction", PublishedReaction), ("PublishedCladdingLoad", PublishedCladdingLoad),
    ("PublishedHole", PublishedHole), ("SheathingNailing", SheathingNailing),
    ("TrimFastening", TrimFastening), ("WindowInstallFastening", WindowInstallFastening),
    ("PublishedWebOpenings", PublishedWebOpenings), ("JoistHoleChart", JoistHoleChart),
    ("JoistFlangeAllowance", JoistFlangeAllowance), ("EquipmentHangers", EquipmentHangers),
    ("AirHandlerInstallation", AirHandlerInstallation), ("DrainFittings", DrainFittings),
    ("SegmentalWallSpec", SegmentalWallSpec), ("SrwDrainageZone", SrwDrainageZone),
    ("SrwChartSection", SrwChartSection), ("SrwDrain", SrwDrain),
    ("EndRestraint", EndRestraint),
    ("ShearPanelSpec", ShearPanelSpec), ("DiaphragmSpec", DiaphragmSpec),
    ("DiaphragmDelivery", DiaphragmDelivery), ("ReceivingLine", ReceivingLine),
    ("CollectorBlocking", CollectorBlocking), ("JointNailing", JointNailing),
    ("SpecifiedReaction", SpecifiedReaction), ("TrussAppliedLoad", TrussAppliedLoad),
    ("TrussOrder", TrussOrder),
    ("PanelEdgeBlocking", PanelEdgeBlocking),
    ("HeadConnector", HeadConnector), ("InServiceMoisture", InServiceMoisture),
    ("Library", Library), ("PlanModel", PlanModel),
    ("BookcaseDoorSpec", BookcaseDoorSpec),
    ("Footprint2D", Footprint2D), ("CountertopHole", CountertopHole),
    ("ClearanceZone", ClearanceZone), ("ServicePort", ServicePort),
    ("ShowerAssemblySpec", ShowerAssemblySpec), ("ShowerComponent", ShowerComponent),
    ("ShowerValveDimensions", ShowerValveDimensions), ("ShowerValvePocket", ShowerValvePocket),
    ("PlanRepresentation", PlanRepresentation), ("ModelRepresentation", ModelRepresentation),
    ("Location", Location), ("WallAttachment", WallAttachment), ("Mount", Mount),
):
    register_constructor(_name, _obj)

__all__ = [
    "DoorHardwareItem", "JambFraming",
    "DoorwayProductSpec", "DoorwaySectionPart", "DoorwayTreatment", "ExteriorDoorInstallation",
    "ExteriorDoorSillDesign", "ExteriorDoorCatalogInstallation", "DoorCatalogDimensions",
    "ApproachBearing", "PlyFastening", "FillerBlock", "SillCourseFastening",
    "WinderTurnSpec", "WinderFramingSpec",
    "ReinforcementSpec",
    "BarSpec",
    "HookConfinement",
    "RibLayout",
    "FiberSpec",
    "ConcreteSpec",
    "CementSpec", "ScmFractions", "AsrSpec",
    "PlanModel", "Library", "Project", "Site", "Building", "Storey",
    "Element", "HausModel",
    "Node", "Wall", "Door", "Window", "RoughOpening",
    "FoundationWall", "Footing", "CrushedStoneSpec", "Pad", "FootingBedding", "DrainTile",
    "SegmentalWallSpec", "SrwDrainageZone", "SrwChartSection", "SrwDrain", "EndRestraint",
    "Post", "Beam", "SlatScreen",
    "FrenchDrain", "Drywell", "AreaDrain", "DrainColumn", "Excavation", "SideSlope", "SoilFactor",
    "Dowel", "IsolationBoard", "Connector", "PlateTie", "KneeBrace", "SlatBrace", "StrapBrace",
    "Wedge",
    "Railing", "SnowRetentionSpec",
    "Fascia", "Gutter",
    "Flashing", "FormedFlashingSection", "MovementJoint",
    "EaveSoffit", "FasciaBoard", "EaveGutter", "EaveDripEdge", "EaveTrim", "GlazingPanel",
    "GlazingTrim",
    "Downspout", "DischargeExtension",
    "PlantType", "Plant", "PlantingBed", "GridLayout", "PocketLayout", "AccentRule",
    "Trellis", "RainGarden",
    "SolarPanel",
    "Assembly", "RainscreenBaseFlashing", "Layer", "LayerBound", "LayerExtent", "CavityFill",
    "FramingSpec",
    "MasonrySpec", "AssemblyInterface",
    "ConstructionRule", "Substitution", "Material", "Product",
    "DoorType", "BookcaseDoorSpec", "BypassDoorSpec", "WindowType", "FurnitureType", "FurnitureCut",
    "BuiltInBenchSpec", "CurtainStack", "CurtainTrackSpec", "FixtureType",
    "ProductPart",
    "TubEnclosureSpec",
    "ApplianceType", "EquipmentType",
    "BuiltInBookcaseBay", "BuiltInBookcaseSpec",
    "HeatPumpRating",
    "RegisterType", "RailingType", "FasciaMountSpec", "WallMountSpec", "SurfaceMountSpec",
    "SurfacePostMount",
    "DuctProductType", "TerminalNeck",
    "TerminalNeckComponent", "TerminalNeckInlet", "ElectricalDeviceType",
    "LuminaireType", "MeshRef", "TrackHeadProduct", "TrackHeadSpec", "TrackLightingSpec",
    "JoistSpec", "JoistReinforcement", "Strongback", "DeckLayer", "FloorSystem", "FloorOpening",
    "FloorOpeningEdgeInterval", "FloorOpeningLid", "FloorOpeningPocketClosure",
    "Slab", "SlabFall", "SlabThermalBreak", "DrainDish",
    "Soffit", "SoffitOpening",
    "FloorHeat", "FinishZone",
    "PanelingSubstrate", "BoardAndBatten", "PanelingSpan", "WallPaneling", "WallBacking",
    "BracedWallPanel",
    "SuspensionAnchor", "HangingSeatType",
    "Countertop", "MillworkStandard", "RoomTrim", "StairLandingMillwork", "ShelfBank", "ShelfBay",
    "DoorTrim", "DoorUndercut", "StairSkirt", "TrimStandard", "TrimStock", "WindowStool",
    "DrywallStandard", "ShadowGapProfile", "TerminationBead", "PaintSpec", "PaintStandard",
    "HeaderStandard", "SheetLayoutStandard",
    "Room", "Stair", "Roof", "GridAxis", "Annotation", "Fixture", "Furniture", "Appliance",
    "Alarm",
    "WallLiningException",
    "Slice", "SliceDimension", "Transition", "Continuity", "ExaggerationSpec",
    "DetailAnnotation", "LayerJoin",
    "FaceRef", "face", "LayerMaterial", "ToRoof", "FollowRoof", "Arch", "LayerSpan",
    "OpeningFrameEndSupports", "OpeningPosition", "OpeningSize",
    "PublishedSpan", "PublishedCapacity", "PublishedReaction",
    "PublishedCladdingLoad", "PublishedHole", "PublishedWebOpenings", "JoistHoleChart",
    "JoistFlangeAllowance", "EquipmentHangers", "AirHandlerInstallation", "DrainFittings",
    "SheathingNailing", "TrimFastening", "WindowInstallFastening",
    "ShearPanelSpec", "DiaphragmSpec", "DiaphragmDelivery", "ReceivingLine", "HeadConnector",
    "CollectorBlocking", "JointNailing", "PanelEdgeBlocking",
    "SpecifiedReaction", "TrussAppliedLoad", "TrussOrder",
    "InServiceMoisture",
    "Embed", "outside_of", "inside_of", "layers", "from_node", "centered",
    "in_slab", "under_subfloor",
    "PipeRun", "PipeAccessory", "DrainCleanout", "SleevePenetration", "DuctRun", "DuctDrain",
    "Register", "Equipment",
    "ElectricalDevice",
    "Circuit", "LoadManagement", "BoxStandard", "BoxRow",
    "BoxSupport", "PlateRow", "ConduitRun", "LightRun",
    "RacewayCable",
    "GroundingStandard", "GroundingElectrode", "BondingConductor", "ServiceEntrance",
    "LabelStandard", "LedCable", "LedChannel", "LedController", "LedStandard", "LedStrip",
    "LinesetStandard", "RefrigerantLimits",
    "PenetrationStandard", "PenetrationSleeveRow", "BondSleeveRow", "BootRow", "StrapBlockRow",
    "LinesetInletRow", "MountBlockRow", "StrutRow",
    "DuctStandard", "RoundGaugeRow", "DuctElbowRow", "DuctPartRow", "DuctSupportRow", "PortKit",
    "RectElbowRow", "DuctInsulationRow",
    "Sump", "SumpPump", "VentRun", "VentIncreaser",
    "MonthlyNormal", "SubgradeModulus", "SoilBasis", "ConcreteServiceTemperature",
    "SetbackSpec",
    "SpotElevation", "ImperviousSurface",
    "WindowWell",
    "UtilityLine",
    "Easement", "ErosionControl", "StreetFrontage", "Benchmark",
    "Contour", "Basemap",
    "load_basemap_geojson",
    "LayerFunction", "LayerDatum", "ControlLayer", "JunctionPolicy", "Occupancy",
    "HumidityClass",
    "Service", "AlarmKind",
    "StructuralRole", "SliceKind", "FloorOpeningPurpose", "RadiantSystem", "RacewayMaterial",
    "PartitionLayout", "RoofForm", "ConditionKind",
    "PipeSystem", "PipeAccessoryKind", "DuctSystem", "DuctRouting", "EquipmentKind",
    "BackupTier", "DeviceKind", "LuminaireForm", "RatingBasis", "UtilityKind",
    "ConnectorKind", "RailingKind", "TrimKind", "ShelfProcurement",
    "ClearZone", "PlacementStrategy", "MountKind", "ClearancePolicy",
    "Footprint2D", "CountertopHole", "ClearanceZone",
    "ServicePort", "PortCertainty", "ShowerAssemblySpec", "ShowerComponent",
    "ShowerValveDimensions", "ShowerValvePocket",
    "PlanRepresentation", "ModelRepresentation", "Location", "WallAttachment",
    "Mount",
    "Length", "Area", "Angle", "Pitch", "RValue", "UFactor", "Temperature", "Point2D",
    "ft", "inch", "mm", "m", "deg", "rad", "sqft", "sqm", "r_us", "rsi", "u_us",
    "degC", "degF", "pt",
    "constructor_names", "element_kinds", "register_constructor",
]

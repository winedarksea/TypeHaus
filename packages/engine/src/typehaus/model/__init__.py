"""The element model — the typed heart of the product (→ 10 §Element model).

Importing this package populates the constructor registry (the dialect allowlist) with
every element/library constructor, plus the quantity and reference constructors.
"""

from __future__ import annotations

from typehaus.model.assembly import (
    Assembly,
    AssemblyInterface,
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
    ControlLayer,
    FloorOpeningPurpose,
    JunctionPolicy,
    LayerFunction,
    Occupancy,
    PartitionLayout,
    RadiantSystem,
    RoofForm,
    Service,
    SliceKind,
    StructuralRole,
)
from typehaus.model.floors import (
    DeckLayer,
    FinishZone,
    FloorHeat,
    FloorOpening,
    FloorSystem,
    JoistSpec,
    Slab,
    Soffit,
)
from typehaus.model.materials import Material
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
from typehaus.model.structure import Beam, Footing, FoundationWall, Pad, Post
from typehaus.model.spatial import (
    Annotation,
    Alarm,
    Fixture,
    Furniture,
    GridAxis,
    Roof,
    Room,
    Stair,
    WallLiningException,
)
from typehaus.model.types import (
    DoorType,
    FixtureType,
    FurnitureType,
    MeshRef,
    WindowType,
)
from typehaus.model.views import Continuity, ExaggerationSpec, Slice, Transition
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
):
    register_constructor(_name, _obj)

__all__ = [
    "PlanModel", "Library", "Project", "Site", "Building", "Storey",
    "Element", "HausModel",
    "Node", "Wall", "Door", "Window", "RoughOpening",
    "FoundationWall", "Footing", "Pad", "Post", "Beam",
    "Assembly", "Layer", "FramingSpec", "MasonrySpec", "AssemblyInterface",
    "ConstructionRule", "Substitution", "Material",
    "DoorType", "WindowType", "FurnitureType", "FixtureType", "MeshRef",
    "JoistSpec", "DeckLayer", "FloorSystem", "FloorOpening", "Slab", "Soffit",
    "FloorHeat", "FinishZone",
    "Room", "Stair", "Roof", "GridAxis", "Annotation", "Fixture", "Furniture",
    "Alarm",
    "WallLiningException",
    "Slice", "Transition", "Continuity", "ExaggerationSpec",
    "FaceRef", "face", "ToRoof", "FollowRoof", "Arch", "LayerSpan", "OpeningPosition",
    "Embed", "outside_of", "inside_of", "layers", "from_node", "centered",
    "in_slab", "under_subfloor",
    "LayerFunction", "ControlLayer", "JunctionPolicy", "Occupancy", "Service", "AlarmKind",
    "StructuralRole", "SliceKind", "FloorOpeningPurpose", "RadiantSystem",
    "PartitionLayout", "RoofForm", "ConditionKind",
    "Length", "Area", "Angle", "Pitch", "RValue", "UFactor", "Temperature", "Point2D",
    "ft", "inch", "mm", "m", "deg", "rad", "sqft", "sqm", "r_us", "rsi", "u_us",
    "degC", "degF", "pt",
    "constructor_names", "element_kinds", "register_constructor",
]

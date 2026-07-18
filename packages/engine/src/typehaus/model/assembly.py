"""Assembly, Layer, framing specs, interfaces, construction rules (→ 10, → 11)."""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.enums import (
    ControlLayer,
    JunctionPolicy,
    LayerFunction,
    PartitionLayout,
)
from typehaus.model.refs import LayerSpan
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class FramingSpec(HausModel):
    """A plain record — never geometry — driving the framing solver (risk 6, → 11).

    Carried by a STRUCTURE layer (always) and optionally by a FURRING layer (which
    then generates strapping/battens on its own grid, per ``direction``)."""

    member: str = "2x6"  # nominal lumber size, e.g. "2x4", "2x6", "2x8"
    spacing: Length | None = None  # o.c.; defaults to 16" at the solver
    layout: PartitionLayout = PartitionLayout.SINGLE
    double_top_plate: bool = True
    advanced_framing: bool = False  # single top plate + in-line stud stacking
    stagger_gap: Length | None = None  # for STAGGERED/DOUBLE partition layouts
    direction: str | None = None  # FURRING only: "vertical" | "horizontal"


class MasonrySpec(HausModel):
    """CMU/ICF STRUCTURE layer — layered solid + arithmetic unit takeoff, no members (#23)."""

    unit_size: str  # e.g. "8x8x16 CMU", "ICF-6"
    coursing: Length | None = None
    core_fill: bool = False
    rebar_spacing: Length | None = None


class Layer(HausModel):
    """One layer of an assembly stack (→ 10 §Element model)."""

    name: str
    material_ref: str
    thickness: Length
    function: LayerFunction
    framing: FramingSpec | None = None
    masonry: MasonrySpec | None = None
    control: frozenset[ControlLayer] = frozenset()


class AssemblyInterface(HausModel):
    """A resolved, named physical face role an assembly publishes (#44).

    Semantic roles, not layer indices, so a variant may add/replace layers without
    invalidating a transition that binds to them."""

    role: str  # "bearing" | "structure_ext" | "structure_int" | "envelope_datum" |
    #            "drainage" | "control:air" | ...
    layer_name: str  # the layer whose face realizes this role
    outboard: bool  # which face of that layer (outboard vs inboard)


class Substitution(HausModel):
    """A variant layer-span substitution (#35)."""

    span: LayerSpan
    replacement: tuple[Layer, ...]


class Assembly(HausModel):
    """A layered wall/roof/floor assembly — one definition drives 3D solids, slice
    stacks, R-value, BOM, transition anchors, and the section card (→ 10 §Element model).

    Two-tier (#34): ``layers`` is the *core* (structure + everything outboard);
    ``default_lining`` is the interior-of-structure finish stack, overridable per room."""

    tag: str
    # Base assemblies list their layers; a variant leaves this empty and resolves layers
    # live against its base via ``substitute`` (#35).
    layers: tuple[Layer, ...] = ()
    default_lining: tuple[Layer, ...] = ()
    junction_policy: JunctionPolicy = JunctionPolicy.STRUCTURE_BUTTS_FINISH_WRAPS
    # Variants (#35): resolve live against the base; unchanged layers track it forever.
    variant_of: str | None = None
    substitute: tuple[Substitution, ...] = ()
    # Acoustics (#50): empirical lab-test lookup, never computed.
    stc: int | None = None
    source: str | None = None

    def structure_index(self) -> int | None:
        for i, layer in enumerate(self.layers):
            if layer.function is LayerFunction.STRUCTURE:
                return i
        return None


class ConstructionRule(HausModel):
    """A typed pre-resolve input (#45): blocking, plate/bearing geometry, web
    stiffeners, required gaps. Applied once before final framing. Selected by compact
    family/role predicates. Cannot draw notes/overlays — a Transition documents it."""

    tag: str
    applies_to: str  # family/role predicate, e.g. "roof:eave", "wall:rim"
    kind: str  # "blocking" | "bearing_plate" | "web_stiffener" | "gap" | "offset"
    dimension: Length | None = None
    takeoff_category: str | None = None


for _name, _obj in (
    ("Layer", Layer),
    ("FramingSpec", FramingSpec),
    ("MasonrySpec", MasonrySpec),
    ("Assembly", Assembly),
    ("AssemblyInterface", AssemblyInterface),
    ("ConstructionRule", ConstructionRule),
    ("Substitution", Substitution),
):
    register_constructor(_name, _obj)

"""Assembly, Layer, framing specs, interfaces, construction rules (→ 10, → 11)."""

from __future__ import annotations

from typing import Literal

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
    corner_style: Literal["3-stud", "4-stud"] = "3-stud"
    tee_backing_style: Literal["ladder", "stud-pack", "none"] = "ladder"
    # None uses the framing solver's named domain default.
    tee_blocking_spacing: Length | None = None
    # In-line blocking courses (fire/backing blocking) at these heights above the sole
    # plate. Each height adds one horizontal row of blocking fitted between the studs in
    # every bay. Empty (the default) emits no blocking, so existing walls are unchanged.
    blocking_heights: tuple[Length, ...] = ()


class MasonrySpec(HausModel):
    """CMU/ICF STRUCTURE layer — layered solid + arithmetic unit takeoff, no members (#23)."""

    unit_size: str  # e.g. "8x8x16 CMU", "ICF-6"
    coursing: Length | None = None
    core_fill: bool = False
    rebar_spacing: Length | None = None


class CavityFill(HausModel):
    """Insulation living *inside* a STRUCTURE layer's stud/joist bays — never its own layer.

    A batt between studs occupies the framing depth; it adds no thickness to the assembly
    and shares its host layer's polygon. Modelling it as a sibling ``Layer`` double-counts
    both the wall depth and the R-value (the fill and the framing are a parallel path, not
    a series one) and exports an ``IfcMaterialLayerSet`` that no longer sums to the wall
    thickness — which is what Revit/SketchUp read on import.

    ``thickness`` defaults to the host layer's thickness (a full-depth bay); a shallower
    fill (R-13 batt in a 2x6 bay) states its own, and the remainder is treated as still air.
    """

    material_ref: str
    thickness: Length | None = None  # None => the host STRUCTURE layer's thickness
    framing_factor: float = 0.23  # fraction of area that is framing, not fill
    control: frozenset[ControlLayer] = frozenset()


class Layer(HausModel):
    """One layer of an assembly stack (→ 10 §Element model)."""

    name: str
    material_ref: str
    thickness: Length
    function: LayerFunction
    framing: FramingSpec | None = None
    masonry: MasonrySpec | None = None
    control: frozenset[ControlLayer] = frozenset()
    # STRUCTURE layers only: insulation in the framing bays (non-additive, → CavityFill).
    cavity: CavityFill | None = None


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
    # Named physical-face roles this assembly publishes (#44). The junction solver binds
    # mixed-assembly corners/tees to these roles instead of layer names/indices, so a
    # variant may add or replace layers without invalidating the junction rule.
    interfaces: tuple[AssemblyInterface, ...] = ()
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

    def interface(self, role: str) -> AssemblyInterface | None:
        """The published face role, or None. Roles are matched by name, never layer index."""
        return next((iface for iface in self.interfaces if iface.role == role), None)


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
    ("CavityFill", CavityFill),
    ("FramingSpec", FramingSpec),
    ("MasonrySpec", MasonrySpec),
    ("Assembly", Assembly),
    ("AssemblyInterface", AssemblyInterface),
    ("ConstructionRule", ConstructionRule),
    ("Substitution", Substitution),
):
    register_constructor(_name, _obj)

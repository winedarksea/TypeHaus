"""Assembly, Layer, framing specs, interfaces, construction rules (→ 10, → 11)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import HausModel
from typehaus.model.enums import (
    ControlLayer,
    JunctionPolicy,
    LayerDatum,
    LayerFunction,
    PartitionLayout,
)
from typehaus.model.refs import LayerSpan
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class FramingSpec(HausModel):
    """A plain record — never geometry — driving the framing solver (risk 6, → 11).

    Carried by a STRUCTURE layer (always) and optionally by a FURRING layer (which
    then generates strapping/battens on its own grid, per ``direction``)."""

    member: str = "2x6"  # nominal lumber size, e.g. "2x4", "2x6", "2x8"
    spacing: Length | None = None  # o.c.; defaults to 16" at the solver
    layout: PartitionLayout = PartitionLayout.SINGLE
    # STAGGERED layout: the plate (and end/corner/opening framing) size when it differs
    # from ``member`` — the classic acoustic wet wall is 2x4 studs on 2x6 plates. None
    # means plates match ``member`` (every SINGLE-layout wall today).
    plate_member: str | None = None
    double_top_plate: bool = True
    # Roof STRUCTURE layers only: "rafter" (plain sloped members, the default) or "truss"
    # (top + bottom chord + web members with a raised heel at the eave bearing). Declarative,
    # so a roof assembly asks for engineered trusses without touching the framing solver.
    roof_frame: Literal["rafter", "truss"] = "rafter"
    # truss only — the raised-heel height (top of plate → underside of the top chord at the
    # bearing) so full insulation depth carries over the wall. None uses the solver default.
    heel_height: Length | None = None
    # truss only — chord/web nominal sizes; each defaults to ``member`` (chord) / "2x4" (web).
    chord_member: str | None = None
    web_member: str | None = None
    advanced_framing: bool = False  # single top plate + in-line stud stacking
    # Where the stud module counts from. "wall-start" — the default, and every wall written
    # before this existed — starts at the wall's own station 0, so two collinear segments
    # split at a tee each restart the module and a wall over a wall aligns only by the
    # accident of sharing a start node. "line" counts from the wall's *layout line* instead
    # (→ resolve/layout_lines.py), so the module runs through a tee split and stacks floor
    # to floor, and the battens that phase-lock to it follow for free.
    #
    # Deliberately not folded into ``advanced_framing``, which also drops the second top
    # plate: in-line studs and a single top plate are independent decisions and the code
    # backs that up. R602.3.2's single-top-plate exception turns on *rafters or joists*
    # centred over studs within 1", not on studs stacking over studs (R602.3.3's 5" rule is
    # the bearing-stud one). In-line framing is an APA Advanced Framing technique, not a
    # code mandate, which is exactly why it is an opt-in field rather than an inference.
    layout_origin: Literal["wall-start", "line"] = "wall-start"
    stagger_gap: Length | None = None  # for STAGGERED/DOUBLE partition layouts
    direction: str | None = None  # FURRING only: "vertical" | "horizontal"
    # FURRING only: which way the stick is turned in the band. "flat" (the default, and
    # every furred wall before the truss wall existed) lays the wide face against the
    # sheathing — a 1x4 rainscreen batten, 3-1/2" on the wall and 3/4" through it. "edge"
    # stands it up so the wide face runs *through* the wall: the 2x4 outrigger of a truss
    # wall, 1-1/2" on the wall and 3-1/2" out from it. The default is what keeps every
    # existing FURRING spec framing exactly as it did.
    laid: Literal["flat", "edge"] = "flat"
    corner_style: Literal["3-stud", "4-stud"] = "3-stud"
    # FURRING only — the Larsen/Swinburne plywood corner box (FHB Jan 2024) that closes an
    # owned L corner's two outboard faces outboard of the sheathing, where the band's own
    # mitre otherwise leaves a full-height void with no framed member in it. "none" (the
    # default) keeps every furred wall, including every rainscreen batten, exactly as it
    # framed before this field existed; only a truss wall opts in.
    corner_cap: Literal["none", "plywood-box"] = "none"
    tee_backing_style: Literal["ladder", "stud-pack", "none"] = "ladder"
    # None uses the framing solver's named domain default.
    tee_blocking_spacing: Length | None = None
    # In-line blocking courses (fire/backing blocking) at these heights above the sole
    # plate. Each height adds one horizontal row of blocking fitted between the studs in
    # every bay. Empty (the default) emits no blocking, so existing walls are unchanged.
    blocking_heights: tuple[Length, ...] = ()
    # Compressible sill-seal gasket under the sole/sill plate (capillary + air break at
    # the plate-to-concrete joint), stated as its **compressed, in-place** thickness — the
    # dimension the wall-base detail draws and the one the bearing seat is derived from
    # (a house's seat = joist depth + mudsill + gasket). It was the *uncompressed* roll
    # thickness until 2026-08-24, which no consumer wanted: the only reader draws the
    # joint as built, and a house that needed the real number was hard-coding it beside
    # this field. None = no gasket.
    sill_gasket: Length | None = None
    # Which sill-seal product that gasket is, for the BOM. None (the default) lets
    # ``resolve/construction_sills.py`` pick from the wall itself: a wall with a cladding
    # layer is an air-barrier crossing and gets the peel-and-stick form, an interior wall
    # gets plain closed-cell foam. State it only to override that.
    sill_gasket_product: str | None = None


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


class LayerBound(HausModel):
    """One end of a layer's vertical extent: a datum, plus a signed offset from it."""

    datum: LayerDatum
    offset: Length = inch(0)


class LayerExtent(HausModel):
    """How far up a wall one layer of the stack actually runs.

    This is the "vertically compound wall" of a BIM authoring tool — a layer row split into
    regions at a height — expressed on the *type* rather than on each wall, which is the only
    place it can live: an ``Assembly`` is shared by many walls and knows none of their
    elevations. Two layers with non-overlapping extents that name the same ``Layer.slot``
    are the two regions of one split row, and share one depth position in the stack.

    ``None`` on either end means the wall's own end, which is what every layer written before
    this existed still says by carrying no ``extent`` at all.
    """

    bottom: LayerBound | None = None   # None -> the wall's base
    top: LayerBound | None = None      # None -> the wall's top


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
    # Vertical extent, when this layer does not run the wall's full height — a protection
    # panel above grade, a splash course at the base, a water table. ``None`` is full height,
    # and is what the whole catalog said before this field existed. A banded layer with no
    # ``slot`` still occupies its full depth in the stack: it displaces the layers outboard
    # of it over the whole wall, exactly as a full-height layer of the same thickness would,
    # because the alternative — a stack whose total thickness varies with elevation — is not
    # something ``Wall.alignment`` or any junction rule can answer.
    extent: LayerExtent | None = None
    # The regions of ONE row of the stack, named. Layers sharing a ``slot`` occupy a single
    # depth position between them rather than one each — a brick plinth under a different
    # brick field, a parge below grade under a protection panel above it. Without it the
    # only way to spell a split row was to author the regions as separate layers, and the
    # stack walk then charged the wall for every one of them: four 3 5/8" brick regions
    # resolved to a 14 1/2" wythe.
    #
    # The rules, enforced by ``integrity.assembly_layers``: every member carries the same
    # ``thickness`` (a slot with no single depth is not a depth position), every member
    # carries an ``extent`` (one that did not would claim the whole wall and hide its
    # siblings), and no two members' bands overlap. Elevations not claimed by any member
    # are simply not built — a row may have a gap, and that is what a reveal is.
    slot: str | None = None


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
    # What this assembly IS, which every rule about it has had to guess from its layers.
    #
    # "enclosure" — the only kind that existed: a wall, a roof, a floor, a slab. It separates
    # an inside from an outside, so it must have a STRUCTURE layer
    # (``integrity.assembly_layers``), its interior-most face is a face somebody stands in
    # front of (``code.R316_4``), and a horizontal one is a surface somebody walks on
    # (``resolve.site_earth``).
    #
    # "band" — a buried, single-purpose layer of the ground: an FPSF wing of rigid foam
    # under a slab, a capillary break, a skirt. It has no structure by definition, faces no
    # room (IRC R316.5 exempts foam used under a slab or in a foundation from R316.4 for
    # exactly this reason), and is nobody's walking surface. Modelled as a thin ``Slab``
    # because ``Layer.extent`` measures from WALL_BASE / WALL_TOP / GRADE and is
    # vertical-only, so it cannot describe a skirt reaching out sideways under a floor.
    #
    # Authored rather than inferred, because the natural inference — "no STRUCTURE layer" —
    # is precisely the mistake ``integrity.assembly_layers`` exists to catch, and a rule
    # cannot both catch a thing and treat it as a declaration.
    role: Literal["enclosure", "band"] = "enclosure"
    source: str | None = None

    def depth_layers(self) -> tuple[Layer, ...]:
        """The layers that occupy their own slice of the stack depth, interior→exterior.

        The regions of one ``Layer.slot`` share a slice: they sit at different elevations in
        the same row, so only the first of them counts toward how deep the assembly is. Any
        caller measuring or rolling up the STACK — total thickness, an R-value walk — wants
        this rather than ``layers``, which is every authored region and would report a
        four-region brick wythe as four wythes deep.

        A caller that wants each region, because it is billing area or drawing a band, wants
        ``layers`` and is right to.
        """
        seen: set[str] = set()
        out: list[Layer] = []
        for layer in self.layers:
            if layer.slot is not None:
                if layer.slot in seen:
                    continue
                seen.add(layer.slot)
            out.append(layer)
        return tuple(out)

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
    kind: str  # "blocking" | "bearing_plate" | "web_stiffener" | "furring" | "gap" | "offset"
    dimension: Length | None = None
    takeoff_category: str | None = None
    # Optional element tag the finder clips its search to — the rule applies *there* and
    # nowhere else. A predicate alone selects a family ("every framed wall on concrete");
    # some returns are a single room's decision (resilient channel under one living-room
    # ceiling, not under the whole deck), and without this the only way to say so would be
    # to invent a one-off predicate per room. Finders that ignore it are unaffected.
    scope_ref: str | None = None


for _name, _obj in (
    ("Layer", Layer),
    ("LayerBound", LayerBound),
    ("LayerExtent", LayerExtent),
    ("CavityFill", CavityFill),
    ("FramingSpec", FramingSpec),
    ("MasonrySpec", MasonrySpec),
    ("Assembly", Assembly),
    ("AssemblyInterface", AssemblyInterface),
    ("ConstructionRule", ConstructionRule),
    ("Substitution", Substitution),
):
    register_constructor(_name, _obj)

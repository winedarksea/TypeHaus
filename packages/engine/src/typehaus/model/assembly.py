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
    # Wall STRUCTURE layers only: "studs" (a sole plate, studs, and top plate(s) — the
    # default) or "plate" — the layer IS one course of lumber laid flat, and nothing
    # stands on it.
    #
    # A rafter plate on an attic subfloor is the case that needed it: in a story-and-a-half
    # the roof lands on a 2x laid flat over the wall below, and there is no knee wall at all.
    # That course still has to exist as a wall — it closes the storey's room loop and it is
    # what the roof bears on — but it is 1 1/2" tall, and the solver's sole plate plus double
    # top plate is already 4 1/2" of hard floor. Below that, `top_at` hands out NEGATIVE stud
    # lengths and `_append_plates` stacks courses through each other, silently, with no
    # finding. A course of lumber is not a short stud wall; it is a different thing, and this
    # says which one the layer means rather than leaving the solver to guess from a height.
    wall_frame: Literal["studs", "plate"] = "studs"
    # truss only — the raised-heel height (top of plate → underside of the top chord at the
    # bearing) so full insulation depth carries over the wall. None uses the solver default.
    heel_height: Length | None = None
    # truss only — chord/web nominal sizes; each defaults to ``member`` (chord) / "2x4" (web).
    chord_member: str | None = None
    web_member: str | None = None
    advanced_framing: bool = False  # single top plate + in-line stud stacking
    # Where the stud module counts from. "wall-start" — the default — starts at the wall's
    # own station 0, so two collinear segments
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
    # FURRING + ``direction="horizontal"`` only: what the COURSE module counts from.
    # "wall-base" — the default — is ``rw.z0_m``, the bottom of the band itself.
    # "framing-base" is ``rw.base_ref_z_m``,
    # the datum every opening's sill height is measured from, which on a wall extended
    # down over a floor rim band is 13-7/16" higher.
    #
    # The two are the same elevation on a wall that starts at its own storey datum, and
    # they are not on a main-storey platform wall — which is the whole reason this exists.
    # Courses phased off the bottom of the cladding lap and sills phased off the floor put
    # a field course a fraction of an inch from an opening's own head or sill course: two
    # nailers inside one board's width, one of them redundant, thirteen times over on
    # catlin (``notes/outie_window_truss_detail.md``).
    course_datum: Literal["wall-base", "framing-base"] = "wall-base"
    #: Added to that datum before the module counts from it. ``None`` is 0. It is the phase
    #: knob: with the datum fixed by the sills, this is what slides the whole field clear
    #: of them. May be negative — the module is unbounded below and the band's own bottom
    #: is where the courses actually start.
    course_offset: Length | None = None
    stagger_gap: Length | None = None  # for STAGGERED/DOUBLE partition layouts
    direction: str | None = None  # FURRING only: "vertical" | "horizontal"
    # FURRING only: which way the stick is turned in the band. "flat" (the default, and
    # every furred wall before the truss wall existed) lays the wide face against the
    # sheathing — a 1x4 rainscreen batten, 3-1/2" on the wall and 3/4" through it. "edge"
    # stands it up so the wide face runs *through* the wall: the 2x4 outrigger of a truss
    # wall, 1-1/2" on the wall and 3-1/2" out from it. The default is what keeps every
    # existing FURRING spec framing exactly as it did.
    laid: Literal["flat", "edge"] = "flat"
    # FURRING only: the band is held off the layer behind it by BLOCKS fastened through at
    # the framing module, rather than lying on it. "none" (the default) is every furring
    # band ever authored — a batten screwed flat to the sheathing, an outrigger standing on
    # a plywood tab. "block" is the *catlin truss* girt band: a flat 2x4 course bearing on a
    # block at each module station, taking one long structural screw per block through girt
    # + block into what is behind it (→ ``framing/truss_girts.py``).
    #
    # **A girt wall is ONE horizontal, flat FURRING band with ``standoff="block"``.** The
    # TWO-band form — an inner tier buried in the insulation with the outer one screwed to
    # it — stays legal for a house that wants it; ``truss_girt_bands`` returns the inner
    # band as ``None`` when there is only one, and everything downstream iterates the tiers
    # that are actually there.
    #
    # **The block's DEPTH is not fixed at one ply and is never authored.** It is whatever
    # the stack leaves between the sheathing and this band's inboard face — 1-1/2" on the
    # two-band wall, 4-1/2" (three 2x4 offcuts, ``profile="3-2x4"``) on catlin's one-band
    # one, where the last 1/2" of it stands proud of the foam and IS the vent gap. The frame
    # reads that depth off the resolved layers and derives the ply count from it, so moving
    # the girt out in an assembly moves the block, the screw length and the BOM row with it.
    #
    # It is the girt frame's whole selector, and it is deliberately not ``laid``: a girt is
    # laid FLAT like an ordinary batten and only the standoff distinguishes it. Stood on
    # edge as well (``laid="edge"``) it is neither one thing nor the other — that is the
    # Swinburne outrigger, which frames on a tab, not on blocks — and
    # ``integrity.assembly_layers`` refuses the pair.
    standoff: Literal["none", "block"] = "none"
    corner_style: Literal["3-stud", "4-stud"] = "3-stud"
    # FURRING only — the Larsen/Swinburne plywood corner box (FHB Jan 2024) that closes an
    # owned L corner's two outboard faces outboard of the sheathing, where the band's own
    # mitre otherwise leaves a full-height void with no framed member in it. "none" (the
    # default) leaves every furred wall, including every rainscreen batten, framed as an
    # ordinary batten; only a truss wall opts in.
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
    # (a house's seat = joist depth + mudsill + gasket). None = no gasket.
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
    #: SUPERSEDED by ``Layer.concrete`` + the elements' ``ReinforcementSpec``, and read by
    #: nothing today. Kept only so no house's authored value has to move in the same change
    #: that introduces the replacement; removing it is a separate cleanup.
    rebar_spacing: Length | None = None


class FiberSpec(HausModel):
    """Fiber reinforcement dosed into a concrete mix.

    ``kind`` is what the fiber DOES, not who makes it, because the three families answer
    three different questions and are not interchangeable:

    * ``micro-synthetic`` — monofilament or fibrillated PP at ~0.75-1.5 lb/cy, targeting
      *plastic shrinkage* cracking in the first hours. It is not structural and never
      replaces steel. Monofilament is the polishable one: what little presents at a
      finished surface sits in the paste layer a cream polish removes.
    * ``macro-synthetic`` — 3-8 lb/cy, a post-crack residual strength that can stand in for
      shrinkage-and-temperature mesh on a slab-on-ground. Visible at the surface, which is
      why it belongs on a garage or an exterior pad and not on a polished interior floor.
    * ``steel`` — the strongest residual, and foreclosed on any finished or exposed surface
      because a fiber lying near it rust-stains.

    ``dose_pcy`` is pounds per cubic yard, the unit every TDS publishes. ``product`` is the
    specified item verbatim, for the submittal; it is prose and nothing grades it.
    """

    kind: Literal["micro-synthetic", "macro-synthetic", "steel"]
    dose_pcy: float | None = None
    product: str | None = None


class ConcreteSpec(HausModel):
    """What a concrete pour IS — the mix, its exposure class, its cover and its bar coating.

    Hung on the STRUCTURE layer of an :class:`Assembly` (``Layer.concrete``), exactly as
    :class:`MasonrySpec` is, because that is where ``material_ref="concrete"`` already lives
    and ``resolve/assembly_material.py::assembly_structure_material`` is already the one
    reduction that says "this is a concrete pour". Read it through
    ``resolve/concrete.py::concrete_spec_for`` and never by walking layers in a consumer.

    Before this type existed every one of these facts was English prose inside
    ``Assembly.source``, where nothing read it and nothing could grade it: the engine
    hardcoded one presumptive 3,000 psi for the whole house and *regex-scraped* cover out of
    a free-text cage string. A house could not state a 5,000 psi F3+C2 mix, so its columns
    were graded — silently, and in the safe direction — as if it had not specified one.

    **Only ``fc_psi`` is required.** Every other field is optional and a missing one reports
    UNKNOWN rather than defaulting into a number nobody authored (decision #32): a mix with
    no stated w/cm is a mix whose w/cm this model does not know, which is a different fact
    from a mix at 0.45.

    The four ACI 318-19 Table 19.3.1.1 exposure categories are **four separate fields, not a
    set**. They are orthogonal in ACI — a pour is simultaneously some F, some S, some W and
    some C — and collapsing them into one collection would make "F3" and "C2" look like
    alternatives to each other. (The editable dialect forbids ``frozenset`` in any case.)
    """

    #: Specified compressive strength, psi. The one required field: a pour whose strength
    #: is unstated is the condition that made every calc in this engine read one presumptive
    #: value, and it is the thing this type exists to end.
    fc_psi: float
    #: Maximum water-cementitious ratio. ACI Table 19.3.2.1 pairs it with the exposure
    #: class: F3 and C2 both demand <= 0.40, and 0.40 with 5,000 psi is one requirement
    #: stated two ways rather than two requirements.
    w_cm_max: float | None = None
    #: Total air content, percent, and the tolerance the spec allows around it. Air is the
    #: freeze-thaw mechanism; a F3 mix that is not air-entrained is not an F3 mix.
    air_content_pct: float | None = None
    air_tolerance_pct: float | None = None
    #: ACI 318-19 Table 19.3.1.1 exposure categories. F = freezing-and-thawing,
    #: S = sulfate, W = water (in contact with, requiring low permeability),
    #: C = corrosion protection of reinforcement.
    exposure_f: Literal["F0", "F1", "F2", "F3"] | None = None
    exposure_s: Literal["S0", "S1", "S2", "S3"] | None = None
    exposure_w: Literal["W0", "W1", "W2"] | None = None
    exposure_c: Literal["C0", "C1", "C2"] | None = None
    #: Specified clear cover to the outermost bar. Where a pour states none, the consuming
    #: calc falls back to the ACI Table 20.5.1.3.1 minimum for the condition and says which
    #: of the two it used. Authored per pour on purpose: raising the engine-wide default
    #: would move every unrelated calc at once.
    cover: Length | None = None
    #: What the bar is protected with. ``hdg-a767`` is ASTM A767 (galvanized after
    #: fabrication), ``hdg-a1094`` is A1094 (continuously galvanized, bent after coating).
    #: The distinction is real at the bender and irrelevant to capacity; both take
    #: ACI 318-19 §25.4.2.5's psi_e = 1.0, and it is EPOXY that takes 1.2-1.5 — reading the
    #: epoxy row for a galvanized bar lengthens every lap in a house by half.
    bar_coating: Literal["black", "hdg-a767", "hdg-a1094", "stainless", "gfrp",
                         "epoxy"] | None = None
    fiber: FiberSpec | None = None
    #: Supplementary cementitious materials, verbatim — "25% class F fly ash", "50% slag".
    #: Prose: the substitution rate interacts with cold-weather set times and early
    #: strength in ways nothing here grades.
    scm: str | None = None
    #: Nominal maximum aggregate size. Bounds bar clear spacing at (4/3) x this
    #: (ACI 318-19 §25.2.1) and is what makes a small column core a placement question.
    max_aggregate: Length | None = None
    #: Where these numbers come from — a mix design number, a supplier, a note in
    #: ``houses/<name>/notes/``. Prose, for the submittal.
    source: str | None = None


class CavityFill(HausModel):
    """Insulation living *inside* a STRUCTURE layer's stud/joist bays — never its own layer.

    A batt between studs occupies the framing depth; it adds no thickness to the assembly
    and shares its host layer's polygon. Modelling it as a sibling ``Layer`` double-counts
    both the wall depth and the R-value (the fill and the framing are a parallel path, not
    a series one) and exports an ``IfcMaterialLayerSet`` that no longer sums to the wall
    thickness — which is what Revit/SketchUp read on import.

    ``thickness`` defaults to the host layer's thickness (a full-depth bay); a shallower
    fill (R-13 batt in a 2x6 bay) states its own, and the remainder is treated as still air.

    A bay may hold MORE THAN ONE fill in series — ``Layer.cavity`` takes a tuple, and
    flash-and-batt is what it is for: closed-cell foam sprayed against the deck with a batt
    packed in front of it is two materials at two thicknesses through one joist depth, and
    the framing is still the single parallel path across the whole of it. The tuple is
    ordered the way the layer list is, **interior -> exterior**, so the batt is authored
    first and the flash against the sheathing last. Every member of one tuple must carry the
    same ``framing_factor``: it describes the bay's geometry, not the fill's, and two fills
    in one bay that disagree about how much of the plane is wood are describing two
    different bays (``integrity.assembly_layers`` rejects it).
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

    ``None`` on either end means the wall's own end.
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
    # The mix, exposure class, cover and bar coating of a concrete pour. Belongs on the
    # STRUCTURE layer, where ``material_ref="concrete"`` already is. Read it through
    # ``resolve/concrete.py::concrete_spec_for`` — a consumer that walks layers itself is
    # a second spelling of the same rule, and that is how the two come to disagree.
    concrete: ConcreteSpec | None = None
    control: frozenset[ControlLayer] = frozenset()
    # Insulation in this layer's framing bays (non-additive, → CavityFill). STRUCTURE
    # layers (a batt between studs) and FURRING layers alike: a furring band's fill resolves
    # as a cavity layer of its own sharing the band's depth position
    # (``resolve/topology.py``), bills as ``insulation (cavity)`` and parallel-paths against
    # the sticks in ``analysis._layer_rsi`` exactly as a stud bay does. That is what lets a
    # truss wall's foam be authored band by band instead of as one slab that hides the wood.
    # A tuple is flash-and-batt: several fills in series through one bay depth, ordered
    # interior -> exterior like the layer list itself. Read it through ``cavity_fills``,
    # never by attribute — a consumer that says ``layer.cavity.material_ref`` sees the
    # foam or the batt depending on how the bay happened to be authored.
    cavity: CavityFill | tuple[CavityFill, ...] | None = None
    # Vertical extent, when this layer does not run the wall's full height — a protection
    # panel above grade, a splash course at the base, a water table. ``None`` is full
    # height. A banded layer with no ``slot`` still occupies its full depth in the stack:
    # it displaces the layers outboard of it over the whole wall, exactly as a full-height
    # layer of the same thickness would,
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

    @property
    def cavity_fills(self) -> tuple[CavityFill, ...]:
        """Every fill in this layer's bay, interior -> exterior; empty for an open bay.

        The single accessor for ``cavity``, which is one of three things: ``None``, one
        ``CavityFill``, or a tuple of them (flash-and-batt). Consumers walk this instead of
        the field so that "is there insulation in this bay", "what does the bay cost" and
        "what is the bay worth thermally" cannot disagree about a two-material bay.
        """
        if self.cavity is None:
            return ()
        if isinstance(self.cavity, CavityFill):
            return (self.cavity,)
        return tuple(self.cavity)

    @property
    def cavity_framing_factor(self) -> float:
        """The bay's framing fraction, clamped to 0..1 — 0.0 when the bay carries no fill.

        One number for the whole bay by construction: ``integrity.assembly_layers`` rejects
        a tuple whose members disagree, so reading the first is reading all of them.
        """
        fills = self.cavity_fills
        if not fills:
            return 0.0
        return min(max(fills[0].framing_factor, 0.0), 1.0)

    def cavity_thickness(self, fill: CavityFill) -> Length:
        """``fill``'s depth, defaulted to this layer's own — a bay packed solid."""
        return fill.thickness if fill.thickness is not None else self.thickness

    @property
    def cavity_filled_thickness(self) -> Length:
        """Total depth of bay this layer's fills occupy; the rest of it is still air."""
        return inch(sum(self.cavity_thickness(fill).inches
                        for fill in self.cavity_fills))


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
    ("ConcreteSpec", ConcreteSpec),
    ("FiberSpec", FiberSpec),
    ("Assembly", Assembly),
    ("AssemblyInterface", AssemblyInterface),
    ("ConstructionRule", ConstructionRule),
    ("Substitution", Substitution),
):
    register_constructor(_name, _obj)

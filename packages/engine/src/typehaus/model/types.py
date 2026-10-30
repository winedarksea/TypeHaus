"""Library types: openings, placeables, and structural product catalogs."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.built_in_bench import BENCH_ENVELOPE_TOLERANCE_M, BuiltInBenchSpec
from typehaus.model.curtain_track import CurtainTrackSpec
from typehaus.model.door_hardware import DoorHardwareItem, JambFraming
from typehaus.model.doorway import DoorwayTreatment
from typehaus.model.enums import (
    DoorOperation,
    LuminaireForm,
    RatingBasis,
    Service,
    WindowOperation,
)
from typehaus.model.exterior_door import DoorCatalogDimensions
from typehaus.model.furniture_cut import FurnitureCut
from typehaus.model.opening_size import OpeningSize
from typehaus.model.placeables import (
    ClearanceZone,
    Footprint2D,
    ModelRepresentation,
    Mount,
    PlacementStrategy,
    PlanRepresentation,
    ServicePort,
)
from typehaus.model.refs_holes import PublishedHole
from typehaus.model.registry import register_constructor
from typehaus.model.track_lighting import (
    ASSEMBLY_DIMENSION_RELATIVE_TOLERANCE,
    ASSEMBLY_DIMENSION_TOLERANCE_M,
    TrackLightingSpec,
)
from typehaus.quantities import Length, UFactor, m


class BookcaseDoorSpec(HausModel):
    """Published dimensions for a factory bookcase door.

    ``DoorType.width``/``height`` are its nominal leaf and ``DoorType.rough_opening`` the
    maker's RO, as for any door; this record holds the cabinet and its clearances.
    """

    body_width: Length
    body_height: Length
    body_depth: Length
    casing_overall_width: Length
    clear_passage_width: Length
    hinge_side_clearance: Length
    # How far the field-applied casing laps the face frame: legs and head alike. The derived
    # house casing (``interior_trim_casing``) stands its inner edge here, not at the RO.
    casing_lap: Length
    # Catalog wood used for the visible cabinet boards; selects both color and the 3D board
    # finish in the viewer. A factory finish can omit this where no house material is chosen.
    material_ref: str | None = None
    # The shelf face: its face frame is flush with this face's finish, the body runs back
    # through the opening, and only this face is cased. A placement datum, not a claim
    # about the hinge/pivot axis or opening sweep.
    mounting_face: Literal["negative_normal", "positive_normal"] = "negative_normal"
    source: str


class DoorType(HausModel):
    """A door product type. Drives schedules, energy checks, and opening appearance."""

    catalog_dimensions: DoorCatalogDimensions | None = None
    # A product's PUBLISHED rough opening. None derives it from the leaf and the house's
    # ``TrimStandard`` (``resolve/door_sizing``).
    rough_opening: OpeningSize | None = None
    # An authored clear passage width; overrides both the published and estimated figure.
    clear_passage: Length | None = None
    # A fixed centre post or mullion between a pair's leaves: only the active leaf is clear.
    center_post: bool = False
    hardware: tuple[DoorHardwareItem, ...] = ()
    jamb_framing: JambFraming | None = None
    field_finish: tuple[str, str] | None = None
    doorway: DoorwayTreatment | None = None
    tag: str
    # The NOMINAL leaf, as ordered (a pair counts as one width). An overhead door is
    # ordered by its opening, so for it these are the RO.
    width: Length
    height: Length
    u_factor: UFactor | None = None
    # A glazed door is *fenestration* under R202, so it admits solar gain exactly as a window
    # does and the block load has to see it. Same semantics as ``WindowType.shgc``/``vt``;
    # meaningful only where ``glazed`` is true.
    shgc: float | None = None  # solar heat gain coefficient
    vt: float | None = None  # visible transmittance
    operation: DoorOperation = DoorOperation.SWING
    exterior: bool = False
    # A glazed leaf is transparent in 3D exports and the live viewer. Kept separate from
    # operation because a swinging, sliding, or French door can each be glazed.
    glazed: bool = False
    # No applied casing — drywall return jamb: the gwb wraps into the opening and dies
    # against a concealed jamb, so 3D exports and the live viewer draw no frame boxes.
    trimless: bool = False
    # Where a trimless leaf sits in the jamb depth: "pull" is flush with the face it swings
    # toward (EzyJamb-type); "push" is set at the far face of a full-depth jamb, behind a
    # rebated stop, so an in-swing door reads near-flush on the side it is pushed from.
    leaf_set: Literal["pull", "push"] = "pull"
    # Surface appearance only; None inherits the type/product default.
    frame_material_ref: str | None = None
    leaf_material_ref: str | None = None
    # Type-level engineered-header default (e.g. '2-ply 14" LVL') for openings wide enough
    # that the solver's dimensional-lumber header tables don't apply; a Door instance's
    # own header_spec wins over this.
    header_spec: str | None = None
    # Type-level ALLOWABLE HOLES chart for the header this type's openings get, where the
    # header product is a property of the type rather than of one door. A Door instance's
    # own published_hole wins over this. See ``model/refs.PublishedHole``.
    published_hole: PublishedHole | None = None
    # A purchased bookshelf/Murphy door.  Its closed cabinet, face frame and casing are
    # real product geometry; its clearance is published installation information only.
    bookcase_door: BookcaseDoorSpec | None = None
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
    # What this leaf is BOUGHT as, which is what its hardware costs: a lockset's price is a
    # function of its function, not of its size. "passage" is a latch with no lock, "privacy"
    # a push-button bath/bedroom set, "entry" a keyed exterior set (plus a deadbolt),
    # "pocket_privacy" the mechanism-plus-two-pulls a pocket door needs and no plate ever
    # covers, "closet" a dummy knob or a bifold/bypass's own track hardware, and "overhead" a
    # sectional door, whose only hardware is its operator. Declared rather than inferred: the
    # operation says a leaf CAN be locked, never whether it is.
    #
    # It sits on the TYPE because that is what a hardware allowance is bought by — one order
    # of one set per type. The same commodity leaf hung at a bath and at a study is two
    # functions and one type: a house that prices them apart splits the type, and a catalog
    # type that cannot know leaves this None. None means not stated, and an allowance driven
    # off this field simply does not select the row.
    function: Literal["entry", "passage", "privacy", "pocket_privacy", "closet",
                      "garage_man_door", "overhead"] | None = None
    # The CATALOG FAMILY a pocket's frame kit is bought from (e.g. "eclisse"); the host wall's
    # depth picks the kit within it. None is the commodity ladder (Johnson / Cavity Sliders).
    # A family may publish its own rough opening, so it moves the framing as well as the BOM.
    pocket_frame: str | None = None
    # The chosen product, by ``Product.tag`` — see ``FurnitureType.product_ref``.
    product_ref: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def _unit_fits_its_published_rough_opening(self) -> DoorType:
        """Decision #96: a published RO must take the unit (or leaf) plus its shims.
        A derived RO fits by construction, and a held one lives on the Door, exempt."""
        from typehaus.model.opening_size import FIT_TOLERANCE_M, PREHUNG_SHIM_M

        ro = self.rough_opening
        if ro is None or self.operation == DoorOperation.OVERHEAD:
            return self
        catalog = self.catalog_dimensions
        unit_w = catalog.unit_width.meters if catalog else self.width.meters
        unit_h = catalog.unit_height.meters if catalog else self.height.meters
        if (unit_w + 2 * PREHUNG_SHIM_M > ro.width.meters + FIT_TOLERANCE_M
                or unit_h + PREHUNG_SHIM_M > ro.height.meters + FIT_TOLERANCE_M):
            what = "unit" if catalog else "leaf"
            raise ValueError(
                f"{self.tag}: the {unit_w / 0.0254:g} x {unit_h / 0.0254:g} in {what} does not "
                f"fit its published {ro.width.inches:g} x {ro.height.inches:g} in rough "
                "opening with 1/4 in of shim a side")
        return self

    @model_validator(mode="after")
    def _push_set_is_trimless(self) -> DoorType:
        if self.leaf_set == "push" and not self.trimless:
            raise ValueError(f"{self.tag}: leaf_set='push' describes a trimless jamb; "
                             "set trimless=True")
        return self


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
    # Frame depth — the unit's jamb dimension, front of frame to back. A house whose windows
    # are *outie* derives the mount plane from the wall (notes/outie_window_truss_detail.md:
    # "no window in this house carries a depth dimension"), which fixes where the OUTSIDE of
    # the frame lands and says nothing about where the inside does. That difference is the
    # interior return the stool has to cover, so a derived ``WindowStool`` depth cannot be
    # computed without it. None means not authored: the stool reports UNKNOWN and carries no
    # depth rather than guessing one (#32).
    frame_depth: Length | None = None
    # The maker's published NET clear opening (R310.2.1), sash open in normal operation.
    # Selected products need exact openings or deductions below to receive R310 credit.
    net_clear_width: Length | None = None
    net_clear_height: Length | None = None
    # Manufacturer deductions from the resolved frame, for custom sizes. Exact published
    # openings above and sizing formulas are alternative contracts on each axis.
    net_clear_width_deduction: Length | None = None
    net_clear_height_deduction: Length | None = None
    # Orderable custom sizes: the unit rounds DOWN to this step inside its flashed opening,
    # which must exceed the unit by at least the allowance (total, per dimension).
    frame_size_increment: Length | None = None
    minimum_rough_opening_allowance: Length | None = None
    # The chosen product, by ``Product.tag`` — see ``FurnitureType.product_ref``.
    product_ref: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def _validate_clear_opening_dimensions(self) -> WindowType:
        for axis in ("width", "height"):
            exact = getattr(self, f"net_clear_{axis}")
            deduction = getattr(self, f"net_clear_{axis}_deduction")
            if exact is not None and deduction is not None:
                raise ValueError(f"{self.tag}: state net clear {axis} or its deduction, not both")
            if deduction is not None and (not math.isfinite(deduction.meters)
                                          or deduction.meters < 0):
                raise ValueError(f"{self.tag}: net clear {axis} deduction must be nonnegative")
        step, allowance = self.frame_size_increment, self.minimum_rough_opening_allowance
        if step is not None and not (math.isfinite(step.meters) and step.meters > 0):
            raise ValueError(f"{self.tag}: frame size increment must be positive")
        if allowance is not None and not (math.isfinite(allowance.meters)
                                          and allowance.meters >= 0):
            raise ValueError(f"{self.tag}: rough opening allowance must be nonnegative")
        return self


class MeshRef(HausModel):
    """Reference to a .glb sidecar under the house dir (written by `haus import`, #49)."""

    path: str


class BuiltInBookcaseBay(HausModel):
    """One clear opening in a fitted, stepped bookcase run."""

    clear_width: Length
    height: Length
    horizontal_board_count: int
    # A fixed carcass-thickness front panel closing the bay from the floor to here (the
    # underside of its lowest board): the boards distribute above it, none below.
    closed_base_height: Length = m(0)

    @model_validator(mode="after")
    def _has_usable_geometry(self) -> BuiltInBookcaseBay:
        if self.clear_width.meters <= 0 or self.height.meters <= 0:
            raise ValueError("built-in bookcase bay width and height must be positive")
        if self.horizontal_board_count < 2:
            raise ValueError("built-in bookcase bay needs a base and top board")
        if not 0 <= self.closed_base_height.meters < self.height.meters:
            raise ValueError("built-in bookcase closed base must lie inside the bay height")
        return self


class BuiltInBookcaseSpec(HausModel):
    """Explicit fabrication geometry for fitted open bookcases, optionally closed at the base.

    ``FurnitureType.footprint`` remains the placement and collision envelope.  This spec
    describes the boards inside it so sheets, GLB, and IFC do not reduce fitted work to a
    generic box.
    """

    bays: tuple[BuiltInBookcaseBay, ...]
    shelf_depth: Length
    horizontal_board_thickness: Length
    divider_thickness: Length
    back_thickness: Length
    # Fixed closure between the first end divider and an adjacent return wall. It belongs
    # to the one fabricated Furniture occurrence but is not a shelf bay or shared divider.
    west_filler_width: Length = m(0)
    # Sheet goods behind the furniture's named wood fronts. Zero trim dimensions keep
    # the original solid-board construction for bookcases without applied fronts.
    panel_material_ref: str | None = None
    shelf_nosing_depth: Length = m(0)
    shelf_nosing_height: Length = m(0)
    face_strip_width: Length = m(0)

    @model_validator(mode="after")
    def _has_usable_geometry(self) -> BuiltInBookcaseSpec:
        if not self.bays:
            raise ValueError("built-in bookcase needs at least one bay")
        if any(value.meters <= 0 for value in (
            self.shelf_depth, self.horizontal_board_thickness,
            self.divider_thickness, self.back_thickness,
        )):
            raise ValueError("built-in bookcase thicknesses and shelf depth must be positive")
        if self.west_filler_width.meters < 0:
            raise ValueError("built-in bookcase west filler width cannot be negative")
        trim = (self.shelf_nosing_depth.meters, self.shelf_nosing_height.meters,
                self.face_strip_width.meters)
        if any(value < 0 for value in trim) or (any(trim) and not all(trim)):
            raise ValueError("bookcase front dimensions must all be positive or all zero")
        if all(trim):
            depth, height, width = trim
            if depth >= self.shelf_depth.meters or height < self.horizontal_board_thickness.meters:
                raise ValueError("bookcase nosing must fit its shelf depth and cover its thickness")
            if width < self.divider_thickness.meters or any(
                bay.clear_width.meters <= 2 * (width - self.divider_thickness.meters)
                for bay in self.bays
            ):
                raise ValueError("bookcase face strips must cover dividers and leave open bays")
        if any(bay.height.meters - bay.closed_base_height.meters
               < self.horizontal_board_thickness.meters for bay in self.bays):
            raise ValueError("built-in bookcase bay is shorter than its boards")
        return self


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
    # How deep the CARCASS is, where that is less than the footprint depth. An island or a
    # peninsula is drawn as one rectangle because that is what it occupies in plan, but only
    # part of that depth is box: the rest is knee space with a cantilevered top over it. The
    # footprint alone cannot tell the two apart, and ``advisory.countertop_overhang`` needs
    # exactly that split — without it a 39" top on a 24" box reads as fully supported and a
    # cantilever nobody may build silently passes.
    #
    # ``None`` means "the carcass IS the footprint", which is true of every base cabinet in a
    # run against a wall; a consumer reads ``footprint[1]`` in that case.
    carcass_depth: Length | None = None
    mesh: MeshRef | None = None
    # The chosen product, by ``Product.tag`` (model/product.py). A type is a
    # *specification* — the width the run is cut to, the circuit the electrician pulls —
    # and stays one when nobody has picked a brand yet; naming a product records that the
    # pick has been made, without moving a dimension. Identity only, never a price (#28).
    product_ref: str | None = None
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
    # Mounting-post centres: local (width offset, height above body base), on the back
    # plane (+depth/2). Final screw drilling follows the manufacturer's template.
    wall_fixing_points: tuple[tuple[Length, Length], ...] = ()
    # Names a generated glyph + massing from ``model/placeable_symbols`` (see SYMBOL_NAMES).
    # An imported ``plan_representation``/``model_representation`` still wins over it.
    plan_symbol: str | None = None
    # ``None`` is ordinary catalog furniture.  A value makes this a fitted, generated
    # assembly: exact board geometry is shared by drawings, browser, GLB, and IFC.
    built_in_bookcase: BuiltInBookcaseSpec | None = None
    built_in_bench: BuiltInBenchSpec | None = None
    # A curtain track: the envelope is the CLOSED curtain, the model draws it open.
    curtain_track: CurtainTrackSpec | None = None
    # The catalog ``Material`` its generic ``wood`` parts are made of (a shelf, a side, every
    # board of a built-in, or a sauna symbol's seat/supports). Colour and 3D texture follow
    # that material; ``wood-dark`` backs keep their shadow tone. ``None`` draws generic wood.
    wood_material_ref: str | None = None
    # Owner-built: the parts a mill cuts per placed piece (model/furniture_cut.py).
    cut_list: tuple[FurnitureCut, ...] = ()

    @model_validator(mode="after")
    def _curtain_track_fits(self) -> FurnitureType:
        if self.curtain_track is not None:
            self.curtain_track.check_fits(self.footprint[0].meters, self.footprint[1].meters)
        return self

    @model_validator(mode="after")
    def _bench_envelope_matches(self) -> FurnitureType:
        bench = self.built_in_bench
        if bench is not None:
            if self.built_in_bookcase is not None or self.mesh is not None or self.cut_list:
                raise ValueError("bench owns its geometry and cut list; no other fabrication")
            expected = (bench.width.meters, bench.overall_depth_m, bench.back_height.meters)
            actual = (*(v.meters for v in self.footprint), self.height.meters)
            if any(abs(a - b) > BENCH_ENVELOPE_TOLERANCE_M
                   for a, b in zip(actual, expected, strict=True)):
                raise ValueError("bench footprint/height must match its fabrication envelope")
        return self


class RailingType(HausModel):
    """A railing product identity, separate from its resolved guard geometry.

    The three ``*_material`` refs are *product* defaults for the parts a guard is built
    from; a ``Railing`` instance's own field wins over them, and where neither is authored
    the part keeps today's assembly-driven colour (→ resolve/railings/parts.py).

    The three dimensions below are product facts no code rule fixes — R312.1.3 constrains
    the *gap*, never the picket. They are :class:`Length`, not nominal strings, because
    dressed-lumber arithmetic (2" nominal → 1.5" actual) is a lumber convention a 3/4"
    extruded aluminium picket does not obey.
    """

    tag: str
    name: str
    mesh: MeshRef | None = None
    post_material: str | None = None
    rail_material: str | None = None
    infill_material: str | None = None
    baluster_width: Length | None = None   # picket cross-section, square
    cable_diameter: Length | None = None   # tensioned cable, e.g. 3/16"
    panel_thickness: Length | None = None  # lite / sheet thickness
    # Safety glazing in a glass infill. Mirrors ``WindowType.tempered`` / ``DoorType
    # .tempered``: geometry cannot know what was ordered, so the product states it. This
    # is what R308.4.4 (structural glass balusters) reads; ``None`` means "not stated",
    # which that rule reports as UNKNOWN rather than as a deficiency.
    glazing: Literal["tempered", "laminated", "laminated-tempered"] | None = None
    # A round rail's outside diameter. Wins over any size in ``graspable_profile``.
    rail_diameter: Length | None = None
    # The length the rail stock comes in; a longer run is spliced (take-off counts them).
    stock_length: Length | None = None
    # The product's largest span between supports along the rail (R301.5's 200 lb load).
    bracket_spacing_max: Length | None = None
    # Fascia-mount bracket plate, drawn at each post of a ``mount="fascia"`` guard. Height is
    # the product's; width and projection are None until read off its drawing.
    fascia_bracket_height: Length | None = None
    fascia_bracket_width: Length | None = None
    fascia_bracket_projection: Length | None = None
    # The chosen product, by ``Product.tag`` — see ``FurnitureType.product_ref``.
    product_ref: str | None = None
    source: str | None = None


class FixturePart(HausModel):
    """A separately procured component, counted for each placed fixture."""

    role: Literal["basin", "faucet", "trap", "top", "drain"]
    product_ref: str
    quantity: int = Field(default=1, gt=0)


class FixtureType(HausModel):
    """A plumbing/equipment fixture type — needs services, has clearances (M3)."""

    tag: str
    name: str
    footprint: tuple[Length, Length]
    height: Length
    needs: frozenset[Service] = frozenset()
    clearance: tuple[Length, Length, Length, Length] | None = None
    # The chosen product, by ``Product.tag`` — see ``FurnitureType.product_ref``.
    parts: tuple[FixturePart, ...] = ()
    product_ref: str | None = None
    source: str | None = None
    import_provenance: dict[str, object] | None = None
    placement: PlacementStrategy = PlacementStrategy.FREE_PLACED
    footprint_shape: Footprint2D | None = None
    # Finished counter opening in the fixture's local frame, separate from its flange
    # and faucet installation envelope. Countertop.cutouts follows the placed fixture.
    countertop_cutout: Footprint2D | None = None
    # Solid cabinet sides below an overhanging purchased top, in the type's local frame.
    # Cabinet-mounted accessories fasten to these faces, not to the ceramic/quartz envelope.
    cabinet_body_footprint: Footprint2D | None = None
    clearances: tuple[ClearanceZone, ...] = ()
    ports: tuple[ServicePort, ...] = ()
    plan_representation: PlanRepresentation | None = None
    model_representation: ModelRepresentation | None = None
    mount: Mount = Mount()
    plan_symbol: str | None = None
    # True when the product's own hardware already satisfies P2902.3.1's hose-thread
    # backflow protection (a wall hydrant with a built-in anti-siphon vacuum breaker, e.g.
    # a Woodford Model 19) — as opposed to a hydrant whose thread is bare and needs a
    # separate screw-on `PipeAccessory(kind=VACUUM_BREAKER)` (a Y-pattern yard hydrant).
    # Declared rather than inferred, same reason as `ApplianceType.quick_closing`: nothing
    # in a hydrant's geometry says which kind it is. Checks that key on it must stop the
    # plan from also authoring a redundant accessory for the same device, which would bill
    # a part the fixture's own price already includes.
    integral_vacuum_breaker: bool = False
    # Clear framing bay a concealed in-wall carrier needs, between the flanking studs, for a
    # fixture whose ``mount.kind`` is WALL. ``None`` — the default, and true of every
    # fixture that simply hangs off a finished wall — means "no frame in the wall", and the
    # framing solver lays its module out as usual. A value makes the bay a first-class
    # keepout: ``resolve/framing/carriers.py`` parts the module studs around it and frames
    # it. Declared rather than inferred, same reason as ``integral_vacuum_breaker``:
    # nothing in a bowl's footprint says whether there is a frame behind it.
    carrier_bay_width: Length | None = None
    # Does this fixture present a LAVATORY BASIN — the thing NEC 210.52(D) / IRC E3901.6
    # measures its 36" from, and the thing 210.52(C) deliberately does not reach. True on a
    # lavatory or a vanity that holds one, False on a water closet, a tub or a shower.
    # Declared rather than inferred, same reason as ``integral_vacuum_breaker``: the check
    # used to read ``plan_symbol``, a DRAWING vocabulary, so a product drawn with a symbol
    # nobody had listed silently left the rule's scope. None means not stated: the check
    # falls back to the symbol and reports UNKNOWN where the symbol answers neither way.
    basin: bool | None = None


class ApplianceType(FurnitureType):
    """A product requiring services but not a plumbing fixture (for example a washer)."""

    needs: frozenset[Service] = frozenset()
    # A listed condensing (ductless) appliance — the heat-pump dryer that throws its moisture
    # down a condensate line instead of out a wall. M1502.1 exempts exactly these from the
    # whole of M1502, and there is no other way to tell one from a vented dryer: both are
    # 28x40 boxes named "dryer" with a 240V port. False is the safe default — an unstated
    # dryer is a vented dryer and owes the code a duct.
    ductless: bool = False
    # A solenoid or other fast-acting supply valve — the thing P2903.5 requires a
    # water-hammer arrestor for. A washer and a dishwasher both have one; a refrigerator's
    # ice-maker line usually does too. Declared rather than inferred for the same reason
    # ``ductless`` is: "washer" in a product name is a naming convention, and a check that
    # keyed on one would silently stop applying the day a product was renamed.
    quick_closing: bool = False


class AirHandlingProductFacts(HausModel):
    """Product facts an air-side part carries that decide how it is *serviced*.

    A mixin rather than fields on ``FurnitureType`` because a bookcase has no filter, and
    rather than fields on ``EquipmentType`` alone because in this house the filter is not in
    the machine: the air handler hung in a soffit has no filter cabinet, and the only filter
    in System 1 lives behind ``REG-T-HP-RET``'s hinged face. The part that carries the filter
    is a *register* and the part that is opened to reach it is the same register, so the
    facts have to be sayable of both families or they have nowhere to live.

    All three are documentation the schedules and the O&M sheet print. Nothing grades them,
    deliberately: a rule that decides whether a filter can be *reached* needs a swing
    envelope and a standing position, which this model does not have, and a MERV rule needs
    a design pressure drop the catalog does not state.
    """

    #: Nominal filter size as it is ordered, e.g. ``"28x12x1"``. A string and not three
    #: Lengths: it is a purchased size off a shelf, and 20x25x1 is one SKU, not a rectangle.
    filter_nominal_size: str | None = None
    #: ASHRAE 52.2 MERV of the filter this part is specified with.
    filter_merv: int | None = None
    #: Which face of the part is opened to service it, in the type's own local frame — the
    #: same frame ``ServicePort.position`` and the plan symbols use, ``+y`` toward the back.
    #: A ceiling grille's hinged face is ``"bottom"``; a cabinet's door is ``"front"``.
    service_face: Literal["front", "back", "left", "right", "top", "bottom"] | None = None
    #: Measured static loss across this part, as ``((cfm, Pa), ...)`` ascending in cfm —
    #: a plenum, a balancing damper, a diffuser, a transition. Pascals and not inches w.g.
    #: because that is the unit every European and most North American component sheets
    #: publish a component loss in; the fan curve is in inches w.g. because that is the
    #: unit ITS sheet publishes. Two units, each the one its source states, converted once
    #: where they meet. Empty means the sheet does not state one, and the static budget
    #: reports the gap rather than inventing a K-factor.
    static_loss_pa_at_cfm: tuple[tuple[float, float], ...] = ()


class HeatPumpRating(HausModel):
    """One row of a heat pump's published heating-capacity table.

    **The defect this closes.** ``EquipmentType`` carried two scalars,
    ``heating_capacity_btuh`` (the 47 °F rating) and ``heating_capacity_at_design_btuh``, and
    the catalog's own preamble said the quiet part out loud: *"the engine does no curve
    interpolation itself, so whatever is authored here IS the machine as far as every check
    is concerned."* A scalar cannot express what a modulating heat pump actually does, and
    two things fell through the gap:

    * **Turn-down.** An inverter's MINIMUM output rises as it gets colder — the FLEXX Ultra
      goes 10,800 Btu/h at 47 °F to 14,000 at 5 °F — while the zone load falls. catlin's
      System 1 zone wants 4,056 Btu/h at 47 °F against a 10,800 Btu/h floor: it short-cycles
      through most of the heating season, and the check PASSed with "+7,163 Btu/h margin"
      because a single at-design scalar cannot see a minimum at all.
    * **Staleness.** *At design* depends on ``Site.design_temp_heating``, which an
      ``EquipmentType`` has never known. Move the house and the authored scalar is silently
      a number for the wrong site. ``takeoff/hvac.capacity_at`` now reads the table at the
      site's own design temperature (→ decision #76).

    **Cooling stays out of this table, deliberately.** No document publishes heating and
    cooling on one row: a manufacturer's extended ratings give heating against outdoor
    dry-bulb at a stated return temperature, and cooling against a different outdoor
    dry-bulb at a stated indoor wet-bulb. One row carrying both would be two reads pretending
    to be one.
    """

    #: The key, and the table must be strictly ascending in it.
    outdoor_db_f: float
    #: The three capacity columns a modulating unit publishes, Btu/h. A single-stage unit
    #: states ``minimum == rated == maximum``, which is a true statement about it and is what
    #: earns the turndown check its NOT_APPLICABLE. At least one must be stated: a row with
    #: no capacity at all is a temperature with nothing to say.
    minimum_btuh: float | None = None
    rated_btuh: float | None = None
    maximum_btuh: float | None = None
    #: COP at each of those three levels, where the document gives it. A COP for a level
    #: whose capacity is absent is refused: it describes an operating point the row does not
    #: claim exists.
    cop_at_minimum: float | None = None
    cop_at_rated: float | None = None
    cop_at_maximum: float | None = None
    #: The indoor return dry-bulb the row was measured at. Capacity moves with it, and two
    #: tables read at different returns are not comparable — 70 °F is the usual residential
    #: heating condition and the one every figure in catlin's catalog is read at.
    return_db_f: float | None = None
    #: Where the row came from. See :class:`RatingBasis`.
    basis: RatingBasis = RatingBasis.MANUFACTURER
    #: **Required, and it is the whole point.** A capacity with no provenance is the defect
    #: this class exists to close: name the document, the model number, the page or table,
    #: and — when sources disagree at this temperature — what the other one said and why
    #: this row is the one the house sizes against.
    citation: str


class EquipmentType(FurnitureType, AirHandlingProductFacts):
    needs: frozenset[Service] = frozenset()
    #: The published heating-capacity table, ascending in ``outdoor_db_f`` (→
    #: :class:`HeatPumpRating`). This REPLACES the two scalars that were here —
    #: ``heating_capacity_btuh`` (the 47 °F rating) and ``heating_capacity_at_design_btuh``
    #: — with no back-compatibility shim, because a shim would let a house keep authoring
    #: the defect. Empty means the type publishes no table, and the sizing checks say so
    #: rather than assuming one.
    heating_ratings: tuple[HeatPumpRating, ...] = ()
    #: Electric resistance heat this unit can add, Btu/h. A SCALAR and not a table, and that
    #: is physics rather than a simplification: a resistance element's output is flat with
    #: outdoor temperature. A strip heater in a cabinet that can interlock it, an aux kit,
    #: a baseboard.
    resistance_heating_btuh: float | None = None
    #: The outdoor temperature above which the control locks the resistance heat OUT — the
    #: thermostat setting that stops a heat pump's aux stage running when the compressor
    #: could carry the load alone. ``None`` means no lockout is configured, so the aux heat
    #: is available at every temperature.
    #:
    #: This is what makes the heat kit's at-design contribution DERIVED rather than a
    #: hand-computed zero: at a −15 °F design temperature a kit locked out above −22 °F
    #: contributes nothing, and the engine can now say so instead of the catalog asserting
    #: it. Move the site and the answer moves with it.
    aux_lockout_above_f: float | None = None
    # Rated sensible cooling output (Btu/h at the AHRI 95 °F point). Advisory only: the
    # block load's cooling side is a UA + solar sum, not a Manual J latent split.
    cooling_capacity_btuh: float | None = None
    # Ventilation equipment (ERV/HRV) only: the continuous balanced airflow it moves, and
    # the datasheet sensible recovery effectiveness (0..1) at that flow. Both feed the
    # ventilation term of the block load — never defaulted, because a guessed SRE moves
    # the load by thousands of Btu/h.
    ventilation_cfm: float | None = None
    sensible_recovery_effectiveness: float | None = None
    #: The published fan curve, as ``((static in. w.g., net cfm), ...)`` — the whole table a
    #: ventilator's spec sheet prints, not the one point its model number is named for.
    #: ``ventilation_cfm`` is the DESIGN intent; this is what the machine can actually do
    #: against the duct system it was given, and ``mep.erv_static_budget`` interpolates it.
    #: Strictly increasing in static and non-increasing in cfm — a curve that rises with
    #: static is a transcription error, and the validator below refuses it at load time.
    fan_curve: tuple[tuple[float, float], ...] = ()
    #: The static past which the manufacturer will not operate the machine at all — a hard
    #: ceiling, distinct from the last point on the curve. The Broan B210E75RT's core
    #: deforms above 1.3 in. w.g., which is a different kind of statement from "the curve
    #: stops here", and a budget that merely ran off the end of the table would understate it.
    fan_curve_max_static_in_wg: float | None = None
    #: Distribution plenums (``EquipmentKind.DUCT_MANIFOLD``): how many branch ports the
    #: part is fabricated with, and their diameter. ``mep.erv_manifold_ports`` counts the
    #: runs landing in the part against this, which is what turns "10 of 10" from a comment
    #: into a verdict. Never inferred from the type name.
    #:
    #: **A COUNT is a weaker statement than a layout, and both are expressible.** A type may
    #: also state where each collar is, and it does so with no new field: a **collar** is a
    #: ``ServicePort`` that is ``EXACT`` and whose ``section_m()`` is ``port_diameter`` in
    #: both directions. The trunk port is not one — ``library/hvac.py`` gives it no section
    #: at all — so the two are told apart by what the product says rather than by a tag
    #: convention. Where collars are stated ``mep.erv_manifold_ports`` grades each radial
    #: against the collar it lands on, and :meth:`_check_collars` below holds the two
    #: statements to each other.
    duct_ports: int | None = None
    port_diameter: Length | None = None
    # Lowest outdoor temperature the unit is rated to operate at (cold-climate heat pumps).
    # Compared against the site heating design temperature by the HVAC schedule.
    min_operating_temp_f: float | None = None
    # Rated seasonal efficiencies, as the datasheet publishes them — the three numbers the
    # MN energy certificate posted at the panel has a line for. HSPF2/SEER2 are the AHRI
    # 210/240-2023 ratings (a 2023-and-later heat pump publishes these, not HSPF/SEER);
    # AFUE is the combustion equivalent. Never derived from one another and never defaulted:
    # a certificate that states an efficiency nobody measured is worse than one that says
    # "not modelled".
    hspf2: float | None = None
    seer2: float | None = None
    afue: float | None = None
    # True for resistance heat that *supplements* a zone rather than carrying it: an electric
    # fireplace, a radiant mat. It never claims a zone of its own however it is rated — but
    # its output does count toward the zone that contains its room, because at design temp
    # it is real heat the heat pump doesn't have to make.
    supplemental_heat: bool = False
    # --- Energy storage (BATTERY kinds) ------------------------------------------------
    # Usable energy of one module, kWh. The R327.5 capacity check sums this per unit and
    # in aggregate; the autonomy calc divides it by the tier draw.
    storage_kwh: float | None = None
    # Listed and labeled to UL 9540 (IRC R327.2). Declared, never inferred: no product
    # name or capacity implies a listing, and an unlisted battery must read as unlisted
    # rather than as a gap in the model.
    ul_9540_listed: bool = False
    # --- Hybrid inverter (INVERTER kinds) ----------------------------------------------
    # Continuous AC output, kW — the ceiling the simultaneous backup load is checked
    # against. Note this is NOT the product's name plate PV number (the EG4 "12kPV" puts
    # 8 kW out and takes 12 kW of PV in).
    inverter_kw_continuous: float | None = None
    # Short-duration output ceiling, kW, for motor starting (the datasheet's largest surge
    # step). The autonomy calc compares a compressor's locked-rotor start against it.
    inverter_kw_surge: float | None = None
    # Maximum PV array the inverter accepts, kW DC.
    pv_input_kw: float | None = None

    @model_validator(mode="after")
    def _check_heating_ratings(self) -> EquipmentType:
        """A ratings table is refused at load time, for ``_check_fan_curve``'s reason.

        The ways a transcribed table goes wrong — rows out of order, a repeated
        temperature, a COP for a level with no capacity, a minimum above a maximum — are
        facts about the TYPING, not about the building, so they are not findings a check
        could report. A capacity interpolated through them returns a plausible number that
        means nothing.

        **Monotonicity in temperature is deliberately NOT checked**, and someone will try to
        add it. ``EQ-T-GREE-SAPPHIRE-9-OD`` publishes 8,900 Btu/h at 17 °F and **11,500 at
        5 °F**: capacity RISING as it gets colder. That is not a transcription error, it is a
        real boosted low-ambient map — the compressor is allowed to overspeed below a
        threshold — and several cold-climate units publish one. A monotonicity rule would
        refuse the machine this house actually bought.
        """
        rows = self.heating_ratings
        if not rows:
            return self
        if len(rows) < 2:
            raise ValueError(f"{self.tag}: heating_ratings needs at least two rows to read "
                             "a capacity between; one row is a rating, not a table")
        for previous, row in zip(rows, rows[1:], strict=False):
            if row.outdoor_db_f <= previous.outdoor_db_f:
                raise ValueError(
                    f"{self.tag}: heating_ratings outdoor_db_f must strictly increase; "
                    f"{row.outdoor_db_f} follows {previous.outdoor_db_f}")
        for row in rows:
            levels = (row.minimum_btuh, row.rated_btuh, row.maximum_btuh)
            if all(value is None for value in levels):
                raise ValueError(
                    f"{self.tag}: heating_ratings row at {row.outdoor_db_f} °F states no "
                    "capacity at all — a temperature with nothing to say is not a row")
            stated = [value for value in levels if value is not None]
            if any(value <= 0 for value in stated):
                raise ValueError(
                    f"{self.tag}: heating_ratings row at {row.outdoor_db_f} °F states a "
                    "non-positive capacity")
            ordered = [(row.minimum_btuh, row.rated_btuh), (row.rated_btuh, row.maximum_btuh),
                       (row.minimum_btuh, row.maximum_btuh)]
            for low, high in ordered:
                if low is not None and high is not None and low > high:
                    raise ValueError(
                        f"{self.tag}: heating_ratings row at {row.outdoor_db_f} °F has "
                        f"minimum <= rated <= maximum violated ({low} > {high})")
            for capacity, cop, level in ((row.minimum_btuh, row.cop_at_minimum, "minimum"),
                                         (row.rated_btuh, row.cop_at_rated, "rated"),
                                         (row.maximum_btuh, row.cop_at_maximum, "maximum")):
                if cop is None:
                    continue
                if cop <= 0:
                    raise ValueError(f"{self.tag}: heating_ratings COP at {level} must be "
                                     f"> 0 ({cop} at {row.outdoor_db_f} °F)")
                if capacity is None:
                    raise ValueError(
                        f"{self.tag}: heating_ratings row at {row.outdoor_db_f} °F states a "
                        f"COP at {level} but no {level} capacity — a COP describes an "
                        "operating point, and the row does not claim that one exists")
        return self

    @model_validator(mode="after")
    def _check_fan_curve(self) -> EquipmentType:
        """A fan curve is refused at load time rather than graded, and the reason is scope.

        Every other datasheet field here is a single number nobody can mistranscribe into
        something self-contradictory. A curve is a table, and the two ways it goes wrong —
        points out of order, cfm RISING with static — are not facts about the building that
        a ``Finding`` could report. They are facts about the typing, and a static budget
        interpolated through them would return a plausible number that means nothing.
        """
        curve = self.fan_curve
        if not curve:
            return self
        if len(curve) < 2:
            raise ValueError(f"{self.tag}: fan_curve needs at least two points to "
                             "interpolate between; one point is a rating, not a curve")
        for (s0, c0), (s1, c1) in zip(curve, curve[1:], strict=False):
            if s1 <= s0:
                raise ValueError(f"{self.tag}: fan_curve static must strictly increase; "
                                 f"{s1} follows {s0}")
            if c1 > c0:
                raise ValueError(f"{self.tag}: fan_curve cfm must not rise with static; "
                                 f"{c1} cfm at {s1} in. w.g. follows {c0} at {s0}")
        return self

    def collars(self) -> tuple[ServicePort, ...]:
        """The branch collars this type dimensions, in declaration order.

        A collar is an EXACT port whose section is ``port_diameter`` both ways. The trunk
        port on a plenum carries no section, so it is never one; nor is the 6" spigot on a
        machine whose ``port_diameter`` is 4". Empty where the type states a count and no
        layout, which is the undimensioned case and is not a defect — a shared catalog part
        has no shop drawing behind it (see ``library/hvac.py``).
        """
        diameter = self.port_diameter
        if diameter is None:
            return ()
        out = []
        for port in self.ports:
            if not port.is_exact():
                continue
            section = port.section_m()
            if section is None:
                continue
            if all(abs(value - diameter.meters) <= 1e-9 for value in section):
                out.append(port)
        return tuple(out)

    @model_validator(mode="after")
    def _check_collars(self) -> EquipmentType:
        """A dimensioned plenum has to agree with its own port count, and with geometry.

        Refused at load time rather than graded, for ``_check_fan_curve``'s reason: a box
        that says ten ports and draws eight is a fact about the TYPING. A check reporting it
        would be reporting a shop drawing against itself, and every census taken from it in
        the meantime would be a number that means nothing.

        Two rules, and both are about what a fabricator can actually cut:

        * the collars and ``duct_ports`` must be the same number where both are stated;
        * **no two collars of one type closer than ``port_diameter``** centre to centre. Two
          4" collars on 2" centres are one 6" hole, and a spacing rule off the diameter is
          the weakest statement that refuses it. It is deliberately not a *clearance* rule
          (a diameter of metal between them): plenums really are built with collars close
          together, and a rule this file cannot source is a rule that belongs in a check.
        """
        collars = self.collars()
        if not collars:
            return self
        if self.duct_ports is not None and len(collars) != self.duct_ports:
            raise ValueError(
                f"{self.tag}: duct_ports says {self.duct_ports} but {len(collars)} collar(s) "
                "are dimensioned on it — a count and a layout of the same part must agree")
        pitch = self.port_diameter.meters if self.port_diameter is not None else 0.0
        for index, first in enumerate(collars):
            for second in collars[index + 1:]:
                gap = max(abs(a.meters - b.meters)
                          for a, b in zip(first.position, second.position, strict=True))
                if gap < pitch - 1e-9:
                    raise ValueError(
                        f"{self.tag}: collars {first.tag} and {second.tag} are "
                        f"{gap / 0.0254:.2f}\" apart and the ports are "
                        f"{pitch / 0.0254:.2f}\" across — two collars closer than their own "
                        "diameter are one hole")
        return self


class DuctProductType(HausModel):
    """The duct itself as a purchased product: what a run is made of, and how it resists.

    A ``DuctRun`` states a *material* and a *nominal diameter* and nothing else about the
    pipe — which is right, because those two are what an estimator orders on and are exactly
    the pair ``prices.toml``'s ``[ducts]`` qualifies its rows by. What they cannot tell a
    pressure calculation is the **bore** (4" snap-lock is 4.0" inside; 4" semi-rigid
    aluminium is not) or the **roughness**, and both move friction by more than the tolerance
    of the answer. So the pair is the key and this row is the value, matched by
    ``(material, nominal_diameter)`` — one join, the same join the price uses, and a run
    whose pair names no row is reported UNKNOWN rather than given a default ε.

    **The physics is the engine's; the coefficients are the house's.** Darcy-Weisbach with
    the Colebrook friction factor is public and lives in ``checks/mep/erv_static.py``. The
    absolute roughness of galvanized steel and of semi-rigid aluminium, and the equivalent
    length of a bend, are readings off ASHRAE tables that belong to whoever authored the
    row — the same division ``PublishedSpan`` makes between a table read and a calculation.
    """

    tag: str
    name: str
    #: Matches ``DuctRun.material`` exactly (``"galvanized"``, ``"semi_rigid"``, ``"flex"``).
    material: str
    #: Matches ``DuctRun.diameter`` — the size the run is drawn and ordered at.
    nominal_diameter: Length
    #: The actual inside diameter. Friction goes as roughly the fifth power of it, so the
    #: nominal size is not close enough to stand in.
    bore_diameter: Length
    #: Absolute roughness ε, in metres, as the authoring note reads it off ASHRAE.
    roughness_m: float
    #: The most air the product is used for at the velocity the house designs to. Advisory:
    #: ``mep.erv_static_budget`` grades each radial's ``design_cfm`` against it.
    max_cfm: float | None = None
    #: Equivalent length of one 90-degree bend in this product — authored, not derived. A
    #: fitting loss is a measured coefficient, and deriving one from geometry would be the
    #: engine inventing a number its sources publish.
    bend_equivalent_length: Length | None = None
    product_ref: str | None = None
    source: str | None = None


class RegisterType(FurnitureType, AirHandlingProductFacts):
    needs: frozenset[Service] = frozenset({Service.SUPPLY_AIR})
    # A ventilation terminal (the ERV's fresh-air/stale-air grilles) rather than a
    # conditioned-air register. Same product family, different sizing basis — a ventilation
    # terminal is sized for the whole-house rate, a supply register for a heating CFM — and
    # the plan set/IFC handoff has to tell a reader which one it is looking at.
    ventilation_terminal: bool = False


class ElectricalDeviceType(FurnitureType):
    needs: frozenset[Service] = frozenset({Service.POWER_120})
    # E3905.7 / NEC 314.27(B): floor receptacles need a box listed for floor use.
    # A general receptacle listing alone does not establish that application.
    floor_box_listing: str | None = None
    # NEMA configuration (e.g. "5-20R", "14-50R") — typed data the panel schedule reads,
    # instead of parsing it out of the display name. Voltage stays derivable from ports.
    nema: str | None = None
    # Connected load in volt-amps; summed per circuit by the panel-schedule takeoff.
    load_va: float | None = None
    output_voltage: int | None = None  # DC supplies; distinct from branch voltage
    # Breaker spaces in the enclosure (panel kinds only) — what electrical.panel_spaces
    # reconciles the circuit slots against.
    spaces: int | None = None
    # Busbar rating in amps (panel kinds only). NEC 705.12(B)(3)(2) sizes the allowable
    # backfeed against the bus, not the main breaker, so the number has to be carried on
    # the type rather than assumed equal to the service size.
    bus_amps: int | None = None
    # Service ampacity (meter sockets and main-disconnect panels). Distinct from
    # ``bus_amps``: the bus is what a backfeed is measured against, this is the main
    # breaker — on a METER type the service size, on a PANEL type that panel's own main,
    # which is the term ``code.NEC_705_12_interconnection`` uses and what
    # ``electrical.panel_feeder_load`` grades the feeder demand against. A 225A-bus panel
    # behind a 200A meter is the ordinary case where bus and main differ; a Class 320
    # meter-main feeding two 200A panels is the case where meter and panel do. Before this
    # field the service size was a literal 200 inside ``takeoff/electrical.py``, so a house
    # could not state a 400A service and every plan was graded against 200A no matter what
    # it drew.
    service_amps: int | None = None
    # How a SWITCH device controls what it feeds: "dimmer" | "timer" | "smart" | None
    # (a plain toggle). Read by the lighting-controls check and printed in the E-602
    # control schedule; a product attribute, not a kind, for the same reason NEMA is.
    control: str | None = None
    # IFC export class for this product, overriding the ``DeviceKind`` map in
    # emit/ifc/mep.py::_device_ifc_classes. ``DeviceKind`` is the symbol axis and is
    # deliberately coarse — one ``DATA_OUTLET`` covers a patch enclosure, an access point and
    # a PoE camera — but those are three different IFC entities and three different Revit
    # categories, and exporting them all as one would land them there as proxies. Naming the
    # entity on the *type* means the next low-voltage product is a catalog entry, not a patch
    # to five engine maps. ``ifc_type_entity`` is the paired IfcTypeObject; left None it is
    # derived as ``ifc_entity + "Type"``, which holds for every IFC4 class used here.
    ifc_entity: str | None = None
    ifc_predefined_type: str | None = None
    ifc_type_entity: str | None = None
    # Power drawn over the data cable, where a device is fed by the PoE switch rather than
    # from a branch circuit. Distinct from ``load_va``: this load lands on the switch's
    # circuit, not the device's own (a PoE access point names no ``circuit`` at all), so a
    # per-panel ``load_va`` sum must not pick it up. E-603 totals it against the switch.
    poe_watts: float | None = None
    # Device yokes side by side, which picks the box row (→ BoxStandard). The combined and
    # quad receptacle symbols are two whatever this says.
    gangs: int = 1
    # Whether a wall-hosted instance takes a box from the house's BoxStandard. None derives
    # it from the kind: receptacles, switches and lights do, data outlets and enclosures do
    # not. False for a type that carries its own (a gasketed in-use box).
    device_box: bool | None = None


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
    # Dark-sky shielding declaration: the housing emits no light above the horizontal
    # plane (IES/IDA "full cutoff"). A product attribute like the UL listings above it —
    # ``advisory.dark_sky_lighting`` grades exterior fixtures on it.
    full_cutoff: bool = False
    # Linear forms only: the load per lineal foot a ``LightRun`` multiplies by its length
    # to get connected VA and to size its 24V supply.
    watts_per_ft: float | None = None
    # Hung forms only: the longest hang the product ships, canopy to its lowest point with
    # the cable or stem let out in full. ``height`` is the body; the resolved suspension
    # (→ resolve/suspension.py) is the cable above it, and `electrical.suspension_reach`
    # grades the two together against this.
    max_overall_height: Length | None = None
    # The canopy at the ceiling, which a cluster spreads to the width of its whole cascade.
    canopy_diameter: Length | None = None
    track_lighting: TrackLightingSpec | None = None

    @model_validator(mode="after")
    def _track_configuration(self):
        if (self.form == LuminaireForm.TRACK) != (self.track_lighting is not None):
            raise ValueError("TRACK luminaires require a track_lighting configuration")
        if self.track_lighting is not None:
            from typehaus.model.placeable_symbols._track_lighting import (
                track_bounds,
                track_dimensions,
            )

            dimensions = track_dimensions(self.track_lighting)
            actual = (self.footprint[0].meters, self.footprint[1].meters, self.height.meters)
            if any(not math.isclose(a, b, abs_tol=ASSEMBLY_DIMENSION_TOLERANCE_M,
                                    rel_tol=ASSEMBLY_DIMENSION_RELATIVE_TOLERANCE)
                   for a, b in zip(actual, dimensions, strict=True)):
                raise ValueError("Track assembly dimensions must match configured geometry")
            x0, y0, _z0, x1, y1, _z1 = track_bounds(self.track_lighting)
            expected = sorted(((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
            points = sorted(p.xy_m for p in self.footprint_shape.points) \
                if self.footprint_shape is not None else []
            if len(points) != 4 or any(not math.isclose(
                    a, b, abs_tol=ASSEMBLY_DIMENSION_TOLERANCE_M,
                    rel_tol=ASSEMBLY_DIMENSION_RELATIVE_TOLERANCE)
                                      for point, corner in zip(points, expected, strict=True)
                                      for a, b in zip(point, corner, strict=True)):
                raise ValueError("Track footprint must retain the rail midpoint and actual bounds")
            spec = self.track_lighting
            if self.watts != spec.watts or self.lumens != spec.lumens:
                raise ValueError("Track watts and lumens must be derived from configured heads")
            voltage = 24 if spec.system == "magnetic_24v" else 120
            if self.voltage != voltage or self.load_va != (None if voltage == 24 else spec.watts):
                raise ValueError("Track branch load must match its electrical system")
        return self


for _name, _obj in (
    ("DoorType", DoorType),
    ("WindowType", WindowType),
    ("FurnitureType", FurnitureType),
    ("RailingType", RailingType),
    ("FixtureType", FixtureType),
    ("FixturePart", FixturePart),
    ("ApplianceType", ApplianceType),
    ("EquipmentType", EquipmentType),
    ("HeatPumpRating", HeatPumpRating),
    ("DuctProductType", DuctProductType),
    ("RegisterType", RegisterType),
    ("ElectricalDeviceType", ElectricalDeviceType),
    ("LuminaireType", LuminaireType),
    ("MeshRef", MeshRef),
):
    register_constructor(_name, _obj)

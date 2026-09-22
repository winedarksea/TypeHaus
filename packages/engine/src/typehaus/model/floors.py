"""Two-tier floor model + soffits + radiant heat (#21, #40, #39, → 11 §Floors)."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from typehaus.model.assembly import Layer
from typehaus.model.base import Element, HausModel
from typehaus.model.enums import FloorOpeningPurpose, RadiantSystem
from typehaus.model.rebar import ReinforcementSpec
from typehaus.model.refs import Embed, PublishedSpan
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


class JoistSpec(HausModel):
    """Framing spec for a FloorSystem deck. Bearing refs are wall/beam tags."""

    member: str = "11.875 I-joist"
    spacing: Length | None = None  # o.c.; defaults to 16" at the solver
    direction: str = "x"  # "x" | "y" — joist span direction in the plan frame
    bearing_refs: tuple[str, ...] = ()
    # Overhang past the two outermost bearing lines (a balcony/porch deck cantilevers its
    # joist tips beyond the beam so the decking covers them). None = flush ends.
    cantilever: Length | None = None
    # Per-end overrides, for a deck whose two ends are not alike: the porch runs from a
    # concrete sill (flush) out over its back-beam line to the house gap (a 17" overhang),
    # and one symmetric scalar cannot say that — it either overshot the concrete wall to
    # the south or fell short of the deck edge to the north. Each defaults to ``cantilever``.
    # "start"/"end" are the low/high ends along the joist span direction.
    cantilever_start: Length | None = None
    cantilever_end: Length | None = None
    # Catalog material for the two rim (band) boards alone, when the band is a *finished*
    # face rather than framing hidden behind a skin — an exposed deck band painted with the
    # posts it sits over, say. ``None`` (the ordinary case) leaves the rims coloured by
    # category and billed on the bare profile key. It is deliberately
    # narrower than a whole-system material: the joists behind the band are still bare
    # lumber, and saying so per member is the only honest way to bill the paint.
    rim_material: str | None = None
    # The band board's own SECTION, where the derived 1 1/4" rim is not enough stick. A rim
    # under a *bearing* line is a squash block a hundred feet long: the load crossing it is
    # not the deck's own but whatever stands on the plate above — a story-and-a-half's
    # rafter plate over the attic deck, a wall stacking over a floor — and 1 1/4" of OSB
    # band has no business carrying it in crush. ``None`` keeps the derived
    # ``1.25x<depth> rim``, which is right for a band that only caps joist ends.
    #
    # Authored, not derived, and deliberately so: deciding "this rim is under a bearing
    # line" would mean the engine knowing what stacks two storeys above it, and being wrong
    # in either direction is worse than a field. The section is the engine's to carry; the
    # reason is the house's to state.
    rim_member: str | None = None
    # --- open-web panel layout (2026-09-19) --------------------------------------------
    # **What a truss's webs actually do to the slot the engine reads.**
    # ``profiles.open_web_opening_m`` gives an open-web member an 8 7/8" chord-to-chord
    # window and nothing narrows it along the span, so the engine reads the truss as a
    # CONTINUOUS SLOT: thirteen ducts crossing every truss inside a 41" band pass
    # ``mep.run_member_crossing`` without a complaint. Real trusses have webs at panel
    # points, and a duct lands in an opening or it lands on a web.
    #
    # Three numbers say the layout, all optional and all from the fabricator's drawing:
    # the centre-to-centre PITCH of the panel points, the CLEAR opening between webs
    # measured at the chord, and the OFFSET from the member's start to the first panel
    # point. State all three or none — two of them describe nothing.
    #
    # Unauthored is not a defect and must not read as one: a truss layout is a shop
    # drawing, and ``mep.open_web_panel`` reports UNKNOWN naming the floor rather than
    # inventing a pitch. What IS a defect is a house that authors them and then over-fills
    # an opening.
    web_panel_pitch: Length | None = None
    web_opening_width: Length | None = None
    web_panel_offset: Length | None = None
    # End bearing this deck's members take on a *shared* bearing line, as (ref, length)
    # pairs. A line two decks land on from opposite sides is one plate split between them,
    # and the split is a design decision, not a derivation: an open-web floor truss wants
    # 3" of seat where an I-joist wants 1 3/4", so a centreline split (2 3/4" each on a 2x6
    # plate) shorts the truss and over-serves the joist. Authoring the number here moves
    # this deck's joist ends off the ref's *near* structure face by exactly that much —
    # the face its joists approach — so the two decks' authored bearings have to add up to
    # the plate or the pair does not meet. Only a shared line reads this: an unshared end
    # bearing already runs its joists to the framing face behind the rim (resolve/floors.py
    # ``_end_coords``), and an interior line the deck spans over is not an end at all.
    end_bearing: tuple[tuple[str, Length], ...] = ()


class JoistReinforcement(HausModel):
    """Extra joist plies sistered under a concentrated load, plus solid blocking.

    A post landing mid-span — worse, out on a cantilever — is carried by one 1 1/2" joist
    unless something is added under it. Authoring the reinforcement here rather than as
    loose members keeps the *intent* ("this point load is answered") in the plan: the
    resolver derives the geometry, the take-off bills it, and
    ``structural.cantilever_point_load`` reads it as the mitigation it is.

    ``at`` is a plan point, not a joist index — the joist line nearest it is the one that
    gets the plies, so a post that moves 2" does not silently reinforce its neighbour.
    ``member`` defaults to the deck's own joist member (a sister is the same stock).
    """

    at: Point2D
    plies: int = 3  # total plies at the line, the authored joist included
    member: str | None = None  # None = the deck's own JoistSpec.member
    blocking: bool = True  # solid blocking out to the joist line on each side
    source: str | None = None


class DeckLayer(HausModel):
    material_ref: str
    thickness: Length


@register_element
class FloorOpening(Element):
    """First-class opening in a FloorSystem; referenced by tag from a Stair (#21)."""

    outline: tuple[Point2D, ...]
    purpose: FloorOpeningPurpose = FloorOpeningPurpose.STAIR
    # Authored support intent for opening edges.  The framing resolver never assumes
    # that a nearby partition can receive cut joists.
    bearing_refs: tuple[str, ...] = ()
    #: The runs this hole was framed FOR, by tag — the same field and the same statement as
    #: ``RoughOpening.penetration_for``. ``mep.riser_through_deck`` reads it: a riser
    #: standing in a deck is a defect unless a void contains it, and a void somebody framed
    #: on purpose for that run is the strongest form of saying so. A STAIR or a CHASE
    #: contains a riser geometrically and needs no names; this is for the hole that exists
    #: only because a pipe goes through it.
    penetration_for: tuple[str, ...] = ()


class FloorOpeningEdgeInterval(HausModel):
    """One low-to-high station interval on a rectangular floor-opening edge.

    The edge names deliberately use the opening box's fixed compass vocabulary.  A pocket
    closure is a narrow stair-well exception, so it must not grow a second arbitrary-line
    geometry language beside ``FloorOpening.outline``.
    """

    edge: Literal["west", "east", "south", "north"]
    start: Length
    end: Length


@register_element
class FloorOpeningPocketClosure(Element):
    """A walled, non-walkable pocket immediately beside a stair floor opening.

    This is evidence for one and only one conclusion: the named interval is enclosed and
    therefore is not an open stair-well side.  Furniture is intentionally absent from the
    relation; a bookcase may occupy the pocket, but only its actual walls can close it.
    ``source`` records the construction decision a reviewer must be able to find.
    """

    opening_ref: str
    edge_interval: FloorOpeningEdgeInterval
    wall_refs: tuple[str, ...]
    pocket_outline: tuple[Point2D, ...]
    source: str


@register_element
class FloorSystem(Element):
    """Per-storey structural deck: joists, subfloor, ceiling-below, and openings (#21).

    Its total depth feeds the storey elevation delta — one source of truth for
    floor-to-floor rise (→ 11 §Floors)."""

    joists: JoistSpec
    # Absolute joist-top datum for a local deck whose finished boards must meet a
    # threshold independently of the containing storey's structural floor datum.
    top_elevation: Length | None = None
    #: **A joist field that follows tilted bearings.** The rise of the field's HIGH
    #: perpendicular edge above the datum, which is taken at the LOW one — perpendicular
    #: meaning across ``joists.direction``, the axis a fall runs along when the joists
    #: themselves stay level. Unset (the default) is the flat plane every other deck here is.
    #:
    #: The joists do not rake. Each one is level at its own height, a staircase of small
    #: steps across the field, which is exactly how a sloped deck is framed — the RIM bands,
    #: which run along the slope, do rake, and carry their far-end elevations on
    #: ``FramedMember.z0_end_m``/``z1_end_m``.
    #:
    #: **Author it with the beams, or not at all.** It exists because ``Beam.top_rise_end``
    #: does: a tilted beam under a flat joist field puts the beam's top through the joists
    #: it carries, which ``structural.member_interference`` reports and which is not a
    #: drafting complaint — it is the model disagreeing with itself about where the bearing
    #: is. The two rises have to match over the same run.
    #:
    #: **What it does NOT tilt: the deck PLANE.** ``ResolvedFloor.deck_z0_m``/``deck_z1_m``
    #: are single values read by the room, energy, section and guard consumers, and they stay
    #: at the datum — so the resolved walking surface is the deck's LOW edge. A house
    #: authoring this is stating that its finished deck stands up to ``top_rise`` higher at
    #: the far edge than the model's plane says.
    top_rise: Length | None = None
    # Sistered plies + blocking under concentrated loads (a post bearing on the deck).
    # Empty is the ordinary case: a deck with no point load on it needs none.
    reinforcements: tuple[JoistReinforcement, ...] = ()
    subfloor: DeckLayer | None = None
    # The ceiling hung under this deck's joists, room side first (furring, membrane,
    # finish — same "interior -> exterior" convention as ``Assembly.default_lining``).
    # Empty means no ceiling is authored below this deck at all (open-to-structure).
    ceiling_below: tuple[Layer, ...] = ()
    openings: tuple[str, ...] = ()  # FloorOpening tags
    # What this deck *is*, structurally. "floor" is an interior floor: the 40 psf live +
    # dead residential floor tables in ``checks/structural/checks.py`` grade it. "deck" is an
    # exterior walking surface on posts and beams, which IRC R507 / AWC DCA6 govern instead —
    # different span tables, plus post, footing and guard rules that an interior floor has no
    # equivalent of. Nothing derives this from geometry: a freestanding deck and an interior
    # floor both resolve to joists on bearings, so the distinction has to be authored.
    service: Literal["floor", "deck"] = "floor"
    # Optional explicit footprint. When given, the joist field is scoped to this outline's
    # perpendicular extent instead of the storey's whole wall bbox — needed for a deck that
    # frames a freestanding sub-structure sharing a storey with the main building.
    outline: tuple[Point2D, ...] = ()
    #: **The SHEET, where it is not the joist field.** ``outline`` scopes the framing and the
    #: subfloor follows it, bearing line to bearing line — which is right for a plywood deck
    #: and wrong for a plank that oversails its rim. The breezeway's composite decking runs
    #: 2 3/4" past the rim at each end onto ``D-M-ENTRY``'s and ``D-G-SERVICE``'s thresholds,
    #: which is what a deck board does and what those two doors open onto; widening
    #: ``outline`` to say so would lay a JOIST on each new edge, straight through the posts.
    #: ``JoistSpec.cantilever*`` cannot help either — a bearing line is a span boundary, so a
    #: cantilever is a joist-AXIS quantity by construction, and this oversail is on the
    #: perpendicular one.
    #:
    #: So: an authored sheet polygon that wins outright, the direct analogue of ``outline``
    #: above and of ``Slab.top_elevation``. It replaces the derived corners and nothing else —
    #: ``deck_voids``, ``deck_z0_m``, ``deck_z1_m`` and the joist solver are all untouched.
    #: Empty means the sheet is the joist field, which is every other deck in the house.
    #:
    #: **Bound it against the framing you are asking it to reach.**
    #: ``preferences.toml [framing] bearing_plan_tolerance_in`` (8" by default) is how far
    #: ``structural.uplift_path`` will look for a member's tie; a sheet oversailing further
    #: than that finds neither a derived tie nor a hanger and FAILs every member under it.
    #: ``structural.subfloor_oversail`` grades exactly that.
    subfloor_outline: tuple[Point2D, ...] = ()
    iic: int | None = None  # empirical lookup (#50)
    # Self-adhered membrane over the joist and rim TOPS — butyl "joist tape" and its kin.
    # A catalog material ref, so the house prices it and the engine ships no number for it.
    #
    # It is not a ``DeckLayer``: a subfloor is a sheet spanning the joist field and bills by
    # the square foot, while this follows each stick and bills by the lineal foot. Modelling
    # it as a thin layer would put a 6" strip's price on the whole deck's area.
    #
    # Two jobs, on an exterior deck: it keeps water out of the fastener holes and off the
    # end grain, and — where the decking or the flashing is aluminium over copper-treated
    # lumber — it is the dielectric that stops the treatment corroding the metal (AWC DCA6
    # warns against that contact outright). ``None`` is bare framing, which is every
    # interior floor.
    top_protection: str | None = None
    source: str | None = None


class SlabThermalBreak(HausModel):
    """Vertical rigid-insulation break between a slab edge and whatever abuts it
    (stem wall, foundation wall) — the thermal cut that stops the slab conducting
    straight into the frost-depth concrete. Minimal by design: a material, its
    horizontal ``thickness`` in the joint, and how far ``depth`` runs down the slab
    edge (None = the slab's full thickness)."""

    material_ref: str
    thickness: Length  # horizontal insulation thickness in the edge joint
    depth: Length | None = None  # vertical extent down the slab edge; None = full slab
    #: The board's published compressive rating and the sheet it is read off — the
    #: ``IsolationBoard`` vocabulary. Unstated, a thrust through the edge is graded at the
    #: lowest ASTM C578 type of ``material_ref`` (``thermal_break_board.rated``).
    psi: float | None = None
    modulus_psi: float | None = None
    modulus_estimated: bool = False
    source: str | None = None
    #: The sheet's sustained-load rule as a fraction of ``psi`` (Owens Corning: dead load
    #: <= 1/3). Graded beside a thrust row as its own limit state (free body §11k).
    sustained_load_fraction: float | None = None

    @model_validator(mode="after")
    def _rating_names_its_sheet(self) -> SlabThermalBreak:
        if (self.psi is not None or self.modulus_psi is not None) and not self.source:
            raise ValueError("SlabThermalBreak: a psi or modulus_psi needs the `source` it "
                             "is read off")
        return self


@register_element
class Slab(Element):
    """Slab-on-grade or structural concrete deck (instead of a FloorSystem).

    Like a FloorSystem it may own FloorOpenings (the catlin main deck is a 9"
    slab with a stair hole, → 30 WP3.1)."""

    outline: tuple[Point2D, ...]
    thickness: Length
    assembly: str | None = None
    #: The steel this pour actually contains. Unset means this model does not say — which
    #: for a footing is the ordinary case and a legal one: ACI 318-19 §14.1.4 permits PLAIN
    #: concrete in a footing (unlike §14.1.5 for a column), so a missing spec grades as plain
    #: and reports OK or OVER rather than INCOMPLETE.
    reinforcement: ReinforcementSpec | None = None
    openings: tuple[str, ...] = ()  # FloorOpening tags
    # Which side of the storey datum (= top of floor structure) this slab occupies.
    # "structure" — the slab *is* the floor structure, so it hangs its thickness below the
    # datum. This is the default and covers every slab-on-grade and structural concrete deck.
    # "walking_surface" — decking laid over a FloorSystem whose joists already top out at the
    # datum, so it rides on top instead, exactly like that FloorSystem's own subfloor sheet.
    # Authoring this explicitly rather than inferring it from a shared footprint keeps two
    # coincidentally-congruent elements (a patio slab under a deck, say) from silently
    # swapping conventions.
    datum: Literal["structure", "walking_surface"] = "structure"
    # Absolute top-of-slab elevation, in the project frame, when this slab does not sit on
    # its storey's datum at all — a garage slab left at grade while the house floor above it
    # stays at 0'-0", say. Mirrors ``FoundationWall.top_elevation``. When set it wins over
    # the storey datum outright and ``datum`` no longer applies: the slab hangs its
    # thickness below this elevation. Leave it None (the norm) and the storey datum plus
    # ``datum`` decide. Authoring it is what lets a slab be filed on the storey it belongs
    # to rather than on whichever storey happens to sit at its elevation.
    top_elevation: Length | None = None
    # Slab-on-grade only: rigid-insulation edge break against the abutting stem/foundation
    # wall. None = slab edge pours directly against the concrete it meets.
    perimeter_thermal_break: SlabThermalBreak | None = None
    # This slab's own top face is the finished floor wherever a room sits on it — a
    # polished or sealed cap, not a deck waiting for a covering. Where set, `resolve/rooms.py`
    # intersects this outline with each room's clear face and emits the result as a
    # ResolvedFinishZone, so the room's own `floor_finish` stays the FIELD finish and the
    # concrete bills, draws and prices as its own area. Leave it None (the norm) and a slab
    # is structure only. Not on FloorSystem: a joisted deck's top is a subfloor sheet, and
    # what goes over it is the room's decision, never the deck's.
    floor_finish: str | None = None
    # The ceiling hung under this slab, room side first, meaningful only where a room sits
    # under it (``datum == "structure"``): a slab-on-grade with no occupied space below
    # authors none. Same convention as ``FloorSystem.ceiling_below``.
    ceiling_below: tuple[Layer, ...] = ()
    # The published table row that answers this deck's span, where one does. A
    # manufacturer's table is a PRESCRIPTIVE read — a reviewer opens the document and the
    # question is closed — so authoring one here takes the requirement out of the
    # engineering register rather than into it. See ``model/refs.PublishedSpan``, which
    # carries the drift guards that stop a quotation outliving the model it was read for,
    # and ``checks/structural/slab_span.py``, which grades it. Only a SUSPENDED slab
    # (a room underneath) spans anything; a slab-on-grade authors none.
    published_span: PublishedSpan | None = None


class SoffitOpening(HausModel):
    """A framed hole through a soffit's ladder — a service hatch, not a duct penetration.

    ** IT IS THE FRAMING THAT NEEDS THIS FIELD, NOT THE DRAWING. ** A hatch drawn as a
    placeable in the ceiling below is already expressible (a ``Furniture`` access panel),
    and until this existed that is all a soffit hatch was: a lid in a plane, with the
    generator laying its rungs straight through the hole underneath it. Nothing reported
    the rung standing in the opening, because nothing compared them — so the model asserted
    a panel that could not be opened.

    Naming the opening here instead makes ``resolve/framing/soffit.py`` cut the rungs it
    crosses and frame headers along the box between the two bounding stations, which is
    what a carpenter does and what the take-off should carry. It is deliberately NOT a
    duct penetration: a duct leaves a soffit through its END (the ``along`` clip in
    ``duct_occupants`` is built on exactly that), and a hole in a ladder rail is a
    different article with a different check.

    ``outline`` is an axis-aligned rectangle in the same plan frame as ``Soffit.outline``,
    and it is the CLEAR opening — the hole a hand goes through, not the panel that covers
    it. The panel is its own placeable and is free to be larger by its frame's flange.
    """

    tag: str
    outline: tuple[Point2D, ...]


@register_element
class Soffit(Element):
    """Storey-level dropped ceiling; polygon may span rooms (#40)."""

    outline: tuple[Point2D, ...]
    drop: Length | None = None
    underside_elevation: Length | None = None
    framing: object | None = None  # FramingSpec | None (avoids import cycle)
    # Framed holes through the ladder — access hatches. See SoffitOpening: authoring one
    # is what makes the generator cut the rungs it crosses and head them off, instead of
    # laying lumber straight through a panel drawn below it.
    openings: tuple[SoffitOpening, ...] = ()


@register_element
class FloorHeat(Element):
    """Zone-level radiant heat on a Slab/FloorSystem (#39). No routing solver."""

    zone: tuple[Point2D, ...] | None = None
    room_ref: str | None = None
    system: RadiantSystem = RadiantSystem.HYDRONIC
    spacing: Length | None = None
    embed: Embed | None = None
    stat: Point2D | None = None
    sensors: tuple[Point2D, ...] = ()
    # Connected electric input, when the mat is sized. Left None the output is unknown and the
    # mat contributes nothing to its zone's heating capacity — never inferred from area, since
    # a guessed W/ft2 would move a sizing verdict on an assumption the author never made.
    watts: float | None = None
    # What the finished floor DELIVERS to the room, Btu/h per square foot of heated zone —
    # a different quantity from ``watts``, which is what the cable DRAWS. The two are not
    # convertible: a mat draws its nameplate whatever it is under, while what reaches the
    # room is set by the covering, the floor surface temperature the covering tolerates and
    # the operative temperature of the room. Schluter publishes the relation as a curve of
    # ΔT between those two, and a reading off it is the authored number here. Never
    # defaulted and never derived from ``watts``: the derivation would silently assume the
    # cable's whole draw arrives in the room, which is the optimistic error in exactly the
    # calculation (``mep.room_heat_source``) that decides whether a radiant floor can be a
    # room's only heat.
    delivered_btuh_per_ft2: float | None = None


class FinishZone(HausModel):
    """An in-room floor-finish override zone (tile inlay, hearth pad) (#21)."""

    outline: tuple[Point2D, ...]
    material_ref: str


for _name, _obj in (
    ("JoistSpec", JoistSpec),
    ("JoistReinforcement", JoistReinforcement),
    ("DeckLayer", DeckLayer),
    ("FloorOpening", FloorOpening),
    ("FloorOpeningEdgeInterval", FloorOpeningEdgeInterval),
    ("FloorOpeningPocketClosure", FloorOpeningPocketClosure),
    ("FloorSystem", FloorSystem),
    ("Slab", Slab),
    ("SlabThermalBreak", SlabThermalBreak),
    ("Soffit", Soffit),
    ("SoffitOpening", SoffitOpening),
    ("FloorHeat", FloorHeat),
    ("FinishZone", FinishZone),
):
    register_constructor(_name, _obj)

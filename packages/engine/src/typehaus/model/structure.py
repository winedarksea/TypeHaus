"""Foundation & structural elements (#27 — schema in M1, sheets in M3)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element, HausModel
from typehaus.model.elements import Wall
from typehaus.model.enums import ConnectorKind, RailingKind
from typehaus.model.refs import FaceRef
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D, inch


@register_element
class FoundationWall(Wall):
    """A Wall in every structural sense, distinguished by kind (→ 11 §Foundations).

    Carries explicit top/bottom elevations for the walkout/sunken-garden condition."""

    top_elevation: Length | None = None
    bottom_elevation: Length | None = None
    # Height of backfill retained against this wall with no balancing fill on the other side —
    # the span IRC Table R404.1.2(1) is indexed on. Authored only where the derived value
    # (grade down to the footing) is not the real condition: a wall backfilled part way, or
    # one with a slab bearing against its inside face. Left None it is derived — see
    # checks/structural/foundation.py.
    unbalanced_fill: Length | None = None
    # An engineer's design for this wall, verbatim. Same escape hatch as Door.header_spec:
    # an authored spec IS the design, so the prescriptive table stops applying and the check
    # reports PASS citing it rather than FAIL demanding what is already in hand.
    engineering_spec: str | None = None
    # The vertical reinforcement actually specified for this wall, verbatim — e.g.
    # '#6 @ 38" o.c.'. IRC Table R404.1.2(8) answers what a wall NEEDS; this records what it
    # HAS, and the check compares them. Left None where the table's cell reads NR, since
    # there is nothing to record.
    vertical_reinforcement: str | None = None
    # Whether the wall is permanently braced top and bottom — a slab or footing key at the
    # base, a floor diaphragm at the head. This is not a detail, it is the precondition for
    # the whole prescriptive path: IRC Table R404.1.2(8) presumes it (footnote g), and
    # R404.1.1 sends a wall retaining more than 48" WITHOUT it to an engineered design, as
    # R404.4 does for a free-standing retaining wall. Unauthored, a wall retaining 4' or more
    # is UNKNOWN rather than assumed braced — the assumption is the unsafe direction.
    #
    # ``"base"`` is a THIRD state and not a flavour of ``"unsupported"``: restrained against
    # translation at the base, free at the top. It is what a retaining wall standing in a
    # closed loop of cast concrete has — the sunken garden's court, where the two side walls
    # face each other across a strut and their thrusts cancel through it. It must NEVER reach
    # Table R404.1.2(8): footnote g's presumption is bracing top *and* bottom, and a
    # base-only wall falling through to the table would collect a prescriptive PASS with no
    # engineering behind it at all. ``checks/structural/foundation.py::_grade_one`` routes it
    # to the R404.4 handoff beside ``"unsupported"``, and it stays in
    # ``engineering/retaining_wall``'s suite.
    lateral_support: Literal["top_and_bottom", "unsupported", "base"] | None = None
    # The tag of the element that closes the base restraint — for ``lateral_support="base"``,
    # the cross-member whose presence makes the loop a loop and whose removal breaks it.
    #
    # **Authored, never derived** (``*_ref`` is the repo convention), and the pair is checked
    # both ways: a ``"base"`` wall without this ref, or this ref without ``"base"``, is a
    # half-authored claim, and a half-authored claim is the shape a free pass arrives in.
    # Naming it does not GRANT the restraint either — ``engineering/retaining_system`` goes
    # and verifies that the named element is a real member of the same closed structural loop
    # and reports INCOMPLETE when it is not.
    base_restraint_ref: str | None = None


@register_element
class Footing(Element):
    """Strip/spread footing auto-following its parent's geometry (→ IfcFooting)."""

    under: str  # wall or post tag
    width: Length
    depth: Length
    # What the strip is made of. Unset stays "plain concrete" — the resolved solid carries
    # no assembly, ``structural_solids_takeoff`` groups it bare and prices it out of
    # ``emit/trades``' hardcoded category row, and nothing moves. That is right for most
    # footings and wrong for the one that matters: an insulated footing form (EPS faces
    # around a concrete core) is the FPSF answer to a shallow-cover condition.
    assembly: str | None = None
    # What the strip is centred on. "axis" — the parent wall's raw node line — is the
    # historical behaviour and stays the default. It is only right where the wall is
    # centred on its own axis; under an ``alignment=face(...)`` wall the section sits to
    # one side of the node line, and a strip centred there runs out from under it. "wall"
    # centres on the midline of the *resolved* layer band instead, which is the wall the
    # concrete is actually poured as, giving a symmetric toe either side.
    center_on: Literal["axis", "wall"] = "axis"
    #: Signed displacement of the footing's centre off the line ``center_on`` picks, square
    #: to the wall, **in the resolver's own frame**: positive along the LEFT-hand normal of
    #: the wall's ``start_node`` -> ``end_node`` direction, which is the same ``left``/
    #: ``right`` frame ``resolve/geometry.rect_between`` already lays the strip out in.
    #:
    #: **What it is for.** A retaining wall's footing is not a bearing footing: the toe and
    #: the heel do different jobs, and the width that fixes one is rarely the width that
    #: fixes the other. A centred strip is the wrong shape for both and the only shape this
    #: model could state — so the sunken garden's court could buy eccentricity margin only
    #: by growing its footings symmetrically, which walks the OUTBOARD edge into the raised
    #: garden's apron. With an offset the same concrete goes where it is free: 6" toward the
    #: court, toe 4'-0" / heel 3'-0", outboard edge exactly where the 7'-0" strip left it.
    #:
    #: Ignored for a post-hosted footing, which has no axis to be square to.
    #:
    #: The frame is geometric and deliberately not structural: it says which way, not which
    #: side is the toe. ``engineering/retaining_basis._geometry`` resolves toe from heel with
    #: ``resolve/orientation.wall_outward_sign``, and refuses (INCOMPLETE) rather than guess
    #: where an offset is authored and the storey's winding is unrecoverable.
    offset: Length | None = None
    # Where the underside bears, for a footing that does NOT hang off the thing above it.
    # A strip footing's top follows its wall's bottom and a post-hosted spread footing's
    # top was pinned to the storey datum, which is right for a pad poured in the same lift
    # as the slab and wrong for the other way a column gets founded: an augered shaft with
    # a belled base, where the bell bears at frost depth and the sonotube above it simply
    # gets longer. That was inexpressible — the only way to reach 42" was ``depth=42"`` at
    # the *bell's* width, which draws a 30"x30"x42" prism and bills 1.41 cy where 0.20 cy
    # of extra shaft gets built. ``Pad`` has carried exactly this field for exactly this
    # reason ("at frost depth, typically"); a Footing under a Post now can too. The hosted
    # Post follows, because ``_resolve_post`` reads its support's top — so authoring this
    # means also lengthening the post by the same amount, or its top leaves its beam.
    #
    # Ignored for a wall-hosted footing: there the wall's underside IS the datum, and two
    # sources for one elevation is how they disagree.
    bottom_elevation: Length | None = None


@register_element
class Pad(Element):
    """Isolated pad / thickened slab (→ IfcFooting)."""

    outline: tuple[Point2D, ...]
    thickness: Length
    bottom_elevation: Length | None = None


class DrainTile(HausModel):
    """Drain-tile product spec for a FootingBedding — what the bare ``drain_tile: bool``
    cannot say: pipe size/material, sock, and where the run discharges. A detail slice
    and the take-off read this; the bool keeps meaning merely "one exists"."""

    diameter: Length
    material: str = "perforated corrugated HDPE"
    sock: bool = True  # filter-fabric sock over the perforations
    discharge: str | None = None  # "daylight" | "sump" | free-text run note
    # The washed-rock surround the tile floats in. Optional because a bedding that only says
    # "there is a tile" is a legitimate level of detail; when authored, the perimeter-drain
    # detail draws these instead of the pinned reference dimensions it had to inline while
    # the model had nowhere to put them (``emit/draw/detail_components/config.py``).
    rock_width: Length | None = None
    rock_depth: Length | None = None


@register_element
class FootingBedding(Element):
    """Excavation/bedding prep beneath a strip Footing — or beneath a wall that has none.

    Digs an extra ``undercut`` below the host's underside for a compacted washed-stone
    bed on non-woven geotextile (no-slip) with a drain tile — breaks direct footing-to-wet-
    clay contact (thermal loss) and drains the bearing surface. ``perimeter_insulation``
    continues the foundation wall's exterior rigid foam down over the footing sides;
    ``cast_foam_in_aggregate`` optionally casts foam into the stone itself for a further
    thermal cut. Never resizes/moves the host — an annotation + bearing-prep record.

    ``host_ref`` names a Footing, or a FoundationWall that is founded on the bed itself:
    a dry-stacked SRW retaining wall beds its base course straight onto a compacted
    levelling pad and has no concrete under it at all. Both cases are the same excavation
    and the same order of stone, which is why they are the same element and not two.
    """

    host_ref: str  # Footing tag, or FoundationWall tag for a wall founded on the bed
    undercut: Length  # additional depth dug below the host's underside
    # Band width for a wall-hosted bed, which a levelling pad runs wider than the block it
    # carries (6" past each face is the usual SRW rule). ``None`` beds the host's own
    # footprint, which is always what a footing-hosted bedding wants.
    width: Length | None = None
    aggregate: str = "ASTM C33 #57 washed crushed stone"
    # Is that aggregate section non-frost-susceptible? NFS is a *gradation* claim — under
    # an ASTM D422 sieve analysis, less than 6% by mass passing the #200 sieve — and it is
    # authored here rather than derived, because ``aggregate`` above is free text and
    # reading a soil classification out of a substring is guessing (the same reason
    # ``emit/draw/elevation_finish._recipe_for`` wants two authored fields instead of one
    # string to match on). ``None`` therefore means nobody has stated it, and an unstated
    # section counts for nothing.
    #
    # It matters because ASCE 32 treats a *well-drained* NFS layer's thickness as counting
    # toward the design frost depth — soil replacement — and IRC R403.1.4.1 admits a
    # foundation "constructed in accordance with ASCE 32" as one of its listed
    # frost-protection methods (MN Rules 1309.0403 keeps it). So a footing whose concrete
    # stops short of frost depth can still be protected, by the stone under it reaching
    # down instead. ``structural.frost_depth`` counts a section only where this is True
    # *and* ``drain_tile`` runs one: an undrained NFS layer is not what ASCE 32 describes.
    non_frost_susceptible: bool | None = None
    geotextile: bool = True
    drain_tile: bool = True
    # Optional product spec for the tile above; None keeps the bool's bare annotation.
    drain_tile_spec: DrainTile | None = None
    perimeter_insulation: Length | None = None
    cast_foam_in_aggregate: bool = False


@register_element
class FrenchDrain(Element):
    """A stone-filled interceptor trench with a tile in it, on an authored plan path.

    Distinct from the tile a :class:`FootingBedding` runs: that one is *derived* from the
    excavation it sits in and always follows a footing, while this is a run somebody put
    where the water goes — across a slope, along a retaining wall, out to daylight. It is
    what the code below grade drains *to* rather than part of a bearing detail.

    ``invert`` is the trench floor at the run's start; the tile inside it is derived from
    ``tile`` exactly as a bedding's is (``resolve/drain_tile.py``), so both kinds of run bill
    and draw the same way. ``discharge_ref`` names where it lets go — a ``Drywell``, a
    ``Sump``, or nothing when it daylights.
    """

    path: tuple[Point2D, ...]  # plan centreline, start → discharge end
    invert: Length             # trench floor elevation
    trench_width: Length
    trench_depth: Length
    tile: DrainTile | None = None
    discharge_ref: str | None = None


@register_element
class Drywell(Element):
    """An aggregate-filled soakaway: a hole that takes water faster than it arrives.

    Where a :class:`FrenchDrain` moves water sideways, a drywell holds it while the soil
    takes it, which is why it is a volume (diameter × depth of stone) rather than a run. Its
    ``inlet_refs`` name what feeds it — leaders, french drains, a footing's tile.
    """

    position: Point2D
    diameter: Length
    depth: Length  # of stone, measured down from the top of the well
    aggregate: str = "ASTM C33 #57 washed crushed stone"
    geotextile: bool = True  # fabric-wrapped, or the surrounding soil silts the voids shut
    inlet_refs: tuple[str, ...] = ()
    # Top of stone. A soakaway is dug from the ground, not from a floor, so this defaults to
    # site grade rather than to the storey datum — a drywell outside the garage authored on
    # the basement storey would otherwise start at the basement floor.
    top_elevation: Length | None = None


@register_element
class Post(Element):
    """A point structural member (→ IfcColumn)."""

    position: Point2D
    size: str = "6x6"
    height: Length | None = None
    # Tag of what the post bears on — a pad/footing/slab, or a wall the post stands on top
    # of (the balcony pillars bear on the masonry porch railing). Unset hangs the post's
    # top at its storey datum instead.
    supported_by: str | None = None
    assembly: str | None = None  # optional finish assembly (e.g. paint) for render/IFC material
    # Tag of the wall this post deliberately stands *inside* — the suite's tudor timbers
    # sit in W-S-W3's stud line, proud to the drywall face. The framer cuts the plates and
    # studs around such a post, a joint the box IR cannot express, so
    # ``structural.member_interference`` clears the post against exactly this wall's
    # framing and no other. Authored, never guessed (same doctrine as flush-framed beams):
    # a post that merely crashes into a wall it never named is still reported.
    within_wall: str | None = None
    # The reinforcing cage in a CAST post, verbatim — e.g. '(4) #5 vertical, #3 ties @ 10"
    # o.c.'. Same contract as FoundationWall.vertical_reinforcement (records what the member
    # HAS, so a check can compare it against what the code requires), but **the spec shape is
    # different and deliberately so**: a wall's bars are stated as a SPACING because the wall
    # is billed per foot of length, while a column's are stated as a COUNT because the cage
    # is a discrete thing that either has four bars in it or does not. ACI 318-19 §10.6.1.1
    # bounds the count (0.01Ag to 0.08Ag) and §10.7.3.1 sets its floor at four within
    # circular ties, and neither question can be asked of a spacing.
    #
    # Left None on a wood post, where it means nothing, and on a plain cast PEDESTAL, which
    # ACI 318-19 §14.1.3(d) permits to have no steel at all. Left None on a cast COLUMN it is
    # not a silence the engine may fill: §14.1.5 does not permit a plain concrete column at
    # any stress, so ``engineering/deck_post.py`` reports INCOMPLETE naming this field rather
    # than assuming a sonotube "probably" has bars in it.
    vertical_reinforcement: str | None = None


@register_element
class Beam(Element):
    """An axis structural member; a valid bearing ref for JoistSpec (→ IfcBeam)."""

    start_node: str
    end_node: str
    size: str = "3.5x11.875 LVL"
    bearing_refs: tuple[str, ...] = ()
    datum: FaceRef | None = None
    # Project-frame absolute top of the beam, overriding the derived bearing-stack drop.
    # The resolver normally hangs a beam a joist depth below its storey datum, which it
    # infers from the FloorSystem that bears on it. A beam that carries no joists but must
    # still sit low — the balcony E-W girts bolt to the pillar faces *under* beams whose own
    # tops are already dropped — has no such inference available, and authoring it into a
    # FloorSystem's bearing_refs to borrow the drop would claim joists it does not carry.
    top_elevation: Length | None = None
    # Optional finish assembly (paint/stain), same contract as Post.assembly: the resolver
    # forwards it to the beam's solid so render/IFC read the finish instead of the bare
    # per-category palette colour. Unset leaves the beam its structural wood colour.
    assembly: str | None = None
    # Self-adhered membrane over the beam's top face — the same field, and the same reasons,
    # as ``FloorSystem.top_protection``; see that docstring. A built-up beam is the member
    # that wants it most: every ply seam is an open joint running the beam's whole length.
    top_protection: str | None = None


@register_element
class Dowel(Element):
    """A fiberglass (GFRP) rebar dowel tying two footings across a thermal break.

    The house and the sunken-garden footings share a compacted bed; where they abut, GFRP
    dowels pin them together *through* a rigid-foam block so the connection transfers shear
    without bridging heat. ``foam_thickness`` / ``foam_psi`` describe the XPS block the
    dowel passes through — resolved as its own solid
    so the thermal break reads in the model, IFC, and take-off."""

    position: Point2D  # plan center of the dowel span (midpoint of the break)
    axis: str = "y"  # "x" | "y": the direction the dowel bar runs across the break
    length: Length  # embedment-to-embedment span across the joint
    diameter: Length  # bar diameter (e.g. #5 GFRP ≈ 0.625")
    elevation: Length  # bar centerline, project-frame absolute
    count: int = 1  # bars in the row
    spacing: Length | None = None  # o.c. spacing when count > 1 (perpendicular to axis)
    connects: tuple[str, ...] = ()  # the two footing tags doweled together
    foam_thickness: Length | None = None  # XPS thermal-break block thickness (along axis)
    foam_height: Length | None = None  # block height (defaults to footing thickness)
    foam_psi: float = 40.0  # XPS compressive rating


@register_element
class Connector(Element):
    """Modeled connection hardware — joist hangers, hurricane ties, knee braces, post bases.

    A first-class element with a small resolved solid at its connection point
    (→ IfcMechanicalFastener / IfcDiscreteAccessory), and named refs to the members it
    joins."""

    kind: ConnectorKind
    position: Point2D
    elevation: Length | None = None  # connector center, project-frame absolute
    size: str = ""  # product model, e.g. "APVKB", "H2.5A", "LUS28", "ABU66"
    connects: tuple[str, ...] = ()  # member/wall/post tags the hardware joins
    axis: str | None = None  # optional in-plane run direction ("x" | "y") for braces


@register_element
class KneeBrace(Element):
    """A 45-degree diagonal brace stiffening a post/beam joint (→ IfcMember/BRACE).

    The structural element is the wood diagonal; ``connector`` names the hardware that
    fastens it (a Simpson Outdoor Accents APVKB, say), which resolves as a small marker at
    the upper end. One element per *physical* brace — a post braced in both plan directions
    carries two of them — so the take-off counts braces rather than multiplying a per-joint
    rule that only holds where a beam continues past its post.

    Geometry is the 45-degree triangle a carpenter cuts: the brace leaves the post *face*
    (never its centre — an embedded end reads as a member clash) and runs ``leg`` out along
    ``axis``/``direction`` while rising the same ``leg`` to ``soffit_elevation``. That soffit
    is authored rather than derived because the members a post is braced to need not share
    an elevation: the balcony's N-S braces land on the beam soffit and its E-W braces a rail
    depth lower.

    ``position`` is the **braced post's plan centre**. A brace that does not run in its
    post's own plane says so with ``plane_offset`` + ``foot_lap``, never by moving
    ``position`` off the post — author the offset point instead and the geometry still
    resolves, the section still looks right, and the foot quietly leaves the post with
    nothing to bear on; see ``plane_offset``.
    """

    position: Point2D  # braced post's plan centre
    soffit_elevation: Length  # underside of the member braced to, project-frame absolute
    leg: Length  # horizontal run; equal to the rise at 45 degrees
    axis: str = "y"  # "x" | "y": the plan direction the brace runs from the post
    direction: int = 1  # +1 / -1 sense along ``axis``
    member: str = "2x6"  # the diagonal's own nominal profile
    post_size: str = "6x6"  # braced post's section, so the brace starts at its face
    connector: str = "APVKB45-6"  # hardware model at the joint
    assembly: str | None = None  # optional finish assembly (paint), same contract as Post.assembly
    connects: tuple[str, ...] = ()  # post + beam/girt tags the brace joins
    #: The brace's own plane, offset from the post's centre and measured **square to**
    #: ``axis`` — signed along +y for an ``axis="x"`` brace, along +x for an ``axis="y"`` one.
    #:
    #: A brace is not always in its post's plane. The balcony's E-W braces rise into
    #: ``BM-SG-RAIL-R/F``, which are face-bolted to the *inboard* face of each pillar row —
    #: half a post plus half a rail, 3 1/2", off the post axis. A brace can be coplanar with
    #: that rail, or it can bear on the post's side face, and it cannot be both. Reaching
    #: across would skew it in plan, and no flat 45-degree stabiliser strap wraps a skewed
    #: joint. **Coplanar wins**: the thrust then lands in the rail's own plane, bending it
    #: about its strong axis with no eccentricity, where a brace offset from that plane would
    #: twist a member already at l_e/d 80 about its weak one.
    #:
    #: Offsetting the plane costs the foot its bearing, so it comes with ``foot_lap``.
    plane_offset: Length | None = None
    #: A **face-lapped** foot: instead of butting the post face, the foot runs this far back
    #: past it, lying flat on the post's adjacent face and through-bolted there. It is the
    #: other half of ``plane_offset`` — an offset brace has no post material in front of its
    #: end to bear on, so it laps the post and the bolts carry the joint.
    #:
    #: Set it to the post's own width to lap the full face (the balcony's case: 5 1/2" of 2x6
    #: lying diagonally across a 6x6's inboard face, ~7 3/4" of brace length over it).
    #: ``None`` keeps the bearing contract in the class docstring, which is what an in-plane
    #: brace — every N-S one here — actually does.
    #:
    #: It moves geometry only. The bolt schedule the lap implies is
    #: ``takeoff/hardware_config.KneeBraceRules``' business and the capacity is NDS Ch. 12's,
    #: neither of which this field decides.
    foot_lap: Length | None = None
    #: A licensed engineer's lateral design for this brace, cited. Verbatim the contract
    #: ``FoundationWall.engineering_spec`` carries and for the same reason: an authored,
    #: external, stamped design IS the design, and ``structural.lateral_racking`` stands down
    #: to a PASS quoting it, exactly as ``checks/structural/foundation.py::_grade_one`` stands
    #: down from IRC R404.4's tables. Until one exists the check reports UNKNOWN with its own
    #: worked demand-to-capacity ratio, which is a screening calculation and says so.
    #:
    #: **Nothing in this repository may author this field on its own arithmetic.** It is the
    #: record of a document that exists outside the model, and a value invented to silence an
    #: UNKNOWN would convert an open question into a fabricated pass — the one failure mode
    #: the tri-state exists to prevent.
    engineering_spec: str | None = None


@register_element
class Wedge(Element):
    """A tapered framing shim: a rip that grows from a feather to a crown (→ IfcMember).

    The breezeway's drainage wedges are the case this exists for. A ``Beam`` is a prism, so
    a member whose depth changes along its run cannot be one — but ``FramedMember`` already
    carries ``z0_end_m``/``z1_end_m``, and ``member_box`` already builds the raked
    hexahedron a tapered band needs. So the wedge is authored here, resolves to one raked
    stick of lumber, and is ordered, cut and counted like any other piece of wood.

    Geometry is the triangle a carpenter rips: the piece starts ``run`` long at
    ``position`` — the **thick** end, ``rise`` deep — and feathers to nothing at the far end
    along ``axis``/``direction``. A pair back to back on one member therefore makes a crown,
    which is exactly how a flat roof is given its fall.

    ``bears_on`` names the members the wedge is nailed to, for the same reason
    ``Beam.bearing_refs`` does: the take-off and the details need to know what carries it.
    """

    position: Point2D  # the thick (crown) end, in plan
    base_elevation: Length  # underside of the wedge, project-frame absolute
    run: Length  # horizontal run from the crown to the feathered end
    rise: Length  # depth at the crown; zero at the far end
    axis: str = "x"  # "x" | "y": the plan direction the taper runs
    direction: int = 1  # +1 / -1 sense along ``axis``
    member: str = "2x4"  # the stock the taper is ripped from
    bears_on: tuple[str, ...] = ()  # member tags the wedge is fastened to
    assembly: str | None = None  # optional finish assembly, same contract as Post.assembly


@register_element
class Railing(Element):
    """A first-class guard rail framed from posts + rails along a plan path (→ IfcRailing).

    The metal fascia-mounted balcony guard is modeled here rather than approximated as a
    parapet wall. The resolver frames posts at ``post_spacing`` o.c. along ``path`` plus
    ``rail_count`` horizontal rails, all riding at ``base_elevation`` (the deck top)."""

    type_ref: str | None = None  # product identity; geometry remains shared by kind/path
    path: tuple[Point2D, ...]  # guard line, >= 2 plan points
    kind: RailingKind = RailingKind.METAL_FASCIA_MOUNT
    height: Length  # guard height above the deck
    base_elevation: Length  # deck top, project-frame absolute
    post_spacing: Length  # posts o.c. along the path
    post_size: str = "2x2"  # nominal post cross-section
    rail_count: int = 2  # horizontal rails (top + bottom)
    mount: str = "fascia"  # "fascia" | "surface"
    assembly: str | None = None  # optional finish assembly for render/IFC material
    # --- guard vs handrail (R311.7.8, R312.1.3) ------------------------------------------
    # A Railing was only ever a *guard*: a plan path with a height, framed into posts and
    # rails. That is the right model for a balcony edge and the wrong one for a stair, where
    # the code asks two further questions a guard cannot answer — is there something to hold
    # onto, and can a 4" sphere pass through what is under it.
    #
    # Every field below is optional and defaulted, so existing authoring loads unchanged and
    # a house that says nothing gets UNKNOWN rather than a fabricated verdict.
    role: Literal["guard", "handrail", "guard_and_handrail"] = "guard"
    serves_stair: str | None = None  # Stair tag; None for a floor-edge guard
    # Handrail top above the *nosings*, which is not the same datum as ``height`` (the guard
    # height above the deck). R311.7.8.1 wants 34"-38" measured from the nosing line.
    top_height: Length | None = None
    # R311.7.8.3 graspability: "type-I" (circular 1-1/4"-2", or equivalent perimeter),
    # "type-II" (the shaped profile with a finger recess), or a product name.
    graspable_profile: str | None = None
    continuous: bool = True  # R311.7.8.2: the full length of the flight, no interruption
    infill: Literal["balusters", "panel", "cable", "mesh"] | None = None
    # R312.1.3: the largest opening the infill admits. For balusters this is the clear gap
    # between them, which is *not* ``post_spacing`` — that is the structural post rhythm.
    baluster_spacing: Length | None = None
    # --- per-part finish (→ resolve/railings/parts.py) -----------------------------------
    # A guard is rarely one material: a glass balcony rail is aluminium posts, an aluminium
    # cap and a glass lite, and ``assembly`` can only say one thing about all three. Each of
    # these names a catalog ``Material`` for one part; ``None`` falls to the product type's
    # own default, then to today's ``assembly`` behaviour, so authoring nothing changes
    # nothing. The alpha byte of an authored ``#RRGGBBAA`` colour is what makes an infill
    # read as glass, in both the .glb and the live viewer.
    post_material: str | None = None
    rail_material: str | None = None
    infill_material: str | None = None


@register_element
class GlazingPanel(Element):
    """A flat translucent sheet spanning a frame — multiwall polycarbonate, glass, acrylic.

    Not a :class:`~typehaus.model.elements.Window`: a window is an *opening* cut in a host
    wall and framed by it. This is the sheet itself, standing free in a post-and-beam frame
    with no wall to host it — the enclosure of a breezeway, a canopy, a lean-to. It is also
    not a ``Slab`` with a glazing assembly, because a Slab is pinned to its storey datum and
    a canopy panel sits at whatever absolute elevation its rafters put it.

    ``plane`` picks the extrusion:

    * ``"horizontal"`` — ``outline`` is the panel's footprint, lying flat with its top at
      ``top_elevation`` and its underside a ``thickness`` below.
    * ``"vertical"`` — ``outline`` is the panel's *run* in plan (two or more points), stood
      up from ``base_elevation`` to ``top_elevation`` and given ``thickness`` across the run.

    Sheet economy is a real design constraint for these (they come in 4'x8' stock and cutting
    them is waste), so the take-off bills them by area *and* by whole sheets.
    """

    outline: tuple[Point2D, ...]
    thickness: Length
    top_elevation: Length
    plane: Literal["horizontal", "vertical"] = "horizontal"
    base_elevation: Length | None = None  # vertical panels; required when plane="vertical"
    assembly: str | None = None
    # Applied film — UV, solar-control, or bird-safety patterning. Recorded rather than
    # modeled: it is 2 mil of surface treatment, not a layer with a thermal or dimensional
    # consequence, but it is a line on the order and a note on the drawing.
    film: str | None = None
    # Safety glazing. A breezeway enclosure and a canopy are both R308.4 hazardous
    # locations by construction — a free-standing sheet at walking height is the case the
    # section was written for — so this is the one place the flag is nearly always true.
    tempered: bool = False


@register_element
class SolarPanel(Element):
    """One PV module lying on a roof plane, mounted on standing-seam clamps.

    Not a :class:`GlazingPanel`: that element is axis-flat (horizontal or vertical) while
    a module lies *in the roof plane* — the resolver computes its four tilted corners from
    the referenced roof's pitch, standing it ``standoff`` off the plane (clamp + rail
    height) with ``thickness`` across it. ``origin`` is the module's ridge-side corner
    with the smallest along-ridge coordinate; the module runs ``width`` along the ridge
    and ``length`` down the slope (both measured in the panel plane, so the plan
    projection of ``length`` is foreshortened by the pitch).

    The clamps are separate ``Connector(STANDING_SEAM_CLAMP)`` elements so the hardware
    take-off counts them like every other modeled connector.
    """

    roof_ref: str  # ResolvedRoof tag, e.g. "RF-HOUSE"
    origin: Point2D  # ridge-side, min-along-ridge corner (plan frame)
    width: Length  # along-ridge module edge (69.4" landscape)
    length: Length  # down-slope module edge, in the panel plane (44.6")
    thickness: Length  # module depth (1.2")
    standoff: Length = inch(3)  # clamp + rail height off the roof plane
    watts: float = 0.0  # nameplate DC watts — summed by the solar take-off
    product: str = ""
    # Series string this module belongs to (e.g. "STR-W"). Modules in a string share a
    # conductor pair, so string is what the Voc sums and the RSD grouping are computed
    # over; "" means the array is not broken into declared strings yet.
    string: str = ""
    # Rated open-circuit voltage at STC, and the same voltage temperature-corrected to the
    # site's design low. ``voc_cold`` is authored rather than derived because the
    # correction needs a temperature coefficient and a design temperature that are both
    # datasheet/jurisdiction facts, not model geometry — and it is the ONLY Voc the 80V
    # rapid-shutdown grouping may be computed from (rated Voc understates it badly in MN).
    voc: float | None = None
    voc_cold: float | None = None
    # A SunSpec rapid-shutdown transmitter/PLC device is fitted to this module. False on a
    # module means it must be covered by a group whose summed ``voc_cold`` stays under the
    # 690.12 limit.
    rsd: bool = False


for _name, _obj in (
    ("DrainTile", DrainTile),
    ("FoundationWall", FoundationWall),
    ("Footing", Footing),
    ("GlazingPanel", GlazingPanel),
    ("SolarPanel", SolarPanel),
    ("Pad", Pad),
    ("FootingBedding", FootingBedding),
    ("FrenchDrain", FrenchDrain),
    ("Drywell", Drywell),
    ("Post", Post),
    ("Beam", Beam),
    ("Dowel", Dowel),
    ("Connector", Connector),
    ("KneeBrace", KneeBrace),
    ("Wedge", Wedge),
    ("Railing", Railing),
):
    register_constructor(_name, _obj)

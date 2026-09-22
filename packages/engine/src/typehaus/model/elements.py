"""Core plan elements: Node, Wall, and openings (Door/Window/RoughOpening) (→ 11)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element
from typehaus.model.enums import StructuralRole
from typehaus.model.refs import (
    Arch,
    FaceRef,
    LayerMaterial,
    OpeningPosition,
    PublishedHole,
    PublishedSpan,
    ShearPanelSpec,
    ToRoof,
)
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


@register_element
class Node(Element):
    """A 2D point in a storey's project-north plan frame (auto-tagged N-1…)."""

    position: Point2D
    open_end: bool = False  # a legitimate wing-wall terminus (suppresses gap error)
    anchored: bool = False  # pinned: move_nodes holds it in place


@register_element
class Wall(Element):
    """An edge between exactly two nodes. Cannot exist without an assembly (→ 11)."""

    start_node: str
    end_node: str
    assembly: str
    # Top constraint; only the Length arm resolves in M1.
    top: Length | ToRoof | None = None  # None => underside of FloorSystem above
    # Which assembly face lies on the node-to-node axis.
    alignment: FaceRef | None = None  # None => center
    # Which side layer 0 (the assembly's *interior* face) looks at, named by Room tag.
    # The storey's outer loop settles this for an exterior wall, but an interior partition
    # has rooms on both sides, so an asymmetric assembly (a sauna liner, say) needs the side
    # declared. A Room reference rather than a bare flip: swapping start_node/end_node would
    # silently invert a flip, and does not touch this.
    interior_room: str | None = None  # None => follow the storey's outward sign
    structural_role: StructuralRole = StructuralRole.UNKNOWN
    # Where the wall's base sits, as an absolute project elevation. ``None`` means the
    # storey datum, which is what a framed wall standing on the floor does. It is authored
    # where a wall stands on something *within* its own storey: a framed wall on a concrete
    # curb, where the studs start a curb's height above the slab and are that much shorter.
    # Deliberately a separate field from ``FoundationWall.bottom_elevation`` (the walkout
    # condition), because a FoundationWall's pair is bottom+top absolute while a framed wall
    # keeps stating its height with ``top`` relative to its own base.
    #
    # Everything downstream follows for free: ``ResolvedWall.z0_m`` is what the framing
    # solver measures plates and studs from, what ``base_ref_z_m`` (and so every opening
    # sill) is datumed on, and what ``Footing.under`` reads for its own top.
    base_elevation: Length | None = None
    # The exterior surface at the foot of this wall PONDS, and nothing may reach the
    # interior over this wall less than this far above it. Authored, not derived, for the
    # same reason ``WindowType.fall_protection`` is: whether a court holds water is a
    # drainage judgement about a bowl, an outlet and a storm, and a model that guessed it
    # from geometry would be inventing the premise rather than grading it. What the engine
    # can hold to, once the premise is stated, is the arithmetic — see
    # ``building_science.flood_step_threshold``, which grades this wall's TOP against the
    # highest surface below it outside. A curb built to a bare literal is a number in a
    # comment; this is the same number the checker can defend.
    min_threshold_step: Length | None = None
    # Vertical stacking (#43).
    vertical_datum: FaceRef | None = None  # None => storey default
    stacks_on: str | None = None  # tiebreaker: tag of the wall below
    bearing_refs: tuple[str, ...] = ()
    # Per-end corner-framing override ("3-stud" | "4-stud" | "california") consumed by the
    # corner solver; None follows the assembly's FramingSpec.corner_style. Authored per wall
    # end because a corner belongs to two walls — the override lives on the end that hosts
    # the extra stud, so two walls never fight over one corner's style.
    corner_style_start: Literal["3-stud", "4-stud", "california"] | None = None
    corner_style_end: Literal["3-stud", "4-stud", "california"] | None = None
    # This wall *is* a guard at an open edge, not an enclosure — a masonry parapet standing
    # where a Railing would otherwise be. A guard is the one thing a wall can be that
    # changes which rules apply to it: R312.1.3 has nothing to measure in solid masonry
    # (it admits no sphere by construction), structural.deck_guard has to see it as the
    # guard the deck is relying on, and its own dead load has to land on something that can
    # carry it (structural.masonry_guard_bearing). Marked rather than inferred: "short wall
    # at a floor edge" describes a knee wall, a planter and a stair curb just as well.
    guard: bool = False
    # This wall is claimed as a SHEAR PANEL — one of the lines a frame's lateral load is
    # shared out to — and the SDPWS row that claim rests on. Unset means "not a lateral
    # line", which is the conservative default: a frame whose other lines take the whole
    # shear is never made weaker by a wall nobody declared. See ShearPanelSpec.
    shear_panel: ShearPanelSpec | None = None
    # Per-layer material substitution: appearance only, and the alternative to duplicating
    # a whole Assembly to restate one `material_ref` (see LayerMaterial in model/refs.py).
    # A tuple rather than a mapping because the editable dialect has no mapping literal.
    layer_materials: tuple[LayerMaterial, ...] = ()
    # The published table row that answers a question about this wall, where one does.
    # Mirrors ``Door.published_span``: a manufacturer's table is a PRESCRIPTIVE read — a
    # reviewer opens the document and the question is closed — so authoring the row here
    # takes the requirement out of the engineering register rather than into it.
    #
    # On a wall the row is the partition top plate's SDPW DEFLECTOR schedule: Simpson's
    # maximum-spacing table for the screw that spans the 3/4" deflection gap
    # (``resolve/partition.DEFLECTION_GAP_M``). ``span`` carries the maximum on-centre
    # SPACING that row publishes and ``carried_span`` the wall height it is indexed by —
    # the two dimensions a spacing table is a function of. See
    # ``checks/structural/partition_fasteners.py`` and
    # ``houses/catlin/notes/partition_top_deflection.md`` §7.4.
    published_span: PublishedSpan | None = None
    # Fork/variant provenance (#38).
    forked_from: str | None = None


@register_element
class Door(Element):
    """A door opening hosted on a wall (→ 10 §Element model)."""

    host: str
    type_ref: str
    position: OpeningPosition
    sill_height: Length | None = None  # exterior threshold override
    arch: Arch | None = None
    flip_hinge: bool = False
    flip_swing: bool = False
    # Per-opening engineered-header override (e.g. '2-ply 14" LVL'); None lets the framing
    # solver size the header. Falls back to the DoorType's header_spec when unset there too.
    header_spec: str | None = None
    # The published table row that answers this member's span, where one does. A
    # manufacturer's table is a PRESCRIPTIVE read — a reviewer opens the document and the
    # question is closed — so authoring one here takes the requirement out of the
    # engineering register rather than into it. See ``model/refs.PublishedSpan``, which
    # carries the drift guards that stop a quotation outliving the model it was read for.
    published_span: PublishedSpan | None = None
    # The maker's ALLOWABLE HOLES chart for the header over this opening, where one is
    # published. No IRC table reaches a header (``resolve/mep_bores.header_bore``), so
    # ``mep.run_through_header`` is UNKNOWN until this row is quoted; with it, every run
    # crossing this header is graded — diameter, zone along the span, band of the depth and
    # spacing. Falls back to the DoorType's ``published_hole`` when unset here.
    published_hole: PublishedHole | None = None


@register_element
class Window(Element):
    """A window opening hosted on a wall."""

    host: str
    type_ref: str
    position: OpeningPosition
    sill_height: Length
    arch: Arch | None = None


@register_element
class RoughOpening(Element):
    """A bare framed/cut opening (pass-through, future penetration host)."""

    host: str
    position: OpeningPosition
    width: Length
    height: Length
    sill_height: Length | None = None
    arch: Arch | None = None
    #: The tags of the runs this hole exists FOR — a duct, pipe or raceway penetration
    #: rather than a pass-through. ``mep.run_through_opening`` grades "a run drawn across the
    #: hole the trades left for something else"; when the something else IS one of these
    #: runs, the crossing is the point. Naming a run here exempts exactly that pairing and
    #: nothing else: any run NOT named crossing this opening is still a finding, and so is a
    #: named run crossing any other opening.
    #:
    #: A TUPLE because one hole routinely serves more than one run. A wall hydrant is the
    #: worked case: the barrel passes through the hole, and the feed that lands on the
    #: hydrant's seat terminates INSIDE it — both belong to the penetration, and naming only
    #: the barrel reported the feed as "a riser in a window". A 1-tuple needs its trailing
    #: comma in the editable dialect; ``haus build --inspect`` is what says so.
    penetration_for: tuple[str, ...] = ()
    #: How far this hole runs INTO the wall from the face it opens on (``depth_from``).
    #: ``None`` — every opening authored before 2026-09-20 — is a THROUGH hole and behaves
    #: exactly as it always did.
    #:
    #: A value makes the hole BLIND: a recess with a back. Only the layers the depth reaches
    #: are cut, the layers outboard of it stay whole, and everything that treats a hole in an
    #: exterior wall as a hole in the ENVELOPE stops applying — it is not fenestration
    #: (``wwr``), it has no U-factor (``energy_load``), it has no reveal to be concentric
    #: with (``reveal_alignment``), and it has no cladding jamb to bear on
    #: (``truss_wall_opening_support``). The cladding and sheathing take no deduction for it.
    #:
    #: The worked case is a firebox pocket: 30" x 25" x 6" into ``W-M-E1``, behind a brick
    #: breast. Authored as a through hole it would delete 4.9 SF of sheathing, foam, girt and
    #: cladding to the east yard and bill as an east-facing window.
    #:
    #: What a blind hole still does is REMOVE STUDS — the framing does not care which side
    #: the back is on — so the stud solver frames it exactly as before.
    depth: Length | None = None
    #: Which face ``depth`` is measured from, and therefore which side the recess OPENS on:
    #: ``"interior"`` (the default) from the room-side finish face, ``"exterior"`` from the
    #: outermost face. Both cases are real and neither is derivable — a firebox pocket opens
    #: into the living room, and a wall hydrant's barrel is admitted from the yard and stops
    #: at its seat inside the cavity without ever piercing the board. Ignored while
    #: ``depth`` is ``None``.
    depth_from: Literal["interior", "exterior"] = "interior"
    #: The maker's ALLOWABLE HOLES chart for this opening's header, where one is published
    #: — the ``Door.published_hole`` field, on the opening kind that carries neither a
    #: ``header_spec`` nor a ``published_span``. ``mep.run_through_header`` reads it.
    published_hole: PublishedHole | None = None


for _name, _obj in (
    ("Node", Node),
    ("Wall", Wall),
    ("Door", Door),
    ("Window", Window),
    ("RoughOpening", RoughOpening),
):
    register_constructor(_name, _obj)

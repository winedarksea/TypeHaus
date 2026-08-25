"""Core plan elements: Node, Wall, and openings (Door/Window/RoughOpening) (→ 11)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element
from typehaus.model.enums import StructuralRole
from typehaus.model.refs import Arch, FaceRef, OpeningPosition, ToRoof
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


@register_element
class Node(Element):
    """A 2D point in a storey's project-north plan frame (auto-tagged N-1…)."""

    position: Point2D
    open_end: bool = False  # a legitimate wing-wall terminus (suppresses gap error)


@register_element
class Wall(Element):
    """An edge between exactly two nodes. Cannot exist without an assembly (→ 11)."""

    start_node: str
    end_node: str
    assembly: str
    # Top constraint — in the schema from day one; only the Length arm resolves in M1.
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
    # Vertical stacking (#43).
    vertical_datum: FaceRef | None = None  # None => storey default
    stacks_on: str | None = None  # tiebreaker: tag of the wall below
    bearing_refs: tuple[str, ...] = ()
    # Per-end corner-framing override ("3-stud" | "4-stud") consumed by the corner
    # solver; None follows the assembly's FramingSpec.corner_style. Authored per wall end
    # because a corner belongs to two walls — the override lives on the end that hosts
    # the extra stud, so two walls never fight over one corner's style.
    corner_style_start: Literal["3-stud", "4-stud"] | None = None
    corner_style_end: Literal["3-stud", "4-stud"] | None = None
    # This wall *is* a guard at an open edge, not an enclosure — a masonry parapet standing
    # where a Railing would otherwise be. A guard is the one thing a wall can be that
    # changes which rules apply to it: R312.1.3 has nothing to measure in solid masonry
    # (it admits no sphere by construction), structural.deck_guard has to see it as the
    # guard the deck is relying on, and its own dead load has to land on something that can
    # carry it (structural.masonry_guard_bearing). Marked rather than inferred: "short wall
    # at a floor edge" describes a knee wall, a planter and a stair curb just as well.
    guard: bool = False
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


for _name, _obj in (
    ("Node", Node),
    ("Wall", Wall),
    ("Door", Door),
    ("Window", Window),
    ("RoughOpening", RoughOpening),
):
    register_constructor(_name, _obj)

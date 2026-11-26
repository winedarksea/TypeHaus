"""A shower's door: kind, entry edge and leaf, the facts the clearance check reads.

Sized to the product (a Flex door, a neo-angle pivot), never drawn from a symbol, so the plan
glyph, the resolved sector and ``shower.door_opening`` read one source. Hinged and pivot
leaves always swing OUT of the compartment; sliding and curtain take no swing.
"""

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch, m

EnclosureKind = Literal["hinged", "pivot", "sliding", "curtain"]
# A local footprint edge (-y is the room-facing one), or the cut corner of a neo-angle pan.
EnclosureEdge = Literal["-y", "+y", "-x", "+x", "diagonal"]


class ShowerEnclosure(HausModel):
    kind: EnclosureKind
    entry_edge: EnclosureEdge
    # The passage with the door open: the product's published figure, graded against the code
    # minimum. A leaf swung to ``max_opening_degrees`` gives ``leaf_width`` of it.
    clear_opening: Length
    leaf_width: Length | None = None
    # Seen from OUTSIDE the entry, looking in.
    hinge: Literal["left", "right"] | None = None
    # Reach of the leaf tip INCLUDING the handle; the leaf width when unset.
    swing_radius: Length | None = None
    max_opening_degrees: float = 90.0
    # Pivot station: along the entry from its hinge end, and the door plane in from the edge.
    hinge_inset: Length = m(0)
    plane_inset: Length = m(0)
    # Other edges carrying fixed glass; every edge not named here or as the entry is a wall.
    fixed_glass_edges: tuple[EnclosureEdge, ...] = ()
    # Recommended room in front of the entry; a design figure, not a code minimum.
    front_zone_depth: Length = inch(24)
    product_ref: str | None = None

    @property
    def swings(self) -> bool:
        return self.kind in ("hinged", "pivot")

    @property
    def reach(self) -> Length:
        """Leaf tip radius; ``leaf_width`` unless a handle stands the tip further out."""
        return self.swing_radius if self.swing_radius is not None else self.leaf_width

    @model_validator(mode="after")
    def _consistent(self):
        if self.clear_opening.meters <= 0:
            raise ValueError("clear_opening must be positive")
        if self.swings:
            if self.leaf_width is None or self.leaf_width.meters <= 0 or self.hinge is None:
                raise ValueError(f"a {self.kind} door needs a leaf_width and a hinge side")
            if self.swing_radius is not None and self.swing_radius.meters < self.leaf_width.meters:
                raise ValueError("swing_radius includes the handle, so it is at least leaf_width")
            if not 0 < self.max_opening_degrees <= 180:
                raise ValueError("max_opening_degrees must be in (0, 180]")
        elif self.hinge is not None or self.swing_radius is not None:
            raise ValueError(f"a {self.kind} enclosure takes no hinge or swing_radius")
        if self.entry_edge in self.fixed_glass_edges:
            raise ValueError("the entry edge is the door, not fixed glass")
        if self.front_zone_depth.meters < 0 or self.hinge_inset.meters < 0 \
                or self.plane_inset.meters < 0:
            raise ValueError("insets and the front zone cannot be negative")
        return self


register_constructor("ShowerEnclosure", ShowerEnclosure)

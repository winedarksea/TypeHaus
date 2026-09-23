"""Surface stormwater inlets: an area drain set in a paved floor.

A :class:`AreaDrain` is where water on a SURFACE enters the buried network — the one thing
a drain tile (which collects from stone) and a leader (which collects from a roof) are not.
"""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


@register_element
class AreaDrain(Element):
    """A grated catch basin in a slab, with a solid outlet riser down to where it lets go.

    ``outlet_invert`` is ABSOLUTE — where the riser's open end lets water go, which on a
    soakaway is inside the stone. ``catchment`` is the open plan area the grate serves;
    storage checks read it as the surface that sheds into this drain.
    """

    position: Point2D
    grate_size: Length          # square grate, side
    basin_depth: Length         # grate top to basin floor
    outlet_diameter: Length
    outlet_invert: Length
    host_ref: str               # the slab the basin is cast into
    #: Top of grate; ``None`` = the host slab's top.
    rim_elevation: Length | None = None
    discharge_ref: str | None = None
    product: str = ""
    outlet_material: str = "pvc"
    catchment: tuple[Point2D, ...] = ()


register_constructor("AreaDrain", AreaDrain)

"""Wall paneling — a room-scoped surface finish band billed by the square foot.

``FinishZone`` is the floor's in-room override; this is the wall's counterpart, and the
first wall-finish concept that exists *outside* an assembly's layer stack. Two jobs:

* **Applied paneling** (a walnut wainscot to 36"): material laid over whatever the wall
  assembly already finishes with. Billed as its own material; nothing subtracted.
* **A finish override** (the tile splash walls inside a wood-lined sauna): the band
  *replaces* the assembly's own FINISH layer there, so it bills as its material and is
  subtracted from the assembly finish behind it — FinishZone semantics, stood upright.

A paneling names its room, not its walls: the resolver derives the bounding walls the same
way every other room-side consumer does (``resolve/room_walls.py``), so a wall split or
renamed under the room does not silently strand the finish. ``walls``/``spans`` narrow the
scope where the material genuinely covers less than the room's shared face.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length


class PanelingSpan(HausModel):
    """A window of one wall's run, measured along the axis from its start node."""

    wall_ref: str
    start: Length
    length: Length


@register_element
class WallPaneling(Element):
    """A finish band on a room's bounding walls (→ ``takeoff/wood_surfaces.py``)."""

    room: str
    material_ref: str
    # Band height above the room floor; None runs to each wall's top.
    height: Length | None = None
    # Band bottom above the room floor (a frieze, a tiled tub surround); None = 0.
    offset: Length | None = None
    # Restrict to these bounding walls; () = every wall the room shares a face with.
    walls: tuple[str, ...] = ()
    # Per-wall windows; () = the full shared run of each wall in scope.
    spans: tuple[PanelingSpan, ...] = ()
    # True: the band replaces the wall assembly's own FINISH layer (billed as this
    # material, subtracted from that one). False: applied over it, nothing subtracted.
    replaces_wall_finish: bool = False


for _name, _obj in (
    ("PanelingSpan", PanelingSpan),
    ("WallPaneling", WallPaneling),
):
    register_constructor(_name, _obj)

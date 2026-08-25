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

Or it names a **layout line** instead. ``room`` did double duty — it *selected* the faces
and it *segmented* the band — and a room lives on one storey, so a band that runs an
exterior facade grade to eave was unauthorable however the walls were chunked. Naming a
line (→ ``resolve/layout_lines.py``) selects that line's walls across every storey it
reaches and measures the band from the line's base rather than each room's floor. The room
path is untouched and stays the default: interior finish genuinely does stop at a room.
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
    """A finish band on a room's bounding walls, or on a layout line's.

    Exactly one of ``room`` / ``layout_line`` is named; naming both or neither is an
    ``integrity.paneling_ref`` error rather than a silent precedence rule
    (→ ``takeoff/wood_surfaces.py``).
    """

    # The room whose bounding walls carry the band. None only when ``layout_line`` names
    # the scope instead.
    room: str | None = None
    # A derived layout line's tag (``LL-<wall>``), when the band belongs to a *facade*
    # rather than to a room: its walls are the line's members, across every storey, and
    # ``offset``/``height`` are measured from the line's base instead of the room floor.
    layout_line: str | None = None
    material_ref: str
    # Band height above the room floor (or the line's base); None runs to each wall's top.
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

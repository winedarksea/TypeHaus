"""Interior millwork — the solid-hardwood pieces a mill cuts, not a lump allowance.

Deliberately *not* ``model/trim.py``: that module's docstring scopes it to envelope edge
runs along a deck or roof edge (fascia, gutter, drip), and an interior stool has nothing to
do with that responsibility (AGENTS.md §1.1). This parallels ``model/paneling.py`` — one
interior-finish concept, in its own file.

Two derived-geometry elements and one declaration:

* :class:`WindowStool` — the interior sill board returning from the window frame to the
  room. Its ``depth`` is normally ``None`` and **derived from the host wall**, because the
  house's windows are *outie*: they sit in a mount plane 6" outboard of the sheathing, and
  ``notes/outie_window_truss_detail.md`` records that no window here carries a depth
  dimension at all — the plane follows the outermost furring layer. An authored stool depth
  would silently drift the first time the wall's foam or girt depth moved, which is exactly
  the failure ``EaveTrim`` exists to prevent on the roof side.
* :class:`ShelfBank` — a run of shelves in one case, bay by bay. A shelf is board stock cut
  to a finished size; a placeable carcass's *symbol* shelves are display geometry built from
  a hard-coded literal (``model/placeable_symbols/_families.py``) and bill nothing.
* :class:`Countertop` — the work surface over a run of base cabinets. Hosted on the
  placeables it covers, so its plan area is *derived* from the run rather than authored:
  a counter is the one piece of millwork whose quantity is a consequence of the layout,
  and a hand-figured square footage in a price file goes stale the first time a cabinet
  moves. It is not drawn — see ``resolve/millwork.py`` for why.
* :class:`MillworkStandard` — declared once, derived many. It states the default stool
  material/thickness/overhang/horn and the *scope* of which windows get a stool, so 39
  near-identical elements never have to be authored, while a per-window ``WindowStool``
  override stays available.

``MillworkStandard`` is an ``Element`` rather than a bare ``HausModel`` for one reason:
``EaveTrim`` nests inside the ``Roof`` it trims, and interior millwork has no such host.
Authoring it as an element is what lets it live in a ``# haus: editable`` file with a uid
``haus fmt`` mints, like everything else the UI can reach. Exactly one per plan; a second is
an ``integrity.millwork_standard`` error rather than a silent precedence rule.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length


@register_element
class WindowStool(Element):
    """The interior sill board under one window, plus its horns.

    ``depth`` is the *finished* board depth, front edge to back edge. Leave it ``None``
    (the normal case) and the resolver derives it from the host wall:

        depth = (interior finish face -> window mount plane) - frame_depth + overhang

    The mount plane is the outer face of the wall's outermost ``FURRING`` layer — the
    cladding nailer the flanges bear on. ``WindowType.frame_depth`` is the only term of
    that sum nothing else in the model knows; absent it the stool reports UNKNOWN and
    carries no depth rather than guessing one (#32).
    """

    window_ref: str
    material_ref: str
    thickness: Length
    # How far the finished board stands proud of the finished interior wall face.
    overhang: Length
    # How far the board runs past the rough opening on EACH side (the horn). Total finished
    # length is the opening width plus twice this.
    horn: Length
    # Finished depth, front edge to back. None = derive from the host wall (the default and
    # the point of the element).
    depth: Length | None = None
    # What the mill runs: "S4S", "eased", "bullnose", ... A stool's front edge is the one
    # part of it anybody touches, so it is a real instruction and not decoration.
    profile: str = "eased"


class ShelfBay(HausModel):
    """One bay of a shelf bank: its clear width, its clear height, its shelf count.

    Per-bay rather than a bank-wide spacing because a raked or stepped case does not divide
    evenly — the attic study's five bays step from a 7'-6" case top down to 4'-6", and a
    uniform spacing would put a shelf through the rake.

    ``shelf_count`` is the number of HORIZONTAL BOARDS in the bay, the case top included:
    the top of a built-in case is cut from the same stock, at the same width, on the same
    day, and a schedule that left it out would under-order every bay by one board.
    ``width`` is the CLEAR width between the bay's partitions — the length a shelf is cut
    to — not the bay's pitch.
    """

    width: Length
    clear_height: Length
    shelf_count: int


@register_element
class ShelfBank(Element):
    """A run of shelves in one case — a built-in pocket or a placeable carcass.

    ``host`` names either a wall tag (a built-in, whose pocket depth is derived from the
    wall's own layers) or a placeable tag (a carcass, whose depth is derived from the
    furniture type's footprint). ``depth`` overrides that derivation, which is what a
    17-1/2" shelf in a 24"-deep pantry needs: a shelf deeper than the available board
    width would otherwise silently become an edge glue-up.
    """

    host: str
    bays: tuple[ShelfBay, ...]
    material_ref: str
    thickness: Length
    # Finished depth, front edge to back. None = derive from the host wall pocket or the
    # carcass footprint depth.
    depth: Length | None = None
    profile: str = "S4S"


@register_element
class Countertop(Element):
    """The work surface over a run of base cabinets — one fabricated slab, one material.

    ``hosts`` names the placeables this slab covers, in run order. It is AUTHORED rather
    than grown from adjacency alone, and the reference house is why: its peninsula's north
    face butts the east run's south face, so a purely geometric walk would hand the
    fabricator one L-shaped slab crossing two orientations, two depths and — after the
    overhang decision below — two materials. Which cabinets share a slab is a fabrication
    judgement (seam placement, slab yield, a material change at the knee), exactly as a
    routed pipe is a judgement (``typehaus/routing``). What the resolver *does* derive is
    everything a judgement cannot state honestly: the run's contiguity (a named gap is an
    error, not a silently longer top), the slab polygon, its area, and the cantilever.

    ``depth`` is the finished depth front edge to back. Leave it ``None`` — the normal case
    — and it derives as the host's carcass depth plus ``overhang``, which is what a top on a
    run against a wall is. Author it only where the slab deliberately stops short of the
    footprint: the reference house's peninsula is a 39" rectangle carrying a 24" stone work
    surface and a 15" wood bar top, meeting at the carcass face.

    ``unsupported_overhang`` is how much of that depth cantilevers past the box. ``None``
    derives it as ``depth - carcass depth``, which is right for a top that starts at the
    carcass back; author it for a slab that sits entirely off the box (that bar top is 15"
    deep and 15" of it is cantilever, and a derivation would report zero).
    """

    hosts: tuple[str, ...]
    material_ref: str
    thickness: Length
    # How far the finished slab stands proud of the carcass face it covers. The ordinary
    # 1"-ish oversail past a door, not the knee: that is ``unsupported_overhang``.
    overhang: Length
    # Finished depth, front edge to back. None = carcass depth + overhang.
    depth: Length | None = None
    # Finished length along the run. None = the run's own extent, which is the point.
    length: Length | None = None
    # None = derived (depth - carcass depth, floored at zero).
    unsupported_overhang: Length | None = None
    # What carries the cantilever: "none" (the slab alone), "corbels", "brackets",
    # "steel-plate". A supported overhang is not a cantilever, and the fabricators' limits
    # are cantilever limits — so this field is the difference between a finding and none,
    # which is why it is a stated fact rather than an inference from a bracket nobody drew.
    support: str = "none"
    # What the fabricator runs on the exposed edge: "eased", "bullnose", "mitred", ...
    profile: str = "eased"


@register_element
class MillworkStandard(Element):
    """The house's millwork defaults, declared once and derived over every window in scope.

    ``stool_assemblies`` / ``stool_rooms`` are the scope: a window gets a derived stool when
    its host wall's assembly tag is listed (and, when ``stool_rooms`` is non-empty, when the
    wall bounds one of those rooms). Empty ``stool_assemblies`` derives nothing — a house
    that has not opted in gets no stools, rather than 45 of them.
    """

    stool_material_ref: str
    stool_thickness: Length
    stool_overhang: Length
    stool_horn: Length
    stool_profile: str = "eased"
    stool_assemblies: tuple[str, ...] = ()
    stool_rooms: tuple[str, ...] = ()
    # Which stairs get hardwood treads, and of what. A ``Stair`` carries no finish material
    # — a tread is a ``FramedMember`` with a deck profile, and which flight is oak and which
    # is carpet lived only in a ``prices.toml`` comment. Naming it here is the same promotion
    # the shelf bays get: from prose nothing can check to data the schedule reads. Empty
    # scopes no stair, which is what a house with no hardwood treads should say.
    tread_material_ref: str | None = None
    tread_stairs: tuple[str, ...] = ()
    # The widest board the supply can produce. An owner-supply fact, not an engine constant
    # and not a price, so it belongs in the house exactly as ``prices.toml`` numbers do
    # (plans/01-decisions.md #28). ``takeoff/hardwood.py`` reads it for the ``layup`` column:
    # a finished width past this cannot come off one board.
    max_board_width: Length


for _name, _obj in (
    ("WindowStool", WindowStool),
    ("ShelfBay", ShelfBay),
    ("ShelfBank", ShelfBank),
    ("Countertop", Countertop),
    ("MillworkStandard", MillworkStandard),
):
    register_constructor(_name, _obj)

"""The plane a foot actually lands on, storey by storey.

A storey elevation is the TOP OF JOISTS. A deck's ``deck_z1_m`` is the top of the subfloor
sheet. Neither is the walking surface: the floor finish stands on the second of those, and
until ``Material.finish_thickness_in`` existed nobody could say by how much — ``Room``
carries a bare ``floor_finish`` tag with no depth. That gap is why catlin's basement flight
climbed to the main joist tops and left an 8 1/4" step onto a floor 15/16" higher, at 0 FAIL
(plans/TODO.md).

Two rules make this honest rather than convenient:

* **Structure and finish are separate answers.** ``deck_top_m`` is measured; ``finish_in``
  may be ``None`` because a covering exists whose depth nobody stated. A reader that wants
  the walking surface gets ``None`` in that case and must report UNKNOWN — never the deck
  top, which would silently under-measure by whatever the finish is.
* **A coating is a sourced zero, not a missing number.** ``Material.coating`` says outright
  that a sealer or a polish has no plane of its own, so a sealed slab resolves to a surface
  exactly at the deck rather than to UNKNOWN.

Leaf module: it reads ``ResolvedModel`` and the plan's material catalog and imports no
check, takeoff or emitter.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Point, Polygon

from typehaus.resolve.model import ResolvedModel

# Deck covers shrink by this before containment. Stair edges and room boundaries are
# authored on the very lines a deck's outline and voids are cut to, so a boundary probe
# otherwise flips between in-void and on-deck on float summation error. 5 mm decides no
# real floor — the same epsilon ``code.R311_7_2_stair_headroom`` samples cover with.
_PLAN_EPS_M = 0.005


@dataclass(frozen=True)
class FloorSurface:
    """What stands at one point, structure and finish stated separately."""

    deck_tag: str
    #: Top of the subfloor sheet, decking, slab or hardscape — always known.
    deck_top_m: float
    #: The room whose finish was read, or ``None`` where no room covers the probe.
    room_tag: str | None
    #: The authored ``floor_finish`` tag, or ``None`` for a bare deck.
    finish_ref: str | None
    #: Inches the finish stands proud of the deck. ``0.0`` for a coating or a bare deck;
    #: ``None`` where a covering exists whose depth the catalog does not state.
    finish_in: float | None

    @property
    def surface_m(self) -> float | None:
        """The plane underfoot, or ``None`` when the finish depth is unstated."""
        if self.finish_in is None:
            return None
        return self.deck_top_m + self.finish_in * 0.0254


def _finish_depth(model: ResolvedModel, finish_ref: str | None) -> float | None:
    """Inches a ``floor_finish`` tag adds, ``0.0`` for a coating, ``None`` if unstated."""
    if finish_ref is None:
        return 0.0
    for material in model.plan.library.materials:
        if material.tag != finish_ref:
            continue
        if material.finish_thickness_in is not None:
            return material.finish_thickness_in
        # A coating is a sourced zero: it is billed by area and has no plane of its own.
        return 0.0 if material.coating else None
    return None


def _covers(model: ResolvedModel, point: tuple[float, float]):
    """(tag, storey, structural top) for every modelled surface standing at ``point``.

    **Deliberately not filtered by storey.** A storey is a filing decision and the question
    here is physical: catlin's garage service flight is filed on ``garage`` at both ends and
    arrives on ``FS-BW-GARAGE``, a deck filed on ``main``, so a storey-scoped lookup finds
    only the slab 2'-10" under its own foot and reports a 27" top riser. The caller
    disambiguates by elevation instead, which is the honest question anyway.

    A framed deck's stair wells are holes in its cover, so a probe inside one finds the deck
    it passes *through* rather than the deck it lands on. Hardscape is included because an
    exterior flight foots on it: a surface's near edge is the one against the building,
    which is the edge a flight meets (the far edge falls 2% away under R401.3).
    """
    probe = Point(*point)
    for floor in model.floors:
        if len(floor.deck_outline) < 3:
            continue
        cover = Polygon(floor.deck_outline,
                        holes=[list(void) for void in floor.deck_voids]
                        ).buffer(-_PLAN_EPS_M)
        if not cover.is_empty and cover.contains(probe):
            yield floor.tag, floor.storey, floor.deck_z1_m
    for solid in model.solids:
        if solid.category != "slab" or len(solid.outline) < 3:
            continue
        cover = Polygon(solid.outline,
                        holes=[list(void) for void in solid.voids]).buffer(-_PLAN_EPS_M)
        if not cover.is_empty and cover.contains(probe):
            yield solid.tag, solid.storey, solid.z1_m
    for surface in getattr(model.plan.project.site, "impervious_surfaces", ()):
        verts = [vertex.xy_m for vertex in surface.outline]
        if len(verts) >= 3 and Polygon(verts).buffer(-_PLAN_EPS_M).contains(probe):
            yield f"'{surface.label}'", None, surface.near_elevation.meters


def surfaces_at(model: ResolvedModel,
                point: tuple[float, float]) -> list[FloorSurface]:
    """Every plane a foot could land on at ``point``, finish resolved, unordered.

    More than one is the normal case, not an error: a bridge deck laps the slab under it,
    and a landing laps the floor it serves. Which one a flight means is an elevation
    question, so this reports them all and leaves that to the caller.
    """
    out: list[FloorSurface] = []
    for tag, storey, top in _covers(model, point):
        room_tag, finish_ref, finish_in = (
            room_finish_at(model, storey, point) if storey is not None
            else (None, None, 0.0))
        # A deck carrying its own ``floor_finish`` outranks the room's, which is the FIELD
        # finish (resolve/rooms.py::_derived_finish_zones bills the same way). Catlin's
        # RM-M-LIVING is the case: it is authored LVP and spans a wood bay and a polished
        # concrete band, and its centroid lands on the band. Taking the room's finish there
        # stood the plank on top of the polish and lifted the floor 6 mm.
        own = _own_finish(model, tag)
        if own is not None:
            finish_ref, finish_in = own, _finish_depth(model, own)
        out.append(FloorSurface(deck_tag=tag, deck_top_m=top, room_tag=room_tag,
                                finish_ref=finish_ref, finish_in=finish_in))
    return out


def _own_finish(model: ResolvedModel, deck_tag: str) -> str | None:
    """The ``floor_finish`` a ``FloorSystem``/``Slab`` states for itself, if any."""
    by_tag = getattr(model.plan, "by_tag", None)
    element = by_tag(deck_tag) if by_tag is not None else None
    return getattr(element, "floor_finish", None)


def room_finish_at(model: ResolvedModel, storey: str, point: tuple[float, float]
                   ) -> tuple[str | None, str | None, float | None]:
    """(room tag, finish ref, inches) for the room covering ``point``, finish alone.

    Split from ``floor_surface_at`` because the two halves are not always asked at the same
    place. A stair's top nosing stands inside its own well, where no deck covers it — the
    arrival deck is the one the well is a hole in — but a ``Room``'s ``clear_face`` is not
    cut by a floor opening, so the room whose finish the flight lands on is readable right
    there. Returns ``(None, None, 0.0)`` where no room covers the probe: outdoors and in a
    garage bay there is no covering to stand on, which is a bare deck, not a missing number.
    """
    probe = Point(*point)
    for room in model.rooms:
        if room.storey != storey or len(room.clear_face) < 3:
            continue
        if Polygon(room.clear_face).covers(probe):
            return room.tag, room.floor_finish, _finish_depth(model, room.floor_finish)
    return None, None, 0.0


def deck_owning_opening(model: ResolvedModel, storey: str,
                        opening_tag: str) -> tuple[str, float] | None:
    """(tag, top of the structural plane) for the deck a FloorOpening is cut in.

    A stair's arrival floor is the deck its well is a hole in, and that cannot be probed in
    plan: every point of the well is inside the hole. The authored element is the one that
    knows, and ``resolve/stairs/dispatch.py`` has already refused any stair whose opening no
    deck on the destination storey owns.
    """
    from typehaus.model.floors import FloorSystem, Slab

    for element in model.plan.storey_elements(storey):
        if not isinstance(element, (FloorSystem, Slab)):
            continue
        if opening_tag not in element.openings:
            continue
        for floor in model.floors:
            if floor.tag == element.tag:
                return floor.tag, floor.deck_z1_m
        for solid in model.solids:
            if solid.tag == element.tag and solid.category == "slab":
                return solid.tag, solid.z1_m
    return None

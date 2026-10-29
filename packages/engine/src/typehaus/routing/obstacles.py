"""Hard obstacles and priced soft volumes, inflated once by radius + clearance.

Hard prisms include opening bucks (not door swings), voids, unsleeved concrete, existing
runs, and --avoid elements. Soft prisms price finished room volume and in-wall travel.
Shared opening/run geometry comes from resolve.mep_envelopes, also read by checks.
Workflow and module map: docs/routing.md."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.solid_categories import is_pour_slab

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: How much clear air a run wants beyond its own radius. Half an inch is a hanger's strap
#: and the tolerance a trade actually works to; it is deliberately smaller than the 2"
#: ``HANGER_GAP_M`` two ducts want between each other, because that gap is about hanging
#: two things and this one is about not touching one.
CLEARANCE_M = 0.0127


@dataclass(frozen=True)
class HardPrism:
    """A plan footprint and a z band the route may not enter. Already inflated."""

    tag: str
    kind: str  # opening | void | stair | member | beam | concrete | run | clear_zone | avoid
    footprint: Any  # shapely Polygon
    z0_m: float
    z1_m: float

    def blocks(self, point: tuple[float, float], z: float) -> bool:
        from shapely.geometry import Point

        return (self.z0_m <= z <= self.z1_m
                and self.footprint.covers(Point(point)))


@dataclass(frozen=True)
class SoftPrism:
    """A plan footprint and z band the route may enter at a stated per-foot price.

    ``occupancy`` is carried rather than the price itself, so one :class:`RouteCost` can
    reprice a whole world without rebuilding it — which is what makes ``--explain`` able
    to say what a different weight would have chosen.
    """

    tag: str
    kind: str  # "room" | "wall"
    footprint: Any
    z0_m: float
    z1_m: float
    occupancy: str | None = None


def _polygon(ring: Any) -> Any:
    """Convert either a raw (x, y) ring or a Length-based Point2D ring to a polygon.

    Room footprints are raw resolved tuples; floor voids retain authored Point2D values.
    Return None for an absent/degenerate ring."""
    from shapely.geometry import Polygon

    if ring is None or len(ring) < 3:
        return None
    points = [p.xy_m if hasattr(p, "xy_m") else p for p in ring]
    try:
        poly = Polygon(points)
    except (TypeError, ValueError):
        return None  # a ring of something this does not know how to read
    if not poly.is_valid or poly.is_empty:
        return None
    return poly


def hard_prisms(model: ResolvedModel, radius_m: float, *, avoid: frozenset[str] = frozenset(),
                touch: frozenset[str] = frozenset(),
                clearance_m: float = CLEARANCE_M) -> list[HardPrism]:
    """Forbidden prisms, inflated by radius + clearance.

    ``avoid`` adds hard element tags. ``touch`` exempts runs being replaced or joined so a
    branch can reach its parent. Shared envelopes come from resolve.mep_envelopes."""
    from typehaus.resolve.mep_envelopes import opening_prisms

    inflate = radius_m + clearance_m
    out: list[HardPrism] = []

    # **Un-eroded, and that is the whole difference from the check's reading.** A raceway
    # strapped to a jack stud shares a coordinate with the opening beside it, and
    # ``mep.run_through_opening`` must not report that; a router must not PROPOSE it
    # either, and half an inch of tolerance is exactly the width of the lane it would
    # propose. The check's tolerance is forgiveness after the fact and the router has
    # nothing to forgive, so the two are one derivation with one parameter.
    for tag, _is_door, _host, prism, low, high, _for in opening_prisms(model, erode_m=0.0):
        grown = prism.buffer(inflate)
        if grown.is_empty:
            continue
        out.append(HardPrism(tag=tag, kind="opening", footprint=grown,
                             z0_m=low - inflate, z1_m=high + inflate))

    # A swinging leaf's quadrant, below the head (``mep.run_through_opening`` grades it too).
    from typehaus.resolve.mep_door_swing import door_swing_prisms

    for tag, _host, sector, low, high, _for in door_swing_prisms(model):
        out.append(HardPrism(tag=tag, kind="opening", footprint=sector.buffer(inflate),
                             z0_m=low - inflate, z1_m=high + inflate))

    # Deck voids, less the walls that cross them: a run over a void has nothing to strap
    # to unless a wall carries it, which is exactly ``mep.run_over_void``'s reading.
    cover = _wall_union(model)
    for floor in model.floors:
        joists = [m.z0_m for m in floor.members if m.z0_m is not None]
        low = min(joists) if joists else floor.deck_z0_m
        for ring in (floor.deck_voids or ()):
            poly = _polygon(ring)
            if poly is None:
                continue
            if cover is not None:
                poly = poly.difference(cover)
            poly = poly.buffer(inflate)
            if poly.is_empty:
                continue
            out.append(HardPrism(tag=floor.tag, kind="void", footprint=poly,
                                 z0_m=low - inflate,
                                 z1_m=floor.deck_top_range(ring)[1] + inflate))

    # A flight's R311.7.2 headroom and its own structure (``resolve/stair_headroom``, the
    # volume the check grades). Fixed: nobody moves a stair to make room for a duct. Goings
    # are PAIRED here (z band the pair's envelope): every riser was a lattice line, and one
    # per going took DU-B-ERV-R-SAUNA-SUP over MAX_LATTICE_NODES. The check stays exact.
    from itertools import groupby

    from typehaus.resolve.stair_headroom import headroom_prisms

    for _key, flight in groupby(headroom_prisms(model), key=lambda p: (p.stair_tag, p.flight)):
        goings = list(flight)
        for start in range(0, len(goings), _GOINGS_PER_PRISM):
            pair = goings[start:start + _GOINGS_PER_PRISM]
            out.append(HardPrism(tag=pair[0].stair_tag, kind="stair",
                                 footprint=_going_footprint(pair, inflate),
                                 z0_m=min(g.z0_m for g in pair) - inflate,
                                 z1_m=max(g.z1_m for g in pair) + inflate))

    # Open-web truss WEBS, where the deck states its fabricator's panel layout. An
    # open-web member hands a service its 8 7/8" chord-to-chord space and nothing narrowed
    # it ALONG the span, so the router read a floor truss as a continuous chase and would
    # lane a duct straight through a web. These are ``fixed`` — a web is not bored, notched
    # or moved by anybody — so a search threads the openings by construction rather than
    # being told off by a check afterwards.
    #
    # Unauthored is silence here too: no layout, no prisms, and the reading is exactly what
    # it was. ``mep.open_web_panel`` is the one that says the layout is missing.
    from typehaus.resolve.mep_crossings import member_window, web_panels

    for floor in model.floors:
        panels = web_panels(floor)
        window = member_window(floor) if panels is not None else None
        if panels is None or window is None or window.kind != "open_web":
            continue
        along_x = floor.direction == "x"
        for member in floor.members:
            if member.category != "joist" or member.z0_m is None:
                continue
            low, high = sorted((member.p0[0], member.p1[0]) if along_x
                               else (member.p0[1], member.p1[1]))
            breadth = _member_breadth(member)
            across = member.p0[1] if along_x else member.p0[0]
            for start, end in panels.web_bands(low, high):
                corners = ([(start, across - breadth), (end, across - breadth),
                            (end, across + breadth), (start, across + breadth)]
                           if along_x else
                           [(across - breadth, start), (across + breadth, start),
                            (across + breadth, end), (across - breadth, end)])
                poly = _polygon(corners)
                if poly is None:
                    continue
                out.append(HardPrism(tag=floor.tag, kind="member",
                                     footprint=poly.buffer(inflate),
                                     z0_m=window.z0_m - inflate,
                                     z1_m=window.z1_m + inflate))

    # Beams: a carrier is not bored for a run, and ``mep.run_through_beam`` reads the same
    # sections (``resolve/beam_sections``).
    from typehaus.resolve.beam_sections import beam_sections

    for tag, footprint, z0, z1 in beam_sections(model):
        out.append(HardPrism(tag=tag, kind="beam", footprint=footprint.buffer(inflate),
                             z0_m=z0 - inflate, z1_m=z1 + inflate))

    # Concrete. Only the bands that are actually concrete — a stay-in-place foam deck form
    # is not a pour, and ``resolve/mep_queries.concrete_bands`` is the one place that
    # reading lives.
    from typehaus.resolve.mep_queries import concrete_bands

    for solid in model.solids:
        if not (solid.category == "footing" or is_pour_slab(solid.category)):
            continue
        poly = _polygon(solid.outline)
        if poly is None:
            continue
        grown = poly.buffer(inflate)
        for z0, z1 in concrete_bands(model, solid):
            out.append(HardPrism(tag=solid.tag, kind="concrete", footprint=grown,
                                 z0_m=z0 - inflate, z1_m=z1 + inflate))

    # Existing runs. A proposal that occupies a lane something else already has is not a
    # proposal, and this is the only obstacle class whose membership the caller edits by
    # deleting the run it is re-routing.
    #
    # **One prism per SEGMENT, over that segment's own z range.** What stood here buffered
    # a run's whole plan polyline and banded it over ``min(z)..max(z)``, so a branch that
    # drops six feet at one end blocked a full-height wall along its entire length — which
    # is how a perfectly clear lane comes back as "every lane is blocked". The per-segment
    # reading is ``resolve/mep_envelopes``, which the checks read too.
    #
    # **A segment is still BANDED over its own fall here, and that is deliberate.**
    # ``mep.run_interference`` stopped grading the band on 2026-09-19 and measures the real
    # clearance at the station instead (``resolve/mep_clearance``); a router may not. A
    # check is READING a drawn run and can say where it is; a router is CHOOSING and has to
    # stay out of everywhere the run might be, because the lane it picks has to survive the
    # next person moving a vertex by an inch. The two readings differ on purpose and each
    # says so.
    from typehaus.resolve.mep_envelopes import envelopes

    for envelope in envelopes(model, inflate_m=inflate):
        if envelope.tag in avoid or envelope.tag in touch:
            continue
        for prism in envelope.prisms:
            out.append(HardPrism(tag=envelope.tag, kind="run", footprint=prism.footprint,
                                 z0_m=prism.z0_m, z1_m=prism.z1_m))

    # A reservation keeps its finite band even when also named by --avoid.
    zone_tags = {zone.tag for zone in model.clear_zones}
    for zone in model.clear_zones:
        poly = _polygon(zone.outline)
        if poly is not None:
            out.append(HardPrism(tag=zone.tag, kind="clear_zone",
                                 footprint=poly.buffer(inflate),
                                 z0_m=zone.z0_m - inflate, z1_m=zone.z1_m + inflate))

    for tag in sorted(avoid - zone_tags):
        element = model.plan.by_tag(tag)
        poly = _polygon(getattr(element, "outline", None))
        if poly is not None:
            out.append(HardPrism(tag=tag, kind="avoid", footprint=poly.buffer(inflate),
                                 z0_m=float("-inf"), z1_m=float("inf")))
    return out


_GOINGS_PER_PRISM = 2


def _going_footprint(goings: list[Any], inflate: float) -> Any:
    """Consecutive goings, inflated across the flight and past its ends but NOT at a riser.

    Every prism's bounds are lattice lines, so a going grown on all four sides put two lines
    at each riser; adjacent goings meeting on the shared station line put one. Both keep the
    same clearance around the flight as a whole. Mitred, because arc vertices are lines too.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import intersection

    def across(edge: Any, reach: float) -> tuple[Any, Any]:
        (ax, ay), (bx, by) = edge
        length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 or 1.0
        ux, uy = (bx - ax) / length, (by - ay) / length
        return (ax - ux * reach, ay - uy * reach), (bx + ux * reach, by + uy * reach)

    def along(edge: Any, other: Any, reach: float) -> tuple[Any, Any]:
        mid = ((edge[0][0] + edge[1][0]) / 2.0, (edge[0][1] + edge[1][1]) / 2.0)
        far = ((other[0][0] + other[1][0]) / 2.0, (other[0][1] + other[1][1]) / 2.0)
        length = ((mid[0] - far[0]) ** 2 + (mid[1] - far[1]) ** 2) ** 0.5 or 1.0
        dx, dy = (mid[0] - far[0]) / length * reach, (mid[1] - far[1]) / length * reach
        return tuple((x + dx, y + dy) for x, y in edge)

    from typehaus.resolve.overlay import union_all

    head, tail = goings[0], goings[-1]
    grown = union_all([g.footprint for g in goings]).buffer(inflate, join_style="mitre")
    near = along(head.near, head.far, inflate) if head.first else head.near
    far = along(tail.far, tail.near, inflate) if tail.last else tail.far
    big = 10.0 * (inflate + 1.0)
    (n0, n1), (f0, f1) = across(near, big), across(far, big)
    strip = Polygon([n0, n1, f1, f0])
    if not strip.is_valid:
        return grown
    clipped = intersection(grown, strip)
    return grown if clipped.is_empty else clipped


def soft_prisms(model: ResolvedModel) -> list[SoftPrism]:
    """Every prism a route may enter for a price: finished room air, and wall cavities.

    The room band is the same one ``mep.run_in_finished_volume`` grades against — the
    storey datum up to ``ResolvedCeiling.z0_m`` — because a router aimed at a different
    band from the check that will judge it is a router nobody will take a line from. A
    ``FollowRoof`` ceiling resolves no plane and so contributes no prism: the check reports
    those rooms UNKNOWN, and the cost function is silent about them for the same reason.
    """
    storey_z = {s.tag: s.elevation.meters for s in model.plan.storeys}
    # ``Room.closed_to_services`` is priced as finished air, as the check grades it:
    # "living" is the table's price for a room people are in.
    occupancies = {room.tag: "living" if room.closed_to_services else room.occupancy
                   for room in model.rooms}
    out: list[SoftPrism] = []
    for ceiling in model.ceilings:
        if ceiling.z0_m is None:
            continue
        poly = _polygon(ceiling.outline)
        if poly is None:
            continue
        out.append(SoftPrism(tag=ceiling.room_ref, kind="room", footprint=poly,
                             z0_m=storey_z.get(ceiling.storey, 0.0),
                             z1_m=ceiling.z0_m,
                             occupancy=occupancies.get(ceiling.room_ref)))
    for wall in model.walls:
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        poly = _polygon(structure.polygon) if structure is not None else None
        if poly is None:
            continue
        out.append(SoftPrism(tag=wall.tag, kind="wall", footprint=poly,
                             z0_m=wall.z0_m, z1_m=wall.z1_m))
    return out


def _wall_union(model: ResolvedModel) -> Any:
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    polygons = [Polygon(layer.polygon)
                for wall in model.walls for layer in wall.layers
                if len(layer.polygon) >= 3]
    valid = [p for p in polygons if p.is_valid and not p.is_empty]
    return union_all(valid) if valid else None


def inches(metres: float) -> float:
    """Metres to inches — the unit every cost term in this package is stated in."""
    return metres / M_PER_IN


def _member_breadth(member) -> float:
    """Half a member's plan width, for the web rectangles above.

    Same reading and same fallback as ``mep_queries._JOIST_BREADTH_FALLBACK_M``: an
    unparsed profile errs toward a NARROWER obstacle, so a router is never blocked by a
    guess.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(member.profile)
    return (getattr(section, "width_m", None) or 0.0381) / 2.0

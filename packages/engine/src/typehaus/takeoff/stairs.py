"""Stair finish: treads, risers and landing decking as a millwork order.

The stringers, joists and rims already bill as lumber through ``framing_takeoff`` — they are
``FramedMember``s with a profile like every other stick. The *finish* does not, and it is a
different order from a different supplier: a tread is a milled hardwood board with a bullnose
and a riser is a finished board, both counted by the piece and priced by the run, not bought
as 2x stock by the lineal foot.

Counting is off the resolved members rather than off ``riser_count``, so a stair with winders
bills the winders it actually generated. A closed riser is a ``riser`` member
(``Stair.riser_thickness``) and bills like a tread; an open-riser flight buys none.
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel, ResolvedStair
from typehaus.resolve.room_lookup import axis_polygon, axis_ring
from typehaus.takeoff.labels import _fraction_in

_M_TO_FT = 3.280839895
_M2_TO_FT2 = 10.7639104

# The walking surfaces a stair buys as finish goods, and what each is ordered as.
_TREAD_CATEGORIES = ("tread", "winder")
_LANDING_CATEGORY = "landing"
_RISER_CATEGORY = "riser"


def separate_stair_wear_members(model: ResolvedModel):
    """Walking surfaces and risers in a finish material, ordered by the piece, not as lumber.

    A tread, winder or landing is a finish good when it carries a material other than its
    flight's carriage — an oak tread over SPF stringers, or a composite tier over a PT box.
    One whose material IS the flight's (a PT exterior stair) stays in the lumber order.
    """
    for _stair, member in _wear_members(model):
        yield member


def _wear_members(model: ResolvedModel):
    for stair in model.stairs:
        authored = model.plan.by_tag(stair.tag)
        if not isinstance(authored, Stair) or authored.carriage == "cast":
            continue
        for member in stair.members:
            if (member.category in (*_TREAD_CATEGORIES, _LANDING_CATEGORY, _RISER_CATEGORY)
                    and member.material is not None and member.material != authored.material):
                yield stair, member


def winder_blank_in(member, nosing_m: float) -> tuple[float, float]:
    """``(width, length)`` in inches of the rectangle a winder is cut from.

    The physical polygon already includes the nose and rear fit. Grain runs along its
    leading nosing; rough milling allowances belong to the millwork schedule.
    """
    del nosing_m  # retained for callers; projecting a physical panel adds no second nose
    ring, edge = member.plan_outline, member.nosing_line
    if not ring or edge is None:
        raise ValueError("a winder millwork blank needs its physical outline and nosing")
    (ax, ay), (bx, by) = edge
    span = math.hypot(bx - ax, by - ay)
    if span < 1e-9:
        raise ValueError("a winder nosing must have positive length")
    ux, uy = (bx - ax) / span, (by - ay) / span
    along = [(x - ax) * ux + (y - ay) * uy for x, y in ring]
    across = [(x - ax) * -uy + (y - ay) * ux for x, y in ring]
    return ((max(across) - min(across)) / 0.0254,
            (max(along) - min(along)) / 0.0254)


def stair_tread_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Finish walking surfaces by the piece: one row per (stair, use, material, size).

    What the stair installer quotes. ``supply`` says who buys the stock: a material that
    ``requires_custom_milling`` is owner-milled (its rough board order is ``haus millwork``),
    so the line is labour only.
    """
    materials = {material.tag: material for material in model.plan.library.materials}
    stairs = {stair.tag: stair for stair in model.stairs}
    groups: dict[tuple[str, str, str, float, float, float], int] = {}
    for stair, member in _wear_members(model):
        section = cross_section(member.profile)
        # A landing's member is the whole 1 1/2" deck; its finish field states its own board.
        finish = getattr(materials.get(str(member.material)), "finish_thickness_in", None)
        thickness = finish or min(section.width_m, section.depth_m) / 0.0254
        width = max(section.width_m, section.depth_m) / 0.0254
        length = member.length_m / 0.0254
        if member.category == "winder":
            width, length = winder_blank_in(member, stair.nosing_depth_m)
        key = (stair.tag, member.category, str(member.material), round(thickness, 3),
               round(width, 2), round(length, 2))
        groups[key] = groups.get(key, 0) + 1
    rows: list[dict[str, object]] = []
    for (tag, use, material_ref, thickness, width, length), pieces in sorted(groups.items()):
        material = materials.get(material_ref)
        milled = bool(getattr(material, "requires_custom_milling", False))
        name = getattr(material, "name", material_ref)
        supply = "owner-milled" if milled else "purchased"
        rows.append({
            "stair": tag, "use": use, "material": material_ref, "supply": supply,
            "pieces": pieces, "thickness_in": thickness, "width_in": width, "length_in": length,
            "area_sqft": round(pieces * width * length / 144.0, 1),
            "conditioned": _in_conditioned_space(model, stairs[tag]),
            "description": (f"Stair {use}, {name}, {_fraction_in(thickness)} x "
                            f"{_fraction_in(width)} x {_fraction_in(length)}"
                            + (", owner-furnished (install only)" if milled else "")),
            "tags": [tag],
        })
    return rows


def cast_stair_members(model: ResolvedModel):
    """Members of a flight whose construction is authored as pours, not as this flight.

    A ``carriage="cast"`` stair still resolves tread members — every rule that grades a
    stair reads them, and a flight with no walking surface grades as UNKNOWN width and FAILS
    R311.7 outright — but its concrete is billed by the ``Slab`` elements that ARE the tiers.
    Left in ``all_members()`` unfiltered these would bill as 2x stock by the lineal foot,
    which is the opposite of what they are, so ``framing_takeoff`` drops them here. They are
    NOT wear members either: a cast nosing is not a finish good ordered by the piece.
    """
    for stair in model.stairs:
        authored = model.plan.by_tag(stair.tag)
        if isinstance(authored, Stair) and authored.carriage == "cast":
            yield from stair.members


def _in_conditioned_space(model: ResolvedModel, stair: ResolvedStair) -> bool:
    """Does this stair stand in a conditioned room?

    ``ResolvedStair`` carries a ``storey`` and an ``outline`` but no room reference, so the
    question is answered geometrically: the centroid of the outline against ``axis_face``
    for every room on the same storey (the containment test ``checks/mep/exhaust.py``
    already uses to name the room a duct end lands in).

    A stair that lands in no room at all is reported **conditioned**, which is the safe
    default for a *finish* schedule: an unrecognised stair keeps its nosing in the bill
    rather than silently dropping scope, and the reader sees a row either way.
    """
    from shapely.geometry import Polygon

    if len(stair.outline) < 3:
        return True
    probe = Polygon(stair.outline).centroid
    for room in model.rooms:
        if room.storey != stair.storey or len(axis_ring(room)) < 3:
            continue
        if axis_polygon(room).covers(probe):
            return room.conditioned
    return True


def _lip_length_m(part) -> float:
    """A lip's run: the longer side of its plan rectangle."""
    (a, b, c, *_rest) = part.outline
    return max(math.dist(a, b), math.dist(b, c))


def stair_finish_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per stair: treads and risers by the piece, landing decking by the square foot.

    Tread width is the member's own run length, so a winder's tapered board bills at its wide
    end — which is the blank a millwork shop cuts it from, not the average of its two ends.

    ``conditioned`` is a **column, not a filter**: the row stays whatever it says. A stair in
    unconditioned space still buys treads, risers and stringers, and a schedule that dropped
    it would hide a real stair from the reader — ``test_bom_sweep`` asserts every stair tag
    appears here for exactly that reason. What the flag is for is the scopes that only exist
    where a finish floor meets the stair: nosings, thresholds, transition strips. Those a
    price row can select with ``[conditioned=True]`` rather than a rate hand-corrected by
    a ratio.

    ``has_nosing`` is the second such column, and ``conditioned`` alone was not enough.
    ``_in_conditioned_space`` reports a stair that lands in **no room at all** as
    conditioned — the safe default for a finish schedule, since an unrecognised stair should
    keep its scope rather than silently drop it. An OUTDOOR stair stands in no ``Room``, so
    it takes that default and buys nosing it cannot have. A driver filter can only *include*
    (it compares ``str(value)`` for equality), so "everything except the outdoor one" is not
    expressible; ``nosing_depth > 0`` is, it is authored on the stair rather than inferred,
    and it is the actual physical question a nosing allowance is asking.
    """
    rows: list[dict[str, object]] = []
    for stair in sorted(model.stairs, key=lambda item: item.tag):
        treads = [m for m in stair.members if m.category in _TREAD_CATEGORIES]
        landings = [m for m in stair.members if m.category == _LANDING_CATEGORY]
        risers = [m for m in stair.members if m.category == _RISER_CATEGORY]
        if not treads and not landings:
            continue
        tread_lf = sum(m.length_m for m in treads)
        widest = max((m.length_m for m in treads), default=0.0)
        landing_area = sum(
            m.length_m * cross_section(m.profile).width_m for m in landings)
        tread_area = sum(Polygon(m.plan_outline).area if m.plan_outline
                         else m.length_m * cross_section(m.profile).width_m for m in treads)
        authored = model.plan.by_tag(stair.tag)
        rows.append({
            "stair": stair.tag,
            "conditioned": _in_conditioned_space(model, stair),
            "has_nosing": stair.nosing_depth_m > 0.0,
            "treads": len(treads),
            "tread_run_in": round(stair.tread_depth_m / 0.0254, 2),
            "tread_lf": round(tread_lf * _M_TO_FT, 1),
            "tread_material": getattr(authored, "tread_material", None)
                              or getattr(authored, "material", None),
            "tread_area_sqft": round(tread_area * _M2_TO_FT2, 1),
            "widest_tread_ft": round(widest * _M_TO_FT, 2),
            "risers": len(risers),
            "riser_height_in": round(stair.riser_height_m / 0.0254, 2),
            "riser_lf": round(sum(m.length_m for m in risers) * _M_TO_FT, 1),
            "landing_decks": len(landings),
            "landing_area_sqft": round(landing_area * _M2_TO_FT2, 1),
            # Nosings on landing and floor edges (R311.7.5.3): the resolved lips' run.
            "lip_lf": round(sum(_lip_length_m(p) for p in stair.finish_parts
                                if p.role == "landing-nosing") * _M_TO_FT, 1),
        })
    return rows

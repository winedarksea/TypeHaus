"""Which details exist, and where each one cuts — the derivation half of A-4xx.

One detail is scaffolded per distinct bound condition key: this module decides the cut
plane, direction and extent from the resolved model, and hands ``details.py`` a
:class:`DerivedDetail` to draw. The seam is real — the server's ``/details`` endpoints
need the index and the payload without ever building a scene.
"""

from __future__ import annotations

import hashlib
import math
import weakref
from dataclasses import dataclass

from typehaus.emit.draw.detail_station import (
    clear_fraction,
    floor_fractions,
    stack_has_floor,
    stack_pair,
)
from typehaus.model.enums import SliceKind
from typehaus.model.patterns import first_match
from typehaus.model.views import Slice
from typehaus.quantities import m, pt
from typehaus.resolve.detail_keys import detail_keys
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals, slice_solid
from typehaus.resolve.model import BoundaryCondition, ResolvedModel


@dataclass(frozen=True)
class DerivedDetail:
    """One scaffolded transition detail: a cut slice + its bound condition/transition."""

    key: str
    condition: BoundaryCondition
    transition: object | None  # model.views.Transition, if a binding matched
    view: Slice
    direction: str
    station: float
    part: str | None = None  # "head" | "sill" on an enlarged child (``enlarged_details``)
    opening_kind: str | None = None  # "window" | "door" where one key holds both


def _matched_transition(model: ResolvedModel, cond: BoundaryCondition, key: str | None = None):
    """The binding of a detail key, falling back to its condition's own key: a qualified
    opening key (``opening_kind_key``) takes its assembly's transition unless one names it."""
    transitions = model.plan.library.transitions
    return (key and first_match(transitions, key)) or first_match(transitions, cond.key)


def _host_wall(model: ResolvedModel, cond: BoundaryCondition):
    """The wall the condition is about — named directly, or via its opening's host.

    ``opening_perimeter`` conditions carry the *opening's* tag, so the wall has to be
    reached through ``ResolvedOpening.host_wall``; without that hop every opening
    condition silently derived no detail at all.
    """
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    walls = condition_walls(model, cond)
    return walls[0] if walls else None


def _condition_opening(model: ResolvedModel, cond: BoundaryCondition):
    from typehaus.emit.draw.detail_components.geometry import condition_opening

    return condition_opening(model, cond)


#: ``id(model) -> (weakref, signature, details)``. Sheet numbering re-derives the whole set for
#: every detail, callout and schedule row (~0.2 s a call on catlin, 81 calls per print).
_DERIVED_CACHE: dict[int, tuple[weakref.ref, tuple, tuple[DerivedDetail, ...]]] = {}


def _signature(model: ResolvedModel) -> tuple:
    """Cheap staleness guard for a model mutated after a first derive (tests do)."""
    return (id(model.plan), len(model.walls), len(model.solids), len(model.junctions),
            len(model.conditions))


def derive_detail_slices(model: ResolvedModel) -> list[DerivedDetail]:
    """:func:`_derive_detail_slices`, memoized per model object."""
    hit = _DERIVED_CACHE.get(id(model))
    signature = _signature(model)
    if hit is not None and hit[0]() is model and hit[1] == signature:
        return list(hit[2])
    details = _derive_detail_slices(model)
    key = id(model)
    _DERIVED_CACHE[key] = (weakref.ref(model, lambda _ref: _DERIVED_CACHE.pop(key, None)),
                           signature, tuple(details))
    return details


def _derive_detail_slices(model: ResolvedModel) -> list[DerivedDetail]:
    """One derived DETAIL slice per distinct bound condition key (skip authored-claimed keys).

    The cut plane runs perpendicular to the host wall at its midpoint, slid clear of any
    opening (``clear_fraction``); the crop is a junction
    z-window × u-window sized to the junction kind.
    """
    claimed = {
        s.condition_key for s in model.plan.elements_of_kind("Slice")
        if getattr(s, "condition_key", None)
    }
    out: list[DerivedDetail] = []
    seen: set[str] = set()
    keyed = detail_keys(model)
    for cond, key, opening_kind in keyed:
        if key in seen or key in claimed:
            continue
        tr = _matched_transition(model, cond, key)
        if tr is None:
            continue  # unbound conditions are the coverage check's concern, not a detail
        if getattr(tr, "suppress", False):
            seen.add(key)
            continue  # bound-but-suppressed: covered for integrity, no sheet derives
        wall = _host_wall(model, cond)
        if wall is None:
            # roof_ridge conditions carry a roof and a beam, never a wall — the cut frame
            # comes from the ridge member instead.
            if cond.kind.value == "roof_ridge":
                derived = _build_ridge_derived(model, cond, tr)
                if derived is not None:
                    seen.add(key)
                    out.append(derived)
            continue
        seen.add(key)
        if cond.kind.value in _STACK_KINDS:
            derived = _stack_detail(model, key, [c for c, k, _ in keyed if k == key])
        else:
            derived = _build_derived(model, cond, tr, wall, key, opening_kind)
        if derived is not None:
            out.append(derived)
    out.sort(key=lambda d: d.key)
    return out


_STACK_KINDS = frozenset({"storey_stack", "stack_width_change"})


def _stack_detail(model, key: str, conds) -> DerivedDetail | None:
    """The stack detail of ``key``, cut where a floor member of the floor between the walls
    is cut (REPORT §1.17): the default station first, then joist/rim lines, then the key's
    other conditions. A rim band with no floor in frame at any station (stacking pairs walls
    across storeys that carry no wall on the line, or the floor is open at a stair well)
    derives no detail; a stack shelf (width change) keeps its default cut, since the step
    in the wall is its subject."""
    fallback = None
    for cond in conds:
        tr = _matched_transition(model, cond, key)
        wall = _host_wall(model, cond)
        lower, upper = stack_pair(model, cond)
        if tr is None or wall is None or upper is None:
            continue
        derived = _build_derived(model, cond, tr, wall, key)
        if derived is None:
            continue
        if stack_has_floor(model, derived, upper):
            return derived
        base_t = clear_fraction(model, cond, wall)
        for t in floor_fractions(model, cond, wall, upper, base_t):
            moved = _build_derived(model, cond, tr, wall, key, t_override=t)
            if moved is not None and stack_has_floor(model, moved, upper):
                return moved
        fallback = fallback or derived
    return fallback if conds[0].kind.value == "stack_width_change" else None


# Per junction kind: how far the crop reaches (metres) below/above the junction plane, and
# beyond the wall's inboard/outboard faces. A detail is a close-up — the window has to hold
# the junction and the things drawn around it (footing, drain and grade below a foundation;
# the overhang and gutter outboard of an eave) and nothing else, or it reads as a sliver
# floating in white space.
_CROP_WINDOWS = {
    #                     below,  above,  inboard, outboard
    # wall_roof reaches further above the junction (the plate top) since eave_z_m became
    # the deck plane: the rafter rises ~0.27 m above the plate before the roof stack starts.
    "wall_roof":         (0.75,   0.75,   0.30,    0.35),
    "wall_foundation":   (1.30,   0.90,   0.55,    0.90),
    "wall_slab":         (1.00,   0.70,   0.55,    0.70),
    "storey_stack":      (0.55,   0.55,   0.25,    0.25),
    "stack_width_change": (0.50,  0.50,   0.25,    0.25),
    "assembly_change":   (0.50,   0.50,   0.30,    0.30),
    # opening_perimeter measures below from the *sill* and above from the *head* (the crop
    # holds the whole opening); the u margins clear the frame's interior/exterior returns.
    "opening_perimeter": (0.45,   0.45,   0.25,    0.25),
    # roof_ridge has no wall faces: the u margins measure symmetrically off the ridge line,
    # wide enough to hold the beam, its hangers and the first stretch of rafter each side.
    "roof_ridge":        (0.90,   0.45,   0.75,    0.75),
}
_DEFAULT_WINDOW = (0.50, 0.50, 0.25, 0.25)


def _wall_u_extent(wall, direction: str, station: float,
                   fallback_center: float) -> tuple[float, float]:
    """The wall's inboard/outboard face positions in section coordinates."""
    plane = CutPlane(axis=direction, station_m=station)
    bounds: list[float] = []
    for layer in wall.layers:
        for (u0, u1) in ring_intervals(layer.polygon, plane):
            bounds.extend((u0, u1))
    if not bounds:
        half = wall.thickness_m / 2.0
        return fallback_center - half, fallback_center + half
    return min(bounds), max(bounds)


def _junction_z(model, cond, wall, direction: str | None = None,
                station: float | None = None) -> float:
    """The elevation the detail is *about* — what the crop's below/above measure from.

    For the stacked kinds that is the *shared* plane between the two elements, i.e. the top
    of the lower one. Using the host wall's own base instead put the foundation detail a
    storey below its own junction, showing the footing and nothing of the wall it carries.
    An opening's plane is its own mid-height (the crop then reaches past sill and head);
    a ridge's is the ridge elevation itself, wall or no wall.
    """
    kind = cond.kind.value
    if kind == "roof_ridge":
        roof = next((r for r in model.roofs if r.tag in cond.element_tags), None)
        if roof is not None:
            return roof.ridge_z_m
    if kind == "opening_perimeter" and wall is not None:
        opening = _condition_opening(model, cond)
        if opening is not None:
            return wall.base_ref_z_m + opening.sill_m + opening.height_m / 2.0
    top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    if kind == "wall_roof":
        # A raked (gable) top is read AT the cut, not at the wall's end (A-592 was blank).
        return _top_at(wall, direction, station) if station is not None else top
    if kind in ("wall_foundation", "storey_stack", "stack_width_change", "assembly_change"):
        walls = [w for w in (model.wall(tag) for tag in cond.element_tags) if w is not None]
        if len(walls) >= 2:
            lower = min(walls, key=lambda w: w.z0_m)
            return lower.z1_m
        return top
    if kind == "wall_slab":
        return wall.z0_m
    return (wall.z0_m + top) / 2.0


def _top_at(wall, direction: str | None, station: float) -> float:
    top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    if wall.top_z0_m is None or wall.top_z1_m is None or direction is None:
        return top
    i = 0 if direction == "y" else 1  # a "y" cut is a plane at x = station
    (a, b) = wall.axis
    span = b[i] - a[i]
    if abs(span) < 1e-9:
        return top
    t = min(1.0, max(0.0, (station - a[i]) / span))
    return wall.top_z0_m + (wall.top_z1_m - wall.top_z0_m) * t


_TRIM_CATEGORIES = frozenset({"fascia", "soffit", "gutter", "drip_edge", "corner_trim"})
_TRIM_NEAR_M = 1.0
_TRIM_MARGIN_M = 0.08


def _trim_reach(model, cond, direction: str, station: float, u_lo: float,
                u_hi: float) -> tuple[float, float]:
    """The u extent of the condition's roof trim cut at ``station`` within 1 m of the wall.

    Roof members in ``_TRIM_CATEGORIES`` and the resolved cladding trim the condition's
    elements own (host_ref) both count: a wall-top closure or eave piece reaches out past
    the cladding just as a fascia does.
    """
    plane = CutPlane(axis=direction, station_m=station)
    us = [u_lo, u_hi]

    def _take(solid_like) -> None:
        for profile in slice_solid(solid_like, plane):
            us.extend(u for u, _z in profile.outline
                      if u_lo - _TRIM_NEAR_M <= u <= u_hi + _TRIM_NEAR_M)

    for roof in model.roofs:
        if roof.tag not in cond.element_tags:
            continue
        for member in roof.members:
            if member.category not in _TRIM_CATEGORIES:
                continue
            solid = member_solid(member)
            if solid is not None:
                _take(solid)
    for solid in model.solids:
        if (solid.category == "cladding_trim" and solid.body_mesh is not None
                and solid.host_ref in cond.element_tags):
            _take(solid.body_mesh)
    return min(us), max(us)


# How far an eave cut may slide to reach a clear pan middle: a 16" pan module against 24"
# rafters puts every third middle on a rafter, so the nearest clear one can be ~1'-4" away.
_PAN_SLIDE_M = 0.45
# Clearance a mid-pan station keeps from a rafter's face, so the cut shows the eave block.
_RAFTER_CLEAR_M = 0.0254


def _mid_pan_station(model, cond, direction: str, station: float, u_lo: float,
                     u_hi: float) -> float:
    """``station`` slid to the middle of the nearest standing-seam pan at this eave.

    A cut on a seam draws the seam stub's fold and none of the pan hem; mid-pan is where the
    hem, the eave lip and the lap order read. A middle that lands on a rafter is skipped: the
    cut would run down the rafter and lose the eave block. A roof with no pan ends keeps its
    station.
    """
    from typehaus.emit.draw.section_sheet_metal import PAN_END_CONNECTION
    from typehaus.resolve.framing.profiles import cross_section

    along, across = (1, 0) if direction == "x" else (0, 1)
    roofs = [roof for roof in model.roofs if roof.tag in cond.element_tags]
    middles = [(member.p0[along] + member.p1[along]) / 2.0
               for roof in roofs for member in roof.members
               if member.connection == PAN_END_CONNECTION
               and u_lo - _TRIM_NEAR_M <= member.p0[across] <= u_hi + _TRIM_NEAR_M]
    rafters = [(member.p0[along], cross_section(member.profile).width_m / 2.0)
               for roof in roofs for member in roof.members
               if member.category == "rafter" and abs(member.p0[along] - member.p1[along]) < 1e-6]

    def clear(mid: float) -> bool:
        return all(abs(mid - at) > half + _RAFTER_CLEAR_M for at, half in rafters)

    for mid in sorted(middles, key=lambda mid: abs(mid - station)):
        if abs(mid - station) > _PAN_SLIDE_M:
            break
        if clear(mid):
            return mid
    return station


def _build_derived(model, cond, tr, wall, key: str, opening_kind: str | None = None,
                   t_override: float | None = None) -> DerivedDetail | None:
    (x0, y0), (x1, y1) = wall.axis
    opening = (_condition_opening(model, cond)
               if cond.kind.value == "opening_perimeter" else None)
    if opening is not None:
        # Cut through the opening, not the wall midpoint: the head and sill this detail is
        # about only exist in the plane that actually crosses the opening.
        length = math.hypot(x1 - x0, y1 - y0)
        t = opening.center_along_m / length if length > 1e-9 else 0.5
        mx, my = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    else:
        t = t_override if t_override is not None else clear_fraction(model, cond, wall)
        mx, my = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    if dx >= dy:
        # wall runs along x → cut perpendicular is a plane at x=const (u = world y).
        direction, station, center_u = "y", mx, my
    else:
        direction, station, center_u = "x", my, mx

    below, above, inboard, outboard = _CROP_WINDOWS.get(cond.kind.value, _DEFAULT_WINDOW)
    if opening is not None:
        # The z-window holds the whole opening: below measures off the sill, above off the
        # head, so a full-height door and a high awning window both crop to their subject.
        sill_z = wall.base_ref_z_m + opening.sill_m
        z0, z1 = sill_z - below, sill_z + opening.height_m + above
    else:
        junction_z = _junction_z(model, cond, wall)
        z0, z1 = junction_z - below, junction_z + above

    # Measure the margins off the wall's real faces, not its axis: a wall aligned on its
    # sheathing plane is nowhere near centred on its axis, so an axis-centred window leaves
    # a wide empty band on one side and clips the drawing on the other.
    u_lo, u_hi = _wall_u_extent(wall, direction, station, center_u)
    if cond.kind.value == "wall_roof":
        station = _mid_pan_station(model, cond, direction, station, u_lo, u_hi)
        junction_z = _junction_z(model, cond, wall, direction, station)
        z0, z1 = junction_z - below, junction_z + above
        # Hold the roof's eave trim (fascia, soffit, drip edge, gutter) whole: an overhung
        # eave reaches well past a fixed margin, and a crop through the fascia hides it.
        reach_lo, reach_hi = _trim_reach(model, cond, direction, station, u_lo, u_hi)
        outboard = max(outboard, reach_hi - u_hi + _TRIM_MARGIN_M)
        inboard = max(inboard, u_lo - reach_lo + _TRIM_MARGIN_M)
    view = Slice(
        uid="", tag=f"D-{_key_slug(key)}", kind=SliceKind.DETAIL,
        title=(tr.title or tr.tag if tr is not None else key),
        cut_origin=pt(m(station if direction == "y" else center_u),
                      m(center_u if direction == "y" else station)),
        cut_direction=direction,
        crop=(pt(m(u_lo - inboard), m(z0)), pt(m(u_hi + outboard), m(z1))),
    )
    return DerivedDetail(key=key, condition=cond, transition=tr, view=view,
                         direction=direction, station=station, opening_kind=opening_kind)


def _build_ridge_derived(model, cond, tr) -> DerivedDetail | None:
    """A ridge detail cut perpendicular to the ridge member at its midpoint.

    The frame comes from the resolved ridge-beam member (falling back to the roof's own
    ridge line), and the crop is a symmetric window about the ridge line at the ridge
    elevation — there are no wall faces to measure margins from.
    """
    from typehaus.emit.draw.detail_components.ridge import ridge_beam_member

    roof = next((r for r in model.roofs if r.tag in cond.element_tags), None)
    if roof is None:
        return None
    member = ridge_beam_member(roof)
    if member is not None:
        (x0, y0), (x1, y1) = member.p0, member.p1
    else:
        xs = [p[0] for p in roof.footprint]
        ys = [p[1] for p in roof.footprint]
        if roof.ridge_direction == "x":
            (x0, y0), (x1, y1) = ((min(xs), (min(ys) + max(ys)) / 2.0),
                                  (max(xs), (min(ys) + max(ys)) / 2.0))
        else:
            (x0, y0), (x1, y1) = (((min(xs) + max(xs)) / 2.0, min(ys)),
                                  ((min(xs) + max(xs)) / 2.0, max(ys)))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    if dx >= dy:
        direction, station, center_u = "y", mx, my
    else:
        direction, station, center_u = "x", my, mx
    below, above, inboard, outboard = _CROP_WINDOWS.get("roof_ridge", _DEFAULT_WINDOW)
    ridge_z = roof.ridge_z_m
    view = Slice(
        uid="", tag=f"D-{_key_slug(cond.key)}", kind=SliceKind.DETAIL,
        title=(tr.title or tr.tag if tr is not None else cond.key),
        cut_origin=pt(m(station if direction == "y" else center_u),
                      m(center_u if direction == "y" else station)),
        cut_direction=direction,
        crop=(pt(m(center_u - inboard), m(ridge_z - below)),
              pt(m(center_u + outboard), m(ridge_z + above))),
    )
    return DerivedDetail(key=cond.key, condition=cond, transition=tr, view=view,
                         direction=direction, station=station)


def _key_slug(key: str) -> str:
    slug = key.replace(":", "-").replace("|", "-").replace("*", "x")
    if len(slug) <= 40:
        return slug
    # Two long keys can share their first 40 characters (the PORCH_RAILING pair did),
    # and a shared slug means one render filename silently overwriting the other.
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:6]
    return f"{slug[:33]}-{digest}"


def detail_index(model: ResolvedModel) -> list[dict]:
    """Pure-data index of scaffolded details (server ``/details`` + Pyodide, offline-safe)."""
    out = []
    for d in derive_detail_slices(model):
        tr = d.transition
        authored = any(
            getattr(a, "condition_key", None) == d.key
            for a in model.plan.elements_of_kind("DetailAnnotation")
        )
        out.append({
            "key": d.key,
            "kind": d.condition.kind.value,
            "title": d.view.title or d.key,
            "transition": tr.tag if tr is not None else None,
            "overlay": getattr(tr, "overlay", None) if tr is not None else None,
            "elements": list(d.condition.element_tags),
            "state": "authored" if authored else "seed",
            # ``star`` is the effective, per-condition answer the UI toggles and the
            # primary export filters on; ``transition_star`` plus the two override lists
            # are the raw authored state, so the navigator can tell "starred because the
            # pattern is" from "starred by an override on this key alone".
            "star": bool(tr.stars(d.key)) if tr is not None else False,
            "transition_star": bool(getattr(tr, "star", False)) if tr is not None else False,
            "starred_conditions": list(getattr(tr, "starred_conditions", ()))
                                  if tr is not None else [],
            "unstarred_conditions": list(getattr(tr, "unstarred_conditions", ()))
                                    if tr is not None else [],
        })
    return out

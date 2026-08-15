"""Which details exist, and where each one cuts — the derivation half of A-4xx.

One detail is scaffolded per distinct bound condition key: this module decides the cut
plane, direction and extent from the resolved model, and hands ``details.py`` a
:class:`DerivedDetail` to draw. The seam is real — the server's ``/details`` endpoints
need the index and the payload without ever building a scene.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from typehaus.model.enums import SliceKind
from typehaus.model.patterns import matches
from typehaus.model.views import Slice
from typehaus.quantities import m, pt
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


def _matched_transition(model: ResolvedModel, cond: BoundaryCondition):
    for tr in model.plan.library.transitions:
        if matches(tr.condition_pattern, cond.key):
            return tr
    return None


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


def derive_detail_slices(model: ResolvedModel) -> list[DerivedDetail]:
    """One derived DETAIL slice per distinct bound condition key (skip authored-claimed keys).

    The cut plane runs perpendicular to the host wall at its midpoint; the crop is a junction
    z-window × u-window sized to the junction kind.
    """
    claimed = {
        s.condition_key for s in model.plan.elements_of_kind("Slice")
        if getattr(s, "condition_key", None)
    }
    out: list[DerivedDetail] = []
    seen: set[str] = set()
    for cond in model.conditions:
        if cond.key in seen or cond.key in claimed:
            continue
        tr = _matched_transition(model, cond)
        if tr is None:
            continue  # unbound conditions are the coverage check's concern, not a detail
        if getattr(tr, "suppress", False):
            seen.add(cond.key)
            continue  # bound-but-suppressed: covered for integrity, no sheet derives
        wall = _host_wall(model, cond)
        if wall is None:
            # roof_ridge conditions carry a roof and a beam, never a wall — the cut frame
            # comes from the ridge member instead.
            if cond.kind.value == "roof_ridge":
                derived = _build_ridge_derived(model, cond, tr)
                if derived is not None:
                    seen.add(cond.key)
                    out.append(derived)
            continue
        seen.add(cond.key)
        derived = _build_derived(model, cond, tr, wall)
        if derived is not None:
            out.append(derived)
    out.sort(key=lambda d: d.key)
    return out


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
    from typehaus.emit.draw.section import ring_cut_intervals

    bounds: list[float] = []
    for layer in wall.layers:
        for (u0, u1) in ring_cut_intervals(layer.polygon, direction, station):
            bounds.extend((u0, u1))
    if not bounds:
        half = wall.thickness_m / 2.0
        return fallback_center - half, fallback_center + half
    return min(bounds), max(bounds)


def _junction_z(model, cond, wall) -> float:
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
            return wall.z0_m + opening.sill_m + opening.height_m / 2.0
    top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    if kind == "wall_roof":
        return top
    if kind in ("wall_foundation", "storey_stack", "stack_width_change", "assembly_change"):
        walls = [w for w in (model.wall(tag) for tag in cond.element_tags) if w is not None]
        if len(walls) >= 2:
            lower = min(walls, key=lambda w: w.z0_m)
            return lower.z1_m
        return top
    if kind == "wall_slab":
        return wall.z0_m
    return (wall.z0_m + top) / 2.0


def _build_derived(model, cond, tr, wall) -> DerivedDetail | None:
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
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
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
        sill_z = wall.z0_m + opening.sill_m
        z0, z1 = sill_z - below, sill_z + opening.height_m + above
    else:
        junction_z = _junction_z(model, cond, wall)
        z0, z1 = junction_z - below, junction_z + above

    # Measure the margins off the wall's real faces, not its axis: a wall aligned on its
    # sheathing plane is nowhere near centred on its axis, so an axis-centred window leaves
    # a wide empty band on one side and clips the drawing on the other.
    u_lo, u_hi = _wall_u_extent(wall, direction, station, center_u)
    view = Slice(
        uid="", tag=f"D-{_key_slug(cond.key)}", kind=SliceKind.DETAIL,
        title=(tr.tag if tr is not None else cond.key),
        cut_origin=pt(m(station if direction == "y" else center_u),
                      m(center_u if direction == "y" else station)),
        cut_direction=direction,
        crop=(pt(m(u_lo - inboard), m(z0)), pt(m(u_hi + outboard), m(z1))),
    )
    return DerivedDetail(key=cond.key, condition=cond, transition=tr, view=view,
                         direction=direction, station=station)


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
        title=(tr.tag if tr is not None else cond.key),
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

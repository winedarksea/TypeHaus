"""The wind a ROOF on beams hands its lateral system — whatever that system turns out to be.

Split out of ``roof_moment`` on 2026-09-29 (that module was at 497 lines), and for a reason
better than length: ``roof_moment`` skips a roof with no cast column under it, because it
answers "what base moment does a FIXED column take". A canopy on PINNED posts still has
wind on it; it only has nowhere of its own to put it. Read through ``roof_moment`` alone,
retyping the east posts to steel would have deleted ``lateral_system/RF-BW-CANOPY`` from
the register without a word. The demand is computed here for every roof on beams, and
``roof_moment`` and ``diaphragm_delivery`` each take what they need from it.

**The surrogate is ``roof_moment``'s**, for the reason its docstring gives: the roof's
vertical projection as a solid sign at ``MAX_VERIFIED_CASE_AB``.

**A pinned post splits its own drag half to each end** — ``wL/2`` at each support of a
simple span. The head half joins the deck; the base half goes down to whatever the post
stands on and never reaches the diaphragm. A post framed into a wall (``Post.within_wall``)
is not counted: its face is the wall's.

**Oracle.** ``houses/catlin/notes/canopy_garage_diaphragm.md`` §2 (and
``entry_column_base_fixity.md`` §7a for the bands); ``tests/test_diaphragm_delivery_calcs.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering.registry import EngineeringContext

_M_PER_FT = 0.3048


@dataclass(frozen=True)
class PinnedPost:
    """A non-concrete post under a roof's bearing beam: pinned at both ends, so it resists
    no storey shear, and its own drag returns half to each end."""

    tag: str
    x_ft: float
    y_ft: float
    width_ft: float
    length_ft: float
    drag_lb: float
    #: What it stands on, by tag (``Post.supported_by``), or ``None``.
    below: str | None

    @property
    def head_lb(self) -> float:
        return self.drag_lb / 2.0

    @property
    def base_lb(self) -> float:
        return self.drag_lb / 2.0


@dataclass(frozen=True)
class RoofWind:
    """One roof's wind, on both axes, before anybody has decided who resists it."""

    roof_tag: str
    q_h_psf: float
    height_ft: float
    #: ASD psf on any projected band: 0.6 q_h G C_f.
    pressure_psf: float
    grade_ft: float
    basis_text: str
    #: ``axis -> ASD lb`` on the roof's own projection and its headers, at the roof plane.
    top_shear: dict[str, float]
    #: The roof and header bands resolve at the footprint centre (§8g's convention).
    centre_ft: tuple[float, float]
    pinned: tuple[PinnedPost, ...] = ()

    def delivered_lb(self, axis: str) -> float:
        """The deck-level shear with every pinned post's head half added."""
        return self.top_shear.get(axis, 0.0) + sum(p.head_lb for p in self.pinned)

    def resultant_ft(self, axis: str) -> float:
        """Where the deck-level shear resolves ACROSS the wind: x for N-S, y for E-W."""
        index = 0 if axis == "y" else 1
        top = self.top_shear.get(axis, 0.0)
        total = self.delivered_lb(axis)
        if total <= 0.0:
            return self.centre_ft[index]
        moment = top * self.centre_ft[index] + sum(
            p.head_lb * (p.x_ft if axis == "y" else p.y_ft) for p in self.pinned)
        return moment / total


_WINDS: dict[str, RoofWind] = {}


def roof_winds(ctx: EngineeringContext) -> dict[str, RoofWind]:
    """Every roof that bears on beams, and the wind on it. Rebuilt on every call."""
    from typehaus.model.spatial import Roof

    _WINDS.clear()
    for roof in sorted(ctx.model.roofs, key=lambda r: r.tag):
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof):
            continue
        wind = roof_wind(ctx, element, roof)
        if wind is not None:
            _WINDS[roof.tag] = wind
    return dict(_WINDS)


def current_winds() -> dict[str, RoofWind]:
    """The last :func:`roof_winds` answer, every roof."""
    return dict(_WINDS)


def wind_of(roof_tag: str) -> RoofWind | None:
    """The last :func:`roof_winds` answer for one roof."""
    return _WINDS.get(roof_tag)


def bearing_beams(ctx: EngineeringContext, element: Any) -> list[Any]:
    from typehaus.model.structure import Beam

    return [b for b in (ctx.plan.by_tag(r) for r in element.bearing_refs)
            if isinstance(b, Beam)]


def roof_wind(ctx: EngineeringContext, element: Any, roof: Any) -> RoofWind | None:
    """The wind on one roof on beams, or ``None`` where no demand can be formed."""
    from typehaus.engineering.balcony_wind import Demand, ground_below_ft, solid_bands
    from typehaus.wind import velocity_pressure_psf, wind_basis
    from typehaus.wind_tables import GUST_EFFECT_RIGID, MAX_VERIFIED_CASE_AB

    beams = bearing_beams(ctx, element)
    basis = wind_basis(ctx.plan.project.site)
    if not beams or basis is None:
        return None
    rise_ft = (roof.ridge_z_m - roof.eave_z_m) / _M_PER_FT
    top_ft = roof.ridge_z_m / _M_PER_FT
    ground_ft = ground_below_ft(ctx.plan)
    if rise_ft <= 0.0 or top_ft <= ground_ft:
        return None
    grade = getattr(ctx.plan.project.site, "grade", None)
    grade_ft = float(grade.inches) / 12.0 if grade is not None else ground_ft
    q_h = velocity_pressure_psf(basis, top_ft - ground_ft)
    member_tags = {b.tag for b in beams}
    top: dict[str, float] = {}
    for axis in ("x", "y"):
        bands = (*roof_projection_bands(roof, axis, rise_ft),
                 *solid_bands(ctx.plan, axis, member_tags, None))
        top[axis] = Demand(axis=axis, q_h_psf=q_h, height_ft=top_ft - ground_ft,
                           bands=bands).storey_shear_lb(MAX_VERIFIED_CASE_AB)
    from typehaus.wind import ASD_WIND_FACTOR

    pressure = ASD_WIND_FACTOR * q_h * GUST_EFFECT_RIGID * MAX_VERIFIED_CASE_AB
    xs = [p[0] / _M_PER_FT for p in roof.footprint]
    ys = [p[1] / _M_PER_FT for p in roof.footprint]
    centre = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0) if xs else (0.0, 0.0)
    return RoofWind(
        roof_tag=roof.tag, q_h_psf=q_h, height_ft=top_ft - ground_ft,
        pressure_psf=pressure, grade_ft=grade_ft, basis_text=basis.describe(),
        top_shear=top, centre_ft=centre,
        pinned=tuple(pinned_posts(ctx, beams, pressure)))


def pinned_posts(ctx: EngineeringContext, beams: list[Any],
                 pressure_psf: float) -> list[PinnedPost]:
    """Every non-concrete post a bearing beam names, less those framed into a wall."""
    from typehaus.model.structure import Post
    from typehaus.resolve.assembly_material import assembly_structure_material
    from typehaus.resolve.framing.profiles import cross_section

    out: list[PinnedPost] = []
    seen: set[str] = set()
    for beam in beams:
        for ref in beam.bearing_refs or ():
            post = ctx.plan.by_tag(ref)
            if not isinstance(post, Post) or ref in seen or post.height is None:
                continue
            if assembly_structure_material(ctx.plan, post.assembly) == "concrete":
                continue
            if getattr(post, "within_wall", None):
                continue
            seen.add(ref)
            section = cross_section(post.size)
            width_ft = (section.width_m or 0.0) / _M_PER_FT
            length_ft = post.height.inches / 12.0
            x_ft, y_ft = (c / _M_PER_FT for c in post.position.xy_m)
            out.append(PinnedPost(
                tag=ref, x_ft=x_ft, y_ft=y_ft, width_ft=width_ft, length_ft=length_ft,
                drag_lb=pressure_psf * width_ft * length_ft,
                below=getattr(post, "supported_by", None)))
    return sorted(out, key=lambda p: p.tag)


def roof_projection_bands(roof: Any, axis: str, rise_ft: float) -> tuple[Any, ...]:
    """The roof's own vertical projection, as one :class:`balcony_wind.Band`.

    A gable seen ALONG its ridge is the gable triangle — half the base times the rise.
    Seen ACROSS the ridge it is the slope band, the rise over the run along the ridge, once
    rather than twice: the leeward slope stands in the windward slope's own shadow, and
    counting both would be projecting the same rise twice onto one plane.
    """
    from typehaus.engineering.balcony_wind import Band

    xs = [p[0] / _M_PER_FT for p in roof.footprint]
    ys = [p[1] / _M_PER_FT for p in roof.footprint]
    # Wind along y meets the E-W run; wind along x meets the N-S run.
    run_ft = (max(xs) - min(xs)) if axis == "y" else (max(ys) - min(ys))
    if run_ft <= 0.0:
        return ()
    along_ridge = axis == roof.ridge_direction
    depth_ft = rise_ft / 2.0 if along_ridge else rise_ft
    label = "gable-end triangle" if along_ridge else "slope rise"
    return (Band(f"{roof.tag} {label}", depth_ft, run_ft, roof.tag),)


def column_drag_bands(posts: dict[str, Any], columns: list[str], roof: Any,
                      grade_ft: float) -> tuple[Any, ...]:
    """Each cast column's own face, diameter by exposed height.

    ** THE EXPOSED HEIGHT IS SITE GRADE TO THE EAVE, AND IT IS A BOUND. ** What catches
    wind is the shaft between the ground and the roof; ``Site.grade`` is the only ground
    elevation this module holds that is not the sunken court nine feet down. Eave rather
    than header soffit makes it an over-count. Bounded by the shaft's own length, so a
    column shorter than its own exposure — a modelling error — cannot inflate the demand.
    """
    from typehaus.engineering.balcony_wind import Band
    from typehaus.engineering.pier_basis import _round_size

    out = []
    for tag in columns:
        post = posts[tag]
        size = _round_size(post.size)
        if size is None or post.height is None:
            continue
        exposed_ft = min(post.height.inches / 12.0,
                         (roof.eave_z_m / _M_PER_FT) - grade_ft)
        if exposed_ft <= 0.0:
            continue
        out.append(Band(f"{tag} drag", exposed_ft, size[0] / 12.0, tag))
    return tuple(out)


def panel_forces(ctx: EngineeringContext, roof_tag: str) -> dict[str, dict[str, float]]:
    """``axis -> {panel wall tag: ASD lb}`` — what a roof's shear panels are graded at.

    Where the roof DELIVERS to a neighbour, the envelope of
    ``notes/canopy_garage_diaphragm.md`` §4: every panel is taken at 100% of the deck-level
    shear along its own direction, because no stiffness judgement is made across the joint.
    Otherwise the panel's share of the frame distribution ``roof_moment`` built, as before.
    """
    from typehaus.engineering.lateral_lines import panel_runs_along, panels_under
    from typehaus.engineering.roof_moment import frame_cases_of

    element = ctx.plan.by_tag(roof_tag)
    spec = getattr(element, "diaphragm", None)
    out: dict[str, dict[str, float]] = {}
    cases = frame_cases_of(roof_tag)
    framed = {case.axis for case in cases}
    if spec is not None and spec.delivers_to is not None:
        wind = wind_of(roof_tag)
        resolved = next((r for r in ctx.model.roofs if r.tag == roof_tag), None)
        if wind is None or resolved is None:
            return out
        # ** 100% ONLY ON AN AXIS THE DECK HAS NO FRAME ON. ** Where cast columns share the
        # axis with the panel (the `cast` variant), the panel's share of the canopy's OWN
        # frame is a split inside one structure and stands; what the envelope refuses is a
        # stiffness judgement ACROSS the joint, and the garage is graded at 100% for that.
        for wall in panels_under(ctx, resolved):
            for axis in ("x", "y"):
                if axis not in framed and panel_runs_along(ctx, wall, axis):
                    here = out.setdefault(axis, {})
                    here[wall.tag] = max(here.get(wall.tag, 0.0), wind.delivered_lb(axis))
    for case in cases:
        here = out.setdefault(case.axis, {})
        for tag, share in case.panels_governing.shares.items():
            if tag in case.panel_tags:
                here[tag] = max(here.get(tag, 0.0), share * case.diaphragm_shear_lb)
    return out

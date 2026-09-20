"""Reading a frame's lateral LINES off the model — which elements resist, and how stiffly.

``diaphragm_basis`` is the arithmetic; this is the part that has to look at a building and
decide what is in the lateral system. It is the half that can be wrong about the structure
rather than about the algebra, so every rule it applies is stated here rather than implied.

**Three rules, and each one refuses rather than assumes.**

1. **A CAST COLUMN is a line when it is fixed at its base**, which is what the rest of the
   register has always taken these columns to be. Its stiffness is the cantilever ``3EI/h³``
   on the GROSS round section — see ``diaphragm_basis.cantilever_stiffness_lb_per_in`` for
   why gross rather than ACI's 0.70 I_g, and why that is the end that does not flatter the
   column.
2. **A WALL is a line only where it carries a ``ShearPanelSpec``**, and only for the
   direction it runs in. Sheathing is not a shear wall; a fastener schedule is. A wall with
   plywood on it and no spec contributes nothing and its neighbours take the whole, which
   is the conservative direction and makes the field impossible to use by accident.
3. **A wall is only THIS frame's line if it stands under this roof.** The test is the plan
   footprint, both ends of the wall inside the roof's own outline with a tolerance — not a
   storey, not a tag prefix. A panel forty feet away bracing something else must not appear
   in this frame's stiffness sum, and a tag convention is not evidence of where a wall is.

**The line, not the element.** Two columns on one station are two entries at one station,
and ``tributary_shares`` splits that station's tributary between them while
``rigidity_shares`` gives each its own. That is the right pair of answers: a flexible deck
delivers load to a POSITION, a rigid one to a STIFFNESS.
"""

from __future__ import annotations

from typehaus.engineering.diaphragm_basis import (
    CRACKED_COLUMN_FACTOR,
    Line,
    cantilever_stiffness_lb_per_in,
    member_area_in2,
    round_inertia_in4,
    shear_wall_deflection_in,
)

_M_PER_FT = 0.3048

#: How much of a wall's own run has to lie inside the roof's plan footprint before the wall
#: is read as standing under it. A fraction rather than a tolerance in feet, because the two
#: ends are exactly where the disagreement is: a screen wall is set out to the framing it
#: closes and a roof to its own bearing line, so a panel routinely oversails a roof by a
#: foot at one end and is plainly still under it. Half is far more than any neighbouring
#: structure's wall could manage and far less than this alignment slop.
_UNDER_ROOF_FRACTION = 0.5

#: A wall is taken to run along an axis when its own direction is within this of it, feet
#: of drift per foot of run. A shear panel resists in its own plane and in no other.
_PARALLEL_TOLERANCE = 0.05


def column_lines(ctx, posts: dict, columns: list[str], axis: str,
                 cracked: bool = False) -> list[Line]:
    """One entry per cast column, stationed across the diaphragm's span.

    ``cracked`` applies ACI 318-19 §6.6.3.1.1's 0.70 I_g. It is the end of the band that
    makes the COLUMNS soft and so hands more shear to a panel — the right end when it is the
    panel's own capacity being graded, and the wrong one when it is the column's.
    """
    from typehaus.engineering.pier_basis import _round_size
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    out: list[Line] = []
    for tag in columns:
        post = posts.get(tag)
        if post is None or post.height is None:
            continue
        size = _round_size(post.size)
        if size is None:
            continue
        strength = fc_psi(concrete_spec_for(ctx.plan, post)) or 3000.0
        modulus = 57_000.0 * strength ** 0.5
        inertia = round_inertia_in4(size[0])
        if cracked:
            inertia *= CRACKED_COLUMN_FACTOR
        stiffness = cantilever_stiffness_lb_per_in(modulus, inertia,
                                                   post.height.inches)
        x_ft, y_ft = (c / _M_PER_FT for c in post.position.xy_m)
        out.append(Line(
            tag=tag, kind="cast column",
            station_ft=x_ft if axis == "y" else y_ft,
            stiffness_lb_per_in=stiffness, element_tags=(tag,),
            how=(f"cantilever 3EI/h³ on a {size[0]:.0f}\" round, f'c {strength:,.0f} psi, "
                 f"{post.height.inches / 12.0:.2f}' base to head"
                 + (" at ACI 318-19 §6.6.3.1.1 0.70 I_g" if cracked
                    else " on the gross section"))))
    return out


def panels_under(ctx, resolved_roof) -> list:
    """Every ``Wall`` carrying a ``ShearPanelSpec`` whose plan run lies under this roof."""
    from typehaus.model.elements import Wall

    xs = [p[0] / _M_PER_FT for p in resolved_roof.footprint]
    ys = [p[1] / _M_PER_FT for p in resolved_roof.footprint]
    if not xs or not ys:
        return []
    box = (min(xs), max(xs), min(ys), max(ys))
    out = []
    for wall in ctx.plan.all_elements():
        if not isinstance(wall, Wall) or wall.shear_panel is None:
            continue
        ends = _ends_ft(ctx, wall)
        if ends is None:
            continue
        if _overlap_fraction(ends, box) >= _UNDER_ROOF_FRACTION:
            out.append(wall)
    return out


def _overlap_fraction(ends, box: tuple[float, float, float, float]) -> float:
    """What fraction of a wall's run lies inside a roof's plan bounding box.

    The segment is clipped to the box with the Liang-Barsky parameter form, which for an
    axis-aligned box is four one-line comparisons and needs no polygon library. A wall that
    misses the box entirely returns 0.0 rather than raising.
    """
    (x0, y0), (x1, y1) = ends
    lo_x, hi_x, lo_y, hi_y = box
    t0, t1 = 0.0, 1.0
    for delta, span in ((x1 - x0, (lo_x - x0, hi_x - x0)),
                        (y1 - y0, (lo_y - y0, hi_y - y0))):
        if abs(delta) < 1e-9:
            if span[0] > 0.0 or span[1] < 0.0:
                return 0.0
            continue
        a, b = sorted((span[0] / delta, span[1] / delta))
        t0, t1 = max(t0, a), min(t1, b)
        if t0 >= t1:
            return 0.0
    return t1 - t0


def panel_line(ctx, wall, axis: str, shear_lb: float) -> Line | None:
    """One shear panel as a line, or ``None`` when it does not resist along ``axis``.

    The stiffness is ``V/δ`` at the shear the panel is being asked to carry, because SDPWS's
    third term — the anchorage's own stretch — is stated at a design shear rather than as a
    rate. ``distribute`` re-enters this at the share it converges on, so the pair settles.
    """
    ends = _ends_ft(ctx, wall)
    if ends is None:
        return None
    (x0, y0), (x1, y1) = ends
    run_x, run_y = abs(x1 - x0), abs(y1 - y0)
    length_ft = (run_x ** 2 + run_y ** 2) ** 0.5
    if length_ft <= 0.0:
        return None
    along = run_y / length_ft if axis == "y" else run_x / length_ft
    if along < 1.0 - _PARALLEL_TOLERANCE:
        return None
    height_ft = _height_ft(wall)
    if height_ft is None or height_ft <= 0.0:
        return None
    spec = wall.shear_panel
    chord_area = member_area_in2(spec.chord_member, spec.chord_plies)
    if chord_area is None:
        return None
    slip = spec.anchorage_slip.inches if spec.anchorage_slip is not None else None
    if slip is None:
        return None
    unit_shear = max(shear_lb, 0.0) / length_ft
    delta = shear_wall_deflection_in(unit_shear, height_ft, length_ft,
                                     spec.apparent_stiffness_kips_per_in,
                                     chord_area, slip)
    if delta is None or delta <= 0.0 or shear_lb <= 0.0:
        return None
    station = (x0 + x1) / 2.0 if axis == "y" else (y0 + y1) / 2.0
    return Line(
        tag=wall.tag, kind="shear panel", station_ft=station,
        stiffness_lb_per_in=shear_lb / delta, element_tags=(wall.tag,),
        how=(f"SDPWS 4.3.2 on {length_ft:.2f}' x {height_ft:.2f}' of {spec.fastening}: "
             f"G_a {spec.apparent_stiffness_kips_per_in:.0f} kips/in, d_a {slip:.3f}\", "
             f"δ {delta:.3f}\" at {unit_shear:.0f} plf"))


def panel_geometry_ft(ctx, wall) -> tuple[float, float] | None:
    """``(length ft, height ft)`` of a shear panel, or ``None``."""
    ends = _ends_ft(ctx, wall)
    height_ft = _height_ft(wall)
    if ends is None or height_ft is None:
        return None
    (x0, y0), (x1, y1) = ends
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5, height_ft


def _ends_ft(ctx, wall) -> tuple[tuple[float, float], tuple[float, float]] | None:
    start = ctx.plan.by_tag(getattr(wall, "start_node", "") or "")
    end = ctx.plan.by_tag(getattr(wall, "end_node", "") or "")
    if start is None or end is None:
        return None
    a = getattr(start, "position", None)
    b = getattr(end, "position", None)
    if a is None or b is None:
        return None
    return ((a.xy_m[0] / _M_PER_FT, a.xy_m[1] / _M_PER_FT),
            (b.xy_m[0] / _M_PER_FT, b.xy_m[1] / _M_PER_FT))


def _height_ft(wall) -> float | None:
    """A shear panel's own height — the ``top`` arm, which for a wall is relative to its base.

    Refused where ``top`` is a ``ToRoof`` or absent: a panel whose height is settled by the
    thing above it has no single ``h`` to put in SDPWS's equation, and picking one would be
    inventing the input the equation is most sensitive to.
    """
    top = getattr(wall, "top", None)
    inches = getattr(top, "inches", None)
    return None if inches is None else float(inches) / 12.0

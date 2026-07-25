"""Resolve modeled accessories into geometry (→ take-off / glTF / IFC).

Dowels, connectors, guard rails, sump pits, vent risers, and edge trim all resolve into
plain :class:`ResolvedSolid` prisms in the shared IR, so the existing glTF and IFC solid
paths render and export them without a bespoke emitter per kind. Authored elevations are
project-frame absolute; the resolver derives geometry from authored intent and never
invents a position or a route.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.mep import Sump, VentRun
from typehaus.model.structure import Connector, Dowel, KneeBrace, Railing
from typehaus.model.trim import EaveSoffit, Fascia, Flashing, GlazingTrim, Gutter
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import circle_outline, length, rect_between, sub
from typehaus.resolve.model import (
    FramedMember,
    ResolvedBrace,
    ResolvedModel,
    ResolvedSolid,
)
from typehaus.resolve.vent_termination import (
    derived_termination_elevation,
    exterior_riser_point,
)

# Pipe risers are round sections faceted into the prism-only solid IR. A horizontal run
# cannot be a vertical prism at all, so it is swept as bands stacked in Z whose plan width
# tracks the circle. The band boundaries land on the *same* regular-polygon vertex
# elevations the vertical risers are faceted at, so the jog reads as the identical n-gon
# section rather than as a few square bands: an n-gon spans n/2 bands top to bottom.
_PIPE_FACETS = 12
_PIPE_SWEEP_BANDS = _PIPE_FACETS // 2
_PIPE_BUNDLE_SPACING = 1.6  # centre-to-centre spacing of bundled risers, in diameters

# Trim ``TrimKind`` values collapse onto a small render/IFC category set.
_TRIM_CATEGORY = {
    "fascia": "fascia",
    "soffit": "soffit",
    "gutter": "gutter",
    "drip_flashing": "flashing",
    "wrb_counterflashing": "flashing",
    # The glazing extrusions share the edge-run shape but not the flashing category: they
    # are an aluminium order billed by the lineal foot, and the take-off groups on this.
    "glazing_channel": "glazing_trim",
    "glazing_bar": "glazing_trim",
}


def resolve_accessories(model: ResolvedModel) -> list[Finding]:
    """Append accessory solids to ``model.solids``. Geometry only, so the findings it can
    return are WARN-tier reports of geometry it could not derive — never a build failure."""
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for el in model.plan.storey_elements(storey.tag):
            if isinstance(el, Dowel):
                _resolve_dowel(model, el, storey.tag)
            elif isinstance(el, Connector):
                _resolve_connector(model, el, storey.tag)
            elif isinstance(el, KneeBrace):
                _resolve_knee_brace(model, el, storey.tag)
            elif isinstance(el, Railing):
                _resolve_railing(model, el, storey.tag)
            elif isinstance(el, Sump):
                _resolve_sump(model, el, storey)
            elif isinstance(el, VentRun):
                findings.extend(_resolve_vent(model, el, storey.tag))
            elif isinstance(el, (EaveSoffit, Fascia, Gutter, Flashing, GlazingTrim)):
                _resolve_edge_run(model, el, storey.tag)
    return findings


# --- helpers ----------------------------------------------------------------
def _square(cx: float, cy: float, half_x: float, half_y: float) -> list[tuple[float, float]]:
    return [(cx - half_x, cy - half_y), (cx + half_x, cy - half_y),
            (cx + half_x, cy + half_y), (cx - half_x, cy + half_y)]


def _bar(cx: float, cy: float, axis: str, run_m: float, dia_m: float) -> list[tuple[float, float]]:
    """Plan footprint of a horizontal bar of diameter ``dia_m`` running ``run_m`` along axis."""
    if axis == "x":
        return _square(cx, cy, run_m / 2.0, dia_m / 2.0)
    return _square(cx, cy, dia_m / 2.0, run_m / 2.0)


def _nominal_actual_m(size: str) -> float:
    """Actual cross-section (m) from a nominal like "2x2" (2" nominal → 1.5" actual)."""
    try:
        nominal = float(size.lower().split("x")[0])
    except (ValueError, IndexError):
        nominal = 2.0
    return max(nominal - 0.5, 0.75) * 0.0254


# --- per-kind ---------------------------------------------------------------
def _resolve_dowel(model: ResolvedModel, el: Dowel, storey: str) -> None:
    cx, cy = el.position.xy_m
    z = el.elevation.meters
    dia = el.diameter.meters
    run = el.length.meters
    spacing = el.spacing.meters if el.spacing is not None else 0.0
    perp = "x" if el.axis == "y" else "y"  # bars are spaced perpendicular to their run
    row_span = spacing * max(el.count - 1, 0)
    # Foam thermal-break block the dowels pass through. The block *is* the joint: its thin
    # dimension is the dowel axis (the direction the bars cross it) and its long dimension
    # runs along the joint line, spanning the row of bars. Swapping those two turns the block
    # 90° and it stops separating the two structures it is breaking the bridge between.
    if el.foam_thickness is not None:
        ft_m = el.foam_thickness.meters
        fh = (el.foam_height.meters if el.foam_height is not None else inch(12).meters)
        block_along_joint = max(row_span + 8 * dia, inch(12).meters)
        half_x, half_y = (block_along_joint / 2.0, ft_m / 2.0) if el.axis == "y" else \
            (ft_m / 2.0, block_along_joint / 2.0)
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-foam", tag=f"{el.tag}-FOAM", storey=storey,
            category="thermal_break",
            outline=_square(cx, cy, half_x, half_y),
            z0_m=z - fh / 2.0, z1_m=z + fh / 2.0,
        ))
    # Individual dowel bars, spaced across the joint.
    for i in range(max(el.count, 1)):
        off = (i - (el.count - 1) / 2.0) * spacing
        bx = cx + off if perp == "x" else cx
        by = cy + off if perp == "y" else cy
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
            category="dowel", outline=_bar(bx, by, el.axis, run, dia),
            z0_m=z - dia / 2.0, z1_m=z + dia / 2.0,
        ))


def _resolve_connector(model: ResolvedModel, el: Connector, storey: str) -> None:
    cx, cy = el.position.xy_m
    z = el.elevation.meters if el.elevation is not None else \
        next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    # A compact marker box at the connection point. Hardware is billed from the element, not
    # measured off this solid, so the marker only has to read at the right place.
    half = inch(2.5).meters
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-conn", tag=el.tag, storey=storey,
        category="connector", outline=_square(cx, cy, half, half),
        z0_m=z - inch(3).meters, z1_m=z + inch(3).meters,
    ))


def _resolve_knee_brace(model: ResolvedModel, el: KneeBrace, storey: str) -> None:
    """A 45-degree brace: one raked wood member plus a marker for its hardware.

    The diagonal is a :class:`FramedMember` rather than a swept solid so it bills as the
    stick of lumber it is. ``ResolvedSolid`` only extrudes a plan outline vertically, so a
    diagonal would otherwise have to be faked as a stack of bands — and the solids take-off
    would then count each band as its own piece of structure.
    """
    cx, cy = el.position.xy_m
    ux, uy = (el.direction, 0.0) if el.axis == "x" else (0.0, el.direction)
    # Start at the post *face*: a brace end buried in the column overlaps it in plan by more
    # than the interference check's tolerance, and the butt-joint exemption does not reach an
    # endpoint that far inside the column's centroid.
    offset = _nominal_actual_m(el.post_size) / 2.0
    p0 = (cx + ux * offset, cy + uy * offset)
    leg = el.leg.meters
    p1 = (p0[0] + ux * leg, p0[1] + uy * leg)
    # At 45 degrees the member's own depth, measured square to its axis, opens up to
    # ``depth / cos(45)`` when read vertically — the cut a carpenter sees on the end grain.
    thickness_z = cross_section(el.member).depth_m * math.sqrt(2.0)
    soffit = el.soffit_elevation.meters
    model.braces.append(ResolvedBrace(
        uid=el.uid or f"{el.tag}-brace", tag=el.tag, storey=storey,
        members=(FramedMember(
            parent_uid=el.uid or el.tag, child_key="brace", category="brace",
            profile=el.member, p0=p0, p1=p1,
            z0_m=soffit - leg - thickness_z, z1_m=soffit - leg,
            length_m=leg * math.sqrt(2.0),
            z0_end_m=soffit - thickness_z, z1_end_m=soffit,
            connection=f"kneebrace:{el.connector}",
        ),),
    ))
    # The hardware itself, at the upper (member) end of the diagonal.
    half = inch(2.5).meters
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-conn" if el.uid else f"{el.tag}-conn", tag=f"{el.tag}-CONN",
        storey=storey, category="connector", outline=_square(p1[0], p1[1], half, half),
        z0_m=soffit - inch(6).meters, z1_m=soffit,
    ))


def _resolve_railing(model: ResolvedModel, el: Railing, storey: str) -> None:
    path = [p.xy_m for p in el.path]
    if len(path) < 2:
        return
    base = el.base_elevation.meters
    top = base + el.height.meters
    post = _nominal_actual_m(el.post_size)
    spacing = max(el.post_spacing.meters, 0.3)
    idx = 0
    # Posts: at every segment start plus interior spacing stations; final vertex closes it.
    placed: list[tuple[float, float]] = []
    for a, b in zip(path[:-1], path[1:]):
        seg = length(sub(b, a))
        n = max(int(seg // spacing), 1)
        for k in range(n):
            t = (k * spacing) / seg if seg else 0.0
            placed.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    placed.append(path[-1])
    for (px, py) in placed:
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-p{idx:02d}", tag=f"{el.tag}-POST{idx + 1}", storey=storey,
            category="railing", outline=_square(px, py, post / 2.0, post / 2.0),
            z0_m=base, z1_m=top, assembly=el.assembly,
        ))
        idx += 1
    # Rails: rail_count evenly spaced horizontal runs (top rail at the guard height).
    rail = inch(1.5).meters
    levels = el.rail_count if el.rail_count > 0 else 1
    ridx = 0
    for a, b in zip(path[:-1], path[1:]):
        for j in range(levels):
            frac = 1.0 - (j / max(levels - 1, 1)) if levels > 1 else 1.0
            rz = base + el.height.meters * frac
            model.solids.append(ResolvedSolid(
                uid=f"{el.uid}-r{ridx:02d}", tag=f"{el.tag}-RAIL{ridx + 1}", storey=storey,
                category="railing", outline=rect_between(a, b, -rail / 2.0, rail / 2.0),
                z0_m=rz - rail / 2.0, z1_m=rz + rail / 2.0, assembly=el.assembly,
            ))
            ridx += 1


def _resolve_sump(model: ResolvedModel, el: Sump, storey) -> None:
    cx, cy = el.position.xy_m
    host = next((s for s in model.solids if s.tag == el.host_ref and s.category == "slab"),
                None) if el.host_ref else None
    z1 = host.z1_m if host is not None else storey.elevation.meters
    z0 = (host.z0_m if host is not None else z1) - el.depth.meters
    half = el.diameter.meters / 2.0
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-sump", tag=el.tag, storey=storey.tag,
        category="sump", outline=_square(cx, cy, half, half), z0_m=z0, z1_m=z1,
    ))


def _round_run_bands(start: tuple[float, float], end: tuple[float, float], radius: float,
                     center_z: float) -> list[tuple[list[tuple[float, float]], float, float]]:
    """Sweep a horizontal pipe as ``(outline, z0, z1)`` bands stacked in Z.

    ``ResolvedSolid`` only extrudes a plan outline vertically, so a horizontal run has no
    round cross-section available to it. Each band spans an equal arc of the circle and is
    as wide as the chord at that arc's midpoint, so the stack neither inscribes nor
    circumscribes the pipe and its silhouette stays centred on the true diameter. With
    ``_PIPE_SWEEP_BANDS`` bands the boundaries fall on the riser polygon's own vertex
    elevations, so the jog's section is that same polygon turned on its side.
    """
    bands = []
    for index in range(_PIPE_SWEEP_BANDS):
        low_angle = math.pi * index / _PIPE_SWEEP_BANDS
        high_angle = math.pi * (index + 1) / _PIPE_SWEEP_BANDS
        half_width = radius * math.sin((low_angle + high_angle) / 2.0)
        bands.append((rect_between(start, end, -half_width, half_width),
                      center_z - radius * math.cos(low_angle),
                      center_z - radius * math.cos(high_angle)))
    return bands


def _resolve_vent(model: ResolvedModel, el: VentRun, storey: str) -> list[Finding]:
    cx, cy = el.chase_position.xy_m
    ox, oy = el.exit_offset.xy_m
    ex, ey = exterior_riser_point(el)
    z_start, z_exit = el.start_elevation.meters, el.exit_elevation.meters
    # The termination is a *derived* dimension: 12" above the roof plane at the riser, not
    # an independent input. Authored elevations only stand in where no roof is derivable.
    derived_top = derived_termination_elevation(model, el)
    authored_top = (el.roof_termination_elevation.meters
                    if el.roof_termination_elevation is not None else None)
    z_top = derived_top if derived_top is not None else authored_top
    if z_top is None:
        return [Finding(
            severity=Severity.WARN, check_id="integrity.vent_termination_unresolved",
            message=(f"vent {el.tag} clears no derivable roof and authors no "
                     "roof_termination_elevation — its exterior riser is not resolved"),
            element_tags=(el.tag,), result=Result.FAIL)]
    radius = el.diameter.meters / 2.0
    # Parallel risers, one per bundled system, offset perpendicular to the horizontal jog.
    perp_x = abs(oy) >= abs(ox)  # offset in x when the jog is mostly along y
    n = max(len(el.systems), 1)
    for i, system in enumerate(el.systems or (None,)):
        d = (i - (n - 1) / 2.0) * el.diameter.meters * _PIPE_BUNDLE_SPACING
        dx, dy = (d, 0.0) if perp_x else (0.0, d)
        sysname = system.value if system is not None else "vent"
        key = f"{el.uid}-{sysname}"
        # 1) up the chase
        model.solids.append(ResolvedSolid(
            uid=f"{key}-riser", tag=f"{el.tag}-{sysname}-CHASE", storey=storey,
            category="vent", outline=circle_outline((cx + dx, cy + dy), radius, _PIPE_FACETS),
            z0_m=z_start, z1_m=z_exit))
        # 2) 90° out through the wall
        for band, (outline, z0, z1) in enumerate(
                _round_run_bands((cx + dx, cy + dy), (ex + dx, ey + dy), radius, z_exit)):
            model.solids.append(ResolvedSolid(
                uid=f"{key}-out{band:02d}", tag=f"{el.tag}-{sysname}-OUT{band + 1}", storey=storey,
                category="vent", outline=outline, z0_m=z0, z1_m=z1))
        # 3) 90° up the siding to 12" above the roof
        model.solids.append(ResolvedSolid(
            uid=f"{key}-term", tag=f"{el.tag}-{sysname}-TERM", storey=storey,
            category="vent", outline=circle_outline((ex + dx, ey + dy), radius, _PIPE_FACETS),
            z0_m=z_exit, z1_m=z_top))
    return []


def _resolve_edge_run(model: ResolvedModel, el, storey: str) -> None:
    path = [p.xy_m for p in el.path]
    if len(path) < 2:
        return
    category = _TRIM_CATEGORY.get(el.kind.value, "flashing")
    top = el.top_elevation.meters
    z0 = top - el.depth.meters
    half = el.thickness.meters / 2.0
    for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
            category=category, outline=rect_between(a, b, -half, half), z0_m=z0, z1_m=top,
        ))

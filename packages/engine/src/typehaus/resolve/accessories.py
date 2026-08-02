"""Resolve modeled accessories into geometry (→ take-off / glTF / IFC).

Dowels, connectors, guard rails, sump pits, vent risers, and edge trim all resolve into
plain :class:`ResolvedSolid` prisms in the shared IR, so the existing glTF and IFC solid
paths render and export them without a bespoke emitter per kind. Authored elevations are
project-frame absolute; the resolver derives geometry from authored intent and never
invents a position or a route.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.enums import LayerFunction, TrimKind
from typehaus.model.mep import Sump, VentRun
from typehaus.model.structure import Connector, Dowel, KneeBrace, Railing
from typehaus.model.trim import Downspout, EaveSoffit, Fascia, Flashing, GlazingTrim, Gutter
from typehaus.quantities import inch
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import circle_outline, length, rect_between, sub
from typehaus.resolve.model import (
    FramedMember,
    ResolvedBrace,
    ResolvedModel,
    ResolvedSolid,
)
from typehaus.resolve.stairs.walkline import flight_walklines, walkline_z_at
from typehaus.resolve.trim_bands import drip_edge_bands, open_channel_bands
from typehaus.resolve.vent_termination import (
    derived_termination_elevation,
    exterior_riser_point,
)

# Round-section faceting lives in resolve/round_solids.py, shared with pipe runs.
from typehaus.resolve.round_solids import (
    PIPE_BUNDLE_SPACING as _PIPE_BUNDLE_SPACING,
    PIPE_FACETS as _PIPE_FACETS,
    PIPE_SWEEP_BANDS as _PIPE_SWEEP_BANDS,
    round_run_bands as _round_run_bands,
)

# Trim ``TrimKind`` values collapse onto a small render/IFC category set.
_TRIM_CATEGORY = {
    "fascia": "fascia",
    "soffit": "soffit",
    "gutter": "gutter",
    "downspout": "downspout",
    "drip_flashing": "flashing",
    "wrb_counterflashing": "flashing",
    # The glazing extrusions share the edge-run shape but not the flashing category: they
    # are an aluminium order billed by the lineal foot, and the take-off groups on this.
    "glazing_channel": "glazing_trim",
    "glazing_bar": "glazing_trim",
}

# Rainscreen base closure. The strip is a stock corrugated section: 1-1/2" tall, sold by the
# lineal foot, cut to the cavity's own depth. Only the height is a constant here — the depth
# is read off the wall's furring layer, so a change to the batten size moves the order with
# it instead of leaving a strip that no longer fills the cavity.
BUG_SCREEN_MATERIAL = "corrugated-vent-strip"
BUG_SCREEN_HEIGHT_IN = 1.5
_STACK_TOLERANCE_M = 0.05   # a storey's walls land exactly on the one below; this is slop
_STACK_PLAN_TOL_M = 0.5     # two stacked walls share a plan line within a wall's thickness


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
                if (el.type_ref is not None
                        and not any(product.tag == el.type_ref
                                    for product in model.plan.library.railing_types)):
                    findings.append(element_error(
                        "integrity.unknown_railing_type",
                        f"railing {el.tag} references missing type {el.type_ref!r}", el.tag))
                _resolve_railing(model, el, storey.tag)
            elif isinstance(el, Sump):
                _resolve_sump(model, el, storey)
            elif isinstance(el, VentRun):
                findings.extend(_resolve_vent(model, el, storey.tag))
            elif isinstance(el, Downspout):
                _resolve_downspout(model, el, storey.tag)
            elif isinstance(el, (EaveSoffit, Fascia, Gutter, Flashing, GlazingTrim)):
                _resolve_edge_run(model, el, storey.tag)
    _resolve_bug_screens(model)
    return findings


def rainscreen_cavity_m(layers) -> float | None:
    """Depth of a wall's rainscreen cavity, or ``None`` if the stack has no rainscreen.

    A rainscreen is not any furring — it is a FURRING layer with CLADDING *outboard* of it,
    which is what makes the gap a drained and vented cavity rather than a service chase. The
    predicate is read off the assembly, so every wall built on a rainscreen stack qualifies
    automatically and an interior partition (no cladding at all) never does.

    ``layers`` are the resolved depth layers, interior→exterior.
    """
    depth = None
    for layer in layers:
        if layer.function == LayerFunction.FURRING.value:
            depth = layer.thickness_m
        elif layer.function == LayerFunction.CLADDING.value and depth is not None:
            return depth
    return None


def _point_segment_distance(p: tuple[float, float], a: tuple[float, float],
                            b: tuple[float, float]) -> float:
    run = sub(b, a)
    span = run[0] * run[0] + run[1] * run[1]
    if span <= 0.0:
        return length(sub(p, a))
    t = min(1.0, max(0.0, ((p[0] - a[0]) * run[0] + (p[1] - a[1]) * run[1]) / span))
    return length(sub(p, (a[0] + run[0] * t, a[1] + run[1] * t)))


def _continues_cavity_below(model: ResolvedModel, wall) -> bool:
    """Is this wall's rainscreen cavity fed from a rainscreen wall directly beneath it?

    Platform framing stacks a storey's walls on the one below, and the cladding and its
    vent cavity run past that joint uninterrupted — there is no cladding start there and so
    no screen. A wall only gets one where the cavity genuinely begins: at grade, or on top
    of something that is not itself a rainscreen (a concrete stem wall, a garage curb).

    The test is that some rainscreen wall's top lands on this wall's base *and* shares its
    plan line; matching elevation alone would suppress the screen on every wall in a storey
    the moment one of them stacked.
    """
    for other in model.walls:
        if other.tag == wall.tag or abs(other.z1_m - wall.z0_m) > _STACK_TOLERANCE_M:
            continue
        if rainscreen_cavity_m(other.depth_layers()) is None:
            continue
        mid = ((wall.axis[0][0] + wall.axis[1][0]) / 2.0,
               (wall.axis[0][1] + wall.axis[1][1]) / 2.0)
        if _point_segment_distance(mid, other.axis[0], other.axis[1]) <= _STACK_PLAN_TOL_M:
            return True
    return False


def _resolve_bug_screens(model: ResolvedModel) -> None:
    """A vented insect closure where a rainscreen cavity opens at the base of the cladding.

    Derived rather than authored: the screen exists because of how the wall is built, not
    because of anything about a particular wall, so hand-authoring one run per wall would
    mean the next exterior wall someone draws silently ships an open cavity for wasps. The
    strip fills the furring layer's own plan band — its depth *is* the cavity depth, by
    construction — and sits at the bottom of that cavity.

    Only the *bottom* of a cavity is screened: see :func:`_continues_cavity_below`.

    Geometry only: the solid renders and exports, and
    :func:`typehaus.takeoff.envelope.bug_screen_takeoff` bills the same runs by the lineal
    foot off the same predicate.
    """
    height = inch(BUG_SCREEN_HEIGHT_IN).meters
    for wall in model.walls:
        if not screens_rainscreen_base(model, wall):
            continue
        furring = next(layer for layer in wall.depth_layers()
                       if layer.function == LayerFunction.FURRING.value)
        model.solids.append(ResolvedSolid(
            uid=f"{wall.uid}-bugscreen", tag=f"{wall.tag}-BUGSCREEN", storey=wall.storey,
            category=TrimKind.BUG_SCREEN.value, outline=list(furring.polygon),
            z0_m=wall.z0_m, z1_m=wall.z0_m + height, assembly=wall.assembly,
        ))


def screens_rainscreen_base(model: ResolvedModel, wall) -> bool:
    """Does this wall carry a bug-screen run? Shared by the resolver and the take-off, so
    the geometry and the order can never disagree about which walls are screened."""
    return (rainscreen_cavity_m(wall.depth_layers()) is not None
            and not _continues_cavity_below(model, wall))


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
    """A 45-degree brace: one raked wood member plus a wrap band for each end's hardware.

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
            # An authored finish assembly (POST_WHITE_PAINT on the balcony braces) reduces
            # to its structure layer's material, exactly as a solid's assembly does in the
            # palette — without it the diagonal renders bare category lumber while the
            # pillars it braces read white.
            material=assembly_structure_material(model.plan, el.assembly),
        ),),
    ))
    # The hardware as what it is: an APVKB-style knee-brace kit is a pair of wrap-around
    # straps — one band at each end of the diagonal. The top band ties the brace to the
    # beam/girt soffit it rises to; the bottom band ties it to the post face it leaves
    # from. Each band hugs the member's own plan run and the z-band the wood occupies at
    # that end, so the hardware reads at both joints instead of as one floating marker box
    # at the top. Billing still comes from the element (takeoff/anchors.py::
    # knee_brace_rows), never off these solids.
    band_run = inch(3).meters  # strap width, measured along the brace's plan run
    band_half = cross_section(el.member).width_m / 2.0 + inch(0.25).meters  # wrap clearance
    uid_base = el.uid or el.tag
    for end, (near, far), band_top in (
            ("BOT", (p0, (p0[0] + ux * band_run, p0[1] + uy * band_run)), soffit - leg),
            ("TOP", ((p1[0] - ux * band_run, p1[1] - uy * band_run), p1), soffit)):
        model.solids.append(ResolvedSolid(
            uid=f"{uid_base}-band-{end.lower()}", tag=f"{el.tag}-{el.connector}-{end}",
            storey=storey, category="connector",
            outline=rect_between(near, far, -band_half, band_half),
            z0_m=band_top - thickness_z, z1_m=band_top,
        ))


def _railing_post_stations(path: list[tuple[float, float]],
                           spacing: float) -> list[tuple[float, float]]:
    """Posts at every segment start plus interior spacing stations; final vertex closes."""
    placed: list[tuple[float, float]] = []
    for a, b in zip(path[:-1], path[1:]):
        seg = length(sub(b, a))
        n = max(int(seg // spacing), 1)
        for k in range(n):
            t = (k * spacing) / seg if seg else 0.0
            placed.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    placed.append(path[-1])
    return placed


def _resolve_railing(model: ResolvedModel, el: Railing, storey: str) -> None:
    path = [p.xy_m for p in el.path]
    if len(path) < 2:
        return
    if el.serves_stair is not None:
        stair = next((s for s in model.stairs if s.tag == el.serves_stair), None)
        if stair is not None:
            _resolve_raking_railing(model, el, storey, path, stair)
            return
    base = el.base_elevation.meters
    top = base + el.height.meters
    post = _nominal_actual_m(el.post_size)
    spacing = max(el.post_spacing.meters, 0.3)
    idx = 0
    placed = _railing_post_stations(path, spacing)
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


# Sloped-rail banding: plan length of each flat band approximating a raking rail, and how
# far a path point may sit from every flight centreline before it is judged *off* the stair
# (and rides at the authored ``base_elevation`` instead). 2 m clears a rail path at the far
# edge of a code-width flight plus a landing's depth without ever reaching the next lane's
# flight one storey away in plan.
_RAIL_BAND_STEP_M = 0.25
_RAIL_STAIR_REACH_M = 2.0


def _resolve_raking_railing(model: ResolvedModel, el: Railing, storey: str,
                            path: list, stair) -> None:
    """A ``serves_stair`` railing rakes along its stair's sloped nosing line.

    The flat resolver extrudes every rail at one elevation, which turns an authored stair
    handrail into a horizontal bar floating over the flight. Here each post stands on the
    walking surface under it — the interpolated nosing line of the nearest flight
    (:mod:`typehaus.resolve.stairs.walkline`, the same derivation the R311.7 checks
    measure) — and rises ``top_height`` (R311.7.8.1's above-the-nosings datum; ``height``
    when none is authored). Rails become short flat bands stepping along the slope: the
    boxes-only solid IR extrudes plan outlines vertically, so a raking run is approximated
    exactly the way the round pipe sweeps are (→ :mod:`typehaus.resolve.round_solids`).
    Take-off is unaffected — railings bill per element (takeoff/railings.py), never off
    these solids. Path points beyond every flight (a rail continuing onto a floor edge)
    fall back to the authored ``base_elevation``, so a guard-and-handrail wrapping a well
    corner stays level where the floor is.
    """
    lines = flight_walklines(stair)
    base = el.base_elevation.meters
    rail_h = (el.top_height if el.top_height is not None else el.height).meters

    def surface_z(p: tuple) -> float:
        z = walkline_z_at(lines, p, _RAIL_STAIR_REACH_M)
        return base if z is None else z

    post = _nominal_actual_m(el.post_size)
    for idx, (px, py) in enumerate(_railing_post_stations(
            path, max(el.post_spacing.meters, 0.3))):
        z0 = surface_z((px, py))
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-p{idx:02d}", tag=f"{el.tag}-POST{idx + 1}", storey=storey,
            category="railing", outline=_square(px, py, post / 2.0, post / 2.0),
            z0_m=z0, z1_m=z0 + rail_h, assembly=el.assembly,
        ))
    rail = inch(1.5).meters
    levels = el.rail_count if el.rail_count > 0 else 1
    ridx = 0
    for a, b in zip(path[:-1], path[1:]):
        seg = length(sub(b, a))
        steps = max(int(math.ceil(seg / _RAIL_BAND_STEP_M)), 1)
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            zs = surface_z(((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0))
            for j in range(levels):
                frac = 1.0 - (j / max(levels - 1, 1)) if levels > 1 else 1.0
                rz = zs + rail_h * frac
                model.solids.append(ResolvedSolid(
                    uid=f"{el.uid}-r{ridx:02d}", tag=f"{el.tag}-RAIL{ridx + 1}",
                    storey=storey, category="railing",
                    outline=rect_between(pa, pb, -rail / 2.0, rail / 2.0),
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
    # Two of the kinds are *formed* metal, not extruded stock, and the boxes-only solid IR
    # can only say so by composing the section out of bands (see :mod:`.trim_bands`). The
    # rest are genuinely one band and fall through to the plain extrusion below.
    recipe = _BANDED_SECTIONS.get(el.kind)
    if recipe is not None:
        _resolve_banded_run(model, el, storey, path, category, top, half,
                            recipe(2.0 * half, el.depth.meters))
        return
    for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-{i:02d}", tag=f"{el.tag}-{i + 1}", storey=storey,
            category=category, outline=rect_between(a, b, -half, half), z0_m=z0, z1_m=top,
            material=el.material,
        ))


#: Which edge-run kinds resolve as a composed section rather than as one extruded band.
#: A gutter is an open-top U — the single bar it used to get read as a solid billet of
#: aluminium, nothing rain could fall *into*. A drip edge is a bent angle: a flat leg lapped
#: under the roofing and a turn-down that throws the water clear. Both are the same recipes
#: the roof's *derived* trim uses, so an authored run and a derived one cannot drift into
#: different-looking metal on the same house.
_BANDED_SECTIONS = {
    TrimKind.GUTTER: open_channel_bands,
    TrimKind.DRIP_FLASHING: drip_edge_bands,
}


def _resolve_banded_run(model: ResolvedModel, el, storey: str, path, category: str,
                        top: float, half: float, bands) -> None:
    """Lay a composed section's bands across the ``[-half, +half]`` span the bar occupied.

    The run stays exactly where it was authored; only its cross-section stops being solid.
    """
    for key, offset, band_t, bottom_drop, top_drop in bands:
        left, right = _cross_span(half, offset, band_t, el.back_side)
        for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
            model.solids.append(ResolvedSolid(
                uid=f"{el.uid}-{i:02d}-{key}", tag=f"{el.tag}-{i + 1}-{key.upper()}",
                storey=storey, category=category,
                outline=rect_between(a, b, left, right),
                z0_m=top - bottom_drop, z1_m=top - top_drop,
                material=el.material,
            ))


def _resolve_downspout(model: ResolvedModel, el, storey: str) -> None:
    """The leader as a round prism from the gutter outlet down to its discharge.

    Faceted exactly like the vent riser (:func:`_resolve_vent`) so the two read as the same
    kind of round metal on the elevation rather than one being smooth and the other a prism.
    """
    z0, z1 = el.bottom_elevation.meters, el.top_elevation.meters
    if z1 - z0 <= 0.0:
        return
    model.solids.append(ResolvedSolid(
        uid=f"{el.uid}-00", tag=el.tag, storey=storey, category="downspout",
        outline=circle_outline(el.position.xy_m, el.diameter.meters / 2.0, _PIPE_FACETS),
        z0_m=z0, z1_m=z1, material=el.material))


def _cross_span(half: float, offset: float, band_t: float,
                back_side: str) -> tuple[float, float]:
    """A band's ``[left, right]`` offsets, given where its inboard end sits.

    The band recipes measure offsets from the section's *inboard* end. ``rect_between``
    measures from the path's left-hand normal, so when the building is on the left the two
    frames run in opposite directions and the offsets have to be mirrored — not merely
    relabelled.
    """
    if back_side == "left":
        right = half - offset
        return right - band_t, right
    left = -half + offset
    return left, left + band_t

"""Resolve modeled accessories into geometry (→ take-off / glTF / IFC).

Dowels, connectors, guard rails, sump pits, vent risers, and edge trim all resolve into
plain :class:`ResolvedSolid` prisms in the shared IR, so the existing glTF and IFC solid
paths render and export them without a bespoke emitter per kind. Authored elevations are
project-frame absolute; the resolver derives geometry from authored intent and never
invents a position or a route.
"""

from __future__ import annotations

from typehaus.findings import Finding
from typehaus.model.mep import Sump, VentRun
from typehaus.model.structure import Connector, Dowel, Railing
from typehaus.model.trim import Fascia, Flashing, Gutter
from typehaus.quantities import inch
from typehaus.resolve.geometry import length, rect_between, sub
from typehaus.resolve.model import ResolvedModel, ResolvedSolid

# Trim ``TrimKind`` values collapse onto a small render/IFC category set.
_TRIM_CATEGORY = {
    "fascia": "fascia",
    "gutter": "gutter",
    "drip_flashing": "flashing",
    "wrb_counterflashing": "flashing",
}


def resolve_accessories(model: ResolvedModel) -> list[Finding]:
    """Append accessory solids to ``model.solids``. Never fails a build (geometry only)."""
    for storey in model.plan.storeys:
        for el in model.plan.storey_elements(storey.tag):
            if isinstance(el, Dowel):
                _resolve_dowel(model, el, storey.tag)
            elif isinstance(el, Connector):
                _resolve_connector(model, el, storey.tag)
            elif isinstance(el, Railing):
                _resolve_railing(model, el, storey.tag)
            elif isinstance(el, Sump):
                _resolve_sump(model, el, storey)
            elif isinstance(el, VentRun):
                _resolve_vent(model, el, storey.tag)
            elif isinstance(el, (Fascia, Gutter, Flashing)):
                _resolve_edge_run(model, el, storey.tag)
    return []


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
    # Foam thermal-break block the dowels pass through.
    if el.foam_thickness is not None:
        ft_m = el.foam_thickness.meters
        fh = (el.foam_height.meters if el.foam_height is not None else inch(12).meters)
        block_perp = max(row_span + 8 * dia, inch(12).meters)
        half_along, half_perp = (ft_m / 2.0, block_perp / 2.0) if el.axis == "y" else \
            (block_perp / 2.0, ft_m / 2.0)
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-foam", tag=f"{el.tag}-FOAM", storey=storey,
            category="thermal_break",
            outline=_square(cx, cy, half_along, half_perp),
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
    # A compact marker box; knee braces read as a short angled bar along their axis.
    half = inch(2.5).meters
    if el.kind.value == "kneebrace" and el.axis in ("x", "y"):
        outline = _bar(cx, cy, el.axis, inch(18).meters, inch(3).meters)
    else:
        outline = _square(cx, cy, half, half)
    model.solids.append(ResolvedSolid(
        uid=el.uid or f"{el.tag}-conn", tag=el.tag, storey=storey,
        category="connector", outline=outline,
        z0_m=z - inch(3).meters, z1_m=z + inch(3).meters,
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


def _resolve_vent(model: ResolvedModel, el: VentRun, storey: str) -> None:
    cx, cy = el.chase_position.xy_m
    ox, oy = el.exit_offset.xy_m
    ex, ey = cx + ox, cy + oy
    z_start, z_exit = el.start_elevation.meters, el.exit_elevation.meters
    z_top = el.roof_termination_elevation.meters
    dia = el.diameter.meters
    # Parallel risers, one per bundled system, offset perpendicular to the horizontal jog.
    perp_x = abs(oy) >= abs(ox)  # offset in x when the jog is mostly along y
    n = max(len(el.systems), 1)
    for i, system in enumerate(el.systems or (None,)):
        d = (i - (n - 1) / 2.0) * dia * 1.6
        dx, dy = (d, 0.0) if perp_x else (0.0, d)
        sysname = system.value if system is not None else "vent"
        key = f"{el.uid}-{sysname}"
        # 1) up the chase
        model.solids.append(ResolvedSolid(
            uid=f"{key}-riser", tag=f"{el.tag}-{sysname}-CHASE", storey=storey,
            category="vent", outline=_square(cx + dx, cy + dy, dia / 2.0, dia / 2.0),
            z0_m=z_start, z1_m=z_exit))
        # 2) 90° out through the wall
        model.solids.append(ResolvedSolid(
            uid=f"{key}-out", tag=f"{el.tag}-{sysname}-OUT", storey=storey,
            category="vent",
            outline=rect_between((cx + dx, cy + dy), (ex + dx, ey + dy), -dia / 2.0, dia / 2.0),
            z0_m=z_exit - dia / 2.0, z1_m=z_exit + dia / 2.0))
        # 3) 90° up the siding to 12" above the roof
        model.solids.append(ResolvedSolid(
            uid=f"{key}-term", tag=f"{el.tag}-{sysname}-TERM", storey=storey,
            category="vent", outline=_square(ex + dx, ey + dy, dia / 2.0, dia / 2.0),
            z0_m=z_exit, z1_m=z_top))


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

"""Draw every derived duct part and hanger as a product solid (decision #114).

``resolve/duct_parts.py`` leaves ``ResolvedDuctPart`` / ``ResolvedDuctSupport`` records;
this turns each into one ``derived`` ``ResolvedSolid`` with a closed ``body_mesh``: a loft
between two sections for a collar, reducer, transition, boot or flex, a sleeve and quadrant
for a damper, a U strap or paired rods for a hanger. Billing stays on the records. An
integral part (the terminal's or machine's own collar) draws nothing. Dimensions the row
never read fall back to the envelope of the sections it joins, never to detail the standard
does not state.

Sections and mesh primitives live in ``duct_mesh``; a boot's shape in ``boot_solids``.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.boot_solids import COLLAR_LENGTH_M, boot_mesh
from typehaus.resolve.connector_geometry.mesh import combine_meshes, plate_mesh, transform_mesh
from typehaus.resolve.duct_mesh import (  # noqa: F401 - re-exported for older callers
    Section,
    _add,
    _box,
    _ring,
    _unit,
    loft,
    parse_section,
    prism,
)
from typehaus.resolve.geometry_ir import GMesh, Vec3
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.model_ducts import ResolvedDuctPart, ResolvedDuctSupport
from typehaus.resolve.sweep import leg_frame
from typehaus.resolve.takeoff_solids import run_at as _run_at
from typehaus.resolve.takeoff_solids import takeoff_mesh

MIN_DROP_M = 0.5 * M_PER_IN
STRAP_WIDTH_M, STRAP_THICKNESS_M = 1.0 * M_PER_IN, M_PER_IN / 32.0
ROD_DIAMETER_M = 0.375 * M_PER_IN
#: The collar damper's quadrant handle: along the collar, around it, and out from it.
HANDLE_M = (1.5 * M_PER_IN, 2.0 * M_PER_IN, 0.25 * M_PER_IN)
HANDLE_STANDOFF_M = 0.125 * M_PER_IN  # the shaft, undrawn
_CATEGORY = {"takeoff": "duct_fitting", "tee": "duct_fitting", "reducer": "duct_fitting",
             "transition": "duct_fitting", "boot": "duct_fitting",
             "collar_damper": "duct_damper", "damper": "duct_damper", "flex": "duct_connector",
             "connector": "duct_connector", "drain_tee": "duct_fitting",
             "cap": "duct_fitting"}
#: An end cap drawn as a slip-on lid: this far over the run's end.
CAP_LENGTH_M = 0.5 * M_PER_IN


def _into_run(part: ResolvedDuctPart, model: ResolvedModel) -> bool:
    """Whether the record's ``axis`` runs into its own ``run_tag`` (not its ``other``)."""
    from typehaus.resolve.duct_branches import duct_ends

    duct = next((d for d in model.ducts if d.tag == part.run_tag), None)
    return duct is not None and any(
        math.dist(end, part.point) < 1e-3 and sum(a * b for a, b in zip(axis, part.axis,
                                                                         strict=True)) > 0.99
        for _, end, axis in duct_ends(duct))


def _end_vertex(model: ResolvedModel, tag: str | None, point: Vec3) -> Vec3 | None:
    """``tag``'s end vertex nearest ``point``, within 30" (an eccentric joint's centre)."""
    from typehaus.resolve.duct_branches import duct_ends

    duct = next((d for d in model.ducts if d.tag == tag), None)
    ends = [e for _, e, _ in duct_ends(duct)] if duct is not None else []
    best = min(ends, key=lambda e: math.dist(e, point), default=None)
    return best if best is not None and math.dist(best, point) < 30 * M_PER_IN else None


def _transition_length(part: ResolvedDuctPart) -> float:
    sizes = [s for s in (parse_section(part.size), parse_section(part.branch)) if s]
    return part.length_m or max((s.larger for s in sizes), default=0.0)


def _turned_reducer(model: ResolvedModel, part: ResolvedDuctPart, big: Section,
                    small: Section) -> GMesh | None:
    """A reducer at a turn, recorded on the big run: drawn as the small run's stub.

    Starts at the joint, runs the small run's axis at most to its first bend, and takes the
    big section's extent along each of the stub's axes where the big run has a cross-section
    there (its own axis has none, so the small dimension stays). None when collinear.
    """
    from typehaus.resolve.duct_branches import duct_ends

    other = next((d for d in model.ducts if d.tag == part.other), None)
    end = next((a for _, e, a in duct_ends(other) if math.dist(e, part.point) < 1e-3),
               None) if other is not None else None
    _, run = _run_at(model, part.run_tag, part.point)
    if end is None or run is None:
        return None
    # Collinear, or the record's axis already is the small run's: the plain loft is right.
    along = abs(sum(a * b for a, b in zip(end, run, strict=True)))
    if along > 0.99 or math.dist(end, part.axis) < 1e-3:
        return None
    right, up = leg_frame(end)
    br, bu = leg_frame(run)

    def extent(axis: Vec3, fallback: float) -> float:
        if big.is_round:
            return big.width
        if abs(sum(a * b for a, b in zip(axis, run, strict=True))) > 0.7:
            return fallback
        along_r = abs(sum(a * b for a, b in zip(axis, br, strict=True)))
        along_u = abs(sum(a * b for a, b in zip(axis, bu, strict=True)))
        return big.width if along_r >= along_u else big.depth

    start = Section(big.is_round, extent(right, small.width), extent(up, small.depth))
    pts = [(x, y, z) for (x, y), z in zip(other.path, other.z_m, strict=True)]
    first = pts[1] if math.dist(pts[0], part.point) < 1e-3 else pts[-2]
    return loft(part.point, end, start, small,
                min(_transition_length(part), math.dist(part.point, first)))


def _part_mesh(model: ResolvedModel, part: ResolvedDuctPart,
               siblings: list[ResolvedDuctPart]) -> GMesh | None:
    axis = _unit(part.axis)
    size, branch = parse_section(part.size), parse_section(part.branch)
    if axis is None or size is None:
        return None
    if part.kind in ("takeoff", "tee", "drain_tee"):
        return takeoff_mesh(model, part, axis, branch or size)
    if part.kind in ("reducer", "transition"):
        small = branch or size
        length = _transition_length(part)
        # A reducer's record is on the bigger run and its axis may point down either side;
        # a transition runs from the machine's port into the run.
        if part.kind == "reducer" and (turned := _turned_reducer(model, part, size, small)):
            return turned
        flipped = _into_run(part, model) if part.kind == "reducer" else True
        ends = (small, size) if flipped else (size, small)
        if part.kind == "reducer":
            # Each ring on its own run's centreline: a flat-bottomed or offset reducer when
            # the runs' faces are flush, concentric when their centrelines meet.
            big_end = _end_vertex(model, part.run_tag, part.point)
            small_end = _end_vertex(model, part.other, part.point)
            if big_end is not None and small_end is not None:
                near, away = (small_end, big_end) if flipped else (big_end, small_end)
                gap = sum((away[i] - near[i]) * axis[i] for i in range(3))
                if gap > 0.25 * M_PER_IN:  # the runs stop short: the reducer fills the gap
                    return loft(near, axis, *ends, gap, far=away)
                return loft(near, axis, *ends, length, far=_add(away, axis, length))
        return loft(part.point, axis, *ends, length)
    if part.kind in ("collar_damper", "damper"):
        # A collar starts at its plenum; an in-line body is centred on its station.
        body = COLLAR_LENGTH_M if part.kind == "collar_damper" else (
            part.length_m or size.larger)
        start = part.point if part.kind == "collar_damper" else _add(part.point, axis,
                                                                      -body / 2.0)
        collar = loft(start, axis, size, size, body)
        right, up = leg_frame(axis)
        mid = _add(start, axis, body / 2.0)
        out = size.width / 2.0 + HANDLE_STANDOFF_M + HANDLE_M[2] / 2.0
        along, around, thick = HANDLE_M
        return combine_meshes(collar, _box(_add(mid, right, out), (axis, up, right),
                                           (along, around, thick)))
    if part.kind == "boot":
        return boot_mesh(model, part, size, branch)
    if part.kind == "cap":  # a lid over the end, its axis pointing into the run
        return loft(_add(part.point, axis, -CAP_LENGTH_M / 2.0), axis, size, size,
                    CAP_LENGTH_M)
    # flex / connector: a sleeve of the run's section, clear of a transition at the same port
    behind = sum(_transition_length(s) for s in siblings
                 if s.kind == "transition" and s.run_tag == part.run_tag
                 and s.port == part.port and s.point == part.point)
    return loft(_add(part.point, axis, behind), axis, size, size,
                part.length_m or size.larger)


def _support_mesh(model: ResolvedModel, hanger: ResolvedDuctSupport) -> GMesh | None:
    duct, direction = _run_at(model, hanger.run_tag, hanger.point)
    if duct is None:
        return None
    flat = _unit((direction[0], direction[1], 0.0)) if direction else None
    run = flat or (1.0, 0.0, 0.0)
    across = (run[1], -run[0], 0.0)
    half_w, half_d = duct.width_m / 2.0, duct.depth_m / 2.0
    drop = max(hanger.drop_m, MIN_DROP_M)
    px, py, pz = hanger.point
    top = half_d + drop
    if hanger.hanger == "rod_trapeze":
        diameter = hanger.width_m or ROD_DIAMETER_M
        rod = Section(True, diameter, diameter)
        reach = half_w + diameter / 2.0
        return combine_meshes(*(
            loft((px + across[0] * s * reach, py + across[1] * s * reach, pz - half_d),
                 (0.0, 0.0, 1.0), rod, rod, half_d + top) for s in (-1.0, 1.0)))
    width = hanger.width_m or STRAP_WIDTH_M
    t = hanger.thickness_m or STRAP_THICKNESS_M
    u = ((-half_w - t, top), (-half_w - t, -half_d - t), (half_w + t, -half_d - t),
         (half_w + t, top), (half_w, top), (half_w, -half_d), (-half_w, -half_d),
         (-half_w, top))
    if hanger.hanger == "saddle":  # the band over the duct, its feet on the deck below
        foot = half_d + hanger.drop_m
        u = tuple((a, -foot if z == top else -z) for a, z in reversed(u))
    elif hanger.hanger == "bracket":  # the band cradling the duct; its wall anchor not drawn
        u = tuple((a, half_d if z == top else z) for a, z in u)
    plate = plate_mesh(tuple((a / M_PER_IN, 0.0, z / M_PER_IN) for a, z in u),
                       (0.0, width / M_PER_IN, 0.0))
    shifted = transform_mesh(plate, origin_m=_add(hanger.point, run, -width / 2.0),
                             x_axis=across, y_axis=run, z_axis=(0.0, 0.0, 1.0))
    return shifted


def _solid(uid: str, tag: str, storey: str, category: str, mesh: GMesh,
           product: str | None, host: str) -> ResolvedSolid:
    from shapely.geometry import MultiPoint

    xs, ys, zs = zip(*mesh.positions, strict=True)
    hull = MultiPoint([(x, y) for x, y, _ in mesh.positions]).convex_hull
    ring = ([(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
            if hull.geom_type != "Polygon" else [tuple(p) for p in hull.exterior.coords][:-1])
    return ResolvedSolid(uid=uid, tag=tag, storey=storey, category=category, outline=ring,
                         z0_m=min(zs), z1_m=max(zs), product=product, host_ref=host,
                         body_mesh=mesh, derived=True)  # billed off its record, not measured


def neck_drawn(model: ResolvedModel) -> set[str]:
    """Registers whose type's ``neck`` already draws the boot (``resolve/terminal_necks``);
    a ``separate_boot`` neck is only the damper, and its boot is drawn here."""
    types = {t.tag: t for t in getattr(model.plan.library, "register_types", ())}
    necks = {o.tag: getattr(types.get(o.type_ref), "neck", None)
             for o in model.canvas_objects if o.kind == "Register"}
    return {tag for tag, neck in necks.items()
            if neck is not None and not neck.separate_boot}


def part_solids(model: ResolvedModel) -> None:
    """Append one solid per non-integral part (a boot a neck draws excepted) and hanger."""
    uids = {d.tag: d.uid for d in model.ducts}
    necked = neck_drawn(model)
    seen: dict[tuple[str, str], int] = {}
    for part in model.duct_parts:
        if part.integral or (part.kind == "boot" and part.other in necked):
            continue
        mesh = _part_mesh(model, part, model.duct_parts)
        if mesh is None:
            continue
        n = seen[(part.run_tag, part.kind)] = seen.get((part.run_tag, part.kind), 0) + 1
        model.solids.append(_solid(
            f"{uids.get(part.run_tag, part.run_tag)}-{part.kind}-{n}",
            f"{part.run_tag}-{part.kind.upper()}-{n}", part.storey, _CATEGORY[part.kind],
            mesh, part.product_ref, part.run_tag))
    for n, hanger in enumerate(model.duct_supports, start=1):
        mesh = _support_mesh(model, hanger)
        if mesh is None:
            continue
        model.solids.append(_solid(
            f"{uids.get(hanger.run_tag, hanger.run_tag)}-hanger-{n}",
            f"{hanger.run_tag}-HANGER-{n}", hanger.storey, "duct_support", mesh,
            hanger.product_ref, hanger.run_tag))

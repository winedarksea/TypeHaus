"""Resolve interior millwork: derived window stools and shelf banks (→ model/millwork.py).

The stool half is the ``EaveTrim`` pattern applied indoors — declare once, derive many.
A :class:`~typehaus.model.millwork.MillworkStandard` names the assemblies (and optionally
the rooms) in scope, and every window hosted in one gets a stool sized off *its own host
wall*, never off an authored number. That is the whole point: the reference house's 45
windows sit in four assemblies of four different thicknesses, so a single authored depth
would be wrong for at least three of them and would go wrong again the first time a foam
lift or a girt depth moved.

The derivation, per window::

    return  = interior finish face -> window mount plane   (the host wall's own layers)
    depth   = return - frame_depth + overhang

The mount plane is the outer face of the outermost layer that is neither cladding nor
finish — on the reference house's exterior walls that is the outer girt, "which is also
what the cladding lands on" (notes/outie_window_truss_detail.md), and on a wall with no
furring it is the sheathing. See :func:`interior_return_m` for why the rule is stated as
an exclusion rather than as "the outermost furring layer".

Records are dimensional, not drawn. A stool is a 4"-deep board on the room side of a
reveal; giving it a ``ResolvedSolid`` would put a new category in the 3D Inspector and a
new row in ``structural_solids`` for something whose value is entirely in the schedule
``takeoff/hardwood.py`` builds from these records.

A ``Countertop`` is not drawn either, and for a stronger reason than the stool's: the slab
is drawn ALREADY. ``model/placeable_symbols/_families.py::counter_case`` puts a counter box
on top of every base cabinet and sink base, so a ``ResolvedSolid`` here would be a second
surface in the same place — two coplanar slabs fighting for the same pixels, a new category
to register in ``emit/trades.py``, ``emit/gltf/palette.py``, the solid-trade table and the
checked-in vocabulary manifest, and not one fact a reader could not already see. What was
missing was never the picture; it was the CONTINUOUS SLAB behind it — one area to bill, one
cantilever to grade — and that is a record, not geometry. (The known cost of the decision:
the peninsula's two-material top still renders as one colour, because the symbol draws it.)
"""

from __future__ import annotations

import math
from typing import NamedTuple

from shapely.geometry import Polygon

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.enums import LayerFunction
from typehaus.model.millwork import Countertop, MillworkStandard, ShelfBank, WindowStool
from typehaus.model.plan import PlanModel
from typehaus.model.types import FurnitureType
from typehaus.resolve.model import (
    ResolvedCanvasObject,
    ResolvedCountertop,
    ResolvedModel,
    ResolvedShelf,
    ResolvedShelfBank,
    ResolvedWall,
    ResolvedWindowStool,
    Ring,
)
from typehaus.resolve.overlay import union_all
from typehaus.resolve.placeable_groups import (
    RUN_GAP_TOLERANCE_M,
    run_gap_m,
    run_is_contiguous,
)
from typehaus.resolve.room_walls import bounding_walls

_M_TO_IN = 39.37007874
#: Half the filler tolerance — the buffer radius that closes a run's leftovers into one slab.
_FILLER_CLOSE_M = RUN_GAP_TOLERANCE_M / 2.0


def resolve_millwork(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Populate ``model.window_stools``, ``model.shelf_banks`` and ``model.countertops``."""
    findings: list[Finding] = []
    standard, standard_findings = _the_standard(plan)
    findings.extend(standard_findings)
    findings.extend(_resolve_stools(plan, model, standard))
    findings.extend(_resolve_shelf_banks(plan, model))
    findings.extend(_resolve_countertops(plan, model))
    return findings


# --- the declaration -------------------------------------------------------------------

def _the_standard(plan: PlanModel) -> tuple[MillworkStandard | None, list[Finding]]:
    """The house's single ``MillworkStandard``, or None. Two is an error, not a winner."""
    found = [el for el in plan.all_elements() if isinstance(el, MillworkStandard)]
    if not found:
        return None, []
    if len(found) > 1:
        return None, [Finding(
            severity=Severity.ERROR, check_id="integrity.millwork_standard",
            message=("a house declares at most one MillworkStandard; found "
                     f"{len(found)}: {', '.join(sorted(el.tag for el in found))}"),
            element_tags=tuple(sorted(el.tag for el in found)), result=Result.FAIL)]
    return found[0], []


# --- window stools ---------------------------------------------------------------------

def _resolve_stools(plan: PlanModel, model: ResolvedModel,
                    standard: MillworkStandard | None) -> list[Finding]:
    findings: list[Finding] = []
    materials = {material.tag for material in plan.library.materials}
    window_types = {wt.tag: wt for wt in plan.library.window_types}
    walls = {wall.tag: wall for wall in model.walls}
    storey_of_wall = {wall.tag: wall.storey for wall in model.walls}
    openings = {opening.tag: opening for opening in model.openings}

    authored: dict[str, WindowStool] = {}
    for el in plan.all_elements():
        if not isinstance(el, WindowStool):
            continue
        if el.window_ref in authored:
            findings.append(element_error(
                "integrity.window_stool_ref",
                f"stool {el.tag} is the second stool authored for window "
                f"{el.window_ref!r}", el.tag))
            continue
        if el.window_ref not in openings:
            findings.append(element_error(
                "integrity.window_stool_ref",
                f"stool {el.tag} names no window {el.window_ref!r}", el.tag))
            continue
        if el.material_ref not in materials:
            findings.append(element_error(
                "integrity.window_stool_ref",
                f"stool {el.tag} names no material {el.material_ref!r}", el.tag))
            continue
        authored[el.window_ref] = el

    in_scope = _stool_scope(model, standard)
    for opening in model.openings:
        stool = authored.get(opening.tag)
        derived = stool is None
        if stool is None and (standard is None or opening.tag not in in_scope):
            continue
        wall = walls.get(opening.host_wall)
        if wall is None:
            continue
        assert standard is not None or stool is not None
        material_ref = stool.material_ref if stool else standard.stool_material_ref  # type: ignore[union-attr]
        thickness = (stool.thickness if stool else standard.stool_thickness).meters  # type: ignore[union-attr]
        overhang = (stool.overhang if stool else standard.stool_overhang).meters  # type: ignore[union-attr]
        horn = (stool.horn if stool else standard.stool_horn).meters  # type: ignore[union-attr]
        profile = stool.profile if stool else standard.stool_profile  # type: ignore[union-attr]

        window_type = window_types.get(opening.type_ref or "")
        frame_depth = (window_type.frame_depth.meters
                       if window_type is not None and window_type.frame_depth is not None
                       else None)
        interior_return = interior_return_m(wall)
        authored_depth = stool.depth.meters if stool and stool.depth is not None else None
        if authored_depth is not None:
            depth: float | None = authored_depth
        elif interior_return is None or frame_depth is None:
            depth = None
            findings.append(Finding(
                severity=Severity.WARN, check_id="millwork.stool_depth",
                message=(f"stool for {opening.tag} carries no depth: "
                         + ("its host wall resolves no mount plane"
                            if interior_return is None else
                            f"window type {opening.type_ref!r} authors no frame_depth")),
                element_tags=(opening.tag,), result=Result.UNKNOWN,
                fix_hint="author WindowType.frame_depth, or WindowStool.depth"))
        else:
            depth = interior_return - frame_depth + overhang

        model.window_stools.append(ResolvedWindowStool(
            uid=stool.uid if stool else "",
            tag=stool.tag if stool else f"STOOL-{opening.tag}",
            storey=storey_of_wall.get(wall.tag, ""),
            window_ref=opening.tag,
            wall_tag=wall.tag,
            assembly=wall.assembly,
            material_ref=material_ref,
            thickness_m=thickness,
            length_m=opening.width_m + 2.0 * horn,
            depth_m=depth,
            overhang_m=overhang,
            horn_m=horn,
            profile=profile,
            return_m=interior_return,
            frame_depth_m=frame_depth,
            derived=derived,
        ))
    return findings


def _stool_scope(model: ResolvedModel, standard: MillworkStandard | None) -> set[str]:
    """Tags of the windows a ``MillworkStandard`` derives a stool for."""
    if standard is None or not standard.stool_assemblies:
        return set()
    assemblies = set(standard.stool_assemblies)
    walls = {wall.tag: wall for wall in model.walls}
    if standard.stool_rooms:
        wanted = set(standard.stool_rooms)
        reachable = {wall.tag for room in model.rooms if room.tag in wanted
                     for wall, _span in bounding_walls(model, room)}
    else:
        reachable = None
    scope: set[str] = set()
    for opening in model.openings:
        if opening.kind != "window":
            continue
        wall = walls.get(opening.host_wall)
        if wall is None or wall.assembly not in assemblies:
            continue
        if reachable is not None and wall.tag not in reachable:
            continue
        scope.add(opening.tag)
    return scope


def interior_return_m(wall: ResolvedWall) -> float | None:
    """Interior finish face -> window mount plane, in metres, off the wall's own layers.

    The mount plane is the outer face of the outermost layer that is neither ``CLADDING``
    nor ``FINISH`` — the last thing a flange can bear on before the skin goes over it. On
    the reference house's exterior walls that lands exactly on the outer girt the note
    names ("the outer face of the outer girt, which is also what the cladding lands on");
    on a wall with no furring at all it lands on the sheathing, which is where a window in
    such a wall really does mount.

    Stated as an exclusion rather than as "the outermost FURRING layer" on purpose: a
    liner wall carries furring on its INSIDE face (the sauna's ``liner-furring`` sits
    inboard of the studs), and a rule that took the outermost furring would return 1-1/2"
    of liner as the whole reveal.

    ``None`` when the wall resolves no such layer — a wall of nothing but finish.
    """
    layers = wall.depth_layers()
    plane_index = None
    for index, layer in enumerate(layers):
        if layer.function not in (LayerFunction.CLADDING.value, LayerFunction.FINISH.value):
            plane_index = index
    if plane_index is None:
        return None
    return sum(layer.thickness_m for layer in layers[: plane_index + 1])


# --- shelf banks -----------------------------------------------------------------------

def _resolve_shelf_banks(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    materials = {material.tag for material in plan.library.materials}
    walls = {wall.tag: wall for wall in model.walls}
    furniture_types = {ft.tag: ft for ft in plan.library.furniture_types}
    placeables = {obj.tag: obj for obj in model.canvas_objects}

    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            if not isinstance(el, ShelfBank):
                continue
            if el.material_ref not in materials:
                findings.append(element_error(
                    "integrity.shelf_bank_ref",
                    f"shelf bank {el.tag} names no material {el.material_ref!r}", el.tag))
                continue
            wall = walls.get(el.host)
            placeable = placeables.get(el.host)
            if wall is None and placeable is None:
                findings.append(element_error(
                    "integrity.shelf_bank_ref",
                    f"shelf bank {el.tag} names no wall or placeable {el.host!r}", el.tag))
                continue
            host_kind = "wall" if wall is not None else "placeable"
            depth = el.depth.meters if el.depth is not None else (
                _pocket_depth_m(wall) if wall is not None
                else _carcass_depth_m(placeable, furniture_types))
            if depth is None:
                findings.append(Finding(
                    severity=Severity.WARN, check_id="millwork.shelf_depth",
                    message=(f"shelf bank {el.tag} carries no depth: host {el.host!r} "
                             f"resolves neither a case pocket nor a footprint depth"),
                    element_tags=(el.tag,), result=Result.UNKNOWN,
                    fix_hint="author ShelfBank.depth"))
            shelves = tuple(
                ResolvedShelf(bay_index=index, width_m=bay.width.meters, depth_m=depth,
                              clear_height_m=bay.clear_height.meters,
                              count=bay.shelf_count)
                for index, bay in enumerate(el.bays))
            model.shelf_banks.append(ResolvedShelfBank(
                uid=el.uid, tag=el.tag, storey=storey.tag, host=el.host,
                host_kind=host_kind, material_ref=el.material_ref,
                thickness_m=el.thickness.meters, depth_m=depth, profile=el.profile,
                shelves=shelves))
    return findings


def _pocket_depth_m(wall: ResolvedWall) -> float | None:
    """A built-in's clear case pocket: the wall's ``AIRGAP`` band plus its stud bay.

    A bookcase wall is authored as a void inside the assembly (the reference house's
    ``INT_2X4_BOOKCASE_12`` carries a ``case-pocket`` AIRGAP over its stud layer),
    so the depth a shelf is cut to is the depth of that void — never the wall's overall
    thickness, which includes the case back and the finish on the far side.
    """
    depth = sum(layer.thickness_m for layer in wall.depth_layers()
                if layer.function in (LayerFunction.AIRGAP.value,
                                      LayerFunction.STRUCTURE.value))
    return depth if depth > 0.0 else None


def _carcass_depth_m(placeable: ResolvedCanvasObject | None,
                     furniture_types: dict[str, FurnitureType]) -> float | None:
    """A carcass's shelf depth: its type's footprint depth.

    Inherited rather than restated on the bank: the carcass already states how deep it is,
    and a second authored number is the one that goes stale.
    """
    if placeable is None:
        return None
    ftype = furniture_types.get(placeable.type_ref or "")
    if ftype is None:
        return None
    return float(ftype.footprint[1].meters)


# --- countertops -------------------------------------------------------------------------

class _Size(NamedTuple):
    """A placeable type's plan size, and how much of its depth is BOX under a top."""

    width_m: float
    depth_m: float
    carcass_m: float


def _resolve_countertops(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Populate ``model.countertops``: one derived slab per authored ``Countertop``."""
    findings: list[Finding] = []
    materials = {material.tag for material in plan.library.materials}
    placeables = {obj.tag: obj for obj in model.canvas_objects}
    sizes = _placeable_sizes(plan)

    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            if not isinstance(el, Countertop):
                continue
            hosts = [placeables.get(tag) for tag in el.hosts]
            missing = [tag for tag, obj in zip(el.hosts, hosts, strict=True) if obj is None]
            if not el.hosts or missing or el.material_ref not in materials:
                findings.append(element_error(
                    "integrity.countertop_ref",
                    f"countertop {el.tag} names no material {el.material_ref!r}"
                    if el.material_ref not in materials else
                    f"countertop {el.tag} names no placeable "
                    f"{', '.join(repr(tag) for tag in missing)}"
                    if missing else f"countertop {el.tag} covers no placeable", el.tag))
                continue
            run = [obj for obj in hosts if obj is not None]
            if not run_is_contiguous([obj.footprint for obj in run]):
                findings.append(element_error(
                    "integrity.countertop_run",
                    f"countertop {el.tag}'s hosts are not one unbroken run "
                    f"({' -> '.join(obj.tag for obj in run)}): a slab does not jump a gap "
                    f"wider than the {RUN_GAP_TOLERANCE_M * _M_TO_IN:g}\" filler tolerance. "
                    "Author one countertop per run", el.tag))
                continue
            unsized = [obj.tag for obj in run if (obj.type_ref or "") not in sizes]
            if unsized:
                findings.append(Finding(
                    severity=Severity.WARN, check_id="millwork.countertop_depth",
                    message=(f"countertop {el.tag} carries no depth: host(s) "
                             f"{', '.join(unsized)} name no type in any placeable catalog"),
                    element_tags=(el.tag,), result=Result.UNKNOWN,
                    fix_hint="give the host placeable a type, or drop it from the run"))
                continue
            record, record_findings = _slab(el, run, storey.tag, sizes)
            findings.extend(record_findings)
            if record is not None:
                model.countertops.append(record)
    return findings


def _placeable_sizes(plan: PlanModel) -> dict[str, _Size]:
    """Type tag -> its plan size, across every catalog a countertop can sit on.

    Only a ``FurnitureType`` splits carcass from footprint (an island or a peninsula draws
    as one rectangle and is box for part of it); every other catalog's footprint depth *is*
    its carcass, because a dishwasher and a vanity are boxes all the way to the front.
    """
    sizes: dict[str, _Size] = {}
    for ftype in plan.library.furniture_types:
        width, depth = ftype.footprint
        carcass = ftype.carcass_depth if ftype.carcass_depth is not None else depth
        sizes[ftype.tag] = _Size(float(width.meters), float(depth.meters),
                                 float(carcass.meters))
    for catalog in (plan.library.fixture_types, plan.library.appliance_types,
                    plan.library.equipment_types):
        for ptype in catalog:
            width, depth = ptype.footprint
            sizes[ptype.tag] = _Size(float(width.meters), float(depth.meters),
                                     float(depth.meters))
    return sizes


def _slab(el: Countertop, run: list[ResolvedCanvasObject], storey: str,
          sizes: dict[str, _Size]) -> tuple[ResolvedCountertop | None, list[Finding]]:
    """The derived slab: its polygon, its area, and the cantilever the check reads."""
    carcass = sizes[run[0].type_ref or ""].carcass_m
    overhang = el.overhang.meters
    depth = el.depth.meters if el.depth is not None else carcass + overhang
    unsupported = (el.unsupported_overhang.meters if el.unsupported_overhang is not None
                   else max(0.0, depth - carcass))
    # Where the slab's back edge sits, measured forward from the host's back face. A top
    # that starts at the carcass back has offset 0; the reference house's bar top is 15"
    # deep and 15" of it is cantilever, so it starts at the carcass FACE — which is what
    # this puts it at, rather than needing a second authored coordinate.
    offset = carcass - (depth - unsupported)

    covered = [sizes[obj.type_ref or ""].width_m for obj in run]
    length = sum(covered) + sum(
        run_gap_m(first.footprint, second.footprint)
        for first, second in zip(run, run[1:], strict=False))
    if el.length is not None:
        # An authored length trims the LAST host from its far end: the slab keeps the start
        # of ``hosts[0]``, which is the end a run is measured from.
        remaining = el.length.meters - (length - covered[-1])
        if remaining <= 0.0:
            return None, [element_error(
                "integrity.countertop_run",
                f"countertop {el.tag}'s authored length is shorter than the hosts before "
                f"its last one, so the slab covers nothing of {run[-1].tag}", el.tag)]
        covered[-1] = min(covered[-1], remaining)
        length = el.length.meters

    rects = [_covered_rect(obj, width, sizes[obj.type_ref or ""], offset, depth)
             for obj, width in zip(run, covered, strict=True)]
    outline, area = _slab_outline(rects)
    return ResolvedCountertop(
        uid=el.uid, tag=el.tag, storey=storey, room=run[0].room,
        hosts=tuple(obj.tag for obj in run), material_ref=el.material_ref,
        thickness_m=el.thickness.meters, depth_m=depth, length_m=length,
        overhang_m=overhang, unsupported_overhang_m=unsupported, support=el.support,
        profile=el.profile, outline=outline, area_m2=area), []


def _covered_rect(obj: ResolvedCanvasObject, width: float, size: _Size,
                  offset: float, depth: float) -> Polygon:
    """The slab's footprint over one host, in world coordinates.

    Local +y is the host's BACK — ``model/placeable_symbols`` draws every counter's front
    edge at local -y — so the slab runs forward from the back face by ``offset`` and covers
    ``depth``. ``width`` is measured from the host's local -x end, which is where an
    authored length starts.
    """
    angle = math.radians(obj.rotation_degrees)
    along = (math.cos(angle), math.sin(angle))
    back = (-math.sin(angle), math.cos(angle))
    origin = (obj.position[0] - along[0] * size.width_m / 2.0 + back[0] * size.depth_m / 2.0,
              obj.position[1] - along[1] * size.width_m / 2.0 + back[1] * size.depth_m / 2.0)
    corners = [(origin[0] + along[0] * step - back[0] * dive,
                origin[1] + along[1] * step - back[1] * dive)
               for step, dive in ((0.0, offset), (width, offset), (width, offset + depth),
                                  (0.0, offset + depth))]
    return Polygon(corners)


def _slab_outline(rects: list[Polygon]) -> tuple[Ring, float]:
    """One polygon and its area, with the run's fillers closed over.

    A leftover under the filler tolerance is not a hole in the stone — the slab is cut
    straight across it — so the union is morphologically closed at half that width. Mitred,
    because every rectangle here is a rectangle and a rounded join would shave the corners.
    """
    merged = union_all(rects)
    closed = merged.buffer(_FILLER_CLOSE_M, join_style=2).buffer(-_FILLER_CLOSE_M,
                                                                join_style=2)
    if closed.geom_type != "Polygon" or closed.is_empty:
        closed = merged if merged.geom_type == "Polygon" else max(
            merged.geoms, key=lambda part: part.area)
    return tuple((float(x), float(y)) for x, y in closed.exterior.coords[:-1]), closed.area

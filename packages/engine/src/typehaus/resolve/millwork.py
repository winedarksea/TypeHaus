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
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.enums import LayerFunction
from typehaus.model.millwork import MillworkStandard, ShelfBank, WindowStool
from typehaus.model.plan import PlanModel
from typehaus.model.types import FurnitureType
from typehaus.resolve.model import (
    ResolvedCanvasObject,
    ResolvedModel,
    ResolvedShelf,
    ResolvedShelfBank,
    ResolvedWall,
    ResolvedWindowStool,
)
from typehaus.resolve.room_walls import bounding_walls


def resolve_millwork(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Populate ``model.window_stools`` and ``model.shelf_banks``."""
    findings: list[Finding] = []
    standard, standard_findings = _the_standard(plan)
    findings.extend(standard_findings)
    findings.extend(_resolve_stools(plan, model, standard))
    findings.extend(_resolve_shelf_banks(plan, model))
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
    ``CATLIN_INT_2X4_BOOKCASE_12`` carries a ``case-pocket`` AIRGAP over its stud layer),
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

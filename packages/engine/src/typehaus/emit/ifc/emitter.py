"""IFC4 emitter over the ResolvedModel (WP1.7, → 12 §IFC emission).

Core LOD = one IfcWall per wall with IfcMaterialLayerSetUsage + shared IfcWallType;
framed LOD additionally aggregates generated members. Parent GUIDs are identical across
LODs (diff stability). GUIDs are derived from (project_uuid, uid) so moved/renamed
elements keep their GlobalId. Determinism: sorted iteration + pinned OwnerHistory.

This file is the facade and the running order, nothing else: the discipline emitters live in
``architectural``/``structural``/``mep``/``site`` beside it (plus the older ``roof`` and
``electrical``), and the IfcOpenShell calls live in ``lowlevel``. ``emit_ifc`` stays here
because the *sequence* is the contract — spatial structure before the elements it contains,
elements before the systems that group them — and every caller outside this package imports
it (and only it) from this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from typehaus._meta import IFC_APP_NAME, PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.architectural import (
    _emit_furniture,
    _emit_opening,
    _emit_opening_types,
    _emit_resolved_placeables,
    _emit_space,
    _emit_wall,
    _emit_wall_types,
)
from typehaus.emit.ifc.electrical import emit_conduits, emit_light_runs, emit_solar_panels
from typehaus.emit.ifc.mep import (
    _ACCESSORY_IFC_CLASS,
    _PIPE_SYSTEM_OBJECT_TYPES,
    _PIPE_SYSTEM_TYPES,
    _emit_data_system,
    _emit_duct_run,
    _emit_pipe_accessories,
    _emit_pipe_run,
    _emit_pipe_system,
    _emit_registers_equipment_devices,
    _emit_sleeve,
    _emit_stormwater_system,
    _emit_sump_pumps,
)
from typehaus.emit.ifc.roof import emit_roof
from typehaus.emit.ifc.site import (
    _emit_footing_bedding,
    _emit_site_representation,
    _emit_utilities,
    _georef,
)
from typehaus.emit.ifc.structural import (
    _emit_brace,
    _emit_construction_return,
    _emit_floor,
    _emit_solid,
    _emit_stair,
)
from typehaus.emit.trades import (
    DRAINAGE_CATEGORIES,
    PIPE_ACCESSORY_CATEGORIES,
    ROUTED_RUN_CATEGORIES,
)
from typehaus.model.enums import Service
from typehaus.resolve.model import ResolvedModel

#: ``emit_ifc`` is the whole public surface; the private names are re-exported because the
#: IFC tests read the system/accessory tables through this module's historical import path.
__all__ = ["emit_ifc", "_ACCESSORY_IFC_CLASS", "_PIPE_SYSTEM_OBJECT_TYPES",
           "_PIPE_SYSTEM_TYPES"]


def emit_ifc(model: ResolvedModel, out_path: Path, lod: str = "framed",
             sequence: bool = False, house_dir: Path | None = None) -> Path:
    """Emit the resolved model to an IFC4 file at ``out_path``. Returns the path.

    ``sequence=True`` additionally writes the derived work packages as
    ``IfcWorkPlan``/``IfcWorkSchedule``/``IfcTask`` plus ``IfcCostSchedule``/``IfcCostItem``
    (``emit/ifc/sequence.py``). Off by default: the permit IFC goes to a plan reviewer who
    wants geometry, and a construction schedule in that file is noise they have to page
    past. ``house_dir`` supplies ``prices.toml`` so the cost items carry numbers; without
    it the tasks still emit, priceless.
    """
    f = ll.new_file(IFC_APP_NAME)
    project_uuid = model.plan.project.project_uuid
    ifc_project = ll.create_entity(f, "IfcProject", name=model.plan.project.name)
    # Length/area/volume/plane-angle units, explicit and metric (→ lowlevel.assign_project_units):
    # left unset, Revit/SketchUp import against the IFC4 Reference View MVD's assumed default
    # rather than this file's actual (metre) coordinates.
    ll.assign_project_units(f)
    # IfcOpenShell attaches representation contexts to IfcProject; creating this first is
    # required by current 0.8.x APIs and keeps the output portable to Blender/Bonsai.
    body = ll.add_context(f)
    _georef(f, ifc_project, model, body.ParentContext)
    site = ll.create_entity(f, "IfcSite", name="Site")
    building = ll.create_entity(f, "IfcBuilding", name=model.plan.project.building.name)
    ll.aggregate(f, ifc_project, [site])
    ll.aggregate(f, site, [building])
    _emit_site_representation(f, body, site, model)

    storeys: dict[str, Any] = {}
    for storey in sorted(model.plan.storeys, key=lambda s: s.elevation.meters):
        ifc_storey = ll.create_entity(f, "IfcBuildingStorey", name=storey.tag)
        ll.set_storey_elevation(f, ifc_storey, storey.elevation.meters)
        ll.ensure_pset(f, ifc_storey, PSET_SOURCE,
                       {"uid": storey.uid, "tag": storey.tag})
        storeys[storey.tag] = ifc_storey
    ll.aggregate(f, building, list(storeys.values()))

    wall_types = _emit_wall_types(f, model, project_uuid)
    wall_entities: dict[str, Any] = {}
    for rw in sorted(model.walls, key=lambda w: w.uid):
        wall_entities[rw.tag] = _emit_wall(
            f, body, rw, storeys, project_uuid, lod, wall_types
        )

    opening_types = _emit_opening_types(f, model, project_uuid)

    for opening in sorted(model.openings, key=lambda o: o.uid):
        _emit_opening(f, body, opening, model, wall_entities, storeys, project_uuid, opening_types)

    # tag -> emitted entity, for the schedule emitter at the bottom of this function: an
    # IfcTask is assigned to the products it covers, and it can only be assigned to entities
    # that already exist. Collected as they are emitted rather than looked up afterwards —
    # ifcopenshell has no tag index, and building one would re-walk the whole file.
    element_entities: dict[str, Any] = dict(wall_entities)

    drainage_elements = []
    for solid in sorted(model.solids, key=lambda item: item.uid):
        # Pipe accessories have a dedicated emitter (``_emit_pipe_accessories``) that knows
        # which IfcValve PredefinedType each kind is. Emitting the solid too would put a
        # second, untyped copy of every shutoff in the file — and, since none of these
        # categories is in ``_SOLID_IFC_CLASS``, that copy would be an ``IfcFooting``.
        if (solid.category or "").lower() in PIPE_ACCESSORY_CATEGORIES:
            continue
        # And a routed run's own tube, for the same reason: ``_emit_pipe_run`` and
        # ``emit_conduits`` already export it as the segments it is. The solid is how glTF
        # and the viewer draw a run; in IFC it would be a duplicate, and an IfcFooting.
        if (solid.category or "").lower() in ROUTED_RUN_CATEGORIES:
            continue
        element = _emit_solid(f, body, solid, storeys, project_uuid, model)
        element_entities.setdefault(solid.tag, element)
        if (solid.category or "").lower() in DRAINAGE_CATEGORIES:
            drainage_elements.append(element)
    drainage_elements.extend(_emit_sump_pumps(f, model, storeys, project_uuid))
    _emit_stormwater_system(f, building, drainage_elements)

    for ret in sorted(model.construction_returns, key=lambda item: item.uid):
        _emit_construction_return(f, body, ret, storeys, project_uuid)

    for roof in sorted(model.roofs, key=lambda item: item.uid):
        emit_roof(f, body, roof, storeys, project_uuid, lod, model)

    for floor in sorted(model.floors, key=lambda item: item.uid):
        _emit_floor(f, body, floor, storeys, project_uuid, model)

    for stair in sorted(model.stairs, key=lambda item: item.uid):
        _emit_stair(f, body, stair, storeys, project_uuid, lod)

    for brace in sorted(model.braces, key=lambda item: item.uid):
        _emit_brace(f, body, brace, storeys, project_uuid)

    for room in sorted(model.rooms, key=lambda r: r.uid):
        _emit_space(f, body, room, storeys, project_uuid, model)

    _emit_furniture(f, body, model, storeys, project_uuid)
    _emit_resolved_placeables(f, body, model, storeys, project_uuid)

    # The piped distribution systems, built the way the stormwater one above is: the
    # segments and the devices on them are collected as they are emitted, then grouped, one
    # ``IfcDistributionSystem`` per authored ``PipeSystem``. Separate systems on purpose —
    # hot and cold are two systems in every tool that reads this (a recirculation loop, an
    # insulation requirement and a mixing valve belong to one and not the other), and the
    # waste side splits the same way (a cleanout schedule is sanitary; an air-admittance
    # question is vent). Every authored run lands in a system: ``system_elements`` covers
    # the whole ``PipeSystem`` enum via ``_PIPE_SYSTEM_TYPES``, so a ``.get(run.system, [])``
    # lookup cannot silently discard a system the dict lacks and leave a run unsystemed.
    # An accessory without a host
    # system (``accessory.system`` empty) stays ungrouped deliberately: inventing a system
    # for it would file a device under plumbing that nobody authored onto a run.
    system_elements: dict[str, list] = {key: [] for key in _PIPE_SYSTEM_TYPES}
    for run in sorted(model.pipe_runs, key=lambda item: item.uid):
        segments = _emit_pipe_run(f, body, run, storeys, project_uuid)
        system_elements[run.system].extend(segments)
    for accessory, entity in _emit_pipe_accessories(f, body, model, storeys, project_uuid):
        if (accessory.system or "") in system_elements:
            system_elements[accessory.system].append(entity)
    for system_key in _PIPE_SYSTEM_TYPES:
        _emit_pipe_system(f, building, system_key, system_elements[system_key])

    for sleeve in sorted(model.sleeves, key=lambda item: item.uid):
        _emit_sleeve(f, body, sleeve, storeys, project_uuid)

    for duct in sorted(model.ducts, key=lambda item: item.uid):
        _emit_duct_run(f, body, duct, storeys, project_uuid)

    raceways_by_service = emit_conduits(f, body, model, storeys, project_uuid,
                                        ll.assign_representation)
    emit_light_runs(f, body, model, storeys, project_uuid, ll.assign_representation)
    emit_solar_panels(f, body, model, storeys, project_uuid, ll.assign_representation)

    data_devices = _emit_registers_equipment_devices(f, body, model, storeys, project_uuid)
    # Structured cabling as one ``IfcDistributionSystem``, for the same reason the piped
    # systems above are: without it the raceway, the patch enclosure and the access point on
    # the end of it are unrelated elements that happen to be near each other, and a BIM
    # tool's system browser shows nothing under communications. Power raceways stay
    # ungrouped — a branch-circuit topology is the panel schedule's job, not the raceway's,
    # and inventing a system per circuit would claim a routing nobody authored.
    _emit_data_system(f, building, raceways_by_service.get(Service.DATA.value, []),
                      data_devices)
    _emit_utilities(f, body, model, project_uuid)

    for bedding in sorted(model.footing_beddings, key=lambda item: item.uid):
        _emit_footing_bedding(f, body, bedding, storeys, project_uuid)

    # Last, and that ordering is the contract stated in this module's docstring: cost and
    # task entities *reference* elements, so every product they assign has to exist first.
    if sequence:
        _emit_work_schedule(f, ifc_project, model, house_dir, element_entities)

    # Containment was collected rather than written as it went (→ ll.assign_container);
    # this is where it becomes entities, and it must happen before the file is serialized.
    ll.flush_containers(f)

    f.write(str(out_path))
    return out_path


def _emit_work_schedule(f: Any, ifc_project: Any, model: ResolvedModel,
                        house_dir: Any, element_entities: dict[str, Any]) -> None:
    """Derive the work packages and hand them to the sequence emitter.

    ``house_dir`` supplies ``prices.toml``: without it the packages still emit, carrying
    their elements and their order but no cost — which is the correct behaviour under
    decision #28, where dollars are opt-in and user-supplied.
    """
    from typehaus.emit.ifc.sequence import emit_sequence
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.tasks import build_work_items

    estimate = None
    if house_dir is not None:
        from pathlib import Path as _Path

        from typehaus.cli.prices import estimate_costs, load_prices

        try:
            prices = load_prices(_Path(house_dir))
        except ValueError:
            prices = None  # a malformed prices.toml must not stop the IFC export
        if prices is not None:
            from typehaus.server.space_summary import estimate_areas

            estimate = estimate_costs(bill_of_materials(model), prices,
                                      estimate_areas(model))
    bom = bill_of_materials(model)
    emit_sequence(f, ifc_project, model, build_work_items(model, bom, estimate),
                  element_entities)

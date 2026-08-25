"""IFC emission for the mechanical, electrical and plumbing trades — elements *and* systems.

Split out of :mod:`typehaus.emit.ifc.emitter` (→ AGENTS.md §1.1). Two halves live here, and
the second is why they are kept together: the elements (pipe and duct segments, in-line
accessories, cast-in sleeves, air terminals, HVAC equipment, electrical devices, sump pumps)
and the ``IfcDistributionSystem`` groupings that make them read as *systems* rather than as
loose proxies that happen to be near each other. Without the grouping tables a BIM tool's
system browser shows nothing at all under domestic water, sanitary or communications, so the
element emitter and the table naming its system have to change in one place.

Raceways, light runs and solar modules are the exception: they were already split into
:mod:`typehaus.emit.ifc.electrical` and stay there.

This module is over the 500-line budget and knows it. The seam it would split on is
distribution runs (pipes, ducts, systems) against placed products (terminals, equipment,
devices) — a real boundary, not an arbitrary one, but one that wants its own plan step.
"""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.architectural import _emit_service_ports, _type_identity
from typehaus.emit.trades import PIPE_ACCESSORY_CATEGORIES
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.placeables import resolved_mount_elevation

STORMWATER_SYSTEM_NAME = "Stormwater"


def _emit_sump_pumps(f: Any, model: ResolvedModel, storeys: dict[str, Any],
                     project_uuid: Any) -> list:
    """An ``IfcPump/SUMPPUMP`` for every pit that carries one.

    The pump is a spec on the ``Sump``, not an element with a plan position of its own, so
    it has no solid and would otherwise never reach IFC — leaving the export with a pit and
    no way to say the water leaves it under power. No representation: what matters here is
    that the equipment exists, is on a named circuit, and belongs to the stormwater system.
    """
    pumps = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            pump = getattr(element, "pump", None)
            if pump is None or element.element_kind != "Sump":
                continue
            entity = ll.create_entity(f, "IfcPump", name=f"{element.tag}-PUMP")
            entity.PredefinedType = "SUMPPUMP"
            entity.GlobalId = derive_child_guid(project_uuid, element.uid, "pump")
            ll.ensure_pset(f, entity, PSET_SOURCE, {
                "uid": element.uid, "tag": element.tag, "category": "sump_pump"})
            ll.ensure_pset(f, entity, "TypeHaus_SumpPump", {
                "model": pump.model, "horsepower": pump.horsepower,
                "discharge": pump.discharge or "", "circuit_ref": pump.circuit_ref or ""})
            ll.assign_container(f, entity, storeys[storey.tag])
            pumps.append(entity)
    return pumps


def _emit_stormwater_system(f: Any, building: Any, elements: list) -> Any:
    """Group every drainage element into one ``IfcDistributionSystem/STORMWATER``.

    The gutter, the leader it drops into, the perimeter tile and the pit are one system in
    the building even though they resolve from four unrelated authored elements. Saying so in
    IFC is the difference between a BIM tool showing "Stormwater" in its system browser and
    showing four unrelated proxies that happen to be near each other.
    """
    if not elements:
        return None
    system = ll.create_system(f, STORMWATER_SYSTEM_NAME, "STORMWATER")
    ll.assign_to_group(f, system, elements)
    ll.serves_building(f, system, building)
    return system


#: ``PipeSystem`` value → the ``IfcDistributionSystem`` it belongs to, as
#: ``(system name, PredefinedType)``. Every authored system is mapped — a run whose system
#: is missing here is *silently* unsystemed — exactly the failure mode this mapping exists
#: to catch. Rainwater alone is deliberately absent: gutters/leaders/drain tile are solids, not
#: ``PipeRun``s, and they already group under ``_emit_stormwater_system``/STORMWATER.
#:
#: PredefinedType choices, against IfcDistributionSystemEnum (IFC4):
#: * drain → ``SEWAGE``. The enum has no SANITARY member; SEWAGE is IFC4's sanitary
#:   drainage ("removal of foul water"), where DRAINAGE is the generic and WASTEWATER the
#:   treated-effluent variant. SEWAGE is the specific one a DWV stack is.
#: * vent → ``VENT`` — exact.
#: * radon → ``USERDEFINED`` with ``ObjectType`` "RADON" (→ ``_PIPE_SYSTEM_OBJECT_TYPES``).
#:   Folding it into VENT would claim the soil-gas riser connects to the plumbing vents,
#:   which is exactly what a radon rough-in must never do; the enum has no member for it,
#:   and USERDEFINED+ObjectType is IFC's way of saying so honestly.
#: * gas → ``GAS`` — exact (no catlin runs today, but an authored one must not vanish).
_PIPE_SYSTEM_TYPES = {
    "water_cold": ("DomesticColdWater", "DOMESTICCOLDWATER"),
    "water_hot": ("DomesticHotWater", "DOMESTICHOTWATER"),
    "drain": ("Sanitary", "SEWAGE"),
    "vent": ("SanitaryVent", "VENT"),
    "radon": ("RadonVent", "USERDEFINED"),
    "gas": ("Gas", "GAS"),
}


#: Where the enum has no member for what the system is, ``ObjectType`` carries the name —
#: the same convention ``_SOLID_OBJECT_TYPE`` uses for the drywell.
_PIPE_SYSTEM_OBJECT_TYPES = {"radon": "RADON"}


# What a ``PipeAccessoryKind`` becomes in IFC. The valves are ``IfcValve`` with the
# PredefinedType that says which valve it is — ISOLATING for a shutoff, DOUBLECHECK for a
# backflow assembly, ANTIVACUUM for a hose-bib vacuum breaker, DRAWOFFCOCK for the capped RO
# tee (a draw-off point that is not yet drawn off). The other two are not valves at all: an
# arrestor is a sealed chamber in the line and a penetration seal is a fitting around it, so
# both are ``IfcPipeFitting/USERDEFINED`` with an ObjectType naming what they are — inventing
# a valve type for either would put a device in a valve schedule that nobody can turn.
_ACCESSORY_IFC_CLASS: dict[str, tuple[str, str]] = {
    "main_shutoff": ("IfcValve", "ISOLATING"),
    "shutoff": ("IfcValve", "ISOLATING"),
    "backflow_preventer": ("IfcValve", "DOUBLECHECK"),
    "vacuum_breaker": ("IfcValve", "ANTIVACUUM"),
    "ro_stub": ("IfcValve", "DRAWOFFCOCK"),
    "water_hammer_arrestor": ("IfcPipeFitting", "USERDEFINED"),
    "penetration_seal": ("IfcPipeFitting", "USERDEFINED"),
}


_ACCESSORY_OBJECT_TYPE = {
    "water_hammer_arrestor": "WATERHAMMERARRESTOR",
    "penetration_seal": "PENETRATIONSEAL",
}


def _emit_pipe_accessories(f: Any, body: Any, model: ResolvedModel,
                           storeys: dict[str, Any], project_uuid: Any) -> list[tuple]:
    """Every in-line supply device as its own typed IFC element.

    Returns ``(accessory, entity)`` pairs so the caller can file each into the hot or cold
    system its host run belongs to. The box representation is the resolver's marker solid,
    rebuilt here rather than taken from ``model.solids`` because the generic solid loop
    deliberately skips this category — a device that fell through ``_SOLID_IFC_CLASS`` would
    export as an ``IfcFooting``, which is exactly the wart this emitter exists to avoid.
    """
    out: list[tuple] = []
    for accessory in sorted(model.pipe_accessories, key=lambda item: item.uid):
        ifc_class, predefined = _ACCESSORY_IFC_CLASS.get(
            accessory.kind, ("IfcPipeFitting", "USERDEFINED"))
        element = ll.create_entity(f, ifc_class, name=accessory.tag)
        element.PredefinedType = predefined
        object_type = _ACCESSORY_OBJECT_TYPE.get(accessory.kind)
        if object_type is not None:
            element.ObjectType = object_type
        element.GlobalId = derive_guid(project_uuid, accessory.uid)
        solid = next((s for s in model.solids
                      if s.tag == accessory.tag
                      and s.category in PIPE_ACCESSORY_CATEGORIES), None)
        if solid is not None and solid.outline:
            ll.assign_representation(f, element, ll.add_prism_from_profile(
                f, body, solid.outline, solid.z1_m - solid.z0_m, solid.z0_m))
        # The category is per-device (``emit/trades.py``), so it carries into the file as the
        # device rather than as the family — a downstream reader filtering PSET_SOURCE gets
        # "vacuum_breaker", the same string every other consumer of this solid sees.
        ll.ensure_pset(f, element, PSET_SOURCE, {
            "uid": accessory.uid, "tag": accessory.tag, "category": accessory.kind})
        ll.ensure_pset(f, element, "TypeHaus_PipeAccessory", {
            "kind": accessory.kind, "model": accessory.model,
            "pipe_ref": accessory.pipe_ref or "", "system": accessory.system or "",
            "accessible": accessory.accessible, "room": accessory.room or "",
            "serves": ", ".join(accessory.serves),
            "install_parts": ", ".join(accessory.install_parts)})
        ll.assign_container(f, element, storeys[accessory.storey])
        out.append((accessory, element))
    return out


def _emit_pipe_system(f: Any, building: Any, system_key: str, elements: list) -> Any:
    """Group one ``PipeSystem``'s segments and devices into an ``IfcDistributionSystem``.

    The same argument ``_emit_stormwater_system`` makes: without this the trunk, its
    branches and the shutoff on it are unrelated proxies that happen to be near each other,
    and a BIM tool's system browser shows nothing at all under domestic water — or, until
    the sanitary/vent systems landed, under the entire waste side of the house.
    """
    if not elements:
        return None
    name, predefined = _PIPE_SYSTEM_TYPES[system_key]
    system = ll.create_system(f, name, predefined)
    object_type = _PIPE_SYSTEM_OBJECT_TYPES.get(system_key)
    if object_type is not None:
        system.ObjectType = object_type
    ll.assign_to_group(f, system, elements)
    ll.serves_building(f, system, building)
    return system


def _emit_pipe_run(f: Any, body: Any, run: Any, storeys: dict[str, Any],
                   project_uuid: Any) -> list:
    """One ``IfcPipeSegment`` per path segment, each a real ``IfcSweptDiskSolid``.

    This used to be "a plan rectangle of width ``diameter_m`` around the centerline, extruded
    ``diameter_m`` tall at the segment's interpolated invert (a boxy placeholder profile, not
    a true cylindrical sweep)". The run now knows its own invert at every vertex, and IFC4
    has the idiom for exactly this shape, so a segment arrives as the pipe it is — including
    the vertical drops, which were a square prism and are now simply a directrix pointing
    down. ``_interpolated_invert`` survives only for a legacy run that authored two
    elevations and no ``z_m``.

    Returns the segments, so the caller can group a run's pieces into the
    ``IfcDistributionSystem`` its system belongs to."""
    segments: list = []
    radius = run.diameter_m / 2.0
    cumulative = 0.0
    z_m = getattr(run, "z_m", None)
    for index in range(len(run.path) - 1):
        p0, p1 = run.path[index], run.path[index + 1]
        seg_len = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
        if z_m is not None:
            z0, z1 = z_m[index], z_m[index + 1]
        else:
            invert = _interpolated_invert(run, cumulative, cumulative + seg_len)
            z0 = z1 = invert
        cumulative += seg_len
        if seg_len < 1e-6 and abs(z1 - z0) < 1e-9:
            continue  # a repeated vertex at one invert is one point, not a segment
        child_key = f"seg-{index:02d}"
        element = ll.create_entity(f, "IfcPipeSegment", name=f"{run.tag}/{child_key}")
        segments.append(element)
        element.GlobalId = derive_child_guid(project_uuid, run.uid, child_key)
        ll.assign_representation(f, element, ll.add_swept_disk(
            f, body, points_m=[(p0[0], p0[1], z0), (p1[0], p1[1], z1)], radius_m=radius,
        ))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": run.uid, "tag": run.tag})
        ll.ensure_pset(f, element, "TypeHaus_Pipe", {
            "system": run.system, "diameter_m": run.diameter_m,
            "slope": _slope_text(run),
            # Blank rather than absent where unset: a pset key that comes and goes makes a
            # schedule column that comes and goes.
            "material": run.material or "", "finish": run.finish or "",
            "insulation": run.insulation or "",
        })
        ll.assign_container(f, element, storeys[run.storey])
    return segments


def _interpolated_invert(run: Any, from_len: float, to_len: float) -> float:
    """Invert elevation at the segment midpoint, linearly interpolated along the run."""
    if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
        return run.z_start_m if run.z_start_m is not None else 0.0
    mid = (from_len + to_len) / 2.0
    t = mid / run.length_m
    return run.z_start_m + t * (run.z_end_m - run.z_start_m)


def _slope_text(run: Any) -> str:
    if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
        return "unknown"
    drop_in = (run.z_start_m - run.z_end_m) / M_PER_IN
    slope_in_per_ft = drop_in / (run.length_m * 3.280839895)
    return f"{slope_in_per_ft:.3f} in/ft"


def _emit_sleeve(f: Any, body: Any, sleeve: Any, storeys: dict[str, Any],
                 project_uuid: Any) -> None:
    """A visible marker at the exact cast-in-place point (host slab's full z0..z1)."""
    half = sleeve.sleeve_d_m / 2.0
    cx, cy = sleeve.center
    outline = [(cx - half, cy - half), (cx + half, cy - half),
               (cx + half, cy + half), (cx - half, cy + half)]
    element = ll.create_entity(f, "IfcBuildingElementProxy", name=sleeve.tag)
    element.GlobalId = derive_guid(project_uuid, sleeve.uid)
    ll.assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, sleeve.z1_m - sleeve.z0_m, sleeve.z0_m,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": sleeve.uid, "tag": sleeve.tag,
                                               "host": sleeve.host_slab})
    ll.ensure_pset(f, element, "TypeHaus_Sleeve", {
        "host": sleeve.host_slab,
        "pipe_diameter_in": sleeve.pipe_d_m / M_PER_IN,
        "sleeve_diameter_in": sleeve.sleeve_d_m / M_PER_IN,
        "serves_fixture": sleeve.serves_fixture or "",
    })
    ll.assign_container(f, element, storeys[sleeve.storey])


def _emit_duct_run(f: Any, body: Any, duct: Any, storeys: dict[str, Any],
                   project_uuid: Any) -> None:
    """One ``IfcDuctSegment`` per path segment — a swept disk for round, a prism for rect.

    This used to be a width x depth box at a z the emitter derived *here*, from the duct's
    joist bay or its storey: the only vertical information a duct had anywhere in the
    engine, which is why no other consumer could draw one and why every riser in the house
    was undrawn. The resolver owns that derivation now (→ resolve/mep_ducts.py) and hands
    over ``z_m`` per vertex, so a vertical leg exports as the vertical leg it is rather than
    as a zero-length box, and a round run exports as ``IfcSweptDiskSolid`` the way a pipe
    does instead of as a square prism pretending to be a pipe.
    """
    z_m = getattr(duct, "z_m", None) or ()
    for index in range(len(duct.path) - 1):
        p0, p1 = duct.path[index], duct.path[index + 1]
        seg_len = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
        z0, z1 = (z_m[index], z_m[index + 1]) if len(z_m) == len(duct.path) else (0.0, 0.0)
        if seg_len < 1e-6 and abs(z1 - z0) < 1e-9:
            continue  # a repeated vertex at one elevation is one point, not a segment
        child_key = f"seg-{index:02d}"
        element = ll.create_entity(f, "IfcDuctSegment", name=f"{duct.tag}/{child_key}")
        element.GlobalId = derive_child_guid(project_uuid, duct.uid, child_key)
        if duct.diameter_m is not None:
            representation = ll.add_swept_disk(
                f, body, points_m=[(p0[0], p0[1], z0), (p1[0], p1[1], z1)],
                radius_m=duct.diameter_m / 2.0,
            )
        else:
            # A rectangular run stays a prism: IFC has no mitred-rectangle sweep idiom, and
            # the plan-rectangle-at-the-lower-elevation shape is what every importer reads.
            # It is placed at the segment's own base now rather than at the whole run's.
            representation = ll.add_prism_from_profile(
                f, body, rect_between(p0, p1, -duct.width_m / 2.0, duct.width_m / 2.0),
                duct.depth_m, min(z0, z1) - duct.depth_m / 2.0,
            )
        ll.assign_representation(f, element, representation)
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": duct.uid, "tag": duct.tag})
        ll.ensure_pset(f, element, "TypeHaus_Duct", {
            "system": duct.system, "width_in": duct.width_m / M_PER_IN,
            "depth_in": duct.depth_m / M_PER_IN, "routing": duct.routing,
            # Blank rather than absent where unset: a pset key that comes and goes makes a
            # schedule column that comes and goes.
            "diameter_in": (duct.diameter_m / M_PER_IN
                            if duct.diameter_m is not None else 0.0),
            "material": duct.material or "", "insulation": duct.insulation or "",
        })
        ll.assign_container(f, element, storeys[duct.storey])


def _emit_data_system(f: Any, building: Any, raceways: list, devices: list) -> Any:
    """Structured cabling as one ``IfcDistributionSystem``/COMMUNICATION.

    COMMUNICATION rather than IfcDistributionSystemEnum's DATA: DATA is the narrower
    "data circuits" member, while COMMUNICATION is the one Revit and the common IFC
    importers map onto their Communication Devices category, which is where the access
    points need to land for this to be worth exporting at all."""
    elements = list(raceways) + list(devices)
    if not elements:
        return None
    system = ll.create_system(f, "Data", "COMMUNICATION")
    ll.assign_to_group(f, system, elements)
    ll.serves_building(f, system, building)
    return system


def _emit_registers_equipment_devices(f: Any, body: Any, model: ResolvedModel,
                                      storeys: dict[str, Any],
                                      project_uuid: Any) -> list[Any]:
    """Emit them all; return the low-voltage devices so they can join the data system.

    An access point that exports as a well-classed ``IfcCommunicationsAppliance`` but belongs
    to no system is still invisible in a BIM tool's system browser — the same argument
    ``_emit_pipe_system`` makes for a shutoff valve."""
    data_devices: list[Any] = []
    type_collections = {
        "Register": {item.tag: item for item in model.plan.library.register_types},
        "Equipment": {item.tag: item for item in model.plan.library.equipment_types},
        "ElectricalDevice": {item.tag: item for item in model.plan.library.electrical_device_types},
    }
    resolved = {item.uid: item for item in model.canvas_objects}
    type_cache: dict[tuple[str, str], Any] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            product_type = type_collections.get(element.element_kind, {}).get(getattr(element, "type_ref", None))
            resolved_item = resolved.get(element.uid)
            if element.element_kind == "Register":
                _emit_register(f, body, element, storey, storeys, project_uuid, product_type, resolved_item,
                               _placeable_ifc_type(f, type_cache, product_type, "IfcAirTerminal",
                                                   "IfcAirTerminalType", project_uuid))
            elif element.element_kind == "Equipment":
                ifc_class, type_class = _equipment_ifc_classes(element.kind.value)
                _emit_equipment(f, body, element, storey, storeys, project_uuid, product_type, resolved_item,
                                _placeable_ifc_type(f, type_cache, product_type, ifc_class,
                                                    type_class, project_uuid),
                                ifc_class)
            elif element.element_kind == "ElectricalDevice":
                ifc_class, type_class = _device_ifc_classes(element.kind.value, product_type)
                entity = _emit_device(
                    f, body, element, storey, storeys, project_uuid, product_type,
                    resolved_item,
                    _placeable_ifc_type(f, type_cache, product_type, ifc_class, type_class,
                                        project_uuid))
                if element.kind.value == "data_outlet":
                    data_devices.append(entity)
    return data_devices


def _emit_register(f: Any, body: Any, register: Any, storey: Any, storeys: dict[str, Any],
                   project_uuid: Any, product_type: Any | None, resolved: Any | None,
                   type_object: Any | None) -> None:
    x, y = register.position.xy_m
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, 0.10, 0.10)
    height = product_type.height.meters if product_type is not None else 0.05
    z0 = resolved.z_m if resolved is not None else storey.elevation.meters
    element = ll.create_entity(f, "IfcAirTerminal", name=register.tag)
    element.GlobalId = derive_guid(project_uuid, register.uid)
    ll.assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, height, z0,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": register.uid, "tag": register.tag,
                                               "rotation_degrees": _rotation_metadata(register, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": register.uid, "tag": register.tag,
                                                        "source_type": register.type_ref or ""})
    # Which family of terminal this is: a continuous-flow ventilation diffuser on the ERV's
    # balanced trunks, or a conditioned-air register on a heat-pump duct. Same IfcAirTerminal
    # class either way — they are sized on different bases, not built differently.
    ll.ensure_pset(f, element, "TypeHaus_AirTerminal", {
        "system": register.kind.value,
        "terminal_style": ("ventilation"
                           if getattr(product_type, "ventilation_terminal", False)
                           else "conditioned_air"),
        "duct_ref": register.duct_ref or "",
    })
    if product_type is not None:
        _emit_service_ports(f, element, product_type.ports, project_uuid, register.uid)
    if type_object is not None:
        ll.assign_type(f, element, type_object)
    ll.assign_container(f, element, storeys[storey.tag])


def _rotation_metadata(element: Any, resolved: Any | None) -> str:
    """Persist the resolved plan bearing so IFC reconciliation can name rotation edits."""
    degrees = resolved.rotation_degrees if resolved is not None else getattr(
        getattr(element, "rotation", None), "degrees", 0.0,
    )
    return f"{degrees:.6f}"


def _equipment_ifc_classes(kind: str) -> tuple[str, str]:
    """Map an ``EquipmentKind`` onto a real IFC class where one exists.

    Split systems are ``IfcUnitaryEquipment`` — the IFC4 class for a packaged
    heating/cooling unit, which is what a condenser, a wall head and a concealed ducted air
    handler each are — and an ERV is ``IfcAirToAirHeatRecovery``. Everything else (water
    heaters, sauna heaters, resistance space heaters) has no better fit than the proxy it
    already emitted as — including FURNACE and AIR_HANDLER, which are arguably unitary
    equipment too but which nothing models yet; re-classing an element nobody authors would
    churn the round-trip diff for no reader's benefit.

    GUIDs are unaffected: ``derive_guid`` keys on the element uid, not the class, so a unit
    that was a proxy in an earlier emit keeps its GlobalId across this change.

    Mirrored by ``diff/ifc_adapter.py`` (``class_for_kind`` plus the external read list) —
    change both together or the round-trip diff reads the class change as a deletion.
    """
    return {
        "heat_pump": ("IfcUnitaryEquipment", "IfcUnitaryEquipmentType"),
        "indoor_head": ("IfcUnitaryEquipment", "IfcUnitaryEquipmentType"),
        "ducted_air_handler": ("IfcUnitaryEquipment", "IfcUnitaryEquipmentType"),
        "erv": ("IfcAirToAirHeatRecovery", "IfcAirToAirHeatRecoveryType"),
    }.get(kind, ("IfcBuildingElementProxy", "IfcBuildingElementProxyType"))


def _emit_equipment(f: Any, body: Any, equipment: Any, storey: Any, storeys: dict[str, Any],
                    project_uuid: Any, product_type: Any | None, resolved: Any | None,
                    type_object: Any | None,
                    ifc_class: str = "IfcBuildingElementProxy") -> None:
    width, depth = (dim.meters for dim in equipment.footprint)
    x, y = equipment.position.xy_m
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, width, depth)
    height = product_type.height.meters if product_type is not None else 1.5
    z0 = resolved.z_m if resolved is not None else storey.elevation.meters
    element = ll.create_entity(f, ifc_class, name=equipment.tag)
    element.GlobalId = derive_guid(project_uuid, equipment.uid)
    ll.assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, height, z0,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": equipment.uid, "tag": equipment.tag,
                                               "rotation_degrees": _rotation_metadata(equipment, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": equipment.uid, "tag": equipment.tag,
                                                        "source_type": equipment.type_ref or ""})
    # The HVAC facts a Revit/SketchUp reader needs to identify the unit and its zone: the
    # ratings from the type, and the two authored relations (which rooms it serves, which
    # condenser it pairs with) that no geometry can carry. Empty string / 0.0 where the
    # datasheet number is not authored — an absent property is indistinguishable from a
    # property this emitter forgot.
    ll.ensure_pset(f, element, "TypeHaus_Equipment", {
        "kind": equipment.kind.value, "circuit": equipment.circuit or "",
        "zone_rooms": ",".join(getattr(equipment, "zone_rooms", ()) or ()),
        "outdoor_ref": getattr(equipment, "outdoor_ref", None) or "",
        "heating_capacity_btuh": float(
            getattr(product_type, "heating_capacity_btuh", None) or 0.0),
        "heating_capacity_at_design_btuh": float(
            getattr(product_type, "heating_capacity_at_design_btuh", None) or 0.0),
        "cooling_capacity_btuh": float(
            getattr(product_type, "cooling_capacity_btuh", None) or 0.0),
        "min_operating_temp_f": float(
            getattr(product_type, "min_operating_temp_f", None) or 0.0),
        "ventilation_cfm": float(getattr(product_type, "ventilation_cfm", None) or 0.0),
        "sensible_recovery_effectiveness": float(
            getattr(product_type, "sensible_recovery_effectiveness", None) or 0.0),
    })
    if product_type is not None:
        _emit_service_ports(f, element, product_type.ports, project_uuid, equipment.uid)
    if type_object is not None:
        ll.assign_type(f, element, type_object)
    ll.assign_container(f, element, storeys[storey.tag])


def _emit_device(f: Any, body: Any, device: Any, storey: Any, storeys: dict[str, Any],
                 project_uuid: Any, product_type: Any | None, resolved: Any | None,
                 type_object: Any | None) -> Any:
    x, y = device.position.xy_m
    half = 0.05  # 4"x4" nominal device box
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, half * 2, half * 2)
    # The placeable resolver owns the Mount contract, so IFC reads the same elevation as
    # glTF and the UI instead of carrying its own per-kind defaults (which would diverge).
    z0 = resolved.z_m if resolved is not None else resolved_mount_elevation(storey, device)
    ifc_class, _ = _device_ifc_classes(device.kind.value, product_type)
    element = ll.create_entity(f, ifc_class, name=device.tag)
    element.GlobalId = derive_guid(project_uuid, device.uid)
    predefined = getattr(product_type, "ifc_predefined_type", None)
    if predefined and hasattr(element, "PredefinedType"):
        element.PredefinedType = predefined
    ll.assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, product_type.height.meters if product_type is not None else 0.05, z0))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": device.uid, "tag": device.tag,
                                               "rotation_degrees": _rotation_metadata(device, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": device.uid, "tag": device.tag,
                                                        "source_type": device.type_ref or ""})
    ll.ensure_pset(f, element, "TypeHaus_Device", {
        "kind": device.kind.value, "circuit": device.circuit or "",
        # A PoE device names no circuit — its power arrives over the data cable — so the
        # schedule needs the watts here or the load has nowhere to be read.
        "poe_watts": getattr(product_type, "poe_watts", None) or 0.0,
    })
    if product_type is not None:
        _emit_service_ports(f, element, product_type.ports, project_uuid, device.uid)
    if type_object is not None:
        ll.assign_type(f, element, type_object)
    ll.assign_container(f, element, storeys[storey.tag])
    return element


def _placeable_ifc_type(f: Any, cache: dict[tuple[str, str], Any], product_type: Any | None,
                        ifc_class: str, type_class: str, project_uuid: Any) -> Any | None:
    if product_type is None:
        return None
    key = (ifc_class, product_type.tag)
    if key not in cache:
        entity = ll.create_entity(f, type_class, name=product_type.name)
        entity.GlobalId = derive_child_guid(project_uuid, f"{ifc_class}-types", product_type.tag)
        ll.ensure_pset(f, entity, "TypeHaus_Identity", _type_identity(product_type))
        photometry = _luminaire_photometry(product_type)
        if photometry:
            ll.ensure_pset(f, entity, "TypeHaus_Lighting", photometry)
        cache[key] = entity
    return cache[key]


def _luminaire_photometry(product_type: Any) -> dict[str, Any]:
    """A luminaire type's photometric row, or empty for anything that is not a luminaire.

    Colour temperature is a *type* property in every tool that models it — Revit's Initial
    Color Temperature, IFC's own light source — which is exactly why it belongs on the
    ``IfcLightFixtureType`` and not on each placed can. Two marks that differ only in
    Kelvin are therefore two IFC types, and this pset is what tells them apart downstream.
    Keys mirror ``emit/ifc/electrical.emit_light_runs`` so the point fixtures and the tape
    runs read alike; ``0``/``""`` stand in for a missing value because IFC psets are typed
    and a null would need a different property class.
    """
    form = getattr(product_type, "form", None)
    if form is None or getattr(product_type, "cct_k", "missing") == "missing":
        return {}
    return {
        "form": getattr(form, "value", str(form)),
        "type_mark": getattr(product_type, "type_mark", None) or "",
        "lamp": getattr(product_type, "lamp", None) or "",
        "watts": getattr(product_type, "watts", None) or 0.0,
        "watts_per_ft": getattr(product_type, "watts_per_ft", None) or 0.0,
        "lumens": getattr(product_type, "lumens", None) or 0.0,
        "cct_k": getattr(product_type, "cct_k", None) or 0,
        "cri": getattr(product_type, "cri", None) or 0,
        "voltage": getattr(product_type, "voltage", 120),
        "dimmable": bool(getattr(product_type, "dimmable", False)),
        "damp_rated": bool(getattr(product_type, "damp_rated", False)),
        "wet_rated": bool(getattr(product_type, "wet_rated", False)),
    }


def _device_ifc_classes(kind: str, product_type: Any | None = None) -> tuple[str, str]:
    """The IFC entity pair for a device: its product type wins, else the kind map.

    ``DeviceKind`` is the plan-symbol axis and is deliberately coarse — one ``DATA_OUTLET``
    covers a patch enclosure, a wireless access point and a PoE camera, which share a glyph
    and the E-COMM layer but are three different IFC entities landing in three different
    Revit categories. Letting ``ElectricalDeviceType.ifc_entity`` override means the next
    low-voltage product is one catalog entry rather than a patch to five engine maps."""
    entity = getattr(product_type, "ifc_entity", None)
    if entity:
        type_entity = getattr(product_type, "ifc_type_entity", None) or f"{entity}Type"
        return entity, type_entity
    # Mirrored by diff/ifc_adapter.py (electrical_classes + the external read list) —
    # change both together or the round-trip diff reads an edit as a deletion.
    return {
        "receptacle": ("IfcOutlet", "IfcOutletType"), "gfci": ("IfcOutlet", "IfcOutletType"),
        "receptacle_240": ("IfcOutlet", "IfcOutletType"),
        "switch": ("IfcSwitchingDevice", "IfcSwitchingDeviceType"),
        "light": ("IfcLightFixture", "IfcLightFixtureType"),
        "panel": ("IfcElectricDistributionBoard", "IfcElectricDistributionBoardType"),
        "junction_box": ("IfcJunctionBox", "IfcJunctionBoxType"),
        "meter": ("IfcFlowMeter", "IfcFlowMeterType"),
        "disconnect": ("IfcSwitchingDevice", "IfcSwitchingDeviceType"),
        # Bare fallback for a low-voltage device whose type names no ``ifc_entity``: a data
        # jack is an outlet. Access points and cameras override it on the type.
        "data_outlet": ("IfcOutlet", "IfcOutletType"),
    }.get(kind, ("IfcBuildingElementProxy", "IfcBuildingElementProxyType"))


def _rectangle(x: float, y: float, width: float, depth: float) -> list[tuple[float, float]]:
    return [(x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
            (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2)]

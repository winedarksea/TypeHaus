"""Alarm heads as ``IfcSensor``s: the resolved body (``resolve/alarm_heads.py``) the viewer and
the GLB draw, the head's ``ElectricalDeviceType`` as its IFC type, contained in its storey."""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.mep import _placeable_ifc_type
from typehaus.model.ids import derive_guid
from typehaus.resolve.model import ResolvedModel

# IFC4 IfcSensorTypeEnum by AlarmKind. A combo head reads as its smoke sensor; the
# ``TypeHaus_Device.kind`` pset keeps the CO half. A freeze alert is a thermometer, not
# FROSTSENSOR (ice on a surface).
SENSOR_PREDEFINED = {
    "smoke": "SMOKESENSOR", "combo": "SMOKESENSOR", "co": "COSENSOR",
    "heat": "HEATSENSOR", "leak": "MOISTURESENSOR", "freeze": "TEMPERATURESENSOR",
}


def emit_alarms(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                project_uuid: Any) -> None:
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    alarms = {a.uid: a for storey in model.plan.storeys
              for a in model.plan.storey_elements(storey.tag) if a.element_kind == "Alarm"}
    type_cache: dict[tuple[str, str], Any] = {}
    for head in sorted(model.alarm_heads, key=lambda item: item.uid):
        if head.body is None:
            continue
        alarm = alarms[head.uid]
        product_type = types.get(head.type_ref) if head.type_ref else None
        entity = getattr(product_type, "ifc_entity", None) or "IfcSensor"
        type_entity = getattr(product_type, "ifc_type_entity", None) or f"{entity}Type"
        element = ll.create_entity(f, entity, name=head.tag)
        element.GlobalId = derive_guid(project_uuid, head.uid)
        predefined = (getattr(product_type, "ifc_predefined_type", None)
                      or (SENSOR_PREDEFINED[head.kind] if entity == "IfcSensor" else None))
        if predefined and hasattr(element, "PredefinedType"):
            element.PredefinedType = predefined
        prism = head.body.solids[0]
        ll.assign_representation(f, element, ll.add_prism_from_profile(
            f, body, list(prism.ring), prism.z1_m - prism.z0_m, prism.z0_m))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": head.uid, "tag": head.tag})
        ll.ensure_pset(f, element, "TypeHaus_Identity", {
            "uid": head.uid, "tag": head.tag, "source_type": head.type_ref or ""})
        ll.ensure_pset(f, element, "TypeHaus_Device", {
            "kind": head.kind, "circuit": alarm.circuit or "", "mount": head.mount,
            "room": alarm.room or ""})
        type_object = _placeable_ifc_type(f, type_cache, product_type, entity, type_entity,
                                          project_uuid)
        if type_object is not None:
            if predefined and hasattr(type_object, "PredefinedType"):
                type_object.PredefinedType = predefined
            ll.assign_type(f, element, type_object)
        ll.assign_container(f, element, storeys[head.storey])

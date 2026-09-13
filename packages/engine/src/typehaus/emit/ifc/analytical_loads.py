"""Load cases, actions and combinations — the loads the calculations actually consumed.

One ``IfcStructuralLoadCase`` per source, one action per load in the graph, each connected
to the structural item it acts on with ``IfcRelConnectsStructuralActivity`` — SAP2000 and
ETABS import an action *only* through that relationship, so an unconnected action is an
action that silently does not arrive.

Nothing here derives a load. Every number comes off ``analytical/graph``, which took it
from the record that graded the member; a load case that disagreed with the calc sheet
beside it in the same bundle would be worse than none. Each action's property set names
the ``source`` string that says which record and which quantity.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from typehaus.analytical.graph import (
    AnalyticalModel,
    LoadCaseKind,
    MemberLoad,
    MemberPointLoad,
    NodeLoad,
)
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.analytical import PSET_ANALYTICAL, AnalyticalEntities
from typehaus.model.ids import derive_child_guid

_ANALYTICAL_NS = "analytical"

#: ``(IfcActionTypeEnum, IfcActionSourceTypeEnum)`` per case. ``ActionType`` is the
#: Eurocode permanent/variable split IFC borrowed; ``ActionSource`` names the physics.
#: Earth pressure has no member in ``IfcActionSourceTypeEnum`` (checked against the IFC4
#: schema), so it is USERDEFINED and the ``Purpose`` field says what it is — the honest
#: statement, where mapping it onto SETTLEMENT_U would be a different load.
_CASE_ACTION = {
    LoadCaseKind.DEAD: ("PERMANENT_G", "DEAD_LOAD_G", None),
    LoadCaseKind.LIVE: ("VARIABLE_Q", "LIVE_LOAD_Q", None),
    LoadCaseKind.SNOW: ("VARIABLE_Q", "SNOW_S", None),
    LoadCaseKind.WIND: ("VARIABLE_Q", "WIND_W", None),
    LoadCaseKind.EARTH: ("PERMANENT_G", "USERDEFINED", "earth pressure"),
    LoadCaseKind.GUARD: ("VARIABLE_Q", "LIVE_LOAD_Q", "IRC R301.5 guard point load"),
}

#: A graph direction -> the ``IfcStructuralLoad*`` attribute for that global axis.
_LINEAR_AXIS = {"GX": "LinearForceX", "GY": "LinearForceY", "GZ": "LinearForceZ"}
_FORCE_AXIS = {"GX": "ForceX", "GY": "ForceY", "GZ": "ForceZ"}


def emit_analytical_loads(f: Any, model: AnalyticalModel, entities: AnalyticalEntities,
                          project_uuid: UUID) -> None:
    """Write the cases, their actions and the combinations over them."""
    cases: dict[LoadCaseKind, Any] = {}
    actions: dict[LoadCaseKind, list] = {}
    for case in sorted(model.cases, key=lambda c: c.kind.value):
        cases[case.kind] = _load_case(f, case, project_uuid)
        actions[case.kind] = []

    for index, load in enumerate(model.member_loads):
        entity = _linear_action(f, model, load, entities, project_uuid, index)
        if entity is not None:
            actions.setdefault(load.case, []).append(entity)
    for index, load in enumerate(model.member_point_loads):
        entity = _member_point_action(f, model, load, entities, project_uuid, index)
        if entity is not None:
            actions.setdefault(load.case, []).append(entity)
    for index, load in enumerate(model.node_loads):
        entity = _node_action(f, load, entities, project_uuid, index)
        if entity is not None:
            actions.setdefault(load.case, []).append(entity)

    for kind, case_entity in cases.items():
        # The case OWNS its actions: ``IfcStructuralLoadGroup.IsGroupedBy`` is how a reader
        # asks "what is in the dead case", and an ungrouped action belongs to no case.
        members = actions.get(kind) or []
        if members:
            ll.assign_to_group(f, case_entity, members)

    if cases:
        entities.analysis_model.LoadedBy = [cases[kind] for kind in
                                            sorted(cases, key=lambda k: k.value)]
    entities.analysis_model.HasResults = None
    _combinations(f, model, cases, project_uuid)


def _load_case(f: Any, case: Any, project_uuid: UUID) -> Any:
    import ifcopenshell.api.structural

    action_type, action_source, purpose = _CASE_ACTION[case.kind]
    entity = ifcopenshell.api.structural.add_structural_load_case(
        f, name=case.name, action_type=action_type, action_source=action_source)
    entity.GlobalId = derive_child_guid(project_uuid, _ANALYTICAL_NS, f"case:{case.name}")
    if purpose:
        entity.Purpose = purpose
    ll.ensure_pset(f, entity, PSET_ANALYTICAL,
                   {"case": case.name, "description": case.description})
    return entity


# --- actions ---------------------------------------------------------------------------


def _linear_action(f: Any, model: AnalyticalModel, load: MemberLoad,
                   entities: AnalyticalEntities, project_uuid: UUID,
                   index: int) -> Any | None:
    member = entities.members.get(load.member)
    if member is None:
        return None
    partial = load.x0 != 0.0 or load.x1 != 1.0
    tapered = load.w0_n_m != load.w1_n_m
    if partial or tapered:
        applied = _load_configuration(f, model, load)
        predefined = "LINEAR" if tapered else "CONST"
    else:
        applied = _linear_force(f, load.direction, load.w0_n_m, load.source)
        predefined = "CONST"
    action = _activity(f, applied, member, "IfcStructuralLinearAction", predefined)
    action.Name = f"{load.case.value}:{load.member}"
    # TRUE_LENGTH: the graph's w is per metre OF MEMBER, not per metre of its plan
    # projection. A sloped rafter read as PROJECTED_LENGTH is short by its own cosine.
    action.ProjectedOrTrue = "TRUE_LENGTH"
    action.GlobalId = derive_child_guid(
        project_uuid, _ANALYTICAL_NS, f"line:{load.case.value}:{load.member}:{index}")
    ll.ensure_pset(f, action, PSET_ANALYTICAL, {
        "case": load.case.value, "member": load.member, "source": load.source,
        "direction": load.direction, "w0_n_per_m": float(load.w0_n_m),
        "w1_n_per_m": float(load.w1_n_m), "x0": float(load.x0), "x1": float(load.x1),
    })
    return action


def _linear_force(f: Any, direction: str, value: float, name: str) -> Any:
    load = f.create_entity("IfcStructuralLoadLinearForce", Name=name or None)
    setattr(load, _LINEAR_AXIS[direction], float(value))
    return load


def _load_configuration(f: Any, model: AnalyticalModel, load: MemberLoad) -> Any:
    """A trapezoid or a partial load as two forces at two stations along the member.

    ``IfcStructuralLoadConfiguration`` is the schema's own answer and ifcopenshell has no
    api for it, so it is written directly. ``Locations`` are lengths along the member from
    its i end, which is what the fractions in the graph mean.
    """
    length = model.length_m(model.member(load.member))
    values = [_linear_force(f, load.direction, load.w0_n_m, load.source),
              _linear_force(f, load.direction, load.w1_n_m, load.source)]
    return f.create_entity(
        "IfcStructuralLoadConfiguration", Name=load.source or None, Values=values,
        Locations=[[float(load.x0 * length)], [float(load.x1 * length)]])


def _member_point_action(f: Any, model: AnalyticalModel, load: MemberPointLoad,
                         entities: AnalyticalEntities, project_uuid: UUID,
                         index: int) -> Any | None:
    member = entities.members.get(load.member)
    if member is None:
        return None
    applied = _single_force(f, load.direction, load.p_n, load.source)
    action = _activity(f, applied, member, "IfcStructuralPointAction")
    action.Name = f"{load.case.value}:{load.member}@{load.x:g}"
    action.GlobalId = derive_child_guid(
        project_uuid, _ANALYTICAL_NS, f"point:{load.case.value}:{load.member}:{index}")
    graph_member = model.member(load.member)
    a, b = model.node(graph_member.n0), model.node(graph_member.n1)
    at = tuple(float(pa + (pb - pa) * load.x) for pa, pb in zip(a.xyz, b.xyz, strict=True))
    origin = f.createIfcCartesianPoint(at)
    action.ObjectPlacement = f.createIfcLocalPlacement(
        None, f.createIfcAxis2Placement3D(origin, None, None))
    ll.ensure_pset(f, action, PSET_ANALYTICAL, {
        "case": load.case.value, "member": load.member, "source": load.source,
        "direction": load.direction, "p_n": float(load.p_n),
        "location_fraction": float(load.x),
    })
    return action


def _node_action(f: Any, load: NodeLoad, entities: AnalyticalEntities,
                 project_uuid: UUID, index: int) -> Any | None:
    connection = entities.connections.get(load.node)
    if connection is None:
        return None
    applied = f.create_entity(
        "IfcStructuralLoadSingleForce", Name=load.source or None,
        ForceX=float(load.fx_n) or None, ForceY=float(load.fy_n) or None,
        ForceZ=float(load.fz_n) or None, MomentX=float(load.mx_nm) or None,
        MomentY=float(load.my_nm) or None, MomentZ=float(load.mz_nm) or None)
    action = _activity(f, applied, connection, "IfcStructuralPointAction")
    action.Name = f"{load.case.value}:{load.node}"
    action.GlobalId = derive_child_guid(
        project_uuid, _ANALYTICAL_NS, f"node-load:{load.case.value}:{load.node}:{index}")
    ll.ensure_pset(f, action, PSET_ANALYTICAL, {
        "case": load.case.value, "node": load.node, "source": load.source,
        "fx_n": float(load.fx_n), "fy_n": float(load.fy_n), "fz_n": float(load.fz_n),
        "mx_n_m": float(load.mx_nm), "my_n_m": float(load.my_nm),
        "mz_n_m": float(load.mz_nm),
    })
    return action


def _single_force(f: Any, direction: str, value: float, name: str) -> Any:
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name or None)
    setattr(load, _FORCE_AXIS[direction], float(value))
    return load


def _activity(f: Any, applied: Any, item: Any, ifc_class: str,
              predefined_type: str | None = None) -> Any:
    """The action plus the ``IfcRelConnectsStructuralActivity`` that makes it arrive.

    SAP2000 and ETABS import an action only when it reaches a structural item through this
    relationship; without it the load is in the file and in no analysis.
    """
    import ifcopenshell.api.structural

    kwargs = {"ifc_class": ifc_class, "global_or_local": "GLOBAL_COORDS"}
    if predefined_type is not None:
        kwargs["predefined_type"] = predefined_type
    return ifcopenshell.api.structural.add_structural_activity(
        f, applied_load=applied, structural_member=item, **kwargs)


def _combinations(f: Any, model: AnalyticalModel, cases: dict[LoadCaseKind, Any],
                  project_uuid: UUID) -> None:
    """Each ASD combination as a LOAD_COMBINATION group over its cases, factor and all.

    ``IfcRelAssignsToGroupByFactor`` carries the factor, which is the only place in IFC a
    combination's coefficients can live without inventing a property convention.
    """
    import ifcopenshell.api.structural

    for combination in sorted(model.combinations, key=lambda c: c.name):
        group = ifcopenshell.api.structural.add_structural_load_group(
            f, name=combination.name)
        group.PredefinedType = "LOAD_COMBINATION"
        group.GlobalId = derive_child_guid(project_uuid, _ANALYTICAL_NS,
                                           f"combination:{combination.name}")
        ll.ensure_pset(f, group, PSET_ANALYTICAL,
                       {"combination": combination.name, "source": combination.source})
        for kind in sorted(combination.factors, key=lambda k: k.value):
            case_entity = cases.get(kind)
            if case_entity is None:
                continue
            f.create_entity(
                "IfcRelAssignsToGroupByFactor", GlobalId=ll.new_guid(),
                Name=f"{combination.name}:{kind.value}", RelatedObjects=[case_entity],
                RelatingGroup=group, Factor=float(combination.factors[kind]))

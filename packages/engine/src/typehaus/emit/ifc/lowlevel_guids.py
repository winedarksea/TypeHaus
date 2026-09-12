"""Make an IFC file's machine-minted GUIDs a function of its content, not of the clock.

Every element this engine emits already carries a GUID derived from its own uid, so two
runs agree about the building. What they did not agree about is everything ifcopenshell
mints for us on the way past: ``IfcRelAggregates``, ``IfcRelContainedInSpatialStructure``,
``IfcRelAssociatesMaterial``, ``IfcRelDefinesByProperties`` and the property sets
themselves all get a fresh uuid4 per run, and the STEP header carries a wall-clock
timestamp. The file therefore differed in a few thousand bytes between two identical
builds.

That matters for exactly one reason, and it is not tidiness: ``haus handoff`` hands a PE a
bundle with a manifest of sha256s. If regenerating the bundle changes the hashes, the
manifest proves nothing — a reviewer cannot tell a re-run from an edit, and neither can the
owner six months later.

**A GUID is rewritten, never re-derived from scratch**, and only for entities that have no
identity of their own. A relationship's identity is what it relates: the tuple of
``(type, name, relating, related...)`` is hashed under the project's own uuid5 namespace, so
the same building always produces the same GUID and two different relationships never
collide. Where two genuinely identical relationships exist, an ordinal breaks the tie in
file order, which is itself deterministic.
"""

from __future__ import annotations

import contextlib
import uuid
from typing import Any

#: The entity families whose GUIDs this engine does not author. Anything NOT listed keeps
#: the GUID it was given: an element's identity comes from its model uid and rewriting it
#: would break every external reference to the file.
_MACHINE_MINTED = (
    "IfcRelAggregates",
    "IfcRelAssignsToGroup",
    "IfcRelAssignsToProduct",
    "IfcRelAssociatesMaterial",
    "IfcRelConnectsStructuralMember",
    "IfcRelContainedInSpatialStructure",
    "IfcRelDefinesByProperties",
    "IfcRelDefinesByType",
    "IfcRelFillsElement",
    "IfcRelNests",
    "IfcRelServicesBuildings",
    "IfcRelVoidsElement",
)

#: Definitions a relationship POINTS AT. These are pinned first, because a relationship's
#: identity hashes its ends' GUIDs — pin the relationship before the property set it
#: relates and it hashes a uuid4 that is about to be replaced.
_MACHINE_MINTED_DEFINITIONS = (
    "IfcPropertySet",
    "IfcElementQuantity",
)

#: The attributes that carry "what this relates to", tried in order. A relationship names
#: its subject in one of these; the rest of its attributes are metadata.
_RELATING = ("RelatingObject", "RelatingStructure", "RelatingMaterial", "RelatingSystem",
             "RelatingPropertyDefinition", "RelatingType", "RelatingOpeningElement",
             "RelatingBuildingElement", "RelatingGroup", "RelatingProduct",
             "RelatingElement")
_RELATED = ("RelatedObjects", "RelatedElements", "RelatedFeatureElement",
            "RelatedBuildingElement", "RelatedOpeningElement", "RelatedStructuralMember",
            "RelatedBuildings", "RelatedObject")


def pin_relationship_guids(f: Any, project_uuid: uuid.UUID) -> int:
    """Rewrite every machine-minted GUID as a uuid5 of what it relates; return the count."""
    import ifcopenshell.guid

    namespace = uuid.uuid5(project_uuid, "typehaus/ifc/relationships")
    seen: dict[str, int] = {}
    rewritten = 0
    for kind in _MACHINE_MINTED_DEFINITIONS + _MACHINE_MINTED:
        try:
            entities = f.by_type(kind)
        except RuntimeError:
            # The schema has no such entity — IFC4 vs IFC4X3, or a build without it.
            continue
        for entity in entities:
            key = _identity(entity, kind)
            ordinal = seen.get(key, 0)
            seen[key] = ordinal + 1
            if ordinal:
                key = f"{key}#{ordinal}"
            entity.GlobalId = ifcopenshell.guid.compress(uuid.uuid5(namespace, key).hex)
            rewritten += 1
    return rewritten


def _identity(entity: Any, kind: str) -> str:
    """What this relationship IS, as a string: its type, its name, and both of its ends."""
    parts = [kind, str(getattr(entity, "Name", None) or "")]
    for attribute in _RELATING:
        value = getattr(entity, attribute, None)
        if value is not None:
            parts.append(f"{attribute}={_reference(value)}")
            break
    related: list[str] = []
    for attribute in _RELATED:
        value = getattr(entity, attribute, None)
        if value is None:
            continue
        items = value if isinstance(value, (tuple, list)) else [value]
        related.extend(_reference(item) for item in items)
    # Sorted: the order ifcopenshell hands back a relationship's members is not part of what
    # the relationship means, and sorting keeps a reordering from minting a new GUID.
    parts.append("related=" + ",".join(sorted(related)))
    return "|".join(parts)


def _reference(entity: Any) -> str:
    """A stable name for one end of a relationship — its own GUID where it has one."""
    guid = getattr(entity, "GlobalId", None)
    if guid:
        return str(guid)
    name = getattr(entity, "Name", None)
    return f"{entity.is_a()}:{name}" if name else f"{entity.is_a()}:{entity.id()}"


#: The STEP header timestamp. Pinned rather than omitted: ``FILE_NAME`` requires the field,
#: and the epoch is the reproducible-builds convention for "no meaningful time here".
PINNED_TIMESTAMP = "1980-01-01T00:00:00"


def pin_header_timestamp(f: Any) -> None:
    """Replace the wall-clock ``FILE_NAME.time_stamp`` with a fixed one."""
    # An ifcopenshell build that does not expose the header this way is survivable: the
    # manifest will notice the drift, and a crash here would take the whole emit with it
    # for one cosmetic field.
    with contextlib.suppress(AttributeError, RuntimeError):
        f.header.file_name.time_stamp = PINNED_TIMESTAMP


def pin_project_guid(ifc_project: Any, project_uuid: uuid.UUID) -> None:
    """The project's GUID is the project's uuid, which is exactly what it means.

    ``root.create_entity`` mints a uuid4 for it like anything else. Every element in the
    file already derives its GUID from this same project uuid (``model/ids.py``), so the
    project taking a random one was the one identity in the file that was not a function of
    the model.
    """
    import ifcopenshell.guid

    ifc_project.GlobalId = ifcopenshell.guid.compress(project_uuid.hex)


def pin_unit_order(f: Any) -> None:
    """Sort ``IfcUnitAssignment.Units``.

    ifcopenshell's ``unit.assign_unit`` collects them through a ``set``, so the four SI
    units come out in hash order and two runs disagree. The order carries no meaning.
    """
    try:
        assignments = f.by_type("IfcUnitAssignment")
    except RuntimeError:
        return
    for assignment in assignments:
        units = assignment.Units or ()
        assignment.Units = tuple(sorted(units, key=lambda u: (u.is_a(), str(
            getattr(u, "UnitType", "")), str(getattr(u, "Name", "")))))


#: Spatial containers this engine creates one of, with no model element behind them to take
#: a uid from. Their identity is their role in the file, which is what is hashed.
_SINGLETON_SPATIAL = (
    "IfcSite", "IfcBuilding", "IfcBuildingStorey",
    # Systems are named containers this engine mints one of per trade — "Stormwater",
    # "Sanitary" — with no model element behind them either. Same treatment, and they must
    # be pinned here because the IfcRelAssignsToGroup that fills them hashes their GUID.
    "IfcDistributionSystem", "IfcSystem", "IfcZone", "IfcGroup",
)


def pin_spatial_guids(f: Any, project_uuid: uuid.UUID) -> None:
    """Pin the site and building GUIDs, which no model uid backs.

    Must run BEFORE :func:`pin_relationship_guids`: the aggregates that hang the building
    off the site hash their ends' GUIDs, so an unpinned end makes a pinned relationship
    unstable anyway.
    """
    import ifcopenshell.guid

    namespace = uuid.uuid5(project_uuid, "typehaus/ifc/spatial")
    for kind in _SINGLETON_SPATIAL:
        try:
            entities = f.by_type(kind)
        except RuntimeError:
            continue
        # Sorted by name so the key is a property of the building and not of emit order.
        for ordinal, entity in enumerate(sorted(entities, key=lambda e: (
                str(getattr(e, "Name", None) or ""),
                str(getattr(e, "PredefinedType", None) or "")))):
            key = (f"{kind}|{getattr(entity, 'Name', None) or ''}"
                   f"|{getattr(entity, 'PredefinedType', None) or ''}|{ordinal}")
            entity.GlobalId = ifcopenshell.guid.compress(uuid.uuid5(namespace, key).hex)


#: Relationships whose member ORDER carries no meaning, so it may be sorted. ``IfcRelNests``
#: is deliberately absent: IFC defines its RelatedObjects as an ordered list, and sorting it
#: would change what the file says.
_UNORDERED_MEMBERS = {
    "IfcRelAggregates": ("RelatedObjects",),
    "IfcRelAssignsToGroup": ("RelatedObjects",),
    "IfcRelAssignsToProduct": ("RelatedObjects",),
    "IfcRelAssociatesMaterial": ("RelatedObjects",),
    "IfcRelContainedInSpatialStructure": ("RelatedElements",),
    "IfcRelDefinesByProperties": ("RelatedObjects",),
    "IfcRelDefinesByType": ("RelatedObjects",),
    "IfcRelServicesBuildings": ("RelatedBuildings",),
}


def pin_relation_member_order(f: Any) -> None:
    """Sort the member lists of relationships whose order is not meaningful.

    ifcopenshell collects them through sets in several api calls, so two runs list the same
    nineteen elements in two different orders. Sorted by GlobalId, which every product in
    the file now has deterministically.
    """
    for kind, attributes in _UNORDERED_MEMBERS.items():
        try:
            entities = f.by_type(kind)
        except RuntimeError:
            continue
        for entity in entities:
            for attribute in attributes:
                members = getattr(entity, attribute, None)
                if not members:
                    continue
                setattr(entity, attribute,
                        tuple(sorted(members, key=lambda e: str(
                            getattr(e, "GlobalId", "") or e.id()))))

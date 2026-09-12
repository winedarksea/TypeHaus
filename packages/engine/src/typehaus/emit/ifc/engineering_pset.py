"""Every engineered item's record, riding on the elements it grades.

An IFC a reviewing engineer can *check against* rather than only look at. A PE opening
``model.ifc`` in Bonsai and clicking the balcony's centre column should see, on that
column, that it is item ``deck_post/PT-SG-BF2``, that bearing governs at 0.45, what clause
the capacity came from, and the fingerprint a seal over it would be pinned to. Without
that, the geometry and the calculation package are two documents a person has to correlate
by tag, forty times.

The property sets are **derived and never authored**: everything here comes off an
``EngineeringRecord``, and the record comes off the calculation. Nothing in this module
decides anything about the building.

``Pset_TH_Engineering_<kind>`` follows the IFC convention for a vendor-defined property set
— a name outside the ``Pset_`` reserved space would be dropped by strict importers, and a
prefix nobody else uses keeps it out of the way of the standard ones. Alongside it, the
standard ``Pset_BeamCommon`` / ``Pset_ColumnCommon`` carry Span and LoadBearing where the
record knows them, because those are the fields a structural importer actually reads.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.ifc import lowlevel as ll

#: One element may be named by more than one record — a wall in a retaining SYSTEM is also
#: a retaining WALL. Both attach; they are different property sets and different questions.
_PREFIX = "Pset_TH_Engineering_"


def attach_engineering_psets(f: Any, model: Any, element_entities: dict[str, Any],
                             engineering: Any, register: Any = None) -> int:
    """Attach one property set per (element, record). Returns how many were written."""
    written = 0
    # One element may be named by several records — a column is a `deck_post` and its pad
    # is a `spread_footing` on the same tag. Each gets its own Pset_TH_Engineering_<kind>,
    # but the STANDARD pset has one Reference field, so the first record in id order wins
    # and the later one does not silently overwrite it.
    done: set[str] = set()
    for item_id in sorted(engineering):
        record = engineering[item_id]
        properties = _properties(record, register)
        for tag in record.element_tags:
            element = element_entities.get(tag)
            if element is None:
                # The element has no IFC representation — an Equipment placeable draws no
                # solid, a deferred roof may resolve no member. Silently skipping is right:
                # this is an annotation pass, not a completeness check, and `haus calcs`
                # is where an item's absence would be a finding.
                continue
            ll.ensure_pset(f, element, f"{_PREFIX}{record.kind}", properties)
            written += 1
        _attach_common(f, record, element_entities, done)
    return written


def _properties(record: Any, register: Any) -> dict[str, Any]:
    """The record as flat IFC properties — strings and reals, no nesting.

    IFC property sets are flat by nature and a reviewer reads them in a table, so the
    governing limit state is spread into four fields rather than carried as a name a person
    then has to look up in the calc package.
    """
    from typehaus.engineering.fingerprint import fingerprint

    properties: dict[str, Any] = {
        "ItemId": record.item_id,
        "Kind": record.kind,
        "Status": record.status.value,
        "Summary": record.summary or "",
        "Basis": record.basis or "",
        "BasisVersion": record.basis_version or "",
    }
    governing = record.governing
    if governing is not None:
        properties.update({
            "GoverningLimitState": governing.name,
            "Demand": float(governing.demand),
            "Capacity": float(governing.capacity),
            "DemandCapacityRatio": float(governing.ratio),
            "Unit": governing.unit,
            "Citation": governing.citation,
        })
    if record.missing:
        properties["OpenInputs"] = "; ".join(record.missing)
    if record.oracle:
        properties["OracleNotes"] = ", ".join(
            oracle.note for oracle in record.oracle if getattr(oracle, "note", None))

    # The fingerprint, and whether anybody's seal still matches it. A record with no inputs
    # (a deferred kind) has nothing to hash, and saying so beats printing a digest of an
    # empty set that a stamp could then be pinned against.
    if record.inputs:
        properties["Fingerprint"] = fingerprint(record)
    else:
        properties["Fingerprint"] = "none — no inputs to fingerprint"
    properties["Seal"] = _seal(record, register)
    return properties


def _seal(record: Any, register: Any) -> str:
    if register is None:
        return "unsealed"
    try:
        state, signoff = register.freshness(record)
    except (AttributeError, TypeError):
        return "unsealed"
    label = getattr(state, "value", str(state))
    return f"{label} ({signoff.id})" if signoff is not None else label


#: Which standard property set a record's elements take, by the IFC class they were emitted
#: as. Only the two the schema defines the Span/LoadBearing fields on.
_COMMON = {
    "IfcBeam": ("Pset_BeamCommon", True),
    "IfcColumn": ("Pset_ColumnCommon", True),
    "IfcMember": ("Pset_MemberCommon", True),
}


def _attach_common(f: Any, record: Any, element_entities: dict[str, Any],
                   done: set[str]) -> None:
    """``Pset_BeamCommon``/``Pset_ColumnCommon`` — the fields a structural importer reads.

    Span comes off the record's own inputs where the calculation consumed one, because that
    is the span the capacity was computed for. Deriving it from the geometry instead would
    let the two disagree, which is exactly the disagreement this pset exists to rule out.
    """
    spans = {q.name: q.value for q in record.inputs}
    span = spans.get("clear_span") or spans.get("span")
    for tag in record.element_tags:
        element = element_entities.get(tag)
        if element is None or tag in done:
            continue
        entry = _COMMON.get(element.is_a())
        if entry is None:
            continue
        name, load_bearing = entry
        properties: dict[str, Any] = {"LoadBearing": load_bearing,
                                      "Reference": record.item_id}
        if span:
            properties["Span"] = float(span) * 0.3048
        ll.ensure_pset(f, element, name, properties)
        done.add(tag)

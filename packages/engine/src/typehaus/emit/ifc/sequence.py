"""IFC cost and schedule entities — ``IfcWorkSchedule``/``IfcTask`` and
``IfcCostSchedule``/``IfcCostItem`` for the derived work packages.

Emitted **last**, and that is the contract the emitter's docstring already states: spatial
structure, then the elements it contains, then the systems that group them — and cost and
task entities *reference elements*, so they cannot be written before the elements exist.

Gated behind ``emit_ifc(..., sequence=True)`` (``haus build --lod schedule``) rather than
always on: the permit IFC goes to a plan reviewer who wants geometry and nothing else, and
a work schedule in that file is noise a reviewer has to page past.

Built on ``ifcopenshell.api.sequence.*`` / ``.cost.*`` rather than hand-rolled entities.
0.8 ships both, and the API gets the inverse relationships right — an ``IfcTask`` needs its
``IfcTaskTime``, its nesting under the schedule's root task, and its ``IfcRelAssignsToProcess``
wired consistently, and a hand-built one that misses any of them opens in Navisworks as an
empty schedule rather than as an error.

Every id here is a ``derive_guid(project_uuid, "task/{trade}/{storey}")`` — stable across
rebuilds and retagging — so re-exporting into a receiving tool updates the same task rather
than creating a second one.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.trades import CONSTRUCTION_SEQUENCE

#: One relationship type per predecessor edge. Finish-to-start is the only honest one here:
#: the sequence table says which trade must be substantially complete before another starts,
#: and nothing in the model supports a lead, a lag or an overlap.
_FINISH_TO_START = "FINISH_START"


def emit_sequence(f: Any, project: Any, model: Any, work_items: list[Any],
                  element_entities: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write the work plan, schedule, tasks and cost items for ``work_items``.

    Tags the emitter never produced an entity for are skipped rather than faked.
    ``element_entities`` may seed the tag -> entity index; anything it lacks is recovered
    from the file itself (see :func:`_tag_index`).

    Returns ``{slug: IfcTask}`` so a caller can extend the schedule.
    """
    import ifcopenshell.api

    if not work_items:
        return {}
    entities = _tag_index(f, element_entities)

    plan = ifcopenshell.api.run("sequence.add_work_plan", f, name="Construction")
    schedule = ifcopenshell.api.run("sequence.add_work_schedule", f,
                                    name="Construction sequence", work_plan=plan)
    order = {trade: index for index, trade in enumerate(CONSTRUCTION_SEQUENCE)}

    tasks: dict[str, Any] = {}
    for item in work_items:
        task = ifcopenshell.api.run("sequence.add_task", f, work_schedule=schedule)
        ifcopenshell.api.run("sequence.edit_task", f, task=task, attributes={
            "Name": item.title,
            "Description": item.description,
            "Identification": item.slug,
            # The construction-order rank, not a duration. IfcTask has no field for "this
            # comes fourth" other than the sequence relationships below, and a reader
            # sorting by name would get alphabetical order, which is meaningless here.
            "Priority": order.get(item.trade, len(order)),
            "IsMilestone": False,
        })
        # Deliberately NO IfcTaskTime: durations, crew sizes and dates are not derivable
        # from a geometry model, and a fabricated duration is worse than an absent one —
        # it is the number the whole schedule would then be built on.
        ll.ensure_pset(f, task, "Pset_TypeHausWorkItem", {
            "Slug": item.slug,
            "Trade": item.trade,
            "Storey": item.storey,
            "CostCode": item.cost_code,
            "TakeoffRows": ", ".join(f"{section}:{key}" for section, key in item.rows),
        })
        tasks[item.slug] = task

        products = [entities[tag] for tag in item.element_tags if tag in entities]
        if products:
            _assign_products(f, task, products)

    for item in work_items:
        for predecessor in item.depends_on:
            if predecessor in tasks:
                ifcopenshell.api.run("sequence.assign_sequence", f,
                                     relating_process=tasks[predecessor],
                                     related_process=tasks[item.slug],
                                     sequence_type=_FINISH_TO_START)

    _emit_cost_schedule(f, work_items)
    return tasks


def _tag_index(f: Any, seed: dict[str, Any] | None) -> dict[str, Any]:
    """Element tag -> IFC entity, recovered from the file that was just written.

    Every emitter already stamps ``Pset_TH_Source`` with the element's ``uid`` and ``tag``,
    so the file carries the index; reading it back is one pass over the property-set
    relationships. The alternative — threading a dict through eleven emitter signatures,
    most of which currently return ``None`` — would touch every discipline emitter to add a
    return value none of them otherwise needs.
    """
    from typehaus._meta import PSET_SOURCE

    index: dict[str, Any] = dict(seed or {})
    for rel in f.by_type("IfcRelDefinesByProperties"):
        pset = rel.RelatingPropertyDefinition
        if not (pset.is_a("IfcPropertySet") and pset.Name == PSET_SOURCE):
            continue
        tag = next((prop.NominalValue.wrappedValue
                    for prop in (pset.HasProperties or []) if prop.Name == "tag"), None)
        if tag is None:
            continue
        for obj in rel.RelatedObjects:
            index.setdefault(str(tag), obj)
    return index


def _assign_products(f: Any, task: Any, products: list[Any]) -> None:
    """``IfcRelAssignsToProcess`` task -> the elements it covers.

    ``IfcRelAssignsToProcess`` rather than ``IfcRelAssignsToProduct``: both express the
    link, but the product form takes one product per relationship (which is why
    ``sequence.assign_product`` builds one each call), and a task covering 300 elements
    would then write 300 relationship entities where one with 300 members says the same
    thing. Same direction, same reading in a schedule browser, 1/300th of the file.
    """
    f.create_entity(
        "IfcRelAssignsToProcess",
        GlobalId=ll.new_guid(),
        RelatedObjects=products,
        RelatingProcess=task,
    )


def _emit_cost_schedule(f: Any, work_items: list[Any]) -> None:
    """One ``IfcCostSchedule`` with an ``IfcCostItem`` per work package.

    The cost carried is the estimate *range*: ``IfcCostValue`` takes an
    ``IfcMonetaryMeasure``, so the low and high ends are two values on the same item rather
    than one invented midpoint. A package with no priced rows gets an item with no value —
    present, and honestly empty.
    """
    import ifcopenshell.api

    schedule = ifcopenshell.api.run("cost.add_cost_schedule", f, name="Estimate",
                                    predefined_type="ESTIMATE")
    for item in work_items:
        cost_item = ifcopenshell.api.run("cost.add_cost_item", f, cost_schedule=schedule)
        ifcopenshell.api.run("cost.edit_cost_item", f, cost_item=cost_item, attributes={
            "Name": item.title,
            "Identification": item.cost_code or item.slug,
        })
        if item.estimate.low or item.estimate.high:
            for end in (item.estimate.low, item.estimate.high):
                value = ifcopenshell.api.run("cost.add_cost_value", f, parent=cost_item)
                ifcopenshell.api.run("cost.edit_cost_value", f, cost_value=value,
                                     attributes={"AppliedValue": round(end, 2)})

"""Work packages — the model's quantities, grouped the way work is actually bought.

There is no phase, stage, sequence or predecessor concept anywhere in the model, and
``emit/trades.TRADES`` is a 3D-viewer visibility axis with no ordering. This module is the
bridge: it groups the bill of materials at **(trade × storey)** granularity, attaches each
group's cost roll-up straight from ``estimate_costs``, and orders the groups with the
authored :data:`~typehaus.emit.trades.CONSTRUCTION_SEQUENCE`.

Three properties are load-bearing.

**Stable ids.** Each item's id is ``derive_guid(project_uuid, "task/{trade}/{storey}")``.
``model/ids.py`` guarantees a GlobalId stable across rebuilds and retagging, so re-exporting
into Trello, Asana, Buildertrend or an IFC schedule updates the same task instead of
creating a second one. The slug is kept human-readable for the same reason: it is the half a
receiving tool can key on when it has no GUID field.

**No money invented, none lost.** A BOM row lands on a storey only when *every* element it
covers is on that storey. Rows whose tags span storeys, and rows that carry no tags at all
(``framing_by_size``, ``envelope_layers``, ``sheet_goods`` — the takeoff rolls those up
building-wide), go to that trade's ``building`` item. Splitting them pro-rata would be an
allocation nobody authored, and the per-storey numbers would then be confidently wrong. The
item estimates therefore sum to exactly the estimate total.

**Nothing derived that the model cannot know.** No durations, no crew sizes, no calendar
dates. A fabricated duration is worse than an absent one: it is the number a schedule is
built on, and there is nothing in a geometry model that implies it.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from typehaus.cli.prices import ZERO, PriceRange
from typehaus.emit.trades import CONSTRUCTION_SEQUENCE, TRADE_PREDECESSORS
from typehaus.takeoff.cost_codes import cost_code

#: The storey slot for work a takeoff bills building-wide. Named rather than blank so a
#: spreadsheet row reads as a deliberate scope, not as a missing field.
BUILDING = "building"


@dataclass(frozen=True)
class WorkItem:
    """One (trade × storey) package of work, with everything a PM tool needs to file it."""

    id: str
    slug: str
    trade: str
    storey: str
    cost_code: str
    #: ``(section, key)`` BOM rows this package covers.
    rows: tuple[tuple[str, str], ...] = ()
    element_tags: tuple[str, ...] = ()
    estimate: PriceRange = ZERO
    actual_cost: float | None = None
    depends_on: tuple[str, ...] = ()
    status: str = "todo"

    @property
    def title(self) -> str:
        where = "whole building" if self.storey == BUILDING else self.storey
        return f"{self.trade.title()} — {where}"

    @property
    def description(self) -> str:
        if not self.rows:
            return "No priced takeoff rows fall to this package."
        listed = ", ".join(f"{section}:{key}" for section, key in self.rows[:8])
        more = f" (+{len(self.rows) - 8} more)" if len(self.rows) > 8 else ""
        return f"{len(self.rows)} takeoff row(s): {listed}{more}"

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "slug": self.slug, "title": self.title,
                "description": self.description, "status": self.status,
                "trade": self.trade, "storey": self.storey, "cost_code": self.cost_code,
                "estimate": self.estimate.as_dict(), "estimate_fmt": self.estimate.fmt(),
                "actual_cost": self.actual_cost,
                "depends_on": list(self.depends_on),
                "element_tags": list(self.element_tags),
                "rows": [{"section": s, "key": k} for s, k in self.rows]}


@dataclass
class _Bucket:
    rows: list[tuple[str, str]] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    estimate: PriceRange = ZERO
    actual: float = 0.0
    has_actual: bool = False


def _storey_of_tag(model: Any) -> dict[str, str]:
    """tag -> storey, for every authored element. Built once per export."""
    index: dict[str, str] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            index[element.tag] = storey.tag
    return index


def _row_storey(tags: Any, storey_of: Mapping[str, str]) -> str:
    """The one storey a BOM row belongs to, or :data:`BUILDING` when it is not one storey.

    Untagged rows and rows spanning storeys both land building-wide — see the module
    docstring on why they are not split pro-rata.
    """
    if not tags:
        return BUILDING
    storeys = {storey_of.get(str(tag)) for tag in tags} - {None}
    return str(storeys.pop()) if len(storeys) == 1 else BUILDING


def build_work_items(model: Any, bom: dict[str, Any], estimate: dict[str, Any] | None = None,
                     costs_state: Any = None) -> list[WorkItem]:
    """Group a priced BOM into ordered work packages.

    ``estimate`` is a :func:`typehaus.cli.prices.estimate_costs` payload; without it the
    packages still carry their rows and element tags, just no money.
    """
    from typehaus.model.ids import derive_guid

    storey_of = _storey_of_tag(model)
    tags_by_row = _tags_by_row(bom)
    entries = getattr(costs_state, "entries", {}) or {}

    buckets: dict[tuple[str, str], _Bucket] = {}
    for section, key, cost in _priced_or_bare_rows(bom, estimate):
        trade = cost_code(section, key).trade
        tags = tags_by_row.get((section, key), ())
        slot = (trade, _row_storey(tags, storey_of))
        bucket = buckets.setdefault(slot, _Bucket())
        if (section, key) not in bucket.rows:
            bucket.rows.append((section, key))
        bucket.tags.update(str(tag) for tag in tags)
        bucket.estimate = bucket.estimate.plus(cost)
        actual = getattr(entries.get(section, {}).get(key), "actual_cost", None)
        if actual is not None:
            bucket.actual += float(actual)
            bucket.has_actual = True

    project_uuid = model.plan.project.project_uuid
    order = {trade: i for i, trade in enumerate(CONSTRUCTION_SEQUENCE)}
    storey_order = {storey.tag: i for i, storey in enumerate(model.plan.storeys)}
    items: list[WorkItem] = []
    for trade, storey in sorted(
            buckets, key=lambda slot: (order.get(slot[0], len(order)),
                                       storey_order.get(slot[1], len(storey_order)))):
        bucket = buckets[(trade, storey)]
        slug = f"task/{trade}/{storey}"
        rows = tuple(sorted(bucket.rows))
        items.append(WorkItem(
            id=derive_guid(project_uuid, slug),
            slug=slug,
            trade=trade,
            storey=storey,
            # The trade's own account, from the same table the CSV export uses. A package
            # spanning several sections takes the first row's code rather than none.
            cost_code=(cost_code(rows[0][0], rows[0][1]).nahb if rows else ""),
            rows=rows,
            element_tags=tuple(sorted(bucket.tags)),
            estimate=bucket.estimate,
            actual_cost=round(bucket.actual, 2) if bucket.has_actual else None,
            depends_on=(),
        ))

    # Predecessors are resolved against the packages that actually exist: a house with no
    # stairs must not leave a dangling dependency on a stair package nobody will ever close.
    by_trade: dict[str, list[str]] = {}
    for item in items:
        by_trade.setdefault(item.trade, []).append(item.slug)
    return [
        WorkItem(**{**item.__dict__,
                    "depends_on": tuple(sorted(
                        slug for predecessor in TRADE_PREDECESSORS.get(item.trade, ())
                        for slug in by_trade.get(predecessor, ())))})
        for item in items
    ]


def _priced_or_bare_rows(
    bom: dict[str, Any], estimate: dict[str, Any] | None
) -> Iterator[tuple[str, str, PriceRange]]:
    """``(section, key, cost)`` for every takeoff row — priced when an estimate exists.

    Without an estimate the work breakdown is still real: which trades touch which storeys,
    covering which takeoff rows and which elements, is a property of the *model*, not of
    anybody's price list. Decision #28 makes dollars opt-in, and a house that opts out
    should lose the money, not the schedule.
    """
    from typehaus.cli.prices import ESTIMATE_PLANS

    if estimate is not None:
        for section, body in estimate.get("sections", {}).items():
            for row in body.get("rows", []):
                yield section, row["key"], PriceRange(row["cost"]["low"], row["cost"]["high"])
        return
    for section, bom_key, key_field, _quantity_field, _unit in ESTIMATE_PLANS:
        seen = set()
        for row in bom.get(bom_key, []) or []:
            key = str(row.get(key_field))
            if key not in seen:
                seen.add(key)
                yield section, key, ZERO


def _tags_by_row(bom: dict[str, Any]) -> dict[tuple[str, str], tuple[str, ...]]:
    """``(section, key)`` -> the element tags its BOM rows name, where the takeoff kept them.

    Several takeoff families carry ``tags``; the building-wide roll-ups (framing by profile,
    envelope layers by material, sheet goods by scope) deliberately do not, because the row
    *is* the whole-building total. Those land in the ``building`` package.
    """
    from typehaus.cli.prices import ESTIMATE_PLANS

    out: dict[tuple[str, str], list[str]] = {}
    for section, bom_key, key_field, _quantity_field, _unit in ESTIMATE_PLANS:
        for row in bom.get(bom_key, []) or []:
            tags = row.get("tags")
            if not tags:
                continue
            out.setdefault((section, str(row.get(key_field))), []).extend(
                str(tag) for tag in tags)
    return {slot: tuple(sorted(set(tags))) for slot, tags in out.items()}

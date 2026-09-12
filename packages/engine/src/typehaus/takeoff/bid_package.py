"""A bid package: one trade's unpriced view of the bill of materials (decision #71).

Built from the same walk the estimate reads (:mod:`typehaus.takeoff.bom_walk`) and filed by
the same rule (:func:`typehaus.takeoff.cost_codes.cost_code`), so every BOM row lands in
exactly one package and a sub's count reconciles to the estimate line by line. Dollars are
opt-in (decision #28): a package carries a price only when the caller passes an estimate
and asks for it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from typehaus.emit.trades import TRADE_LABELS, sequence_rank
from typehaus.schedule.propose import family_rank
from typehaus.takeoff.bid_recipes import Recipe, recipe_for, shape_for
from typehaus.takeoff.bom_walk import BomRow, walk_bom
from typehaus.takeoff.cost_codes import cost_code
from typehaus.takeoff.labels import EMPTY_LABELS, LabelIndex, describe

BUILDING = "building"


@dataclass(frozen=True)
class BidLine:
    section: str
    key: str
    description: str
    quantity: float
    unit: str
    detail: str
    storeys: tuple[str, ...]
    element_tags: tuple[str, ...]
    unit_price: tuple[float, float] | None = None
    total: tuple[float, float] | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "section": self.section, "key": self.key, "description": self.description,
            "quantity": self.quantity, "unit": self.unit, "detail": self.detail,
            "storeys": list(self.storeys), "element_tags": list(self.element_tags)}
        if self.unit_price is not None and self.total is not None:
            out["unit_price"] = {"low": self.unit_price[0], "high": self.unit_price[1]}
            out["total"] = {"low": self.total[0], "high": self.total[1]}
        return out


@dataclass(frozen=True)
class BidGroup:
    section: str
    heading: str
    unit: str
    lines: tuple[BidLine, ...]


@dataclass(frozen=True)
class BidPackage:
    trade: str
    label: str
    recipe: Recipe
    groups: tuple[BidGroup, ...]
    #: Owner allowances filed under this trade — scope the model does not resolve, listed
    #: without dollars so the sub knows it is carried elsewhere.
    allowances: tuple[BidLine, ...]
    sheets: tuple[str, ...]
    priced: bool

    @property
    def lines(self) -> tuple[BidLine, ...]:
        return tuple(line for group in self.groups for line in group.lines)

    @property
    def element_tags(self) -> tuple[str, ...]:
        return tuple(sorted({tag for line in self.lines for tag in line.element_tags}))

    @property
    def storeys(self) -> tuple[str, ...]:
        return tuple(sorted({s for line in self.lines for s in line.storeys}))

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "trade": self.trade, "label": self.label, "title": self.recipe.title,
            "intro": self.recipe.intro, "sheets": list(self.sheets),
            "priced": self.priced,
            "groups": [{"section": g.section, "heading": g.heading, "unit": g.unit,
                        "lines": [line.as_dict() for line in g.lines]} for g in self.groups],
            "allowances": [line.as_dict() for line in self.allowances],
            "element_tags": list(self.element_tags), "storeys": list(self.storeys)}
        if self.priced:
            out["total"] = {"low": round(sum(line.total[0] for line in self.lines
                                              if line.total), 2),
                            "high": round(sum(line.total[1] for line in self.lines
                                               if line.total), 2)}
        return out


def _storeys(tags: tuple[str, ...], storey_of: Mapping[str, str]) -> tuple[str, ...]:
    found = sorted({storey_of[tag] for tag in tags if tag in storey_of})
    return tuple(found) if found else (BUILDING,)


def _price_index(estimate: Mapping[str, Any] | None
                 ) -> dict[tuple[str, str], Mapping[str, Any]]:
    index: dict[tuple[str, str], Mapping[str, Any]] = {}
    for section, body in (estimate or {}).get("sections", {}).items():
        for row in body.get("rows", []):
            index.setdefault((section, str(row["key"])), row)
    return index


def _line(item: BomRow, storey_of: Mapping[str, str], labels: LabelIndex,
          prices: Mapping[tuple[str, str], Mapping[str, Any]], priced: bool) -> BidLine:
    shape = shape_for(item.section)
    detail = shape.detail(item.row) if shape.detail else ""
    unit_price = total = None
    if priced:
        row = prices.get((item.section, item.qualified_key)) or prices.get((item.section, item.key))
        if row is not None:
            unit_price = (float(row["unit_price"]["low"]), float(row["unit_price"]["high"]))
            total = (float(row["cost"]["low"]), float(row["cost"]["high"]))
    return BidLine(
        section=item.section, key=item.qualified_key,
        description=describe(item.section, item.qualified_key, item.row, labels),
        quantity=round(item.quantity, 2), unit=shape.unit or item.unit, detail=detail,
        storeys=_storeys(item.tags, storey_of), element_tags=tuple(sorted(item.tags)),
        unit_price=unit_price, total=total)


def _allowance_lines(trade: str, estimate: Mapping[str, Any] | None, priced: bool
                     ) -> tuple[BidLine, ...]:
    rows = (estimate or {}).get("sections", {}).get("allowances", {}).get("rows", [])
    out = []
    for row in rows:
        if row.get("trade") != trade:
            continue
        out.append(BidLine(
            section="allowances", key=str(row["key"]), description=str(row["description"]),
            quantity=float(row.get("quantity") or 0.0), unit=str(row.get("unit") or "ls"),
            detail="", storeys=(BUILDING,), element_tags=(),
            unit_price=((float(row["unit_price"]["low"]), float(row["unit_price"]["high"]))
                        if priced else None),
            total=((float(row["cost"]["low"]), float(row["cost"]["high"])) if priced else None)))
    return tuple(sorted(out, key=lambda line: line.key))


def build_bid_packages(model: Any, bom: Mapping[str, Any], *,
                       estimate: Mapping[str, Any] | None = None, priced: bool = False,
                       labels: LabelIndex | None = None,
                       sheet_numbers: tuple[str, ...] | None = None,
                       ) -> dict[str, BidPackage]:
    """``trade -> package`` for every trade a BOM row files under, in construction order.

    ``priced`` without an ``estimate`` is refused: a price with nothing behind it is exactly
    the number this format exists not to invent.
    """
    if priced and estimate is None:
        raise ValueError("a priced package needs an estimate; without prices.toml there is none")
    from typehaus.takeoff.tasks import _storey_of_tag

    labels = labels or EMPTY_LABELS
    storey_of = _storey_of_tag(model)
    prices = _price_index(estimate)
    by_trade: dict[str, dict[str, list[BidLine]]] = {}
    for item in walk_bom(bom):
        trade = cost_code(item.section, item.key, material=item.material, row=item.row).trade
        line = _line(item, storey_of, labels, prices, priced)
        by_trade.setdefault(trade, {}).setdefault(item.section, []).append(line)
    if estimate is not None:
        for row in estimate.get("sections", {}).get("allowances", {}).get("rows", []):
            by_trade.setdefault(str(row.get("trade") or "general"), {})

    from typehaus.cli.prices import ESTIMATE_PLANS

    estimate_order = {plan[0]: i for i, plan in enumerate(ESTIMATE_PLANS)}
    packages: dict[str, BidPackage] = {}
    for trade in sorted(by_trade, key=sequence_rank):
        recipe = recipe_for(trade)
        lead = {section: i for i, section in enumerate(recipe.section_order)}
        sections = sorted(by_trade[trade], key=lambda s: (lead.get(s, len(lead)),
                                                         estimate_order.get(s, 999), s))
        groups = []
        for section in sections:
            shape = shape_for(section)
            lines = sorted(by_trade[trade][section],
                           key=lambda line: (family_rank(trade, f"{section}:{line.key}"),
                                             line.key))
            groups.append(BidGroup(section=section, heading=shape.heading,
                                   unit=shape.unit or (lines[0].unit if lines else ""),
                                   lines=tuple(lines)))
        sheets = tuple(s for s in recipe.sheets
                       if sheet_numbers is None or s in sheet_numbers)
        packages[trade] = BidPackage(
            trade=trade, label=TRADE_LABELS.get(trade, trade), recipe=recipe,
            groups=tuple(groups), allowances=_allowance_lines(trade, estimate, priced),
            sheets=sheets, priced=priced)
    return packages

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

from typehaus.emit.trade_rules import material_trade
from typehaus.emit.trades import (
    DRAINAGE_CATEGORIES,
    PIPE_ACCESSORY_CATEGORIES,
    ROUTED_RUN_CATEGORIES,
    TRADE_LABELS,
    sequence_rank,
)
from typehaus.resolve.solid_categories import categories_where, is_pour_category
from typehaus.takeoff.bid_recipes import Recipe, recipe_for, shape_for
from typehaus.takeoff.bom_walk import BomRow, walk_bom
from typehaus.takeoff.cost_codes import cost_code
from typehaus.takeoff.labels import EMPTY_LABELS, LabelIndex, describe
from typehaus.takeoff.solid_sections import SOLID_SECTIONS

BUILDING = "building"

#: ``structural_solids`` categories whose PRODUCT is billed in a dedicated section (pipe by
#: the foot, hardware by the part, trim by the foot…). The solids table still carries their
#: volume — that is the takeoff's geometry view — but a package that listed "0.01 cy of
#: backflow preventer" beside the valve itself read as a cast pour to every reviewer
#: (audit:2026-09-12, 41 rows across nine trades). Dropped from packages, never from the BOM.
MIRRORED_SOLID_CATEGORIES = (ROUTED_RUN_CATEGORIES | PIPE_ACCESSORY_CATEGORIES
                             | DRAINAGE_CATEGORIES | categories_where(billed_elsewhere=True))

#: Aggregates a sub buys by the yard, even where the takeoff carries them as a layer area.
_AGGREGATE_TRADES = frozenset({"earth", "landscaping"})
_BF_PER_CUFT = 12.0
_CY_PER_CUFT = 1.0 / 27.0


def _mirrored(item: BomRow) -> bool:
    if item.section in SOLID_SECTIONS:
        return item.key in MIRRORED_SOLID_CATEGORIES
    # A room with no finish authored is a gap in the model, not a line to quote.
    return item.section == "floor_finishes" and item.key in ("None", "")


def _shaped_quantity(item: BomRow, trade: str, default_unit: str) -> tuple[float, str]:
    """``(quantity, unit)`` in the unit this item is bought in (audit:2026-09-12).

    The estimate prices a solid by the yard whatever it is; a sub does not. A wood beam is
    board feet, an aluminium stand a piece, a foam wing or a plywood cap an area; brick and
    block are wall face; aggregate under a green is a yard, not the net area of its layer.
    """
    row = item.row
    key = item.key
    material = str(item.material or row.get("material") or "").lower()
    if item.section in SOLID_SECTIONS:
        if material == "concrete" or (not material and (
                is_pour_category(key) or key in ("thermal_break", "dowel"))):
            if key == "dowel":
                return float(row.get("count") or 0), "ea"
            if key == "thermal_break":
                return float(row.get("count") or 0), "ea"
            return item.quantity, "cy"
        if key in ("beam", "column"):
            if "alum" in material or "steel" in material:
                return float(row.get("count") or 0), "ea"
            return round(float(row.get("volume_cuft") or 0) * _BF_PER_CUFT, 1), "bf"
        return float(row.get("plan_area_sqft") or 0), "SF"
    if item.section == "wall_structure":
        mat_trade = material_trade(material)
        if mat_trade in ("masonry", "landscaping", "siding"):
            return float(row.get("net_area_sqft") or 0), "SF"
        if mat_trade == "framing":
            return round(float(row.get("volume_cuft") or 0) * _BF_PER_CUFT, 1), "bf"
        return item.quantity, "cy"
    if item.section == "envelope_layers" and trade in _AGGREGATE_TRADES:
        mat = str(row.get("material") or "")
        if not (mat.endswith("sod") or mat.startswith("geotextile")):
            depth_ft = float(row.get("thickness_in") or 0) / 12.0
            return round(float(row.get("net_area_sqft") or 0) * depth_ft * _CY_PER_CUFT, 2), "cy"
    if item.section == "drainage" and key in ("drywell", "french_drain"):
        return float(row.get("aggregate_cubic_yards") or 0), "cy"
    if item.section == "solar_modules":
        return float(row.get("panels") or 0), "ea"
    if item.section == "framing" and "truss" in str(row.get("profile") or ""):
        return float(row.get("pieces") or 0), "ea"
    if item.section == "sheet_goods":
        mat = str(row.get("material") or "")
        if mat.endswith("-deck") or "membrane" in mat:
            return float(row.get("net_area_sqft") or 0), "SF"
    return item.quantity, default_unit


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


def _line(item: BomRow, trade: str, storey_of: Mapping[str, str], labels: LabelIndex,
          prices: Mapping[tuple[str, str], Mapping[str, Any]], priced: bool) -> BidLine:
    shape = shape_for(item.section)
    detail = shape.detail(item.row) if shape.detail else ""
    spelled = shape.unit_of(item.row) if shape.unit_of else (shape.unit or item.unit)
    quantity, unit = _shaped_quantity(item, trade, spelled)
    if unit != spelled and item.quantity:
        detail = f"{detail}; {item.quantity} {item.unit} in the takeoff".strip("; ")
    unit_price = total = None
    if priced:
        row = prices.get((item.section, item.qualified_key)) or prices.get((item.section, item.key))
        if row is not None:
            unit_price = (float(row["unit_price"]["low"]), float(row["unit_price"]["high"]))
            total = (float(row["cost"]["low"]), float(row["cost"]["high"]))
    return BidLine(
        section=item.section, key=item.qualified_key,
        description=describe(item.section, item.qualified_key, item.row, labels),
        quantity=round(quantity, 2), unit=unit, detail=detail,
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


def is_mirrored(item: BomRow) -> bool:
    """Whether a walked row is left out of every package (see MIRRORED_SOLID_CATEGORIES)."""
    return _mirrored(item)


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
        if _mirrored(item):
            continue
        trade = cost_code(item.section, item.key, material=item.material, row=item.row).trade
        line = _line(item, trade, storey_of, labels, prices, priced)
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
            # By key: the schedule's family order lives in the schedule leaf, which
            # nothing upstream may import (tests/test_package_leaves.py); the recipe's
            # section order is the ordering a package needs.
            lines = sorted(by_trade[trade][section], key=lambda line: line.key)
            units = {line.unit for line in lines}
            groups.append(BidGroup(section=section, heading=shape.heading,
                                   unit=units.pop() if len(units) == 1 else "mixed",
                                   lines=tuple(lines)))
        sheets = tuple(s for s in recipe.sheets
                       if sheet_numbers is None or s in sheet_numbers)
        packages[trade] = BidPackage(
            trade=trade, label=TRADE_LABELS.get(trade, trade), recipe=recipe,
            groups=tuple(groups), allowances=_allowance_lines(trade, estimate, priced),
            sheets=sheets, priced=priced)
    return packages

"""Price each declared courtyard variant from its own resolved model and ``prices.toml``.

The study once priced formula quantities at unit rates written into the engine, which broke
decision #28 twice: dollars shipped, and the quantities were not the model's. Here every
``variants.toml`` entry is resolved, ablated to the courtyard scope, billed, and priced by
the house. ``engineering/`` is a leaf, so the join lives in ``cli/`` and hands the report
plain :class:`CostLine` data.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from typehaus.engineering.sunken_garden.comparison import CostLine, CostRange

#: Court, raised terrace and comparison planter tags (-SG-, -RG-, -RGV-).
SCOPE_TAG = re.compile(r"-(SG|RG|RGV)-")
#: The walkout finish belongs to the house wall, not a garden tag; the swap retypes it.
SCOPE_ASSEMBLIES = frozenset({"BASEMENT_BRICK_VENEER", "BASEMENT_FIBER_CEMENT_SCREEN"})
#: Whole-site allowances that touch the court; reported beside the deltas, never inside them.
ALLOWANCE_WORDS = re.compile(r"sunken-garden|court")


@dataclasses.dataclass(frozen=True)
class VariantCosts:
    lines: dict[str, tuple[CostLine, ...]]
    allowances: tuple[tuple[str, CostRange], ...]
    source: str


def _tag(item: object) -> str | None:
    tag = getattr(item, "tag", None)
    if isinstance(tag, str):
        return tag
    for name in ("source", "wall", "element"):
        tag = getattr(getattr(item, name, None), "tag", None)
        if isinstance(tag, str):
            return tag
    return None


def _in_scope(item: object) -> bool:
    tag = _tag(item)
    if tag and SCOPE_TAG.search(tag):
        return True
    return getattr(item, "assembly", None) in SCOPE_ASSEMBLIES


def ablate_to_scope(model) -> None:
    """Keep only courtyard elements in every tagged collection; untagged graphs stay."""

    for item in dataclasses.fields(model):
        values = getattr(model, item.name)
        if isinstance(values, list) and any(_tag(value) for value in values):
            setattr(model, item.name, [value for value in values if _in_scope(value)])
    model.index_by_tag()


def _range(value: dict) -> CostRange:
    return CostRange(float(value["low"]), float(value["high"]))


def _lines(estimate: dict) -> tuple[CostLine, ...]:
    out = []
    for section, payload in sorted(estimate["sections"].items()):
        rows = payload.get("rows") or []
        if not rows:
            continue
        quantities: dict[str, float] = {}
        material = labor = merged = CostRange(0.0, 0.0)
        for row in rows:
            unit = str(row.get("unit") or "")
            quantities[unit] = quantities.get(unit, 0.0) + float(row.get("quantity") or 0.0)
            material += _range(row["material"])
            labor += _range(row["labour"])
            merged += _range(row["merged"])
        quantity = "; ".join(f"{value:,.1f} {unit}" for unit, value in sorted(quantities.items()))
        out.append(CostLine(section.replace("_", " "), quantity, material, labor, merged))
    return tuple(out)


def price_variants(house: Path) -> VariantCosts | None:
    """``None`` when the house has no ``prices.toml`` — the study then reports no dollars."""

    from typehaus.cli.price_file import load_prices
    from typehaus.cli.prices import estimate_costs
    from typehaus.diff.compare import resolve_variant
    from typehaus.diff.variants import load_variants
    from typehaus.takeoff.bom import bill_of_materials

    prices = load_prices(house)
    if prices is None:
        return None
    allowances = tuple(
        (key, CostRange(float(price.low), float(price.high)))
        for key, price in sorted(prices.allowances.items())
        if ALLOWANCE_WORDS.search(key) and not getattr(price, "driver", None))
    # Driven allowances read whole-house BOM fields an ablated BOM no longer has, and none
    # of them varies with a courtyard layout.
    scoped_prices = dataclasses.replace(prices, allowances={})
    lines: dict[str, tuple[CostLine, ...]] = {}
    for spec in load_variants(house):
        model, _ = resolve_variant(spec.selection(house))
        ablate_to_scope(model)
        lines[spec.name] = _lines(estimate_costs(bill_of_materials(model), scoped_prices))
    return VariantCosts(lines, allowances, prices.path.name)

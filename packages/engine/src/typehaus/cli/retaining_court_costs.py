"""Price each declared courtyard variant from its own resolved model and ``prices.toml``.

The study once priced formula quantities at unit rates written into the engine, which broke
decision #28 twice: dollars shipped, and the quantities were not the model's. Here every
``variants.toml`` entry is resolved, ablated to the courtyard scope, billed, and priced by
the house. ``engineering/`` is a leaf, so the join lives in ``cli/`` and hands the report
plain :class:`CostLine` data.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from typehaus.engineering.retaining_court.comparison import CostLine, CostRange

#: ``variants.toml``'s optional ``[study]`` table names the scope. Its ``scope_tags`` are tag
#: substrings (the court, its terrace, a comparison planter); ``allowance_words`` pick the
#: whole-site allowances reported beside the deltas, never inside them. Every assembly a
#: variant swaps is in scope too: a swap retypes an element the study compares.
STUDY_TABLE = "study"


@dataclasses.dataclass(frozen=True)
class StudyScope:
    tags: tuple[str, ...] = ()
    assemblies: frozenset[str] = frozenset()
    allowance_words: tuple[str, ...] = ()

    def contains(self, item: object) -> bool:
        tag = _tag(item)
        if tag and any(part in tag for part in self.tags):
            return True
        return getattr(item, "assembly", None) in self.assemblies


def study_scope(house: Path, specs) -> StudyScope:
    import tomllib

    from typehaus.diff.variants import VARIANTS_FILENAME

    path = Path(house) / VARIANTS_FILENAME
    table = tomllib.loads(path.read_text()).get(STUDY_TABLE, {}) if path.exists() else {}
    swapped = {name for spec in specs for pair in spec.assembly_swaps.items() for name in pair}
    return StudyScope(tuple(str(t) for t in table.get("scope_tags", ())), frozenset(swapped),
                      tuple(str(w) for w in table.get("allowance_words", ())))


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


def ablate_to_scope(model, scope: StudyScope) -> None:
    """Keep only the study's elements in every tagged collection; untagged graphs stay."""

    for item in dataclasses.fields(model):
        values = getattr(model, item.name)
        if isinstance(values, list) and any(_tag(value) for value in values):
            setattr(model, item.name, [value for value in values if scope.contains(value)])
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
    specs = load_variants(house)
    scope = study_scope(house, specs)
    allowances = tuple(
        (key, CostRange(float(price.low), float(price.high)))
        for key, price in sorted(prices.allowances.items())
        if any(word in key for word in scope.allowance_words)
        and not getattr(price, "driver", None))
    # Driven allowances read whole-house BOM fields an ablated BOM no longer has, and none
    # of them varies with a courtyard layout.
    scoped_prices = dataclasses.replace(prices, allowances={})
    lines: dict[str, tuple[CostLine, ...]] = {}
    for spec in specs:
        model, _ = resolve_variant(spec.selection(house))
        ablate_to_scope(model, scope)
        lines[spec.name] = _lines(estimate_costs(bill_of_materials(model), scoped_prices))
    return VariantCosts(lines, allowances, prices.path.name)

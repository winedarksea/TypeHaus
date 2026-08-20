"""Turning a net priced BOM into a bid number — waste, contingency, markup, tax, $/sf.

Kept out of :mod:`typehaus.cli.prices`, which owns the *file format*, because this owns the
*arithmetic* and the two change for different reasons.

The order is fixed and each stage is reported on its own line::

    subtotal_net  ->  waste  ->  subtotal_ordered  ->  contingency  ->  markup  ->  tax
                                                                                     |
                                                                                   total

Nothing is folded silently into a section. An estimate whose sections already contain a
contingency is an estimate nobody can compare against a real bid, and the four stages are
each somebody different's number: waste is the takeoff's, contingency is the designer's,
markup is the builder's, tax is the state's.

Two rules the whole design exists to protect:

- **Never divide a merged number.** An ``installed`` row without a declared split is
  reported as *merged*, not as an invented 55/45. Sales tax therefore applies to the
  ``material`` subtotal only, and the payload says how much sat in ``merged`` where tax
  could not reach it.
- **Never double-count waste.** Four sections are billed on an order quantity that already
  carries it (:data:`typehaus.cli.prices.WASTE_IN_QUANTITY`); the loader refuses a
  price-side factor on those, so this module never has to decide.
- **Waste is a material fact, not a labour one.** It never rides on declared labour — see
  :func:`apply_waste`. Without that rule waste and contingency stop being distinguishable,
  which is exactly the confusion the two-stage design exists to prevent.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from typehaus.cli.prices import INSTALLED, LABOUR, MATERIAL, ZERO, PriceRange, waste_in_quantity


def split_by_basis(cost: PriceRange, price: Any) -> dict[str, PriceRange]:
    """Route one row's cost into ``material`` / ``labour`` / ``merged``.

    ``price`` is a :class:`typehaus.cli.prices.UnitPrice`; a plain ``PriceRange`` (an older
    caller) is treated as material, which is what the file format's own default says.
    """
    buckets = {MATERIAL: ZERO, LABOUR: ZERO, "merged": ZERO}
    material, labour = getattr(price, "material", None), getattr(price, "labour", None)
    if material is not None and labour is not None:
        # A declared split scales with the row: the ratio is the file's, the quantity is
        # the model's. Labour is the *remainder* rather than its own product, so the two
        # parts always add back to exactly the row cost — an estimate whose parts do not
        # sum to its own total is one nobody will trust again.
        whole = material.plus(labour)
        share = (cost.low / whole.low if whole.low else 0.0,
                 cost.high / whole.high if whole.high else 0.0)
        material_part = PriceRange(round(material.low * share[0], 2),
                                   round(material.high * share[1], 2))
        buckets[MATERIAL] = material_part
        buckets[LABOUR] = PriceRange(cost.low - material_part.low,
                                     cost.high - material_part.high)
        return buckets
    basis = getattr(price, "basis", MATERIAL)
    buckets["merged" if basis == INSTALLED else basis] = cost
    return buckets


def _add(into: dict[str, PriceRange], parts: dict[str, PriceRange]) -> None:
    for name, value in parts.items():
        into[name] = into[name].plus(value)


def empty_buckets() -> dict[str, PriceRange]:
    return {MATERIAL: ZERO, LABOUR: ZERO, "merged": ZERO}


def buckets_as_dict(buckets: dict[str, PriceRange]) -> dict[str, Any]:
    out: dict[str, Any] = {name: value.as_dict() for name, value in buckets.items()}
    out["fmt"] = {name: value.fmt() for name, value in buckets.items()}
    return out


def apply_waste(section: str, key: str, parts: Mapping[str, PriceRange],
                adjustments: Any) -> PriceRange:
    """The waste *added* to one row (not the ordered cost — the delta).

    ** WASTE NEVER RIDES ON DECLARED LABOUR. ** Waste is a *quantity* fact: you buy 110 SF of
    board to install 100 SF and throw 10 SF away. You do not pay the installer 10% more for
    it — an installed labour rate is quoted per square foot of FINISHED area and already has
    normal cutting inside it. Charging waste on labour makes waste and contingency look like
    the same thing, which is the complaint that produced this fix: before it, 41% of this
    house's waste ($10,531 – $19,796) was being added to labour.

    A MERGED row is the exception, and necessarily so: an installed price with no declared
    split cannot have its material half identified, so the factor rides on the whole number
    and this docstring is where that is admitted. It is the same "never divide a merged
    number" rule that keeps sales tax off merged rows — the difference is only which way the
    honest default falls. Waste over-applies slightly on a merged row; tax under-applies.
    Declaring a split fixes both at once, which is the third reason to declare one.
    """
    if waste_in_quantity(section):
        return ZERO
    wasteable = parts[MATERIAL].plus(parts["merged"])
    return wasteable.times(adjustments.waste_rate(section, key))


def roll_up(section_buckets: dict[str, dict[str, PriceRange]], waste: dict[str, PriceRange],
            adjustments: Any, excluded: frozenset[str],
            tax_paid: Mapping[str, PriceRange] | None = None) -> dict[str, Any]:
    """The five stages, from per-section basis buckets to one total.

    ``section_buckets`` and ``waste`` are keyed by section name; sections in ``excluded``
    (furnishings) are summed beside the construction total, never into it, and take no
    contingency, markup or tax — a sofa is not something a builder marks up.

    ``tax_paid`` is material whose authored price already carries sales tax, and it is
    subtracted from the taxable base rather than from the total: the money is real and stays
    in the estimate; it just must not be taxed twice. See ``Adjustments.tax_included``.
    """
    net = empty_buckets()
    waste_total = ZERO
    net_total = ZERO
    tax_paid_total = ZERO
    for name, buckets in section_buckets.items():
        if name in excluded:
            continue
        _add(net, buckets)
        waste_total = waste_total.plus(waste.get(name, ZERO))
        tax_paid_total = tax_paid_total.plus((tax_paid or {}).get(name, ZERO))
        # Accumulated per section, matching how ``estimate_costs`` builds its own ``total``
        # from section subtotals. Summing the three buckets across every row instead would
        # be the same money in a different float order, and land a cent away from the total
        # printed two lines above it — which reads as a bug, not as float arithmetic.
        net_total = net_total.plus(
            buckets[MATERIAL].plus(buckets[LABOUR]).plus(buckets["merged"]))
    ordered = net_total.plus(waste_total)
    contingency = ordered.times(adjustments.contingency)
    marked_base = ordered.plus(contingency)
    overhead = marked_base.times(adjustments.overhead)
    profit = marked_base.plus(overhead).times(adjustments.profit)
    # Tax rides on the *material* portion, grown by the same waste and contingency the
    # material itself is subject to — you buy and pay tax on the ordered quantity, not the
    # net one. Merged rows are excluded and said so, rather than guessed at.
    taxable_material = PriceRange(max(0.0, net[MATERIAL].low - tax_paid_total.low),
                                  max(0.0, net[MATERIAL].high - tax_paid_total.high))
    material_share = (taxable_material.low / net_total.low if net_total.low else 0.0,
                      taxable_material.high / net_total.high if net_total.high else 0.0)
    taxable = PriceRange(marked_base.low * material_share[0],
                         marked_base.high * material_share[1])
    tax = taxable.times(adjustments.material_tax_rate)
    total = marked_base.plus(overhead).plus(profit).plus(tax)

    def _line(label: str, value: PriceRange, rate: float | None = None) -> dict[str, Any]:
        row: dict[str, Any] = {"label": label, **value.as_dict(), "fmt": value.fmt()}
        if rate is not None:
            row["rate"] = rate
        return row

    return {
        "net": buckets_as_dict(net),
        "stages": [
            _line("subtotal_net", net_total),
            _line("waste", waste_total),
            _line("subtotal_ordered", ordered),
            _line("contingency", contingency, adjustments.contingency),
            _line("overhead", overhead, adjustments.overhead),
            _line("profit", profit, adjustments.profit),
            _line("tax", tax, adjustments.material_tax_rate),
            _line("total", total),
        ],
        "subtotal_net": net_total.as_dict(),
        "subtotal_ordered": ordered.as_dict(),
        "total": total.as_dict(),
        "total_fmt": total.fmt(),
        # How much of the base the tax could not see, because it is merged material+labour.
        # Named rather than absorbed: it is the number that tells you whether declaring more
        # splits in prices.toml would change the answer.
        "untaxed_merged": net["merged"].as_dict(),
        # Material the tax stage deliberately skipped because its price already carries tax.
        # Reported for the same reason ``untaxed_merged`` is: a stage that quietly declines to
        # tax a third of the material is one nobody can check.
        "material_tax_already_paid": tax_paid_total.as_dict(),
        "taxable_material": taxable_material.as_dict(),
    }


def per_sf(value: Mapping[str, float],
           denominators: Mapping[str, float]) -> dict[str, dict[str, float]]:
    """``{low, high}`` divided by each named area, skipping zero denominators."""
    out: dict[str, dict[str, float]] = {}
    for name, area in denominators.items():
        if not area:
            continue
        out[name] = {"low": round(value["low"] / area, 2),
                     "high": round(value["high"] / area, 2)}
    return out

"""Pricing a bill of materials — the join, the roll-up, and what it refuses to guess.

Split from :mod:`typehaus.cli.price_file`, which owns the *file format*: this module owns
the *join* between a ``prices.toml`` and a ``bill_of_materials`` payload, and the two change
for different reasons. Everything the old single module exported is still importable from
here, so ``from typehaus.cli.prices import ...`` keeps working for every caller.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Optional

from typehaus.cli.price_file import (  # noqa: F401  (re-exported: this is the public name)
    _SECTIONS,
    ALTERNATE_UNITS,
    BASES,
    INSTALLED,
    LABOUR,
    MATERIAL,
    PRICES_FILENAME,
    WASTE_IN_QUANTITY,
    ZERO,
    Adjustments,
    PriceRange,
    Prices,
    UnitPrice,
    _dollars,
    _price,
    load_prices,
    waste_in_quantity,
)

#: The re-export surface. ``price_file`` owns the file format and this module owns the join,
#: but every existing caller says ``from typehaus.cli.prices import ...`` — naming the names
#: here keeps that path a declared contract rather than an implicit one.
__all__ = [
    "ALTERNATE_UNITS", "BASES", "INSTALLED", "LABOUR", "MATERIAL", "PRICES_FILENAME",
    "ALLOWANCE_KEY_FIELD", "ALLOWANCES", "Adjustments",
    "ESTIMATE_PLANS", "EXCLUDED_FROM_TOTAL", "MATERIAL_ONLY", "PriceRange", "Prices", "UnitPrice",
    "QUALIFIED_KEY_FIELD", "UNPRICED_VIEWS", "WASTE_IN_QUANTITY", "ZERO",
    "estimate_costs", "load_prices",
    "waste_in_quantity",
]

#: BOM fields that read as a human description, most specific first. A CSV row that says
#: only "framing / 2x6" is not something a supplier can quote from.
_DESCRIPTION_FIELDS = ("description", "scope", "name", "label", "product", "assembly")


def _describe(row: Mapping[str, object], section: str, key: str) -> str:
    for field_name in _DESCRIPTION_FIELDS:
        value = row.get(field_name)
        if isinstance(value, str) and value:
            return value
    types = row.get("types")
    if isinstance(types, (list, tuple)) and types:
        return ", ".join(str(t) for t in types)
    return f"{section.replace('_', ' ')} · {key}"


def _sum(ranges: Iterable[PriceRange]) -> PriceRange:
    total = ZERO
    for item in ranges:
        total = total.plus(item)
    return total


#: How each price section joins the BOM, authored once: ``(estimate section, bom key,
#: price key field, quantity field, unit)``. The price table itself is the ``Prices``
#: attribute named by the section. Both :func:`estimate_costs` and the cost-tracking
#: payload (``takeoff/costs.py``) read this — the ``(section, key)`` a paid check-off is
#: stored under has to be the *same* join the estimate prices, or the two views drift.
#:
#: ``waste_in_quantity`` is derived from :data:`WASTE_IN_QUANTITY` rather than repeated as a
#: sixth tuple element: one list, one place to be wrong.
ESTIMATE_PLANS = (
    ("framing", "framing_by_size", "profile", "order_length_ft", "LF"),
    ("sheet_goods", "sheet_goods", "material", "sheets_4x8", "sheets"),
    ("hardware", "hardware", "part_number", "count", "ea"),
    ("concrete", "structural_solids", "category", "volume_cubic_yards", "cy"),
    ("floor_heat", "floor_heat", "system", "wire_length_ft", "LF"),
    ("placeables", "placeables", "type", "count", "ea"),
    # Priced on the *order* quantity, not the net area: a finish is bought with its
    # waste, and pricing net area would under-cost every plank and tile room.
    ("floor_finishes", "floor_finishes", "finish", "order_area_sqft", "SF"),
    ("envelope_layers", "envelope_layers", "material", "net_area_sqft", "SF"),
    # Order quantity like floor_finishes (wood is bought with its waste). Timber rows
    # carry no order_area_sqft and price as 0 here — they bill via structural_solids.
    ("wood_surfaces", "wood_surfaces", "material", "order_area_sqft", "SF"),
    ("openings", "openings", "type", "count", "ea"),
    ("footing_bedding", "footing_bedding", "aggregate", "volume_cubic_yards", "cy"),
    ("pipe_runs", "pipe_runs", "system", "length_ft", "LF"),
    ("pipe_fittings", "pipe_fittings", "fitting", "count", "ea"),
    ("ducts", "ducts", "system", "length_ft", "LF"),
    ("sleeves", "sleeves", "sleeve_diameter_in", "count", "ea"),
    ("conduit", "conduit", "trade_size_in", "length_ft", "LF"),
    ("plumbing_specialties", "plumbing_specialties", "kind", "count", "ea"),
    ("install_parts", "install_parts", "part", "count", "ea"),
    ("pipe_insulation", "pipe_insulation", "spec", "length_ft", "LF"),
    ("edge_trim", "edge_trim", "category", "length_ft", "LF"),
    # Placed by the yard, keyed on the assembly — see the field comment on ``Prices``.
    ("wall_structure", "wall_structure", "assembly", "volume_cubic_yards", "cy"),
    # The wood half of ``structural_solids`` (2026-08-22). Identical join to ``concrete``,
    # on the identical BOM table; ``MATERIAL_ONLY`` is what keeps the two from both
    # billing the same row. See the field comment on ``Prices.timber``.
    ("timber", "structural_solids", "category", "volume_cubic_yards", "cy"),
    ("railings", "railings", "type", "length_ft", "LF"),
    # Pre-framing returns by the foot, keyed on ``takeoff_category`` (2026-08-18).
    ("construction_returns", "construction_returns", "category", "length_ft", "LF"),
    # The sill seal under those plates, keyed on the product the resolver picked
    # (2026-08-24). Priced separately from ``pt-sill-plate`` above, which is a delta over
    # the SPF board and no longer carries a foam-sealer component.
    ("sill_gaskets", "sill_gaskets", "product", "length_ft", "LF"),
    ("drainage", "drainage", "category", "length_ft", "LF"),
    # Reads the *same* BOM rows as ``placeables`` — see ``EXCLUDED_FROM_TOTAL``.
    ("furnishings", "placeables", "type", "count", "ea"),
    # Lump sums (2026-08-20). The BOM table this names does not come from the model — see
    # ``ALLOWANCES`` and ``_allowance_rows``.
    ("allowances", "allowances", "item", "count", "ls"),
)

#: The one estimate section whose "BOM" is synthesised from the price table rather than read
#: from the model, and the field its synthetic rows key on.
#:
#: Everything else in :data:`ESTIMATE_PLANS` is a rate joined to a quantity the model
#: resolved, which is the whole discipline of the estimate: a price with nothing to multiply
#: cannot appear. But that discipline also means the total silently omits every real cost the
#: model does not resolve — excavation, the water and sewer connections, permits, the general
#: contractor — and a total that omits the excavator is not a total, it is a subtotal wearing
#: the wrong label.
#:
#: So an allowance is a row at quantity 1 whose "unit price" is the lump sum. Synthesising it
#: here rather than special-casing it downstream is what keeps it honest: it flows through the
#: identical basis split, waste, cost-code, CSV, contingency, markup and tax path as a stick of
#: 2x6, and it is visible on its own line with its own basis rather than folded into a total.
ALLOWANCES = "allowances"
ALLOWANCE_KEY_FIELD = "item"

#: Sections that may only bill a BOM row made of certain materials, and the set of
#: ``structure_material`` values each will accept. ``None`` in a set means "the model never
#: said" — no assembly, so no material — and a section carrying it is the CATCH-ALL for
#: its BOM table.
#:
#: ``concrete`` needs the guard because ``structural_solids`` keys on solid CATEGORY, and a
#: category is not a material. "slab" covers SL-M-DECK (9" of cast concrete) *and* a Wahoo
#: aluminium plank deck and a composite plank deck; "column" covers a concrete pier and
#: four solid elm timbers. Without this guard the wood ones bill at the ready-mix $/cy on
#: top of billing as lumber in ``sheet_goods``/``framing`` — a double-count, not just a
#: mis-price.
#:
#: The value was a single material tag until 2026-08-22, and one tag could not say "any
#: structural wood" — which is what ``timber`` needs. ``timber`` reads the *same*
#: ``structural_solids`` table ``concrete`` does, and the two are told apart here and
#: nowhere else: a Beam or a Post is a solid whose category says nothing about what it is
#: made of, so the material is the only honest discriminator.
#:
#: WHY THE SET NAMES ONLY ENGINEERED AND TREATED LUMBER, not every wood tag in the library:
#: ``spf`` is the STRUCTURE material of ordinary stud-wall assemblies, and a solid that is
#: not lumber at all can carry one — catlin's rainscreen vent strip is a ``bug_screen``
#: solid holding ``CATLIN_EXT_2X6``, whose structure layer is spf studs. So ``spf`` on a
#: solid does not mean "this solid is a stick of timber", while ``lvl``/``lsl``/``kdat`` are
#: only ever authored on a member that really is one. A house whose own wood tag should bill
#: here either uses one of these or prices the row by QUALIFIED key, exactly as the elm
#: posts already do.
#:
#: The guard is a *default*, not a wall. A house that authors the QUALIFIED key for one of
#: these rows (``"slab:BALCONY_DECK_ALUMINUM"``, see :data:`QUALIFIED_KEY_FIELD`) has said
#: which assembly it means and at what rate, so ``estimate_costs`` prices it. That is the
#: escape hatch for a solid no other table bills — the aluminium balcony deck, the elm
#: posts, the breezeway polycarbonate — none of which are lumber and so none of which are
#: double-counted. A bare-category row is still filtered.
MATERIAL_ONLY: dict[str, frozenset[str | None]] = {
    "concrete": frozenset({"concrete", None}),
    "timber": frozenset({"lvl", "lsl", "kdat"}),
}


#: Sections whose price table may key a row more narrowly than its ``key_field`` alone,
#: by appending a second BOM field as ``"<key>:<qualifier>"``. The qualified key is used
#: ONLY when the house's table actually carries it, so a bare-category row keeps pricing
#: exactly as before and no existing ``prices.toml`` changes meaning.
#:
#: ``concrete`` needs this because ``structural_solids`` keys on ``category``, and
#: "slab" is one category covering things that cost wildly different amounts per yard: a
#: slab-on-grade is poured on the ground, while a *suspended* deck carries formwork,
#: shoring, rebar and an engineer's stamp — 3-5x the $/cy. The category taxonomy itself
#: must not be split to say so (``ResolvedSolid.category`` is read by a dozen checks and
#: printed in the 3D Inspector), so the price table qualifies by assembly instead.
#: ``drainage`` needs it for the same reason one step down: ``gutter`` is one category over
#: 47.8 LF of seamless aluminium K-style and 73.7 LF of fabricated dark box gutter, which
#: differ by about 3x per foot, and ``downspout`` is one category over 3" aluminium and 4"
#: dark formed. A single blended rate is weighted correctly only for today's mix and becomes
#: wrong the moment one run changes length. ``takeoff/drainage.py`` already reports the
#: product per row, so qualifying by it costs nothing and makes the box-gutter downgrade in
#: ``plans/cost-options.md`` a checkable number instead of an argument about an average.
#: ``wall_structure`` needs it a third time, and for the sharpest version of the same
#: problem: one assembly can now be more than one material. ``Layer.slot`` splits a row of
#: the stack into regions at a height, and catlin's ``BASEMENT_BRICK_VENEER`` is a brown
#: unglazed plinth under a lapis glazed field with two golden-yellow registers in it —
#: three brick colours whose delivered prices differ by 2-3x, since a second glaze colour is
#: its own special-order pallet with its own lead time. One rate on the assembly would be
#: weighted right only for today's band heights and would silently become wrong the moment a
#: band moved. ``wall_structure_takeoff`` already reports the material per row, so
#: qualifying by it costs nothing.
#: ``framing`` needs it a fourth time, one profile string over two products: a truss wall's
#: outriggers are KDAT 2x4 on edge and the studs beside them are SPF 2x4, and treated stock
#: is roughly double. ``framing_by_size`` reports the material per row (``None`` for
#: ordinary lumber, which is every row of every house authored before truss walls), so a
#: table that says nothing prices ``2x4`` exactly as it always did.
#: ``envelope_layers`` needs it a fifth time, and for the sharpest version yet: the SAME
#: material at two depths. A truss wall's closed-cell foam is authored as a 1-1/2" band and
#: a 2-1/2" one — deliberately, so the outrigger inside the outer band parallel-paths — and
#: they are one $/SF rate only if a 2-1/2" spray costs what a 1-1/2" spray costs, which it
#: does not. Qualifying by ``thickness_in`` prices each band at its own rate; a house that
#: keeps its bare ``polyiso`` key keeps one rate over every thickness, unchanged.
QUALIFIED_KEY_FIELD = {"concrete": "assembly", "timber": "assembly",
                       "drainage": "product", "wall_structure": "material",
                       "framing": "material", "envelope_layers": "thickness_in"}


#: Sections priced and reported but held out of the construction total. They stay in
#: ``sections`` (with ``in_total: False``) and roll up into ``excluded_total`` /
#: ``grand_total``, so nothing is hidden — only re-filed.
EXCLUDED_FROM_TOTAL = frozenset({"furnishings"})

#: The price table an estimate section reads: every section except concrete (which prices
#: the ``structural_solids`` rows) shares its table's name.
_PLAN_TABLE = {name: name for name, *_ in ESTIMATE_PLANS}


#: BOM tables no :data:`ESTIMATE_PLANS` entry reads, and why each is not a hole.
#:
#: The estimate's discipline is that a price with nothing to multiply cannot appear. The
#: mirror of that — a *quantity* with no price — is what ``unpriced`` reports, and until
#: 2026-08-21 it could only report a miss inside a table some plan already read. A table no
#: plan named at all fell through both: not priced, and not listed as unpriced either. That
#: is how ``light_run_materials`` (LED tape, extrusion channel, end caps and corner
#: connectors) came to be resolved, exported, and invisible to every cost surface.
#:
#: So the sweep at the end of :func:`estimate_costs` is now the other way round: every BOM
#: table is either priced by a plan, **declared here with a reason**, or listed in
#: ``unpriced``. A new takeoff table added upstream surfaces as unpriced until somebody
#: decides which of the three it is — loud by default, which is the point.
#:
#: A "view" is a table whose scope is genuinely billed somewhere else. Each value says
#: where, and each was checked against the catlin estimate rather than assumed.
UNPRICED_VIEWS: dict[str, str] = {
    # Same sticks, aggregated differently — `framing_by_size` is the priced view.
    "framing": "priced as framing_by_size",
    # Solid categories, so they reach [concrete] by qualified key (`glazing:<assembly>`,
    # `bug_screen:<assembly>`) rather than through a table of their own.
    "glazing_panels": "priced in [concrete] as glazing:<assembly> (structural_solids)",
    "glazing_trim": "priced in [concrete] as glazing_trim (structural_solids)",
    "bug_screens": "priced in [concrete] as bug_screen:<assembly> (structural_solids)",
    # Tread and riser stock is lumber; the nosings and transitions are an allowance.
    "stair_finish": "treads bill in [framing]; nosings in the finish-transitions allowance",
    # Every one of these is a schedule *view* of ElectricalDevice placeables, which price
    # per type in [placeables] (the ED-T-* families). Pricing them again would double-count.
    "electrical_devices": "priced in [placeables] as the ED-T-* types",
    "data_devices": "priced in [placeables] as the ED-T-* types",
    "luminaire_schedule": "priced in [placeables] as the ED-T-LT-* types",
    "lighting_controls": "priced in [placeables] as the ED-T-* types",
    # Schedule and engineering summaries — a panel schedule is not a thing you buy. The
    # breakers behind it are the electrical-afci-gfci-breakers allowance.
    "panel_schedule": "schedule data; breakers are the electrical-afci-gfci allowance",
    "service_load": "engineering summary, not a purchase",
    "lighting_load": "engineering summary, not a purchase",
    "poe_budget": "engineering summary, not a purchase",
    "light_runs": "run geometry; its materials are light_run_materials",
    # Covered by a named allowance, because the model resolves the route but not the wire.
    "conductors": "the electrical-branch-circuit-conductors allowance",
    "data_raceways": "the electrical-structured-low-voltage-drops allowance",
    "solar": "the electrical-pv-array-modules-and-racking allowance",
    "backup_power": "priced in [placeables] as the EQ-T-* types",
}

#: Fields to read an unread table's row key from, most identifying first. A generic reader
#: cannot know a new table's shape, and a coarse "channel / 31.4 LF" line is worth far more
#: than the silence it replaces.
_UNREAD_KEY_FIELDS = ("item", "part", "kind", "category", "material", "spec", "system",
                      "type", "profile", "mark", "tag")


def _unread_table_rows(bom_key: str, table: list[Any]) -> list[dict[str, Any]]:
    """One ``unpriced`` entry per distinct (key, unit) in a table no price plan reads.

    Summed rather than listed row by row, for the same reason the CSV aggregates on
    ``(section, key)``: the reader wants "how much of this is unpriced", not the raw table.
    """
    groups: dict[tuple[str, str], float] = {}
    for row in table:
        if not isinstance(row, Mapping):
            continue
        key = next((str(row[field]) for field in _UNREAD_KEY_FIELDS
                    if isinstance(row.get(field), str) and row[field]), bom_key)
        unit_value = row.get("unit")
        unit = unit_value if isinstance(unit_value, str) and unit_value else "ea"
        quantity = row.get("quantity")
        amount = float(quantity) if isinstance(quantity, (int, float)) else 1.0
        groups[(key, unit)] = groups.get((key, unit), 0.0) + amount
    return [{"section": bom_key, "key": key, "quantity": round(amount, 2), "unit": unit}
            for (key, unit), amount in sorted(groups.items())]



def _allowance_rows(prices: Prices) -> list[dict[str, Any]]:
    """One synthetic BOM row per authored allowance, at quantity 1.

    Sorted so the estimate, the CSV and the task export list them in the same order run to
    run; a lump-sum block that reshuffles between exports is one no reviewer can diff.
    """
    return [{ALLOWANCE_KEY_FIELD: key, "count": 1, "description": key}
            for key in sorted(prices.allowances)]


def estimate_costs(bom: dict[str, Any], prices: Prices,
                   areas: Optional[Mapping[str, float]] = None) -> dict[str, Any]:
    """Price a :func:`typehaus.takeoff.bill_of_materials` payload against ``prices``.

    Returns ``{"sections": {name: {"rows": [...], "subtotal": {...}}}, "total": {...},
    "unpriced": [...]}}``. Sections the BOM has no rows for are omitted; rows without a
    price land in ``unpriced`` so the total is honest about what it excludes.

    ``total`` is the *construction* total: sections in :data:`EXCLUDED_FROM_TOTAL` are
    priced and reported like any other, then summed into ``excluded_total`` instead.
    ``grand_total`` is the two together, for the reader who wants one number.

    Three further roll-ups ride alongside, each of them opt-in and each zero unless the
    house's ``prices.toml`` asks for it (decision #28 — the house owns its numbers):

    - ``basis``: material / labour / merged subtotals, per section and overall. A row is
      merged when its price is ``installed`` with no declared split, and a merged number is
      **never divided**.
    - ``bid``: the ``net -> waste -> ordered -> contingency -> markup -> tax -> total``
      ladder from :mod:`typehaus.takeoff.cost_model`, each stage its own reported line.
    - ``per_sf``: $/sf against the ``areas`` mapping the caller supplies (conditioned and
      gross, from ``server/space_summary.build_space_summary``). Absent when ``areas`` is.
    """
    from typehaus.takeoff.cost_codes import cost_code
    from typehaus.takeoff.cost_model import (
        apply_waste,
        buckets_as_dict,
        empty_buckets,
        per_sf,
        roll_up,
        split_by_basis,
    )
    sections: dict[str, dict[str, Any]] = {}
    total = ZERO
    excluded_total = ZERO
    # A BOM table may feed more than one price section (``placeables`` feeds both
    # [placeables] and [furnishings]), so a miss is only really unpriced when *no* section
    # reading that table priced the key. Collect misses first, then drop the ones another
    # plan caught — otherwise every furnished row would read as unpriced in the other.
    priced: dict[str, set[str]] = {}
    misses: list[tuple[str, dict[str, Any]]] = []
    section_buckets: dict[str, dict[str, PriceRange]] = {}
    section_waste: dict[str, PriceRange] = {}
    # Material whose authored price ALREADY carries sales tax — tracked beside the buckets
    # rather than as a fourth bucket, so ``basis_subtotals`` keeps the shape every consumer
    # and test already reads. See ``Adjustments.tax_included``.
    section_tax_paid: dict[str, PriceRange] = {}
    adjustments = prices.adjustments
    # The allowances "BOM" is the price table itself — see ``ALLOWANCES``. Written into a
    # local copy so a caller's payload is never mutated by having been priced.
    if prices.allowances:
        bom = {**bom, ALLOWANCES: _allowance_rows(prices)}
    for name, bom_key, key_field, section_quantity_field, section_unit in ESTIMATE_PLANS:
        table = getattr(prices, _PLAN_TABLE[name])
        alternates = ALTERNATE_UNITS.get(name) or {}
        rows = []
        buckets = empty_buckets()
        waste_sum = ZERO
        tax_paid_sum = ZERO
        required_materials = MATERIAL_ONLY.get(name)
        for row in bom.get(bom_key, []) or []:
            if required_materials is not None:
                material = row.get("structure_material")
                if material not in required_materials:
                    # A wood deck is not ready-mix, so this section does not price the row
                    # *by default*. But a QUALIFIED key names one assembly and nothing else,
                    # so authoring `slab:BALCONY_DECK_ALUMINUM` in [concrete] is an explicit
                    # statement that the house wants this row priced here — the only table
                    # that bills `structural_solids` at all. Honour that; skip only when the
                    # house has stayed silent.
                    qualifier_field = QUALIFIED_KEY_FIELD.get(name)
                    qualified = (f"{row.get(key_field)}:{row.get(qualifier_field)}"
                                 if qualifier_field else str(row.get(key_field)))
                    if not (qualifier_field and table.get(qualified) is not None):
                        # Recorded, never silent — but recorded ONCE. Two guarded sections
                        # now read ``structural_solids`` (concrete and timber), and a row
                        # that plainly belongs to the other one is not a hole in this one:
                        # reporting from both would list every pipe sleeve and gutter twice
                        # and drown the real misses. The CATCH-ALL — the section whose set
                        # carries ``None``, i.e. the one that bills a solid the model never
                        # gave a material — owns the report; the specialist stays quiet.
                        # A row homeless in *every* section still surfaces, from the
                        # catch-all, exactly as it did before ``timber`` existed.
                        if None in required_materials:
                            quantity = float(row.get(section_quantity_field) or 0.0)
                            if quantity:
                                misses.append((bom_key, {
                                    "section": name, "key": qualified,
                                    "quantity": round(quantity, 2), "unit": section_unit}))
                        continue
            key = str(row.get(key_field))
            qualifier_field = QUALIFIED_KEY_FIELD.get(name)
            if qualifier_field:
                qualifier = row.get(qualifier_field)
                if qualifier and table.get(f"{key}:{qualifier}") is not None:
                    key = f"{key}:{qualifier}"
            price = table.get(key)
            # A row that names its own unit is read against a DIFFERENT field of the same BOM
            # row — see ``ALTERNATE_UNITS``. Resolved per row rather than per section, because
            # `sump` is priced each while `footing` beside it is still priced by the yard.
            quantity_field, unit = section_quantity_field, section_unit
            if price is not None and getattr(price, "unit", None):
                unit = price.unit
                quantity_field = alternates[unit]
            quantity = float(row.get(quantity_field) or 0.0)
            if price is None:
                if quantity:
                    misses.append((bom_key, {"section": name, "key": key,
                                             "quantity": round(quantity, 2), "unit": unit}))
                continue
            priced.setdefault(bom_key, set()).add(key)
            # Rounded to the cent *before* it is split or summed, so the three basis
            # subtotals, the section subtotal and the grand total are all sums of the same
            # numbers. Splitting the unrounded value instead lands the bid ladder a cent
            # away from the total printed above it.
            cost = PriceRange(**price.times(quantity).as_dict())
            parts = split_by_basis(cost, price)
            for bucket, value in parts.items():
                buckets[bucket] = buckets[bucket].plus(value)
            waste = apply_waste(name, key, parts, adjustments)
            waste_sum = waste_sum.plus(waste)
            tax_included = adjustments.tax_is_included(name, key)
            if tax_included:
                tax_paid_sum = tax_paid_sum.plus(parts[MATERIAL])
            # ``structure_material`` is absent on every BOM row but a solid's, and
            # only the solids section reads it — see ``cost_codes._solid_code``.
            code = cost_code(name, key, dict(prices.codes),
                             material=row.get("structure_material"))
            rows.append({"key": key, "description": _describe(row, name, key),
                         "quantity": round(quantity, 2), "unit": unit,
                         "unit_price": price.as_dict(), "cost": cost.as_dict(),
                         "cost_fmt": cost.fmt(),
                         "basis": getattr(price, "basis", MATERIAL),
                         "material": parts[MATERIAL].as_dict(),
                         "labour": parts[LABOUR].as_dict(),
                         "merged": parts["merged"].as_dict(),
                         "waste_pct": round(adjustments.waste_rate(name, key), 4),
                         "tax_included": tax_included,
                         "waste_in_quantity": waste_in_quantity(name),
                         "order_quantity": round(quantity * (1.0 + (
                             0.0 if waste_in_quantity(name)
                             else adjustments.waste_rate(name, key))), 2),
                         **code.as_dict()})
        if rows:
            subtotal = _sum(PriceRange(r["cost"]["low"], r["cost"]["high"]) for r in rows)
            in_total = name not in EXCLUDED_FROM_TOTAL
            sections[name] = {"rows": rows, "subtotal": subtotal.as_dict(),
                              "subtotal_fmt": subtotal.fmt(), "in_total": in_total,
                              "basis": prices.basis.get(name, MATERIAL),
                              "basis_note": prices.basis_notes.get(name),
                              "basis_subtotals": buckets_as_dict(buckets),
                              "waste": waste_sum.as_dict(),
                              "material_tax_already_paid": tax_paid_sum.as_dict(),
                              "waste_in_quantity": waste_in_quantity(name)}
            section_buckets[name] = buckets
            section_waste[name] = waste_sum
            section_tax_paid[name] = tax_paid_sum
            if in_total:
                total = total.plus(subtotal)
            else:
                excluded_total = excluded_total.plus(subtotal)
    unpriced = [row for bom_key, row in misses
                if row["key"] not in priced.get(bom_key, ())]
    # Every BOM table is priced, declared a view, or listed here — see ``UNPRICED_VIEWS``.
    read_tables = {bom_key for _, bom_key, *_ in ESTIMATE_PLANS}
    for bom_key, table in bom.items():
        if bom_key in read_tables or bom_key in UNPRICED_VIEWS:
            continue
        if isinstance(table, list) and table:
            unpriced.extend(_unread_table_rows(bom_key, table))
    grand_total = total.plus(excluded_total)
    bid = roll_up(section_buckets, section_waste, adjustments, EXCLUDED_FROM_TOTAL,
                  section_tax_paid)
    payload = {"sections": sections, "total": total.as_dict(), "total_fmt": total.fmt(),
               "excluded_sections": sorted(n for n in sections
                                           if n in EXCLUDED_FROM_TOTAL),
               "excluded_total": excluded_total.as_dict(),
               "excluded_total_fmt": excluded_total.fmt(),
               "grand_total": grand_total.as_dict(), "grand_total_fmt": grand_total.fmt(),
               "basis_declared": prices.basis_declared,
               "basis": dict(prices.basis), "basis_notes": dict(prices.basis_notes),
               "bid": bid,
               "unpriced": unpriced}
    if areas:
        payload["areas"] = dict(areas)
        payload["per_sf"] = {
            "total": per_sf(total.as_dict(), areas),
            "bid_total": per_sf(bid["total"], areas),
            "sections": {name: per_sf(body["subtotal"], areas)
                         for name, body in sections.items()},
        }
    return payload

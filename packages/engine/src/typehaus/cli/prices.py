"""Pricing a bill of materials — the join, the roll-up, and what it refuses to guess.

Split from :mod:`typehaus.cli.price_file`, which owns the *file format*: this module owns
the *join* between a ``prices.toml`` and a ``bill_of_materials`` payload, and the two change
for different reasons. Everything the old single module exported is still importable from
here, so ``from typehaus.cli.prices import ...`` keeps working for every caller.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

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
    "candidate_keys", "qualifier_fields",
    "estimate_costs", "load_prices",
    "waste_in_quantity",
]

from typehaus.takeoff.product_labels import specified_product

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
    ("duct_fittings", "duct_fittings", "fitting", "count", "ea"),
    ("duct_insulation", "duct_insulation", "spec", "length_ft", "LF"),
    ("sleeves", "sleeves", "sleeve_diameter_in", "count", "ea"),
    ("conduit", "conduit", "trade_size_in", "length_ft", "LF"),
    # Three tables the model resolves and nothing else prices, each replacing a lump sum in
    # [allowances]. ``conductors`` keys on ``poles`` (1 = a 120 V circuit's three wires, 2 = a
    # 240 V circuit's four); ``solar_modules`` is billed by the WATT, which is how the PV
    # trade quotes and what the model carries; ``data_raceways`` keys on ``service`` and reads
    # a table ``conduit`` deliberately excludes, so the two tag families stay disjoint and no
    # run bills twice.
    ("conductors", "conductors", "poles", "length_ft", "LF"),
    ("solar_modules", "solar_modules", "product", "watts", "W"),
    ("data_raceways", "data_raceways", "service", "length_ft", "LF"),
    ("plumbing_specialties", "plumbing_specialties", "kind", "count", "ea"),
    ("install_parts", "install_parts", "part", "count", "ea"),
    ("pipe_insulation", "pipe_insulation", "spec", "length_ft", "LF"),
    # Heater cable by the foot, keyed on the spec. Mirrors nothing: [pipe_runs] bills the
    # pipe the cable follows, never the cable.
    ("freeze_protection", "freeze_protection", "spec", "length_ft", "LF"),
    ("edge_trim", "edge_trim", "category", "length_ft", "LF"),
    # Framing-top membrane by the foot, keyed on the material tag. Mirrors nothing: `framing`
    # bills the stick the tape covers, not the tape.
    ("member_protection", "member_protection", "material", "length_ft", "LF"),
    # Placed by the yard, keyed on the assembly — see the field comment on ``Prices``.
    ("wall_structure", "wall_structure", "assembly", "volume_cubic_yards", "cy"),
    # Reinforcing steel by the POUND — how it is milled, shipped, and quoted. The key is the
    # bar designation and the qualifier is the coating, so a house that has not told black
    # and galvanized apart still prices on `#5` while one that has gets `#5:hdg-a767`.
    ("reinforcement", "reinforcement", "bar", "weight_lb", "lb"),
    # The wood half of ``structural_solids``. Identical join to ``concrete``, on the
    # identical BOM table; ``MATERIAL_ONLY`` is what keeps the two from both billing the same
    # row. See the field comment on ``Prices.timber``.
    ("timber", "structural_solids", "category", "volume_cubic_yards", "cy"),
    ("railings", "railings", "type", "length_ft", "LF"),
    # Pre-framing returns by the foot, keyed on ``takeoff_category``.
    ("construction_returns", "construction_returns", "category", "length_ft", "LF"),
    # The sill seal under those plates, keyed on the product the resolver picked. Priced
    # separately from ``pt-sill-plate`` above, which is a delta over the SPF board and does
    # not carry a foam-sealer component.
    ("sill_gaskets", "sill_gaskets", "product", "length_ft", "LF"),
    ("drainage", "drainage", "category", "length_ft", "LF"),
    # Reads the *same* BOM rows as ``placeables`` — see ``EXCLUDED_FROM_TOTAL``.
    ("furnishings", "placeables", "type", "count", "ea"),
    # Lump sums. The BOM table this names does not come from the model — see ``ALLOWANCES``
    # and ``_allowance_rows``.
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
#: A single material tag cannot say "any structural wood" — which is what ``timber`` needs.
#: ``timber`` reads the *same*
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
    # ``glulam-treated`` joins the three since 2026-09-03: the balcony beams are a
    # manufactured member bought by the lineal foot out of [timber], and without the
    # entry the material guard drops them from the bill entirely — which makes the
    # total FALL and reads as a saving.
    "timber": frozenset({"lvl", "lsl", "kdat", "glulam-treated"}),
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
#: ``ducts`` needs it a sixth time: one ``supply`` rate covering a 6" insulated riser, a 3"
#: semi-rigid radial and a 14x8 galvanized trunk, because ``ducts`` keys on ``system`` alone.
#: Semi-rigid is roughly half the material of sheet metal and installs in a fraction of the
#: time — that speed IS the argument for a radial system — so one blended rate is weighted
#: for today's mix and silently wrong the moment the mix moves. The takeoff reports
#: ``material`` per row; a row whose material the model never named (the sheet-metal trunks)
#: has an empty string there, which is falsy, so it keeps pricing on the bare key.
#:
#: A value may be a TUPLE, in which case the qualifiers stack most-significant first and a
#: lookup tries progressively less specific keys: ``supply:semi_rigid:3.0`` →
#: ``supply:semi_rigid`` → ``supply``. Because it falls back, every price file that was
#: written against the older, shorter key keeps its exact meaning — a house opts into the
#: finer grain by authoring the finer key and not otherwise. ``[ducts]`` is the case that
#: forced it: a 3" radial branch and a 6" trunk are not the same article at all, and one
#: blended per-foot rate across 246 LF of each was the standing admission in prices.toml.
QUALIFIED_KEY_FIELD: dict[str, str | tuple[str, ...]] = {
    "concrete": "assembly", "timber": "assembly",
    # THE one line that prices black and galvanized bar separately while leaving a house
    # that authors only `#5` completely unchanged — `#5:hdg-a767` falls back to `#5` through
    # ``candidate_keys``. HDG is roughly +$0.30/lb, and if the two do not price apart then
    # specifying it is invisible in the estimate, which is most of the point of specifying it.
    "reinforcement": "coating",
    "drainage": "product", "wall_structure": "material",
    "framing": "material", "envelope_layers": "thickness_in",
    "ducts": ("material", "diameter_in"),
}


def qualifier_fields(section: str) -> tuple[str, ...]:
    """The BOM-row fields whose values qualify ``section``'s price key, most significant
    first. Empty when the section prices on the bare key."""
    field = QUALIFIED_KEY_FIELD.get(section)
    if not field:
        return ()
    return (field,) if isinstance(field, str) else tuple(field)


def candidate_keys(key: object, qualifiers: object = None) -> list[str]:
    """Price-table keys to try for ``key``, most specific first, bare key last.

    ``qualifiers`` is one value or a sequence of them. A falsy qualifier TRUNCATES the
    chain rather than being skipped: the takeoff writes an empty string where the model
    never named a material, and ``supply::3.0`` is not a key anybody would author. That
    truncation is also what keeps a section whose rows have no material pricing on the bare
    key exactly as it did before.

    Values are stringified with ``str()``, which is the same conversion the takeoff row
    carries — ``diameter_in`` is rounded to 2 dp there, so the key is ``:3.0``, never
    ``:3``. Getting that wrong misses SILENTLY and falls back to the blend with no error,
    which is why ``test_duct_prices_qualify_on_diameter`` pins the exact spelling.
    """
    base = str(key)
    values = () if qualifiers is None else (
        (qualifiers,) if isinstance(qualifiers, str | bytes) or not isinstance(
            qualifiers, (list, tuple)) else tuple(qualifiers))
    parts: list[str] = []
    for value in values:
        if not value:
            break
        parts.append(str(value))
    return [f"{base}:{':'.join(parts[:i])}" for i in range(len(parts), 0, -1)] + [base]


def rate_for(prices: Prices, section: str, key: object,
             qualifier: object = None) -> tuple[str, Any]:
    """The unit rate a BOM row prices at, and the price-table key it resolved to.

    The one implementation of the ``[section] key`` / ``[section] key:qualifier`` join.
    :func:`estimate_costs` uses it for every row of every section, and
    :func:`typehaus.takeoff.runs.run_schedule` uses it to put a $ on a single run — and
    they have to be the same lookup or the per-run cost and the estimate line it rolls into
    will disagree. ``[ducts]`` is the case that forces the point: its key is qualified by
    ``material`` and then ``diameter_in`` (see :data:`QUALIFIED_KEY_FIELD`), so a second,
    hand-rolled ``table.get(system)`` would price a 3" semi-rigid radial at the sheet-metal
    rate. ``qualifier`` may be one value or a sequence of them; the lookup walks
    :func:`candidate_keys` most-specific first and returns the first key the table has.

    Returns ``(resolved_key, price_or_None)``. The key is returned because the caller needs
    to *name* what it looked up — in ``unpriced``, in a CSV, in a schedule row.
    """
    table = getattr(prices, _PLAN_TABLE[section])
    candidates = (candidate_keys(key, qualifier) if QUALIFIED_KEY_FIELD.get(section)
                  else [str(key)])
    for candidate in candidates:
        if table.get(candidate) is not None:
            return candidate, table[candidate]
    return candidates[-1], table.get(candidates[-1])


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
#: mirror of that — a *quantity* with no price — is what ``unpriced`` reports. A table no
#: plan named at all must not fall through both silently: not priced, and not listed as
#: unpriced either.
#:
#: The sweep at the end of :func:`estimate_costs` guarantees every BOM table is either priced
#: by a plan, **declared here with a reason**, or listed in ``unpriced``. A new takeoff table
#: added upstream surfaces as unpriced until somebody decides which of the three it is — loud
#: by default, which is the point.
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
    # Tread and riser stock is lumber; the nosings and transitions are an allowance DRIVEN
    # off this very table's ``tread_lf``, so the quantity is not unread, only unpriced by a
    # section of its own.
    "stair_finish": "treads bill in [framing]; nosings drive the finish-transitions allowance",
    # The milling schedule. Everything it shares with another section says so (``also_in_*``)
    # and bills there; what is only here — the stool and shelf boards — is deliberately
    # unpriced: the stock is owner-milled at a rate that is not a market price, and the
    # fabrication labour is already in the finish-window-stools and cabinet-study-bookcase
    # allowances. Pricing it would bill that work twice (→ takeoff/hardwood.py).
    "hardwood": ("a rough-stock VIEW; shared rows bill in their own sections, "
                 "stools and shelves in [allowances]"),
    # Every one of these is a schedule *view* of ElectricalDevice placeables, which price
    # per type in [placeables] (the ED-T-* families). Pricing them again would double-count.
    "electrical_devices": "priced in [placeables] as the ED-T-* types",
    "data_devices": "priced in [placeables] as the ED-T-* types",
    "luminaire_schedule": "priced in [placeables] as the ED-T-LT-* types",
    "lighting_controls": "priced in [placeables] as the ED-T-* types",
    # Schedule and engineering summaries — a panel schedule is not a thing you buy. The
    # breakers behind it are the electrical-afci-gfci-breakers allowance.
    "panel_schedule": ("schedule data; its row COUNT drives the electrical-afci-gfci "
                       "allowance (2026-08-27)"),
    "service_load": "engineering summary, not a purchase",
    "lighting_load": "engineering summary, not a purchase",
    "poe_budget": "engineering summary, not a purchase",
    "light_runs": "run geometry; its materials are light_run_materials",
    # ``solar`` is a dict of summaries (panel/watt totals, the per-string voltage check);
    # the priced view of it is the ``solar_modules`` list beside it — see ``takeoff/bom.py``.
    # ``conductors`` and ``data_raceways`` are priced in their own sections: the model
    # resolves the route *and* the wire.
    "solar": "priced as solar_modules (the by_product view of this dict)",
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



#: The two scalars a driver may address that are not a BOM table: the ``areas`` denominators
#: ``estimate_costs`` is already given. Spelled ``space_summary.<name>`` because that is the
#: module they come from (``server/space_summary.build_space_summary``), and because a house
#: reading its own file should not have to know that the engine calls the mapping "areas".
DRIVER_SCALARS = {"space_summary.conditioned_sf": "conditioned",
                  "space_summary.gross_sf": "gross"}

#: The pseudo-field a driver names to COUNT rows rather than sum a number off them. Some
#: tables are one row per thing and carry no count column — ``panel_schedule`` is one row per
#: circuit, ``data_devices`` one row per device — and "36 circuits" is exactly the quantity a
#: breaker allowance wants. Reserved rather than inferred: a table that really has a ``rows``
#: column would otherwise change meaning silently.
DRIVER_ROW_COUNT = "rows"


def _driver_parts(spec: str) -> tuple[str, str, dict[str, str]]:
    """``"openings.count[kind=door]"`` -> ``("openings", "count", {"kind": "door"})``.

    The shape was validated at load (``price_file._driver``); this is the same grammar read
    for its parts, and a spec that reaches here has already matched it.
    """
    from typehaus.cli.price_file import _DRIVER_GRAMMAR

    match = _DRIVER_GRAMMAR.match(spec)
    assert match is not None, spec  # load-time validation is what makes this safe
    raw = match["filters"] or ""
    filters = dict(clause.split("=", 1) for clause in raw.split(",")) if raw else {}
    return match["table"], match["field"], filters


def _resolve_driver(bom: Mapping[str, Any], areas: Mapping[str, float] | None,
                    key: str, spec: str) -> tuple[float, list[tuple[str, Mapping[str, Any]]]]:
    """A driven allowance's quantity, and the BOM rows it was measured off.

    The second half of the return is not decoration: it is what the double-count guard reads.
    [allowances]'s one rule is that an allowance must be scope NO OTHER SECTION PRICES, and a
    driver makes a breach easy to write by accident — pointing at
    ``envelope_layers.net_area_sqft[material=gwb]`` is a perfectly valid driver that bills the
    drywall a second time. Nothing can decide that
    automatically (measuring a vent mat off the roof cladding's area is right; billing the
    cladding twice is wrong, and the two drivers look identical), so the rows are carried out
    and :func:`estimate_costs` reports the overlap for a human to judge.

    Raises ``ValueError`` naming the key for an unresolvable driver — an unknown table, a
    field no row carries, a scalar with no ``areas`` behind it. Deliberately the same class of
    failure as a malformed price: a quantity that cannot be found must never quietly become
    zero, which would print the row as free rather than as unpriced.
    """
    if spec in DRIVER_SCALARS:
        if not areas:
            raise ValueError(
                f"[{ALLOWANCES}] {key!r} has driver {spec!r}, but this estimate was built "
                f"without areas. Pass the space summary's conditioned/gross denominators to "
                f"estimate_costs, or drive the row off a BOM table instead.")
        name = DRIVER_SCALARS[spec]
        if name not in areas:
            raise ValueError(f"[{ALLOWANCES}] {key!r} has driver {spec!r}; the areas mapping "
                             f"offers {sorted(areas)}")
        return float(areas[name]), []
    table_name, field, filters = _driver_parts(spec)
    if table_name == "space_summary":
        raise ValueError(f"[{ALLOWANCES}] {key!r} has driver {spec!r}; the addressable "
                         f"scalars are {sorted(DRIVER_SCALARS)}")
    table = bom.get(table_name)
    if not isinstance(table, list):
        raise ValueError(
            f"[{ALLOWANCES}] {key!r} has driver {spec!r}, but the BOM has no LIST table "
            f"{table_name!r}. A driver reads a table of rows; "
            f"{'that key is a summary dict' if table_name in bom else 'no such key exists'}. "
            f"Tables: {sorted(k for k, v in bom.items() if isinstance(v, list))}")
    for filter_field in filters:
        if not any(filter_field in row for row in table if isinstance(row, Mapping)):
            raise ValueError(f"[{ALLOWANCES}] {key!r} has driver {spec!r}, but no row of "
                             f"{table_name!r} carries a {filter_field!r} field")
    matched = [row for row in table if isinstance(row, Mapping)
               and all(str(row.get(f)) == v for f, v in filters.items())]
    if field == DRIVER_ROW_COUNT:
        return float(len(matched)), [(table_name, row) for row in matched]
    if not any(field in row for row in table if isinstance(row, Mapping)):
        raise ValueError(
            f"[{ALLOWANCES}] {key!r} has driver {spec!r}, but no row of {table_name!r} "
            f"carries a {field!r} field. Its fields are "
            f"{sorted({f for row in table if isinstance(row, Mapping) for f in row})}, and "
            f"{DRIVER_ROW_COUNT!r} counts rows.")
    total = 0.0
    consumed: list[tuple[str, Mapping[str, Any]]] = []
    for row in matched:
        value = row.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += float(value)
            consumed.append((table_name, row))
    return total, consumed


def _allowance_rows(prices: Prices, bom: Mapping[str, Any],
                    areas: Mapping[str, float] | None
                    ) -> tuple[list[dict[str, Any]],
                               dict[str, list[tuple[str, Mapping[str, Any]]]]]:
    """One synthetic BOM row per authored allowance, and what each driven one consumed.

    An UNDRIVEN row is quantity 1 and unit "ls": the number in the file is the line total. A
    DRIVEN row carries the model quantity its ``driver =`` resolved instead, so the same rate
    moves when the house does — and it is still an allowance, with an allowance's basis, cost
    code, CSV row and work package. Nothing downstream needs to know which kind it got.

    Sorted so the estimate, the CSV and the task export list them in the same order run to
    run; a lump-sum block that reshuffles between exports is one no reviewer can diff.
    """
    rows: list[dict[str, Any]] = []
    consumed: dict[str, list[tuple[str, Mapping[str, Any]]]] = {}
    for key in sorted(prices.allowances):
        price = prices.allowances[key]
        spec = getattr(price, "driver", None)
        if not spec:
            rows.append({ALLOWANCE_KEY_FIELD: key, "count": 1, "description": key})
            continue
        quantity, used = _resolve_driver(bom, areas, key, spec)
        consumed[key] = used
        rows.append({ALLOWANCE_KEY_FIELD: key, "count": quantity,
                     "description": key, "driver": spec})
    return rows, consumed


def _driver_overlaps(consumed: Mapping[str, list[tuple[str, Mapping[str, Any]]]],
                     priced: Mapping[str, set[str]]) -> list[dict[str, Any]]:
    """Driven allowances whose quantity was measured off rows another section also PRICED.

    ** THE GUARD [allowances] NEVER HAD. ** Its header says an allowance must be scope no
    other section prices and admits that nothing in the loader can catch a breach; the BOM
    join that protects every other table from a mirror does not exist for a lump sum. A
    driver does not create that risk but it does make it one line of TOML away, so this is
    the reporting the mechanism owes.

    An overlap is a FINDING, not an error, and that is the whole design: measuring the roof
    vent mat off the standing seam's area is correct and reports an overlap, while billing
    the standing seam twice is wrong and reports the identical shape. Only a reader knows
    which one is written, so name it and let them look.
    """
    findings = []
    for key in sorted(consumed):
        hits: dict[str, set[str]] = {}
        for bom_key, row in consumed[key]:
            for name, plan_key, key_field, *_ in ESTIMATE_PLANS:
                if plan_key != bom_key or name == ALLOWANCES:
                    continue
                # Both spellings, because a section may price a row under a QUALIFIED key
                # ("supply:semi_rigid") — checking only the bare one under-reports exactly
                # where a section has taken the trouble to price precisely.
                fields = qualifier_fields(name)
                qualifiers = tuple(row.get(field) for field in fields)
                bare = str(row.get(key_field))
                for row_key in set(candidate_keys(bare, qualifiers)):
                    if row_key in priced.get(bom_key, ()):
                        hits.setdefault(name, set()).add(row_key)
        if hits:
            findings.append({
                "item": key,
                "sections": {name: sorted(keys) for name, keys in sorted(hits.items())},
            })
    return findings


def estimate_costs(bom: dict[str, Any], prices: Prices,
                   areas: Mapping[str, float] | None = None,
                   products: Mapping[tuple[str, str], str] | None = None
                   ) -> dict[str, Any]:
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

    ``products`` is the *specified* product per ``(section, key)`` — see
    :func:`typehaus.takeoff.product_labels.product_labels`. A row that has one gains a
    ``product`` label, which is the plan's answer to "which product is this line?" and takes
    no part in any arithmetic: it is not a price, it never reaches a subtotal, and a caller
    that passes nothing gets exactly the payload it got before.
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
    driver_consumed: dict[str, list[tuple[str, Mapping[str, Any]]]] = {}
    if prices.allowances:
        allowance_rows, driver_consumed = _allowance_rows(prices, bom, areas)
        bom = {**bom, ALLOWANCES: allowance_rows}
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
                    fields = qualifier_fields(name)
                    keys = candidate_keys(row.get(key_field),
                                          tuple(row.get(f) for f in fields))
                    # The most specific spelling, for the miss report; the opt-in test
                    # accepts ANY qualified spelling the house actually authored.
                    qualified = keys[0]
                    if not (fields and any(table.get(k) is not None for k in keys[:-1])):
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
            fields = qualifier_fields(name)
            key, price = rate_for(prices, name, row.get(key_field),
                                  tuple(row.get(f) for f in fields) if fields else None)
            # A row that names its own unit is read against a DIFFERENT field of the same BOM
            # row — see ``ALTERNATE_UNITS``. Resolved per row rather than per section, because
            # `sump` is priced each while `footing` beside it is still priced by the yard.
            quantity_field, unit = section_quantity_field, section_unit
            driver = getattr(price, "driver", None) if price is not None else None
            if price is not None and getattr(price, "unit", None):
                unit = price.unit
                # A driven allowance's unit is a printed LABEL — the driver already chose the
                # field, and the resolved quantity is on the synthetic row's ``count``. Every
                # other section's unit SELECTS a field, which is what ``alternates`` maps.
                if not driver:
                    quantity_field = alternates[unit]
            quantity = float(row.get(quantity_field) or 0.0)
            if price is None:
                if quantity:
                    misses.append((bom_key, {"section": name, "key": key,
                                             "quantity": round(quantity, 2), "unit": unit}))
                continue
            if driver and not quantity:
                # A driver that resolved to zero is not a free line, it is a line this house
                # has none of — or a filter that matched nothing, which is the same report to
                # the reader and a different fix. Reported as unpriced, never at $0: an
                # allowance for scope the model says does not exist is exactly the claim the
                # reader has to see to disagree with.
                misses.append((bom_key, {"section": name, "key": key, "quantity": 0.0,
                                         "unit": unit, "driver": driver}))
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
            # The product the PLAN specifies for this line, where it names one — never the
            # as-bought record, which lives in costs.toml and is the estimator's to write.
            specified = specified_product(name, key, row, products)
            rows.append({"key": key, "description": _describe(row, name, key),
                         **({"product": specified} if specified else {}),
                         **({"driver": driver} if driver else {}),
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
               # Driven allowances measured off rows another section also priced. A finding
               # for a reader, not an error — see ``_driver_overlaps``.
               "driver_overlaps": _driver_overlaps(driver_consumed, priced),
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

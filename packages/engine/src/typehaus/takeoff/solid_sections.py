"""Which estimate section prices a ``structural_solids`` row — exactly one of four.

The table holds a volume for every resolved solid (a pour, a timber, a drywell, a pane of
polycarbonate), so no single $/cy section can honestly be named for it. Each row files by
material first, then by its category's trade (``emit/trade_rules.solid_trades``):

- ``concrete`` — cast concrete, or a concrete-trade category the model gave no material;
- ``timber``   — engineered and treated structural lumber (:data:`TIMBER_MATERIALS`);
- ``site``     — stormwater, planting and aggregate: the excavator's and landscaper's;
- ``solids``   — everything else: glazing, elm, aluminium, composite, soffits, screens.

A row carrying a material outside its section's own (a composite deck in ``solids``)
prices only on a QUALIFIED key (``slab:PORCH_DECK_COMPOSITE``): it usually bills as lumber
or sheet goods elsewhere too, so a bare-category rate would double-count it.
"""

from __future__ import annotations

from collections.abc import Mapping

from typehaus.emit.trade_rules import solid_trades

SOLID_SECTIONS = ("concrete", "timber", "site", "solids")

#: Only members that really are sticks: ``spf`` is also the structure of a stud-wall
#: assembly a non-lumber solid can carry (a rainscreen bug screen holding ``EXT_2X6``).
TIMBER_MATERIALS = frozenset({"lvl", "lsl", "kdat", "glulam-treated"})

SITE_TRADES = frozenset({"drainage", "landscaping", "earth"})


def solid_section(category: str | None, material: str | None) -> str:
    """The one section that prices a ``structural_solids`` row."""
    if material in TIMBER_MATERIALS:
        return "timber"
    trade = solid_trades(category, material)[0]
    if trade == "concrete" and material in (None, "", "concrete"):
        return "concrete"
    return "site" if trade in SITE_TRADES else "solids"


def bare_key_prices(section: str, material: str | None) -> bool:
    """May an unqualified category key price this row in ``section``? Not when the row
    carries a material its section does not own — see the module docstring."""
    return section in ("concrete", "timber") or not material


def row_section(row: Mapping[str, object]) -> str:
    return solid_section(row.get("category"), row.get("structure_material"))  # type: ignore[arg-type]

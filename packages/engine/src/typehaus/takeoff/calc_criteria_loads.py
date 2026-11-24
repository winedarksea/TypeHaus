"""Design-criteria blocks for gravity loads, seismic and the deck snow basis.

Split out of :mod:`typehaus.takeoff.calc_criteria` (500-line ceiling). The numbers are read off
the inputs the calculations consumed; only the clause each is cited from is written here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.emit.md_writer import table

if TYPE_CHECKING:  # pragma: no cover — typing only
    from typehaus.takeoff.calc_package import PackageInputs


def input_name(name: str) -> str:
    """A quantity's own name, without a ``<tag>.`` or ``<tag>:`` prefix."""
    return name.rsplit(".", 1)[-1].rsplit(":", 1)[-1]


def consumed(inputs: PackageInputs, names: set[str], unit: str) -> dict[float, list[str]]:
    """``{value: [item ids]}`` for every input named ``names`` in ``unit``."""
    found: dict[float, list[str]] = {}
    for record in inputs.records:
        for quantity in record.inputs:
            if input_name(quantity.name) in names and quantity.unit == unit:
                found.setdefault(round(float(quantity.value), 3), []).append(record.item_id)
    return found


#: ``(label, input names, unit, where the value is cited from)``. Values are derived.
_GRAVITY = (
    ("Live load, floors and decks", {"floor_live", "live_load"}, "psf",
     "IRC 2018 Table R301.5 (balconies and decks 40 psf); deck footnotes of Table R507.6 as "
     "amended by MN Rules 1309.0507 (live 40 psf)"),
    ("Dead load, floors and decks", {"floor_dead", "dead_load"}, "psf",
     "MN Rules 1309.0507, Table R507.6 footnotes b and c (dead 10 psf)"),
    ("Dead load, roof", {"design_dead"}, "psf", "assembly weight carried on the roof beam sheet"),
    ("Dead load, truss wall", {"wall_dead"}, "psf",
     "assembly weight, carried high (jamb take-down note)"),
    ("Guard, concentrated load", {"head_lateral_guard"}, "lb",
     "IRC 2018 Table R301.5: 200 lb in any direction at the top of the guard"),
)


def gravity_block(inputs: PackageInputs) -> str:
    """Live, dead and guard loads the records were graded at, with the items using each."""
    rows = []
    for label, names, unit, cite in _GRAVITY:
        found = consumed(inputs, names, unit)
        if not found:
            continue
        values = ", ".join(f"{v:g}" for v in sorted(found))
        items = {i for ids in found.values() for i in ids}
        rows.append([label, values, unit, cite, len(items)])
    if not rows:
        return "_No calculation in this package consumed a gravity load input._"
    return table(["Load", "Value", "Unit", "Cited from", "Items"], rows)


def seismic_text(inputs: PackageInputs) -> str:
    """The seismic statement: the category the jurisdiction assigns, and what that does here."""
    category = getattr(getattr(inputs, "profile", None), "seismic_design_category", None)
    if not category:
        return ("The jurisdiction profile states no Seismic Design Category. No calculation in "
                "this package computes a seismic demand; every lateral demand here is wind.")
    return (f"**Seismic Design Category {category}**, as the jurisdiction assigns it (IRC Table "
            "R301.2.2.1; Minnesota is category A statewide). **No calculation in this package "
            "computes a seismic demand: every lateral demand is wind.** Seismic is not "
            "analysed and nothing here claims that it does not govern.")


def deck_snow_block(site: Any, inputs: PackageInputs) -> str:
    """The balcony-deck snow basis. One source: ``engineering.balcony_loads.deck_basis_text``,
    the same wording the balcony records carry (adopted Minnesota basis, balanced comparison,
    reconciliation with the house's deck snow input, the owner's reasoning)."""
    from types import SimpleNamespace

    from typehaus.engineering.balcony_loads import deck_basis_text

    preferences = getattr(inputs, "preferences", None)
    if preferences is None:
        return ""
    return "**Deck snow.** " + deck_basis_text(SimpleNamespace(preferences=preferences))

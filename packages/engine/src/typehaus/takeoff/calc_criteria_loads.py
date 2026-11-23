"""Design-criteria blocks for gravity loads, seismic and the deck snow basis.

Split out of :mod:`typehaus.takeoff.calc_criteria` (500-line ceiling). The numbers are read off
the inputs the calculations consumed; only the clause each is cited from is written here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.emit.md_writer import table

if TYPE_CHECKING:  # pragma: no cover — typing only
    from typehaus.takeoff.calc_package import PackageInputs

#: Balanced flat-roof snow, ASCE 7-16 eq. 7.3-1: ``p_f = 0.7 Ce Ct Is p_g``.
PF_FACTOR = 0.7
#: Ct for an unheated open structure, as the house's own roof calculation takes it.
CT_UNHEATED = 1.2


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


def design_snow_rows(site: Any, inputs: PackageInputs) -> list[list[Any]]:
    """The balanced comparison, once: ``[basis, factors, psf, against 40 psf deck live]``."""
    ground = getattr(site, "ground_snow_load_psf", None) if site is not None else None
    if ground is None:
        return []
    live = consumed(inputs, {"floor_live", "live_load"}, "psf")
    deck_live = max(live) if live else None

    def versus(pf: float) -> str:
        if deck_live is None:
            return "—"
        gap = pf - deck_live
        return (f"{abs(gap):g} psf below the {deck_live:g} psf live load" if gap < 0 else
                f"{gap:g} psf above the {deck_live:g} psf live load")

    cases = [("Ce = Ct = Is = 1.0", 1.0), (f"Ce = Is = 1.0, Ct = {CT_UNHEATED:g} (unheated, "
                                          "open)", CT_UNHEATED)]
    return [[f"balanced, {label}", f"{PF_FACTOR:g} x {ct:g} x {float(ground):g}",
             round(PF_FACTOR * ct * float(ground), 1), versus(PF_FACTOR * ct * float(ground))]
            for label, ct in cases]


def deck_snow_block(site: Any, inputs: PackageInputs) -> str:
    """The balcony-deck snow basis: adopted, compared once, reconciled with the house input.

    The adopted basis is the Minnesota deck table (40 live + 10 dead, no snow, no drift); the
    balanced comparison and the house's own ``deck_snow_psf`` are printed so a reviewer can see
    the difference rather than discover it. The reasoning is the owner's, and says so.
    """
    rows = design_snow_rows(site, inputs)
    structural = getattr(getattr(inputs, "preferences", None), "structural", None)
    house_psf = getattr(structural, "deck_snow_psf", None)
    if not rows and house_psf is None:
        return ""
    out = [
        "**Deck snow — adopted basis.** The garden balcony decks are designed to the Minnesota "
        "deck basis as adopted: **40 psf live + 10 psf dead, with no snow load and no drift** "
        "(MN Rules 1309.0507, Table R507.6 footnotes b and c). **The reason is the owner's, "
        "not a calculation:** the decks are elevated and wind-swept, so snow is not expected "
        "to lie on them. It is listed under *not covered, owner* on the reviewer's summary.",
    ]
    if rows:
        out.append(table(["Balanced snow comparison (ASCE 7-16 eq. 7.3-1)",
                          "p_f = 0.7 x Ct x p_g", "p_f, psf", "Against deck live load"], rows)
                   + "\n\nBoth rows take Ce = 1.0: no reduction for a wind-swept site is "
                   "claimed in either (ASCE 7-16 Table 7.3-1).")
    if house_psf is not None:
        first = rows[0][2] if rows else None
        same = (f"equals {PF_FACTOR:g} x p_g (the first row above)"
                if first is not None and abs(float(house_psf) - first) < 0.05 else
                "is an owner input, not a row above")
        out.append(
            f"**Reconciliation.** The house input `deck_snow_psf = {float(house_psf):g}` psf "
            f"{same}. It is used only to confirm that the 40 psf live load governs the "
            "deck-joist table; no calculation in this package applies it. The row that "
            "carries Ct is the figure the house's roof calculation uses for the same snow; "
            "it is not carried on the decks.")
    return "\n\n".join(out)

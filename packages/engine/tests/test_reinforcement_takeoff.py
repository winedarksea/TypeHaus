"""``takeoff/reinforcement.py`` — reinforcing steel by the pound, and the guard around it.

Rebar reached the estimate only as an invisible component of the ``[concrete]`` and
``[wall_structure]`` $/cy rates: roughly five tons of it, ordered by nobody, checkable against
nothing. These pin the three properties that make billing it separately safe rather than
merely possible.

* :func:`test_the_bom_bills_only_what_the_house_authored` is the load-bearing one. The BOM
  must never bill what the ENGINEERING SUITE designed, or a ``BASIS_VERSION`` bump moves the
  estimate — the exact failure the engineering fingerprint exists to prevent, arriving through
  the money door.
* :func:`test_pricing_reinforcement_against_an_inclusive_rate_is_a_hard_error` pins the
  double-billing guard. `plans/cost-options.md` recorded the "cut the $/cy rates the same day"
  condition and observed that *"nothing enforces that"*, against a five-ton exposure.
* :func:`test_an_empty_reinforcement_table_moves_no_money` pins the safety property of the
  quantity-only step: the tonnage ships and can be reviewed before any rate is touched.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from typehaus.takeoff.reinforcement import reinforcement_takeoff

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def rows(catlin_model):
    return reinforcement_takeoff(catlin_model)


def _row(rows, bar, scope):
    found = [r for r in rows if r["bar"] == bar and r["scope"] == scope]
    assert found, f"no {bar} in {scope}; got {[(r['bar'], r['scope']) for r in rows]}"
    return found[0]


def test_a_row_bills_cut_length_by_counted_piece(rows) -> None:
    """Cut = placed + laps + hooks, summed over the laid-out pieces (decision #75).

    The old ``area / spacing`` arithmetic is a tolerance oracle now
    (``test_rebar_layout_vs_area.py``); what this module bills is the pieces a fabricator
    cuts, so the three parts must add up and a lapped run must count as one bar.
    """
    for row in rows:
        parts = row["placed_length_ft"] + row["lap_length_ft"] + row["hook_length_ft"]
        assert row["length_ft"] == pytest.approx(parts, abs=0.15), row
        assert row["pieces"] >= row["count"] > 0
    # Runs over stock split into lapped pieces; a dowel laps without splitting.
    assert any(r["pieces"] > r["count"] for r in rows)


def test_weight_is_the_astm_unit_mass(rows) -> None:
    """Steel is bought by the pound, so the pound is what the row has to carry."""
    from typehaus.model.rebar import BARS

    for row in rows:
        number = int(str(row["bar"]).lstrip("#"))
        assert row["weight_lb"] == pytest.approx(
            row["length_ft"] * BARS[number].weight_plf, rel=0.001)


def test_the_coating_comes_from_the_pours_mix_not_the_schedule(rows) -> None:
    """A coating is normally a property of the bar you BUY for a pour, not of a role in it.

    You do not order galvanized verticals and black ties for one cage — a house that tried
    would be specifying a corrosion cell. So it lives on ``ConcreteSpec`` and every row of a
    pour inherits it, which is what makes ``#5:hdg-a767`` a price key worth having. Every
    footing and wall row here is galvanized for exactly that reason: their pours state it.

    **The columns used to be the exception and are not one any more.** Until 2026-09-03
    neither ``SUNKEN_GARDEN_COLUMN_12`` nor ``PIER_CONCRETE_12`` carried a ``ConcreteSpec``,
    so the galvanizing on half the cages was an authored fact with nowhere else to live and
    was stated per-bar via ``BarSpec.coating`` — while the other half read black.
    ``PIER_CONCRETE_12`` named ``EXPOSED_MIX`` that day and ``SUNKEN_GARDEN_COLUMN_12``
    followed on 2026-09-10, so both now inherit A767 from the pour and the per-bar overrides
    are belt and braces rather than the only route. Six columns on each type, twelve cages.
    This still asserts a UNIFORM result reached by two routes, because either one alone
    would be enough and a scope carrying two coatings is the failure worth catching.

    Uniformity is the assertion worth making rather than a coincidence to tolerate. Mixing
    coatings inside one pour is specifying a corrosion cell, and the check that would notice
    is a person reading this table.
    """
    by_scope = {}
    for row in rows:
        by_scope.setdefault(row["scope"], set()).add(row["coating"])
    assert by_scope["footing"] == {"hdg-a767"}
    assert by_scope["foundation wall"] == {"hdg-a767"}
    assert by_scope["column"] == {"hdg-a767"}
    # The one black pour is the interior deck cap, and its MIX says so (DECK_CAP_MIX: no
    # chloride, no freeze-thaw) — the same route, a different answer.
    assert by_scope["slab"] == {"black"}
    assert all(len(coatings) == 1 for coatings in by_scope.values()), by_scope


def test_the_bom_bills_only_what_the_house_authored(catlin_model) -> None:
    """**The load-bearing rule.** Remove the authored spec and the steel disappears.

    The engine SIZES reinforcement and grades the authored schedule against it; it never
    substitutes its own answer. If this module ever started billing the engineering suite's
    design, a ``BASIS_VERSION`` bump would move the estimate — the exact failure the
    engineering fingerprint exists to prevent, arriving through the money door.

    A pour with no authored steel therefore contributes NOTHING here. That is a *hole*, not a
    zero, and it is reported as one by the checks rather than papered over by the takeoff.
    """
    import typehaus.takeoff.reinforcement as module

    tags = {tag for row in reinforcement_takeoff(catlin_model) for tag in row["tags"]}
    assert tags, "catlin authors reinforcement somewhere; this test proves nothing if not"

    # `engineering` must not be IMPORTED here — checked on the parse tree rather than on the
    # text, because the docstring talks about the engineering suite at length and a substring
    # scan would fail on the prose that explains the rule.
    import ast

    tree = ast.parse(Path(module.__file__).read_text())
    imported = {
        name.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for name in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    offenders = sorted(m for m in imported if "engineering" in m)
    assert not offenders, (
        f"takeoff must never import engineering (found {offenders}): a BOM that depended on "
        f"a record would move every time a calc moved")


def test_dowels_bill_only_where_authored_as_l_bars(catlin_model) -> None:
    """A dowel bills when a house authors role ``dowels``, and then as an L (decision #75 D6).

    Its length is a hooked foot in the pour below plus a lap above, so every piece carries a
    lap and a hook. A pour that authors none bills none: nothing here invents one.
    """
    dowels = [(s.host_tag, b) for s in catlin_model.rebar for b in s.bars
              if b.role == "dowels"]
    assert dowels
    authored = {el.tag for el in catlin_model.plan.all_elements()
                if getattr(el, "reinforcement", None) is not None
                and any(b.role == "dowels" for b in el.reinforcement.bars)}
    assert {tag for tag, _ in dowels} == authored
    for _tag, bar in dowels:
        assert bar.lap_length_m > 0 and bar.hook_kinds == ("std90",) and len(bar.path) == 3


def test_an_empty_reinforcement_table_moves_no_money() -> None:
    """catlin bills the steel and prices none of it — on purpose, and that is the safety.

    Every row lands in the estimate's ``unpriced`` list, which satisfies "every BOM table is
    priced, declared, or unpriced" BY BEING LISTED, and the total does not move by one cent.
    The tonnage ships before the dollar does, so it can be read against the allowance
    register's ~5 tons before a single $/cy rate is cut.
    """
    from typehaus.cli.price_file import load_prices

    prices = load_prices(_CATLIN)
    assert prices is not None
    assert prices.reinforcement == {}, (
        "catlin prices no reinforcement yet. When it does, the [concrete] and "
        "[wall_structure] rates must be cut in the SAME commit — see [rebar_inclusive].")
    assert prices.basis["reinforcement"] == "material"


def test_pricing_reinforcement_against_an_inclusive_rate_is_a_hard_error() -> None:
    """The double-billing guard, in both directions.

    ``prices.toml`` states the "cut the $/cy rates the same day" condition in two places, and
    `plans/cost-options.md` observed that *"nothing enforces that"* — against roughly five
    tons and $10,000-18,000. This is the enforcement, and it is the same shape the file
    already uses twice: an explicit opt-in boolean deciding whether a part bills separately
    or rides inside a rate, and a hard error naming both sides of a double-count.
    """
    from typehaus.cli.price_file import load_prices

    source = (_CATLIN / "prices.toml").read_text()
    priced = source.replace("[reinforcement]\n",
                            '[reinforcement]\n"#6" = { low = 1.05, high = 1.35 }\n', 1)

    with tempfile.TemporaryDirectory() as tmp:
        house = Path(tmp)
        (house / "prices.toml").write_text(priced)
        with pytest.raises(ValueError) as excinfo:
            load_prices(house)
        message = str(excinfo.value)
        # It must name BOTH sides: what is priced, and which rate still contains it.
        assert "[reinforcement] is priced" in message
        assert "[concrete]" in message and "[wall_structure]" in message
        assert "rebar_inclusive" in message

        # And declaring the cut lets it through — the guard is a gate, not a wall.
        cut = priced.replace("concrete       = true", "concrete       = false") \
                    .replace("wall_structure = true", "wall_structure = false")
        (house / "prices.toml").write_text(cut)
        assert load_prices(house).reinforcement


def test_the_default_is_inclusive_so_an_old_price_file_keeps_its_meaning() -> None:
    """Silence means "the rate still contains its rebar", because that was the only place it
    could live before this section existed. Defaulting the other way would let a file written
    last year start double-billing the day the new section got a price, silently."""
    from typehaus.cli.price_file import rebar_is_inclusive

    assert rebar_is_inclusive({}, "concrete") is True
    assert rebar_is_inclusive({"rebar_inclusive": {"concrete": False}}, "concrete") is False
    assert rebar_is_inclusive({"rebar_inclusive": {}}, "wall_structure") is True

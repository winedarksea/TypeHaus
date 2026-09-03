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


def test_a_mat_bills_at_area_over_spacing(rows) -> None:
    """``length = area / spacing`` is the whole derivation, and it is worth pinning as such.

    A bar every ``s`` inches across a plane of area ``A`` is ``A/s`` of bar whichever way it
    runs — the run length cancels. That one expression serves a wall's verticals, a wall's
    horizontals, a footing's transverse mat and a slab's mat alike.

    The court's three retaining footings carry ``#6 @ 10"`` top AND bottom, so their #6 is
    exactly twice their #4 @ 18" bottom-only mat scaled by the spacing ratio: (2 / (10/12))
    against (1 / (18/12)), i.e. 3.6x.
    """
    six = _row(rows, "#6", "footing")
    four = _row(rows, "#4", "footing")
    assert six["length_ft"] / four["length_ft"] == pytest.approx(3.6, rel=0.01)


def test_weight_is_the_astm_unit_mass(rows) -> None:
    """Steel is bought by the pound, so the pound is what the row has to carry."""
    from typehaus.model.rebar import BARS

    for row in rows:
        number = int(str(row["bar"]).lstrip("#"))
        assert row["weight_lb"] == pytest.approx(
            row["length_ft"] * BARS[number].weight_plf, rel=0.001)


def test_the_coating_comes_from_the_pours_mix_not_the_schedule(rows) -> None:
    """A coating is a property of the bar you BUY for a pour, not of a role within it.

    You do not order galvanized verticals and black ties for one cage — a house that tried
    would be specifying a corrosion cell. So it lives on ``ConcreteSpec`` and every row of a
    pour inherits it, which is also what makes ``#5:hdg-a767`` a price key worth having.
    """
    assert {row["coating"] for row in rows} == {"hdg-a767"}


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


def test_dowels_are_not_billed(catlin_model) -> None:
    """A dowel's length is a lap into the pour below, and nothing in this model carries it.

    Billing it at the member's own height would be inventing a number, which is worse than
    the hole it fills.
    """
    from typehaus.model.rebar import BarSpec
    from typehaus.quantities import inch
    from typehaus.takeoff.reinforcement import _spaced_length_ft

    dowel = BarSpec(role="dowels", bar=5, spacing=inch(12.0))
    assert _spaced_length_ft(dowel, 1000.0) == 0.0


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

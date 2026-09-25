"""The courtyard study prices each variant's own resolved model, from the house's prices."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import typehaus.engineering.retaining_court as study_package
from typehaus.cli.retaining_court_costs import price_variants
from typehaus.engineering.retaining_court.report import write_study

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


def test_the_engineering_study_ships_no_dollar_figure() -> None:
    """Decision #28: no numeric literal may be handed to a CostRange inside the engine."""

    for path in Path(study_package.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "CostRange":
                literal = [arg for arg in node.args
                           if isinstance(arg, ast.Constant) and arg.value not in (0, 0.0)]
                assert not literal, f"{path.name}:{node.lineno} ships a price"


def test_a_house_without_prices_is_reported_unpriced(tmp_path: Path) -> None:
    assert price_variants(tmp_path) is None
    report = write_study(tmp_path / "study").read_text(encoding="utf-8")
    assert "no `prices.toml`" in report
    assert "| reference | unpriced |" in report
    assert "$" not in report.split("## Common-structure comparison")[1].split("## Does")[0]


@pytest.fixture(scope="module")
def catlin_costs():
    priced = price_variants(CATLIN)
    assert priced is not None
    return priced


def _line(priced, variant: str, section: str):
    return next(line for line in priced.lines[variant] if line.item == section)


def test_every_declared_variant_is_priced_from_its_own_model(catlin_costs) -> None:
    from typehaus.diff.variants import load_variants

    assert set(catlin_costs.lines) == {spec.name for spec in load_variants(CATLIN)}
    reference = _line(catlin_costs, "reference", "railings")
    # The against-wall guard is real railing in that variant's model, not a formula.
    assert _line(catlin_costs, "against-wall-24-brick", "railings").quantity != reference.quantity
    # Removing the terrace removes block wall; the setback ring adds more than it had.
    ref_wall = _line(catlin_costs, "reference", "wall structure").installed.low
    assert _line(catlin_costs, "yard-grade-brick", "wall structure").installed.low < ref_wall
    assert _line(catlin_costs, "setback-24-brick", "wall structure").installed.low > ref_wall
    # The cladding swap reaches the walkout wall, so the two finishes price differently.
    brick = _line(catlin_costs, "yard-grade-brick", "wall structure").installed
    screen = _line(catlin_costs, "yard-grade-fiber-cement", "wall structure").installed
    assert screen != brick


def test_whole_site_allowances_stay_outside_the_deltas(catlin_costs) -> None:
    keys = [key for key, _ in catlin_costs.allowances]
    assert "site-excavation-sunken-garden-drained-backfill" in keys
    assert all("court" in key or "sunken-garden" in key for key in keys)

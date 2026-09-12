"""A bid package is an unpriced per-trade view of the BOM (decision #71).

    .venv/bin/python -m pytest packages/engine/tests/test_bid_packages.py --bless

rewrites the framing golden from the current build; read the diff before committing it.
"""

from __future__ import annotations

import filecmp
import json
import subprocess
import sys
from pathlib import Path

import pytest
from _helpers import CATLIN, REPO_ROOT
from typer.testing import CliRunner

from typehaus.cli.app import app
from typehaus.cli.prices import ESTIMATE_PLANS
from typehaus.emit.trades import TRADES
from typehaus.takeoff.bid_package import build_bid_packages, is_mirrored
from typehaus.takeoff.bid_recipes import RECIPES, SHAPES, _validate
from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.bom_walk import walk_bom
from typehaus.takeoff.labels import LabelIndex

GOLDEN = REPO_ROOT / "packages" / "engine" / "tests" / "fixtures" / "bid_goldens" / "framing.md"
runner = CliRunner()


def test_every_recipe_and_shape_names_a_real_section_and_trade() -> None:
    _validate()
    sections = {plan[0] for plan in ESTIMATE_PLANS}
    assert set(SHAPES) <= sections
    assert set(RECIPES) <= TRADES
    for recipe in RECIPES.values():
        assert set(recipe.section_order) <= sections


@pytest.fixture(scope="module")
def packages(catlin_model):
    bom = bill_of_materials(catlin_model)
    labels = LabelIndex.from_plan(catlin_model.plan)
    return bom, build_bid_packages(catlin_model, bom, labels=labels)


def test_every_bom_row_lands_in_exactly_one_package(packages) -> None:
    """Every walked row is in exactly one package, except the solids whose product is
    billed in a dedicated section (a pipe's volume beside the pipe by the foot) and the
    unresolved floor-finish row — those are left out on purpose, never doubled."""
    bom, built = packages
    walked = [(item.section, item.qualified_key) for item in walk_bom(bom)
              if not is_mirrored(item)]
    placed = [(line.section, line.key) for p in built.values() for line in p.lines]
    assert sorted(placed) == sorted(walked)
    assert set(built) <= TRADES
    mirrored = [item for item in walk_bom(bom) if is_mirrored(item)]
    assert mirrored and all(item.section in ("concrete", "floor_finishes") for item in mirrored)


def test_quantities_take_the_unit_a_sub_quotes_in(packages) -> None:
    """audit:2026-09-12 — a wood beam is board feet, brick is wall face, a PV module is a
    module, a truss is a truss, aggregate under the green is a yard."""
    _bom, built = packages
    by_key = {(line.section, line.key): line for p in built.values() for line in p.lines}
    assert by_key[("concrete", "beam:BEAM_KDAT")].unit == "bf"
    assert by_key[("wall_structure", "BASEMENT_BRICK_VENEER:brown-brick")].unit == "SF"
    assert by_key[("solar_modules", "Aptos 440 W module, 69.4 x 44.6 x 1.2 in")].unit == "ea"
    assert by_key[("framing", "24 roof truss")].unit == "ea"
    assert by_key[("envelope_layers", "usga-choker-sand:2.0")].unit == "cy"
    footing = next(line for line in built["concrete"].lines if line.key.startswith("footing"))
    assert footing.unit == "cy"
    assert by_key[("concrete", "slab:SG_FROST_WING_XPS1")].unit == "SF"
    assert any(line.key == "slab:SG_FROST_WING_XPS1" for line in built["concrete"].lines)
    assert ("concrete", "pipe_drain") not in by_key


def test_unpriced_by_default_and_priced_needs_an_estimate(packages, catlin_model) -> None:
    _bom, built = packages
    for package in built.values():
        assert not package.priced
        assert all(line.total is None and line.unit_price is None for line in package.lines)
        assert "total" not in package.as_dict()
    with pytest.raises(ValueError):
        build_bid_packages(catlin_model, bill_of_materials(catlin_model), priced=True)


def test_the_framing_package_reads_as_a_cut_list(packages) -> None:
    _bom, built = packages
    framing = built["framing"]
    assert framing.groups[0].section == "framing"
    lumber = framing.groups[0].lines
    assert any("pcs" in line.detail for line in lumber)
    assert all("(" in line.description for line in lumber)
    assert "S-100" in framing.sheets


def _strip_hash(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("**Model hash:**"))


def test_framing_golden(request, tmp_path: Path) -> None:
    out = tmp_path / "framing.md"
    result = runner.invoke(app, ["bids", str(CATLIN), "--trade", "framing", "--md", str(out)])
    assert result.exit_code == 0, result.output
    rendered = out.read_text(encoding="utf-8")
    if request.config.getoption("--bless"):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(rendered, encoding="utf-8")
        pytest.skip("blessed the framing bid golden")
    assert GOLDEN.exists(), "no golden yet — run with --bless"
    assert _strip_hash(rendered) == _strip_hash(GOLDEN.read_text(encoding="utf-8"))


def test_all_is_byte_deterministic(tmp_path: Path) -> None:
    for name in ("a", "b"):
        result = subprocess.run([sys.executable, "-m", "typehaus.cli.app", "bids", str(CATLIN),
                                 "--all", "--out", str(tmp_path / name)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    match, mismatch, errors = filecmp.cmpfiles(
        tmp_path / "a", tmp_path / "b", [p.name for p in (tmp_path / "a").iterdir()],
        shallow=False)
    assert not mismatch and not errors, (mismatch, errors)
    manifest = json.loads((tmp_path / "a" / "MANIFEST.json").read_text())
    assert "framing.md" in manifest["files"] and "README.md" in manifest["files"]


def test_priced_is_refused_without_prices(starter_dir: Path) -> None:
    result = runner.invoke(app, ["bids", str(starter_dir), "--priced"])
    assert result.exit_code == 2

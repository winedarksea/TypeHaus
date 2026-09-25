"""The SolidCategory registry covers everything the reference houses mint."""

from __future__ import annotations

import pytest

from typehaus.emit.trades import (
    PIPE_ACCESSORY_CATEGORIES,
    ROUTED_RUN_CATEGORIES,
    TRADES,
)
from typehaus.resolve.solid_categories import SOLID_CATEGORIES, solid_category


@pytest.fixture(scope="module")
def starter_model(starter_dir):
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _findings = resolve(load_plan(starter_dir).plan)
    return model


def _minted(model) -> set[str]:
    kinds = {element.kind for element in model.geometry.elements}
    return {solid.category for solid in model.solids} | kinds


def test_every_category_catlin_mints_is_registered(catlin_model_ro):
    missing = sorted(_minted(catlin_model_ro) - set(SOLID_CATEGORIES))
    assert not missing, f"unregistered solid categories / IR kinds: {missing}"


def test_every_category_starter_mints_is_registered(starter_model):
    missing = sorted(_minted(starter_model) - set(SOLID_CATEGORIES))
    assert not missing, f"unregistered solid categories / IR kinds: {missing}"


def test_every_trade_is_a_trade():
    bad = {row.name: row.trade for row in SOLID_CATEGORIES.values()
           if row.trade is not None and row.trade not in TRADES}
    assert not bad


def test_enum_derived_categories_are_registered():
    assert not (ROUTED_RUN_CATEGORIES | PIPE_ACCESSORY_CATEGORIES) - set(SOLID_CATEGORIES)


def test_an_unknown_category_raises():
    with pytest.raises(KeyError):
        solid_category("no_such_category")


def test_ifc_emit_raises_on_an_unregistered_or_classless_category():
    from typehaus.emit.ifc.structural import _solid_ifc

    with pytest.raises(KeyError):
        _solid_ifc("no_such_category")
    with pytest.raises(ValueError):
        _solid_ifc("pipe_drain")  # a routed run: exported as segments, never as a solid


def test_non_solid_kinds_have_no_solid_trade():
    from typehaus.emit.trades import SOLID_CATEGORY_TRADE

    non_solid = {row.name for row in SOLID_CATEGORIES.values() if row.non_solid}
    assert {"wall", "floor", "roof", "earth", "framing", "solar_panel"} <= non_solid
    assert not non_solid & set(SOLID_CATEGORY_TRADE)

"""WWR's south-overhang check reads the roof edge that faces TRUE south (decision #153)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.building_science.wwr import _adequate_south_overhang
from typehaus.checks.registry import Preferences
from typehaus.model.spatial import Roof
from typehaus.quantities import deg, ft


def _ctx(roof: Roof, true_north_deg: float) -> SimpleNamespace:
    site = SimpleNamespace(true_north=deg(true_north_deg))
    plan = SimpleNamespace(project=SimpleNamespace(site=site), all_elements=lambda: [roof])
    return SimpleNamespace(plan=plan, preferences=Preferences())


def _roof(**fields) -> Roof:
    return Roof.model_construct(**{"overhang": None, "edge_overhangs": (), **fields})


@pytest.mark.parametrize(("theta", "roof", "expected"), [
    (0, _roof(overhang=ft(3)), True),
    (0, _roof(overhang=ft(3), edge_overhangs=(("south", ft(0)),)), False),
    (0, _roof(overhang=ft(0), edge_overhangs=(("north", ft(4)),)), False),
    (0, _roof(edge_overhangs=(("south", ft(3)),)), True),
    # Turned 180 deg, project north faces true south.
    (180, _roof(overhang=ft(0), edge_overhangs=(("north", ft(4)),)), True),
    (180, _roof(overhang=ft(3), edge_overhangs=(("north", ft(0)),)), False),
])
def test_only_the_true_south_edge_counts(theta, roof, expected) -> None:
    assert _adequate_south_overhang(_ctx(roof, theta)) is expected

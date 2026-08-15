"""`retype_placeable` — type swap that keeps the wall-mounted face seated (2026-07-31).

The 2026-07-30 shower→tub-shower hand edit showed what a bare type_ref PATCH misses:
position is the footprint *center*, so a footprint change un-seats a wall-backed unit,
and every authored reference to the tag (serves lists, sleeves, slices) was sized
against the old type. The macro re-anchors the back face and surfaces the references
as warnings. Out of scope, deliberately: tag renames, catalog edits, rewriting
dependent diameters, alcove re-centring.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.macros import MacroError, retype_placeable
from _helpers import CATLIN as CATLIN_DIR, copy_house



@pytest.fixture(scope="module")
def catlin_plan():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None
    return result.plan


def _fixture(plan, tag):
    return next(e for e in plan.all_elements() if getattr(e, "tag", None) == tag)


def test_retype_holds_the_mounted_back_face(catlin_plan):
    """FX-M-BATH2-SH 36"x36" → 60"x30": the back (local +y) face must not move, so the
    center shifts by (36-30)/2 = 3" along the back direction."""
    result = retype_placeable(catlin_plan, "main", tag="FX-M-BATH2-SH",
                              type_ref="FX-TUBSHOWER-60")
    (op,) = result.ops
    assert op.fields["type_ref"] == "FX-TUBSHOWER-60"
    # rotation is unauthored (0): back is +y, old back at y + 18", new depth 30" — the
    # center must land 3" further +y so the new back face sits at the same coordinate
    # (the exact coordinates are asserted through the source round-trip below).
    assert op.fields["position"].expr.startswith("pt(")
    assert any("re-anchored" in w for w in result.warnings)


def test_retype_round_trips_through_source_and_reseats_the_back_face(tmp_path):
    house = tmp_path / "catlin"
    copy_house(CATLIN_DIR, house)
    plan = load_plan(house).plan
    shower = _fixture(plan, "FX-M-BATH2-SH")
    x, y = shower.position.xy_m
    old_back_y = y + 0.9144 / 2.0
    result = retype_placeable(plan, "main", tag="FX-M-BATH2-SH",
                              type_ref="FX-TUBSHOWER-60")
    coordinator = ProjectCoordinator(house)
    coordinator.apply_patch(result.ops, coordinator.revision())
    reloaded = load_plan(house)
    assert reloaded.plan is not None, [f.message for f in reloaded.findings]
    swapped = _fixture(reloaded.plan, "FX-M-BATH2-SH")
    assert swapped.type_ref == "FX-TUBSHOWER-60"
    new_x, new_y = swapped.position.xy_m
    assert new_x == pytest.approx(x, abs=1e-6)
    assert new_y + 0.762 / 2.0 == pytest.approx(old_back_y, abs=2e-4)  # 1/16" grid snap


def test_retype_warns_about_every_authored_reference(catlin_plan):
    result = retype_placeable(catlin_plan, "main", tag="FX-M-BATH2-SH",
                              type_ref="FX-TUBSHOWER-60")
    text = "\n".join(result.warnings)
    # The DFU-bearing serves lists and the cast slab stub were authored against the 36"
    # shower — they keep pointing at the tag (no rename), but their sizing is up for
    # review, which is exactly what the warnings say.
    assert "PR-B-MAIN-DRAIN" in text
    assert "SP-" in text  # the slab stub via serves_fixture


def test_same_footprint_retype_moves_nothing(catlin_plan):
    """FX-TUB-60 and FX-TUBSHOWER-60 share a 5' x 2'-6" footprint: no re-anchor."""
    result = retype_placeable(catlin_plan, "main", tag="FX-M-BATH2-TUB",
                              type_ref="FX-TUBSHOWER-60")
    (op,) = result.ops
    assert "position" not in op.fields
    assert not any("re-anchored" in w for w in result.warnings)


def test_retype_rejects_an_unknown_type(catlin_plan):
    with pytest.raises(MacroError):
        retype_placeable(catlin_plan, "main", tag="FX-M-BATH2-SH", type_ref="FX-NOPE")

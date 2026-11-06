"""R602.7 header reads, oracled against ``houses/catlin/notes/header_spans_r602_7.md``."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.structural.header_spans import wall_role_load
from typehaus.findings import Result
from typehaus.model.enums import StructuralRole
from typehaus.model.framing_standards import HeaderStandard
from typehaus.resolve.framing.header_tables import (
    EXTERIOR_TABLE,
    INTERIOR_TABLE,
    ONE_CENTER_FLOOR,
    TWO_CENTER_FLOORS,
    TableCondition,
    header_row,
    row_for,
    table_condition,
)
from typehaus.resolve.framing.tables import header_profile_from_spec
from typehaus.resolve.header_loads import LoadIndex

_ONE = TableCondition(EXTERIOR_TABLE, ONE_CENTER_FLOOR, 36, 50)
_TWO = TableCondition(EXTERIOR_TABLE, TWO_CENTER_FLOORS, 36, 50)


def test_table_cells_match_the_oracle():
    assert row_for(_ONE, "2-2x8").span_in == 45 and row_for(_ONE, "2-2x8").jacks == 2
    assert row_for(_ONE, "2-2x8", unbraced=True).allowable_in == pytest.approx(31.5)
    assert row_for(_ONE, "2-2x6", unbraced=True).allowable_in == 36  # note f skips 2x6
    assert row_for(_TWO, "2-2x8").span_in == 39
    interior = TableCondition(INTERIOR_TABLE, "one_floor", 36)
    assert (row_for(interior, "2-2x8").span_in, row_for(interior, "2-2x8").jacks) == (53, 2)


def test_lookup_takes_the_smallest_row_at_or_above_the_minimum():
    def unbraced(size):
        return True
    assert header_row(_TWO, 27.5, 5.5, unbraced=unbraced).size == "2-2x6"
    lifted = header_row(_TWO, 27.5, 5.5, min_size="2-2x8", unbraced=unbraced)
    assert (lifted.size, lifted.jacks) == ("2-2x10", 3)  # 2-2x8 is 27.3" < 27.5"
    assert header_row(_ONE, 27.5, 5.5, min_size="2-2x8", unbraced=unbraced).size == "2-2x8"
    assert header_row(_ONE, 200.0, 5.5) is None


@pytest.mark.parametrize(("args", "expected"), [
    ((True, True, ("center",), 30.0, 50.0), (ONE_CENTER_FLOOR, 36, 50)),
    ((True, True, (), 12.0, 20.0), ("roof_ceiling", 12, 30)),  # note e
    ((True, True, ("center", "clear"), 36.0, 70.0), ("two_clear_floors", 36, 70)),
    ((False, False, ("center",), 24.0, 50.0), ("one_floor", 24, None)),
])
def test_table_condition_rounds_up(args, expected):
    condition = table_condition(*args)
    assert (condition.row, condition.width_ft, condition.snow_psf) == expected


@pytest.mark.parametrize("args", [
    (True, True, (), 37.0, 50.0), (True, True, (), 36.0, 80.0),
    (False, True, ("center",), 36.0, 50.0), (True, True, ("center",) * 3, 36.0, 50.0),
    (True, False, (), 36.0, 50.0),
])
def test_table_condition_refuses(args):
    assert isinstance(table_condition(*args), str)


def test_built_up_spec_and_standard():
    assert header_profile_from_spec("2-2x8") == "2-2x8"
    assert HeaderStandard(tag="H", min_bearing_header=" 2-2x8 ").min_bearing_header == "2-2x8"
    with pytest.raises(ValueError):
        HeaderStandard(tag="H", min_bearing_header="2x8")


def _condition(index, model, tag):
    opening = next(op for op in model.openings if op.tag == tag)
    half = opening.width_m / 2
    lo, hi = opening.center_along_m - half, opening.center_along_m + half
    if opening.pocket_run_m:
        hi += opening.pocket_run_m if opening.pocket_sign > 0 else 0.0
        lo -= opening.pocket_run_m if opening.pocket_sign < 0 else 0.0
    return index.condition(model.wall(opening.host_wall), lo, hi)


def test_catlin_oracle_conditions(catlin_plan, catlin_model_ro):
    index = LoadIndex.of(catlin_plan, catlin_model_ro)
    e1 = _condition(index, catlin_model_ro, "WIN-M-LIV-E1")
    assert e1.exterior and e1.roofs == ("RF-HOUSE",)
    # FS-ATTIC names W-S-E2, and its joists land on the whole x=36' line, W-S-E1 included.
    assert e1.floors == (("FS-S-EAST", "center"), ("FS-ATTIC", "center"))
    assert e1.building_width_m == pytest.approx(36 * 0.3048)
    bed1 = _condition(index, catlin_model_ro, "WIN-S-BED1")
    assert bed1.floors == (("FS-ATTIC", "center"),) and bed1.roofs == ("RF-HOUSE",)
    sauna = _condition(index, catlin_model_ro, "D-B-SAUNA")
    assert not sauna.exterior and sauna.roofs == ("RF-HOUSE",) and len(sauna.floors) == 3
    assert _condition(index, catlin_model_ro, "D-M-LAUN").point_loads == ("FO-A-HALL",)
    # The stair wells' trimmers land beside D-B-CLOSET's span, not across their holes.
    assert _condition(index, catlin_model_ro, "D-B-CLOSET").point_loads == ()


class _Unauthored:
    """``catlin_plan`` with W-M-N2 read back as NONBEARING."""

    def __init__(self, plan):
        self._plan = plan

    def by_tag(self, tag):
        element = self._plan.by_tag(tag)
        if tag == "W-M-N2":
            return SimpleNamespace(structural_role=StructuralRole.NONBEARING)
        return element

    def __getattr__(self, name):
        return getattr(self._plan, name)


def test_a_nonbearing_wall_carrying_a_stair_fails(catlin_plan, catlin_model_ro):
    findings = wall_role_load(SimpleNamespace(plan=_Unauthored(catlin_plan),
                                              model=catlin_model_ro))
    failed = [f for f in findings if f.result is Result.FAIL]
    assert [f.element_tags for f in failed] == [("W-M-N2",)]
    assert "ST-M2S" in failed[0].message

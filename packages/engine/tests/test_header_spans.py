"""R602.7 header reads, oracled against ``houses/catlin/notes/header_spans_r602_7.md``."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus.checks.structural.header_spans import published_read, wall_role_load
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
from typehaus.resolve.header_line_load import header_line_load
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
    # FO-A-HALL's trimmer lies on W-S-SN3 over W-M-HS3: a strip of FS-ATTIC, plus BM-S-BATH-E
    # hung in it at x=10'-0" — on D-M-LAUN's strike pack since 2026-11-07, not in its span.
    laundry = _condition(index, catlin_model_ro, "D-M-LAUN")
    assert laundry.floors == (("FS-ATTIC", "center"),) and laundry.point_loads == ()
    # FS-S-WEST's trusses run along the line and a truss deck gets no blocks: the squash block
    # and the authored 1 1/4" LSL strip carry it (decision 22).
    assert "on P-S-SN3-SQUASH, sister-0-0 in FS-S-WEST under W-S-SN3" in laundry.ladders
    hall = catlin_model_ro.wall("W-M-HS3")
    whole = index.condition(hall, 0.0, math.dist(*hall.axis))
    assert whole.point_loads == ("BM-S-BATH-E",)
    # A published row is read on the whole clear span, pocket cavity included (note §4b).
    door = next(o for o in catlin_model_ro.openings if o.tag == "D-M-LAUN")
    ctx = SimpleNamespace(plan=catlin_plan, model=catlin_model_ro)
    assert published_read(ctx, door, index) == (pytest.approx(74.5 / 12), ())
    # The stair wells' trimmers land beside D-B-CLOSET's span, not across their holes.
    assert _condition(index, catlin_model_ro, "D-B-CLOSET").point_loads == ()


def test_a_stair_ledger_is_a_strip_and_the_stack_reads_a_line_load(catlin_plan, catlin_model_ro):
    index = LoadIndex.of(catlin_plan, catlin_model_ro)
    niche = _condition(index, catlin_model_ro, "AO-M-FIRE-NICHE")
    assert niche.point_loads == () and niche.strips == ("ST-S2A",)
    # note §5b: 18' of roof and three floors, 288 plf of walls above: D + L governs.
    ctx = SimpleNamespace(plan=catlin_plan, model=catlin_model_ro)
    load = header_line_load(ctx, index, catlin_model_ro.wall("W-B-CS3"),
                            _condition(index, catlin_model_ro, "D-B-GYM"))
    assert (load.dead_plf, load.live_plf, load.snow_plf) == pytest.approx((1098, 2160, 630), abs=2)
    assert load.governing_plf == pytest.approx(3258, abs=2)


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

"""``WindowOperation`` is a closed vocabulary, and the catlin catalog respects it.

Windows carried a bare ``str`` operation with the vocabulary written out in a comment, so a
typo ("cassement") or a plausible-but-unmodeled value ("jalousie") authored in a house's
plan reached the plan symbol and the schedule unchallenged and simply drew nothing. Typing
the field turns that into a load error at authoring time — this test pins the guarantee, and
pins the split between a picture unit and an operable one of identical size, which is the
distinction that has no other representation in the model.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.model.enums import WindowOperation
from typehaus.model.types import WindowType
from typehaus.quantities import ft
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



@pytest.fixture(scope="module")
def catlin_plan():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None, [f.message for f in result.findings]
    return result.plan


def test_every_catlin_window_type_declares_a_modeled_operation(catlin_plan):
    window_types = catlin_plan.library.window_types
    assert window_types, "the catlin catalog must declare window types"
    for window_type in window_types:
        assert isinstance(window_type.operation, WindowOperation), (
            f"{window_type.tag} operation {window_type.operation!r} is not a modeled "
            "WindowOperation member"
        )


def test_catlin_carries_a_fixed_picture_unit_alongside_its_operable_twin(catlin_plan):
    by_tag = {wt.tag: wt for wt in catlin_plan.library.window_types}
    fixed = by_tag["WT-3660-FIX"]
    operable = by_tag["WT-3660"]
    assert fixed.operation is WindowOperation.FIXED
    assert operable.operation is WindowOperation.CASEMENT
    # Same hole, same glass: only the operation differs, which is exactly why the fixed unit
    # has to be its own type rather than a note on the casement.
    assert (fixed.width, fixed.height) == (operable.width, operable.height)
    assert (fixed.u_factor, fixed.shgc, fixed.vt) == (operable.u_factor, operable.shgc,
                                                      operable.vt)


def test_window_operation_coerces_authored_strings_and_rejects_unmodeled_ones():
    # Plan source authors bare strings (and the value crosses model.json as one), so the
    # str mixin has to survive the round trip in both directions.
    coerced = WindowType(tag="WT-TEST", width=ft(3), height=ft(5), operation="awning")
    assert coerced.operation is WindowOperation.AWNING
    assert coerced.operation == "awning"
    # A window with no stated operation is a picture unit — the conservative default, since
    # it claims neither ventilation nor egress.
    assert WindowType(tag="WT-TEST", width=ft(3), height=ft(5)).operation is WindowOperation.FIXED
    with pytest.raises(Exception):
        WindowType(tag="WT-TEST", width=ft(3), height=ft(5), operation="jalousie")


def test_the_attic_juliet_pair_is_a_casement_and_not_an_awning(catlin_plan):
    by_tag = {wt.tag: wt for wt in catlin_plan.library.window_types}
    juliet = by_tag["WT-1864"]
    # The pair's whole premise is a sash that swings like a door leaf; an awning (bottom-hung
    # only) would open the head and nothing else, which is not the same window. It was a
    # TILT_TURN for the few hours the pair was 32" wide — narrowing the RO to 18" put it
    # under the ~500 mm minimum frame that hardware line is made in, and a casement leaf is
    # what a juliet unit is anyway.
    assert juliet.operation is WindowOperation.CASEMENT
    assert juliet.operation == "casement"


def test_tilt_turn_is_a_modeled_operation_even_with_no_current_placement():
    # No catlin type carries it today (see above), but the member is the vocabulary's only
    # dual-axis entry — it is what an authored "tilt_turn" has to coerce to rather than
    # failing the closed-vocabulary check, and dropping it would silently reject valid source.
    unit = WindowType(tag="WT-TEST", width=ft(2, 8), height=ft(6, 4), operation="tilt_turn")
    assert unit.operation is WindowOperation.TILT_TURN
    assert unit.operation == "tilt_turn"

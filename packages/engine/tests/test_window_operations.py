"""``WindowOperation`` is a closed vocabulary, and the catlin catalog respects it.

Windows carried a bare ``str`` operation with the vocabulary written out in a comment, so a
typo ("cassement") or a plausible-but-unmodeled value ("jalousie") authored in a house's
plan reached the plan symbol and the schedule unchallenged and simply drew nothing. Typing
the field turns that into a load error at authoring time — this test pins the guarantee, and
pins the split between a picture unit and an operable one of identical size, which is the
distinction that has no other representation in the model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from typehaus import Window
from typehaus.model.enums import WindowOperation
from typehaus.model.types import WindowType
from typehaus.quantities import ft


# ``catlin_plan`` is conftest's session fixture; this module shadowed it with an
# identical module-scoped load.
def test_every_catlin_window_type_declares_a_modeled_operation(catlin_plan):
    window_types = catlin_plan.library.window_types
    assert window_types, "the catlin catalog must declare window types"
    for window_type in window_types:
        assert isinstance(window_type.operation, WindowOperation), (
            f"{window_type.tag} operation {window_type.operation!r} is not a modeled "
            "WindowOperation member"
        )


@pytest.mark.parametrize("fixed_tag, operable_tag", [
    ("WT-3660-FIX", "WT-3660"),
    ("WT-1424-FIX", "WT-1424"),
    ("WT-1424-FIX-T", "WT-1424-T"),
    ("WT-2736-FIX", "WT-2736"),
    ("WT-2736-FIX-T", "WT-2736-T"),
    ("WT-2748-FIX-T", "WT-2748-T"),
])
def test_catlin_carries_a_fixed_picture_unit_alongside_its_operable_twin(
    catlin_plan, fixed_tag, operable_tag,
):
    by_tag = {wt.tag: wt for wt in catlin_plan.library.window_types}
    fixed = by_tag[fixed_tag]
    operable = by_tag[operable_tag]
    assert fixed.operation is WindowOperation.FIXED
    assert operable.operation in (WindowOperation.CASEMENT, WindowOperation.AWNING)
    # Same hole, same glass: only the operation differs, which is exactly why the fixed unit
    # has to be its own type rather than a note on the casement.
    assert (fixed.width, fixed.height) == (operable.width, operable.height)
    assert fixed.tempered == operable.tempered
    assert fixed.frame_depth == operable.frame_depth
    assert (fixed.u_factor, fixed.shgc, fixed.vt) == (operable.u_factor, operable.shgc,
                                                      operable.vt)


def test_catlin_picture_window_selection_preserves_the_operable_exceptions(catlin_plan):
    window_types = {
        window_type.tag: window_type for window_type in catlin_plan.library.window_types
    }
    windows = {
        element.tag: element for element in catlin_plan.all_elements()
        if isinstance(element, Window)
    }
    selected_picture_windows = {
        "WIN-S-STAIR-N": "WT-2748-FIX-T",
        "WIN-A-N1": "WT-2736-FIX",
        "WIN-A-S2": "WT-1424-FIX",
        "WIN-A-S3": "WT-1424-FIX",
        "WIN-M-BATH2": "WT-2736-FIX-T",
    }
    for tag, type_ref in selected_picture_windows.items():
        assert windows[tag].type_ref == type_ref, tag
        assert window_types[type_ref].operation is WindowOperation.FIXED, tag

    for window in windows.values():
        window_type = window_types[window.type_ref]
        if window_type.width.inches == 14 and window_type.height.inches == 24:
            expected_operation = (
                WindowOperation.AWNING
                if window.tag in {"WIN-M-KITCH-N", "WIN-M-KIT-E"}
                else WindowOperation.FIXED
            )
            assert window_type.operation is expected_operation, window.tag

    # The mudroom was already fixed; the bedroom's larger north unit still opens.
    assert windows["WIN-M-MUD"].type_ref == "WT-1424-FIX"
    for tag in ("WIN-M-KITCH", "WIN-A-N2"):
        assert window_types[windows[tag].type_ref].operation is WindowOperation.TILT_TURN, tag
    for tag in ("WIN-S-HALL-N", "WIN-S-BED1", "WIN-S-BED2"):
        assert window_types[windows[tag].type_ref].operation is WindowOperation.CASEMENT, tag


def test_window_operation_coerces_authored_strings_and_rejects_unmodeled_ones():
    # Plan source authors bare strings (and the value crosses model.json as one), so the
    # str mixin has to survive the round trip in both directions.
    coerced = WindowType(tag="WT-TEST", width=ft(3), height=ft(5), operation="awning")
    assert coerced.operation is WindowOperation.AWNING
    assert coerced.operation == "awning"
    # A window with no stated operation is a picture unit — the conservative default, since
    # it claims neither ventilation nor egress.
    assert WindowType(tag="WT-TEST", width=ft(3), height=ft(5)).operation is WindowOperation.FIXED
    with pytest.raises(ValidationError):
        WindowType(tag="WT-TEST", width=ft(3), height=ft(5), operation="jalousie")


# Every window a sleeping room relies on for R310 escape (notes/window_procurement.md §7).
EGRESS_CASEMENTS = (
    "WIN-M-BED-S1", "WIN-M-BED-S2", "WIN-S-BED1", "WIN-S-BED2", "WIN-S-HALL-N",
    "WIN-S-SUITE1", "WIN-S-SUITE2", "WIN-A-S-JUL-W", "WIN-A-S-JUL-E",
)


def test_catlin_egress_windows_are_casements_and_the_rest_tilt_turn(catlin_plan):
    # 2026-10-21: the casements went tilt-turn for import, then the egress set came back. A
    # 27" tilt-turn nets ~18" clear at a Euro sightline and R310 wants 20"; a US egress-hinge
    # casement nets ~20 3/4". The 14" kitchen pair stays an outward awning.
    window_types = {wt.tag: wt for wt in catlin_plan.library.window_types}
    operations = {
        element.tag: window_types[element.type_ref].operation
        for element in catlin_plan.all_elements() if isinstance(element, Window)
    }
    casements = {tag for tag, op in operations.items() if op is WindowOperation.CASEMENT}
    assert casements == set(EGRESS_CASEMENTS)
    assert sum(op is WindowOperation.TILT_TURN for op in operations.values()) == 11
    assert {tag for tag, op in operations.items() if op is WindowOperation.AWNING} == {
        "WIN-M-KITCH-N", "WIN-M-KIT-E"}


def test_tilt_turn_coerces_from_authored_source():
    # The vocabulary's only dual-axis entry: an authored "tilt_turn" must coerce to it.
    unit = WindowType(tag="WT-TEST", width=ft(2, 8), height=ft(6, 4), operation="tilt_turn")
    assert unit.operation is WindowOperation.TILT_TURN
    assert unit.operation == "tilt_turn"

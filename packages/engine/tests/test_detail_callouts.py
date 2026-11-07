"""Detail cross-references: the callout and the title bubble (→ 30 §Graphics).

A set with 76 detail sheets and no reference to any of them is a set of unrelated
drawings, which is what this one was. The cross-reference is a matched pair and both
halves have to exist: a callout on the drawing where the condition IS, saying which sheet
draws it, and a number on the detail sheet itself so a reader holding that sheet can say
which one it is.
"""

from __future__ import annotations

from typehaus.emit.draw.callouts import (
    CALLOUT_LAYER,
    DERIVED_SERIES,
    FIRST_DETAIL_SHEET,
    detail_sheet_numbers,
    sheet_sort_key,
)
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.section import build_center_section


def test_the_two_numberings_agree(catlin_model_ro, catlin_sheet_index):
    """The load-bearing assertion in this module.

    ``callouts.detail_sheet_numbers`` cannot import ``build_sheet_index`` — ``sheets``
    imports every scene builder, so a scene builder importing it back is a cycle — so the
    mapping is DERIVED TWICE from the same input. This is what stops the two drifting: a
    callout naming a sheet the set does not emit is worse than no callout.
    """
    derived = detail_sheet_numbers(catlin_model_ro)
    index = [s.number for s in catlin_sheet_index(sets="full")
             if s.number.startswith(f"A-{FIRST_DETAIL_SHEET // 100}")]
    # An enlarged head/sill (A-560.1.1) is a sub-sheet of its detail, never a callout target.
    details = [n for n in index if "." not in n or n.rsplit(".", 1)[0] not in set(index)]
    assert sorted(derived.values(), key=sheet_sort_key) == details


def test_details_number_by_family_with_headroom(catlin_model_ro):
    """Every condition kind has its own series, so the block cannot fill again (it did at
    A-599 when every detail took a whole number)."""
    from typehaus.model.enums import ConditionKind

    assert set(DERIVED_SERIES) == set(ConditionKind)
    numbers = list(detail_sheet_numbers(catlin_model_ro).values())
    assert all(n.startswith("A-5") for n in numbers)
    assert numbers == sorted(numbers, key=sheet_sort_key)


def test_a_detail_keeps_its_number_in_both_sets(catlin_sheet_index):
    """Every detail is numbered before the set filter, so the permit set drops sheets
    without renumbering the ones it keeps. A callout pointing at A-540.4 must not move
    because an unstarred sheet ahead of it was filtered out."""
    full = {s.number: s.title for s in catlin_sheet_index(sets="full")}
    for sheet in catlin_sheet_index(sets="permit"):
        assert full[sheet.number] == sheet.title


def test_the_section_calls_out_the_details_it_passes_through(catlin_model_ro,
                                                            catlin_sheet_index):
    scene = build_center_section(catlin_model_ro)
    texts = [n.content for n in scene.nodes
             if isinstance(n, Text) and n.layer == CALLOUT_LAYER]
    pairs = list(zip(texts[::2], texts[1::2]))  # (number, sheet) per bubble
    assert pairs, "the building section references no detail at all"
    emitted = {s.number for s in catlin_sheet_index()}
    # "1 over A-501" is sheet A-501; "4 over A-540" is series member A-540.4.
    dangling = [p for p in pairs if len({p[1], f"{p[1]}.{p[0]}"} & emitted) != 1]
    assert not dangling, f"callouts point at sheets that do not exist: {dangling}"


def test_a_callout_is_a_polyline_and_never_a_symbol(catlin_model_ro):
    """``plan_marks`` documents why: both writers dispatch Symbol off a closed vocabulary
    and an unlisted name falls through and renders as a window glass bar."""
    scene = build_center_section(catlin_model_ro)
    on_layer = [n for n in scene.nodes if getattr(n, "layer", "") == CALLOUT_LAYER]
    assert on_layer
    assert all(isinstance(n, (Polyline, Text)) for n in on_layer)


def test_callouts_do_not_overprint_each_other(catlin_model_ro):
    from typehaus.emit.draw.callouts import bubble_radius_in
    from typehaus.emit.draw.section import _CALLOUT_MIN_GAP_IN

    scene = build_center_section(catlin_model_ro)
    scale = scene.frame.scale if scene.frame is not None else None
    assert 2 * bubble_radius_in(scale) <= _CALLOUT_MIN_GAP_IN
    centres = [n.anchor for n in scene.nodes
               if isinstance(n, Text) and n.layer == CALLOUT_LAYER
               and n.content.startswith("A-")]
    # A series member reads "4 over A-540" for A-540.4, so the bubble stays five wide.
    assert all(len(n.content) <= 5 for n in scene.nodes
               if isinstance(n, Text) and n.layer == CALLOUT_LAYER)
    for i, a in enumerate(centres):
        for b in centres[i + 1:]:
            assert abs(a[0] - b[0]) >= _CALLOUT_MIN_GAP_IN - 1e-6 \
                or abs(a[1] - b[1]) >= _CALLOUT_MIN_GAP_IN - 1e-6


def test_every_detail_sheet_says_which_sheet_it_is(catlin_model_ro):
    """The other half of the pair, read off a real detail scene."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    numbers = detail_sheet_numbers(catlin_model_ro)
    derived = next(d for d in derive_detail_slices(catlin_model_ro)
                   if d.key == "wall_roof:EXT_2X6|ROOF")
    scene, _ = build_detail(catlin_model_ro, derived)
    printed = {n.content for n in scene.nodes if isinstance(n, Text)}
    assert f"SHEET {numbers[derived.key]}" in printed

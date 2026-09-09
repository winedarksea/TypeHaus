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
    FIRST_DETAIL_SHEET,
    detail_sheet_numbers,
)
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.section import build_center_section
from typehaus.emit.draw.sheets import build_sheet_index


def test_the_two_numberings_agree(catlin_model_ro):
    """The load-bearing assertion in this module.

    ``callouts.detail_sheet_numbers`` cannot import ``build_sheet_index`` — ``sheets``
    imports every scene builder, so a scene builder importing it back is a cycle — so the
    mapping is DERIVED TWICE from the same input. This is what stops the two drifting: a
    callout naming a sheet the set does not emit is worse than no callout.
    """
    derived = detail_sheet_numbers(catlin_model_ro)
    index = [s.number for s in build_sheet_index(catlin_model_ro, sets="full")
             if s.number.startswith(f"A-{FIRST_DETAIL_SHEET // 100}")]
    assert sorted(derived.values()) == sorted(index)


def test_a_detail_keeps_its_number_in_both_sets(catlin_model_ro):
    """``FIRST_DETAIL_SHEET`` numbers EVERY derived detail, so the permit set drops sheets
    without renumbering the ones it keeps. A callout pointing at A-560 must not move
    because an unstarred sheet ahead of it was filtered out."""
    full = {s.number: s.title for s in build_sheet_index(catlin_model_ro, sets="full")}
    for sheet in build_sheet_index(catlin_model_ro, sets="permit"):
        assert full[sheet.number] == sheet.title


def test_the_section_calls_out_the_details_it_passes_through(catlin_model_ro):
    scene = build_center_section(catlin_model_ro)
    sheets = {n.content for n in scene.nodes
              if isinstance(n, Text) and n.layer == CALLOUT_LAYER
              and n.content.startswith("A-")}
    assert sheets, "the building section references no detail at all"
    emitted = {s.number for s in build_sheet_index(catlin_model_ro)}
    assert sheets <= emitted, f"callouts point at sheets that do not exist: {sheets - emitted}"


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

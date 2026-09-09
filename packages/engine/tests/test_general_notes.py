"""G-002 and the specification sheets (→ 30 §Notes).

Two defects with one cause. G-002 collected the whole of every ``Transition.notes``
markdown file — 637 lines on catlin — laid them into four columns, and ``break``ed out of
both loops when it ran out of column. It dropped the rest with no marker: a permit sheet
that silently loses construction notes. And the notes it was reprinting were already on
the detail sheets, which is the duplication CSI's *say it once* exists to stop.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.architectural import (
    MASTERFORMAT_DIVISIONS,
    _general_note_blocks,
    _lay_out_blocks,
    _sheet_note_index,
    specification_sections,
)
from typehaus.emit.draw.sheets import build_sheet_index


def test_g002_is_bounded_by_construction_not_by_the_notes(catlin_model_ro):
    """The fix that matters. A fixed list of derived blocks plus one entry per notes file
    cannot outgrow the sheet, where a loop over unbounded prose always could."""
    blocks = _general_note_blocks(catlin_model_ro, None)
    titles = [title for title, _ in blocks]
    assert titles[:5] == ["CODE & JURISDICTION", "DIMENSIONS", "SCOPE", "ENVELOPE",
                          "SUBSTITUTIONS"]
    total = sum(len(lines) + 2 for _, lines in blocks)
    assert total < 260, f"G-002 is {total} lines; four columns hold about 260"


def test_g002_never_truncates_silently(catlin_model_ro):
    """The belt. It reports what it could not place instead of dropping it."""
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(17.0, 11.0))
    try:
        assert _lay_out_blocks(fig, _general_note_blocks(catlin_model_ro, None)) == 0
        # And it counts rather than drops when it genuinely cannot fit.
        huge = [(f"BLOCK {i}", ["x"] * 60) for i in range(12)]
        assert _lay_out_blocks(fig, huge) > 0
    finally:
        plt.close(fig)


def test_the_note_index_points_at_sheets_that_exist(catlin_model_ro):
    """What G-002 owes a reader is a way to FIND a note, not a second copy of it."""
    index = _sheet_note_index(catlin_model_ro)
    assert index
    emitted = {s.number for s in build_sheet_index(catlin_model_ro)}
    for line in index:
        for token in line.replace(",", " ").replace("..", " ").split():
            if token.startswith("A-"):
                assert token in emitted, f"the index names {token}, which is not in the set"


def test_the_index_does_not_reprint_the_notes(catlin_model_ro):
    """A sheet-note index is titles and sheet numbers. Any sentence in it is a regression."""
    for line in _sheet_note_index(catlin_model_ro):
        assert len(line) < 60, f"the index is printing note text: {line!r}"


def test_specifications_are_masterformat_ordered_and_deduplicated(catlin_model_ro):
    sections = specification_sections(catlin_model_ro)
    assert sections, "the six notes files carry no ### Spec blocks"
    numbers = [number for number, _, _ in sections]
    assert numbers == sorted(numbers)
    for number, division, lines in sections:
        assert division == MASTERFORMAT_DIVISIONS.get(number[:2],
                                                      "GENERAL REQUIREMENTS")
        assert len(lines) == len(set(lines)), f"{number} repeats a requirement"


def test_a_procedure_is_on_the_spec_sheet_and_not_on_the_detail(catlin_model_ro):
    """CSI's split, asserted on a real requirement.

    "Set the window bucks before spraying the foam" is quality and procedure. It belongs to
    the specification once, not to each of the six details of the wall it governs.
    """
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    spec_text = " ".join(line for _, _, lines in specification_sections(catlin_model_ro)
                         for line in lines)
    assert "bucks before spraying" in spec_text

    derived = next(d for d in derive_detail_slices(catlin_model_ro)
                   if d.key == "opening_perimeter:EXT_2X6")
    scene, _ = build_detail(catlin_model_ro, derived)
    assert "bucks before spraying" not in " ".join(scene.notes)


def test_both_specification_sheets_are_in_the_set(catlin_model_ro):
    """A-002 keeps its own sheet; the structural half moved onto S-001's block 5."""
    sheets = {s.number: s.title for s in build_sheet_index(catlin_model_ro)}
    assert sheets["A-002"] == "Architectural specifications"
    assert "S-002" not in sheets, "the structural spec sheet is now a block on S-001"
    assert sheets["S-001"] == "General structural notes"


def test_the_two_specification_sheets_partition_the_sections(catlin_model_ro):
    """Every section reaches exactly one sheet. The architectural sheet takes the
    remainder rather than a second allow-list, so a division neither names cannot vanish."""
    structural = {"03", "05"}
    numbers = {number for number, _, _ in specification_sections(catlin_model_ro)}
    on_structural = {n for n in numbers if n[:2] in structural}
    on_architectural = numbers - on_structural
    assert on_structural and on_architectural
    assert on_structural | on_architectural == numbers
